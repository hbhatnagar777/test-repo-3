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
    """ [Laptop] [AdminConsole]: Laptop Actions for a laptop in Laptops->Solution page"""

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole]: Laptop Actions for a laptop in Laptops->Solution page"
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
            def validate_retire_client():
                #Refreshing the clients associated with the commcell Object
                self.commcell.clients.refresh()
                # validate "retired client""" from adminconsole
                self.laptop_obj.validate_client_from_adminconsole(actvation=False)

            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company1'))
            self.laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])
            self.organization = OrganizationHelper(self._commcell, self.tcinputs['Tenant_company'])
            self.utility = OptionsSelector(self._commcell)

            #-------------------------------------------------------------------------------------
            self.laptop_helper.tc.log_step("""
                1. Set default plan for Tenant Company

                2. Execute SimCallWrapper and register the client with user [user1]

                4. Update Software [ Select Reboot if Required option on the pop-up ]
                5. Check Readiness
                6. Send Logs
                7. Retire client
                7. Deactivation covered in testcases 54472 & 54213 & 54214
                8. Restore covered in Testcase 54212
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

            self.laptop_obj = LaptopMain(self.admin_console, self.commcell, self.csdb)
            self.laptop_obj.client_name = self.tcinputs['Machine_host_name']

            self.laptop_helper.tc.log_step(""" Started executing 'Update Software' operation """)
            self.laptop_obj.update_software(reboot=False)
            self.laptop_helper.tc.log_step(""" Started executing 'check_readiness' operation """)
            self.laptop_obj.check_readiness()
            self.laptop_helper.tc.log_step(""" Started executing 'retire_client' operation """)
            self.laptop_obj.retire_client()
            validate_retire_client()
            self.log.info("*****Actions for a laptop completed successfully*****")
            self.laptop_helper.cleanup(self.tcinputs)

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

