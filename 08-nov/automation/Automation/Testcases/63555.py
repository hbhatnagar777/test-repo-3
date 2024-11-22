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
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Laptop.Laptops import Laptops

class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole][AdminMode]: Hyper Links validation from laptop listing page """

    test_step = TestStep()
    
    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][AdminMode]: Hyper Links validation from laptop listing page"
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
    def validate_company_hyper_link(self, table_data):
        """
        hyper link validation for company column
        """
        company_name=table_data['Company'][0]
        self.laptop_obj.navigate_to_laptops_page()
        self.admin_console.wait_for_completion()
        self.rtable.click_reset_column_widths('Reset column widths')
        self.rtable.access_link(company_name)
        panel_info = RPanelInfo(self.admin_console, 'General').get_details()
        if panel_info['Company alias']== company_name:
            self.log.info("Successfully navigated to plan details page from Laptop listing page")
        else:
            raise CVTestStepFailure("not able to see correct plan details after navigated.current vale {0}"\
                                    .format(panel_info['Company alias']))

    @test_step
    def validate_plans_hyper_link(self, table_data):
        """
        hyper link validation for plan column
        """
        plan_name=table_data['Plans'][0]
        self.laptop_obj.navigate_to_laptops_page()
        self.admin_console.wait_for_completion()
        self.rtable.click_reset_column_widths('Reset column widths')
        self.rtable.access_link(plan_name)
        query =  """select id from app_plan where name = '{0}'""".format(plan_name)
        plan_result= self.utility.exec_commserv_query(query)
        plan_id = plan_result[0][0]
        current_url = self.driver.current_url.split("commandcenter")[1]
        expected_url = f'/#/profileDetails/{plan_id}'
        if not current_url==expected_url:
            raise CVTestStepFailure("Hyper link not working correctly for plans column for {0}".format(plan_name))
        else:
            title = PageContainer(self.admin_console).fetch_title()
            if title== plan_name:
                self.log.info("Successfully navigated to plans details page from Laptop listing page")
            else:
                raise CVTestStepFailure("not able to see correct plan name after navigated.current vale {0}"\
                                        .format(title))
    @test_step
    def validate_owner_hyper_link(self, table_data):
        """
        hyper link validation for Owner column
        """
        user_name=table_data['Owners'][0]
        self.laptop_obj.navigate_to_laptops_page()
        self.admin_console.wait_for_completion()
        self.rtable.click_reset_column_widths('Reset column widths')
        self.rtable.access_link(user_name)
        user_title = self.laptops.get_users_page_title()
        if user_title== user_name:
            self.log.info("Successfully navigated to user details page from Laptop listing page")
        else:
            raise CVTestStepFailure("not able to see correct username after navigated.current vale {0}"\
                                    .format(user_title))
                        
    @test_step
    def validate_name_hyper_link(self, table_data):
        """
        hyper link validation for Name column
        """
        self.rtable.click_reset_column_widths('Reset column widths')
        laptop_name=table_data['Name'][0]
        client_id = int(self._commcell.clients.get(name= laptop_name).client_id)
        self.rtable.access_link(laptop_name)
        self.admin_console.wait_for_completion()
        current_url = self.driver.current_url.split("commandcenter")[1]
        expected_url = f'/#/devices/{client_id}?mode=admin'
        if not current_url==expected_url:
            raise CVTestStepFailure("Hyper link not working correctly for Name column for client {0}".format(laptop_name))
        else:
            summary_dict = RPanelInfo(self.admin_console, 'Summary').get_details()
            if summary_dict['Host name']==laptop_name:
                self.log.info("Successfully navigated to Laptop details page from Laptop listing page")
            else:
                raise CVTestStepFailure("not able to see correct laptop name after navigated.current vale {0}"\
                                        .format(laptop_name))

    @test_step
    def validate_hyper_links(self):
        """
        Hyper Links validation from laptop listing page
        """
        self.rtable.search_for(self.tcinputs["Client_name"])
        self.rtable.click_grid_reset_button()
        hidden_colum_list= ['Company']
        self.rtable.display_hidden_column(hidden_colum_list)
        visible_columns = self.rtable.get_visible_column_names()
        visible_columns.remove('Actions')
        required_columns = ['Name', 'Owners', 'Plans', 'Company']
        hide_colums_from_display = list(set(visible_columns) - set(required_columns))                
        self.rtable.hide_selected_column_names(hide_colums_from_display)
        table_data = self.rtable.get_table_data()
        self.validate_name_hyper_link(table_data)
        self.validate_owner_hyper_link(table_data)      
        self.validate_plans_hyper_link(table_data) 
        if not table_data['Company'][0]=='CommCell':    
            self.validate_company_hyper_link(table_data)
        else:
            self.log.info("For given client Company is ** COMMCELL ** and does not have hyper link so not validating")

    def run(self):

        try:
            self.laptop_helper = LaptopHelper(self)
            self.tcinputs.update(EdgeHelper.set_testcase_inputs(self))
            self.utility = OptionsSelector(self.commcell)

            #-------------------------------------------------------------------------------------
            self.laptop_helper.tc.log_step("""

            From laptop listing page Below Columns have the hyper links and when click on these Columns 

            it should redirect to corresponding details page 
                1. Name: 
                2: Owner 
                3. Plans 
                4. Company  # if client belongs to commcell it does not have hyper link
                
            """, 200)

            #-------------------------------------------------------------------------------------

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
            self.validate_hyper_links()
            self.log.info("*****Hyper Links validation from laptop listing page completed successfully*****")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            self.laptop_obj.navigate_to_laptops_page()
            self.admin_console.wait_for_completion()
            self.rtable.click_grid_reset_button()
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

