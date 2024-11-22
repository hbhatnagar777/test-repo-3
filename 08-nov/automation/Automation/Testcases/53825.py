# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.Custom.utils import CustomReportUtils

from Web.Common.cvbrowser import BrowserFactory, Browser

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.Reports.manage_reports import ManageReport

from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.Reports.Custom.inputs import ListBoxController
from Web.AdminConsole.Reports.Custom.viewer import CustomReportViewer
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):
    """Admin Console: Validate 'Save as View' on Report"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Admin Console: Validate 'Save as View' on Report"
        self.utils = CustomReportUtils(self)
        self.browser = None
        self.webconsole = None
        self.report = None
        self.admin_console = None
        self.navigator = None
        self.manage_report = None

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.utils.webconsole = self.webconsole
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode["commcell"]["commcellUsername"],
                                     self.inputJSONnode["commcell"]["commcellPassword"])
            self.navigator = self.admin_console.navigator
            self.manage_report = ManageReport(self.admin_console)
            self.navigator.navigate_to_reports()
            self.manage_report.access_report("Audit trail")
            self.report = Report(self.admin_console)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def save_view(self):
        """Save a view  and set it to default"""
        report_viewer = CustomReportViewer(self.admin_console)
        list_box_controller = ListBoxController("Users")
        report_viewer.associate_input(list_box_controller)
        list_box_controller.select_value(self.inputJSONnode["commcell"]["commcellUsername"])
        list_box_controller.apply()
        self.report.save_as_view(self.utils.testcase.id)

        if self.utils.testcase.id not in self.report.get_all_views():
            raise CVTestStepFailure("The created view is not listed")

    @test_step
    def verify_view(self):
        """Verify loading of same view on accessing again"""
        self.navigator.navigate_to_reports()
        self.manage_report.access_report("Audit trail")
        current_view = self.report.get_current_view()
        if self.utils.testcase.id != current_view:
            raise CVTestStepFailure(f"Expected View:{self.name},  Currnet View: {current_view}.")

    @test_step
    def delete_view(self):
        """Delete the view"""
        self.report.delete_view(self.id)
        if self.id in self.report.get_all_views():
            raise CVTestStepFailure("View exists even after deleting it")

    def run(self):
        try:
            self.init_tc()
            if self.id in self.report.get_all_views():
                self.delete_view()
            self.save_view()
            self.verify_view()
            self.delete_view()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
