from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from random import randint, sample
from Web.AdminConsole.AdminConsolePages.Commcell import Commcell as CommcellPage
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
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
        self.name = "Plan Details Edit Validation: Security Tile"

    def setup(self):
        """Setup function of this test case"""
        self.log.info('Creating required entities...')
        # create required plan using api
        self.plan_name = f"TC 62738 PLAN - {str(randint(0, 100000))}"
        self.commcell.plans.add(plan_name= self.plan_name, plan_sub_type= 'Server', 
                                storage_pool_name= sample(list(self.commcell.storage_pools.all_storage_pools.keys()), 1)[0], 
                                override_entities= {})

        # create user using api
        self.user_name_a = f"DEL_automated_user_{str(randint(0, 100000))}"
        self.commcell.users.add(
            user_name=self.user_name_a,
            email=f'automateduser{str(randint(0, 100000))}@abcd.com',
            password=self.inputJSONnode['commcell']['commcellPassword'],
        )

        # create the required custom roles
        if not self.commcell.roles.has_role('Delete Plan Role'):
            self.commcell.roles.add('Delete Plan Role', ['Delete Plan'])

        if not self.commcell.roles.has_role('Edit Plan Role'):
            self.commcell.roles.add('Edit Plan Role', ['Edit Plan'])

        if not self.commcell.roles.has_role('Create Plan Role'):
            self.commcell.roles.add('Create Plan Role', ['Create Plan'])

        self.log.info('Required entities creation completed.')

        # Login as MSP
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.plans_page = Plans(self.admin_console)
        self.plan_details = PlanDetails(self.admin_console)
        self.commcell_page = CommcellPage(self.admin_console)

        # login as user A
        self.user_a_browser = BrowserFactory().create_browser_object()
        self.user_a_browser.open()
        self.user_a_admin_console = AdminConsole(self.user_a_browser, self.commcell.webconsole_hostname)
        self.user_a_admin_console.login(self.user_name_a, self.inputJSONnode['commcell']['commcellPassword'])
        self.user_a_navigator = self.user_a_admin_console.navigator
        self.user_a_plans_page = Plans(self.user_a_admin_console)
        self.user_a_plans_helper = PlanMain(self.user_a_admin_console)
        self.user_a_plans_helper.plan_name = self.plan_name
        
    def run(self):
        """Run function of this test case"""
        try:
            self.log.info('Make sure navigation is available for commcell users or else testcase would fail while navigating...')
            
            self.user_a_plans_helper.validate_permission(can_see_plan_in_listing= False)
            
            self.give_permission('View')
            self.user_a_plans_helper.validate_permission(can_see_plan_in_listing= True, can_edit_all_tiles= False, can_derive= False, can_delete= False)
            self.delete_permission('View')
            
            self.give_permission('Plan Subscription Role')
            self.user_a_plans_helper.validate_permission(can_see_plan_in_listing= True, can_edit_all_tiles= False, can_derive= False, can_delete= False)
            
            self.give_permission('Derived Plan Creator Role')
            self.user_a_plans_helper.validate_permission(can_see_plan_in_listing= True, can_edit_all_tiles= False, can_derive= True, can_delete= False)
            
            self.give_permission('Edit Plan Role')
            self.user_a_plans_helper.validate_permission(can_see_plan_in_listing= True, can_edit_all_tiles= True, can_derive= True, can_delete= False)
            
            self.give_permission('Delete Plan Role')
            self.user_a_plans_helper.validate_permission(can_see_plan_in_listing= True, can_edit_all_tiles= True, can_derive= True, can_delete= True)
            self.user_a_plans_page.delete_plan(self.plan_name)
            
            self.give_permission_on_commcell('Create Plan Role')
            # self.user_a_plans_helper.validate_permission(can_create_plans= True) # TODO
            
            self.log.info('Testcase Validation Completed.')
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        PlansHelper(commcell_obj=self.commcell).cleanup_plans('TC 62738 PLAN')
            
        self.commcell.users.refresh()
        if self.commcell.users.has_user(self.user_name_a):
            self.commcell.users.delete(self.user_name_a, self.inputJSONnode['commcell']['commcellUsername'])
            
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        AdminConsole.logout_silently(self.user_a_admin_console)
        Browser.close_silently(self.user_a_browser)
        
    def give_permission(self, permission_name):
        """Method to give permission to a user on a plan"""
        self.log.info(f'Adding Security Association : {permission_name}')
        self.plans_page.select_plan(self.plan_name)
        self.plan_details.add_security_associations({self.user_name_a : [permission_name]})
        
    def delete_permission(self, permission_name):
        """Method to revoke permission from a user on a plan"""
        self.log.info(f'Deleting Security Association : {permission_name}')
        self.plans_page.select_plan(self.plan_name)
        self.plan_details.delete_security_associations({self.user_name_a : [permission_name]})

    def give_permission_on_commcell(self, permission_name):
        """Method to add security association at commcell level"""
        self.log.info(f'Adding Security Association : {permission_name}')
        self.navigator.navigate_to_commcell()
        self.admin_console.wait_for_completion()
        self.commcell_page.add_security_associations({self.user_name_a : [permission_name]})
