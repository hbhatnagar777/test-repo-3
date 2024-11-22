# -*- coding: utf-8 -*-


# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Cases for validating [Laptop] [AdminConsole][AdminMode]: Validation of the of laptop users from Security-->
    users

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole, Browser
from Laptop.laptophelper import LaptopHelper
from Web.AdminConsole.Laptop.Laptops import Laptops
from Web.AdminConsole.Helper.UserHelper import UserMain
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.dialog import RSecurity
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.AdminConsolePages.Roles import Roles
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.exceptions import CVWebAutomationException


class TestCase(CVTestCase):
    """Test Case for validating [Laptop] [AdminConsole][AdminMode]: Deactivate and Activate Laptop validation from
    CC Based on permissions"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.driver = None
        self.rtable = None
        self.rsecurity = None
        self.navigator = None
        self.admin_console = None
        self.browser = None
        self.name = "[Laptop] [AdminConsole][AdminMode]: Deactivate and Activate Laptop validation from CC Based on " \
                    "permissions"
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.ADMINCONSOLE
        self.laptops = None
        self.laptop_helper = None
        self.user = None
        self.page_container = None
        self.roles = None
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}
        self.custompackage_kwargs = {}

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']["webconsoleHostname"])
        self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"], self.inputJSONnode['commcell']
        ["commcellPassword"])
        self.navigator = self.admin_console.navigator
        self.user = UserMain(self.admin_console, self.commcell)
        self.laptops = Laptops(self.admin_console)
        self.rtable = Rtable(self.admin_console)
        self.page_container = PageContainer(self.admin_console)
        self.rsecurity = RSecurity(self.admin_console)
        self.roles = Roles(self.admin_console)
        self.admin_console.load_properties(self)
        self.driver = self.browser.driver

    @test_step
    def add_user_and_entity(self):
        """
            Create a user and to that user, add associated entity: Laptops > client > role
        """
        self.log.info("Creating new user")
        self.user.user_name = self.tcinputs.get("user_name")
        self.user.full_name = self.tcinputs.get("user_name")
        self.user.email = self.tcinputs.get("user_name") + "@test.com"
        self.user.password = self.tcinputs.get("user_password")
        self.navigator.navigate_to_users()
        self.user.add_new_local_user()
        self.log.info("Local user has been created successfully")
        self.log.info("Associating entities to the new user")
        self.admin_console.access_tab("Associated entities")
        self.admin_console.click_button(value="Add association")
        self.rsecurity.add_associated_entities(associations={
            'Laptops': [{
                'entity_name': self.tcinputs.get('Machine_client_name'),
                'role_name': self.tcinputs.get('role_name')
            }]
        })
        self.log.info("Entity for laptop without Agent Management Permission associated to the user successfully")

    @test_step
    def check_visibility_of_acdeac(self, text=None, given=False):
        """
            Check for visibility of activate & deactivate first, action visibility in both listing
            and details is subject to [Agent Management] permission

            Args:
                text    (str) :  Activate / Deactivate to choose the flow
                given   (bool):  True, if AGENT MANAGEMENT permission has been given
        """
        AdminConsole.logout_silently(self.admin_console)
        self.log.info("Logging in as the newly created user")
        self.admin_console.login(self.tcinputs.get('Tenant_company') + '\\' + self.tcinputs.get('user_name'),
                                 self.tcinputs.get('user_password'))
        self.log.info(f"Checking for visibility of [{text}] on Listing and Details page")
        self.log.info("Checking for Listing page")
        self.log.info("Navigating to Laptops page")
        self.navigator.navigate_to_devices()
        self.admin_console.access_tab("Laptops")
        actions_list = self.rtable.get_grid_actions_list(self.tcinputs.get('Machine_client_name'))
        if not given:
            self.log.info(f"Checking if [{text}] is not part of the Actions list")
            if text not in actions_list:
                self.log.info(f"Successful: [{text}] not in the Actions list, as expected")
            else:
                exp = f"[{text}] in the Actions list, point of failure"
                self.log.exception(exp)
                raise CVWebAutomationException(exp)
        else:
            self.log.info(f"Checking if [{text}] is part of the Actions list")
            if text in actions_list:
                self.log.info(f"Successful: [{text}] in the Actions list, as expected")
            else:
                exp = f"[{text}] not in the Actions list, point of failure"
                self.log.exception(exp)
                raise CVWebAutomationException(exp)
        self.log.info("Checking for Details page")
        self.admin_console.refresh_page()
        self.rtable.access_link(self.tcinputs.get('Machine_client_name'))
        if text == 'Activate':
            if not given:
                if not self.admin_console.check_if_entity_exists('link', text):
                    self.log.info(f"Successful: [{text}] not in the Details page, as expected")
                else:
                    exp = f"[{text}] in the Details page, point of failure"
                    self.log.exception(exp)
                    raise CVWebAutomationException(exp)
            else:
                if self.admin_console.check_if_entity_exists('xpath', f"//button[contains(.,'{text}')]"):
                    self.log.info(f"Successful: [{text}] in the Details page, as expected")
                else:
                    exp = f"[{text}] not in the Details page, point of failure"
                    self.log.exception(exp)
                    raise CVWebAutomationException(exp)
        if text == 'Deactivate':
            if not given:
                if not self.page_container.check_if_page_action_item_exists(text):
                    self.log.info(f"Successful: [{text}] not in the Actions list, as expected")
                else:
                    exp = f"[{text}] in the Actions list, point of failure"
                    self.log.exception(exp)
                    raise CVWebAutomationException(exp)
            else:
                if self.page_container.check_if_page_action_item_exists(text):
                    self.log.info(f"Successful: [{text}] in the Actions list, as expected")
                else:
                    exp = f"[{text}] not in the Actions list, point of failure"
                    self.log.exception(exp)
                    raise CVWebAutomationException(exp)
        if not given:
            self.log.info("Checking visibility without Agent Management Permission has now completed")
        else:
            self.log.info("Checking visibility with Agent Management Permission has now completed")

    def acdeac_action(self, action=None):
        """
            Helper method for performing and checking activate and deactivate actions for laptops
                Args:
                    action  (str): Activate / Deactivate to choose the flow of actions

                Returns:
                    config_status   (str): Configuration status from the Details page for laptops
        """
        self.check_visibility_of_acdeac(text=action, given=True)
        if action == 'Activate':
            self.log.info("Proceeding with CLIENT ACTIVATION from laptop actions")
        else:
            self.log.info("Proceeding with CLIENT DEACTIVATION from laptop actions")
        self.log.info("Navigating to Protect > Laptops page")
        self.navigator.navigate_to_devices()
        self.admin_console.access_tab("Laptops")
        if action == 'Activate':
            self.laptops.activate_laptop_byuser(self.tcinputs.get('Machine_client_name'))
            self.log.info("Action [Activation] completed. Checking UI and DB")
        else:
            self.laptops.deactivate_laptop(self.tcinputs.get('Machine_client_name'))
            self.log.info("Action [Deactivation] completed. Checking UI and DB")
        self.admin_console.refresh_page()
        self.rtable.access_link(self.tcinputs.get('Machine_client_name'))
        config_status = RPanelInfo(self.admin_console, title="Summary").get_details().get('Configuration status')
        return config_status

    @test_step
    def check_activate(self):
        """
            Check for visibility of Activate in listing and details and perform the action, verify UI in
            both listing and details, and verify from DB (API call)
        """
        self.log.info("Checking visibility of [Activate] and verifying the action")
        config_status = self.acdeac_action(action='Activate')
        if "active" not in config_status.lower():
            exp = "Activation not completed successfully"
            self.log.exception(exp)
            raise CVWebAutomationException(exp)
        else:
            self.log.info("[Activation] completed, verified on Command Center")
        self.log.info("Proceeding to check completed action in the Backend")
        if not (self.laptop_helper.organization.validate_client(self.tcinputs['Machine_object'], fail=False) and
                self.laptop_helper.organization.is_client_activated(self.tcinputs['Machine_client_name'],
                self.tcinputs['Default_Plan'])):
            exp = "Activation not showing in the Backend"
            self.log.exception(exp)
            raise Exception(exp)
        else:
            self.log.info("[Activation] completed, verified on the Backend")

    #
    @test_step
    def check_deactivate(self):
        """
            Check for visibility of Deactivate in listing and details and perform the action, verify UI in
            both listing and details, and verify from DB (API call)
        """
        self.log.info("Checking visibility of [Deactivate] and performing the action")
        config_status = self.acdeac_action(action='Deactivate')
        if "retired" not in config_status.lower():
            exp = "Deactivation not completed successfully"
            self.log.exception(exp)
            raise CVWebAutomationException(exp)
        else:
            self.log.info("Deactivation completed, verified on Command Center")
        self.log.info("Proceeding to check completed action in the Backend")
        if not (self.laptop_helper.organization.validate_client(self.tcinputs['Machine_object'], fail=False) and
                self.laptop_helper.organization.is_client_activated(self.tcinputs['Machine_client_name'],
                self.tcinputs['Default_Plan'])):
            self.log.info("[Deactivation] completed, verified on the Backend")
        else:
            exp = "Deactivation not showing in the Backend"
            self.log.exception(exp)
            raise Exception(exp)

    def run(self):
        """ Main function for test case execution."""
        try:
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company1'))
            self.laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])

            # -------------------------------------------------------------------------------------
            self.laptop_helper.tc.log_step("""
                        1. Create User WITH OUT Agent management permissions.
                        2. Log-in to CC with above user and verify whether user able to see Activate and deactivate 
                        options from laptop actions in UI 
                        Note: Without Agent management permissions user should not able to see the Activate / deactivate
                         options
                        3. Add Agent management permissions to the above user and re-login to adminconsole and verify 
                        able to see  Activate and deactivate options from laptop actions
                        4. With "Agent management permissions" perform activate and deactivate and verify operation 
                        completed successfully from both UI and backend 
                        Note: verify operation completed successfully from the backend

                        PRE-REQS: Have a role defined without the Agent Management Permission (true, until running code)
                    """, 200)

            # -------------------------------------------------------------------------------------

            self.refresh()
            self.laptop_helper.install_laptop(
                self.tcinputs, self.config_kwargs, self.install_kwargs, self.custompackage_kwargs
            )
            # Create a user and to that user, add associated entity: Laptops > client > role
            AdminConsole.logout_silently(self.admin_console)
            self.admin_console.login(self.tcinputs["Tenant_admin"], self.tcinputs["Tenant_password"])
            self.add_user_and_entity()

            # Check for visibility of activate & deactivate first, action shouldn't be visible in both listing
            # and details
            self.log.info("Checking Activate and Deactivate visibility")
            self.check_visibility_of_acdeac(text="Deactivate")
            AdminConsole.logout_silently(self.admin_console)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"], self.inputJSONnode['commcell']
            ["commcellPassword"])
            self.log.info("Navigating to Laptops page")
            self.navigator.navigate_to_devices()
            self.admin_console.access_tab("Laptops")
            self.rtable.access_action_item(self.tcinputs.get('Machine_client_name'), 'Deactivate', search=True)
            self.check_visibility_of_acdeac(text="Activate")
            self.log.info("Checking Activate and Deactivate visibility, completed now")

            # To the role, add the permission
            AdminConsole.logout_silently(self.admin_console)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"], self.inputJSONnode['commcell']
            ["commcellPassword"])
            self.log.info("Adding [Agent Management] Permission to the user now")
            self.log.info("Navigating to Roles page")
            self.navigator.navigate_to_roles()
            self.roles.edit_role(self.tcinputs.get('role_name'), self.tcinputs.get('role_name'),
                                 {"Add": ["Agent Management"], "Remove":
                                     ["Install Package/Update"]}, True)
            self.log.info("Added [Agent Management Permission] to the user, proceeding...")

            # Check for visibility of Deactivate in listing and details and perform the action, verify UI in
            #           both listing and details, and verify from DB (API call)
            self.check_deactivate()

            # Check for visibility of activate in listing and details and perform the action, verify UI in
            #           both listing and details, and verify from DB (API call)
            self.check_activate()

            # cleanup and delete user
            self.laptop_helper.cleanup(self.tcinputs)
            self.user.delete_user(self.tcinputs.get('user_name'))
        except Exception as excp:
            self.laptop_helper.tc.fail(excp)
            handle_testcase_exception(self, excp)
            self.laptop_helper.cleanup(self.tcinputs)

    def tear_down(self):
        """ Tear down function of this test case """
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    def refresh(self):
        """ Refresh the dicts"""
        self.config_kwargs.clear()
        self.install_kwargs.clear()
        self.custompackage_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': False
        }

        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True,
            'check_num_of_devices': False,
            'client_groups': [self.tcinputs['Default_Plan'] + ' clients', 'Laptop Clients']
        }