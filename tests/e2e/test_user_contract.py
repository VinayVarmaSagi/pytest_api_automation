import pytest

from framework.builders.request_builder import RequestBuilder
from framework.contract.user_contract import UserContract
from framework.validators.response_validator import ResponseValidator

# Two layers of checks on purpose:
#   validate_json_schema -> full shape of the gorest response (schema test)
#   validate_contract    -> only the fields OUR tests depend on (consumer contract)
# A dropped field we never use fails the schema check but not the contract.


@pytest.mark.contract
def test_list_users_honor_contract(api_client):
    # List endpoint: every item must satisfy the contract, not just the first one
    get_response = api_client.get("public/v2/users")
    ResponseValidator.validate_status_code(get_response, 200)

    users = get_response.json()
    assert isinstance(users, list) and users, "expected a non-empty list of users"
    ResponseValidator.validate_contract(users, UserContract)


@pytest.mark.contract
def test_get_single_user_matches_schema(api_client, create_user):
    userid = create_user["id"]
    get_response = api_client.get(f"public/v2/users/{userid}")
    ResponseValidator.validate_status_code(get_response, 200)
    ResponseValidator.validate_json_schema(get_response.json(), "user")
    ResponseValidator.validate_contract(get_response.json(), UserContract)


@pytest.mark.contract
def test_create_user_response_matches_schema(api_client, test_data):
    payload = test_data()
    request_builder = RequestBuilder().build()  # pull payload out separately since client.post() takes it as its own positional-ish kwarg, not part of **request
    post_response = api_client.post("public/v2/users", request_body=payload, **request_builder)
    ResponseValidator.validate_status_code(post_response, 201)
    post_response_json = post_response.json()
    user_id = post_response_json.get("id")

    try:
        ResponseValidator.validate_json_schema(post_response_json, "user")
        ResponseValidator.validate_contract(post_response_json, UserContract)
    finally:
        # cleanup runs even if a schema/contract assertion fails,
        # so test users don't pile up in gorest
        delete_response = api_client.delete(f"public/v2/users/{user_id}")
        assert delete_response.status_code in (204, 404), (
            f"failed in teardown step, got {delete_response.status_code}"
        )