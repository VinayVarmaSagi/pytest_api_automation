#This is stub (Canned) gorest responses
BASE_URL = "https://gorest.co.in/public/v2"
USERS_URL = f"{BASE_URL}/users"
FAKE_TOKEN = "fake-test-token"


def user(user_id: int = 1001, **overrides) -> dict:
    data = {
        "id": user_id,
        "name": "Mock User",
        "email": f"mock.user{user_id}@example.com",
        "gender": "female",
        "status": "active",
    }
    data.update(overrides)
    return data
    #function instead of plain dict to get separate copy for each tests, else other tests may fail if this corrupted request is sent to other tests


def user_list(count: int = 3) -> list:
    return [user(1000 + i) for i in range(count)]
    #to generate no of users(here 3) in gorest, uses above user response structure


def pagination_headers(total: int, pages: int, page: int = 1, limit: int = 10) -> dict:
    return {
        "x-pagination-total": str(total),
        "x-pagination-pages": str(pages),
        "x-pagination-page": str(page),
        "x-pagination-limit": str(limit),
    }
    #simulating header data of gorest response. str(total) etc because the actual response is in string, hence we are simulating the same format


# --- gorest error bodies (real shapes) ---
AUTH_FAILED = {"message": "Authentication failed"}               # 401
NOT_FOUND = {"message": "Resource not found"}                    # 404
EMAIL_TAKEN = [{"field": "email", "message": "has already been taken"}]  # 422 is a LIST

#stub payloads in one module, copied from real API shapes and built through factories so each test gets a fresh, valid object it can tweak. The data is only a stub once it’s registered with the HTTP mock, and only acts as a mock when I assert on the calls.

#stub vs mock vs service virtualisation
#“A stub controls what comes back, a mock also verifies how it was called, and service virtualization is a shared fake server the whole team and CI can hit. I mock what I don’t control or can’t make fail on demand, and I back the mocks with contract and live tests so they don’t drift from reality.”
#in Python, the same tool often plays both roles. responses is a stub when you only register a reply, and it becomes a mock once you assert on .calls.
