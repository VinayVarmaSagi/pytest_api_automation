import pytest

from framework.auth.auth_manager import AuthManager
from framework.client.api_client import APIClient
from framework.builders.request_builder import RequestBuilder
from framework.utils.string_utils import generate_random_string, generate_random_email
from framework.validators.response_validator import ResponseValidator

#auth=AuthManager()
#client=APIClient("https://gorest.co.in/",headers=auth.get_headers())

@pytest.fixture
def create_user(api_client,test_data):#its called for each of the get and delete tests separately
    payload=test_data(gender="female")
    #builder = RequestBuilder().with_name().with_email().with_gender("female").with_status("active")
    request=RequestBuilder().build()
    post_response = api_client.post("public/v2/users", request_body=payload,**request)
    ResponseValidator.validate_response_time(post_response)
    ResponseValidator.validate_status_code(post_response,201)
    ResponseValidator.validate_status_category(post_response, '2XX')
    post_response_json = post_response.json()
    print(post_response_json)
    #return post_response_json["id"]#we need to use this in dictionary format instead of .id as this is json response which is like a dictionary format
    return post_response_json.get("id")

@pytest.mark.smoke
@pytest.mark.regression
def test_get_user(create_user,api_client,test_data):#parameter is used here for fixture which calls and exeuctes that and its return value will be used inside this test
    user_id=create_user#we use this since its a fixture not a method, hence we dont use create_user()
    get_response=api_client.get(f"public/v2/users/{user_id}")
    ResponseValidator.validate_response_time(get_response)
    ResponseValidator.validate_status_code(get_response,200)
    ResponseValidator.validate_status_category(get_response, '2XX')
    get_response_json=get_response.json()
    print(get_response_json)


    assert get_response_json["id"] == user_id
    #get test if fails - still it executes delete test. pytest need to independent

@pytest.mark.smoke
@pytest.mark.regression
def test_delete_user(create_user,api_client):
    user_id=create_user
    delete_response=api_client.delete(f"public/v2/users/{user_id}")
    ResponseValidator.validate_response_time(delete_response)
    ResponseValidator.validate_status_code(delete_response, 204)
    ResponseValidator.validate_status_category(delete_response, '2XX')




