# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for validating Laptop client reinstall cases with diff hostname and admin user

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelper

class TestCase(CVTestCase):
    """Test case class for validating Laptop client reinstall cases with diff hostname"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Laptop Install] - [MSP] - Reinstall client with with same client name but different host name"
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}

        # PRE-REQUISITES OF THE TESTCASE
        # - Company should be created on commcell
        # - A Plan should be created on commcell which could be associated to the company as default plan.

    def run(self):
        """ Main function for test case execution."""
        try:
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company1'))
            laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                            REINSTALL WITH SAME USERNAME AND DIFFERENT CLIENT HOSTNAME - TAKEOVER
                1. Set default plan for Tenant Company and install custom package *without authcode with options:
                        <InstallationPackage>.exe /silent /install /silent
                        Run Simcalwrapper with different client hostname

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

                3. Execute Step 3) above again.
                    Install custom package again on the client and register with the same user

            """, 200)
            #-------------------------------------------------------------------------------------

            # Install laptop client and validate laptop installation
            self.refresh()
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)

            self.install_kwargs['delete_client'] = False
            self.install_kwargs['skip_osc'] = True
            self.install_kwargs['wait_for_reinstalled_client'] = True
            self.install_kwargs['check_num_of_devices'] = False
            self.config_kwargs['org_enable_auth_code'] = False
            self.install_kwargs['client_hostname'] = "anything"
            laptop_helper.company.refresh()

            # Reinstall client and validate
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)
            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            laptop_helper.cleanup(self.tcinputs)

    def refresh(self):
        """ Refresh the dicts """
        self.config_kwargs.clear()
        self.install_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': True,
            'org_set_default_plan': True,
        }

        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True,
        }
