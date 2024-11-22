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

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

"""

import time

from Application.CloudApps import constants as cloud_apps_constants
from Application.CloudApps.cloud_connector import CloudConnector
from AutomationUtils import config
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Office365Pages.onedrive import OneDrive
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception

_CONFIG = config.get_config()


class TestCase(CVTestCase):
    """OneDrive Content Indexing: Basic verification of CI job triggering
    and completing when CI job is triggered manually"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = (f'OneDrive Content Indexing: Basic verification of CI job triggering and completing '
                     f'when CI job is triggered manually')
        self.browser = None
        self.backup_jobID = None
        self.client_name = None
        self.cvcloud_object = None
        self.users = None
        self.o365_plan = None
        self.navigator = None
        self.admin_console = None
        self.mssql = None
        self.tcinputs = {
            'ServerPlanName': None,
            'IndexServer': None,
            'AccessNodes': None,
            'O365Plan': None,
            'Users': None
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

    def setup(self):
        """ Initial configuration for the test case. """
        try:
            self._tcinputs['application_id'] = _CONFIG.Azure.CiApp.ApplicationID
            self._tcinputs['azure_directory_id'] = _CONFIG.Azure.CiApp.DirectoryID
            self._tcinputs['application_key_value'] = _CONFIG.Azure.CiApp.ApplicationSecret

            self.client_name = "OD_63129"
            self.log.info(f'Checking if OneDrive client : {self.client_name} already exists')
            if self.commcell.clients.has_client(self.client_name):
                self.log.info(f'OneDrive client : {self.client_name} already exists, deleting the client')
                self.commcell.clients.delete(self.client_name)
                self.log.info(f'Successfully deleted OneDrive client : {self.client_name} ')
            else:
                self.log.info(f'OneDrive client : {self.client_name} does not exists')
            self.log.info(f'Creating new OneDrive client : {self.client_name}')
            self.commcell.clients.add_onedrive_for_business_client(client_name=self.client_name,
                                                         server_plan=self.tcinputs['ServerPlanName'],
                                                         azure_app_id=self._tcinputs['application_id'],
                                                         azure_app_key_id=self._tcinputs['application_key_value'],
                                                         azure_directory_id=self._tcinputs['azure_directory_id'],
                                                         **{
                                                             'index_server': self.tcinputs.get('IndexServer'),
                                                             'access_nodes_list': self.tcinputs.get('AccessNodes')
                                                         })

            self._initialize_sdk_objects()

            self.users = self.tcinputs['Users'].split(",")
            self.o365_plan = self.tcinputs['O365Plan']
            self.cvcloud_object = CloudConnector(self)
            self.cvcloud_object.cvoperations.cleanup()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def _initialize_browser(self):
        """Initializes browser and required constants"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)

        self.admin_console.login(
            self.inputJSONnode['commcell']['loginUsername'],
            self.inputJSONnode['commcell']['loginPassword'])

        self.log.info("Creating an object for office365 helper")
        self.tcinputs['office_app_type'] = OneDrive.AppType.one_drive_for_business

        self.navigator = self.admin_console.navigator
        self.navigator.navigate_to_office365()

    @test_step
    def add_users_and_backup(self):
        """
        Adds users into onedrive app and runs a backup

        """
        try:
            self.log.info(f'Waiting until discovery is complete')
            self.cvcloud_object.cvoperations.wait_until_discovery_is_complete()

            self.log.info("Adding users to client")
            self.subclient.add_users_onedrive_for_business_client(self.users, self.o365_plan)
            self.log.info("Backing up the users")

            # Run initial backup
            backup_level = constants.backup_level.INCREMENTAL.value
            self.log.info('Run initial sub-client level backup')
            backup_job = self.client.backup_all_users_in_client()
            self.cvcloud_object.cvoperations.check_job_status(job=backup_job, backup_level_tc=backup_level)

            self.backup_jobID = backup_job.job_id
        except:
            raise CVTestStepFailure(f"OneDrive add users and backup failed")

    @test_step
    def select_app_run_ci(self):
        """Runs CI Job manually"""
        onedrive = OneDrive(self.tcinputs, self.admin_console)
        onedrive.run_ci_job(self.client_name)

    @test_step
    def delete_client(self):
        """Deletes the onedrive app"""
        try:
            self.cvcloud_object.cvoperations.delete_client(self.client_name)
            self.cvcloud_object.cvoperations.cleanup()
        except Exception as exception:
            CVTestStepFailure(f'Failed to delete client with exception: {str(exception)}')

    def run(self):
        try:
            self.add_users_and_backup()
            self._initialize_browser()
            self.select_app_run_ci()
            self.delete_client()
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            self.log.info(f'Test case status: {self.status}')
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
