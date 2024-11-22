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

    teardown()      --  tears down the things created for running the testcase

"""
import time

from cvpysdk.job import Job

from Application.CloudApps import constants as cloud_apps_constants
from Application.CloudApps.cloud_connector import CloudConnector
from Application.CloudApps.csdb_helper import CSDBHelper
from AutomationUtils import config
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.GovernanceAppsPages.ComplianceSearch import ComplianceSearch, CustomFilter
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.Office365Pages.onedrive import OneDriveContentIndexing
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception

_CONFIG = config.get_config()


class TestCase(CVTestCase):
    """OneDrive Content Indexing: Verification of Preview Generation"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = f'OneDrive Content Indexing: Verification of Preview Generation'
        self._ci_helper = None
        self.ci_jobID = None
        self.app = None
        self.gov_app = None
        self.browser = None
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

            self.client_name = "OD_63131"
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

            self.cvcloud_object = CloudConnector(self)
            self._ci_helper = OneDriveContentIndexing(self.cvcloud_object)
            self.cvcloud_object.cvoperations.cleanup()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def _initialize_browser(self):
        """Initialize Browser"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)

        self.admin_console.login(
            self.inputJSONnode['commcell']['loginUsername'],
            self.inputJSONnode['commcell']['loginPassword'])

        self.app = ComplianceSearch(self.admin_console)
        gov_app = GovernanceApps(self.admin_console)

        navigator = self.admin_console.navigator
        navigator.navigate_to_governance_apps()

        gov_app.select_compliance_search()

    @test_step
    def set_preferences(self):
        """
            Set the Index Server and Search View in Preferences tab
            Set Datatype as OneDrive
        """
        self.app.set_indexserver_and_searchview_preference(
            self.tcinputs['IndexServer'], self.tcinputs['SearchView'])

        self.app.set_datatype(['OneDrive for Business'])
        self.app.click_search_button()

    @test_step
    def validate_preview(self):
        """
            Validates Generated Preview
        """
        try:
            custom_filter = CustomFilter(self.admin_console)
            custom_filter.apply_custom_filters_with_search(
                {"Client name": [self.client_name]})

            preview_data = self.app.get_preview_body()

            self.log.info(preview_data)

            if "Error" in preview_data:
                raise CVTestStepFailure(f"Document preview did not get generated")
        except:
            raise CVTestStepFailure(f"Failed to verify preview")

    @test_step
    def add_users_and_backup(self):
        """
        Adds users into onedrive app and runs a backup

        """
        try:
            self.log.info(f'Waiting until discovery is complete')
            self.cvcloud_object.cvoperations.wait_until_discovery_is_complete()

            self.log.info("Adding users to client")
            self.subclient.add_users_onedrive_for_business_client(self.tcinputs['Users'].split(","), self.tcinputs['O365Plan'])
            self.log.info("Backing up the users")

            # Run initial backup
            backup_level = constants.backup_level.INCREMENTAL.value
            self.log.info('Run initial sub-client level backup')
            backup_job = self.client.backup_all_users_in_client()
            self.cvcloud_object.cvoperations.check_job_status(job=backup_job, backup_level_tc=backup_level)

        except:
            raise CVTestStepFailure(f"OneDrive add users and backup failed")

    @test_step
    def get_content_indexing_job_id(self):
        """Gets ContentIndexing JobID from active jobs"""

        _csdb_helper = CSDBHelper(self)

        time.sleep(60)
        subclient_id = _csdb_helper.get_subclient_id(self.client_name)
        self.ci_jobID = self._ci_helper.get_content_indexing_job_id(self.commcell, int(subclient_id[1]))

        if self.ci_jobID is not None:
            self.log.info(f"Content Indexing Job got triggered successfully with job ID: {str(self.ci_jobID)}")

    @test_step
    def verify_ci_job_complete(self, job_id):
        """
        Verify whether CI job completed successfully

        Args:
            job_id: Job Id of CI job

        """
        ci_job = Job(self.commcell, job_id)
        ci_job.wait_for_completion(timeout=60)

        self.log.info("Job status is: " + ci_job.status)

        if 'Completed' in ci_job.status:
            self.log.info("Ci job has completed successfully")
        else:
            raise CVTestStepFailure(f"Content Indexing Job Failed to complete")

    @test_step
    def delete_client(self):
        """Tear down function of this test case"""
        try:
            self.log.info(f'Test case status: {self.status}')
            # Delete the client if test case is successful
            self.cvcloud_object.cvoperations.delete_client(self.client_name)
            self.cvcloud_object.cvoperations.cleanup()
        except Exception as exception:
            CVTestStepFailure(f'Failed to delete client with exception: {str(exception)}')

    def run(self):
        try:
            self.add_users_and_backup()
            self.get_content_indexing_job_id()
            self.verify_ci_job_complete(self.ci_jobID)
            self._initialize_browser()
            self.set_preferences()
            self.validate_preview()
            self.delete_client()
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
