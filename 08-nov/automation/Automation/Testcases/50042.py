# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from Reports.storeutils import StoreUtils
from Web.Common.cvbrowser import (
    Browser,
    BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Store: Min Version in Reports"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.SOFTWARESTORE
        self.feature = self.features_list.WEBCONSOLE
        self.browser: Browser = None
        self.webconsole: WebConsole = None
        self.store: StoreApp = None
        self.inputs = StoreUtils.get_store_config()
        self.utils = StoreUtils(self)

    def init_tc(self):
        try:
            self.utils.store_server_api
            self.utils.validate_if_package_exists(
                self.inputs.Reports.V11SP20
            )
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser, self.commcell.webconsole_hostname
            )
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.store = StoreApp(self.webconsole)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def greater_than_current_sp(self):
        """Report with min-version greater than WC version should not be visible"""
        self.webconsole.goto_reports()
        Navigator(self.webconsole).goto_store()
        packages = self.store.search_packages(self.inputs.Reports.V11SP20)
        if self.inputs.Reports.V11SP20 in packages:
            raise CVTestStepFailure(
                f"Report [{self.inputs.Reports.V11SP20}] should not be visible"
            )

    @test_step
    def lower_than_current_sp(self):
        """Report with min-version less than or equal to current WC should be visible"""
        self.webconsole.goto_store(direct=True)
        packages = list(map(lambda r: r.lower(), self.store.search_packages(
            self.inputs.Reports.FREE.name,
            refresh=True
        )))
        if self.inputs.Reports.FREE.name.lower() not in packages:
            raise CVTestStepFailure(
                "[%s] not visible on current service pack" %
                self.inputs.Reports.FREE.name
            )

    def run(self):
        try:
            self.init_tc()
            self.greater_than_current_sp()
            self.lower_than_current_sp()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
