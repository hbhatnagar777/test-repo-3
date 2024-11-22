# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main module for generating data for testcases"""

from __future__ import unicode_literals
import os
import random
import string

from AutomationUtils import machine, config
from ..exchangepowershell_helper import ExchangePowerShell
from .constants import TEST_DATA_GENERATION_JSON
from . import constants as CONSTANT


class TestData:
    """Class to create testdata for testcases"""

    def __init__(self, ex_object):
        """Initializes the Testdata object

            Args:
                tc_object (object) -- instance of the testcase object

        """

        self.ex_object = ex_object
        self.testcase_id = str(ex_object.tc_object.id)
        self.log = self.ex_object.log
        self.host_machine = machine.Machine(
            ex_object.server_name, self.ex_object.commcell)
        self.json_value = self.read_data_from_json()
        try:
            self.json_value = getattr(self.json_value, ("t" + self.testcase_id))
        except:
            self.json_value = None
        self.exchange_type = ex_object.exchange_type
        self.mailbox_type = ex_object.mailbox_type
        if (self.ex_object.exchange_type == CONSTANT.environment_types.EXCHANGE_ONPREMISE.value
                or self.ex_object.mailbox_type == CONSTANT.mailbox_type.JOURNAL.name):
            self.service_account_user = ex_object.service_account_user
            self.service_account_password = ex_object.service_account_password
        else:
            self.service_account_user = ex_object.exchange_online_user
            self.service_account_password = ex_object.exchange_online_password
        self.powershell_object = ExchangePowerShell(
            self.ex_object, self.ex_object.exchange_cas_server, self.ex_object.exchange_server[0],
            self.service_account_user, self.service_account_password, self.ex_object.server_name,
            self.ex_object.domain_name)

    @staticmethod
    def read_data_from_json():
        """Method to read data from JSON file

            Returns:
                sheet_number(int)  --  Sheet number to read the test data

        """

        return config.get_config(
            reset=True, json_path=TEST_DATA_GENERATION_JSON)

    def clean_online_mailbox_contents(self):
        """Method to clean content from exchange online mailboxes"""
        try:
            for _iterator in self.json_value.CleanupMailbox:
                mb_name = (f'{_iterator.DISPLAYNAME}'
                           f'{self.ex_object.server_name}'
                           f'{self.testcase_id}')
                self.powershell_object.exch_online_operations(
                    alias_name=mb_name, op_type="CLEANUP")

        except Exception as excp:
            self.log.exception("Exception in cleanMailboxContents(): %s", excp)
            raise excp

    def send_email_online_mailbox(self):
        """Method to send emails to exchange online mailboxes

            Returns:
                smtp_list(list)  --  List of smtp address

        """
        try:
            smtp_list = []
            for _iterator in self.json_value.SendEmail:
                smtp = (f'{_iterator.SMTP}{self.ex_object.server_name}'
                        f'{self.testcase_id}@{self.ex_object.domain_name}')
                smtp_list.append(smtp.lower())

            self.powershell_object.send_email_online_mailbox(smtp_list)

            return smtp_list
        except Exception as excp:
            self.log.exception(
                "Exception in send_email_online_mailbox(): %s", excp)
            raise excp

    def create_online_mailbox(self, use_json: bool = True, count: int = 4, special_chars: bool = False):
        """
            Method to create exchange online mailboxes

            Returns:
                alias_name_list     (list)  --  List of alias name
                use_json            (bool)  --  Whether to use the JSON for mailbox creation
                count               (int)   --  Number of mailboxes to create
                    Used only when use_json is false
                special_chars       (bool)  --  Use special characters while generating address also

        """
        try:
            alias_name_list = []
            if use_json is False:
                for _ in range(count):
                    _alias = ''.join(random.choices(string.ascii_lowercase, k=7))
                    if special_chars:
                        _special_char = ''.join(random.choices("!# $%&'*+-/=?^_`{|}~", k=2))
                        #   special chars cannot be first or last letter of the name, so generate and append to alias

                        _alias = _alias + _special_char

                    alias_name = (f'{_alias}'
                                  f'{self.ex_object.server_name}'
                                  f'{self.testcase_id}')

                    self.log.info('Creating mailbox: {}'.format(alias_name))
                    self.powershell_object.exch_online_operations(alias_name=alias_name, op_type="CREATE")
                    alias_name_list.append(alias_name)

            if use_json:
                for _mbiterator in self.json_value.Mailbox:
                    alias_name = ""
                    if _mbiterator.OPTYPE.lower() == "create":
                        alias_name = (f'{_mbiterator.ALIASNAME}'
                                      f'{self.ex_object.server_name}'
                                      f'{self.testcase_id}')

                        display_name = (f'{_mbiterator.DISPLAYNAME}'
                                        f'{self.ex_object.server_name}'
                                        f'{self.testcase_id}')

                        smtp = (f'{_mbiterator.SMTP}'
                                f'{self.ex_object.server_name}'
                                f'{self.testcase_id}')

                        self.log.info('Creating mailbox %s', alias_name)
                        self.powershell_object.exch_online_operations(alias_name=alias_name, smtp_address=smtp,
                                                                      display_name=display_name, op_type="CREATE")

                    alias_name_list.append(alias_name)
            return alias_name_list
        except Exception as excp:
            self.log.exception("Exception in create_online_mailbox(): %s", excp)
            raise excp

    def clean_onprem_mailbox_contents(self, cleanup_mbx_list):
        """Method to clean content from exchange onprem mailboxes
            Args:
                cleanup_mbx_list(list)  -- List of mailboxes
        """
        try:
            for _iterator in cleanup_mbx_list:
                self.powershell_object.clean_on_premise_mailbox_contents(
                    _iterator)

        except Exception as excp:
            self.log.exception("Exception in cleanMailboxContents(): %s", excp)
            raise excp

    def create_mailbox(self):
        """Method to create exchange on premise mailboxes

            Returns:
                alias_name_list(list)  --  List of alias name

        """
        try:
            if "Mailbox" not in self.json_value._fields:
                self.log("provide details for mailbox creation")
            old_db=""
            alias_name_list = []

            for _mbiterator in self.json_value.Mailbox:

                if _mbiterator.OPTYPE.lower() == "create":
                    alias_name = f'{_mbiterator.ALIASNAME}_{self.testcase_id}'
                    display_name = f'{_mbiterator.DISPLAYNAME}_{self.testcase_id}'
                    smtp = f'{_mbiterator.SMTP}_{self.testcase_id}'

                    self.log.info('Creating mailbox %s ', alias_name)
                    database_name = (f'{_mbiterator.DATABASE}_'
                                     f'{self.ex_object.exchange_server[0]}_'
                                     f'{self.testcase_id}')
                    if database_name!= old_db and not self.check_if_db_exists(database_name):
                        self.powershell_object.create_database(database_name)
                    self.powershell_object.create_mailbox(display_name, alias_name,
                                                          smtp, database_name)
                    old_db = database_name
                    alias_name_list.append(alias_name)
            return alias_name_list
        except Exception as excp:
            self.log.exception("Exception in create_mailbox(): %s", excp)
            raise excp

    def create_journal_mailbox(self):
        """Method to create exchange on premise journal mailboxes

            Returns:
                alias_name_list(list)  --  List of alias name

        """
        try:

            alias_name_list = []

            for _mbiterator in self.json_value.Mailbox:

                if _mbiterator.OPTYPE.lower() == "create":
                    alias_name = f'{_mbiterator.ALIASNAME}_{self.testcase_id}'
                    display_name = f'{_mbiterator.DISPLAYNAME}_{self.testcase_id}'
                    smtp = f'{_mbiterator.SMTP}_{self.testcase_id}'
                    self.log.info('Creating mailbox %s', alias_name)
                    database_name = (f'{_mbiterator.DATABASE}_'
                                     f'{self.ex_object.exchange_server[0]}_'
                                     f'{self.testcase_id}')
                    if not self.check_if_db_exists(database_name):
                        self.powershell_object.create_database(database_name)
                    self.powershell_object.create_journal_mailbox(
                        display_name, alias_name, smtp, database_name)
                    alias_name_list.append(alias_name)
            return alias_name_list
        except Exception as excp:
            self.log.exception(
                "Exception in create_journal_mailbox(): %s", excp)
            raise excp

    def get_o365_groups(self, max_retries=3, cnt=0):
        """Method to Get Office 365 groups
            Args:
                max_retries(int)        -- Number of retries allowed
                    Default: 3

                cnt(int)                -- Keep a count on number of retries
                    Default: 0

            Returns:
                dict of all O365 groups discovered

        """
        try:
            groups = self.powershell_object.get_o365_groups()
            if "Result is: 0" in groups:
                return None
            if "Result is: -1" in groups:
                if cnt < max_retries:
                    self.log.info("Error while running powershell commands to get groups."
                                  "Retrying to get groups")
                    groups = self.get_o365_groups(cnt=cnt + 1)
                else:
                    raise Exception(
                        "Getting O365 groups failed after 3 attempts")
            return self.get_o365_groups_helper(groups)
        except Exception as excp:
            self.log.exception("Exception in get_o365_groups(): %s", excp)
            raise excp

    def get_o365_groups_helper(self, groups_data):
        """Helper method to parse data received from Powershell script
            Args:
                groups_data(string)        -- Powershell output

            Returns:
                dict of all O365 groups discovered
        """
        try:
            groups, group_dict = {}, {}
            key = None
            groups_data = groups_data.split("\r\n")
            for data in groups_data:
                data = data.split(":")
                if len(data) > 1:
                    if data[0].strip().lower() == "alias":
                        key = data[1].strip().lower()
                        group_dict = {'alias_name': key}
                    elif data[0].strip().lower() == "externaldirectoryobjectid":
                        group_dict['user_guid'] = data[1].strip().replace("-", 'X').upper()
                        groups[key] = group_dict
                        group_dict = {}
                    elif data[0].strip().lower() == "primarysmtpaddress":
                        group_dict["smtp_address"] = data[1].strip().lower()
                    elif data[0].strip().lower() == "displayname":
                        group_dict["display_name"] = data[1].strip().lower()
            return groups
        except Exception as excp:
            self.log.exception("Exception in parse_o365_groups(): %s", excp)
            raise excp

    def check_if_db_exists(self, dbname):
        """Method to check if database exists"""
        self.log.info("Checking if DB exists: %s", dbname)

        databases = self.powershell_object.get_databases()

        retrieved_db_list = ((databases).split("Name")[-1]).splitlines()
        for temp_db in retrieved_db_list:
            temp_db1 = temp_db.strip()
            temp_db1 = ''.join(temp_db1.split())
            if temp_db1 == dbname:
                return True

        return False

    def import_pst(self):
        """Method to import pst

            Returns:
                smtp_list(list)  --  List of Smtp addresses

        """
        try:

            smtp_list = []
            for _mbiterator in self.json_value.ImportPST:
                if _mbiterator.OPTYPE.lower() == "import":
                    alias_name = f'{_mbiterator.DISPLAYNAME}_{self.testcase_id}'
                    self.log.info('Import PST to mailbox %s', alias_name)
                    smtp_list.append(
                        (alias_name + "@" + self.ex_object.domain_name))
                    self.powershell_object.import_pst(
                        alias_name, self.ex_object.pst_path)
            return smtp_list

        except Exception as excp:
            self.log.exception("Exception in import_pst(): %s", excp)
            raise excp

    def import_data_contentstore_mailbox(self):
        """Method to copy mailboxes data to contentStore mailboxes

            Returns:
                mailboxes(list)  --  List of mailboxes

        """
        mailbox_list = []
        self.log.info('Import Mailbox data to ContentStore Mailboxes')

        for mailbox in self.json_value.Mailbox:
            mailbox_dict = {}
            mailbox_dict['smtpAdrress'] = "{0}_{1}@commvault.com".format(mailbox.SMTP,
                                                                         self.testcase_id)
            mailbox_dict['displayName'] = "{0}_{1}".format(mailbox.DISPLAYNAME,
                                                           self.testcase_id)

            self.log.info('Copying data to mailbox %s', mailbox_dict['displayName'])

            if isinstance(self.ex_object.smtp_mailbox_path, str):
                mailbox_path = os.path.join(self.ex_object.smtp_mailbox_path, "Mailboxes",
                                            (mailbox.DISPLAYNAME + "_" + str(self.testcase_id)))

            if self.host_machine.check_directory_exists(mailbox_path):
                self.log.info('Deleting the existing mailbox path')
                self.host_machine.client_object.stop_service("GxImapServer(Instance001)")
                self.host_machine.remove_directory(mailbox_path)
                self.host_machine.client_object.start_service("GxImapServer(Instance001)")
            self.host_machine.copy_folder(self.ex_object.contentstore_mailbox_path, mailbox_path)
            mailbox_list.append(mailbox_dict.copy())
        return mailbox_list

    def create_o365_group(self, use_json: bool = True, special_chars: bool = False, group_members: list = list()):
        """
            Method to create Office 365 Groups
                Arguments:
                    None
                Returns:
                    group_name_list         (list)--   List of Groups Created
                Note:
                    Makes use of MS Graph API
        """
        try:
            group_name_list = list()
            if use_json is False:
                _group_mail_nickname = ''.join(random.choices(string.ascii_lowercase, k=7))
                if special_chars:
                    _special_char = ''.join(random.choices("!# $%&'*+-/=?^_`{|}~", k=2))
                    #   special chars cannot be first or last letter of the mail address, so generate and append to alias

                    _group_mail_nickname = _group_mail_nickname + _special_char

                _group_mail_nickname = (f'{_group_mail_nickname}'
                                        f'{self.ex_object.server_name}'
                                        f'{self.testcase_id}')
                #
                # _chars = string.digits + string.ascii_letters + string.punctuation
                # _group_name = ''.join(random.choices(_chars, k=10))

                self.log.info('Creating AD Group: {}'.format(_group_mail_nickname))
                self.ex_object.graph_helper.create_group(group_name=_group_mail_nickname, mail_nickname=_group_mail_nickname)
                group_name_list.append(_group_mail_nickname)

                if group_members:
                    self.ex_object.graph_helper.add_group_members(group_name=_group_mail_nickname, members=group_members)
            else:
                for _grpiterator in self.json_value.O365Group:
                    _group_name = str()
                    if _grpiterator.OPTYPE.upper() == 'CREATE':
                        _group_name = (f'{_grpiterator.GROUPNAME}'
                                       f'{self.ex_object.server_name}'
                                       f'{self.testcase_id}')
                        self.log.info('Creating Group: {}'.format(_group_name))
                        self.ex_object.graph_helper.create_group(group_name=_group_name)
                        group_name_list.append(_group_name)

                    if _grpiterator.MEMBERS:
                        members = _grpiterator.MEMBERS
                        smtp_list = list()
                        for alias_name in members:
                            smtp = (f'{alias_name}'
                                    f'{self.ex_object.server_name}'
                                    f'{self.testcase_id}@{self.ex_object.domain_name}')
                            smtp_list.append(smtp)
                        self.ex_object.graph_helper.add_group_members(group_name=_group_name, members=smtp_list)
            return group_name_list
        except Exception as excp:
            self.log.exception("Exception in Create Online AD Group: %s", excp)
            raise excp

    def delete_online_mailboxes(self, mailboxes_list: list):
        """
            Method to delete Exchange online mailboxes

            Arguments:
                    mailboxes_list   (list)--   List of mailbox SMTP address to delete

            Returns
                None
        """
        try:
            for mailbox in mailboxes_list:
                self.log.info("Deleting Exchange Online Mailbox: {}".format(mailbox))
                self.powershell_object.exch_online_operations(
                    op_type="DELETE",
                    smtp_address=mailbox)

        except Exception as excp:
            self.log.exception("Exception while deleting online mailboxes: %s", excp)
            raise excp
