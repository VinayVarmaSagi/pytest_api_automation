import time
import pytest
import os

from framework.auth.auth_manager import AuthManager
from framework.client.api_client import APIClient
from framework.builders.request_builder import RequestBuilder
from framework.utils.string_utils import generate_random_string, generate_random_email
from framework.validators.response_validator import ResponseValidator
from framework.config.config import TOKEN

@pytest.mark.smoke
def test_positive_auth(test_data):
    auth = AuthManager()
    client = APIClient("https://gorest.co.in/", headers=auth.get_headers())
    payload=test_data(gender="female")
    request_builder = RequestBuilder().build()
    post_response = client.post("public/v2/users", request_body=payload,**request_builder)
    ResponseValidator.validate_response_time(post_response)
    ResponseValidator.validate_status_category(post_response, '2XX')
    ResponseValidator.validate_status_code(post_response,201)
    post_response_json = post_response.json()
    print(post_response_json)
    #assert post_response.status_code == 201  # its integer type

    #return post_response_json["id"]  # we need to use this in dictionary format instead of .id as this is python object which is like a dictionary format
    #dictionaries dont support attributes by default ie cant use .id
    #response_json['id']   # works — dict key access
    #response_json.id      # AttributeError: 'dict' object has no attribute 'id'
    #instead of using post_response_json["id"] use post_response_json.get("id") as this returns None instead of throwing keyerror if this doesnt exist in response
    return post_response_json.get("id")

@pytest.mark.slow
@pytest.mark.regression
@pytest.mark.security
@pytest.mark.negative
def test_negative_auth_manager_refresh_logic():
    auth = AuthManager(token="invalid",token_ttl_seconds=1)#sending invalid token from test instead of taking from .env file which is valid
    assert auth.is_token_expired()==False #the token is not expired yet
    time.sleep(1.5)#intentionally waiting beyond the token valid time ie token_ttl_seconds
    assert auth.is_token_expired() == True#the token is expired now
    old_issued_at=auth._token_issued_at
    auth.get_valid_token()
    new_issued_at=auth._token_issued_at
    assert new_issued_at>old_issued_at#new token issued time more than old issued token time
    assert auth.is_token_expired() == False  # the token is new, hence not expired yet

@pytest.mark.regression
@pytest.mark.security
@pytest.mark.negative
def test_negative_auth_invalid_token_rejected(make_client,test_data):
    #auth = AuthManager(token="invalid",token_ttl_seconds=1)#sending invalid token from test instead of taking from .env file which is valid
    client = make_client(token="invalid")
    #client = APIClient("https://gorest.co.in/", headers=auth.get_headers())
    payload=test_data(gender="female")
    #builder = RequestBuilder().with_name().with_email().with_gender("female").with_status("active")
    request_builder = RequestBuilder().build()
    post_response = client.post("public/v2/users", request_body=payload,**request_builder)
    ResponseValidator.validate_response_time(post_response)
    ResponseValidator.validate_status_code(post_response,401)
    post_response_json = post_response.json()
    ResponseValidator.validate_response_field_value(post_response_json,"message","Invalid token")
    print("response json is",post_response_json)
    #assert post_response_json["message"] == "Invalid token"

@pytest.mark.security
@pytest.mark.negative
@pytest.mark.skipif(not TOKEN, reason="TOKEN env var not set: needs a valid token for the initial 201 call")
def test_negative_auth_token_corrupted_mid_suite(make_client, test_data):
    auth = AuthManager()  # the object we'll corrupt mid-test
    client = make_client()  # its own internal auth is irrelevant — we override per call

    payload=test_data(gender="female")
    #builder = RequestBuilder().with_name().with_email().with_gender("female").with_status("active")
    request = RequestBuilder().build()
    request.pop("auth", None)

    good_response = client.post("public/v2/users", request_body=payload,
                                auth=auth._token, **request)
    ResponseValidator.validate_response_time(good_response)
    ResponseValidator.validate_status_code(good_response,201)


    auth._token = "corrupted"
    assert auth.is_token_expired() == False

    bad_response = client.post("public/v2/users", request_body=payload,
                               auth=auth._token, **request)
    ResponseValidator.validate_response_time(bad_response)
    ResponseValidator.validate_status_code(bad_response, 401)
    post_response_json = bad_response.json()
    ResponseValidator.validate_response_field_value(post_response_json, "message", "Invalid token")
    """auth = AuthManager()#during creation proper token is fetched but then we are corrputing it
    #the difference between this test and above is here - we fetch valid token from auth and then corrupting it
    #here happening in between of suite
    #but in above test test_negative_auth_invalid_token_rejected the token itself we are sending wrong

    client = make_client(token="invalid")
    #client=make_client(token=auth.get_valid_token())
    # simulating "token went bad for reasons other than expiration" — e.g. revoked server-side
    #auth._token = "corrupted"  # writing in between the invalid token
    # here my token time is not expired yet, so it will not generate new token ie fetch from .venv, it will use this only

    #client = APIClient("https://gorest.co.in/", headers=auth.get_headers())

    assert auth.is_token_expired()==False

    builder = RequestBuilder().with_name().with_email().with_gender("female").with_status("active")
    request = builder.build()
    post_response = client.post("public/v2/users", request_body=builder.get_payload(),**request)
    ResponseValidator.validate_response_time(post_response)
    ResponseValidator.validate_status_code(post_response, 401)
    post_response_json = post_response.json()
    print("response json is", post_response_json)
    ResponseValidator.validate_response_field_value(post_response_json,"message","Invalid token")"""

#difference of last two tests summarised below
"""
in Scenario B, steps 1–2 could have made a perfectly successful 201 call if you'd called client.post(...) right there — 
the token was genuinely good. It's only because you overwrote auth._token in step 3, 
before the next request went out, that step 4 fails. In a real suite, 
the equivalent isn't you manually typing "corrupted" — it's something like: your access token's TTL genuinely expiring mid-run, 
a server-side session revocation, or a secrets-rotation job firing while your 20-minute regression suite is still executing. 
Test A can never catch that class of bug, because the token is bad before any request is ever attempted. 
Test B is the one that actually exercises "a request that used to succeed now fails, and my framework needs to surface that as a clean 401, not a stack trace."
"""