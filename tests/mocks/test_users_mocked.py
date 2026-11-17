"""
Real ApiClient + real User model run; only the HTTP wire is faked.
"""
import pytest
import requests
import responses
from pydantic import ValidationError
from responses import matchers

from framework.mocks import gorest_stubs as stubs
from framework.models.user import User

pytestmark = pytest.mark.mock
#this is for file marker

#--happy path tests----------------------

def test_get_user_by_id(mock_gorest, mocked_client):
    #below is registering the stub, .add adds one rule to registry if GET arrives with https://gorest.co.in/.... reply 200 with JSON. nothing is sent yet. this only arms the stub
    mock_gorest.add(responses.GET, f"{stubs.USERS_URL}/1001", json=stubs.user(1001), status=200)
    #below is calling apu through real client
    #get() _request("GET","users/1001",...) after path params, auth, url, self.session. session merges its headers(bearer fake token), adapter.send() PATCHED by responses
    #responses intercepts
    #inside the patched send() looks for matching method plus url, builds real requests.response object with status 200 and json body
    #records the call in mock_gorest.calls including request url and headers. this is what makes mock style assertions possible later.
    #returns the response to session.request() which returns it to _request(), logger prints "expected response status code 200" and returns resp
    resp = mocked_client.get("/users/1001")

    assert resp.status_code == 200
    u = User(**resp.json())          # Pydantic model validates the stub
    assert u.id == 1001
    #assertions are verified
    #tear down
    #fixture teardown first is mocked_client,closes the session
    #mock_gorest resumes after yield
    #with block now exits by doing 2 things ie assert_all_requests_are_fired check as true. GET is called. if it hadnt been, we'd see error at tear down
    #unpatches requests, restoring real networking so the next test/live gorest test isnt affected.



def test_create_user_no_sleep_needed(mock_gorest, mocked_client):
    payload = {"name": "Nikky", "email": "nikky@example.com", "gender": "female", "status": "active"}
    mock_gorest.add(
        responses.POST, stubs.USERS_URL,
        json=stubs.user(5555, **payload), status=201,
        #without below matchers a stub only checks method and URL
        # matchers = stub only answers if the request is EXACTLY right ie both the request body and header
        match=[
            matchers.json_params_matcher(payload),
            matchers.header_matcher({"Authorization": f"Bearer {stubs.FAKE_TOKEN}"}),
        ],
    )

    resp = mocked_client.post("/users", payload)
    #this request payload gets compared with above matchers payload as dict, key order doesnt matter
    #this also gets compared with stub token, other additional headers are allowed by default but this is required
    #if we dont send body, we would see error(Connection error) like request.body doesnt match - whicch stub came closest and why it rejected the request
    #with match above its a mock(answers and verifies how its called)
    #above match is same as doing below checks
    #sent = mock_gorest.calls[0].request
    #assert json.loads(sent.body) == payload
    #assert sent.headers["Authorization"] == f"Bearer {stubs.FAKE_TOKEN}"
    #Matchers vs. asserting on .calls afterward:
    #Matchers: verification happens before the response. A wrong request fails immediately, but the error lives inside a ConnectionError message.
    #.calls asserts: verification happens after. You get a clearer assert x == y diff, and you can check things matchers can’t easily express (like “the header is absent”).

    assert resp.status_code == 201
    assert User(**resp.json()).email == "nikky@example.com"


#--------Header related tests below----------------

def test_pagination_headers(mock_gorest, mocked_client):
    mock_gorest.add(
        responses.GET, stubs.USERS_URL,
        json=stubs.user_list(3), status=200,
        headers=stubs.pagination_headers(total=3, pages=1),
        match=[matchers.query_param_matcher({"page": "1"})],
    )

    resp = mocked_client.get("/users", params={"page": 1})

    assert int(resp.headers["x-pagination-total"]) == len(resp.json()) == 3


def test_empty_user_list(mock_gorest, mocked_client):
    mock_gorest.add(responses.GET, stubs.USERS_URL, json=[], status=200)
    assert mocked_client.get("/users").json() == []


