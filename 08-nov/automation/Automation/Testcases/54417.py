"""Validating Shared datasets"""

from Reports.Custom.utils import CustomReportUtils

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Custom import builder
from Web.WebConsole.Reports.Custom import viewer

from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Reports: Validate Shared Dataset"
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.table = None
        self.shared_dataset = None
        self.report_builder = None
        self.utils = CustomReportUtils(self)
        self.query = """SELECT TOP 5 CAST(id AS varchar(10)) id, Name from App_client with (NOLOCK)"""
        self.shared_ds_name = 'TC54417'

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.utils.webconsole = self.webconsole
            self.webconsole.login(self.inputJSONnode['commcell']['commcellUsername'],
                                  self.inputJSONnode['commcell']['commcellPassword'])
            self.webconsole.goto_reports()
            self.utils.cre_api.delete_custom_report_by_name(self.name, suppress=True)
            self.navigator = Navigator(self.webconsole)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def create_dataset(self):
        """Creates dataset"""
        self.navigator.goto_dataset_configuration()

        self.table = viewer.DataTable(title='')
        rpt_viewer = viewer.CustomReportViewer(self.webconsole)
        rpt_viewer.associate_component(self.table, comp_id='dataSetManagerTable')
        self.table.set_filter('Data Set Name', self.shared_ds_name )
        if self.table.get_column_data('Data Set Name'):
            self.log.info(f"Dataset {self.shared_ds_name} already exist")
        else:
            self.log.info(f"Creating Dataset {self.shared_ds_name}")
            button_viewer = viewer.DataTable.Button("New DataSet")
            self.table.associate_button(button_viewer)
            button_viewer.click_button()
            dataset = builder.Datasets.DatabaseDataset()
            dataset.configure_dataset(self.webconsole)
            dataset.set_dataset_name(self.shared_ds_name)
            dataset.set_local_commcell_datasource()
            dataset.set_sql_query(self.query)
            dataset.save_and_deploy()

    @test_step
    def create_shared_dataset(self):
        """Creates Shared dataset"""
        self.navigator.goto_report_builder()
        self.report_builder = builder.ReportBuilder(self.webconsole)
        self.report_builder.set_report_name(self.name)
        self.shared_dataset = builder.Datasets.SharedDataset()
        self.report_builder.add_dataset(self.shared_dataset)
        self.shared_dataset.set_dataset_name("Shared DS")
        self.shared_dataset.select_dataset(self.shared_ds_name)
        self.shared_dataset.save()

    @test_step
    def verify_data(self):
        """Verifying data displayed by Shared dataset"""
        self.table = builder.DataTable("Automation Table 54417")
        self.report_builder.add_component(self.table, self.shared_dataset)
        self.table.add_column_from_dataset()
        elements = self.utils.cre_api.execute_sql(self.query)
        col_list = self.table.get_rows_from_table_data()
        if col_list.sort() != elements.sort():
            self.log.error("Expected : %s", elements)
            self.log.error("Displayed : %s", col_list)
            raise CVTestStepFailure("Data displayed in builder is "
                                    "not matching with the expected table data")
        self.report_builder.save(deploy=True)

    def run(self):
        try:
            self.init_tc()
            self.create_dataset()
            self.create_shared_dataset()
            self.verify_data()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
