from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Plans import Plans, PlanRules
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from random import randint, choice
from Server.Plans.planshelper import PlansHelper
from cvpysdk.subclient import Subclients


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "[Plan Rules]: Basic Validation from UI"
        self.tcinputs = {}

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.password = self.inputJSONnode['commcell']['commcellPassword']
        self.admin_console.login(
            self.inputJSONnode['commcell']['commcellUsername'], self.password)
        self.navigator = self.admin_console.navigator

        self.plans_helper = PlanMain(
            admin_console=self.admin_console, commcell=self.commcell, csdb=self.csdb)
        self.sdk_plans_helper = PlansHelper(commcell_obj=self.commcell)
        self.plans = Plans(self.admin_console)
        self.plan_rules = PlanRules(self.admin_console)

        self.plan_name = self.plans_helper.plan_name = f"TC 62945 PLAN - {str(randint(0, 100000))}"

        # Get file server details
        self.file_server_name = (
            self.tcinputs.get('file_server')
            or
            choice(list(self.commcell.clients.file_server_clients.values()))[
                'displayName']
        )
        self.log.info(f'FS Client => {self.file_server_name}')
        self.client = self.commcell.clients.get(self.file_server_name)
        self.default_backupset = self.client.agents.get('File System').backupsets.get('defaultBackupSet')
        self.subclient_name = 'default'
        self.default_subclient = Subclients(self.default_backupset).get(self.subclient_name)
        self.default_subclient.plan = None
        self.client.change_company_for_client('Commcell')

        # Get storage details to create plan
        self.storage_name = (
            self.tcinputs.get('storage_pool')
            or
            self.sdk_plans_helper.get_storage_pool()
        )
        self.log.info(f'Storage Pool => {self.storage_name}')

        # create plan
        self.navigator.navigate_to_plan()
        self.plans.create_server_plan(
            self.plan_name, {'pri_storage': self.storage_name})
        self.commcell.plans.refresh()
        self.admin_console.wait_for_completion()
        self.log.info(f'Created Server Plan : {self.plan_name}')

        # set content for the plan
        self.plan = self.commcell.plans.get(self.plan_name)
        content = {
            "windowsIncludedPaths": ["Desktop"],
            "unixIncludedPaths": ["Music"]
        }
        self.plan.update_backup_content(content)

    def run(self):
        """Run function of this test case"""
        try:
            self.plan_rules.go_to_plan_rules_page()

            self.delete_existing_plan_rules()

            self.validate_add_plan_rule()

            self.validate_exclude_subclient()

            self.validate_include_subclient()

            self.validate_manual_plan_assoc()

            self.validate_manual_plan_assoc_for_multiple_subclients()

            self.validate_delete_plan_rule()

            self.validate_execution_mode_edit()

            # TODO: validate plan rule for server groups

            # TODO: validate plan rule for solutions

            # TODO: combination of above

            # TODO: edit plan rule

            # TODO: try different combination in plan rule and check subclient shows up and disappears accordingly

            self.log.info('Testcase Validation Completed.')
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        self.default_subclient.plan = None
        self.sdk_plans_helper.cleanup_plans('TC 62945 PLAN')

    @test_step
    def delete_existing_plan_rules(self):
        """Method to clean up existing plan rules"""
        for plan_rule in reversed(self.plan_rules.available_plan_rules()):
            self.plan_rules.delete(plan_rule)

    @test_step
    def validate_add_plan_rule(self):
        """Method to add simple plan rule and validate"""
        self.plan_rules.add(rule_props={'serverPlan': self.plan_name})
        self.log.info(f'Available Plan Rules => {self.plan_rules.available_plan_rules()}')
        if not self.plan_rules.is_subclient_present_in_waiting_room(self.file_server_name, self.subclient_name):
            raise CVTestStepFailure('Subclient not found in waiting  room!')
        self.log.info(
            'Successfully validated plan rule creation and subclient showing up in the waiting room!')

    @test_step
    def validate_delete_plan_rule(self):
        """Method to delete plan rule and validate"""
        plan_rule_index = self.plan_rules.available_plan_rules()[-1]
        self.plan_rules.delete(plan_rule_index)
        if plan_rule_index in self.plan_rules.available_plan_rules():
            raise CVTestStepFailure('Failed to delete plan rule!')
        self.log.info('Plan rule successfully deleted!')

    @test_step
    def validate_manual_plan_assoc(self):
        """Method to validate manual plan assoc from waiting room"""
        self.plan_rules.manually_assign_plan(
            self.file_server_name, self.subclient_name)
        self.default_subclient.refresh()
        self.log.info(
            f'Default subclient is associated to plan => {self.default_subclient.plan} & Expected Plan => {self.plan_name}')
        if self.default_subclient.plan.lower() != self.plan_name.lower():
            raise CVTestStepFailure('Manual plan association failed!')

    @test_step
    def validate_manual_plan_assoc_for_multiple_subclients(self):
        """Method to validate manual plan assoc for multiple subclients from waiting room"""
        backupsets = self.client.agents.get('File System').backupsets
        self.log.info('Creating a new backupset to test manual plan association for multiple subclients...')

        if backupsets.has_backupset('PlanRuleBackupSet'):
            backupsets.delete('PlanRuleBackupSet')

        second_backupset = backupsets.add('PlanRuleBackupSet')
        second_subclient = Subclients(second_backupset).get('default')

        # remove existing plan association
        self.default_subclient.plan = None
        second_subclient.plan = None

        self.log.info('Assigning plan to multiple subclients manually from the waiting room...')
        self.plan_rules.go_to_plan_rules_page()
        self.plan_rules.manually_assign_plan(self.file_server_name, self.subclient_name)

        # validation
        self.default_subclient.refresh()
        second_subclient.refresh()

        self.log.info(f'Default subclient is associated to plan => {self.default_subclient.plan} & Expected Plan => {self.plan_name}')
        self.log.info(f'Second subclient is associated to plan => {second_subclient.plan} & Expected Plan => {self.plan_name}')

        if self.default_subclient.plan.lower() != self.plan_name.lower():
            raise CVTestStepFailure('Manual plan association failed for first default subclient!')
        if second_subclient.plan.lower() != self.plan_name.lower():
            raise CVTestStepFailure('Manual plan association failed for second default subclient!')

        # delete the newly created backupset
        backupsets.delete('PlanRuleBackupSet')

        self.log.info('Successfully validated manual plan association for multiple subclients!')

    @test_step
    def validate_include_subclient(self):
        """Method to include subclient and validate"""
        self.plan_rules.include_subclient(
            self.file_server_name, self.subclient_name)
        if not self.plan_rules.is_subclient_present_in_waiting_room(self.file_server_name, self.subclient_name):
            raise CVTestStepFailure('Failed to include subclient!')
        self.log.info(
            'Successfully included subclient to the plan rule framework!')

    @test_step
    def validate_exclude_subclient(self):
        """Method to exclude subclient and validate"""
        self.plan_rules.exclude_subclient(
            self.file_server_name, self.subclient_name)
        if not self.plan_rules.is_subclient_excluded(self.file_server_name, self.subclient_name):
            raise CVTestStepFailure('Failed to exclude subclient!')
        self.log.info(
            'Successfully excluded subclient from the plan rule framework!')

    def edit_exec_mode(self, new_mode, excep_msg, sucess_msg):
        """Helper function to edit execution mode"""
        self.log.info(
            f'Current execution mode  => {self.plan_rules.get_execution_mode()}')
        self.log.info(f'Changing execution mode to => {new_mode}')
        self.plan_rules.set_execution_mode(new_mode)

        if self.plan_rules.get_execution_mode() != new_mode:
            raise CVTestStepFailure(excep_msg)
        self.log.info(sucess_msg)

    @test_step
    def validate_execution_mode_edit(self):
        """Method to edit execution mode and validate"""
        old_mode = self.plan_rules.get_execution_mode()
        new_mode = 'manual' if old_mode == 'automatic' else 'automatic'

        self.edit_exec_mode(
            new_mode,
            'Failed to modify execution mode',
            'Successfully modified execution mode!',
        )

        # reset to the original mode
        self.edit_exec_mode(
            old_mode,
            'Failed to revert back execution mode',
            'Successfully reverted execution mode!',
        )
