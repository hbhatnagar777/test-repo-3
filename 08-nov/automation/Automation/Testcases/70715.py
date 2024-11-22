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

from AutomationUtils import constants
import time
from Application.Sharepoint import sharepointconstants as sharepoint_constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVTestCaseInitFailure
from Application.Sharepoint.sharepoint_online import SharePointOnline
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
        self.name = "Sharepoint : Syntex client creation, backup and restore"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.SHAREPOINT
        self.feature = self.features_list.AUTOMATION
        self.show_to_user = True
        self.M365_Plan = None
        self.site_url = None
        self.client_name = None
        self.tcinputs = {
            'M365Plan': None,
            'SiteUrl': None,
            'AccessNode': None,
            'GlobalAdmin': None,
            'Password': None,
            'tenant_user_name': None,
            'tenant_password': None,
            'Name': None
        }

    def init_tc(self):
        """Initialization function for the test case."""
        try:
            self.log.info('Creating SharePoint client object.')
            self.sp_client_object = SharePointOnline(self)
            self.sp_client_object.machine_name = self.tcinputs['AccessNode']
            self.log.info('SharePoint client object created.')
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def run_and_verify_discovery(self, run=False):

        if run:
            # Run discovery
            self.log.info(f'Running the discovery')
            self.sp_client_object.cvoperations.run_manual_discovery(wait_for_discovery_to_complete=True)

        # Verify discovery
        self.log.info(f'Verifying the discovery')
        self.sp_client_object.cvoperations.wait_for_process_to_complete(
            machine_name=self.sp_client_object.machine_name,
            process_name=sharepoint_constants.MANUAL_DISCOVERY_PROCESS_NAME,
            time_out=5400,
            poll_interval=60)

    def verify_backup_time(self, retries=3, poll_interval=120):

        """ Verifies the backup time population in user tab """

        while retries > 0:
            # Run discovery
            self.run_and_verify_discovery(run=True)
            site_details = self.sp_client_object.cvoperations.get_sites_user_account_info([self.site_url])
            if site_details[self.site_url].get('lastBackupJobRanTime', {}).get('time', None):
                self.log.info("Last backup job run time is populated")
                return
            else:
                self.log.info(f"Waiting for {poll_interval/60} minutes to check the backup status again")
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
        self.app_type = O365AppTypes.sharepoint
        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_office365()
        self.log.info("Creating an object for office365 helper")
        self.office365_obj = Office365Apps(self.admin_console, self.app_type, is_react=True)

        # Create a Sharepoint client
        self.client_name = self.tcinputs['Name']
        self.office365_obj.create_office365_app_syntex(name=self.client_name,
                                                       global_admin=self.tcinputs['GlobalAdmin'],
                                                       password=self.tcinputs['Password'])
        self.client_name = self.office365_obj.get_app_name()

        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

        # Verify client creation
        if self.commcell.clients.has_client(self.client_name):
            self.log.info("Client is created.")

        self.init_tc()
        self.site_url = self.tcinputs['SiteUrl']
        self.M365_Plan = self.tcinputs['M365Plan']
        self.sp_client_object.site_url = self.tcinputs['SiteUrl']
        self.sp_client_object.office_365_plan = [(self.tcinputs.get('M365Plan'),
                                                  int(self.sp_client_object.cvoperations.get_plan_obj
                                                      (self.tcinputs.get('M365Plan')).plan_id))]
        self.sp_client_object.pseudo_client_name = self.client_name

    def run(self):
        """Run function of this test case"""
        try:
            # Verify auto discovery
            self.run_and_verify_discovery()

            # Add sites to backup
            self.log.info(f'Adding site: {self.site_url} to client')
            self.sp_client_object.cvoperations.browse_for_sp_sites()
            self.sp_client_object.cvoperations.associate_content_for_backup(
                self.sp_client_object.office_365_plan[0][1])

            self.log.info(f'Added site: {self.site_url} to client')
            site_details = self.sp_client_object.cvoperations.get_sites_user_account_info([self.site_url])

            # Run discovery to add user to Microsoft Protection Policy
            self.run_and_verify_discovery(run=True)

            time.sleep(20)

            # Verify backup time population
            self.verify_backup_time()

            # Verify restore
            self.log.info(f'Run inplace restore for site: {self.site_url}')
            restore_job = self.sp_client_object.cvoperations.subclient.restore_in_place_syntex(paths=[self.site_url])

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
            self.log.info("Deleting the pseudo client ")
            self.sp_client_object.cvoperations.delete_share_point_pseudo_client(client_name=self.client_name)

        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')