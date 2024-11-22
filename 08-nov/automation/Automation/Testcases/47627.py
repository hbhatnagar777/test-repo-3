# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from Reports.storeutils import StoreUtils
from Web.API import (
    customreports as custom_reports_api,
    webconsole as webconsole_api
)
from Web.Common.cvbrowser import (
    Browser,
    BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure,
    CVWebAPIException
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom.viewer import CustomReportViewer
from Web.WebConsole.Reports.home import ReportsHomePage
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Store: Install, Update and Download Report"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.SOFTWARESTORE
        self.feature = self.features_list.WEBCONSOLE
        self.browser: Browser = None
        self.webconsole: WebConsole = None
        self.store: StoreApp = None
        self.cre_api = None
        self.wc_api = None
        self.inputs = StoreUtils.get_store_config()
        self.util = StoreUtils(self)

    def init_tc(self, browser_type):
        try:
            self.browser = BrowserFactory().create_browser_object(browser_type)
            self.browser.set_downloads_dir(self.util.get_temp_dir())
            self.browser.open()
            if browser_type.value == '_IEBrowser':
                self.browser.set_implicit_wait_time(10)
            self.webconsole = WebConsole(
                self.browser, self.commcell.webconsole_hostname
            )
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.store = StoreApp(self.webconsole)
            self.wc_api = webconsole_api.Reports(
                self.commcell.webconsole_hostname
            )
            self.cre_api = custom_reports_api.CustomReportsAPI(
                self.commcell.webconsole_hostname
            )
            self.cre_api.delete_custom_report_by_name(
                self.inputs.Reports.FREE.name, suppress=True
            )
            self.webconsole.goto_store()
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def validate_install_status(self):
        """Install status should be seen for report when its not installed"""
        try:
            self.store.install_report(
                self.inputs.Reports.FREE.name
            )
            self.cre_api.get_report_definition_by_name(
                self.inputs.Reports.FREE.name
            )
        except CVWebAPIException as e:
            raise CVTestStepFailure(
                f"[{self.inputs.Reports.FREE.name}] not found after install"
            ) from e

    @test_step
    def install_report(self):
        """After installing report, status should be Open"""
        pkg_status = self.store.get_package_status(
            self.inputs.Reports.FREE.name,
            category="Reports",
            refresh=True
        )
        if pkg_status != "Open":
            raise CVTestStepFailure(
                f"[{self.inputs.Reports.FREE.name}] does not have "
                f"Up-to-date status"
            )

    @test_step
    def open_report(self):
        """When clicked on Open, report should open"""
        self.store.open_package(self.inputs.Reports.FREE.name)
        report_viewer = CustomReportViewer(self.webconsole)
        if report_viewer.get_report_name() != self.inputs.Reports.FREE.name:
            raise CVTestStepFailure(
                f"Unable to open [{self.inputs.Reports.FREE.name}]"
            )
        Navigator(self.webconsole).goto_store()

    @test_step
    def validate_update_status(self):
        """When newer report is available, status should be Update"""
        self.log.info(
            f"Changing the installed report "
            f"[{self.inputs.Reports.FREE.name}]'s revision"
        )
        self.util.set_report_revision(
            self.inputs.Reports.FREE.name,
        )
        pkg_status = self.store.get_package_status(
            self.inputs.Reports.FREE.name,
            category="Reports",
            refresh=True
        )
        if pkg_status != "Update":
            raise CVTestStepFailure(
                f"[{self.inputs.Reports.FREE.name}] does not have "
                f"Update status after updating revision"
            )

    @test_step
    def update_available_icon(self):
        """On WW reports page, reports which need update should have a red icon on them"""
        self.webconsole.goto_applications()
        self.webconsole.goto_reports()
        home = ReportsHomePage(self.webconsole)
        home.search_report(self.inputs.Reports.FREE.name)
        reports = home.get_reports_having_update()
        if self.inputs.Reports.FREE.name not in reports:
            raise CVTestStepFailure(
                f"[{self.inputs.Reports.FREE.name}] "
                f"does not have update icon"
            )
        Navigator(self.webconsole).goto_store()

    @test_step
    def update_report(self):
        """When you click Update, latest report should be installed"""
        self.store.update_report(self.inputs.Reports.FREE.name)
        rpt_defi = self.cre_api.get_report_definition_by_name(
            self.inputs.Reports.FREE.name
        )
        if rpt_defi["revision"] == "$Revision: 1.12 $":
            raise CVTestStepFailure(
                f"[{self.inputs.Reports.FREE.name}] not updated "
                f"after clicking update"
            )

    @test_step
    def validate_download_status(self):
        """When store is directly accessed, Download status should be seen"""
        self.log.info(
            f"Switching to store server "
            f"[{self.util.get_store_server()}]'s webconsole"
        )
        WebConsole.logout_silently(self.webconsole)
        self.webconsole = WebConsole(
            self.browser, self.util.get_store_server()
        )
        self.store = StoreApp(self.webconsole)
        self.webconsole.goto_store(direct=True)
        pkg_status = self.store.get_package_status(
            self.inputs.Reports.FREE.name,
            category="Reports"
        )
        if pkg_status != "Download":
            raise CVTestStepFailure(
                f"[{self.inputs.Reports.FREE.name}] does not have "
                f"status 'Download'"
            )

    @test_step
    def download_report(self):
        """When clicked on Download, package should download after login"""
        try:
            self.util.reset_temp_dir()
            self.store.download_report(
                self.inputs.Reports.FREE.name,
                validate_cloud_login=True
            )
            self.util.poll_for_tmp_files(ends_with=".xml")
            self.util.validate_tmp_files(
                ends_with=".xml",
                hashes=[self.inputs.Reports.FREE.hash]
            )
        except CVTestStepFailure as e:
            raise CVTestStepFailure(
                "Download failed or downloaded file is corrupted: " + str(e.args)
            ) from e

    def run(self):
        try:
            browsers = (
                Browser.Types.FIREFOX,
                Browser.Types.CHROME
                # Browser.Types.IE # Commenting due to Loading issue in IE
            )
            for browser in browsers:
                self.log.info(f"Validation with browser {browser.value}")
                self.init_tc(browser)
                self.validate_install_status()
                self.install_report()
                self.open_report()
                self.validate_update_status()
                # self.update_available_icon()
                self.update_report()
                self.validate_download_status()
                if browser.value != '_IEBrowser':  #download popup isnt handled yet in IE
                    self.download_report()
                Browser.close_silently(self.browser)
        except Exception as err:
            self.util.handle_testcase_exception(err)
        finally:
            custom_reports_api.logout_silently(self.cre_api)
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
