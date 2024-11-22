# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure, CVTestStepFailure
)
from Web.Common.page_object import TestStep

from Web.WebConsole.Reports.Custom import builder
from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.webconsole import WebConsole

from Reports.Custom.sql_utils import (
    SQLQueries, ValueProcessors
)
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report (DataSet) - R Script"
        self.webconsole = None
        self.manage_reports = None
        self.admin_console = None
        self.navigator = None
        self.builder: builder.ReportBuilder = None
        self.browser = None
        self.utils = TestCaseUtils(self)
        self.r_dataset = None
        self.expected_data = None
        self.db_query = "select top 5 id, name from app_client"

    def init_tc(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"]
            )
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_reports()
            self.manage_reports = ManageReport(self.admin_console)
            self.manage_reports.delete_report(self.name)
            self.manage_reports.add_report()
            self.builder = builder.ReportBuilder(self.webconsole)
            self.builder.set_report_name(self.name)
            self.expected_data = self.utils.cre_api.execute_sql(self.db_query, as_json=True)

        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def create_db_dataset(self):
        """Create DataSet with CommServ datasource"""
        dataset = builder.Datasets.DatabaseDataset()
        self.builder.add_dataset(dataset)
        dataset.set_dataset_name("DBDataSet")
        dataset.set_local_commcell_datasource()
        dataset.set_sql_query(self.db_query)
        dataset.save()
        self.builder.save_and_deploy()

    @test_step
    def create_r_dataset(self):
        """Create R Dataset"""
        r_db_query = """
        da<-data.frame(id=DBDataSet$id,name=DBDataSet$name)
        da"""
        plot_query = """
        p<-ggplot(data=da, aes(x=id,y=id*2)) +geom_line()
        plot(p)"""
        self.r_dataset = builder.Datasets.RDataset()
        self.builder.add_dataset(self.r_dataset)
        self.r_dataset.set_dataset_name("Test R Dataset")
        self.r_dataset.select_dataset("DBDataSet")
        self.r_dataset.set_dataset_query(r_db_query)
        self.r_dataset.set_plot_query(plot_query)
        received_data = self.r_dataset.get_preview_data()
        # validate data
        SQLQueries.validate_equality(
            received=received_data,
            expected=self.expected_data,
            value_processor=ValueProcessors.lower_and_unique,
            err_msg="Unexpected Table data when viewed dataset preview"
        )
        self.r_dataset.save()

    @test_step
    def add_dataset_to_table(self):
        """Associate the dataset to table and verify data"""
        table = builder.DataTable("R Dataset Table")
        self.builder.add_component(table, self.r_dataset)
        table.add_column_from_dataset()
        received_data = table.get_table_data()
        SQLQueries.validate_equality(
            received=received_data,
            expected=self.expected_data,
            value_processor=ValueProcessors.lower_and_unique,
            err_msg="Unexpected Table data in report viwer page"
        )

    @test_step
    def add_rplot_chart(self):
        """Add R plot chart"""
        chart = builder.RComponent('R Plot')
        self.builder.add_component(chart, self.r_dataset)
        chart.drop_data_column('id')
        self.builder.save_and_deploy()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)

    @test_step
    def verify_r_plot(self):
        """Verify R plot on viewer"""
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        chart = viewer.RComponent("R Plot")
        report_viewer.associate_component(chart)
        if not chart.get_img_src():
            raise CVTestStepFailure("R Chart doesn't seem to be not generated")

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.create_db_dataset()
            self.create_r_dataset()
            self.add_dataset_to_table()
            self.add_rplot_chart()
            self.verify_r_plot()
            self.delete_report()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
