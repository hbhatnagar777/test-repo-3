from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from AutomationUtils import database_helper
from random import randint, choice
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
        self.name = "Plan Details Edit Validation: Edit Backup Content"

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        
        self.csdb = database_helper.CommServDatabase(self.commcell)
        self.plans_helper = PlanMain(admin_console= self.admin_console, commcell= self.commcell, csdb= self.csdb)
        self.plans = Plans(self.admin_console)

        self.plan_name = f"TC 62725 PLAN - {str(randint(0, 100000))}"
        self.csdb.execute(f"SELECT NAME FROM ARCHGROUP WITH(NOLOCK) WHERE id = {choice(list(self.commcell.storage_pools.all_storage_pools.values()))}")
        self.storage_name = self.csdb.fetch_all_rows()[0][0]
        
    def run(self):
        """Run function of this test case"""
        try:
            self.navigator.navigate_to_plan()
            
            self.plans.create_server_plan(self.plan_name, {'pri_storage': self.storage_name})
            self.log.info(f'Created Server Plan : {self.plan_name}')
            
            self.plans_helper.plan_name = self.plan_name
            
            self.plans_helper.validate_backup_content()
            
            self.plans_helper.validate_backup_system_state()
            
            self.log.info('Testcase Validation Completed.')
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        PlansHelper(commcell_obj=self.commcell).cleanup_plans('TC 62725 PLAN')