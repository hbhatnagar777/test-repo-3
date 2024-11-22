# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for performing Smart Client Group related operations for Creation, Cleanup of Smart client groups.

SmartClientHelper is the class defined in this file

SmartClientHelper : Class containing utilities for various Smart Client group Generation, Cleanup Capabilities


SmartClientHelper :
    __init__() : Initializes the class properties and logger object

    generate_random_email() : Creates a random email

    create_smart_client_json() : Creates the Smart Client Group JSON payload used for creation of group

    create_smart_client() : Creates the Smart Client group with appropriate data

    create_smart_rule() : Used for creating a smart rule of given conditions

    update_scope() : Used for Updating the Scope of the Smart Client group without changing the filter rules

    has_client_group() : Used to check if given client group is present in the client groups for the Commcell

    get_clients_list() : Gets the List of clients associated with a Client Group

    preview_clients() : Gets the list of clients which will be associated with a particular Group

    get_commcell_clients() : Gets the list of all clients for given commcell

    get_company_clients() : Gets the list of clients of a company

    get_user_clients() : Gets the list of clients of a particular user

    get_usergroup_clients() : Gets the list of clients of a particular user group

    validate_clients_list() : Validates if the preview clients list and generated clients list are same

    refresh_client_groups() : Updates the value of client groups to reflect changes

    get_client_group() : Used for return the Object corresponding to given Client group if it exists

    smart_client_cleanup() : Used for cleaning up the Smart Client group that was created
