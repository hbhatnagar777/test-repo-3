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
    __init__()                                          -- initialize TestCase class
    init_tc()                                           -- initialize pre-requisites
    run_send_log()                                      -- To run sendLogs job
    received_all_send_log_bundle()                      -- checking all received send log
                                                           chunk size
    run()                                               -- run function of this test case

Input Example:

    "testCases":
            {
                "55122":
                        {
                        }
            }

"""
import time
import os
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Web.AdminConsole.AdminConsolePages.Commcell import Commcell
from Web.AdminConsole.AdminConsolePages.send_logs import SendLogs
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import handle_testcase_exception
from cvpysdk.license import LicenseDetails
from Reports.SendLog.utils import SendLogUtils

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """Class for executing send log files with split file option test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  send log files with split file option


        """
        super(TestCase, self).__init__()
        self.browser = None
        self.admin_console = None
        self.send_log = None
        self.sjob_id = None
        self.commcell_id = None
        self.file_size = 0
        self.count = 0
        self.path = None
        self.commcell_name = None
        self.navigator = None
        self.send_log_utils = None
        self.commserv_client = None
        self.controller_machine = None
        self.jobid_list = []
        self.name = "sendlogfiles with split file option"

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        try:
            self.log.info("Initializing pre-requisites")
            licence = LicenseDetails(self.commcell)
            self.commcell_id = licence.commcell_id_hex
            self.commcell_name = self.commcell.commserv_name
            self.commserv_client = self.commcell.commserv_client
            self.controller_machine = Machine()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])
            self.send_log_utils = SendLogUtils(self, self.controller_machine)
            navigator = self.admin_console.navigator
            navigator.navigate_to_commcell()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run_send_log(self):
        """Running SendLog job"""
        comm_cell = Commcell(self.admin_console)
        comm_cell.access_sendlogs()
        send_log = SendLogs(self.admin_console)
        advanced_list = send_log.Advancedlist
        send_log.deselect_advanced(advanced_list=[advanced_list.SCRUB_LOGFILES])
        info_list = send_log.Informationlist
        send_log.select_information(information_list=[info_list.CSDB, info_list.OS_LOGS,
                                                      info_list.LOGS])
        send_log.select_advanced(advanced_list=[advanced_list.JOBS_RESULTS])
        self.sjob_id = send_log.submit()
        job_obj = self.commcell.job_controller.get(self.sjob_id)
        job_status = job_obj.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure(
                f"Send log job id [{self.sjob_id}] failed"
            )

    @test_step
    def received_all_send_log_bundle(self):
        """ verifying all received send log bundle with extension 7z.001, 7z.002, ...... """
        self.log.info('Log file path : ' + str(self.path))
        file = self.controller_machine.get_files_in_path(folder_path=self.path)
        file_name_suffix = self.sjob_id + ".7z.00"
        file_name_dict = {"sendLogFiles": [False, 0], "DBFiles": [False, 0], "jobresult": [False,0]}
        for file_var in file:
            for file_name_prefix in file_name_dict.keys():
                if file_name_suffix in file_var and file_name_prefix in file_var:
                    file_size = self.controller_machine.get_file_size(file_path=file_var)
                    self.log.info(f"[{file_var}] present at location : [{self.path}] file size : [{file_size}]")
                    if file_size > 512:
                        raise CVTestStepFailure(
                            f" Chunked File Size is greater than 512 MB, file name {file_var}"
                        )
                    file_name_dict[file_name_prefix][0] = True
                    file_name_dict[file_name_prefix][1] += 1

        for file_name, (found, count) in file_name_dict.items():
            if not found:
                raise CVTestStepFailure(
                    f"{file_name} no present with chunking {file_name_suffix}"
                )
            self.log.info(f'{count} number of chunks for {file_name} present')

    def run(self):
        try:
            self.init_tc()
            self.run_send_log()
            self.log.info(
                'Waiting for 15 minutes  to check file present '
                + ' for send log job id ' + self.sjob_id)
            time.sleep(900)
            self.path = self.send_log_utils.get_compressed_path(self.sjob_id, self.jobid_list)
            self.received_all_send_log_bundle()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
