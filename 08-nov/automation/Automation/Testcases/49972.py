# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Custom report: Check version count and deploy version count. """


from AutomationUtils.cvtestcase import CVTestCase

from Reports.utils import TestCaseUtils

from Web.Common.cvbrowser import Browser
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.Reports.Custom import viewer
from Web.WebConsole.Reports.Custom.builder import Datasets
from Web.WebConsole.Reports.Custom.builder import (
    ReportBuilder,
    DataTable
)
from Web.WebConsole.Reports.Custom.viewer import CustomReportViewer
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom report: Report and Deploy versions"
        self.browser = None
        self.webconsole = None
        self.utils = None
        self.data = None
        self.report_builder = None
        self.report_version = 1
        self.deployed_version = 1

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.utils = TestCaseUtils(self, username=self.inputJSONnode['commcell']['commcellUsername'],
                                       password=self.inputJSONnode['commcell']['commcellPassword'])

            # Initializes browser.
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()

            # Log in and navigate to Reports.
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(self.inputJSONnode['commcell']['commcellUsername'],
                                  self.inputJSONnode['commcell']['commcellPassword'])
            self.webconsole.goto_reports()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def create_custom_report(self):
        """ Creates a custom report having Database dataset.

        Returns:
                dict - The table of the created custom report.
        """
        # Deletes any previous report if any with the same name.
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
        database_dataset.set_dataset_name("Automation Dataset")
        database_dataset.set_sql_query("SELECT @sys_userid [UserID], @sys_username\
                                            [UserName], @sys_locale [Locale],\
                                             @sys_timezone [Timezone]")
        database_dataset.save()

        # Create Table and populate with the Dataset.
        table = DataTable("Automation Dataset")
        self.report_builder.add_component(table, database_dataset)
        table.add_column_from_dataset("UserID")
        table.add_column_from_dataset("UserName")

        # Save and Deploy the report.
        self.report_builder.save()
        self.validate_report_version()

        return table

    @test_step
    def deploy_report(self):
        """ Deploys report. """
        self.report_builder.deploy()
        self.validate_deployed_version()

    @test_step
    def make_changes(self, table):
        """ Make changes to report. """

        # Making Changes
        table_data_before_deploy = table.get_table_data()
        table.add_column_from_dataset("Locale")
        table.add_column_from_dataset("Timezone")

        # Saving the report
        self.report_builder.save()
        self.validate_report_version()

        # Opening the report
        self.report_builder.open_report()

        # Checking if changes are reflected
        self.verify_change(table_data_before_deploy)
        return table

    @test_step
    def deploy_changed_report(self, table):
        """ Deploys changed report. """
        driver = self.webconsole.browser.driver
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        self.report_builder.deploy()
        self.validate_deployed_version()
        modified_table = table.get_table_data()
        self.report_builder.open_report()
        self.verify_change(modified_table)

    def validate_report_version(self):
        """ Check report version. """
        if self.report_version == int(self.report_builder.get_report_version()):
            self.report_version += 1
        else:
            raise CVTestStepFailure("Report version is '{0}' after the creation of the report"
                                    .format(self.report_version))

    def validate_deployed_version(self):
        """ Check deployed version. """
        if self.deployed_version == int(self.report_builder.get_deployed_version()):
            self.deployed_version += 1
        else:
            raise CVTestStepFailure("Deployed version is '{0}' after the creation of the report"
                                    .format(self.deployed_version))

    def verify_change(self, expected_data):
        """ Checks whether changes made in the table title are reflected.

        Args:
            expected_data: table object of the modified table
        Returns:
            bool - True if changes are reflected, else false.

        """

        table = viewer.DataTable("Automation Dataset")
        report_viewer = CustomReportViewer(self.webconsole)
        report_viewer.associate_component(table)
        received_data = table.get_table_data()
        if expected_data != received_data:
            self.log.error(
                f"\nExpecting [{expected_data}]"
                f"\nReceived [{received_data}]"
            )
            raise CVTestStepFailure("Saving the changes, reflects before deploying it.")

    def run(self):
        try:
            self.init_tc()
            table = self.create_custom_report()
            self.deploy_report()
            table = self.make_changes(table)
            self.deploy_changed_report(table)
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
