#anywhere inside tests folder or sub folder will detect this no need to get this imported explicitly to run tests
import pytest
import logging

from framework.builders.request_builder import RequestBuilder
from framework.auth.auth_manager import AuthManager
from framework.client.api_client import APIClient
from framework.utils.string_utils import generate_random_string,generate_random_email
from framework.config.config import BASE_URL
from framework.validators.response_validator import ResponseValidator

#below runs when conftest.py file is loaded
#the below is also kind of an autouse fixture but doesnt have parameter usage, runs for every test in its scope
#This runs at module load time (once, when conftest.py is imported), not as a fixture at all currently.
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#logging.INFO - constant from logging module. if info is set both info and warning logs are shown. if only warning, the info logs would be dropped. warning is at higher severity than info,the configured level and above gets printed. INFO, WARNING, ERROR and CRITICAL get through; DEBUG is dropped.
#%(asctime)s - timestamp of log call
#%(name)s- loggers name, which is __name__ from apiclient logging.getLogger(__name__)
#%(levelname)s - INFO,WARNING etc
#%(message)s - actual f string message
#%()s is older style of printing , now we use f string
#note only warning and error gets printed, pytest swallows usually those passed logs, if we want use -s in cmd and exeucte
#logging.basicConfig(level=.....) - plain statement that runs once, when pytest imports conftest.py during startup.
#Every logger created with logging.getLogger(__name__) (like the one in APIClient) inherits this setup. Pytest also captures logs and only shows them for failing tests unless you run with -s.


@pytest.fixture(scope="session")
def auth_token():
    auth = AuthManager()
    return auth.get_headers()  # returns {"Authorization": "Bearer ..."} #uses return rather than yield as there is nothing to cleanup afterwards

@pytest.fixture(scope="session")
def api_client(auth_token):
    client = APIClient(BASE_URL, headers=auth_token)
    yield client
    client.session.close()
#This is dependency injection in action — api_client doesn't build its own AuthManager, it receives auth_token as a parameter, and pytest resolves that chain for you (runs auth_token first since api_client declares it needs it).
#A fixture can only depend on fixtures of the same or wider scope. Session depending on session is fine. A session fixture depending on a function-scoped one would raise a ScopeMismatch error.
#@pytest.fixture(scope="session")
#using session as scope here because we want to use this across all test runs for ex suite
#here all the tests use the shared object - using so which doesnt affect here
#if we go with default function scope, it would create object for every test and eventually reloading .env, new auth headers etc which is not required here
#even if the ttl time lapses in between the test run, it would still refresh and create new token for us without creating any issues.
#That's the benefit of putting the expiry logic inside AuthManager rather than relying on fixture scope to manage freshness — they're decoupled by design, which is good architecture.
#meaning if we use fixture scope as function for each test to avoid token refresh issue , it would create as many token as tests. which is of no use as the token is still not expired.
#read below for additional details

@pytest.fixture(scope="function")
#using function scoped here since we dont want to ripple these invalid token changes to positive tests
#using function inside function
#Why bother nesting _make instead of just writing a plain fixture that takes arguments directly?
#pytest fixtures can't take arbitrary arguments from the test the way regular functions can — a fixture's only "input" is other fixtures. So if you want per-test flexibility (different token, different token_ttl_seconds for different tests), you can't just do def make_client(token): ... — pytest has no way to know what token should be per test. The workaround is: the fixture returns a function, and the test calls that function directly with whatever arguments it needs. That's the whole reason for the extra layer — it's not returning a client, it's returning a client-builder.
#fixtures cant taken input parameters hence we are using function inside the function
#te
def make_client():
    """Returns a function tests can call to build a client with custom auth config."""
    clients = []

    def _make(token=None, token_ttl_seconds=120):
        auth = AuthManager(token, token_ttl_seconds)
        client = APIClient(BASE_URL, auth.get_headers())
        clients.append(client)
        return client

    yield _make

    for client in clients:## close every client this test created via the factory (a test may create several). this doesnt impact in parallel runs as each process gets its own client since its function scoped.
        client.session.close()

    return _make#fixture returning the function here instead of object as seen in above fixture.closing client session after each test starts a new session(function scope here hence new client/session for each test)

