# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics: Verify non existence of Dedup tiles under Growth and Trend Report on public cloud"""
from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure
)
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.growthtrend import GrowthNTrend

from AutomationUtils.cvtestcase import CVTestCase

from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """TestCase class used to execute the test case from here."""

    test_step = TestStep()
    DEDUP_TILES = ["CommCell Dedupe Savings", "Agent Dedupe Savings",
                   "Subclient Dedupe Savings", "Storage Policy Dedupe Savings"]

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics: Verify non existence of Dedup tiles under Growth and Trend Report on public cloud"
        self.browser = None
        self.webconsole = None
        self.utils = TestCaseUtils(self)

    def _init_tc(self):
        """Initial configuration for the test case"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(self._inputJSONnode["commcell"]["commcellUsername"],
                                  self._inputJSONnode["commcell"]["commcellPassword"])
            self.webconsole.goto_commcell_dashboard()
            navigator = Navigator(self.webconsole)
            navigator.goto_commcell_reports("Growth and Trends", self.commcell.commserv_name)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def verify_absence_of_dedup_tiles(self):
        """Verify absence of Dedup tiles"""
        entities = GrowthNTrend(self.webconsole).get_entities()
        violated_tiles = [tile for tile in TestCase.DEDUP_TILES if tile in entities]
        if violated_tiles:
            raise CVTestStepFailure(f"{violated_tiles} are seen in public cloud Growth and Trend report")

    def run(self):
        try:
            self._init_tc()
            self.verify_absence_of_dedup_tiles()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
