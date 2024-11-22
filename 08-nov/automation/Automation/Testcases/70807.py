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
from Application.CloudApps import constants as cloud_apps_constants
from Application.CloudApps.cloud_connector import CloudConnector
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
        self.name = 'Verification of Syntex processes for Onedrive Client'
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.CLOUDCONNECTOR
        self.feature = self.features_list.AUTOMATION
        self.show_to_user = True
        self.client_name = None
        self.M365_Plan = None
        self.cv_cloud_object = None
        self.user = None
        self.browser = None
        self.navigator = None
        self.app_type = None
        self.office365_obj = None
        self.admin_console = None
        self.tcinputs = {
            'M365Plan': None,
            'user': None,
            'AccessNode': None,
            'GlobalAdmin': None,
            'Password': None,
            'tenant_user_name': None,
            'tenant_password': None,
        }

    def _initialize_sdk_objects(self):
        """Initializes the sdk objects after app creation"""

        self.log.info(f'Create client object for: {self.client_name}')
        self._client = self.commcell.clients.get(self.client_name)

        self.log.info(f'Create agent object for: {cloud_apps_constants.ONEDRIVE_AGENT}')
        self._agent = self._client.agents.get(cloud_apps_constants.ONEDRIVE_AGENT)

        self.log.info(f'Create instance object for: {cloud_apps_constants.ONEDRIVE_INSTANCE}')
        self._instance = self._agent.instances.get(cloud_apps_constants.ONEDRIVE_INSTANCE)

        self.log.info(f'Create backupset object for: {cloud_apps_constants.ONEDRIVE_BACKUPSET}')
        self._backupset = self._instance.backupsets.get(cloud_apps_constants.ONEDRIVE_BACKUPSET)

        self.log.info(f'Create sub-client object for: {cloud_apps_constants.ONEDRIVE_SUBCLIENT}')
        self._subclient = self._backupset.subclients.get(cloud_apps_constants.ONEDRIVE_SUBCLIENT)

    def run_and_verify_discovery(self, run=False):

        """Run discovery and verify its completion"""

        if run:
            # Run discovery
            self.log.info(f'Running the discovery')
            self.subclient.run_subclient_discovery()

        # Verify discovery completion or wait for discovery to complete
        self.log.info(f'Waiting until discovery is complete')
        self.cv_cloud_object.cvoperations.wait_until_discovery_is_complete()

        # Verify discovery
        self.log.info(f'Verifying the discovery')
        status, res = self.subclient.verify_discovery_onedrive_for_business_client()
        if status:
            self.log.info("Discovery successful")
        else:
            raise Exception("Discovery is not successful")

    def verify_backup_time(self, retries=3, poll_interval=120):

        """ Verifies the backup time population in user tab """

        while retries > 0:
            # Run discovery
            self.run_and_verify_discovery(run=True)

            user_details, no_of_records = self.subclient.browse_for_content(discovery_type=1)

            if user_details[self.user]['lastBackupTime']:
                self.log.info("Last backup job run time is populated")
                return
            else:
                self.log.info(f"Waiting for {poll_interval / 60} minutes to check the backup status again")
                time.sleep(poll_interval)
            retries -= 1

        raise Exception("Backup time did not populate after %d retries ", retries)

    def setup(self):
        """Setup function of this test case"""
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tcinputs['tenant_user_name'],
                                 self.tcinputs['tenant_password'])
        self.service = HubServices.office365
        self.app_type = O365AppTypes.onedrive
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_office365()
        self.log.info("Creating an object for office365 helper")
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react=True)

        # Create a client
        self.client_name = cloud_apps_constants.ONEDRIVE_CLIENT.format(str(int(time.time())))
        self.office365_obj.create_office365_app_syntex(name=self.client_name,
                                                       global_admin=self.tcinputs['GlobalAdmin'],
                                                       password=self.tcinputs['Password'])
        self.client_name = self.office365_obj.get_app_name()

        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

        # Verify client creation
        if self.commcell.clients.has_client(self.client_name):
            self.log.info("Client is created.")

        self._initialize_sdk_objects()
        self.proxy_client = self.tcinputs['AccessNode']
        self.cv_cloud_object = CloudConnector(self)
        self.cv_cloud_object.cvoperations.cleanup()
        self.M365_Plan = self.tcinputs['M365Plan']
        self.user = self.tcinputs['user']

    def run(self):
        """Run function of this test case"""
        try:
            self.run_and_verify_discovery()

            # Add users to client
            self.log.info(f'Adding user: {self.user} to client')
            self.subclient.add_users_onedrive_for_business_client([self.user], self.M365_Plan)
            self.log.info(f'Added user: {self.user} to client')

            # Run discovery to add user to Microsoft Protection Policy
            self.run_and_verify_discovery(run=True)

            time.sleep(20)

            # Verify backup time population
            self.verify_backup_time()

            # Verify restore
            self.log.info(f'Run inplace restore for user: {self.user}')
            restore_job = self.subclient.in_place_restore_onedrive_syntex(users=[self.user])

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
            self.cv_cloud_object.cvoperations.delete_client(self.client_name)
            # Clear temp
            self.cv_cloud_object.cvoperations.cleanup()

        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')
