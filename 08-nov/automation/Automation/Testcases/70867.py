import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Server.Plans.planshelper import PlansHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "[Duplicate entity] - Lookup validation for plans"
        self.browser = None
        self.admin_console = None
        self.plan_name = f'Duplicate_Entity - plan {str(time.time()).split(".")[0]}'
        self.navigator = None
        self.plan_helper = None
        self.plan = None
        self.plans_api_helper = None
        self.tcinputs = {
            "Company": None,
            'Disk': None
        }

    def setup(self):
        """Setup function of this test case"""
        # open browser and login to CC
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.plan = Plans(self.admin_console)
        self.plan_helper = PlanMain(self.admin_console)
        self.plans_api_helper = PlansHelper(commcell_obj=self.commcell)

    def run(self):
        """Run function of this test case"""
        try:
            # create a plans as MSP and a duplicate plan as Tenant
            self.log.info("Step 1: Creating a plans as MSP and a duplicate plans as Tenant")
            self.create_plan(name=self.plan_name)
            self.create_plan(name=self.plan_name, switch_company=True, company=self.tcinputs['Company'])

            # validating duplicate plans lookup in various places
            self.log.info("Step 2: validating duplicate plans lookup in various places")
            validation_data = ['FILESERVER', 'VMGROUP']

            for entity_type in validation_data:
                self.validate_plans(entity_type, self.plan_name)

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.cleanup()
        AdminConsole.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)

    @test_step
    def create_plan(self, name: str, switch_company: bool = False, company: str = None):
        """Create a plan and optionally switch company"""
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
            self.plan.create_server_plan(plan_name=name, storage=storage)
            self.plan_name = name
            self.navigator.navigate_to_plan()

            if switch_company:
                self.navigator.switch_company_as_operator('Reset')
        except Exception as exp:
            CVTestStepFailure(f'failed to create plan : {exp}')

    @test_step
    def validate_plans(self, entity_type: str, plan_name: str):
        """Helper function to validate plans from dropdowns."""
        plan_list = self.plan_helper.plans_lookup(entity_type, plan_name)
        self.log.info(f"plans lookup for {entity_type}: {plan_list}")

        plan_with_suffix = [f'{self.plan_name} (Commcell)', f'{self.plan_name} ({self.tcinputs["Company"]})']

        if not all(item in plan_list for item in plan_with_suffix):
            raise CVTestStepFailure(f'Validation failed for {entity_type}')
        self.log.info(f"Validation successful for entity type : {entity_type}")

    def cleanup(self):
        """
        Method to cleanup plans
        """
        self.commcell.switch_to_company(self.tcinputs["Company"])
        self.plans_api_helper.cleanup_plans('duplicate_entity - plan')

        self.commcell.reset_company()
        self.plans_api_helper.cleanup_plans('duplicate_entity - plan')

