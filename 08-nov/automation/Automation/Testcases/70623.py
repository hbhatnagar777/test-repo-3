from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.exceptions import CVTestStepFailure
from Server.regions_helper import RegionsHelper
from Server.Plans.planshelper import PlansHelper
import random


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Plan Backup destination validation: overlapping location in plan"
        self.key_names = None
        self.SP = None
        self.plan_name = None
        self.plan = None
        self.regions = None
        self.plan_helper = None
        self.region_helper = None

    def setup(self):
        """Setup function of this test case"""
        self.plan = self.commcell.plans
        self.region_helper = RegionsHelper(self.commcell)
        self.plan_helper = PlansHelper(commcell_obj=self.commcell)

        self.log.info('creating regions with overlapping locations')

        self.regions = self.region_helper.create_overlapping_location_region(['Pune'], 3)
        self.SP = self.commcell.version
        self.key_names = ['allowOverlappingLocationInPlan', 'restrictOverlappingLocationInPlan']

        self.log.info('Checking if additional setting already set at CS...')
        for key in self.key_names:
            for set_key in self.commcell.get_configured_additional_setting():
                if key == set_key.get('keyName'):
                    self.log.info(f'Additional setting [{key}] already set at CS, removing it.')
                    self.commcell.delete_additional_setting(category='CommServDB.GxGlobalParam',
                                                            key_name=key)

    @test_step
    def create_plan(self, expected_success: bool) -> bool:
        """Method to create plan with multiple regions having overlapping zones"""
        self.plan_name = f'overlapping_zones_plan_{random.randint(1, 1000)}'
        storage = self.plan_helper.get_storage_pool()
        backup_destination = [{"storage_name": storage, "region_name": self.regions[0]},
                              {"storage_name": storage, "region_name": self.regions[1]}]
        try:
            self.log.info(f'creating server plan with regions {self.regions[:2]}')
            self.plan.create_server_plan(plan_name=self.plan_name, backup_destinations=backup_destination)
            self.log.info(f'Successfully created server plan {self.plan_name}')
            success_flag = True
        except Exception as exp:
            self.log.warn(f"[EXPECTED ERROR] {exp}")
            success_flag = False

        if expected_success != success_flag:
            self.log.error(
                f'Create Plan Validation Failed: Expected success {expected_success} but got {success_flag}')
            raise CVTestStepFailure(f'Create Plan Validation Failed')
        return success_flag

    @test_step
    def add_copy(self, expected_success: bool) -> bool:
        """Method to add a new copy to an existing plan with regions having overlapping zones."""
        storage = self.plan_helper.get_storage_pool()
        try:
            self.plan.refresh()
            if self.plan_name is None:
                self.log.error("Plan name is not set.")
                return False

            self.log.info(f'Adding region {self.regions[2]} to the plan {self.plan_name}')
            self.plan.get(self.plan_name).add_copy(copy_name="Primary", storage_pool=storage,
                                                   region=self.regions[2])
            self.log.info(f'Successfully added region {self.regions[2]} to the plan {self.plan_name}')
            success_flag = True
        except Exception as exp:
            self.log.warn(f'[EXPECTED ERROR] {exp}')
            success_flag = False

        if expected_success != success_flag:
            self.log.error(
                f'add copy Validation Failed: Expected success {expected_success} but got {success_flag}')
            raise CVTestStepFailure(f'Add Copy Validation Failed.')

        return success_flag

    @test_step
    def validate_setting(self, key_expected_condition: bool, setting_key: str, setting_name: str,
                         expected_behavior: str):
        """Method to validate the addition of a setting and its effect on plan creation and copy addition."""
        self.log.info(f'Starting validation for setting [{setting_name}]')

        if self.create_plan(not key_expected_condition) and self.add_copy(not key_expected_condition):
            # Add the setting
            self.log.info(f'Adding setting [{setting_name}]')
            self.commcell.add_additional_setting(key_name=setting_key,
                                                 category='CommServDB.GxGlobalParam',
                                                 data_type='INTEGER',
                                                 value='1')
            self.commcell.refresh()

            # Check if the expected behavior matches the actual outcome
            if self.create_plan(key_expected_condition) == key_expected_condition and\
                    self.add_copy(key_expected_condition) == key_expected_condition:
                self.log.info('Validation Successful')
            else:
                raise CVTestStepFailure(f'[{setting_name}] Key validation Failed! {expected_behavior}')

    def run(self):
        """Run function of this test case"""
        try:
            if '11.36' in self.SP:
                self.validate_setting(key_expected_condition=True,
                                      setting_key=self.key_names[0],
                                      setting_name="allowOverlappingLocationInPlan",
                                      expected_behavior="Unable to create plan/add copy with overlapping zones")
            else:
                self.validate_setting(key_expected_condition=False,
                                      setting_key=self.key_names[1],
                                      setting_name="restrictOverlappingLocationInPlan",
                                      expected_behavior="Plan with overlapping zones created")
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.plan_helper.cleanup_plans("overlapping_zones_plan_")
        self.region_helper.cleanup("overlapping_zones_region_")
        for key in self.key_names:
            self.commcell.delete_additional_setting(key_name=key,
                                                    category='CommServDB.GxGlobalParam')
