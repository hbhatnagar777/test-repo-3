# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup method for test case

    run             --  run function of this test case
"""


from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.FileServerPages.file_servers import FileServers

from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """ Class for executing Basic acceptance Test for client migration """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test for Client Migration in AdminConsole"
        self.utils = TestCaseUtils(self)
        self.file_server_obj = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
            'client_name': None,
            'company_name': None,
            'company_username': None,
            'company_password': None}

    def setup(self):
        """ Method to setup test variables """
        self.log.info("Started executing %s testcase", self.id)
        self.log.info("*" * 10 + " Initialize browser objects " + "*" * 10)
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.file_server_obj = FileServers(self.admin_console)

    @test_step
    def is_client_displayed_in_migrated_company(self):
        """ Test step to check if the client is displayed in migrated company """
        self.admin_console.logout()
        self.admin_console.login(self.tcinputs['company_username'],
                                 self.tcinputs['company_password'])
        self.navigator.navigate_to_file_servers()
        self.file_server_obj.access_server(self.tcinputs['client_name'])

    def run(self):
        """ Main function for test case execution """
        try:

            self.navigator.navigate_to_file_servers()
            self.file_server_obj.migrate_client_to_company(self.tcinputs['client_name'],
                                                           self.tcinputs['company_name'])
            self.is_client_displayed_in_migrated_company()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
