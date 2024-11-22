# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Test Cases for validating [Laptop] [AdminConsole][AdminMode]: Validation of the of laptop users from Security-->
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
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Web.AdminConsole.AdminConsolePages.Plans import Plans

from Web.AdminConsole.Components.table import Rtable
from Web.Common.page_object import handle_testcase_exception, TestStep
from Laptop.laptophelper import LaptopHelper

class TestCase(CVTestCase):
    """Test Case for validating Laptop Plan creation in two ways"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole] - Laptop Plan creation validation"
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.ADMINCONSOLE
        self.driver = None
        self.browser = None
        self.admin_console = None
        self.plan_obj = None
        self.plans = None
        self.plan1_name = None
        self.plan2_name = None
        self.rtable = None
        self.navigator = None
        self.plan_inputs = None
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
        self.plans = Plans(self.admin_console)
        self.plan_obj = PlanMain(self.admin_console)
        self.plan1_name = "Automation_LPviaPlans_63828"
        self.plan2_name = "Automation_LPviaDevices_63828"
        self.rtable = Rtable(self.admin_console)

    def validate_plan_page_redirection(self, is_plan_page=False):
        self.log.info("Validating redirection")
        self.rtable.access_toolbar_menu(self.admin_console.props['label.createProfile'])
        if is_plan_page:
            self.rtable.access_menu_from_dropdown('Laptop')
        self.admin_console.wait_for_completion()
        current_url = self.admin_console.current_url()
        self.log.info(f"Redirected_url: {current_url}")
        if "createlaptopplan" not in current_url.lower():
            exp = "Not redirected to Laptop Plan creation page correctly"
            self.log.exception(exp)
            raise Exception(exp)
        self.log.info("Redirection validated successfully")

    @test_step
    def create_lap_plan(self, via_laptop=False):
        """Method for creation of laptop plan"""
        if not via_laptop:
            self.log.info("Navigating to Manage > Plans page")
            self.plan_obj.plan_name = {"laptop_plan": self.plan1_name}
            self.navigator.navigate_to_plan()
            self.validate_plan_page_redirection(is_plan_page=not via_laptop)
            self.navigator.navigate_to_plan()
            plan_names = self.rtable.get_column_data("Plan name")
            if self.plan1_name in plan_names:
                self.plans.delete_plan(self.plan1_name)
                self.admin_console.wait_for_completion()
        else:
            self.log.info("Navigating to Protect > Laptops > Plans page")
            self.plan_obj.plan_name = {"laptop_plan": self.plan2_name}
            self.navigator.navigate_to_devices()
            self.admin_console.access_tab("Plans")
            self.validate_plan_page_redirection()
            self.navigator.navigate_to_devices()
            self.admin_console.access_tab("Plans")
            plan_names = self.rtable.get_column_data("Plan name")
            if self.plan2_name in plan_names:
                self.plans.delete_plan(self.plan2_name)
                self.admin_console.wait_for_completion()

        storage = {'pri_storage': self.tcinputs['Primary_storage']}

        if not via_laptop:
            self.plans.create_laptop_plan(plan_name=self.plan1_name,
                                          storage=storage,
                                          retention={},
                                          alerts={})
        else:
            self.plans.create_laptop_plan(plan_name=self.plan2_name,
                                          storage=storage,
                                          retention={},
                                          alerts={},
                                          from_plans_page=not via_laptop)
        self.admin_console.wait_for_completion()

    @test_step
    def validate_lap_plan(self, plan_name):
        """Method to validate the details of the laptop plan created"""
        self.log.info("Validation of laptop plan has started")
        validation_dict = {'PlanName': plan_name,
                           'General': {'Number of users': '0', 'Number of laptops': '0'},
                           'Associated users and user groups': {},
                           'Backup content': {'Windows': ['Desktop', 'Documents', 'User Settings'],
                                              'Unix': ['Desktop', 'Documents'],
                                              'Mac': ['Desktop', 'Documents', 'User Settings']},
                           'Allowed features': {'DLP': True},
                           'Security': {'master': [['Plan Creator Role']]},
                           'Override restrictions': {'Allow plan to be overridden': False},
                           'RPO': {'Backup frequency': 'Runs every 8 hour(s)',
                           'SLA': 'Use system default SLA'},
                           'Retention': {'Deleted item retention': '2 year(s)', 'File versions': '5 versions'},
                           'Alerts': {},
                           'Options': {'File system quota': 'Infinite'},
                           'Network throttle': {'Throttle send': '5000 Kbps', 'Throttle receive': 'No limit'},
                           'Retire offline laptops': {'Retire laptops when they are offline': '183 days',
                                                      'Delete retired laptops': '1 year'},
                           'Tags': {},
                           'Backup destinations': [self.tcinputs["Primary_storage"]]}
        self.navigator.navigate_to_plan()
        self.rtable.reload_data()
        self.plan_obj.validate_plan_details(validation_dict=validation_dict)
        self.log.info("Validation of laptop plan has completed")

    def run(self):
        """Main function for the test case execution"""
        try:
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Commcell'))
            laptop_helper = LaptopHelper(self)

            # -------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                        Create laptop plan via two ways and validate all tiles are showing correct default values
                        1. Protect-->Laptop -->plans -->create plan (after clicking on create plan button it 
                           should redirect to #/createLaptopPlan page and plan should be created successfully) 
                        2. Plans -->Laptop --> createplan -->Laptop -->Plan creation should be successful
                    """, 200)

            # -------------------------------------------------------------------------------------
            self.log.info("Attempting to create laptop plan via Manage > Plans > Create Laptop Plan")
            self.create_lap_plan()
            self.log.info("Laptop plan created successfully")

            self.log.info("Attempting to validate the laptop plan created via Plans page")
            self.validate_lap_plan(plan_name=self.plan1_name)
            self.log.info("Laptop plan validation completed successfully")

            self.log.info("Attempting to create laptop plan via Protect > Laptops > Plans")
            self.create_lap_plan(via_laptop=True)
            self.log.info("Laptop plan created successfully")

            self.log.info("Attempting to validate the laptop plan created via Devices page")
            self.validate_lap_plan(plan_name=self.plan2_name)
            self.log.info("Laptop plan validation completed successfully")

        except Exception as excp:
            laptop_helper.tc.fail(excp)
            handle_testcase_exception(self, excp)

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            self.navigator.navigate_to_plan()
            self.plans.delete_plan(self.plan1_name)
            self.plans.delete_plan(self.plan2_name)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
