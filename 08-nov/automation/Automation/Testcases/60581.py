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
    __init__()                          --  initialize TestCase class

    setup()                             --  sets up the variables required for running the testcase

    run()                               --  run function of this test case

    tear_down()                         --  tears down the activate created entities for running the testcase

    create_company()                    --  Creates Storage pool, plan and company

    add_activate_solution_to_company()  --  Adds activate as supported solution for the company
                                            Moves Index server and client needed for activate operation

    add_data_controller_user_and_group()--  Creates user and data controller user group
                                            Adds the user to data controller group

    login_as_tenant_admin()             --  Logout as MSP admin and Login as
                                            tenant admin to complete guided setup of activate

    create_getting_started_sdg_plan()   --  Creates Data Classification Plan

    create_getting_started_inventory()  --  Creates Inventory from guided setup With Nameserver

    create_custom_entity()              --  Creates a custom entity to be used in SDG plan

    login_as_tenant_data_controller()   --  Logout as tenant admin and Login as tenant data
                                            controller user to perform activate operations

    edit_sdg_plan()                     --  Edit Data Classification Plan

    create_sda_project()                --  Creates SDA Project And Runs Analysis

    add_file_server_datasource(self)    --  Add File Server DataSource

    validate_project_dashboard()        --  Validate the total and sensitive file count
                                            in project dashboard for the datasource

    delete_custom_entity()              --  Deletes custom entity

    perform_cleanup()                   --  Performs Cleanup Operation of activate entities and tenant entities

