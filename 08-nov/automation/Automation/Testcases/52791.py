# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Metrics:Health report export validation for cloud metrics server"""
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.report import MetricsReport

from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase

from Reports.utils import TestCaseUtils
from Reports import reportsutils


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics:Health report export validation for cloud metrics server"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.METRICSREPORTS
        self.feature = self.features_list.WEBCONSOLE
        self.show_to_user = True
        self.log = logger.get_log()
        self.tcinputs = {
            "customer_user_name": None,
            "customer_password": None
        }
        self.browser = None
        self.webconsole = None
        self.report = None
        self.navigator = None
        self.export = None
        self.commcell_name = None
        self.utils = TestCaseUtils(self)

    def access_health_page(self, user_name, password):
        """
        login to webconsole and access health page
        Args:
            user_name: webconsole login user name
            password: webconsole login password
        """
        try:
            download_directory = self.utils.get_temp_dir()
            self.log.info("Download directory:%s", download_directory)
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.set_downloads_dir(download_directory)
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(user_name, password)
            self.commcell_name = reportsutils.get_commcell_name(self.commcell)
            self.webconsole.goto_commcell_dashboard()
            self.navigator = Navigator(self.webconsole)
            self.navigator.goto_commcell_reports(commcell_name=self.commcell_name)
            self.navigator.goto_health_report()
            self.report = MetricsReport(self.webconsole)
            self.export = self.report.export_handler()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def verify_export_to_pdf(self):
        """
        Verify pdf export
        """
        self.utils.reset_temp_dir()
        self.export.to_pdf()
        self.webconsole.wait_till_loadmask_spin_load()
        self.utils.poll_for_tmp_files('pdf', timeout=600, min_size=500)
        self.log.info("pdf export completed successfully")

    @test_step
    def verify_export_to_word(self):
        """
        Verify word export
        """
        self.utils.reset_temp_dir()
        self.export.to_health_word()
        self.webconsole.wait_till_loadmask_spin_load()
        self.utils.poll_for_tmp_files('docx', timeout=280)
        self.log.info("docx export completed successfully")

    @test_step
    def verify_export_to_health_ppt(self):
        """
        Verify Health ppt export
        """
        self.utils.reset_temp_dir()
        self.export.to_health_ppt()
        self.webconsole.wait_till_loadmask_spin_load(timeout=80)
        self.utils.poll_for_tmp_files("pptx", timeout=380)
        self.log.info("health ppt export completed successfully")

    @test_step
    def verify_export_to_value_assessment_ppt(self):
        """
        Verify value assessment ppt export
        """
        self.utils.reset_temp_dir()
        self.export.to_value_assesment_ppt()
        self.webconsole.wait_till_loadmask_spin_load()
        self.utils.poll_for_tmp_files('pptx', timeout=180)
        self.log.info("value assessment ppt export completed successfully")

    @test_step
    def verify_customer_export_options(self):
        """
        Verify expected available export options for non commvault user
        """
        try:
            expected_option = ["PDF", "CSV"]
            available_export_options = self.export.get_available_export_types()
            self.log.info("Expected export options:%s", str(expected_option))
            self.log.info("Available export options:%s", str(available_export_options))
            if expected_option != available_export_options:
                raise CVTestStepFailure("Expected export [%s] is not present in health export. "
                                        "Available exports are:[%s]" %
                                        (str(expected_option), str(available_export_options)))
            self.log.info("verified available export options in health page successfully")
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)

    def run(self):
        try:
            self.access_health_page(user_name=self.tcinputs['customer_user_name'],
                                    password=self.tcinputs['customer_password'])
            self.verify_customer_export_options()
            self.access_health_page(user_name=self.inputJSONnode['commcell']["commcellUsername"],
                                    password=self.inputJSONnode['commcell']["commcellPassword"])
            self.verify_export_to_pdf()
            self.verify_export_to_word()
            self.verify_export_to_health_ppt()
            self.verify_export_to_value_assessment_ppt()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)