# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase
from Reports.storeutils import StoreUtils
from urllib.parse import urlsplit
from Web.Common.cvbrowser import (
    Browser,
    BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Store.storeapp import (
    StoreApp, ReadMe
)
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Store: Packages with multiple version on store"
        self.browser: Browser = None
        self.webconsole: WebConsole = None
        self.store: StoreApp = None
        self.util = StoreUtils(self)
        self.conf = StoreUtils.get_store_config()
        self.tc_config = config.get_config()
        self.readme = None

    def init_tc(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.util.get_temp_dir())
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser, urlsplit(self.tc_config.Store_Server).netloc
            )
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.store = StoreApp(self.webconsole)
            self.webconsole.goto_store()
            self.store = StoreApp(self.webconsole)
            self.store.goto_readme(self.conf.Reports.VERSION.name)
            self.readme = ReadMe(self.webconsole)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def view_all_package_versions(self):
        """All versions of the package should be shown on store server"""
        # rel = self.readme.get_package_info().get("ReleasedIn", "")
        # if rel != "SP13":
        #     raise CVTestStepFailure(
        #         f"Unexpected release [{rel}] on readme page"
        #     )
        releases = self.readme.get_all_release_versions()
        expected = self.conf.Reports.VERSION.releases
        has_releases = all(
            release in set(expected)
            for release in set(releases)
        )
        if has_releases and len(releases) == 2:
            return releases
        raise CVTestStepFailure(
            "Unexpected Released In found on the readme page, "
            f"received [{releases}]"
        )

    @test_step
    def view_details_of_specific_release(self, releases):
        """When we click Details, the report corresponding to the version should be opened"""
        self.readme.goto_release(releases[0])
        # Commenting as Released In info removed in SP23
        # pkg_info = self.readme.get_package_info().get("ReleasedIn", "")
        # if pkg_info != releases[0]:
        #     raise CVTestStepFailure(
        #         "Unable to open other package versions"
        #     )

    @test_step
    def download_package(self):
        """Download package corresponding to non default version"""
        self.util.reset_temp_dir()
        self.readme.download_package()
        self.util.validate_tmp_files(ends_with="xml", count=1)
        rpt_xml = self.util.get_temp_files("xml")[0]
        self.log.info(f"Downloaded file {rpt_xml}")
        with open(rpt_xml) as fp:
            data = fp.read()
            if "<customReportName>Multi Version SP11</customReportName>" not in data:
                raise CVTestStepFailure("Unable to download file")

    def run(self):
        try:
            self.init_tc()
            releases = self.view_all_package_versions()
            self.view_details_of_specific_release(releases)
            self.download_package()
        except Exception as err:
            self.util.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
