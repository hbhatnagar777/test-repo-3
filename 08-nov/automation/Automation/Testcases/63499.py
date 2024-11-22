# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case"""

import time
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
from Laptop import laptopconstants as lc

class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole][EdgeMode]- Verify Add/Remove contents for Laptop Clients"""

    test_step = TestStep()

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][EdgeMode]- Verify Add/Remove contents for Laptop Clients"
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
        self.include_content = None
        self.file_name = None
        self.remove_file = None
        self.documents_path = None
        self.documents_file_path = None
        self.exclude_file_path = None
        self.documents_remove_path = None
        self.rbrowse = None
        self.folder_name= None
        self.download_directory = None
        self.edgesettings = None
        self.job_manager = None
        self.driver = None
        self.navigator = None
        self.rtable = None
        self.removed_browse_path = None

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
        self.edgesettings = EdgeSettings(self.admin_console)
        self.rbrowse = RBrowse(self.admin_console)
        self.job_manager = JobManager(commcell=self.commcell)
        self.driver = self.admin_console.driver
        self.navigator = self.admin_console.navigator
        self.rtable = Rtable(self.admin_console)
        self.tcinputs = self.edgeHelper_obj.check_laptop_backup_mode(self.tcinputs)


    def cleanup(self):
        """
        cleanup the entities after validation
        """
        self.navigator.navigate_to_devices_edgemode()
        self.edgemain_obj.navigate_to_client_settings_page(self.tcinputs["Client_name"])
        self.edgesettings.remove_backup_content(self.include_content)
        self.edgesettings.remove_exclude_content(self.exclude_file_path)
        self.utility.remove_directory(self.machine_object, self.documents_file_path)
        self.utility.remove_directory(self.machine_object, self.exclude_file_path)
        self.utility.remove_directory(self.machine_object, self.documents_remove_path)

    @test_step
    def verify_browseresult_when_backup_content_added(self, client_name):
        """
        verify the browse result when content added
        """
        self.edgemain_obj.navigate_to_client_restore_page(client_name)
        self.log.info("Client path is : {0}".format(self.documents_path))
        self.rbrowse.navigate_path(self.documents_path, use_tree=False)
        browse_res= self.rtable.get_table_data()
        if not self.file_name in browse_res['Name']:
            raise CVTestStepFailure("Backed up file: {0} is not found in browse result".format(self.file_name))
        self.log.info("*** As Expected! Backed up file: '{0}' is found in browse result ***".format(self.file_name))

    @test_step
    def verify_browseresult_when_exclude_content_added(self, client_name):
        """
        verify the browse result when content excluded
        """
        self.edgemain_obj.navigate_to_client_restore_page(client_name)
        self.log.info("Client path is : {0}".format(self.tcinputs["Test_data_path"]))
        self.rbrowse.navigate_path(self.tcinputs["Test_data_path"], use_tree=False)
        browse_res= self.rtable.get_table_data()
        if self.file_name in browse_res['Name']:
            raise CVTestStepFailure("Excluded file: {0} is found in browse result".format(self.file_name))
        self.log.info("*** As Expected! Excluded file: '{0}' is not found in browse result ***".format(self.file_name))

    @test_step
    def verify_browseresult_when_content_removed(self, client_name):
        """
        verify the browse result after content removed
        """
        self.edgemain_obj.navigate_to_client_restore_page(client_name)
        self.log.info("Client path is : {0}".format(self.documents_path))
        self.rbrowse.navigate_path(self.removed_browse_path, use_tree=False)
        browse_res= self.rtable.get_table_data()
        if self.include_content in browse_res['Name']:
            raise CVTestStepFailure(" Removed path found in browse result".format(self.file_name))
        self.log.info("*** As Expected! removed content not found in browse result ***".format(self.file_name))

    @test_step
    def verify_add_content_functionality(self):
        """ verify add documents as content and run the backup"""
        # Adding the documents moniker to validate browse path from edit backup content tile
        client_name = self.tcinputs["Client_name"]
        self.edgemain_obj.navigate_to_client_settings_page(client_name)
        self.edgesettings.add_client_backup_content(content=[self.include_content])
        OptionsSelector(self._commcell).sleep_time(180, "CCSDB wait time to update the filter")
        self.laptop_utils.create_file(self.machine_object, self.documents_path, self.documents_file_path)
        if self.tcinputs['Cloud_direct'] is True:
            self.log.info("Trigger and validate backup on cloud client [{0}]".format(client_name))
            self.edgeHelper_obj.trigger_v2_laptop_backup(self.client_name, self.tcinputs['os_type'])
        else:
            self.edgeHelper_obj.trigger_v1_laptop_backup(self.tcinputs["Client_name"])
      
        self.verify_browseresult_when_backup_content_added(client_name)
        self.log.info("Add documents as content functionality verification completed successfully")

    @test_step
    def verify_exclude_content_functionality(self):
        """ verify exclude the content and validate backup functionality"""
        client_name = self.tcinputs["Client_name"]
        self.navigator.navigate_to_devices_edgemode()
        self.edgemain_obj.navigate_to_client_settings_page(client_name)
        self.edgesettings.add_client_exception_content(custom_path=[self.exclude_file_path])
        self.laptop_utils.create_file(self.machine_object, self.tcinputs["Test_data_path"], self.exclude_file_path)
        if self.tcinputs['Cloud_direct'] is True:
            self.log.info("Trigger and validate backup on cloud client [{0}]".format(client_name))
            self.edgeHelper_obj.trigger_v2_laptop_backup(self.client_name, 
                                                        self.tcinputs['os_type'], 
                                                        validate_logs=False)
        else:
            self.edgeHelper_obj.trigger_v1_laptop_backup(self.tcinputs["Client_name"])
        
        self.verify_browseresult_when_exclude_content_added(client_name)
        self.log.info("Exclude content functionality verification completed successfully") 

    @test_step
    def verify_remove_contnent_functionality(self):
        """ Remove the backup and exclude contents from backup tile and verify"""
        client_name = self.tcinputs["Client_name"]
        self.navigator.navigate_to_devices_edgemode()
        self.edgemain_obj.navigate_to_client_settings_page(client_name)
        self.edgesettings.remove_backup_content(self.include_content)
        self.edgesettings.remove_exclude_content(self.exclude_file_path)
        OptionsSelector(self._commcell).sleep_time(180, "waiting for remove content to be reflected in GUI")
        self.laptop_utils.create_file(self.machine_object, self.documents_path, self.documents_remove_path)
        subclient_obj = CommonUtils(self.commcell).get_subclient(client_name)
        backup_content_list = subclient_obj.content
        filter_content = subclient_obj.filter_content
        if self.include_content in backup_content_list:
            raise CVTestStepFailure("backup content is not removed from the subclient")
        if self.tcinputs["Test_data_path"] in filter_content:
            raise CVTestStepFailure("Filter content is not removed from the subclient")
         
        if self.tcinputs['Cloud_direct'] is True:
            self.edgeHelper_obj.trigger_v2_laptop_backup(self.client_name, 
                                                        self.tcinputs['os_type'], 
                                                        validate_logs=False)
        else:
            self.edgeHelper_obj.trigger_v1_laptop_backup(self.tcinputs["Client_name"])

        self.verify_browseresult_when_content_removed(client_name)

        self.log.info(" Remove content functionality verification completed successfully")

        
    def create_testpath(self):
        """
        Create test path with required folders and files
        """
        self.include_content = "Documents"
        local_time = int(time.time())
        self.file_name = 'backupfile_'+str(local_time)+".txt"
        self.remove_file = 'removefile_'+str(local_time)+".txt"
        if self.tcinputs['os_type']=="Windows":
            self.documents_path = lc.WINDOWS_PATH 
            self.documents_file_path = self.documents_path + '\\' + self.file_name
            self.exclude_file_path = self.tcinputs["Test_data_path"] + '\\' + self.file_name
            self.documents_remove_path = self.documents_path + '\\' + self.remove_file
            self.removed_browse_path = lc.WINDOWS_ADMIN_PATH
        else:
            self.documents_path = lc.MAC_PATH
            self.documents_file_path = self.documents_path + '/' + self.file_name
            self.exclude_file_path = self.tcinputs["Test_data_path"] + '/' + self.file_name
            self.documents_remove_path = self.documents_path + '/' + self.remove_file
            self.removed_browse_path = lc.MAC_HOME_PATH

    def run(self):

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.edgeHelper_obj.enduser = self.tcinputs["Edge_username"]
            self.edgeHelper_obj.validate_enduser_loggedin_url()
            self.edgeHelper_obj.verify_client_exists_or_not(self.tcinputs["Client_name"])
            self.create_testpath()
            self.verify_add_content_functionality()
            self.verify_exclude_content_functionality()
            self.verify_remove_contnent_functionality()
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            try:
                self.cleanup()
            except Exception as err:
                self.log.info("Cleanup failed with error {0}".format(err))
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

