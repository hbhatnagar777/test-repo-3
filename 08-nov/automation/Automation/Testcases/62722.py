from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from AutomationUtils import database_helper
from random import randint, sample, choice
from Server.organizationhelper import OrganizationHelper
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
        self.name = "Plan Details Edit Validation: Inheritance Tile"

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.org_helper = OrganizationHelper(self.commcell)
        self.csdb = database_helper.CommServDatabase(self.commcell)
        self.plans_helper = PlanMain(admin_console= self.admin_console, commcell= self.commcell, csdb= self.csdb)
        self.plans = Plans(self.admin_console)
        
        self.csdb.execute(f"SELECT NAME FROM ARCHGROUP WHERE id = {sample(list(self.commcell.storage_pools.all_storage_pools.values()), 1)[0]}")
        self.storage_name = self.csdb.fetch_all_rows()[0][0]
        
        # NAMES
        random_num = str(randint(0,100000))
        self.plan_name = "TC 62722 UI PLAN - " + random_num
        self.sdk_plan_name = "TC 62722 SDK PLAN - " + random_num
        self.sdk_org_name = "TC 62722 SDK ORG - " + random_num
        self.msp_derived_plan = "TC 62722 MSP DERIVED - " + random_num
        self.ta_derived_plan = "TC 62722 TA DERIVED - " + random_num
        
    def run(self):
        """Run function of this test case"""
        try:
            self.navigator.navigate_to_plan()
            
            self.plans.create_server_plan(self.plan_name, {'pri_storage': self.storage_name})
            self.log.info(f'Created Server Plan : {self.plan_name}')
            
            self.plans_helper.plan_name = self.plan_name
            
            self.plans_helper.validate_override_restrictions()
            
            self.__create_plan_and_org()
            
            self.derive_plan_as_msp()
                        
            self.derive_plan_as_tenant_admin()
            
            self.log.info('Testcase Validation Completed.')
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        self.browser.close()
        self.commcell.organizations.refresh()
        self.org_helper.delete_company(wait=True, timeout=10)
        self.commcell.plans.refresh()
        for plan in [self.msp_derived_plan, self.plan_name, self.sdk_plan_name]:
            self.log.info(f'Cleaning up plan : {plan}')
            if self.commcell.plans.has_plan(plan):
                self.commcell.plans.delete(plan)
        PlansHelper(commcell_obj=self.commcell).cleanup_plans('TC 62722')
        
    @test_step
    def __create_plan_and_org(self):
        """Method to create plan, organization and share plan with org"""
        # create plan
        self.commcell.plans.add(self.sdk_plan_name, 'Server', self.storage_name, override_entities= {})
        
        # create company
        organization = self.org_helper.setup_company(company_name= self.sdk_org_name, plans=[self.sdk_plan_name], 
                                                     ta_password= self.inputJSONnode['commcell']['commcellPassword'])
        self.tenant_admin_username = organization['ta_name']
        
        self.log.info(f'Associated plan : {self.sdk_plan_name} with the company : {self.sdk_org_name}')
        
    @test_step
    def derive_plan_as_msp(self):
        """Method to validate plan derive as MSP"""
        override_storage = choice([True, False])
        override_rpo     = choice([True, False])
        self.log.info(f'Override Storage: {override_storage}, Override RPO: {override_rpo}')
        
        self.plans.create_derived_server_plan(self.sdk_plan_name, self.msp_derived_plan, override_storage, override_rpo)
        self.log.info('MSP derived plan successfully!')
        
    @test_step
    def derive_plan_as_tenant_admin(self):
        """Method to derive plan as tenant admin"""
        self.admin_console.logout()
        self.admin_console.login(self.tenant_admin_username, self.inputJSONnode['commcell']['commcellPassword'])
        self.plans.create_derived_server_plan(self.sdk_plan_name, self.ta_derived_plan)