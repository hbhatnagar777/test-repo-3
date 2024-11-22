# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Custom Report: Full Text Search"""
from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.report_templates import DefaultReport
from Reports.Custom.sql_utils import SQLQueries
from Reports.Custom.utils import CustomReportUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole

from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure)
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom import builder
from Web.AdminConsole.Reports.Custom import viewer

from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()
    KEYWORD = "Big Flat Earth"
    KEYWORD_2 = "Text00000032"

    def __init__(self):
        super(TestCase, self).__init__()
        self.manage_reports = None
        self.navigator = None
        self.admin_console = None
        self.name = "Custom Report: Full Text Search"
        self.utils = None
        self.webconsole = None
        self.browser = None
        self.report = None
        self.search_bar = None
        self.report_viewer = None
        self.table_viewer = None
        self.search_bar_viewer = None

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.utils = CustomReportUtils(self, username=self.inputJSONnode['commcell']['commcellUsername'],
                                           password=self.inputJSONnode['commcell']['commcellPassword'])
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.utils.webconsole = self.webconsole
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
            self.report = DefaultReport(self.utils, browser=self.browser)
            self.report.build_default_report(open_report=False, sql=SQLQueries.sql_server_q2(3),
                                             keep_same_tab=True)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def filter_using_search_bar(self):
        """filter using a String type search text in the search bar component."""
        self.search_bar = builder.SearchBar("Automation SearchBar")
        self.report.report_builder.add_component(self.search_bar, self.report.dataset)
        self.search_bar.add_column_from_dataset()

        self.search_bar.search(TestCase.KEYWORD)
        data = self.report.table.get_table_data()
        if data['text'] != [TestCase.KEYWORD]:
            raise CVTestStepFailure(f"In Builder, Expected: {[TestCase.KEYWORD]}. \n Received: {data['text']}")

        self._save_deploy_open_report()

        self.search_bar_viewer.search(TestCase.KEYWORD)
        data = self.table_viewer.get_table_data()
        if data['text'] != [TestCase.KEYWORD]:
            raise CVTestStepFailure(f"In Viewer, Expected: {[TestCase.KEYWORD]}. \n Received: {data['text']}")

    @test_step
    def filter_with_other_data_types(self):
        """filter with other data types."""
        keyword = "1"
        self.search_bar_viewer.search(keyword)
        data = self.table_viewer.get_table_data()
        for key, value in data.items():
            if value:
                if 'No data available' in value:
                    continue
                raise CVTestStepFailure(f"In Viewer, Expected: []. \n Received: {data}")
        self._switch_to_builder()
        self.search_bar.search(keyword)
        data = self.report.table.get_table_data()
        for key, value in data.items():
            if value:
                raise CVTestStepFailure(f"In Builder, Expected: []. \n Received: {data}")
        self.search_bar.search("")

    @test_step
    def filter_with_multiple_components(self):
        """filter when there are components from more than one data set"""
        table_2 = builder.DataTable("Automation Table 2")
        self.report.report_builder.add_component(table_2, self.report.dataset)
        table_2.add_column_from_dataset()

        dataset = builder.Datasets.DatabaseDataset()
        self.report.report_builder.add_dataset(dataset)
        dataset.set_dataset_name("Automation Dataset 2")
        dataset.set_sql_query(SQLQueries.sql_server_q1(5))
        dataset.save()

        table_3 = builder.DataTable("Automation Table 3")
        self.report.report_builder.add_component(table_3, dataset)
        table_3.add_column_from_dataset()

        search_bar_2 = builder.SearchBar("Automation SearchBar 2")
        self.report.report_builder.add_component(search_bar_2, dataset)
        search_bar_2.add_column_from_dataset("text_t")

        search_bar_2.search(TestCase.KEYWORD_2)
        data_3 = table_3.get_table_data()
        if data_3["text_t"] != [TestCase.KEYWORD_2]:
            raise CVTestStepFailure(f"In Builder, Expected: {[TestCase.KEYWORD_2]}. \n Received: {data_3['text_t']}")

        self.search_bar.search(TestCase.KEYWORD)
        data_1 = self.report.table.get_table_data()
        data_2 = table_2.get_table_data()
        data_3 = table_3.get_table_data()
        self.log.info("********In Builder********")
        if data_1["text"] != [TestCase.KEYWORD] or data_2["text"] != [TestCase.KEYWORD]:
            raise CVTestStepFailure(f"Expected a single row with value '{[TestCase.KEYWORD]}' under column 'text'.\n"
                                    f"Received {data_1['text']} and {data_2['text']} on table 1 and 2 respectively")
        if data_3.get("text_t", []) == [TestCase.KEYWORD]:
            raise CVTestStepFailure(f"Table 3 shows positive for the {[TestCase.KEYWORD]}")

        self._save_deploy_open_report()

        table_viewer_2 = viewer.DataTable("Automation Table 2")
        table_viewer_3 = viewer.DataTable("Automation Table 3")
        search_bar_viewer = viewer.SearchBarViewer("Automation SearchBar 2")
        self.report_viewer.associate_component(table_viewer_2)
        self.report_viewer.associate_component(table_viewer_3)
        self.report_viewer.associate_component(search_bar_viewer)

        search_bar_viewer.search(TestCase.KEYWORD_2)
        data_3 = table_3.get_table_data()
        if data_3["text_t"] != [TestCase.KEYWORD_2]:
            raise CVTestStepFailure(f"In Viewer, Expected: {[TestCase.KEYWORD_2]}. \n Received: {data_3['text_t']}")

        self.search_bar_viewer.search(TestCase.KEYWORD)
        data_1 = self.table_viewer.get_table_data()
        data_2 = table_viewer_2.get_table_data()
        data_3 = table_viewer_3.get_table_data()
        self.log.info("********In Viewer********")
        if data_1["text"] != [TestCase.KEYWORD] or data_2["text"] != [TestCase.KEYWORD]:
            raise CVTestStepFailure(f"Expected a single row with value '{[TestCase.KEYWORD]}' under column 'text'.\n"
                                    f"Received {data_1['text']} and {data_2['text']} on table 1 and 2 respectively")
        if data_3.get("text_t", []) == [TestCase.KEYWORD]:
            raise CVTestStepFailure(f"Table 3 shows positive for the {[TestCase.KEYWORD]}")

    def _save_deploy_open_report(self):
        """Saves deploys and opens report"""
        self.report.report_builder.save()
        self.report.report_builder.deploy()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.navigator.navigate_to_reports()
        self.manage_reports.access_report(self.name)
        self.search_bar_viewer = viewer.SearchBarViewer("Automation SearchBar")
        self.table_viewer = viewer.DataTable("Automation Table")
        self.report_viewer = viewer.CustomReportViewer(self.admin_console)
        self.report_viewer.associate_component(self.search_bar_viewer)
        self.report_viewer.associate_component(self.table_viewer)

    def _switch_to_builder(self):
        """Closes current tab and switches to builder"""
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[-1])

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.filter_using_search_bar()
            self.filter_with_other_data_types()
            self.filter_with_multiple_components()
            self.delete_report()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
