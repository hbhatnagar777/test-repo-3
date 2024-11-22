import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVWebAutomationException,CVTestStepFailure
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages import Plans
from Web.AdminConsole.Helper import PlanHelper, global_search_helper
from Server.Plans.planshelper import PlansHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Duplicate entity] - CRUD operations for plans"
        self.plan_names = []
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.plans = None
        self.plans_helper = None
        self.plan_sdk_helper = None
        self.gs_helper = None
        self.tcinputs = {
            "Company1": None,
            "Company2": None,
            "Disk": None
        }
        """
        Note: make sure the Disk is associated to Company1 and Company2 so that the plan can be created successfully
        """

    def setup(self):
        """Setup function of this test case"""
        # open browser and login to CC
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.plans_helper = PlanHelper.PlanMain(self.admin_console)
        self.plans = Plans.Plans(self.admin_console)
        self.plan_sdk_helper = PlansHelper(commcell_obj=self.commcell)
        self.gs_helper = global_search_helper.GlobalSearchHelper(self.admin_console)

    def run(self):
        """Run function of this test case"""
        try:

            self.log.info("Step 1: Creating initial plan")
            self.create_plans(name=f'duplicate_entity - plan {str(time.time()).split(".")[0]}')
            self.validate_listing_and_global_search(suffix='Commcell', name_index=0)

            # switch to company1 tenant operator
            self.log.info("Step 2: Switching to Company1 and creating a plan with swapped case name")
            self.create_plans(name=self.plan_names[0].swapcase(), switch_company=True,
                              company=self.tcinputs['Company1'])
            self.validate_listing_and_global_search(duplicate=True, suffix=self.tcinputs['Company1'], name_index=1)

            # switch to company2 tenant operator
            self.log.info("Step 3: Switching to Company2 and creating a new plan")
            self.create_plans(name=f'Duplicate_Entity - plan {str(time.time()).split(".")[0]}', switch_company=True,
                              company=self.tcinputs['Company2'])
            self.validate_listing_and_global_search(suffix='Commcell', name_index=2)

            # rename plans
            self.log.info("Step 4: Renaming the second plan and validating the listing grid")
            self.plans.select_plan(self.plan_names[2])
            self.plans.edit_plan_name(self.plan_names[1])
            self.navigator.navigate_to_plan()

            self.validate_listing_and_global_search(duplicate=True, suffix=self.tcinputs['Company2'], name_index=1)

            # delete plans created by tenant operators
            self.log.info("Step 5: Deleting the plans and validating the final listing grid")
            self.plans.delete_plan(plan_name=self.plan_names[1], company=self.tcinputs["Company2"])
            self.plans.delete_plan(plan_name=self.plan_names[1], company=self.tcinputs["Company1"])

            self.validate_listing_and_global_search(suffix='Commcell', name_index=0)

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.cleanup()
        AdminConsole.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)

    @test_step
    def create_plans(self, name: str, switch_company: bool = False, company: str = None):
        """Create a plans and optionally switch company"""
        try:
            if switch_company:
                self.navigator.switch_company_as_operator(company)

            self.navigator.navigate_to_plan()
            storage = {'pri_storage': self.tcinputs['Disk'],
                       'pri_ret_period': '30',
                       'snap_pri_storage': None,
                       'sec_storage': None,
                       'sec_ret_period': '45',
                       'ret_unit': 'Day(s)'}
            self.plans.create_server_plan(plan_name=name, storage=storage)
            self.plan_names.append(name)
            self.navigator.navigate_to_plan()

            if switch_company:
                self.navigator.switch_company_as_operator('Reset')

        except Exception as exp:
            CVTestStepFailure(f'failed to create plans : {exp}')

    @test_step
    def validate_listing_and_global_search(self,
                                           global_search: bool = True,
                                           listing: bool = True,
                                           duplicate: bool = False,
                                           suffix: str = None,
                                           name_index: int = None):
        """Validate plans names in listing grid and global search results"""
        try:
            if global_search:
                gs_res = self.navigator.get_category_global_search("Plans", self.plan_names[name_index])
                self.log.info(f'global search result : {gs_res}')
                if not duplicate:
                    if f'{self.plan_names[name_index]} ({suffix})' in gs_res:
                        raise CVWebAutomationException(
                            "Company Name suffix displayed for non duplicate entity in global search.")
                    self.log.info('Company name suffix not displayed for non duplicate entity in global search.')
                else:
                    if f'{self.plan_names[0]} (Commcell)' not in gs_res \
                            and f'{self.plan_names[name_index]} ({suffix})' not in gs_res:
                        raise CVWebAutomationException(
                            "Company Name suffix not displayed for duplicate entity in global search results.")
                    self.log.info('Company name suffix displayed for duplicate entity in global search.')

            if listing:
                list_res = self.plans.search_for(self.plan_names[name_index])
                self.log.info(f'listing page result : {list_res}')
                if not duplicate:
                    if f'{self.plan_names[name_index]} ({suffix})' in list_res:
                        raise CVWebAutomationException(
                            "Company Name suffix displayed for non duplicate entity in listing grid.")
                    self.log.info('Company name suffix not displayed for non duplicate entity in listing grid.')

                else:
                    if f'{self.plan_names[0]} (Commcell)' not in list_res \
                            and f'{self.plan_names[name_index]} ({suffix})' not in list_res:
                        raise CVWebAutomationException(
                            "Company Name suffix not displayed for duplicate entity in listing grid.")
                    self.log.info('Company name suffix displayed for duplicate entity in listing grid.')
        except Exception as exp:
            CVTestStepFailure(f'failed to validate : {exp}')

    def cleanup(self):
        """
        Method to cleanup plans
        """
        companies = [self.tcinputs["Company1"], self.tcinputs["Company2"], None, None]
        for company in companies:
            if company:
                self.commcell.switch_to_company(company)
            else:
                self.commcell.reset_company()
            self.plan_sdk_helper.cleanup_plans('duplicate_entity - plan')
            self.commcell.reset_company()
