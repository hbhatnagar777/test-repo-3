from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Plans import Plans, RPO
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from random import randint, choice, sample
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
        self.name = "[Plan Edit Testcase]: Edit Validation for Blackout window and SLA"
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
        self.rpo = RPO(self.admin_console)
        self.plan_details = PlanDetails(self.admin_console)

        self.plan_name = f"TC 63962 PLAN - {str(randint(0, 100000))}"

        # Get storage details to create plan
        self.storage_name = (
            self.tcinputs.get('storage_pool')
            or
            self.sdk_plans_helper.get_storage_pool()
        )
        self.log.info(f'Storage Pool => {self.storage_name}')

    def run(self):
        """Run function of this test case"""
        try:

            self.create_plan_with_backup_window_config()

            self.edit_backup_window()

            self.validate_labels()

            self.set_sla_period()

            self.set_system_default_sla()

            self.exclude_sla_with_reason()

            self.log.info('Testcase Validation Completed.')
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        self.sdk_plans_helper.cleanup_plans('TC 63962 PLAN')

    @test_step
    def create_plan_with_backup_window_config(self):
        """Method to validate plan creation along with backup window configuration"""
        backup_window = self.plans_helper.generate_blackout_window_config()
        full_backup_window = self.plans_helper.generate_blackout_window_config()

        self.navigator.navigate_to_plan()
        self.plans.create_server_plan(self.plan_name,
                                      {
                                          'pri_storage': self.storage_name
                                      },
                                      backup_window=backup_window,
                                      full_backup_window=full_backup_window
                                      )
        self.commcell.plans.refresh()
        self.admin_console.wait_for_completion()
        self.log.info(f'Created Server Plan : {self.plan_name}')

        self.log.info(
            'Validating if backup window values are retained post plan creation...')
        self.admin_console.wait_for_completion()
        ui_data = self.rpo.get_backup_window_config()

        expected = {
            'Backup window': backup_window,
            'Full backup window': full_backup_window
        }

        self.log.info(f'Comparing => UI: {ui_data}, Expected: {expected}')
        if sorted(ui_data.items()) != sorted(expected.items()):
            raise CVTestStepFailure(
                f"Validation failed for plan creation along with backup window, UI: {ui_data}. Expected: {expected}")

        self.log.info(
            'Validation completed for plan creation along with backup window')

    @test_step
    def edit_backup_window(self):
        """Method to validate backup window edit from plan details page"""
        backup_window = self.plans_helper.generate_blackout_window_config()
        full_backup_window = self.plans_helper.generate_blackout_window_config()

        self.plan_details.edit_backup_window(backup_window, full_backup_window)
        self.admin_console.refresh_page()

        # validation
        self.admin_console.wait_for_completion()
        ui_data = self.rpo.get_backup_window_config()

        expected = {
            'Backup window': backup_window,
            'Full backup window': full_backup_window
        }

        self.log.info(f'Comparing => UI: {ui_data}, Expected: {expected}')
        if sorted(ui_data.items()) != sorted(expected.items()):
            raise CVTestStepFailure(
                f"Validation failed for backup window edit, UI: {ui_data}. Expected: {expected}")

        self.log.info('Validation completed for backup window edit')

    @test_step
    def validate_labels(self):
        """Method to validate backup windows labels"""
        labels = self.plan_details.get_backup_window_labels()

        backup_window_labels = labels['Backup window']
        full_backup_window_labels = labels['Full backup window']

        expected = {
            'Selected Slot': 'Run interval',
            'DeSelected Slot': 'Do not run interval'
        }

        self.log.info(
            f'Comparing => UI: {backup_window_labels}, Expected: {expected}')
        if sorted(backup_window_labels.items()) != sorted(expected.items()):
            raise CVTestStepFailure(
                f"Validation failed for backup window labels, UI: {backup_window_labels}. Expected: {expected}")

        self.log.info(
            f'Comparing => UI: {full_backup_window_labels}, Expected: {expected}')
        if sorted(full_backup_window_labels.items()) != sorted(expected.items()):
            raise CVTestStepFailure(
                f"Validation failed for full backup window labels, UI: {full_backup_window_labels}. Expected: {expected}")

        self.log.info(
            'Successfully validated labels associated with backup window are correct')

    @test_step
    def set_sla_period(self):
        """Method to validate setting SLA period from plan details page"""
        self.log.info('Configuring SLA period from the available options...')
        valid_sla_periods = ['1 day', '2 days', '3 days',
                             '5 days', '1 week', '2 weeks', '1 month', '3 months']
        new_sla = choice(valid_sla_periods)
        self.__set_sla_period_and_validate(new_sla)

        self.log.info('Configuring custom SLA days...')
        custom_day = choice([num for num in range(
            1, 91) if num not in [1, 2, 3, 5, 7, 14, 30, 90]])
        self.__set_sla_period_and_validate(custom_days=custom_day)

        self.log.info(
            'Successfully validated setting SLA period from available options and custom days!')

    @test_step
    def set_system_default_sla(self):
        """Method to validate setting system default SLA from plan details page"""
        self.plan_details.use_system_default_sla()
        self.admin_console.refresh_page()
        self.admin_console.wait_for_completion()

        # validation
        ui_sla = self.plan_details.get_configured_sla()
        if 'inherited from' not in ui_sla:
            raise CVTestStepFailure(
                f'Failed to configure system default SLA, UI SLA String => {ui_sla}')

        self.log.info('Successfully validated setting system default SLA')

    @test_step
    def exclude_sla_with_reason(self):
        """Method to validate exclude SLA from plan details page"""
        self.plan_details.exclude_from_sla('This is Exclude Reason')
        self.admin_console.refresh_page()
        self.admin_console.wait_for_completion()

        ui_sla = self.plan_details.get_configured_sla()
        if ui_sla != 'Excluded from SLA':
            raise CVTestStepFailure(
                f'Failed to exclude SLA, UI SLA String => {ui_sla}')

        reason = self.plan_details.get_sla_exclude_reason()
        if reason != 'This is Exclude Reason':
            raise CVTestStepFailure(
                f'Exclude reason not matching, UI Exclude reason => {reason}')

        self.log.info('Successfully validated exclude from SLA')

    def __set_sla_period_and_validate(self, new_sla=None, custom_days=None):
        """Helper function to set sla period and validate the changes"""
        self.plan_details.set_sla_period(new_sla, custom_days)
        self.admin_console.refresh_page()
        self.admin_console.wait_for_completion()

        # validation
        ui_sla = self.plan_details.get_configured_sla()
        if custom_days:
            new_sla = f'{custom_days} days'
        expected_sla = f'SLA period is {new_sla.replace("3 months", "90 days")}'
        if ui_sla != expected_sla:
            raise CVTestStepFailure(
                f'Validation failed for setting SLA period, Expected: {expected_sla}, UI SLA string: {ui_sla}')
        self.log.info('Successfully validated setting SLA period!')
