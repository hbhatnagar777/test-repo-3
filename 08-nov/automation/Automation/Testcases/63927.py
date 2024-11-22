# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case"""

import time
import zipfile
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Laptop.LaptopEdgeMode import EdgeRestore
from Web.AdminConsole.Helper.LaptopEdgeHelper import EdgeHelper
from Web.AdminConsole.Components.browse import RBrowse
from AutomationUtils.options_selector import OptionsSelector
from Laptop.laptoputils import LaptopUtils
from AutomationUtils.idautils import CommonUtils
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Components.table import Rtable
from Server.JobManager.jobmanager_helper import JobManager
from Web.AdminConsole.Helper.LaptopHelper import LaptopMain
from Web.Common.exceptions import CVTestStepFailure
from AutomationUtils.machine import Machine

class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole][AdminMode]: Deleted items Download validation as tenant admin"""

    test_step = TestStep()

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[[Laptop] [AdminConsole][AdminMode]: Deleted items Download validation as tenant admin"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.idautils = None
        self.utility = None
        self.edgeHelper_obj = None
        self.machine_object= None
        self.laptop_utils = None
        self.client_name = None
        self.file_name = None
        self.file_path = None
        self.test_path = None
        self.folder_path = None
        self.rbrowse = None
        self.rtable = None
        self.folder_name= None
        self.folder_file_name = None
        self.edgerestore = None
        self.job_manager = None
        self.dest_path = None
        self.laptop_obj = None
        self.download_directory = None
        self.download_dict = {}
        self.validation_dict = {}

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
        self.admin_console.login(self.tcinputs["Tenant_admin"],
                                 self.tcinputs["Tenant_password"])
        self.laptop_obj = LaptopMain(self.admin_console, self.commcell)
        self.edgeHelper_obj = EdgeHelper(self.admin_console, self.commcell)
        self.rbrowse = RBrowse(self.admin_console)
        self.rtable = Rtable(self.admin_console)
        self.edgerestore = EdgeRestore(self.admin_console)
        self.job_manager = JobManager(commcell=self.commcell)
        self.tcinputs = self.edgeHelper_obj.check_laptop_backup_mode(self.tcinputs)

    @test_step
    def delete_testdata_and_backup(self):
        """
        delete the backedup content from laptop client and run the backup 
        """
        self.utility.remove_directory(self.machine_object, self.folder_path)
        self.utility.remove_directory(self.machine_object, self.file_path)
        self.run_backup()

    @test_step
    def download_deleted_data(self):
        """
        Download the deleted files and folders
        """
        local_machine = Machine()
        self.rtable.access_action_item(self.client_name, 'Restore')
        self.log.info("-- Delete Folder downlaod started : [{0}] --".format(self.folder_name))
        self.rbrowse.select_deleted_items_for_restore(content_path=self.test_path, files_folders=[self.folder_name])
        notification = self.rbrowse.submit_for_download()
        download_job_id = EdgeHelper.extarct_job_id_from_text(notification)
        jobobj = self.commcell.job_controller.get(job_id=download_job_id)
        self.job_manager.job = jobobj
        self.job_manager.wait_for_state('completed')
        self.rbrowse.clear_all_selection()
        #--Extract the downloaded folder 
        self.utils.wait_for_file_to_download("zip", timeout_period=300)
        files = local_machine.get_files_in_path(self.download_directory)  # to extract Zip files
        for file in files:
            with zipfile.ZipFile(file, 'r') as zip_file:
                zip_file.extractall(self.download_directory)
        downloaded_folder_hash = local_machine.get_folder_hash(self.download_directory + '\\' + self.folder_name)
        for each_val in downloaded_folder_hash:
            self.download_dict[self.folder_name]=each_val[1]
        self.log.info("-- Deleted File download started : [{0}] --".format(self.file_name))
        self.rbrowse.select_files(file_folders=[self.file_name])
        self.rbrowse.submit_for_download()
        downloaded_file_hash = local_machine.get_file_hash(self.download_directory + '\\' + self.file_name)
        self.download_dict[self.file_name]=downloaded_file_hash

    @test_step
    def download_data_validation(self):
        """
        Download validation of the deleted data
        """
        for dict_key, dict_val in self.validation_dict.items():
            self.log.info("deleted data download validation for item [{0}] ".format(dict_key))
            if dict_val == self.download_dict[dict_key]:
                self.log.info("Backedup file and deleted file both are same")
            else:
                raise CVTestStepFailure(
                    """
                    Backedup item Hash [{0}] does not match with downloaded item Hash [{1}] for deleted item: [{2}]
                    """.format(dict_val, self.download_dict[dict_key], dict_key)
                    )
    @test_step
    def run_backup(self):
        """ Trigger backup """
        if self.tcinputs['Cloud_direct'] is True:
            self.log.info("initiating backup on cloud laptop client [{0}]".format(self.client_name))
            self.laptop_obj.trigger_cloudlaptop_backup(self.client_name, 
                                                       self.tcinputs['os_type'], 
                                                       backup_type='backup_from_actions')
            self.utility.sleep_time(300, "Wait for index play back to finish")
        
        else:
            self.log.info("initiating backup on classic laptop client [{0}]".format(self.client_name))
            subclient_obj = self.idautils.get_subclient(self.client_name)
            _job_obj = self.idautils.subclient_backup(subclient_obj)
            
    @test_step
    def create_testdata_and_backup(self):
        """
        Create test data and backup the files and folder
        """
        self.client_name = self.tcinputs["Client_name"]
        self.folder_name = 'TC_'+str(self.id)
        tc_test_foldername = 'DeletedData_download_Test_'+str(self.id)
        local_time = int(time.time())
        self.dest_path = self.utility.create_directory(self.machine_object)
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

        folder_checksum = self.machine_object.get_file_hash(self.folder_file_name)
        file_checksum = self.machine_object.get_file_hash(self.file_path)
        self.validation_dict[self.folder_name] = folder_checksum
        self.validation_dict[self.file_name] = file_checksum
        self.run_backup()

    def run(self):

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.laptop_obj.navigate_to_laptops_page()
            self.create_testdata_and_backup()
            self.delete_testdata_and_backup()
            self.download_deleted_data()
            self.download_data_validation()
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.utility.remove_directory(self.machine_object, self.test_path)


