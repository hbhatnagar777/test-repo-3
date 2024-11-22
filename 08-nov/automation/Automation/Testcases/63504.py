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
from AutomationUtils.idautils import CommonUtils
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestStepFailure, CVWebAutomationException
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole][EdgeMode] - Upload and download of single file/Live Browse functionality for Laptop Clients"""

    test_step = TestStep()

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][EdgeMode] - Upload and download of single file/Live Browse functionality for Laptop Clients"
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
        self.file_path = None
        self.file_name = None
        self.upload_file_path = None
        self.rbrowse = None
        self.rtable = None
        self.navigator = None
        self.download_directory = None
        self.local_machine = None
        self.client_file_path = None
        self.edgerestore = None
        self.driver = None

        # PRE-REQUISITES OF THE TESTCASE
        # - "Test_data_path" is already created on machine and also added as subclient content
        
    def setup(self):
        """Initializes objects required for this testcase"""
        self.utils.reset_temp_dir()
        self.download_directory = self.utils.get_temp_dir()
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
        self.browser.set_downloads_dir(self.download_directory)
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
        self.driver = self.admin_console.driver

    @test_step
    def verify_browse_result(self):
        """
        verify able to browse the File or not 
        """
        browse_res= self.rtable.get_table_data()
        if not self.file_name in browse_res['Name']:
            raise CVTestStepFailure("uploaded file {0} is not found in live browse results".format(self.file_name))
        self.log.info("*** As Expected ! uploaded file '{0}' is found in live browse result ***".format(self.file_name))
        
    @test_step
    def validate_livebrowse_file_upload(self):
        """
        verification of single file upload functionality in live browse
        """
        # - in angular when single file is uploaded in live browse, uploaded file shows from browse without any hard refresh
        # - But incase of multiple files upload need to refresh the page to see the files in browse 
        # - in automation, verifying the browse result with out any refresh for single file 
        #    and refreshing the page incase of multiple files to read from browse as per angular behaviour 

        self.log.info("verification of single file upload functionality started for client: {0}" .format(self.tcinputs["Client_name"]))
        self.edgemain_obj.navigate_to_client_restore_page(self.tcinputs["Client_name"])
        self.rbrowse.navigate_path(self.tcinputs["Test_data_path"], use_tree=False)
        self.rbrowse.select_action_dropdown_value(index=0, value='Show live machine data')
        self.edgerestore.upload_file_in_livebrowse(self.upload_file_path)
        self.edgerestore.track_upload_progress()
        self.verify_browse_result()
        self.log.info("verify hashes for upload file in live browse ")
        uploaded_file_hash = self.local_machine.get_file_hash(self.upload_file_path)
        self.log.info("Uploaded file hash: [{0}]".format(uploaded_file_hash))
        client_file_hash = self.machine_object.get_file_hash(self.client_file_path)
        self.log.info("client machine file hash: [{0}]".format(client_file_hash))
        if not uploaded_file_hash == client_file_hash:
            raise CVTestStepFailure("Hashes of both Files are not same for client: [{0}]".format(self.tcinputs["Client_name"]))
        self.log.info("Hashes of both Files are same for client: [{0}]".format(self.tcinputs["Client_name"]))

    @test_step
    def validate_livebrowse_file_download(self):
        """
        verification of single file download functionality in live browse
        """
        self.utils.reset_temp_dir()
        self.rbrowse.select_files(file_folders=[self.file_name])
        notification = self.rbrowse.submit_for_download()
        if notification:
            raise CVWebAutomationException("Unexpected notification [%s] while download request submitted"
                                           .format(notification))
        self.utils.wait_for_file_to_download("txt", timeout_period=300)
        downloaded_file_hash = self.local_machine.get_file_hash(self.upload_file_path)
        self.log.info("Downloaded file hash: [{0}]".format(downloaded_file_hash))
        client_file_hash = self.machine_object.get_file_hash(self.client_file_path)
        self.log.info("client machine file hash: [{0}]".format(client_file_hash))
        if not downloaded_file_hash == client_file_hash:
            raise CVTestStepFailure("Hashes of both Files are not same for client: [{0}]".format(self.tcinputs["Client_name"]))
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
        self.file_name = 'Livebrowse_upload_'+str(local_time)+".txt"
        if self.tcinputs['os_type']=="Windows":
            self.upload_file_path = temp_path + '\\' + self.file_name
            self.client_file_path = self.tcinputs["Test_data_path"] + '\\' + self.file_name
        else:
            self.upload_file_path = temp_path + '/' + self.file_name
            self.client_file_path = self.tcinputs["Test_data_path"] + '/' + self.file_name
        # create test data
        self.laptop_utils.create_file(self.local_machine, temp_path, self.upload_file_path)

    def run(self):

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.edgeHelper_obj.validate_enduser_loggedin_url()
            self.edgeHelper_obj.verify_client_exists_or_not(self.tcinputs["Client_name"])
            self.create_testpath()
            self.validate_livebrowse_file_upload()
            self.validate_livebrowse_file_download()
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.utility.remove_directory(self.machine_object, self.client_file_path)


