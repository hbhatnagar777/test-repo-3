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
from cvpysdk.deployment.deploymentconstants import DownloadPackages, DownloadOptions
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures, UnixDownloadFeatures
from Install import installer_utils
from AutomationUtils.machine import Machine
from Install.install_helper import InstallHelper
from AutomationUtils import config
from Install.install_validator import InstallValidator
from Install.softwarecache_helper import SoftwareCache
from Install.installer_constants import DEFAULT_COMMSERV_USER
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep
from Web.AdminConsole.adminconsole import AdminConsole
from Laptop.laptophelper import LaptopHelper
from Reports.utils import TestCaseUtils
from Server.organizationhelper import OrganizationHelper
from Laptop import laptopconstants as lc
from Server.Plans.planshelper import PlansHelper
from Server.Security.userhelper import UserHelper
from Server.Plans import plansconstants
from Web.AdminConsole.Laptop.LaptopEdgeMode import EdgeMain
from Web.AdminConsole.Helper.LaptopEdgeHelper import EdgeHelper
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.Helper.LaptopHelper import LaptopMain
from Web.AdminConsole.Setup.getting_started import GettingStarted

class TestCase(CVTestCase):
    """ [Precert ]- Acceptance Testcase """

    test_step = TestStep()

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Precert ]- Acceptance Testcase"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self._service_pack_to_install = None
        self.config_json = None
        self.install_helper = None
        self.cs_machine = None
        self.software_cache_helper = None
        self.update_acceptance = False
        self.media_path = None
        self.show_to_user = False
        self.browser = None
        self.admin_console = None
        self.laptop_obj = None
        self.utility = None
        self.utils = None
        self.laptop_helper = None
        self.organization = None
        self.company_password = None
        self.company_name = None
        self.company_obj = None
        self.email = None
        self.domain_name = None
        self.spool = None
        self.plan = None
        self.plan_name = None
        self._user_helper = None
        self.user_helper = None
        self.commcell_obj = None
        self.endpoint_obj = None
        self.plans_api_helper = None
        self.company_details = None
        self.company = None
        self.edgeHelper_obj = None
        self.edgemain_obj = None
        self.source_path_dir = None
        self.storage_pool_name = None
        self.install_kwargs = {}
        self.config_kwargs = {}
        self.install_inputs = {}
        self.tcinputs = {
            'ServicePack': None,
            "domain_name": None,
            "netbios_name":None,
            "domain_username":None,
            "domain_password":None
        }

    def fresh_cs_installation(self):
        """ Fresh Installation of Windows CS"""
        
        if self.cs_machine.check_registry_exists("Session", "nCVDPORT"):
            self.install_helper.uninstall_client(delete_client=False)
        
        self.log.info("Determining Media Path for Installation")
        self.media_path = self.tcinputs.get('MediaPath') if self.tcinputs.get('MediaPath') else ''
        _service_pack = self.tcinputs.get("ServicePack") if self.tcinputs.get("ServicePack") \
            else self.config_json.Install.commserve_client.sp_version
        _service_pack = _service_pack.split('_')[0] if '_' in _service_pack else _service_pack
        self._service_pack_to_install = installer_utils.get_latest_recut_from_xml(_service_pack)
        if "{sp_to_install}" in self.media_path:
            self.media_path = self.media_path.replace("{sp_to_install}", self._service_pack_to_install)
        self.log.info("Service Pack used for Installation: %s" % _service_pack)
        if self.media_path:
            self.install_inputs["mediaPath"] = self.media_path
            self.log.info("Media Path used for Installation: %s" % self.media_path)
        self.log.info("Starting CS Installation")
        if self.update_acceptance:
            self.install_helper.install_acceptance_insert()
        self.install_helper.install_commserve(install_inputs=self.install_inputs, feature_release=_service_pack)
        self.log.info("Login to Commcell after CS Installation")
        time.sleep(400)
        try:
            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=DEFAULT_COMMSERV_USER,
                                     commcell_password=self.config_json.Install.cs_password,
                                     verify_ssl=False)
        except Exception:
            time.sleep(500)
            self.commcell = Commcell(webconsole_hostname=self.config_json.Install.commserve_client.machine_host,
                                     commcell_username=DEFAULT_COMMSERV_USER,
                                     commcell_password=self.config_json.Install.cs_password,
                                     verify_ssl=False)

        self.log.info("Checking Readiness of the CS machine")
        commserv_client = self.commcell.commserv_client
        if commserv_client.is_ready:
            self.log.info("Check Readiness of CS successful")
        else:
            self.log.error("Check Readiness Failed")
        
        self.log.info("Starting download software job")
        self.software_cache_helper = SoftwareCache(self.commcell)
        job_obj = self.commcell.download_software(
            options=DownloadOptions.LATEST_HOTFIXES.value,
            os_list=[DownloadPackages.WINDOWS_64.value, DownloadPackages.UNIX_LINUX64.value])
        self.log.info("Job %s started", job_obj.job_id)
        if job_obj.wait_for_completion():
            self.log.info("Download Software Job Successful")
        else:
            self.log.error("Download job failed")
        
        self.log.info("Starting Install Validation")
        package_list = [UnixDownloadFeatures.COMMSERVE.value] if self.commcell.is_linux_commserv \
            else [WindowsDownloadFeatures.COMMSERVE.value]
        install_validation = InstallValidator(commserv_client.client_hostname, self,
                                               machine_object=self.cs_machine, package_list=package_list,
                                               media_path=self.media_path if self.media_path else None)
        install_validation.validate_install(validate_mongodb=True)
        if self.update_acceptance:
            self.install_helper.commcell = self.commcell
            self.install_helper.install_acceptance_update('Pass', '-', self.cs_machine.machine_name)
        
    def entities_creation(self):
        """ Create Entities on newly installed CS"""
        #-------------------------------------------------------------------------------------
        self.laptop_helper.tc.log_step("""
        1.Create Company
        2.Associate domain (AD) to above created company
        3.Create storage Pool
        4.Create Lapto plan
        5.Associate the user to plan 
        6.Set the default Plan 
        """, 200)
        #-------------------------------------------------------------------------------------
        self.log.info("----- STEP1 : Company Creation----- ") 
        self.company_details = self.organization.setup_company(
                        company_name=self.company_name,
                        email= self.email,
                        ta_password=self.company_password) 
        organizations = self.commcell.organizations
        if not organizations.has_organization(self.company_name):
            raise Exception(f"Company does not exists with name: [{self.company_name}]")
        
        self.log.info("----- STEP2 : Associate the Domain the company---- ") 
        if self.commcell.domains.has_domain(self.tcinputs["netbios_name"]):
            raise Exception(f"Domain [{self.domain_name}] already exist . Please add another domain")
        organization_obj = self.commcell.organizations.get(self.company_name)
        self.log.info(f"Associating Domain [{self.domain_name}] to company [{self.company_name}]")
        self.commcell.domains.add(
                domain_name=self.domain_name, 
                netbios_name=self.tcinputs["netbios_name"],
                user_name=self.tcinputs["domain_username"],
                password=self.tcinputs["domain_password"], 
                company_id=int(organization_obj.organization_id),
                ad_proxy_list=None,
                enable_sso=False)
        self.log.info(f"Domain [{self.domain_name}] associated successfully to company [{self.company_name}]")
        
        self.log.info("----- STEP3 : Storage pool Creation----- ") 
        if self._commcell.media_agents.all_media_agents:
            self.log.info('Storage was not available for the user.. Creating storage on available media agent..')
            media_agent_name = self.organization._get_media_agent()
            self.log.info(f'Creating New Storage Pool : [{self.storage_pool_name}] on MA [{media_agent_name}]...')
            _spool = self._commcell.storage_pools.add(
                    storage_pool_name=self.storage_pool_name,
                    mountpath="c:\\AutoMountPaths\\" + self.storage_pool_name + "_path",
                    media_agent=media_agent_name,
                    ddb_ma=media_agent_name,
                    dedup_path="c:\\AutoMountPaths\\" + self.storage_pool_name + "_path\\DDB")
            self.log.info('Storage created successfully')
        
        else:
            raise Exception('No Media Agent available in the setup!')

        self.log.info("----- STEP4 : Plan Creation----- ") 
        self._commcell.refresh()
        self.log.info(f'Creating plan')
        plan = self._commcell.plans.add(
             plan_name=self.plan_name,
             plan_sub_type=plansconstants.SUBTYPE_LAPTOP,
             storage_pool_name=self.storage_pool_name,
             sla_in_minutes=480
        )
        self.log.info(f'Plan Created successfully: {plan.plan_name}')
        self._commcell.plans.refresh()
        time.sleep(5)
        # Associate plan to company
        self.plans_api_helper['MSPAdmin'].plan_to_company(self.company_name,self.plan_name)
        self.log.info("----- STEP5 : Associate the user to the Plan----- ") 
        self.user_helper = UserHelper(self.commcell_obj)
        domain_u1 = self.tcinputs["Activation_User"].split('\\')[0]
        user_name = self.tcinputs["Activation_User"].split('\\')[1]
        self.log.info(f'Adding domain user {self.tcinputs["Activation_User"]} on commcell')
        self.user_helper.create_user(user_name=user_name,
                                      email='{0}@{1}'.format(domain_u1, self.domain_name),
                                      domain=self.tcinputs["netbios_name"])
        self.log.info(f'Domain user {self.tcinputs["Activation_User"]} added successfully to commcell')
        self.plans_api_helper['MSPAdmin'].associate_user_to_plan(
            self.plan_name,
            self.tcinputs["Activation_User"],
            send_invite=False
            )
        self.log.info(f'user {self.tcinputs["Activation_User"]} associated to Plan : {self.plan_name}')
        
        self.log.info("----- STEP6: Setting the company's default plan to company----- ") 
        self.company = self._commcell.organizations.get(self.company_name)
        value = {
                'Laptop Plan' : self.plan_name
            }
        self.company.default_plan = value
        self.company.tenant_client_group = self.plan_name

    def laptop_installation(self):
        """ Install Laptop """
        #-------------------------------------------------------------------------------------
        self.laptop_helper.tc.log_step("""
            a.Create Laptop package
            b. Install downloaded pacakage interactively:
            c. Wait for laptop full backup job to start and complete from osc schedule.
            d. Validation
            """, 200)
        #-------------------------------------------------------------------------------------
        self.refresh()
        self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company1'))
        self.tcinputs['Default_Plan']=self.plan_name
        laptop_helper = LaptopHelper(self, company=self.company_name)
        laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)

    @test_step
    def adminmode_validation(self):
        """ Laptop validation in admin mode """
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.config_json.Install.commserve_client.machine_host)
        self.admin_console.login(username=self.config_json.ADMIN_USERNAME,password=self.config_json.Install.cs_password)
        getting_started = GettingStarted(self.admin_console)
        getting_started.skip_coresetup_completion()
        #### Dashboard operations for new tenant ####
        self.laptop_obj = LaptopMain(self.admin_console, self.commcell)
        self.laptop_obj.navigate_to_laptops_page()
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

    @test_step
    def edgemode_validation(self):
        """
        Browse and Restore validation as Enduser in Edgemode
        """
        self.log.info(""" Initialize browser objects """)
        client_name = self.tcinputs['Machine_host_name']
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.config_json.Install.commserve_client.machine_host)
        self.admin_console.login(username=self.tcinputs["Activation_User"],
                                  password=self.tcinputs["Activation_Password"])

        self.edgeHelper_obj = EdgeHelper(self.admin_console, self.commcell)
        self.edgemain_obj = EdgeMain(self.admin_console)
        self.edgeHelper_obj.enduser = self.tcinputs["Activation_User"]
        self.edgeHelper_obj.client_name = client_name 
        self.edgeHelper_obj.validate_enduser_loggedin_url(metallic=False)
        self.edgeHelper_obj.verify_client_exists_or_not(str(client_name))
        self.edgemain_obj.navigate_to_client_restore_page(client_name )
        self.edgeHelper_obj.machine_object = self.tcinputs['Machine_object']
        self.edgeHelper_obj.source_dir=self.source_path_dir
        self.log.info(f'Browse and restore validation started for user: {self.tcinputs["Activation_User"]}')
        self.edgeHelper_obj.subclient_restore_as_enduser()

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        self.utils = TestCaseUtils(self)
        self.log.info("Creating CS Machine Object")
        self.cs_machine = Machine(
            machine_name=self.config_json.Install.commserve_client.machine_host,
            username=self.config_json.Install.commserve_client.machine_username,
            password=self.config_json.Install.commserve_client.machine_password)
        self.install_helper = InstallHelper(None, machine_obj=self.cs_machine, tc_object=self)
        _cs_password = self.config_json.Install.cs_encrypted_password if 'windows' in self.cs_machine.os_info.lower() \
            else self.config_json.Install.cs_password
        self.install_inputs = {
            "csClientName": self.config_json.Install.commserve_client.client_name,
            "csHostname": self.config_json.Install.commserve_client.machine_host,
            "commservePassword": _cs_password,
            "instance": "Instance001"
        }
        self.update_acceptance = self.config_json.Install.update_acceptance_database

    def run(self):
        
        try:
 
            #install fresh CS 
            self.fresh_cs_installation() 
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company1'))
            self.laptop_helper = LaptopHelper(self)
            self.organization = OrganizationHelper(self.commcell)
            self.utility = OptionsSelector(self.commcell)
            self.plan_name = datetime.datetime.now().strftime("Autoplan-%d-%B-%H-%M")
            self.company_name = datetime.datetime.now().strftime("Endpoint-%d-%B-%H-%M")
            self.company_password = self.config_json.Organizations.company_user_password
            self.storage_pool_name =  datetime.datetime.now().strftime("AutoStoragePool-%d-%B-%H-%M")
            suffix = str(int(time.time()))
            self.email = "cvautouser" + suffix + "@test.com"
            self.domain_name = self.tcinputs['domain_name']
            self.tcinputs["MSPCommCell"] = self.config_json.Install.commserve_client.machine_host
            self.tcinputs["MSPadminUser"] = self.config_json.ADMIN_USERNAME
            self.tcinputs["MSPadminUserPwd"] = self.config_json.Install.cs_password
            self.commcell_obj = self.commcell
            self.plans_api_helper = {
                'MSPAdmin': PlansHelper(
                    self.tcinputs["MSPCommCell"],
                    commcell_obj=self.commcell_obj
                )
            }
            #-------------------------------------------------------------------------------------
            self.laptop_helper.tc.log_step("""
            
                1. Fresh Installation of CS :
                  ---------------------
                    1. Fresh Installation of CS from given media path and SP 

                2. Entities creation validation :
                  ---------------------
                    1. On newly installed CS , create company 
                    2. Validate above created company 
                    3. Assocaite the domain to above created company
                    4. Validate above created domain 
                    5. Create Lapto plan
                    6. validate above created plan
                    7. Associate the user to plan from above craeted domain
                   
                3. Install and activation of the laptop:
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
                        
                4. Adminconsole Operations:
                 -------------------------
                    a. Add new source data
                    b. Click On backup from Laptop actions in adminconsole
                    C. Run out-of-place restore of above folder and validate the Restore

                5. Enduser Operations:
                 -------------------------
                    a. Validate self service URL as enduser
                    b. Browse and restore the data backedup in previous step
                    C. Run out-of-place restore of above folder and validate the Restore

                    
            """, 200)
            
            #-------------------------------------------------------------------------------------
            self.entities_creation()
            self.laptop_installation()
            self.adminmode_validation()
            self.edgemode_validation()
            self.log.info("****Precert Validation completed successfully on newly installed CS*****")
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
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def refresh(self):
        """ Refresh the dicts """
        self.config_kwargs.clear()
        self.install_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': False,
        }

        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True,
            'check_num_of_devices': False,
            'validate_user': False,
            'backupnow': False,
            'post_osc_backup': False,
            'skip_osc': False,
            'sleep_before_osc': True
        }

