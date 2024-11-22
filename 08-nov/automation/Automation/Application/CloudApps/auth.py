# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main Module for authenticating cloud apps.

GAuth and OneDriveAuth are the classes defined in this module to authenticate
google APIs and/or Microsoft Graph.

GAuth: Class for getting credential object and build google service for different google APIs.

OneDriveAuth: Class for authenticating OneDrive for business app.

GAuth:
    __init__(log_object)  --  Initializes the GSuite Authentication object
    with given P12 or JSON key file.

    __repr__()  --  Representation string for the instance of the GAuth class

    _get_credentials()  --  Creates credential object from JSON or P12 service account Key file

    build_service(APIName, delegated_user)  --  Builds Google service object for invoking
    Google APIs

    __del__()   --  Deletes the credentials from Storage

OneDriveAuth:
    __init__(log_object)    --  Initializes the MS Graph authentication object
    with given account details.

    __repr__()  --  Representation string for the instance of OneDriveAuth class

    authenticate_client()   --  Authenticates the OneDrive for business app to access MS Graph APIs.

Attributes
==========

        **service_account_email**   --  Treats service_account_email as read only attribute

"""

from __future__ import unicode_literals
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.file import Storage
from apiclient import discovery
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from . import constants
from .exception import CVCloudException


class GAuth:
    """Class for authenticating Google API via service account P12 or JSON private key file."""

    def __init__(self, logger):
        """Initializes the GSuite Authentication object with given P12 or JSON key file.

                Args:

                    logger (object)  --   instance of logger module

                Returns:

                    object  -   instance of GAuth class
        """

        self.log = logger
        self.__service_account_email = None
        self.api_name = self.__class__.__name__

    def __repr__(self):
        """Representation string for the instance of the GAuth class."""

        return 'GAuth class instance for Google service account: %s', self.__service_account_email

    def _get_credentials(self):
        """Creates credential object from JSON or P12 service account Key file
        and store it temporarily using OAuth2.file.Storage object.
        If credential storage already exists, it returns the credentials from
        the storage.If credentials are expired,
        it renews and returns the credential object

                Args:

                    None

                Returns:

                    OAuth2 credential object -- (instance of ServiceAccountCredential class
                    of Google's oauth2Client package)

        """
        try:
            storage = Storage(constants.CRED_STORAGE_FILE)
            credentials = storage.get()
            if not credentials:
                self.log.info('credentials are none.')
                if constants.KEY_FILE_PATH.split('.')[1].lower() == 'p12':
                    credentials = ServiceAccountCredentials.from_p12_keyfile(
                        constants.CLIENT_EMAIL, constants.KEY_FILE_PATH, scopes=constants.SCOPES)
                    self.log.info(
                        'Got Google credential object from P12 Key file. '
                        'Storing credential in storage..')

                elif constants.KEY_FILE_PATH.split('.')[1].lower() == 'json':
                    credentials = ServiceAccountCredentials.from_json_keyfile_name(
                        constants.KEY_FILE_PATH, scopes=constants.SCOPES)
                    self.log.info(
                        'Got Google credential object from JSON Key file. '
                        'Storing credential in storage..')

                else:
                    self.log.error('Invalid Key file name.')
                    raise CVCloudException(self.api_name, '101')
                storage.put(credentials)
                self.log.info('Credentials are stored in %s', constants.CRED_STORAGE_FILE)

            elif credentials.access_token_expired:

                self.log.info(
                    'Google credentials from storage are in expired state.'
                    'Trying to refresh the credentials..')
                credential_info = credentials.get_access_token()
                credentials.set_store(storage)
                self.log.info(
                    'Credentials are refreshed with following info: %s', credential_info)
            if not self.__service_account_email:
                self.__service_account_email = credentials.service_account_email
            return credentials

        except Exception as excp:
            self.log.exception(
                'Exception while creating Google credentials object for google API')
            raise excp

    def build_service(self, api_name, delegated_user=None):
        """Builds Google service object for invoking Google APIs

                Args:

                    api_name (Str)   --   The name of the API to invoke.
                                         This should be provided as defined in constants.

                    delegated_user  (Str)   --   User's email id to impersonate user.
                                                 Default value is admin email from constants

                Returns:

                    Google service object  (object) -- Instance of Google client API resource class

        """
        try:
            if delegated_user is None:
                delegated_user = constants.ADMIN_EMAIL
            credentials = self._get_credentials()
            servicename = constants.GOOGLE_API_DICT.get(api_name)[0]
            serviceversion = constants.GOOGLE_API_DICT.get(api_name)[1]
            self.log.info(
                'Building service object for API Name: %s and API version: %s',
                servicename,
                serviceversion)
            delegated_cred = credentials.create_delegated(delegated_user)
            self.log.info(
                'Obtained delegated credentials for user: %s',
                delegated_user)
            http_auth = delegated_cred.authorize(Http())
            self.log.info('http_auth object created')
            google_service = discovery.build(
                servicename, serviceversion, http=http_auth)
            self.log.info(
                'Google service object created for API Name: %s and API Version: %s',
                servicename,
                serviceversion)
            return google_service

        except Exception as excp:
            self.log.exception(
                'Exception while building google service object. '
                'Service Name or version may be incorrect or credentials can not be refreshed.'
            )
            raise CVCloudException(self.api_name, '102', str(excp))

    @property
    def service_account_email(self):
        """Treats service_account_email as read only attribute """

        return self.__service_account_email

    def __del__(self):
        """Deletes the credentials from Storage"""

        self.log.info('entered destructor. deleting credential store')
        try:
            storage = Storage(constants.CRED_STORAGE_FILE)
            storage.delete()
            self.log.info('deleted credential store')
        except Exception:
            self.log.warning(
                'Error while deleting credential storage. The file may not exist.')


class OneDriveAuth:
    """Class for authenticating Microsoft Graph API via application id and secret key."""

    def __init__(self, logger, cloud_region=1):
        """Initializes the OneDrive Authentication object with given application id and secret key.

                Args:

                    logger (object)  --   instance of logger module
                    cloud_region (int) -- cloud region of the client which determines the gcc or gcc high configuration

                Returns:

                    object  -   instance of OneDriveAuth class

        """

        self.log = logger
        self.__application_id = None
        self.api_name = self.__class__.__name__
        self.client_id = constants.CLIENT_ID
        self.client_secret = constants.CLIENT_SECRET
        self.tenant = constants.TENANT
        self.auth_token_url = constants.AUTH_TOKEN_URL % self.tenant
        self.scope = constants.ONEDRIVE_SCOPE
        if cloud_region == 5:
            self.auth_token_url = constants.GCC_HIGH_AUTH_TOKEN_URL % self.tenant
            self.scope = constants.GCC_HIGH_ONEDRIVE_SCOPE
        self.oauth = None
        self.token = None

    def __repr__(self):
        """Representation string for the instance of the OneDriveAuth class."""

        return 'OneDriveAuth class instance for Azure app ID: %s', self.__application_id

    def authenticate_client(self):
        """This method authenticates the OneDrive App for MS Graph APIs."""

        try:
            self.log.info('Authenticating the OneDrive client via BackendApplicationClient')
            client = BackendApplicationClient(client_id=self.client_id)
            self.oauth = OAuth2Session(client=client)
            self.token = self.oauth.fetch_token(
                token_url=self.auth_token_url,
                client_id=self.client_id,
                client_secret=self.client_secret,
                scope=self.scope,
                include_client_id=True)
            self.token = self.token.get('access_token')
            self.log.info('Access token fetched from MS Graph')
        except Exception as excp:
            self.log.exception('Error occurred during OneDrive backend authentication')
            raise CVCloudException(self.api_name, '101', str(excp))
        