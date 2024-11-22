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
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Laptop.laptophelper import LaptopHelper
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Helper.UserHelper import UserMain
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.exceptions import CVWebAutomationException

class TestCase(CVTestCase):
    """Test Case for validating [Laptop] [AdminConsole][AdminMode]: Validation of the of laptop users from Security-->
        users"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.driver = None
        self.userHelper = None
        self.rtable = None
        self.navigator = None
        self.admin_console = None
        self.browser = None
        self.name = "[Laptop] [AdminConsole][AdminMode]: Validation of the of laptop users from Security-->users"
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.ADMINCONSOLE
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
        self.rtable = Rtable(self.admin_console)
        self.userHelper = UserMain(self.admin_console, self.commcell)
        self.admin_console.load_properties(self)
        self.driver = self.browser.driver

    @test_step
    def validate_user_information(self, user_page=False, laptop_page=False):
        """
        Navigate to Manage > Security > Users > Laptop users tab and validate user information

        Args:
            user_page   (bool): True, if current page is Users page
            laptop_page (bool): True, if current page is Devices page

        Raises:
            Exception
                -- if a singular point of difference in information exists
        """
        if user_page:
            self.log.info("Navigating to Laptop Users page")
            self.navigator.navigate_to_users()
            self.rtable.view_by_title('Laptop users')
            self.rtable.reload_data()

        if laptop_page:
            self.log.info("Navigating to Protect > Laptops > Users page")
            self.navigator.navigate_to_devices()
            self.admin_console.access_tab("Users")
            self.rtable.reload_data()

        self.log.info("Validating user information for the activating user")
        self.log.info("Searching for the user in the table")
        self.rtable.search_for(self.tcinputs['FullName'])
        displayed_dict = self.rtable.get_table_data()
        self.log.info(displayed_dict)

        self.log.info("Comparing values of displayed dict and validate dict")
        displayed_dict.pop('Actions', None)
        validate_dict = {'Email': self.tcinputs["Email"], 'Full name': self.tcinputs["FullName"],
                         'User principal name': self.tcinputs["UPN"], 'User name': self.tcinputs['Activation_User']}
        for key, value in displayed_dict.items():
            displayed_dict[key] = value[0]
        for key, value in validate_dict.items():
            if displayed_dict[key].lower() != value.lower():
                raise CVWebAutomationException(f'Value does not match for {key}, Displayed value : {displayed_dict[key]},'
                      f' Expected value : {value}')
        else:
            self.log.info('Displayed information matches with the expected information for the user')

    def execute_user_action(self, action, delete_flag=False):
        """
        Executes the listed actions for the user

        Args:
            action      (str) : Name of the action to execute
            delete_flag (bool): If True, proceed with deletion action
        """
        self.admin_console.refresh_page()
        if action == "Invite user":
            notification_text = self.rtable.access_action_item(entity_name=self.tcinputs["FullName"], action_item=action,
                                                               expect_notification=True)
            if "Successfully" in notification_text:
                self.log.info("Invite user action executed successfully")
            else:
                exp = "Invite user action was not successfully executed"
                self.log.exception(exp)
                raise Exception(exp)
        elif action == "Reset password":
            notification_text = self.rtable.access_action_item(entity_name=self.tcinputs["FullName"], action_item=action,
                                                               expect_notification=True)
            if "email will be sent" in notification_text:
                self.log.info("Reset password action executed successfully")
            else:
                exp = "Reset password action was not successfully executed"
                self.log.exception(exp)
                raise Exception(exp)
        elif action == "Delete":
            self.rtable.access_action_item(entity_name=self.tcinputs["FullName"], action_item=action)
            if not delete_flag:
                self.admin_console.click_button(value="No")
            else:
                self.admin_console.click_button(value="Yes")
                self.navigator.navigate_to_users()
                self.rtable.reload_data()
                if self.tcinputs["FullName"] not in self.rtable.get_column_data(column_name="Full name", fetch_all=True):
                    self.log.info("Delete action executed successfully")

    @test_step
    def list_user_actions_execute(self, user_page=False, laptop_page=False):
        """
        Check the available actions and execute them

        Args:
            user_page   (bool): True, if current page is Users page
            laptop_page (bool): True, if current page is Devices page
        """
        if user_page:
            self.navigator.navigate_to_users()
            self.rtable.view_by_title('Laptop users')
        if laptop_page:
            self.navigator.navigate_to_devices()
            self.admin_console.access_tab("Users")
        actions_list = self.rtable.get_grid_actions_list(self.tcinputs["FullName"])
        actions_list.sort(reverse=True)
        for action in actions_list:
            self.execute_user_action(action, laptop_page)

    def run(self):
        """ Main function for test case execution."""
        try:
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company1'))
            laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                1.  install the laptop and activate to plan with domain user
                2. Goto security--> Users -page -->click on laptop users
                3. validate below info from the laptop users
                    --> Activated user able to visible or not (Note: users should be visible without any hardrefresh of the page)
                    --> email of the user available
                    --> Full name is showing correctly
                    --> UPN is showing correctly
                4. User actions Should work
                5. Validation of users information from protect-->laptop--Users page
            """, 200)

            # -------------------------------------------------------------------------------------

            self.refresh()
            laptop_helper.install_laptop(
                self.tcinputs, self.config_kwargs, self.install_kwargs, self.custompackage_kwargs)
            AdminConsole.logout_silently(self.admin_console)
            self.admin_console.login(self.tcinputs["Tenant_admin"], self.tcinputs["Tenant_password"])

            self.log.info("Validation for Manage > Users page has started")
            self.validate_user_information(user_page=True)
            self.log.info("Validation for Manage > Users page has completed")

            self.log.info("Validation for Protect > Laptops > Users page has started")
            self.validate_user_information(laptop_page=True)
            self.log.info("Validation for Protect > Laptops > Users page has completed")

            self.log.info("Validation for User actions in Manage > Users has started")
            self.list_user_actions_execute(user_page=True)
            self.log.info("Validation for User actions in Manage > Users has completed")

            self.log.info("Validation for User actions in Protect > Laptops > Users page has started")
            self.list_user_actions_execute(laptop_page=True)
            self.log.info("Validation for User actions in Protect > Laptops > Users page has completed")

            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(excp)
            handle_testcase_exception(self, excp)
            laptop_helper.cleanup(self.tcinputs)

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
