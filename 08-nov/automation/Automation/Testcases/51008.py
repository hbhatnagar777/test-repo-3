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
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Store: Workflow Search"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.SOFTWARESTORE
        self.feature = self.features_list.WEBCONSOLE
        self.browser = None
        self.webconsole = None
        self.reports = None
        self.store = None
        self.inputs = StoreUtils.get_store_config()

    def init_tc(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.webconsole.goto_store()
            self.store = StoreApp(self.webconsole)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def start_step1(self):
        """Search with workflow name"""
        pkg = self.inputs.Workflows.FREE.name
        if self.store.search_package_by_name(pkg, category="Workflows") is not True:
            raise CVTestStepFailure("Workflow [%s] not found" % pkg)

    @test_step
    def start_step2(self):
        """Search with workflow description"""
        pkg_list = self.store.search_packages(
            self.inputs.Workflows.FREE.desc, category="Workflows"
        )
        pkg_name = self.inputs.Workflows.FREE.name
        if pkg_name not in pkg_list:
            raise CVTestStepFailure("Workflow [%s] not found" % str(pkg_name))

    def run(self):
        try:
            self.init_tc()
            self.start_step1()
            self.start_step2()
        except Exception as err:
            StoreUtils(self).handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
