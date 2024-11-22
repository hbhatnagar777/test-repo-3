# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase to validate Metrics single commcell user
"""

from AutomationUtils.cvtestcase import CVTestCase

from Reports.utils import TestCaseUtils
from Web.AdminConsole.Reports.commcells import Commcell
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.adminconsole import AdminConsole

from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.page_object import TestStep

from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """Testcase to verify backward compatibility of Metrics Collection queries"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self._driver = None
        self.manage_report = None
        self.name = "Metrics: Single commcell user validation"
        self.admin_console = None
        self.navigator = None
        self.browser = None
        self.metrics_commcell = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "single_commcell_user": None,
            "password": None
        }

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.tcinputs["single_commcell_user"],
                                     self.tcinputs["password"])
            self.manage_report = ManageReport(self.admin_console)
            self.metrics_commcell = Commcell(self.admin_console)
            self.navigator = self.admin_console.navigator
            self._driver = self.browser.driver
            self.navigator.navigate_to_metrics()
            self.manage_report.access_dashboard()
            if self.metrics_commcell.is_it_single_commcell() is False:
                cc_count = len(self.metrics_commcell.get_commcell_names())
                raise CVTestCaseInitFailure(
                    "Single user account needed for this Testcase, "
                    f"user [{self.tcinputs['single_commcell_user']}] has {cc_count} CommCells"
                )

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    @test_step
    def verify_commcell_dashboard(self):
        """Verify CommCell level dashboard is visible by default"""
        self.manage_report.access_commcell()
        cc_list = self.metrics_commcell.get_commcell_names()
        if len(cc_list) != 1:
            raise CVTestCaseInitFailure(
                f"Expected commcell count in monitoring page is 1 but [{len(cc_list)}] are shown"
            )
        self.manage_report.select_commcell_name(cc_list[0])
        title = self.manage_report.get_dashboard_title()
        cc_name = cc_list[0]
        if title != cc_name:
            raise CVTestStepFailure(
                f"Expected tile is CommCell Name [{cc_name}] but it is {title}"
            )

    @test_step
    def verify_reports_visible(self):
        """Verify all metrics reports are visible in commcell level report page also"""
        total_reports = self.tcinputs['report_count']
        self.manage_report.access_report_tab()
        reports = Report(self.admin_console)
        report_count = len(reports.get_all_reports())
        if report_count != total_reports:
            raise CVTestStepFailure(f"Report count is not matching expected CommCell level Reports {total_reports}"
                                    f"but received {report_count}")

    def run(self):
        try:
            self.init_tc()
            self.verify_commcell_dashboard()
            self.verify_reports_visible()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
