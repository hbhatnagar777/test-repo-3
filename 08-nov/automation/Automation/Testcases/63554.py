# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case"""

from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory, Browser
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.LaptopHelper import LaptopMain
from Laptop.laptophelper import LaptopHelper
from Web.Common.page_object import TestStep
from Web.AdminConsole.Helper.LaptopEdgeHelper import EdgeHelper
from Web.AdminConsole.Components.table import Rtable
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.Laptop.Laptops import Laptops

class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole][AdminMode]: Show / Hide Column grid validation from laptop listing page """

    test_step = TestStep()
    
    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][AdminMode]: Show / Hide Column grid validation from laptop listing page"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.browser = None
        self.admin_console = None
        self.laptop_obj = None
        self.utils = TestCaseUtils(self)
        self.utility = None
        self.laptop_helper = None
        self.client_obj = None
        self.rtable = None
        self.driver = None
        self.laptops = None
        
        # PRE-REQUISITES OF THE TESTCASE
        # - Validating this testcase as MSP admin login. 
        #   Makesure MSP ADMIN username and password updated in config file


    @test_step
    def validate_reset_button(self):
        """
        validate reset button from grid working correctly
        """
        self.rtable.search_for(self.tcinputs["Client_name"])
        self.rtable.click_grid_reset_button()
        visible_columns = self.rtable.get_visible_column_names()
        default_columns = ['Name',
                           'Owners', 
                           'User name', 
                           'Email', 
                           'Configured', 
                           'Last backup', 
                           'Last job status',
                           'Application size',
                           'Plans',
                           'SLA status',
                           'Last successful backup',
                           'Tags']
        
        visible_columns.remove('Actions')
        visible_columns.sort()
        default_columns.sort()
        if visible_columns != default_columns: 
            raise CVTestStepFailure("Issue with Reset button default columns not showing correctly from listing page [{0}]"\
                                        .format(visible_columns))
        self._log.info("reset button validation completed successfully")

    @test_step
    def validate_show_hidden_columns_from_grid(self):
        """
        Validate able to select hidden columns from grid or not
        """
        self.rtable.search_for(self.tcinputs["Client_name"])
        self.rtable.click_grid_reset_button()
        column_list= ['SLA reason', 'Version']
        self.rtable.display_hidden_column(column_list)
        visible_columns = self.rtable.get_visible_column_names()
        for each_column in column_list:
            if not each_column in visible_columns:
                raise CVTestStepFailure("unable to find new columns from listing page [{0}]"\
                                            .format(visible_columns))
        self._log.info("select hidden columns and display validation completed successfully")


    @test_step
    def validate_remove_display_columns_from_grid(self):
        """
        Validate able to hide the display columns from grid or not
        """
        self.rtable.search_for(self.tcinputs["Client_name"])
        self.rtable.click_grid_reset_button()
        visible_columns = self.rtable.get_visible_column_names()
        visible_columns.remove('Actions')
        required_columns = ['Name', 'Owners', 'Email', 'Plans']
        hide_colums_from_display = list(set(visible_columns) - set(required_columns))                
        self.rtable.hide_selected_column_names(hide_colums_from_display)
        latest_visible_columns = self.rtable.get_visible_column_names()
        latest_visible_columns.remove('Actions')
        latest_visible_columns.sort() 
        required_columns.sort() 
        if latest_visible_columns != required_columns: 
            raise CVTestStepFailure("columns not showing correctly after removed[{0}]"\
                                        .format(latest_visible_columns))
        self._log.info(" hide display columns validation completed successfully")
                      
                          
    def run(self):

        try:
            self.laptop_helper = LaptopHelper(self)
            self.tcinputs.update(EdgeHelper.set_testcase_inputs(self))
            self.utility = OptionsSelector(self.commcell)

            self.log.info("Started executing %s testcase", self.id)

            self.laptop_helper.tc.log_step(""" Initialize browser objects """)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login()
            self.laptop_obj = LaptopMain(self.admin_console, self.commcell)
            self.driver = self.admin_console.driver
            self.rtable = Rtable(self.admin_console)
            self.laptops = Laptops(self.admin_console)
            self.laptop_obj.client_name = self.tcinputs["Client_name"]
            self.laptop_obj.navigate_to_laptops_page()
            self.validate_reset_button()
            self.validate_show_hidden_columns_from_grid()
            self.validate_remove_display_columns_from_grid()
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            self.laptop_obj.navigate_to_laptops_page()
            self.admin_console.wait_for_completion()
            self.rtable.click_grid_reset_button()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

