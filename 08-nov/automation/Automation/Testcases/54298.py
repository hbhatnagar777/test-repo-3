# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This testcase will verify [Laptop Install] - [Plans]: Interactive - EdgeMonitorApp - Install with authcode on the app

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Install.client_installation import Installation
from Laptop.laptophelper import LaptopHelper
from Server.Security.securityhelper import OrganizationHelper

class TestCase(CVTestCase):
    """[Laptop Install] - [Plans]: Interactive - EdgeMonitorApp - Install with authcode on the app"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Laptop Install] - [Plans]: Interactive - EdgeMonitorApp - Install with authcode on the app"
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
            orghelper = OrganizationHelper(self.commcell)
            orghelper.commcell_default_plan = self.tcinputs['Default_Plan']
            install_authcode = Installation(self.tcinputs, self.commcell).commcell_install_authcode()
            self.refresh(install_authcode)
            laptop_helper.install_laptop(
                self.tcinputs, self.config_kwargs, self.install_kwargs, self.custompackage_kwargs
            )
            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            laptop_helper.cleanup(self.tcinputs)

    def refresh(self, authcode):
        """ Refresh the dicts
        Args:
            authcode (str): Authcode for commcell

        """
        self.config_kwargs.clear()
        self.install_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': False,
        }
        self.custompackage_kwargs = {'hideApps': 'false'}

        self.install_kwargs = {
            'install_with_authcode': True,
            'authcode': authcode,
            'execute_simcallwrapper': False,
            'interactive_install': True,
            'check_num_of_devices': False,
        }
