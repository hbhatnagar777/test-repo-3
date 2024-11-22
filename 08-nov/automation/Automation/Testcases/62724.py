from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Plans import Plans, RPO
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.Helper.PlanHelper import PlanMain
from AutomationUtils import database_helper
from random import randint, sample, choice
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
        self.name = "Plan Details Edit Validation: RPO Tile Edit Validation"

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
        self.sdk_plans_helper = PlansHelper(commcell_obj= self.commcell)
        self.plans = Plans(self.admin_console)
        self.rpo = RPO(self.admin_console)
        self.schedules = []

        self.plan_name = f"TC 62724 PLAN - {str(randint(0, 100000))}"
        self.storage_name = self.sdk_plans_helper.get_storage_pool()
        
    def run(self):
        """Run function of this test case"""
        try:
            self.navigator.navigate_to_plan()
            
            self.plans.create_server_plan(self.plan_name, {'pri_storage': self.storage_name})
            self.log.info(f'Created Server Plan : {self.plan_name}')
            
            self.plans_helper.plan_name = self.plan_name
            self.admin_console.wait_for_completion()
            
            # validate default schedule of server plan
            default_schedules = [
                "Run incremental every 1 day(s) at 9:00 PM", 
                "Run transaction log for databases every 4 hour(s) with automatic disk utilization rules"
            ]
            available_schedules = self.rpo.get_schedules()
            if any(schedule not in available_schedules for schedule in default_schedules):
                raise CVTestStepFailure(f"Default schedule's are missing!, Available Schedules => {available_schedules}")
            self.log.info('Default Schedules Verified!')
            
            # create schedules
            for _ in range(randint(2, 4)):
                self.plans_helper.validate_create_schedule(self.__get_random_schedule())
                self.admin_console.wait_for_completion()
            
            # validate edit schedule
            updated_value = self.__get_random_schedule()
            updated_value.pop('Agents', 'NA') # Editing agents not allowed

            # to update the schedule - pick any schedule which is not synthetic full
            schedule_to_be_updated = choice(self.__get_schedule_indices(synth_full=False))
            
            # editing transaction log schedule backuptype is not allowed
            if self.rpo.get_schedule_prop(schedule_to_be_updated)['BackupType'] == 'Transaction log':
                updated_value.pop('BackupType')

            self.plans_helper.validate_edit_schedule(schedule_to_be_updated, updated_value)
            self.admin_console.wait_for_completion()
            
            # validate delete schedule
            self.plans_helper.validate_delete_schedule(choice(self.__get_schedule_indices(synth_full=False)))
            self.admin_console.wait_for_completion()
            
            # validate rpo for modified schedule during plan creation
            self.validate_rpo_during_plan_creation()
            
            self.log.info('Testcase Validation Completed.')
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        self.sdk_plans_helper.cleanup_plans(marker= 'TC 62724 PLAN')
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    def __get_schedule_indices(self, synth_full=True, transaction_log=True) -> list:
        """Method to get schedule indices based on the given parameters.
        
        This method returns a list of indices corresponding to the available schedules based on the given parameters, which can be used to select a schedule for further operations on UI
        
        Parameters:
        - synth_full (bool): Flag indicating whether synthetic full schedules should be included (default: True).
        - transaction_log (bool): Flag indicating whether transaction log schedules should be included (default: True).
        
        Returns:
        - list: A list of indices representing the available schedules that meet the specified criteria.
        """
        available_schedules = self.rpo.get_schedules()
        
        if synth_full and transaction_log:
            return list(range(1, len(available_schedules) + 1)) # return all schedule indices
        
        excluded_schedules = []
        if not synth_full:
            excluded_schedules.append("synthetic full")
        if not transaction_log:
            excluded_schedules.append("transaction log")

        # return indices of schedules that do not contain any of the excluded schedules
        return [i+1 for i, schedule in enumerate(available_schedules) if all(exclude not in schedule for exclude in excluded_schedules)]

    def __get_random_schedule(self):
        """Method to get random schedule"""
        schedule = {
            'BackupType' : choice(self.rpo.backup_types),
            'Agents'     : choice(self.rpo.agents),
            'FrequencyUnit' : choice(self.rpo.frequency_units)
        }

        if schedule['Agents'] == 'All agents':
            schedule.pop('Agents') # this is default value so remove

        if schedule['FrequencyUnit'] != 'Year':
            schedule['Frequency'] = str(randint(10, 60))

        if schedule['FrequencyUnit'] not in ['Minute(s)', 'Hour(s)']:
            schedule[
                'StartTime'
            ] = f'{randint(1, 12):02d}:{randint(0, 59):02d} ' + str(
                choice(['am', 'pm'])
            )

        self.log.info(f'Generated Random Schedule : {schedule}')
        return schedule

    def validate_rpo_during_plan_creation(self):
        """Method to validate RPO during plan creation"""
        self.plan_name_2, schedule = f'{self.plan_name} - 2', self.__get_random_schedule()

        self.navigator.navigate_to_plan()
        self.plans.create_server_plan(self.plan_name_2, {'pri_storage': self.storage_name}, [schedule])
        self.admin_console.wait_for_completion()
        self.log.info(f'Created Server Plan : {self.plan_name_2}')

        # validate rpo for newly added schedule during plan creation by excluding synthetic full
        schedule_to_be_validated = choice([schedule for schedule in self.rpo.get_schedules() if 'synthetic full' not in schedule])
        self.plans_helper.validate_schedule_properties(schedule_to_be_validated, schedule)