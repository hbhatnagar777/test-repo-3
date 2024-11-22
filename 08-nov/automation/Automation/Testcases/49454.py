# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
#

""""
TestCase to validate Instant Refresh feature in cloud metrics dashboard.
"""
from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config

from Reports.utils import TestCaseUtils

from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator
from Web.WebConsole.Reports.Metrics.dashboard import Dashboard

from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.exceptions import CVTestStepFailure

from cvpysdk.metricsreport import CloudMetrics
from cvpysdk.internetoptions import InternetOptions
from cvpysdk.client import Clients

_CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """TestCase to validate Instant Refresh feature in cloud metrics dashboard"""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics: instant Refresh feature"
        self.private_metrics = None
        self.browser = None
        self.webconsole = None
        self.dashboard = None
        self.cloud_metrics = None
        self.internet = None
        self.utils = TestCaseUtils(self)
        self.last_collection_time = None
        self.current_collection_time = None
        self.tcinputs = {
            "GatewayClientName": None,
        }
        self.gateway_enabled = False
        self.gateway_client = None
        self.config = config.get_config()
        self.cloud_metrics_server = self.config.Cloud

    def setup(self):
        """Initializes Private metrics object required for this test case"""
        self.cloud_metrics = CloudMetrics(self.commcell)
        self.last_collection_time = self.cloud_metrics.lastcollectiontime
        self.internet = InternetOptions(self.commcell)
        self.gateway_client = Clients(self.commcell).get(self.tcinputs["GatewayClientName"])
        self.internet.set_no_gateway()

    def init_tc(self):
        """Initialize the application to the state required by the testcase"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.cloud_metrics_server.host_name)
            self.webconsole.login(self.cloud_metrics_server.username, self.cloud_metrics_server.password)
            self.webconsole.goto_reports()
            Navigator(self.webconsole).goto_commcell_dashboard(self.commcell.commserv_name)
            self.dashboard = Dashboard(self.webconsole)
            if self.dashboard.is_commcell_active() is False:
                raise CVTestCaseInitFailure(
                    'Commcell [%s] is not active verify signalR connection',
                    self.commcell.commserv_name
                )
        except Exception as excep:
            raise CVTestCaseInitFailure(excep) from excep

    @test_step
    def perform_instant_refresh(self):
        """Performing Instant refresh operation"""
        self.dashboard.do_instant_refresh()
        sleep(5)
        self.webconsole.get_all_unread_notifications(
            expected_count=1,
            expected_notifications=[
                'Refresh request submitted. It will take a few minutes for the data to process'
            ]
        )

    def verify_upload_initiated(self):
        """Verify public upload is initiated in Commserve"""
        self.log.info('Waiting for 30 seconds')
        sleep(30)
        self.cloud_metrics.refresh()
        self.current_collection_time = self.cloud_metrics.lastcollectiontime
        if self.last_collection_time != 0:
            if self.current_collection_time != self.last_collection_time:
                self.log.info(
                    'Cloud upload initiated in Commserv [%s]', self.commcell.commserv_name
                )
                return True
            else:
                raise CVTestStepFailure(
                    'Cloud upload not initiated in Commserv [%s] after instant Refresh'
                )
        else:
            try:
                self.cloud_metrics.wait_for_download_completion()
                self.log.info(
                    'Cloud upload initiated in Commserv [%s]', self.commcell.commserv_name
                )
                return True
            except TimeoutError:
                raise CVTestStepFailure(
                    'Cloud upload not initiated in Commserv [%s] after instant Refresh'
                )

    def prepare(self):
        """Prepare setup for second design case"""
        self.log.info('Setting up internet Gateway client [%s]', self.gateway_client.client_name)
        self.internet.set_internet_gateway_client(self.gateway_client.client_name)
        self.cloud_metrics.wait_for_collection_completion()
        self.last_collection_time = self.cloud_metrics.lastcollectiontime
        self.webconsole.clear_all_notifications()
        self.gateway_enabled = True

    def run(self):
        try:
            self.init_tc()
            self.perform_instant_refresh()
            self.verify_upload_initiated()
            self.prepare()
            self.perform_instant_refresh()
            self.verify_upload_initiated()

        except Exception as error:
            if self.gateway_enabled:
                self.log.error('Failure with Gateway Enabled')
            self.utils.handle_testcase_exception(error)

        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Tear down function of this test case"""
        self.internet.set_no_gateway()
