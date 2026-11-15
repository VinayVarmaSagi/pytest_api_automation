#this test covers parametrize and payload matrix

import pytest
from data.user_factory import UserFactory
from framework.utils.string_utils import generate_random_string

@pytest.mark.parametrize("request_payload", [
    pytest.param(  UserFactory.default_user(),id="created-user-1"), #usind id for differentiating in logs
    pytest.param( UserFactory.default_user(), id="created-user-2"),
    #each row gets its own payload and doesnt override during the process be it test run or session or per worker
])


@pytest.mark.regression
def test_data_driven_get_method(request_payload,api_client):#fixtures are fetched during setup (before test execution and after collection)
    response = api_client.post("public/v2/users", request_body=request_payload)
    assert response.status_code == 201
    #its better to have this in fixture and delete the userid after tests so it doesnt put heavy load on gorest with unwanted data

@pytest.mark.regression
@pytest.mark.parametrize("name_length, expected_status, expected_message", [
    pytest.param(0,   422, "can't be blank", id="empty-name"),
    pytest.param(1,   201, None,             id="min-valid-1-char"),
    pytest.param(200, 201, None,             id="max-valid-200-chars"),
    pytest.param(201, 422, "is too long",    id="max-breached-201-chars"),
    pytest.param(None, 422, "can't be blank", id="missing-name-key")
])
def test_boundary_values_name(name_length, expected_status, expected_message, api_client):
    # building the payload at execution time so every run and retry gets a fresh unique email
    if name_length is None:
        payload = UserFactory.default_user()
        payload.pop("name")  # key removed entirely, not sent as ""
    else:
        name = generate_random_string(name_length) if name_length > 0 else ""
        payload = UserFactory.default_user(name=name)

    response = api_client.post("public/v2/users", request_body=payload)
    assert response.status_code == expected_status, response.text

    if expected_status == 422:
        errors = response.json()   # list of {"field": ..., "message": ...}


        fields = [err["field"] for err in errors]
        print(fields)
        assert fields == ["name"], f"unexpected errors: {errors}" # name must be the only failing field, so unrelated errors can't hide - anything other than name comes, it will fail here
        assert expected_message in errors[0]["message"]
#Adding comment for uncommited changes, stash error
#adding another commit which is not commited this time