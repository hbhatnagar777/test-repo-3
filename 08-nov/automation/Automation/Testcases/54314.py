# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for validating [Laptop Install] - [Plans]: Interactive - EdgeMonitorApp takeover

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelper
from Server.Security.securityhelper import OrganizationHelper

class TestCase(CVTestCase):
    """Test case class for [Laptop Re Install] - [Plans] - Re Install - Takeover  and register with user associated
        to commcell's default plan"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop Install] - [Plans]: Interactive - EdgeMonitorApp takeover"""
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}
        self.custompackage_kwargs = {}

    def run(self):
        """ Main function for test case execution."""
        try:
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Commcell'))
            laptop_helper = LaptopHelper(self)

            #-------------------------------------------------------------------------------------

            orghelper = OrganizationHelper(self.commcell)
            orghelper.commcell_default_plan = self.tcinputs['Default_Plan']
            self.refresh()
            laptop_helper.install_laptop(
                self.tcinputs, self.config_kwargs, self.install_kwargs, self.custompackage_kwargs
            )

            # Reinstall laptop client and validate laptop installation
            self.install_kwargs['delete_client'] = False
            self.install_kwargs['skip_osc'] = True
            self.install_kwargs['wait_for_reinstalled_client'] = True
            self.install_kwargs['check_num_of_devices'] = False
            self.install_kwargs['execute_simcallwrapper'] = False
            self.install_kwargs['interactive_install'] = True

            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs,
                                         self.custompackage_kwargs)
            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(excp)
            self.log.error("Testcase failed with exception [{0}]".format(excp))
            laptop_helper.cleanup(self.tcinputs)

    def refresh(self):
        """ Refresh the dicts """
        self.config_kwargs.clear()
        self.install_kwargs.clear()
        self.custompackage_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': False
        }

        self.custompackage_kwargs = {'hideApps': 'false'}

        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True,
            'interactive_install': False,
            'check_num_of_devices': False,
            'takeover_client': True,
        }

