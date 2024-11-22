# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from Reports.storeutils import StoreUtils
from Web.Common.cvbrowser import Browser
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Store: Quick Access Tool Install"
        self.applicable_os = self.os_list.WINDOWS
        self.browser: Browser = None
        self.webconsole: WebConsole = None
        self.store: StoreApp = None
        self.store_config = StoreUtils.get_store_config()
        self.util = StoreUtils(self)

    def init_tc(self):
        try:
            self.util.delete_tool(
                self.store_config.TOOL.id,
                suppress=True
            )
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser, self.commcell.webconsole_hostname
            )
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.webconsole.goto_store()
            self.store = StoreApp(self.webconsole)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def install_tool(self):
        """Install any Quick Access Tool"""
        self.store.install_quick_access_tool(
            self.store_config.TOOL.name
        )
        self.util.validate_if_tool_exists(
            self.store_config.TOOL.id
        )

    def run(self):
        try:
            self.init_tc()
            self.install_tool()
        except Exception as err:
            self.util.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
