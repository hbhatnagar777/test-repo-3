# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole

from Web.AdminConsole.Reports.health import Health
from Web.AdminConsole.Reports.health_tiles import GenericTile
from Web.AdminConsole.Reports.manage_reports import ManageReport

from Web.Common.cvbrowser import Browser
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep


from Reports.utils import TestCaseUtils

from Web.Common.exceptions import CVTestStepFailure


_CONFIG = get_config()


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.admin_console = None
        self.name = "Validate show and hidden tiles on Health report"
        self.utils = None
        self.browser = None
        self.webconsole = None
        self.health = None
        self.navigator = None
        self.total_tiles = 0
        self.tile = None

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
            manage_reports.access_commcell_health(self.commcell.commserv_hostname.split('.')[0].lower())
            self.total_tiles = self.health.get_total_tiles_count()
            tile_name = 'Security Assessment'
            self.tile = GenericTile(self.admin_console, tile_name)

        except Exception as expt:
            raise CVTestCaseInitFailure(expt) from expt

    @test_step
    def hide_tiles(self):
        """Hide a tile in Health report"""
        self.tile.hide()
        self.log.info("Tile [%s] is successfully hidden" % self.tile.tile_name)

    @test_step
    def validate_hidden_tiles(self):
        """Verify hidden tiles are not showing in report"""
        hidden_tiles = self.health.get_hidden_tiles()
        visible_tiles_list = self.health.get_visible_tiles()
        for each_tile in hidden_tiles:
            if each_tile not in visible_tiles_list:
                self.log.info("Tile [%s] is not visible in health report" % each_tile)
            else:
                raise CVTestStepFailure("Tile [%s]is visible in health report" % each_tile)

    @test_step
    def verify_show_all_tiles(self):
        """Verify show all tiles option is working"""
        self.health.show_all_tiles()
        tiles_count = len(self.health.get_visible_tiles())
        if self.total_tiles == tiles_count:
            self.log.info("All the tiles are visible")
        else:
            raise CVTestStepFailure("Expected tile count is [%s] but visible tile count is [%s]"
                                    % (self.total_tiles, tiles_count))

    def run(self):
        try:
            self.init_tc()
            self.hide_tiles()
            self.validate_hidden_tiles()
            self.verify_show_all_tiles()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
