# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for validating User Centric Laptop reinstall case

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelperUserCentric

class TestCase(CVTestCase):
    """Test case class for validating User Centric Laptop client reinstall cases"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop Install] - [MSP- User Centric] - Reinstall and register with same user - Takeover"""
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}

        # PRE-REQUISITES OF THE TESTCASE
        # - Company should be created on commcell
        # - A Plan should be created on commcell which could be associated to the company as default plan.

    def setup(self):
        """ Setup test case inputs from config template """
        common_inputs = [
            "Activation_User1",
            "Activation_Password1",
            "Activation_User2",
            "Activation_Password2"
        ]

        test_inputs = LaptopHelperUserCentric.set_inputs(self, 'Company2', common_inputs)
        # Generate User map
        test_inputs['user_map'] = LaptopHelperUserCentric.create_pseudo_map(test_inputs)
        self.log.info("User map: [{0}]".format(test_inputs['user_map']))
        self.tcinputs.update(test_inputs)

        self.tcinputs['Activation_User'] = self.tcinputs['Activation_User1']
        self.tcinputs['Activation_Password'] = self.tcinputs['Activation_Password1']

    def run(self):
        """ Main function for test case execution."""
        try:
            laptop_helper = LaptopHelperUserCentric(self, company=self.tcinputs['Tenant_company'])

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                            REINSTALL WITH SAME USERNAME AND SAME CLIENT NAME - TAKEOVER
                1. Enable shared laptop, authcode, set default plan for Tenant Company and install custom package
                    *without authcode with options:
                        <InstallationPackage>.exe /silent /install /silent
                        Run Simcalwrapper

                    - Wait for laptop full backup job to start from osc schedule.
                        Change subclient content, wait for incremental backup to trigger.
                        Execute out of place restore.

                    - Validation
                        - Check client readiness succeeds
                        - Verify Session->nchatterflag is off in registry for clients
                        - Verify FileSystem->nLaptopAgent flag is set to 1 in registry for the client
                        - Verify Plan and company's client group associations for activated client
                        - Client is visible in Company's devices
                        - Validate client ownership is set to the activating user

                2. Uninstall the client locally. Do not delete the client from the commcell.

                3. Install custom package again on the client and register with the same user

                4. Validate post install fro each activateed user

                5.Disable share laptop, uninstall and delete client from CS

            """, 200)
            #-------------------------------------------------------------------------------------

            # Install laptop client and validate laptop installation
            self.refresh()
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)

            # Reinstall laptop client and validate laptop installation
            self.install_kwargs['delete_client'] = False
            self.install_kwargs['skip_osc'] = True
            self.install_kwargs['wait_for_reinstalled_client'] = True
            self.install_kwargs['check_num_of_devices'] = False
            laptop_helper.company.refresh()
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
        finally:
            laptop_helper.cleanup_user_centric(self.tcinputs)

    def refresh(self):
        """ Refresh the dicts """
        self.config_kwargs.clear()
        self.install_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': True,
        }

        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True,
        }
