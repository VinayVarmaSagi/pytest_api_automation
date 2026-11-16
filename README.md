# gorest API Test Automation Framework

A Python API test automation framework built against the public [gorest.co.in](https://gorest.co.in) REST API. It covers request building, auth, response validation (status codes, JSON Schema, Pydantic models), parameterized suites, and consumer contract testing.

## Project layout

```
PythonProject/
├── pytest.ini                  # markers, test paths; run pytest from here
├── .env                        # gorest token (not committed)
├── framework/
│   ├── auth/
│   │   └── auth_manager.py     # loads the bearer token from .env
│   ├── builders/
│   │   └── request_builder.py  # Builder pattern: fluent headers/params/auth
│   ├── client/
│   │   └── api_client.py       # HTTP transport over requests, with logging
│   ├── contract/
│   │   ├── user_contract.py    # consumer contract (Pydantic)
│   │   └── export_schema.py    # writes the contract to framework/schemas/
│   ├── models/
│   │   └── user.py             # full gorest User response model
│   ├── schemas/
│   │   ├── user.json           # full-shape JSON Schema
│   │   └── user_v1.json        # generated consumer contract schema
│   ├── utils/
│   │   └── string_utils.py     # random names/emails for test data
│   └── validators/
│       └── response_validator.py
└── tests/
    ├── conftest.py             # api_client, test_data, create_user fixtures
    ├── test_user_contract.py   # live contract + schema checks
    ├── test_backward_compat.py # offline provider-change simulations
    └── ...                     # CRUD, status code, parameterized suites
    
#Sequence of files execution : when i run this in terminal - pytest
#1.requirements.txt - Before any run (one time only). never loaded during a test run. It’s only read when you run pip install -r requirements.txt to install packages (pytest, requests, python-dotenv, and so on) into your virtual environment.
#2.Pytest finds the root directory and reads pytest.ini. If there’s no pytest.ini, it looks in pyproject.toml, tox.ini or setup.cfg instead. From this file it picks up addopts, markers, testpaths, log settings and so on.
#3.Installed plugins load, for example pytest-html or pytest-xdist if you have them.
#4.The root conftest.py is imported. This one step pulls in a lot:
#Its import lines load your   modules: config.py, auth_manager.py, api_client.py, request_builder.py, response_validator.py, string_utils.py.
#config.py runs load_dotenv(), so .env gets read here.
#logging.basicConfig(...) runs.
#Fixtures and hooks get registered, but not run yet.
#Python also runs any __init__.py files in package folders as those packages get imported.
#5.pytest_addoption runs and registers --run-slow. Then the CLI gets parsed: addopts from pytest.ini plus whatever you typed.
#6.Collection. Pytest walks testpaths, imports any nested conftest.py files, then imports each test_*.py file and finds the test functions in it.
#7.pytest_collection_modifyitems runs: it adds the security markers and skips slow tests.
#8.Tests run. For each test:
#Fixtures are set up. Session-scoped ones (auth_token, api_client) are created only on first need.
#The autouse fixture (log_test_boundaries) starts.
#The test body runs.
#Function-scoped teardown runs (create_user deletes its user).
#9.End of session. Session teardown runs (api_client closes its session), then pytest prints the summary.
#Other points :Files that never load during a test run: requirements.txt, .gitignore and README.md.
#Other points : A key point - config.py doesn’t load because pytest knows about it. It loads only because conftest.py (or a test file) imports it. If nothing imported it, it would never run.
    
```