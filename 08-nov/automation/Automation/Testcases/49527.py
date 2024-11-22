
from AutomationUtils.cvtestcase import CVTestCase
from Reports.Custom import sql_utils
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import (
    CVTestStepFailure,
    CVTestCaseInitFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom import builder
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report: (DataSet) - Preview, Create, Edit and Delete"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.SOFTWARESTORE
        self.feature = self.features_list.WEBCONSOLE
        self.show_to_user = True
        self.utils = TestCaseUtils(self)
        self.manage_reports = None
        self.navigator = None
        self.admin_console = None
        self.webconsole: WebConsole = None
        self.browser: Browser = None
        self.rpt_builder = None
        self.dataset = None
        self.table = None

    def init_tc(self):
        try:
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
        except Exception as e:
            raise CVTestCaseInitFailure(e)

    @TestStep()
    def preview(self):
        """Preview dataset during dataset creation"""
        self.rpt_builder = builder.ReportBuilder(self.webconsole)
        self.dataset = builder.Datasets.DatabaseDataset()
        self.rpt_builder.add_dataset(self.dataset)
        self.dataset.set_dataset_name("AutomationDataset")
        self.dataset.set_sql_query(sql_utils.SQLQueries.sql_server_q1())
        data = self.dataset.get_preview_data()
        expected_data = sql_utils.SQLQueries.sql_server_r1(
            value_processor=sql_utils.ValueProcessors.string
        )
        if data != expected_data:
            self.log.error(
                f"Unexpected preview data received:[{data}]\n"
                f"Expected [{expected_data}]"
            )
            raise CVTestStepFailure("Unexpected preview data")

    @TestStep()
    def save(self):
        """Save dataset and associate any component to it"""
        self.rpt_builder.set_report_name(self.name)
        self.dataset.save()
        self.table = builder.DataTable("AutomationTable")
        self.rpt_builder.add_component(self.table, self.dataset)
        self.table.add_column_from_dataset()
        data = self.table.get_table_data()
        expected_data = sql_utils.SQLQueries.sql_server_r1(
            value_processor=sql_utils.ValueProcessors.string
        )
        if expected_data != data:
            self.log.error(
                f"Unexpected preview data received:[{data}]\n"
                f"Expected [{expected_data}]"
            )
            raise CVTestStepFailure("Unexpected data in table")
        self.rpt_builder.save_and_deploy()

    @TestStep()
    def edit(self):
        """Edit dataset and save the dataset"""
        self.rpt_builder.edit_dataset(self.dataset)
        self.dataset.set_sql_query("SELECT 1 [One], 2 [Two]")
        data = self.dataset.get_preview_data()
        if data != {"One": ["1"], "Two": ["2"]}:
            self.log.error(
                f"Unexpected preview data received:[{data}]\n"
                "Expected [{'One': ['1'], 'Two': ['2']}}]"
            )
            raise CVTestStepFailure(
                "Unexpected Preview data after edit"
            )
        self.dataset.save()
        self.rpt_builder.refresh()
        data = self.table.get_table_data()
        if data != {"One": ["1"], "Two": ["2"]}:
            self.log.error(
                f"Unexpected Table data received:[{data}]\n"
                "Expected [{'One': ['1'], 'Two': ['2']}}]"
            )
            raise CVTestStepFailure(
                "Unexpected Table data after edit"
            )

    @TestStep()
    def delete(self):
        """Delete dataset"""
        # TODO: check if dataset is removed
        self.rpt_builder.delete_dataset("AutomationDataset")
        if "AutomationTable" in self.rpt_builder.get_all_component_titles():
            self.log.error(
                "Table not deleted after deleting dataset"
            )
            raise CVTestStepFailure(
                "Table exists even after deleting dataset"
            )
        self.rpt_builder.save_and_deploy()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()

    def run(self):
        try:
            self.init_tc()
            self.preview()
            self.save()
            self.edit()
            self.delete()
        except Exception as excp:
            self.utils.handle_testcase_exception(excp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
