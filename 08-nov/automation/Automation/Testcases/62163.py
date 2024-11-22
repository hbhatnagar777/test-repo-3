# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Verify LocalMetrics from the Command Center"""

from datetime import datetime, timedelta
import time

from AutomationUtils.cvtestcase import CVTestCase

from Web.AdminConsole.adminconsole import AdminConsole

from Web.AdminConsole.Reports.metrics_reporting import LocalMetricsReporting

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

from Web.WebConsole.webconsole import WebConsole

from Reports.utils import TestCaseUtils

from cvpysdk.metricsreport import LocalMetrics


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "LocalMetrics reporting validation"
        self.utils = TestCaseUtils(self)
        self.metrics_server = None
        self.browser: Browser = None
        self.admin_console = None
        self.local_metrics = None

    def init_tc(self):
        """ initialization for testcase """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.utils.webconsole = webconsole
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode['commcell']["commcellUsername"],
                self.inputJSONnode['commcell']["commcellPassword"]
            )
            self.utils = TestCaseUtils(self, self.inputJSONnode['commcell']["commcellUsername"],
                                       self.inputJSONnode['commcell']["commcellPassword"])
            navigator = self.admin_console.navigator
            navigator.navigate_to_metrics_reporting()
            self.local_metrics = LocalMetricsReporting(self.admin_console, 'Local metrics reporting')
            self.local_metrics.enable_local_metrics()

        except Exception as ex:
            raise CVTestCaseInitFailure(ex) from ex

    @test_step
    def verify_last_upload_time(self):
        """ validate last upload time is within last 24 hours"""
        local_metric = LocalMetrics(self.commcell)
        lastupload= local_metric.last_upload_time
        dtime = datetime.now() + timedelta(seconds=3)
        current_unixtime = time.mktime(dtime.timetuple())
        time_different = current_unixtime - lastupload
        if time_different > 86400:
            raise CVTestStepFailure(
                f"Metrics direct dip last collection time is more than 1 day. "
                f"No hours difference [{time_different/3600}] hours"
            )
        self.log.info("Last upload time is less than 1day")

    @test_step
    def validate_local_metrics_queries(self):
        """ validates the metrics local metrics collection queries from the database"""
        query = "SELECT count(*) from cf_CommservSurveyQueries where (flags & 1024) = 1024"
        response = self.utils.cre_api.execute_sql(query, database_name='Cvcloud')
        if response[0][0] != 130:
            raise CVTestStepFailure(f"Expected total number of queries 125 but received {response[0][0]}")
        self.local_metrics.disable_local_metrics()

    @test_step
    def validate_health_only_query(self):
        """validate health collection queries from the database"""
        query = "SELECT count(*) from cf_CommservSurveyQueries where (flags & 1024) = 1024"
        response = self.utils.cre_api.execute_sql(query, database_name='Cvcloud')
        if response[0][0] != 94:
            raise CVTestStepFailure(f"Expected total number of queries 89 but received {response[0][0]}")

    @test_step
    def verify_local_metrics_enabled(self):
        """verify the local metrics is enabled properly"""
        self.local_metrics.enable_local_metrics()
        self.log.info("Enable the local metrics option from Command Center")
        self.validate_local_metrics_queries()
        self.log.info("Local metrics is enabled successfully")

    def run(self):
        """run method"""
        try:
            self.init_tc()
            self.verify_last_upload_time()
            self.validate_local_metrics_queries()
            self.validate_health_only_query()
            self.verify_local_metrics_enabled()

        except Exception as ex:
            self.utils.handle_testcase_exception(ex)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
