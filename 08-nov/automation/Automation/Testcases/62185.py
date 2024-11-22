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
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Helper.UserHelper import UserMain
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.exceptions import CVWebAutomationException

class TestCase(CVTestCase):
    """Test Case for validating [Laptop] [AdminConsole][AdminMode]: User Details Page Validation for owned laptops"""

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
        self.details_from_devices_page = {}
        self.details_from_users_page = {}

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
    def collect_laptop_info_from_devices(self):
        """
        Navigates to the Devices page and fetches details for the laptop and checks redirection from
        Owners tile in Configuration tab

        Returns:
            fetched_details (dict): laptop information collected

        Raises:
            Exception
                -- if Owner values mismatch

                -- Incorrect redirection when clicked on the Owner name

                -- Redirected to wrong user details
        """
        self.log.info("Navigating to Laptops page")
        self.navigator.navigate_to_devices()
        self.admin_console.access_tab("Laptops")
        self.rtable.search_for(self.tcinputs.get('Machine_client_name'))
        fetched_details = self.rtable.get_table_data()
        self.log.info(f"Fetched details from Devices page: {fetched_details}")
        self.log.info("Cleaning the dictionary for further processing")
        fetched_details.pop("Actions", None)
        owner_from_listing = fetched_details["Owners"][0].split(', ')
        for key, value in fetched_details.items():
            fetched_details[key] = value[0]
        fetched_details["Plan"] = fetched_details["Plans"]
        del_keys = []
        for key in fetched_details.keys():
            if key not in ["Name", "Email", "Configured", "Last backup", "Last job status",
                           "Application size", "SLA status", "Plan"]:
                del_keys.append(key)
        for key in del_keys:
            del fetched_details[key]
        fetched_details["Owners"] = owner_from_listing
        self.log.info("Checking Owner value consistency across Listing and Details pages")
        self.rtable.access_link(self.tcinputs.get('Machine_client_name'))
        self.admin_console.access_tab("Configuration")
        owner_from_details = RPanelInfo(self.admin_console, title="Owners").get_details().get('')
        if isinstance(owner_from_details, str):
            owner_from_details = [owner_from_details]
        if owner_from_details != owner_from_listing:
            exp = "Owner value inconsistency"
            self.log.exception(exp)
            raise Exception(exp)

        self.log.info("Verifying if clicking on Owner redirects to User Details page")
        if isinstance(owner_from_details, list):
            self.admin_console.select_hyperlink(owner_from_details[0])
        else:
            self.admin_console.select_hyperlink(owner_from_details)
        redirected_url = self.admin_console.current_url()
        self.log.info(f"Redirected URL: {redirected_url}")
        if "users" not in redirected_url:
            exp = "Not redirected to User Details page correctly"
            self.log.exception(exp)
            raise Exception(exp)
        email_from_details = RPanelInfo(self.admin_console, title="User summary").get_details().get('Email')
        email_from_listing = fetched_details["Email"].split(', ')[0]
        if email_from_details != email_from_listing:
            exp = "Redirected to wrong User Details"
            self.log.exception(exp)
            raise Exception(exp)
        self.log.info("Verifications and details collected successfully")
        return fetched_details

    @test_step
    def collect_laptop_info_from_users(self, owner=None):
        """
        Navigates to the User Details > Laptops page and fetches details for the laptop

        Returns:
            fetched_details (dict): laptop information collected
        """
        self.log.info("Navigating to Laptop Users page")
        self.navigator.navigate_to_users()
        self.rtable.view_by_title("Laptop users")
        self.rtable.reload_data()
        self.rtable.access_link(owner)
        self.admin_console.access_tab("Laptops")
        self.rtable.apply_filter_over_column(column_name="Name", filter_term=self.tcinputs.get('Machine_client_name'))
        fetched_details = self.rtable.get_table_data()
        owners = fetched_details["Owners"][0].split(', ')
        self.log.info("Cleaning the dictionary for further processing")
        for key, value in fetched_details.items():
            fetched_details[key] = value[0]
        del fetched_details["Owners"]
        fetched_details["Owners"] = owners
        return fetched_details

    @test_step
    def compare_details_for_laptop_info(self, expected_dict, displayed_dict):
        """
        Uses the provided information to compare the laptop information for a user

        Args:
            expected_dict (dict)  : Information from the device listing page
            displayed_dict (dict) : Information from the user's laptops page

        Raises:
            Exception
                -- if a singular point of difference between the two dictionaries
        """
        for key, value in expected_dict.items():
            if displayed_dict[key] != value:
                raise CVWebAutomationException(f'Value does not match for {key}, Displayed value : {displayed_dict[key]},'
                      f' Expected value : {value}')
        else:
            self.log.info('Displayed information matches with the expected information for the user')

    @test_step
    def validate_user_details_redirection(self, name=None):
        """
        Validates redirection from Laptops > Users page and collection of user details

        Args:
            name (str): Name of the user to redirect to

        Raises:
            Exception
                -- if incorrectly redirected upon clicking the user-name

                -- if unable to validate user information
        """
        self.log.info("Navigating to Protect > Laptops > Users page")
        self.navigator.navigate_to_devices()
        self.admin_console.access_tab("Users")
        self.log.info("Verifying if clicking on User redirects to User Details page")
        self.admin_console.select_hyperlink(link_text=name)
        redirected_url = self.admin_console.current_url()
        self.log.info(f"Redirected URL: {redirected_url}")
        if "users" not in redirected_url:
            exp = "Not redirected to User Details page correctly"
            self.log.exception(exp)
            raise Exception(exp)
        displayed_details = RPanelInfo(self.admin_console, title="User summary").get_details()
        self.log.info(displayed_details)
        for value in displayed_details.values():
            if value is None or value == '':
                exp = "Failed to validate user information"
                self.log.exception(exp)
                raise Exception(exp)
        self.log.info("Verification completed successfully")

    def run(self):
        """ Main function for test case execution."""
        try:
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company1'))
            laptop_helper = LaptopHelper(self, company=self.tcinputs["Tenant_company"])

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                Step1: install new laptop and activate to plan and makesure OSC backup job completed successfully
                Step2: log in to command center as tenant admin
                Step3: Picks the above laptop owner and  Navigate to User details page--> laptop owner-->laptops --> validate all columns of the  laptop showing correctly
                    Make sure job status column of Laptop grid shows correctly.
                Step4: Validation of users details information from Protect--> Laptop--> Users page
            """, 200)

            # -------------------------------------------------------------------------------------

            self.refresh()
            laptop_helper.install_laptop(
                self.tcinputs, self.config_kwargs, self.install_kwargs, self.custompackage_kwargs
            )
            self.admin_console.logout_silently(self.admin_console)
            self.admin_console.login(self.tcinputs["Tenant_admin"], self.tcinputs["Tenant_password"],
                                     stay_logged_in=True)

            self.details_from_devices_page = self.collect_laptop_info_from_devices()

            self.details_from_users_page = self.collect_laptop_info_from_users(self.details_from_devices_page
                                                                               .get("Owners")[0])

            self.compare_details_for_laptop_info(self.details_from_devices_page, self.details_from_users_page)

            self.validate_user_details_redirection(self.details_from_devices_page.get("Owners")[0])

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