"""

import time
import json
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from AutomationUtils.machine import Machine
from dynamicindex.activate_tenant_helper import ActivateTenantHelper
from dynamicindex.utils import constants as cs
from dynamicindex.utils.activateutils import ActivateUtils
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole

_TENANT_CONFIG_DATA = get_config().DynamicIndex.ActivateTenant.Tenant01
_ACTIVATE_DATA = get_config().DynamicIndex.ActivateTenant


class TestCase(CVTestCase):
    """Class For executing Activate Automation to support SDG File system in tenant environment
    for verifying create and edit of inventory, plan, project and add data source and validate the
    collected information in Project dashboard"""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Activate Automation to support SDG File system in tenant environment for verifying " \
                    "create and edit of inventory, plan, project and add data source and validate the " \
                    "collected information in Project dashboard"
        # Test Case constants
        self.inventory_name = None
        self.sdg_plan_name = None
        self.server_plan_name = None
        self.storage_pool_name = None
        self.company_prod_name = None
        self.prod_admin_user = None
        self.prod_admin_user_fn = None
        self.prod_dc_user = None
        self.prod_dc_user_fn = None
        self.company_user_password = None
        self.prod_index_server = None
        self.prod_domain_server = None
        self.project_name = None
        self.file_server_display_name = None
        self.activate_tenant_helper = None
        self.client_name = None
        self.directory = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.navigator = None
        self.short_wait_time = 10
        self.custom_entity = None

    def setup(self):
        """Initial Configuration For Testcase"""
        try:
            self.file_server_display_name = f'{self.id}_test_file_server'
            self.inventory_name = f'{self.id}_inventory_file_server'
            self.sdg_plan_name = f'{self.id}_sdg_plan_file_server'
            self.project_name = f'{self.id}_project_file_server'
            self.server_plan_name = f'{self.id}_server_plan'
            self.storage_pool_name = f'{self.id}_storage_pool'
            self.company_prod_name = f'{self.id}_activate_prod_company'
            self.prod_admin_user = f'{self.id}_prod_admin_user'
            self.prod_admin_user_fn = f'{self.company_prod_name}\\{self.prod_admin_user}'
            self.prod_dc_user = f'{self.id}_prod_dc_user'
            self.prod_dc_user_fn = f'{self.company_prod_name}\\{self.prod_dc_user}'
            self.custom_entity = f'{self.id}_custom_entity'
            self.company_user_password = _TENANT_CONFIG_DATA.user_password
            self.prod_index_server = _TENANT_CONFIG_DATA.IndexServer.index_server_name
            self.prod_domain_server = _TENANT_CONFIG_DATA.NameServer.domain_name
            self.client_name = _TENANT_CONFIG_DATA.FileServer.machine_name
            self.directory = _TENANT_CONFIG_DATA.FileServer.directory
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=self.inputJSONnode['commcell']['commcellUsername'],
                                              password=self.inputJSONnode['commcell']['commcellPassword'])
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.log.info(f"Creating GDPR Object for test case [{self.id}]")
            self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
            self.activate_tenant_helper = ActivateTenantHelper(self.commcell)
        except Exception as exception:
            self.status = constants.FAILED
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """Run Function For Test Case Execution"""
        try:
            self.activate_tenant_helper.cleanup_all(self.company_prod_name, self.prod_index_server,
                                                    self.client_name, self.server_plan_name, self.storage_pool_name,
                                                    domain_name=_TENANT_CONFIG_DATA.NameServer.netbios_name)
            self.create_company()
            self.add_activate_solution_to_company()
            self.add_data_controller_user_and_group()
            self.login_as_tenant_admin()
            self.create_getting_started_sdg_plan()
            self.create_getting_started_inventory()
            self.create_custom_entity()
            self.login_as_tenant_data_controller()
            self.edit_sdg_plan()
            self.create_sda_project()
            self.add_file_server_datasource()
            self.validate_project_dashboard()
        except Exception as exp:
            self.status = constants.FAILED
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            if self.status != constants.FAILED:
                self.perform_cleanup()
        except Exception as exp:
            self.status = constants.FAILED
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    @test_step
    def create_company(self):
        """
        Create Storage pool, plan and company
        """
        ma_config = _TENANT_CONFIG_DATA.MediaAgent
        self.activate_tenant_helper.add_storage_pool(self.storage_pool_name, ma_config.mount_path,
                                                     ma_config.name, ma_config.ddb_path)
        self.activate_tenant_helper.add_plan(self.server_plan_name, self.storage_pool_name)
        self.activate_tenant_helper.add_company(self.company_prod_name, f'{self.id}_prod_admin_user@commvault.com',
                                                self.prod_admin_user, self.server_plan_name)
        self.activate_tenant_helper.change_company_user_password(self.prod_admin_user_fn,
                                                                 self.company_user_password,
                                                                 self.inputJSONnode['commcell']['commcellPassword'])

    @test_step
    def add_activate_solution_to_company(self):
        """
        Adds activate as supported solution for the company
        Moves Index server and client needed for activate operation
        """
        self.activate_tenant_helper.add_activate_to_company(self.company_prod_name)
        self.activate_tenant_helper.move_client_to_company(self.company_prod_name, self.prod_index_server)
        self.activate_tenant_helper.move_client_to_company(self.company_prod_name, self.client_name)
        self.activate_tenant_helper.add_domain_to_company(self.prod_domain_server,
                                                          _TENANT_CONFIG_DATA.NameServer.netbios_name,
                                                          _TENANT_CONFIG_DATA.NameServer.username,
                                                          _TENANT_CONFIG_DATA.NameServer.password,
                                                          self.company_prod_name)

    @test_step
    def add_data_controller_user_and_group(self):
        """
        Creates user and data controller user group
        Adds the user to data controller group
        """
        self.activate_tenant_helper.add_user(f'{self.prod_dc_user_fn}',
                                             f'{self.id}_prod_dc_user@commvault.com',
                                             self.prod_dc_user, self.company_user_password)
        self.activate_tenant_helper.add_data_governance_user_group(f'{self.id}_prod_dc_usr_group',
                                                                   self.company_prod_name,
                                                                   [f'{self.prod_dc_user_fn}'])

    @test_step
    def login_as_tenant_admin(self):
        """
        Logout as MSP admin and Login as tenant admin to complete guided setup of activate
        """

        self.log.info("Logging out currently logged in user")
        self.admin_console.logout()
        self.log.info(f"Logging in as user [{self.prod_admin_user_fn}] ")
        self.admin_console.login(username=f'{self.prod_admin_user_fn}',
                                 password=self.company_user_password)

    @test_step
    def create_getting_started_sdg_plan(self):
        """
        Create Data Classification Plan
        """
        entities_list_map = json.loads(_TENANT_CONFIG_DATA.EntitiesListMap.replace("'", '"'))
        self.gdpr_obj.entities_list = list(entities_list_map.values())
        self.gdpr_obj.entities_list_map = entities_list_map
        entities_list = list(entities_list_map.keys())
        self.navigator.navigate_to_getting_started()
        self.navigator.switch_to_activate_tab()
        self.gdpr_obj.inventory_details_obj.select_sda_getting_started()
        self.gdpr_obj.plans_obj.getting_started_create_sdg_plan(
            self.sdg_plan_name, self.prod_index_server,
            _TENANT_CONFIG_DATA.ContentAnalyzer.content_analyzer_name, entities_list)
        time.sleep(self.short_wait_time)

    @test_step
    def create_getting_started_inventory(self):
        """
        Create Inventory from guided setup With Nameserver
        """
        self.gdpr_obj.inventory_details_obj.add_inventory(
            self.inventory_name, self.prod_index_server, name_server=self.prod_domain_server, guided_setup=True)
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        self.gdpr_obj.inventory_details_obj.navigate_to_inventory_details(
            self.inventory_name)
        associations = {
            f'{self.prod_dc_user_fn}': [[cs.VIEW]]
        }
        self.gdpr_obj.inventory_details_obj.share_inventory(associations)
        time.sleep(self.short_wait_time)
        if not self.gdpr_obj.inventory_details_obj.wait_for_asset_status_completion(
                self.prod_domain_server):
            raise Exception("Could not complete Asset Scan")

    @test_step
    def create_custom_entity(self):
        """
        Creates a custom entity to be used in SDG plan
        """
        self.log.info("Navigating to Activate page")
        self.admin_console.navigator.navigate_to_governance_apps()
        self.log.info("Selecting entity manager")
        self.gdpr_obj.inventory_details_obj.select_entity_manager()
        self.log.info(f"Creating custom entity with Name - [{self.custom_entity}],"
                      f"Sensitivity - [{_ACTIVATE_DATA.custom_entity.Sensitivity}], "
                      f"Keywords - [{_ACTIVATE_DATA.custom_entity.Keywords}]")
        self.gdpr_obj.entity_manager_obj.add_custom_entity(self.custom_entity,
                                                           _ACTIVATE_DATA.custom_entity.Sensitivity,
                                                           keywords=_ACTIVATE_DATA.custom_entity.Keywords.split(","))
        self.log.info("Created custom entity successfully")

    @test_step
    def login_as_tenant_data_controller(self):
        """
        Logout as tenant admin and Login as tenant data controller user to perform activate operations
        """
        self.log.info(f"Logging out as user [{self.prod_admin_user_fn}] ")
        self.admin_console.logout()
        self.log.info(f"Logging in as user [{self.prod_dc_user_fn}] ")
        self.admin_console.login(username=f'{self.prod_dc_user_fn}',
                                 password=self.company_user_password)

    @test_step
    def edit_sdg_plan(self):
        """
        Edit Data Classification Plan
        """
        self.log.info(f"Editing SDG plan [{self.sdg_plan_name}] to add new custom entity [{self.custom_entity}]")
        self.gdpr_obj.entities_list_map[self.custom_entity] = self.custom_entity
        self.gdpr_obj.entities_list = list(self.gdpr_obj.entities_list_map.values())
        self.navigator.navigate_to_plan()
        self.admin_console.select_hyperlink(self.sdg_plan_name)
        self.gdpr_obj.plans_obj.edit_data_classification_plan(self.sdg_plan_name,
                                                              list(self.gdpr_obj.entities_list_map.keys()))
        self.log.info(f"Successfully added new custom entity [{self.custom_entity}] to plan [{self.sdg_plan_name}]")

    @test_step
    def create_sda_project(self):
        """
        Create SDA Project And Run Analysis
        """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.add_project(
            self.project_name, self.sdg_plan_name)

    @test_step
    def add_file_server_datasource(self):
        """
        Add File Server DataSource
        """
        self.gdpr_obj.file_server_lookup_obj.select_add_data_source()

        self.log.info(f"Adding datasource with name "
                      f"[{self.file_server_display_name}] for client [{self.client_name}]")
        self.gdpr_obj.file_server_lookup_obj.add_file_server(
            self.client_name, cs.CLIENT_NAME,
            self.file_server_display_name, cs.USA_COUNTRY_NAME,
            self.directory, agent_installed=True, live_crawl=True,
            inventory_name = self.inventory_name)
        self.log.info("Sleeping for: '%d' seconds" % self.short_wait_time)
        time.sleep(self.short_wait_time)
        if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name, timeout=60):
            raise Exception("Could not complete Data Source Scan")

    @test_step
    def validate_project_dashboard(self):
        """
        Validate the total and sensitive file count in project dashboard for the datasource
        """
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.navigate_to_project_discover(self.project_name)
        self.admin_console.select_report_tab(self.admin_console.props['label.fileSystem'])
        self.admin_console.wait_for_completion()
        self.log.info(f"Waiting for [{self.short_wait_time}] seconds for reports page load to complete")
        time.sleep(self.short_wait_time)
        self.log.info(f"Initializing machine class for machine - [{self.client_name}]")
        machine = Machine(self.client_name, self.commcell)
        self.log.info(f"Initialized machine class for machine - [{self.client_name}]")
        self.log.info(f"Fetching count of items in folder [{self.directory}] "
                      f"for machine - [{self.client_name}]")
        expected_count = machine.number_of_items_in_folder(self.directory,
                                                           include_only=cs.TYPE_FILES, recursive=True)
        self.log.info(f"Total count of files in folder [{self.directory}] "
                      f"obtained is [{expected_count}]")
        actual_count = self.gdpr_obj.data_source_discover_obj.get_total_files()
        if not actual_count == expected_count:
            raise Exception(f"File count [{actual_count}] in dashboard doesn't match the total number of files "
                            f"[{expected_count}] at crawl path [{self.directory}]")
        self.log.info(f"File count [{actual_count}] in dashboard matches the total number of files "
                      f"[{expected_count}] at crawl path [{self.directory}]")

        actual_count = self.gdpr_obj.data_source_discover_obj.get_sensitive_files()
        activate_utils = ActivateUtils()
        sensitive_files = activate_utils.db_get_sensitive_columns_list(
            cs.FILE_SYSTEM,
            self.gdpr_obj.entities_list,
            _ACTIVATE_DATA.TestDataSQLiteDBPath
        )
        sensitive_file_count = len(sensitive_files)
        if not actual_count == sensitive_file_count:
            raise Exception(f"Sensitive File count [{actual_count}] in dashboard doesn't match "
                            f"the total number of files [{sensitive_file_count}] at crawl path "
                            f"[{self.directory}]")
        self.log.info(f"Sensitive file count [{actual_count}] in dashboard matches the total number of files "
                      f"[{sensitive_file_count}] at crawl path [{self.directory}]")

    @test_step
    def delete_custom_entity(self):
        """
        Deletes custom entity
        """
        self.log.info("Navigating to entity manager")
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_entity_manager()
        self.gdpr_obj.entity_manager_obj.delete_entity(self.custom_entity)
        self.log.info(f"Successfully deleted entity with name [{self.custom_entity}]")

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.delete_custom_entity()
        self.activate_tenant_helper.remove_client_association(self.company_prod_name, self.prod_index_server)
        self.activate_tenant_helper.remove_client_association(self.company_prod_name, self.client_name)
        self.activate_tenant_helper.delete_company(self.company_prod_name)
        self.activate_tenant_helper.delete_plan(self.server_plan_name)
        self.activate_tenant_helper.delete_storage_pool(self.storage_pool_name)
