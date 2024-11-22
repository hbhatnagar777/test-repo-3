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

    setup()                      --  Setup function for this test case

    run()                        --  Main function for test case execution

TestCase Parameters:
    validation_delay    (int)   -   seconds delay between validations per log (default: 10)
    validations         (int)   -   number of times to validate each log (default: 2)
    ClientName          (str)   -   name of client to validate view logs for (default: commserv client)
    log_names           (str)   -   comma separated log names to validate (default: cvd.log)
    lines_lag           (str)   -   max acceptable number of lines UI has not loaded yet (default: 20)
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
        self.name = "Admin console : View Logs Acceptance"
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
            self.logs_helper.validate_logs()
        except Exception as err:
            self._utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
