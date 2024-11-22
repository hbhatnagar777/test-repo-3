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
from Server.Plans import planshelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper import RegionHelper
from Server.regions_helper import RegionsHelper
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
        self.name = "Workload and Backup destination Regions for physical clients(UI)"
        self.plan_helper = None
        self.non_elastic_plan = None
        self.elastic_plan = None
        self.client_name = None
        self.region_helper_api = None
        self.region_helper = None
        self.admin_console = None
        self.browser = None

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']["webconsoleHostname"])
        self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                 self.inputJSONnode['commcell']["commcellPassword"])
        self.region_helper = RegionHelper.AssociatedRegion(self.admin_console)
        self.region_helper_api = RegionsHelper(self.commcell)
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
    def reset_region(self):
        """Pick a physical client and set the workload region to None"""
        self.region_helper.set_workload_region(entity_type="CLIENT",
                                               region="None",
                                               entity_name=self.client_name)
        if 'Not set' not in self.region_helper.get_workload_region(entity_type="CLIENT",
                                                                   entity_name=self.client_name):
            raise CVTestStepFailure("validation failed, Not set expected in response.")

    @test_step
    def calculate_region(self):
        """Call GET API with calculate=True for the physical client"""
        region = self.region_helper_api.validate_calculated_region(entity_region_type="WORKLOAD",
                                                                   entity_type="CLIENT",
                                                                   entity_name=self.client_name)
        region_name = self.region_helper_api.get_region_name(region_id=region)[0]
        self.region_helper_api.edit_region_of_entity(entity_type="CLIENT",
                                                     entity_name=self.client_name,
                                                     entity_region_type="WORKLOAD",
                                                     region_id=region)
        if region_name != self.region_helper.get_workload_region(entity_type="CLIENT",
                                                                 entity_name=self.client_name):
            raise CVTestStepFailure("validation failed, expected region is %s" % region_name)

    @test_step
    def assign_nonelastic_plan(self, plan_name):
        """associate a non_elastic plan"""
        self.region_helper.set_backup_region(entity_type="CLIENT",
                                             entity_name=self.client_name,
                                             plan=plan_name)
        if 'No region' not in self.region_helper.get_backup_region(entity_type="CLIENT",
                                                                   entity_name=self.client_name):
            raise CVTestStepFailure("validation failed, Not set expected in response")

    @test_step
    def assign_elastic_plan(self, plan_name):
        """associate an elastic plan"""
        self.region_helper.set_backup_region(entity_type="CLIENT", entity_name=self.client_name,
                                             plan=plan_name)
        self.region_helper.validate_backup_region(entity_type="CLIENT", entity_name=self.client_name,
                                                  plan=plan_name)

    def run(self):
        """ run function of this test case """
        try:
            self.reset_region()

            self.calculate_region()

            self.assign_nonelastic_plan(plan_name=self.non_elastic_plan)

            self.assign_elastic_plan(plan_name=self.elastic_plan)

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        self.plan_helper.dissociate_entity(client_name=self.client_name, backup_set="defaultBackupSet")
        self.plan_helper.cleanup_plans(marker='regions_automation_plan_')
