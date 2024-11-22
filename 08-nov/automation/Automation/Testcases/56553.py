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
    __init__()                   --  initialize TestCase class

    setup()                      --  Setup function for test case

    run()                        --  Main function for test case execution

TestCase Params:
    ClientName  (str)   -   Name of client to test logs filter for (default: commserv client)
    log_names   (str)   -   Names of logs [comma separated] to test filters for (default: cvd.log)
    validations (int)   -   Number of random filters to validate per log file (default: 2)
    lines_lag   (int)   -   Acceptable number of bad lines (that do not follow filter rule)
"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.logs_helper import LogsHelper
from Web.AdminConsole.adminconsole import AdminConsole


class TestCase(CVTestCase):
    """Test case to verify view log file feature acceptance"""

    def __init__(self):
        """Init method for test case class"""
        super(TestCase, self).__init__()
        self._utils = TestCaseUtils(self)
        self.logs_helper = None
        self.name = "Admin Console : View Logs Filters test case"
        self.browser = None
        self.admin_console = None
        self.tcinputs = {}

    def setup(self):
        """Initialize browser and redirect to page"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            self.inputJSONnode['commcell']['commcellUsername'],
            self.inputJSONnode['commcell']['commcellPassword']
        )
        self.logs_helper = LogsHelper(self.commcell, self.admin_console, **self.tcinputs)

    def run(self):
        """Main function for test case execution"""
        try:
            self.logs_helper.validate_log_filters(pause=self.tcinputs.get('pause', '').lower() != 'false')
        except Exception as err:
            self._utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
