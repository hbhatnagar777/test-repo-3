""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
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
        self.name = "Workload Region of VM (UI)"
        self.tcinputs = {
            "vm": None,
            "region_1": None
        }
        """
        Note: make sure all the three regions are not same.
        """
    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']["webconsoleHostname"])
        self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                 self.inputJSONnode['commcell']["commcellPassword"])
        self.region_helper = RegionHelper.AssociatedRegion(self.admin_console)

    @test_step
    def edit_region(self, entity_type,region_name, entity_name=None):
        """Method to edit region of the entity"""
        self.region_helper.set_workload_region(entity_type=entity_type,
                                          entity_name=entity_name,
                                          region=region_name)
        response = self.region_helper.get_workload_region(entity_type=entity_type,
                                                    entity_name=entity_name)
        if response == region_name:
            self.log.info("validation successful")
        else:
            raise CVTestStepFailure(
                "validation failed, response returned is %s, expected response is %s." % (response, region_name))

    def run(self):
        """ run function of this test case """
        try:
            # Pick a VM and set the workload region
            self.edit_region(entity_type="VM",
                             entity_name= self.tcinputs["vm"],
                             region_name=self.tcinputs["region_1"])

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)