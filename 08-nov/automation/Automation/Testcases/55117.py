# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Notes :
1>   For email verification give email and its credential in config.json and servername in input.json :

Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                                    --  initialize TestCase class
    init_tc()                                     --  initial configuration for this test case
    run_send_log()                                -- To run sendLogs job
    verify_commvault_logs()                       -- to verify the basic logs on CS/client
    verify_os_logs()                              -- verify OS logs from CS/client
    verify_machine_config_logs()                  -- verify machine configuration logs from CS/client
    verify_support_dir()                          -- verify the support directory is deleted
    verify_description_richtext_in_email()        -- verify the description richtext in email
    run()                                         --  run function of this test case

Input Example:

    "testCases":
            {
                "55117":
                 {
                     "user_name": "username",
                     "ClientName": "C1"
                 }
            }


"""
import time
import os
import datetime
from AutomationUtils.machine import Machine
from Web.Common.page_object import handle_testcase_exception
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Commcell import Commcell
from Web.AdminConsole.AdminConsolePages.send_logs import SendLogs
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from cvpysdk.license import LicenseDetails
from Reports.SendLog.utils import SendLogUtils

_STORE_CONFIG = get_config()


class TestCase(CVTestCase):
    """This test case verifies basic sendlogfiles feature"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.subject = None
        self.description_link = None
        self.description_text = None
        self.browser = None
        self.admin_console = None
        self.send_log = None
        self.info_list = None
        self.jobid = None
        self.utils = None
        self.file_server = None
        self.commcell_id = None
        self.commcell_name = None
        self.commserv_machine = None
        self.client_machine = None
        self.machine = None
        self.commserv_client = None
        self.cs_OS = None
        self.client_OS = None
        self.local_machine = None
        self.base_path = None
        self.curr_path = None
        self.download_directory = None
        self.send_log_utils = None
        self.jobid_list = []
        self.comm_cell = None
        self.name = "Acceptance of Sendlogs for logs collection"

    def init_tc(self):
        """
            Initial configuration for the test case
            """
        try:
            self.log.info("Initializing pre-requisites")
            self.commserv_client = self.commcell.commserv_client
            self.commserv_machine = Machine(self.commserv_client)
            self.client_machine = Machine(self.client)
            self.machine = Machine()
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']["commcellUsername"],
                                     self.inputJSONnode['commcell']["commcellPassword"])

            self.send_log_utils = SendLogUtils(self, self.machine)
            self.download_directory = self.send_log_utils.create_directory_for_given_path("TC55117")
            navigator = self.admin_console.navigator
            navigator.navigate_to_commcell()
            licence = LicenseDetails(self.commcell)
            self.commcell_id = licence.commcell_id_hex
            self.commcell_name = self.commcell.commserv_name
            self.comm_cell = Commcell(self.admin_console)
            self.local_machine = Machine()
            self.send_log = SendLogs(self.admin_console)
            self.file_server = FileServers(self.admin_console)
            self.cs_OS = self.commserv_client.os_info.lower()
            self.client_OS = self.client.os_info.lower()
            self.info_list = self.send_log.Informationlist
            self.description_text = f'This is bold text'
            self.description_link = f'http://' + self.commcell.webconsole_hostname + '/webconsole'
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def run_send_log(self, client=False):
        """Running SendLog job"""

        datetime_obj = datetime.datetime.now()
        job_start_timestamp = datetime_obj.strftime("%m/%d %H:%M")
        if client:
            self.admin_console.navigator.navigate_to_servers()
            self.admin_console.wait_for_completion()
            time.sleep(5)
            self.file_server.action_sendlogs(self.tcinputs["ClientName"])
            self.subject = 'Sendlogs job with user ' + self.tcinputs[
                'user_name'] + ' in cc field' + ' - ' + job_start_timestamp
            self.send_log.email(users=[], cc_users=[self.tcinputs['user_name']],
                                subject=self.subject,
                                description_text=self.description_text,
                                description_link=self.description_link)
        else:
            self.comm_cell.access_sendlogs()
            self.subject = 'Sendlogs job with user ' + self.tcinputs[
                'user_name'] + ' in to field' + ' - ' + job_start_timestamp
            self.send_log.email(users=[self.tcinputs['user_name']], subject=self.subject)

        info_list = self.send_log.Informationlist
        self.send_log.select_information(information_list=[info_list.MACHINE_CONFIG, info_list.OS_LOGS])
        advanced_list = self.send_log.Advancedlist
        self.send_log.deselect_advanced(advanced_list=[advanced_list.SCRUB_LOGFILES])
        self.send_log.disable_self_email_notification()
        self.jobid = self.send_log.submit()
        job_obj = self.commcell.job_controller.get(self.jobid)
        job_status = job_obj.wait_for_completion()
        if not job_status:
            raise CVTestStepFailure(
                f"Send log job id [{self.jobid}] failed"
            )

    @test_step
    def verify_commvault_logs(self, client=False):
        """Verifying commvault send logs """
        self.log.info('Opening client folder and  Verifying logs:')
        entities_dict = {'cvd.log': False, 'cvfwd.log': False}
        if not client:
            entities_dict.update({'JobManager.log': False})

        entities_dict.update({'cacert.pem': False})
        file_list = self.local_machine.get_files_in_path(self.curr_path)
        self.send_log_utils.verify_entities(file_list, entities_dict, self.curr_path)

    @test_step
    def verify_os_logs(self, client=False):
        """Verifying OS logs"""
        self.log.info("Verifying OS Logs")
        os_info = self.client_OS if client else self.cs_OS
        if "windows" in os_info:
            entities_dict = {'Application.evtx': False, 'Application.log': False, 'system.evtx': False,
                             'system.log': False}
        else:
            entities_dict = {'osc_config.xml': False}
        file_list = self.local_machine.get_files_in_path(self.curr_path)
        self.send_log_utils.verify_entities(file_list, entities_dict, self.curr_path,
                                            partial_name_verify=True)

    @test_step
    def verify_machine_config_logs(self, client=False):
        """Verifying machine configuration logs"""
        self.log.info("Verifying Machine Configuration Logs")
        os_info = self.client_OS if client else self.cs_OS
        file_list = self.local_machine.get_files_in_path(self.curr_path)
        if "windows" in os_info:
            entities_dict = {'SystemConfig.txt': False, 'volumeinfo.txt':False,
                             'ipconfig.txt': False, 'netstat.txt': False,
                             'systeminfo.txt': False, 'network_configs.txt': False,
                             'etchosts.txt': False}
        else:
            entities_dict = {'diskfree.log': False, 'mountinfo.log': False,
                             'netconfig.log': False, 'ospatch.log': False,
                             'unameinfo.log': False, 'messages': False,
                             'diskspace.log': False}
        self.send_log_utils.verify_entities(file_list, entities_dict, self.curr_path, partial_name_verify=True)

    @test_step
    def verify_description_richtext_in_email(self):
        """Verifying description rich text in email"""
        file_list = self.local_machine.get_files_in_path(self.download_directory)
        description_text_found = False
        description_link_found = False
        for file_name in file_list:
            if "cc field" not in file_name:
                continue
            with open(os.path.join(self.download_directory, file_name), errors="ignore") as email_html:
                lines = email_html.readlines()
                for line in lines:
                    if self.description_text in line:
                        description_text_found = True
                    if self.description_link in line:
                        description_link_found = True
                    if description_link_found and description_text_found:
                        break
            if not description_text_found or not description_link_found:
                raise CVTestStepFailure(
                    f" description text or link not present in the email"
                )
            else:
                self.log.info(f'description found in the email')

    @test_step
    def verify_support_dir(self):
        """Verifying that support directory is deleted from job results folder after the job"""
        folders = self.commserv_machine.get_folders_in_path(folder_path=self.commserv_client.job_results_directory)
        for folder in folders:
            if ("support" in folder.lower() and self.jobid in folder.lower()) or ("sendlogs" in folder.lower() and
                                                                                  self.jobid in folder.lower()):
                raise CVTestStepFailure(
                    f" directory  {folder} created as part of the send logs job is not deleted"
                )

    def run(self):
        """Run function of this test case to Run backup """
        try:
            job_types = ["commserv", "client"]
            for job_type in job_types:
                self.init_tc()
                self.run_send_log(client=job_type == "client")
                self.log.info(f'Waiting for 1 minute to check email for send log job id {self.jobid}')
                time.sleep(60)
                self.send_log_utils.verify_email(self.download_directory, self.subject)
                if job_type == "client":
                    self.verify_description_richtext_in_email()
                self.log.info(f"Waiting for 20 minutes to check file present at "
                              f"network location for send log job id {self.jobid}")
                time.sleep(1200)
                self.base_path = self.send_log_utils.get_uncompressed_path(self.jobid, self.jobid_list)
                if job_type == "commserv":
                    self.curr_path = os.path.join(self.base_path, self.commcell_name)
                else:
                    self.curr_path = os.path.join(self.base_path, self.tcinputs["ClientName"])

                self.verify_commvault_logs(client=job_type == "client")
                self.verify_os_logs(client=job_type == "client")
                self.verify_machine_config_logs(client=job_type == "client")
                if job_type == "commserv":
                    self.verify_support_dir()

            self.machine.remove_directory(self.download_directory)

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
