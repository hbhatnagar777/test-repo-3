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
from Web.AdminConsole.Laptop.LaptopEdgeMode import EdgeMain
from Web.AdminConsole.Helper.LaptopEdgeHelper import EdgeHelper
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.Components.table import Rtable
from AutomationUtils.options_selector import OptionsSelector
from Laptop.laptoputils import LaptopUtils
from AutomationUtils.idautils import CommonUtils
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestStepFailure, CVWebAutomationException

class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole][EdgeMode]- Erase / Delete data as end-user"""

    test_step = TestStep()

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][EdgeMode]- Erase / Delete data as end-user"
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
        self.rbrowse = None
        self.rtable = None
        self.navigator = None
        self.download_directory = None

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
        self.rbrowse = RBrowse(self.admin_console)
        self.rtable = Rtable(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.tcinputs = self.edgeHelper_obj.check_laptop_backup_mode(self.tcinputs)

    @test_step
    def verify_browse_result(self):
        """
        verify able to browse the File or not after deletion
        """
        self.edgemain_obj.navigate_to_client_restore_page(self.tcinputs["Client_name"])
        self.rbrowse.navigate_path(self.tcinputs["Test_data_path"], use_tree=False)
        browse_res= self.rtable.get_table_data()
        if self.file_name in browse_res['Name']:
            raise CVTestStepFailure("File: {0} found in browse result even after erased".format(self.file_name))
        self.log.info("*** As Expected ! File {0} is not found in browse result after erased ***".format(self.file_name))

    @test_step
    def validate_file_erase(self):
        """
        Erase / Delete File in edgemode 
        """
        self.edgemain_obj.navigate_to_client_restore_page(self.tcinputs["Client_name"])
        self.rbrowse.navigate_path(self.tcinputs["Test_data_path"], use_tree=False)
        self.rbrowse.select_files(file_folders=[self.file_name])
        self.rbrowse.select_action_dropdown_value(index=0, value='Delete')
        self.admin_console.click_button_using_text('Yes')
        notification = self.admin_console.get_notification()
        self.admin_console.wait_for_completion()
        if notification:
            raise CVWebAutomationException("Unexpected notification [%s] while deleting the folder"
                                           .format(notification))
        self.verify_browse_result()
        self.log.info("Run incremental backup and verify folder deleted perminently and not backedup again")
        self.navigator.navigate_to_devices_edgemode()
        if self.tcinputs['Cloud_direct'] is True:
            self.log.info("Trigger and validate backup on cloud client [{0}]".format(self.tcinputs["Client_name"]))
            self.edgeHelper_obj.trigger_v2_laptop_backup(self.tcinputs["Client_name"], 
                                                         self.tcinputs['os_type'],
                                                         validate_logs=False)
        else:
            self.edgeHelper_obj.trigger_v1_laptop_backup(self.tcinputs["Client_name"])
        self.verify_browse_result()
        
    @test_step
    def create_testpath(self):
        """
        Create test path with required folders and files 
        """
        local_time = int(time.time())
        self.file_name = 'Erasefile_'+str(local_time)+".txt"
        if self.tcinputs['os_type']=="Windows":
            self.file_path = self.tcinputs["Test_data_path"] + '\\' + self.file_name
        else:
            self.file_path = self.tcinputs["Test_data_path"] + '/' + self.file_name
        self.laptop_utils.create_file(self.machine_object, self.tcinputs["Test_data_path"], self.file_path)

    def run(self):

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.edgeHelper_obj.validate_enduser_loggedin_url()
            self.edgeHelper_obj.verify_client_exists_or_not(self.tcinputs["Client_name"])
            self.create_testpath()
            if self.tcinputs['Cloud_direct'] is True:
                self.log.info("Trigger and validate backup on cloud client [{0}]".format(self.tcinputs["Client_name"]))
                self.edgeHelper_obj.trigger_v2_laptop_backup(self.tcinputs["Client_name"], self.tcinputs['os_type'])
            else:
                self.edgeHelper_obj.trigger_v1_laptop_backup(self.tcinputs["Client_name"])

            self.validate_file_erase()
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.utility.remove_directory(self.machine_object, self.file_path)


