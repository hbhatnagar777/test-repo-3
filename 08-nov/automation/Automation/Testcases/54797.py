# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for validating [Laptop Install] - [Plans] - Install and register with user associated to commcell's
    default plan on a fresh VM

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.vmoperations import VmOperations
from AutomationUtils.config import get_config
from Laptop.laptophelper import LaptopHelper
from Server.Security.securityhelper import OrganizationHelper


class TestCase(CVTestCase):
    """Test case class for [Laptop Install] - [Plans] - Install and register with user associated
        to commcell's default plan and validate backup now button
        Pre Requisites:  Need a VM with a fresh snapshot after creating the VM"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """ [Laptop Install] - [Plan] - Install and register from EdgeMonitorApp on a fresh VM"""
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.tcinputs = {
            "vm_name": None,
            "snapshot_name": None,
            "server_type": None
        }

        self.install_kwargs = {}
        self.config_kwargs = {}
        self.custompackage_kwargs = {}

        # In case no revision needs to be passed as input, set it to 0 in inputs
        # Need it for the current release.

    def run(self):
        """ Main function for test case execution."""
        try:
            #-------------------------------------------------------------------------------------
            try:
                self.tcinputs.update(LaptopHelper.set_inputs(self, 'Commcell'))
                laptop_helper = LaptopHelper(self)
                orghelper = OrganizationHelper(self.commcell)
                inputs = {}
                _HYPERV_CONFIG = get_config()
                if self.tcinputs['server_type'] == "VCenter":
                    self.server_hostname = _HYPERV_CONFIG.Laptop.Install.ESXHostname
                    self.server_password = _HYPERV_CONFIG.Laptop.Install.ESXPasswd
                    self.server_user = _HYPERV_CONFIG.Laptop.Install.ESXUser
                elif self.tcinputs['server_type'] == "HyperV":
                    self.server_hostname = _HYPERV_CONFIG.Laptop.Install.HyperVHostname
                    self.server_password = _HYPERV_CONFIG.Laptop.Install.HyperVPasswd
                    self.server_user = _HYPERV_CONFIG.Laptop.Install.HyperVUser

                if self.server_hostname or self.server_password or self.server_user is None:
                    excp = "HyperV configuration parameters are not set in template_config.json"
                    self.result_string = str(excp)
                    raise Exception(excp)
            except Exception:
                self.status = constants.SKIPPED
                return

            orghelper.commcell_default_plan = self.tcinputs['Default_Plan']
            snapshot_name = self.tcinputs['snapshot_name']
            vm_name = self.tcinputs['vm_name']
            inputs['server_host_name'] = self.server_hostname
            inputs['vm_name'] = vm_name
            inputs['username'] = self.server_user
            inputs['password'] = self.server_password
            inputs['server_type'] = self.tcinputs['server_type']
            self.refresh()
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs,
                                         self.custompackage_kwargs)
            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(excp)
            self.log.error("Testcase failed with exception [{0}]".format(excp))
            laptop_helper.cleanup(self.tcinputs)

        finally:
            if inputs:
                self.log.info("Reverting the snap for the next run to be a fresh install")
                vm_obj = VmOperations.create_vmoperations_object(inputs)
                vm_obj.revert_snapshot(vm_name, snapshot_name)

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
            'execute_simcallwrapper': False,
            'interactive_install': True,
            'check_num_of_devices': False,
            'validate_user': True,
            'backupnow': True
        }
