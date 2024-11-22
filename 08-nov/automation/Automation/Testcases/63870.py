# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------
"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --   initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.Common.cvbrowser import BrowserFactory
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.dashboard import Dashboard
from Web.WebConsole.Reports.Metrics.licensesummary import LicenseSummary


class TestCase(CVTestCase):
    """ basic acceptance test case for license summary """

    def __init__(self):
        """Initializing the Test case file """
        super(TestCase, self).__init__()
        self.name = "Verify current workload usage page on license summary worldwide report"
        self.factory = None
        self.browser = None
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.clientname = None
        self.webconsole = None
        self.navigator  = None
        self.dashboard = None
        self.lic_summary = None
        self.tcinputs = {
            'clientname': None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""

        self.clientname = self.tcinputs['clientname']
        self.factory = BrowserFactory()
        self.browser = self.factory.create_browser_object()
        self.browser.open()
        self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
        self.webconsole.login(self.inputJSONnode['commcell']['commcellUsername'],
                              self.inputJSONnode['commcell']['commcellPassword'])        
        self.navigator = Navigator(self.webconsole)
        self.dashboard = Dashboard(self.webconsole)
        self.lic_summary = LicenseSummary(self.webconsole)
        
    def run(self):
        """Run function of this test case"""
        try:
            self.webconsole.goto_commcell_dashboard()
            self.navigator.goto_commcell_dashboard(self.clientname)
            self.dashboard.view_detailed_report("Current Capacity Usage")
            self.lic_summary.click_workloadusage() 
            self.webconsole.wait_till_load_complete()
            log_windows = self.browser._driver.window_handles
            if len(log_windows)>=1:
                self.browser._driver.switch_to.window(log_windows[1])
            self.lic_summary.get_table_data("workload")
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """To clean-up the test case environment created"""
        self.browser.close()
