# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for validating [Laptop Install] - [MSP] - Create custom package *with auth code and
    install *without /authcode

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelper

class TestCase(CVTestCase):
    """Test case class for [Laptop Install] - [MSP] - Create custom package *with auth code and install
        *without /authcode"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Laptop Install] - [MSP] - Create custom package *with auth code and install *without /authcode"
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}
        self.custompackage_kwargs = {}

        # PRE-REQUISITES OF THE TESTCASE
        # - Tenant_company and Default_Plan should be created on commcell

    def run(self):
        """ Main function for test case execution."""
        try:
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company1'))
            laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                1. Enable auth code for the Tenant Company and Set default plan for Tenant Company

                2. Create a custom package that uses "Do not require end user interaction", with
                    auth code, and download the package from cloud.

                    a. Install custom package *without authcode with options:
                        <InstallationPackage>.exe /silent /install /silent

                    b. Wait for laptop full backup job to start from osc schedule.
                        Change subclient content, wait for incremental backup to trigger.
                        Execute out of place restore.

                    c. Validation
                        - Check client readiness succeeds
                        - Verify Session->nchatterflag is off in registry for clients
                        - Verify FileSystem->nLaptopAgent flag is set to 1 in registry for the client
                        - Verify Plan and company's client group associations for activated client
                        - Client is visible in Company's devices
                        - Validate client ownership is set to the activating user
            """, 200)

            self.refresh()
            laptop_helper.install_laptop(
                self.tcinputs, self.config_kwargs, self.install_kwargs, self.custompackage_kwargs
            )
            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            laptop_helper.cleanup(self.tcinputs)

    def refresh(self):
        """ Refresh the dicts """
        self.config_kwargs.clear()
        self.install_kwargs.clear()
        self.custompackage_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': True,
            'override_auth_code': False,
            'org_set_default_plan': True
        }

        self.custompackage_kwargs = {
            'authcode_flag': True,
            'requireCredentials': "false"
        }

        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': False,
        }