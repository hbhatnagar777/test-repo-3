# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case"""

from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.LaptopHelper import LaptopMain
from Laptop.laptophelper import LaptopHelper
from AutomationUtils.options_selector import OptionsSelector
from Server.Security.securityhelper import OrganizationHelper
from Reports.utils import TestCaseUtils



class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole]: Deactivate and Activate Laptop from a plan """

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole]: Deactivate and Activate Laptop from a plan"
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
        self.install_kwargs = {}
        self.config_kwargs = {}
        self.tcinputs = {
            "Second_Plan":None
            }

    def run(self):

        try:
            self.utility = OptionsSelector(self._commcell)
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company1'))
            self.laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])
            self.organization = OrganizationHelper(self._commcell, self.tcinputs['Tenant_company'])

            #-------------------------------------------------------------------------------------
            #install testcase [53807]
            self.laptop_helper.tc.log_step("""
                1. Set default plan for Tenant Company

                2. Execute SimCallWrapper and register the client with user [user1]

                3. Deactivate the Laptop from adminconsole

                4. Activate the Laptop by plan from adminconsole:

                5. Validation
                        - Check client readiness succeeds
                        - Verify Session->nchatterflag is off in registry for clients
                        - Verify FileSystem->nLaptopAgent flag is set to 1 in registry for the client
                        - The client should be a part of the default plan that was set for the commcell.
                        - Validate client ownership is set to the activating user

                6.verify user able to backup data from adminconsole after activation

            """, 200)

            #-------------------------------------------------------------------------------------

            self.log.info("Started executing %s testcase", self.id)

            self.refresh()

            self.organization.checkfor_company_secondplan(self.tcinputs['Second_Plan'])
            #install laptop by creating custom package
            self.laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)
            
            self.utility.sleep_time(60, "Waiting for OSC job to be completed and updated in adminconsole")
            
            self.commcell.clients.refresh()
            self.client_obj = self.commcell.clients.get(self.tcinputs['Machine_host_name'])
            _path = self.tcinputs['Machine_object'].join_path('UserCentricUsers', 'AllUsers')

            self.laptop_helper.tc.log_step(""" Initialize browser objects """)

            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)

            self.admin_console.login(self.tcinputs['Tenant_admin'],
                                     self.tcinputs['Tenant_password'])

            self.laptop_obj = LaptopMain(self.admin_console, self.commcell)
            self.laptop_obj.host_name = self.tcinputs['Machine_host_name']
            self.laptop_obj.user_name = self.tcinputs['Machine_user_name']
            self.laptop_obj.password = self.tcinputs['Machine_password']
            self.laptop_obj.activation_plan = self.tcinputs['Default_Plan']
            self.laptop_obj.client_name = self.tcinputs['Machine_host_name']

            self.laptop_helper.tc.log_step(""" Started Laptop Activation validation with [ORIGINAL] PLAN """)
            # Deactivate the client
            self.laptop_obj.navigate_to_laptops_page()
            self.laptop_obj.deactivate_laptop()

            #Activate the laptop by the given plan
            self.laptop_helper.tc.log_step(""" Activate Laptop by [ORIGINAL] PLAN """)
            self.laptop_obj.activate_laptop(self.tcinputs['Default_Plan'])

            # validate """activated client""" from adminconsole
            self.laptop_helper.tc.log_step(""" Validation - Laptop activation from adminconsole """)
            self.laptop_obj.client_activation_validation(self.tcinputs['Default_Plan'])

            #validate installed laptop client
            self.laptop_helper.tc.log_step(""" Validation - Laptop activation from Client and commcell """)
            self.laptop_helper.organization.validate_client(self.tcinputs['Machine_object'],
                                                            client_groups=None,
                                                            clients_joined=False,
                                                            nLaptopAgent=1)

            self.laptop_helper.tc.log_step(""" Verify incremental backup job after activation """)
            self.laptop_obj.action_click()
            __backup_job_id = self.laptop_obj.perform_backup_now(backup_type='backup_from_actions')

            self.laptop_helper.tc.log_step(""" Started Laptop Activation validation with [SECOND] PLAN """)
            self.laptop_obj.deactivate_laptop()

            self.laptop_helper.tc.log_step(""" Activate Laptop by [SECOND] plan """)
            self.laptop_obj.activate_laptop(self.tcinputs['Second_Plan'])

            # validate """activated client""" from adminconsole
            self.laptop_helper.tc.log_step(""" Validation - Laptop activation with [SECOND] plan """)
            self.laptop_obj.client_activation_validation(self.tcinputs['Second_Plan'])

            #validate installed laptop client
            self.laptop_helper.tc.log_step(""" Validation - Laptop activation from Client and commcell """)
            second_client_group = self.tcinputs['Second_Plan'] + ' clients'
            self.laptop_helper.organization.validate_client(self.tcinputs['Machine_object'],
                                                            expected_owners=[self.tcinputs['Activation_User']],
                                                            client_groups=[
                                                                second_client_group,
                                                                'Laptop Clients',
                                                                self.tcinputs['Tenant_company']],
                                                            clients_joined=False,
                                                            nLaptopAgent=1)
            self.laptop_helper.tc.log_step(""" Verify incremental backup job after activation """)
            self.laptop_obj.action_click()
            __backup_job_id = self.laptop_obj.perform_backup_now(backup_type='backup_from_actions')
            
            self.log.info("*****Deactivate and Activate Laptop from a plan validation completed successfully*****")


        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            self.laptop_helper.cleanup(self.tcinputs)

    def refresh(self):
        """ Refresh the dicts """
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

