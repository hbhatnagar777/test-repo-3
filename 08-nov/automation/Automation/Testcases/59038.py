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
from Web.WebConsole.Reports.Custom.builder import Datasets
from Web.Common.page_object import handle_testcase_exception, CVTestStepFailure


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report: validate Multi commcell data aggregation"
        self.utils = TestCaseUtils(self)
        self.webconsole: WebConsole = None
        self.manage_reports = None
        self.admin_console = None
        self.browser: Browser = None
        self.rpt_builder = None
        self.navigator = None
        self.dataset = None
        self.expected_data = None
        self.received_data = None
        self.report_name = 'TC 59038-Multi-Commcell Query'
        self.q1 = f"""
                select count(id) as 'ID_count' from APP_Client
                """
        self.q2 = f"""
                select sum(ID_count) as ID_count from $this$
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
            self.manage_reports.delete_report(self.name)
            self.manage_reports.add_report()
            self.rpt_builder = builder.ReportBuilder(self.webconsole)
            self.rpt_builder.set_report_name(self.report_name)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def create_dataset(self):
        """Create Database dataset"""
        self.dataset = Datasets.DatabaseDataset()
        self.rpt_builder.add_dataset(self.dataset)
        self.dataset.set_dataset_name("testDB-1")
        self.dataset.set_all_commcell_datasource()
        self.dataset.set_sql_query(self.q1)
        data = self.dataset.get_preview_data()
        self.expected_data = list(map(int, data['ID_count']))
        self.dataset.set_multicommcell_query(self.q2)
        self.received_data = int(self.dataset.get_preview_data()['ID_count'][0])
        self.dataset.save()

    @test_step
    def verify_data(self):
        """validate the data"""
        if sum(self.expected_data) != self.received_data:
            raise CVTestStepFailure(f"expected sum {sum(self.expected_data)} {self.expected_data} "
                                    f"received sum {self.received_data}")
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()

    def run(self):
        try:
            self.init_tc()
            self.create_dataset()
            self.verify_data()
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