# ----------error paths tests ----------

@pytest.mark.parametrize("status, body", [
    (401, stubs.AUTH_FAILED),
    (404, stubs.NOT_FOUND),
    (429, {"message": "Too many requests"}),
    (500, {"message": "Internal server error"}),
    (503, None),
])
def test_error_statuses(mock_gorest, mocked_client, status, body):
    mock_gorest.add(responses.GET, f"{stubs.USERS_URL}/1", json=body, status=status)

    resp = mocked_client.get("/users/1")

    assert resp.status_code == status


def test_422_email_taken_shape(mock_gorest, mocked_client):
    mock_gorest.add(responses.POST, stubs.USERS_URL, json=stubs.EMAIL_TAKEN, status=422)

    resp = mocked_client.post("/users", {"email": "dup@example.com"})

    errors = resp.json()
    assert resp.status_code == 422
    assert isinstance(errors, list)           # gorest 422 = list of {field, message}
    assert {"field": "email", "message": "has already been taken"} in errors


# ----------contract drift — model catches a bad response ----------

def test_model_rejects_missing_field(mock_gorest, mocked_client):
    broken = stubs.user(1001)
    del broken["email"]                       # gorest "drops" a field
    mock_gorest.add(responses.GET, f"{stubs.USERS_URL}/1001", json=broken, status=200)

    with pytest.raises(ValidationError):
        User(**mocked_client.get("/users/1001").json())


def test_model_rejects_wrong_type(mock_gorest, mocked_client):
    mock_gorest.add(responses.GET, f"{stubs.USERS_URL}/1001",
                    json=stubs.user(1001, id="not-an-int"), status=200)

    with pytest.raises(ValidationError):
        User(**mocked_client.get("/users/1001").json())


# ----------Verify what client has sent basically mocking----------

def test_client_sends_auth_and_accept_headers(mock_gorest, mocked_client):
    mock_gorest.add(responses.GET, stubs.USERS_URL, json=[], status=200)

    mocked_client.get("/users")

    sent = mock_gorest.calls[0].request.headers
    assert sent["Authorization"] == f"Bearer {stubs.FAKE_TOKEN}"

def test_per_call_auth_overrides_session_token(mock_gorest, mocked_client):
    mock_gorest.add(responses.GET, stubs.USERS_URL, json=[], status=200)
    mock_gorest.add(responses.GET, stubs.USERS_URL, json=[], status=200)

    mocked_client.get("/users", auth="other-token")   # override toking from here
    mocked_client.get("/users")                       # gets the token from mocked_client which has fake token

    assert mock_gorest.calls[0].request.headers["Authorization"] == "Bearer other-token"
    assert mock_gorest.calls[1].request.headers["Authorization"] == f"Bearer {stubs.FAKE_TOKEN}"

def test_path_params_build_correct_url(mock_gorest, mocked_client):
    mock_gorest.add(responses.GET, f"{stubs.BASE_URL}/users/5/posts", json=[], status=200)
    mocked_client.get("/users/{id}/posts", path_params={"id": 5})
    assert mock_gorest.calls[0].request.url == f"{stubs.BASE_URL}/users/5/posts"

#how the sequence is
"""
1.COLLECTION   pytest finds the test, sees it needs: mock_gorest, mocked_client
2.SETUP        ① mock_gorest   → patch requests, start recording, yield rsps     ⏸ paused
             ② mocked_client → build APIClient with fake token, yield client   ⏸ paused
3.TEST BODY    ③ register stub → ④ call API → ⑤ intercept → ⑥ assert
4.TEARDOWN     ⑦ mocked_client resumes → session.close()          (last in, first out)
             ⑧ mock_gorest resumes   → check all stubs fired → un-patch requests
"""
#stubs - Http level : responses, record/play - most common daya to day - used in API framework tests, error and edge cases, CI Smoke
#mocks - asserting on calls , medium used , unit testing framework itself like auth manager
#service virtualisation - wiremock etc, often owned by platform/QA team , used for unfinished downstream services, mobile UI tests etc