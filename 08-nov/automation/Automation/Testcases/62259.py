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
    __init__()                                          --  initialize TestCase class

    setup()                                             --  setup function of this test case

    validate_server_group_list()                        --  Method to compare serve group lists from DB and UI

    validate_default_server_group_listing()             --  Case to validate default server group list without adding any new server group

    validate_add_server_group_listing()                 --  Case to validate server group listing after adding a server group as admin

    validate_add_server_group_listing_as_operator()     --  Case to validate server group listing after adding a server group as tenant operator(admin)

    validate_server_group_all_companies()               --  Case to validate server group listing for every company as MSP admin

    run()                                               --  run function of this test case

    tear_down()                                         --  tear down function of this test case

"""
from datetime import datetime
import random

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.server_groups import ServerGroups
from Web.AdminConsole.AdminConsolePages.Companies import Companies
from Server.servergrouphelper import ServerGroupHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.exceptions import CVTestStepFailure
from collections import Counter
from datetime import datetime


class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "[CC Acceptance] server group: CRUD operations on server group page"
        self.navigator = None
        self.config = get_config()
        self.company_name = None
        self.servergroup_name = None
        self.servergroup_name_company = None
        self.tcinputs = {
        }

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.navigator = self.admin_console.navigator
        self._servergroups = ServerGroups(self.admin_console)
        self._servergroupshelper = ServerGroupHelper(self.commcell)
        self.__companies = Companies(self.admin_console)
        self.servergroup_name = "Test Server Group_" + str(datetime.now())[-4:]
        self.servergroup_name_company = "Test Server Group Company_" + str(datetime.now())[-4:]

    def validate_server_group_list(self, company_name_UI=None, company_name_DB=None):
        """Method to compare serve group lists from DB and UI"""
        if company_name_DB:
            DB_list = self._servergroupshelper.get_server_groups_for_company(company_name_DB)
        else:
            DB_list = self._servergroupshelper.get_all_server_groups()

        if company_name_UI:
            UI_list = self._servergroups.get_all_servers_groups(company_name_UI)
        else:
            UI_list = self._servergroups.get_all_servers_groups()

        if Counter(DB_list) != Counter(UI_list):
            raise CVTestStepFailure(
                f"Servergroups from DB {DB_list} does not match the expected servergroups from UI {UI_list}"
            )

    @test_step
    def validate_default_server_group_listing(self):
        """Case to validate default server group list without adding any new server group"""
        self.navigator.navigate_to_server_groups()
        self.validate_server_group_list()

    @test_step
    def validate_add_server_group_listing(self):
        """Case to validate server group listing after adding a server group as admin"""
        self.navigator.navigate_to_server_groups()
        self._servergroups.add_manual_server_group(self.servergroup_name)
        self.navigator.navigate_to_server_groups()
        self.validate_server_group_list()

    @test_step
    def validate_add_server_group_listing_as_operator(self):
        """Case to validate server group listing after adding a server group as tenant operator(admin)"""
        self.navigator.switch_company_as_operator(self.company_name)
        self.navigator.navigate_to_server_groups()
        self._servergroups.add_manual_server_group(self.servergroup_name_company)
        self.navigator.navigate_to_server_groups()
        self.validate_server_group_list(company_name_DB=self.company_name)

    @test_step
    def validate_server_group_all_companies(self):
        """Case to validate server group listing for every company as MSP admin"""

        self.navigator.navigate_to_server_groups()
        for name in self.company_list:
            self.validate_server_group_list(company_name_DB=name, company_name_UI=name)

    def run(self):
        """Run function of this test case"""
        try:
            self.navigator.navigate_to_companies()
            company_list = self.__companies.get_active_companies()
            item = min(5, len(company_list))
            self.company_list = random.sample(company_list, item)

            self.company_name = self.company_list[0]
            if not self.company_name:
                raise CVTestStepFailure("Please create a company to run this test case")

            self.validate_default_server_group_listing()

            self.validate_add_server_group_listing()

            self.validate_add_server_group_listing_as_operator()

            self.navigator.switch_company_as_operator("Reset")

            self.validate_server_group_all_companies()


        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.navigator.navigate_to_server_groups()
        self._servergroups.delete_server_group(self.servergroup_name)
        self._servergroups.delete_server_group(self.servergroup_name_company)
        self.browser.close()
