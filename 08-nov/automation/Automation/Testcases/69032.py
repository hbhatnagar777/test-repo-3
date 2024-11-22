# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for Cluster Deployment
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Sample input json
"69032": {
          "CVBackupAdminPassword": "password",
          "RevertSnapshots":true/false, 
          "CreateSnapshots":true/false,
          "CleanupFromCs":true/false,
          "IsoKey": "3.2312",
          "IsoDatastore":null,
          "ClusterName": ,
          "VMNames": [
            "vm-name-1",
            "vm-name-2",
            "vm-name-3"
        ],
        "HostNames": [
          "hostname1",
          "hostname2",
          "hostname3"
        ],
          "BlockName": "",
          "DPIPs": <list of dpips>,
          "SPIPs": <list of spips>,
          "Gateway": "gateway ip",
          "DNSs": <list of dnsses>,
          "DPNetmask": "data protection netmask",
          "SPNetmask": "storage pool netmask",
          "DPIFs": [
            "dp interface name",
            "dp interface name"
          ],
          "SPIFs": [
            "sp interface name",
            "sp interface name"
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
    """Hyperscale test class for Cluster Deployment"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for Cluster Deployment"
        self.result_string = ""
        self.username = ""
        self.password = ""
        self.client_name = ""
        self.dp_ips = None
        self.sp_ips = None
        self.hyperscale_helper = None
        self.tcinputs = {
        "VMNames": None,
        "AddNodeVMNames": None,
        "CVBackupAdminPassword": None,
        "RevertSnapshots": None,
        "CreateSnapshots":None,
        "CleanupFromCs":None,
        "IsoKey": None,
        "IsoDatastore":None,
        "ClusterName": None,
        "VMNames": None,
        "HostNames": None,
        "AddNodeHostNames": None,
        "BlockName": None,
        "Gateway": None,
        "DNSs": None,
        "DPNetmask": None,
        "SPNetmask": None,
        "DPIFs": None,
        "SPIFs":None
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


        self.cvbackupadmin_password = self.tcinputs["CVBackupAdminPassword"]
        self.revert_snapshots = self.tcinputs["RevertSnapshots"]
        self.create_snapshots = self.tcinputs["CreateSnapshots"]
        self.cleanup_from_cs = self.tcinputs["CleanupFromCs"]
        self.cluster_name = self.tcinputs["ClusterName"]
        self.vm_names = self.tcinputs['VMNames']
        self.add_node_names = self.tcinputs['AddNodeVMNames']
        self.vm_hostnames = self.tcinputs.get('HostNames', self.vm_names)
        self.add_node_hostnames = self.tcinputs.get('AddNodeHostNames', self.add_node_names)
        self.dp_ips = self.tcinputs.get('DPIPs')
        if not self.dp_ips and "." in self.vm_hostnames[0]:
            self.dp_ips = [socket.gethostbyname(name) for name in self.vm_hostnames]
        self.sp_ips = self.tcinputs.get('SPIPs')
        if not self.sp_ips:
            self.sp_ips = ["192.168."+ip.split(".", 2)[-1] for ip in self.dp_ips]

        self.iso_key = self.tcinputs["IsoKey"]
        self.iso_datastore = self.tcinputs.get("IsoDatastore")
        self.gateway = self.tcinputs['Gateway']
        self.dnss = self.tcinputs['DNSs']
        self.dp_ifs = self.tcinputs['DPIFs']
        self.sp_ifs = self.tcinputs['SPIFs']
        self.dp_nm = self.tcinputs['DPNetmask']
        self.sp_nm = self.tcinputs['SPNetmask']
        self.block_name = self.tcinputs['BlockName']

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


    def run(self):
        try:
        
            self.successful = HyperscaleSetup.start_hsx_setup(
                host=self.esx_hostname,
                user=self.esx_username,
                password=self.esx_password,
                vm_names=self.vm_names,
                add_node_names=self.add_node_names,
                vm_hostnames=self.vm_hostnames,
                add_node_hostnames=self.add_node_hostnames,
                iso_key=self.iso_key,
                iso_datastore=self.iso_datastore,
                sp_ips=self.sp_ips,
                dp_ips=self.dp_ips,
                gateway=self.gateway,
                dnss=self.dnss,
                dp_ifs=self.dp_ifs,
                sp_ifs=self.sp_ifs,
                dp_nm=self.dp_nm,
                sp_nm=self.sp_nm,
                block_name=self.block_name,
                cluster_name=self.cluster_name,
                cs_host=self.client_name,
                cs_user=self.username,
                cs_password=self.password,
                cvbackupadmin_password=self.cvbackupadmin_password,
                revert_snapshots=self.revert_snapshots,
                create_snapshots=self.create_snapshots,
                cleanup_from_cs=self.cleanup_from_cs
            )

        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
            
