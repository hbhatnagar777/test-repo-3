# -*- coding: utf-8 -*-


# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Cases for validating [Laptop] [AdminConsole][AdminMode]-Validate 'Laptop configuration' option in Laptop page

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
from Web.Common.page_object import TestStep, handle_testcase_exception
from Laptop.laptophelper import LaptopHelper
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.table import Rtable

class TestCase(CVTestCase):
    """Test Case for Validating 'Laptop configuration' option in Laptop page"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.driver = None
        self.navigator = None
        self.admin_console = None
        self.browser = None
        self.name = "[Laptop] [AdminConsole][AdminMode]-Validate 'Laptop configuration' option in Laptop page"
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = True

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']["webconsoleHostname"])
        self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"], self.inputJSONnode['commcell']
                                ["commcellPassword"])
        self.navigator = self.admin_console.navigator
        self.driver = self.browser.driver

    def validate_laptop_config(self):
        """Method to list the panels and get the details from the panels after validating that the landing page is
        correct"""
        self.log.info("Navigating to Protect > Laptops page")
        self.navigator.navigate_to_devices()
        self.admin_console.access_tab('Laptops')
        self.admin_console.click_button('Laptop configuration')
        current_url = self.admin_console.current_url()
        self.log.info(f"Current URL: {current_url}")
        if "laptopsettings" not in current_url.lower():
            exp = "Failed to redirect to Laptop Configuration page"
            self.log.exception(exp)
            raise Exception(exp)
        list_of_available_panels = sorted(RPanelInfo(self.admin_console).available_panels())
        self.log.info(f"Available panels: {list_of_available_panels}")
        if list_of_available_panels != ['Automatic laptop ownership assignment', 'Laptop admins',
                                        'Retire offline laptops']:
            exp = "Mismatch in displayed panel names"
            self.log.exception(exp)
            raise Exception(exp)
        for panel in list_of_available_panels:
            if panel == "Laptop admins":
                laptop_admin_table = Rtable(self.admin_console, id="laptopAdminsTable")
                column_name = laptop_admin_table.get_visible_column_names()[0]
                self.log.info(f"Visible column: {column_name}")
                user_group_name = laptop_admin_table.get_column_data(column_name=column_name)
                if not user_group_name:
                    self.log.info(f"User/UserGroup name: No data available")
                else:
                    self.log.info(f"User/UserGroup name: {user_group_name}")
            if panel == "Automatic laptop ownership assignment":
                ownership_panel = RPanelInfo(self.admin_console, title="Automatic laptop ownership assignment")
                laptop_owner_option = ownership_panel.get_details().get("Laptop owner options")
                self.log.info(f"Laptop Owner Option: {laptop_owner_option}")
            if panel == "Retire offline laptops":
                retire_panel = RPanelInfo(self.admin_console, title="Retire offline laptops")
                retire_info = retire_panel.get_details()
                self.log.info(f"Retire laptops when they are offline for: "
                              f"{retire_info.get('Retire laptops when they are offline for')}")
                self.log.info(f"Delete retired laptops after: {retire_info.get('Delete retired laptops after')}")

    @test_step
    def try_msp_commcell_config(self):
        """Method to attempt landing on the Laptop Settings page as MSP admin of commcell"""
        self.validate_laptop_config()

    @test_step
    def try_toperator_company_config(self):
        """Method to attempt landing on the Laptop Settings page as tenant operator"""
        self.validate_laptop_config()

    @test_step
    def try_tadmin_company_config(self):
        """Method to attempt landing on the Laptop Settings page as tenant admin of company"""
        self.validate_laptop_config()

    def run(self):
        """ Main function for test case execution."""
        try:
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Commcell'))
            laptop_helper = LaptopHelper(self)

            # -------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                        Step1: In Protect-->laptops page, select Laptops tab, click 'Laptop configuration' button
                        Step2: Try above case as tenant admin and tenant operator
                    """, 200)

            self.try_msp_commcell_config()

            self.tcinputs.update(LaptopHelper.set_inputs(self, "Company1"))
            self.navigator.switch_company_as_operator(self.tcinputs["Tenant_company"])
            self.try_toperator_company_config()

            AdminConsole.logout_silently(self.admin_console)
            self.admin_console.login(self.tcinputs["Tenant_admin"], self.tcinputs["Tenant_password"],
                                     stay_logged_in=True)

            self.try_tadmin_company_config()

        except Exception as excp:
            laptop_helper.tc.fail(excp)
            handle_testcase_exception(self, excp)

    def tear_down(self):
        """ Tear down function of this test case """
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
