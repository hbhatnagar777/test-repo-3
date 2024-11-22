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
    category = "Media Kits"

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Store: Version Filters"
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

    def _validate_if_filter_works(self, category, sub_category, quick_filter):
        self.log.info("")
        self.log.info(
            f"Validating packages inside Category - [{category}], "
            f"Subcategory - [{sub_category}], quick filter [{quick_filter}]"
        )
        packages = self.store.get_all_packages(
            category=category,
            sub_category=sub_category,
            quick_filter=quick_filter
        )
        quick_filter = "%" if quick_filter == "All" else quick_filter
        db_pkgs = self.utils.get_pkgs_from_server_db(
            category=category,
            sub_category=sub_category,
            version=quick_filter
        ).sort()
        if packages.sort() != db_pkgs:
            raise CVTestStepFailure(
                f"One or more package don't belong to Category {category} "
                f"and Sub-Category {sub_category}; Packages are {packages}"
            )

    @test_step
    def validate_all_filters_exist(self):
        """Validating all filters exist"""
        self.log.info(f"Validating filters for category {TestCase.category}")
        self.store.filter_by(category=TestCase.category)
        ui_filters = self.store.get_all_available_filters()
        db_filters = self.utils.get_version_filters_from_db(TestCase.category)
        if db_filters.sort() != ui_filters.sort():
            raise CVTestStepFailure(
                f"Expected {db_filters}, received {ui_filters}"
            )

    @test_step
    def validate_version_filters(self):
        """When we click on the filter, only packages matching the filter should be displayed"""
        sub_categories = self.utils.get_subcategories_from_server_db(TestCase.category)[:2]
        for sub_catg in range(2):
            quick_filters = self.utils.get_version_filters_from_db(TestCase.category, sub_categories[sub_catg])
            for quick_filter in quick_filters:
                self._validate_if_filter_works(TestCase.category, sub_categories[sub_catg], quick_filter)

    def run(self):
        try:
            self.init_tc()
            self.validate_all_filters_exist()
            self.validate_version_filters()
        except Exception as e:
            self.utils.handle_testcase_exception(e)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
