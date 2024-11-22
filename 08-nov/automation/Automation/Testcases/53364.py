# -*- coding: utf-8 -*-


# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This testcase will verify you can [Server Install] - Install and register with authcode of commcell

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop import laptopconstants as LC
from Laptop.laptophelper import LaptopHelper
from Install.client_installation import Installation
from Server.Security.securityhelper import OrganizationHelper

class TestCase(CVTestCase):
    """Test case class for [Server Install] - Install and register with authcode of commcell"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Server Install] - Install and register with authcode of commcell"""
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}
        self.custompackage_kwargs = {}

        # PRE-REQUISITES OF THE TESTCASE
        # - A laptop Plan should be created on commcell which should be associated to the commcell
        # Skipping Mac as this testcase is for Server backups.

    def run(self):
        """ Main function for test case execution."""
        try:
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Commcell', ["Server_Plan"], []))
            laptop_helper = LaptopHelper(self)

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                - Turn on authcode from the commcell level from AdminConsole->Commcell->Administration
                  Set Default Laptop plan for the Commcell from Adminconsole->Commcell->Administration

                - Create a custom package from cloud workflow that uses "Do not require end user interaction"
                    *without the authcode.
                - Download the package from cloud and copy it on the client machine.
                - Install relevant platform packages on client
                    <Package executable> /wait /silent /install /silent
                    Run SimCalwrapper with authcode
                - Once the client is registered a backup job should get triggered automatically from OSC schedule.
                    Wait for job to complete.
                - Modify subclient content and add new content. Automatic incremental backup should be triggered for
                    new content added.
                - Execute out of place restore for the content backed by backup job.
                - Uninstall client

                Validation:
                    - Check client readiness succeeds
                    - Verify Session->nchatterflag is off in registry for clients
                    - Verify FileSystem->nLaptopAgent flag is set to 1 in registry for the client
                    - The client should be a part of the default plan that was set for the commcell.
                    - Validate client ownership is set to the activating user
            """, 200)

            orghelper = OrganizationHelper(self.commcell)
            install_authcode = Installation(self.tcinputs, self.commcell).commcell_install_authcode()
            orghelper.commcell_default_plan = self.tcinputs['Server_Plan']
            clientgroup = LC.CG_AUTH_REGISTER
            _ = laptop_helper.entities.create({'clientgroup':{'name': clientgroup}})
            self.refresh(clientgroup, install_authcode)
            laptop_helper.install_laptop(
                self.tcinputs, self.config_kwargs, self.install_kwargs, self.custompackage_kwargs
            )
            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(excp)
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            laptop_helper.cleanup(self.tcinputs)

    def refresh(self, clientgroup, authcode):
        """ Refresh the dicts
        Args:
            client_group (str): Client group

            authcode (str): authcode for instllation on Commcell
        """
        self.config_kwargs.clear()
        self.install_kwargs.clear()
        self.custompackage_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': False
        }

        # Do not configure for laptop package, as this test case is applicable for Servers only.
        self.custompackage_kwargs = {
            'laptopClient': "false",
            'ClientGroups': clientgroup
        }

        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True,
            'register_authcode': authcode,
            'check_num_of_devices': False,
            'client_groups': [clientgroup],
            'expected_owners': [],
            'post_osc_backup': False,
            'nLaptopAgent': 0,
            'LaunchEdgeMonitor': "false",
            'check_client_activation': False
        }
