import re
from framework.config.config import MAX_RESPONSE_TIMEOUT
import json
from pathlib import Path
from functools import lru_cache
from jsonschema import Draft7Validator,FormatChecker
from referencing import Registry, Resource
from typing import Type
from pydantic import BaseModel, ValidationError

#this loads once per session
SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"
class ResponseValidator:

    @staticmethod
    def validate_response_time(response,max_ms=MAX_RESPONSE_TIMEOUT):
        elapsed_ms=response.elapsed.total_seconds()*1000 #to convert secs into ms
        assert elapsed_ms<=max_ms,(f'response time expected should be less than {max_ms} but the current response time is {elapsed_ms}')

    @staticmethod
    def validate_status_code(response, expected_status_code):
        assert response.status_code==expected_status_code,(f"expected status code {expected_status_code} but got {response.status_code}")
        #above are assertion msgs, expected vs actual msgs something like AssertionError: Expected status code 201, but got 400
        #static method - since it belongs to class and we can access using classname. and it doesnt have self , similarly we have instance methods and class methods which we will learn later

    @staticmethod
    def validate_request_header(response,expectedkey,expectedvalue):
        assert response.request.headers[expectedkey].startswith(expectedvalue),(f"expected header value as {expectedvalue} but got {response.request.headers[expectedkey]}")

    @staticmethod
    def validate_response_header(response, expectedkey, expectedvalue):
        assert response.headers[expectedkey].startswith(expectedvalue), (
            f"expected response value as {expectedvalue} but got {response.headers[expectedkey]}")

    @staticmethod
    def validate_status_category(response,expected_category):
        response_status_code=response.status_code#status code is int and it doesnt have [0] so convert to str first as shown below
        validate_code=f'{str(response_status_code)[0]}XX' #taking first index and making it like 2XX, 4XX etc
        valid_status_codes = ['2XX', '3XX', '4XX', '5XX']
        if expected_category not in valid_status_codes:
            raise ValueError(f'Invalid expected category target requested : {valid_status_codes}')

        assert expected_category == validate_code,(f"API Status Code mismatch! Got {response_status_code} ({validate_code}), "
            f"but expected category {expected_category}.")#using string concatenation f" {value} , "f" {other valuie} for us"

    @staticmethod
    def validate_response_body_schema_gorestapi(response):
        # replaced ~20 lines of manual loops with the error.json contract
        ResponseValidator.validate_json_schema(response.json(), "error")

    """
    All the below is equivalent to above
    @staticmethod
    def validate_response_body_schema_gorestapi(response):
        expected_response_json_keys = ["field","message"]
        response_json=response.json()

        #checks response json is a list
        assert isinstance(response_json,list),(f"expected the response json as list but got {type(response_json).__name__}")#.__name__ prints just list,dict etc instead of class <'dict'> to keep msgs clear in logs


        #enumerate() gives you both the index and the value while looping — so you don't have to manually track a counter.
        for index,item in enumerate(response_json):#index , item is the dictionary for our 422 go rest response
            assert isinstance(item,dict),(f"expected {item} as dictionary but got {type(item).__name__}")#using "" instead of single because of something like '' comes in between it doesnt throw syntax errors

            #here compare every key of expected key with the actual key instead of comparing every actual key present in expected key
            for expectedkey in expected_response_json_keys:
                assert expectedkey in item,(f"expected the keys from list of {expected_response_json_keys} but {expectedkey} key is missing in response json ")
        
        422 response -
                [
          {
            "field": "email",
            "message": "has already been taken"
          }
        ]
        """
    @staticmethod
    def validate_schema(response,model):
        try:
            return model(**response)
        except Exception as e:
            raise AssertionError(f'schema validation failed:{e}')

    @staticmethod
    def validate_response_field_value(response,field_path_or_name,expected):
        dotmatch="." in field_path_or_name
        if not dotmatch:
            actual = response.get(field_path_or_name)
            assert actual == expected, (
                f"expected '{field_path_or_name}' = {expected!r}, got {actual!r}"
            )
        #if the response is simple and doesnt have any field path with dot like user.msg, then we are trying to fetch the value using            #return None
        else:
            """field_path like 'user.address.city' for nested lookups."""
            keys=field_path_or_name.split(".")#splits into array
            current=response
            for key in keys:
                assert isinstance(current,dict) and key in current,(f"missing field {key} in path {field_path_or_name}")
                current=current[key]
            assert current == expected, (
                    f"expected '{field_path_or_name}' = {expected!r}, got {current!r}"
            )
            #return current

    @staticmethod
    @lru_cache(maxsize=None)  # order matters: @staticmethod must be on top on Python 3.9
    #lru cache reads file and returns the stored dict
    def _load_schema(schema_name):
        # cached -> each schema file is read from disk once per test session
        # the same dict is returned every call, so never mutate the returned schema
        with open(SCHEMA_DIR / f"{schema_name}.json") as f:
            return json.load(f)

    @staticmethod
    @lru_cache(maxsize=None)
    def _schema_registry():
        # lookup table of every schema in schemas/, keyed by file name ("user.json" -> its schema)
        # lets one schema point to another via "$ref": "user.json"; built once per session
        resources = [
            (path.name, Resource.from_contents(json.loads(path.read_text())))
            for path in SCHEMA_DIR.glob("*.json")
        ]
        return Registry().with_resources(resources)

    @staticmethod
    def validate_json_schema(response_json, schema_name):
        # contract check against schemas/<schema_name>.json (Pydantic check stays in validate_schema)
        schema = ResponseValidator._load_schema(schema_name)
        Draft7Validator.check_schema(
            schema)  # SchemaError if the schema FILE is broken (validate() did this for us; Draft7Validator doesn't)
        validator = Draft7Validator(
            schema,
            registry=ResponseValidator._schema_registry(),  # resolves $ref to other schema files
            format_checker=FormatChecker(),
        ) # without format_checker, "format": "email" is ignored
        errors = sorted(validator.iter_errors(response_json), key=lambda e: e.json_path)  # all errors, stable order
        #lambda is python way of writing function  ie lambda e: e.json_path, it tries to get list of errors and its json path
        #way of telling how to sort
        # sorted(["banana", "Kiwi", "apple"], key=str.lower)
        # ['apple', 'banana', 'Kiwi']      ← case-insensitive

        #above returns sorted list, sorted by error path
        #below asserting non empty list if not [] , its false , test fails
        assert not errors, (
                f"Schema '{schema_name}' validation failed with {len(errors)} error(s):\n"
                + "\n".join(f"  {e.json_path}: {e.message}" for e in errors)
        )

    @staticmethod
    def validate_contract(data, contract: Type[BaseModel]):
        # Accepts one dict (GET /users/{id}) or a list (GET /users),
        # so one method covers both single and list endpoints
        items = data if isinstance(data, list) else [data]
        for index, item in enumerate(items):
            try:
                contract.model_validate(item)  # Pydantic v1: contract.parse_obj(item)
            except ValidationError as e:
                # AssertionError makes pytest report a test failure, not a crash;
                # "from None" hides the noisy chained traceback
                raise AssertionError(
                    f"Contract violation at item {index} (id={item.get('id')}):\n{e}"
                ) from None