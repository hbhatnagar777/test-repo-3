from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom import builder
from Web.WebConsole.webconsole import WebConsole
from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.Reports.Custom.builder import Datasets
from Web.Common.page_object import handle_testcase_exception, CVTestStepFailure


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report (DataSet)-Script dataset"
        self.utils = TestCaseUtils(self)
        self.webconsole: WebConsole = None
        self.admin_console = None
        self.manage_reports = None
        self.browser: Browser = None
        self.rpt_builder = None
        self.navigator = None
        self.dataset = None
        self.data_table = None
        self.table = None
        self.viewer = None
        self.expected_data = None
        self.report_name = 'TC 59035-Script'
        self.q1 = f"""
                select top 2 id, name from app_client
                """
        self.q2 = f"""
                var DbDs= DataSet.getInstance("dbdataset", false);
                var clients= DbDs.getColumnData("name");
                var temp= ''
                for(var i=0;i<clients.length;i++)
                    temp += clients[i] + ';';
                provider.execute("select '" +temp + "' as name");
                """

    def init_tc(self):
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.utils.get_temp_dir())
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
            self.manage_reports.delete_report(self.report_name)
            self.manage_reports.add_report()
            self.rpt_builder = builder.ReportBuilder(self.webconsole)
            self.rpt_builder.set_report_name(self.report_name)
            self.viewer = viewer.CustomReportViewer(self.admin_console)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def create_database_dataset(self):
        """Create Database dataset"""
        dataset = Datasets.DatabaseDataset()
        self.rpt_builder.add_dataset(dataset)
        dataset.set_dataset_name("dbdataset")
        dataset.set_sql_query(self.q1)
        self.expected_data = dataset.get_preview_data()
        self.expected_data = self.expected_data['name'][0] + ';' + self.expected_data['name'][1] + ';'
        dataset.save()
        self.rpt_builder.save_and_deploy()
        self.browser.driver.refresh()
        self.webconsole.wait_till_load_complete()

    @test_step
    def create_script_dataset(self):
        """Create DataSet with CommServ datasource"""
        self.dataset = Datasets.ScriptDataset()
        self.rpt_builder.add_dataset(self.dataset)
        self.dataset.set_dataset_name("scriptds")
        self.dataset.set_sql_query(self.q2)
        self.dataset.save()

    @test_step
    def add_datasource_to_table(self):
        """Add the datasource to any table"""
        self.data_table = builder.DataTable("TestTable")
        self.rpt_builder.add_component(self.data_table, self.dataset)
        self.data_table.add_column_from_dataset()
        self.rpt_builder.save_and_deploy()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.report_name)

    @test_step
    def verify_data(self):
        """Verify that the table data is correct"""
        self.table = viewer.DataTable("TestTable")
        self.viewer.associate_component(self.table)
        received_data = self.table.get_table_data()
        received_data = received_data['name'][0]
        if received_data != self.expected_data:
            raise CVTestStepFailure(f'Expected data {self.expected_data} '
                                    f'received data {received_data}')

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.report_name)

    def run(self):
        try:
            self.init_tc()
            self.create_database_dataset()
            self.create_script_dataset()
            self.add_datasource_to_table()
            self.verify_data()
            self.delete_report()
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
