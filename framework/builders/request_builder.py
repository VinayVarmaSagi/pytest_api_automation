from framework.utils.string_utils import generate_random_string, generate_random_email

class RequestBuilder:#to build request in one place - can be changed here itself if we want to not in every other place
    def __init__(self):
        #._ as protected to make sure user doesnt update the name from tests, hence we use protected instead of public, private is overkill - not required here
        #protected can be used inside class or subclass , but python cant enforce
        self._payload={}#instead of creating everything in this payload. we are creating based on whatever user calls, hence empty json
        self.headers={}
        self.param= {}
        self.path_param={}
        self.body=None
        self.cookies= {}
        self.auth=None
        self.timeout=30

    def with_name(self,name=None):#if we put this default name=None and user doesnt send it, it will update above payload as None and it will fail
        self._payload["name"]=name or generate_random_string(8)#if name is none in request, it creates using this method
        return self

    def with_email(self,email=None):
        self._payload["email"]=email or generate_random_email()
        return self#enables chaining else it would return None and we cant use chaining, send the same object while building request to its next step ie with_email().with_name() - so same object is used while building requests

    def with_gender(self,gender):
        self._payload["gender"]=gender
        return self

    def with_status(self,status):
        self._payload["status"]=status
        return self

    def with_header(self,key,value):#singular - sets ONE key/value pair, matches with_param/with_cookie below
        self.headers[key]=value
        return self

    def with_param(self,key,value):
        self.param[key]=value
        return self

    def with_path_param(self,key,value):
        self.path_param[key]=value
        return self

    def with_body(self,data):#for raw json payloads, use instead of the with_name/with_email/etc field setters
        self.body=data
        return self

    def with_cookie(self,key,value):
        self.cookies[key]=value
        return self

    def with_auth(self,token):
        self.auth=token
        return self

    def with_timeout(self,seconds):
        self.timeout=seconds if seconds and seconds>0 else self.timeout
        return self

    def get_payload(self):
        return self.body if self.body is not None else self._payload

    def build(self):
        #assembles everything set via with_* calls into one dict for api_client to consume
        return {
            "headers": self.headers,
            "params": self.param,
            "path_params": self.path_param,
            "cookies": self.cookies,
            "auth": self.auth,
            "timeout": self.timeout,
        }