# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from Reports.storeutils import StoreUtils
from Web.API.customreports import (
    CustomReportsAPI,
    logout_silently
)
from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import (
    CVTestStepFailure,
    CVTestCaseInitFailure,
    CVWebAPIException
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Store import storeapp
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Store: Auto Update packages"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.SOFTWARESTORE
        self.feature = self.features_list.WEBCONSOLE
        self.browser = None
        self.webconsole = None
        self.store: storeapp.StoreApp = None
        self.store_config = None
        self.wf_api = None
        self.cre_api = None
        self.utils = StoreUtils(self)

    def __initialize_basic_objects(self):
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.webconsole = WebConsole(
            self.browser,
            self.commcell.webconsole_hostname
        )
        self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                              self.inputJSONnode['commcell']["commcellPassword"])
        self.cre_api = CustomReportsAPI(self.commcell.webconsole_hostname)
        self.webconsole.goto_store()
        self.store = storeapp.StoreApp(self.webconsole)
        self.store.goto_store_home()
        self.store_config = StoreUtils.get_store_config()

    def __configure_package_revisions(self):
        try:
            self.cre_api.get_report_definition_by_name(
                self.store_config.Reports.FREE.name
            )
        except CVWebAPIException:
            self.store.install_report(
                self.store_config.Reports.FREE.name
            )
        self.utils.set_report_revision(
            self.store_config.Reports.FREE.name
        )

        try:
            self.utils.has_workflow(
                self.store_config.Workflows.FREE.id
            )
        except CVTestStepFailure:
            self.store.install_workflow(
                self.store_config.Workflows.FREE.name
            )
        self.utils.set_workflow_revision(
            self.store_config.Workflows.FREE.id
        )

    def init_tc(self):
        try:
            self.__initialize_basic_objects()
            self.__configure_package_revisions()
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def step1(self):
        """When auto-update is enabled, packages with Update status should be updated"""
        self.store.goto_store_home()
        self.store.enable_auto_update()
        self.utils.poll_till_auto_update()
        rpt_status = self.store.get_package_status(
            self.store_config.Reports.FREE.name,
            category="Reports",
            refresh=True
        )
        if rpt_status != "Open":
            raise CVTestStepFailure(
                f"Report [{self.store_config.Reports.FREE.name}] "
                f"has status [{rpt_status}] after auto-update; "
                f"expected [Open]"
            )
        wf_status = self.store.get_package_status(
            self.store_config.Workflows.FREE.name,
            category="Workflows"
        )
        if wf_status != "Open":
            raise CVTestStepFailure(
                f"Report [{self.store_config.Workflows.FREE.name}] "
                f"has status [{wf_status}] after auto-update; "
                f"expected [Open]"
            )

    @test_step
    def step2(self):
        """Only packages without local modifications should be auto-updated"""
        self.utils.modify_report_and_update_revision(
            self.store_config.Reports.FREE.name
        )
        self.utils.modify_workflow_and_update_revision(
            self.store_config.Workflows.FREE.id
        )
        self.utils.poll_till_auto_update()
        rpt_status = self.store.get_package_status(
            self.store_config.Reports.FREE.name,
            category="Reports",
            refresh=True
        )
        if rpt_status != "Update":
            raise CVTestStepFailure(
                f"Report [{self.store_config.Reports.FREE.name}] "
                f"has status [{rpt_status}] after auto-update; "
                f"expected [Update]"
            )
        wf_status = self.store.get_package_status(
            self.store_config.Workflows.FREE.name,
            category="Workflows"
        )
        if wf_status != "Update":
            raise CVTestStepFailure(
                f"Report [{self.store_config.Workflows.FREE.name}] "
                f"has status [{wf_status}] after auto-update; "
                f"expected [Update]"
            )

    @test_step
    def step3(self):
        """If auto-update is disabled, packages should not be updated"""
        # self.__configure_package_revisions()
        self.store.disable_auto_update()
        self.utils.set_report_revision(
            self.store_config.Reports.FREE.name
        )
        self.utils.set_workflow_revision(
            self.store_config.Workflows.FREE.id
        )
        self.utils.poll_till_auto_update()
        rpt_status = self.store.get_package_status(
            self.store_config.Reports.FREE.name,
            category="Reports",
            refresh=True
        )
        if rpt_status != "Update":
            raise CVTestStepFailure(
                f"Report [{self.store_config.Reports.FREE.name}] "
                f"has status [{rpt_status}] after auto-update; "
                f"expected [Update]"
            )
        wf_status = self.store.get_package_status(
            self.store_config.Workflows.FREE.name,
            category="Workflows"
        )
        if wf_status != "Update":
            raise CVTestStepFailure(
                f"Report [{self.store_config.Workflows.FREE.name}] "
                f"has status [{wf_status}] after auto-update; "
                f"expected [Update]"
            )

    def run(self):
        try:
            self.init_tc()
            self.step1()
            self.step2()
            self.step3()
        except Exception as e:
            self.utils.handle_testcase_exception(e)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            logout_silently(self.cre_api)
