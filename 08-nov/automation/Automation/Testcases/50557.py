# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Custom Reports : Custom Grouping in Charts"""
from Reports.Custom.sql_utils import SQLQueries
from Reports.utils import TestCaseUtils

from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Custom import builder

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.Custom import viewer

from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()
    QUERY = """
            DECLARE @tmpTbl TABLE(id int, intMod5 int)
            DECLARE @i int = 0
            WHILE @i < 100
            BEGIN
                SET @i = @i + 1
                INSERT INTO @tmpTbl VALUES(@i, @i % 5)
            END
            SELECT * FROM @tmpTbl
            """
    VERTICAL_BAR_FIELD = "id"
    PIE_CHART_FIELD = "intMod5"
    VERTICAL_BAR_GROUPS = [['Less Than 30', '<30'], ['Greater Than 75', '>75']]
    PIE_CHART_GROUPS = [['Less Than 2', '<2'], ['Equals 3', '3'], ['Greater Than 3', '>3']]
    VERTICAL_BAR = {
        'x-axis_title': 'id',
        'y-axis_title': 'id Count',
        'count': 2,
        'height': ['29', '25'],
        'x-axis_labels': ['Less Than 30', 'Greater Than 75'],
        'y-axis_labels': ['0', '10', '20', '30', '40']
    }
    PIE_CHART = {
        'slice_count': 3,
        'slice_values': ['40', '20', '20']
    }

    def __init__(self):
        super(TestCase, self).__init__()
        self.manage_reports = None
        self.navigator = None
        self.admin_console = None
        self.name = "Custom Reports : Custom Grouping in Charts"
        self.browser = None
        self.webconsole = None
        self.utils = None
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
        """Adds Dataset"""
        self.builder = builder.ReportBuilder(self.webconsole)
        self.builder.set_report_name(self.name)
        self.dataset = builder.Datasets.DatabaseDataset()
        self.builder.add_dataset(self.dataset)
        self.dataset.set_dataset_name("Automation Dataset")
        self.dataset.set_sql_query(TestCase.QUERY)
        self.dataset.save()

    @test_step
    def create_vertical_bar(self):
        """Creates Vertical Bar chart"""
        vertical_bar = builder.VerticalBar("Automation Chart 1")
        self.builder.add_component(vertical_bar, self.dataset)
        vertical_bar.set_x_axis(TestCase.VERTICAL_BAR_FIELD)
        vertical_bar.add_custom_group(TestCase.VERTICAL_BAR_FIELD, TestCase.VERTICAL_BAR_GROUPS)
        details = vertical_bar.get_chart_details()
        SQLQueries.validate_equality(TestCase.VERTICAL_BAR, details,
                                     err_msg="Expected and received values are not equal in Vertical Bar")

    @test_step
    def create_pie_chart(self):
        """Creates Pie chart"""
        pie = builder.PieChart("Automation Chart 2")
        self.builder.add_component(pie, self.dataset)
        pie.add_column_to_dimension(TestCase.PIE_CHART_FIELD)
        pie.add_custom_group(TestCase.PIE_CHART_FIELD, TestCase.PIE_CHART_GROUPS)
        details = pie.get_chart_details()
        SQLQueries.validate_equality(TestCase.PIE_CHART, details,
                                     err_msg="Expected and received values are not equal in Pie Chart")

    def validate_viewer(self):
        """Validates chart in viewer"""
        self.builder.save(deploy=True)
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        vertical_bar = viewer.VerticalBar("Automation Chart 1")
        pie_chart = viewer.PieChart("Automation Chart 2")

        report_viewer.associate_component(vertical_bar)
        report_viewer.associate_component(pie_chart)

        details = vertical_bar.get_chart_details()
        SQLQueries.validate_equality(TestCase.VERTICAL_BAR, details,
                                     err_msg="Expected and received values are not equal in Vertical Bar")

        details = pie_chart.get_chart_details()
        SQLQueries.validate_equality(TestCase.PIE_CHART, details,
                                     err_msg="Expected and received values are not equal in Pie Chart")

    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.add_dataset()
            self.create_vertical_bar()
            self.create_pie_chart()
            self.validate_viewer()
            self.delete_report()

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
