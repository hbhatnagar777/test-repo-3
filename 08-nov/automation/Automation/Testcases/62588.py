# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

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
from Web.AdminConsole.FileServerPages import file_servers
from Web.AdminConsole.Helper import file_servers_helper, global_search_helper
from Web.Common.page_object import TestStep, CVTestStepFailure, handle_testcase_exception
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
        self.name = "[Global Search]: Global search listing and action automation for File servers"
        self.browser = None
        self.admin_console = None
        self.navigate = None
        self.fs = None
        self.fileServerHelper = None
        self.gs_helper = None
        self.client_name = None
        self.plan = None
        self.plan_helper = None

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']["webconsoleHostname"])
        self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                 self.inputJSONnode['commcell']["commcellPassword"])
        self.navigate = self.admin_console.navigator
        self.fs = file_servers.FileServers(self.admin_console)
        self.fileServerHelper = file_servers_helper.FileServersMain(self.admin_console, self.commcell)
        self.gs_helper = global_search_helper.GlobalSearchHelper(self.admin_console)
        self.plan_helper = planshelper.PlansHelper(commcell_obj=self.commcell)

        # choose a random client
        self.commcell.clients.refresh()
        self.client_name = random.choice(list(self.commcell.clients.file_server_clients.keys()))
        self.log.info(f"client to be used for the testcase: {self.client_name}")

        # create a temp plan
        plan_name = f'global_search_temp_plan_{random.randint(0, 10000)}'
        storage = self.plan_helper.get_storage_pool()
        self.plan = self.plan_helper.create_base_plan(plan_name=plan_name,
                                                      subtype='Server',
                                                      storage_pool=storage).plan_name
        self.log.info(f'Successfully created temp plan : {self.plan}')

    def listing_page_search(self):
        """ function for validating listing page search"""
        self.fileServerHelper.listing_page_search(self.client_name)

    @test_step
    def edit_entity(self, new_name=None):
        """ function used to edit name of the entity"""
        if not new_name:
            new_name = "edited_" + self.client_name
        self.fileServerHelper.edit_Client_name(old_name=self.client_name, new_name=new_name)
        if self.gs_helper.validate_global_entity_search("File servers", new_name):
            self.client_name = "edited_"+self.client_name
            self.log.info("Successfully updated entity's name")
        else:
            raise CVTestStepFailure("Edited entity not listed in global search")

    def actions(self):
        """ function to test actions from action menu """
        self.navigate.navigate_to_file_servers()

        """ view jobs"""
        self.fs.view_jobs(self.client_name)
        self.navigate.navigate_to_file_servers()

        """ check readiness"""
        self.fs.run_check_readiness(client_name=self.client_name)
        self.navigate.navigate_to_file_servers()

        """ Manage plan"""
        self.fs.manage_plan(self.client_name, self.plan)

    def run(self):
        """ run function of this test case """
        try:
            self.gs_helper.validate_global_entity_search("File servers", self.client_name)
            self.listing_page_search()
            self.edit_entity()
            self.actions()
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """ Tear down function of this test case """
        try:
            self.edit_entity(new_name=self.client_name)
            self.plan_helper.dissociate_entity(client_name=self.client_name, backup_set="defaultBackupSet")
            self.plan_helper.cleanup_plans(marker='global_search_temp_plan_')
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close()
