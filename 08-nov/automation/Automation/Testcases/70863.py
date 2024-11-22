import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVWebAutomationException, CVTestStepFailure
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages import regions
from Web.AdminConsole.Helper import RegionHelper
from Server.regions_helper import RegionsHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Duplicate entity] - CRUD operations for Regions"
        self.browser = None
        self.admin_console = None
        self.region_names = []
        self.navigator = None
        self.region_helper = None
        self.Regions = None
        self.tcinputs = {
            "Company1": None,
            "Company2": None,
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
        self.region_helper = RegionHelper.RegionMain(self.admin_console)
        self.Regions = regions.Regions(self.admin_console)

    def run(self):
        """Run function of this test case"""
        try:

            self.log.info("Step 1: Creating initial region")
            self.create_regions(name=f'Duplicate_Entity - region {str(time.time()).split(".")[0]}')
            self.validate_listing_search(suffix='Commcell', name_index=0)

            # switch to company1 tenant operator
            self.log.info("Step 2: Switching to Company1 and creating a region with swapped case name")
            self.create_regions(name=self.region_names[0].swapcase(), switch_company=True,
                                company=self.tcinputs['Company1'])
            self.validate_listing_search(duplicate=True, suffix=self.tcinputs['Company1'], name_index=1)

            # switch to company2 tenant operator
            self.log.info("Step 3: Switching to Company2 and creating a new region")
            self.create_regions(name=f'Duplicate_Entity - region {str(time.time()).split(".")[0]}', switch_company=True,
                                company=self.tcinputs['Company2'])
            self.validate_listing_search(suffix='Commcell', name_index=2)

            # rename region
            self.log.info("Step 4: Renaming the second region and validating the listing grid")
            self.Regions.edit_region_name(self.region_names[2], self.region_names[1])

            self.validate_listing_search(duplicate=True, suffix=self.tcinputs['Company2'], name_index=1)

            # delete Regions created by tenant operators
            self.log.info("Step 5: Deleting the Regions and validating the final listing grid")
            self.commcell.regions.delete(f'{self.region_names[1]}_({self.tcinputs["Company1"]})')
            self.commcell.regions.delete(f'{self.region_names[1]}_({self.tcinputs["Company2"]})')
            self.navigator.navigate_to_dashboard()

            self.validate_listing_search(suffix='Commcell', name_index=0)

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        RegionsHelper(self.commcell).cleanup("duplicate_entity - region")
        RegionsHelper(self.commcell).cleanup("duplicate_entity - region")
        AdminConsole.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)

    @test_step
    def create_regions(self, name: str, switch_company: bool = False, company: str = None):
        """Create a region and optionally switch company"""
        try:
            if switch_company:
                self.navigator.switch_company_as_operator(company)

            self.region_helper.region_name = name
            self.region_helper.add_new_region()
            self.region_names.append(name)

            if switch_company:
                self.navigator.switch_company_as_operator('Reset')
        except Exception as exp:
            CVTestStepFailure(f'failed to create region : {exp}')

    @test_step
    def validate_listing_search(self, duplicate: bool = False, suffix: str = None, name_index: int = None):
        """Validate region names in listing grid results"""
        try:
            self.navigator.navigate_to_regions()
            list_res = self.Regions.search_for(self.region_names[name_index])
            self.log.info(f'listing page result : {list_res}')
            if not duplicate:
                if f'{self.region_names[name_index]} ({suffix})' in list_res:
                    raise CVWebAutomationException(
                        "Company Name suffix displayed for non duplicate entity in listing grid.")
                self.log.info('Company name suffix not displayed for non duplicate entity in listing grid.')

            else:
                if f'{self.region_names[0]} (Commcell)' not in list_res \
                        and f'{self.region_names[name_index]} ({suffix})' not in list_res:
                    raise CVWebAutomationException(
                        "Company Name suffix not displayed for duplicate entity in listing grid.")
                self.log.info('Company name suffix displayed for duplicate entity in listing grid.')
        except Exception as exp:
            CVTestStepFailure(f'failed to validate : {exp}')
