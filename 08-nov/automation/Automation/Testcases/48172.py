# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Webconsle -  Data Backup functionality for Laptop Clients"""

import os.path
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.WebConsole.Laptop.Computers.client_details import ClientDetails
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Laptop.navigator import Navigator
from Web.WebConsole.Laptop.Computers.browse import Browse
from Web.WebConsole.Laptop.Computers.summary import Summary
from Reports.utils import TestCaseUtils
from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptoputils import LaptopUtils
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Webconsle -  Data Backup functionality for Laptop Clients"
        self.product = self.products_list.LAPTOP
        self.show_to_user = True
        self.tcinputs = {
            "webconsole_username": None,
            "webconsole_password": None,
            "Windows_client_name": None,
            "windows_test_Path": None,
            "Mac_client_name": None,
            "Mac_test_Path": None,
        }
        self.utils = TestCaseUtils(self)
        self.laptop_utils = None
        self.webconsole = None
        self.browser = None
        self.backups = None
        self.browse = None
        self.computers = None
        self.navigator = None
        self.webconsole_username = None
        self.webconsole_password = None
        self.clients = []
        self.clients_found = []
        self.cleanup_dict = {}

    def init_tc(self, user_name, password):
        """
        Initial configuration for the test case
        """
        try:
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.open()
            self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
            self.webconsole.login(user_name, password)
            self.webconsole.goto_mydata()
            self.navigator = Navigator(self.webconsole)
            self.computers = Summary(self.webconsole)
            self.backups = ClientDetails(self.webconsole)
            self.browse = Browse(self.webconsole)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def setup(self):
        """Initializes objects required for this testcase"""
        self.clients.append(self.tcinputs["Windows_client_name"])
        self.clients.append(self.tcinputs["Mac_client_name"])
        self.webconsole_username = (self.tcinputs["webconsole_username"])
        self.webconsole_password = (self.tcinputs["webconsole_password"])
        self.laptop_utils = LaptopUtils(self)

    @test_step
    def _verify_backup_running(self, backup_text):
        """
        Verify if any backup is running on client machine.
        """
        for _i in range(1, 6):
            if not self.backups.is_backup_running():
                return 0
            else:
                self.log.info(" [{0}] backup job running.Will wait about 5 minutes to let job finish"
                              .format(backup_text))

                OptionsSelector(self._commcell).sleep_time(120, "Waiting for Backup job to finish")
        raise CVTestStepFailure("Backup did not finish in 10 minutes. Exiting")

    @test_step
    def _verify_browse_results(self, each_client, client_path, folder_name=None, kill=False):
        """
        Verify browse results on given machine.
        """
        browse_list_pause = []
        browse_list_kill = []
        files_list = []
        self.computers.get_client_restore_link(client_name=each_client, goto_link=True)
        self.log.info("Client path is : {0}".format(client_path))
        self.browse.navigate_to_restore_page(client_path)
        browse_res = self.browse.read_browse_results()

        if kill:
            for each_item in browse_res:
                browse_list_kill.append(each_item['FolderName'])

            file_found = 0
            for each_item in browse_list_kill:
                if folder_name == each_item:
                    file_found = 1
                    raise CVTestStepFailure("Kill backup job functionality failed as" +
                                            "folder [{0}] backed up even backup job is killed"
                                            .format(folder_name))
            if file_found == 0:
                self.log.info("Kill backup job functionality is completed successfully")

        else:
            for each_item in browse_res:
                browse_list_pause.append(each_item['FileName'])

            _list = self.laptop_utils.get_files_in_path(each_client, client_path)
            for each_file in _list:
                files_list.append(os.path.basename(each_file))
            browse_list_pause.sort()
            files_list.sort()
            if browse_list_pause == files_list:
                self.log.info("All files backed up successfully while pause and resume the job on client: [{0}]"
                              .format(each_client))
            else:
                raise CVTestStepFailure("All files not backed up while pause and resume the job on client: [{0}]"
                                        .format(each_client))

    @test_step
    def _verify_kill_backup_job_functionality(self, client_name, client_path, kill_folder):
        """
        verify Kill backup job functionality
        """
        self.log.info("*" * 10 + " Kill backup job functionality verification started for client : [{0}] "
                      .format(client_name) + "*" * 10)
        # navigate to computers page from previous page
        self.computers.get_client_prop(client_name=client_name, goto_link=True)  # get the client properties
        self._verify_backup_running('previous')
        self.laptop_utils.create_file(client_name, kill_folder, files=5)
        self.backups.click_on_backup_button()  # Trigger the backup
        self.backups.click_kill_button()
        job_id = self.backups.get_job_id()
        OptionsSelector(self._commcell).sleep_time(30, "waiting for job killed")
        self.laptop_utils.verify_job_status_in_gui(job_id=job_id, expected_state='killed')
        self._verify_browse_results(client_name, client_path, folder_name=kill_folder, kill=True)

    @test_step
    def _verify_pause_resume_backup_job_functionality(self, client_name, client_path):
        """
        verify Pause and resume functionality
        """
        self.log.info("*" * 10 + " Pause and resume backup job verification started for client : [{0}] "
                      .format(client_name) + "*" * 10)

        self.computers.get_client_prop(client_name=client_name, goto_link=True)  # get the client properties
        self._verify_backup_running('previous')
        # ******verify pause functionality********
        self.backups.click_on_backup_button()
        self.backups.click_pause_button()
        self.backups.wait_for_job_paused()
        self._log.info("Backup job has been paused successfully")
        job_id = self.backups.get_job_id()
        self.laptop_utils.verify_job_status_in_gui(job_id=job_id, expected_state='suspended')
        # ******Verify Resume functionality******
        self.backups.click_on_resume_job()
        self._verify_backup_running('Current')
        self.laptop_utils.verify_job_status_in_gui(job_id=job_id, expected_state='completed')
        self._verify_browse_results(client_name, client_path)

    @test_step
    def pause_resume_kill_backup_job(self, clients_found):
        """
        verify Pause, resume and kill functionality
        """
        for each_client in clients_found:
            if each_client == self.tcinputs["Windows_client_name"]:
                client_name = self.tcinputs["Windows_client_name"]
                client_path = self.tcinputs["windows_test_Path"]
                self.laptop_utils.generate_test_data(client_name, client_path)
                kill_folder = client_path + '/' + 'TC_48172'
                self.cleanup_dict.setdefault(client_name, client_path)

            else:
                client_name = self.tcinputs["Mac_client_name"]
                client_path = self.tcinputs["Mac_test_Path"]
                self.laptop_utils.create_file(client_name, client_path, files=5)
                kill_folder = client_path + '/' + 'TC_48172'
                self.cleanup_dict.setdefault(client_name, client_path)

            self._verify_pause_resume_backup_job_functionality(client_name, client_path)
            self._verify_kill_backup_job_functionality(client_name, client_path, kill_folder)
        self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

    def run(self):
        try:
            self.init_tc(self.webconsole_username, self.webconsole_password)
            self.navigator.go_to_computers()
            console_clients = self.computers.get_clients_list()
            self.clients_found = self.laptop_utils.check_clients_exists(self.clients, console_clients)
            self.pause_resume_kill_backup_job(self.clients_found)

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            try:
                for client_name in self.clients_found:
                    self.laptop_utils.remove_directory(client_name, self.cleanup_dict[client_name])
            except Exception as err:
                self.log.info("Failed to remove directory {0}".format(err))
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
