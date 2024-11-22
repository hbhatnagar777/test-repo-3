# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Main file for performing Team operations.

Users, User are the classes defined in this file.

Users:  Class for representing all Azure Users.

User: Class for representing a single User.

Users:
======
    get_user_details()      --  Get details of a particular user.
    get_user()              --  Return User object for an existing user.
    create_user()           --  Create a new user and return a User object.
    _compute_all_users()    --  Computes the value of property _all_users.

Users Instance Attributes:
=========================
    **all_users**   --  A dictionary of all the users.

User:
=====
    _init_()        --  Initialize object of User.

"""

import json

import Application.Teams.request_response as rr
import Application.Teams.teams_constants as const
import AutomationUtils.config as config
from Application.Teams.Registry.user_registry import UserRegistry
apis = const.MS_GRAPH_APIS
config = config.get_config().Azure


class Users:
    """Class for all Users in Azure."""

    user_registry = UserRegistry.get_instance(UserRegistry)

    def __init__(self):
        """Initializes an object representing all Azure users."""
        self._all_users = {}

    def _compute_all_users(self, cross_tenant_details=None):
        """Computes the value of property _all_users.
            Args:
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None
        """

        if not self._all_users:
            USERS = apis['USERS']['url']
            _, response = rr.get_request(url=USERS, cross_tenant_details=cross_tenant_details)
            response = json.loads(response.text)

            def process_values(response):
                value = response['value']
                for val in value:
                    self._all_users[val['displayName']] = User(val['displayName'], cross_tenant_details)
                if "@odata.nextLink" in response.keys():
                    _, response = rr.get_request(url=response["@odata.nextLink"], status_code=200,
                                                 cross_tenant_details=cross_tenant_details)
                    response = json.loads(response.text)
                    process_values(response)

            process_values(response)

    @property
    def all_users(self, cross_tenant_details=None):
        """A property to represent all Users.
            Args:
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None
            Returns:
                dict - A dictionary of the user names as keys and user details as values.
        """
        if not self._all_users:
            self._compute_all_users(cross_tenant_details)
        return self._all_users

    @staticmethod
    def get_user_details(name, cross_tenant_details=None):
        """Get all user details
            Args:
                name (str)   --  Name of the user.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                tuple   --  bool, True If details exist Else false.
                            dict, of user details If present Else empty dict.

            Raises:
                Exception if we fail to get user details or could not verify whether the user exists or not.

        """

        api = apis['GET_USER']
        flag, response = rr.get_request(url=api['url'].format(
            user_principal_name='@'.join((name.replace(" ", ""), config.Tenant if not cross_tenant_details else cross_tenant_details["Tenant"]))),
            status_code=200, cross_tenant_details=cross_tenant_details)
        if flag:
            details = json.loads(response.text)
            return flag, details
        elif not flag and response.status_code == 404:
            return flag, {}
        else:
            raise Exception("Failed to get user details, could not verify whether user exists or not.")

    @staticmethod
    def get_user(name, cross_tenant_details=None):
        """Retrieves user details.
            Args:
                name    (str)   --  Name of the user.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                obj --  An object of User for the given name.

            Raises:
                Exception if we failed to fetch user details.

        """
        user = Users.user_registry.get(name)
        if user:
            return user

        flag, user = Users.get_user_details(name, cross_tenant_details)
        if flag:
            user = User(user, cross_tenant_details)
            Users.user_registry.add(name, user)
            return user
        # CREATE IF USER IS NOT PRESENT
        user = Users.create_user(name, cross_tenant_details)
        Users.user_registry.add(name, user)
        return user

    def refresh(self):
        """Clear existing value and get the value for all users."""
        self._all_users = {}
        self._all_users = self.all_users

    @staticmethod
    def create_user(name, password='#####', cross_tenant_details=None, **kwargs):
        """Create a user.
            Args:
                name        (str)   --  Name of user to be created.
                password    (str)   --  Password for user.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None
                \\*\\*kwargs  (dict)  --  Optional arguments.
                    Available kwargs Options:
                        nick_name   (str)   --  Nickname of user.
                            default:    Value of argument 'name'

            Returns:
                obj --  Instance of User.

            Raises:
                When user failed to be created.

        """
        api = apis['USERS']
        email = '@'.join((name, config.Tenant if not cross_tenant_details else cross_tenant_details["Tenant"]))
        data = json.loads(api['data'].format(name=name, nick_name=kwargs.get('nick_name', name), email=email, pwd=password))
        flag, resp = rr.post_request(url=api['url'], data=data, status_code=201, cross_tenant_details=cross_tenant_details)
        if flag:
            return User(json.loads(resp.content)['displayName'], cross_tenant_details)
        raise Exception("Failed to create user.")


class User:
    """Class representing an Azure User resource."""

    def __init__(self, display_name, cross_tenant_details=None):
        """Initializes instance of User.
            Args:
                display_name    (str)   --  Display name of the user.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Raises:
                Exception in case we failed to retrieve the User's details.

        """

        flag, user = [True, display_name] if isinstance(display_name, dict) \
            else Users.get_user_details(display_name, cross_tenant_details)
        if flag and user != {}:
            self.display_name = user["displayName"]
            self.id = user['id']
            self.user_principal_name = user['userPrincipalName']
        else:
            raise Exception("Failed to get the user's details.")

