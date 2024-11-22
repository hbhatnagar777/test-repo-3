# -*- coding: utf-8 -*-


# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for validating [Laptop Install] - [Plans- User Centric] -
Install and register with user associated to commcell's default plan

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelperUserCentric
from Server.Security.securityhelper import OrganizationHelper

class TestCase(CVTestCase):
    """Test case class for [Laptop Install] - [Plans- User Centric] -
    Install and register with user associated to commcell's default plan"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Laptop Install] - [Plans- User Centric] - Install and register with user associated to commcell's default plan"
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}
        self.custompackage_kwargs = {}

        # PRE-REQUISITES OF THE TESTCASE
        # - Please make sure to keep a session active for the client
        #    with the user that should be the owner
        #    of the client.

    def setup(self):
        """ Setup test case inputs from config template """
        platform_inputs = ["Activation_User1", "Activation_Password1"]
        testcase_inputs = LaptopHelperUserCentric.set_inputs(self, 'Commcell', [], platform_inputs)

        # Generate User map
        testcase_inputs['user_map'] = LaptopHelperUserCentric.create_pseudo_map(testcase_inputs)
        self.log.info("User map: [{0}]".format(testcase_inputs['user_map']))
        self.tcinputs.update(testcase_inputs)

    def run(self):
        """ Main function for test case execution."""
        try:
            laptop_helper = LaptopHelperUserCentric(self)

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                1. Create client group where laptop is supposed to be associated
                    [This client group is given as custom package input]

                2. Create a custom package with properties:
                    - "Do not require end user interaction"
                    - Specific client group to add the client too
                    - *Without any authcode OR user credentials
                    - Authenticate later set to true
                    - Create all shortcuts set to true

                    a. Install custom package options:
                        <InstallationPackage>.exe /silent /install /silent
                        Register with SimCallWrapper with activating user name

                    b. Validate osc backup/restore for the default subclient

                    c. Validation
                        - Check client readiness succeeds
                        - Verify Session->nchatterflag is off in registry for clients
                        - Verify FileSystem->nLaptopAgent flag is set to 1 in registry for the client
                        - The client should be a part of the default plan that was set for the commcell.
                        - Validate client ownership is set to the activating user
            """, 200)
            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                Set Default Laptop plan for the Commcell from Adminconsole->Commcell->Administration
            """)
            orghelper = OrganizationHelper(self.commcell)
            orghelper.commcell_default_plan = self.tcinputs['Default_Plan']
            self.refresh()

            laptop_helper.install_laptop(
                self.tcinputs, self.config_kwargs, self.install_kwargs, self.custompackage_kwargs
            )

        except Exception as excp:
            laptop_helper.tc.fail(excp)
            self.log.error("Testcase failed with exception [{0}]".format(excp))
        finally:
            laptop_helper.cleanup_user_centric(self.tcinputs)

    def refresh(self):
        """ Refresh the dicts
        Args:

            client_group (str): Client group
        """
        self.config_kwargs.clear()
        self.install_kwargs.clear()
        self.custompackage_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': False
        }


        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True,
            'check_num_of_devices': False,
            'client_groups': ['Laptop Clients']
        }
