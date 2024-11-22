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
from Web.AdminConsole.Laptop.LaptopEdgeMode import EdgeMain, EdgeRestore
from Web.AdminConsole.Helper.LaptopEdgeHelper import EdgeHelper
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.Components.table import Rtable
from AutomationUtils.options_selector import OptionsSelector
from Laptop.laptoputils import LaptopUtils
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestStepFailure
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole][EdgeMode]-Upload test cases"""

    test_step = TestStep()

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][EdgeMode]-Upload test cases"
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
        self.upload_file_path = None
        self.rbrowse = None
        self.rtable = None
        self.navigator = None
        self.local_machine = None
        self.edgerestore = None
        self.driver = None
        self.file_names = None
        self.client_file_path = None
        self.upload_file_path = None
        self.client_path = None
        self.file_name = None
        self.upload_file_paths = None

        # PRE-REQUISITES OF THE TESTCASE
        # - "Test_data_path" is already created on machine and also added as subclient content
        
    def setup(self):
        """Initializes objects required for this testcase"""
        upload_directory = self.utils.get_temp_dir()
        self.tcinputs.update(EdgeHelper.set_testcase_inputs(self))
        self.utility = OptionsSelector(self.commcell)
        self.laptop_utils = LaptopUtils(self)
        self.machine_object = self.utility.get_machine_object(
                self.tcinputs['Machine_host_name'],
                self.tcinputs['Machine_user_name'], 
                self.tcinputs['Machine_password']
            )
        self.log.info(""" Initialize browser objects """)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.set_downloads_dir(upload_directory)
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
       
        self.admin_console.login(self.tcinputs["Edge_username"],
                                 self.tcinputs["Edge_password"])
        self.edgeHelper_obj = EdgeHelper(self.admin_console, self.commcell)
        self.edgemain_obj = EdgeMain(self.admin_console)
        self.edgerestore = EdgeRestore(self.admin_console)
        self.rbrowse = RBrowse(self.admin_console)
        self.rtable = Rtable(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.tcinputs = self.edgeHelper_obj.check_laptop_backup_mode(self.tcinputs)

    @test_step
    def verify_single_upload_browse_result(self):
        """
        verify able to browse uploaded file after backup
        """
        self.edgemain_obj.navigate_to_client_restore_page(self.tcinputs["Client_name"])
        self.rbrowse.navigate_path(self.tcinputs["Test_data_path"], use_tree=False)
        browse_res= self.rtable.get_table_data()
        if not self.file_name in browse_res['Name']:
            raise CVTestStepFailure("uploaded file {0} is not found browse results after backup".format(self.file_name))
        self.log.info("*** As Expected ! uploaded file '{0}' is found in browse result ***".format(self.file_name))


    @test_step
    def verify_multfile_upload_browse_result(self):
        """
        verify able to browse the File 
        """
        self.edgemain_obj.navigate_to_client_restore_page(self.tcinputs["Client_name"])
        self.rbrowse.navigate_path(self.tcinputs["Test_data_path"], use_tree=False)
        browse_res= self.rtable.get_table_data()
        for each_file in self.file_names:
            if not each_file in browse_res['Name']:
                raise CVTestStepFailure("uploaded file {0} is not found browse results".format(each_file))
            self.log.info("*** As Expected ! uploaded file '{0}' is found in browse result ***".format(each_file))
            
    @test_step
    def trigger_backup(self):
        """
        trigger the backup after file is uploaded to client
        """
        self.navigator.navigate_to_devices_edgemode()
        if self.tcinputs['Cloud_direct'] is True:
            self.log.info("Trigger and validate backup on cloud client [{0}]".format(self.tcinputs["Client_name"]))
            self.edgeHelper_obj.trigger_v2_laptop_backup(self.tcinputs["Client_name"], self.tcinputs['os_type'])
        else:
            self.edgeHelper_obj.trigger_v1_laptop_backup(self.tcinputs["Client_name"])
        
    @test_step
    def verify_single_file_upload(self):
        """
        verification of file upload functionality 
        """
        self.edgemain_obj.navigate_to_client_restore_page(self.tcinputs["Client_name"])
        self.rbrowse.navigate_path(self.tcinputs["Test_data_path"], use_tree=False)
        self.edgerestore.upload_file_in_livebrowse(self.upload_file_path)
        self.edgerestore.track_upload_progress()
        self.admin_console.wait_for_completion()
        self.log.info("validating hashes from both local machine and client machine after folder uploaded ")
        uploaded_file_hash = self.local_machine.get_file_hash(self.upload_file_path)
        self.log.info("Uploaded file hash: [{0}]".format(uploaded_file_hash))
        client_file_hash = self.machine_object.get_file_hash(self.client_path)
        self.log.info("client machine file hash: [{0}]".format(client_file_hash))
        if not uploaded_file_hash == client_file_hash:
            raise CVTestStepFailure("Hashes of both Files are not same : [{0}]  [{1}]" \
                                    .format(uploaded_file_hash, client_file_hash))
        self.log.info("Hashes of both Files are same for client: [{0}]".format(self.tcinputs["Client_name"]))
        
    @test_step
    def verify_multi_file_upload(self):
        """
        verification of multiple files upload functionality 
        """
        self.edgemain_obj.navigate_to_client_restore_page(self.tcinputs["Client_name"])
        self.rbrowse.navigate_path(self.tcinputs["Test_data_path"], use_tree=False)
        self.edgerestore.upload_file_in_livebrowse(self.upload_file_paths)
        self.edgerestore.track_upload_progress()
        self.admin_console.wait_for_completion()
        self.log.info("validating hashes from both local machine and client machine after folder uploaded ")
        for idx, file_path in enumerate(self.upload_file_paths):
            uploaded_file_hash = self.local_machine.get_file_hash(file_path)
            client_file_hash = self.machine_object.get_file_hash(self.client_file_path[idx])
            if not uploaded_file_hash == client_file_hash:
                raise CVTestStepFailure("Hashes of both Files are not same : [{0}]  [{1}]" \
                                        .format(uploaded_file_hash, client_file_hash))
            self.log.info("Hashes of both Files are same for client: [{0}]".format(self.tcinputs["Client_name"]))   
        
    @test_step
    def create_testpath(self):
        """
        Create test path with required folders and files 
        """
        self.local_machine = Machine()  # create test data
        self.utils.reset_temp_dir()
        temp_path = self.utils.get_temp_dir()
        local_time = int(time.time())
        self.file_names = []
        self.client_file_path = []
        self.upload_file_paths=[]
        self.file_name = 'File_upload_'+str(local_time)+".txt"
        file_name_01 = 'multifile_upload_01_'+str(local_time)+".txt"
        file_name_02 = 'multifile_upload_02_'+str(local_time)+".txt"

        if self.tcinputs['os_type']=="Windows":

            self.upload_file_path = temp_path + '\\' + self.file_name
            self.client_path = self.tcinputs["Test_data_path"] + '\\' + self.file_name
            upload_file_path_01 = temp_path + '\\' + file_name_01
            upload_file_path_02 = temp_path + '\\' + file_name_02
            client_file_path1 = self.tcinputs["Test_data_path"] + '\\' + file_name_01
            client_file_path2 = self.tcinputs["Test_data_path"] + '\\' + file_name_01
            self.client_file_path.extend([client_file_path1, client_file_path2])
            self.file_names.extend([file_name_01, file_name_02])
            self.upload_file_paths.extend([upload_file_path_01, upload_file_path_02])
            
        else:
            self.upload_file_path = temp_path + '/' + self.file_name
            self.client_path = self.tcinputs["Test_data_path"] + '/' + self.file_name
            upload_file_path_01 = temp_path + '/' + file_name_01
            upload_file_path_02 = temp_path + '/' + file_name_02
            client_file_path1 = self.tcinputs["Test_data_path"] + '/' + file_name_01
            client_file_path2 = self.tcinputs["Test_data_path"] + '/' + file_name_01
            self.client_file_path.extend([client_file_path1, client_file_path2])
            self.file_names.extend([file_name_01, file_name_02])
            self.upload_file_paths.extend([upload_file_path_01, upload_file_path_02])
        # create test data
        self.laptop_utils.create_file(self.local_machine, temp_path, self.upload_file_path)
        for each_filepath in self.upload_file_paths:
            self.laptop_utils.create_file(self.local_machine, temp_path, each_filepath)

        
    def run(self):

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.edgeHelper_obj.validate_enduser_loggedin_url()
            self.edgeHelper_obj.verify_client_exists_or_not(self.tcinputs["Client_name"])
            self.create_testpath()
            self.log.info("single file upload validations started")
            self.verify_single_file_upload()
            self.trigger_backup()
            self.verify_single_upload_browse_result()
            self.log.info("multifile upload validations started")
            self.verify_multi_file_upload()
            self.trigger_backup()
            self.verify_multfile_upload_browse_result()

            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.utility.remove_directory(self.machine_object, self.client_path)
            try:
                for each_path in self.client_file_path:
                    self.utility.remove_directory(self.machine_object, each_path)
            except Exception as err:
                self.log.info("Failed to delete test data{0}".format(err))

