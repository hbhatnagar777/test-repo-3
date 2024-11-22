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
from Web.AdminConsole.Laptop.LaptopEdgeMode import EdgeMain, EdgeShares
from Web.AdminConsole.Helper.LaptopEdgeHelper import EdgeHelper
from AutomationUtils.options_selector import OptionsSelector
from Laptop.laptoputils import LaptopUtils
from Reports.utils import TestCaseUtils
from AutomationUtils.machine import Machine
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure


class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole][EdgeMode]-Downloads from Public Share"""

    test_step = TestStep()

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][EdgeMode]-Downloads from Public Share"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.browser = None
        self.admin_console = None
        self.share_created_time = None
        self.share_access = None
        self.share_expire = None
        self.public_folder_name = None
        self.folder_name = None
        self.machine_object = None
        self.laptop_utils = None
        self.edgeHelper_obj = None
        self.edgemain_obj = None
        self.edgeshares = None
        self.utility = None
        self.test_path = None
        self.recepient_user = None
        self.driver = None
        self.public_share_link  = None
        self.share_validation_time = None
        self.folder_path = None
        self.file_name = None
        self.file_path = None
        self.folder_file_name= None
        self.driver = None
        self.download_directory = None
        self.tc_test_foldername = None
        self.download_dict = {}
        self.validation_dict = {}
        self.utils = TestCaseUtils(self)


        # PRE-REQUISITES OF THE TESTCASE
        # - "Root folder of the "Test_data_path" is already created on machine and also added as subclient content
        #----------------------------------------------------------------------------------
        #   This test case verifies Public Share With VIEW ACCESS and With NEVER EXPIRE permissions
        #------------------------------------------------------------------------------------
        
    def user_login(self, login_username, login_password):
        """ Login to commadncenter with given user """
        try:
            self.tcinputs.update(EdgeHelper.set_testcase_inputs(self))
            self.utils.reset_temp_dir()
            self.download_directory = self.utils.get_temp_dir()
            self.log.info(""" Initialize browser objects """)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.download_directory)
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(login_username, login_password)
            self.driver = self.browser.driver
            self.edgeHelper_obj = EdgeHelper(self.admin_console, self.commcell)
            self.edgemain_obj = EdgeMain(self.admin_console)
            self.edgeshares = EdgeShares(self.admin_console)
            
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    @test_step
    def delete_the_share_as_owner(self):
        """
        delete the share as owner and validate after deleted
        """
        self.user_login(self.tcinputs["Edge_username"],
                        self.tcinputs["Edge_password"])
        self.edgeshares.delete_private_share(self.tc_test_foldername, share_type='PublicShare', private_share=False)
        self._log.info("Deleted share has been validated successfully")
        self.edgeHelper_obj.validate_deleted_share(self.tc_test_foldername)
        AdminConsole.logout_silently(self.admin_console)
        self.driver.close()
        Browser.close_silently(self.browser)

    @test_step
    def validation_of_download(self):
        """
        validation of the files downloaded
        """
        downloaded_folder_hashes = []
        client_folder_hashes = []
        local_machine = Machine()
        client_name = self.tcinputs["Client_name"]
        #--Extract the downloaded folder 
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
    def download_of_public_share_validation_as_recepient(self):
        """
        Checking public share link is accessable and access the files /folders shared
        """
        # access the link and verify files shared correct or not
        self.user_login(self.tcinputs["Private_share_recepient_username"],
                        self.tcinputs["Private_share_recepient_password"])
        self.driver.get(self.public_share_link )
        self.edgeshares.download_items_from_shares(self.tc_test_foldername, select_all=True, navigate_to_folder=False)
        self.validation_of_download()
        self._log.info("-- Now will logout from adminconsole as recepient--")
        AdminConsole.logout_silently(self.admin_console)
        self.driver.close()
        Browser.close_silently(self.browser)
        
    @test_step
    def download_of_public_share_validation_as_owner(self, share_tab):
        """
        verifying downloads from public shares as owner
        """
        self.edgeshares.navigate_to_webconsole_shares_page(share_tab)
        self.edgeshares.download_items_from_shares(self.tc_test_foldername, select_all=True, navigate_to_folder=True)
        self.validation_of_download()
        self._log.info("downloads from shares has been validated successfully as owner")
        self._log.info("-- Now will logout from adminconsole as owner--")
        AdminConsole.logout_silently(self.admin_console)
        self.driver.close()
        Browser.close_silently(self.browser)

    @test_step
    def create_public_share(self):
        """
        create public share with given options
        """
        self._log.info("Sharing a file /folder with access type as :{0} , Share access expire as : {1}"\
                            .format(self.share_access, self.share_expire))
        
        self.edgemain_obj.navigate_to_client_restore_page(self.tcinputs["Client_name"])
        self.public_share_link = self.edgeshares.create_public_share(self.tcinputs["Test_data_path"], 
                                                                self.tc_test_foldername, 
                                                                self.share_expire)
    @test_step
    def create_testdata_and_backup(self):
        """Create test path with required folders and files"""
        self.folder_name = 'PublicShareFolder_'+str(self.id)
        self.tc_test_foldername = 'TC_'+str(self.id)
        local_time = int(time.time())
        self.test_path = self.machine_object.join_path(self.tcinputs["Test_data_path"], self.tc_test_foldername)
        self.folder_path = self.machine_object.join_path(self.test_path , self.folder_name)
        self.file_name = 'backupfile_'+str(local_time)+".txt"
        self.file_path = self.machine_object.join_path(self.test_path , self.file_name)
        self.folder_file_name = self.machine_object.join_path(self.folder_path, self.file_name)

        self.laptop_utils.create_file(client=self.machine_object, 
                                      client_path=self.folder_path, 
                                      file_path=self.file_path)
        
        self.laptop_utils.create_file(client=self.machine_object,
                                       client_path=self.folder_path,
                                       file_path=self.folder_file_name)       
        
        if self.tcinputs['Cloud_direct'] is True:
            self.log.info("Trigger and validate backup on cloud client [{0}]".format(self.tcinputs["Client_name"]))
            self.edgeHelper_obj.trigger_v2_laptop_backup(self.tcinputs["Client_name"], 
                                                         self.tcinputs['os_type'])
        else:
            self.edgeHelper_obj.trigger_v1_laptop_backup(self.tcinputs["Client_name"])
            
    def cleanup(self):
        """cleanup shares and other entities"""
        self.log.info("--Cleanup started--")
        self.utility.remove_directory(self.machine_object, self.test_path)
        self.user_login(self.tcinputs["Edge_username"], self.tcinputs["Edge_password"])
        self.edgeshares.delete_private_share(self.folder_name, share_type='PublicShare', private_share=False)

    def run(self):

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.tcinputs.update(EdgeHelper.set_testcase_inputs(self))
            self.user_login(self.tcinputs["Edge_username"],
                            self.tcinputs["Edge_password"])
            self.utility = OptionsSelector(self.commcell)
            self.edgeHelper_obj.client_name = self.tcinputs["Client_name"]
            self.laptop_utils = LaptopUtils(self)
            self.tcinputs = self.edgeHelper_obj.check_laptop_backup_mode(self.tcinputs)
            self.machine_object = self.tcinputs['client_object'] 
            self.share_access = self.tcinputs["Share_view_access_type"]
            self.share_expire = self.tcinputs["Share_never_expire"]
            self.edgeHelper_obj.validate_enduser_loggedin_url()
            self.edgeHelper_obj.verify_client_exists_or_not(self.tcinputs["Client_name"])
            self.create_testdata_and_backup()
            self.create_public_share()
            #validate downloads from shares as owner
            self.download_of_public_share_validation_as_owner('PublicShare')
            #validate downloads from shares as recepient
            self.download_of_public_share_validation_as_recepient()
            self.delete_the_share_as_owner()
            
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            self.cleanup()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)



