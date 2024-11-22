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

    __init__()                                   --  initialize TestCase class

    init_tc()                                    --  Initial configuration for the testcase

    run()                                        --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.AdminConsolePages.Index_Server import IndexServer
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep


class TestCase(CVTestCase):
    """Class for executing this Testcase"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Check whether Backup Plans dropdown shows only correct plans & not other plans" \
                    " like data classification or exchange plans"
        # Testcase Constants
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.index_servers_obj = None
        self.index_server_name = None

    def init_tc(self):
        """ Initial configuration for the test case """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.index_servers_obj = IndexServer(self.admin_console)
            self.index_server_name = f'{self.id}_IS'

        except Exception:
            raise Exception("Testcase initialization failed")

    def run(self):
        try:
            self.init_tc()
            self.index_servers_obj.validate_backup_plan_dropdown(index_server_name=self.index_server_name,
                                                                 commcell_obj=self.commcell)
            self.log.info('Testcase Passed')

        except Exception as err:
            self.log.info('Testcase Failed')
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
