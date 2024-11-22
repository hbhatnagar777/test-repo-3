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
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Store: Install, Update and Download Alerts"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.SOFTWARESTORE
        self.feature = self.features_list.WEBCONSOLE
        self.browser: Browser = None
        self.webconsole: WebConsole = None
        self.store: StoreApp = None
        self.util = StoreUtils(self)
        self.input = StoreUtils.get_store_config()

    def init_tc(self):
        try:
            self.util.store_server_api
            self.util.cre_api
            self.util.delete_alert(self.input.Alerts.FREE.name, suppress=True)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.util.get_temp_dir())
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser,
                self.commcell.webconsole_hostname
            )
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.webconsole.goto_store()
            self.store = StoreApp(self.webconsole)
            self.util.reset_temp_dir()
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def start_step1(self):
        """Install status should be seen for alert when its not installed"""
        self.store.install_alert(self.input.Alerts.FREE.name)
        self.util.verify_if_alert_exists(self.input.Alerts.FREE.name)

    @test_step
    def start_step2(self):
        """After installing alert, status should be Up-to-date"""
        pkg_status = self.store.get_package_status(
            self.input.Alerts.FREE.name,
            category="Alerts",
            refresh=True
        )
        self.util.verify_if_alert_exists(self.input.Alerts.FREE.name)
        if pkg_status != "Up-to-date":
            raise CVTestStepFailure(
                f"[{self.input.Alerts.FREE.name}] does "
                f"not have Up-to-date status, found [{pkg_status}]"
            )

    @test_step
    def start_step3(self):
        """When newer alert is available, status should be Update"""
        self.util.set_alert_revision(self.input.Alerts.FREE.name)
        pkg_status = self.store.get_package_status(
            self.input.Alerts.FREE.name,
            category="Alerts",
            refresh=True
        )
        if pkg_status != "Update":
            raise CVTestStepFailure(
                f"[{self.input.Alerts.FREE.name}] does not have Update "
                f"status after updating revision"
            )

    @test_step
    def start_step4(self):
        """When you click Update, latest alert should be installed"""
        self.store.update_alert(self.input.Alerts.FREE.name)
        alert_revision = self.util.get_alert_revision(
            self.input.Alerts.FREE.name
        )
        if alert_revision == "$Revision: 1.4 $":
            raise CVTestStepFailure(
                f"[{self.input.Alerts.FREE.name}] not updated after "
                f"clicking update, expected revision [$Revision: 1.4 $]"
                f"received revision is [{alert_revision}]"
            )

    @test_step
    def start_step5(self):
        """When store is directly accessed, Download status should be seen"""
        self.log.info(
            f"Switching to store server [{self.util.get_store_server()}]'s "
            f"webconsole"
        )
        WebConsole.logout_silently(self.webconsole)
        self.webconsole = WebConsole(
            self.browser, self.util.get_store_server()
        )
        self.store = StoreApp(self.webconsole)
        self.webconsole.goto_store(direct=True)
        pkg_status = self.store.get_package_status(
            self.input.Alerts.FREE.name,
            category="Alerts"
        )
        if pkg_status != "Download":
            raise CVTestStepFailure(
                f"[{self.input.Alerts.FREE.name}] does not have status 'Download'"
            )

    @test_step
    def start_step6(self):
        """When clicked on Download, package should download after credentials are supplied"""
        self.util.reset_temp_dir()
        self.store.download_alert(
            self.input.Alerts.FREE.name,
            validate_cloud_login=True
        )
        self.util.poll_for_tmp_files(ends_with="xml")
        self.util.validate_tmp_files(
            ends_with="xml",
            hashes=[self.input.Alerts.FREE.hash]
        )

    def run(self):
        try:
            self.init_tc()
            self.start_step1()
            self.start_step2()
            self.start_step3()
            self.start_step4()
            self.start_step5()
            self.start_step6()
        except Exception as err:
            self.util.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
