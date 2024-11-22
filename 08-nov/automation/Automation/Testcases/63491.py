# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case"""

import time
import os
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


class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole][AdminMode]: File versions Restore validation as tenant admin"""

    test_step = TestStep()

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][AdminMode]: File versions Restore validation as tenant admin"
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
        self.laptop_obj = None
        self.laptop_utils = None
        self.client_name = None
        self.file_name = None
        self.file_path = None
        self.test_path = None
        self.rbrowse = None
        self.rtable = None
        self.folder_name= None
        self.edgerestore = None
        self.job_manager = None
        self.dest_path = None
        self.local_time = None
        self.client_name = None
        self.subclient_obj = None
        self.version_restored_dict = {}
        self.version_validation_dict = {}
        
        # PRE-REQUISITES OF THE TESTCASE
        # - Validating this testcase as Tenant admin login. 


    def setup(self):
        """Initializes objects required for this testcase"""
        self.tcinputs.update(EdgeHelper.set_testcase_inputs(self))
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
    def run_backup(self):
        """ Trigger backup """
        if self.tcinputs['Cloud_direct'] is True:
            self.log.info("initiating backup on cloud laptop client [{0}]".format(self.client_name))
            self.laptop_obj.trigger_cloudlaptop_backup(self.client_name, 
                                                       self.tcinputs['os_type'], 
                                                       backup_type='backup_from_actions')
        else:
            self.log.info("initiating backup on classic laptop client [{0}]".format(self.client_name))
            self.subclient_obj = self.idautils.get_subclient(self.client_name)
            _job_obj = self.idautils.subclient_backup(self.subclient_obj)
            
    @test_step
    def restore_all_versions(self):
        """ Restore all version files"""

        self.dest_path = self.utility.create_directory(self.machine_object)
        self.rtable.access_action_item(self.client_name, 'Restore')
        self.log.info("Client restore path is : [{0}]".format(self.tcinputs["Test_data_path"]))
        self.rbrowse.navigate_path(self.tcinputs["Test_data_path"], use_tree=False)
        self.rbrowse.select_files(file_folders=[self.file_name])
        self.rbrowse.select_action_dropdown_value(index=0, value='View versions')
        browse_res= self.rtable.get_table_data()
        no_of_version_files = len(browse_res['Name'])
        if not no_of_version_files==3:
            raise CVTestStepFailure("number of versions not showing correct [{0}]" .format(no_of_version_files))
        for i in range (0 , no_of_version_files):
            versionfile_to_select =browse_res['Name'][i]
            self.rbrowse.select_files(file_folders=[versionfile_to_select])
            restore_job_id = self.edgerestore.browse_and_restore(source_data_path=None, 
                                                                 dest_path=self.dest_path, 
                                                                 navigate_to_sourcepath=False)
            jobobj = self.commcell.job_controller.get(job_id=restore_job_id)
            self.job_manager.job = jobobj
            self.job_manager.wait_for_state('completed')
            self.rbrowse.clear_all_selection()

    @test_step
    def validate_restored_versions(self):
        """ validate restored version files"""
        
        restored_versions = self.machine_object.get_files_in_path(self.dest_path)
        if not len(restored_versions)==3:
            raise CVTestStepFailure("number of restored versions not showing correct on destination computer[{0}]" \
                                           .format(len(restored_versions)))

        for each_version  in restored_versions:
            file_name = os.path.basename(each_version)
            file_hash = self.machine_object.get_file_hash(each_version)
            self.version_restored_dict[file_name]=file_hash
            
        for dict_key, dict_val in self.version_validation_dict.items():
            self.log.info('validation verification for version file "{0}"'.format(dict_key))
            if dict_val == self.version_restored_dict[dict_key]:
                self.log.info("Backedup file version and restored file version both are same")
            else:
                raise CVTestStepFailure(
                    """
                    Backedup version Hash [{0}] does not match with restored version Hash [{1}] for version: [{2}]
                    """.format(dict_val, self.version_restored_dict[dict_key], dict_key)
                    )
            
    @test_step
    def create_versions_and_backup(self):
        """
        Create file versions and backup the file
        """
        self.machine_object.create_file(self.file_path, "*-Version 1 Test data-*")
        version1_cheksum = self.machine_object.get_file_hash(self.file_path)
        version1_file_name = 'FileVersions'+str(self.local_time)+ ",1" +".txt"
        self.version_validation_dict[version1_file_name]=version1_cheksum
        self.run_backup()
        self.machine_object.append_to_file(self.file_path, "**--Version 2 Test data--**")
        version2_cheksum = self.machine_object.get_file_hash(self.file_path)
        version2_file_name = 'FileVersions'+str(self.local_time)+ ",2" +".txt"
        self.version_validation_dict[version2_file_name]=version2_cheksum
        self.run_backup()
        self.machine_object.append_to_file(self.file_path, "***---Version 3 Test data---***")
        version3_cheksum = self.machine_object.get_file_hash(self.file_path)
        version3_file_name = 'FileVersions'+str(self.local_time)+ ",3" +".txt"
        self.version_validation_dict[version3_file_name]=version3_cheksum
        self.run_backup()

    def create_testpath(self):
        """
        Create File for version validation
        """
        self.client_name = self.tcinputs["Client_name"]
        self.local_time = int(time.time())
        if self.tcinputs['os_type']=="Windows":
            self.file_name = 'FileVersions'+str(self.local_time )+".txt"
            self.file_path = self.tcinputs["Test_data_path"] + '\\' + self.file_name
            
        else:
            self.file_name = 'FileVersions'+str(self.local_time )+".txt"
            self.file_path = self.tcinputs["Test_data_path"] + '/' + self.file_name
                          
    def run(self):

        try:
            self.laptop_obj.navigate_to_laptops_page()
            self.create_testpath()
            self.create_versions_and_backup()
            self.restore_all_versions()
            self.validate_restored_versions()
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.utility.remove_directory(self.machine_object, self.file_path)
            self.utility.remove_directory(self.machine_object, self.dest_path)

