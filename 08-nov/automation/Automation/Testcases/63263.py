from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module is used for configuring case manager
"""

import time
import datetime
from Web.AdminConsole.Components.panel import DropDown, ModalPanel
from Web.AdminConsole.Components.dialog import ModalDialog
from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import WebAction, PageService
from Web.Common.exceptions import CVWebAutomationException
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL
from Web.Common.cvbrowser import Browser, BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.GovernanceAppsPages.CaseManager import CaseManager
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.Components.table import Table

class TestCase(CVTestCase):
    """Class for Verification of case creation from Case
    Manager page with 'Continous' data collection for FS"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("Verification of case creation from Case Manager"
                     "page with 'Continous' data collection")
        self.data_collection = 'Continuous'
        self.current_time = int(time.time())
        self.delete_cases_older_than = 3
        self.case_name = None
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.activate = None
        self.case_manager = None
        self.jobs = None
        self.index_copy_job_id = None
        
        self.tcinputs = {
            "CaseName": None,
            "DCPlan": None,
            "ServerPlan": None,
            "DataType": None,
            "Custodians": None,
            "Keyword": None,
            "SQLServerName": None,
            "SQLUsername": None,
            "SQLPassword": None
        }

        self.mssql = None
        self.custodians_num = None
        self.table = None

    def init_tc(self):
        """Initial configuration for the test case"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open(maximize=True)
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode['commcell']['loginUsername'],
                self.inputJSONnode['commcell']['loginPassword'])

            self.activate = GovernanceApps(self.admin_console)
            self.case_manager = CaseManager(self.admin_console)
            self.jobs = Jobs(self.admin_console)
            self.table = Table(self.admin_console)

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()
            self.case_name = self.tcinputs['CaseName'] + str(int(time.time()))
            self.custodians = self.tcinputs['Custodians']

        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception
        
    @test_step
    def cleanup_previous_cases(self):
        """ Clean up cases older than 3 days"""
        try:
            self.table.apply_sort_over_column('Creation time')
            case_list = self.table.get_table_data()
            case_num = len(case_list['Creation time'])
            self.log.info(f'No of cases: {case_num}')
            self.log.info(case_list)
            for i in range(case_num):
                case_creation_time = case_list['Creation time'][i]
                epoch_time = int(time.mktime(
                    datetime.datetime.strptime(
                        case_creation_time, "%b %d, %Y %I:%M:%S %p").timetuple()))
                self.log.info(epoch_time)
                if self.current_time - epoch_time > (self.delete_cases_older_than * 86400):
                    self.case_manager.delete_case(case_list['Name'][i])
        except Exception:
            raise CVTestStepFailure("Error deleting case")

    def create_case_manager_client(self):
        """Enter basic details, custodians, keyword and save it"""
        self.fileServers=self.tcinputs['fileServers']
        try:
            self.case_manager.select_add_case()
            self.case_manager.enter_case_details(
                self.case_name,
                self.tcinputs['DataType'],
                self.data_collection,
                self.custodians,
                self.tcinputs['DCPlan'],
                self.tcinputs['ServerPlan'],
                self.tcinputs['Keyword'],
                fileServers=self.fileServers
            )
            
            self.log.info('Case Added')
        except Exception:
            raise CVTestStepFailure(f"Error entering details")
        
    @test_step
    def verify_case_manager_page(self):
        """Verifying that the case with the given name is listed in 'Case Manager' page"""
        try:
            self.navigator.navigate_to_governance_apps()
            self.activate.select_case_manager()
            
                      
            if self.table.is_entity_present_in_column('Name', self.case_name):
                self.log.info(
                    'VERIFIED: Case with given name listed in Case Manager page')
            else:
                raise CVTestStepFailure(
                    "Case with given name not listed in Case Manager page")
        except BaseException:
            raise CVTestStepFailure(
                "Error Verifying whether case listed in Case Manager page")
            
    @test_step             
    def get_client_id(self):
        """Get all the list of clients"""
        
        casename= self.case_name
        try:
            all_clients = self.client_object.all_clients()
            self.log.info("Client list is", all_clients)
            self.get_id=all_clients[casename]['id']
        except BaseException:
            raise CVTestStepFailure(
                "Unable to get client id")
            
             
        
    @test_step
    def submit_collection_job(self):
        """Verifying whether the Case Manager Index Copy Job has been submitted"""
        self.case_manager.submit_collection_job()
        self.log.info("job completion")

            
            
    @test_step
    def get_no_of_files(self):
        """Getting the number of files from admin console"""
        try:
            self.admin_console.refresh_page()
            self.case_manager.open_search_tab()
            self.case_manager.check_CMSTatus()
            self.browser.driver.find_element(By.ID, "searchPreview_button_#5268").click()
            self.log.info("Search successful")
            time.sleep(30)
            no_files = int(self.table.get_total_rows_count())
            self.log.info(no_files)
            if no_files >= 1:
                self.log.info("Number of files matched case")
                
        except Exception:
            raise CVTestStepFailure(
                f"Error getting the number of files from search")

    def run(self):
        """
        Testcase execution starts from here
        """
        try:
            self.init_tc()
            self.create_case_manager_client()
            self.submit_collection_job()
            time.sleep(700)
            self.get_no_of_files()
            self.verify_case_manager_page()
            self.log.info("Waiting for jobs to complete")
            time.sleep(700)
            self.case_manager.delete_case(self.case_name)
        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

