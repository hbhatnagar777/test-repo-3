# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics Report : Verify Health Tiles loaded properly"""
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure,
    CVWebAutomationException
)
from Web.Common.page_object import TestStep

from Web.AdminConsole.Reports.health import Health
from Web.AdminConsole.Reports.health_tiles import GenericTile
from Web.AdminConsole.Reports.manage_reports import ManageReport

from AutomationUtils.cvtestcase import CVTestCase

from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """TestCase class used to execute the test case from here."""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics Report : Verify Health Tiles loaded properly"
        self.browser = None
        self.webconsole = None
        self.utils = TestCaseUtils(self)

    def _init_tc(self):
        """Initial configuration for the test case"""
        try:
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
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def verify_tiles(self):
        """Verify for properly loaded tiles"""
        health = Health(self.admin_console)
        outcome = list()
        status = list()
        for tile_name in health.get_visible_tiles():
            tile = GenericTile(self.admin_console, tile_name)
            if not tile.get_outcome():
                outcome.append(tile.tile_name())
            try:
                tile.get_health_status()
            except CVWebAutomationException:
                status.append(tile.tile_name())

        if status or outcome:
            raise CVTestStepFailure(f"{status} does not have any status \n "
                                    f"{outcome} does not have any content in the body")

    def run(self):
        try:
            self._init_tc()
            self.verify_tiles()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
