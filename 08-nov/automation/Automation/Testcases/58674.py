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
    __init__()                                    --  initialize TestCase class
    init_tc()                                     --  Initialize pre-requisites
    run_cloud_troubleshooting_send_log()          --  method for run cloud troubleshoot request
    is_index_file_exists()                        --  method that verifies the index file in titan
    verify_email_filter()
    run()                                         --  run function of this test case
Input Example:

    "testCases":
            {
                "58674":
                        {
                           "EmailId": "your_email_id@commvault.com",
                           "ClientWithWindowsMA": "client_test1",
                           "ClientWithLinuxMA": "client_test2",
                           "ClientWithSubclientLevelIndex": "client_test3",
                           "SubclientName": "subclient name",
                           "VMClient": "vm client",
                           "LogsPath": None,
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
from Web.API.customreports import CustomReportsAPI
from Reports.utils import TestCaseUtils
from Reports.metricsutils import MetricsServer
from Reports.SendLog.utils import SendLogUtils
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from cvpysdk.commcell import Commcell
from cvpysdk.job import JobController

CONSTANTS = get_config()

class TestCase(CVTestCase):
    """ Sendlogs with Index upload """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

        """
        super(TestCase, self).__init__()
        self.name = "Sendlogs with Index upload"
        self.browser = None
        self.web_console = None
        self.metrics_server = None
        self.request_id = None
        self.metrics_server = None
        self.cloud_send_log = None
        self.tcinputs = {
            "EmailId": None,
            "ClientWithWindowsMA": None,
            "ClientWithLinuxMA": None,
            "ClientWithSubclientLevelIndex": None,
            "SubclientName": None,
            "VMClient": None,
            "LogsPath": None
        }
        self.client_windows_ma = None
        self.client_linux_ma = None
        self.backupset_guid1 = None
        self.backupset_guid2 = None
        self.backupset_guid3 = None
        self.subclient_guid = None
        self.subclient_name = None
        self.sendlog_vm_client = None
        self.client_subclient_index = None
        self.send_log_utils = None
        self.machine = None
        self.job_id = None
        self.logs_path = None
        self.commcell_id_hex = None
        self.email_id = None
        self.download_directory = None
        self.commcell_name = None
        self.commcell_user_name = None
        self.commcell_password = None
        self.commcell_object = None
        self.utils = TestCaseUtils(self)
        self.cre_api = None
        self.job_controller = None

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        try:
            self.log.info("Initializing pre-requisites")
            username = CONSTANTS.Cloud.username
            password = CONSTANTS.Cloud.password
            cloud_url = CONSTANTS.Cloud.host_name
            self.machine = Machine()
            self.client_windows_ma = self.tcinputs["ClientWithWindowsMA"]
            self.client_linux_ma = self.tcinputs["ClientWithLinuxMA"]
            self.client_subclient_index = self.tcinputs["ClientWithSubclientLevelIndex"]
            self.subclient_name = self.tcinputs["SubclientName"]
            self.sendlog_vm_client = self.tcinputs["VMClient"]
            self.commcell_name = self.tcinputs["CommCellName"]
            self.logs_path = self.tcinputs["LogsPath"]
            self.email_id = self.tcinputs["EmailId"]
            self.commcell_user_name = self.tcinputs["CommCellUserName"]
            self.commcell_password = self.tcinputs["CommCellPassword"]
            self.commcell_id_hex = self.tcinputs["CommCellId"]
            self.commcell_object = Commcell(self.commcell_name, self.commcell_user_name,
                                            self.commcell_password)
            self.job_controller = JobController(self.commcell_object)
            if not username or not password:
                self.log.info("Cloud username and password are not configured in config.json")
                raise Exception("Cloud username and password are not configured. Please update "
                                "the username and password details under "
                                "<Automation_Path>/CoreUtils/Templates/template-config.json")
            self.metrics_server = MetricsServer(cloud_url, username, password)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.web_console = WebConsole(self.browser, cloud_url)
            self.web_console.login(username, password)
            self.web_console.goto_troubleshooting()
            self.send_log_utils = SendLogUtils(self, self.machine)
            self.download_directory = self.send_log_utils.create_directory_for_given_path("TC58674")

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def init_backupset_guids(self):
        """
        read backup set guid from the database
        """
        self.webconsole = WebConsole(
            self.browser, self.commcell_name, self.commcell_user_name, self.commcell_password)
        self.webconsole.login()
        self.cre_api = CustomReportsAPI(self.commcell_name)
        query = r"select distinct BS.GUID from APP_Client C with(nolock) " \
                "inner join app_application A with(nolock) " \
                "on C.id = A.clientid and A.apptypeid = 33 " \
                "and A.subclientStatus & 8 = 0 " \
                "inner join APP_BackupSetName BS with(nolock) " \
                "on A.backupSet = BS.id and BS.status & 8 = 8 " \
                " where C.name = '" + self.client_windows_ma + "'"

        response = self.cre_api.execute_sql(query)
        if not response:
            raise CVTestStepFailure(
                "Retreiving Backupset set guid from Database failed"
            )
        self.backupset_guid1 = response[0][0]

        query = r"select distinct BS.GUID from APP_Client C with(nolock) " \
                "inner join app_application A with(nolock) " \
                "on C.id = A.clientid and A.apptypeid = 33 " \
                "and A.subclientStatus & 8 =0 " \
                "inner join APP_BackupSetName BS with(nolock) " \
                "on A.backupSet = BS.id and BS.status & 8 = 8 " \
                " where C.name = '" + self.client_linux_ma + "'"

        response = self.cre_api.execute_sql(query)
        if not response:
            raise CVTestStepFailure(
                "Retreiving Backupset set guid from Database failed"
            )
        self.backupset_guid2 = response[0][0]

        query = r"select distinct BS.GUID from APP_Client C with(nolock) " \
                "inner join app_application A with(nolock) " \
                "on C.id = A.clientid and A.apptypeid = 106 " \
                "inner join APP_BackupSetName BS with(nolock) " \
                "on A.backupSet = BS.id  " \
                " where C.name = '" + self.sendlog_vm_client + "'"

        response = self.cre_api.execute_sql(query)
        if not response:
            raise CVTestStepFailure(
                "Retreiving Backupset set guid for vm client failed"
            )
        self.backupset_guid3 = response[0][0]

        query = r"select distinct A.GUID from APP_Client C with(nolock) " \
                "inner join app_application A with(nolock) " \
                "on C.id = A.clientid and A.apptypeid = 33 " \
                " where C.name = '" + self.client_subclient_index + "'" \
                " and A.subclientName = '" + self.subclient_name + "'"

        response = self.cre_api.execute_sql(query)
        if not response:
            raise CVTestStepFailure(
                "Retreiving subclient  guid for client failed"
            )
        self.subclient_guid = response[0][0]

    @test_step
    def run_cloud_troubleshooting_send_log(self):
        """
                Method to run cloud troubleshooting request for send logs send_log
        """
        self.cloud_send_log = CloudSendLog(self.web_console)
        self.cloud_send_log.access_commcell(self.commcell_name)
        self.cloud_send_log.close_popup()
        self.cloud_send_log.select_computer_information([self.client_windows_ma,
                                                         self.client_linux_ma,
                                                         self.client_subclient_index])
        self.cloud_send_log.select_pseudo_clients_vms([self.sendlog_vm_client])
        self.cloud_send_log.select_email_notification(True, [self.email_id])
        self.cloud_send_log.select_index()
        self.cloud_send_log.submit()
        if self.cloud_send_log.is_request_submit_success() is False:
            raise CVTestStepFailure("Cloud troubleshooting request for send log failed ")
        self.log.info('Send Log request submitted from cloud')

    def change_http_setting(self, http_site):
        """
            Modify send logs http site in GxGlobalParam
        """
        self.log.info('Changing the http site to ' + http_site)
        self.commcell.add_additional_setting(category='CommServDB.GxGlobalParam',
                                             key_name='SendLogsCurrentHTTPSite',
                                             data_type='STRING',
                                             value=http_site)

    def run(self):
        try:
            self.init_tc()
            http_url = 'https://' + CONSTANTS.Reports.SENDLOGS_HTTP_UPLOAD + '/webconsole'
            self.change_http_setting(http_url)
            self.run_cloud_troubleshooting_send_log()
            self.log.info('Wait 1 minute for xml creation in script folder')
            time.sleep(60)
            self.request_id = self.send_log_utils.get_request_id()
            WebConsole.logout_silently(self.web_console)
            self.init_backupset_guids()
            all_jobs_dict = self.job_controller.active_jobs()
            jobs = []
            for job_id, props in all_jobs_dict.items():
                if props['job_type'] == 'Send Log Files':
                    jobs.append(job_id)
            last_job = max(jobs)
            job_obj = self.job_controller.get(last_job)
            self.log.info('Waiting for send logs job ' + str(last_job) + ' completion')
            job_obj.wait_for_completion()
            self.logs_path = self.send_log_utils.get_uncompressed_path(str(last_job))
            self.send_log_utils.is_index_file_exists(self.logs_path,
                                                     self.client_windows_ma,
                                                     self.backupset_guid1)
            self.send_log_utils.is_index_file_exists(self.logs_path,
                                                     self.client_linux_ma,
                                                     self.backupset_guid2)
            self.send_log_utils.is_index_file_exists(self.logs_path,
                                                     self.sendlog_vm_client,
                                                     self.backupset_guid3)
            self.send_log_utils.is_index_file_exists(self.logs_path,
                                                     self.client_subclient_index,
                                                     self.subclient_guid)
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:

            WebConsole.logout_silently(self.web_console)
            Browser.close_silently(self.browser)
