# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Triggering workflow from Custom Reports"""

from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.report_templates import DefaultReport
from Reports.Custom.utils import CustomReportUtils

from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole

from Web.WebConsole.Forms.forms import Forms
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.Custom import viewer


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom Report Table: triggering workflow"
        self.browser = None
        self.manage_reports = None
        self.navigator = None
        self.webconsole = None
        self.utils = None
        self.button = None
        self.report = None
        self.forms = None
        self.admin_console = None

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.utils = CustomReportUtils(self, username=self.inputJSONnode['commcell']['commcellUsername'],
                                           password=self.inputJSONnode['commcell']['commcellPassword'])
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.utils.webconsole = self.webconsole
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
            self.report = DefaultReport(self.utils, browser=self.browser)
            self.report.build_default_report(keep_same_tab=True)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def add_button_and_set_workflow(self):
        """Adds button to the table and runs workflow"""
        self.button = self.report.table.Button("Workflow button")
        self.report.table.toggle_button_panel()
        self.report.table.add_button(self.button)
        self.button.set_workflow("Demo_CheckReadiness")
        self.report.report_builder.save_and_deploy()

    def access_report_cc(self):
        """Opens report in command center"""
        self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
        self.browser.driver.refresh()
        self.manage_reports.access_report(self.name)

    @test_step
    def verify_workflow(self):
        """verifies if workflow panel is open"""
        self.forms = Forms(self.admin_console)
        cc_report_viewer = viewer.CustomReportViewer(self.admin_console)
        cc_table = viewer.DataTable("Automation Table")
        cc_report_viewer.associate_component(cc_table)
        cc_button = cc_table.Button("Workflow button")
        cc_report_viewer.associate_component(cc_button)
        cc_button.click_button()
        if self.forms.is_form_open("Demo_CheckReadiness"):
            self.forms.click_cancel()
        else:
            raise CVTestStepFailure("Workflow panel doesn't open")

    @test_step
    def delete_report(self):
        """Deletes the report"""
        self.navigator.navigate_to_reports()
        self.manage_reports.delete_report(self.name)

    def run(self):
        try:
            self.init_tc()
            self.add_button_and_set_workflow()
            self.access_report_cc()
            self.verify_workflow()
            self.delete_report()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
