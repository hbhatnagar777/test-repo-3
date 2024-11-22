# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Custom Reports : Validate Reports Charts"""
from Reports.Custom.sql_utils import SQLQueries
from Reports.utils import TestCaseUtils

from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.Custom import viewer

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Custom import builder

from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()
    QUERY = """
            DECLARE @i INT = 0
            DECLARE @tmpTable table(emp_id VARCHAR(MAX),department_name VARCHAR(MAX),
                                    department_code INT,joining_date DATE)
            WHILE @i < 10
            BEGIN
                  SET NOCOUNT ON
                  if @i % 3 = 0
                     INSERT INTO @tmpTable (emp_id,department_name,
                                              department_code,joining_date)
                     VALUES('EMP0'+CAST(@i AS varchar),'SALES',111,DATEADD(day,30,GETDATE()))
                  else
                     INSERT INTO @tmpTable(emp_id,department_name,
                                             department_code,joining_date)
                     VALUES('EMP0'+CAST(@i AS varchar),'RESEARCH',222,DATEADD(day,45,GETDATE()))
                  SET @i = @i + 1
            END

            SELECT * from @tmpTable

    """
    COLUMNS_FOR_CHART = ['department_code', 'joining_date']
    HORIZONTAL_BAR = {
        'x-axis_title': 'department_code',
        'y-axis_title': 'department_code',
        'count': 2,
        'height': ['6', '4'],
        'x-axis_labels': ['222', '111']
    }

    VERTICAL_BAR = {
        'x-axis_title': 'department_code',
        'y-axis_title': 'department_code Sum',
        'count': 2,
        'height': ['1,332', '444'],
        'x-axis_labels': ['222', '111']
    }

    PIE_CHART = {
        'slice_count': 2,
        'slice_values': ['222', '111']
    }

    DONUT_CHART = {
        'slice_count': 2,
        'slice_values': ['222', '111']
    }

    LINE_CHART = {
        'x-axis_title': 'department_code',
        'y-axis_title': 'department_code Max',
        'count': 2,
        'height': ['222', '111'],
        'x-axis_labels': ['222', '111'],
        'y-axis_labels': ['100', '125', '150', '175', '200', '225', '250']
    }

    TIMELINE_CHART = {
        'x-axis_title': 'joining_date',
        'y-axis_title': 'department_code Count',
        'count': 2,
        'height': ['4', '6'],
        'y-axis_labels': ['3', '4', '5', '6', '7']
    }

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Reports : Validate Reports Charts"
        self.browser = None
        self.webconsole = None
        self.admin_console = None
        self.manage_reports = None
        self.navigator = None
        self.builder = None
        self.dataset = None
        self.utils = TestCaseUtils(self)

    def init_tc(self):
        """ Initial configuration for the test case. """
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

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def add_dataset(self):
        """Adds dataset"""
        self.builder = builder.ReportBuilder(self.webconsole)
        self.builder.set_report_name(self.name)
        self.dataset = builder.Datasets.DatabaseDataset()
        self.builder.add_dataset(self.dataset)
        self.dataset.set_dataset_name("Automation Dataset")
        self.dataset.set_sql_query(TestCase.QUERY)
        self.dataset.save()

    @test_step
    def create_horizontal_bar(self):
        """Creates Horizontal Bar chart"""
        horizontal_bar = builder.HorizontalBar("Automation Chart 1")
        self.builder.add_component(horizontal_bar, self.dataset)
        horizontal_bar.set_x_axis(TestCase.COLUMNS_FOR_CHART[0])
        horizontal_bar.set_aggregation("Count")
        details = horizontal_bar.get_chart_details()
        del details["y-axis_labels"]
        SQLQueries.validate_membership_equality(TestCase.HORIZONTAL_BAR, details,
                                                err_msg="Expected and received values are not equal in Horizontal Bar")

    @test_step
    def create_vertical_bar(self):
        """Creates Vertical Bar chart"""
        vertical_bar = builder.VerticalBar("Automation Chart 2")
        self.builder.add_component(vertical_bar, self.dataset)
        vertical_bar.set_x_axis(TestCase.COLUMNS_FOR_CHART[0])
        vertical_bar.set_aggregation("Sum")
        details = vertical_bar.get_chart_details()
        del details["y-axis_labels"]
        SQLQueries.validate_equality(TestCase.VERTICAL_BAR, details,
                                     err_msg="Expected and received values are not equal in Vertical Bar")

    @test_step
    def create_pie_chart(self):
        """Creates Pie chart"""
        pie = builder.PieChart("Automation Chart 3")
        self.builder.add_component(pie, self.dataset)
        pie.add_column_to_dimension(TestCase.COLUMNS_FOR_CHART[0])
        pie.set_aggregation("Min")
        details = pie.get_chart_details()
        SQLQueries.validate_equality(TestCase.PIE_CHART, details,
                                     err_msg="Expected and received values are not equal in Pie Chart")

    @test_step
    def create_donut_chart(self):
        """Creates Donut chart"""
        donut = builder.DonutChart("Automation Chart 4")
        self.builder.add_component(donut, self.dataset)
        donut.add_column_to_dimension(TestCase.COLUMNS_FOR_CHART[0])
        donut.set_aggregation("Avg")
        details = donut.get_chart_details()
        SQLQueries.validate_equality(TestCase.DONUT_CHART, details,
                                     err_msg="Expected and received values are not equal in Donut Chart")

    @test_step
    def create_line_chart(self):
        """Creates Line Chart"""
        line = builder.LineChart("Automation Chart 5")
        self.builder.add_component(line, self.dataset)
        line.set_x_axis(TestCase.COLUMNS_FOR_CHART[0])
        line.set_aggregation("Max")
        details = line.get_chart_details()
        SQLQueries.validate_equality(TestCase.LINE_CHART, details,
                                     err_msg="Expected and received values are not equal in Line Chart")

    @test_step
    def create_timeline_chart(self):
        """Creates Timeline chart """
        timeline = builder.TimelineChart("Automation Chart 6")
        self.builder.add_component(timeline, self.dataset)
        timeline.set_x_axis(TestCase.COLUMNS_FOR_CHART[1])
        timeline.set_time_grouping("Weekly")
        timeline.set_y_axis(TestCase.COLUMNS_FOR_CHART[0])
        timeline.set_aggregation("Count")
        details = timeline.get_chart_details()
        del details['x-axis_labels']
        SQLQueries.validate_equality(TestCase.TIMELINE_CHART, details,
                                     err_msg="Expected and received values are not equal in Timeline Chart")

    @test_step
    def validate_viewer(self):
        """Validates chart in viewer"""
        self.builder.save(deploy=True)
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        horizontal_bar = viewer.HorizontalBar("Automation Chart 1")
        vertical_bar = viewer.VerticalBar("Automation Chart 2")
        pie_chart = viewer.PieChart("Automation Chart 3")
        donut = viewer.DonutChart("Automation Chart 4")
        line_chart = viewer.LineChart("Automation Chart 5")
        timeline_chart = viewer.TimelineChart("Automation Chart 6")

        report_viewer.associate_component(horizontal_bar)
        report_viewer.associate_component(vertical_bar)
        report_viewer.associate_component(pie_chart)
        report_viewer.associate_component(donut)
        report_viewer.associate_component(line_chart)
        report_viewer.associate_component(timeline_chart)

        details = horizontal_bar.get_chart_details()
        del details['y-axis_labels']
        SQLQueries.validate_membership_equality(TestCase.HORIZONTAL_BAR, details,
                                                err_msg="Expected and received values are not equal in Horizontal Bar")

        details = vertical_bar.get_chart_details()
        del details["y-axis_labels"]
        SQLQueries.validate_equality(TestCase.VERTICAL_BAR, details,
                                     err_msg="Expected and received values are not equal in Vertical Bar")

        details = pie_chart.get_chart_details()
        SQLQueries.validate_equality(TestCase.PIE_CHART, details,
                                     err_msg="Expected and received values are not equal in Pie Chart")

        details = donut.get_chart_details()
        SQLQueries.validate_equality(TestCase.DONUT_CHART, details,
                                     err_msg="Expected and received values are not equal in Donut Chart")

        details = line_chart.get_chart_details()
        SQLQueries.validate_equality(TestCase.LINE_CHART, details,
                                     err_msg="Expected and received values are not equal in Line Chart")

        details = timeline_chart.get_chart_details()
        del details['x-axis_labels']
        del details['y-axis_labels']
        del TestCase.TIMELINE_CHART['y-axis_labels']
        SQLQueries.validate_equality(TestCase.TIMELINE_CHART, details,
                                     err_msg="Expected and received values are not equal in Timeline Chart")

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.add_dataset()
            self.create_horizontal_bar()
            self.create_vertical_bar()
            self.create_pie_chart()
            self.create_donut_chart()
            self.create_line_chart()
            self.create_timeline_chart()
            self.validate_viewer()
            self.delete_report()

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
