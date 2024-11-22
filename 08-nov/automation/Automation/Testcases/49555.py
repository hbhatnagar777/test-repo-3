# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Custom reports: Validate localization"""
from AutomationUtils.cvtestcase import CVTestCase
from Reports.Custom.sql_utils import SQLQueries

from Reports.Custom.utils import CustomReportUtils

from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import (
    CVTestStepFailure,
    CVTestCaseInitFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom.builder import (
    ReportBuilder,
    Locale
)

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Custom import viewer, builder


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()
    RPT_TITLE_1 = ["fr_CA", "RPT_TITLE", "Custom Report Localization - canadian french"]
    TABLE_TITLE_1 = ["default", "TABLE_TITLE", "English Title"]
    TABLE_TITLE_2 = ["fr_CA", "TABLE_TITLE", "Canadian French Title"]
    RPT_DESCRIPTION_1 = ["fr_CA", "RPT_DESCRIPTION", "Canadian French Description"]
    INPUT_LIST = [RPT_TITLE_1, TABLE_TITLE_1, TABLE_TITLE_2, RPT_DESCRIPTION_1]
    TABLE_DATA = {'No Column Name1': ['fr_CA']}

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom reports: Validate localization"
        self.show_to_user = True
        self.browser = None
        self.webconsole = None
        self.utils = None
        self.report_builder = None
        self.localization = None

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
            navigator = Navigator(self.webconsole)
            navigator.goto_report_builder()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def add_localization(self):
        """Adds new locale key value triplet."""
        self.report_builder = ReportBuilder(self.webconsole)
        self.report_builder.set_report_name(self.name)
        self.report_builder.set_report_description("Test english description")
        self.localization = Locale()
        self.report_builder.add_localization(self.localization)
        for input_ in TestCase.INPUT_LIST:
            self.localization.add_localization(*input_)
        self.localization.save_localization()
        table = builder.DataTable("=rpt.translate('TABLE_TITLE')")
        dataset = builder.Datasets.DatabaseDataset()
        self.report_builder.add_dataset(dataset)
        dataset.set_dataset_name("Automation Dataset")
        dataset.set_sql_query("SELECT @sys_locale")
        dataset.save()
        self.report_builder.add_component(table, dataset)
        table.add_column_from_dataset()
        self.report_builder.save(deploy=True)

    @test_step
    def change_language(self):
        """Changes language"""
        self.report_builder.open_report()
        report_viewer = viewer.CustomReportViewer(self.webconsole)
        table = viewer.DataTable(TestCase.TABLE_TITLE_1[2])
        report_viewer.associate_component(table)

        self.webconsole.set_language("fr_CA")
        viewer_rpt_name = report_viewer.get_report_name()
        if viewer_rpt_name != TestCase.RPT_TITLE_1[2]:
            raise CVTestStepFailure(f"Expected Report Title: {TestCase.RPT_TITLE_1}.\n"
                                    f" Actual Report Title:{viewer_rpt_name}")

        viewer_rpt_desc = report_viewer.get_report_description()
        if viewer_rpt_desc != TestCase.RPT_DESCRIPTION_1[2]:
            raise CVTestStepFailure(f"Expected Report Description: {TestCase.RPT_DESCRIPTION_1}.\n"
                                    f"Actual Report Description:{viewer_rpt_desc}")

        viewer_table_title = table.get_table_title()
        if viewer_table_title != TestCase.TABLE_TITLE_2[2]:
            raise CVTestStepFailure(f"Expected Table Title: {TestCase.TABLE_TITLE_2}.\n"
                                    f"Actual Table Title:{viewer_table_title}")

        viewer_table = table.get_table_data()
        SQLQueries.validate_equality(TestCase.TABLE_DATA, viewer_table)

    def run(self):
        try:
            self.init_tc()
            self.add_localization()
            self.change_language()

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
