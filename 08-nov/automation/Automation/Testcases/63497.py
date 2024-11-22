# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Laptop.LaptopEdgeMode import EdgeMain, EdgeSettings
from Web.AdminConsole.Helper.LaptopEdgeHelper import EdgeHelper
from Web.AdminConsole.Components.browse import RBrowse
from AutomationUtils.options_selector import OptionsSelector
from Laptop.laptoputils import LaptopUtils
from AutomationUtils.idautils import CommonUtils
from Reports.utils import TestCaseUtils
from Server.JobManager.jobmanager_helper import JobManager
from Web.AdminConsole.Components.table import Rtable
from Web.Common.exceptions import CVTestStepFailure

class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole][EdgeMode]-Backup functionality (Suspend /kill)for Laptop Clients"""

    test_step = TestStep()

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][EdgeMode]-Backup functionality (Suspend /kill)for Laptop Clients"
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
        self.folder_path_kill = None
        self.test_path = None
        self.rbrowse = None
        self.folder_name= None
        self.download_directory = None
        self.edgesettings = None
        self.job_manager = None
        self.driver = None
        self.navigator = None
        self.rtable = None
        self.dest_path = None
        self.folder_name_kill = None
        # PRE-REQUISITES OF THE TESTCASE
        # - Root folder of the "Test_data_path" is already created on machine and also added as subclient content
        # ------------This Test case is not applicable for v2 laptop ------------
        
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
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
       
        self.admin_console.login(self.tcinputs["Edge_username"],
                                  self.tcinputs["Edge_password"])
        self.edgeHelper_obj = EdgeHelper(self.admin_console, self.commcell)
        self.edgemain_obj = EdgeMain(self.admin_console)
        self.edgesettings = EdgeSettings(self.admin_console)
        self.rbrowse = RBrowse(self.admin_console)
        self.job_manager = JobManager(commcell=self.commcell)
        self.driver = self.admin_console.driver
        self.navigator = self.admin_console.navigator
        self.rtable = Rtable(self.admin_console)

    @test_step
    def verify_browse_result(self):
        """
        verify able to browse the File or not after job killed
        """
        browse_res= self.rtable.get_table_data()
        if self.folder_name_kill in browse_res['Name']:
            raise CVTestStepFailure("Kill backup job functionality failed as" +
                                            "folder [{0}] backed up even backup job is killed"
                                            .format(self.folder_path_kill))
        self.log.info("Kill backup job functionality is completed successfully")
        
    @test_step
    def validate_backupjob_kill_functionality(self):
        """
        verify Kill backup job functionality
        """
        client_name = self.tcinputs["Client_name"]
        self.laptop_utils.create_file(client=self.machine_object, 
                                      client_path=self.folder_path_kill, 
                                      files=10)
        self.navigator.navigate_to_devices_edgemode()
        self.edgemain_obj.navigate_to_client_settings_page(client_name)
        self.edgeHelper_obj.verify_any_backup_running()
        job_id = self.edgesettings.click_on_backup_button(wait=False)  # Trigger the backup
        self.edgesettings.kill_backup_job()
        jobobj = self.commcell.job_controller.get(job_id=job_id)
        self.job_manager.job = jobobj
        self.job_manager.wait_for_state('killed')
        self.edgemain_obj.navigate_to_client_restore_page(client_name)
        self.rbrowse.navigate_path(self.tcinputs["Test_data_path"], use_tree=False)
        self.verify_browse_result()
        
    @test_step
    def validate_backupjob_pause_and_resume(self):
        """
        verify Pause and resume functionality of the backup job
        """
        client_name = self.tcinputs["Client_name"]
        self.edgemain_obj.navigate_to_client_settings_page(client_name)
        self.edgeHelper_obj.verify_any_backup_running()
        job_id = self.edgesettings.click_on_backup_button(wait=False)  # Trigger the backup
        self.edgesettings.click_suspend_button(self.tcinputs['os_type'])
        self.edgesettings.wait_for_job_paused()
        self._log.info("Backup job has been paused successfully")
        jobobj = self.commcell.job_controller.get(job_id=job_id)
        self.job_manager.job = jobobj
        self.job_manager.wait_for_state('suspended')
        self.edgesettings.resume_backup_job()
        self.job_manager.wait_for_state('completed')
        self.edgeHelper_obj.source_dir=self.folder_path
        self.edgeHelper_obj.machine_object=self.machine_object
        #--Restore the data 
        self.edgemain_obj.navigate_to_client_restore_page(client_name)
        if self.tcinputs['os_type']!="Windows":
            self.machine_object.create_directory(self.dest_path)

        self.edgeHelper_obj.subclient_restore_as_enduser(tmp_path=self.dest_path)

    @test_step
    def create_testpath(self):
        """
        Create test path with required folders and files 
        """
        self.folder_name = 'TC_'+str(self.id)+'_Pause'
        self.folder_name_kill = 'TC_'+str(self.id)+'_Kill'
        if self.tcinputs['os_type']=="Windows":
            self.test_path = self.tcinputs["Test_data_path"]
            self.folder_path = self.machine_object.join_path(self.test_path, self.folder_name)
            self.folder_path_kill = self.machine_object.join_path(self.test_path, self.folder_name_kill)
            self.dest_path = None
            
        else:
            self.test_path = self.tcinputs["Test_data_path"]
            self.folder_path = self.machine_object.join_path(self.test_path, self.folder_name)
            self.folder_path_kill = self.machine_object.join_path(self.test_path, self.folder_name_kill)
            _restore_folder_name = 'TC_'+str(self.id)+'_Restore'
            self.dest_path =  self.machine_object.join_path(self.test_path, _restore_folder_name)
    
        self.laptop_utils.create_file(client=self.machine_object, 
                                      client_path=self.folder_path, 
                                      files=10)

    def run(self):

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.edgeHelper_obj.enduser = self.tcinputs["Edge_username"]
            self.edgeHelper_obj.validate_enduser_loggedin_url()
            self.edgeHelper_obj.verify_client_exists_or_not(self.tcinputs["Client_name"])
            self.create_testpath()
            self.validate_backupjob_pause_and_resume()
            self.validate_backupjob_kill_functionality()
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.utility.remove_directory(self.machine_object, self.folder_path)
            self.utility.remove_directory(self.machine_object, self.folder_path_kill)


