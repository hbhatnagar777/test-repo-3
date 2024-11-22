# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""Main file for executing this test case"""

from selenium.common.exceptions import WebDriverException

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVWebAutomationException
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure
from Web.WebConsole.Reports.Company.RegisteredCompanies import RegisteredCompanies
from Web.WebConsole.Reports.Metrics.components import MetricsTable
from Web.WebConsole.Reports.Metrics.profile import Profile
from Web.WebConsole.Reports.Metrics.report import MetricsReport

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator

from Reports.utils import TestCaseUtils

_CONFIG = get_config()

"""Metrics Profile : Verify profile dashboard"""


class TestCase(CVTestCase):
    """TestCase class used to execute the test case from here."""
    test_step = TestStep()
    FOLDER_NAME = "Automation Folder"

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics Profile : Verify profile dashboard"
        self.browser = None
        self.webconsole = None
        self.commcell_group = None
        self.navigator = None
        self.utils = None
        self.profile = None
        self.report = None

    def init_tc(self):
        """Initial configuration for the test case."""
        try:
            self.utils = TestCaseUtils(self)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.utils.get_temp_dir())

            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(self.inputJSONnode['commcell']['commcellUsername'],
                                  self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = Navigator(self.webconsole)
            self.webconsole.goto_reports()
            self.navigator.goto_companies()
            company = RegisteredCompanies(self.webconsole)
            company.access_company(self.tcinputs['company'])
            self.navigator.goto_profile()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def verify_sla_trends_and_documents(self, division_name):
        """Verifies proper loading of SLA Trends report under the given commcell group

        Args:
            division_name:  name of the division under which SLA Trend report is seen

        Returns:

        """
        self.profile = Profile(self.webconsole)
        try:
            self.profile.delete_folder_in_documents(TestCase.FOLDER_NAME)
        except CVWebAutomationException:
            pass
        self.profile.create_new_folder(TestCase.FOLDER_NAME)
        self.profile.download_file_in_documents("custom_reports.png")
        self.utils.wait_for_file_to_download('png')
        self.utils.validate_tmp_files("png")
        self.log.info("png download completed successfully")
        _ = self.utils.get_temp_files("png")[0]
        self.profile.delete_folder_in_documents(TestCase.FOLDER_NAME)

        self.profile.access_sla_trend_report()
        self.report = MetricsReport(self.webconsole)
        if self.report.is_page_blank():
            raise CVTestStepFailure("SLA Trend Report is blank")

        if division_name not in self.navigator.get_bread_crumb():
            raise CVTestStepFailure(f"SLA Trend Report is not opened under {division_name}")

        self.navigator.goto_profile()
        if self.profile.is_document_upload_icon_visible() is False:
            raise CVTestStepFailure("Upload icon is not visible")

    @test_step
    def verify_export(self):
        """Exports the report as PDF"""
        self.utils.reset_temp_dir()
        report = MetricsReport(self.webconsole)
        export = report.export_handler()
        export.to_pdf()
        self.utils.wait_for_file_to_download('pdf')
        self.utils.validate_tmp_files("pdf")
        self.log.info("pdf export completed successfully")
        _ = self.utils.get_temp_files("pdf")[0]

    def verify_customer_satisfation_as_commvault_user(self):
        """Verifies proper loading of Customer Satisfaction report under the given commcell group"""
        try:
            self.profile.submit_customer_satisfaction("dummy")
            raise CVTestStepFailure("Commvault user is able to add customer satisfaction")
        except CVWebAutomationException:
            pass

        self.profile.access_customer_satisfaction_report()
        table_1 = MetricsTable(self.webconsole, "Customer Satisfaction")
        table_2 = MetricsTable(self.webconsole, "Commvault Influence")
        try:
            table_1.get_table_title()
            table_2.get_table_title()
        except WebDriverException:
            raise CVTestStepFailure("Unable to get satisfaction of influence table")

        self.navigator.goto_profile()

    @test_step
    def verify_customer_satisfation_as_non_commvault_user(self):
        """Verifies proper loading of Customer Satisfaction report under for non commvault user"""
        with BrowserFactory().create_browser_object() as browser,\
                WebConsole(browser, self.commcell.webconsole_hostname,
                           self.tcinputs['customer_user'], self.tcinputs['password']) as webconsole:
            navigator = Navigator(webconsole)
            webconsole.goto_reports()
            navigator.goto_companies()
            company = RegisteredCompanies(webconsole)
            company.access_company(self.tcinputs['company'])
            navigator.goto_profile()
            profile = Profile(webconsole)
            profile.submit_customer_satisfaction("Sample response")
            profile.access_customer_satisfaction_report()

            table_1 = MetricsTable(webconsole, "Customer Satisfaction")
            table_2 = MetricsTable(webconsole, "Commvault Influence")
            table_1.get_table_title()
            try:
                table_2.get_table_title()
                raise CVTestStepFailure("Commvault Influence is seen by non commvault user")
            except WebDriverException:
                pass

    def run(self):
        try:
            self.init_tc()
            # self.verify_profile_panel_under_navigation_panel()

            self.verify_sla_trends_and_documents(f"{self.tcinputs['company']} (Reports)")
            self.verify_export()
            self.verify_customer_satisfation_as_commvault_user()

            self.log.info(f"{'*'*20}\nRunning on Company Profile\n{'x'*20}")

            self.navigator.goto_companies()
            company = RegisteredCompanies(self.webconsole)
            company.access_company(self.tcinputs['company'])
            self.navigator.goto_profile()

            self.verify_sla_trends_and_documents(f"{self.tcinputs['company']} (Reports)")
            self.verify_export()
            self.verify_customer_satisfation_as_commvault_user()
            self.verify_customer_satisfation_as_non_commvault_user()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
