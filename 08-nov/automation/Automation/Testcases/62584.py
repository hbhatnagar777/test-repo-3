
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
from Web.AdminConsole.AdminConsolePages.Roles import Roles
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper import roles_helper,global_search_helper
from Web.Common.page_object import TestStep, CVTestStepFailure, handle_testcase_exception
from Server.Security import securityhelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

                    Properties to be initialized:

                        name            (str)       --  name of this test case

                """
        super(TestCase, self).__init__()
        self.name = "[Global Search]: Global search listing and action automation for Roles"
        self.entity_list = []

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']["webconsoleHostname"])
        self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"], self.inputJSONnode['commcell']["commcellPassword"])
        self.navigate=self.admin_console.navigator
        self.rolesHelper = roles_helper.RolesMain(self.admin_console, self.commcell)
        self.gs_helper = global_search_helper.GlobalSearchHelper(self.admin_console)

    @test_step
    def create_and_search(self):
        """Method to create entities from /ADD and then search them from global search"""
        for _ in range(5):
            entity = self.gs_helper.validate_add_entities("Roles")
            if self.gs_helper.validate_global_entity_search("Roles", entity):
                self.entity_list.append(entity)
            else:
                raise CVTestStepFailure("Failed to create/search entity from global search")

    @test_step
    def listing_page_search(self, entity_list):
        """ function for validating listing page search"""
        for entity in entity_list:
            self.rolesHelper.listing_page_search(role_name=entity)

    @test_step
    def edit_entity(self, entity_list):
        """ function to edit the test entity """
        edited_entities = []
        for entity in entity_list:
            self.rolesHelper.validate_listing_edit_role_name(old_name= entity,new_name = "edited_"+entity)
            if self.gs_helper.validate_global_entity_search("Roles", "edited_" + entity):
                edited_entities.append("edited_" + entity)
                self.log.info("Successfully updated entity's name")
            else:
                raise CVTestStepFailure("Failed updating entity's name")
        return edited_entities

    @test_step
    def actions(self, entity_list):
        """ function to test actions from action menu """
        for entity in entity_list:
            Roles(self.admin_console).action_delete_role(role_name=entity)

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
        """ Tear down function of this test case """
        self.admin_console.logout_silently(self.admin_console)
        self.browser.close()
        securityhelper.RoleHelper(self.commcell).cleanup_roles("GS_test_role")
