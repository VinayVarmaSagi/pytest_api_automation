from os import name
from http import HTTPStatus

import pytest
import requests
from framework.auth.auth_manager import AuthManager
from framework.builders.request_builder import RequestBuilder
from framework.client.api_client import APIClient
from framework.utils.string_utils import generate_random_email, generate_random_string
from framework.validators.response_validator import ResponseValidator
from framework.config.config import EXISTING_USER

def test_get_is_idempotent(api_client):
    get_response_1=api_client.get(f"public/v2/users/{EXISTING_USER}")
    get_response_json_1=get_response_1.json()
    print(get_response_json_1)
    #assert get_response_1.status_code==200
    ResponseValidator.validate_response_time(get_response_1)
    ResponseValidator.validate_status_code(get_response_1,200)

    get_response_2 = api_client.get(f"public/v2/users/{EXISTING_USER}")
    get_response_json_2 = get_response_2.json()
    print(get_response_json_2)
    #assert get_response_2.status_code == 200
    ResponseValidator.validate_response_time(get_response_2)
    ResponseValidator.validate_status_code(get_response_1,200)
    assert get_response_json_1==get_response_json_2
    #calling get twice and comparing response to check if get is idempotent(any no of requests doesnt change the behaviour of the resource)

def test_put_is_idempotent(api_client,test_data):
    #builder = RequestBuilder().with_name("vin va").with_status("inactive")
    payload=test_data(name="vin va",status="inactive")
    request = RequestBuilder().build()
    put_response_1=api_client.put(f"public/v2/users/{EXISTING_USER}",request_body=payload,**request)
    ResponseValidator.validate_response_time(put_response_1)
    ResponseValidator.validate_status_code(put_response_1,200)
    put_response_json_1 = put_response_1.json()
    print(put_response_json_1)
    ResponseValidator.validate_response_field_value(put_response_json_1,"status","inactive")
    ResponseValidator.validate_response_field_value(put_response_json_1,"name","vin va")


    put_response_2=api_client.put(f"public/v2/users/{EXISTING_USER}",request_body=payload,**request)
    ResponseValidator.validate_response_time(put_response_2)
    ResponseValidator.validate_status_code(put_response_2, 200)
    put_response_json_2 = put_response_2.json()
    print(put_response_json_2)
    ResponseValidator.validate_response_field_value(put_response_json_2, "status", "inactive")
    ResponseValidator.validate_response_field_value(put_response_json_2, "name", "vin va")


@pytest.mark.regression
def test_post_is_idempotent(api_client,test_data):
    #builder = RequestBuilder().with_name().with_email().with_gender("female").with_status("active")
    request=RequestBuilder().build()
    payload=test_data(gender="female",status="active")
    post_response1 = api_client.post("public/v2/users", request_body=payload,**request)
    ResponseValidator.validate_response_time(post_response1)
    ResponseValidator.validate_status_code(post_response1, 201)

    post_response_json1 = post_response1.json()
    print(post_response_json1)


    post_response2 = api_client.post("public/v2/users", request_body=payload,**request)
    ResponseValidator.validate_response_time(post_response2)
    ResponseValidator.validate_status_code(post_response2, 422)#because post doesnt accept same payloads multipletimes with same details
    post_response_json2 = post_response2.json()
    print(post_response_json2)
    assert post_response_json1!=post_response_json2

@pytest.mark.regression
@pytest.mark.xfail(
    reason="KNOWN-BUG <ticket-id>: GET /users/1234 expected 200, API returns 404",
    raises=AssertionError,#only this error we want to raise when status code is not matching, strictly focusing on the bug here ie status code mismatch
    strict=True#if we remove this , it will run and get passed
)
def test_xfail_because_of_bug(api_client):
    response = api_client.get("public/v2/users/1234")
    ResponseValidator.validate_status_code(response, HTTPStatus.OK)#if this passes, test fails as xafil works other way. if this fails xfail gives xfail warning



