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
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from Web.AdminConsole.Components.table import Rtable

from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole][[AdminMode]]: Laptop Deactivation and Activation from plan """

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole][[AdminMode]]: Laptop Deactivation and Activation from plan"
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
        self.navigator = None
        self.rtable = None
        self.install_kwargs = {}
        self.config_kwargs = {}

        # PRE-REQUISITES OF THE TESTCASE
        # - Tenant_company and Default_Plan should be created on commcell
    

    def dissociate_user_from_plan(self):
        """ Dissociates User from the given plan"""
        self.navigator.navigate_to_plan()
        Plans(self.admin_console).select_plan(self.tcinputs['Default_Plan'])
        PlanDetails(self.admin_console).remove_associated_users_and_groups(user_user_group_de_association=
                                                                           {"DeleteAll": False,
                                                                            "DeleteAllUsers": True,
                                                                            "DeleteAllUserGroups": False,
                                                                            "Delete_Specific_user_user_or_group": False
                                                                            }
                                                                           )
    def validation_from_adminconsole_after_deactivation(self):
        """ validate laptop after user disassociated from plan"""
        client_name = self.tcinputs['Machine_host_name']
        self.rtable.search_for(client_name)
        client_details= self.rtable.get_table_data()
        if 'No plan is associated' not in client_details['Plans'][0]:
            exp = "Client {0} is still associated to plan after deactivation".format(client_name)
            self.log.exception(exp)
            raise Exception(exp)
        
        grid_list = self.rtable.get_grid_actions_list(client_name)
        if 'Activate' not in grid_list or 'Deactivate' in grid_list:
            exp = "deactivate button is still showing from actions"
            self.log.exception(exp)
            raise Exception(exp)
        #backup button validation after client deactivated
        self.laptop_obj.validate_backup_after_deactivation()

    def associate_user_from_plan(self):
        """ Associates User to the given plan"""
        self.navigator.navigate_to_plan()
        Plans(self.admin_console).select_plan(self.tcinputs['Default_Plan'])
        PlanDetails(self.admin_console).edit_plan_associate_users_and_groups([self.tcinputs['Activation_User']])
        
    def validation_from_adminconsole_after_activation(self):
        """ validate laptop after user associated from plan"""
        client_name = self.tcinputs['Machine_host_name']
        plan_name = self.tcinputs['Default_Plan']
        self.rtable.search_for(client_name)
        client_details= self.rtable.get_table_data()
        
        if not plan_name in client_details['Plans'][0]:
            exp = "Client {0} is not associated to plan after activation".format(client_name)
            self.log.exception(exp)
            raise Exception(exp)
        
        grid_list = self.rtable.get_grid_actions_list(client_name)
        if 'Activate' in grid_list or 'Deactivate' not in grid_list:
            exp = "Activate button is showing instead of deactivate when laptop activated"
            self.log.exception(exp)
            raise Exception(exp)
        
        #backup button validation after client deactivated
        self.laptop_obj.action_click()
        __backup_job_id = self.laptop_obj.perform_backup_now(backup_type='backup_from_actions')
        
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

                2. Execute SimCallWrapper and register the client with user [testlab\testuser_01]

                3. Login to Adminconsole with Tenant Admin

                4. Activate laptop with domain user (for e.g: testlab\testuser_01) and validate if user is associated to the plan
                
                5. Disassociate / Remove the user from the Plan association ( This deactivates your device from the plan as well )

                6. Under Plan's User Associations add the user back the plan
                 
                7. Validate the device is activated and associated back to the plan.

            """, 200)

            #-------------------------------------------------------------------------------------

            self.log.info("Started executing %s testcase", self.id)

            self.refresh()
            #install laptop by creating custom package
            
            self.laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)
            _path = self.tcinputs['Machine_object'].join_path('UserCentricUsers', 'AllUsers')
            self.client_obj = self.commcell.clients.get(self.tcinputs['Machine_host_name'])

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
            self.laptop_obj.tenant_company= self.tcinputs['Tenant_company']
            
            self.log.info("Laptop Deactivation and Activation from plan validation started")
            self.navigator = self.admin_console.navigator
            self.rtable = Rtable(self.admin_console)
            self.dissociate_user_from_plan()
            self.laptop_obj.navigate_to_laptops_page()
            #validate """deactivated client""" from registry, client group , db
            self.laptop_helper.tc.log_step(""" Validation - Laptop deactivation from Client registry """)
            self.organization.validate_deactivation(self.client_obj, _path)
            #validate """deactivated client""" from adminconsole
            self.validation_from_adminconsole_after_deactivation()

            self.associate_user_from_plan()
            self.laptop_obj.navigate_to_laptops_page()
            #validate installed laptop client
            self.laptop_helper.tc.log_step(""" Validation - Laptop activation from Client and commcell """)
            plan_client_group = self.tcinputs['Default_Plan'] + ' clients'
            self.laptop_helper.organization.validate_client(self.tcinputs['Machine_object'],
                                                            expected_owners=[self.tcinputs['Activation_User']],
                                                            client_groups=[
                                                               plan_client_group,
                                                                'Laptop Clients',
                                                                self.tcinputs['Tenant_company']],
                                                            clients_joined=False,
                                                            nLaptopAgent=1)
            #validate """client activation""" from adminconsole
            self.validation_from_adminconsole_after_activation()
            
            self.log.info("*****Laptop Deactivation and Activation from plan Validation completed successfully*****")


        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            self.associate_user_from_plan()
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
