# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
    ExchangeCSDBHelper is the only class in this file

ExchangeCSDBHelper:

    Class for performing operations on CommServ DB pertaining to Exchange Mailbox Agent


ExchangeCSDBHelper
=======

    __init__(exmbclient_object)             --  initialize object of ExchangeCSDBHelper class associated with
                                                the Exchange Mailbox

    get_backup_time_size_from_csdb()        --  Method to get the last played backup time and size

    get_public_folder_guid()                --  Get the GUID assigned to a public folder

    get_mailbox_assoc_policy()              --  Get the Association Policies assigned to a mailbox associated with
                                                the Exchange Client
    check_deleted_flag_set()                --  Checks whether the deleted flag is set for a mailbox
    get_assoc_mailbox_count()				--	Get the number of mailboxes associated with a client
    get_mailbox_guid()                      --  Get the GUIDs of the mailboxes
    get_number_of_items_for_backup_job()    --  Method to get the number of items in the backup job
    get_discovery_prop()                    --  Method to get the last discovery state stats for a client.
    get_licensed_users_for_client()         --  Get the licensed users for a client.
"""

from __future__ import unicode_literals
from collections import OrderedDict
from xmltodict import parse
from AutomationUtils.options_selector import OptionsSelector
from . import constants


class ExchangeCSDBHelper:
    """
        Class for performing all operations on CommServ DB pertaining to Exchange Mailbox Agent
    """

    def __init__(self, ex_object):
        """Initializes the input variables,logging and creates object from other modules.

                Args:
                    ex_object   --  instance of ExchangeMailbox class

                Returns:
                    object  --  instance of ExchangeCSDBHelper class"""
        self.tc_object = ex_object.tc_object
        self._utility = OptionsSelector(self.tc_object.commcell)
        self.log = self.tc_object.log
        self.log.info('logger initialized for Exchange DB Helper')
        self.csdb = self.tc_object.csdb

    def get_backup_time_size_from_csdb(self):
        """
            Method to get the lastBackupTime and the totalBackupSize of an
            Exchange Client's Backupset from CSDB

            Arguments:
                 None
            Returns:
                prop_dict       (dict)--    Dictionary of retrieved properties
            Example:
                  {
                    'lastBackupTime': value,
                    'totalBackupSize' : value
                    }
        """
        query = constants.GET_BACKUP_PROP % self.tc_object.backupset.backupset_id
        query_result = self._utility.exec_commserv_query(query=query)
        self.tc_object.log.info(query_result)
        query_result = OrderedDict(
            parse(
                query_result[0][0],
                process_namespaces=True
            )
        )
        res_dict = dict()
        res_dict['applicationSize'] = query_result['Indexing_DbStats']['apps']['stat']['@applicationSize']
        res_dict['lastPlayedBackupTime'] = query_result['Indexing_DbStats']['@lastPlayedBkpTime']
        return res_dict

    def get_public_folder_guid(self):
        """
            Method to get the GUID associated with the 'All Public Folders'
            association in the CSDB

            Arguments:
                None

            Returns:
                public_folder_guid      (str)--     The GUID associated with the Public Folder
        """

        query = constants.GET_PUBLIC_FOLDER_GUID % self.tc_object.client.client_id
        query_result = self._utility.exec_commserv_query(query=query)
        public_folder_guid = query_result[0][0]
        return public_folder_guid

    def get_mailbox_assoc_policy(self, mailbox_smtp_address):
        """
            Method to get the policy IDs associated with the mailbox in the CSDB.

            Arguments:
                mailbox_smtp_address    (str)-- The SMTP Address of the mailbox

            Returns:
                policies                (dict)-- Dictionary of Archive, Retention and Config Policy
        """
        query = constants.GET_MAILBOX_ASSOC_POLICY % (
            mailbox_smtp_address, self.tc_object.client.client_id)
        query_result = self._utility.exec_commserv_query(query=query)
        self.tc_object.log.info(query_result)
        polic_dict = dict()
        for policyId, policyVal in query_result[1]:
            if policyId == '1':
                polic_dict['archive_policy'] = policyVal
            elif policyId == '2':
                polic_dict['cleanup_policy'] = policyVal
            elif policyId == '3':
                polic_dict['retention_policy'] = policyVal
        return polic_dict

    def check_deleted_flag_set(self, mailbox_smtp_address):
        """
            Checks whether the deleted flag is set for a mailbox in CSDB or not

            Arguments:
                mailbox_smtp_address        (str)--     The SMTP Address of the mailbox

            Returns
                deleted_flag_is_set         (Bool)--    True if the deleted flag is set
        """
        query = constants.CHECK_MAILBOX_DELETED_FLAG % (
            self.tc_object.client.client_id, mailbox_smtp_address)
        self.csdb.execute(query)
        row = self.csdb.fetch_one_row()
        return False if row == [''] else True

    def get_assoc_mailbox_count(self):
        """
            Method to get a count f the number of mailboxes associated with the Client
            Client ID is taken from TC_Object-> Client-> Client ID

            Arguments:
                None

            Returns:
                associated_mailbox_count        (int)--     Number of mailboxes associated with the client

        """

        query = constants.GET_ASSOC_MBX_COUNT % self.tc_object.client.client_id
        user_count_sql_server = self._utility.exec_commserv_query(query)
        assoc_count = int(user_count_sql_server[0][0])
        return assoc_count

    def get_mailbox_guid(self, mailbox_list: list):
        """
            Method to get the GUIDs for the list of mailboxes

            Arguments:
                mailbox_list        (list)--    List of mailboxes to get the GUID of

            Returns:
                mailbox_guid_dict   (dict)--    Dictionary of mailbox GUIDs
                Format:
                    mailbox_alias is the key
                    mailbox_guid would be the value

        """
        mailbox_guid_dict = dict()

        for mailbox in mailbox_list:
            _query = (
                    "select userguid from APP_EmailConfigPolicyAssoc where "
                    "subClientId = '%s'and aliasName = '%s' and modified = 0" %
                    (self.tc_object.subclient.subclient_id, mailbox))

            self.csdb.execute(_query)
            mailbox_guid = self.csdb.fetch_one_row()
            mailbox_guid = mailbox_guid[0]

            mailbox_guid_dict[mailbox.lower()] = mailbox_guid

        return mailbox_guid_dict

    def get_discovery_prop(self, client_id: int = int()):
        """
            Method to get the last discovery state stats for an Exchange Online client.

            Arguments:
                client_id           (int)--     Client ID for which details are required.
                    Optional
                        If None, value from test case object -> client object is used

            Returns:
                discovery_xml       (dict)--    Discovery XML for the client

        """
        if not client_id:
            client_id = self.tc_object.client.client_id
        _query = "select attrVal from App_idaProp where componentNameId = (select id from APP_IDAName where " \
                 "clientId = {}) and attrName = 'Discovery State' and modified = 0".format(client_id)
        res = self._utility.exec_commserv_query(_query)
        self.log.info("Discovery Property for client: {}".format(res))
        try:
            res = res[0][0]
        except IndexError as excep:
            self.log.exception("Error: {} in indexing the DB query result- set".format(excep))
            raise Exception("Invalid list/ tuple returned after executing DB query")

        dict_of_discovery_xml = OrderedDict(
            parse(
                res,
                process_namespaces=True))
        return dict_of_discovery_xml

    def get_number_of_items_for_backup_job(self, job_id: int):
        """
            Method to get the number of items in the backup job
            Args:
                job_id(int)        -- Job id for which number of items is required

            Returns:
                Number of items in the provided job id
        """
        try:
            self.log.info(
                "Getting number of items in job %s from database" %
                job_id)
            query_string = "select totalNumOfFiles from JMBkpStats Where jobId=%s" % job_id
            self.csdb.execute(query_string)
            result = self.csdb.fetch_one_row()
            self.log.info(
                "Number of items in job %s is: %s" %
                (job_id, result[0]))
            return int(result[0])
        except Exception as excp:
            self.log.exception(
                "Error in getting job details from database. %s" %
                str(excp))
            raise excp

    def get_licensed_users_for_client(self) -> list:
        """
            Get the users for a client, which were marked as licensed by discovery
        """
        _query = "select smtpAdrress, licensingStatus from app_emailconfigpolicyassoc where " \
                 "licensingStatus > 0 and clientId = {} and modified = 0".format(self.tc_object.client.client_id)
        res = self._utility.exec_commserv_query(_query)
        _users = res[1]
        self.log.info("Licensed Users from DB: {}".format(res))
        return _users

    def get_attr_for_mailbox(self, property_name: str, mailbox_smtp_address: str):
        """
            Get the value for a particular attribute for a user mailbox from association table
            Arguments:
                property_name       (str):      Name of the property to be fetched
                mailbox_smtp_address(str):      SMTP Address to be fetched

        """
        self.log.info("Fetching property: {} for User: {}".format(property_name, mailbox_smtp_address))
        _query = f"Select {property_name} from APP_EmailConfigPolicyAssoc where " \
                 f"clientId = {self.tc_object.client.client_id} and smtpAdrress = '{mailbox_smtp_address}' " \
                 f"and modified = 0 "
        res = self._utility.exec_commserv_query(_query)
        self.log.info("Fetch User Property Response: {}".format(res))
        return res[0][0]
