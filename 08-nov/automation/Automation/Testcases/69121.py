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
"69121": {
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
vmconfig_help = """
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
"""

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
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from MediaAgents.MAUtils.hyperscale_setup import HyperscaleSetup
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.screen_matcher import ScreenMatcher
from pyVim import connect
from pyVim.task import WaitForTask
from pyVmomi import vim
from Metallic.hubutils import HubManagement
import time
import datetime
import base64
from cvpysdk.commcell import Commcell


class TestCase(CVTestCase):
    """Hyperscale test class for Cluster Deployment"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for HSX Metallic Setup configuration"
        self.result_string = ""
        self.username = ""
        self.password = ""
        self.client_name = ""
        self.dp_ips = None
        self.sp_ips = None
        self.tenant_hyperscale_helper = None
        self.cvautoexec_hyperscale_helper = None
        self.tenant_commcell = None
        self.client_name = None
        self.backup_gateway_host = None
        self.backup_gateway_port = None
        self.tcinputs = {
            "VMNames": None,
            "CVBackupAdminPassword": None,
            "RevertSnapshots": None,
            "CreateSnapshots": None,
            "CleanupFromCs": None,
            "IsoKey": None,
            "IsoDatastore": None,
            "ClusterName": None,
            "VMNames": None,
            "HostNames": None,
            "BlockName": None,
            "Gateway": None,
            "DNSs": None,
            "DPNetmask": None,
            "SPNetmask": None,
            "DPIFs": None,
            "SPIFs": None,
            "ClientName": None,
            "BackupGatewayHost": None,
            "BackupGatewayPort": None
        }
        self.successful = False

    def setup(self):
        """Initializes test case variables"""
        self.cs_hostname = self.inputJSONnode["commcell"]["webconsoleHostname"]
        self.username = self.inputJSONnode["commcell"]["commcellUsername"]
        self.password = self.inputJSONnode["commcell"]["commcellPassword"]
        self.tenant_admin = self.tcinputs["TenantAdmin"]
        self.tenant_password = self.tcinputs["TenantPassword"]
        self.client_name = self.tcinputs["ClientName"]
        self.backup_gateway_host = self.tcinputs["BackupGatewayHost"]
        self.backup_gateway_port = self.tcinputs["BackupGatewayPort"]
        self.client_machine = Machine(self.client_name, self.commcell)
        self.tenant_commcell = Commcell(
            self.cs_hostname, self.tenant_admin, self.tenant_password
        )
        # VM setup + VM automation
        self.hs_vm_config = self.tcinputs.get("VMConfig")
        if self.hs_vm_config:
            self.esx_hostname = self.hs_vm_config["ServerHostName"]
            self.esx_username = self.hs_vm_config["Username"]
            self.esx_password = self.hs_vm_config["Password"]
        else:
            self.config = get_config()
            if not hasattr(self.config.HyperScale, "VMConfig"):
                raise (
                    f"Please add VMConfig to HyperScale in config.json file as {vmconfig_help}"
                )
            self.hs_vm_config = self.config.HyperScale.VMConfig
            self.esx_hostname = self.hs_vm_config.ServerHostName
            self.esx_username = self.hs_vm_config.Username
            self.esx_password = self.hs_vm_config.Password

        vm_config = {
            "server_type": "vCenter",
            "server_host_name": self.esx_hostname,
            "username": self.esx_username,
            "password": self.esx_password,
        }

        self.node_user = self.tcinputs["NodeUser"]
        self.node_password = self.tcinputs["NodePassword"]
        self.cvbackupadmin_password = self.tcinputs["CVBackupAdminPassword"]
        self.revert_snapshots = self.tcinputs["RevertSnapshots"]
        self.create_snapshots = self.tcinputs["CreateSnapshots"]
        self.cleanup_from_cs = self.tcinputs["CleanupFromCs"]
        self.cluster_name = self.tcinputs["ClusterName"]
        self.vm_names = self.tcinputs["VMNames"]
        self.vm_hostnames = self.tcinputs.get("HostNames", self.vm_names)
        self.add_node_names = self.tcinputs["AddNodeVMNames"]
        self.add_node_hostnames = self.tcinputs["AddNodeHostNames"]
        self.dp_ips = self.tcinputs.get("DPIPs")
        if not self.dp_ips and "." in self.vm_hostnames[0]:
            self.dp_ips = [socket.gethostbyname(name) for name in self.vm_hostnames]
        self.sp_ips = self.tcinputs.get("SPIPs")
        if not self.sp_ips:
            self.sp_ips = ["192.168." + ip.split(".", 2)[-1] for ip in self.dp_ips]

        self.iso_key = self.tcinputs["IsoKey"]
        self.iso_datastore = self.tcinputs.get("IsoDatastore")
        self.gateway = self.tcinputs["Gateway"]
        self.dnss = self.tcinputs["DNSs"]
        self.dp_ifs = self.tcinputs["DPIFs"]
        self.sp_ifs = self.tcinputs["SPIFs"]
        self.dp_nm = self.tcinputs["DPNetmask"]
        self.sp_nm = self.tcinputs["SPNetmask"]
        self.block_name = self.tcinputs["BlockName"]

        self.control_nodes = self.tcinputs["HostNames"]
        self.ma_machines = {}
        self.mas = []
        for ma_name in self.control_nodes:
            if self.commcell.clients.has_client(ma_name):
                self.mas.append(ma_name)
                # username/password is necessary as MAs will be marked in maintenance mode
                self.log.info(f"Creating machine object for: {ma_name}")
                machine = UnixMachine(
                    ma_name, username=self.node_user, password=self.node_password
                )
                self.ma_machines[ma_name] = machine

        self.cvautoexec_hyperscale_helper = HyperScaleHelper(
            self.commcell, self.csdb, self.log
        )
        self.tenant_hyperscale_helper = HyperScaleHelper(
            self.tenant_commcell, self.csdb, self.log
        )

        # CSDB
        self.config = get_config()
        tcinputs_sql_login = self.tcinputs.get("SqlLogin")
        tcinputs_sql_password = self.tcinputs.get("SqlPassword")
        if tcinputs_sql_login == "":
            # go for default credentials
            if not hasattr(self.config.SQL, "Username"):
                raise Exception(
                    f"Please add default 'Username' to SQL in config.json file OR provide SqlLogin in TC inputs"
                )
            self.sql_login = self.config.SQL.Username
            if not hasattr(self.config.SQL, "Password"):
                raise Exception(f"Please add default 'Password' to SQL in config.json")
            self.sql_sq_password = self.config.SQL.Password
        else:
            # received a sql username from user
            self.sql_login = tcinputs_sql_login
            self.sql_sq_password = tcinputs_sql_password

    def create_tenant(self):
        """
        Create a new tenant for the automation
        """
        date_info = datetime.datetime.now()
        self.company_name = date_info.strftime("HSX-Automation-Metallic")
        self.unique_param = date_info.strftime("%d-%B-%H-%M")
        user_firstname = "HSX_tenantadmin"
        user_lastname = "user"
        user_email = user_firstname + user_lastname + "@domain.com"
        user_phonenumber = "00000000"
        user_country = self.tcinputs.get("UserCountry", "United States")
        self.log.info(f"Creating Tenant with Company name {self.company_name}")
        # Create a tenant and get password that is returned
        self.cs_user = self.hub_management.create_tenant(
            company_name=self.company_name,
            email=user_email,
            first_name=user_firstname,
            last_name=user_lastname,
            phone_number=user_phonenumber,
            country=user_country,
        )

    def create_test_data(self, path, content_gb):
        """Creates the test data with content_gb size at given path
        Args:
            path        (str)   -- The path where data is to be created
            content_gb  (int)   -- The size of the data in gb
        Returns:
            result      (bool)  -- If data got created
        """
        if self.client_machine.check_directory_exists(path):
            self.client_machine.remove_directory(path)
        self.client_machine.create_directory(path)
        result = self.options_selector.create_uncompressable_data(
            "mmtest1_30", path, content_gb, num_of_folders=1, file_size=0
        )
        if not result:
            return False
        return True

    def cleanup_test_data(self):
        """Clears the test data directory"""
        path = self.test_case_path
        if self.client_machine.check_directory_exists(path):
            self.client_machine.remove_directory(path)
            self.log.info(f"Cleared {path} on {self.client_name}")
        else:
            self.log.info(f"Already cleared {path} on {self.client_name}")

    def fail_test_case(self, reason):
        """Prints failure reason, sets the result string
        Args:
            reason         (str)   --  Failure reason
        """
        self.log.error(reason)
        self.result_string = reason
        self.status = constants.FAILED
        self.successful = False

    def get_client_content_folder(self, prefix, content_gb, parent=None):
        """Returns the folder path which will be backed up or restored to
        Args:
            prefix      (str)   -- The string to add in folder name
            content_gb  (int)   -- The size of the data (used in name)
            parent      (str)   -- The parent path to join to (optional)
        Returns:
            name        (str)   -- The folder name
        """
        folder = f"Data{prefix}-{content_gb}Gb"
        if parent:
            folder = self.client_machine.join_path(self.test_data_path, folder)
        return folder

    def cleanup(self):
        """Cleans up the test case resources and directories"""

        policy_exists = self.commcell.storage_policies.has_policy(
            self.storage_policy_name
        )
        if policy_exists:
            policy_obj = self.commcell.storage_policies.get(self.storage_policy_name)
            # TODO: kill all jobs related to the subclient before doing this
            policy_obj.reassociate_all_subclients()
            self.log.info(f"Reassociated all {self.storage_policy_name} subclients")
        if self.backupset.subclients.has_subclient(self.subclient_name):
            self.backupset.subclients.delete(self.subclient_name)
            self.log.info(f"{self.subclient_name} deleted")
        if policy_exists:
            self.commcell.storage_policies.delete(self.storage_policy_name)
            self.log.info(f"{self.storage_policy_name} deleted")
        self.cleanup_test_data()

        for ma in self.mas:
            ma_obj = self.commcell.media_agents.get(ma)
            ma_obj.mark_for_maintenance(False)
        self.log.info("All MAs marked out of maintenance")

    def tear_down(self):
        """Tear down function for this test case"""
        # Deleting created objects for backup
        self.log.info(f"tear_down {self.id}")
        if self.successful:
            self.log.info("Test case successful.")
            self.status == constants.PASSED
        else:
            self.status = constants.FAILED

    def run(self):
        try:
            self.successful = True
            HyperscaleSetup.metallic_start_hsx_setup(
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
                cs_host=self.cs_hostname,
                cvautoexec_user=self.username,
                cvautoexec_password=self.password,
                tenant_admin=self.tenant_admin,
                tenant_password=self.tenant_password,
                backup_gateway_host=self.backup_gateway_host,
                backup_gateway_port=self.backup_gateway_port,
                cvbackupadmin_password=self.cvbackupadmin_password,
                revert_snapshots=self.revert_snapshots,
                create_snapshots=self.create_snapshots,
                cleanup_from_cs=self.cleanup_from_cs,
            )

            self.storage_pool_name = (
                self.tenant_hyperscale_helper.get_storage_pool_from_media_agents(
                    self.mas
                )
            )
            if not self.storage_pool_name:
                self.log.info("creating storage pool: %s", self.cluster_name)
                status, response = (
                    self.tenant_hyperscale_helper.hsx_create_storage_pool(
                        self.cluster_name, self.vm_names
                    )
                )
                # Validating storage pool after creation
                status = False
                attempts = 5
                while status is False and attempts != 0:
                    status = (
                        self.tenant_hyperscale_helper.check_if_storage_pool_is_present(
                            self.cluster_name
                        )
                    )
                    if status is False:
                        self.log.info(
                            "Storage pool not present, waiting for entry to be added"
                        )
                    time.sleep(120)
                    attempts = attempts - 1
                if status is False:
                    raise Exception("Storage Pool creation failed")
                else:
                    self.log.info("Storage Pool creation Successful")

        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception(
                "Exception message while executing test case: %s", self.result_string
            )
