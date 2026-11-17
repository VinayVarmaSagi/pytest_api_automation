import pytest
import requests
from http import HTTPStatus
import time
from framework.client.api_client import APIClient
from framework.auth.auth_manager import AuthManager
from framework.utils.string_utils import generate_random_string,generate_random_email
from framework.config.config import EXISTING_USER,BASE_URL
from data.user_factory import UserFactory

#post_request_payload={ "name": generate_random_string(6), "email": generate_random_email(), "gender": "male", "status": "active" }
#if i load the payload in advance - it would be shared across test cases and gets loaded even before tests call it


#Merged variable names into a single string separated by a comma
#we can have multiple pytest.mark.parametrize but each should be right above its usage
@pytest.mark.parametrize("setup_status_code, target_status_code, is_duplicate_test", [
    # For a normal creation, there is no setup request (we can pass None)
    pytest.param(None, 201, False, id="created"), #usind id for differentiating in logs
    # For a duplicate test, the setup request MUST succeed (201), and the second must fail (422)
    pytest.param(201, 422, True, id="duplicate-email", marks=pytest.mark.negative),
])

#using post_request_payload() for each row gives each row its own independent dict object,
#so row 1 and row 2 don't share/mutate the same payload — avoids cross-row data pollution.
#note: both calls happen once at collection time (when pytest reads the decorator - ie when mark.parmeterise is loaded),
#not fresh at each test's execution time — but that's fine here since we only need
#uniqueness between the two rows, not freshness relative to when the test actually runs.
@pytest.mark.regression
def test_status_codes_post_method(create_user,setup_status_code, target_status_code, is_duplicate_test, api_client):
    payload = UserFactory.default_user()

    if is_duplicate_test:
        first_response = api_client.post("public/v2/users", request_body=payload)
        # Dynamic comparison using the new parameter!
        assert first_response.status_code == setup_status_code

    response = api_client.post("public/v2/users", request_body=payload)
    assert response.status_code == target_status_code

    #if its duplicate test - first it fires the request and creates account, then the below requests get triggered again. it means duplicate and expected 422 is returned
    #if not duplicate test - it just triggers request and creates account, then it gives expected 201
    #variable names of marker and test method should match

#rewriting above tests like the below
@pytest.mark.regression
def test_create_user_returns_201(api_client):
    payload = UserFactory.default_user()
    response = api_client.post("public/v2/users", request_body=payload)
    user_id = response.json().get("id") if response.status_code == HTTPStatus.CREATED else None
    try:
        assert response.status_code == HTTPStatus.CREATED
    finally:
        if user_id:
            api_client.delete(f"public/v2/users/{user_id}")


@pytest.mark.regression
@pytest.mark.negative
def test_duplicate_email_returns_422(api_client, create_user):
    # create_user already POSTed and asserted 201; reuse its data to trigger the duplicate
    payload = {key: create_user[key] for key in ("name", "email", "gender", "status")}
    response = api_client.post("public/v2/users", request_body=payload)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.slow
def test_slow_example():
    time.sleep(3)