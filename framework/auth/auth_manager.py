import time
from framework.config.config import TOKEN_TTL_SECONDS, TOKEN

class AuthManager:
    def __init__(self,token=None,token_ttl_seconds=None):
        self._token=token or TOKEN
        self._token_issued_at=time.time()#should be per instance else if its global - it would be created long ago than before creating instance of the class
        self._token_ttl_seconds = token_ttl_seconds if token_ttl_seconds is not None else TOKEN_TTL_SECONDS#construct can still get from object or from config file

        if not self._token:
            raise ValueError("No auth token provided. Set GOREST_TOKEN env variable or pass token explicitly.")


    def get_headers(self):
        return {"Authorization":f"Bearer {self.get_valid_token()}"}
        #PI client calls it before each request and gets a ready-to-use dict, so it never has to know about Bearer formatting or expiry.

    def _is_token_expired(self):
        return time.time() - self._token_issued_at > self._token_ttl_seconds# expired if elapsed time > TTL
        #current time - token issued time <= token expired time


    def _refresh_token(self):
        # Real OAuth2 client would POST to /oauth/token with grant_type=refresh_token
        # and swap self._token for the new access token here.
        # gorest has no refresh endpoint, so we just reset the clock.
        self._token_issued_at = time.time()#we need to know when the token is issued, hence current time
        return self._token#for now just returning token from __init__ which takes from .env file

    def get_valid_token(self):
        if self._is_token_expired():
            return self._refresh_token()
        return self._token#from __init__
        #when you need the raw token 1)A different header scheme (X-Api-Key, or a query param) 2)Passing the token to something that isn’t requests, like a websocket or a CLI call

    #some variables and methods have ._ but some doesnt, means for internal usage vs public access outside of the class


