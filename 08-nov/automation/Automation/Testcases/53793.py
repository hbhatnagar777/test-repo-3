# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Testcase to access all pages available via navigation menu"""

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.adminconsole import AdminConsole

from Reports.utils import TestCaseUtils

_CONFIG = get_config()


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Admin console page access"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.utils = None

    def init_tc(self):
        try:
            self.utils = TestCaseUtils(self)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode['commcell']["commcellUsername"],
                self.inputJSONnode['commcell']["commcellPassword"],
                stay_logged_in=True
            )
            self.navigator = self.admin_console.navigator
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    def get_all_methods(self):
        """Returns all navigation methods in Adminconsole"""
        return [method_name for method_name in dir(self.navigator)if 'navigate_to_' in method_name]

    @test_step
    def navigate_to_all(self, methods):
        """Navigates to all methods exposed in navigation class"""
        for each_method in methods:
            nav_method = getattr(self.navigator, each_method)
            try:
                nav_method()
                if each_method == 'navigate_to_getting_started':
                    self.browser.driver.back()
            except Exception as excep:
                self.log.error(f"unable to access [{each_method}] with error {excep}")

    def run(self):
        try:
            self.init_tc()
            method_names = self.get_all_methods()
            self.navigate_to_all(method_names)
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
