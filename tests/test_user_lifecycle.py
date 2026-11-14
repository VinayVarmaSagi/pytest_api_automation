from framework.builders.request_builder import RequestBuilder
from framework.validators.response_validator import ResponseValidator
import time

def test_api_chaining(test_data,api_client):
    #POST Request
    payload = test_data(gender="female",status="active")
    request_builder = RequestBuilder().build()
    post_response = api_client.post("public/v2/users", request_body=payload, **request_builder)
    post_response_json = post_response.json()
    ResponseValidator.validate_status_code(post_response, 201)
    user_id = post_response_json.get("id")

    try:
        #POST Validations which may fail need to catch so we dont miss deleting the created resource
        ResponseValidator.validate_response_time(post_response)
        ResponseValidator.validate_request_header(post_response, "content-type", "application/json")

        # Wait for sometime before calling GET
        time.sleep(3)

        # GET Request

        get_response = api_client.get(f"public/v2/users/{user_id}")
        ResponseValidator.validate_response_time(get_response)
        ResponseValidator.validate_status_code(get_response, 200)
        ResponseValidator.validate_response_header(get_response, "content-type", "application/json")
        get_json = get_response.json()
        assert payload.items() <= get_json.items(), f"GET body doesn't match POST payload: {get_json}"
        #items gives key value pairs ofr esponse
        assert get_json.get("id") == user_id

        #UPDATE Request
        put_payload = test_data(status="inactive")
        put_response = api_client.put(f"public/v2/users/{user_id}", request_body=put_payload, **request_builder)
        ResponseValidator.validate_response_time(put_response)
        ResponseValidator.validate_status_code(put_response, 200)
        ResponseValidator.validate_request_header(put_response, "content-type", "application/json")
        ResponseValidator.validate_response_field_value(put_response.json(),"status","inactive")

    finally:
    #DELETE Request
        delete_response = api_client.delete(f"public/v2/users/{user_id}")
        ResponseValidator.validate_response_time(delete_response)
        ResponseValidator.validate_status_code(delete_response, 204)

    #GET Request again to check the resource/userid is deleted
    get_response = api_client.get(f"public/v2/users/{user_id}")
    ResponseValidator.validate_response_time(get_response)
    ResponseValidator.validate_status_code(get_response, 404)