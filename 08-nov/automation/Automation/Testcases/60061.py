# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# -------------------------------------------------------------------------

""""Main file for executing this test case"""

import time
import datetime
from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.endpoint import EndPoint
from Laptop.laptophelper import LaptopHelper
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.Helper.LaptopHelper import LaptopMain
from Laptop.laptophelper import LaptopHelperMetallic
from Reports.utils import TestCaseUtils
from Metallic.hubutils import HubManagement
from Web.AdminConsole.Laptop.LaptopEdgeMode import EdgeMain
from Web.AdminConsole.Helper.LaptopEdgeHelper import EdgeHelper
from Laptop import laptopconstants as lc
from AutomationUtils.config import get_config

class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole]: Metallic_Laptop_Acceptance """

    test_step = TestStep()

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole]: Metallic_Laptop_Acceptance"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.browser = None
        self.admin_console = None
        self.laptop_obj = None
        self.utils = TestCaseUtils(self)
        self.utility = None
        self.laptop_helper = None
        self.organization = None
        self.client_obj = None
        self.metallic_laptop_helper = None
        self.custompkg_directory = None
        self.install_kwargs = {}
        self.config_kwargs = {}
        self.windows = False
        self.laptop_obj = None
        self.mac = False
        self.companyname = None
        self.default_plan = None
        self.tenant_company = None
        self.hubmgr=None
        self.commcell_host=None
        self.tenant_username=None
        self.tenant_pwd=None
        self.edgeuser=None
        self.endpoint_obj=None
        self.commcell_obj=None
        self.source_path_dir=None
        self.ring_hostname=None
        self.config = get_config()
        self.machine_object=None
        self.edgeHelper_obj = None
        self.edgemain_obj = None

        self.tcinputs = {
            "os_type": None,
            "ring_hostname":None
        }
        # - On metallic create new Tenant_company 
    def create_tenant(self):
        """create tenant user"""
        suffix = str(int(time.time()))
        firstname = 'Endpoint-Automation'
        lastname = datetime.datetime.now().strftime("%d-%B-%H-%M")
        self.companyname = datetime.datetime.now().strftime("Endpoint-Automation-%d-%B-%H-%M")
        email = "cvautouser" + suffix + "@test.com"
        self.hubmgr = HubManagement(self, self.commcell.webconsole_hostname)
        self.tenant_username = self.hubmgr.create_tenant(self.companyname, email, firstname, lastname, "888-888-8886")
        self.tenant_pwd = self.config.Metallic.tenant_password

        # - On metallic create edge user to activate the laptop 
    def create_Edgeuser(self):
        """create tenant user"""
        self.edgeuser = self.hubmgr.create_tenant_user('Edgeuser', email='Edgeuser@%s' % self.companyname)
        self.hubmgr.reset_user_password(self.edgeuser)
               
    def setup(self):
    
        platform_inputs = [
             "Machine_host_name",
             "Machine_user_name",
             "Machine_password"
        ]
        self.log.info("%s Creating new tenant %s", "*" * 15, "*" * 15)
        self.utility = OptionsSelector(self._commcell)
        self.create_tenant()
        self.create_Edgeuser()
        
        testcase_inputs = LaptopHelper.set_inputs(
            self, 'Company1', [], platform_inputs, self.tcinputs["os_type"]
         )
        self.tcinputs.update(testcase_inputs)
        self.log.info("%s initializing browser objects %s", "*" * 15, "*" * 15)
        self.utils.reset_temp_dir()
        self.custompkg_directory = self.utils.get_temp_dir()
        self.log.info("Setting the Download directory for custom package:%s", self.custompkg_directory)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.set_downloads_dir(self.custompkg_directory)
        self.log.info("%s Opening the browser %s", "*" * 15, "*" * 15)
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=self.tenant_username,
                                 password=self.tenant_pwd)
        #### Dashboard operations for new tenant ####
        self.endpoint_obj = EndPoint(self.admin_console)
        self.endpoint_obj.login_to_dashboard()
        self.endpoint_obj.get_storage_plan_provisioning()
        self.log.info("%s Storage and Plan configuration completed successfully for new tenant %s", "*" * 8, "*" * 8)
    
    @test_step
    def edgemode_validation(self):
        """
        Browse and Restore validation as Enduser in Edgemode
        """
        self.log.info(""" Initialize browser objects """)
        client_name = self.tcinputs['Machine_host_name']
        self.browser = BrowserFactory().create_browser_object()
        
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        
        self.admin_console.login(username=self.edgeuser,
                                  password=self.tenant_pwd)

        self.edgeHelper_obj = EdgeHelper(self.admin_console, self.commcell)
        self.edgemain_obj = EdgeMain(self.admin_console)
        self.edgeHelper_obj.enduser = self.edgeuser
        self.edgeHelper_obj.client_name = client_name 
        self.edgeHelper_obj.validate_enduser_loggedin_url(metallic=True)
        self.edgeHelper_obj.verify_client_exists_or_not(str(client_name))
        self.edgemain_obj.navigate_to_client_restore_page(client_name )
        self.edgeHelper_obj.machine_object = self.tcinputs['Machine_object']
        self.edgeHelper_obj.source_dir=self.source_path_dir
        self.log.info("Browse and restore validation started for edgeuser [{0}]".format(self.edgeuser))
        self.edgeHelper_obj.subclient_restore_as_enduser()
        
    def run(self):
        
        try:
 
            self.ring_hostname = self.tcinputs["ring_hostname"]
            self.laptop_helper = LaptopHelper(self)
            #-------------------------------------------------------------------------------------
            self.laptop_helper.tc.log_step("""
            
                1. Hub Operation:
                  ---------------------
                   a.Create new tenant 
                   b. Login to Hub as new tenant 
                   b. Select EndPoint Workload
                   c. Click on Download package option
                   d. Download the required package
                   
                2. Install and activation of the laptop:
                  -------------------------------------
                    a. Install above downloaded pacakage interactively:
                    b. Wait for laptop full backup job to start and complete from osc schedule.
                    c. Validation
                        - Check client readiness succeeds
                        - Verify Session->nchatterflag is off in registry for clients
                        - Verify FileSystem->nLaptopAgent flag is set to 1 in registry for the client
                        - Verify Plan and company's client group associations for activated client
                        - Client is visible in Company's devices
                        - Validate client ownership is set to the activating user
                        
                3. Adminconsole Operations:
                 -------------------------
                    a. Add new source data
                    b. Click On backup from Laptop actions in adminconsole
                    C. Run out-of-place restore of above folder and validate the Restore

                4. Enduser Operations:
                 -------------------------
                    a. Validate self service URL as enduser
                    b. Browse and restore the data backedup in previous step
                    C. Run out-of-place restore of above folder and validate the Restore

                    
            """, 200)
            
            #-------------------------------------------------------------------------------------
            self.commcell_host = self.ring_hostname
            self.commcell_obj = Commcell(self.commcell_host, self.tenant_username, self.tenant_pwd)
            self.commcell = self.commcell_obj 
            self.tenant_company = self.commcell_obj.organizations.get(self.companyname)
            self.default_plan = self.tenant_company.default_plan
            self.tcinputs['Default_Plan']=self.default_plan
            self.tcinputs['Tenant_company']= self.companyname
            self.tcinputs['Activation_User']= str(self.edgeuser)
            self.tcinputs['Activation_Password']=self.tenant_pwd   
            self.metallic_laptop_helper = LaptopHelperMetallic(self, company=self.companyname)
            self.log.info("Started executing %s testcase", self.id)
            #**** Download package from metallic ring
            self.laptop_helper.tc.log_step("""select workload and download metallic package""")
            if self.tcinputs['os_type'] == 'Windows':
                self.refresh1()
                self.endpoint_obj.download_laptop_package('Windows')
                self.utils.wait_for_file_to_download(".exe", timeout_period=300)
            
            else:
                self.refresh2()
                self.endpoint_obj.download_laptop_package('Mac')
                self.utils.wait_for_file_to_download(".pkg", timeout_period=300)
            
            #--------------------------------------------------------------------------
            # Sometimes backup job taking around 20 minutes due to default throttle set at plan level  
            #  + activation via edge app together taking more than 30 minutes . 
            # Due to idle time of the command center it is logging out automatically and  
            # unable to navigate from dashboard to commadecenter. so logout and relogin the commandcenter 
            # -----------------------------------------------------------------------------------------
            
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.laptop_helper.tc.log_step("""Installation and activation of the laptop""")
            self.metallic_laptop_helper.install_laptop(
                 self.tcinputs,
                 self.config_kwargs, 
                 self.install_kwargs, 
                 self.custompkg_directory
             )   
            self.laptop_helper.tc.log_step("""Backup and restore operations from adminconsole""")
            #----------Relogin the commandcenter after laptop activated and backup completed------------
            self.browser = BrowserFactory().create_browser_object()
            self.browser.set_downloads_dir(self.custompkg_directory)
            self.log.info("%s Opening the browser %s", "*" * 15, "*" * 15)
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.tenant_username,
                                     password=self.tenant_pwd)
            #### Dashboard operations for new tenant ####
            self.endpoint_obj = EndPoint(self.admin_console)
            self.endpoint_obj.login_to_dashboard()
            self.endpoint_obj.login_to_adminconsole()
            self.laptop_obj = LaptopMain(self.admin_console, self.commcell)
            self.laptop_obj.client_name = self.tcinputs['Machine_host_name']
            dir_string = OptionsSelector.get_custom_str('TC_'+str(self.id), 'Data')
            if self.tcinputs['os_type'] == 'Windows':
                _source_data_dir = lc.WINDOWS_PATH + dir_string
                osc_options=None
            else:
                _source_data_dir = lc.MAC_PATH + dir_string
                osc_options=self.tcinputs['osc_options']
            
            # **** Creating test data in above directory *****
            self.source_path_dir = self.utility.create_directory(self.tcinputs['Machine_object'], _source_data_dir)
            _ = self.utility.create_test_data(self.tcinputs['Machine_object'],
                                               self.source_path_dir,
                                               level=10,
                                               file_size=5000,
                                               options=osc_options)            
                                               
            self.laptop_obj.machine_object = self.tcinputs['Machine_object']
            self.laptop_obj.source_dir = self.source_path_dir
            self.laptop_helper.tc.log_step("Step1: Verification - Backup verification from adminconsole")
            backup_job_id = self.laptop_obj.perform_backup_now(backup_type='backup_from_actions')
           
            self.laptop_helper.tc.log_step("Step2: Restore Verification from Laptop actions")
            self.laptop_obj.subclient_restore(backup_job_id, restore_type='restore_from_actions')
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            #--edge mode validation--
            self.edgemode_validation()
            self.log.info("*****Laptop Backup and restore Validation completed successfully*****")
                  
        except Exception as exp:
            self.laptop_helper.tc.fail(str(exp))
            self.utils.handle_testcase_exception(exp)

        finally:
            try:
                self.laptop_helper.cleanup_clients(self.tcinputs)
                self.utility.delete_client(self.tcinputs['Machine_host_name'], commcell_name=self.commcell)
                self.utility.remove_directory(self.tcinputs['Machine_object'], self.source_path_dir)
            except Exception as err:
                self.log.info("failed to cleanup the client{0}".format(err))    
            self.hubmgr.deactivate_tenant(self.companyname)
            self.hubmgr.delete_tenant(self.companyname)
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

            
    def refresh1(self):
        """ Refresh the dicts for windows interactive install"""
        self.config_kwargs.clear()
        self.install_kwargs.clear()
        
        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': True,
        }
        
        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': False,
            'interactive_install': True,
            'check_num_of_devices': False,
            'validate_user': False,
            'backupnow': False,
            'post_osc_backup': False,
            'skip_osc': False,
			'sleep_before_osc': True
        }
        
    def refresh2(self):
        """ Refresh the dicts for mac """
        self.config_kwargs.clear()
        self.install_kwargs.clear()
        
        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': True
        }
        
        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True,
            'post_osc_backup': False
       }
