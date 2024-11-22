# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics Reports page to enable/disable a report and edit Retention """
from xml.etree import ElementTree as ET

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.report import MetricsReport
from Web.WebConsole.Reports.settings import ReportSettings

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import CommServDatabase

from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics Reports page to enable/disable a report and edit Retention"
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.report = None
        self.report_settings = None
        self.metrics_report = None
        self.retention_report = None
        self.status_report = None
        self.old_retention_web = None
        self.csdb = None
        self.backup_jobs_page = None
        self.utils = TestCaseUtils(self)

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            # open browser
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.open()

            # login to web console
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(
                self.inputJSONnode['commcell']["commcellUsername"],
                self.inputJSONnode['commcell']["commcellPassword"]
            )
            self.webconsole.goto_reports()
            self.navigator = Navigator(self.webconsole)
            self.metrics_report = MetricsReport(self.webconsole)
            self.report_settings = ReportSettings(self.webconsole)
            self.navigator.goto_report_settings()
            self.csdb = CommServDatabase(self._commcell)
            self.retention_report = "Average Throughput of Jobs in the Last Week"
            self.status_report = "Activity - Job Details"
            if self.report_settings.get_report_status(self.status_report) == 'Disabled':
                self.report_settings.set_report_status(report_name=self.status_report,
                                                       status=self.report_settings.ReportStatus.
                                                       REPORT_ENABLED)
            self.navigator.goto_report_settings()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def verify_report_hyperlink(self):
        """Access report and verify its redirecting to correct report page from settings"""
        report_table = self.metrics_report.get_tables()[0]
        reports = report_table.get_data_from_column('Report Name')
        for each_report in reports:
            self.report_settings.access_report(each_report)
            self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])
            report_title = self.metrics_report.get_page_title()
            expected_report_title = each_report
            if each_report == 'Activity - Job Details':
                expected_report_title = 'Daily Backup Jobs'

            elif each_report in ['Daily Storage Usage and Chargeback',
                                 'Weekly Storage Usage and Chargeback',
                                 'Monthly Storage Usage and Chargeback']:
                expected_report_title = 'Chargeback'
            if report_title == expected_report_title:
                self.log.info("Verified [%s] report hyperlink", report_title)
                self.browser.driver.close()
                self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
                continue
            raise CVTestStepFailure("Report title [%s] from settings page is not same as "
                                    "report name [%s]" % (each_report, report_title))

    def get_retention_value_from_db(self):
        """Get retention value of report from db"""
        query = "select userModifiedProps from cvcloud..cf_WebConsoleReports where name = '" + \
                self.retention_report + "'"
        self.csdb.execute(query)
        row = self.csdb.fetch_all_rows()[0][0]
        retention_node = ET.fromstring(row)
        retention_dict = retention_node.attrib
        return retention_dict['retention']

    @test_step
    def verify_retention(self):
        """Verify retention"""
        self.old_retention_web = self.report_settings.get_retention_value(self.retention_report)
        self.old_retention_web = int(self.old_retention_web.split()[0])
        self.report_settings.set_retention(report_name=self.retention_report,
                                           retention_value=str(self.old_retention_web+1))
        retention_value_db = self.get_retention_value_from_db()
        if retention_value_db != str(self.old_retention_web + 1):
            raise CVTestStepFailure("Failure to edit the retention value of the [%s] report")
        self.log.info("Retention is successfully set")

    def verify_report_status_from_db(self):
        """Verify report status from db"""
        self.log.info("Verifying in db report status is set as disabled")
        query = "select userModifiedProps from cvcloud..cf_WebConsoleReports where name = '" + \
                self.status_report + "'"
        self.csdb.execute(query)
        row = self.csdb.fetch_all_rows()[0][0]
        status_node = ET.fromstring(row)
        status_dict = status_node.attrib
        status_value_db = status_dict['status']
        if status_value_db != '0':
            raise CVTestStepFailure("Disabling report did not disable report in DB")

    def verify_report_status(self):
        """Verify report status"""
        self.log.info("Set report status as disabled for the [%s] report in settings page",
                      self.status_report)
        self.report_settings.set_report_status(self.status_report,
                                               self.report_settings.ReportStatus.REPORT_DISABLED)
        self.verify_report_status_from_db()
        self.log.info("[%s] report is successfully disabled in db", self.status_report)

    def reset_report_settings(self):
        """Reset report settings"""
        self.log.info("Reset retention period")
        self.report_settings.set_retention(self.retention_report, self.old_retention_web)
        self.log.info("Reset report status as enabled")
        self.report_settings.set_report_status(report_name=self.status_report,
                                               status=self.report_settings.ReportStatus.REPORT_ENABLED)

    def run(self):
        try:
            self.init_tc()
            self.verify_report_hyperlink()
            self.verify_retention()
            self.verify_report_status()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.reset_report_settings()
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
