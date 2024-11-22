# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics : Reports content search"""

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.home import ReportsHomePage
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Custom import viewer
from Web.WebConsole.Reports.Metrics.settings import SearchSettings

from AutomationUtils.cvtestcase import CVTestCase

from Reports.utils import TestCaseUtils
from Reports import reportsutils

from cvpysdk.security.user import Users


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics : Reports content search"
        self.commcell_name = None
        self.navigator = None
        self.browser = None
        self.webconsole = None
        self.utils = None
        self.report_home_page = None
        self.report = None
        self.search = {}
        self.browser_2 = None
        self.webconsole_2 = None
        self.report_home_page_2 = None

    def setup(self):
        """ Setup function of test case. """
        self.commcell_name = reportsutils.get_commcell_name(self.commcell)
        self.search = {
            "METRIC_CONTENT_KEYWORD": "<1GB",
            "METRIC_CONTENT_REPORT": "Largest 25 Clients",
            "METRIC_COLUMN_KEYWORD":  "Jobs Affected",
            "METRIC_COLUMN_REPORT": "Top 10 Errors in last 24 hours",
            "CUSTOM_CONTENT_KEYWORD": "Replication",
            "CUSTOM_CONTENT_REPORT": "License summary",
            "CUSTOM_COLUMN_KEYWORD":  "Purchased",
            "CUSTOM_COLUMN_REPORT":   "License summary"
        }

        self.utils = TestCaseUtils(self)

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object(name="Admin Browser")
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login()
            self.webconsole.goto_reports()
            self.report_home_page = ReportsHomePage(self.webconsole)
            self.navigator = Navigator(self.webconsole)
            self.is_server_configured()     # Check whether advanced search is configured.
            self.does_user_exist(self._tcinputs["report_management_user"])
            self.report = viewer.CustomReportViewer(self.webconsole)
            self.unshare_report()  # unshare before checking with non admin user
            self.navigator.goto_worldwide_report()

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def does_user_exist(self, user_name):
        """ Checks whether the user exists. """
        users = Users(self.commcell)
        if not users.has_user(user_name):
            raise CVTestCaseInitFailure("Has no user under the name {}".format(user_name))

    def is_server_configured(self):
        """ verifies whether advanced search is configured. """

        # Navigates to report settings
        self.navigator.goto_settings_configuration()

        # Verify server configured
        search_settings = SearchSettings(self.webconsole)
        if search_settings.is_advanced_search_configured() is False:
            raise CVTestStepFailure("Advanced Search is not configured on this server.\
                                     Cannot proceed with the test case.")

        # Navigates back to WorldWide Report Page.
        self.navigator.goto_worldwide_report()

    @test_step
    def verify_metrics_content_search(self):
        """ Verifies content search on metrics report. """
        self.report_home_page.advanced_search_by_content(self.search["METRIC_CONTENT_KEYWORD"])
        if self.report_home_page.is_advanced_search_report_exists(
                self.search["METRIC_CONTENT_REPORT"]) is False:
            raise CVTestStepFailure(
                "Metric content search FAILED for the keyword '{0}',"
                "Since it cannot find the report '{1}'.".format(
                    self.search["METRIC_CONTENT_KEYWORD"],
                    self.search["METRIC_CONTENT_REPORT"])
            )

    @test_step
    def verify_metrics_column_search(self):
        """ Verifies column search on metrics report. """
        self.report_home_page.advanced_search_by_column(self.search["METRIC_COLUMN_KEYWORD"])
        if self.report_home_page.is_advanced_search_report_exists(
                self.search["METRIC_COLUMN_REPORT"]) is False:
            raise CVTestStepFailure(
                "Metric column search FAILED for the keyword '{0}'"
                " Since it cannot find the report '{1}'.".format(
                    self.search["METRIC_COLUMN_KEYWORD"],
                    self.search["METRIC_COLUMN_REPORT"]
                )
            )

    @test_step
    def verify_custom_content_search(self):
        """ Verifies content search on custom report. """
        self.report_home_page.advanced_search_by_content(self.search["CUSTOM_CONTENT_KEYWORD"])
        if self.report_home_page.is_advanced_search_report_exists(
                self.search["CUSTOM_CONTENT_REPORT"]) is False:
            raise CVTestStepFailure(
                "Custom content search FAILED for the keyword '{0}',"
                " Since it cannot find the report '{1}'.".format(
                    self.search["CUSTOM_CONTENT_KEYWORD"],
                    self.search["CUSTOM_CONTENT_REPORT"]
                )
            )

    @test_step
    def verify_custom_column_search(self):
        """ Verifies column search on custom report. """
        self.report_home_page.advanced_search_by_column(self.search["CUSTOM_COLUMN_KEYWORD"])
        if self.report_home_page.is_advanced_search_report_exists(
                self.search["CUSTOM_COLUMN_REPORT"]) is False:
            raise CVTestStepFailure(
                "Custom column search FAILED for the keyword '{0}',"
                " Since it cannot find the report '{1}'.".format(
                    self.search["CUSTOM_COLUMN_KEYWORD"],
                    self.search["CUSTOM_COLUMN_REPORT"]
                )
            )

    def login_as_non_admin_user(self):
        """ Opens a new browser window and logs in as non admin user,
        further navigating to reports home page.

        """
        self.browser_2 = BrowserFactory().create_browser_object(name="Non-Admin Browser")
        self.browser_2.open()
        self.webconsole_2 = WebConsole(self.browser_2, self.commcell.webconsole_hostname)
        self.webconsole_2.login(
            self._tcinputs["report_management_user"],
            self._tcinputs["password"]
        )
        self.webconsole_2.goto_reports()
        self.report_home_page_2 = ReportsHomePage(self.webconsole_2)

    @test_step
    def custom_column_search_non_admin(self, visibility):
        """ Verifies column search on custom report as a non admin user. """
        if visibility:
            error_msg = ("Custom column search FAILED for the keyword '{0}', "
                         "Since shared report does not come under search result '{1}'.")
            self.browser_2.driver.refresh()
            self.webconsole_2.wait_till_load_complete(overlay_check=True)
        else:
            error_msg = ("Custom column search FAILED for the keyword '{0}', " 
                         "Since unshared report comes under search result '{1}'.")

        self.report_home_page_2.advanced_search_by_column(self.search["CUSTOM_COLUMN_KEYWORD"])
        if self.report_home_page_2.is_advanced_search_report_exists(
                self.search["CUSTOM_COLUMN_REPORT"]) is not visibility:
            raise CVTestStepFailure(
                error_msg.format(
                    self.search["CUSTOM_COLUMN_KEYWORD"],
                    self.search["CUSTOM_COLUMN_REPORT"]
                )
            )

    @test_step
    def share_report(self):
        """ Shares the report to the non admin user."""
        self.report_home_page.goto_report(self.search["CUSTOM_COLUMN_REPORT"])
        security = self.report.open_security()
        security.associate_security_permission(users=[self._tcinputs["report_management_user"]])
        security.update()

    def cleanup(self):
        """ De-associates the user. """
        security = self.report.open_security()
        if security.is_user_associated(self._tcinputs["report_management_user"]):
            security.deassociate_user(self._tcinputs["report_management_user"])
            security.update()
        else:
            security.cancel()

    def unshare_report(self):
        """Unshare the report"""
        self.report_home_page.goto_report(self.search["CUSTOM_COLUMN_REPORT"])
        self.cleanup()

    def run(self):
        try:
            self.init_tc()
            self.verify_metrics_content_search()
            self.verify_metrics_column_search()
            self.verify_custom_content_search()
            self.verify_custom_column_search()
            self.login_as_non_admin_user()
            self.custom_column_search_non_admin(False)
            self.share_report()
            self.custom_column_search_non_admin(True)
            self.cleanup()

        except Exception as err:
            self.utils.handle_testcase_exception(err)

        finally:
            WebConsole.logout_silently(self.webconsole)
            WebConsole.logout_silently(self.webconsole_2)
            Browser.close_silently(self.browser)
            Browser.close_silently(self.browser_2)
