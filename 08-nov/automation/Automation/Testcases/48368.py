# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config

from Reports.storeutils import StoreUtils
from Web.API import (
    customreports as custom_reports_api,
    webconsole as webconsole_api
)
from Web.Common.cvbrowser import (
    Browser,
    BrowserFactory
)
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.Store.storeapp import (StoreApp, ReadMe)
from Web.WebConsole.webconsole import WebConsole

from cvpysdk.commcell import Commcell

_CONFIG = get_config()


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Store: Backward Compatibility"
        self.browser: Browser = None
        self.webconsole: WebConsole = None
        self.store: StoreApp = None
        self.cre_api = None
        self.wc_api = None
        self.tcinputs = {
            "webconsole": None,
            "username": None,
            "password": None
        }
        self.conf = StoreUtils.get_store_config()
        self.util = StoreUtils(self)

    def delete_workflow(self, workflow_name):
        """delete workflow from remote CommCell"""
        commcell2 = Commcell(
            self.tcinputs["webconsole"],
            self.tcinputs["username"],
            self.tcinputs["password"]
        )
        commcell2.workflows.delete_workflow(workflow_name)

    def init_tc(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.util.get_temp_dir())
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser, self.tcinputs["webconsole"]
            )
            self.webconsole.login(self.tcinputs["username"],
                                  self.tcinputs["password"])
            self.store = StoreApp(self.webconsole)
            self.wc_api = webconsole_api.Reports(
                self.tcinputs["webconsole"],
                username=self.tcinputs["username"],
                password=self.tcinputs["password"]
            )
            self.cre_api = custom_reports_api.CustomReportsAPI(
                self.tcinputs["webconsole"],
                username=self.tcinputs["username"],
                password=self.tcinputs["password"]
            )
            self.cre_api.delete_custom_report_by_name(
                self.conf.Reports.FREE.name, suppress=True
            )
            self.delete_workflow(self.conf.Workflows.FREE.id)
            self.webconsole.goto_store()
            self.store = StoreApp(self.webconsole)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def install_report(self):
        """Install report from a WC which is one SP behind the latest"""
        self.store.install_report(self.conf.Reports.FREE.name)

    @test_step
    def install_workflow(self):
        """Install Workflow from a WC which is one SP behind latest"""
        self.store.install_workflow(self.conf.Workflows.FREE.name)

    @test_step
    def open_readme(self):
        """Open readme page from a WC lagging behind by one SP"""
        self.store.goto_readme(
            self.conf.MEDIAKIT.Single.name,
            category="Media Kits"
        )
        readme = ReadMe(self.webconsole)
        desc = readme.get_readme_description()
        readme.goto_store_home()
        return desc

    @test_step
    def download_media_kit(self, descriptions):
        """Download media kit from a WC lagging behind by one SP"""
        self.util.reset_temp_dir()
        self.store.download_package(
            self.conf.MEDIAKIT.Single.name,
            category="Media Kits"
        )
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

    def run(self):
        try:
            self.init_tc()
            self.install_report()
            self.install_workflow()
            desc = self.open_readme()
            # self.download_media_kit(desc)

        except Exception as err:
            self.util.handle_testcase_exception(err)

        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
