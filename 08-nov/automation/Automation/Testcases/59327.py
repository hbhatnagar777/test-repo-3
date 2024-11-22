# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""Main file for executing this test case

Test cases to validate Min service pack while importing report.


"""
import os

from Web.API.webconsole import Reports
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole

from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Custom import builder

from Reports.utils import TestCaseUtils

from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase


CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom report: Validate Min SP while importing report"
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.rpt_api = None
        self.rpt_builder = None
        self.utils = None
        self.report_name = "Feature Release Validation"

    def init_tc(self):
        """
        Initial configuration for the test case
        """
        try:
            self.utils = TestCaseUtils(self, username=self.inputJSONnode['commcell']['commcellUsername'],
                                       password=self.inputJSONnode['commcell']['commcellPassword'])
            self.utils.cre_api.delete_custom_report_by_name(
                self.report_name, suppress=True
            )
            self.rpt_api = Reports(
                self.commcell.webconsole_hostname,
                username=self.inputJSONnode['commcell']['commcellUsername'],
                password=self.inputJSONnode['commcell']['commcellPassword']
            )
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.utils.get_temp_dir())
            self.browser.open()
            self.utils.reset_temp_dir()
            self.webconsole = WebConsole(
                self.browser, self.commcell.webconsole_hostname
            )
            self.webconsole.login(self.inputJSONnode['commcell']['commcellUsername'],
                                  self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = Navigator(self.webconsole)
            self.navigator.goto_report_builder()
            self.rpt_builder = builder.ReportBuilder(self.webconsole)
            self.rpt_builder.set_report_name(self.report_name)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def set_feature_release(self):
        """Set Feature release in report"""
        self.log.info("Setting feature release in report")
        self.rpt_builder.add_feature_release("99")  # setting Min SP as 99
        self.rpt_builder.save(deploy=True)
        self.log.info("Feature release set in report and report is saved and deployed")

    @test_step
    def export_report_definition(self):
        """Export report definition"""
        self.rpt_builder.export_report_template()
        self.rpt_builder.open_report()
        self.log.info("Exported report definition successfully!")

    @test_step
    def delete_report(self):
        """Delete report"""
        self.utils.cre_api.delete_custom_report_by_name(self.report_name, suppress=True)
        self.log.info("Report is deleted")

    @test_step
    def verify_report_import(self):
        """Verify import of report in lower SP Commcell throws exception"""
        try:
            self.rpt_api.import_custom_report_xml(os.path.join(self.utils.get_temp_dir(),
                                                               f"{self.report_name}.xml"))
        except Exception as exception:
            self.log.info(exception)
            if 'Custom Report import failed' in str(exception):
                self.log.info("Report import failed in commcell of lower SP as expected")
        else:
            self.log.info("Report imported in lower SP Commcell")
            raise CVTestStepFailure("Report imported in Commcell lower than specified in report")
        self.log.info("Verified that import of report in lower SP Commcell throws exception")

    def run(self):
        """Main function for test case execution"""
        try:
            self.init_tc()
            self.set_feature_release()
            self.export_report_definition()
            self.delete_report()
            self.navigator.goto_worldwide_report()
            self.verify_report_import()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
