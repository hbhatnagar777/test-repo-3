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
    __init__()                --  initialize TestCase class

    init_tc()                 --  Initial configuration for the test case
    set_http_settings()            -- enable http settings
    validate_private_uploadnow()   -- metrics upload
    verify_logs()                  -- verify http proxy is used by reading the cs logs
    run()                          --  run function of this test case

Input Example:

    "testCases":
            {
                "48734":
                        {
                            "HttpProxyHost": "http proxy server"
                            "HttpProxyPort": "http proxy port"
                        }
            }


"""
import os
import datetime
import requests
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestStepFailure
from cvpysdk.metricsreport import CloudMetrics
from cvpysdk.internetoptions import InternetOptions
from requests.exceptions import ConnectionError

_CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """TestCase to validate Metrics collection with http proxy"""

    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Metrics collection with http proxy"
        self.public_metrics = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "HttpProxyHost": None,
            "HttpProxyPort": None
        }
        self.cre_api = None
        self.http_proxy = None
        self.http_proxy_port = None
        self.cs_machine = None
        self.uploadnow_start_time = None
        self.internet = None

    def init_tc(self):
        """Initializes Private metrics object required for this test case"""
        self.public_metrics = CloudMetrics(self.commcell)
        self.http_proxy = self.tcinputs['HttpProxyHost']
        self.http_proxy_port = self.tcinputs['HttpProxyPort']
        self.internet = InternetOptions(self.commcell)
        self.internet.set_http_proxy(self.http_proxy, self.http_proxy_port)
        self.cs_machine = Machine(self.commcell.commserv_name, self.commcell)

    @test_step
    def verify_http_Proxy(self):
        """verifies if http proxy server is running"""
        http_proxy_website = "http://" + self.http_proxy + ":" + self.http_proxy_port + "/"
        try:
            requests.get(http_proxy_website)
        except ConnectionError:
            raise CVTestStepFailure(f"http proxy is not running. Please check the proxy.")

    @test_step
    def initiate_public_uploadnow(self):
        """Validates public uploadNow operation """
        self.log.info('Initiating public Metrics upload now')
        self.public_metrics.upload_now()
        self.public_metrics.wait_for_uploadnow_completion()
        self.log.info('Cloud Metrics upload now completed Successfully')


    @test_step
    def verify_logs(self):
        """verify proxy is used by reading the log file"""
        log_dir = self.cs_machine.join_path(self.commcell.commserv_client.log_directory,
                                            "CommservSurveyUtility.log")
        file_content = self.cs_machine.read_file(log_dir)
        proxy_log_line = "Public: Using HTTP Proxy. Proxy Server [" + self.http_proxy + "]"
        start_pos = file_content.find(self.uploadnow_start_time)
        if proxy_log_line not in file_content[start_pos:]:
            raise CVTestStepFailure(
                f"Http proxy  [{self.http_proxy}] is not used for the metrics upload"
            )

    def run(self):
        try:
            self.init_tc()
            self.verify_http_Proxy()
            self.uploadnow_start_time = datetime.datetime.now().strftime("%m/%d %H:%M")
            self.log.info('upload now start time: ' + self.uploadnow_start_time)
            self.initiate_public_uploadnow()
            self.verify_logs()
        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            self.internet.disable_http_proxy()
