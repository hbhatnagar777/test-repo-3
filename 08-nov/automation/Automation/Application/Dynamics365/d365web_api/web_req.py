import json
import os
import time
from functools import wraps
import requests
from .web_auth import MSALAuthentication, AuthCodeManager
from .web_auth import Credentials
from AutomationUtils import logger
from requests.exceptions import ConnectionError, ChunkedEncodingError
import AutomationUtils.config as config


class D365APICallDecorator:
    """Class for handling timeout of Dynamics 365 API connection"""

    def __init__(self):
        """
        Constructor function for the class

        Args:

        """

        self.log = logger.get_log()
        self._max_retries = 3

    def __call__(self):
        """
        Wrapper method that checks if Dynamics 365 Web API connection has timed out
        and reattempts the operation

        Returns:
            function: The wrapped function
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                for i in range(self._max_retries):
                    try:
                        return_val = func(*args, **kwargs)
                        break
                    except (ConnectionError, ChunkedEncodingError) as exp:
                        self.__exp = exp
                        self.log.error(f"{exp}")
                        time.sleep(45)
                        self.log.info(f"Tried {i + 1} times out of {self._max_retries}. Retrying....")

                else:
                    raise Exception(
                        f"Dynamics 365Web API Call timeout error. Tried {self._max_retries} times and failed.") \
                        from self.__exp
                return return_val

            return wrapper

        return decorator


class Token:
    """
        Class denoting an access token for a Dynamics 365 resource
    """

    def __init__(self):
        self._adal_auth = MSALAuthentication()
        self._token = dict()
        self._token_gen_time = dict()
        self.config = config.get_config()

    def _check_if_token_exists(self, resource: str):
        """
            Method to check is the token exists in the Dictionary or not.
            :param resource: Resource to check for
            :return: True/ False depending on whether the token exists in the dictionary or not
        """
        if resource.lower() in self._token.keys():
            return True
        return False

    def _check_is_token_valid(self, resource: str):
        """
            Method to check is we have a vlid token present or not
            :param resource: Resource for which we have to check the presence of a valid token
            :return: True or False depending on the token validity status
        """
        try:
            if not self._check_if_token_exists(resource=resource):
                return False

            else:
                gen_time = self._token_gen_time[resource.lower()]
                if time.time() - gen_time > 3599:
                    return False
                return True
        except KeyError:
            return False

    def _generate_token_from_refresh_token(self, credentials, token_file: str, resource: str):
        """
            Method to generate token from refresh token
            :param token_file: File containing the refresh token
            :param resource: Resource for which the token is to be generated
            :return: Access token for the resource
        """
        with open(token_file, "r") as json_file:
            token_config = json.load(json_file)
        if "refresh_token" not in token_config:
            raise Exception("Refresh token not found in the token file")
        refresh_token = token_config["refresh_token"]
        credentials.refresh_token = refresh_token
        return self._generate_token(credentials=credentials, resource=resource)

    def get_token(self, credentials, resource: str):
        """
            Method to get token for a Dynamics 365 resource, using the supplied credentials.
            credentials:        Credential:     credential object to be used for the request.
            resource:           str:            Resource to be used for the request.
        """
        if self._check_is_token_valid(resource=resource):
            return self._token[resource.lower()]
        elif os.path.exists("token.json"):
            return self._generate_token_from_refresh_token(credentials, "token.json", resource)
        else:
            return self._generate_token(credentials=credentials, resource=resource)

    def _generate_token(self, credentials, resource):
        """
            Method to generate a token for the given resource using the supplied credentials
            :param credentials: Credentials to be used for the request
            :param resource: Resource to be used for the request
            :return: Access token for the resource
        """
        if credentials.auth_code is None and credentials.refresh_token is None:
            auth_code = self._adal_auth.get_auth_code(credentials=credentials)
            credentials.auth_code = auth_code
        gen_token = self._adal_auth.get_auth_token(resource=resource, credentials=credentials)
        self._token[resource.lower()] = gen_token
        self._token_gen_time[resource.lower()] = time.time()
        return gen_token


class PyWebAPIRequests:
    """
        Method to make requests to the Dynamics 365 WEB API's.

            # Only make requests here, fetch the token  from the token helper and send request
            # token helper: would take care fo acquiring token, storing token temporarily
            # refreshing token
    """
    web_api_call = D365APICallDecorator()

    def __init__(self):
        self._token = None
        self._headers = {
            'OData-MaxVersion': '4.0',
            'OData-Version': '4.0',
            'Accept': 'application/json',
            # 'Authorization': 'Bearer ' + self._token,
            'Content-Type': 'application/json; charset=utf-8',
            'Prefer': 'return=representation',
        }
        self._auth_value = "Bearer %s"
        self._token_helper = Token()

    @staticmethod
    def _process_web_response(response):
        if not response.ok:
            response.raise_for_status()
        else:
            try:
                return response.json()
            except Exception:
                return response

    @web_api_call()
    def _make_request(self, method, endpoint, access_token, body: dict = dict()):
        authorization_header = self._auth_value % access_token
        headers = self._headers
        headers["Authorization"] = authorization_header
        if method in ['GET', 'DELETE']:
            request = requests.request(method=method, url=endpoint, headers=headers)
        elif method in ['POST', 'PUT', 'PATCH']:
            request = requests.request(method=method, url=endpoint, headers=headers, json=body)
        return self._process_web_response(response=request)

    def make_webapi_request(self, method: str, access_endpoint: str, credentials: Credentials, resource: str = "",
                            body: dict = dict()):
        """
            Make a request to the endpoint passed, using the given credentials, using the passed method.
            access_endpoint:    Endpoint to generate access token from.

            credentials:        Credentials to access the resource.
            resource:           Resource to be accessed.
            body:               Body to be used for the request.

            Example:
                access_endpoint:    https://env-name.crm.dynamics.com/api/data/v9.0/EntityDefinitions
                resource:           https://env-name.crm.dynamics.com/.default
        """

        _access_token = self._token_helper.get_token(resource=resource, credentials=credentials)
        response = self._make_request(method=method, endpoint=access_endpoint, access_token=_access_token, body=body)
        return response
