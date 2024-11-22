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
    __init__()                  --  Initialize TestCase class
    setup()                     --  Initialize TestCase attributes
    create_inventory()          --  Creates Activate Inventory
    create_plan()               --  Creates SDG DC Plan
    create_credential()         --  Create Credential for Cloud Storage through Credential Manager
    add_sdg_proj()              --  Creates the SDG project
    add_data_source()           --  Adds an Object Storage data source to the SDG project
    verify_data_source()        --  Selects the data source and verifies the sensitive files and the entities in
                                    each sensitive file.
    perform_cleanup()           --  Perform cleanup related tasks
    run()                       --  Run function of this test case
    tear_down()                 --  Tear Down tasks
"""

from Application.CloudStorage.s3_helper import S3Helper
from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.utils.activateutils import ActivateUtils
from Web.AdminConsole.Helper.FSOHelper import FSO
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.AdminConsolePages.credential_manager import CredentialManager
from Web.AdminConsole.GovernanceAppsPages.FileServerLookup import ObjectStorageClient
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import Browser, BrowserFactory
import dynamicindex.utils.constants as cs

CONFIG = get_config().DynamicIndex.Activate.AWS


class TestCase(CVTestCase):
    """SDG basic acceptance test for AWS Cloud App"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "SDG basic acceptance test for AWS Cloud App"
        self.activate_utils = ActivateUtils()
        self.tcinputs = {
            "IndexServerName": None,
            "AccessNode": None,
            "ContentAnalyzer": None,
            "DataGeneratorDir": None
        }
        # Test Case constants
        self.user_password = None
        self.username = None
        self.datasource_name = None
        self.cloud_app_type = None
        self.inventory_name = None
        self.plan_name = None
        self.project_name = None
        self.object_storage_client_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_helper = None
        self.fso_helper = None
        self.credential_manager = None
        self.credential_name = None
        self.object_storage = None
        self.s3helper = None
        self.error_dict = {}
        self.entities_list = None

    def setup(self):
        """Testcase Setup Method"""
        try:
            self.user_password = self.inputJSONnode['commcell']['commcellPassword']
            self.username = self.commcell.commcell_username
            self.cloud_app_type = cs.AWS
            self.datasource_name = f"{self.id}_datasource"
            self.inventory_name = f"{self.id}_inventory"
            self.plan_name = f"{self.id}_plan"
            self.project_name = f"{self.id}_project"
            self.object_storage_client_name = f'{self.id}_object_storage_{self.cloud_app_type.lower()}'
            self.credential_name = f'{self.id}_credentials'
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser,
                self.commcell.webconsole_hostname,
                username=self.commcell.commcell_username,
                password=self.user_password)
            self.admin_console.login(username=self.username,
                                     password=self.user_password)
            self.gdpr_helper = GDPR(self.admin_console)
            self.entities_list = [cs.ENTITY_EMAIL, cs.ENTITY_IP]
            self.gdpr_helper.testdata_path = None
            self.gdpr_helper.entities_list = self.entities_list
            self.gdpr_helper.data_source_name = self.datasource_name
            self.fso_helper = FSO(self.admin_console, self.commcell, self.csdb)
            self.credential_manager = CredentialManager(self.admin_console)
            self.object_storage = ObjectStorageClient(
                self.admin_console, self.cloud_app_type, CONFIG)
            self.s3helper = S3Helper(self)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def create_inventory(self):
        """
        Creates an Inventory
        """
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_helper.inventory_details_obj.select_inventory_manager()
        self.gdpr_helper.inventory_details_obj.add_inventory(
            self.inventory_name, self.tcinputs['IndexServerName'])

    @test_step
    def create_plan(self):
        """
        Create SDG Data Classification Plan
        """
        self.admin_console.navigator.navigate_to_plan()
        self.gdpr_helper.plans_obj.create_data_classification_plan(
            self.plan_name, self.tcinputs['IndexServerName'],
            self.tcinputs['ContentAnalyzer'], self.entities_list)

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
            authentication_type=cs.AUTH_TYPE_ACCESS_SECRET_KEYS_AWS)

    @test_step
    def add_data_source(self):
        """Adds an Object Storage data source to the SDG project"""
        self.gdpr_helper.file_server_lookup_obj.select_add_data_source(
            data_source_type=cs.OBJECT_STORAGE)
        self.object_storage.create_client(
            self.object_storage_client_name,
            self.credential_name,
            self.tcinputs['AccessNode'])
        self.object_storage.add_data_source(
            object_storage_client=self.object_storage_client_name,
            datasource_name=self.datasource_name,
            plan_name=self.plan_name,
            credential_name=self.credential_name,
            access_node=self.tcinputs['AccessNode'],
            inventory_name = self.inventory_name)
        self.gdpr_helper.file_server_lookup_obj.wait_for_data_source_status_completion(
            self.datasource_name)

    @test_step
    def add_sdg_project(self):
        """Creates a SDG Project and adds a File Server to it."""
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_helper.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_helper.file_server_lookup_obj.add_project(
            self.project_name, self.plan_name)

    @test_step
    def verify_data_source(self):
        """
        Selects the data source and verifies the sensitive files and the entities in each sensitive file
        """
        s3_session = self.s3helper.create_session_s3(
            CONFIG.AccountName, CONFIG.AccessKey, CONFIG.BucketRegion)
        bucket_name = self.s3helper.search_bucket_by_prefix(
            s3_session, 'activate-test-')
        meta_data = self.s3helper.fetch_file_metadata(
            s3_session, CONFIG.ContainerName)
        assert meta_data, "Metadata result is None"
        self.gdpr_helper.testdata_path = meta_data[0][cs.FSO_METADATA_FIELD_PARENT_DIR]
        self.gdpr_helper.create_sqlite_db_connection(
            f"{self.tcinputs['DataGeneratorDir']}\\{cs.ENTITY_TABLE_NAME}.db")
        self.gdpr_helper.file_server_lookup_obj.select_data_source(
            self.datasource_name)
        self.gdpr_helper.verify_data_source_discover()
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_helper.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_helper.file_server_lookup_obj.navigate_to_project_details(
            self.project_name)
        self.gdpr_helper.file_server_lookup_obj.select_data_source(
            self.datasource_name)
        self.gdpr_helper.data_source_discover_obj.select_review()
        folder_path = f"{bucket_name}/{self.gdpr_helper.testdata_path}"
        folder_path = folder_path.replace("\\", "/")
        self.gdpr_helper.verify_data_source_review(
            folder_path=folder_path,
            unique=False)

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.gdpr_helper.cleanup(
            self.project_name,
            self.inventory_name,
            self.plan_name,
            pseudo_client_name=self.object_storage_client_name,
            credential_name=self.credential_name)

    def run(self):
        """
        Main function for test case execution
        """
        try:

            self.perform_cleanup()
            self.create_plan()
            self.create_inventory()
            self.create_credential()
            self.activate_utils.run_data_generator(
                self.tcinputs["DataGeneratorDir"], self.cloud_app_type)
            self.add_sdg_project()
            self.add_data_source()
            self.verify_data_source()

        except Exception as exp:
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