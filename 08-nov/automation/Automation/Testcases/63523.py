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
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestStepFailure

class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole][EdgeMode]-Preview Check"""

    test_step = TestStep()

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][EdgeMode]-Preview Check"
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
        self.edgeshares = None

        # PRE-REQUISITES OF THE TESTCASE
        # - This testcase verifies previews working correctly for all types of the files
        #   So assuming folder path given in config file contains all types of the files and already backedup
        #---------------------------------------------------------------------------------------------------
    
    def setup(self):
        """Initializes objects required for this testcase"""
        self.tcinputs.update(EdgeHelper.set_testcase_inputs(self))
        self.log.info(""" Initialize browser objects """)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tcinputs["Edge_username"],
                                 self.tcinputs["Edge_password"])
        self.edgeHelper_obj = EdgeHelper(self.admin_console, self.commcell)
        self.edgemain_obj = EdgeMain(self.admin_console)
        self.rbrowse = RBrowse(self.admin_console)
        self.rtable = Rtable(self.admin_console)
        self.edgeshares = EdgeShares(self.admin_console)

    @test_step
    def validate_file_preview(self):
        """
        validate file Preview working correctly for all type of files backedup
        """
        preview_validation_failed_list=[]
        self.edgemain_obj.navigate_to_client_restore_page(self.tcinputs["Client_name"])
        self.rbrowse.navigate_path(self.tcinputs["Preview_Folder_path"], use_tree=False)
        browse_res= self.rtable.get_table_data()
        preview_failed_files, preview_details = self.edgeshares.verify_file_preview(browse_res['Name'])
        if  not preview_failed_files:
            self.log.info("**Previewed the files validation completed successfuly for all files**")
        else:
            raise CVTestStepFailure("preview validation failed for files {0}" .format(preview_failed_files))     
        
        for each_item in browse_res['Name']: 
            each_file_details = preview_details[each_item]
            details_list = each_file_details.rsplit('\n | \n')
            File_size = details_list[1]
            date_modified = details_list[2]
            file_idx = browse_res['Name'].index(each_item)
            if browse_res['Date modified'][file_idx]in date_modified and browse_res['Size'][file_idx] in File_size:
                self.log.info("--Previewd file details validation completed for file:{0} --".format(each_item))
            else:
                preview_validation_failed_list.append(each_item)

        if  not preview_validation_failed_list:
            self.log.info("previews files details validation completed successfully for all files")
        else:
            raise CVTestStepFailure("preview files details validation failed for files {0}" .format(preview_validation_failed_list))     
            

    def run(self):

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.edgeHelper_obj.validate_enduser_loggedin_url()
            self.edgeHelper_obj.verify_client_exists_or_not(self.tcinputs["Client_name"])
            self.validate_file_preview()
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

