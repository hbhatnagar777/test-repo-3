# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Custom Report: Verify Pages. """


from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.Reports.Custom.builder import ReportBuilder, Datasets, DataTable, Page
from Web.WebConsole.Reports.Custom.viewer import CustomReportViewer
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.webconsole import WebConsole

from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.utils import CustomReportUtils
from Reports.Custom.sql_utils import SQLQueries


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report: Verify Pages"
        self.browser = None
        self.webconsole = None
        self.utils = None
        self.report_builder = None
        self.component_title = {
            "table_title1": ["AutomationTable 1"],
            "table_title2": ["AutomationTable 2"]
        }

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.utils = CustomReportUtils(self, username=self.inputJSONnode["commcell"]["commcellUsername"],
                                           password=self.inputJSONnode["commcell"]["commcellPassword"])
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.utils.webconsole = self.webconsole
            self.webconsole.login(self.inputJSONnode['commcell']['commcellUsername'],
                                  self.inputJSONnode['commcell']['commcellPassword'])
            self.webconsole.goto_reports()
            self.utils.cre_api.delete_custom_report_by_name(self.name, suppress=True)

            # Navigate to Custom Report Builder Page.
            navigator = Navigator(self.webconsole)
            navigator.goto_report_builder()

            # Set Report Name.
            self.report_builder = ReportBuilder(self.webconsole)
            self.report_builder.set_report_name(self.name)

            # Add Dataset.
            database_dataset = Datasets.DatabaseDataset()
            self.report_builder.add_dataset(database_dataset)
            database_dataset.set_dataset_name("AutomationDataSet 1")
            database_dataset.set_sql_query(SQLQueries.sql_server_q1())
            database_dataset.save()

            # Create Table and populate with the Dataset.
            table = DataTable(self.component_title["table_title1"][0])
            self.report_builder.add_component(table, database_dataset)
            table.add_column_from_dataset()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def add_new_page(self):
        """Creates a custom report having a single page with some data."""
        page1 = Page("Page1")
        self.report_builder.add_new_page(page1)

        if self.report_builder.get_all_component_titles():
            raise CVTestStepFailure("Components in Page0 is shown in Page1")

        # Add Dataset.
        database_dataset = Datasets.DatabaseDataset()
        self.report_builder.add_dataset(database_dataset)
        database_dataset.set_dataset_name("AutomationDataSet 2")
        database_dataset.set_sql_query(SQLQueries.sql_server_q1())
        database_dataset.save()

        # Create Table and populate with the Dataset.
        table = DataTable((self.component_title["table_title2"][0]))
        self.report_builder.add_component(table, database_dataset, page1.page_name)
        table.add_column_from_dataset()

        if len(self.report_builder.get_all_component_titles()) != 1:
            raise CVTestStepFailure("Components in Page1 contains more than one component")

    @test_step
    def verify_if_pages_are_shown_as_tabs(self):
        """Saves and Deploys a two page report without enabling 'Show as Tabs'"""
        # Save and Deploy the report.
        self.report_builder.save(deploy=True)

        # Opens the report
        self.report_builder.open_report()
        custom_report_viewer = CustomReportViewer(self.webconsole)
        if custom_report_viewer.get_all_page_title_names():
            raise CVTestStepFailure("Pages are shown as tabs")

        driver = self.webconsole.browser.driver
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

    @test_step
    def enable_show_pages_as_tabs(self):
        """Enable the 'Show as Tabs' option on pages"""
        self.report_builder.enable_show_pages_as_tabs()
        self.report_builder.save()
        self.report_builder.deploy()
        self.report_builder.open_report()

        custom_report_viewer = CustomReportViewer(self.webconsole)
        if not custom_report_viewer.get_all_page_title_names():
            raise CVTestStepFailure("Pages are not shown as tabs")

    @test_step
    def url_switching_of_tabs(self):
        """Add page name to URL"""
        current_title = {}

        custom_report_viewer = CustomReportViewer(self.webconsole)
        current_title["table_title1"] = custom_report_viewer.get_all_component_titles()

        new_url = self.browser.driver.current_url
        new_url += "&pageName=Page1"
        self.browser.driver.get(new_url)
        self.webconsole.wait_till_load_complete()

        current_title["table_title2"] = custom_report_viewer.get_all_component_titles()

        if current_title != self.component_title:
            raise CVTestStepFailure("Component and their page mismatch."
                                    "Builder: {0} "
                                    "Viewer {1}".format(self.component_title, current_title))

    def run(self):
        try:
            self.init_tc()
            self.add_new_page()
            self.verify_if_pages_are_shown_as_tabs()
            self.enable_show_pages_as_tabs()
            self.url_switching_of_tabs()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
