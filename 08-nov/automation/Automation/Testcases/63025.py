from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Plans import Plans, RPO
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from AutomationUtils import database_helper
from random import randint, sample, choice
from Web.Common.exceptions import CVTestStepFailure

class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "[Metallic]: Simplified Plan View Validation"

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
        self.plan_details = PlanDetails(self.admin_console)
        self.rpo = RPO(self.admin_console)

        self.csdb.execute(f"SELECT NAME FROM ARCHGROUP WHERE id = {sample(list(self.commcell.storage_pools.all_storage_pools.values()), 1)[0]}")
        self.storage_name  = self.csdb.fetch_all_rows()[0][0]
        self.cc_plan_name = f"TC 63025 UI PLAN - {str(randint(0, 100000))}"
        self.sdk_plan_name = f"TC 63025 SDK PLAN - {str(randint(0, 100000))}"
        
    def run(self):
        """Run function of this test case"""
        try:
            self.validation_for_cc_created_plan()
            
            self.validation_for_api_created_plan()
            
            self.log.info('Testcase Validation Completed.')
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        self.commcell.plans.refresh()
        for plan_name in [self.cc_plan_name, self.sdk_plan_name]:
            if self.commcell.plans.has_plan(plan_name):
                self.commcell.plans.delete(plan_name)
        self.browser.close()
        
    @test_step
    def validation_for_cc_created_plan(self):
        """Method to validate plan created on Command Center"""
        self.navigator.navigate_to_plan()
        
        self.plans.create_server_plan(self.cc_plan_name, {'pri_storage': self.storage_name})
        self.log.info(f'Created Server Plan : {self.cc_plan_name}')
                                
        if not self.plan_details.is_plan_in_advanced_view():
            raise CVTestStepFailure('Command Center created plan is not loaded in advanced view')
        
        if self.plan_details.is_advance_view_toggle_visible():
            raise CVTestStepFailure('Command Center create plan is not restricted to Advanced View. User gets toggle to switch back to Simplified view')
        
    @test_step
    def validation_for_api_created_plan(self):
        """Method to validate api created plan"""
        self.commcell.plans.add(self.sdk_plan_name, 'Server', self.storage_name)
        self.plans.select_plan(self.sdk_plan_name)
        
        if self.plan_details.is_plan_in_advanced_view():
            raise CVTestStepFailure('API created plan is loading in advanced view')
        
        if not self.plan_details.is_advance_view_toggle_visible():
            raise CVTestStepFailure('Advance view toggle not available on simplified plan view')
        
        self.plan_details.enable_advanced_view()
        if not self.plan_details.is_plan_in_advanced_view():
            raise CVTestStepFailure('Failed to switch to Advanced View')
        
        self.plan_details.disable_advanced_view()
        if self.plan_details.is_plan_in_advanced_view():
            raise CVTestStepFailure('Failed to switch back to Simplified View')
        
        # EDIT RPO FROM SIMPLIFIED PLAN VIEW
        self.plans_helper.validate_edit_schedule(1, {
            'BackupType' : choice(self.rpo.backup_types),
            'FrequencyUnit' : choice(self.rpo.frequency_units)
        })
        self.log.info('RPO can be edited on simplified view!')
        
        self.plan_details.enable_advanced_view()
        
        self.plan_details.edit_plan_backup_content('Windows', content_folders= ['Desktop' , 'Documents' , 'Downloads'])
        
        if self.plan_details.is_advance_view_toggle_visible():
            raise CVTestStepFailure('Toggle still visible after editing panel from advanced view')
        
        