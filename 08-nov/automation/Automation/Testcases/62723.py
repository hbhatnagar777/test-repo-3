from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Plans import Plans, RPO
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from AutomationUtils import database_helper
from random import randint, sample, choice
from Web.Common.exceptions import CVTestStepFailure
from selenium.common.exceptions import ElementClickInterceptedException
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
        self.name = "Plan Details Edit Validation: Tags, Snapshot options, Database options Tile"

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator

        self.csdb = database_helper.CommServDatabase(self.commcell)
        self.plans_helper = PlanMain(
            admin_console=self.admin_console, commcell=self.commcell, csdb=self.csdb)
        self.sdk_plans_helper = PlansHelper(commcell_obj=self.commcell)
        self.plans = Plans(self.admin_console)
        self.plan_details = PlanDetails(self.admin_console)
        self.rpo = RPO(self.admin_console)

        self.plan_name = f"TC 62723 PLAN - {str(randint(0, 100000))}"
        self.storage_name = self.sdk_plans_helper.get_storage_pool(dedupe=False)

    def run(self):
        """Run function of this test case"""
        try:
            self.navigator.navigate_to_plan()

            self.plans.create_server_plan(
                self.plan_name, {'pri_storage': self.storage_name, 'snap_pri_storage': self.storage_name})
            self.log.info(f'Created Server Plan : {self.plan_name}')

            self.plans_helper.plan_name = self.plan_name

            self.plans_helper.validate_snapshot_options()

            self.validate_database_options()

            self.plans_helper.validate_tags()

            self.log.info('Testcase Validation Completed.')
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        self.sdk_plans_helper.cleanup_plans('TC 62723 PLAN')

    def validate_tlog_ui_values(self):
        """Helper function to check if UI values are matching expected values"""
        self.admin_console.refresh_page()
        self.admin_console.wait_for_completion()
        ui_values = self.rpo.get_schedule_prop(self.tlog_index)

        def compare_dicts(expected_values:dict, ui_data:dict) -> bool:
            for expected_key, expected_value in expected_values.items():
                if expected_key in ui_data and str(expected_value).lower() != str(ui_data[expected_key]).lower():
                        return False
            return True
        
        if not compare_dicts(self.tlog_values, ui_values):
            raise CVTestStepFailure(f'Expected values not matching with UI values => {self.tlog_values} != {ui_values}')
        # for key, value in self.tlog_values.items():  # check if all expected values present in ui
        #     if key not in ui_values or ui_values[key] != value:
        #         raise CVTestStepFailure(
        #             f'Expected values not matching with UI values => {self.tlog_values} != {ui_values}')
        self.log.info('UI values and expected values are matching!')

    @test_step
    def validate_default_tlog_values(self):
        """Method to validate default values of transaction log schedule"""
        self.tlog_values = {
            'BackupType': 'Transaction log',
            'Agents': 'Databases',
            'Frequency': 4,
            'FrequencyUnit': 'Hour(s)',
            'AdvanceOptions': True,
            'ScheduleMode': 'Based on automatic schedule settings',
            'DiskCache': False
        }
        self.validate_tlog_ui_values()

    @test_step
    def edit_and_validate_tlog_schedule(self):
        """Method to validate transaction log schedule edit"""
        self.tlog_values = self.rpo.get_schedule_prop(self.tlog_index)
        freq_unit = choice(self.rpo.frequency_units)
        freq = randint(10, 60) if freq_unit != 'Year' else 1
        self.tlog_values |= {'FrequencyUnit': freq_unit, 'Frequency': freq}
        for prop in ['ScheduleMode', 'DiskCache', 'CommitEvery']:
            self.tlog_values.pop(prop, None)

        if freq_unit in ['Minute(s)', 'Hour(s)']:
            schedule_mode = choice(
                ['Continuous', 'Based on automatic schedule settings'])
            self.tlog_values['ScheduleMode'] = schedule_mode
            if 'automatic' in schedule_mode:
                self.tlog_values |= {'DiskCache': True,
                                     'CommitEvery': randint(1, 24)}
        else:
            self.tlog_values[
                'StartTime'
            ] = f"{randint(1, 12):02d}:{randint(0, 59):02d} {choice(['AM', 'PM'])}"

        self.log.info(f'Editing T-log schedule with values: {self.tlog_values}')
        self.rpo.edit_schedule(self.tlog_index, self.tlog_values)

        self.log.info('Validating edited T-log schedule values on UI')
        self.validate_tlog_ui_values()

    @test_step
    def change_tlog_to_other_types(self):
        """Method to validate if T-log schedules can be switched to any other types"""
        self.tlog_values = self.rpo.get_schedule_prop(self.tlog_index)
        backup_type = choice(['Differential', 'Full', 'Incremental'])
        self.tlog_values.update({'BackupType': backup_type})
        for prop in ['ScheduleMode', 'DiskCache', 'CommitEvery']:
            self.tlog_values.pop(prop, None)

        if backup_type != 'Full':
            value, unit = (randint(1, 999), choice(['Day(s)', 'Week(s)']))
            if unit == 'Day(s)' and value % 7 == 0:
                self.tlog_values.update(
                    {'ForceFullBackup': (value//7, 'Week(s)')})

        self.rpo.edit_schedule(self.tlog_index, {'BackupType': backup_type})
        self.validate_tlog_ui_values()

    @test_step
    def switch_back_to_tlog(self):
        """Method to switch the schedule type back to tlog"""
        self.tlog_values = self.rpo.get_schedule_prop(self.tlog_index)
        self.tlog_values.update({'BackupType': 'Transaction log'})
        self.tlog_values.pop('ForceFullBackup', None)
        if self.tlog_values['FrequencyUnit'] in ['Minute(s)', 'Hour(s)']:
            self.tlog_values.update(
                {'ScheduleMode': 'Based on automatic schedule settings', 'DiskCache': False})
            self.tlog_values.pop('StartTime', None)
        self.rpo.edit_schedule(
            self.tlog_index, {'BackupType': 'Transaction log'})
        self.validate_tlog_ui_values()

    @test_step
    def create_and_validate_tlog_schedule(self):
        """Method to validate creation of transaction log schedule"""
        self.rpo.create_schedule({'BackupType': 'Transaction log'})
        self.admin_console.refresh_page()
        ui_available_schedules = self.rpo.get_schedules()
        if all(
            'transaction' not in schedule for schedule in ui_available_schedules
        ):
            raise CVTestStepFailure(
                f'Failed to add new transaction log schedule: {ui_available_schedules}')
        self.log.info('Succesfully verified that transaction log schedule can be added!')

    @test_step
    def validate_no_duplicate_tlog_schedule_creation(self):
        """Method to check that the duplicate T-log schedule adding is not possible"""
        try:
            self.rpo.create_schedule({'BackupType': 'Transaction log'})
        except ElementClickInterceptedException as err:
            self.log.info(err)
        self.admin_console.refresh_page()
        ui_available_schedules = self.rpo.get_schedules()
        if (
            sum('transaction' in schedule for schedule in ui_available_schedules)
            > 1
        ):
            raise CVTestStepFailure(
                f'Duplicate transaction log schedule can be added! => {ui_available_schedules}')

    @test_step
    def delete_and_validate_tlog_schedule(self):
        """Method to validate deletion of transaction log schedule"""
        tlog_index = self.rpo.get_schedule_index('Transaction Log')[0]
        self.rpo.delete_schedule(tlog_index)
        self.admin_console.refresh_page()
        ui_available_schedules = self.rpo.get_schedules()
        if any('transaction' in schedule for schedule in ui_available_schedules):
            raise CVTestStepFailure(
                f'Failed to delete transaction log schedule: {ui_available_schedules}')

    @test_step
    def validate_tlog_schedule_on_ui(self):
        """Method to validate tlog wrt applicable solutions"""
        self.plan_details.edit_applicable_solns(solutions=['File Servers'])
        ui_available_schedules = self.rpo.get_schedules()
        if any('transaction' in schedule for schedule in ui_available_schedules):
            raise CVTestStepFailure(
                f'Transaction log schedule visible for Non DB plan: {ui_available_schedules}')

    def validate_database_options(self):
        """Method to validate database options"""
        self.plans.select_plan(self.plan_name)
        self.tlog_index = self.rpo.get_schedule_index('Transaction Log')[0]

        self.validate_default_tlog_values()

        self.edit_and_validate_tlog_schedule()

        # self.change_tlog_to_other_types() # Changing transaction to any other backup type is blocked for now

        # self.switch_back_to_tlog() 

        self.delete_and_validate_tlog_schedule()

        self.create_and_validate_tlog_schedule()

        self.validate_no_duplicate_tlog_schedule_creation()

        self.validate_tlog_schedule_on_ui()

        self.log.info('Database options validations are completed!')
