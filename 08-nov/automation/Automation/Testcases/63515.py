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
from Web.AdminConsole.Laptop.LaptopEdgeMode import EdgeMain, EdgeShares
from Web.AdminConsole.Helper.LaptopEdgeHelper import EdgeHelper
from Web.AdminConsole.Components.browse import RBrowse
from Web.AdminConsole.Components.table import Rtable
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from AutomationUtils.options_selector import OptionsSelector
from Web.Common.exceptions import CVTestStepFailure

class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole][EdgeMode]- Download from Preview Page"""

    test_step = TestStep()

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][EdgeMode]- Download from Preview Page"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.browser = None
        self.admin_console = None
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
        self.edgeshares = None
        self.local_machine = None
        self.utils = None

        # PRE-REQUISITES OF THE TESTCASE
        # - This testcase verifies downloads from previews working correctly for all types of the files
        #   So assuming folder path given in config file contains all types of the files and already backedup
        #---------------------------------------------------------------------------------------------------
    
    def setup(self):
        """Initializes objects required for this testcase"""
        self.utils = TestCaseUtils(self)
        self.utils.reset_temp_dir()
        self.download_directory = self.utils.get_temp_dir()
        self.tcinputs.update(EdgeHelper.set_testcase_inputs(self))
        self.utility = OptionsSelector(self.commcell)
        self.local_machine = Machine()
        self.log.info(""" Initialize browser objects """)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.set_downloads_dir(self.download_directory)
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tcinputs["Edge_username"],
                                 self.tcinputs["Edge_password"])
        self.machine_object = self.utility.get_machine_object(
                self.tcinputs['Machine_host_name'],
                self.tcinputs['Machine_user_name'], 
                self.tcinputs['Machine_password']
            )
        
        self.edgeHelper_obj = EdgeHelper(self.admin_console, self.commcell)
        self.edgemain_obj = EdgeMain(self.admin_console)
        self.rbrowse = RBrowse(self.admin_console)
        self.rtable = Rtable(self.admin_console)
        self.edgeshares = EdgeShares(self.admin_console)

    @test_step
    def validate_download_from_file_preview(self):
        """
        validate download from file Preview working correctly for all type of files backedup
        """
        if self.tcinputs['os_type']=="Windows":
            path_delimeter =  '\\' 
        else:
            path_delimeter =  '/' 
        self.edgemain_obj.navigate_to_client_restore_page(self.tcinputs["Client_name"])
        self.rbrowse.navigate_path(self.tcinputs["Preview_Folder_path"], use_tree=False)
        browse_res= self.rtable.get_table_data()
        downloaded_files_hashes = self.edgeshares.verify_download_from_preview(browse_res['Name'], 
                                                                       self.local_machine,
                                                                       self.download_directory,
                                                                       self.utils)
        for each_file in browse_res['Name']:
            backupfile_hash = self.machine_object.get_file_hash(self.tcinputs["Preview_Folder_path"] + path_delimeter + each_file)
            if downloaded_files_hashes[each_file]==backupfile_hash:
                self.log.info("---Both backedup file hash and downloaded file has are same for file: {0}--".format(each_file))
            else:
                raise CVTestStepFailure("Backedup file hash {0} and downloaded file hash {1} does not match for file{3}" 
                                        .format(backupfile_hash, downloaded_files_hashes[each_file], each_file))     

    def run(self):

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.edgeHelper_obj.validate_enduser_loggedin_url()
            self.edgeHelper_obj.verify_client_exists_or_not(self.tcinputs["Client_name"])
            self.validate_download_from_file_preview()
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

