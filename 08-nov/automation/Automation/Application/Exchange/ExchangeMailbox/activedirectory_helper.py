# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main Module for invoking active directory APIs.

MailboxInfo, ADGroup, ActiveDirectory are the classes defined in this file.

MailboxInfo: Class for all MailboxInfo Info.

ADGroup: Class for all Adgroups Info.

ActiveDirectory: Class for performing all ActiveDirectory
                related operations like getting all users and groups.

"""
import re
import os
import time
import xml.etree.ElementTree as ET
import pythoncom
from azure.graphrbac import GraphRbacManagementClient
from azure.common.credentials import UserPassCredentials
from active_directory import AD_object, search, root
from AutomationUtils import machine
from .constants import GET_ONLINE_USERS
from .constants import GET_ONLINE_AD_USERS
from .constants import GET_ONLINE_AD_GROUPS
from .constants import GET_MEMBERS_OF_GROUP
from . import constants as CONSTANT


class MailboxInfo:
    """Class for Mailbox Detail Info"""

    def __init__(self):
        """Initializes the MailboxInfo object."""

        self.alias_name = ""
        self.display_name = ""
        self.smtp_address = ""
        self.user_guid = ""
        self.database_name = ""
        self.exchange_server_name = ""
        self.legacy_dn = ""
        self.ldap_homeserver = ""
        self.ldap_home_mbdb = ""
        self.memberof = []
        self.distinguished_name = ""
        self.exch_version = ""
        self.object_guid = ""
        self.object_type = ""
        self.primary_group_id = ""


class ADGroup:
    """Class for AdGroup Detail Info"""

    def __init__(self):
        """Initializes the ADGroup object."""
        self.samaccount_name = ""
        self.alias_name = ""
        self.display_name = ""
        self.distinguish_name = ""
        self.group_mail = ""
        self.parent_groups = []
        self.users = []
        self.primary_token = ""


class DiscoveryOptions():
    """Class for performing active directory operation for Exchange account."""

    def __new__(cls, ex_object):
        """Decides which instance object needs to be created"""
        ex_type = CONSTANT.environment_types
        exchange_type = ex_object.exchange_type
        if exchange_type == ex_type.EXCHANGE_ONLINE.value:
            return object.__new__(AzureActiveDirectory)

        return object.__new__(ActiveDirectory)

    def __init__(self, ex_object):
        """Initializes the DiscoveryOptions object.

               Args:
                    ex_object  (Object)  --  instance of ExchangeMailbox module
                Returns:
                    object  --  instance of Active Directory class
        """
        self.log = ex_object.log
        self.exchange_server = ""
        self._users = {}
        self._groups = {}
        self._databases = {}
        self._journal_users = {}
        self.tc_object = ex_object.tc_object
        self.exch_object = ex_object
        self.subclient = self.exch_object.tc_object.subclient
        self.ex_type = CONSTANT.environment_types
        self.exchange_type = ex_object.exchange_type
        self.host_machine = machine.Machine(
            ex_object.server_name, ex_object.tc_object.commcell)

    @property
    def users(self):
        """Returns the users for Exchange"""
        return self._users

    @property
    def groups(self):
        """Returns the groups in the domain"""
        return self._groups

    @property
    def databases(self):
        """Returns the databases from Exchange"""
        return self._databases

    @property
    def journal_users(self):
        """Returns the journal user from Exchange"""
        return self._journal_users

    def validate_user_discovery(self):
        """This method validates user discovery"""
        try:
            self.log.info("Validating User discovery")
            discover_users = self.subclient.discover_users

            discover_users_list = []
            for user in discover_users:
                discover_users_list.append(user['aliasName'].lower())
            self.log.debug('Discover Users: "{0}"'.format(discover_users_list))
            self.log.debug('AD Users: "{0}"'.format(self.users.keys()))
            for key in self.users:
                if key.lower() in discover_users_list:
                    continue
                else:
                    self.log.error(
                        'AD Users: "{0}" not found in discover. '
                        'PLease check discover logs'.format(key))
                    raise Exception('User discovery Validation failed')
            self.log.info("Successfully Validated User discovery")

        except Exception as excp:
            self.log.exception("An error occurred while validating user discovery")
            raise excp

    def validate_journal_discovery(self):
        """This method validates user discovery"""
        try:
            self.log.info("Validating Journal Mailbox discovery")
            discover_journal_users = self.subclient.discover_journal_users

            discover_users_list = []
            for user in discover_journal_users:
                discover_users_list.append(user['aliasName'].lower())
            self.log.debug('Discover Users: "{0}"'.format(discover_users_list))
            self.log.debug('AD Journal Users: "{0}"'.format(self.journal_users.keys()))
            for key in self.journal_users:
                if key.lower() in discover_users_list:
                    continue
                else:
                    self.log.error(
                        'AD Journal Users: "{0}" not found in discover. '
                        'PLease check discover logs'.format(key))
                    raise Exception('Journal discovery validation failed')
            self.log.info("Successfully Validated Journal Mailbox discovery")

        except Exception as excp:
            self.log.exception("An error occurred while validating user discovery")
            raise excp

    def validate_ad_discovery(self):
        """This method validates Ad group discovery"""
        try:
            self.log.info("Validating AD discovery")
            discover_group = self.subclient.discover_adgroups
            discover_group_list = []
            for group in discover_group:
                discover_group_list.append(group['adGroupName'].lower())

            self.log.debug('Discover group: "{0}"'.format(discover_group_list))
            self.log.debug('AD groups: "{0}"'.format(self.groups.keys()))

            for key in self.groups:
                if key.lower() in discover_group_list:
                    continue
                else:
                    self.log.error(
                        'AD Group: "{0}" not found in discover. '
                        'PLease check discover logs'.format(key))
                    raise Exception('Ad discovery validation failed')
            self.log.info("Successfully Validated AD discovery")

        except Exception as excp:
            self.log.exception("An Aerror occurred while validating AD discovery")
            raise excp

    def validate_db_discovery(self):
        """This method validates Database discovery"""
        try:
            self.log.info("Validating Database discovery")
            discover_databases = self.subclient.discover_databases
            discover_databases_list = []
            for database in discover_databases:
                discover_databases_list.append(database['databaseName'].lower())

            self.log.debug('Discover group: "{0}"'.format(discover_databases_list))
            self.log.debug('Databases: "{0}"'.format(self.databases.keys()))

            for key in self.databases:
                if key.lower() in discover_databases_list:
                    continue
                else:
                    self.log.error(
                        'Database: "{0}" not found in discover. '
                        'PLease check discover logs'.format(key))
                    raise Exception('DB discovery validation failed')
            self.log.info("Successfully Validated DB discovery")

        except Exception as excp:
            self.log.exception("An error occurred while validating DB discovery")
            raise excp

    def validate_adgroup_discovery(self, discovered_groups, groups):
        """
            Method to determine if all the groups are in the list of discovered groups

            Arguments:
                discovered_groups   (list)  -   List of groups discovered
                groups              (list)  -   List of groups to be searched

            Returns
                status              (bool)  -   Whether all groups were in list of discovered groups or not
        """
        for group in groups:
            if group.lower() not in discovered_groups:
                return False
        return True

    def validate_allusers_assocaition(self, subclient_content, office365=False):
        """This method validates all users assocaitions
            Args:
                subclient_content   (dict)  --  dict of policies which needs to
                                                be assocaited to association

                    subclient_content = {

                        'archive_policy' : "CIPLAN Archiving policy",

                        'cleanup_policy' : 'CIPLAN Clean-up policy',

                        'retention_policy': 'CIPLAN Retention policy'
                }
        """
        try:
            self.log.info("Validate user association")

            users = self.subclient.users
            self.log.info('Users associated for subclient: "{0}" '.format(users))
            mailboxes_list = [user.lower() for user in self.users]
            if len(users) != len(mailboxes_list):
                self.log.error("Discovery and automation user list does not match")
                raise Exception('AllUser assocaition failed')

            for user in users:
                if user['alias_name'].lower() in mailboxes_list:
                    if not office365:
                        if (user['is_auto_discover_user'] == 'True' and
                                user['archive_policy'] ==
                                subclient_content['archive_policy'].configuration_policy_name and
                                user['cleanup_policy'] ==
                                subclient_content['cleanup_policy'].configuration_policy_name
                                and user['retention_policy'] ==
                                subclient_content['retention_policy'].configuration_policy_name):
                            continue
                        else:
                            self.log.error(
                                'Policies details for user "{0}" is '
                                'not set properly. PLease check discover logs'.format(
                                    user['alias_name']))
                            raise Exception('AllUser assocaition failed')
                    else:
                        if (user['is_auto_discover_user'] == 'True' and
                                user['plan_name'] == subclient_content['plan'].plan_name and
                                user['plan_id'] == subclient_content['plan'].plan_id):
                            continue
                        else:
                            self.log.error(
                                'Plan details for user "{0}" is '
                                'not set properly. PLease check discover logs'.format(
                                    user['alias_name']))
                            raise Exception('AllUser assocaition validation failed')
                else:
                    self.log.error(
                        'User is not given in input but assocaited: "{0}"  '
                        'PLease check discover logs'.format(
                            user['alias_name']))
                    raise Exception('AllUser assocaition failed')
            self.log.info("Successfully validated user associations")

        except Exception as excp:
            self.log.exception("An error occurred while validating user assocaitions")
            raise excp

    def set_user_assocaitions(self, subclient_content, use_policies=True):
        """This method sets user assocaitions
            Args:
                subclient_content   (dict)  --  dict of the Users to add to the
                                                subclient

                    subclient_content = {

                        'mailboxNames' : ["AutoCi2"],

                        'archive_policy' : "CIPLAN Archiving policy",

                        'cleanup_policy' : 'CIPLAN Clean-up policy',

                        'retention_policy': 'CIPLAN Retention policy'
                }

                use_policies    (bool)  -- Boolean to set if we are using Policies(True) or plans(False)
                    Default: True
        """
        try:
            self.log.info("Create user association")
            self.log.info('User Content: "{0}" '.format(subclient_content))
            self.subclient.set_user_assocaition(subclient_content, use_policies)
            self.log.info("Successfully created user associations")
        except Exception as excp:
            self.log.exception("An error occurred while set user assocaitions")
            raise excp

    def set_pst_associations(self, subclient_content):
        """This method sets pst associations
            Args:
                subclient_content   (dict)  --  dict of the pst to add to the subclient

                        subclient_content = {

                            'pstTaskName' : "Task Name for PST",

                            'folders' : ['list of folders'] //If pst ingestion by folder location,
                            'fsContent': Dictionary of client, backupset, subclient
                            Ex: {'client1':{'backupset1':[subclient1], 'backupset2':None},
                                'client2': None}
                            This would add subclient1, all subclients under backupset2 and
                            all backupsets under client2 to the association


                            'pstOwnerManagement' : {

                                'defaultOwner': "default owner if no owner is determined",

                                'pstDestFolder': "ingest psts under this folder",

                                'usePSTNameToCreateChild': Boolean
                            }
                    }
        """
        try:
            self.log.info("Create PST association")
            self.log.info('PST Content: "{0}" '.format(subclient_content))
            self.subclient.set_pst_association(subclient_content)
            self.log.info("Successfully created PST associations")
        except Exception as excp:
            self.log.exception("An error occurred while setting pst associations")
            raise excp

    def set_o365group_asscoiations(self, subclient_content):
        """This method sets o365 group associations
            Args:
                subclient_content   (dict)  --  dict of the policies to associate

                    subclient_content = {

                        'archive_policy' : "CIPLAN Archiving policy",

                        'cleanup_policy' : 'CIPLAN Clean-up policy',

                        'retention_policy': 'CIPLAN Retention policy'
                }
        """
        try:
            self.log.info("Create user association")
            self.log.info('User Content: "{0}" '.format(subclient_content))
            self.subclient.set_o365group_asscoiations(subclient_content)
            self.log.info("Successfully created user associations")
        except Exception as excp:
            self.log.exception("An error occurred while set user assocaitions")
            raise excp

    def delete_user_assocaitions(self, subclient_content):
        """This method deletes user assocaitions
                        Args:
            subclient_content   (dict)  --  dict of the Users to add to the
                                            subclient

                subclient_content = {

                    'mailboxNames' : ["AutoCi2"],

                    'archive_policy' : "CIPLAN Archiving policy",

                    'cleanup_policy' : 'CIPLAN Clean-up policy',

                    'retention_policy': 'CIPLAN Retention policy'
                }
        """
        try:
            self.log.info("Deleting user association")
            self.log.info('User Content: "{0}" '.format(subclient_content))
            self.subclient.delete_user_assocaition(subclient_content)
            self.log.info("Successfully deletd user associations")

        except Exception as excp:
            self.log.exception("An error occurred while deleting user assocaitions")
            raise excp

    def delete_o365group_associations(self, subclient_content):
        """This method deletes o365 group associations"""
        try:
            self.log.info("Deleting O365 Group association")
            self.subclient.delete_o365group_association(subclient_content)
            self.log.info("Successfully deleted O365 Group associations")

        except Exception as excp:
            self.log.exception("An error occurred while deleting user assocaitions")
            raise excp

    def validate_user_assocaition(self, subclient_content):
        """This method validates user assocaitions
            Args:
                subclient_content   (dict)  --  dict of the Users to add to the
                                                subclient

                    subclient_content = {

                        'mailboxNames' : ["AutoCi2"],

                        'archive_policy' : "CIPLAN Archiving policy",

                        'cleanup_policy' : 'CIPLAN Clean-up policy',

                        'retention_policy': 'CIPLAN Retention policy'
                }
        """
        try:
            self.log.info("Validate user association")

            users = self.subclient.users
            self.log.info('Users associated for subclient: "{0}" '.format(users))
            mailboxes_list = [mailbox.lower() for mailbox in subclient_content['mailboxNames']]
            for user in users:
                if user['alias_name'].lower() in mailboxes_list:
                    if (user['is_auto_discover_user'] == 'False' and user['archive_policy'] ==
                            subclient_content['archive_policy'].configuration_policy_name and
                            user['cleanup_policy'] ==
                            subclient_content['cleanup_policy'].configuration_policy_name
                            and user['retention_policy'] ==
                            subclient_content['retention_policy'].configuration_policy_name):
                        continue
                    else:
                        self.log.error(
                            'Policies details for user "{0}" is '
                            'not set properly. PLease check discover logs'.format(
                                user['alias_name']))
                        raise Exception('Exception occurred failed to validate user associations')
                else:
                    self.log.error(
                        'User is not given in input but assocaited: "{0}"  '
                        'PLease check discover logs'.format(
                            user['alias_name']))
                    raise Exception('Exception occurred failed to validate user associations')
            self.log.info("Successfully validated user associations")

        except Exception as excp:
            self.log.exception("An error occurred while validating user assocaitions")
            raise excp

    def validate_o365group_association(self, o365group_dict, subclient_content):
        """This method validates O365 Group associations
            Args:
                o365group_dict (dict)   -- dict of groups in the exchange online environment

                subclient_content   (dict)  --  dict of the policies associated

                    subclient_content = {

                        'archive_policy' : "CIPLAN Archiving policy",

                        'cleanup_policy' : 'CIPLAN Clean-up policy',

                        'retention_policy': 'CIPLAN Retention policy'
                }
        """
        try:
            self.log.info("Validate o365 group mailbox association")
            o365groups = self.subclient.o365groups
            self.log.info('Groups associated for subclient: "{0}" '.format(o365groups))
            for o365group in o365groups:
                if o365group['alias_name'].lower() in o365group_dict:
                    if (('archive_policy' in subclient_content and o365group['archive_policy']
                         != subclient_content['archive_policy'].configuration_policy_name) or (
                            'cleanup_policy' in subclient_content and o365group['cleanup_policy']
                            != subclient_content['cleanup_policy'].configuration_policy_name) or (
                            'retention_policy' in subclient_content and
                            o365group['retention_policy'] !=
                            subclient_content['retention_policy'].configuration_policy_name)):
                        self.log.error(
                            'Policies details for office 365 group "{0}" is '
                            'not set properly. PLease check discover logs'.format(
                                o365group['alias_name']))
                        raise Exception('Exception occurred failed to validate user associations')
                    self.log.info("Validated association for group: %s" %
                                  o365group['alias_name'].lower())
                else:
                    self.log.error(
                        'User is not given in input but assocaited: "{0}"  '
                        'PLease check discover logs'.format(o365group['alias_name']))
                    raise Exception('Exception occurred failed to validate user associations')
            self.log.info("Successfully validated group associations")

        except Exception as excp:
            self.log.exception("An error occurred while validating user assocaitions")
            raise excp

    def set_database_associations(self, subclient_content):
        """This method sets Database assocaitions
        Args:
            subclient_content   (dict)  --  dict of the Users to add to the
                                                subclient

                subclient_content = {

                    'databaseNames' : ["SGDB-1"],

                    'archive_policy' : "CIPLAN Archiving policy",

                    'cleanup_policy' : 'CIPLAN Clean-up policy',

                    'retention_policy': 'CIPLAN Retention policy'
                }
        """
        try:
            self.log.info("Create DB association")
            self.log.info('DB Content: "{0}" '.format(subclient_content))
            self.subclient.set_database_assocaition(subclient_content)
            self.log.info("Successfully created database associations")

        except Exception as excp:
            self.log.exception("An error occurred while set database assocaitions")
            raise excp

    def validate_database_assocaition(self, subclient_content):
        """This method validates Database assocaitions
        Args:
            subclient_content   (dict)  --  dict of the Users to add to the
                                                subclient

                subclient_content = {

                    'databaseNames' : ["SGDB-1"],

                    'archive_policy' : "CIPLAN Archiving policy",

                    'cleanup_policy' : 'CIPLAN Clean-up policy',

                    'retention_policy': 'CIPLAN Retention policy'
                }
        """
        try:
            self.log.info("Validate database association")
            databases = self.subclient.databases
            self.log.info('Databases associated for subclient: "{0}" '.format(databases))
            databases_list = [group.lower() for group in subclient_content['databaseNames']]
            for database in databases:
                if subclient_content['is_auto_discover_user']:
                    if database['database_name'].lower() in databases_list:
                        if (str(database['is_auto_discover_user']) ==
                                str(subclient_content['is_auto_discover_user'])
                                and database['archive_policy'] ==
                                subclient_content['archive_policy'].configuration_policy_name
                                and database['cleanup_policy'] ==
                                subclient_content['cleanup_policy'].configuration_policy_name
                                and database['retention_policy'] ==
                                subclient_content['retention_policy'].configuration_policy_name):
                            continue
                        else:
                            self.log.error(
                                'Policies details for Database "{0}" is not set properly.PLease '
                                'check discover logs'.format(database['database_name']))
                            raise Exception('Exception occurred failed to validate '
                                            'Database associations')
                    else:
                        self.log.error('Database is not given in input but assocaited: "{0}" '
                                       'PLease check discover logs'.
                                       format(database['database_name']))
                        raise Exception('Exception occurred failed to validate'
                                        'Database associations')
            self.log.info("Successfully validated Database associations")
            return True

        except Exception as excp:
            self.log.exception("An error occurred while validating Database Assocaitions")
            raise excp

    def set_adgroup_associations(self, subclient_content, use_policies=True):
        """This method sets adgroup assocaitions
            Args:
                subclient_content   (dict)  --  dict of the Users to add to the
                                                subclient

                    subclient_content = {

                        'adGroupNames' : ["_Man5_Man5_"],

                        'archive_policy' : "CIPLAN Archiving policy",

                        'cleanup_policy' : 'CIPLAN Clean-up policy',

                        'retention_policy': 'CIPLAN Retention policy'
                }
                :param use_policies: Set to False if you are associating with the help of
                Office 365 Plan
        """
        try:
            self.log.info("Create AD association")
            self.log.info('AD Content: "{0}" '.format(subclient_content))
            self.subclient.set_adgroup_associations(subclient_content, use_policies)
            self.log.info("Successfully created ad group associations")

        except Exception as excp:
            self.log.exception("An error occurred while set adgroup assocaitions")
            raise excp

    def validate_adgroup_assocaition(self, subclient_content, use_policies=True):
        """This method validates adgroup assocaitions
            Args:
                subclient_content   (dict)  --  dict of the Users to add to the
                                                subclient

                    subclient_content = {

                        'adGroupNames' : ["_Man5_Man5_"],

                        'archive_policy' : "CIPLAN Archiving policy",

                        'cleanup_policy' : 'CIPLAN Clean-up policy',

                        'retention_policy': 'CIPLAN Retention policy'
                }
        """
        try:
            self.log.info("Validate AD association")
            adgroups = self.subclient.adgroups
            self.log.info('ADGroups associated for subclient: "{0}" '.format(adgroups))
            adgroup_list = [group.lower() for group in subclient_content['adGroupNames']]
            for group in adgroups:
                if subclient_content['is_auto_discover_user']:
                    if group['adgroup_name'].lower() in adgroup_list:
                        if (str(group['is_auto_discover_user']) ==
                                str(subclient_content['is_auto_discover_user'])
                                and group['archive_policy'] ==
                                subclient_content['plan_object'].archive_policy_name
                                and group['cleanup_policy'] ==
                                subclient_content['plan_object'].cleanup_policy_name
                                and group['retention_policy'] ==
                                subclient_content['plan_object'].retention_policy_name):
                            continue
                        else:
                            self.log.error(
                                'Policies details for Group "{0}" is not set properly.'
                                ' PLease check discover logs'.format(
                                    group['adgroup_name']))
                            raise Exception(
                                'Exception occurred failed to validate Ad group associations')
                    else:
                        self.log.error('Group is not given in input but assocaited: "{0}"  '
                                       'PLease check discover logs'.format(group['adgroup_name']))
                        raise Exception(
                            'Exception occurred failed to validate Ad Group associations')
            self.log.info("Successfully validated ad group associations")

        except Exception as excp:
            self.log.exception("An error occurred while validating AD discovery")
            raise excp

    def validate_users_in_group(self, subclient_content):
        """This method validates all users from groups are associated
            Args:
                subclient_content   (dict)  --  dict of the Users to add to the
                                                subclient

                    subclient_content = {

                        'adGroupNames' : ["_Man5_Man5_"],

                        'archive_policy' : "CIPLAN Archiving policy",

                        'cleanup_policy' : 'CIPLAN Clean-up policy',

                        'retention_policy': 'CIPLAN Retention policy'
                }
        """
        try:
            self.log.info("Validate users are associated properly by AD association")

            adgroup_list = [group.lower() for group in subclient_content['adGroupNames']]
            users = self.subclient.users
            self.log.info('Associated users from subclient: "{0}" '.format(users))

            for group in adgroup_list:
                self.log.info('Input ADGroup associated for subclient: "{0}" '.format(group))
                group_object = self.groups[group]
                users_in_group = group_object.users

                for user in users_in_group:
                    if user.display_name is None and user.exchange_server_name == "":
                        break
                    if user.ldap_homeserver is not None:
                        server = user.ldap_homeserver.split("cn")[-1]
                        if server != self.exchange_server:
                            break
                    self.log.info(
                        'Input ADGroup users associated for subclient: "{0}" '.format(
                            user.display_name))
                    display_name = ""
                    if user.display_name.lower() not in adgroup_list:
                        display_name = user.display_name
                        if not any(dict['display_name'] == display_name for dict in users):
                            self.log.error('User is not assocaited to subclient : "{0}"  '
                                           'PLease check discover logs'.format(
                                display_name))
                            raise Exception('Exception occurred failed to validate adgroup '
                                            'users from adgroup association')
                    for subclient_user in users:
                        if display_name in subclient_user['display_name']:
                            if (subclient_user['is_auto_discover_user'] == str(
                                    subclient_content['is_auto_discover_user']) and
                                    subclient_user['archive_policy'] ==
                                    subclient_content['plan_object'].archive_policy_name
                                    and subclient_user['cleanup_policy'] ==
                                    subclient_content['plan_object'].cleanup_policy_name
                                    and subclient_user['retention_policy'] == subclient_content[
                                        'plan_object'].retention_policy_name):
                                continue
                            else:
                                self.log.error(
                                    'Policies details for user "{0}" is not set properly.'
                                    'PLease check discover logs'.format(
                                        subclient_user['display_name']))
                                raise Exception('Exception occurred failed to validate adgroup '
                                                'users from adgroup association')

            self.log.info("Successfully validated users are associated properly by AD association")

            return True

        except Exception as excp:
            self.log.exception("An error occurred while validating users in group")
            raise excp

    def set_journal_assocaition(self, subclient_content, use_policies=True):
        """This method sets journal mailbox assocaitions
            Args:
                subclient_content   (dict)  --  dict of the Users to add to the
                                                subclient

                    subclient_content = {

                        'mailboxNames' : ["AutoCi2"],,

                        'archive_policy' : "CIPLAN Archiving policy",

                        'cleanup_policy' : 'CIPLAN Clean-up policy',

                        'retention_policy': 'CIPLAN Retention policy'
                }

                use_policies   (bool)  --  Boolean to specify whether to use policies or plans
        """
        try:
            self.log.info("Create Journal mailbox association")
            self.log.info('Journal mailbox Content: "{0}" '.format(subclient_content))
            self.subclient.set_journal_user_assocaition(subclient_content, use_policies)
            self.log.info("Successfully created journal mailbox associations")

        except Exception as excp:
            self.log.exception("An error occurred while set journal assocaitions")
            raise excp

    def validate_journal_assocaition(self, subclient_content, use_policies=True):
        """This method validates user assocaitions
            Args:
                subclient_content   (dict)  --  dict of the Users to add to the
                                                subclient

                    subclient_content = {

                        'mailboxNames' : ["AutoCi2"],,

                        'archive_policy' : "CIPLAN Archiving policy",

                        'cleanup_policy' : 'CIPLAN Clean-up policy',

                        'retention_policy': 'CIPLAN Retention policy'
                }
        """
        try:
            self.log.info("Validate journal association")

            users = self.subclient.journal_users
            self.log.info('Journal users'
                          ' associated for subclient: "{0}" '.format(users))
            mailboxes_list = [mailbox.lower() for mailbox in subclient_content[
                'mailboxNames']]
            for user in users:
                if user['alias_name'].lower() in mailboxes_list:
                    if use_policies:
                        if (user['is_auto_discover_user'] == 'False' and
                                user['journal_policy'] ==
                                subclient_content['journal_policy'].configuration_policy_name and
                                user['retention_policy'] ==
                                subclient_content['retention_policy'].configuration_policy_name):
                            continue
                        else:
                            self.log.error(
                                'Policies details for user "{0}" is '
                                'not set properly. PLease check discover logs'.format(
                                    user['alias_name']))
                            raise Exception(
                                'Exception occurred failed to validate Journal associations')
                    else:
                        if (user['is_auto_discover_user'] == 'False' and
                                user['plan'].lower() == subclient_content['plan_name'].lower()):
                            continue
                        else:
                            self.log.error(
                                'Policies details for user "{0}" is '
                                'not set properly. PLease check discover logs'.format(
                                    user['alias_name']))
                            raise Exception(
                                'Exception occurred failed to validate Journal associations')
                else:
                    self.log.error(
                        'User is not given in input but assocaited: "{0}"  '
                        'PLease check discover logs'.format(
                            user['alias_name']))
                    raise Exception('Exception occurred failed to validate Journal associations')
            self.log.info("Successfully validated Journal associations")

        except Exception as excp:
            self.log.exception("An error occurred while validating user assocaitions")
            raise excp


class AzureActiveDirectory(DiscoveryOptions):
    """Class for performing azure active directory  operation for
    Exchange online account."""

    def __init__(self, ex_object):
        """Initializes the AzureActiveDirectory object.

            Args:
                ex_object (Object)  --  instance of ExchangeMailbox module


            Returns:
                object  --  instance of AzureActiveDirectory class
        """

        super(AzureActiveDirectory, self).__init__(ex_object)

        self.log.info('-------Azure Active Directory constructor--------')

        self.tenant_name = ex_object.tc_object.tcinputs['azureTenantName']
        self.exchange_online_user = ex_object.exchange_online_user
        self.exchange_online_password = ex_object.exchange_online_password
        self.referesh()

    def get_azure_ad_users(self):
        """Gets all the users by calling azure API.

            Returns:
                Dict    --  A dict with key as users alias name and value as
                                MailboxInfo object
        """

        try:

            self.log.info('Getting azure users ')

            self.log.info(
                'Getting azure users from powershell. Powershell Path  "{0}"'.format(
                    GET_ONLINE_USERS))
            prop_dict = {
                "LoginUser": self.exchange_online_user,
                "LoginPassword": self.exchange_online_password
            }

            output = self.host_machine._execute_script(GET_ONLINE_USERS, prop_dict)

            if output.exit_code != 0:
                return False

            content = ((output.output.strip()).split("Alias"))[1:]
            content = [(mb.strip()).lower() for mb in content]
            content = [mb.strip().lower() for mb in content[0].split('\r\n')]

            user_info = {}
            for user in self.exch_object.graph_helper.get_all_users():
                mailbox_info = MailboxInfo()
                mailbox_info.alias_name = user.get("userPrincipalName").split("@")[0]
                mailbox_name = user.get("mail") or ""
                mailbox_info.display_name = user.get("displayName")
                mailbox_info.smtp_address = user.get("userPrincipalName")
                mailbox_info.object_guid = user.get("id")
                # mailbox_info.object_type = user.object_type

                pattern = re.compile("HealthMailbox")
                if not pattern.match(
                        mailbox_name) and user.get("mail") is not None and user.get("userPrincipalName").split("@")[
                    0] in content:
                    # and user.mail_nickname in mbs: add this when nikhil fixes
                    user_info[mailbox_name.lower()] = mailbox_info
                    # log.debug("mailboxname : " + str(mailbox_name))
                # user_info[mailbox_name] = mailbox_info
            return user_info
        except Exception as excp:
            self.log.exception("An error occurred while getting Azure users")
            raise excp

    def get_azure_groups(self):
        """Gets all the adgroups by calling azure API.

            Returns:
                Dict    --  A dict with key as adgroup alias name and value as
                                        ADGroup object
        """

        try:
            self.log.info('Getting azure Groups ')
            adgroups_map = {}
            for group in self.exch_object.graph_helper.get_all_groups():
                adgroup_info = ADGroup()
                adgroup_info.samaccount_name = group.get("displayName")
                adgroup_info.group_mail = group.get("mail")
                adgroup_info.alias_name = group.get("mailNickname")
                members = self.exch_object.graph_helper.get_group_members(group.get("displayName"))
                for member in members:
                    mailbox_info = MailboxInfo()
                    mailbox_info.alias_name = member.get("userPrincipalName").split("@")[0]
                    mailbox_info.display_name = member.get("displayName")
                    mailbox_info.smtp_address = member.get("userPrincipalName")
                    mailbox_info.object_guid = member.get("id")
                    # mailbox_info.object_type = member.object_type

                    # if member.mail is not None:
                    #     alias_name = ""
                    #     if member.user_principal_name is not None:
                    #         alias_name = member.user_principal_name.split('@')[0]
                    if member.get("userPrincipalName") in self.users:
                        adgroup_info.users.append(mailbox_info)
                if group.get("mail") is not None:
                    adgroups_map[str(group.get("mailNickname")).lower()] = adgroup_info
            return adgroups_map
        except Exception as excp:
            self.log.exception("An error occurred while getting azure groups")
            raise excp

    def referesh(self):
        """Refresh the Azure Active Directory."""
        self._users = self.get_azure_ad_users()
        self._groups = self.get_azure_groups()

    def wait_mailbox_smtp_update_complete(
            self, original_smtp_address, new_smtp_address, mailbox_upn=""):
        """
            Method to check and wait for the updated
            updated SMTP to be reflected on the Graph API endpoint.


            Arguments
                original_smtp_address       (str)-- The original SMTP Address
                new_smtp_address            (str)-- The new STP Address that needs to be present
                mailbox_upn                 (str)-- The UPN of the mailbox user account

            Returns
                mailbox_present__status     (bool)--    IF The mailbox is reflected on the Graph API

            Raises
                Exception                   (Exception)-- If the updated SMTP Address is not queried from Graph API
        """

        credentials = UserPassCredentials(
            self.exchange_online_user,  # Your user
            self.exchange_online_password,  # Your password
            resource="https://graph.windows.net"
        )

        tenant_id = self.tenant_name

        graphrbac_client = GraphRbacManagementClient(
            credentials,
            tenant_id
        )
        self.log.info(
            'Tenant Name "{0}"'.format(tenant_id))

        mailbox_upn = original_smtp_address if mailbox_upn == "" else mailbox_upn

        count = 1
        while count < 10:
            user = graphrbac_client.users.get(upn_or_object_id=mailbox_upn)
            self.log.info('Current SMTP on Graph API: {}'.format(user.mail))
            if user.mail == new_smtp_address:
                return True
            else:
                time.sleep(15)
        raise Exception('Updated Mailbox SMTP not returned by Graph API')


class ActiveDirectory(DiscoveryOptions):
    """Class for performing Active directory related operations."""

    def __init__(self, ex_object):
        """Initializes the Restore object.

            Args:
                exchange_server  (str)  -- Exchange Server name


            Returns:
                object  --  instance of ActiveDirectory class
        """
        super(ActiveDirectory, self).__init__(ex_object)
        self.log.info('--------Active Directory constructor---------')
        self.ex_object = ex_object
        self.mb_type = CONSTANT.mailbox_type
        pythoncom.CoInitialize()
        self._database_level_journal_mailbox = []
        self._rule_based_journal_mailbox = []
        self.domain_name = ex_object.domain_name
        self.exchange_server = ex_object.exchange_server[0].lower()
        self.ad_object = AD_object(self.domain_controller)
        self.refresh()
        pythoncom.CoUninitialize()

    @property
    def domain_controller(self):
        """Returns the domain controller name"""
        domain_controller = str(root().distinguishedName)
        return "LDAP://CN=Configuration," + domain_controller

    @property
    def exchange_dn(self):
        """Returns the exchange distinguish name"""
        if self.exchange_server in self._servers:
            return self._servers[self.exchange_server][0]

        return ""

    @property
    def version(self):
        """Returns the verison of exchange server"""
        return self._servers[self.exchange_server][1]

    @property
    def databases(self):
        """Returns the databases in exchange server"""
        return self._databases

    @property
    def ad_users(self):
        """Returns all the ad users in the exchange server"""
        return self._all_ad_users

    @property
    def users(self):
        """Returns only user mailbox from exchange server"""
        return self._users

    @property
    def groups(self):
        """Returns all group from AD"""
        return self._groups

    @property
    def journal_users(self):
        """Returns all journal users"""
        return self._journal_users

    def _get_exchange_servers(self):
        """Gets all the exchange servers in the domain
         by calling active_directory API.

            Returns:
                Dict    --  A dict with key as users alias name and value as
                                MailboxInfo object
        """
        exchange_servers = {}
        for server in self.ad_object.search(objectCategory='msExchExchangeServer'):
            version = str(server.serialNumber)
            version = (version.split(' ')[1]).split('.')[0]
            exchange_servers[(server.name).lower()] = [server.distinguishedName, version]
        return exchange_servers

    def _get_databases(self):
        """Gets all the databases for given exchange server in subclient
         by calling active_directory API.

            Returns:
                Dict    --  A dict with key as users alias name and value as
                                MailboxInfo object
        """
        databases = {}
        try:
            for database in self.ad_object.search(
                    objectClass='msExchPrivateMDB',
                    msExchOwningServer=self.exchange_dn):  # will get all db in exchange
                databases[database.name] = database.distinguishedName
        except Exception:
            pass

        return databases

    def _get_ad_users(self):
        """Gets all the ad users including journal users
         by calling active_directory API.

            Returns:
                Dict    --  A dict with key as users alias name and value as
                                MailboxInfo object
        """

        user_info = {}
        if self.exchange_type == self.ex_type.EXCHANGE_ONLINE_AD.value:
            try:
                online_user_file = os.path.join(
                    self.host_machine.client_object.install_directory,
                    "online_users.txt")
                self.log.info('Getting online users ')
                self.log.info('Getting Online users from powershell. Powershell Path %s',
                              GET_ONLINE_AD_USERS)
                prop_dict = {
                    "LoginUser": self.exch_object.exchange_online_user,
                    "LoginPassword": self.exch_object.exchange_online_password,
                    "filepath": online_user_file
                }
                output = self.host_machine._execute_script(GET_ONLINE_AD_USERS, prop_dict)
                if output.exit_code != 0:
                    self.log.error('Getting Online users from powershell failed')
                    raise Exception("Failed to get online user %s ", output.output)

                output = self.host_machine.read_file(online_user_file)
                users_list = output.split('\n\n')
                user_dict = {}
                for user in users_list:
                    for item in user.split("\n"):
                        item = item.replace(" ", "")
                        if item.count(':') < 1:
                            continue
                        else:
                            list_users = item.split(":")
                            user_dict[list_users[0]] = list_users[1]
                        if list_users[0] == 'ArchiveWarningQuota':
                            mailbox_info = MailboxInfo()
                            mailbox_name = user_dict['Alias'].strip()
                            mailbox_info.alias_name = mailbox_name
                            mailbox_info.display_name = user_dict["DisplayName"].strip()
                            mailbox_info.smtp_address = user_dict['PrimarySmtpAddress'].strip()
                            user_info[mailbox_name.lower()] = mailbox_info

            except Exception as excp:
                self.log.exception("An error occurred while getting online users")
                raise excp

        if (self.exchange_type == self.ex_type.EXCHANGE_ONPREMISE.value or self.exchange_type ==
                self.ex_type.HYBRID.value):
            for database in self.databases.values():

                for user in search(objectCategory='User', homeMDB=database):
                    mailbox_info = MailboxInfo()

                    mailbox_name = user.mailNickName
                    mailbox_info.alias_name = mailbox_name
                    mailbox_info.display_name = user.displayName
                    database_dn = user.homeMDB
                    database = (database_dn.split(','))[0].split('=')

                    mailbox_info.database_name = database[1]
                    mailbox_info.exchange_server_name = self.exchange_server
                    mailbox_info.smtp_address = user.mail
                    mailbox_info.ldap_home_mbdb = user.homeMDB
                    mailbox_info.ldap_homeserver = user.msExchHomeServerName
                    mailbox_info.legacy_dn = user.legacyExchangeDN
                    mailbox_info.distinguished_name = user.distinguishedName
                    # mailbox_info.primary_group_id = user.primaryGroupID
                    mailbox_info.exch_version = self.version
                    try:
                        for group in user.memberOf:
                            (mailbox_info.memberof).append(group.distinguishedName)
                    except AttributeError:
                        # when user does not have memberof field, active directory
                        # package throws attribute excpetion. We want to pass in that case
                        pass

                    # put mailboxinfo in Map
                    pattern = re.compile("HealthMailbox")
                    if not pattern.match(mailbox_name):
                        user_info[mailbox_name.lower()] = mailbox_info
        if self.exchange_type == self.ex_type.HYBRID.value:
            try:
                self.log.info('Getting azure users ')
                exchange_online_user = self.exch_object.exchange_online_user
                exchange_online_password = self.exch_object.exchange_online_password
                credentials = UserPassCredentials(
                    exchange_online_user,  # Your user
                    exchange_online_password,  # Your password
                    resource="https://graph.windows.net"
                )

                tenant_id = self.exch_object.tc_object.tcinputs['azTenantName']

                graphrbac_client = GraphRbacManagementClient(
                    credentials,
                    tenant_id
                )
                self.log.info(
                    'Tenant Name "{0}"'.format(tenant_id))

                self.log.info(
                    'Getting azure users from powershell. Powershell Path  "{0}"'.format(
                        GET_ONLINE_USERS))
                prop_dict = {
                    "LoginUser": exchange_online_user,
                    "LoginPassword": exchange_online_password
                }

                output = self.host_machine.execute_script(GET_ONLINE_USERS, prop_dict)

                if output.exit_code != 0:
                    return False

                content = ((output.output.strip()).split("Alias"))[1:]
                content = [(mb.strip()).lower() for mb in content]
                content = [mb.strip().lower() for mb in content[0].split('\r\n')]

                for user in graphrbac_client.users.list():
                    mailbox_info = MailboxInfo()
                    mailbox_info.alias_name = user.mail_nickname
                    mailbox_name = user.mail_nickname
                    mailbox_info.display_name = user.display_name
                    mailbox_info.smtp_address = user.user_principal_name
                    mailbox_info.object_guid = user.object_id
                    mailbox_info.object_type = user.object_type

                    pattern = re.compile("HealthMailbox")
                    if not pattern.match(
                            mailbox_name) and user.mail is not None and user.mail_nickname in content:
                        # and user.mail_nickname in mbs: add this when nikhil fixes
                        user_info[mailbox_name.lower()] = mailbox_info
                        # log.debug("mailboxname : " + str(mailbox_name))
                    # user_info[mailbox_name] = mailbox_info

            except Exception as excp:
                self.log.exception("An error occurred while getting Azure users")
                raise excp

        return user_info

    def _get_datbaselevel_journalmailbox(self):
        """Gets all the database level journal mailbox
         by calling active_directory API.

            Returns:
                Dict    --  A dict with key as users alias name and value as
                                MailboxInfo object
        """

        journal_users = []

        for item in self.ad_object.search(
                objectClass='msExchPrivateMDB', msExchOwningServer=self.exchange_dn):
            try:
                result = str(item.msExchMessageJournalRecipient)
            except AttributeError:
                # when database does not journal recipient
                # package throws attribute excpetion. We want to continue in that case
                continue
            if result != 'None':
                result_mb = (((result.split(','))[0]).split('='))[1]
                if result_mb not in journal_users:
                    journal_users.append(result_mb.lower())
        return journal_users

    def _get_rulebased_journalmailbox(self):
        """Gets all the rule bases journal mailboxes
         by calling active_directory API.

            Returns:
                Dict    --  A dict with key as users alias name and value as
                                MailboxInfo object
        """
        journal_users = []
        for item in self.ad_object.search(objectCategory='msExchTransportRule'):
            try:
                _xml = str(item.msExchTransportRuleXml)
            except AttributeError:
                # when mailbox does not transport rule
                # package throws attribute excpetion. We want to continue in that case
                continue
            if _xml != 'None':
                xml = ET.fromstring(_xml)
                for mailbox in xml.iter('argument'):
                    journal_users.append((mailbox.attrib)['value'].lower())
        return journal_users

    def _get_user_mailboxes(self):
        """Gets all the users mailbox
         by calling active_directory API.

            Returns:
                Dict    --  A dict with key as users alias name and value as
                                MailboxInfo object
        """
        ad_users = self.ad_users.copy()

        # for mailbox in ADUsers.values():
        #     display_names[mailbox.display_name] = mailbox.alias_name
        # for item in Db_JM:
        #
        #     if item in display_names:
        #         del ADUsers[display_names[item]]

        for val in list(ad_users.keys()):

            if ad_users[val].display_name.lower() in map(
                    str.lower, self._database_level_journal_mailbox):
                del ad_users[val]

        for val in list(ad_users.keys()):
            if ad_users[val].smtp_address.lower() in map(
                    str.lower, self._rule_based_journal_mailbox):
                del ad_users[val]

        return ad_users

    def _get_journal_mailboxes(self):
        """Gets all the journal mailboxes
         by calling active_directory API.

            Returns:
                Dict    --  A dict with key as users alias name and value as
                                MailboxInfo object
        """

        journal_users = {}

        ad_users = self.ad_users.copy()
        for item in self._database_level_journal_mailbox:
            if item in ad_users.keys():
                journal_users[item] = ad_users[item]

        for val in ad_users.keys():
            if ad_users[val].smtp_address.lower() in map(
                    str.lower, self._rule_based_journal_mailbox):
                journal_users[val] = ad_users[val]

        return journal_users

    def _get_ad_groups(self):
        """Gets all the adgroups by calling active directory API.

            Returns:
                Dict    --  A dict with key as adgroup alias name and value as
                                        ADGroup object
        """
        adgroups_map = {}
        for group in search(objectClass='group'):
            adgroup_info = ADGroup()
            # we will use this later
            # object_sid = str(group.objectSid)
            # primary_token = object_sid.split('-')[-1]
            # adgroup_info.primary_token = primary_token
            adgroup_info.samaccount_name = group.sAMAccountName
            adgroup_info.distinguish_name = group.distinguishedName
            try:
                for group_member in group.memberOf:
                    adgroup_info.parent_groups.append(group_member.sAMAccountName)

                    for member in group.member:
                        mailbox_info = MailboxInfo()

                        mailbox_info.alias_name = member.mailNickName
                        mailbox_info.display_name = member.displayName
                        database_dn = member.homeMDB
                        if database_dn is not None:
                            database = (database_dn.split(','))[0].split('=')

                            mailbox_info.database_name = database[1]

                        mailbox_info.smtp_address = member.mail
                        mailbox_info.ldap_home_mbdb = member.homeMDB
                        mailbox_info.ldap_homeserver = member.msExchHomeServerName
                        mailbox_info.legacy_dn = member.legacyExchangeDN
                        mailbox_info.distinguished_name = member.distinguishedName
                        mailbox_info.primary_group_id = member.primaryGroupID
                        adgroup_info.users.append(mailbox_info)
            except AttributeError:
                # when group does not have any member, active directory
                # package throws attribute excpetion. We want to pass in that case
                pass

            adgroups_map[(group.sAMAccountName).lower()] = adgroup_info

        if self.exchange_type == self.ex_type.EXCHANGE_ONLINE_AD.value:
            try:
                self.log.info('Getting online groups')
                online_groups_file = os.path.join(
                    self.host_machine.client_object.install_directory,
                    "online_groups.txt")
                self.log.info('Getting Online groups from powershell. '
                              'Powershell Path  %s', GET_ONLINE_AD_GROUPS)
                prop_dict = {
                    "LoginUser": self.exch_object.exchange_online_user,
                    "LoginPassword": self.exch_object.exchange_online_password,
                    "filepath": online_groups_file
                }
                output = self.host_machine._execute_script(GET_ONLINE_AD_GROUPS, prop_dict)

                if output.exit_code != 0:
                    self.log.error('Getting Online groups from powershell failed')
                    raise Exception("Error message: %s", output.output)

                output = self.host_machine.read_file(online_groups_file)
                users_list = output.split('\n\n')
                group_dict = {}
                for user in users_list:
                    for item in user.split("\n"):
                        item = item.replace(" ", "")
                        if item.count(':') < 1:
                            continue
                        else:
                            list = item.split(":")
                            group_dict[list[0].strip()] = list[1]
                        if list[0] == 'SamAccountName':
                            adgroup_info = ADGroup()
                            adgroup_info.distinguish_name = group_dict['DistinguishedName'].strip()
                            adgroup_info.samaccount_name = group_dict['SamAccountName'].strip()
                            adgroup_info.display_name = group_dict['Alias'].strip()
                            self.log.info('Getting Online group members for group '
                                          '"{0}"'.format(group_dict['Alias']))
                            self.log.info(
                                'Getting Online group members from powershell.'
                                ' Powershell Path %s', GET_MEMBERS_OF_GROUP)
                            group_members_file = os.path.join(
                                self.host_machine.client_object.install_directory,
                                "group_members.txt")
                            prop_dict = {
                                "LoginUser": self.exch_object.exchange_online_user,
                                "LoginPassword": self.exch_object.exchange_online_password,
                                "ExchangeServerDomain": self.domain_name,
                                "filepath": group_members_file,
                                "groupname": group_dict['Alias']
                            }
                            output = self.host_machine._execute_script(
                                GET_MEMBERS_OF_GROUP, prop_dict)
                            if output.exit_code != 0:
                                self.log.error('Getting group Members from powershell failed')
                                raise Exception("Error message: %s", output.output)

                            output = self.host_machine.read_file(group_members_file)
                            users_list = output.split('\n\n')
                            user_dict = {}
                            for group_user in users_list:
                                for group_item in group_user.split("\n"):
                                    group_item = group_item.replace(" ", "")
                                    if group_item.count(':') < 1:
                                        continue
                                    else:
                                        list_members = group_item.split(":")
                                        user_dict[list_members[0]] = list_members[1]
                                    if list_members[0] == 'PrimarySmtpAddress':
                                        mailbox_info = MailboxInfo()
                                        mailbox_info.display_name = (user_dict[
                                                                         "DisplayName"].strip())
                                        mailbox_info.smtp_address = (user_dict[
                                                                         'PrimarySmtpAddress'].strip())
                                        adgroup_info.users.append(mailbox_info)
                            adgroups_map[adgroup_info.display_name.lower()] = adgroup_info

            except Exception as excp:
                self.log.exception("An error occurred while getting groups")
                raise excp

        return adgroups_map

    def refresh(self):
        """Refresh the Active Directory."""

        self._servers = self._get_exchange_servers()
        self._databases = self._get_databases()
        self._all_ad_users = self._get_ad_users()
        self._groups = self._get_ad_groups()
        if (self.exchange_type == self.ex_type.EXCHANGE_ONPREMISE.value or
                self.exchange_type == self.ex_type.HYBRID.value or
                self.ex_object.subclient_name.lower() == self.mb_type.JOURNAL.value):
            self._database_level_journal_mailbox = (self._get_datbaselevel_journalmailbox())
            self._rule_based_journal_mailbox = self._get_rulebased_journalmailbox()
            self._journal_users = self._get_journal_mailboxes()
        self._users = self._get_user_mailboxes()
