# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics: Private metrics Health report pdf export validation"""

from Web.AdminConsole.Reports.manage_reports import ManageReport
from Web.AdminConsole.Reports.report import Report
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase

from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.export = None
        self.commcell_name = None
        self.manage_reports = None
        self.name = "Metrics: Private metrics Health report pdf export validation"
        self.page = "health"
        self.log = logger.get_log()
        self.tcinputs = {}
        self.browser = None
        self.admin_console = None
        self.report = None
        self.navigator = None
        self.commcell_password = None
        self.utils = TestCaseUtils(self)

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
            self.utils.reset_temp_dir()
            download_directory = self.utils.get_temp_dir()
            self.log.info("Download directory:%s", download_directory)
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.set_downloads_dir(download_directory)

            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                              username=self.commcell.commcell_username,
                                              password=self.commcell_password)
            self.admin_console.login(username=self.commcell.commcell_username,
                                     password=self.commcell_password)
            self.admin_console.wait_for_completion()
            self.commcell_name = self.commcell.commserv_name
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_metrics()
            self.manage_reports = ManageReport(self.admin_console)
            self.report = Report(self.admin_console)
            self.manage_reports.access_commcell_health(self.commcell_name)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def verify_health_export_to_pdf(self):
        """
        Verify export to pdf in health page
        """
        self.report.save_as_pdf()
        self.utils.wait_for_file_to_download('pdf')
        self.utils.validate_tmp_files("pdf")
        self.log.info("pdf export completed successfully")

    @test_step
    def verify_expected_export_options(self):
        """
        Verify only pdf export option is visible in private metrics
        """
        expected_option = ["PDF"]
        self.admin_console.wait_for_completion()
        available_export_options = self.report.get_available_export_types()
        if expected_option != available_export_options:
            raise CVTestStepFailure("Expected export [%s] is not present in health export. "
                                    "Available exports are:[%s]" %
                                    (str(expected_option), str(available_export_options)))
        self.log.info("verified available export options in health page successfully")

    def run(self):
        try:
            self.init_tc()
            self.verify_expected_export_options()
            self.verify_health_export_to_pdf()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
