# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case"""

import time
from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Laptop.LaptopEdgeMode import EdgeMain, EdgeShares
from Web.AdminConsole.Helper.LaptopEdgeHelper import EdgeHelper
from AutomationUtils.options_selector import OptionsSelector
from Laptop.laptoputils import LaptopUtils
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestCaseInitFailure


class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole][EdgeMode]- Private Share Test- Edit Access"""

    test_step = TestStep()

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][EdgeMode]- Private Share Test- Edit Access"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.browser = None
        self.admin_console = None
        self.share_created_time = None
        self.share_access = None
        self.share_expire = None
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
        self.utils = TestCaseUtils(self)


        # PRE-REQUISITES OF THE TESTCASE
        # - "Root folder of the "Test_data_path" is already created on machine and also added as subclient content
        #----------------------------------------------------------------------------------
        #   This test case verifies Private Share With VIEW ACCESS and With NEVER EXPIRE permissions
        #------------------------------------------------------------------------------------
        
    def user_login(self, login_username, login_password):
        """ Login to commadncenter with given user """
        try:
            self.tcinputs.update(EdgeHelper.set_testcase_inputs(self))
            self.log.info(""" Initialize browser objects """)
            self.browser = BrowserFactory().create_browser_object()
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
        self.edgeshares.delete_private_share(self.folder_name)
        self._log.info("Deleted share has been validated successfully")
        self.edgeHelper_obj.validate_deleted_share(self.folder_name)
        AdminConsole.logout_silently(self.admin_console)
        self.driver.close()
        Browser.close_silently(self.browser)

    @test_step
    def validate_share_as_recepient(self):
        """
        Checking items has been shared and accessable by recepient
        """
        self.user_login(self.tcinputs["Private_share_recepient_username"],
                        self.tcinputs["Private_share_recepient_password"])
        self.edgeshares.navigate_to_webconsole_shares_page('SharedWithMe')
        self.edgeHelper_obj.validate_share_details_as_recepient(
                                            self.folder_name,
                                            self.tcinputs["Edge_username"],
                                            self.share_created_time,
                                            self.share_expire
                                            )
        
        self._log.info("Shared info has been validated successfully")
        AdminConsole.logout_silently(self.admin_console)
        self.driver.close()
        Browser.close_silently(self.browser)

    @test_step
    def validate_share_info_as_owner(self):
        """
        verifying shared data as owner by navigating to webconsole-->shares-->shared by me
        """
        self.edgeshares.navigate_to_webconsole_shares_page('SharedByMe')
        self.edgeHelper_obj.validate_share_details_as_owner(
                                            self.folder_name, 
                                            self.test_path, 
                                            self.share_created_time,
                                            self.share_expire
                                            )

        self._log.info("Shared info has been validated successfully from shares page as owner")
        self._log.info("-- Now will logout from adminconsole as owner--")
        AdminConsole.logout_silently(self.admin_console)
        self.driver.close()
        Browser.close_silently(self.browser)

    @test_step
    def create_private_share(self):
        """
        create private share with given options
        """
        self._log.info("Sharing a file /folder with access type as :{0} , Share access expire as : {1}"\
                            .format(self.share_access, self.share_expire))
        
        self.edgemain_obj.navigate_to_client_restore_page(self.tcinputs["Client_name"])
        current_time = datetime.now()
        self.share_created_time = current_time.strftime('%b %d, %Y %I:%M:%S %p')
        self.edgeshares.create_private_share(self.tcinputs["Test_data_path"],
                                             self.folder_name,
                                             self.recepient_user,
                                             self.share_access,
                                             self.share_expire)
    @test_step
    def create_testdata_and_backup(self):
        """Create test path with required folders and files"""
        self.folder_name = 'PrivateShareFolder_'+str(self.id)
        inner_folder_name = 'TC_'+str(self.id)
        
        local_time = int(time.time())
        if self.tcinputs['os_type']=="Windows":
            self.test_path = self.tcinputs["Test_data_path"] + '\\' + self.folder_name
            folder_path = self.test_path + '\\' +  inner_folder_name
            file_name = 'backupfile_'+str(local_time)+".txt"
            file_path = self.test_path + '\\' + file_name
            folder_file_name = folder_path + '\\' + file_name
            
        else:
            self.test_path = self.tcinputs["Test_data_path"] + '/' + self.folder_name
            folder_path = self.test_path + '/' +  inner_folder_name
            file_name = 'backupmacfile_'+str(local_time)+".txt"
            file_path = self.test_path + '/' + file_name
            folder_file_name = folder_path + '/' + file_name

        self.laptop_utils.create_file(client=self.machine_object, client_path=folder_path, file_path=file_path)
        
        self.laptop_utils.create_file(client=self.machine_object, client_path=folder_path, file_path=folder_file_name)        
        
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
        self.edgeshares.delete_private_share(self.folder_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

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
            self.share_access = self.tcinputs["Share_edit_access_type"]
            self.share_expire = self.tcinputs["Share_expire_days"]
            self.recepient_user = self.tcinputs["Private_share_recepient_username"]
            self.edgeHelper_obj.validate_enduser_loggedin_url()
            self.edgeHelper_obj.verify_client_exists_or_not(self.tcinputs["Client_name"])
            self.create_testdata_and_backup()
            self.create_private_share()
            self.validate_share_info_as_owner()
            self.validate_share_as_recepient()
            self.delete_the_share_as_owner()
            
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.cleanup()



