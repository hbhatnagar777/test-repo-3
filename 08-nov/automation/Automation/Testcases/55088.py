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
    __init__()                                            --  initialize TestCase class
    init_tc()                                             --  Initialize pre-requisites
    run_cloud_troubleshooting_send_log()                   -- method for run cloud troubleshoot
                                                              request
    check_troubleshoot_xml_exist()                         -- method for verify xml
    run()                                                 --  run function of this test case
Input Example:

    "testCases":
            {
                "55088":
                        {
                            EmailId : "",
                            WebConsoleHostName: "",
                            CommCellName  : "",
                            CommCellUserName  : "",
                            CommCellPassword  : "",
                            CommCellId    : ""
                        }
            }


"""
import time
from Web.Common.page_object import handle_testcase_exception
from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.Troubleshooting.troubleshoot import CloudSendLog
from Reports.metricsutils import MetricsServer
from Reports.SendLog.utils import SendLogUtils
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from cvpysdk.job import JobController
from cvpysdk.commcell import Commcell

CONSTANTS = get_config()


class TestCase(CVTestCase):
    """ remote troubleshooting from cloud """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

        """
        super(TestCase, self).__init__()
        self.name = "remote troubleshooting from cloud"
        self.browser = None
        self.web_console = None
        self.request_id = None
        self.metrics_server = None
        self.cloud_send_log = None
        self.send_log_utils = None
        self.machine = None
        self.tcinputs = {
            "EmailId": None,
            "CommCellName": None,
            "WebConsoleHostName": None,
            "CommCellUserName": None,
            "CommCellPassword": None,
            "CommCellId": None
        }
        self.job_controller = None
        self.commcell_object = None

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        try:
            self.log.info("Initializing pre-requisites")
            username = CONSTANTS.Cloud.username
            password = CONSTANTS.Cloud.password
            cloud_url = CONSTANTS.Cloud.host_name
            if not username or not password:
                self.log.info("Cloud username and password are not configured in config.json")
                raise Exception("Cloud username and password are not configured. Please update "
                                "the username and password details under "
                                "<Automation_Path>/CoreUtils/Templates/template-config.json")
            self.metrics_server = MetricsServer(cloud_url, username, password)
            self.machine = Machine()
            self.send_log_utils = SendLogUtils(self, self.machine)
            self.download_directory = self.send_log_utils.create_directory_for_given_path("TC55088")
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.web_console = WebConsole(self.browser, cloud_url)
            self.commcell_name = self.tcinputs["CommCellName"]
            self.wc_hostname = self.tcinputs["WebConsoleHostName"]
            self.email_id = self.tcinputs["EmailId"]
            self.commcell_user_name = self.tcinputs["CommCellUserName"]
            self.commcell_password = self.tcinputs["CommCellPassword"]
            self.commcell_id_hex = self.tcinputs["CommCellId"]
            self.commcell_object = Commcell(self.wc_hostname, self.commcell_user_name,
                                            self.commcell_password)
            self.job_controller = JobController(self.commcell_object)
            self.web_console.login(username, password)
            self.web_console.goto_commcell_dashboard()
            self.commcell_customer_name = self.metrics_server.get_commcell_customername(self.commcell_id_hex)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def run_cloud_troubleshooting_send_log(self):
        """
                Method to run cloud troubleshooting request for send logs send_log
        """
        self.cloud_send_log = CloudSendLog(self.web_console)
        self.cloud_send_log.access_commcell(self.commcell_name)
        self.cloud_send_log.click_troubleshooting_icon()
        self.cloud_send_log.close_popup()
        self.cloud_send_log.select_email_notification(True, [self.email_id])
        self.cloud_send_log.submit()
        if self.cloud_send_log.is_request_submit_success() is False:
            raise CVTestStepFailure("Cloud troubleshooting request for send log  get failed ")
        self.log.info('Send Log  request submitted from cloud')

    @test_step
    def check_troubleshoot_xml_exist(self):
        """check request xml created in Troubleshoot directory"""
        self.log.info('Wait for 30 seconds for xml creation in script folder')
        time.sleep(30)
        self.request_id = self.send_log_utils.get_request_id()
        status, url_paths = self.metrics_server.check_troubleshooting_xml_exists(self.request_id, self.commcell_id_hex)
        if status:
            self.log.info(f"Remote Troubleshooting xmls exist on {url_paths}")
        else:
            raise CVTestStepFailure(
                f"Remote troubleshooting xmls don't exist on {url_paths}"
            )

    @test_step
    def wait_for_jobcompletion(self):
        """wait for job completion"""
        all_jobs_dict = self.job_controller.active_jobs()
        jobs = []
        for job_id, props in all_jobs_dict.items():
            if props['job_type'] == 'Send Log Files':
                jobs.append(job_id)
        last_job = max(jobs)
        job_obj = self.job_controller.get(last_job)
        self.log.info('Waiting for send logs job ' + str(last_job) + ' completion')
        job_obj.wait_for_completion()

    @test_step
    def verify_email(self):
        """verify remote troubleshooting email"""
        retries = 1
        while retries <= 4:
            self.log.info(f'Waiting for 15 minutes to check completion email'
                          f' for send logs request'
                          f' {self.request_id}')
            time.sleep(900)
            subject = "Gather Log Request for [ " + self.commcell_name + "-" + \
                      self.commcell_customer_name + " ] - CommCell ID: [" + \
                      self.commcell_id_hex + "] [Request# " \
                      + str(self.request_id) + "] completed"
            retries = retries + 1
            try:
                self.send_log_utils.verify_email(self.download_directory, subject)
                break
            except Exception as exp:
                if retries == 4:
                    raise
                else:
                    pass

    def run(self):
        try:
            self.init_tc()
            self.run_cloud_troubleshooting_send_log()
            self.check_troubleshoot_xml_exist()
            self.wait_for_jobcompletion()
            WebConsole.logout_silently(self.web_console)
            self.verify_email()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            Browser.close_silently(self.browser)
