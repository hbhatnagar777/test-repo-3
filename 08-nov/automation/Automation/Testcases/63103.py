from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from Server.Plans.planshelper import PlansHelper
from Server.organizationhelper import OrganizationHelper
from AutomationUtils import constants

class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "Plans: Basic CRUD UI Automation"
        self.browser = None
        self.admin_console = None
        self.plans_helper = None

    def setup(self):
        """Setup function of this test case"""
        pass
        
    def perform_validations(self):
        """Method to perform validations"""
        self.login()

        self.plans_helper.validate_listing_simple_plan_creation(storage_name=self.tcinputs.get("storageName"))
        
        self.plans_helper.validate_plan_details_loading(storage_name=self.tcinputs.get("storageName"))
        
        self.plans_helper.validate_listing_edit_plan_name(storage_name=self.tcinputs.get("storageName"))
        
        self.plans_helper.validate_listing_plan_deletion(storage_name=self.tcinputs.get("storageName"))

    def run(self):
        """Run function of this test case"""
        try:
            max_retries = 5

            for _ in range(max_retries-1):
                try:
                    self.perform_validations()
                    break
                
                except Exception as err:
                    self.log.error(err)
                    self.clean_up()
                    max_retries -= 1
                    self.log.info(f'Number of tries left => {max_retries}')
            else:
                self.perform_validations() # run last attempt without handling exception to get stacktrace in logs
            
            self.status = constants.PASSED
            self.log.info('Testcase Validation Completed.')
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        self.clean_up()

    @test_step
    def login(self):
        """Method to login to CC"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        
        self.plans_helper = PlanMain(admin_console= self.admin_console, commcell= self.commcell, csdb= self.csdb)

    @test_step
    def clean_up(self):
        """Method to clean up"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        OrganizationHelper(commcell=self.commcell).cleanup_orgs('DEL automated')
        PlansHelper(commcell_obj= self.commcell).cleanup_plans('DEL automated')