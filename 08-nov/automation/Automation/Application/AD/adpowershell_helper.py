# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing AD and Azure AD Powershell related operations.

ADPowerShell:
        gpo_operations() - Method to perform operations for GPO

        attribute_operations()  - Method to perform attribute operations for a user
AADPowerShell:
        user_ps_operations()    -Method to perform azure ad user related operations
"""

from AutomationUtils import machine
from Application.AD import constants

__author__ = 'Sakshi Gaur'


class ADPowerShell(object):
    """class to run ad powershell command """

    def __init__(self, ad_object, server_name,
                 ad_username, ad_password, domain_name=None):
        """Initializes the ADPowerShell object

            Args:
                ad_object (object)      -- instance of the ad object

                server_name             -- Server name is the machine with commvault's package

                ad_username (str)       -- AD administrator username

                ad_password (str)       -- AD administrator password

                domain_name(str)        -- domain name

        """
        self.ad_object = ad_object
        self.log = self.ad_object.log
        self.server_name = server_name
        self.ad_username = ad_username
        self.ad_password = ad_password
        self.domain_name = domain_name
        self.utils_path = constants.UTILS_PATH
        self.powershell_path = constants.SCRIPT_PATH
        self.output_files = constants.RETRIEVED_FILES_PATH
        self.host_machine = machine.Machine(server_name, self.ad_object.commcell)

    def gpo_operations(self, op_type, gpo_name=None, attr_name=None, value=None, ou=None):
        """Method to perform gpo operations
        Args:
            gpo_name(str)       -- GPO name
            op_type(str)        -- Operation type for GPO
            attr_name(str)      -- Name of the attribute
            value(str)          -- Value of the attribute to set
            ou(str)             -- Organisational Unit
        """

        result = None
        try:
            self.log.info('Performing GPO operation using powershell. '
                          'Powershell Path %s', constants.GPO_OPS)

            prop_dict = {
                "LoginPassword": self.ad_password,
                "LoginUser": self.ad_username,
                "GPOName": gpo_name,
                "OpType": op_type,
                "OU": ou,
                "Domain": self.domain_name,
                "ServerName": self.server_name,
                "Attribute": attr_name,
                "AttributeValue": value
            }
            output = self.host_machine.execute_script(
                constants.GPO_OPS, prop_dict)
            if 'GET' in op_type:
                result = int(output.formatted_output)
            elif op_type in ('GPLINKS_ATT', 'GPLINKS_PROP', 'GUID_ID', 'GPLINK_ID'):
                result = output.__dict__['_formatted_output']

            if output.exit_code != 0:
                raise Exception("Failed to perform gpo operation")

            return result

        except Exception as excp:
            self.log.exception("Exception in performing gpo operation: %s", str(excp))
            raise excp

    def attribute_operations(self, entity_name, op_type, attribute, value=None):
        """Method to perform multi-attribute operations
        Args:
            entity_name(str)    -- Entity name
            op_type(str)        -- Operation type for attribute
            attribute(str)      -- Name of the attribute
            value(str)          -- Corresponding value of the attribute to set
        """

        result = None
        try:
            self.log.info('Performing multi-attribute operations using powershell. '
                          'Powershell Path %s', constants.ATTRIBUTE_OPS)

            prop_dict = {
                "LoginPassword": self.ad_password,
                "LoginUser": self.ad_username,
                "EntityName": entity_name,
                "OpType": op_type,
                "ServerName": self.server_name,
                "Attribute": attribute,
                "Value": value
            }
            output = self.host_machine.execute_script(
                constants.ATTRIBUTE_OPS, prop_dict)
            if 'GET' in op_type:
                result = output.formatted_output
            if output.exit_code != 0:
                raise Exception("Failed to perform attribute operation")

            return result

        except Exception as excp:
            self.log.exception("Exception in performing the attribute operation: %s", str(excp))
            raise excp
    
    def os_remote_ops(self, path, optype): 
        """Method to perform os remote operations
        Args:
            path(str)    -- Path to perform operation
            optype(str)  -- Operation type
        """
        prop_dict = {
            "LoginPassword": self.ad_password,
            "LoginUser": self.ad_username,
            "Path": path,
            "OpType": optype,
            "ServerName": self.server_name
        }
        output = self.host_machine.execute_script(
            constants.OS_OPS, prop_dict)

        return output


class AADPowerShell(object):

    """Class to perform azure ad powershell related operations"""

    def __init__(self, log, azure_username, azure_password):
        """Initializes the class to perform AD operations

            Args:

            log                     --instance of the logger class
            azure_username          --Azure account username
            azure_password          --Azure account password

        """
        self.log = log
        self.azure_username = azure_username
        self.azure_password = azure_password
        self.host_machine = machine.Machine()

    def user_ps_operation(self, op_type,group_object_id=None,user_id=None):
        """
        Function to execute power shell operation to add azure user to a group
        param group_object_id: object id of the group
        param user_id: user id of the user
        op_type: type of operation to perform
        """
        try:

            prop_dict = {
                "AzureUsername": self.azure_username,
                "AzurePassword": self.azure_password,
                "UserId": user_id,
                "GroupObjectId": group_object_id,
                "OpType":op_type
            }

            self.log.info("Executing power shell script")
            power_output = self.host_machine.execute_script(
                constants.Azure_User_Operations, prop_dict)

            if(op_type=='RETURN_MEMBER_GROUPS'):
                attr_value = power_output.__dict__
                result = attr_value['_formatted_output']
                return result

        except Exception as excp:
                self.log.exception("Exception in fetching attributes: %s", str(excp))
                raise excp

