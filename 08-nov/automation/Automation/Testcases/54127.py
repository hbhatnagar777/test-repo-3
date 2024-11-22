# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Webconsle - Data Download functionality for versions of file for Laptop Clients"""

import time
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Laptop.navigator import Navigator
from Web.WebConsole.Laptop.Computers.summary import Summary
from Web.WebConsole.Laptop.Computers.client_details import ClientDetails
from Web.WebConsole.Laptop.Computers.browse import Browse
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from AutomationUtils.options_selector import OptionsSelector
from Laptop.laptoputils import LaptopUtils
from AutomationUtils.machine import Machine
from Laptop.CloudLaptop import cloudlaptophelper


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Webconsle - Data Download functionality for versions of file for Laptop Clients"
        self.product = self.products_list.LAPTOP
        self.show_to_user = True
        self.tcinputs = {
            "webconsole_username": None,
            "webconsole_password": None,
            "Windows_client_name": None,
            "windows_test_Path": None,
            "Mac_client_name": None,
            "Mac_test_Path": None,
            "Cloud_direct": None
        }
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.computers = None
        self.backups = None
        self.browse = None
        self.utils = TestCaseUtils(self)
        self.laptop_utils = None
        self.windows_filename = None
        self.webconsole_username = None
        self.webconsole_password = None
        self.download_directory = None
        self.machine = None
        self.cloud_object = None
        self.clients = []
        self.clients_found = []
        self.cleanup_dict = {}

    def init_tc(self, user_name, password):
        """
        Initial configuration for the test case
        """
        try:
            self.utils.reset_temp_dir()
            self.download_directory = self.utils.get_temp_dir()
            self.log.info("Download directory:%s", self.download_directory)
            self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
            self.browser.set_downloads_dir(self.download_directory)
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
        self.cloud_object = cloudlaptophelper.CloudLaptopHelper(self)

    @test_step
    def _verify_backup_running(self, backup_text):
        """
        Verify if any backup is running on client machine.
        """
        for _i in range(1, 6):
            if not self.backups.is_backup_running():
                return 0
            self.log.info(" '{0}' backup job running.Will wait about 5 minutes to let job finish".format(backup_text))
            OptionsSelector(self._commcell).sleep_time(120, "Waiting for Backup job to finish")
        raise CVTestStepFailure("Backup did not finish in 10 minutes. Exiting")

    @test_step
    def download_file_version(self, client_name, client_path, file_name, file_path, version_file):
        """
        Download the version of the file .
        """
        # create local machine object
        local_machine = Machine()
        self.computers.get_client_restore_link(client_name, goto_link=True)
        self.log.info("Client restore path is : {0}".format(client_path))
        self.browse.navigate_to_restore_page(client_path)
        self.browse.select_required_file(file_name)
        self.browse.go_to_versions_page()
        self.browse.wait_for_page_load()
        browse_res = self.browse.read_browse_results()
        required_file = browse_res[1]['FileName']
        self.log.info("selected version file : [{0}] to download from webconsole".format(required_file))
        self.browse.select_required_file(required_file)
        self.browse.click_on_download_and_watch_for_notifications()
        self.utils.wait_for_file_to_download("txt", timeout_period=300)
        downloaded_file_hash = local_machine.get_file_hash(version_file)
        self.log.info("Downloaded file hash: [{0}]".format(downloaded_file_hash))
        client_file_hash = self.machine.get_file_hash(file_path)
        self.log.info("client machine file hash: [{0}]".format(client_file_hash))
        if not downloaded_file_hash == client_file_hash:
            raise CVTestStepFailure("Hashes of both Files are not same for client: [{0}]".format(client_name))
        self.log.info("Hashes of both Files are same for client: [{0}]".format(client_name))

    @test_step
    def run_backup(self, file_path, client_name):
        """
        Modify the file and run the backup.
        """
        self.machine.append_to_file(file_path, 'Second version of the File')
        #-----------------Changes for cloud laptop -------------#
        if self.tcinputs['Cloud_direct']:
            self.log.info("Trigger and validate backup on cloud client [{0}]".format(client_name))
            self.cloud_object.trigger_and_validate_backup_from_webconsole(client_name, self.webconsole)
        else:
            self._verify_backup_running('previous')
            self.backups.click_on_backup_button()  # Trigger the backup
            self._verify_backup_running('Current')

    @test_step
    def backup_and_download_file_version(self, clients_found):
        """
        Run backup and download file version on given machines.
        """
        local_time = int(time.time())
        for each_client in clients_found:
            if each_client == self.tcinputs["Windows_client_name"]:
                client_name = self.tcinputs["Windows_client_name"]
                file_name = 'backupfile_'+str(local_time)+".txt"
                download_file = 'backupfile_'+str(local_time)+"(2)"+".txt"
                file_path = self.tcinputs["windows_test_Path"] + '\\' + file_name
                client_path = self.tcinputs["windows_test_Path"]
                self.cleanup_dict.setdefault(client_name, client_path)

            else:
                client_name = self.tcinputs["Mac_client_name"]
                file_name = 'backupmacfile_'+str(local_time)+".txt"
                download_file = 'backupmacfile_'+str(local_time)+"(2)"+".txt"
                file_path = self.tcinputs["Mac_test_Path"] + '/' + file_name
                client_path = self.tcinputs["Mac_test_Path"]
                self.cleanup_dict.setdefault(client_name, client_path)

            # create machine object
            self.machine = Machine(client_name, self.commcell)
            version_file = self.download_directory + '\\' + download_file
            # create test data
            self.laptop_utils.create_file(self.machine, client_path, file_path)
            self.computers.get_client_prop(client_name=each_client, goto_link=True)  # get the client properties
            #-----------------Changes for cloud laptop -------------#
            if self.tcinputs['Cloud_direct']:
                self.log.info("Trigger and validate backup on cloud client [{0}]".format(client_name))
                self.cloud_object.trigger_and_validate_backup_from_webconsole(client_name, self.webconsole)
            else:
                self._verify_backup_running('previous')
                self.backups.click_on_backup_button()  # Trigger the backup
                self._verify_backup_running('Current')
            # Run the backup for second version to be created
            self.run_backup(file_path, client_name)
            self.download_file_version(client_name, client_path, file_name, file_path, version_file)
        self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

    def run(self):
        try:
            self.init_tc(self.webconsole_username, self.webconsole_password)
            self.navigator.go_to_computers()
            console_clients = self.computers.get_clients_list()
            self.clients_found = self.laptop_utils.check_clients_exists(self.clients, console_clients)
            self.backup_and_download_file_version(self.clients_found)

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            try:
                for client_name in self.clients_found:
                    self.laptop_utils.remove_directory(client_name, self.cleanup_dict[client_name])
            except Exception as err:
                self.log.info("Failed to delete test data{0}".format(err))
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
