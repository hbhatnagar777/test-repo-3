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
    __init__()                              --  initialize TestCase class

    setup()                                 --  sets up the variables required for running the testcase

    run()                                   --  run function of this test case

    tear_down()                             --  tears down the activate created entities for running the testcase

    setup_company_for_activate_operation()  --   Sets the desired company to proceed with activate related operations

    perform_activate_task_for_tenant()      --  Performs activate related operations on a tenant with given name

    create_company()                        --  Creates Storage pool, plan and company

    add_activate_solution_to_company()      --  Adds activate as supported solution for the company
                                                Moves Index server and client needed for activate operation

    add_data_controller_user_and_group()    --  Creates user and data controller user group
                                                Adds the user to data controller group

    login()                                 --  Logout and Login as the user passed in the argument

    create_getting_started_sdg_plan()       --  Creates Data Classification Plan

    create_getting_started_inventory()      --  Creates Inventory from guided setup With Nameserver

    create_custom_entity()                  --  Creates a custom entity to be used in SDG plan

    edit_sdg_plan()                         --  Edit Data Classification Plan

    create_sda_project()                    --  Creates SDA Project And Runs Analysis

    add_file_server_datasource()            --  Add File Server DataSource

    add_tenant_operator()                   --  Adds a new user as tenant operator user to the commcell

    verify_tenant_operator_case()           --  Logout as current logged in user and Login as tenant operator to
                                                verify tenant operator sharing cases

    __plan_exists()                         --  Check if a given plan exist for current logged in user

    __inventory_exists()                    --  Check if a given inventory exist for current logged in user

    __project_exists()                      --  Check if a given project exist for current logged in user

    __datasource_exists()                   --  Check if a given datasource exist for current logged in user

    __delete_datasource()                   --  Deletes a datasource

    __validate_project_dashboard()          --  Validates the project dashboard page

    perform_cleanup()                       --  Performs Cleanup Operation of activate entities and tenant entities

    perform_cleanup_for_tenant()            --  Perform Cleanup Operation for a given tenant name

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
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.panel import Security

_ACTIVATE_DATA = get_config().DynamicIndex.ActivateTenant
_TENANT01_CONFIG_DATA = _ACTIVATE_DATA.Tenant01
_TENANT02_CONFIG_DATA = _ACTIVATE_DATA.Tenant02


