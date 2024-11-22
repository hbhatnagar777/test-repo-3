# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for enabling/disabling root user using the API
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Sample input json
"70273": {
        "RootAccess": "true/false",
        "RootPassword": if not provided, using CVBackupAdminPassword,
        "CVBackupAdminPassword": "password",
        "StoragePoolName": name of the storage pool,
        "FirewallAddICMPIfRootEnable": to enable icmp (only if root is to be enabled)
        "VMNames": [
            "vm-name-1",
            "vm-name-2",
            "vm-name-3"
            ],
        "HostNames": [
            "hostname1",
            "hostname2",
            "hostname3"
            ]
        }
"""
# The following keys must be present under HyperScale key
# in config.json file
vmconfig_help = '''
"HyperScale": {
    "Credentials": {
        "User": "default hyperscale username",
        "Password": "default hyperscale password"
    },
    "VMConfig": {
        "ServerHostName": "Host name of the VM server",
        "Username": "Login user for the VM server",
        "Password": "password for the user"
    }
}
'''

import atexit
import re
import time
from datetime import datetime
import socket
from pathlib import Path
import threading

import requests
from AutomationUtils import commonutils, constants, vmoperations
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.machine import Machine
from AutomationUtils.unix_machine import UnixMachine
from AutomationUtils.vmoperations import VmOperations
from HyperScale.HyperScaleUtils.esx_console import EsxConsole
from HyperScale.HyperScaleUtils.esx_screenshot import EsxScreenshot
from HyperScale.HyperScaleUtils.esxManagement import EsxManagement
from HyperScale.HyperScaleUtils.esx_vm_io import EsxVmIo
from HyperScale.HyperScaleUtils.vm_io import VmIo
from MediaAgents.MAUtils.hyperscale_setup import HyperscaleSetup
from MediaAgents.MAUtils.screen_matcher import ScreenMatcher
from pyVim import connect
from pyVim.task import WaitForTask
from pyVmomi import vim

from Web.Common.cvbrowser import BrowserFactory


class TestCase(CVTestCase):
    """Hyperscale test class for enabling/disabling root user using the API"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for Cluster Deployment"
        self.result_string = ""
        self.username = ""
        self.password = ""
        self.client_name = ""
        self.hyperscale_helper = None
        self.tcinputs = {
            "RootAccess": None,
            "VMNames": None,
            "CVBackupAdminPassword": None,
            "VMNames": None,
            "HostNames": None,
        }
        self.successful = False

    def setup(self):
        """Initializes test case variables"""
        self.username = self.inputJSONnode["commcell"]["commcellUsername"]
        self.password = self.inputJSONnode["commcell"]["commcellPassword"]
        self.client_name = self.inputJSONnode["commcell"]["webconsoleHostname"]
        # VM setup + VM automation
        self.hs_vm_config = self.tcinputs.get("VMConfig")
        if self.hs_vm_config:
            self.esx_hostname = self.hs_vm_config["ServerHostName"]
            self.esx_username = self.hs_vm_config["Username"]
            self.esx_password = self.hs_vm_config["Password"]
        else:
            self.config = get_config()
            if not hasattr(self.config.HyperScale, 'VMConfig'):
                raise(f"Please add VMConfig to HyperScale in config.json file as {vmconfig_help}")
            self.hs_vm_config = self.config.HyperScale.VMConfig
            self.esx_hostname = self.hs_vm_config.ServerHostName
            self.esx_username = self.hs_vm_config.Username
            self.esx_password = self.hs_vm_config.Password
        
        vm_config = {
            'server_type': 'vCenter',
            'server_host_name': self.esx_hostname,
            'username': self.esx_username,
            'password': self.esx_password
        }

        self.root_access = self.tcinputs["RootAccess"]
        self.cvbackupadmin_password = self.tcinputs["CVBackupAdminPassword"]
        self.vm_names = self.tcinputs['VMNames']
        self.vm_hostnames = self.tcinputs['HostNames']
        self.root_password = self.tcinputs.get('RootPassword')
        self.allow_icmp_if_root_enable = self.tcinputs.get("FirewallAddICMPIfRootEnable", self.root_access)
        if not self.root_password:
            self.root_password = self.cvbackupadmin_password
        self.storage_pool_name = self.tcinputs.get('StoragePoolName', 
                                                   HyperscaleSetup.generate_storage_pool_name(self.vm_names))
    def tear_down(self):
        """Tear down function for this test case"""
        # Deleting created objects for backup
        self.log.info(f"tear_down {self.id}")
        if self.successful:
            self.log.info("Test case successful.")
        else:
            self.status = constants.FAILED
    
    def fail_test_case(self, reason):
        """Prints failure reason, sets the result string

            Args:
                reason         (str)   --  Failure reason

        """
        self.log.error(reason)
        self.result_string = reason
        self.status = constants.FAILED
        self.successful = False
    

    def verify_root_access(self, root_access, vm_hostnames, root_password):
        """Checks whether all nodes comply to root_access parameter

            Args:

                root_access     (bool)  --  True to ensure if all nodes should have root access
                                            False, if not

                vm_hostnames    (list)  --  List of nodes to check root access on

                root_password   (str)   --  Root password

                
            Returns:

                result          (bool)  -- Checks whether all nodes comply to root_access parameter

        """
        import paramiko
        ssh=paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        root_enabled_count = len(vm_hostnames)
        for vm_hostname in vm_hostnames:
            try:
                ssh.connect(vm_hostname, port=22, username='root', password=root_password)
                self.log.info(f"Root is enabled on node {vm_hostname}")
            except Exception as e:
                if "Bad authentication type" in str(e):
                    self.log.info(f"Root is disabled on node {vm_hostname}")
                    root_enabled_count -= 1
                else:
                    raise
        # if root enabled and all ssh work
        if root_access and root_enabled_count == len(vm_hostnames):
            return True
        # if root to be disabled and no ssh work
        if not root_access and not root_enabled_count:
            return True
        return False

    def run(self):
        try:
            
            # send req to api
            esx = HyperscaleSetup._get_esx(host=self.esx_hostname,
                                            user=self.esx_username,
                                            password=self.esx_password
                                        )
            
            # setting root access
            self.log.info(f"Setting root Access on {self.vm_names}")
            result = HyperscaleSetup.set_root_access_on_cluster(
            vm_names=self.vm_names, 
            vm_hostnames=self.vm_hostnames, 
            cs_hostname=self.client_name, 
            cs_username= self.username,
            cs_password=self.password,
            storage_pool_name=self.storage_pool_name, 
            root_access=self.root_access)
            if not result:
                self.fail_test_case(f"Failed to set root access as {str(self.root_access)}")
                return
            self.log.info(f"Successfully set root access as {str(self.root_access)}")

            # to create machine objects firewall must allow ICMP, so adding Firewall rules
            # root access enable and add firewall rule
            if self.allow_icmp_if_root_enable and self.root_access:
                result = HyperscaleSetup.firewall_add_icmp_rule(
                    host=self.esx_hostname,
                    user=self.esx_username,
                    password=self.esx_password,
                    vm_names=self.vm_names,
                    vm_hostnames=self.vm_hostnames,
                    root_password=self.root_password
                )
                if not result:
                    return self.fail_test_case("Unable to get vm_io")
                self.log.info("Successfully enabled ICMP traffic")

            # if root access to be enabled and icmp enabled then no need to fire this
            # if root access to be enabled but firewall not enabled then we must fire this
            # lastly if root access disabled then we fire this to check if all nodes are disabled
            if not(self.root_access and self.allow_icmp_if_root_enable)\
                or (self.root_access and not self.allow_icmp_if_root_enable)\
                or not self.root_access:
                result = self.verify_root_access(self.root_access, self.vm_hostnames, self.root_password)
                if not result:
                    return self.fail_test_case(f"Failed setting Root access to {self.root_access}")
            self.successful = True

        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
            