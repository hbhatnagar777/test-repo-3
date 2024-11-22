# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
import re

from Reports.utils import TestCaseUtils

from Web.Common.cvbrowser import BrowserFactory, Browser

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Custom import builder

from Web.AdminConsole.Reports.Custom import viewer
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure


class TestCase(CVTestCase):
    """Class for executing this test case"""
    QUERY = """
                SELECT * from App_reports
        """
    COLUMN_FOR_CHART = "version"

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "ValidateChartProperty : ShowTopRightTooltip"
        self.browser = None
        self.webconsole = None
        self.admin_console = None
        self.navigator = None
        self.manage_reports = None
        self.utils = TestCaseUtils(self)
        self.builder = None
        self.dataset = None

    def add_dataset(self):
        """Adds dataset"""
        self.builder = builder.ReportBuilder(self.webconsole)
        self.builder.set_report_name(self.name)
        self.dataset = builder.Datasets.DatabaseDataset()
        self.builder.add_dataset(self.dataset)
        self.dataset.set_dataset_name("Automation Dataset")
        self.dataset.set_sql_query(TestCase.QUERY)
        self.dataset.save()

    def create_horizontal_bar(self):
        """ Creates Horizontal Bar chart """
        horizontal_bar = builder.HorizontalBar("Automation Chart")
        self.builder.add_component(horizontal_bar, self.dataset)
        horizontal_bar.set_x_axis(TestCase.COLUMN_FOR_CHART)
        horizontal_bar.set_aggregation("Count")
        horizontal_bar.enable_show_top_right_tooltip()
        self.builder.save(deploy=True)

    def validate_show_top_right_tooltip(self):
        """ tooltip text verify """
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)
        report_viewer = viewer.CustomReportViewer(self.admin_console)
        horizontal_bar = viewer.HorizontalBar("Automation Chart")
        report_viewer.associate_component(horizontal_bar)
        text = horizontal_bar.get_tooltip_text()
        matches = re.findall(r'[A-Za-z ]+', text)
        matches = [match.strip() for match in matches if match.strip()]
        count = len(matches)
        if count != 2:
            raise CVTestStepFailure("tooltip does not have the required text")

    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

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

    def run(self):
        """Run function of this test case"""
        try:
            self.init_tc()
            self.add_dataset()
            self.create_horizontal_bar()
            self.validate_show_top_right_tooltip()
            self.delete_report()

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
