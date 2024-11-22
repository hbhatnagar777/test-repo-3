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
from Web.AdminConsole.Laptop.LaptopEdgeMode import EdgeMain, EdgeRestore
from Web.AdminConsole.Helper.LaptopEdgeHelper import EdgeHelper
from Web.AdminConsole.Components.browse import RBrowse
from AutomationUtils.options_selector import OptionsSelector
from Laptop.laptoputils import LaptopUtils
from AutomationUtils.idautils import CommonUtils
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Components.table import Rtable
from Server.JobManager.jobmanager_helper import JobManager
from AutomationUtils.machine import Machine
from Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole][EdgeMode]- Validation of Versions Download for Laptop Clients"""

    test_step = TestStep()

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][EdgeMode]- Validation of Versions Download for Laptop Clients"
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
        self.file_name = None
        self.file_path = None
        self.test_path = None
        self.rbrowse = None
        self.rtable = None
        self.folder_name= None
        self.download_directory = None
        self.edgerestore = None
        self.job_manager = None
        self.dest_path = None
        self.local_time = None
        self.version_download_dict = {}
        self.version_validation_dict = {}


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
        self.rtable = Rtable(self.admin_console)
        self.edgerestore = EdgeRestore(self.admin_console)
        self.job_manager = JobManager(commcell=self.commcell)
        self.tcinputs = self.edgeHelper_obj.check_laptop_backup_mode(self.tcinputs)

    @test_step
    def run_backup(self):
        """ Trigger backup """
        if self.tcinputs['Cloud_direct'] is True:
            self.log.info("initiating backup on cloud laptop client [{0}]".format(self.tcinputs["Client_name"]))
            self.edgeHelper_obj.trigger_v2_laptop_backup(self.tcinputs["Client_name"], self.tcinputs['os_type'])
        else:
            self.log.info("initiating backup on classic laptop client [{0}]".format(self.tcinputs["Client_name"]))
            self.edgeHelper_obj.trigger_v1_laptop_backup(self.tcinputs["Client_name"])

    @test_step
    def download_all_versions(self):
        """ download all version files"""
        self.dest_path = self.utility.create_directory(self.machine_object)
        self.edgemain_obj.navigate_to_client_restore_page(self.tcinputs["Client_name"])
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
            self.rbrowse.submit_for_download()
            self.utility.sleep_time(30, "Waiting download of the file to be completed")
            self.rbrowse.clear_all_selection()

    @test_step
    def validate_download_versions(self):
        """ validate download version files"""
        local_machine = Machine()
        download_versions = local_machine.get_files_in_path(self.download_directory)
        if not len(download_versions)==3:
            raise CVTestStepFailure("number of download versions not showing correct on destination computer[{0}]" \
                                           .format(len(download_versions)))

        for each_version  in download_versions:
            file_name = os.path.basename(each_version)
            file_hash = local_machine.get_file_hash(each_version)
            self.version_download_dict[file_name]=file_hash
        
        for dict_key, dict_val in self.version_validation_dict.items():
            self.log.info('validation verification for version file "{0}"'.format(dict_key))
            if dict_val == self.version_download_dict[dict_key]:
                self.log.info("Backedup file version and downloaded file version both are same")
            else:
                raise CVTestStepFailure(
                    """
                    Backedup version Hash [{0}] does not match with downloaded version Hash [{1}] for version: [{2}]
                    """.format(dict_val, self.version_download_dict[dict_key], dict_key)
                    )
            
    @test_step
    def create_versions_and_backup(self):
        """
        Create file versions and backup the file
        """
        self.machine_object.create_file(self.file_path, "*-Version 1 Test data-*")
        version1_cheksum = self.machine_object.get_file_hash(self.file_path)
        version1_file_name = 'FileVersions'+str(self.local_time)+ ".txt"
        self.version_validation_dict[version1_file_name]=version1_cheksum
        self.run_backup()
        self.machine_object.append_to_file(self.file_path, "**--Version 2 Test data--**")
        version2_cheksum = self.machine_object.get_file_hash(self.file_path)
        version2_file_name = 'FileVersions'+str(self.local_time)+ " (1)" +".txt"
        self.version_validation_dict[version2_file_name]=version2_cheksum
        self.run_backup()
        self.machine_object.append_to_file(self.file_path, "***---Version 3 Test data---***")
        version3_cheksum = self.machine_object.get_file_hash(self.file_path)
        version3_file_name = 'FileVersions'+str(self.local_time)+ " (2)" +".txt"
        self.version_validation_dict[version3_file_name]=version3_cheksum
        self.run_backup()

    def create_testpath(self):
        """
        Create File for version validation
        """
        self.local_time = int(time.time())
        if self.tcinputs['os_type']=="Windows":
            self.file_name = 'FileVersions'+str(self.local_time )+".txt"
            self.file_path = self.tcinputs["Test_data_path"] + '\\' + self.file_name
            
        else:
            self.file_name = 'FileVersions'+str(self.local_time )+".txt"
            self.file_path = self.tcinputs["Test_data_path"] + '/' + self.file_name

    def run(self):

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.edgeHelper_obj.enduser = self.tcinputs["Edge_username"]
            self.edgeHelper_obj.validate_enduser_loggedin_url()
            self.edgeHelper_obj.verify_client_exists_or_not(self.tcinputs["Client_name"])
            self.create_testpath()
            self.create_versions_and_backup()
            self.download_all_versions()
            self.validate_download_versions()
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.utility.remove_directory(self.machine_object, self.file_path)


