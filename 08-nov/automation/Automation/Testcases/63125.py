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
    __init__()                                          --  initialize TestCase class
    init_tc()                                           --  Initialize pre-requisites
    run_send_log()                                      -- run send log on a Client/CS
    verify_new_process_dump_for_cs()                    -- verifies the latest dump collection for CS
    verify_new_process_dump_for_client()                -- verifies the latest dump collection for client
    run()                                               --  run function of this test case

Input Example:

    "testCases":
            {
                "63125":
                        {
                            "ClientName":"C1",
                           "ProcessName" : "process",
                           "DumpInterval" : ""
                        }
            }


"""
import os
import time
from AutomationUtils.config import get_config
from Web.AdminConsole.AdminConsolePages.Commcell import Commcell
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.send_logs import SendLogs
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Reports.SendLog.utils import SendLogUtils
from cvpysdk.license import LicenseDetails
from AutomationUtils.machine import Machine

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Sendlogs with New Process Dumps"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type


        """
        super(TestCase, self).__init__()

        self.browser = None
        self.admin_console = None
        self.send_log = None
        self.jobid_list = []
        self.process_name = None
        self.process_id = None
        self.sjob_id1 = None
        self.sjob_id2 = None
        self.comm_cell = None
        self.cs_machine = None
        self.client_machine = None
        self.file_server = None
        self.path = None
        self.cs_path = None
        self.client_path = None
        self.commcell_name = None
        self.commcell_id = None
        self.local_machine = None
        self.navigator = None
        self.dump_interval = None
        self.send_log_utils = None
        self.commserv_client = None
        self.job_start_time_for_cs = None
        self.job_start_time_for_client = None
        self.name = "Verify New Process Dumps with Dump Interval"

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        try:
            self.log.info("Initializing pre-requisites")
            self.cs_client = self.commcell.commserv_client
            self.cs_machine = Machine(self.cs_client)
            self.client_machine = Machine(self.client)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])
            self.file_server = FileServers(self.admin_console)
            self.send_log = SendLogs(self.admin_console)
            licence = LicenseDetails(self.commcell)
            self.local_machine = Machine()
            self.comm_cell = Commcell(self.admin_console)
            self.commcell_name = self.commcell.commserv_name
            self.commcell_id = licence.commcell_id_hex
            self.send_log_utils = SendLogUtils(self, self.local_machine)
            self.process_name = self.tcinputs["ProcessName"]
            if "windows" in self.client_machine.os_info.lower():
                self.process_name += ".exe"
            self.process_id = self.client_machine.get_process_id(self.process_name)[0]
            self.dump_interval = int(self.tcinputs["DumpInterval"])

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def run_send_log(self, client=False):
        """Running sendlogs job for CS/client machine with two new dumps at dump interval with process name/id"""
        if client:
            self.admin_console.navigator.navigate_to_servers()
            self.admin_console.wait_for_completion()
            time.sleep(5)
            self.file_server.action_sendlogs(self.tcinputs["ClientName"])
        else:
            self.admin_console.navigator.navigate_to_commcell()
            self.comm_cell.access_sendlogs()
        info_list = self.send_log.Informationlist
        adv_list = self.send_log.Advancedlist
        self.send_log.deselect_information(information_list=[info_list.MACHINE_CONFIG, info_list.OS_LOGS,
                                                             info_list.ALL_USERS_PROFILE])
        self.send_log.select_advanced(advanced_list=[adv_list.NEW_PROCESS_DUMP, adv_list.MULTIPLE_DUMP])
        if client:
            self.send_log.add_process_id(self.process_id)
        else:
            self.send_log.add_process_name(self.tcinputs["ProcessName"])
        self.send_log.add_dump_interval(interval_time=self.dump_interval)
        if client:
            self.sjob_id2 = self.send_log.submit()
            job_obj = self.commcell.job_controller.get(self.sjob_id2)
            self.job_start_time_for_client = job_obj.start_timestamp
            job_status = job_obj.wait_for_completion()
            if not job_status:
                raise CVTestStepFailure(
                    f"Send log job id [{self.sjob_id2}] failed"
                )
        else:
            self.sjob_id1 = self.send_log.submit()
            job_obj = self.commcell.job_controller.get(self.sjob_id1)
            self.job_start_time_for_cs = job_obj.start_timestamp
            job_status = job_obj.wait_for_completion()
            if not job_status:
                raise CVTestStepFailure(
                    f"Send log job id [{self.sjob_id1}] failed"
                )

    @test_step
    def verify_new_process_dump_for_cs(self):
        """Verifying the new process dump collected on CS side with dump interval time"""
        if "windows" in self.cs_machine.os_info.lower():
            file_prefix = self.tcinputs["ProcessName"]
        else:
            file_prefix = f'cvsnapcore_{self.tcinputs["ProcessName"]}'
        file_modified_times = []
        file_list = self.local_machine.get_files_in_path(self.cs_path)
        self.log.info("New Process Dumps from CS Machine")
        for each_file in file_list:
            if file_prefix in each_file and (each_file.endswith('.dmp') or each_file.endswith('.tar.gz')):
                file_name = each_file.split('\\')[-1]  # Extract the file_name from the dump file path
                file_modified_time = os.path.getmtime(each_file)
                if file_modified_time > self.job_start_time_for_cs:
                    file_modified_times.append(file_modified_time)
                    self.log.info(file_name)

        if len(file_modified_times) == 2:
            first_dmp, second_dmp = file_modified_times
            duration_in_minutes = abs(first_dmp - second_dmp) // 60
            if abs(duration_in_minutes - self.dump_interval) <= 2: #Grace Time
                self.log.info(f"Both the dumps collected successfully in time interval : {self.dump_interval} minutes")
            else:
                raise CVTestStepFailure(
                    f"The dumps were not collected successfully in the time interval : {self.dump_interval} minutes"
                )
        else:
            raise CVTestStepFailure(
                f"There was a failure/issue in collecting the process dumps. Please refer sendLogFiles.log on CS for "
                f"sendlogs job id {self.sjob_id1} to debug."
            )

    @test_step
    def verify_new_process_dump_for_client(self):
        """Verifying the new process dump collected on client side with dump interval time"""
        if "windows" in self.client.os_info.lower():
            file_prefix = f"{self.tcinputs['ProcessName']}-{self.process_id}"
        else:
            file_prefix = "cvsnapcore"
        file_modified_times = []
        file_list = self.local_machine.get_files_in_path(self.client_path)
        self.log.info(f"New Process Dumps from Client Machine :{self.tcinputs['ClientName']} ")
        for each_file in file_list:
            if file_prefix in each_file and (each_file.endswith('.dmp') or each_file.endswith('tar.gz')):
                file_name = each_file.split('\\')[-1]
                file_modified_time = os.path.getmtime(each_file)
                if file_modified_time > self.job_start_time_for_client:
                    file_modified_times.append(file_modified_time)
                    self.log.info(file_name)

        if len(file_modified_times) == 2:
            first_dmp, second_dmp = file_modified_times
            duration_in_minutes = abs(first_dmp - second_dmp) // 60
            if abs(duration_in_minutes - self.dump_interval) <= 2: #Grace time
                self.log.info(f"Both the dumps collected successfully in time interval : {self.dump_interval} minutes")
            else:
                raise CVTestStepFailure(
                    f"The dumps were not collected successfully in the time interval : {self.dump_interval} minutes"
                )
        else:
            raise CVTestStepFailure(
                f"There was a failure/issue in collecting the required process dumps. Please refer sendLogFiles.log "
                f"on CS and cvd.log on client side for sendlogs job id : {self.sjob_id2} to debug."
            )

    def run(self):
        try:
            self.init_tc()
            self.run_send_log()
            self.run_send_log(client=True)
            self.log.info('Waiting for 25 minutes to check file present at location ' +
                          _STORE_CONFIG.Reports.uncompressed_logs_path
                          + ' for send log job id ' + self.sjob_id1 + ' and ' + self.sjob_id2)

            time.sleep(1500)
            self.cs_path = self.send_log_utils.get_uncompressed_path(self.sjob_id1, self.jobid_list)
            self.client_path = self.send_log_utils.get_uncompressed_path(self.sjob_id2, self.jobid_list)
            self.verify_new_process_dump_for_cs()
            self.verify_new_process_dump_for_client()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
