# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Default report templates"""

from Reports.Custom.sql_utils import SQLQueries
from Web.Common.exceptions import CVNotFound
from Web.WebConsole.Reports.Custom import builder
from Web.WebConsole.Reports.Custom.viewer import CustomReportViewer


class DefaultReport:
    """Default reports"""

    def __init__(self, cre_utils, admin_console=None, browser=None):
        self.cre_utils = cre_utils
        self.report_builder = None
        self.table = None
        self.dataset = None
        self.admin_console = admin_console
        self.browser = browser

    def __add_dataset(self, sql):
        dataset = builder.Datasets.DatabaseDataset()
        self.report_builder.add_dataset(dataset)
        dataset_name = "Automation Dataset " + self.cre_utils.testcase.id
        dataset.set_dataset_name(dataset_name)
        dataset.set_sql_query(sql)
        dataset.save()
        return dataset

    def __add_table(self, dataset):
        table_name = "Automation Table"
        self.table = builder.DataTable(table_name)
        self.report_builder.add_component(self.table, dataset)
        self.table.add_column_from_dataset()

    def __add_chart(self, dataset, chart_cols):
        chart = builder.VerticalBar("Automation Chart")
        self.report_builder.add_component(chart, dataset)
        chart.set_x_axis(chart_cols["X"])
        chart.set_y_axis(chart_cols["Y"])

    def __create_report(self, rpt_name, sql, chart_cols):
        self.report_builder.set_report_name(rpt_name)
        self.dataset = self.__add_dataset(sql)
        self.__add_table(self.dataset)
        if chart_cols:
            self.__add_chart(self.dataset, chart_cols)
        self.report_builder.save(deploy=True)

    def build_default_report(self, overwrite=True, sql=SQLQueries.sql_server_q1(),
                             open_report=False, chart_cols=None, keep_same_tab=False):
        """Create default report"""
        rpt_name = self.cre_utils.testcase.name
        if overwrite:
            self.cre_utils.cre_api.delete_custom_report_by_name(
                rpt_name, suppress=True
            )
        self.report_builder = builder.ReportBuilder(self.cre_utils.webconsole)
        self.__create_report(rpt_name, sql, chart_cols)
        if open_report:
            self.report_builder.open_report()
        if not keep_same_tab:
            self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
            self.browser.driver.refresh()