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
    """ [Laptop] [AdminConsole]: Laptop Deactivation validation """

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole]: Laptop Deactivation validation"
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

    def run(self):

        try:
            self.utility = OptionsSelector(self._commcell)
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company1'))
            self.laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])
            self.organization = OrganizationHelper(self._commcell, self.tcinputs['Tenant_company'])

            #-------------------------------------------------------------------------------------
            self.laptop_helper.tc.log_step("""
                1. Set default plan for Tenant Company

                2. Execute SimCallWrapper and register the client with user [user1]

                3. Deactivate the Laptop from adminconsole

                3. Validation
                        - Laptop page should show the laptop as deconfigured [ x sign against Configured column ]
                        - Check client deactivation from registry and DB

                4.verify backup for deactivate client from adminconsole
                        - Verify whether able to trigger Full Job for deactivated client
                        - Verify whether able to trigger INCREMENTAL Job for deactivated client
                        - verify Synthetic Full job

            """, 200)

            #------------------------------------------------------------------------------------

            self.log.info("Started executing %s testcase", self.id)

            self.refresh()
            #install laptop by creating custom package
            self.laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)
            
            self.utility.sleep_time(60, "Waiting for OSC job to be completed and updated in adminconsole")
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
            self.laptop_obj.activation_user = self.tcinputs['Activation_User']
            self.laptop_obj.client_name = self.tcinputs['Machine_host_name']

            self.commcell.clients.refresh()
            # **** Deactivate the client
            self.laptop_helper.tc.log_step(""" Deactivate Laptop from adminconsole """)
            self.laptop_obj.navigate_to_laptops_page()
            self.laptop_obj.deactivate_laptop()

            # validate ""deactivated client""" from adminconsole
            self.laptop_helper.tc.log_step(""" Validation - Laptop deactivation from adminconsole """)
            self.laptop_obj.client_deactivation_validation()

            #validate """deactivated client""" from registry, client group , db
            self.laptop_helper.tc.log_step(""" Validation - Laptop deactivation from Client registry """)
            self.organization.validate_deactivation(self.client_obj, _path)

            self.laptop_helper.tc.log_step(""" Verify backup after deactivation """)
            self.laptop_obj.validate_backup_after_deactivation() # to perform backup job
            
            self.log.info("*****Laptop Deactivation validation*****")


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

