# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

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
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Laptop import Laptops
from Web.AdminConsole.Helper import LaptopHelper, global_search_helper
from Web.Common.page_object import TestStep, CVTestStepFailure, handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

                    Properties to be initialized:

                        name            (str)       --  name of this test case

                """
        super(TestCase, self).__init__()
        self.name = "[Global Search]: Global search listing and action automation for Laptops"
        self.tcinputs = {
            "name": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']["webconsoleHostname"])
        self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"], self.inputJSONnode['commcell']["commcellPassword"])
        self.navigate = self.admin_console.navigator
        self.laptop = Laptops.Laptops(self.admin_console)
        self.laptop_Helper = LaptopHelper.LaptopMain(self.admin_console,self.commcell)
        self.gs_helper = global_search_helper.GlobalSearchHelper(self.admin_console)
        self.laptop_name = self.tcinputs["name"]

    @test_step
    def listing_page_search(self):
        """ function for validating listing page search"""
        self.laptop_Helper.validate_listing_page_search(self.laptop_name)

    @test_step
    def edit_entity(self, new_name=None ):
        """ function used to edit name of the entity"""
        if not new_name:
            new_name = "edited_" + self.laptop_name
        self.laptop_Helper.edit_laptop_name(name=self.laptop_name, new_name=new_name)
        if self.gs_helper.validate_global_entity_search("Laptops", new_name):
            self.laptop_name = "edited_"+self.laptop_name
            self.log.info("Successfully updated entity's name")
        else:
            raise CVTestStepFailure("Edited entity not listed in global search")

    @test_step
    def actions(self):
        """ function to test actions from action menu """

        self.navigate.navigate_to_devices()
        """ view restore jobs"""
        self.laptop.view_restore_jobs(self.laptop_name)
        self.navigate.navigate_to_devices()

        """ check readiness"""
        self.laptop.action_check_readiness(client_name=self.laptop_name)
        self.navigate.navigate_to_devices()

    def run(self):
        """ run function of this test case """
        try:
            self.gs_helper.validate_global_entity_search("Laptops", self.laptop_name)
            self.listing_page_search()
            self.edit_entity()
            self.actions()
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """ Tear down function of this test case """
        try:
            self.edit_entity(new_name=self.tcinputs["name"])
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close()

