import time

from cvpysdk.job import Job

from Application.CloudApps import constants as cloud_apps_constants
from Application.CloudApps.cloud_connector import CloudConnector
from Application.CloudApps.csdb_helper import CSDBHelper
from AutomationUtils import config
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Office365Pages.onedrive import OneDriveContentIndexing
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception

_CONFIG = config.get_config()


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.backup_count = None
        self.ci_count = None
        self.name = "OneDrive Content Indexing: Verification of Size Filters"
        self.backup_jobID = None
        self.ci_jobID = None
        self.client_name = None
        self.cvcloud_object = None
        self.users = None
        self.o365_plan = None
        self._csdb_helper = None
        self._ci_helper = None
        self.mssql = None
        self.admin_console = None
        self.plans = None
        self.plan_details = None
        self.custom_size = None
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
        self._tcinputs['application_id'] = _CONFIG.Azure.CiApp.ApplicationID
        self._tcinputs['azure_directory_id'] = _CONFIG.Azure.CiApp.DirectoryID
        self._tcinputs['application_key_value'] = _CONFIG.Azure.CiApp.ApplicationSecret

        self.client_name = "OD_63132"
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

        self.custom_size = self.tcinputs['FilterSize']

        server_name = self.tcinputs['SQLServerName']
        user = self.tcinputs['SQLUsername']
        password = self.tcinputs['SQLPassword']
        self.mssql = MSSQL(
            server_name,
            user,
            password,
            'CommServ',
            as_dict=False)

        self._csdb_helper = CSDBHelper(self)

        self.cvcloud_object = CloudConnector(self)
        self._ci_helper = OneDriveContentIndexing(self.cvcloud_object)
        self.cvcloud_object.cvoperations.cleanup()

    @test_step
    def _initialize_browser(self):
        """Initializes browser"""
        browser = BrowserFactory().create_browser_object()
        browser.open()
        self.admin_console = AdminConsole(
            browser, self.commcell.webconsole_hostname)

        self.admin_console.login(
            self.inputJSONnode['commcell']['loginUsername'],
            self.inputJSONnode['commcell']['loginPassword'])

        self.plans = Plans(self.admin_console)
        self.plan_details = PlanDetails(self.admin_console)

    @test_step
    def get_content_indexing_job_id(self):
        """Gets ContentIndexing JobID from active jobs"""
        time.sleep(60)
        subclient_id = self._csdb_helper.get_subclient_id(self.client_name)
        self.ci_jobID = self._ci_helper.get_content_indexing_job_id(self.commcell, int(subclient_id[1]))

        if self.ci_jobID is not None:
            self.log.info(f"Content Indexing Job got triggered successfully with job ID: {str(self.ci_jobID)}")

    @test_step
    def add_users_and_backup(self):
        """Creates OneDrive app, adds users and runs backup"""
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
    def verify_content_index_count(self, job_id):
        """
        Query Index Server wrt Job Id to get content indexing status

        Args:
            job_id: Job Id of backup job

        """
        try:
            solr_details = self._ci_helper.get_ci_details_from_index(self._csdb_helper, self.mssql, job_id)
            self.log.info(f"Documents in solr are: {solr_details}")

            processed_files = solr_details["Success"] + solr_details["Failed"] + solr_details["Skipped"]

            if processed_files != self.backup_count:
                raise CVTestStepFailure(f'Solr returned {processed_files} content indexed documents '
                                        f'Backup contains {self.backup_count} documents '
                                        f'Count mismatch')
        except Exception as exception:
            raise CVTestStepFailure(f'Failed to verify content indexing count with exception {str(exception)}')

    @test_step
    def set_ci_filters(self, size_filter):
        """
        Navigates to plan page and selects office 365 plan,
        edits content indexing settings to change the max file size filter

        Args:
                size_filter: The filter size to be used to edit ci settings

        """
        self.plans.select_plan(self.o365_plan)
        self.plan_details.edit_content_indexing_maxsize(size_filter)

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
            self._initialize_browser()
            self.set_ci_filters(self.custom_size)
            self.add_users_and_backup()
            self.backup_count = self._ci_helper.get_document_count_in_index(self._csdb_helper, self.mssql,
                                                                            self.backup_jobID)
            self.get_content_indexing_job_id()
            self.verify_ci_job_complete(self.ci_jobID)
            self.verify_content_index_count(self.backup_jobID)
            self.delete_client()

        except Exception as exception:
            handle_testcase_exception(self, exception)
        finally:
            self.log.info(f'Test case status: {self.status}')
