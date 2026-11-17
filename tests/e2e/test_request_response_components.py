import pytest
import json
from framework.auth.auth_manager import AuthManager
from framework.client.api_client import APIClient
from framework.builders.request_builder import RequestBuilder
from framework.utils.string_utils import generate_random_string, generate_random_email
from framework.validators.response_validator import ResponseValidator

@pytest.fixture
def create_user(api_client,test_data):#its called for each of the tests separately
    #this fixture is calling another fixture
    payload=test_data(gender="female")
    #builder = RequestBuilder().with_name().with_email().with_gender("female").with_status("active")
    request=RequestBuilder().build()
    post_response = api_client.post("public/v2/users", request_body=payload,**request)
    ResponseValidator.validate_response_time(post_response)
    ResponseValidator.validate_status_code(post_response, 201)
    post_response_json = post_response.json()
    print(post_response_json)
    #assert post_response.status_code == 201#its integer type

    #assert post_response.request.body["name"]==post_response_json["name"]#comparing request body name sent with response body name using requests
    #cant use above directly for body validations since its in bytes - so convert to Python object using loads
    post_request_body=json.loads(post_response.request.body)#converts to python dictionary
    #assert post_request_body["name"]==post_response_json["name"]
    assert post_request_body.get("name") == post_response_json.get("name")
    return post_response_json.get("id")#we need to use this in dictionary format instead of .id as this is json response which is like a dictionary format

@pytest.mark.smoke
@pytest.mark.regression
def test_get_request_headers_validation(create_user,api_client):
    user_id = create_user  # we use this since its a fixture not a method, hence we dont use create_user()
    get_response = api_client.get(f"public/v2/users/{user_id}")
    get_response_json = get_response.json()
    print(get_response_json)
    #assert get_response.status_code == 200
    ResponseValidator.validate_response_time(get_response)
    ResponseValidator.validate_status_code(get_response,200)
    #assert get_response.request.headers["Authorization"].startswith("Bearer")#validating request headers using response.request.headers
    ResponseValidator.validate_request_header(get_response,"Authorization","Bearer")
    ResponseValidator.validate_response_header(get_response,"content-type","application/json")
    #assert "application/json" in get_response.headers["content-type"]#works like contains, using contains because this string will also have chartset-utf 8 something
