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
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.Store.storeapp import ReadMe
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Store: Media Kit downloads"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.SOFTWARESTORE
        self.feature = self.features_list.WEBCONSOLE
        self.browser = None
        self.webconsole = None
        self.reports = None
        self.store: StoreApp = None
        self.util = StoreUtils(self)
        self.inputs = StoreUtils.get_store_config()
        self.readme: ReadMe = None

    def init_tc(self):
        try:
            self.browser = BrowserFactory().create_browser_object(Browser.Types.FIREFOX)
            self.browser.set_downloads_dir(self.util.get_temp_dir())
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser, self.commcell.webconsole_hostname
            )
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.webconsole.goto_store()
            self.store = StoreApp(self.webconsole)
            self.readme = ReadMe(self.webconsole)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def download_single_media(self):
        """Download media kit package which has only one platform type"""
        self.util.reset_temp_dir()
        self.store.download_package(
            self.inputs.MEDIAKIT.Single.name,
            category="Media Kits"
        )
        self.store.goto_readme(
            self.inputs.MEDIAKIT.Single.name,
            category="Media Kits"
        )
        descriptions = self.readme.get_readme_description()
        self.util.poll_for_tmp_files(ends_with="exe", count=1)
        self.util.validate_tmp_files(
            ends_with="exe",
            count=1,
            hashes=[
                description[:32].lower()
                for description in descriptions.split(" ")
                if len(description.strip()) >= 32
            ]
        )

    @test_step
    def download_multi_media(self):
        """Download media kit from package which has multiple platform types"""
        self.util.reset_temp_dir()
        self.store.goto_store_home()
        self.store.download_packages_with_multiple_platforms(
            self.inputs.MEDIAKIT.Multi.name,
            category="Media Kits",
            platforms=[
                self.inputs.MEDIAKIT.Multi.platforms[0].type
            ]
        )
        self.util.poll_for_tmp_files(
            ends_with="exe",
            count=1
        )
        f_name = self.inputs.MEDIAKIT.Multi.platforms[0].file_name
        self.util.validate_tmp_files(
            ends_with=f_name,
            count=1,
            min_size=1
        )

    @test_step
    def download_all_media(self):
        """Click Download All button on media kit download window"""
        # TODO: Hardcode hashes
        self.util.reset_temp_dir()
        self.store.goto_store_home()
        self.store.download_packages_with_multiple_platforms(
            self.inputs.MEDIAKIT.Multi.name,
            category="Media Kits"
        )
        self.store.goto_readme(
            self.inputs.MEDIAKIT.Multi.name,
            category="Media Kits"
        )
        descriptions = self.readme.get_readme_description()
        self.util.poll_for_tmp_files(
            ends_with="exe",
            count=len(self.inputs.MEDIAKIT.Multi.platforms)
        )
        self.util.validate_tmp_files(
            ends_with="exe",
            count=len(self.inputs.MEDIAKIT.Multi.platforms),
            min_size=1,
            hashes=[
                description[:32].lower()
                for description in descriptions.split(" ")
                if len(description.strip()) >= 32
            ]  # Md5 hashes are 32 chars wide
        )

    @test_step
    def download_status(self):
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
            self.inputs.MEDIAKIT.Single.name,
            category="Media Kits"
        )
        if pkg_status != "Download":
            raise CVTestStepFailure(
                f"[{self.input.Workflows.FREE.name}] does not have status "
                f"'Download'"
            )

    @test_step
    def download_directly(self):
        """When clicked on Download, package should download after credentials are supplied"""
        self.util.reset_temp_dir()
        self.store.download_package(
            self.inputs.MEDIAKIT.Single.name,
            category="Media Kits"
        )
        self.util.poll_for_tmp_files(ends_with="exe", count=1)
        self.util.validate_tmp_files(
            ends_with="exe",
            count=1,
            min_size=1
        )

    def run(self):
        try:
            self.init_tc()
            self.download_single_media()
            self.download_multi_media()
            self.download_all_media()
            self.download_status()
            self.download_directly()
        except Exception as err:
            self.util.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
