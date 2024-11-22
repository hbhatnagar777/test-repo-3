# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test Case for HSX add node
Main file for executing this test case
TestCase is the only class defined in this file.
TestCase: Class for executing this test case
TestCase:
    __init__()                      --  initialize TestCase class
    setup()                         --  setup function of this test case
    setup_vm_automation()           --  Initializes the VM automation helpers
    cleanup()                       --  Cleans up the test case resources and directories
    tear_down()                     --  Tear down function of this test case

    get_sp_version_from_cs()        -- Returns SP version as indicated by CS from client name
    parse_which_commit_output()     -- Parses the ./whichCommit.sh output
    get_which_commit_output()       -- Retrieves the ./whichCommit.sh output for all MAs
    verify_output_changed_post_upgrade() -- Verifies that the output is different post upgrade
    parse_cluster_details()         -- Parses the cluster details output

    check_identical_values()        -- Runs same operation across multiple MAs for output equality.

    fail_test_case()                -- Prints failure reason, sets the result string

    get_client_content_folder()     -- Returns the folder path which will be backed up or restored to

    create_test_data()              -- Creates the test data with content_gb size

    cleanup_test_data()             -- Clears the test data directory

    run()                           --  run function of this test case

Sample input json
"tc_id": {
            "ControlNodes": {
              "MA1": "name",
              "MA2": "name",
              "MA3": "name"
            },
            "CacheNode": {
              "name": "name",
              "username": "username",
              "password": "password"
            },
            "AddNode": {
             "name": "name",
              "username": "username",
              "password": "password",
              "serial_no": "serial_no",
              "dp_ip": "dp_ip",
              "sp_ip": "sp_ip"
          },
            "StoragePoolName": "name",
            "workflow_name" : "workflow_name",
            "SqlLogin": login, (OPTIONAL)
            "SqlPassword": password (OPTIONAL)
         }
