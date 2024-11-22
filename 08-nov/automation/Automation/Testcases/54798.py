# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case class for validating [Laptop Install] - [MSP] - Install and register from tenant user on a fresh VM

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.vmoperations import VmOperations
from Laptop.laptophelper import LaptopHelper

class TestCase(CVTestCase):
    """"Test case class for validating [Laptop Install] - [MSP] - Install and register from tenant user on a fresh VM"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop Install] - [MSP] - Install and register from tenant user on a fresh VM"""
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.tcinputs = {
            "Tenant_company": None,
            "Default_Plan": None,
            "Activation_User": None, # User who will activate the laptop (e.g: cvadmin)
            "Activation_Password": None,
            "Machine_host_name": None,
            "Machine_user_name": None, # User who will install the laptop (e.g: root)
            "Machine_password": None,
            "vm_name": None,
            "snapshot_name": None,
            "server_type": None
        }
        self.install_kwargs = {}
        self.config_kwargs = {}
        # In case no revision needs to be passed as input, set it to 0 in inputs
        # Need it for the current release.
        # PRE-REQUISITES OF THE TESTCASE
        # - Tenant_company and Default_Plan should be created on commcell
        # - Please make sure to keep a session active for the client with the user that should be the owner
        #    of the client. [Activation_User]. Same for mac.

    def run(self):
        """ Main function for test case execution."""
        try:
            laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                1. Set default plan for Tenant Company

                2. Create a custom package that uses "Do not require end user interaction", *without
                    auth code, and download the package from cloud.

                    a. Install custom package *without authcode with options:
                        <InstallationPackage>.exe /silent /install /silent
                        Run Simcalwrapper to register the client

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
            inputs = {}
            try:
                _HYPERV_CONFIG = get_config()
                if self.tcinputs['server_type'] == "VCenter":
                    server_hostname = _HYPERV_CONFIG.Laptop.Install.ESXHostname
                    server_password = _HYPERV_CONFIG.Laptop.Install.ESXPasswd
                    server_user = _HYPERV_CONFIG.Laptop.Install.ESXUser
                elif self.tcinputs['server_type'] == "HyperV":
                    server_hostname = _HYPERV_CONFIG.Laptop.Install.HyperVHostname
                    server_password = _HYPERV_CONFIG.Laptop.Install.HyperVPasswd
                    server_user = _HYPERV_CONFIG.Laptop.Install.HyperVUser

                if server_hostname or server_password or server_user == '':
                    excp = "HyperV configuration parameters are not set in template_config.json"
                    self.result_string = str(excp)
                    raise Exception(excp)
            except Exception as err:
                self.status = constants.SKIPPED
                return
            snapshot_name = self.tcinputs['snapshot_name']
            vm_name = self.tcinputs['vm_name']
            inputs['server_host_name'] = server_hostname
            inputs['vm_name'] = vm_name
            inputs['username'] = server_user
            inputs['password'] = server_password
            inputs['server_type'] = self.tcinputs['server_type']
            self.refresh()
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)
            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            laptop_helper.cleanup(self.tcinputs)

        finally:
            self.log.info("Reverting the snapshot to a fresh vm snapshot")
            vm_obj = VmOperations.create_vmoperations_object(inputs)
            vm_obj.revert_snapshot(vm_name, snapshot_name)

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
