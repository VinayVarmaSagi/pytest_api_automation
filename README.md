# gorest API Test Automation Framework

A Python API test automation framework built against the public [gorest.co.in](https://gorest.co.in) REST API. It covers request building, auth, response validation (status codes, JSON Schema, Pydantic models), parameterized suites, and consumer contract testing.

## Tech stack

| Area | Tool |
|---|---|
| Language | Python 3.9 |
| Test runner | pytest 8.4 |
| HTTP | requests |
| Response models & contracts | Pydantic v2 |
| JSON Schema validation | jsonschema (+ referencing for `$ref`) |
| Config & secrets | python-dotenv (`.env`) |

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
```

Every package folder has an `__init__.py`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pytest requests pydantic python-dotenv jsonschema
```

Create `.env` at the project root with your gorest token (get one at gorest.co.in after signing in). Use the variable name that `auth_manager.py` reads:

```
GOREST_TOKEN=your_token_here
```

## Running tests

Always run from the project root. pytest only searches upward for `pytest.ini`, so running from inside `tests/` loses the config and `rootdir`.

```bash
pytest                          # everything
pytest -m contract              # contract + backward-compat tests only
pytest tests/test_backward_compat.py -v   # offline, no token needed
```

Regenerate the contract schema after changing `UserContract`:

```bash
python -m framework.contract.export_schema
```

## Framework components

**`APIClient`** is the only place that talks HTTP. Tests never call `requests` directly, so logging, base URL and error handling live in one spot.

**`RequestBuilder`** builds request kwargs with method chaining (each method does `return self`), then `.build()` returns them for the client. The payload is passed to `client.post()` separately from the builder output.

**`AuthManager`** reads the token from `.env` so secrets never land in code or git.

**`ResponseValidator`** holds static methods, since validation needs no state:
- `validate_status_code(response, expected)`
- `validate_json_schema(data, name)` validates against `framework/schemas/<name>.json`. It loads every schema in that folder into a registry so `$ref`s resolve, which means **every file there must declare `$schema`**.
- `validate_contract(data, ContractModel)` accepts a single object or a list and raises `AssertionError` with the failing item's index and id.
- header validation helpers

**`models/user.py`** is a Pydantic model of the full gorest user response.

**Fixtures (`conftest.py`)**
- `api_client`: shared client instance
- `test_data`: factory that returns a fresh random user payload per call
- `create_user`: creates a user via POST, yields it, deletes it on teardown

## Contract testing

**Schema test vs contract test.** A schema test checks the full shape of one payload. A contract test checks only what *this consumer* depends on. If gorest drops a field we never read, the schema test fails but the contract test passes, which is correct.

**`UserContract`** (`framework/contract/user_contract.py`)
- Only the fields our tests use: `id`, `name`, `email`, `gender`, `status`
- `extra="ignore"` (tolerant reader): new provider fields are backward compatible and must not fail us. `forbid` would turn every additive change into a false alarm.
- `gender` and `status` are strict `Literal`s, so a new enum value fails the contract.

**Committed artifact.** `export_schema.py` writes `framework/schemas/user_v1.json` with sorted keys and fixed indentation, so a PR diff on that file shows exactly how the contract changed.

**Backward compatibility suite** (`tests/test_backward_compat.py`) applies simulated provider changes to a known-good payload:

| Provider change | Contract result |
|---|---|
| New field added | pass |
| Required field removed | fail |
| `id` → non-numeric string | fail |
| `id` → numeric string (`"8640717"`) | **pass**: Pydantic lax mode coerces it; use `StrictInt` to catch it |
| New `status` value (`"suspended"`) | fail: enum expansion breaks a strict consumer |
| Required field becomes `null` | fail |

**When to use contract tests:** services that deploy independently, many consumers on one provider, third-party APIs you don't control (like gorest). **What they don't catch:** business logic bugs, performance, and anything the contract doesn't mention.

**Pact.** Kept conceptual: the consumer publishes a pact file, a broker stores it, the provider replays every consumer's interactions (with provider states) in CI, and `can-i-deploy` checks the version compatibility matrix before either side ships.

## Gotchas learned

- **Eventual consistency:** gorest can 404 on a GET immediately after a POST. Wait ~3 seconds between them.
- **Fixtures over module variables:** module-level variables don't update from inside tests; return values from fixtures instead.
- **Clean up in `finally`** (or fixture teardown) so a failed assertion doesn't leave test users behind in gorest.
- **Schema registry needs `$schema`:** a JSON file without it raises `CannotDetermineSpecification` for *every* schema test, not just the one using that file.
- **Pydantic coerces by default:** `"5"` passes as an `int`. Know what your validator accepts.
- **urllib3 LibreSSL warning** on macOS system Python is harmless for this project.