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
    extract_send_logs_files   -- Extract send Log file
    verify_commvault_logs()  -- verify different commvault logs
    run()                    --  run function of this test case

Input Example:

    "testCases":
            {
                "57821":
                        {

                        }
            }


"""
import time
import os
from AutomationUtils.machine import Machine
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Commcell import Commcell
from Web.AdminConsole.AdminConsolePages.send_logs import SendLogs
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from cvpysdk.license import LicenseDetails
from Reports.SendLog.utils import SendLogUtils
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Sendlogs: Verify output to local drive"""
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
        self.download_directory = None
        self.machine = None
        self.path = None
        self.directory = None
        self.utils = TestCaseUtils(self)
        self.utils.reset_temp_dir()
        self.download_directory = self.utils.get_temp_dir()
        self.send_log_utils = None
        self.commserv_client = None
        self.name = "Sendlogs: Verify output to local drive"

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        try:
            self.log.info("Initializing pre-requisites")
            self.log.info('Connecting to local machine wait for 1 min')
            self.commserv_client = self.commcell.commserv_client
            self.machine = Machine(self.commserv_client)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])
            self.send_log_utils = SendLogUtils(self, self.machine)
            self.directory = self.send_log_utils.create_directory_for_given_path("TC57821")
            navigator = self.admin_console.navigator
            navigator.navigate_to_commcell()
            licence = LicenseDetails(self.commcell)
            self.commcell_id = licence.commcell_id_hex
            self.commcell_name = self.commcell.commserv_name
            comm_cell = Commcell(self.admin_console)
            comm_cell.access_sendlogs()
            self.send_log = SendLogs(self.admin_console)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def run_send_log(self):
        """Running SendLog job"""
        self.send_log.disable_auto_upload()
        self.send_log.select_local_output(local_path=self.directory)
        advanced_list = self.send_log.Advancedlist
        self.send_log.deselect_advanced(advanced_list=[advanced_list.SCRUB_LOGFILES])
        info_list = self.send_log.Informationlist
        self.send_log.select_information(information_list=[info_list.OS_LOGS, info_list.LOGS])
        self.jobid = self.send_log.submit()
        job_obj = self.commcell.job_controller.get(self.jobid)
        job_status = job_obj.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure(
                f"Send log job id [{self.jobid}] failed"
            )

    @test_step
    def extract_send_logs_files(self):
        """ To unzip send log content """
        self.path = self.send_log_utils.unzip_send_log_file(self.commserv_client, self.path)

    @test_step
    def verify_commvault_logs(self):
        """Verifying commvault send logs """
        self.log.info("Verify the logs present in the directory")
        if "windows" in self.commserv_client.os_info.lower():
            cc_zip_path= os.path.join(self.path, f'{self.commcell_name}.7z')
            self.path = self.send_log_utils.unzip_send_log_file(self.commserv_client, cc_zip_path)
            time.sleep(20)

        entities_dict = {'cvd.log': False, 'EvMgrS.log': False, 'JobManager.log': False}
        file_list = self.machine.get_files_in_path(self.path, recurse=False)
        self.send_log_utils.verify_entities(file_list, entities_dict, self.path)

    def run(self):
        try:
            self.init_tc()
            self.run_send_log()
            self.log.info('Waiting for 1 minute to check file present at ' + self.directory +
                          'location for send log job id' + self.jobid)
            time.sleep(60)
            self.path = self.send_log_utils.send_log_bundle_path(self.directory, self.jobid, self.jobid_list)
            self.extract_send_logs_files()
            self.log.info(f'Waiting for 2 minutes to completely unzip the logs in {self.directory}')
            time.sleep(120)
            self.verify_commvault_logs()
            self.log.info(f'Waiting for a minute to close any open scripts that holds directory')
            time.sleep(60)
            self.machine.remove_directory(self.directory)
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
