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

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.License import License
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Metrics.licensesummary import LicenseSummary


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    
    def __init__(self):
        """Initializing the Test case file """
        super(TestCase, self).__init__()
        self.name = "Verify workload summary details page on license summary report"
        self.browser = None
        self.driver = None
        self.adminconsole = None
        self.adminpage = None
        self.lic_object = None
        self.webconsole = None
        self.lic_summary = None

    def run(self):
        """Run function of this test case"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.driver = self.browser.driver
            self.adminconsole = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.adminconsole.login(self.inputJSONnode['commcell']['commcellUsername'],
                                    self.inputJSONnode['commcell']['commcellPassword'])
            self.adminconsole.navigator.navigate_to_license()
            self.lic_object = License(self.adminconsole)
            self.webconsole = WebConsole(self.browser,self.commcell.webconsole_hostname)
            self.lic_object.access_license_summary(self.webconsole,True)
            self.lic_summary = LicenseSummary(self.webconsole) 
            self.lic_summary.click_workloadsummary()
            self.lic_summary.get_table_data("workload")
        except Exception as exp:
            handle_testcase_exception(self, exp)
    
    def tear_down(self):
        """To clean-up the test case environment created"""
        self.browser.close()
