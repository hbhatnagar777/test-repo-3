# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics:Webconsole/Console url in monitoring form """

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Reports import reportsutils

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.report import MetricsReport
from Web.WebConsole.Reports.monitoringform import ManageCommcells

from AutomationUtils.cvtestcase import CVTestCase

from Reports.utils import TestCaseUtils

CommcellActions = ManageCommcells.CommcellActions


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics:Webconsole/Console url in monitoring form"
        self.show_to_user = True
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.report = None
        self._driver = None
        self.manage_commcells = None
        self.commcell_name = None
        self.utils = TestCaseUtils(self)

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            # open browser
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.open()

            # login to web console and redirect to ww reports.
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(
                self.inputJSONnode['commcell']["commcellUsername"],
                self.inputJSONnode['commcell']["commcellPassword"]
            )
            self._driver = self.browser.driver
            self.webconsole.goto_reports()
            self.commcell_name = reportsutils.get_commcell_name(self.commcell)
            self.manage_commcells = ManageCommcells(self.webconsole)
            self.navigator = Navigator(self.webconsole)
            self.navigator.goto_worldwide_commcells()
            self.report = MetricsReport(self.webconsole)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def verify_commcell_actions(self):
        """Verify valid action options are present in commcell monitoring page"""
        expected_list_of_actions = [CommcellActions.WEBCONSOLE, CommcellActions.ADMIN_CONSOLE,
                                    CommcellActions.CONSOLE, CommcellActions.SECURITY,
                                    CommcellActions.DELETE]
        commcell_action_options_webconsole = self.manage_commcells.get_commcell_action_options(
            self.commcell.commserv_name)
        if sorted(commcell_action_options_webconsole) != sorted(expected_list_of_actions):
            self.log.error("Expected commcell action options %s", expected_list_of_actions)
            self.log.error("Commcell action options present in webconsole %s",
                           commcell_action_options_webconsole)
            raise CVTestCaseInitFailure("Expected commcell actions are not present in "
                                        "commcell monitoring page")
        self.log.info("Expected commcell action options are present in commcell %s",
                      self.commcell.commserv_name)

    def get_tab_url(self):
        """Switch to new tab, get url and close the new tab"""
        self._driver.switch_to.window(self._driver.window_handles[1])
        self.webconsole.wait_till_load_complete()
        url = self._driver.current_url
        self._driver.close()
        self._driver.switch_to.window(self._driver.window_handles[0])
        return url

    @test_step
    def verify_urls(self):
        """For v11 commcells, verify console and web console urls are correct"""
        self.navigator.goto_worldwide_commcells()
        self.manage_commcells.access_commcell_web_console(self.commcell_name)
        url = self.get_tab_url()
        if self.commcell_name.lower() not in url.lower():
            raise CVTestStepFailure("commcell webconsole url is not correct in monitoring "
                                    "page for commcell [%s]"
                                    % self.commcell_name)
        self.log.info("Verified web console url for the [%s] commcell", self.commcell_name)
        self.manage_commcells.access_commcell_console(self.commcell_name)
        url = self.get_tab_url()
        if self.commcell_name.lower() not in url.lower():
            raise CVTestStepFailure("commcell console url is not correct in monitoring "
                                    "page for commcell [%s]"
                                    % self.commcell_name)
        self.log.info("Verified console url for the [%s] commcell", self.commcell_name)

    def run(self):
        try:
            self.init_tc()
            self.verify_commcell_actions()
            self.verify_urls()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
