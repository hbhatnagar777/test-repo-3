# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Class:
Retention - Helper class to get values of retention policies

Retention:

    __init__                            --- initializes Retention object

    get_policy_values                    --- fetch retention policy values

    is_delete_retention_policy_assigned  --- method to verify deletion based retention policy

    get_number_of_days_for_media_pruning --- method to retrieve days for media pruning value
                                             set on retention policy

    get_mailbox_user_guid                --- method to get user guid of a mailbox

"""

from collections import OrderedDict
from xmltodict import parse


class Retention():
    """Class for performing Retention related operations."""

    def __init__(self, ex_object):
        """
            Initializes the Retention object.

            Args:
                ex_object  (Object)  --  instance of ExchangeMailbox module

            Returns:
                object  --  instance of ExchangeLib class

        """
        self.tc_object = ex_object.tc_object
        self.log = self.tc_object.log
        self.app_name = self.__class__.__name__
        self.mail_users = ex_object.users
        self.client_name = ex_object.client_name
        self.csdb = ex_object.csdb

    def get_policy_values(self, mailbox_name):
        """
            Method to get values of retention policy associated to mailbox

            Args:
                mailbox_name  (str)  --  Mailbox name associated to sub client

                Returns:
                    policy_dict (dict) -- Dict of policy values

        """

        # Fetch Client ID
        client_id = self.tc_object.commcell.clients.all_clients[self.client_name.lower()]['id']

        # Fetch User GUID
        _user_guid_query = "select userGuid from APP_EmailConfigPolicyAssoc where " \
            "smtpAdrress = '%s' and clientId = '%s'" % (mailbox_name, client_id)
        self.csdb.execute(_user_guid_query)
        _user_guid_results = self.csdb.fetch_one_row()
        user_guid = _user_guid_results[0]

        # Fetch Policy ID
        _query1 = "select policyId from APP_EmailConfigPolicies where " \
                  "policyType = 3 and componentNameId " \
                  "IN (select assocId from APP_EmailConfigPolicyAssoc where clientId = '%s' " \
                  "and smtpAdrress = '%s' and modified = 0 )" % (client_id, mailbox_name)
        self.csdb.execute(_query1)
        _results1 = self.csdb.fetch_one_row()

        # Fetch Policy details of Exchange Configuration Policy
        _query2 = ("select policyDetails from APP_ConfigurationPolicyDetails"
                   " where  modified = 0 and componentNameId ='%s' " % _results1[0])
        self.csdb.execute(_query2)
        _results2 = self.csdb.fetch_one_row()

        policy_xml = _results2[0]
        policy_dict = {}

        policy_dict['userGuid'] = user_guid

        # Getting the message rules based on the Policy XML retrieved from the CS DB
        # Converting XML into Dict
        dict_of_base_xml = OrderedDict(parse(policy_xml, process_namespaces=True))
        print(dict_of_base_xml)
        days_for_media_pruning = dict_of_base_xml['emailPolicy'][
            'retentionPolicy']['@numOfDaysForMediaPruning']
        policy_dict['days_for_media_pruning'] = str(days_for_media_pruning)

        policy_type = dict_of_base_xml['emailPolicy']['@emailPolicyType']
        policy_dict['policy_type'] = str(policy_type)

        return policy_dict

    def is_delete_retention_policy_assigned(self, mailbox_name):
        """Helper method to check deletion based retention policy
            Args:
                mailbox_name(str)         --  Mailbox smtp address

            Returns:
                Boolean                   -- if deletion based retention policy is assigned

        """
        try:
            policy_dict = self.get_policy_values(mailbox_name)
            return policy_dict['policy_type'] == str(1)
        except Exception as excp:
            self.log.exception('Error occurred while checking delete retention policy assignment:'
                               '%s', mailbox_name)
            raise excp

    def get_number_of_days_for_media_pruning(self, mailbox_name):
        """Helper method to retrieve number of days for media pruning set on retention policy
            Args:
                mailbox_name(str)         --  Mailbox smtp address

            Returns:
                str                       --  Number of days media pruning set on retention policy

        """
        try:
            policy_dict = self.get_policy_values(mailbox_name)
            return policy_dict['days_for_media_pruning']
        except Exception as excp:
            self.log.exception('Error occurred while retrieving days of media pruning'
                               ' set on retention policy: %s ', mailbox_name)
            raise excp

    def get_mailbox_user_guid(self, mailbox_name):
        """Helper method to retrieve user guid of mailbox
            Args:
                mailbox_name(str)         --  Mailbox smtp address

            Returns:
                str                       --  user guid of mailbox
        """
        try:
            policy_dict = self.get_policy_values(mailbox_name)
            return policy_dict['userGuid']
        except Exception as excp:
            self.log.exception('An error occurred while retrieving user guid of mailbox: %s ',
                               mailbox_name)
            raise excp
