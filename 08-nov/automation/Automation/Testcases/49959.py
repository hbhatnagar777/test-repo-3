# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Custom Reports: Exports with post query filter"""

from Reports.Custom.sql_utils import SQLQueries, ValueProcessors
from Reports.Custom.utils import CustomReportUtils
from Reports.Custom.report_templates import DefaultReport
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.adminconsole import AdminConsole

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom.builder import ReportBuilder

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Custom import builder
from Web.AdminConsole.Reports.Custom import viewer

from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.csv_column_data = None
        self.report = None
        self.table = None
        self.manage_report = None
        self.navigator = None
        self.admin_console = None
        self.name = "Custom Reports: Exports with post query filter"
        self.browser = None
        self.webconsole = None
        self.utils = CustomReportUtils(self)
        self.report_builder = None
        self.data = None
        self.commcell_password = None

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.utils.get_temp_dir())
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                         username=self.commcell.commcell_username,
                                         password=self.commcell_password)
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.utils.webconsole = self.webconsole
            self.admin_console.login(username=self.commcell.commcell_username,
                                  password=self.commcell_password)
            self.navigator = self.admin_console.navigator
            self.report = Report(self.admin_console)
            self.manage_report = ManageReport(self.admin_console)
            self.navigator.navigate_to_reports()
            self.manage_report.delete_report(self.name)
            self.browser.driver.refresh()
            self.admin_console.wait_for_completion()
            self.manage_report.add_report()
            self.data = {'id': ['6', '8', '10'],
                         'text_t': ['Text00000048',
                                    'Text00000064', 'Text00000080'],
                         'datetime_t': ['Oct 2, 1992, 09:50:00 AM', 'Oct 2, 1992, 10:56:40 AM',
                                        'Oct 2, 1992, 12:03:20 PM'],
                         'timestamp_t': ['718019400', '718023400',
                                         '718027400']}
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def set_post_query_filter(self):
        """Creates join dataset from two database datasets"""
        # Build default report
        self.report_builder = ReportBuilder(self.webconsole)
        default_report = DefaultReport(self.utils, self.admin_console, self.browser)
        default_report.build_default_report(overwrite=False, open_report=False, sql=SQLQueries.sql_server_q1(10))
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[1])
        # Set Post query filter
        dataset_name = default_report.dataset.dataset_name
        dataset = builder.Datasets.DatabaseDataset()
        dataset.dataset_name = dataset_name
        self.report_builder.edit_dataset(dataset)
        dataset.set_post_query_filter("select * from $this$ where id % 2 = 0 and timestamp_t >= 718019400")
        dataset.save()
        self.report_builder.save()
        self.report_builder.deploy()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.admin_console.wait_for_completion()
        self.manage_report.access_report(self.name)

    @test_step
    def export_to_csv(self):
        """Exports to CSV"""
        # Initialize export handler and verify table data
        self.utils.reset_temp_dir()
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        self.table = viewer.DataTable("Automation Table")
        report_viewer.associate_component(self.table)
        table_column_data = self.table.get_column_data("id")
        SQLQueries.validate_equality(self.data, self.table.get_table_data(),
                                     ValueProcessors.lower_string)
        # Export to CSV
        self.report.save_as_csv()
        self.utils.wait_for_file_to_download('csv')
        self.utils.validate_tmp_files("csv")
        self.log.info("csv export completed successfully")
        exported_file = self.utils.get_temp_files("csv")[0]
        self.csv_column_data = self.get_csv_column_content(exported_file)
        if set(self.csv_column_data) != set(table_column_data):
            self.log.error("CSV column has values :%s", str(self.csv_column_data))
            self.log.error("Web report column has values :%s", set(table_column_data))
            raise CVTestStepFailure("CSV column values are not matching with report column values")
        self.log.info("CSV contents are verified successfully")

    def get_csv_column_content(self, exported_file_name):
        """Get CSV Column Data"""
        csv_content = self.utils.get_csv_content(exported_file_name)
        column_content = list(map(list, zip(*(csv_content[4:20]))))
        for columns in csv_content[3]:
            if columns == 'id':
                index = csv_content[3].index('id')
                return column_content[index]

    @test_step
    def export_to_html(self):
        """Exports to HTML"""
        # Export to HTML
        self.report.save_as_html()
        self.utils.wait_for_file_to_download('html')
        self.utils.validate_tmp_files("html")
        self.log.info("html export completed successfully")

        # Validate table in  HTML content
        path = self.utils.get_temp_files("html")
        self.browser.driver.execute_script("window.open()")
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])
        self.browser.driver.get(path[0])
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        table_1 = viewer.DataTable("Automation Table")
        report_viewer.associate_component(table_1)
        SQLQueries.validate_equality(self.data, table_1.get_exported_table_data(),
                                     ValueProcessors.lower_string)

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.set_post_query_filter()
            self.export_to_csv()
            self.export_to_html()

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
