# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Web Console - Upload multiple files/Live Browse functionality for Laptop Clients"""

import time
import zipfile
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Laptop.navigator import Navigator
from Web.WebConsole.Laptop.Computers.summary import Summary
from Web.WebConsole.Laptop.Computers.client_details import ClientDetails
from Web.WebConsole.Laptop.Computers.browse import Browse
from Web.WebConsole.Laptop.Computers.live_browse import LiveBrowse
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from AutomationUtils.options_selector import OptionsSelector
from Laptop.laptoputils import LaptopUtils
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """
    TestCase class used to execute the test case from here.
    """
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Web Console - Upload multiple files/Live Browse functionality for Laptop Clients"
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
        self.browser = None
        self.webconsole = None
        self.navigator = None
        self.computers = None
        self.backups = None
        self.utility = None
        self.browse = None
        self.live_browse = None
        self.utils = TestCaseUtils(self)
        self.laptop_utils = None
        self.windows_filename = None
        self.webconsole_username = None
        self.webconsole_password = None
        self.download_directory = None
        self.machine = None
        self.path = None
        self.os_info = None
        self.clients = []
        self.clients_found = []
        self.cleanup_dict = {}
        self.file_names = []
        self.upload_file_path = []
        self.client_file_path = []

    def init_tc(self, user_name, password):
        """
        Initial configuration for the test case
        """
        try:
            self.utils.reset_temp_dir()
            self.download_directory = self.utils.get_temp_dir()
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
            self.live_browse = LiveBrowse(self.webconsole)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def setup(self):
        """Initializes objects required for this testcase"""
        self.clients.append(self.tcinputs["Windows_client_name"])
        self.clients.append(self.tcinputs["Mac_client_name"])
        self.webconsole_username = (self.tcinputs["webconsole_username"])
        self.webconsole_password = (self.tcinputs["webconsole_password"])
        self.utility = OptionsSelector(self._commcell)
        self.laptop_utils = LaptopUtils(self)


    @test_step
    def _verify_browse_results(self):
        """
        Verify browse results on given machine.
        """
        browse_res = self.browse.read_browse_results()
        file_found = 0
        for each_file in self.file_names:
            for each_item in browse_res:
                if each_file == each_item['FileName']:
                    self.log.info("uploaded file :{0} is found in live browse results".format(each_file))
                    file_found = 1
            if file_found == 0:
                raise CVTestStepFailure("uploaded file :{0} is not found in live browse results".format(each_file))

    @test_step
    def _verify_multiple_file_download_functionality(self,
                                                     local_machine,
                                                     client_name,
                                                     client_path,
                                                     file_name,
                                                     file_name2):
        """verification of multiple file download functionality in live browse """
        self.utils.reset_temp_dir()
        for each_file in self.file_names:
            self.browse.select_required_file(each_file)
        self.live_browse.click_on_download_and_watch_for_notifications()
        self.utils.wait_for_file_to_download("zip", timeout_period=300)
        files = local_machine.get_files_in_path(self.download_directory) # to extract Zip files
        for file in files:
            with zipfile.ZipFile(file, 'r') as zip_file:
                zip_file.extractall(self.download_directory)
        if self.os_info.lower() == 'windows':
            for idx, file_path in enumerate(self.upload_file_path):
                downloaded_file_hash = local_machine.get_file_hash(file_path)
                self.log.info("Downloaded file hash: [{0}]".format(downloaded_file_hash))
                client_file_hash = self.machine.get_file_hash(self.client_file_path[idx])
                self.log.info("client machine file hash: [{0}]".format(client_file_hash))
        else:
            temp_path = client_path.replace('/', '\\')
            _dir = self.download_directory +  '\\' + temp_path
            upload_file_path = _dir + '\\' + file_name
            upload_file_path2 = _dir + '\\' + file_name2
            self.upload_file_path.clear()
            self.upload_file_path.extend([upload_file_path, upload_file_path2])
            for idx, file_path in enumerate(self.upload_file_path):
                downloaded_file_hash = local_machine.get_file_hash(file_path)
                self.log.info("Downloaded file hash: [{0}]".format(downloaded_file_hash))
                client_file_hash = self.machine.get_file_hash(self.client_file_path[idx])
                self.log.info("client machine file hash: [{0}]".format(client_file_hash))
            if not downloaded_file_hash == client_file_hash:
                raise CVTestStepFailure("Hashes of both Files are not same for client: [{0}]".format(client_name))
            self.log.info("Hashes of both Files are same for client: [{0}]".format(client_name))

    @test_step
    def _verify_multiple_file_upload_functionality(self, local_machine, client_name, client_path):
        """verification of multiple file upload functionality in live browse """
        self.log.info("verification of single file upload functionality started for client: {0}" .format(client_name))
        self.computers.get_client_restore_link(client_name, goto_link=True)
        self.browse.navigate_to_restore_page(client_path)
        self.live_browse.select_live_machine_data_option(self.os_info)
        self.browse.wait_for_page_load()
        self.live_browse.upload_file(self.upload_file_path)
        self.live_browse.track_upload_progress()
        self.live_browse.refresh_live_browse_data()
        self.log.info("verify hashes for upload files")
        for idx, file_path in enumerate(self.upload_file_path):
            uploaded_file_hash = local_machine.get_file_hash(file_path)
            client_file_hash = self.machine.get_file_hash(self.client_file_path[idx])
            if not uploaded_file_hash == client_file_hash:
                raise CVTestStepFailure("Hashes of both Files are not same for client: [{0}]".format(client_name))
            self.log.info("Hashes of both Files are same for client: [{0}]".format(client_name))
        self._verify_browse_results()

    @test_step
    def live_browse_upload_and_download_functionality(self, clients_found):
        """
        Verification of upload and download multiple files in live Browse functionality for Laptop Clients
        """
        local_machine = Machine()  # create test data
        self.utils.reset_temp_dir()
        self.path = self.utils.get_temp_dir()
        local_time = int(time.time())
        for each_client in clients_found:
            self.file_names.clear()
            self.upload_file_path.clear()
            self.client_file_path.clear()
            if each_client == self.tcinputs["Windows_client_name"]:
                client_name = self.tcinputs["Windows_client_name"]
                file_name = 'Livebrowse_upload_1_'+str(local_time)+".txt"
                file_name2 = 'Livebrowse_upload_2_'+str(local_time)+".txt"
                self.file_names.extend([file_name, file_name2])
                upload_file_path = self.path + '\\' + file_name
                upload_file_path2 = self.path + '\\' + file_name2
                self.upload_file_path.extend([upload_file_path, upload_file_path2])
                client_path = self.tcinputs["windows_test_Path"]
                client_file_path = client_path + '\\' + file_name
                client_file_path2 = client_path + '\\' + file_name2
                self.os_info = 'Windows'
                self.client_file_path.extend([client_file_path, client_file_path2])
                self.cleanup_dict.setdefault(client_name, self.client_file_path)

            else:
                client_name = self.tcinputs["Mac_client_name"]
                file_name = 'Livebrowse_mac_upload_1_'+str(local_time)+".txt"
                file_name2 = 'Livebrowse_mac_upload_2_'+str(local_time)+".txt"
                self.file_names.extend([file_name, file_name2])
                upload_file_path = self.path + '/' + file_name
                upload_file_path2 = self.path + '/' + file_name2
                self.upload_file_path.extend([upload_file_path, upload_file_path2])
                client_path = self.tcinputs["Mac_test_Path"]
                client_file_path = client_path + '/' + file_name
                client_file_path2 = client_path + '/' + file_name2
                self.os_info = 'MAC'
                self.client_file_path.extend([client_file_path, client_file_path2])
                self.cleanup_dict.setdefault(client_name, self.client_file_path)
            self.machine = Machine(client_name, self.commcell)
            for each_filepath in self.upload_file_path:
                self.laptop_utils.create_file(local_machine, self.path, each_filepath)
            self._verify_multiple_file_upload_functionality(local_machine, client_name, client_path)
            self._verify_multiple_file_download_functionality(
            local_machine, client_name, client_path, file_name, file_name2
            )

        self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

    def run(self):
        try:
            self.init_tc(self.webconsole_username, self.webconsole_password)
            self.navigator.go_to_computers()
            console_clients = self.computers.get_clients_list()
            self.clients_found = self.laptop_utils.check_clients_exists(self.clients, console_clients)
            self.live_browse_upload_and_download_functionality(self.clients_found)

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            try:
                for client_name in self.clients_found:
                    for each_path in self.cleanup_dict[client_name]:
                        self.laptop_utils.cleanup_testdata(client_name, each_path)
            except Exception as err:
                self.log.info("Failed to delete test data{0}".format(err))
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)