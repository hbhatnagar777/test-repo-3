# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


""""Main file for executing this test case
TestCase is the only class defined in this file.
TestCase: Class for executing this test case
TestCase:
    __init__()      --  initialize TestCase class
    setup()         --  setup function of this test case
    run()           --  run function of this test case
    tear_down()     --  tear down function of this test case
"""
import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.Exchange.ExchangeMailbox import constants as exchange_constants
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from AutomationUtils.windows_machine import Machine
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.office365_apps import Office365Apps

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name                (str)       --  name of this test case
                applicable_os   (str)       —  applicable os for this test case
                                                            Ex: self.os_list.WINDOWS
                 product            (str)     —  applicable product for this test case
                                                                 Ex: self.products_list.FILESYSTEM
                features             (str)      —  qcconstants feature_list item
                                                             Ex: self.features_list.DATAPROTECTION
                 show_to_user   (bool)    —  test case flag to determine if the test case is
                                                             to be shown to user or not
                      Accept:
                                           True    –   test case will be shown to user from commcell gui
                                           False   –   test case will not be shown to user
                        default: False
                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type
        """
        super(TestCase, self).__init__()
        self.name = "Exchange : Syntex client creation, backup and restore"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.EXCHANGEMB
        self.feature = self.features_list.AUTOMATION
        self.show_to_user = True
        self.tcinputs = {
            'M365Plan': None,
            'user': None,
            'GlobalAdmin': None,
            'Password': None,
            'SubclientName': None,
            'BackupsetName': None,
            'IndexServer': None,
            'ProxyServers': None,
            'JobResultDirectory': None,
            'tenant_user_name': None,
            'tenant_password': None,
        }

    def setup(self):
        """Setup function of this test case"""
        try:
            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open()
            self.log.info("Creating a login object")
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.tcinputs['tenant_user_name'],
                                     self.tcinputs['tenant_password'])
            self.service = HubServices.office365
            self.app_type = O365AppTypes.exchange
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.log.info("Creating an object for office365 helper")
            self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react=True)

            # Create an Exchange client
            self.client_name = exchange_constants.EXCHNAGE_CLIENT_NAME % (self.id)
            self.office365_obj.create_office365_app_syntex(name=self.client_name,
                                                           global_admin=self.tcinputs['GlobalAdmin'],
                                                           password=self.tcinputs['Password'])
            self.client_name = self.office365_obj.get_app_name()

            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

            # Verify client creation
            self.client_name = exchange_constants.EXCHNAGE_CLIENT_NAME % (self.id)
            if self.commcell.clients.has_client(self.client_name):
                self.log.info("Client is created.")

            self.log.info('Creating Exchange Mailbox client object.')
            self.exmbclient_object = ExchangeMailbox(self)
            self.exmbclient_object.client_name = self.client_name
            self._subclient = self.exmbclient_object.cvoperations.subclient
            self.mailboxes_list = [self.tcinputs['user']]
            self.machine = Machine(self.tcinputs['ProxyServers'][0], self.commcell)

        except Exception as exp:
            raise Exception(exp)

    def run_discovery_and_monitor(self):
        # Run discovery
        self.log.info("Running discovery and mailbox monitor")
        self.exmbclient_object.cvoperations.run_admailbox_monitor()
        self.machine.wait_for_process_to_exit(process_name=exchange_constants.AD_MAILBOX_MONITORING_EXE)
        self.log.info('AD Mailbox Discovery process completed successfully')
        self._subclient.refresh()

    def verify_backup_time(self, retries=3, poll_interval=120):

        """ Verifies the backup time population in user tab """

        while retries > 0:
            # Run discovery
            self.run_discovery_and_monitor()

            users = self._subclient.users

            if users[0].get('last_archive_job_ran_time', {}).get('time', None):
                self.log.info("Last backup job run time is populated")
                return
            else:
                self.log.info(f"Waiting for {poll_interval / 60} minutes to check the backup status again")
                time.sleep(poll_interval)
                
            retries -= 1

        raise Exception("Backup time did not populate after %d retries ", retries)

    def run(self):
        """Run function of this test case"""
        try:

            self.log.info("-----------------------CREATE USER ASSOCIATION-----------------------")
            subclient_content = {
                'mailboxNames': self.mailboxes_list,
                'plan_name': self.tcinputs["M365Plan"]
            }
            self._subclient.set_user_assocaition(subclient_content, use_policies=False)

            # Run discovery to add mailbox to Microsoft Protection Policy
            self.run_discovery_and_monitor()

            time.sleep(20)

            # Verify backup time population
            self.verify_backup_time()

            # Verify restore
            self.log.info(f'Run inplace restore for mailbox: {self.mailboxes_list}')
            restore_job = self.exmbclient_object.cvoperations.subclient.restore_in_place_syntex(paths=self.mailboxes_list)

            # Verify restore job completion
            self.log.info("Waiting until the restore job gets completed..")
            if not restore_job.wait_for_completion(timeout=150):
                pending_reason = restore_job.pending_reason
                raise Exception(pending_reason)
            else:
                self.log.info("Restore completed")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            self.log.info(f'Test case status: {self.status}')
            # Delete the client
            self.exmbclient_object.cvoperations.delete_client()

        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')