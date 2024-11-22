# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


from AutomationUtils.cvtestcase import CVTestCase
from Reports.Custom.sql_utils import SQLQueries
from Reports.Custom.utils import CustomReportUtils
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure, CVTestStepFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom import builder, viewer
from Web.WebConsole.Reports.Custom.builder import Page, Datasets
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.viewer = None
        self.data_table = None
        self.name = "Custom Report Builder: Component Security Validation"
        self.role = "CommCell Admin"
        self.utils = None
        self.webconsole: WebConsole = None
        self.browser: Browser = None
        self.rpt_builder = None
        self.dataset = None
        self.table = "AutomationTable"
        self.page = "Page1"

    def init_tc(self):
        try:
            self.utils = CustomReportUtils(self, self.webconsole, self.inputJSONnode["commcell"]["commcellUsername"],
                                           self.inputJSONnode["commcell"]["commcellPassword"])
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser, self.commcell.webconsole_hostname
            )
            self.webconsole.login(self.inputJSONnode["commcell"]["commcellUsername"],
                                  self.inputJSONnode["commcell"]["commcellPassword"])
            self.utils.cre_api.delete_custom_report_by_name(self.name, suppress=True)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    def add_component_to_page(self):
        """ Adds a data table component to a page"""
        dataset = Datasets.DatabaseDataset()
        self.rpt_builder.add_dataset(dataset)
        dataset.set_dataset_name("AutomationDataSet")
        dataset.set_local_commcell_datasource()
        dataset.set_sql_query(SQLQueries.sql_server_q1(top=5))
        dataset.save()
        self.data_table = builder.DataTable(self.table)
        self.rpt_builder.add_component(self.data_table, dataset)
        self.data_table.add_column_from_dataset()

    def create_report(self):
        """ Create a sample report with necessary Component Security and Page Security settings """
        try:
            Navigator(self.webconsole).goto_report_builder()
            self.rpt_builder = builder.ReportBuilder(self.webconsole)
            self.rpt_builder.set_report_name(self.name)
            self.add_component_to_page()
            self.data_table.set_component_security(self.role)
            page1 = Page(self.page)
            self.rpt_builder.add_new_page(page1)
            self.rpt_builder.switch_page(page1)
            page1.set_component_security(self.role)
            self.add_component_to_page()
            self.rpt_builder.enable_show_pages_as_tabs()
            self.rpt_builder.save(deploy=True)
            self.log.info("Report is Saved and deployed successfully")
        except Exception as e:
            raise CVTestStepFailure(e)

    def share_report(self):
        """ Share Report with the Tenant Admin """
        try:
            self.rpt_builder.open_report()
            report = viewer.CustomReportViewer(self.webconsole)
            security = report.open_security()
            security.associate_security_permission(users=[self.tcinputs["TenantAdmin"]])
            security.update()
            self.log.info("Report is shared with Tenant Admin")
            WebConsole.logout_silently(self.webconsole)
        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def verify_component_security(self):
        """ Verify Component Security and Page Security """
        self.webconsole.login(self.tcinputs["TenantAdmin"], self.tcinputs["TenantAdminPwd"])
        self.webconsole.goto_reports()
        Navigator(self.webconsole).goto_commcell_reports(report_name=self.name)
        rpt_viewer = viewer.CustomReportViewer(self.webconsole)
        table_list = rpt_viewer.get_all_report_table_names()
        page_list = rpt_viewer.get_all_page_title_names()
        if self.table not in table_list:
            self.log.info(f"{self.table} is not found. Component Security Check Passed")
        else:
            raise CVTestStepFailure(f"{self.table} is seen by Tenant Admin. Component Security check Failed")
        if self.page not in page_list:
            self.log.info(f"{self.page} is not accessible. Page Security Check Passed")
        else:
            raise CVTestStepFailure(f"{self.page} is accessible by Tenant Admin. Page Security check Failed")

    def run(self):
        try:
            self.init_tc()
            self.create_report()
            self.share_report()
            self.verify_component_security()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            self.utils.cre_api.delete_custom_report_by_name(self.name, suppress=True)
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
