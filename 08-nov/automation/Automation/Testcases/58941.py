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
    run_send_log()            -- To run sendLogs job
    verify_scrub_logs()       -- verify that client name, ip address, paths are scrubbed in cvd.log
    verify_scrub_database_logs()    -- verify that scrubbed database is cllected
    get_clientid()            -- fetches the client id of a client
    run()                     --  run function of this test case

Input Example:

    "testCases":
            {
                "58941":
                        {
                            "windows_client": "WindowsClientName"
                        }
            }


"""
import time
import os
import re
import datetime
from math import floor
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from cvpysdk.license import LicenseDetails
from Reports.SendLog.utils import SendLogUtils
from Reports.utils import TestCaseUtils
from Web.Common.page_object import handle_testcase_exception
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Commcell import Commcell
from Web.AdminConsole.AdminConsolePages.send_logs import SendLogs
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.AdminConsole.FileServerPages.file_servers import FileServers

_STORE_CONFIG = get_config()


def has_seperators_around(text, client_name):
    pattern = r'(^|\W)' + re.escape(client_name) + r'($|\W)'
    match = re.match(pattern, text)
    return bool(match)


def get_ip_pattern():
    ipv4_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    ipv6_pattern = r'\b(?:[0-9a-fA-F]{0,4}:){7}[0-9a-fA-F]{0,4}\b'
    combined_ip_pattern = ipv4_pattern + '|' + ipv6_pattern
    return combined_ip_pattern


class TestCase(CVTestCase):
    """Sendlogs: verify sendlogs with scrub logfiles option"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.browser = None
        self.admin_console = None
        self.send_log = None
        self.jobid = None
        self.jobid_list = []
        self.utils = None
        self.commcell_id = None
        self.commcell_name = None
        self.machine = None
        self.path = None
        self.utils = TestCaseUtils(self)
        self.utils.reset_temp_dir()
        self.send_log_utils = None
        self.commserv_client = None
        self.windows_client = None
        self.file_server = None
        self.name = "Sendlogs: verify sendlogs with scrub logfiles option"
        self.cs_job_duration = None
        self.client_job_duration = None
        self.commserv_machine = None

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        try:
            self.log.info("Initializing pre-requisites")
            self.log.info('Connecting to local machine wait for 1 min')
            self.commserv_client = self.commcell.commserv_client
            self.machine = Machine()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])
            self.send_log_utils = SendLogUtils(self, self.machine)
            navigator = self.admin_console.navigator
            navigator.navigate_to_commcell()
            licence = LicenseDetails(self.commcell)
            self.commcell_id = licence.commcell_id_hex
            self.commcell_name = self.commcell.commserv_name
            self.windows_client = self.tcinputs['windows_client']
            self.commserv_machine = Machine(self.commserv_client)
            self.file_server = FileServers(self.admin_console)
            self.send_log = SendLogs(self.admin_console)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def verify_scrub_time(self):
        """verify time taken by scrubbing """
        log_file = self.commserv_machine.join_path(self.commserv_client.log_directory, "sendLogFiles.log")
        self.log.info(f'Opening log file {log_file}')
        expected_pattern = self.jobid + " bundleLogs() - Create scrubbing folder"
        log_content = self.commserv_machine.read_file(log_file)
        last_match_index = log_content.rfind(expected_pattern)
        if last_match_index >= 0:
            scrub_log_start_timestamp = log_content[last_match_index - 15:last_match_index - 1]
        else:
            raise CVTestStepFailure(
                f"scrubbing start log line not found"
            )
        if "windows" in self.commserv_machine.os_info.lower():
            expected_pattern = self.jobid + " Win7ZWrapper::buildCommandLine() - Command string"
        else:
            expected_pattern = self.jobid + " bundleLogs() - Remove directory"
        last_match_index = log_content.rfind(expected_pattern)
        if last_match_index >= 0:
            scrub_log_end_timestamp = log_content[last_match_index - 15:last_match_index - 1]
        else:
            raise CVTestStepFailure(
                f"scrubbing end log line not found"
            )
        time_diff = round((datetime.datetime.strptime(scrub_log_end_timestamp, "%m/%d %H:%M:%S") -
                           datetime.datetime.strptime(scrub_log_start_timestamp,
                                                      "%m/%d %H:%M:%S")).total_seconds() / 60, 1)
        self.log.info(
            f" Scrub start time [{scrub_log_start_timestamp}] end time [{scrub_log_end_timestamp}],"
            f" total duration(minutes) [{time_diff}]")

        if floor(time_diff) > 10:
            raise CVTestStepFailure(
                f"Scrubbing in the job [{self.jobid}]  took more than 10 minutes. Duration [{time_diff}] minutes."
            )

    @test_step
    def run_send_log(self, client=False):
        """Running SendLog job"""
        if client:
            self.admin_console.navigator.navigate_to_file_servers()
            self.admin_console.wait_for_completion()
            self.file_server.action_sendlogs(self.windows_client)
        else:
            comm_cell = Commcell(self.admin_console)
            comm_cell.access_sendlogs()

        information_list = self.send_log.Informationlist
        self.send_log.select_information(information_list=[information_list.LOGS])
        if not client:
            self.send_log.select_information(information_list=[information_list.CSDB, information_list.LATEST_DB])
        self.send_log.deselect_information(information_list=[information_list.OS_LOGS,
                                                             information_list.MACHINE_CONFIG,
                                                             information_list.ALL_USERS_PROFILE])
        advanced_list = self.send_log.Advancedlist
        self.send_log.select_advanced(advanced_list=[advanced_list.SCRUB_LOGFILES])
        self.jobid = self.send_log.submit()
        start_time = time.time()
        job_obj = self.commcell.job_controller.get(self.jobid)
        job_status = job_obj.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure(
                f"Send log job id [{self.jobid}] failed"
            )
        end_time = time.time()
        if client:
            self.client_job_duration = round((end_time - start_time) / 60, 1)
            self.log.info(f"Client's sendlog job took {self.client_job_duration} minutes")
            if floor(self.client_job_duration) > 10:
                raise CVTestStepFailure(
                    f"Send log job [{self.jobid}] for client took more than 10 minutes."
                    f"Duration [{self.client_job_duration}] minutes."
                )
        else:
            self.verify_scrub_time()

    @test_step
    def verify_scrub_logs(self, client_id, is_cs=True):
        """Verifying that client name, ip address and paths are scrubbed """
        self.log.info(
            "Verifying scrbbing in logs: cvd.log ")
        self.path = self.send_log_utils.get_uncompressed_path(str(self.jobid))
        client_dir = "Masked_Clientname_" + str(client_id)
        self.path = os.path.join(self.path, client_dir)
        self.log.info("Output location " + self.path)
        CS_name_exists = False
        windows_client_name_exists = False
        ip_exists = False
        path_exists = False
        with open(os.path.join(self.path, 'CVD.log'), errors="ignore") as cvd_log:
            lines = cvd_log.readlines()
            for text in lines:
                if self.commcell_name in text:
                    if has_seperators_around(text, self.commcell_name):
                        CS_name_exists = True
                if not is_cs:
                    if self.windows_client in text:
                        if has_seperators_around(text, self.windows_client):
                            windows_client_name_exists = True
                ip_pattern = get_ip_pattern()
                ip_exists = re.findall(ip_pattern, text)
                if is_cs:
                    path_exists = re.findall(r'^[a-zA-Z]:(\\.*)$', text)
                if CS_name_exists or ip_exists or path_exists or windows_client_name_exists:
                    self.log.info(text)
                    break
        if CS_name_exists:
            raise CVTestStepFailure(
                f"Commserv name  [{self.commcell_name}] is not scrubbed"
            )
        if ip_exists:
            raise CVTestStepFailure(
                f"IP Address is not scrubbed"
            )
        if path_exists:
            raise CVTestStepFailure(
                f"File path is not scrubbed"
            )
        if windows_client_name_exists:
            raise CVTestStepFailure(
                f"Client name  [{self.windows_client}] is not scrubbed"
            )

    @test_step
    def verify_scrub_database_logs(self):
        """Verifies that scrubbed database is collected successfully"""
        self.path = self.send_log_utils.get_uncompressed_path(str(self.jobid))
        file_list = self.machine.get_files_in_path(self.path, recurse=False)
        for file in file_list:
            if 'Masked_Commserv.bak' in file:
                db_file_size = self.machine.get_file_size(file)
                if db_file_size > 1:
                    self.log.info("Scrubbed Database dump is collected succesfully")
                    return True
                else:
                    raise CVTestStepFailure(
                        f"Scrubbed database dump is collected with less size. Please check sendlogFiles.log"
                        f"for {self.jobid} for further analysis"
                    )
        raise CVTestStepFailure(
            f"Scrubbed database dump was not collected for {self.jobid}. Please check sendLogFiles.log for "
            f"{self.jobid} for further analysis"
        )

    def get_clientid(self):
        """to get the clientId of the given client name"""
        return self.commcell.clients.get(self.windows_client).client_id

    def run(self):
        try:
            self.init_tc()
            self.send_log_utils.change_http_setting()
            self.run_send_log()
            self.log.info('Waiting for 20 minutes to check file present at ' +
                          _STORE_CONFIG.Reports.uncompressed_logs_path +
                          'location for send log job id ' + self.jobid)
            AdminConsole.logout_silently(self.admin_console)
            time.sleep(1200)
            self.verify_scrub_logs(2)
            self.verify_scrub_database_logs()
            '''need to login again as there is time delay'''
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])
            self.log.info('Running senlogs for the Windows Client ' + self.windows_client)
            self.run_send_log(client=True)
            self.log.info('Waiting for 15 minutes to check file present at ' +
                          _STORE_CONFIG.Reports.uncompressed_logs_path +
                          'location for send log job id ' + self.jobid)
            time.sleep(900)
            client_id = self.get_clientid()
            self.log.info(f"Client id is {client_id} ")
            self.verify_scrub_logs(client_id, False)
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
