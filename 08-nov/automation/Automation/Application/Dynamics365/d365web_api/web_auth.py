import json
import os
import threading
import urllib.parse
import uuid
import webbrowser

import requests

import msal
from adal import AuthenticationContext
from flask import Flask, redirect, session, request

from .constants import API_VERSION, AUTH_AUTHORITY_ENDPOINT, AUTH_AUTHORITY_USERID_PASSWD, REDIRECT_URI, SCOPE, RESOURCE
from .constants import CREDENTIAL_TYPE
import AutomationUtils.config as config
from queue import Queue

config = config.get_config()


class Credentials:
    """
        Class denoting a set of credentials to access Dynamics 365 environment
    """

    def __init__(self, refresh_token: str = None, client_id: str = None,
                 client_secret: str = None, tenant_id: str = None, auth_code: str = None):
        self._refresh_token = refresh_token
        self._client_id = client_id
        self._client_secret = client_secret
        self._tenet_id = tenant_id
        self._auth_code = auth_code
        self._credential_type = None

        if self._client_id and self._client_secret and self._tenet_id:
            self._credential_type = CREDENTIAL_TYPE.CLIENT_ID_SECRET

    @property
    def credential_type(self):
        return self._credential_type

    @property
    def client_id(self) -> str:
        return self._client_id

    @property
    def client_secret(self) -> str:
        return self._client_secret

    @property
    def tenant_id(self) -> str:
        return self._tenet_id

    @property
    def refresh_token(self) -> str:
        return self._refresh_token

    @refresh_token.setter
    def refresh_token(self, value: str):
        self._refresh_token = value

    @property
    def auth_code(self) -> str:
        return self._auth_code

    @auth_code.setter
    def auth_code(self, value: str):
        self._auth_code = value


class AuthCodeManager:
    @staticmethod
    def get_authorization_code(credentials):
        """
        Function to get the Auth code, using the credentials provided
        :param credentials: Credentials object, using which Auth code is to be generated
        :return: The Auth code
        """
        auth_code_event = threading.Event()
        auth_code_container = []
        stop_server = threading.Event()

        app = Flask("AuthCodeAcquisition")
        app.config['SECRET_KEY'] = os.urandom(24)
        app.secret_key = os.urandom(24)

        @app.route('/')
        def create_auth_url():
            state = str(uuid.uuid4())
            session['state'] = state
            auth_url = (
                f"https://login.microsoftonline.com/common/oauth2/authorize?"
                f"response_type=code"
                f"&response_mode=form_post"
                f"&client_id={urllib.parse.quote(credentials.client_id)}"
                f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
                f"&prompt=select_account"
                f"&resource={urllib.parse.quote(RESOURCE)}"
                f"&scope={urllib.parse.quote(SCOPE)}"
            )
            return redirect(auth_url)

        @app.route('/getAToken', methods=['POST'])
        def get_authorization_code():
            auth_code = request.form.get('code')
            if not auth_code:
                return 'Authorization failed or invalid state.'
            auth_code_container.append(auth_code)
            auth_code_event.set()
            stop_server.set()  # Signal to stop the server
            return 'Auth Code received successfully. You can close this window now.'

        def run_app():
            from werkzeug.serving import make_server
            server = make_server('localhost', 5000, app)
            server.timeout = 1  # Set a short timeout

            while not stop_server.is_set():
                server.handle_request()

        flask_thread = threading.Thread(target=run_app)
        flask_thread.start()

        # Open the default web browser
        webbrowser.open('http://localhost:5000')

        auth_code_event.wait()  # Wait for the authorization code to be set

        if auth_code_container:
            auth_code = auth_code_container[0]
        else:
            auth_code = None

        flask_thread.join()

        return auth_code


class MSALAuthentication:
    """
        This class would be used for Auth token related operations.
    """

    def __init__(self):
        self._auth_authority = str()
        self._msal_auth_object = None

    def get_auth_code(self, credentials: Credentials):
        """
        Function to get the Auth code, using the credentials provided
        :param credentials: Credentials object, using which Auth code is to be generated
        :return: The Auth code
        """
        self._msal_auth_object = msal.ConfidentialClientApplication(
            client_id=credentials.client_id,
            authority=f'https://login.microsoftonline.com/{credentials.tenant_id}',
            client_credential=credentials.client_secret
        )
        return AuthCodeManager.get_authorization_code(credentials=credentials)

    def get_auth_token(self, resource: str, credentials: Credentials):
        """
                This function fetches a auth token, for the specified resource, using the given credentials
                :param resource: The resource, for which Auth token is required
                :param credentials: The credential object, using which Auth Token is to be generated
                :return: The Auth token, for the specific resource
            """
        response = None
        if self._msal_auth_object is None:
            self._msal_auth_object = msal.ConfidentialClientApplication(
                client_id=credentials.client_id,
                authority=f'https://login.microsoftonline.com/{credentials.tenant_id}',
                client_credential=credentials.client_secret
            )
        if credentials.refresh_token:
            response = self._msal_auth_object.acquire_token_by_refresh_token(refresh_token=credentials.refresh_token,
                                                                             scopes=[resource])
        elif credentials.auth_code:
            response = self._msal_auth_object.acquire_token_by_authorization_code(code=credentials.auth_code,
                                                                                  scopes=[resource],
                                                                                  redirect_uri=REDIRECT_URI)
        if not os.path.exists("token.json"):
            with open("token.json", "w") as json_file:
                json.dump(response, json_file)
        return response['access_token']
