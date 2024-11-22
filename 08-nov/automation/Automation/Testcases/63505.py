# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case"""

import zipfile
import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Laptop.LaptopEdgeMode import EdgeMain
from Web.AdminConsole.Helper.LaptopEdgeHelper import EdgeHelper
from Web.AdminConsole.Components.browse import RBrowse
from AutomationUtils.options_selector import OptionsSelector
from Laptop.laptoputils import LaptopUtils
from AutomationUtils.idautils import CommonUtils
from Reports.utils import TestCaseUtils
from AutomationUtils.machine import Machine
from Server.JobManager.jobmanager_helper import JobManager
from Web.Common.exceptions import CVTestStepFailure, CVWebAutomationException


class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole][EdgeMode] - Download of single file+single folder combination"""

    test_step = TestStep()

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][EdgeMode] - Download of single file+single folder combination"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.idautils = None
        self.utility = None
        self.edgeHelper_obj = None
        self.edgemain_obj = None
        self.machine_object= None
        self.laptop_utils = None
        self.client_name = None
        self.folder_path = None
        self.file_name = None
        self.file_path = None
        self.folder_file_name = None
        self.test_path = None
        self.rbrowse = None
        self.folder_name= None
        self.download_directory = None
        self.job_manager = None
        # PRE-REQUISITES OF THE TESTCASE
        # - Root folder of the "Test_data_path" is already created on machine and also added as subclient content
        
    def setup(self):
        """Initializes objects required for this testcase"""
        self.tcinputs.update(EdgeHelper.set_testcase_inputs(self))
        self.utils.reset_temp_dir()
        self.download_directory = self.utils.get_temp_dir()
        self.utility = OptionsSelector(self.commcell)
        self.idautils = CommonUtils(self)
        self.laptop_utils = LaptopUtils(self)
        self.machine_object = self.utility.get_machine_object(
                self.tcinputs['Machine_host_name'],
                self.tcinputs['Machine_user_name'], 
                self.tcinputs['Machine_password']
            )
        self.log.info(""" Initialize browser objects """)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.set_downloads_dir(self.download_directory)
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
       
        self.admin_console.login(self.tcinputs["Edge_username"],
                                 self.tcinputs["Edge_password"])
        self.edgeHelper_obj = EdgeHelper(self.admin_console, self.commcell)
        self.edgemain_obj = EdgeMain(self.admin_console)
        self.rbrowse = RBrowse(self.admin_console)
        self.job_manager = JobManager(commcell=self.commcell)
        self.tcinputs = self.edgeHelper_obj.check_laptop_backup_mode(self.tcinputs)

    @test_step
    def singlefile_download(self):
        """
        Download of single file
        """
        local_machine = Machine()
        client_path = self.test_path
        client_name = self.tcinputs["Client_name"]
        self.edgemain_obj.navigate_to_client_restore_page(self.tcinputs["Client_name"])
        self.log.info("Client restore path is : {0}".format(client_path))
        self.rbrowse.navigate_path(self.test_path, use_tree=False)
        self.rbrowse.select_files(file_folders=[self.file_name])
        self.rbrowse.submit_for_download()
        self.utility.sleep_time(30, "Waiting download of the file to be completed")
        self.rbrowse.clear_all_selection()
        client_file_hash = self.machine_object.get_file_hash(self.file_path)
        downloaded_file_hash = local_machine.get_file_hash(self.download_directory + '\\' + self.file_name)
        self.log.info("client machine file hash: [{0}]".format(client_file_hash))
        self.log.info("downloaded file hash: [{0}]".format(downloaded_file_hash))
        if not downloaded_file_hash == client_file_hash:
            raise CVTestStepFailure("Hashes of both Files are not same for client: [{0}]".format(client_name))
        self.log.info("Hashes of both Files are same for client: [{0}]".format(client_name))

    @test_step
    def download_file_and_folder_together(self):
        """
        Download of single file+single folder combination .
        """
        downloaded_folder_hashes = []
        client_folder_hashes = []
        local_machine = Machine()
        client_path = self.test_path
        client_name = self.tcinputs["Client_name"]
        self.edgemain_obj.navigate_to_client_restore_page(self.tcinputs["Client_name"])
        self.log.info("Client restore path is : {0}".format(client_path))
        self.rbrowse.navigate_path(self.test_path, use_tree=False)
        self.rbrowse.select_files(select_all=True)
        notification = self.rbrowse.submit_for_download()
        if not 'submitted for processing' in notification:
            raise CVWebAutomationException("Unexpected notification [{0}] while download request submitted"
                                           .format(notification))

        self.utils.wait_for_file_to_download("zip", timeout_period=300)
        files = local_machine.get_files_in_path(self.download_directory)  # to extract Zip files
        for file in files:
            with zipfile.ZipFile(file, 'r') as zip_file:
                zip_file.extractall(self.download_directory)
        downloaded_folder_rs = local_machine.get_folder_hash(self.download_directory + '\\' + self.folder_name)
        client_folder_rs = self.machine_object.get_folder_hash(self.folder_path)
        for each_val in downloaded_folder_rs:
            downloaded_folder_hashes.append(each_val[1])
        self.log.info("Downloaded folder files hashes: [{0}]".format(downloaded_folder_hashes))
        if self.tcinputs['os_type'].lower() == 'windows':
            for each_val in client_folder_rs:
                client_folder_hashes.append(each_val[1])
        else:
            for each_val in client_folder_rs:
                client_folder_hashes.append(each_val[0].split('=')[1])
        self.log.info("client folder files hashes: [{0}]".format(client_folder_hashes))
        if not downloaded_folder_hashes.sort() == client_folder_hashes.sort():
            raise CVTestStepFailure("Hashes of both folders are not same for client: [{0}]".format(client_name))
        self.log.info("Hashes of both Folders are same for client: [{0}]".format(client_name))
        downloaded_file_hash = local_machine.get_file_hash(self.download_directory + '\\' + self.file_name)
        self.log.info("Downloaded file hash: [{0}]".format(downloaded_file_hash))
        client_file_hash = self.machine_object.get_file_hash(self.file_path)
        self.log.info("client machine file hash: [{0}]".format(client_file_hash))
        if not downloaded_file_hash == client_file_hash:
            raise CVTestStepFailure("Hashes of both Files are not same for client: [{0}]".format(client_name))
        self.log.info("Hashes of both Files are same for client: [{0}]".format(client_name))


    @test_step
    def create_testpath(self):
        """
        Create test path with required folders and files for download verification
        """
        self.folder_name = 'TC_'+str(self.id)
        tc_test_foldername = 'Download_test_'+str(self.id)
        local_time = int(time.time())
        if self.tcinputs['os_type']=="Windows":
            self.test_path = self.tcinputs["Test_data_path"] + '\\' + tc_test_foldername
            self.folder_path = self.test_path + '\\' + self.folder_name
            self.file_name = 'backupfile_'+str(local_time)+".txt"
            self.file_path = self.test_path + '\\' + self.file_name
            self.folder_file_name = self.folder_path + '\\' + self.file_name
            
        else:
            self.test_path = self.tcinputs["Test_data_path"] + '/' + tc_test_foldername
            self.folder_path = self.test_path + '/' + self.folder_name
            self.file_name = 'backupmacfile_'+str(local_time)+".txt"
            self.file_path = self.test_path + '/' + self.file_name
            self.folder_file_name = self.folder_path + '/' + self.file_name

        self.laptop_utils.create_file(client=self.machine_object, 
                                      client_path=self.folder_path, 
                                      file_path=self.file_path)
        
        self.laptop_utils.create_file(client=self.machine_object,
                                       client_path=self.folder_path,
                                       file_path=self.folder_file_name)

    def run(self):

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.edgeHelper_obj.enduser = self.tcinputs["Edge_username"]
            self.edgeHelper_obj.validate_enduser_loggedin_url()
            self.edgeHelper_obj.verify_client_exists_or_not(self.tcinputs["Client_name"])
            self.create_testpath()
            
            if self.tcinputs['Cloud_direct'] is True:
                self.log.info("Trigger and validate backup on cloud client [{0}]".format(self.tcinputs["Client_name"]))
                self.edgeHelper_obj.trigger_v2_laptop_backup(self.tcinputs["Client_name"], self.tcinputs['os_type'])
            else:
                self.edgeHelper_obj.trigger_v1_laptop_backup(self.tcinputs["Client_name"])
            
            self.singlefile_download()
            self.download_file_and_folder_together()
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

            
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.utility.remove_directory(self.machine_object, self.test_path)


