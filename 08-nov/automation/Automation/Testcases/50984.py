# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Reports.manage_reports import ManageReport

from Web.Common.cvbrowser import Browser
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.health_tiles import GenericTile
from Web.AdminConsole.Reports.health import Health, HealthConstants

from Reports.utils import TestCaseUtils

from Web.Common.exceptions import CVTestStepFailure

_CONFIG = get_config()


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.admin_console = None
        self.name = "Health tiles view and filter validation"
        self.utils = None
        self.browser = None
        self.health = None
        self.navigator = None
        self.category_list = []
        self.severity_list = []
        self.total_tiles = 0

    def init_tc(self):
        try:
            self.utils = TestCaseUtils(self)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"]
            )
            self.health = Health(self.admin_console)
            self.navigator = self.admin_console.navigator
            manage_reports = ManageReport(self.admin_console)
            self.navigator.navigate_to_metrics()
            manage_reports.access_commcell_health(self.commcell.commserv_hostname.split('.')[0])
            self.total_tiles = len(self.health.get_visible_tiles())
            if self.total_tiles == 0:
                raise Exception("Health Tiles are not visible")
        except Exception as expt:
            raise CVTestCaseInitFailure(expt) from expt

    @test_step
    def validate_view_by_category(self):
        """Validate view by category"""
        self.health.view_by_category()
        self.category_list = self.health.get_category_list()
        if not self.category_list:
            raise CVTestStepFailure("Categories are not visible")
        self.validate_category_order()

    @test_step
    def validate_category_order(self):
        """Validate category order"""
        expected_order = ['Configuration', 'Client', 'Job', 'DeDuplication',
                          'Indexing and Search', 'Usage Profile', 'Capacity Planning',  'Scale Statistics']
        if self.category_list == expected_order:
            self.log.info("Report category is in the order")
        else:
            raise CVTestStepFailure(
                "Report category is not in order, Expected order [%s] visible order [%s]" %
                (expected_order, self.category_list))

    @test_step
    def validate_view_by_severity(self):
        """Validate the severity and check the order"""
        self.health.view_by_severity()
        self.severity_list = self.health.get_category_list()
        if not self.severity_list:
            raise CVTestStepFailure("Severities are not visible ")
        self.validate_severity_order()

    @test_step
    def validate_severity_order(self):
        """Validate the order of severity   """
        expected_order = ['Critical', 'Warning', 'Good', 'Information']
        if self.severity_list == expected_order:
            self.log.info("Report severity is proper")
        else:
            raise CVTestStepFailure(
                "Report severity is not in order, Expected order [%s] visible order[%s]" %
                (expected_order, self.severity_list))

    def validate_visible_tiles_w_filter(self, filter_name):
        """Validate visible tiles each filter"""
        visible_tiles_list = self.health.get_visible_tiles()
        for each_tile in visible_tiles_list:
            health_tile = GenericTile(self.admin_console, each_tile)
            tile_status = health_tile.get_health_status()
            if tile_status != filter_name:
                raise CVTestStepFailure("With Filter [%s] Tile [%s] with status [%s] is"
                                        "visible" %
                                        filter_name,
                                        each_tile,
                                        tile_status)

    @test_step
    def validate_filter_by_critical(self):
        """ Validate critical status and corresponding reports status"""
        self.health.filter_by_critical()
        visible_status = self.health.get_category_list()
        if len(visible_status) != 1 and visible_status[0] != HealthConstants.STATUS_CRITICAL:
            raise CVTestStepFailure("Expected status is [%s] but visible status is [%s]" % (
                HealthConstants.STATUS_CRITICAL, visible_status))
        self.validate_visible_tiles_w_filter(HealthConstants.STATUS_CRITICAL)

    @test_step
    def validate_filter_by_warning(self):
        """Validate warning status and corresponding reports status"""
        self.health.filter_by_warning()
        visible_status = self.health.get_category_list()
        if len(visible_status) != 1 and visible_status[0] == HealthConstants.STATUS_WARNING:
            raise CVTestStepFailure("Expected status is [%s] but visible status is [%s]" % (
                HealthConstants.STATUS_WARNING, visible_status))
        self.validate_visible_tiles_w_filter(HealthConstants.STATUS_WARNING)

    @test_step
    def validate_filter_by_good(self):
        """Validate warning status and corresponding reports"""
        self.health.filter_by_good()
        visible_status = self.health.get_category_list()
        if len(visible_status) != 1 and visible_status[0] == HealthConstants.STATUS_GOOD:
            raise CVTestStepFailure("Expected status is [%s] but visible status is [%s]" % (
                HealthConstants.STATUS_GOOD, visible_status))
        self.validate_visible_tiles_w_filter(HealthConstants.STATUS_GOOD)

    @test_step
    def validate_filter_by_info(self):
        """Validate info status and corresponding reports"""
        self.health.filter_by_information()
        visible_status = self.health.get_category_list()
        if len(visible_status) != 1 and visible_status[0] == HealthConstants.STATUS_INFO:
            raise CVTestStepFailure("Expected status is [%s] but visible status is [%s]" % (
                HealthConstants.STATUS_INFO, visible_status))
        self.validate_visible_tiles_w_filter(HealthConstants.STATUS_INFO)

    @test_step
    def validate_remove_filter(self):
        """Validate remove filter by clicking again on all"""
        self.health.select_all_severity()

        tiles_count = len(self.health.get_visible_tiles())
        if self.total_tiles == tiles_count:
            self.log.info("All the tiles are visible")
        else:
            raise CVTestStepFailure(f"Expected tiles count {self.total_tiles} but received tiles count {tiles_count}")

    def run(self):
        try:
            self.init_tc()
            self.validate_view_by_category()
            self.validate_view_by_severity()
            self.validate_filter_by_critical()
            self.validate_filter_by_warning()
            self.validate_filter_by_good()
            self.validate_filter_by_info()
            self.validate_remove_filter()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
