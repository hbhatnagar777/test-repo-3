# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                          --  initialize TestCase class

    setup()                             --  sets up the variables required for running the testcase

    run()                               --  run function of this test case

    _initialize_sdk_objects()           --  Initializes the sdk objects after app creation

    create_inventory()                  --  Create Inventory With Given Nameserver

    create_plan()                       --  Create Data Classification Plan

    create_sdg_project()                --  Create SDG Project And Run Analysis

    add_onedrive_datasource()           --  Add OneDrive DataSource

    review_onedrive_datasource()        --  Review Added One Drive DataSource

    perform_cleanup()                   --  Perform Cleanup Operation

    tear_down()                         --  tears down the onedrive entities created for running the testcase

    is_test_step_complete()             --  checks if a test step is complete

    set_test_step_complete()            --  Sets the progress with a give test step value

"""
import json
import time
from Application.CloudApps.cloud_connector import CloudConnector
from Application.CloudApps import constants as cloud_apps_constants
from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from HyperScale.HyperScaleUtils.rehydrator import Rehydrator
from dynamicindex.one_drive_sdg_helper import OneDriveSDGHelper
from dynamicindex.utils import constants as cs
from dynamicindex.utils.activateutils import ActivateUtils
from dynamicindex.utils.constants import set_step_complete, is_step_complete, SDGTestSteps as sc
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.cvbrowser import BrowserFactory, Browser

_ONEDRIVE_CONFIG_DATA = get_config().DynamicIndex.Activate.OneDrive


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Basic acceptance of Sensitive Data Governance for backed up OneDrive users whose data " \
                    "is not content indexed"
        self.tcinputs = {
            'ServerPlanName': None,
            'IndexServer': None,
            'AccessNodes': None,
            'O365Plan': None,
            'Users': None,
            "RAEntityDBPath": None
        }
        # Test Case constants
        self.activate_utils = None
        self.users = None
        self.cvcloud_object = None
        self.od_sdg_helper = None
        self.o365_plan = None
        self.client_name = None
        self.server_plan = None
        self.azure_directory_id = None
        self.azure_app_id = None
        self.azure_app_key_id = None
        self.index_server = None
        self.access_nodes_list = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.navigator = None
        self.onedrive_server_display_name = None
        self.inventory_name = None
        self.plan_name = None
        self.db_path = None
        self.project_name = None
        self.test_case_error = None
        self.rehydrator = None
        self.test_progress = None
        self.wait_time = 2 * 60
        self.error_dict = {}

    def setup(self):
        """Initial Configuration For Testcase"""
        try:
            self.rehydrator = Rehydrator(self.id)
            self.test_progress = self.rehydrator.bucket(cs.BUCKET_TEST_PROGRESS)
            self.test_progress.get(default=0)
            self.client_name = f"onedrive_client_{self.id}"
            self.onedrive_server_display_name = f'{self.id}_test_onedrive_server'
            self.inventory_name = f'{self.id}_inventory'
            self.plan_name = f'{self.id}_plan'
            self.project_name = f'{self.id}_project'
            self.server_plan = self.tcinputs.get('ServerPlanName')
            self.index_server = self.tcinputs.get('IndexServer')
            self.access_nodes_list = self.tcinputs['AccessNodes']
            self.o365_plan = self.tcinputs['O365Plan']
            self.users = self.tcinputs['Users'].split(",")
            self.db_path = self.tcinputs.get('RAEntityDBPath')
            self.azure_directory_id = self.tcinputs["azure_directory_id"] = _ONEDRIVE_CONFIG_DATA.AzureDirectoryId
            self.azure_app_id = self.tcinputs["application_id"] = _ONEDRIVE_CONFIG_DATA.ApplicationId
            self.azure_app_key_id = self.tcinputs["application_key_value"] = _ONEDRIVE_CONFIG_DATA.ApplicationKeyValue
            self.activate_utils = ActivateUtils()
            self.od_sdg_helper = OneDriveSDGHelper(self.commcell)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=_ONEDRIVE_CONFIG_DATA.UserName,
                                              password=_ONEDRIVE_CONFIG_DATA.Password)
            self.admin_console.login(username=_ONEDRIVE_CONFIG_DATA.UserName,
                                     password=_ONEDRIVE_CONFIG_DATA.Password)
            self.navigator = self.admin_console.navigator
            self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
        except Exception as exception:
            self.status = constants.FAILED
            raise CVTestCaseInitFailure(exception) from exception

    def is_test_step_complete(self, step_enum):
        """
        checks if a test step is complete
        Args:
            step_enum(SDGTestSteps)     --  enum representing the step
        Returns:
            bool                        --  Returns true if step is complete else false
        """
        return is_step_complete(self.test_progress, step_enum.value)

    def set_test_step_complete(self, step_enum):
        """
        Sets the progress with a give test step value
        Args:
            step_enum(SDGTestSteps)     --  enum representing the step
        """
        set_step_complete(self.test_progress, step_enum.value)

    def run(self):
        """Run Function For Test Case Execution"""
        try:
            self.log.info("Starting test case run")
            if not self.is_test_step_complete(sc.GENERATE_SDG_DATA):
                self.od_sdg_helper.generate_sensitive_files(self.db_path)
                self.set_test_step_complete(sc.GENERATE_SDG_DATA)
            else:
                self.log.info(f"{sc.GENERATE_SDG_DATA.name} step complete. Not starting it")

            if not self.is_test_step_complete(sc.CREATE_CLIENT):
                self._client = self.od_sdg_helper.\
                    create_client(self.client_name, self.server_plan, azure_directory_id = self.azure_directory_id,
                                  azure_app_id = self.azure_app_id, azure_app_key_id = self.azure_app_key_id,
                                  index_server=self.index_server, access_nodes_list=self.access_nodes_list)
                self.set_test_step_complete(sc.CREATE_CLIENT)
            else:
                self.log.info(f"{sc.CREATE_CLIENT.name} step complete. Not starting it")
                self._client = self.commcell.clients.get(self.client_name)
                self.od_sdg_helper.client = self._client
                self.od_sdg_helper.init_od_client_entities()

            self._initialize_sdk_objects()
            self.cvcloud_object = CloudConnector(self)

            if not self.is_test_step_complete(sc.ADD_USER):
                self.od_sdg_helper.add_users(self.users, self.o365_plan, self.cvcloud_object)
                self.set_test_step_complete(sc.ADD_USER)
            else:
                self.log.info(f"{sc.ADD_USER.name} step complete. Not starting it")
                self.od_sdg_helper.cvcloud_object = self.cvcloud_object

            if not self.is_test_step_complete(sc.PERFORM_BACKUP):
                self.od_sdg_helper.run_backup()
                self.set_test_step_complete(sc.PERFORM_BACKUP)
            else:
                self.log.info(f"{sc.PERFORM_BACKUP.name} step complete. Not starting it")

            if not self.is_test_step_complete(sc.CREATE_INVENTORY):
                self.create_inventory()
                self.set_test_step_complete(sc.CREATE_INVENTORY)
            else:
                self.log.info(f"{sc.CREATE_INVENTORY.name} step complete. Not starting it")

            self.create_plan()
            self.create_sdg_project()

            if not self.is_test_step_complete(sc.CREATE_SDG_DATASOURCE):
                self.add_onedrive_datasource()
                self.set_test_step_complete(sc.CREATE_SDG_DATASOURCE)
            else:
                self.log.info(f"{sc.CREATE_SDG_DATASOURCE.name} step complete. Not starting it")
                if not self.is_test_step_complete(sc.PERFORM_REVIEW):
                    self.gdpr_obj.file_server_lookup_obj.select_data_source_panel()

            if not self.is_test_step_complete(sc.PERFORM_SDG_DS_CRAWL):
                if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                        self.onedrive_server_display_name, timeout=self.wait_time):
                    raise Exception("Could Not Complete Data Source Scan")
                self.log.info(f"Sleeping for {str(self.wait_time)} Seconds")
                time.sleep(self.wait_time)
                self.set_test_step_complete(sc.PERFORM_SDG_DS_CRAWL)
            else:
                self.log.info(f"{sc.PERFORM_SDG_DS_CRAWL.name} step complete. Not starting it")

            if not self.is_test_step_complete(sc.PERFORM_REVIEW):
                self.gdpr_obj.file_server_lookup_obj.select_data_source(self.onedrive_server_display_name)
                self.gdpr_obj.data_source_discover_obj.select_review()
                # Data source review - Compare DB values with the values in preview Page
                self.gdpr_obj.create_sqlite_db_connection(self.db_path)
                self.review_onedrive_datasource()
                self.set_test_step_complete(sc.PERFORM_REVIEW)
            else:
                self.log.info(f"{sc.PERFORM_REVIEW.name} step complete. Not starting it")

            if not self.is_test_step_complete(sc.PERFORM_CLEANUP):
                self.navigator.navigate_to_governance_apps()
                self.gdpr_obj.cleanup(self.project_name,
                                      self.inventory_name,
                                      self.plan_name,
                                      pseudo_client_name=self.onedrive_server_display_name)
                self.set_test_step_complete(sc.PERFORM_CLEANUP)
            else:
                self.log.info(f"{sc.PERFORM_CLEANUP.name} step complete. Not starting it")

            self.od_sdg_helper.perform_and_validate_restore(self.users, self.access_nodes_list[0])
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def _initialize_sdk_objects(self):
        """Initializes the sdk objects after app creation"""
        self.log.info(f'Create agent object for: {cloud_apps_constants.ONEDRIVE_AGENT}')
        self._agent = self._client.agents.get(cloud_apps_constants.ONEDRIVE_AGENT)

        self.log.info(f'Create instance object for: {cloud_apps_constants.ONEDRIVE_INSTANCE}')
        self._instance = self._agent.instances.get(cloud_apps_constants.ONEDRIVE_INSTANCE)

        self.log.info(f'Create backupset object for: {cloud_apps_constants.ONEDRIVE_BACKUPSET}')
        self._backupset = self._instance.backupsets.get(cloud_apps_constants.ONEDRIVE_BACKUPSET)

        self.log.info(f'Create sub-client object for: {cloud_apps_constants.ONEDRIVE_SUBCLIENT}')
        self._subclient = self._backupset.subclients.get(cloud_apps_constants.ONEDRIVE_SUBCLIENT)

    @test_step
    def create_inventory(self):
        """
        Create Inventory With Given Nameserver
        """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        self.gdpr_obj.inventory_details_obj.add_inventory(
            self.inventory_name, self.index_server)

    @test_step
    def create_plan(self):
        """
        Create Data Classification Plan
        """
        entities_list_map = json.loads(_ONEDRIVE_CONFIG_DATA.EntitiesListMap.replace("'", '"'))
        entities_list = list(entities_list_map.keys())
        self.gdpr_obj.entities_list = list(entities_list_map.values())
        self.gdpr_obj.entities_list_map = entities_list_map
        if not self.is_test_step_complete(sc.CREATE_SDG_PLAN):
            self.navigator.navigate_to_plan()
            self.gdpr_obj.plans_obj.create_data_classification_plan(
                self.plan_name, self.index_server,
                _ONEDRIVE_CONFIG_DATA.ContentAnalyzer, entities_list)
            self.set_test_step_complete(sc.CREATE_SDG_PLAN)
        else:
            self.log.info(f"{sc.CREATE_SDG_PLAN.name} step complete. Not starting it")

    @test_step
    def create_sdg_project(self):
        """
        Create SDG Project And Run Analysis
        """
        self.gdpr_obj.data_source_name = self.onedrive_server_display_name
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        if not self.is_test_step_complete(sc.CREATE_SDG_PROJECT):
            self.gdpr_obj.file_server_lookup_obj.add_project(
                self.project_name, self.plan_name
            )
            self.set_test_step_complete(sc.CREATE_SDG_PROJECT)
        else:
            self.log.info(f"{sc.CREATE_SDG_PROJECT.name} step complete. Not starting it")
            if not self.is_test_step_complete(sc.PERFORM_REVIEW):
                self.gdpr_obj.file_server_lookup_obj.navigate_to_project_details(self.project_name)

    @test_step
    def add_onedrive_datasource(self):
        """
        Add OneDrive DataSource
        """
        self.gdpr_obj.file_server_lookup_obj.select_add_data_source(data_source_type=cs.ONE_DRIVE)
        self.gdpr_obj.file_server_lookup_obj.add_one_drive_v2_server(
            self.client_name,
            cs.CLIENT_NAME,
            self.onedrive_server_display_name,
            cs.USA_COUNTRY_NAME,
            subclient_list=self.users,
            inventory_name = self.inventory_name
        )

    @test_step
    def review_onedrive_datasource(self):
        """
        Review Added One Drive DataSource
        """
        self.gdpr_obj.verify_data_source_name()
        sensitive_files = self.activate_utils.db_get_sensitive_columns_list(
            cs.ONE_DRIVE,
            self.gdpr_obj.entities_list,
            self.db_path
        )
        self.log.info(f"Sensitive Files from Database are {sensitive_files}")
        for filepath in sensitive_files:
            if not self.gdpr_obj.compare_entities(filepath, cs.ONE_DRIVE):
                self.test_case_error = "Entities Value Mismatched"
                filename = filepath.replace(':', '_')
                filename = filename.replace('\\', '_')
                self.error_dict[f'Entity Matching Failed: {filename}'] = self.test_case_error

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.od_sdg_helper.delete_client(self.client_name)

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            if self.status != constants.FAILED:
                self.perform_cleanup()
                self.rehydrator.cleanup()
                self.log.info("Test case execution completed successfully")
        except Exception as exp:
            self.log.info("Test case execution failed")
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
