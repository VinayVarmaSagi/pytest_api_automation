import re
import pytest
from framework.validators.response_validator import ResponseValidator
from framework.builders.request_builder import RequestBuilder

# Known-good baseline. Each test breaks exactly ONE thing in a copy of it.
VALID_USER = {
    "id": 1,
    "name": "Nikky",
    "email": "nikky@company.com",
    "gender": "female",
    "status": "active",
}

REMOVE = object()  # sentinel: "delete this field" (None can't be used - None is a real value to test)
#so we should use this only to avoid all other options which may be used in test ex like null, NONE

@pytest.mark.parametrize(
    "field, value, expected_error",
    [
        pytest.param("id", "123", "$.id: '123' is not of type 'integer'", id="id_as_string"),
        pytest.param("gender", "other", "$.gender: 'other' is not one of", id="gender_not_in_enum"),
        pytest.param("email", "not-an-email", "$.email: 'not-an-email' is not a 'email'", id="bad_email_format"),
        pytest.param("extra", 1, "('extra' was unexpected)", id="unexpected_field"),
        pytest.param("name", REMOVE, "'name' is a required property", id="missing_required_field"),
    ],
)
def test_user_schema_rejects_contract_drift(field, value, expected_error):
    user = dict(VALID_USER)  # copy so tests never mutate the shared baseline (shallow copy is enough: flat dict)
    if value is REMOVE:
        del user[field]
    else:
        user[field] = value

    # match= checks the failure is for the RIGHT reason, not just "something failed"
    # re.escape because match= is a regex and our messages contain $ . ( ) '
    with pytest.raises(AssertionError, match=re.escape(expected_error)):#escape makes every case check exactly the text you typed.
        ResponseValidator.validate_json_schema(user, "user")


def test_user_schema_accepts_valid_baseline():
    # guards the negative tests: if this fails, VALID_USER itself is broken
    ResponseValidator.validate_json_schema(VALID_USER, "user")

def test_get_users_list_matches_schema(api_client,create_user):
    userid = create_user["id"]
    print(userid)
    get_response = api_client.get(f"public/v2/users")
    ResponseValidator.validate_status_code(get_response, 200)
    ResponseValidator.validate_json_schema(get_response.json(), "users_list")

def test_get_single_user_matches_schema(api_client,create_user):
    # borrow a real id from the list instead of hardcoding one (gorest data changes daily)
    userid = create_user["id"]
    get_response = api_client.get(f"public/v2/users/{userid}")
    ResponseValidator.validate_status_code(get_response, 200)
    ResponseValidator.validate_json_schema(get_response.json(), "user")

def test_invalid_create_returns_error_schema(api_client):
    payload = {"name": "", "email": "not-an-email", "gender": "other", "status": "active"}
    request_builder = RequestBuilder().build()  # pull payload out separately since client.post() takes it as its own positional-ish kwarg, not part of **request
    post_response = api_client.post("public/v2/users", request_body=payload, **request_builder)
    ResponseValidator.validate_status_code(post_response, 422)
    ResponseValidator.validate_response_body_schema_gorestapi(post_response)

def test_create_user_response_matches_schema(api_client,test_data):
    payload = test_data()
    request_builder = RequestBuilder().build()  # pull payload out separately since client.post() takes it as its own positional-ish kwarg, not part of **request
    post_response = api_client.post("public/v2/users", request_body=payload, **request_builder)
    ResponseValidator.validate_status_code(post_response, 201)
    ResponseValidator.validate_json_schema(post_response.json(), "user")
    post_response_json=post_response.json()
    # cleanup so test users don't pile up in gorest
    user_id = post_response_json.get("id")
    delete_response = api_client.delete(f"public/v2/users/{user_id}")
    assert delete_response.status_code in (204, 404), (f"failed in teardown step , got {delete_response.status_code}")


