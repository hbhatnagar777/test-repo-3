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

    setup()                     --  Initialize TestCase attributes
    create_inventory()          --  Creates Activate Inventory
    create_plan()               --  Creates FSO DC Plan
    navigate_to_cloud_apps()    --  Navigate to the cloud apps page in FSO
    select_data_source()        --  Select the data source added in the previous test step
    fetch_metadata_create_db()  --  Fetch the meta data from cloud app and dump it into the db
    perform_cleanup()           --  Perform cleanup related tasks
    run()                       --  Run function of this test case
    tear_down()                 --  Tear Down tasks
"""
from Application.CloudStorage.azure_helper import AzureHelper
from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.credential_manager import CredentialManager
from Web.AdminConsole.GovernanceAppsPages.FileServerLookup import ObjectStorageClient
from Web.AdminConsole.GovernanceAppsPages.SensitiveDataAnalysisProjectDetails import SensitiveDataAnalysisProjectDetails

from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.AdminConsole.Helper.FSOHelper import FSO
from Web.AdminConsole.Helper.GDPRHelper import GDPR

from dynamicindex.utils.activateutils import ActivateUtils
import dynamicindex.utils.constants as cs

from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure

CONFIG = get_config().DynamicIndex.Activate.Azure


class TestCase(CVTestCase):
    """FSO basic acceptance test for Azure Cloud App"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "FSO basic acceptance test for Azure Cloud App"
        self.activate_utils = ActivateUtils()
        self.tcinputs = {
            "IndexServerName": None,
            "DataGeneratorDir": None,
            "AccessNode": None,
            "DatabasePath": None

        }
        # Test Case constants
        self.user_password = None
        self.username = None
        self.datasource_name = None
        self.cloud_app_type = None
        self.inventory_name = None
        self.plan_name = None
        self.object_storage_client_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_helper = None
        self.fso_helper = None
        self.credential_manager = None
        self.credential_name = None
        self.object_storage = None
        self.azure_helper = None
        self.sdg_project_details = None
        self.container_name = None
        self.error_dict = {}

    def setup(self):
        """Testcase Setup Method"""
        try:
            self.user_password = self.inputJSONnode['commcell']['commcellPassword']
            self.username = self.commcell.commcell_username
            self.cloud_app_type = cs.AZURE
            self.datasource_name = f"{self.id}_datasource"
            self.inventory_name = f"{self.id}_inventory"
            self.plan_name = f"{self.id}_plan"
            self.object_storage_client_name = f'{self.id}_object_storage_{self.cloud_app_type.lower()}'
            self.credential_name = f'{self.id}_credentials'
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=self.commcell.commcell_username,
                                              password=self.user_password)
            self.admin_console.login(username=self.username,
                                     password=self.user_password)
            self.gdpr_helper = GDPR(self.admin_console)
            self.fso_helper = FSO(self.admin_console, self.commcell, self.csdb)
            self.credential_manager = CredentialManager(self.admin_console)
            self.fso_helper.data_source_name = self.object_storage_client_name
            self.container_name = CONFIG.ContainerName
            self.object_storage = ObjectStorageClient(self.admin_console, self.cloud_app_type, self.container_name, CONFIG)
            self.azure_helper = AzureHelper(CONFIG.AccountName, CONFIG.AccessKey)
            self.sdg_project_details = SensitiveDataAnalysisProjectDetails(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def create_inventory(self):
        """
        Create Inventory With Given Nameserver
        """
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_helper.inventory_details_obj.select_inventory_manager()
        if not self.gdpr_helper.inventory_details_obj.search_for_inventory(self.inventory_name):
            self.gdpr_helper.inventory_details_obj.add_inventory(self.inventory_name, self.tcinputs['IndexServerName'])

    @test_step
    def create_plan(self):
        """
        Create Data Classification Plan
        """
        self.admin_console.navigator.navigate_to_plan()
        self.gdpr_helper.plans_obj.create_data_classification_plan(
            self.plan_name, self.tcinputs['IndexServerName'],
            content_search=False, content_analysis=False, target_app='fso')

    @test_step
    def create_credential(self):
        """
        Create Credential for Cloud Storage through Credential Manager
        """
        self.admin_console.navigator.navigate_to_credential_manager()
        self.admin_console.wait_for_completion()
        self.credential_manager.add_credential(
            account_type='Cloud Account',
            credential_name=self.credential_name,
            username=CONFIG.AccountName,
            password=CONFIG.AccessKey,
            owner=None,
            description=f'{self.credential_name} TEST Credentials',
            user_or_group=None,
            vendor_type=cs.VENDOR_TYPE[self.cloud_app_type],
            authentication_type=cs.AUTH_TYPE_ACCESS_SECRET_KEYS_AZURE)

    @test_step
    def navigate_to_cloud_apps(self):
        """
            Navigates to the cloud apps page
        """
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_helper.inventory_details_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.select_fso_grid_tab(self.admin_console.props['label.objectStorage'])
        self.fso_helper.fso_obj.add_client(self.inventory_name, self.plan_name,
                                           storage_type=self.admin_console.props['label.objectStorage'])
        self.fso_helper.file_server_lookup.select_inventory(self.inventory_name)

    @test_step
    def select_data_source(self):
        """
        Selects the data source
        """
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_helper.inventory_details_obj.select_file_storage_optimization()
        self.fso_helper.fso_obj.select_fso_grid_tab(self.admin_console.props['label.objectStorage'])
        self.fso_helper.fso_obj.select_details_action(self.object_storage_client_name)

        assert self.fso_helper.fso_client_details.check_if_datasource_exists(
            self.datasource_name), "Added datasource not found"

        self.fso_helper.fso_client_details.select_datasource(self.datasource_name)

    @test_step
    def fetch_metadata_create_db(self):
        """
        Fetches the file meta data from the object storage
        """
        meta_data = self.azure_helper.fetch_file_metadata(self.container_name)
        if not meta_data:
            raise CVTestStepFailure("meta_data result is empty")
        self.activate_utils.create_fso_metadata_db('', self.tcinputs['DatabasePath'], target_machine_name='',
                                                   track_dir_stats=False, meta_data=meta_data)

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.gdpr_helper.cleanup(inventory_name=self.inventory_name, plan_name=self.plan_name)
        self.fso_helper.fso_cleanup(client_name=self.object_storage_client_name, datasource_name=self.datasource_name,
                                    pseudo_client_name=self.object_storage_client_name, dir_path=None, cloud_apps=True,
                                    credential_name=self.credential_name)

        self.gdpr_helper.inventory_details_obj.delete_inventory(self.inventory_name)

    def run(self):
        """
        Main function for test case execution
        """
        try:

            self.perform_cleanup()
            self.create_plan()
            self.create_inventory()
            self.create_credential()
            self.activate_utils.run_data_generator(self.tcinputs["DataGeneratorDir"], self.cloud_app_type.title())
            self.navigate_to_cloud_apps()
            self.object_storage.add_data_source(object_storage_client=self.object_storage_client_name,
                                                datasource_name=self.datasource_name,
                                                plan_name=self.plan_name, credential_name=self.credential_name,
                                                access_node=self.tcinputs['AccessNode'])
            self.sdg_project_details.wait_for_data_source_status_completion(self.datasource_name)
            self.fetch_metadata_create_db()
            self.fso_helper.create_sqlite_db_connection(self.tcinputs['DatabasePath'])
            self.select_data_source()

            self.fso_helper.fso_data_source_discover.load_fso_dashboard(cloud_app_type=self.cloud_app_type)

            try:
                self.fso_helper.review_size_distribution_dashboard(cloud_apps=True)
            except Exception as exp:
                self.error_dict[cs.SIZE_DISTRIBUTION_DASHBOARD] = str(exp)
                self.status = constants.FAILED

            try:
                self.fso_helper.review_file_duplicates_dashboard()
            except Exception as exp:
                self.error_dict[cs.DUPLICATES_DASHBOARD] = str(exp)
                self.status = constants.FAILED

            try:
                self.fso_helper.verify_fso_time_data(cloud_app_type=self.cloud_app_type)
            except Exception as exp:
                self.error_dict[cs.TIME_DATA] = str(exp)
                self.status = constants.FAILED

            if self.status == constants.FAILED:
                raise CVTestStepFailure(str(self.error_dict))

        except Exception as exp:
            if len(self.error_dict) > 0:
                self.log.info("************Following Error Occurred in Automation************")
                for key, value in self.error_dict.items():
                    self.log.info("%s %s" % (key, value))
                self.log.info("**************************************************************")
            handle_testcase_exception(self, exp)

    def tear_down(self):
        try:
            if self.status != constants.FAILED:
                self.perform_cleanup()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
