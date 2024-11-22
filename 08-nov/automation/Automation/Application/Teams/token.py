# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing Token operations.

Token is the only class defined in this file.

Token:  Class for representing Tokens

_init_()                    --  Initializes the token object.
_generate_token()           --  Generates a token.
_generate_delegated_token() --  Generates a delegated token.
refresh()                   --  Generates new tokens.

"""

import requests
import json

import AutomationUtils.config as config

Azure = config.get_config().Azure


class Token:
    """Class representing a token, it uses the Directory ID, Application ID and Secret all of which
    need to be defined in \\CoreUtils\\Templates\\config.json.

    """

    def __init__(self, destination=False):
        """Initializes the token object.
            Args:
                destination     (bool)      --      Whether the object belongs to cross tenant or not
                    Default:    False
        """
        self.token = None
        self.delegated_token = None
        if not destination:
            self.token = self._generate_token()
            self.delegated_token = self._generate_delegated_token()

    @staticmethod
    def _generate_token(cross_tenant_details=None):
        """Generates a token.
            Args:
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                str --  The access token.

            Raises:
                Exception if the token could not be generated.

        """

        if cross_tenant_details is None:
            endpoint = f'https://login.microsoftonline.com/{Azure.App.DirectoryID}/oauth2/v2.0/token'

            data = {'client_id': Azure.App.ApplicationID,
                    'scope': 'https://graph.microsoft.com/.default',
                    'client_secret': Azure.App.ApplicationSecret,
                    'grant_type': 'client_credentials'}

        else:
            endpoint = f'https://login.microsoftonline.com/{cross_tenant_details["App"]["DirectoryID"]}/oauth2/v2.0/token'

            data = {'client_id': cross_tenant_details["App"]["ApplicationID"],
                    'scope': 'https://graph.microsoft.com/.default',
                    'client_secret': cross_tenant_details["App"]["ApplicationSecret"],
                    'grant_type': 'client_credentials'}

        response = requests.post(endpoint, data=data)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf8').replace("'", '"'))['access_token']
        raise Exception("Failed to generate the token, ensure provided credentials and Azure app details are valid.")

    @staticmethod
    def _generate_delegated_token(cross_tenant_details=None):
        """Generates a delegated token.
            Args:
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                str --  The access token.

            Raises:
                Exception if the token could not be generated.

        """
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        if cross_tenant_details is None:
            endpoint = f"https://login.microsoftonline.com/{Azure.App.DirectoryID}/oauth2/token"

            data = f"""grant_type=password&
            client_secret={Azure.App.ApplicationSecret}&
            client_id={Azure.App.ApplicationID}&
            Resource=https%3A%2F%2Fgraph.microsoft.com%2F&
            scope=openid&username={Azure.User}&
            password={Azure.Password}"""

        else:
            endpoint = f"https://login.microsoftonline.com/{cross_tenant_details['App']['DirectoryID']}/oauth2/token"

            data = f"""grant_type=password&
            client_secret={cross_tenant_details['App']['ApplicationSecret']}&
            client_id={cross_tenant_details['App']['ApplicationID']}&
            Resource=https%3A%2F%2Fgraph.microsoft.com%2F&
            scope=openid&username={cross_tenant_details["User"]}&
            password={cross_tenant_details['Password']}"""

        response = requests.post(endpoint, headers=headers, data=data)
        if response.status_code == 200:
            return json.loads(response.content.decode('utf8').replace("'", '"'))['access_token']
        raise Exception("Failed to generate the token, ensure provided credentials and Azure app details are valid.")

    def refresh(self, cross_tenant_details=None):
        """Generates new tokens.
            Args:
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None
        """

        self.token = self._generate_token(cross_tenant_details)
        self.delegated_token = self._generate_delegated_token(cross_tenant_details)
