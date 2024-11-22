# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from Web.API import customreports
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import (
    CVTestStepFailure,
    CVTestCaseInitFailure
)
from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVWebAPIException
from Reports.Custom.utils import CustomReportUtils
from Reports.Custom.report_templates import DefaultReport


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Reports (API): Reports and Dataset"
        self.utils = None
        self.api = None
        self.admin_console = None

    def init_tc(self):
        try:
            self.utils = CustomReportUtils(self, username=self.inputJSONnode["commcell"]["commcellUsername"],
                                           password=self.inputJSONnode["commcell"]["commcellPassword"])
            wc_name = self.commcell.webconsole_hostname
            self.api = customreports.CustomReportsAPI(
                wc_name, username=self.inputJSONnode["commcell"]["commcellUsername"],
                password=self.inputJSONnode["commcell"]["commcellPassword"])
            try:
                self.api.get_report_definition_by_name(self.name)
            except CVWebAPIException:
                with BrowserFactory().create_browser_object() as browser:
                    with AdminConsole(browser, wc_name) as self.admin_console:
                        DefaultReport(self.utils).build_default_report()
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def get_all_installed_reports(self):
        """Get all installed reports"""
        reports = self.api.get_all_installed_reports()
        if len(reports) < 0:
            raise CVTestStepFailure("No reports retrieved")
        self.log.info(f"Retried [{reports}]")
        return reports[0]

    @test_step
    def get_report_definition(self):
        """Get installed report"""
        defi = self.api.get_report_definition_by_name(self.name)
        if not defi:
            raise CVTestStepFailure(
                f"Unable to retrieve {self.name} report"
            )
        self.log.info(f"Retrieved report definition [{defi}]")
        return defi

    @test_step
    def delete_report(self):
        """Delete installed report"""
        self.api.delete_custom_report_by_name(self.name)

    @test_step
    def save_report_definition(self, defi):
        """Save report definition"""
        self.api.save_report_definition(defi)
        self.api.get_report_definition_by_name(self.name)

    @test_step
    def execute_sql(self):
        """Execute SQL using dataset"""
        result = self.api.execute_sql(
            """
            SELECT 1, 2, 3
            UNION 
            SELECT 4, 5, 6
            """
        )
        self.log.info(f"Received {result}")
        if result != [[1, 2, 3], [4, 5, 6]]:
            raise CVTestStepFailure(
                "Unable to execute SQL via dataset, "
                f"received [{result}]"
            )

    def run(self):
        try:
            self.init_tc()
            self.get_all_installed_reports()
            defi = self.get_report_definition()
            self.delete_report()
            self.save_report_definition(defi)
            self.execute_sql()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            customreports.logout_silently(self.api)
