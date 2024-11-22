# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from Reports import utils
from Reports.storeutils import StoreUtils
from Web.API.customreports import logout_silently
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
        self.name = "Store: Free and Premium status"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.SOFTWARESTORE
        self.feature = self.features_list.WEBCONSOLE
        self.browser = None
        self.webconsole = None
        self.reports = None
        self.store: StoreApp = None
        self.utils = None
        self.inputs = None

    def init_tc(self):
        try:
            self.utils = StoreUtils(self)
            self.inputs = StoreUtils.get_store_config()
            # check if package has free and premium status on store server
            self.utils.validate_for_free_status(
                self.inputs.Reports.FREE.name
            )
            # self.utils.validate_for_premium_status(
            #     self.inputs.Reports.PREMIUM
            # )

            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser,
                self.commcell.webconsole_hostname
            )
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.utils.store_server_api
            self.utils.cre_api
            self.store = StoreApp(self.webconsole)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def free_status(self):
        """If the report's pricing is set to 'Free' report should be installable"""
        self.utils.cre_api.delete_custom_report_by_name(
            self.inputs.Reports.FREE.name, suppress=True
        )
        self.webconsole.goto_store(
            username=self.inputs.NONPREMIUM_USERNAME,
            password=self.inputs.NONPREMIUM_PASSWORD
        )
        pkg_status = self.store.get_package_status(
            self.inputs.Reports.FREE.name,
            category="Reports"
        )
        if pkg_status != "Install":
            raise CVTestStepFailure(
                "[%s] is not having install status" %
                self.inputs.Reports.FREE.name
            )
        self.store.install_report(
            self.inputs.Reports.FREE.name
        )

    @test_step
    def premium_status(self):
        """If package is premium, Purchase status should be seen"""
        self.webconsole.goto_store(direct=True)
        status = self.store.get_package_status(
            self.inputs.Reports.PREMIUM,
            category="Reports"
        )
        if status != "Purchase":
            raise CVTestCaseInitFailure(
                "[%s] is having [%s] status instead of Purchase" % (
                    self.inputs.Reports.PREMIUM,
                    status
                )
            )
        info_msg = self.store.get_premium_info_message(
            self.inputs.Reports.PREMIUM
        )
        if "You must be a Premium Member" not in info_msg:
            raise CVTestStepFailure(
                f"Unexpected message [{info_msg}] in Premium popup "
                f"window"
            )

    def run(self):
        try:
            self.init_tc()
            self.free_status()
            # self.premium_status()
        except Exception as err:
            utils.TestCaseUtils(self).handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
            logout_silently(self.utils.cre_api)
