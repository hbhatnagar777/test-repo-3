from AutomationUtils.cvtestcase import CVTestCase
from Reports.Custom.utils import CustomReportUtils
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom import builder
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.webconsole import WebConsole
from Web.AdminConsole.Reports.Custom import viewer
from Web.WebConsole.Reports.Custom.builder import Datasets
from Web.API import customreports
from Web.Common.page_object import handle_testcase_exception, CVTestStepFailure


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Reports: Acceptance for Rest API option in Custom report tables"
        self.utils = None
        self.webconsole: WebConsole = None
        self.admin_console = None
        self.browser: Browser = None
        self.rpt_builder = None
        self.navigator = None
        self.obj_manage_report = None
        self.dataset = None
        self.data_table = None
        self.table = None
        self.viewer = None
        self.api = None
        self.url = None
        self.response_dict = None
        self.report_name = 'TC 59037-Get REST API'

    def init_tc(self):
        try:
            self.utils = CustomReportUtils(self, username=self.inputJSONnode["commcell"]["commcellUsername"],
                                           password=self.inputJSONnode["commcell"]["commcellPassword"])
            self.utils.cre_api.delete_custom_report_by_name(
                self.report_name, suppress=True
            )
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.utils.get_temp_dir())
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser, self.commcell.webconsole_hostname
            )
            self.webconsole.login(self.inputJSONnode['commcell']['commcellUsername'],
                                  self.inputJSONnode['commcell']['commcellPassword'])

            Navigator(self.webconsole).goto_report_builder()
            self.rpt_builder = builder.ReportBuilder(self.webconsole)
            self.rpt_builder.set_report_name(self.report_name)
            self.viewer = viewer.CustomReportViewer(self.admin_console)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def create_dataset(self):
        """Create DataSet with CommServ datasource"""
        self.dataset = Datasets.DatabaseDataset()
        self.rpt_builder.add_dataset(self.dataset)
        self.dataset.set_dataset_name("TestDataset")
        self.dataset.set_local_commcell_datasource()
        self.dataset.set_sql_query('SELECT TOP 20 * FROM APP_Client WITH(NOLOCK)')
        self.dataset.save()

    @test_step
    def add_datasource_to_table(self):
        """Add the datasource to any table"""
        self.data_table = builder.DataTable("TestTable")
        self.rpt_builder.add_component(self.data_table, self.dataset)
        self.data_table.add_column_from_dataset()
        self.data_table.get_all_columns()
        self.rpt_builder.save_and_deploy()
        self.rpt_builder.open_report()
        self.table = viewer.DataTable("TestTable")
        self.viewer.associate_component(self.table)

    @test_step
    def copy_rest_api(self):
        """copy rest api"""
        self.url = self.table.rest_api()
        self.url = self.url.split('datasets/')[1]

    @test_step
    def read_xml(self):
        """Read the XML of the REST API"""
        self.api = customreports.CustomReportsAPI(
            self.commcell.webconsole_hostname, username=self.inputJSONnode["commcell"]["commcellUsername"],
            password=self.inputJSONnode["commcell"]["commcellPassword"]
        )
        self.response_dict = self.api.get_data_by_url(self.url)

    @test_step
    def verify_data(self):
        """Verify the xml and report data"""
        expected_columns_name = self.data_table.get_all_columns()
        received_columns_name = []
        for column in self.response_dict['columns']:
            received_columns_name.append(column['name'])
        received_columns_name.remove('sys_rowid')
        received_columns_name.remove('Data Source')
        expected_columns_name.remove('CommCell')
        if sorted(expected_columns_name) != sorted(received_columns_name):
            raise CVTestStepFailure(f'Expected columns {expected_columns_name} '
                                    f'received columns {received_columns_name}')
        expected_record_count = self.data_table.get_row_count()
        received_record_count = self.response_dict['recordsCount']
        if received_record_count != expected_record_count:
            raise CVTestStepFailure(f'Expected Number of rows {expected_record_count} '
                                    f'received Number of rows {received_record_count}')

    def run(self):
        try:
            self.init_tc()
            self.create_dataset()
            self.add_datasource_to_table()
            self.copy_rest_api()
            self.read_xml()
            self.verify_data()
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
