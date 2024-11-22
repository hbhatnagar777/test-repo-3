# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main Module for setting input variables and creating objects of all other modules.
    This module is imported in any test case.
    You need to create an object of this module in the test case.

ExchangeClient: Class for initializing input variables and other module objects.
"""

from __future__ import unicode_literals
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from ..exchangepowershell_helper import ExchangePowerShell
from .exchangecsdb_helper import ExchangeCSDBHelper
from .msgraph_helper import CVEXMBGraphOps
from .operations import CvOperation
from .activedirectory_helper import DiscoveryOptions
from .exchangelib_helper import ExchangeLib
from .restore_options import Restore
from .cleanup_options import Cleanup
from . import constants


class ExchangeMailbox():
    """Class for initializing input variables and object creation from different modules"""

    def __init__(self, tc_object):
        """Initializes the input variables,logging and creates object from other modules.

                Args:
                    tc_object   --  instance of testcase class

                Returns:
                    object  --  instance of ExchangeMailbox class"""
        self.tc_object = tc_object
        self.log = self.tc_object.log
        self.log.info('logger initialized for Exchange Client')
        self.app_name = self.__class__.__name__
        self._users = None
        self._active_directory = None
        self._exchange_lib = None
        self.csdb = self.tc_object.csdb
        self._restore = None
        self._cleanup = None
        self._exchange_lib = None
        self._active_directory = None
        self._db_helper = None
        self._graph_helper = None
        self._access_node_pwsh : ExchangePowerShell = None
        self.exchange_online_user = ""
        self.exchange_online_password = ""
        self.service_account_user = ""
        self.service_account_password = ""
        self.pst_restore_path = ""
        self.disk_restore_path = ""
        self.populate_tc_inputs(tc_object)
        self.cvoperations = CvOperation(self)

    def __repr__(self):
        """Representation string for the instance of ExchangeMailbox class."""

        return 'ExchangeMailbox class instance for Commcell'

    def populate_tc_inputs(self, tc_object):
        """Initializes all the test case inputs after validation

        Args:
            tc_object (obj)    --    Object of CVTestCase
        Returns:
            None
        Raises:
            Exception:
                if a valid CVTestCase object is not passed.
                if CVTestCase object doesn't have agent initialized"""
        if not isinstance(tc_object, CVTestCase):
            raise Exception(
                "Valid test case object must be passed as argument"
            )
        self.tc_inputs = tc_object.tcinputs
        self.client_name = constants.EXCHNAGE_CLIENT_NAME % (tc_object.id)
        self.commcell = tc_object.commcell

        # proxies, indexserver, shared job result directory are
        # mandatory for all exchange cases

        if isinstance(tc_object.tcinputs.get('ProxyServers'), list):
            self.proxies = tc_object.tcinputs.get('ProxyServers')
            self.server_name = self.proxies[0]
        else:
            raise Exception("Please provide proxies details to run Testcase")

        self.index_server = tc_object.tcinputs.get('IndexServer')
        self.job_results_directory = tc_object.tcinputs.get('JobResultDirectory', "")
        self.subclient_name = tc_object.tcinputs.get('SubclientName')
        self.backupset_name = tc_object.tcinputs.get('BackupsetName')

        self.server_plan = tc_object.tcinputs.get('ServerPlanName', "")
        # Recall service is required for cleanup cases
        self.recall_service = tc_object.tcinputs.get('RecallService', "")
        self.service_account_dict = tc_object.tcinputs.get('ServiceAccountDetails', {})

        # requires this tc input when we want to do import pst
        # this is only applicable for on premise
        self.pst_path = tc_object.tcinputs.get('PSTPath')

        # TCinputs for ContentStore Mailbox backupset
        # requires this path only for content store testcases
        # this path should contain content store mailbox to copy

        self.contentstore_mailbox_path = tc_object.tcinputs.get('ContentStoreMailboxPath')
        self.content_store_mail_server = tc_object.tcinputs.get('ContentStoreServer')
        self.contact = tc_object.tcinputs.get('ContactDisplayName')
        self.contactid = tc_object.tcinputs.get('ContactEmailID')

        # SMTPDashboard details

        self.smtpdashboard_username = tc_object.tcinputs.get('SMTPDashboardUserName')
        self.smtpdashboard_password = tc_object.tcinputs.get('SMTPDashboardPassword')
        self.smtpdashboard_port = tc_object.tcinputs.get('SMTPDashboardPort')
        self.contact = tc_object.tcinputs.get('ContactDisplayName')
        self.contactid = tc_object.tcinputs.get('ContactEmailID')

        # adminconsole automation input details

        self.plan_name = tc_object.tcinputs.get('plan_name')
        self.exchangeplan = tc_object.tcinputs.get('ExchangePlan')

        # Exchange details
        self.environment_type = tc_object.tcinputs.get('EnvironmentType', 1)
        self.exchange_server = tc_object.tcinputs.get('ExchangeServerName', ["."])
        self.azure_app_id = tc_object.tcinputs.get('azureAppKeyID', "")
        self.azure_app_key_secret = tc_object.tcinputs.get('azureAppKeySecret', "")
        self.azure_tenant_name = tc_object.tcinputs.get('azureTenantName', "")
        self.domain_name = tc_object.tcinputs.get('DomainName')
        self.domain_username = tc_object.tcinputs.get('DomainUserName')
        self.domain_userpassword = tc_object.tcinputs.get('DomainUserPassword')
        self.exchange_cas_server = tc_object.tcinputs.get('ExchangeCASServer')
        self.pst_restore_path = tc_object.tcinputs.get("PSTRestorePath")
        self.disk_restore_path = tc_object.tcinputs.get("DiskRestorePath")

        for account in tc_object.tcinputs.get('ServiceAccountDetails', []):
            if account['ServiceType'] == 2:
                self.exchange_online_user = account['Username']
                self.exchange_online_password = account['Password']
            else:
                self.service_account_user = account['Username']
                self.service_account_password = account['Password']

    @property
    def active_directory(self):
        """Returns the instance of the DiscoveryOptions class."""
        self._active_directory = DiscoveryOptions(self)
        return self._active_directory

    @property
    def csdb_helper(self):
        """Returns the instance of ExchangeCSDBHelper"""
        return ExchangeCSDBHelper(self) if self._db_helper is None else self._db_helper

    @property
    def exchange_lib(self):
        """Returns the instance of the ExchangeLib class."""
        self._exchange_lib = ExchangeLib(self)
        return self._exchange_lib

    @property
    def graph_helper(self):
        """Returns the instance of CV EXMB Graph Operations class"""
        if not self._graph_helper:
            self._graph_helper = CVEXMBGraphOps(self)
        return self._graph_helper

    @property
    def cleanup(self):
        """Returns the instance of the Cleanup class."""
        self._cleanup = Cleanup(self)
        return self._cleanup

    @property
    def restore(self):
        """Returns the instance of the Restore class."""
        self._restore = Restore(self)
        return self._restore

    @property
    def users(self):
        """Returns the users."""

        return self._users

    @users.setter
    def users(self, value):
        """Sets the users email adddress to emails users

        Args:
            value     (list) -list of users emails need to be set"""

        self._users = value

    @property
    def exchange_type(self):
        """Returns the exchange type based on service type."""
        mb_type = constants.mailbox_type
        if self.subclient_name.lower() == mb_type.USER.value:
            return self.environment_type
        return None

    @property
    def backupset_type(self):
        """Returns the backup set type for User/ Journal/ ContentStore MBX"""
        bkpset_type = constants.BACKUPSET_IDS
        return bkpset_type[self.backupset_name.lower()]

    @property
    def mailbox_type(self):
        """Returns the mailbox type."""
        mb_type = constants.mailbox_type
        if self.subclient_name.lower() == mb_type.USER.value:
            return mb_type.USER.name
        elif self.subclient_name.lower() == mb_type.JOURNAL.value:
            return mb_type.JOURNAL.name
        elif self.subclient_name.lower() == mb_type.CONTENTSTORE.value:
            return mb_type.CONTENTSTORE.name
        else:
            raise Exception("Subclient was not created")

    @property
    def smtp_mailbox_path(self):
        """Returns the Smtp mailbox path"""
        if self.content_store_mail_server is None:
            raise Exception("ContentStore mail server is required "
                            "to get smtp mailbox path")
        self.windows_machine = Machine(self.content_store_mail_server, self.commcell)
        return self.windows_machine.get_registry_value(r"iDataAgent",
                                                       "strSmtpMailboxPath")

    @property
    def get_job_results_dir(self):
        """
        Get the full job results directory
        Note: Make sure Test case object is initialized with client and subclient objects
              before calling this function
        """
        base_path = self.tc_object.client.job_results_directory

        if not base_path:
            proxy_client = self.commcell.clients.get(self.server_name)
            base_path = proxy_client.job_results_directory

        self.windows_machine = Machine(self.server_name, self.commcell)
        full_path = self.windows_machine.join_path(base_path, "CV_JobResults", "iDataAgent",
                                                   "MS Exchange Virtual Agent",
                                                   str(self.commcell.commcell_id),
                                                   str(self.tc_object.subclient.subclient_id))

        self.log.info("Job results dir: %s", full_path)
        return full_path

    @property
    def access_node_powershell(self):
        """Access the Powershell on access node through this property"""
        if self._access_node_pwsh is None:
            self._access_node_pwsh = ExchangePowerShell(ex_object=self, cas_server_name=self.exchange_cas_server,
                                                        exchange_server=self.exchange_server,
                                                        exchange_adminname=self.service_account_user,
                                                        exchange_adminpwd=self.service_account_password,
                                                        server_name=self.server_name, domain_name=self.domain_name)
        return self._access_node_pwsh