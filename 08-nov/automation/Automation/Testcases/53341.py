# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------

"""

Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.LoginHelper import LoginMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.global_exceptions_helper import GlobalExceptionsMain
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """ basic acceptance test case for global exceptions configuration """
    def __init__(self):
        """Initializing the Test case file """
        super(TestCase, self).__init__()
        self.name = "Admin console - Global exceptions Acceptance"
        self.factory = None
        self.driver = None
        self.login_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.global_filter_obj = None
        self.tcinputs = {
            "global_filter_path": {'windows_global_filter_path', 'unix_global_filter_path'},
            "new_global_filter_path": {'new_windows_global_filter_path', 'new_unix_global_filter_path'}
            }

    def run(self):
        try:
            factory = BrowserFactory()
            browser = factory.create_browser_object()
            browser.open()
            driver = browser.driver

            self.log.info("Creating the login object")
            login_obj = LoginMain(driver, self.csdb)
            login_obj.login(self.inputJSONnode['commcell']['commcellUsername'],
                            self.inputJSONnode['commcell']['commcellPassword'])
            self.log.info("login successful")

            self.admin_console = (AdminConsole(browser, machine=self.inputJSONnode['commcell']['webconsoleHostname'])
                                  .navigator)
            global_filter_obj = GlobalExceptionsMain(self.admin_console)

            global_filter_obj.global_filter_path = self.tcinputs['global_filter_path']

            global_filter_obj.create_global_filter()
            self.log.info("Global filter(s) was created successfully")

            global_filter_obj.validate_global_filter()
            self.log.info("Initial validation for global filter(s) is successfully completed")

            global_filter_obj.global_filter_path = self.tcinputs['new_global_filter_path']

            global_filter_obj.modify_global_filter()
            self.log.info("Global filter(s) was edited successfully")

            global_filter_obj.validate_global_filter()
            self.log.info("Validation for global filter after editing is successfully completed")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        try:
            self.global_filter_obj.del_global_filter()
            self.log.info("Global filter(s) was deleted successfully")
            Browser.close_silently(self.browser)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
