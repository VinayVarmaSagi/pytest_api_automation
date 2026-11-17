import pytest
import responses


from framework.mocks.gorest_stubs import BASE_URL, FAKE_TOKEN
from framework.auth.auth_manager import AuthManager
from framework.client.api_client import APIClient

@pytest.fixture
def mocked_client():
    # Real APIClient + real AuthManager, but with an INJECTED fake token.
    # No .env , hence runs anywhere like CI etc..
    client = APIClient(BASE_URL, auth_manager=AuthManager(token=FAKE_TOKEN))
    yield client
    client.session.close()
    #build APIClient with fake token, yield client   then paused
    #no network activity here, just creating a session, doesnt connect to anything.
    #role: the real code under test, given stub input(the fake token)



@pytest.fixture
def mock_gorest():
    """Inside this block NO real HTTP gorest call is allowed: unregistered URLs raise ConnectionError. if any unregistered url(usually registers from test case) gets called then it would throw ConnectionError
    assert_all_requests_are_fired=True -> fails if you registered a stub the code never called, we registered from test but didnt call that in test"""
    with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
        yield rsps
    #patch requests, start recording, yield rsps     then paused
    #patches requests at its lowest level then adapters send. from now no HTTP call can leave the process
    #creates empty stub registry(no URLs registered yet) and an empty call log ie rsps.calls
    #yield pauses the fixture and hands rsps to test as mock_gorest. with is still open, so patch stays active.
    #role so far : an empty stub engine plus a call recorder
    #rsps logs the call which can be used to assert the calls like fake token sent - its then called mocking
    #after yield this with is still open to close the sessions/unpatch for next requests which has to create new requests either to live or this stubbed point and register again. because these fixtures are function
    #this is like registering an empty stub

#this conftest.py is close to mocks tests folder, so the closer conftest.py wins ie this one and it doesnt leak into other positive tests