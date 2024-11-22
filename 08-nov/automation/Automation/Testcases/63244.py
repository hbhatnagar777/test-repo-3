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
from Server.organizationhelper import OrganizationHelper
from Server.servergrouphelper import ServerGroupHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper import RegionHelper
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
        self.organization_helper = None
        self.company = None
        self.server_group = None
        self.region = None
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
        self.organization_helper = OrganizationHelper(self.commcell)

        # get a temp region
        self.region = random.choice(list(self.commcell.regions.all_regions.keys()))
        self.log.info(f'using region {self.region} for the testcase')

        # creating temp entities (server group/ company)
        self.server_group = self.commcell.client_groups.add\
            (f'regions_automation_temp_group_{random.randint(0, 10000)}').clientgroup_name
        self.company = self.organization_helper.create(
            name=f'regions_automation_temp_company_{random.randint(0, 10000)}').organization_name
        self.log.info(f'Successfully created temp entities : {self.server_group}, {self.company}')

        # refreshing the page so that the CC is updated with new entities
        self.admin_console.refresh_page()

    def edit_region(self, entity_type, expected_response, entity_name=None, region_name="None"):
        """Method to edit region of the entity"""
        self.region_helper.set_workload_region(entity_type=entity_type,
                                               region=region_name,
                                               entity_name=entity_name)
        response = self.region_helper.get_workload_region(entity_type=entity_type,
                                                          entity_name=entity_name)
        if response == expected_response:
            self.log.info("validation successful")
        else:
            raise CVTestStepFailure("validation failed, response returned is %s, expected response is %s."
                                    % (response, expected_response))

    @test_step
    def validate_for_entities(self, entity_type, entity_name=None):
        """commcell entities workload region association validation"""
        self.edit_region(entity_type=entity_type,
                         entity_name=entity_name,
                         expected_response="Not set")

        self.edit_region(entity_type=entity_type,
                         entity_name=entity_name,
                         expected_response=self.region,
                         region_name=self.region)

    def run(self):
        """ run function of this test case """
        try:
            self.validate_for_entities(entity_type="CLIENTGROUP", entity_name=self.server_group)

            self.validate_for_entities(entity_type="COMPANY", entity_name=self.company)

            self.validate_for_entities(entity_type="COMMCELL")

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
        self.organization_helper.cleanup_orgs(marker='regions_automation_temp_company')
        ServerGroupHelper(self.commcell).cleanup_server_groups(marker='regions_automation_temp_group_')
