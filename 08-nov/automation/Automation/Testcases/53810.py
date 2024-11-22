# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for [Laptop Install] - [MSP] - Reinstall client with auth code of different company

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""
import inspect

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelper
from Laptop import laptopconstants

class TestCase(CVTestCase):
    """Test case class for [Laptop Install] - [MSP] - Reinstall client with auth code of different company"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop Install] - [MSP] - Reinstall client of same name with auth code of different company
                            and reinstall again with different user and authcode of company2"""
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}
        self.company1_machine = {}
        self.company1_object = None
        # PRE-REQUISITES OF THE TESTCASE
        # - Company should be created on commcell
        # - A Plan should be created on commcell which could be associated to the company as default plan.
        # Configuration required.
        # For each OS platform:
        # - Machine name should be common and domain should be different

        # - Domains
        # ###### should be registered domain of Company1
        # ###### should be registered domain of Company2
        # - One user should have active session
        #    e.g ######
        #        [This will become owner of client vm2012-vm14]
        # - Two users should have active session on vm2012-vm14.automation.commvault.com
        #    e.g automation\sg_user1, automation\sg_user2
        #
        # As a concept can be validated for Windows as other testcases can cover for Mac platform for functionality,
        # as the scenario is pretty much the same as covered in other test cases.

    def setup(self):
        """ Setup test case inputs from config template """
        # Tenant 1 data
        testcase_inputs = LaptopHelper.set_inputs(self, 'Company1')
        self.tcinputs.update(testcase_inputs)
        self.company1_machine = {
            "Machine_host_name": testcase_inputs["Machine_host_name"],
            "Machine_user_name": testcase_inputs["Machine_user_name"],
            "Machine_password": testcase_inputs["Machine_password"]
        }

    def run(self):
        """ Main function for test case execution."""
        try:
            laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                            REINSTALL WITH AUTHCODE FOR DIFFERENT COMPANY
                1. Enable authcode and set default plan for Tenant Company and install custom package
                2. Install with /authcode ###### option
                3. Wait for osc backup, change subclient content and execute backup/restore
                4. Do client validation.
                5. Uninstall client locally. Add user2 as blacklisted user. [ User1 becomes the owner ]
                6. Install custom package again on ANOTHER client WITH SAME NAME and authcode of another company
                7. Reinstall should not take over client of other company
                8. Do validation for <clientname>___1
                9. Uninstall <clientname>___1 locally. [Leave behind deconfigured entry on commcell]
                10. Remove User2 from blacklisted group.
                11. Reinstall <clientname>___1 with authcode of company2
                12. Client should be taken over with User1 and User2 as the owner.
                13. Do validation for <clientname>___1
            """, 200)
            #-------------------------------------------------------------------------------------

            # Install laptop client and validate laptop installation
            self.refresh()
            self.install_kwargs.update({'new_client_name': self.tcinputs['Machine_client_name']})

            # ----------------------------------------------------------------------------------------
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)
            # ----------------------------------------------------------------------------------------

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(excp))
            laptop_helper.cleanup(self.tcinputs)
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

        try:
            # Tenant 2 data - Do no move this in setup() module. As the RDP sessions are opened for individual
            # installations. and having all inputs together tries to open RDP connections for wrong users.
            common_inputs = [
                "Activation_User1",
                "Activation_Password1",
                "Activation_User2",
                "Activation_Password2"
            ]
            tenant1_tcinputs = LaptopHelper.set_inputs(self, 'Company2', common_inputs)

            self.install_kwargs.update({
                'delete_client': False,
                'activation_time_limit': 12, # With multiple users logged in activation requests go through every 5 min
                'new_client_name': tenant1_tcinputs['Machine_client_name'] + laptopconstants.REINSTALLED_CLIENT_STR,
                'blacklist_user': tenant1_tcinputs['Activation_User2'],
                'remove_blacklisted_user': tenant1_tcinputs['Activation_User1'],
                'post_osc_backup': False
            })
            tenant1_tcinputs['Activation_User'] = tenant1_tcinputs['Activation_User1']
            tenant1_tcinputs['Activation_Password'] = tenant1_tcinputs['Activation_Password1']

            laptop_helper.company.refresh()
            laptop_helper_1 = LaptopHelper(self, company=tenant1_tcinputs['Tenant_company'])

            # ----------------------------------------------------------------------------------------
            laptop_helper_1.install_laptop(tenant1_tcinputs, self.config_kwargs, self.install_kwargs)
            # ----------------------------------------------------------------------------------------

            # Uninstall client2 locally and Reinstall client2 with tenant 2 auth code again with user2.
            # Client should be taken over.
            self.refresh()
            self.install_kwargs.update({
                'delete_client': False,
                'activation_time_limit': 12, # With multiple users logged in activation requests go through every 5 min
                'new_client_name': tenant1_tcinputs['Machine_client_name'] + '___1',
                'skip_osc': True,
                'check_num_of_devices': False,
                'sleep_before_osc': True,
                'remove_blacklisted_user': tenant1_tcinputs['Activation_User2'],
                'expected_owners': [tenant1_tcinputs['Activation_User1'], tenant1_tcinputs['Activation_User2']],
                'post_osc_backup': False
            })
            tenant1_tcinputs['Activation_User'] = tenant1_tcinputs['Activation_User2']
            tenant1_tcinputs['Activation_Password'] = tenant1_tcinputs['Activation_Password2']
            # ----------------------------------------------------------------------------------------
            laptop_helper_1.install_laptop(tenant1_tcinputs, self.config_kwargs, self.install_kwargs)
            # ----------------------------------------------------------------------------------------
            # Prevent deletion of common names client from commcell, else the laptop_helper cleanup crashes evmgrs for
            # commcell since the common client object is referenced for non existent client on commcell.
            self.tcinputs['Machine_object'] = laptop_helper.utility.get_machine_object(
                self.company1_machine["Machine_host_name"],
                self.company1_machine["Machine_user_name"],
                self.company1_machine["Machine_password"]
            )
            laptop_helper.cleanup(self.tcinputs)
            laptop_helper_1.cleanup(tenant1_tcinputs, delete_client=False)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(excp))
            self.tcinputs['Machine_object'] = laptop_helper.utility.get_machine_object(
                self.company1_machine["Machine_host_name"],
                self.company1_machine["Machine_user_name"],
                self.company1_machine["Machine_password"]
            )
            laptop_helper.cleanup(self.tcinputs)
            laptop_helper_1.cleanup(tenant1_tcinputs)

    def refresh(self):
        """ Refresh the dicts """
        self.config_kwargs.clear()
        self.install_kwargs.clear()
        self.config_kwargs = {
            'org_enable_auth_code': True,
            'org_set_default_plan': True,
        }

        self.install_kwargs = {
            'install_with_authcode': True,
            'execute_simcallwrapper': False,
        }