"""
# The following keys must be present under HyperScale key
# in config.json file
vmconfig_help = '''
"HyperScale": {
    ...,
    "VMConfig": {
        "ServerHostName": "Host name of the VM server",
        "Username": "Login user for the VM server",
        "Password": "password for the user"
    }
}
'''

from pyVim import connect
from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.vmoperations import VmOperations
from HyperScale.HyperScaleUtils.esxManagement import EsxManagement
from HyperScale.HyperScaleUtils.vm_io import VmIo
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.options_selector import OptionsSelector
from Web.Common.cvbrowser import (
    Browser, BrowserFactory
)
from Web.WebConsole.webconsole import WebConsole
from Web.AdminConsole.adminconsole import AdminConsole
from Web.WebConsole.Forms.forms import Forms
from Server.Workflow.workflowhelper import WorkflowHelper
from Server.JobManager.jobmanager_helper import JobManager
import time
import re
import atexit


class TestCase(CVTestCase):
    """Hyperscale test class for HSX Add node"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for Add node HSX"
        self.result_string = ""
        self.backupset = ""
        self.backupset_name = ""
        self.subclient_obj = ""
        self.username = ""
        self.password = ""
        self.client = ""
        self.subclient_name = ""
        self.storage_policy = ""
        self.client_name = ""
        self.client_machine = ""
        self.cache_node = ""
        self.control_nodes = {}
        self.ma1 = ""
        self.ma2 = ""
        self.ma3 = ""
        self.mas = []
        self.storage_pool_name = ""
        self.sql_sq_password = ""
        self.sql_login = ""
        self.storage_policy_name = ""
        self.policy = ""
        self.hyperscale_helper = None
        self.add_node_name = ""
        self.add_node_username = ""
        self.add_node_password = ""
        self.serial_no = ""
        self.dp_ip = ""
        self.sp_ip = ""
        self.cache_node_sds = ""
        self.cache_node_username = ""
        self.cache_node_password = ""
        self.ma_machines = ""
        self.cache_machine = ""
        self.other_mas = ""
        self.other_mas_sds = ""
        self.config = ""
        self.mmhelper_obj = ""
        self.options_selector = ""
        self.content_gb = ""
        self.drive = ""
        self.test_case_path = ""
        self.test_data_path = ""
        self.content_path = ""
        self.restore_data_path = ""
        self.restore_path = ""
        self.hs_vm_config = ""
        self.CVUPGRADEOS_LOG = ""
        self.cache_node_install_directory = ""
        self.CVUPGRADEOS_LOG_PATH = ""
        self.HVCMD_LOG = ""
        self.cumulative_hvcmd = ""
        self.YUM_OUT_LOG = ""
        self.YUM_OUT_LOG_PATH = ""
        self.key = ""
        self.workflow_name = ""
        self.workflow = ""
        self.vm_io = ""
        self.esx = ""
        self.tcinputs = {
            "ControlNodes": {
              "MA1": "name",
              "MA2": "name",
              "MA3": "name"
            },
            "CacheNode": {
              "name": "name",
              "username": "username",
              "password": "password"
            },
            "AddNode": {
             "name": "name",
              "username": "username",
              "password": "password",
              "serial_no": "serial_no",
              "dp_ip": "dp_ip",
              "sp_ip": "sp_ip"
          },
            "StoragePoolName": "name",
            "workflow_name" : "workflow_name",
            "SqlLogin": "login, (OPTIONAL)",
            "SqlPassword": "password (OPTIONAL)",
         }
        self.successful = False

    def setup(self):
        """Initializes test case variables"""
        self.username = self.inputJSONnode["commcell"]["commcellUsername"]
        self.password = self.inputJSONnode["commcell"]["commcellPassword"]
        self.client_name = self.commcell.commserv_name
        self.client_machine = Machine(self.client_name, self.commcell)
        # Cache node setup
        self.cache_node = self.tcinputs["CacheNode"]["name"]
        self.add_node_name = self.tcinputs["AddNode"]["name"]
        self.add_node_username = self.tcinputs["AddNode"]["username"]
        self.add_node_password = self.tcinputs["AddNode"]["password"]
        self.serial_no = self.tcinputs["AddNode"]["serial_no"]
        self.dp_ip = self.tcinputs["AddNode"]["dp_ip"]
        self.sp_ip = self.tcinputs["AddNode"]["sp_ip"]
        if not self.commcell.clients.has_client(self.cache_node):
            raise Exception(f"{self.cache_node} MA doesn't exist")
        self.cache_node_sds = f'{self.cache_node}sds'
        self.cache_node_username = self.tcinputs["CacheNode"]["username"]
        self.cache_node_password = self.tcinputs["CacheNode"]["password"]
        # MA setup
        self.control_nodes = self.tcinputs["ControlNodes"]
        self.ma1 = self.control_nodes["MA1"]
        self.ma2 = self.control_nodes["MA2"]
        self.ma3 = self.control_nodes["MA3"]
        self.ma_machines = {}
        for node in self.control_nodes:
            ma_name = self.control_nodes[node]
            if not self.commcell.clients.has_client(ma_name):
                raise Exception(f"{ma_name} MA doesn't exist")
            self.mas.append(ma_name)
            # username/password is necessary as MAs will be marked in maintenance mode
            self.log.info(f"Creating machine object for: {ma_name}")
            machine = Machine(ma_name, username=self.cache_node_username, password=self.cache_node_password)
            self.ma_machines[ma_name] = machine
        self.cache_machine = self.ma_machines[self.cache_node]
        self.other_mas = [ma for ma in self.mas if ma != self.cache_node]
        self.other_mas_sds = [f'{ma}sds' for ma in self.other_mas]

        # CSDB
        self.config = get_config()
        tcinputs_sql_login = self.tcinputs.get('SqlLogin')
        tcinputs_sql_password = self.tcinputs.get('SqlPassword')
        if tcinputs_sql_login is None:
            # go for default credentials
            if not hasattr(self.config.SQL, 'Username'):
                raise Exception(
                    f"Please add default 'Username' to SQL in config.json file OR provide SqlLogin in TC inputs")
            self.sql_login = self.config.SQL.Username
            if not hasattr(self.config.SQL, 'Password'):
                raise Exception(f"Please add default 'Password' to SQL in config.json")
            self.sql_sq_password = self.config.SQL.Password
        else:
            # received a sql username from user
            self.sql_login = tcinputs_sql_login
            self.sql_sq_password = tcinputs_sql_password

        # Subclient & Storage setup
        self.storage_pool_name = self.tcinputs.get('StoragePoolName')
        self.client = self.commcell.clients.get(self.client_name)
        self.agent = self.client.agents.get("FILE SYSTEM")
        self.backupset_name = "defaultBackupSet"
        self.backupset = self.agent.backupsets.get(self.backupset_name)
        self.subclient_name = f"{self.id}_subclient"
        self.storage_policy_name = f"{self.id}_policy"
        self.mmhelper_obj = MMHelper(self)
        self.options_selector = OptionsSelector(self.commcell)
        self.content_gb = 1
        self.drive = self.options_selector.get_drive(self.client_machine, 2 * self.content_gb * 1024)

        # Backup and restore paths
        self.test_case_path = self.client_machine.join_path(self.drive, "Automation", str(self.id))
        self.test_data_path = self.client_machine.join_path(self.test_case_path, "Testdata")
        self.content_path = self.get_client_content_folder('1', self.content_gb, self.test_data_path)
        self.restore_data_path = self.client_machine.join_path(self.test_case_path, 'Restore')
        self.restore_path = self.get_client_content_folder('1', self.content_gb, self.restore_data_path)
        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

        # VM setup
        if not hasattr(self.config.HyperScale, 'VMConfig'):
            raise Exception(f"Please add VMConfig to HyperScale in config.json file as {vmconfig_help}")
        self.hs_vm_config = self.config.HyperScale.VMConfig
        self.CVUPGRADEOS_LOG = "cvupgradeos.log"
        cache_node_obj = self.commcell.clients.get(self.cache_node)
        log_directory = cache_node_obj.log_directory
        self.cache_node_install_directory = cache_node_obj.install_directory
        self.CVUPGRADEOS_LOG_PATH = f"{log_directory}/{self.CVUPGRADEOS_LOG}"
        # Set cumulative_hvcmd to True when verifying pre existing logs
        self.cumulative_hvcmd = False
        if self.cumulative_hvcmd:
            self.HVCMD_LOG_PATH = f"{log_directory}/hsupgradedbg/{self.HVCMD_LOG}"
        else:
            self.HVCMD_LOG_PATH = f"/tmp/{self.HVCMD_LOG}"
        self.YUM_OUT_LOG = "yum.out.log"
        self.YUM_OUT_LOG_PATH = f"{log_directory}/hsupgradedbg/{self.YUM_OUT_LOG}"

        self.key = self.ma_machines[self.ma1].key % "MediaAgent"
        self.workflow_name = self.tcinputs.get('workflow_name')
        self.workflow = WorkflowHelper(self, wf_name=self.workflow_name)

    def setup_vm_automation(self, vm_name):
        """Initializes the VM automation helpers"""
        server_type = VmIo.SERVER_TYPE_ESX
        server_host_name = self.hs_vm_config.ServerHostName
        username = self.hs_vm_config.Username
        password = self.hs_vm_config.Password
        vm_config = {
            'server_type': server_type,
            'server_host_name': server_host_name,
            'username': username,
            'password': password
        }
        self.esx: EsxManagement = VmOperations.create_vmoperations_object(vm_config)
        atexit.register(connect.Disconnect, self.esx.si)
        self.vm_io = VmIo(
            vm_name, server_type, server_host_name, username, password)

    def cleanup(self):
        """Cleans up the test case resources and directories"""

        policy_exists = self.commcell.storage_policies.has_policy(self.storage_policy_name)
        if policy_exists:
            policy_obj = self.commcell.storage_policies.get(self.storage_policy_name)
            # TODO: kill all jobs related to the subclient before doing this
            policy_obj.reassociate_all_subclients()
            self.log.info(f"Reassociated all {self.storage_policy_name} subclients")
        if self.backupset.subclients.has_subclient(self.subclient_name):
            self.backupset.subclients.delete(self.subclient_name)
            self.log.info(f"{self.subclient_name} deleted")
        self.hyperscale_helper.clean_up_storage_pool(self.storage_pool_name, self.sql_login, self.sql_sq_password)
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
        if self.successful:
            self.log.info(f"Test case successful. Cleaning up the entities created (except {self.storage_pool_name})")
            self.cleanup()
        else:
            self.log.warning("Not cleaning up as the run was not successful")
            self.status = constants.FAILED

    def get_sp_version_from_cs(self, client_name):
        """Returns SP version as indicated by CS from client name.
            Args:
                client_name     (str)  --  client name
            Returns:
                sp_version   - the SP version
        """
        client = self.commcell.clients.get(client_name)
        return client.service_pack

    def parse_which_commit_output(self, output):
        """Parses the ./whichCommit.sh output
            Args:
                output   (str)   --  The output from ./whichCommit.sh script
            Returns:
                result  (dict)  --  The parsed output. {CommitId: '', Branch: ''}
        """
        output = output.replace("\n ", "")
        regex = r'(CommitId|Branch): (.*)'
        matches = re.findall(regex, output)
        if not matches:
            return None
        parsed = {tag: value for tag, value in matches}
        return parsed

    def get_which_commit_output(self):
        """Retrieves the ./whichCommit.sh output for all MAs
        output: {ma1: value1, ma2: value2, ma3: value3}
            Args:
                output   (str)   --  The output from ./whichCommit.sh script
            Returns:
                result  (dict)  --  The parsed output. {CommitId: output, Branch: output}
        """
        command = "/usr/local/hedvig/scripts/whichCommit.sh"
        identical, result = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, command)
        if not identical:
            self.log.warning(f"./whichCommit.sh outputs differ. Proceeding")
        else:
            self.log.info("./whichCommit.sh outputs match")
        which_commit_outputs = {}
        for ma_name, output in result.items():
            parsed = self.parse_which_commit_output(output)
            if not parsed:
                self.log.error(f"./whichCommit.sh parse failed for {ma_name}")
                return None
            for key in sorted(parsed.keys()):
                value = which_commit_outputs.get(key, {})
                value[ma_name] = parsed[key]
                which_commit_outputs[key] = value
        return which_commit_outputs

    def verify_output_changed_post_upgrade(self, pre_output, post_output):
        """Verifies that the output is different post upgrade
        output: {ma1: value1, ma2: value2, ma3: value3}
            Args:
                pre_output  (output)    --  The output before upgrade
                post_output (output)    --  The output after upgrade
            Returns:
                result      (bool)      --  If the output is different or not
        """
        for ma in self.mas:
            pre = pre_output[ma]
            post = post_output[ma]
            if pre == post:
                self.log.error(f"{ma} has same {pre} post upgrade")
                return False
            self.log.info(f"{ma} output changed from {pre} to {post}")
        return True

    def parse_cluster_details(self):
        """Parses the cluster details output
            Returns:
                result (bool)   -- Whether parsed or not
        """
        machine = self.ma_machines[self.mas[0]]
        cluster_name = self.hyperscale_helper.get_hedvig_cluster_name(machine)
        if not cluster_name:
            self.log.error("Couldn't get the cluster name")
            return False
        path = '/opt/hedvig/bin/hv_deploy'
        command = f'su -l -c "env HV_PUBKEY=1 {path} --check_cluster_status_detail --cluster_name {cluster_name}" admin'
        identical, result = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, command)
        if not result:
            self.log.error(f"Unable to get cluster details")
            return False
        self.log.info("Cluster details were parsed")
        return True

    def check_identical_values(self, ma_list, operation):
        """Runs same operation across multiple MAs for output equality.
            Args:
                ma_list         (list)      --  list of MA names
                operation       (method)    --  the operation to run
                    should accept ma_name and return output
            Returns:
                (bool, result) - bool indicates if outputs are equal
                    result is {ma_name: command_output}, where
                    ma_name belongs to ma_list and
                    command_output is output of command for ma_name
        """
        outputs = set()
        result = {}
        identical = True
        for ma in ma_list:
            output = operation(ma)
            outputs.add(output)
            result[ma] = output
        if len(outputs) > 1:
            identical = False
        return identical, result

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
        result = self.mmhelper_obj.create_uncompressable_data(self.client_name, path, content_gb)
        if not result:
            return False
        return True

    def cleanup_test_data(self):
        """Clears the test data directory
        """
        path = self.test_case_path
        if self.client_machine.check_directory_exists(path):
            self.client_machine.remove_directory(path)
            self.log.info(f"Cleared {path} on {self.client_name}")
        else:
            self.log.info(f"Already cleared {path} on {self.client_name}")

    def run(self):
        """ run function of this test case"""
        try:

            # Cleanup previous runs' entities
            self.log.info("Running cleanup before run")
            self.cleanup()
            # 1. Power down the nodes
            self.log.info("Powering down the nodes")
            for ma in self.mas:
                result = self.esx.vm_power_control_with_retry_attempts(ma, 'off')
                if not result:
                    reason = f"Couldn't power off {ma}"
                    return self.fail_test_case(reason)
            self.log.info(f"All nodes {self.mas} have been powered down")

            # 2. Disable CD-ROMs, so that it boots from hard drive
            self.log.info("Disabling CDROM for all nodes")
            for ma in self.mas:
                self.esx.vm_set_cd_rom_enabled(ma, False)
            self.log.info(f"All nodes {self.mas} have their CD-ROMs disabled")

            # 3a. Power on the machines
            self.log.info("Powering up the nodes")
            for ma in self.mas:
                result = self.esx.vm_power_control_with_retry_attempts(ma, 'on')
                if not result:
                    reason = f"Couldn't power on {ma}"
                    return self.fail_test_case(reason)
            self.log.info(f"All nodes {self.mas} have been powered on. Waiting for boot to complete")

            # 3b. Wait for power on to complete
            for ma in self.mas:
                result = self.hyperscale_helper.wait_for_ping_result_to_be(0, ma)
                if not result:
                    reason = f"Failure while waiting for power on to complete for {ma}"
                    return self.fail_test_case(reason)
                self.log.info(f"{ma} is back online")
            time.sleep(10)
            self.log.info(f"Boot is completed on all the nodes")

            remote_cache_client = self.commcell.clients.get(self.cache_node)
            self.log.info("Adding additional keys for add node")
            remote_cache_client.add_additional_setting(category="HyperScale", key_name="nDownload20repo",
                                                       data_type="INTEGER", value='1')
            remote_cache_client.add_additional_setting(category="MediaAgent", key_name="nAddNodeManualNetworkConfig",
                                                       data_type="INTEGER", value='1')
            self.log.info("Added additional settings on RC, nAddNodeManualNetworkConfig and nDownload20repo")
            self.log.info("Increasing WF timeout")
            self.commcell.add_additional_setting(category="Database", key_name="nWFRESPONSETIMEOUT",
                                                 data_type="INTEGER", value="300")

            self.log.info("Setting up VM automation again to avoid timeouts")
            self.setup_vm_automation(self.add_node_name)
            # 15. Login via console
            self.log.info(
                f"Logging in to the add node to add reg key nAddNodeManualNetworkConfig {self.add_node_name} via console")
            self.vm_io.send_keys(['MOD_LCTRL', 'MOD_LALT', 'F2'])
            time.sleep(10)
            self.vm_io.send_command(self.add_node_username)
            self.vm_io.send_command(self.add_node_password)
            # sleeping as it takes some time to login
            time.sleep(2)
            self.vm_io.send_command(f'echo "nAddNodeManualNetworkConfig 1" >> {self.key}')
            time.sleep(5)

            # 4. Check if remote cache is present on cache_node
            self.log.info(f"Checking if remote cache is present on {self.cache_node}")
            result = self.hyperscale_helper.is_remote_cache_present(self.cache_node)
            if not result:
                reason = f"Cache node {self.cache_node} doesn't have the remote cache setup."
                return self.fail_test_case(reason)
            self.log.info(f"Cache node {self.cache_node} has the remote cache")

            # 5. Sync the cache so that nodes can be updated to latest SP
            self.log.info("syncing the cache so that nodes can be updated to latest SP")
            sync_job = self.commcell.sync_remote_cache([self.cache_node])
            self.log.info(f"Starting Remote Cache Sync job [{sync_job.job_id}]")
            if not sync_job.wait_for_completion():
                reason = f"Remote Cache Sync Job ({sync_job.job_id}) Failed"
                return self.fail_test_case(reason)
            self.log.info(f"Remote Cache Sync Job ({sync_job.job_id}) Succeeded")

            # 6. update all clients to latest
            self.log.info("Updating all MAs to latest")
            for ma in self.mas:
                client = self.commcell.clients.get(ma)
                job_obj = client.push_servicepack_and_hotfix()
                self.log.info(f"Started update job ({job_obj.job_id}) for {ma}")
                if not job_obj.wait_for_completion():
                    reason = f"{ma} update job {job_obj.job_id} failed to complete"
                    return self.fail_test_case(reason)
            self.log.info(f"All nodes {self.mas} updated to the latest SP")

            # 7. Check SP Version
            self.log.info("Checking SP version for all nodes")
            result, outputs = self.check_identical_values(self.mas, self.get_sp_version_from_cs)
            if not result:
                self.log.error(f"Nodes have version mismatch {outputs}. Proceeding")
            self.log.info(f"All nodes have same version {outputs[self.mas[0]]}")

            # 8. Create a storage pool, if not already there
            if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.log.info(f"Creating storage pool {self.storage_pool_name}")
                status, response = self.hyperscale_helper.create_storage_pool(
                    self.storage_pool_name, *self.mas)
                self.log.info(
                    f"Created storage pool with status: {status} and response: {response}")
                if not status:
                    reason = "Storage pool creation failed"
                    return self.fail_test_case(reason)
            else:
                self.log.info(f"Skipping storage pool creation as {self.storage_pool_name} already exists")

            # 9. populate the remote cache with Unix software
            self.log.info(f"Populating remote cache {self.cache_node} with Unix RPMs")
            result, message = self.hyperscale_helper.populate_remote_cache(self.cache_node)
            if not result:
                reason = message
                return self.fail_test_case(reason)
            self.log.info(f"Successfully populated remote cache {self.cache_node} with Unix RPMs")

            # Part 1: Hedvig upgrade
            # 10a. Backup: create test data
            self.log.info("Proceeding to take backup before Hedvig Add node")
            result = self.create_test_data(self.content_path, self.content_gb)
            if not result:
                reason = "Error while creating test data"
                return self.fail_test_case(reason)
            self.log.info("Created test data")
            # 10b. Backup: take full backup
            self.policy = self.hyperscale_helper.get_or_create_policy(self.storage_pool_name, self.other_mas[0],
                                                                      self.storage_policy_name)
            self.backupset = self.mmhelper_obj.configure_backupset()
            self.subclient_obj = self.mmhelper_obj.configure_subclient(content_path=[self.content_path])
            job_obj = self.subclient_obj.backup("FULL")
            self.log.info(f"Starting backup job [{job_obj.job_id}]")
            if not job_obj.wait_for_completion():
                reason = f"Backup job [{job_obj.job_id}] has failed"
                return self.fail_test_case(reason)
            self.log.info(f"Backup succeeded. Job status {job_obj.status}")

            # 11. Mark MAs in maintenance mode
            self.log.info("Marking media agents in maintenance mode")
            for ma in self.mas:
                ma_obj = self.commcell.media_agents.get(ma)
                ma_obj.mark_for_maintenance(True)
            self.log.info(f"Marked MAs in maintenance mode")

            # 12a. Save whichCommit output
            which_commit_output = self.get_which_commit_output()
            if not which_commit_output:
                reason = "Failed to get ./whichCommit.sh output"
                return self.fail_test_case(reason)
            self.log.info(f"Saved ./whichCommit.sh output")
            # 12b. Parse --check_cluster_status_detail output
            self.log.info("--check_cluster_status_detail")
            if not self.parse_cluster_details():
                reason = "Failed to parse check_cluster_status_detail"
                return self.fail_test_case(reason)
            self.log.info("Parsed check_cluster_status_detail output")
            # 12c. Verify nfsstat -m output
            self.log.info("Verifying nfsstat -m output")
            if not self.hyperscale_helper.verify_nfsstat_output(self.mas, self.ma_machines):
                reason = "Failed to verify nfsstat"
                return self.fail_test_case(reason)
            self.log.info("Verified nfsstat -m output")
            # 12c. Verify df -kht nfs4 output
            self.log.info("Verifying df -kht nfs4 output")
            if not self.hyperscale_helper.verify_df_kht_nfs4_output(self.mas, self.ma_machines):
                reason = "Failed to verify df -kht nfs4"
                return self.fail_test_case(reason)
            self.log.info("Verified df -kht nfs4 output")
            # 12d. Verify whether all hedvig services are up
            self.log.info("Verifying if hedvig services are up")
            result = self.hyperscale_helper.verify_hedvig_services_are_up(self.mas, self.ma_machines)
            if not result:
                reason = "Couldn't verify if hedvig services are up"
                return self.fail_test_case(reason)
            self.log.info("Successfully verified hedvig services are up and running")

            # 12e. Save hedvig-common RPM version
            identical, result = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines,
                                                                              "rpm -qa | grep hedvig-common")
            rpm_hedvig_common = result

            # 12f. Save hedvig-cluster RPM version
            identical, result = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines,
                                                                              "rpm -qa | grep hedvig-cluster")
            rpm_hedvig_cluster = result

            self.log.info(f"Getting number of lines in {self.CVUPGRADEOS_LOG}")
            lines_before_os_upgrade = self.hyperscale_helper.get_lines_in_log_file(self.cache_machine,
                                                                                   self.CVUPGRADEOS_LOG_PATH)
            self.log.info(f"Number of lines in {self.CVUPGRADEOS_LOG}: {lines_before_os_upgrade}")

            # 13b. Get no. of lines in hvcmd.log
            self.log.info(f"Getting number of lines in {self.HVCMD_LOG}")
            if self.cumulative_hvcmd:
                lines_before_hedvig_upgrade = self.hyperscale_helper.get_lines_in_log_file(self.cache_machine,
                                                                                           self.HVCMD_LOG_PATH)
            else:
                lines_before_hedvig_upgrade = 1
            self.log.info(f"Number of lines in {self.HVCMD_LOG}: {lines_before_hedvig_upgrade}")

            # 14. setup_vm_automation again as the session times out after 900 seconds
            self.log.info("Setting up VM automation again to avoid timeouts")
            self.setup_vm_automation(self.cache_node)
            # 15. Login via console
            self.log.info(f"Logging in to the remote cache node {self.cache_node} via console")
            self.vm_io.send_keys(['MOD_LCTRL', 'MOD_LALT', 'F2'])
            time.sleep(10)
            self.vm_io.send_command(self.cache_node_username)
            self.vm_io.send_command(self.cache_node_password)
            # sleeping as it takes some time to login
            time.sleep(2)
            # 16. Run upgrade script
            self.log.info("Running the upgrade script")
            self.vm_io.send_command(f"cd {self.cache_node_install_directory}/MediaAgent")
            self.vm_io.send_command("./cvupgradeos.py -upgrade_hedvig_only")

            is_hedvig_already_upgraded = True
            result, line = self.hyperscale_helper.search_log_line(self.cache_machine, self.CVUPGRADEOS_LOG_PATH,
                                                                  "It looks CDS rpms are up to date on all nodes ...",
                                                                  from_line=lines_before_os_upgrade,
                                                                  tries=7, interval=120)
            if not result:
                is_hedvig_already_upgraded = False

            if not is_hedvig_already_upgraded:
                result, line = self.hyperscale_helper.search_log_line(self.cache_machine, self.CVUPGRADEOS_LOG_PATH,
                                                                      "Successfully upgraded hedvig rpms ...",
                                                                      from_line=lines_before_os_upgrade,
                                                                      tries=15, interval=180)
            if not result:
                reason = f"Some failure in hedvig RPM upgrade please check logs"
                return self.fail_test_case(reason)

            # 21a. Compare whichCommit output
            self.log.info(f"Compare whichCommit.sh output post upgrade")
            output = self.get_which_commit_output()
            if not output:
                reason = "Failed to get whichCommit.sh output post upgrade"
                return self.fail_test_case(reason)
            for key in sorted(output.keys()):
                self.log.info(f"Comparing output for {key}")
                result = self.verify_output_changed_post_upgrade(which_commit_output[key], output[key])
                if not result and not is_hedvig_already_upgraded:
                    reason = f"Failed to verify that {key} was changed post upgrade"
                    return self.fail_test_case(reason)
                self.log.info(f"Successfully verified that {key} was changed post upgrade")

            # 21b. Compare hedvig-common RPM version
            self.log.info("Compare hedvig-common RPM version post upgrade")
            identical, result = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines,
                                                                              "rpm -qa | grep hedvig-common")
            result = self.verify_output_changed_post_upgrade(rpm_hedvig_common, result)
            if not result and not is_hedvig_already_upgraded:
                reason = f"Failed to verify that hedvig-common RPM was changed post upgrade"
                return self.fail_test_case(reason)
            self.log.info(f"Successfully verified that hedvig-common RPM was changed post upgrade")

            # 21c. Compare hedvig-cluster RPM version
            self.log.info("Compare hedvig-cluster RPM version post upgrade")
            identical, result = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines,
                                                                              "rpm -qa | grep hedvig-cluster")
            result = self.verify_output_changed_post_upgrade(rpm_hedvig_cluster, result)
            if not result and not is_hedvig_already_upgraded:
                reason = f"Failed to verify that hedvig-cluster RPM was changed post upgrade"
                return self.fail_test_case(reason)
            self.log.info(f"Successfully verified that hedvig-cluster RPM was changed post upgrade")

            # 21d. Check if commvault service and processes are up
            self.log.info("Verify if commvault service and processes are up post hedvig upgrade")
            result = self.hyperscale_helper.verify_commvault_service_and_processes_are_up(self.mas, self.ma_machines)
            if not result:
                reason = "Failed to verify if commvault service and processes are up post hedvig upgrade"
                return self.fail_test_case(reason)
            self.log.info(f"Successfully verified commvault service and processes are up post hedvig upgrade")

            # 22. Mark MAs out of maintenance mode
            self.log.info("Marking media agents out of maintenance mode")
            for ma in self.mas:
                ma_obj = self.commcell.media_agents.get(ma)
                ma_obj.mark_for_maintenance(False)
            self.log.info(f"Marked MAs out of maintenance mode")

            self.log.info("Setting up VM automation again to avoid timeouts")
            self.setup_vm_automation(self.cache_node)
            # 15. Login via console
            self.log.info(f"Logging in to the remote cache node {self.cache_node} via console")
            self.vm_io.send_keys(['MOD_LCTRL', 'MOD_LALT', 'F2'])
            time.sleep(10)
            self.vm_io.send_command(self.cache_node_username)
            self.vm_io.send_command(self.cache_node_password)
            # sleeping as it takes some time to login
            time.sleep(2)
            self.log.info("Setting MEM_set_profile to small_demo")
            self.vm_io.send_command("su - admin")
            time.sleep(5)
            self.vm_io.send_command("hv_deploy")
            time.sleep(10)
            cluster_name = self.hyperscale_helper.get_hedvig_cluster_name(self.cache_machine)
            self.vm_io.send_command(f"login_to_cluster {cluster_name}")
            time.sleep(20)
            self.vm_io.send_command(f"{self.cache_node_password}")
            time.sleep(120)
            self.vm_io.send_command("set_mem_profile small_demo")
            time.sleep(5)
            self.vm_io.send_command("save_settings")
            time.sleep(60)
            self.vm_io.send_command("exit")
            time.sleep(10)
            self.vm_io.send_command("exit")
            time.sleep(10)

            # TODO: Run WF
            try:
                flag = False
                self.browser = BrowserFactory().create_browser_object()
                self.browser.open()
                self.webconsole = WebConsole(
                    self.browser,
                    self.commcell.webconsole_hostname
                )
                self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
                self.webconsole.login(
                    self.inputJSONnode['commcell']['commcellUsername'],
                    self.inputJSONnode['commcell']['commcellPassword']
                )

                self.webconsole.wait_till_load_complete()
                self.webconsole.goto_forms()
                forms = Forms(self.admin_console)
                forms.open_workflow(self.workflow_name)
                if forms.is_form_open(self.workflow_name):
                    forms.submit()
                    forms._adminconsole.wait_for_completion()
                    add_node_status = False
                    job = self.workflow.workflow_job_status(self.workflow_name, wait_for_job=False)
                    forms._adminconsole.wait_for_completion()
                    forms.is_form_open('Storage Pool')
                    pool_list = forms.get_radiobox_value('Storage Pool')
                    self.log.info(pool_list)
                    if self.storage_pool_name not in pool_list:
                        reason = f"Storage pool {self.storage_pool_name} not present"
                        return self.fail_test_case(reason)
                    forms.select_radio_value('Storage Pool', self.storage_pool_name)
                    forms.click_action_button("Continue")
                    forms._adminconsole.wait_for_completion()
                    forms.click_action_button("Continue")
                    forms._adminconsole.wait_for_completion()
                    forms.is_form_open('Select Nodes')
                    node_list = forms.get_checkbox_value('Nodes')
                    if self.serial_no not in node_list:
                        reason = f"Serial node {self.serial_no} not present"
                        return self.fail_test_case(reason)
                    forms.select_checkbox_value('Nodes', self.serial_no)
                    forms.click_action_button("Continue")
                    forms._adminconsole.wait_for_completion()
                    forms.click_action_button("Continue")
                    forms._adminconsole.wait_for_completion()
                    forms.is_form_open('Cluster Credentials')
                    forms.set_textbox_value("Root Password", self.add_node_password)
                    forms.click_action_button("Continue")
                    forms._adminconsole.wait_for_completion()
                    forms.is_form_open(f"Node Configuration: {self.serial_no}")
                    forms.set_textbox_value('Data Protection IP', self.dp_ip)
                    forms.set_textbox_value('Storage Pool IP', self.sp_ip)
                    forms.click_action_button("Continue")
                    forms._adminconsole.wait_for_completion()
                    forms.click_action_button("Continue")
                    forms._adminconsole.wait_for_completion()
                    self.workflow.workflow_job_status(self.workflow_name)
                    add_node_status = True

                else:
                    raise Exception("Workflow Input Window isnt loaded")
            except Exception as excp:
                self.workflow.test.fail(excp)
                if add_node_status and 'validation failed' not in str(excp):
                    job_manager = JobManager(job, self._commcell)
                    job_manager.modify_job('kill')

            finally:
                WebConsole.logout_silently(self.webconsole)
                Browser.close_silently(self.browser)

            # 22. Mark MAs out of maintenance mode
            self.log.info("Marking media agents out of maintenance mode")
            for ma in self.mas:
                ma_obj = self.commcell.media_agents.get(ma)
                ma_obj.mark_for_maintenance(False)
            self.log.info(f"Marked MAs out of maintenance mode")

            # 23. Perform restore here
            self.log.info("Performing Restore")
            job_obj = self.subclient_obj.restore_out_of_place(self.client, self.restore_data_path, [self.content_path])
            if not job_obj.wait_for_completion():
                reason = f"Restore job {job_obj.job_id} has failed {job_obj.pending_reason}"
                return self.fail_test_case(reason)
            self.log.info("Restore job succeeded. Job status %s", job_obj.status)

            # 24. Now verify the restored data
            self.log.info("Verifying the restored data")
            self.hyperscale_helper.verify_restored_data(self.client_machine, self.content_path, self.restore_path)
            self.log.info(f"Successfully upgraded the Hedvig RPMs")

        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
