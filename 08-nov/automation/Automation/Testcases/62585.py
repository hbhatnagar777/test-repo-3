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
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages import Plans
from Web.AdminConsole.Helper import PlanHelper, global_search_helper
from Web.Common.page_object import TestStep, CVTestStepFailure, handle_testcase_exception
from Server.Plans import planshelper
from Server.organizationhelper import OrganizationHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

                    Properties to be initialized:

                        name            (str)       --  name of this test case

                """
        super(TestCase, self).__init__()
        self.name = "[Global Search]: Global search listing and action automation for Plans"
        self.entity_list = []
        self.browser = None
        self.admin_console = None
        self.navigate = None
        self.Plan = None
        self.planHelper = None
        self.gs_helper = None
        self.company_helper = None
        self.planHelper_api = None

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']["webconsoleHostname"])
        self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                 self.inputJSONnode['commcell']["commcellPassword"])
        self.navigate = self.admin_console.navigator
        self.planHelper = PlanHelper.PlanMain(self.admin_console, self.commcell)
        self.Plan = Plans.Plans(self.admin_console)
        self.gs_helper = global_search_helper.GlobalSearchHelper(self.admin_console)
        self.planHelper_api = planshelper.PlansHelper(commcell_obj=self.commcell)
        self.company_helper = OrganizationHelper(self.commcell)

    @test_step
    def create_and_search(self):
        """Method to create entities from /ADD and then search them from global search"""
        storage = self.planHelper_api.get_storage_pool()
        for _ in range(5):
            entity = self.gs_helper.validate_add_entities("Server back up plan", storage=storage)
            if self.gs_helper.validate_global_entity_search("Plans", entity):
                self.entity_list.append(entity)
            else:
                raise CVTestStepFailure("Failed to create/search entity from global search")

    @test_step
    def listing_page_search(self, entity_list):
        """ function for validating listing page search"""
        for entity in entity_list:
            self.planHelper.listing_page_search(entity)

    @test_step
    def edit_entity(self, entity_list):
        """ function to edit the test entity """
        edited_entities = []
        for entity in entity_list:
            self.planHelper.validate_listing_edit_plan_name(old_name=entity, new_name="edited_"+entity,
                                                            Delete_flag=False)
            if self.gs_helper.validate_global_entity_search("Plans", "edited_"+entity):
                edited_entities.append("edited_" + entity)
                self.log.info("Successfully updated entity's name")
            else:
                raise CVTestStepFailure("Failed updating entity's name")
        return edited_entities

    @test_step
    def actions(self, entity_list):
        """ function to test actions from action menu """
        # create a test company
        company = \
            self.company_helper.create(name=f"global_search_temp_company_{random.randint(0, 10000)}").organization_name
        for entity in entity_list:
            # validate associate to company action
            self.planHelper.validate_action_associate_to_company(plan=entity, company=[company])

            # disassociate plan from company
            self.planHelper.validate_plan_disassociation_from_company(plan_name=entity,
                                                                      company_name=company)

            # validate delete action
            self.navigate.navigate_from_global_search("Plans", "CLICK")
            self.Plan.delete_plan(plan_name=entity)

    def run(self):
        """Run function of this test case"""
        try:
            self.create_and_search()
            self.listing_page_search(self.entity_list)
            edited_entities = self.edit_entity(self.entity_list)
            if len(self.entity_list) == len(edited_entities):
                self.actions(edited_entities)
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """tear down function for the test case"""
        self.admin_console.logout_silently(self.admin_console)
        self.browser.close()
        self.company_helper.cleanup_orgs(marker='global_search_temp_company_')
        self.planHelper_api.cleanup_plans("GS_test_plan")
