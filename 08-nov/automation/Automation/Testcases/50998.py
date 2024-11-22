# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from Reports.storeutils import StoreUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure, CVTestStepFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Forms.forms import Forms
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Store: Install, Update and Download Workflows"
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
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.util.get_temp_dir())
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser,
                self.commcell.webconsole_hostname
            )
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.util.delete_workflow(self.input.Workflows.FREE.id)
            self.store = StoreApp(self.webconsole)
            self.webconsole.goto_store()
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def verify_install_status(self):
        """Install status should be seen for workflow when its not installed"""
        pkg_status = self.store.get_package_status(
            self.input.Workflows.FREE.name,
            category="Workflows"
        )
        if pkg_status != "Install":
            raise CVTestStepFailure(
                f"[{self.input.Workflows.FREE.name}] does "
                f"not have [Install] status, found [{pkg_status}]"
            )

    @test_step
    def verify_open_status(self):
        """After installing workflow, status should be Open"""
        self.store.install_workflow(
            self.input.Workflows.FREE.name, refresh=True
        )
        self.util.has_workflow(self.input.Workflows.FREE.id)

    @test_step
    def verify_workflow_opens(self):
        """When clicked on Open, workflow form should open """
        self.store.open_package(
            self.input.Workflows.FREE.name,
            category="Workflows"
        )
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        forms = Forms(self.admin_console)
        if forms.is_form_open(self.input.Workflows.FREE.id) is False:
            raise CVTestStepFailure(
                f"Forms page is not open after clicking Open on "
                f"[{self.input.Workflows.FREE.name}]"
            )
        self.webconsole.goto_applications()
        self.webconsole.goto_store(direct=True)

    @test_step
    def verify_update_status(self):
        """When newer workflow is available, status should be Update"""
        self.util.set_workflow_revision(self.input.Workflows.FREE.id)
        pkg_status = self.store.get_package_status(
            self.input.Workflows.FREE.name,
            category="Workflows",
            refresh=True
        )
        if pkg_status != "Update":
            raise CVTestStepFailure(
                f"[{self.input.Workflows.FREE.name}] does not have Update "
                f"status after updating revision"
            )

    @test_step
    def validate_install(self):
        """When you click Update, latest workflow should be installed"""
        self.store.update_workflow(self.input.Workflows.FREE.name)
        installed_revision = self.util.get_workflow_revision(
            self.input.Workflows.FREE.id
        )
        if installed_revision == "$Revision: 1.5 $":
            raise CVTestStepFailure(
                f"[{self.input.Workflows.FREE.name}] not updated after "
                f"clicking update"
            )

    @test_step
    def verify_download_status(self):
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
            self.input.Workflows.FREE.name,
            category="Workflows"
        )
        if pkg_status != "Download":
            raise CVTestStepFailure(
                f"[{self.input.Workflows.FREE.name}] does not have status "
                f"'Download'"
            )

    @test_step
    def validate_download(self):
        """When clicked on Download, package should download after credentials are supplied"""
        self.util.reset_temp_dir()
        self.store.download_workflow(
            self.input.Workflows.FREE.name,
            validate_cloud_login=True
        )
        self.util.poll_for_tmp_files(ends_with=".xml")
        self.util.validate_tmp_files(
            ends_with=".xml",
            hashes=[self.input.Workflows.FREE.hash]
        )

    def run(self):
        try:
            self.init_tc()
            self.verify_install_status()
            self.verify_open_status()
            self.verify_workflow_opens()
            self.verify_update_status()
            self.validate_install()
            self.verify_download_status()
            self.validate_download()
        except Exception as err:
            self.util.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