@pytest.fixture()#default scope here ie function
#test_data produces a factory function, not a stored value — there's nothing here that GET/POST/DELETE calls could mutate or leave stale, because each call to _make() builds a brand-new payload from scratch. That's different from api_client, where reusing the same instance across tests is the point (connection pooling, one auth header set). No shared state to protect here, so plain function scope (the default — no scope= argument needed) is the right call
#Factory function — what you just wrote. Any function (or fixture) that, when called, produces and returns an object — here, a payload dict built via RequestBuilder. That's the whole definition. No formal structure required, no class hierarchy, just "calling this thing gives you a new instance of something."
def test_data():
    """Returns a function tests can call to build user payloads, with random defaults that can be overridden."""
    def _make(name=None, email=None, status="active", gender="male"):
        builder=RequestBuilder()
        builder.with_name(name if name is not None else generate_random_string(7))
        builder.with_email(email if email is not None else generate_random_email())
        builder.with_status(status)
        builder.with_gender(gender)
        return builder.get_payload()
    return _make

@pytest.fixture(autouse=True)#this executes for every test we dont need to send this parameter inside every test though
#not a parameter usage though but below logging is also autouse in config.py
#logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
def log_test_boundaries(request):#request is also another pytest fixture, which has information about current running test. request - current running test, items - all collected tests
    """Marks start/end of every test in the logs — helps trace failures in CI output."""
    logging.info(f"===== STARTING: {request.node.name} =====")#prints names for each test in log useful for tracing. request.node is the test item object, and .name is the test’s name,
    yield
    logging.info(f"===== FINISHED: {request.node.name} =====")

@pytest.fixture(scope="function")
def create_user(api_client,test_data):
    payload=test_data(gender="female")
    request_builder = RequestBuilder().build()#pull payload out separately since client.post() takes it as its own positional-ish kwarg, not part of **request
    post_response = api_client.post("public/v2/users", request_body=payload, **request_builder)
    user_id=None
    if post_response.status_code==201:
        post_response_json = post_response.json()
        user_id = post_response_json.get("id")
    try:
        ResponseValidator.validate_response_time(post_response)
        ResponseValidator.validate_status_code(post_response, 201)
        ResponseValidator.validate_request_header(post_response, "content-type", "application/json")
        # user=User(**post_response.json())
        # print(json.dumps(post_response_json,indent=4))
        #The validations run before the yield, so if one fails, pytest reports an ERROR in setup rather than a FAILED test, and the test body never runs.
        yield post_response_json

    finally:#having the teardown in finally so as to run this even if it fails in above response code after creating post as it may not go to other gorest tests
        if user_id:
            delete_response=api_client.delete(f"public/v2/users/{user_id}")
            assert delete_response.status_code in (204,404),(f"failed in teardown step , got {delete_response.status_code}")
            #it can be 404 if the actual delete test already delete, then we get 404
            print(f"DELETED response code is {delete_response.status_code}")

def pytest_addoption(parser):#called by pytest during the cycle of event, name is defined so write as it is. the hooks has to be in conftest.py not in tests
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="also run tests marked as slow",
    )
#How the action and default works above
#1.pytest -s (nothing passed, so every default is used): run_slow = False , env = dev, max_time = 2.0 <class 'float'>
#2.pytest -s --run-slow : run_slow = True , env = dev, max_time = 2.0 <class 'float'>
#3.pytest -s --env staging (store grabs the next word): run_slow = False , env = staging, max_time = 2.0 <class 'float'>
#4.pytest -s --run-slow --env prod --max-time 0.5: run_slow = True , env = prod, max_time = 2.0 <class 'float'>

#This is a hook, not a fixture. Pytest finds it by its exact name, so there’s no decorator(@ above the method / hook name).
#It registers a custom command-line flag: pytest --run-slow.
#action="store_true" makes it a boolean flag. If the flag is present the value is True; otherwise it’s default=False. No value follows the flag.
#help is the text shown in pytest --help.
#pytest_addoption only works in the root conftest.py, or one pytest loads at startup. In a nested tests/subfolder/conftest.py it’s ignored.
#Hook - A hook is a function pytest itself calls at fixed points in its lifecycle: startup, parsing CLI args, collecting tests, before and after each test, and end of session. You never request a hook. You define a function with an exact hook name and pytest finds it and calls it.
#Hooks written inside a regular test file (test_*.py) are ignored, because test modules aren’t registered as plugins.

