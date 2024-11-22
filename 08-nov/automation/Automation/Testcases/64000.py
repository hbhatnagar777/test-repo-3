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
from Web.AdminConsole.Helper.LaptopEdgeHelper import EdgeHelper
from Web.AdminConsole.Components.browse import RBrowse
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from Reports.utils import TestCaseUtils
from Laptop.laptoputils import LaptopUtils
from Web.AdminConsole.Components.table import Rtable
from Server.JobManager.jobmanager_helper import JobManager
from Web.Common.exceptions import CVTestStepFailure, CVWebAutomationException
from AutomationUtils.machine import Machine
from Web.AdminConsole.Helper.LaptopHelper import LaptopMain
from Laptop import laptopconstants

class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole][Adminmode] - Libraries browse and Download validation"""

    test_step = TestStep()

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][Adminmode] - Libraries browse and Download validation"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.browser = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.idautils = None
        self.laptop_utils = None
        self.utility = None
        self.edgeHelper_obj = None
        self.edgemain_obj = None
        self.machine_object= None
        self.client_name = None
        self.rbrowse = None
        self.rtable = None
        self.folder_name= None
        self.file_name = None
        self.file_path = None
        self.download_directory = None
        self.navigation_path = None
        self.folder_path = None
        self.job_manager = None
        self.laptop_obj = None
        self.valdiation_path  = None
        self.subclient_obj = None

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
        self.job_manager = JobManager(commcell=self.commcell)
        self.subclient_obj = self.idautils.get_subclient(self.tcinputs["Client_name"])
        self.tcinputs = self.edgeHelper_obj.check_laptop_backup_mode(self.tcinputs)

    @test_step
    def libraries_download_validation(self):
        """
        Libraries/ monikers Download validation 
        """
        local_machine = Machine()
        downloaded_folder_hashes = []
        client_folder_hashes = []
        self.laptop_obj.navigate_to_laptops_page()
        self.rtable.access_action_item(self.client_name, 'Restore')
        self.rbrowse.navigate_path(self.navigation_path, use_tree=False)
        self.rbrowse.select_files(file_folders=[self.folder_name])
        notification = self.rbrowse.submit_for_download()
        if not 'submitted for processing' in notification:
            raise CVWebAutomationException("Unexpected notification [{0}] while download request submitted"
                                           .format(notification))
        job_id = EdgeHelper.extarct_job_id_from_text(notification)
        jobobj = self.commcell.job_controller.get(job_id=job_id)
        self.job_manager.job = jobobj
        self.job_manager.wait_for_state('completed')
        self.log.info("Restoe job [{0}] completed successfully".format(job_id))
        self.utils.wait_for_file_to_download("zip", timeout_period=300)
        files = local_machine.get_files_in_path(self.download_directory)  # to extract Zip files
        for file in files:
            with zipfile.ZipFile(file, 'r') as zip_file:
                zip_file.extractall(self.download_directory)

        directory_path = self.download_directory + '\\' + self.folder_name
        downloaded_folder_rs = local_machine.get_folder_hash(directory_path)
        client_folder_rs = self.machine_object.get_folder_hash(self.folder_path)
        for each_val in downloaded_folder_rs:
            downloaded_folder_hashes.append(each_val[1])
        if self.tcinputs['os_type']=="Windows":
            for each_val in client_folder_rs:
                client_folder_hashes.append(each_val[1])
        else:
            for each_val in client_folder_rs:
                client_folder_hashes.append(each_val[0].split('=')[1])
        self.log.info("client folder files hashes: [{0}]".format(client_folder_hashes))
        self.log.info("downloaded folder files hashes: [{0}]".format(downloaded_folder_hashes))
        if not downloaded_folder_hashes.sort() == client_folder_hashes.sort():
            raise CVTestStepFailure("Hashes of both folders are not same for client: [{0}]".format(self.tcinputs["Client_name"]))
        self.log.info("Hashes of both folders are same for client: [{0}]".format(self.tcinputs["Client_name"]))
        
    @test_step
    def download_button_validation(self):
        """
        Verify able to see the Download button when user settings option selected
        """
        self.rbrowse.select_files(select_all=True)
        try:
            notification = self.rbrowse.submit_for_download()
            if notification:
                raise CVWebAutomationException("Able to see the download button when usersettings option is selected [{0}]"
                                           .format(notification))
        except Exception as excp:
            self.log.info("As expected ! unable to see the download button when usersettings option is selected [{0}]"
                                        .format(excp))
               
    @test_step
    def user_settings_browse_validation(self):
        """
        Libraries browse validation after user settings option selected
        """
        self.rbrowse.select_action_dropdown_value(self.admin_console.props['label.showUserSettings'])
        browse_res= self.rtable.get_table_data()
        if len(browse_res['Name'])>3:
            raise CVTestStepFailure("Monikers browse count is not showing correct")
        if "User Settings" not in  browse_res['Name']:
            raise CVTestStepFailure("Usersettings option not showing from browse after selected")
        for each_item in browse_res['Name']:
            if (each_item !='Desktop') and (each_item !='Documents') and (each_item !='User Settings'):
                raise CVTestStepFailure("Monikers browse is not showing correct data after Usersettings selected")
        self.log.info("USer settings browse validation completed successfully")
                
    @test_step
    def libraries_browse_validation(self):
        """
        Libraries/ monikers browse validation  
        """
        self.rtable.access_action_item(self.client_name, 'Restore')
        self.rbrowse.navigate_path(self.valdiation_path, use_tree=False)
        browse_res= self.rtable.get_table_data()
        if len(browse_res['Name'])>2:
            raise CVTestStepFailure("Monikers browse count is not showing correct")
        for each_item in browse_res['Name']:
            if each_item !='Desktop' and each_item !='Documents':
                raise CVTestStepFailure("Monikers browse is not showing correct data")
        self.log.info("Monikers browse validation completed successfully")

    @test_step
    def run_backup(self):
        """
        run the backup on the given client 
        """
        if self.tcinputs['Cloud_direct'] is True:
            self.log.info("initiating backup on cloud laptop client [{0}]".format(self.client_name))
            self.laptop_obj.trigger_cloudlaptop_backup(self.client_name, 
                                                       self.tcinputs['os_type'], 
                                                       backup_type='backup_from_actions')

        else:
            self.log.info("initiating backup on classic laptop client [{0}]".format(self.client_name))
            _job_obj = self.idautils.subclient_backup(self.subclient_obj)

    @test_step
    def create_testpath(self):
        """
        Create test path with required folders and files 
        """
        local_time = int(time.time())
        self.client_name = self.tcinputs["Client_name"]
        self.folder_name = 'TC_'+str(self.id)
        if self.tcinputs['os_type']=="Windows":
            test_path = self.tcinputs["Monikers_data_path"]
            self.folder_path = test_path + '\\' + self.folder_name
            file_name = 'backupfile_'+str(local_time)+".txt"
            self.file_path = self.folder_path + '\\' + file_name
            self.navigation_path = test_path.replace("C:\\Users", 'Users')
            self.valdiation_path = laptopconstants.WINDOWS_ADMIN_PATH.replace("C:\\Users", 'Users')

        else:
            test_path = self.tcinputs["Monikers_data_path"]
            self.folder_path = test_path + '/' + self.folder_name
            file_name = 'backupfile_'+str(local_time)+".txt"
            self.file_path = self.folder_path + '/' + file_name
            self.navigation_path = test_path
            self.valdiation_path = laptopconstants.MAC_HOME_PATH

        _path = self.utility.create_directory(targethost=self.machine_object, directory=self.folder_path)
        self.laptop_utils.create_file(self.machine_object, self.tcinputs["Monikers_data_path"], self.file_path)

    def run(self):

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.laptop_obj.navigate_to_laptops_page()
            self.create_testpath()
            self.run_backup()
            self.libraries_browse_validation()
            self.user_settings_browse_validation()
            self.download_button_validation()
            self.libraries_download_validation()
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.utility.remove_directory(self.machine_object, self.folder_path)


