import requests
import logging

class APIClient:

    def __init__(self,base_url,headers=None,timeout=10,auth_manager=None,session=None):
        self.base_url=base_url
        self.timeout=timeout
        self.session=session or requests.Session()#for same Session across requests to avoid multiple TCP handshakes
        self.session.headers.update(headers or {})

        self.logger=logging.getLogger(__name__)

        if auth_manager:
            token=auth_manager.get_valid_token()
            self.session.headers.update({"Authorization":f"Bearer {token}"})

    def _request(self,method,path,params=None,json=None,timeout=None,headers=None,cookies=None,auth=None,path_params=None):
        if path_params:
            #path = "public/v2/users/{id}/posts/{post_id}"
            #path_params = {"id": 5, "post_id": 99}
            path = path.format(**path_params)#substitute {id} etc. in the path template before building the URL

        request_headers = dict(headers or {})#using dict() creates another copy as we dont want to mutate/change the existing headers. instead we want to create copy of that and add auth to it before sending request
        if auth:
            request_headers["Authorization"] = f"Bearer {auth}"#per-call override; requests merges this on top of session.headers, so it wins for this one call only

        self.logger.info(f"request being called for {method} with URL:{self.base_url + path}")
        response=self.session.request(
            method,
            self.base_url+path,
            params=params,
            json=json,
            timeout=timeout or self.timeout,
            headers=request_headers or None,
            cookies=cookies
        )
        modified_response_code=f'{str(response.status_code)[0]}XX'
        valid_status_codes = ['2XX','3XX']
        if modified_response_code in valid_status_codes:
            self.logger.info(f'expected response status code {response.status_code}')
        else:
            self.logger.warning(f'invalid response code we get, ideally they should be from the list : {valid_status_codes}')
        return response

    def get(self,path,params=None,timeout=None,headers=None,cookies=None,auth=None,path_params=None):
        return self._request("GET",path,params=params,timeout=timeout,headers=headers,cookies=cookies,auth=auth,path_params=path_params)

    def post(self,path,request_body,params=None,timeout=None,headers=None,cookies=None,auth=None,path_params=None):
        return self._request("POST",path,json=request_body,params=params,timeout=timeout,headers=headers,cookies=cookies,auth=auth,path_params=path_params)

    def put(self,path,request_body,params=None,timeout=None,headers=None,cookies=None,auth=None,path_params=None):
        return self._request("PUT",path,json=request_body,params=params,timeout=timeout,headers=headers,cookies=cookies,auth=auth,path_params=path_params)

    def patch(self,path,request_body,params=None,timeout=None,headers=None,cookies=None,auth=None,path_params=None):
        return self._request("PATCH",path,params=params,json=request_body,timeout=timeout,headers=headers,cookies=cookies,auth=auth,path_params=path_params)

    def delete(self,path,params=None,timeout=None,headers=None,cookies=None,auth=None,path_params=None):
        return self._request("DELETE",path,params=params,timeout=timeout,headers=headers,cookies=cookies,auth=auth,path_params=path_params)