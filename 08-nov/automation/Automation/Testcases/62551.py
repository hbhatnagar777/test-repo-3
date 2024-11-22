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
        self.name = "Workload region association to commcell entities(API)"
        self.server_group_helper = None
        self.organization_helper = None
        self.company = None
        self.server_group = None
        self.region = None
        self.region_id = None
        self.region_helper = None

    def setup(self):
        """Setup function of this test case"""
        self.region_helper = RegionsHelper(self.commcell)
        self.organization_helper = OrganizationHelper(self.commcell)

        # get a temp region
        self.region = random.choice(list(self.commcell.regions.all_regions.keys()))
        self.region_id = int(self.commcell.regions.get(self.region).region_id)
        self.log.info(f'using region {self.region} for the testcase')

        # creating temp entities (server group/ company)
        self.server_group = self.commcell.client_groups.add\
            (f'regions_automation_temp_group_{random.randint(0, 10000)}').clientgroup_name
        self.company = self.organization_helper.create(
            name=f'regions_automation_temp_company_{random.randint(0, 10000)}').organization_name
        self.log.info(f'Successfully created temp entities : {self.server_group}, {self.company}')

    def edit_region(self, entity_type, entity_name, region_type, region_name=None, response1=None):
        """Method to edit region of the entity"""
        self.region_helper.edit_region_of_entity(entity_type=entity_type,
                                                 entity_name=entity_name,
                                                 entity_region_type=region_type,
                                                 region_name=region_name)
        response = self.region_helper.get_region_of_entity(entity_type=entity_type,
                                                           entity_name=entity_name,
                                                           entity_region_type=region_type)
        if response == response1:
            self.log.info("validation successful")
            return response
        else:
            raise CVTestStepFailure("validation failed, response returned is %s, expected response is %s."
                                    % (response, response1))

    @test_step
    def validate_for_entities(self, entity_type, entity_name):
        """commcell entities workload region association validation"""
        self.edit_region(entity_type=entity_type,
                         entity_name=entity_name,
                         region_type="WORKLOAD")

        self.edit_region(entity_type=entity_type,
                         entity_name=entity_name,
                         region_type="WORKLOAD",
                         region_name=self.region,
                         response1=self.region_id)

    def run(self):
        """ run function of this test case """
        try:
            self.validate_for_entities(entity_type="CLIENT_GROUP", entity_name=self.server_group)

            self.validate_for_entities(entity_type="COMPANY", entity_name=self.company)

            self.validate_for_entities(entity_type="COMMCELL", entity_name=self.commcell.commserv_name)

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.organization_helper.cleanup_orgs(marker='regions_automation_temp_company')
        ServerGroupHelper(self.commcell).cleanup_server_groups(marker='regions_automation_temp_group_')
