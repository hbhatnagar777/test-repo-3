"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
import random

from AutomationUtils.cvtestcase import CVTestCase
from Server.regions_helper import RegionsHelper
from Server.Plans import planshelper
from Web.Common.page_object import handle_testcase_exception, TestStep
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
        self.calculated_region = None
        self.name = "Workload and Backup destination Regions for physical clients(API)"
        self.regions_helper = None
        self.plan_helper = None
        self.non_elastic_plan = None
        self.elastic_plan = None
        self.client_name = None

    def setup(self):
        """Setup function of this test case"""
        self.regions_helper = RegionsHelper(self.commcell)
        self.plan_helper = planshelper.PlansHelper(commcell_obj=self.commcell)

        # get a random file server client
        self.commcell.clients.refresh()
        self.client_name = random.choice(list(self.commcell.clients.file_server_clients.keys()))
        self.log.info(f"client to be used for the testcase: {self.client_name}")

        # create elastic and non elastic plans
        name = [f'regions_automation_plan_{random.randint(0, 10000)}_elastic',
                f'regions_automation_plan_{random.randint(0, 10000)}_non_elastic']
        storage = self.plan_helper.get_storage_pool()
        self.elastic_plan = \
            self.commcell.plans.create_server_plan(plan_name=name[0],
                                                   backup_destinations={"storage_name": storage,
                                                                        "region_name": "asia"}).plan_name
        self.non_elastic_plan = \
            self.commcell.plans.create_server_plan(plan_name=name[1],
                                                   backup_destinations={
                                                       "storage_name": storage}).plan_name
        self.log.info(f'Successfully created temp plans : {self.elastic_plan}, {self.non_elastic_plan}')

    @test_step
    def reset_workload_region(self):
        """ Pick a physical client and set the workload region to None"""
        self.regions_helper.edit_region_of_entity(entity_type="CLIENT", entity_name=self.client_name,
                                                  entity_region_type="WORKLOAD")
        response = self.regions_helper.get_region_of_entity(entity_type="CLIENT", entity_name=self.client_name,
                                                            entity_region_type="WORKLOAD")
        if response:
            raise CVTestStepFailure("validation failed, response returned is %s, expected response is None." % response)

    @test_step
    def calculate_region(self):
        """calculate workload region and assign it to the client"""
        self.calculated_region = self.regions_helper.validate_calculated_region(entity_region_type="WORKLOAD",
                                                                                entity_type="CLIENT",
                                                                                entity_name=self.client_name)
        self.regions_helper.edit_region_of_entity(entity_type="CLIENT",
                                                  entity_name=self.client_name,
                                                  entity_region_type="WORKLOAD",
                                                  region_id=self.calculated_region)
        response = self.regions_helper.get_region_of_entity(entity_type="CLIENT", entity_name=self.client_name,
                                                            entity_region_type="WORKLOAD")
        if response != self.calculated_region:
            raise CVTestStepFailure("validation failed, response returned is %s, expected response is %s", response,
                                    self.calculated_region)

    def reset_backup_destination_region(self):
        """Setting the Backup region for the entity to 0"""
        self.regions_helper.edit_region_of_entity(entity_type="CLIENT", entity_name=self.client_name,
                                                  entity_region_type="BACKUP")
        self.regions_helper.get_region_of_entity(entity_type="CLIENT", entity_name=self.client_name,
                                                 entity_region_type="BACKUP")

    @test_step
    def assign_non_elastic_plan(self, plan_name):
        """Assign a non-elastic plan to the entity"""
        self.reset_backup_destination_region()
        self.plan_helper.entity_to_plan(plan_name=plan_name, client_name=self.client_name,
                                        backup_set="defaultBackupSet")
        response = self.regions_helper.get_region_of_entity(entity_type="CLIENT", entity_name=self.client_name,
                                                            entity_region_type="BACKUP")
        if response != self.calculated_region:
            raise CVTestStepFailure("validation failed, response returned is %s, expected response is None." % response)
        else:
            self.log.info(f"Backup destination updated with Workload region {self.calculated_region}")

    @test_step
    def assign_elastic_plan(self, plan_name):
        """Assign an elastic plan to the entity"""
        self.plan_helper.entity_to_plan(plan_name=plan_name, client_name=self.client_name,
                                        backup_set="defaultBackupSet")
        response2 = self.regions_helper.get_region_of_entity(entity_type="CLIENT", entity_name=self.client_name,
                                                             entity_region_type="BACKUP")
        if not self.regions_helper.validate_backup_destination_region(calculated_region=response2,
                                                                      plan_name=self.elastic_plan,
                                                                      entity_name=self.client_name,
                                                                      entity_type="CLIENT"):
            raise CVTestStepFailure("validation for backup destination region failed")

    def run(self):
        """ run function of this test case """
        try:
            self.reset_workload_region()

            self.calculate_region()

            self.assign_non_elastic_plan(plan_name=self.non_elastic_plan)

            self.assign_elastic_plan(plan_name=self.elastic_plan)

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.plan_helper.dissociate_entity(client_name=self.client_name, backup_set="defaultBackupSet")
        self.plan_helper.cleanup_plans(marker='regions_automation_plan_')
