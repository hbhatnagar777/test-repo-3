# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.LaptopHelper import LaptopMain
from Laptop.laptophelper import LaptopHelper
from AutomationUtils.options_selector import OptionsSelector
from Server.Security.securityhelper import OrganizationHelper


class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole]: Backup Validation for Laptop """

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole]: Backup Validation for Laptop"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.browser = None
        self.admin_console = None
        self.laptop_obj = None
        self.utils = TestCaseUtils(self)
        self.laptop_helper = None
        self.organization = None
        self.source_path_dir = None
        self.utility = None
        self.install_kwargs = {}
        self.config_kwargs = {}

        # PRE-REQUISITES OF THE TESTCASE
        # - Tenant_company and Default_Plan should be created on commcell

    def run(self):

        try:
            self.utility = OptionsSelector(self._commcell)
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company1'))
            self.laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])
            self.organization = OrganizationHelper(self._commcell, self.tcinputs['Tenant_company'])

            dir_string = OptionsSelector.get_custom_str('TC_54212', 'Data')

            #-------------------------------------------------------------------------------------
            #install testcase [53807]
            self.laptop_helper.tc.log_step("""
                1. Set default plan for Tenant Company

                2. Execute SimCallWrapper and register the client with user [user1]

                3. Login to Adminconsole with Tenant Admin

                4. Go to Solutions->Laptop page on AdminConsole

                5. Verify suspend and resume backup from adminconsole and Validate backup
                
                6. validate the job by accessing view jobs link from laptop details page
                
                7. Restore the data from suspend and resumed backup job

            """, 200)

            #-------------------------------------------------------------------------------------

            self.log.info("Started executing %s testcase", self.id)
            self.refresh()

            #install laptop by creating custom package
            self.laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)

            self.laptop_helper.tc.log_step(""" Initialize browser objects """)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)

            self.admin_console.login(self.tcinputs['Tenant_admin'],
                                     self.tcinputs['Tenant_password'])

            self.laptop_obj = LaptopMain(self.admin_console, self.commcell)
            self.laptop_obj.client_name = self.tcinputs['Machine_host_name']
            self.laptop_obj.user_name = self.tcinputs['Machine_user_name']
            self.laptop_obj.password = self.tcinputs['Machine_password']
            self.laptop_obj.activation_user = self.tcinputs['Activation_User']
            self.laptop_obj.activation_plan = self.tcinputs['Default_Plan']
            self.laptop_obj.machine_object = self.tcinputs['Machine_object']
            self.laptop_helper.tc.log_step("Laptop Backup Validation started")
            if self.tcinputs['os_type'] == 'Windows':
                _source_data_dir = "C:\\Users\\Administrator\\Documents\\" + dir_string
               
                osc_options=None
            else:
                _source_data_dir = "/Users/cvadmin/Documents/" + dir_string
                
                osc_options='-testuser root -testgroup admin'
                
            #**** Creating test data in above directory *****
            self.source_path_dir = self.utility.create_directory(self.tcinputs['Machine_object'], _source_data_dir)
            _ = self.utility.create_test_data(self.tcinputs['Machine_object'],
                                               self.source_path_dir,
                                               file_size=5000,
                                               options=osc_options)
            
            self.laptop_obj.source_dir = self.source_path_dir
            self.laptop_helper.tc.log_step("Step1: Verification - Suspend and Resume backup job from details page")
            self.laptop_obj.navigate_to_laptops_page()
            backup_job_id = self.laptop_obj.perform_backup_now(suspend_resume=True, 
                                                               backup_type='backup_from_detailspage')
            
            self.laptop_helper.tc.log_step("Step2: Validation - Click on View Jobs from laptop details page to validate the backup job status")
            self.laptop_obj.view_jobs_validation(backup_job_id)

            self.laptop_helper.tc.log_step("Step3: Validation - Restore the data from Suspend & Resumed backup job and validate")
            self.laptop_obj.subclient_restore(backup_job_id, restore_type='restore_from_job')

            self.log.info("*****Laptop Backup Validation completed successfully*****")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.laptop_helper.cleanup(self.tcinputs)
            self.utility.remove_directory(self.tcinputs['Machine_object'], self.source_path_dir)

    def refresh(self):
        """ Refresh the dicts """
        self.config_kwargs.clear()
        self.install_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': False
        }

        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True,
            'post_osc_backup': False
        }
