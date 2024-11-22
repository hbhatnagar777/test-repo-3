# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

from AutomationUtils.cvtestcase import CVTestCase
from Reports.Custom.utils import CustomReportUtils
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import TestStep

from Web.Common.exceptions import (
    CVTestCaseInitFailure, CVTestStepFailure
)
from Web.Common.cvbrowser import (
    BrowserFactory, Browser
)
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Custom import (
    builder, inputs as wcinputs
)
from Web.AdminConsole.Reports.Custom import viewer
from Web.AdminConsole.Reports.Custom import inputs as acinputs
from Web.API.customreports import CustomReportsAPI


class TestCase(CVTestCase):

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Reports: Commcell input"
        self.manage_reports = None
        self.navigator = None
        self.admin_console = None
        self.util = None
        self.report_viewer = None
        self._browser = None
        self.webconsole: WebConsole = None
        self.tcinputs = {
            "multiCommcell": None,
            "singleCommcell": None
        }
        self.rpt_builder: builder.ReportBuilder = None
        self.input_controller_wc: wcinputs.ListBoxController = None
        self.input_controller_ac: acinputs.ListBoxController = None
        self.expected_multi_cc = None

    @property
    def browser(self):
        if self._browser is None:
            self._browser = BrowserFactory().create_browser_object()
            self._browser.open()
        return self._browser

    def init_multi_commcell_wc(self):
        try:
            self.util = CustomReportUtils(self, username=self.inputJSONnode['commcell']['commcellUsername'],
                                          password=self.inputJSONnode['commcell']['commcellPassword'])
            with CustomReportsAPI(
                    self.tcinputs["multiCommcell"],
                    username=self.inputJSONnode['commcell']['commcellUsername'],
                    password=self.inputJSONnode['commcell']['commcellPassword']
            ) as api:
                self.expected_multi_cc = self.util.get_commcell_datasources(api)
                '''
                self.expected_multi_cc = list(map(
                    lambda c: c.split(".")[0].lower(),
                    self.util.get_commcell_datasources(api)
                ))'''
                self.expected_multi_cc.sort()
                err_msg = f"Not enough commcells on [{self.tcinputs['multiCommcell']}]"
                assert len(self.expected_multi_cc) > 1, err_msg

            self.webconsole = WebConsole(
                self.browser, self.tcinputs["multiCommcell"]
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
        except Exception as err:
            raise CVTestCaseInitFailure(err) from err

    @test_step
    def init_single_commcell_wc(self):
        """Initializing single commcell and verifying """
        try:
            with CustomReportsAPI(
                    self.tcinputs["singleCommcell"],
                    username=self.tcinputs["singleCCUser"],
                    password=self.tcinputs["singleCCPwd"]
            ) as api:
                expected_single_cc = self.util.get_commcell_datasources(api)
                cc = self.tcinputs['singleCommcell']
                err_msg = (
                    f"More than one commcell found on [{cc}]\n." +
                    f"Expecting only one commcell."
                )
                assert len(expected_single_cc) == 1, err_msg
            self.webconsole = WebConsole(
                self.browser, self.tcinputs["singleCommcell"]
            )
            self.admin_console = AdminConsole(self.browser, self.tcinputs["singleCommcell"])
            self.admin_console.login(
                username=self.tcinputs["singleCCUser"],
                password=self.tcinputs["singleCCPwd"]
            )
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_reports()
            self.manage_reports = ManageReport(self.admin_console)
            self.manage_reports.add_report()
            self.rpt_builder = builder.ReportBuilder(self.webconsole)
            self.rpt_builder.set_report_name(self.name)
        except Exception as err:
            raise CVTestCaseInitFailure(err) from err

    def _create_report(self):
        ip_datatype = wcinputs.Commcell("CommcellInput")
        self.rpt_builder.add_input(ip_datatype)
        ip_datatype.enable_multi_selection()
        ip_datatype.set_required()
        self.input_controller_wc = wcinputs.ListBoxController("CommcellInput")
        ip_datatype.add_html_controller(self.input_controller_wc)
        ip_datatype.save()

        ds = builder.Datasets.DatabaseDataset()
        self.rpt_builder.add_dataset(ds)
        ds.set_all_commcell_datasource()
        ds.set_dataset_name("AutomationCommcellDataSet")
        ds.set_sql_query(
            """
            SELECT displayName [Commcell]
            FROM APP_Client
            WHERE id = 2
            """
        )
        ds.save()

        table = builder.DataTable("CommcellTable")
        self.rpt_builder.add_component(table, ds)
        table.add_column_from_dataset("Commcell")

        self.rpt_builder.save_and_deploy()
        self.browser.driver.close()

    @test_step
    def create_report(self):
        """Create a report with commcell input"""
        self._create_report()

    @test_step
    def list_all_commcells(self):
        """Lists all commcells"""
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)
        self.report_viewer = viewer.CustomReportViewer(self.admin_console)
        self.input_controller_ac = acinputs.ListBoxController("CommcellInput")
        self.report_viewer.associate_input(self.input_controller_ac)
        """On machines with multiple commcells, all the commcells should be listed."""
        received_commcells = self.input_controller_ac.get_available_options()
        '''
        received_commcells_ = list(map(
            lambda c: c.split(".")[0].lower(),
            self.input_controller.get_available_options()
        ))
        '''
        received_commcells.sort()
        if self.expected_multi_cc != received_commcells:
            self.log.error(
                f"\nExpected: {self.expected_multi_cc}"
                f"\nReceived: {received_commcells}"
            )
            raise CVTestStepFailure(
                "Commcell list mismatch in multi commcell WebConsole"
            )

        return received_commcells

    @test_step
    def select_commcell_from_dropdown(self, received_commcells):
        """After selecting a commcell, the dataset result should be filtered."""
        self.input_controller_ac.select_value(received_commcells[0], ok=True)
        table = viewer.DataTable("CommcellTable")
        rpt_viewer = viewer.CustomReportViewer(self.admin_console)
        rpt_viewer.associate_component(table)
        data = table.get_column_data("Commcell")
        expected = received_commcells[0].split(".")[0].lower()
        received = (data if data else [""])[0].split(".")[0].lower()
        if expected != received:
            err = f"\nExpected: {expected}\nReceived: {received}"
            raise CVTestStepFailure(f"Commcell list not filtered.{err}")
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)
        AdminConsole.logout_silently(self.admin_console)

    @test_step
    def input_should_not_be_visible(self):
        """In single commcell WC, commcell input should not be shown and report should auto select local commcell."""
        self._create_report()
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)
        rpt_viewer = viewer.CustomReportViewer(self.admin_console)
        if rpt_viewer.get_all_input_names():
            raise CVTestStepFailure("Commcell Input is visible on report viewer")
        table = viewer.DataTable("CommcellTable")
        rpt_viewer.associate_component(table)
        received_data = table.get_column_data("Commcell")[0].split(".")[0]
        from cvpysdk.commcell import Commcell
        single_cc = Commcell(
            self.tcinputs["singleCommcell"],  self.tcinputs["singleCCUser"], self.tcinputs["singleCCPwd"])
        expected_data = single_cc.commserv_name
        if expected_data.lower() != received_data.lower():
            raise CVTestStepFailure(
                f"Unexpected data; "
                f"\nExpected: {expected_data}"
                f"\nReceived: {received_data}"
            )

    @test_step
    def verify_required_input(self):
        """Components should not be visible till all the required inputs are selected"""
        viewer_obj = viewer.CustomReportViewer(self.admin_console)
        if "CommcellTable" in viewer_obj.get_all_component_titles():
            raise CVTestStepFailure(
                "Components are visible without selecting required commcell input"
            )

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_multi_commcell_wc()
            self.create_report()
            commcells = self.list_all_commcells()
            self.verify_required_input()
            self.select_commcell_from_dropdown(commcells)
            self.init_single_commcell_wc()
            self.input_should_not_be_visible()
            self.delete_report()
        except Exception as err:
            self.util.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