"""

import random
import string
from cvpysdk.clientgroup import ClientGroup, ClientGroups
from cvpysdk.exception import SDKException
from AutomationUtils import logger
from AutomationUtils.options_selector import OptionsSelector
from Server.organizationhelper import OrganizationHelper
from Server.Security.userhelper import UserHelper
from Server.Security.usergrouphelper import UsergroupHelper


class SmartClientHelper:
    """
    Class for Smart Client Group Creation and other operations
    """
    def __init__(self, commcell_object, group_name=None, description=None, client_scope=None, value=None):
        """Initialize object of the AlertHelper class.

                Args:
                    commcell_object (object)  --  instance of the Commcell class
                    group_name (string) - Group name of the smart client group to be created
                    description (string) - Description of the smart client group to be created
                    client_scope (string) - Client scope for the smart client group
                    value (string) - Value for the Dropdown for the selected Scope

                Returns:
                    object - instance of the SmartClientHelper class
         """
        self.commcell_object = commcell_object
        self._CLIENTGROUPS = self.commcell_object._services['CLIENTGROUPS']
        self.client_groups = ClientGroups(self.commcell_object)
        self.cs_name = self.commcell_object.commserv_name
        self.group_name = group_name
        self.description = description
        self.client_scope = client_scope
        self.value = value
        self.options_selector = None
        self.scgscope = None
        self.scgrule = None
        self.log = logger.get_log()

    @staticmethod
    def generate_random_username(char_num=14):
        """Generate a random username"""
        random_chars = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(char_num))
        return random_chars
    
    @staticmethod
    def generate_random_email(char_num=14):
        """Generate a random email"""
        random_chars = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(char_num))
        return random_chars + "@commvault.com"

    def create_smart_client(self, smart_rule_list):
        """Creates smart client group for given data
        """
        self.scgrule = self.client_groups.merge_smart_rules(smart_rule_list)

        self.client_groups.add(clientgroup_name=self.group_name,
                               clientgroup_description=self.description,
                               clients=[],
                               scg_rule=self.scgrule,
                               client_scope=self.client_scope,
                               client_scope_value=self.value)
        self.log.info(f'Creation of Smart Client Group {self.group_name} with scope "{self.client_scope}" successful')

    def create_smart_rule(self, filter_rule, filter_condition, filter_value):
        """Creates required dictionary for given smart client data

                Args:
                    filter_rule (string)  --  Filter Rule value
                    filter_condition (string)  --  Filter Condition
                    filter_value (string)  --  Filter Value

                Returns:
                    smart rule object - Smart Rule with specified conditions
        """
        return self.client_groups.create_smart_rule(filter_rule, filter_condition, filter_value)

    def update_scope(self, clientgroup_name, client_scope, value=None):
        """Attempts to update the scope of Smart Client group with given name

                Args:
                    clientgroup_name (string)  --  Name of the Smart client group to edit
                    client_scope (string)  --  New Scope to set
                    value (string)  --  New Scope value to set
                Returns:
                    clientgroup (ClientGroup object) -- client group object

                Note : This only updates the scope value without changing the Client Group Rules
                Note : If function returns None it means the scope is not updated successfully, else returns client
                        clientgroup object
        """
        # Create object for client group of given name
        client_group = self.client_groups.get(clientgroup_name)
        scope_dict = [self.client_groups._create_scope_dict(client_scope, value)]
        scgrule = client_group.properties['scgRule']
        # Formulate the properties dict required for updating properties of a client group
        properties_dict = {
            "description": self.description,
            "isSmartClientGroup": True,
            "clientGroup": {
                "clientGroupName": clientgroup_name,
                "newName": clientgroup_name
            },
            "scgScope": scope_dict,
            "scgRule": scgrule
        }
        try:
            client_group.update_properties(properties_dict)
            self.log.info(f'Successfully Updated Scope of Smart Client Group {clientgroup_name} to {client_scope}')
            return client_group
        except Exception as update_excp:
            self.log.error(f'Encountered exception while updating client group scope\n Error : {update_excp}')
            return

    def has_client_group(self, clientgroup_name):
        """Returns if given client group is present/absent in the client groups for the Commcell

                Args:
                    clientgroup_name (string)  --  Name of the Smart client group to check

                Returns:
                    bool - If the givne client group is present or not
        """
        self.refresh_client_groups()
        return self.client_groups.has_clientgroup(clientgroup_name)

    def get_clients_list(self, clientgroup_name):
        """Returns the list of clients for a given smart client group

                Args:
                    clientgroup_name (string)  --  Name of the Smart client group whose clients are to be returned

                Returns:
                    list - List of clients in the given client group
        """
        self.refresh_client_groups()
        client_group = self.client_groups.get(clientgroup_name)
        return client_group.associated_clients

    def preview_clients(self, client_scope=None, value=None):
        """Returns the list of Clients which would be added to a Client Group with given Scope and Value

                Args:
                    client_scope (string)  --  Client Scope
                    value (string)  --  Client scope Value

                Returns:
                    list -- List of clients which will be a part of the client group with given scope

                Note : This only works for Filter rule -> Clients equals to Installed
        """
        self.options_selector = OptionsSelector(self.commcell_object)
        # Execute different queries based on the client scope
        if client_scope is None:
            client_scope = self.client_scope

        if client_scope is None:
            raise SDKException("ClientGroup", "102", "Client Scope is provided as None")

        if client_scope.lower() == "clients in this commcell" and value is None:
            self.log.info("Getting Clients for scope 'Clients in this Commcell'")
            commcell_clients = self.get_commcell_clients()
            self.log.info("Clients list generated successfully")
            return commcell_clients
        elif client_scope.lower() == "clients of companies" and value is not None:
            self.log.info("Getting Clients for scope 'Clients of Companies'")
            company_clients = self.get_company_clients(company_name=value)
            self.log.info("Clients list generated successfully")
            return company_clients
        elif client_scope.lower() == "clients of user" and value is not None:
            self.log.info("Getting Clients for scope 'Clients of User'")
            user_clients = self.get_user_clients(user_name=value)
            self.log.info("Clients list generated successfully")
            return user_clients
        elif client_scope.lower() == "clients of user group" and value is not None:
            self.log.info("Getting Clients for scope 'Clients of User Group'")
            usergroup_clients = self.get_usergroup_clients(usergroup_name=value)
            self.log.info('Clients list generated successfully')
            return usergroup_clients

    def get_commcell_clients(self):
        """Returns the list of all Commcell Clients"""
        clients_list = []
        query = f"""DECLARE @inClientId INT = 0/*GetAllClients*/;
                            DECLARE @inSCGId INT = 0/*SCGProcessing*/; 
                            select name from app_client where id in (
                            (
                             SELECT clientId FROM dbo.scgV2GetClientProps('=', 1  , @inClientId, @inSCGId ) 
                            ));"""
        db_response = self.options_selector.update_commserve_db(query)
        if len(db_response.rows) == 0:
            return clients_list

        column_index = db_response.columns.index('name')
        for client in db_response.rows:
            clients_list.append(client[column_index])
        return clients_list

    def get_company_clients(self, company_name):
        """Returns the list of clients of a given company name

                Args:
                    company_name (string)  --  Company Name for which associated clients are to be retrieved

                Returns:
                    list -- List of associated clients with given Company

        """
        organization_helper = OrganizationHelper(self.commcell_object, company_name)
        company_clients = organization_helper.get_company_clients()

        return company_clients

    def get_user_clients(self, user_name):
        """Returns the list of clients for a given user

                Args:
                    user_name (string)  --  User Name for which associated clients are to be retrieved

                Returns:
                    list -- List of clients associated with given user

        """
        user_obj = self.commcell_object.users.get(user_name)
        user_helper = UserHelper(self.commcell_object, user_obj)
        user_clients = user_helper.get_user_clients()

        return user_clients

    def get_usergroup_clients(self, usergroup_name):
        """Returns the list of clients for a given user

                Args:
                    usergroup_name (string)  --  User group Name for which associated clients are to be retrieved

                Returns:
                    list -- List of clients associated with given user

        """
        usergroup_obj = self.commcell_object.user_groups.get(usergroup_name)
        usergroup_helper = UsergroupHelper(self.commcell_object, usergroup_obj)
        usergroup_clients = usergroup_helper.get_usergroup_clients()
        if usergroup_name == 'master':
            usergroup_clients = [client for client in usergroup_clients if client != 'Server Plan_IndexServer']

        return usergroup_clients

    def validate_clients_list(self, preview_clients_list, clients_list):
        """Returns if the preview list of clients and clients which belong to the smart client group match

                Args:
                    preview_clients_list (list)  --  List of clients generated before creating the group
                    clients_list (list) -- List of clients which belong to the group created

                Returns:
                    bool -- True if lists match else Rasises Exception

        """
        to_lower = lambda s : s.lower()
        preview_clients_list = sorted(list(map(to_lower, preview_clients_list)))
        self.log.info("List of Preview clients : {0}".format(str(preview_clients_list)))
        clients_list = sorted(list(map(to_lower, clients_list)))
        self.log.info("List of Group clients : {0}".format(str(clients_list)))
        validated = preview_clients_list == clients_list
        if validated:
            self.log.info("Preview Clients list and Created Group Clients list match")
            return validated
        else:
            raise SDKException("ClientGroup", "102", "Preview clients and Created group clients don't match")

    def refresh_client_groups(self):
        """Updates the value of client groups to reflect new change
        """
        self.log.info("Refreshing Client Groups")
        self.client_groups.refresh()

    def get_client_group(self, clientgroup_name):
        """Returns Client group object of given name

                Args:
                    clientgroup_name (string)  --  Name of client group that is to be retrieved

                Returns:
                    object -- Client group object for given client group name

        """
        self.refresh_client_groups()
        return self.client_groups.get(clientgroup_name)

    def smart_client_cleanup(self):
        """Performs cleanup specific to the Smart Client group that was created
        """
        # Cleanup (Delete the smart client group created)
        self.refresh_client_groups()
        clientgroup_name = self.group_name.lower()
        self.log.info(f"Will try to delete smart client group {clientgroup_name} with scope {self.client_scope}")
        try:
            self.client_groups.delete(clientgroup_name)
            self.log.info("Deletion of client group successfull")
        except Exception as group_deletion_excp:
            self.log.error(group_deletion_excp)
