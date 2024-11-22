# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""
Command Center : Global Search for Report

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import Browser
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestStepFailure
from selenium.common.exceptions import TimeoutException


class TestCase(CVTestCase):
    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Command Center Global Search for Report"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.commcell_password = None
        self.admin_console = None
        self.navigator = None

    def setup(self):
        """Setup function of this test case"""
        self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                          username=self.commcell.commcell_username,
                                          password=self.commcell_password)
        self.admin_console.login(username=self.commcell.commcell_username,
                                 password=self.commcell_password)
        self.navigator = self.admin_console.navigator

    def validate_visible_report(self):
        """Search report visible to user"""
        report_name = self.tcinputs['visible_report']
        category = self.navigator.get_category_global_search(report_name)
        if 'REPORTS' in category:
            self.log.info("Visible under 'REPORTS' category")
        else:
            raise CVTestStepFailure("Report not visible under 'REPORTS' category")

    def validate_hidden_report(self):
        """Search report which is not visible for the user"""
        report_name = self.tcinputs['hidden_report']
        try:
            category = self.navigator.get_category_global_search(report_name)
            if 'REPORTS' in category:
                raise CVTestStepFailure("Report should not be visible in global search")
        except TimeoutException:
            self.log.info("Timeout occurred as no matching search result")

    def run(self):
        """Main function for test case execution"""

        try:
            self.validate_visible_report()
            self.validate_hidden_report()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:

            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
