# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Metrics: Validate Dashboard default alerts template"""
from cvpysdk.security.user import User
from cvpysdk.license import LicenseDetails
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils

from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure,
)
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Metrics.dashboard import Alert
from Web.WebConsole.Reports.Metrics.report import MetricsReport
from Web.WebConsole.Reports.Custom import viewer
from Web.WebConsole.Reports.manage_alerts import AlertSettings
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):
    """TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics: Validate Dashboard default alerts template"
        self.browser = None
        self.utils = None
        self.webconsole = None
        self.alert_type = list()
        self.alert_setting = None
        self.navigator = None
        self.alert = None
        self.commcell_id = None
        self.expected_alert_report_title = {}

    def init_tc(self):
        """Initializes browser and navigate to required page"""
        try:
            self.utils = TestCaseUtils(self, username=self.inputJSONnode['commcell']['commcellUsername'],
                                       password=self.inputJSONnode['commcell']['commcellPassword'])
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login()
            self.webconsole.goto_commcell_dashboard()
            self.navigator = Navigator(self.webconsole)
            self.alert = Alert(self.webconsole)
            self.alert_type = [Alert.AlertType.DISK_LIBRARY, Alert.AlertType.DDB_DISK,
                               Alert.AlertType.INDEX_CACHE]
            _license = LicenseDetails(self.commcell)
            self.commcell_id = hex(_license.commcell_id).split("0x")[1].upper()
            self.expected_alert_report_title = {
                "Alert for CommCell [%s(%s)] - Disk Library Growth" %
                (self.commcell.commserv_name, self.commcell_id): "Disk Library Growth",
                "Alert for CommCell [%s(%s)] - DDB Disk Space Utilization" %
                (self.commcell.commserv_name, self.commcell_id): "DDB Disk Space Utilization",
                "Alert for CommCell [%s(%s)] - Index Cache Location" %
                (self.commcell.commserv_name, self.commcell_id): "Index Cache Location"
            }
            self.alert_setting = AlertSettings(self.webconsole)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def toggle_all_alert(self, level="worldwide", on=True):
        """Toggles all alerts"""
        if level == "worldwide":
            self.navigator.goto_worldwide_dashboard()
        else:
            self.navigator.goto_commcell_dashboard(level)
        self.alert.toggle_alerts(self.alert_type, on)

    @test_step
    def verify_alerts(self, level="worldwide", disabled=False):
        """Verify alerts"""
        self.navigator.goto_alerts_configuration()
        error = list(filter(lambda alert: self.alert_setting.is_alert_enabled(alert.value, level) is disabled,
                            self.alert_type))
        if error:
            error = [alert.value for alert in error]
            msg = "enabled" if disabled else "disabled"
            raise CVTestStepFailure(f"The Following alerts are {msg} in World wide alerts:"
                                    f"{error}")

    @test_step
    def validate_email_address(self):
        """Verifies email Address"""
        user = User(self.commcell, self.webconsole.username)
        email = list(map(lambda alert: self.alert_setting.fetch_email_address(alert.value),
                         self.alert_type))
        fetched_email = set(email)
        if len(fetched_email) != 1:
            raise CVTestStepFailure(f"Expected email: {user.email}\nReceived "
                                    f"email:{fetched_email}")
        if user.email != next(iter(fetched_email)):
            raise CVTestStepFailure(f"Expected email: {user.email}\nReceived "
                                    f"email:{next(iter(fetched_email))}")

    @test_step
    def verify_alert_report_titles(self):
        """Verify dashboard alert's edit criteria is redirecting to correct page"""
        self.navigator.goto_alerts_configuration()
        for each_alert_name, expected_title in self.expected_alert_report_title.items():
            self.log.info("Verifying report title for the [%s] alert", each_alert_name)
            _alert = self.alert_setting.edit_alert(each_alert_name)
            _alert.access_edit_criteria()
            self.browser.driver.switch_to.window(self.browser.driver.window_handles[1])
            _alert.cancel()
            if expected_title == 'Index Cache Location':  # Custom Report
                creport = viewer.CustomReportViewer(self.webconsole)
                page_title = creport.get_report_name()
            else:
                mreport = MetricsReport(self.webconsole)
                page_title = mreport.get_page_title()
            if page_title != expected_title:
                raise CVTestStepFailure("[%s] alert isn't matching with title of the report, "
                                        "expecting [%s] as report title, but currently [%s] "
                                        "shown as report title. Please verify. "
                                        % (each_alert_name, expected_title, page_title))
            self.browser.driver.close()
            self.browser.driver.switch_to.window(self.browser.driver.window_handles[0])
            self.log.info("Verified page title for the [%s] alert", each_alert_name)

    def run(self):
        try:
            self.init_tc()
            self.toggle_all_alert()
            self.verify_alerts()
            self.toggle_all_alert(on=False)
            self.verify_alerts(disabled=True)
            self.validate_email_address()
            self.toggle_all_alert(level=self.commcell.commserv_name)
            self.verify_alerts(level="CommCell")
            self.verify_alert_report_titles()
            self.toggle_all_alert(level=self.commcell.commserv_name, on=False)
            self.verify_alerts(level="Commcell", disabled=True)
            self.validate_email_address()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