class TestCase(CVTestCase):
    """Class For executing Activate multi-tenant cases for Sensitive data governance File system that verifies
        security of inventory, project, entity, plan and validate project dashboard as tenant operator user"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Activate multi-tenant cases for Sensitive data governance File system that verifies " \
                    "security of inventory, project, entity, plan and validate project dashboard " \
                    "as tenant operator user"
        # Test Case constants
        self.inventory_name = None
        self.sdg_plan_name = None
        self.server_plan_name = None
        self.storage_pool_name = None
        self.company_name = None
        self.tenant_admin_user = None
        self.tenant_admin_user_fn = None
        self.tenant_dc_user = None
        self.tenant_dc_user_fn = None
        self.project_name = None
        self.file_server_display_name = None
        self.company_config = None
        self.index_server = None
        self.domain_server = None
        self.client_name = None
        self.directory = None
        self.tenant_operator = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.navigator = None
        self.short_wait_time = 20
        self.activate_tenant_helper = None
        self.msp_username = None
        self.msp_password = None
        self.custom_entity_name = None

    def setup(self):
        """Initial Configuration For Testcase"""
        self.tenant_operator = f"{self.id}_" + _ACTIVATE_DATA.tenant_operator
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.msp_username = self.inputJSONnode['commcell']['commcellUsername']
        self.msp_password = self.inputJSONnode['commcell']['commcellPassword']
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                          username=self.msp_username,
                                          password=self.msp_password)
        self.admin_console.login(username=self.msp_username,
                                 password=self.msp_password)
        self.navigator = self.admin_console.navigator
        self.log.info(f"Creating GDPR Object for test case [{self.id}]")
        self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)
        self.activate_tenant_helper = ActivateTenantHelper(self.commcell)

    def run(self):
        """Run Function For Test Case Execution"""
        try:
            self.setup_company_for_activate_operation(_TENANT02_CONFIG_DATA.Name)
            self.activate_tenant_helper.cleanup_all(self.company_name, self.index_server,
                                                    self.client_name, self.server_plan_name, self.storage_pool_name,
                                                    domain_name=self.company_config.NameServer.netbios_name)

            self.setup_company_for_activate_operation(_TENANT01_CONFIG_DATA.Name)
            self.activate_tenant_helper.cleanup_all(self.company_name, self.index_server,
                                                    self.client_name, self.server_plan_name, self.storage_pool_name,
                                                    tenant_operator=self.tenant_operator,
                                                    domain_name=self.company_config.NameServer.netbios_name)
            self.add_tenant_operator()
            self.perform_activate_task_for_tenant(_TENANT01_CONFIG_DATA.Name)
            self.perform_activate_task_for_tenant(_TENANT02_CONFIG_DATA.Name)
            self.verify_tenant_operator_case()
        except Exception as exp:
            self.status = constants.FAILED
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.perform_cleanup()

    @test_step
    def setup_company_for_activate_operation(self, tenant_name):
        """
        Sets the desired company to proceed with activate related operations
        Args:
            tenant_name     --  Name of tenant to do initial setup
        """
        if tenant_name == _TENANT01_CONFIG_DATA.Name:
            self.company_config = _TENANT01_CONFIG_DATA
        else:
            self.company_config = _TENANT02_CONFIG_DATA
        company_name = self.company_config.Name
        self.file_server_display_name = f'{self.id}_{company_name}_file_server'
        self.inventory_name = f'{self.id}_{company_name}_inventory'
        self.sdg_plan_name = f'{self.id}_{company_name}_sdg_plan'
        self.project_name = f'{self.id}_{company_name}_project'
        self.server_plan_name = f'{self.id}_{company_name}_server_plan'
        self.storage_pool_name = f'{self.id}_{company_name}_storage_pool'
        self.company_name = f'{self.id}_{company_name}_activate_company'
        self.tenant_admin_user = f'{self.id}_{company_name}_admin_user'
        self.tenant_admin_user_fn = self.company_name + '\\' + self.tenant_admin_user
        self.tenant_dc_user = f'{self.id}_{company_name}_dc_user'
        self.tenant_dc_user_fn = self.company_name + '\\' + self.tenant_dc_user
        self.custom_entity_name = f'{self.id}_custom_entity'
        self.index_server = self.company_config.IndexServer.index_server_name
        self.domain_server = self.company_config.NameServer.domain_name
        self.client_name = self.company_config.FileServer.machine_name
        self.directory = self.company_config.FileServer.directory

    @test_step
    def perform_activate_task_for_tenant(self, tenant_name):
        """
            Performs activate related operations on a tenant with given name
            Args:
                tenant_name - name of the tenant to perform the activate tasks
        """
        self.setup_company_for_activate_operation(tenant_name)
        self.create_company()
        self.add_activate_solution_to_company()
        self.add_data_controller_user_and_group()
        self.login(self.tenant_admin_user_fn)
        self.create_getting_started_sdg_plan()
        self.create_getting_started_inventory()
        if self.company_config.Name == _TENANT01_CONFIG_DATA.Name:
            self.create_custom_entity()
            self.edit_sdg_plan()
        self.login(self.tenant_dc_user_fn)
        self.create_sda_project()
        self.add_file_server_datasource()

    @test_step
    def create_company(self):
        """
        Create Storage pool, plan and company
        """
        ma_config = self.company_config.MediaAgent
        self.activate_tenant_helper.add_storage_pool(self.storage_pool_name, ma_config.mount_path,
                                                     ma_config.name, ma_config.ddb_path)
        self.activate_tenant_helper.add_plan(self.server_plan_name, self.storage_pool_name)
        self.activate_tenant_helper.add_company(self.company_name,
                                                f'{self.id}_{self.company_config.Name}_admin_user@commvault.com',
                                                self.tenant_admin_user, self.server_plan_name)
        self.activate_tenant_helper.change_company_user_password(self.tenant_admin_user_fn,
                                                                 self.company_config.user_password, self.msp_password)
        if self.company_config.Name == _TENANT01_CONFIG_DATA.Name:
            self.activate_tenant_helper.add_user_as_operator(self.tenant_operator, self.company_name)

    @test_step
    def add_activate_solution_to_company(self):
        """
        Adds activate as supported solution for the company
        Moves Index server and client needed for activate operation
        """
        self.activate_tenant_helper.add_activate_to_company(self.company_name)
        self.activate_tenant_helper.move_client_to_company(self.company_name, self.index_server)
        self.activate_tenant_helper.move_client_to_company(self.company_name, self.client_name)
        self.activate_tenant_helper.add_domain_to_company(self.domain_server,
                                                          self.company_config.NameServer.netbios_name,
                                                          self.company_config.NameServer.username,
                                                          self.company_config.NameServer.password,
                                                          self.company_name)

    @test_step
    def add_data_controller_user_and_group(self):
        """
        Creates user and data controller user group
        Adds the user to data controller group
        """
        user_group_name = f'{self.id}_{self.company_config.Name}_dc_usr_group'
        self.activate_tenant_helper.add_user(f'{self.tenant_dc_user_fn}',
                                             f'{self.id}_{self.company_config.Name}_dc_user@commvault.com',
                                             self.tenant_dc_user, self.company_config.user_password)
        self.activate_tenant_helper.add_data_governance_user_group(user_group_name,
                                                                   self.company_name,
                                                                   [f'{self.tenant_dc_user_fn}'])
        if self.company_config.Name == _TENANT01_CONFIG_DATA.Name:
            self.activate_tenant_helper.associate_user_to_user_group_with_view_permission(
                self.tenant_operator, f"{self.company_name}\\{user_group_name}")

    @test_step
    def login(self, username):
        """
        Logout and Login as the user passed in the argument
        Args:
            username    -   name of the user to login
        """

        self.log.info(f"Logging out as current logged in user [{self.admin_console.get_login_name()}]")
        self.admin_console.logout()
        self.log.info(f"Logging in as user [{username}] ")
        self.admin_console.login(username=f'{username}',
                                 password=self.company_config.user_password)

    @test_step
    def create_getting_started_sdg_plan(self):
        """
        Create Data Classification Plan
        """
        entities_list_map = json.loads(self.company_config.EntitiesListMap.replace("'", '"'))
        self.gdpr_obj.entities_list = list(entities_list_map.values())
        self.gdpr_obj.entities_list_map = entities_list_map
        entities_list = list(entities_list_map.keys())
        self.navigator.navigate_to_getting_started()
        self.navigator.switch_to_activate_tab()
        self.gdpr_obj.inventory_details_obj.select_sda_getting_started()
        self.gdpr_obj.plans_obj.getting_started_create_sdg_plan(
            self.sdg_plan_name, self.index_server,
            self.company_config.ContentAnalyzer.content_analyzer_name, entities_list)
        time.sleep(self.short_wait_time)

    @test_step
    def create_getting_started_inventory(self):
        """
        Create Inventory from guided setup With Nameserver
        """
        self.gdpr_obj.inventory_details_obj.add_inventory(
            self.inventory_name, self.index_server, name_server=self.domain_server, guided_setup=True)
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        self.gdpr_obj.inventory_details_obj.navigate_to_inventory_details(
            self.inventory_name)
        associations = {
            f'{self.tenant_dc_user_fn}': [[cs.VIEW]]
        }
        self.gdpr_obj.inventory_details_obj.share_inventory(associations)
        time.sleep(self.short_wait_time)
        if not self.gdpr_obj.inventory_details_obj.wait_for_asset_status_completion(
                self.domain_server):
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
        self.log.info(f"Creating custom entity with Name - [{self.custom_entity_name}],"
                      f"Sensitivity - [{_ACTIVATE_DATA.custom_entity.Sensitivity}], "
                      f"Keywords - [{_ACTIVATE_DATA.custom_entity.Keywords}]")
        self.gdpr_obj.entity_manager_obj.add_custom_entity(self.custom_entity_name,
                                                           _ACTIVATE_DATA.custom_entity.Sensitivity,
                                                           keywords=_ACTIVATE_DATA.custom_entity.Keywords.split(","))
        self.log.info("Created custom entity successfully")

    @test_step
    def edit_sdg_plan(self):
        """
        Edit Data Classification Plan
        """
        self.log.info(f"Editing SDG plan [{self.sdg_plan_name}] to add new custom entity [{self.custom_entity_name}]")
        self.gdpr_obj.entities_list_map[self.custom_entity_name] = self.custom_entity_name
        self.gdpr_obj.entities_list = list(self.gdpr_obj.entities_list_map.values())
        self.navigator.navigate_to_plan()
        self.admin_console.select_hyperlink(self.sdg_plan_name)
        self.gdpr_obj.plans_obj.edit_data_classification_plan(self.sdg_plan_name,
                                                              list(self.gdpr_obj.entities_list_map.keys()))
        self.log.info(f"Successfully added new custom entity [{self.custom_entity_name}] "
                      f"to plan [{self.sdg_plan_name}]")

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
        if self.company_config.Name == _TENANT01_CONFIG_DATA.Name:
            security = Security(self.admin_console)
            associations = {
                f'{self.tenant_operator}': [[cs.VIEW]]
            }
            self.log.info(f"Received request to provide tenant operator [{self.tenant_operator}] "
                          f"with view permission on datasource with name [{self.file_server_display_name}]")
            security.edit_security_association(associations, add=True)
            self.log.info(f"Successfully Provided tenant operator [{self.tenant_operator}] with view permission on "
                          f" datasource with name [{self.file_server_display_name}]")
        if not self.gdpr_obj.file_server_lookup_obj.wait_for_data_source_status_completion(
                self.file_server_display_name, timeout=60):
            raise Exception("Could not complete Data Source Scan")

    @test_step
    def add_tenant_operator(self):
        """
        Adds a new user as tenant operator user to the commcell
        """
        tenant_user_email = self.tenant_operator + "@commvault.com"
        self.activate_tenant_helper.add_user(self.tenant_operator, tenant_user_email,
                                             self.tenant_operator, self.msp_password)

    @test_step
    def verify_tenant_operator_case(self):
        """
        Logout as current logged in user and Login as tenant operator to
        verify tenant operator sharing cases
        """
        self.admin_console.logout()
        self.log.info(f"Logging in as user [{self.tenant_operator}] ")
        self.admin_console.login(username=f'{self.tenant_operator}',
                                 password=self.msp_password)

        # verify if tenant operator is able to access Tenant01's project, plan and inventory
        # As tenant operator, the user should be able to see the inventory, project and plan created
        # by tenant data controller user
        self.setup_company_for_activate_operation(_TENANT01_CONFIG_DATA.Name)
        self.navigator.switch_company_as_operator(self.company_name)
        if not self.__inventory_exists():
            raise Exception(f"Security issue - Tenant operator [{self.tenant_operator}] should have "
                            f"permission to access inventory [{self.inventory_name}]")
        self.log.info(f"Tenant operator [{self.tenant_operator}] have "
                      f"view permission on the inventory [{self.inventory_name}]. "
                      f"Permission verified")

        if not self.__plan_exists():
            raise Exception(f"Security issue - Tenant operator [{self.tenant_operator}] "
                            f"should have view permission on plan [{self.sdg_plan_name}]")
        self.log.info(f"Tenant operator [{self.tenant_operator}] is able to "
                      f"see the plan [{self.sdg_plan_name}] listed. "
                      f"Permission verified")

        if not self.__project_exists():
            raise Exception(f"Security issue - Tenant operator [{self.tenant_operator}] "
                            f"should have view permission on project [{self.sdg_plan_name}]")
        self.log.info(f"Tenant operator [{self.tenant_operator}] is able to "
                      f"see the project [{self.project_name}] listed. "
                      f"Permission verified")

        if not self.__datasource_exists():
            raise Exception(f"Security issue - "
                            f"Datasource with given name [{self.file_server_display_name}] is not visible to user")
        self.log.info(f"Permission verified. Datasource with given name [{self.file_server_display_name}] exists")

        self.__validate_project_dashboard()

        if self.__delete_datasource():
            raise Exception(f"Security issue - User [{self.admin_console.get_login_name()}] "
                            f"with view permission is able to delete the datasource [{self.file_server_display_name}]")
        self.log.info(f"Permission verified. User [{self.tenant_operator}] is not able"
                      f"to delete the datasource [{self.file_server_display_name}]")

        # verify if tenant operator is able to access Tenant02's project, plan, inventory and custom entity
        # Since self.tenant_operator is not Tenant02's operator, the user shouldn't be able to see
        # the projects or plans or inventories created by user

        self.setup_company_for_activate_operation(_TENANT02_CONFIG_DATA.Name)
        self.navigator.switch_company_as_operator(self.company_name)
        if self.__inventory_exists():
            raise Exception(f"Security issue - Tenant operator [{self.tenant_operator}] is able to "
                            f"access inventory [{self.inventory_name}] without any permission")
        self.log.info(f"Tenant operator [{self.tenant_operator}] does not have "
                      f"view permission on the inventory [{self.inventory_name}]. "
                      f"Permission verified")

        if self.__plan_exists():
            raise Exception(f"Security issue - Tenant operator [{self.tenant_operator}] "
                            f"should not have view permission on plan [{self.sdg_plan_name}]")
        self.log.info(f"Tenant operator [{self.tenant_operator}] is not able to "
                      f"see the plan [{self.sdg_plan_name}] listed. "
                      f"Permission verified")

        if self.__project_exists():
            raise Exception(f"Security issue - Tenant operator [{self.tenant_operator}] "
                            f"should not have view permission on project [{self.sdg_plan_name}]")
        self.log.info(f"Tenant operator [{self.tenant_operator}] is not able to "
                      f"see the project [{self.project_name}] listed. "
                      f"Permission verified")

        # Operations on Custom entity as tenant operator
        self.log.info("Navigating to activate page")
        self.navigator.navigate_to_governance_apps()
        self.log.info("Selecting Entity manager under activate page")
        self.gdpr_obj.inventory_details_obj.select_entity_manager()
        if self.gdpr_obj.entity_manager_obj.check_if_activate_entity_exists(self.custom_entity_name):
            raise Exception(f"Security issue - Tenant operator [{self.tenant_operator}] "
                            f"should not have view permission on custom entity [{self.custom_entity_name}]"
                            f"for company [{self.company_name}]")
        self.log.info(f"Tenant operator [{self.tenant_operator}] is not able to "
                      f"see the custom entity [{self.custom_entity_name}] listed for company [{self.company_name}]. "
                      f"Permission verified")

        # Operations on Custom Entity for Tenant01
        self.setup_company_for_activate_operation(_TENANT01_CONFIG_DATA.Name)
        self.navigator.switch_company_as_operator(self.company_name)
        self.gdpr_obj.entity_manager_obj.delete_entity(self.custom_entity_name)
        self.log.info(f"Successfully deleted entity with name [{self.custom_entity_name}] as [{self.tenant_operator}]"
                      f"for company [{self.company_name}]")

    @test_step
    def __plan_exists(self):
        """
        Check if a given plan exist for current logged in user
        """
        self.log.info(f"Checking if plan [{self.sdg_plan_name}] exist for "
                      f"user [{self.admin_console.get_login_name()}]")
        self.admin_console.navigator.navigate_to_governance_apps()
        self.admin_console.navigator.navigate_to_plan()
        if not self.gdpr_obj.plan_exists(self.sdg_plan_name):
            self.log.info(f"Plan with name [{self.sdg_plan_name}] doesn't exist")
            return False
        self.log.info(f"Plan with name [{self.sdg_plan_name}] is present")
        return True

    @test_step
    def __inventory_exists(self):
        """
        Check if a given inventory exist for current logged in user
        """
        self.log.info(f"Checking if inventory [{self.inventory_name}] exist for "
                      f"user [{self.admin_console.get_login_name()}]")
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_inventory_manager()
        if not self.gdpr_obj.inventory_exists(self.inventory_name):
            self.log.info(f"Inventory with name [{self.inventory_name}] doesn't exist")
            return False
        self.log.info(f"Inventory with name [{self.inventory_name}] is present")
        return True

    @test_step
    def __project_exists(self):
        """
        Check if a given project exist for current logged in user
        """
        self.log.info(f"Checking if project [{self.project_name}] exist for "
                      f"user [{self.admin_console.get_login_name()}]")
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        if not self.gdpr_obj.project_exists(self.project_name):
            self.log.info(f"Project with name [{self.project_name}] doesn't exist")
            return False
        self.log.info(f"Project with name [{self.project_name}] is present")
        return True

    @test_step
    def __datasource_exists(self):
        """
        Check if a given datasource exist for current logged in user
        """
        self.log.info(f"Checking if data source [{self.file_server_display_name}] exist for "
                      f"user [{self.admin_console.get_login_name()}]")
        self.gdpr_obj.file_server_lookup_obj.navigate_to_project_details(self.project_name)
        if not self.gdpr_obj.file_server_lookup_obj.data_source_exists(self.file_server_display_name):
            self.log.info(f"Datasource with name [{self.file_server_display_name}] doesn't exist")
            return False
        self.log.info(f"Datasource with name [{self.file_server_display_name}] is present")
        return True

    @test_step
    def __delete_datasource(self):
        """
        Deletes a datasource
        """
        self.log.info(f"Deleting data source [{self.file_server_display_name}] as "
                      f"user [{self.admin_console.get_login_name()}]")
        if self.gdpr_obj.file_server_lookup_obj.delete_data_source(self.file_server_display_name):
            self.log.info(f"Datasource with name [{self.file_server_display_name}] deleted successfully")
            return True
        self.log.info(f"Datasource with name [{self.file_server_display_name}] cannot be deleted")
        return False

    @test_step
    def __validate_project_dashboard(self):
        """
        Validates the project dashboard page
        """
        self.gdpr_obj.entities_list_map[self.custom_entity_name] = self.custom_entity_name
        self.gdpr_obj.entities_list = list(self.gdpr_obj.entities_list_map.values())
        self.admin_console.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_sensitive_data_analysis()
        self.gdpr_obj.file_server_lookup_obj.navigate_to_project_discover(self.project_name)
        self.admin_console.select_report_tab(self.admin_console.props['label.fileSystem'])
        self.admin_console.wait_for_completion()
        self.log.info(f"Waiting for [{self.short_wait_time}] seconds for reports page load to complete")
        time.sleep(self.short_wait_time)
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
            raise Exception(f"As user [{self.admin_console.get_login_name()}], the actual file count [{actual_count}] "
                            f"did not match the expected file count [{expected_count}] information at crawl path"
                            f"[{self.directory}]")
        self.log.info(f"As user [{self.admin_console.get_login_name()}], the actual file count [{actual_count}] "
                      f"matches the expected file count [{expected_count}] information at crawl path"
                      f"[{self.directory}]")
        actual_count = self.gdpr_obj.data_source_discover_obj.get_sensitive_files()
        activate_utils = ActivateUtils()
        sensitive_files = activate_utils.db_get_sensitive_columns_list(
            cs.FILE_SYSTEM,
            self.gdpr_obj.entities_list,
            _ACTIVATE_DATA.TestDataSQLiteDBPath
        )
        sensitive_file_count = len(sensitive_files)
        if not actual_count == sensitive_file_count:
            raise Exception(f"As user [{self.admin_console.get_login_name()}], the actual sensitive file count "
                            f"[{actual_count}] does not match the expected sensitive file count "
                            f"[{sensitive_file_count}] information at crawl path "
                            f"[{self.directory}]")
        self.log.info(f"As user [{self.admin_console.get_login_name()}], the actual sensitive file count "
                      f"[{actual_count}] matches the expected sensitive file count [{sensitive_file_count}] "
                      f"information at crawl path [{self.directory}]")

    @test_step
    def perform_cleanup(self):
        """
        Perform Cleanup Operation
        """
        self.perform_cleanup_for_tenant(_TENANT02_CONFIG_DATA.Name)
        self.perform_cleanup_for_tenant(_TENANT01_CONFIG_DATA.Name)
        self.activate_tenant_helper.delete_user(self.tenant_operator, new_user=self.msp_username)

    @test_step
    def perform_cleanup_for_tenant(self, company_name):
        """
        Perform Cleanup Operation for a given tenant name
        Args:
            company_name    -   name of the company to cleanup
        """
        self.setup_company_for_activate_operation(company_name)
        self.activate_tenant_helper.remove_client_association(self.company_name, self.index_server)
        self.activate_tenant_helper.remove_client_association(self.company_name, self.client_name)
        self.activate_tenant_helper.delete_company(self.company_name)
        self.activate_tenant_helper.delete_plan(self.server_plan_name)
        self.activate_tenant_helper.delete_storage_pool(self.storage_pool_name)