#pytest_collection_modifyitems is hook. It runs after pytest collects all tests but before running any.
#config is the pytest config object, which gives you access to CLI options.
#items is the list of every collected test. You can modify markers on it, reorder it, or deselect from it.
def pytest_collection_modifyitems(config, items):
    for item in items:
        if item.path.name == "test_auth_manager.py":
            item.add_marker(pytest.mark.security)


    if config.getoption("--run-slow"):
        return  # flag given: leave everything as collected

    skip_slow = pytest.mark.skip(reason="slow test: pass --run-slow to run it")
    #this above reason is shown in output console because of pytest.ini slow marker(when we run pytest --markers)
    for item in items:
        if item.get_closest_marker("slow"):
            item.add_marker(skip_slow)
"""
Piece	            Type	                    Scope	        Runs when
logging.basicConfig	module-level code	        once	        conftest import
auth_token	        fixture	                    session	        first test that needs it
api_client	        fixture (yield)	            session	        setup once, teardown at end
make_client	        factory fixture	            function	    per test that requests it
test_data	        factory fixture	            function	    per test that requests it
log_test_boundaries	autouse fixture	            function	    around every test
create_user	        fixture (yield + finally)   function	    per test, with cleanup
pytest_addoption	hook	                    n/a	            pytest startup
pytest_collection_modifyitems	hook	        n/a	            after collection, before running
"""

#config vs os.environ
#config gets the value after pytest from CLI ie pytest --run-slow , gets using config.getoption('run--slow')
#env variable env=QA
#os.environ holds process variables, flags typed after pytest go into sys.argv and pytest parses those into config.

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

#Design A: fixture scope manages freshness (coupled)
#Suppose you don’t have expiry logic in AuthManager. The only way to get a fresh token is to build a new client, so you’d be forced to make the fixture function-scoped:
#@pytest.fixture(scope="function")   # ← chosen ONLY to keep the token fresh
#def client():
#    auth = AuthManager()
#    return APIClient(BASE_URL, auth.get_headers())
#problems-
#1.50 tokens and 50 sessions for no reason. With a real OAuth API that’s 50 calls to the token endpoint, and you lose connection pooling.
#2.It still breaks if a single test runs longer than 120s, because the token expires mid-test.
#3.You can’t switch to scope="session" for speed. If you did, the token would be created at t=0 and every request after t=120s would get a 401.
#Scope is now doing two jobs, so you can’t tune it for performance without breaking auth. That’s the coupling.
#Design B: AuthManager manages freshness (decoupled) - above design which we used
#AuthManager owns the expiry check, and the client asks it for headers on every request (the refactor from earlier):
#That’s one client, one session and 3 tokens, refreshed exactly when needed.

#explain in interview
#A short version with problem, finding, fix and result:
#In my API framework I first passed auth headers into the client as a plain dict. While reviewing it I realized the AuthManager’s expiry check could never run: the client held a one-time copy, and the manager was discarded. So I refactored the client to receive the AuthManager itself and call get_headers() on every request. Now the token refreshes automatically when it expires, and I can keep a single session-scoped client for speed without worrying about stale tokens.”
#A.Incorrect Approach
#class APIClient:
#    def __init__(self, base_url, headers):
#        self.headers = headers                       # frozen dict
#    def get(self, endpoint):
#        return requests.get(self.base_url + endpoint, headers=self.headers)
#client = APIClient(BASE_URL, AuthManager().get_headers())
#B.right approach
#class APIClient:
#    def __init__(self, base_url, auth_manager):
#        self.auth_manager = auth_manager             # live reference
#    def get(self, endpoint):
#        headers = self.auth_manager.get_headers()    # asked every request
#        return requests.get(self.base_url + endpoint, headers=headers)
#client = APIClient(BASE_URL, AuthManager())