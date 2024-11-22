# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from Reports.storeutils import StoreUtils
from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import (
    CVTestStepFailure,
    CVTestCaseInitFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Store.storeapp import StoreApp
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Store: Price Filters"
        self.store: StoreApp = None
        self.webconsole: WebConsole = None
        self.browser = None
        self.utils = StoreUtils(self)

    def init_tc(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser,
                self.commcell.webconsole_hostname
            )
            self.webconsole.login(self.inputJSONnode['commcell']["commcellUsername"],
                                  self.inputJSONnode['commcell']["commcellPassword"])
            self.webconsole.goto_store()
            self.store = StoreApp(self.webconsole)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    def _validate_if_filter_works(self, category, quick_filter):
        self.log.info("")
        self.log.info(
            f"Validating packages inside Category - [{category}], "
            f" quick filter [{quick_filter}]"
        )
        packages = self.store.get_all_packages(
            category=category,
            quick_filter=quick_filter
        ).sort()
        price_filter = {"All": '%', "Free": 0, "Premium": 1, "Proactive Support": 2}
        quick_filter = price_filter[quick_filter]
        db_pkgs = self.utils.get_pkgs_from_server_db(
            category=category,
            price=quick_filter
        ).sort()
        if packages != db_pkgs:
            raise CVTestStepFailure(
                f"One or more package don't belong to Category {category} "
                f"; Packages are {packages}"
            )

    @test_step
    def validate_price_filters(self):
        """When we click on the filter, only packages matching the filter should be displayed"""
        category = "Reports"
        self.store.filter_by(category=category)
        quick_filter = self.store.get_all_available_filters()
        for x in range(1, -1, -1):
            self._validate_if_filter_works(
                    category, quick_filter[x]
                )

    def run(self):
        try:
            self.init_tc()
            self.validate_price_filters()
        except Exception as e:
            self.utils.handle_testcase_exception(e)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
