# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Metrics direct dip collection validation"""

from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.report import MetricsReport

from Reports.utils import TestCaseUtils
from Reports.metricsutils import MetricsServer

from cvpysdk.metricsreport import PrivateMetrics


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics directdip validation"
        self.utils = TestCaseUtils(self)
        self.metrics_server = None
        self.browser: Browser = None
        self.webconsole: WebConsole = None
        self.navigator: Navigator = None

    def init_tc(self):
        try:
            self.metrics_server = MetricsServer(self.commcell.webconsole_hostname)
            query = "SELECT value FROM GxGlobalParam WHERE name ='CommservMetricsDirectDipEnabled'"
            response = self.utils.cre_api.execute_sql(query)
            if response[0][0] == '0':
                raise CVTestCaseInitFailure("Metrics direct dip is not enabled")
            metrics = PrivateMetrics(self.commcell)
            if self.commcell.webconsole_hostname in metrics.downloadurl:
                raise CVTestCaseInitFailure(
                    "Local download URL set for private metrics, direct dip wont be enabled."
                    " Use different CS or change URL"
                )
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    def init_webconsole(self):
        """initialize webconsole objects"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(
                self.browser,
                self.commcell.webconsole_hostname
            )
            self.webconsole.login()
            self.navigator = Navigator(self.webconsole)
        except Exception as e:
            raise CVTestCaseInitFailure(e) from e

    @test_step
    def validate_metrics_healthpage(self):
        """validate that health page is opening after direct dip colleciton"""
        self.init_webconsole()
        self.webconsole.goto_reports()
        self.navigator.goto_health_report()
        MetricsReport(self.webconsole).verify_page_load()

    @test_step
    def validate_metrics_directdip(self):
        """ validates the metrics direct dip collection time from the database"""

        query = "SELECT datediff(second, '01/01/1970', GetUTCdate()) - value " \
                "as lastCollection   from GxGlobalParam" \
                " WHERE name ='CommservMetricsDirectDipLastCollectionTime'"
        """ getting the number of seconds since last collection time w.r.t current time"""
        response = self.utils.cre_api.execute_sql(query)
        if not response:
            raise Exception("Metrics direct dip last collection time value not found")
        if response[0][0] > 86400:
            raise Exception(
                f"Metrics direct dip last collection time is more than 1 day. "
                f"No collection since [{response[0][0]}] seconds"
            )
        direct_dip_file_name = self.utils.get_direct_dip_filename()
        if self.metrics_server.is_file_in_archive(direct_dip_file_name):
            self.log.info("Direct dip file is present in archive folder")
        else:
            raise Exception(
                f"Direct dip collection file [{direct_dip_file_name}] not found in archive folder"
            )

    def run(self):
        try:
            self.init_tc()
            self.validate_metrics_directdip()
            self.validate_metrics_healthpage()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
