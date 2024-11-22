# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Main file for performing D365 User operations.

Users, User are the classes defined in this file.

Users:  Class for representing all Azure Users.

User: Class for representing a single User.

Users:
======
    get_user()              --  Return User object for an existing user.
    create_user()           --  Create a new user and return a User object.
    _compute_all_users()    --  Computes the value of property _all_users.
    delete_user()           --  Delete a user from Azure
    assign_license()        --  Assigns/Removes licenses for a user

Users Instance Attributes:
=========================
    **all_users**   --  A dictionary of all the users.

User:
=====
    _init_()                --  Initialize object of User.
    get_user_details()      --  Get the user details

"""

import json

from .constants import USERS
from .web_req import PyWebAPIRequests


class Users:
    """Class for all Users in Azure."""

    def __init__(self, credentials):
        """
            Initializes an object representing all Azure users.
            Arguments:
                credentials     (obj)   --  Credentials through which resource can be accessed
        """

        self._all_users = {}
        self._access_endpoint = "https://graph.microsoft.com"
        self._pyd365req = PyWebAPIRequests()
        self._credentials = credentials
        self._tenant = self._credentials._userid.split('@')[1]

    def _compute_all_users(self):
        """
            Computes the value of property _all_users
        """

        if not self._all_users:
            api = USERS['CREATE_USER']
            response = self._pyd365req.make_webapi_request(method="GET", resource=api['url'],
                                                           access_endpoint=self._access_endpoint,
                                                           credentials=self._credentials)

            def process_values(response):
                value = response['value']
                for val in value:
                    self._all_users[val['displayName']] = User(val, self._credentials)
                if "@odata.nextLink" in response.keys():
                    response = self._pyd365req.make_webapi_request(method="GET", resource=response['@odata.nextLink'],
                                                                   access_endpoint=self._access_endpoint,
                                                                   credentials=self._credentials)
                    process_values(response)

            process_values(response)

    @property
    def all_users(self):
        """
            A property to represent all Users.

                Returns:
                    dict - A dictionary of the user names as keys and user details as values.
        """
        if not self._all_users:
            self._compute_all_users()
        return self._all_users

    def get_user(self, name):
        """
            Retrieves user details.
                Args:
                    name    (str)   --  Name of the user.

                Returns:
                    obj --  An object of User for the given name.
        """

        return User(name, self._credentials)

    def refresh(self):
        """
            Clear existing value and get the value for all users.
        """

        self._all_users = {}
        self._all_users = self.all_users

    def create_user(self, name, password='#####', **kwargs):
        """
            Create a user.
                Args:
                    name        (str)   --  Name of user to be created.
                    password    (str)   --  Password for user.
                    \\*\\*kwargs  (dict)  --  Optional arguments.
                        Available kwargs Options:
                            nick_name   (str)   --  Nickname of user.
                                default:    Value of argument 'name'

                Returns:
                    obj --  Instance of User.
        """

        api = USERS['CREATE_USER']
        email = '@'.join((name, self._tenant))
        data = json.loads(
            api['data'].format(name=name, nick_name=kwargs.get('nick_name', name), email=email, pwd=password))
        response = self._pyd365req.make_webapi_request(method="POST", resource=api['url'],
                                                       access_endpoint=self._access_endpoint,
                                                       credentials=self._credentials, body=data)
        return User(response['displayName'], self._credentials)

    def delete_user(self, name):
        """
            Delete a user from Azure
            Arguments:
                name(str)       --  Display Name of the user to be deleted

            Returns:
                obj        --  response obj for the api call
        """

        api = USERS['DELETE_USER']
        user_obj = User(name, self._credentials)
        response = self._pyd365req.make_webapi_request(method="DELETE", resource=api['url'].format(user_id=user_obj.id),
                                                       access_endpoint=self._access_endpoint,
                                                       credentials=self._credentials)
        return response

    def assign_license(self, name, disabled_plans=None, sku_id="", remove_licenses=None):
        """
            Assigns/Removes licenses for a user
            Arguments:
                name(str)                --  Display name of user to which license is to be assigned/removed
                disabled_plans(str)      --  List of Plans to be disabled on the licenses provided to be assigned
                sku_id(str)              --  GUID of the licenses to be assigned
                remove_licenses(str)     --  GUIDs of the licenses to be removed

            Returns:
                obj        --  response obj for the api call
        """

        add_license = []
        flag = False

        def create_body_string(values):
            result = ""
            values = values.split(',')
            n = len(values)
            for index in range(n):
                if index != n - 1:
                    result += f"\"{values[index]}\","
                else:
                    result += f"\"{values[index]}\""
            return result

        if disabled_plans is None:
            disabled_plans = ""
        else:
            disabled_plans = create_body_string(disabled_plans)

        if remove_licenses is None:
            if sku_id == "":
                raise Exception("Provide GUIDs of the license to be assigned/removed ")
            else:
                flag = True
                remove_licenses = ""
        else:
            if sku_id != "":
                flag = True
            remove_licenses = create_body_string(remove_licenses)

        if flag:
            add_license = '[' \
                           f'{{"disabledPlans" : [{disabled_plans}],' \
                           f'"skuId": "{sku_id}"' \
                           f'}}]'

        user_obj = User(name, self._credentials)
        api = USERS["ASSIGN_LICENSE"]

        data = json.loads(
            api['data'].format(add_license=add_license, remove_licenses_id=remove_licenses))
        response = self._pyd365req.make_webapi_request(method="POST", resource=api['url'].format(user_id=user_obj.id),
                                                       access_endpoint=self._access_endpoint,
                                                       credentials=self._credentials, body=data)
        return response


class User:
    """Class representing an Azure User resource."""

    def __init__(self, display_name, credentials):
        """
            Initializes instance of User.
                Args:
                    display_name    (str)   --  Display name of the user.
                    credentials     (obj)   --  Credentials through which resource can be accessed

                Raises:
                    Exception in case we failed to retrieve the User's details.
        """

        self._access_endpoint = "https://graph.microsoft.com"
        self._pyd365req = PyWebAPIRequests()
        self._credentials = credentials
        self._tenant = self._credentials._userid.split('@')[1]

        user = display_name if isinstance(display_name, dict) else self.get_user_details(display_name)
        if user != {}:
            self.display_name = user["displayName"]
            self.id = user['id']
            self.user_principal_name = user['userPrincipalName']
        else:
            raise Exception("Failed to get the user's details.")

    def get_user_details(self, name):
        """
            Get the user details
                Args:
                    name (str)   --  Name of the user.

                Returns:
                    obj        --  response obj for the api call
        """

        api = USERS['GET_USER']
        response = self._pyd365req.make_webapi_request(method="GET", resource=api['url'].format(
            user_principal_name='@'.join((name.replace(" ", ""), self._tenant))), access_endpoint=self._access_endpoint,
                                                       credentials=self._credentials)
        return response
