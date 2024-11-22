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
    run_send_log()                                        --  run send log
    _verify_dump()                                        --  check dmp file exist or not
    verify_dr_dump()                                      --  verify comm serve database in side send log bundle
    files_not_found()                                     -- provides the list of files not found in the bundle
    verify_process_dump()                                 --  verify if process dump is collected
    verify_DB_logs()                                      --  verify SQL error logs
    run()                                                 --  run function of this test case

Input Example:

    "testCases":
            {
                "57820": {}
            }

"""
from AutomationUtils.machine import Machine
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Commcell import Commcell
from Web.AdminConsole.AdminConsolePages.send_logs import SendLogs
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Reports.SendLog.utils import SendLogUtils
from cvpysdk.license import LicenseDetails
from datetime import datetime
import os
import time
import re

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for executing Test Case: Send logs: Verify DR Dumps"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case


        """
        super(TestCase, self).__init__()
        self.browser = None
        self.admin_console = None
        self.job_id = None
        self.local_machine = None
        self.cs_machine = None
        self.path = None
        self.directory = None
        self.send_log_utils = None
        self.navigator = None
        self.commserv_client = None
        self.instance = None
        self.commcell_id = None
        self.commcell_name = None
        self.job_start_time = None
        self.process_id = None
        self.process_name = None
        self.dump_path = None
        self.dump_fullpath = None
        self.base_path = None
        self.pattern = (
            r'.*-(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})(?:-(\d{2})-(AM|PM))?\.dmp'
            r'|.*_.*_(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_FULL\.dmp'
        )
        self.jobid_list = []
        self.name = "Sendlogs: Verify DR Dumps"

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        try:
            self.log.info("Initializing pre-requisites")
            self.commserv_client = self.commcell.commserv_client
            self.commcell_name = self.commcell.commserv_name
            self.instance = self.commserv_client.instance
            self.local_machine = Machine()
            self.cs_machine = Machine(self.commserv_client)
            self.send_log_utils = SendLogUtils(self, self.local_machine)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_commcell()
            licence = LicenseDetails(self.commcell)
            self.commcell_id = licence.commcell_id_hex
            self.process_name = "cvd" + (".exe" if "windows" in self.commserv_client.os_info.lower() else "")

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def run_send_log(self, job_type=None):
        """Running SendLog job"""
        if job_type == 'db_dumps':
            self.process_id = self.cs_machine.get_process_id(self.process_name)[0]
            self.dump_path = self.cs_machine.get_registry_value('EventManager', 'dEVLOGDIR')
            self.dump_fullpath = self.cs_machine.get_process_dump(self.process_id, dump_path=self.dump_path)
        comm_cell = Commcell(self.admin_console)
        comm_cell.access_sendlogs()
        send_log = SendLogs(self.admin_console)
        advanced_list = send_log.Advancedlist
        send_log.deselect_advanced(advanced_list=[advanced_list.SCRUB_LOGFILES])
        info_list = send_log.Informationlist
        send_log.select_information(information_list=[info_list.CSDB, info_list.OTHER_DB,
                                                      info_list.LOGS])
        send_log.deselect_information(information_list=[info_list.OS_LOGS, info_list.MACHINE_CONFIG,
                                                        info_list.ALL_USERS_PROFILE])
        if job_type == 'db_dumps':
            send_log.select_advanced(advanced_list=[advanced_list.PROC_DUMP])
        if job_type == 'latest_db_dumps':
            send_log.select_information(information_list=[info_list.LATEST_DB])

        self.job_id = send_log.submit()
        job_obj = self.commcell.job_controller.get(self.job_id)
        self.job_start_time = job_obj.start_timestamp
        job_status = job_obj.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure(
                f"Send log job id [{self.job_id}] failed"
            )

    def _get_timestamp_from_file(self,filename):
        match = re.match(self.pattern, filename)
        if match:
            if match.group(1):  # This indicates the first pattern matched
                year, month, day, hour, minute, second, period = match.group(1, 2, 3, 4, 5, 6, 7)
                year, month, day, hour, minute = map(int, [year, month, day, hour, minute])
                second = int(second) if second else 0
                if period == 'PM' and hour != 12:
                    hour += 12
                elif period == 'AM' and hour == 12:
                    hour = 0
            else:  # This indicates the second pattern matched
                year, month, day, hour, minute = map(int, match.group(8, 9, 10, 11, 12))
                second = 0  # No seconds in this pattern

            dt = datetime(year, month, day, hour, minute, second)
            epoch_timestamp = int(dt.timestamp())
            return epoch_timestamp

        raise CVTestStepFailure(
            f"Couldn't parse the filename {filename} to fetch the timestamp"
        )

    def _verify_database_dump(self, files_dict, file_list, file_extension, job_type=None):
        """
                Method to check database dump files exist or not
       """
        for file_prefix in files_dict.keys():
            for file_var in file_list:
                if file_prefix.lower() in file_var.lower() and file_extension in file_var:
                    files_dict[file_prefix] = True
                    self.log.info(f"[{file_var}]  present at location [{self.base_path}]")
                    filename = os.path.basename(file_var)
                    birth_time = self._get_timestamp_from_file(filename)
                    modified_time = os.path.getmtime(file_var)
                    self.log.info(f"Birth Time: {birth_time} Job Start Time: {self.job_start_time} ")
                    if job_type == "db_dumps":
                        if self.job_start_time < birth_time:
                            raise CVTestStepFailure(f"Existing Database Dump not collected for {file_var}")
                        break
                    elif job_type == "latest_db_dumps":
                        if self.job_start_time > modified_time:
                            raise CVTestStepFailure(f"Latest Database Dump not collected for {file_var}")
                        break

    def _verify_process_dump(self, files_dict, file_list, file_extension):
        """
                Method to check process dump files exist or not
        """
        for file_prefix in files_dict.keys():
            for file_var in file_list:
                if file_prefix.lower() in file_var.lower() and file_extension in file_var:
                    if file_extension == '.tar.gz':  # Unix dump
                        if 'pkgsharedlib' in file_var.lower():  # Existing process dumps
                            files_dict[file_prefix] = True
                            self.log.info("Existing Linux Process Dump Found")
                            self.log.info(f"[{file_var}]  present at location [{self.base_path}]")

                        else:
                            raise CVTestStepFailure(
                                f"Existing Linux Process Dump is not present for {file_var}"
                            )

                    else:  # Windows dump
                        filename = os.path.basename(file_var)
                        birth_time = self._get_timestamp_from_file(filename)
                        if birth_time < self.job_start_time:
                            files_dict[file_prefix] = True
                            self.log.info("Existing Windows Process Dump Found")
                            self.log.info(f"[{file_var}] present at location [{self.base_path}]")
                        else:
                            raise CVTestStepFailure(
                                f"Existing Windows Process Dump is not present for {file_var}"
                            )

    def files_not_found(self, files_dict):

        """
            Logs the file that are missing from the bundles
        """

        for file_prefix, value in files_dict.items():
            if not value:
                self.log.info(f"{file_prefix} not found at the {self.base_path}")

        raise CVTestStepFailure(
            f"Some files are missing from the bundle. Kindly check the logs and debug further"
        )

    @test_step
    def verify_database_dump(self, job_type=None):
        """ To verify Commserve Database and other databases present in the uncompressed bundle or not """
        file_extension = '.dmp'
        files_dict = {"Commserv_": False, "CVCloud_": False, "HistoryDB_": False}
        file_list = self.local_machine.get_files_in_path(folder_path=self.base_path, recurse=False)
        self._verify_database_dump(files_dict, file_list, file_extension, job_type)
        if not (all(files_dict.values())):
            self.files_not_found(files_dict)

    @test_step
    def verify_process_dump(self):
        """Verifying process dump """
        folder_list = self.local_machine.get_folders_in_path(folder_path=self.base_path, recurse=False)
        procdump_folder = None
        cs_name = self.commcell_name
        for folder in folder_list:
            if f'{cs_name}~procdump~' in folder:
                procdump_folder = folder
                break
        else:
            raise CVTestStepFailure(
                f'Process Dump folder was not found on {self.base_path}'
            )
        file_list = self.local_machine.get_files_in_path(folder_path=procdump_folder)
        if "windows" in self.commserv_client.os_info.lower():
            ps_name = self.process_name.replace('.exe', '')
            file_extension = ".dmp"
            files_dict = {f'{ps_name}-' + self.process_id: False}
        else:
            file_extension = ".tar.gz"
            files_dict = {"cvsnapcore_": False}

        self._verify_process_dump(files_dict, file_list, file_extension)
        if not (all(files_dict.values())):
            self.files_not_found(files_dict)

    @test_step
    def verify_sql_error_logs(self):
        """Verifying DB logs """
        self.log.info('Verifying SQL ERROR log files present or not')
        folder_list = self.local_machine.get_folders_in_path(folder_path=self.base_path, recurse=False)
        for folder in folder_list:
            if "SQL_ERROR_LOGS" in folder:
                self.log.info(f"[{folder}]  present at location [{self.base_path}]")
                sql_folder = folder
                if any(file.lower() == 'errorlog' for file in os.listdir(sql_folder)):
                    self.log.info(f'Error Log is present at {sql_folder}')
                    return
                else:
                    raise CVTestStepFailure(
                        f"Error log was not found on {sql_folder}"
                    )

        raise CVTestStepFailure(
            f"[ SQL_ERROR_LOGS file not present in SendLog path  [{self.base_path}]"
        )

    def run(self):
        try:
            job_type = ["db_dumps", "latest_db_dumps"]
            for job in job_type:
                self.init_tc()
                self.run_send_log(job_type=job)
                self.log.info('Waiting for 25 mins to check file present at location ' +
                              _STORE_CONFIG.Reports.uncompressed_logs_path
                              + ' for send log job id ' + self.job_id)
                time.sleep(1500)
                self.base_path = self.send_log_utils.get_uncompressed_path(self.job_id, self.jobid_list)
                self.verify_database_dump(job_type=job)
                if job == "db_dumps":
                    self.verify_process_dump()
                    self.verify_sql_error_logs()
                self.jobid_list.clear()

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            self.local_machine.remove_directory(self.directory)
            self.cs_machine.delete_file(self.dump_fullpath)
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
