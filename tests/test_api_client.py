import json
import pytest
import time
#from framework.client.api_client import APIClient
from framework.builders.request_builder import RequestBuilder
from framework.models.user import User
#from framework.auth.auth_manager import AuthManager
from framework.validators.response_validator import ResponseValidator

#@pytest.mark.smoek will fail as this is mistyped and not matching with markers in pytest.ini
@pytest.mark.smoke
def test_get_created_user(api_client, create_user):#composite fixture uses create user fixture and api_fixtures
    response = api_client.get(f"public/v2/users/{create_user['id']}")
    assert response.status_code == 200

@pytest.mark.smoke
@pytest.mark.regression
def test_get_user(create_user,api_client):
    userid = create_user["id"]
    print(userid)
    time.sleep(3)
    get_response = api_client.get(f"public/v2/users/{userid}")
    ResponseValidator.validate_response_time(get_response)
    ResponseValidator.validate_status_code(get_response, 200)
    ResponseValidator.validate_response_header(get_response, "content-type","application/json")
    pydantic_get_response=User(**get_response.json())
    assert pydantic_get_response.id==userid
    print(json.dumps(get_response.json(), indent=4))

@pytest.mark.regression
def test_update_user(create_user,api_client,test_data):
    userid = create_user["id"]
    payload=test_data(status="inactive")
    request_builder = RequestBuilder().build()
    put_response=api_client.put(f"public/v2/users/{userid}", request_body=payload, **request_builder)
    ResponseValidator.validate_response_time(put_response)
    ResponseValidator.validate_status_code(put_response, 200)
    ResponseValidator.validate_request_header(put_response,"content-type", "application/json")

@pytest.mark.regression
def test_delete_user(create_user,api_client):
    userid = create_user["id"]
    delete_response=api_client.delete(f"public/v2/users/{userid}")
    ResponseValidator.validate_response_time(delete_response)
    ResponseValidator.validate_status_code(delete_response,204)