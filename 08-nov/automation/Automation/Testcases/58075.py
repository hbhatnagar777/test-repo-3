# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from AutomationUtils import logger

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Commcell import Commcell


class TestCase(CVTestCase):
    """TestCase class used to execute the test case from here."""
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Negative Test case for CS email settings with invalid SMTP server name"
        self.browser = None
        self.utils = None
        self.log = logger.get_log()
        self.navigator_obj = None
        self.commcell_page = None
        self.admin_console = None

    def init_tc(self):
        """Initial configuration for the test case."""
        try:
            self.utils = TestCaseUtils(self)
            self.log.info(""" Initialize browser objects """)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)

            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.navigator_obj = self.admin_console.navigator
            self.navigator_obj.navigate_to_commcell()

            self.commcell_page = Commcell(self.admin_console)

            self.log.info("running negative scenario 1 for SMTP port")
            self.commcell_page.edit_email_settings({'SMTP port': '21'},
                                                   test_scenario="negative")

            self.log.info("running negative scenario 2 for Encryption algorithm")
            self.commcell_page.edit_email_settings({'SMTP port': '21',
                                                    'Encryption algorithm': 'TLS'},
                                                   test_scenario="negative")

            self.log.info("running negative scenario 3 for user authentication")
            self.commcell_page.edit_email_settings({'SMTP server': '172.16.154.12',
                                                    'Use authentication': True,
                                                    'User name': 'invalid_username',
                                                    'Password': 'invalid_password'},
                                                   test_scenario="negative")
        except Exception as err:
            self.utils.handle_testcase_exception(err)

    def tear_down(self):
        """Tear down function"""
        try:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
        except Exception as err:
            self.utils.handle_testcase_exception(err)