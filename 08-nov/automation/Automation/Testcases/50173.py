# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from AutomationUtils.cvtestcase import CVTestCase

from Reports.metricsutils import MetricsServer
from Reports.utils import TestCaseUtils
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
from Web.WebConsole.Reports.Custom.builder import Datasets
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report: (DataSet) - Offline DataSet frequency"
        self.manage_reports = None
        self.navigator = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.webconsole: WebConsole = None
        self.browser: Browser = None
        self.rpt_builder = None
        self.dataset = None
        self.metrics_server = None
        self.freq_str = '--@DYNAMIC\n--@FREQUENCY 60'
        self.dataset_name = 'AutomationOfflineDataset50173'

    def init_tc(self):
        try:
            self.metrics_server = MetricsServer(self.commcell.webconsole_hostname,
                                                self._inputJSONnode["commcell"]["commcellUsername"],
                                                self._inputJSONnode["commcell"]["commcellPassword"])
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser, self.commcell.webconsole_hostname
            )
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
            self.rpt_builder = builder.ReportBuilder(self.webconsole)
            self.rpt_builder.set_report_name(self.name)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def create_offline_report(self):
        """Create offline dataset with frequency settings"""
        self.dataset = Datasets.DatabaseDataset()
        self.rpt_builder.add_dataset(self.dataset)
        self.dataset.set_dataset_name(self.dataset_name)
        self.dataset.set_sql_query(
            """
            SELECT 2 + 2 [Number]
            UNION ALL
            SELECT 2 + 2 + 3
            """
        )
        self.dataset.enable_offline_collection()
        self.dataset.set_collection_frequency(60)
        self.dataset.save()
        table = builder.DataTable("AutomationTable")
        self.rpt_builder.add_component(table, self.dataset)
        table.add_column_from_dataset()
        self.rpt_builder.save_and_deploy()

    @test_step
    def check_frequency_settings(self):
        """check frequency settings in offline query"""
        file_content, file_url = self.metrics_server.get_collect_file_content(self.dataset_name)
        if self.freq_str not in file_content:
            raise CVTestStepFailure(
                f"Frequency flag not found in collection query [{file_url}]"
            )

    @test_step
    def remove_frequency_settings(self):
        """Edit dataset and remove frequency setting"""
        self.rpt_builder.edit_dataset(self.dataset)
        self.dataset.disable_frequency_collection()
        self.dataset.save()
        self.rpt_builder.save()
        self.rpt_builder.deploy()
        file_content, file_url = self.metrics_server.get_collect_file_content(self.dataset_name)
        if self.freq_str in file_content:
            raise CVTestStepFailure(
                f"Frequency flag found in collection query [{file_url}]"
            )
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()

    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.create_offline_report()
            self.check_frequency_settings()
            self.remove_frequency_settings()
            self.delete_report()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
