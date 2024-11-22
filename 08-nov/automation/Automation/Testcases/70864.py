import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages import regions
from Web.AdminConsole.Helper import RegionHelper
from Server import organizationhelper, regions_helper, servergrouphelper
from Server.Plans import planshelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "[Duplicate entity] - Lookup validation for regions"
        self.browser = None
        self.admin_console = None
        self.region_name = f'Duplicate_Entity - region {str(time.time()).split(".")[0]}'
        self.navigator = None
        self.region_helper = None
        self.Regions = None
        self.plans_helper = None
        self.organization_helper = None
        self.company = None
        self.plan = None
        self.client_group = None
        self.region_main_helper = None
        self.tcinputs = {
            "Company": None
        }

    def setup(self):
        """Setup function of this test case"""
        # open browser and login to CC
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.region_helper = RegionHelper.AssociatedRegion(self.admin_console)
        self.region_main_helper = RegionHelper.RegionMain(self.admin_console)
        self.Regions = regions.Regions(self.admin_console)
        self.plans_helper = planshelper.PlansHelper(commcell_obj=self.commcell)
        self.organization_helper = organizationhelper.OrganizationHelper(self.commcell)

        # creating dummy entities
        self.company = self.organization_helper.create(
            name=f'duplicate entity - company {str(time.time()).split(".")[0]}').organization_name
        self.client_group = self.commcell.client_groups.add(
            clientgroup_name=f'duplicate entity - clientgroup {str(time.time()).split(".")[0]}').name
        plan_name = f'duplicate entity - plan{str(time.time()).split(".")[0]}'
        storage = self.plans_helper.get_storage_pool()
        self.plan = self.plans_helper.create_base_plan(plan_name, 'Server', storage).plan_name
        self.log.info(f'successfully created dummy entities : {self.company}, {self.client_group}, {self.plan}')

    def run(self):
        """Run function of this test case"""
        try:
            # create a region as MSP and a duplicate region as Tenant
            self.log.info("Step 1: Creating a region as MSP and a duplicate region as Tenant")
            self.create_regions(name=self.region_name)
            self.create_regions(name=self.region_name, switch_company=True, company=self.tcinputs['Company'])

            # validating duplicate region lookup in various places
            self.log.info("Step 2: validating duplicate region lookup in various places")
            validation_data = [
                ('COMPANY', self.company),
                ('SERVER', None),
                ('CLIENTGROUP', self.client_group),
                ('FILESERVER', None),
                ('PLAN', self.plan)
            ]

            for entity_type, entity_name in validation_data:
                self.validate_regions(entity_type, self.region_name, entity_name)

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.cleanup()
        AdminConsole.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)

    @test_step
    def create_regions(self, name: str, switch_company: bool = False, company: str = None):
        """Create a region and optionally switch company"""
        try:
            if switch_company:
                self.navigator.switch_company_as_operator(company)

            self.region_main_helper.region_name = name
            self.region_main_helper.add_new_region()
            self.navigator.navigate_to_regions()

            if switch_company:
                self.navigator.switch_company_as_operator('Reset')
            self.log.info(f'successfully created region {name}')
        except Exception as exp:
            CVTestStepFailure(f'failed to create region : {exp}')

    @test_step
    def validate_regions(self, entity_type: str, region_name: str, entity_name=None):
        """Helper function to validate regions from dropdowns."""
        regions_list = self.region_helper.regions_lookup(entity_type, region_name, entity_name)
        self.log.info(f"regions lookup for {entity_type}: {regions_list}")

        regions_with_suffix = [f'{self.region_name} (Commcell)', f'{self.region_name} ({self.tcinputs["Company"]})']

        if not all(item in regions_list for item in regions_with_suffix):
            raise CVTestStepFailure(f'Validation failed for {entity_type}')
        self.log.info(f"Validation successful for entity type : {entity_type}")

    @test_step
    def cleanup(self):
        """Cleanup function for dummy entities"""
        try:
            self.log.info('Starting cleanup process...')
            self.organization_helper.cleanup_orgs('duplicate entity - company')
            self.plans_helper.cleanup_plans('duplicate entity - plan')
            servergrouphelper.ServerGroupHelper(self.commcell).cleanup_server_groups("duplicate entity - clientgroup")
            regions_helper.RegionsHelper(self.commcell).cleanup('Duplicate_Entity - region')
            regions_helper.RegionsHelper(self.commcell).cleanup('Duplicate_Entity - region')
            self.log.info("Cleanup process completed successfully.")
        except Exception as exp:
            self.log.error(f"Cleanup process failed: {exp}")
            raise


