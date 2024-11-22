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

    check_rpms_installed()          -- Checks whether rpms installed or not

    run()                           --  run function of this test case

Sample input json
"64166": {
            "ControlNodes": [
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
            },
            "StoragePoolName": "name",
            "workflow_name": "workflow_name",
            "SqlLogin": login, (OPTIONAL)
            "SqlPassword": password (OPTIONAL)
            }
"""
# The following keys must be present under HyperScale key
# in config.json file
vmconfig_help = """
"HyperScale": {
    ...,
    "Credentials": {
        "User": "default username for MA"
        "Password": "default password for MA"
    }
    "VMConfig": {
        "ServerHostName": "Host name of the VM server",
        "Username": "Login user for the VM server",
        "Password": "password for the user"
    }
}
"""

from math import ceil
from pyVim import connect
from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.output_formatter import UnixOutput
from AutomationUtils.unix_machine import UnixMachine
from AutomationUtils.vmoperations import VmOperations
from HyperScale.HyperScaleUtils.esxManagement import EsxManagement
from HyperScale.HyperScaleUtils.rehydrator import Rehydrator
from HyperScale.HyperScaleUtils.vm_io import VmIo
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from MediaAgents.MAUtils.hyperscale_setup import HyperscaleSetup
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.options_selector import OptionsSelector
import time
import re
import atexit
import paramiko


class TestCase(CVTestCase):
    """Hyperscale test class for HSX Add node"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.CVMANAGER_LOG_PATH = None
        self.CVMANAGER_LOG = None
        self.available_nodes = None
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
        self.mas = []
        self.storage_pool_name = ""
        self.sql_sq_password = ""
        self.sql_login = ""
        self.storage_policy_name = ""
        self.policy = ""
        self.hyperscale_helper = None
        self.add_node_name = ""
        self.cache_node_username = ""
        self.cache_node_password = ""
        self.ma_machines = ""
        self.cache_machine = ""
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
        self.vm_io = ""
        self.esx = ""
        self.tcinputs = {
            "ControlNodes": [
                "MA1",
                "MA2",
                "MA3"
            ],
            "AddNode": {
                "names": [],
                "username": "",
                "password": ""
            },
            "CacheNode": {
                "name": "",
                "vmName": "",
                "username": "",
                "password": ""
            },
            "StoragePoolName": "",
            "SqlLogin": "",
            "SqlPassword": "",
        }
        self.successful = False
        self.rpm_path = ""
        self.cvbackupadmin_password = None
        self.pool_size_before_add_node = 0

    def setup(self):
        """Initializes test case variables"""
        self.cs_hostname = self.inputJSONnode["commcell"]["webconsoleHostname"]
        self.username = self.inputJSONnode["commcell"]["commcellUsername"]
        self.password = self.inputJSONnode["commcell"]["commcellPassword"]
        self.client_name = self.commcell.commserv_name
        self.client_machine = Machine(self.client_name, self.commcell)

        # Add node setup
        self.add_nodes = self.tcinputs["AddNode"]["names"]
        self.add_node_vm_names = self.tcinputs["AddNode"].get("vmnames", self.add_nodes)
        self.add_node_username = self.tcinputs["AddNode"]["username"]
        self.add_node_password = self.tcinputs["AddNode"]["password"]

        # Cache node setup
        self.cache_node = self.tcinputs["CacheNode"]["name"]
        self.cache_node_username = self.tcinputs["CacheNode"]["username"]
        self.cache_node_password = self.tcinputs["CacheNode"]["password"]
        self.cache_node_vm_name = self.tcinputs["CacheNode"].get("vmName", self.cache_node)
        self.rpm_path = "/ws/ddb/cvmanager/cvfs_rpm"

        # MA setup
        self.control_nodes = self.tcinputs["ControlNodes"]
        self.ma_machines = {}
        self.mas = []
        for ma_name in self.control_nodes:
            if self.commcell.clients.has_client(ma_name):
                self.mas.append(ma_name)
                # username/password is necessary as MAs will be marked in maintenance mode
                self.log.info(f"Creating machine object for: {ma_name}")
                machine = UnixMachine(
                    ma_name,
                    username=self.cache_node_username,
                    password=self.cache_node_password,
                )
                self.ma_machines[ma_name] = machine

        self.available_nodes = self.mas + self.add_nodes
        self.cache_machine = self.ma_machines[self.cache_node]
        self.add_node_name = self.add_nodes[0]

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
        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

        # # Subclient & Storage setup
        self.storage_pool_name = self.hyperscale_helper.get_storage_pool_from_media_agents(
            self.mas
        )
        self.client = self.commcell.clients.get(self.client_name)
        self.agent = self.client.agents.get("FILE SYSTEM")
        ma_short_name = self.mas[0].split(".", 1)[0]
        prefix = f"{self.id}_{ma_short_name}_"
        self.backupset_name = f"{prefix}backupset"
        self.subclient_name = f"{prefix}subclient;'"
        self.storage_policy_name = f"{prefix}policy"
        self.mmhelper_obj = MMHelper(self)
        self.options_selector = OptionsSelector(self.commcell)
        self.content_gb = 1
        self.drive = self.options_selector.get_drive(
            self.client_machine, 2 * self.content_gb * 1024
        )

        # Backup and restore paths
        self.test_case_path = self.client_machine.join_path(self.drive, "Automation", str(self.id))
        self.test_data_path = self.client_machine.join_path(self.test_case_path, "Testdata")
        self.content_path = self.get_client_content_folder(
            "1", self.content_gb, self.test_data_path
        )
        self.restore_data_path = self.client_machine.join_path(self.test_case_path, "Restore")
        self.restore_path = self.get_client_content_folder(
            "1", self.content_gb, self.restore_data_path
        )

        # VM setup
        if not hasattr(self.config.HyperScale, "VMConfig") or not hasattr(
            self.config.HyperScale, "Credentials"
        ):
            raise Exception(
                f"Please add VMConfig and Credentials to HyperScale in config.json file as {vmconfig_help}"
            )

        self.hs_vm_config = self.config.HyperScale.VMConfig
        self.setup_vm_automation(self.cache_node_vm_name)

        self.CVUPGRADEOS_LOG = "cvupgradeos.log"
        self.CVMANAGER_LOG = "cvmanager.log"
        cache_node_obj = self.commcell.clients.get(self.cache_node)
        log_directory = cache_node_obj.log_directory
        self.cache_node_install_directory = cache_node_obj.install_directory
        self.CVUPGRADEOS_LOG_PATH = f"{log_directory}/{self.CVUPGRADEOS_LOG}"
        self.CVMANAGER_LOG_PATH = f"{log_directory}/{self.CVMANAGER_LOG}"
        self.check_diff_post_upgrade = False

        # setting cvbackupadmin password based on hsx version
        self.hsx3_or_above = self.hyperscale_helper.is_hsx_node_version_equal_or_above(
            self.ma_machines[self.cache_node], 3
        )
        if self.hsx3_or_above:
            self.cvbackupadmin_password = self.cache_node_password
            
        self.rehydrator = Rehydrator(self.id)
        self.lines_before_os_upgrade = self.rehydrator.bucket("lines_before_os_upgrade")
        self.lines_before_add_node = self.rehydrator.bucket("lines_before_add_node")
        self.pre_which_commit = self.rehydrator.bucket("pre_which_commit")
        self.pre_hedvig_common = self.rehydrator.bucket("pre_hedvig_common")
        self.pre_hedvig_cluster = self.rehydrator.bucket("pre_hedvig_cluster")

    def setup_vm_automation(self, vm_name):
        """Initializes the VM automation helpers
        Args :
        vm_name   (str)  --  vm name
        """
        server_type = VmIo.SERVER_TYPE_ESX
        server_host_name = self.hs_vm_config.ServerHostName
        username = self.hs_vm_config.Username
        password = self.hs_vm_config.Password
        vm_config = {
            "server_type": server_type,
            "server_host_name": server_host_name,
            "username": username,
            "password": password,
        }
        self.esx: EsxManagement = VmOperations.create_vmoperations_object(vm_config)
        atexit.register(connect.Disconnect, self.esx.si)
        self.vm_io = VmIo(vm_name, server_type, server_host_name, username, password, self.esx)

    def cleanup(self):
        """Cleans up the test case resources and directories"""
        self.rehydrator.cleanup()
        
        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.agent.backupsets.delete(self.backupset_name)

        policy_exists = self.commcell.storage_policies.has_policy(self.storage_policy_name)
        if policy_exists:
            policy_obj = self.commcell.storage_policies.get(self.storage_policy_name)
            # TODO: kill all jobs related to the subclient before doing this
            policy_obj.reassociate_all_subclients()
            self.log.info(f"Reassociated all {self.storage_policy_name} subclients")

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
            self.log.info(
                f"Test case successful. Cleaning up the entities created (except {self.storage_pool_name})"
            )
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
        regex = r"(CommitId|Branch): (.*)"
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
        identical, result = self.hyperscale_helper.check_identical_output(
            self.mas, self.ma_machines, command
        )
        if not identical:
            self.log.warning(f"./whichCommit.sh outputs differ")
            raise Exception(f"./whichCommit.sh outputs differ")
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
        if not self.check_diff_post_upgrade:
            self.log.info("Skipping output changed post upgrade")
            return True

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
        path = "/opt/hedvig/bin/hv_deploy"
        command = f'su -l -c "env HV_PUBKEY=1 {path} --check_cluster_status_detail --cluster_name {cluster_name}" admin'
        identical, result = self.hyperscale_helper.check_identical_output(
            self.mas, self.ma_machines, command
        )
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
        """Clears the test data directory"""
        path = self.test_case_path
        if self.client_machine.check_directory_exists(path):
            self.client_machine.remove_directory(path)
            self.log.info(f"Cleared {path} on {self.client_name}")
        else:
            self.log.info(f"Already cleared {path} on {self.client_name}")

    def check_rpms_installed(self, machine):
        """
        Checks whether list of rpms are installed or not

        Args :
        machine  (str)   -- machine name on which we want to check
        returns: None
        """
        status = True
        output = machine.execute_command("ls /ws/ddb/cvmanager/cds_rpm | egrep '.rpm$'")
        rpms = output.output.split("\n")[:-1]
        missing_rpms = []
        for rpm_file_name in rpms:
            rpm = rpm_file_name[:-4]
            command = f"rpm -qi {rpm}"
            self.log.info("Checking rpm %s", rpm)
            output = machine.execute_command(command)
            self.log.info(output.output)
            if not output.output:
                self.log.info("RPM %s not present", rpm)
                missing_rpms.append(rpm)
                status = False
        if not status:
            self.log.error(f"Missing rpms {missing_rpms}, please install them")
            return status
        self.log.info("Satisfies requirements ")
        return status

    def run(self):
        """run function of this test case"""
        try:
            # 1. Rebooting nodes - not needed here

            # 2. Check if remote cache is present on cache_node
            self.log.info(f"Checking if remote cache is present on {self.cache_node}")
            result = self.hyperscale_helper.is_remote_cache_present(self.cache_node)
            if not result:
                reason = f"Cache node {self.cache_node} doesn't have the remote cache setup."
                return self.fail_test_case(reason)
            self.log.info(f"Cache node {self.cache_node} has the remote cache")

            # 3. Sync the cache so that nodes can be updated to latest SP
            self.log.info("syncing the cache so that nodes can be updated to latest SP")
            sync_job = self.commcell.sync_remote_cache([self.cache_node])
            self.log.info(f"Starting Remote Cache Sync job [{sync_job.job_id}]")
            if not sync_job.wait_for_completion():
                reason = f"Remote Cache Sync Job ({sync_job.job_id}) Failed"
                return self.fail_test_case(reason)
            self.log.info(f"Remote Cache Sync Job ({sync_job.job_id}) Succeeded")

            # 4. update all clients to latest
            self.log.info("Updating all MAs to latest")
            for ma in self.mas:
                client = self.commcell.clients.get(ma)
                job_obj = client.push_servicepack_and_hotfix()
                self.log.info(f"Started update job ({job_obj.job_id}) for {ma}")
                if not job_obj.wait_for_completion():
                    reason = f"{ma} update job {job_obj.job_id} failed to complete"
                    return self.fail_test_case(reason)
            self.log.info(f"All nodes {self.mas} updated to the latest SP")

            # 5. Check SP Version
            self.log.info("Checking SP version for all nodes")
            result, outputs = self.check_identical_values(self.mas, self.get_sp_version_from_cs)
            if not result:
                self.log.error(f"Nodes have version mismatch {outputs}. Proceeding")
            self.log.info(f"All nodes have same version {outputs[self.mas[0]]}")

            # 6. populate the remote cache with Unix software
            self.log.info(f"Populating remote cache {self.cache_node} with Unix RPMs")
            result, message = self.hyperscale_helper.populate_remote_cache(self.cache_node)
            if not result:
                reason = message
                return self.fail_test_case(reason)
            self.log.info(f"Successfully populated remote cache {self.cache_node} with Unix RPMs")

            # Part 1: Hedvig upgrade
            # 16. Mark MAs out of maintenance mode
            self.log.info("Marking media agents out of maintenance mode")
            for ma in self.mas:
                ma_obj = self.commcell.media_agents.get(ma)
                ma_obj.mark_for_maintenance(False)
            self.log.info(f"Marked MAs out of maintenance mode")

            # 7a. Backup: create test data
            self.log.info("Proceeding to take backup before Hedvig Add node")
            result = self.create_test_data(self.content_path, self.content_gb)
            if not result:
                reason = "Error while creating test data"
                return self.fail_test_case(reason)
            self.log.info("Created test data")
            # 8b. Backup: take full backup
            self.policy = self.hyperscale_helper.get_or_create_policy(
                self.storage_pool_name, self.mas[0], self.storage_policy_name
            )
            self.backupset = self.mmhelper_obj.configure_backupset()
            self.subclient_obj = self.mmhelper_obj.configure_subclient(
                content_path=[self.content_path]
            )
            job_obj = self.subclient_obj.backup("FULL")
            self.log.info(f"Starting backup job [{job_obj.job_id}]")
            if not job_obj.wait_for_completion():
                reason = f"Backup job [{job_obj.job_id}] has failed"
                return self.fail_test_case(reason)
            self.log.info(f"Backup succeeded. Job status {job_obj.status}")

            # 9. Mark MAs in maintenance mode
            self.log.info("Marking media agents in maintenance mode")
            for ma in self.mas:
                ma_obj = self.commcell.media_agents.get(ma)
                ma_obj.mark_for_maintenance(True)
            self.log.info(f"Marked MAs in maintenance mode")

            # 10a. Save whichCommit output
            which_commit_output = self.get_which_commit_output()
            if not which_commit_output:
                reason = "Failed to get ./whichCommit.sh output"
                return self.fail_test_case(reason)
            self.pre_which_commit.set(which_commit_output)
            self.log.info(f"Saved ./whichCommit.sh output")

            # 10b. Save hedvig-common RPM version
            identical, result = self.hyperscale_helper.check_identical_output(
                self.mas, self.ma_machines, "rpm -qa | grep hedvig-common"
            )
            self.pre_hedvig_common.set(result)

            # 10c. Save hedvig-cluster RPM version
            identical, result = self.hyperscale_helper.check_identical_output(
                self.mas, self.ma_machines, "rpm -qa | grep hedvig-cluster"
            )
            self.pre_hedvig_cluster.set(result)

            self.log.info(f"Getting number of lines in {self.CVUPGRADEOS_LOG}")
            self.lines_before_os_upgrade.set(self.hyperscale_helper.get_lines_in_log_file(
                self.cache_machine, self.CVUPGRADEOS_LOG_PATH
            ))
            self.log.info(f"Number of lines in {self.CVUPGRADEOS_LOG}: {self.lines_before_os_upgrade.get()}")

            # 11. setup_vm_automation again as the session times out after 900 seconds
            self.log.info("Setting up VM automation again to avoid timeouts")
            self.setup_vm_automation(self.cache_node_vm_name)
            # 12. Login via console
            self.log.info(f"Logging in to the remote cache node {self.cache_node} via console")
            HyperscaleSetup.hsx_login(self.vm_io, self.cache_node_password)

            # 14. Run upgrade script
            self.log.info("Running the upgrade script")
            self.vm_io.send_command(f"cd {self.cache_node_install_directory}/MediaAgent")
            self.vm_io.send_command("./cvupgradeos.py -upgrade_hedvig_only")

            is_hedvig_already_upgraded = True
            logs = [
                "It looks CDS rpms are up to date on all nodes ...",
                "CVFS packages are up to date on all nodes...",
                "It appears download job was not run to get required RPMs for upgrade",
                "Directory [/ws/ddb/cvmanager/share/cvrepo] is not present, exiting.",
            ]
            log, result, line = self.hyperscale_helper.search_either_log_line(
                self.cache_machine,
                self.CVUPGRADEOS_LOG_PATH,
                logs,
                from_line=self.lines_before_os_upgrade.get(),
                tries=7,
                interval=120,
            )
            if not result:
                is_hedvig_already_upgraded = False
                mins_to_wait = 70
                interval_mins = 3
                result, line = self.hyperscale_helper.search_log_line(
                    self.cache_machine,
                    self.CVUPGRADEOS_LOG_PATH,
                    "Successfully upgraded CDS rpms ...",
                    from_line=self.lines_before_os_upgrade.get(),
                    interval=interval_mins * 60,
                    retry_duration=mins_to_wait * 60
                )
                if not result:
                    reason = f"CDS upgrade failed please check logs"
                    return self.fail_test_case(reason)

            # 15a. Compare whichCommit output
            self.log.info(f"Compare whichCommit.sh output post upgrade")
            output = self.get_which_commit_output()
            if not output:
                reason = "Failed to get whichCommit.sh output post upgrade"
                return self.fail_test_case(reason)
            which_commit_output = self.pre_which_commit.get()
            for key in sorted(output.keys()):
                self.log.info(f"Comparing output for {key}")
                result = self.verify_output_changed_post_upgrade(
                    which_commit_output[key], output[key]
                )
                if not result and not is_hedvig_already_upgraded:
                    reason = f"Failed to verify that {key} was changed post upgrade"
                    return self.fail_test_case(reason)
                self.log.info(f"Successfully verified that {key} was changed post upgrade")

            # 15b. Compare hedvig-common RPM version
            self.log.info("Compare hedvig-common RPM version post upgrade")
            identical, result = self.hyperscale_helper.check_identical_output(
                self.mas, self.ma_machines, "rpm -qa | grep hedvig-common"
            )
            rpm_hedvig_common = self.pre_hedvig_common.get()
            result = self.verify_output_changed_post_upgrade(rpm_hedvig_common, result)
            if not result and not is_hedvig_already_upgraded:
                reason = f"Failed to verify that hedvig-common RPM was changed post upgrade"
                return self.fail_test_case(reason)
            self.log.info(f"Successfully verified that hedvig-common RPM was changed post upgrade")

            # 15c. Compare hedvig-cluster RPM version
            self.log.info("Compare hedvig-cluster RPM version post upgrade")
            identical, result = self.hyperscale_helper.check_identical_output(
                self.mas, self.ma_machines, "rpm -qa | grep hedvig-cluster"
            )
            rpm_hedvig_cluster = self.pre_hedvig_cluster.get()
            result = self.verify_output_changed_post_upgrade(rpm_hedvig_cluster, result)
            if not result and not is_hedvig_already_upgraded:
                reason = f"Failed to verify that hedvig-cluster RPM was changed post upgrade"
                return self.fail_test_case(reason)
            self.log.info(
                f"Successfully verified that hedvig-cluster RPM was changed post upgrade"
            )

            # 15d. Check if commvault service and processes are up
            self.log.info("Verify if commvault service and processes are up post hedvig upgrade")
            result = self.hyperscale_helper.verify_commvault_service_and_processes_are_up(
                self.mas, self.ma_machines
            )
            if not result:
                reason = "Failed to verify if commvault service and processes are up post hedvig upgrade"
                return self.fail_test_case(reason)
            self.log.info(
                f"Successfully verified commvault service and processes are up post hedvig upgrade"
            )

            # 16. Mark MAs out of maintenance mode
            self.log.info("Marking media agents out of maintenance mode")
            for ma in self.mas:
                ma_obj = self.commcell.media_agents.get(ma)
                ma_obj.mark_for_maintenance(False)
            self.log.info(f"Marked MAs out of maintenance mode")

            # 17. size before add Node
            self.pool_size_before_add_node = self.hyperscale_helper.get_storage_pool_size(
                self.storage_pool_name
            )

            self.log.info(f"Getting number of lines in {self.CVMANAGER_LOG}")
            self.lines_before_add_node.set(self.hyperscale_helper.get_lines_in_log_file(
                self.cache_machine, self.CVUPGRADEOS_LOG_PATH
            ))
            self.log.info(f"Number of lines in {self.CVUPGRADEOS_LOG}: {self.lines_before_add_node.get()}")

            # 18. run cvmanager add_node task
            nodes_to_add = [self.add_node_name]
            result = self.hyperscale_helper.cvmanager_add_node_task(
                server_host_name=self.hs_vm_config.ServerHostName,
                server_user_name=self.hs_vm_config.Username,
                server_password=self.hs_vm_config.Password,
                cs_host=self.cs_hostname,
                cs_user=self.username,
                cs_password=self.password,
                existing_node_hostname=self.cache_node,
                existing_node_vm_name=self.cache_node_vm_name,
                existing_node_username=self.cache_node_username,
                existing_node_password=self.cache_node_password,
                nodes_to_add=nodes_to_add,
                cvbackupadmin_password=self.cvbackupadmin_password,
            )
            if not result:
                reason = "Add Node operation failed - cvmanager task failed"
                return self.fail_test_case(reason)

            result, line = self.hyperscale_helper.search_log_line(
                self.cache_machine,
                self.CVMANAGER_LOG_PATH,
                "[Main-> Add_Node_To_Cluster]: Has successfully completed all phases!",
                from_line=self.lines_before_add_node.get(),
                tries=3,
                interval=60,
            )
            if not result:
                reason = "Add Node operation failed - couldn't find the completion log line"
                return self.fail_test_case(reason)

            self.log.info(f"Add node operation completed successfully : {line}")
            
            self.commcell.media_agents.refresh()
            self.commcell.clients.refresh()

            if self.hsx3_or_above:
                result, reason = HyperscaleSetup.ensure_root_access(
                    commcell=self.commcell, node_hostnames=[self.add_node_name], node_root_password=self.cache_node_password)
                if not result:
                    return self.fail_test_case(reason)
                self.log.info(f"Successfully enabled root on the newly added node after add node")
                
            machine = Machine(
                self.add_node_name,
                username=self.cache_node_username,
                password=self.cache_node_password,
            )
            self.ma_machines[self.add_node_name] = machine

            if not self.hyperscale_helper.validate_passwordless_ssh(
                self.available_nodes, self.ma_machines
            ):
                reason = "Failed to validate passwordless SSH"
                return self.fail_test_case(reason)
            self.log.info("Successfully validated passwordless SSH")

            # 19. Verify whether all hedvig services are up
            self.log.info("Verifying if hedvig services are up on existing nodes")
            result = self.hyperscale_helper.verify_hedvig_services_are_up(
                self.mas, self.ma_machines
            )
            if not result:
                reason = "Couldn't verify if hedvig services are up on existing nodes"
                return self.fail_test_case(reason)
            self.log.info(
                "Successfully verified hedvig services are up and running on the existing nodes"
            )

            # 19. Verify whether required hedvig services are up on added node
            self.log.info("Verifying if hedvig services are up on added node")
            result = self.hyperscale_helper.verify_hedvig_services_are_up(
                self.add_nodes, self.ma_machines, services=["hedvighblock"]
            )
            if not result:
                reason = "Couldn't verify if hedvig services are up on added node"
                return self.fail_test_case(reason)
            self.log.info(
                "Successfully verified hedvig services are up and running on the added node"
            )
            
            list_of_nodes_storage_pool = self.hyperscale_helper.get_associated_mas(
                self.storage_pool_name
            )
            if list_of_nodes_storage_pool.sort() != self.available_nodes.sort():
                reason = f"Nodes are not listed in storage pool : {self.storage_pool_name}"
                return self.fail_test_case(reason)

            self.log.info("Nodes are listed properly in the storage pool")

            # 21. Save whichCommit output
            which_commit_output = self.get_which_commit_output()
            if not which_commit_output:
                reason = "Failed to get ./whichCommit.sh output"
                return self.fail_test_case(reason)
            self.log.info(f"whichCommit.sh output :{which_commit_output}")

            # 22. cds_rpm folder is consistent on newly added node
            command = f"ls {self.rpm_path}/*/*.rpm"
            identical, result = self.hyperscale_helper.check_identical_output(
                self.available_nodes, self.ma_machines, command
            )
            if not identical:
                reason = f"cds_rpm folder is inconsistent on {self.add_node_name}"
                return self.fail_test_case(reason)
            self.log.info(f"cds_rpm folder is consistent on {self.add_node_name} ")

            # 23. check whether all the rpms in cds_rpm folder are installed
            if self.add_node_name not in self.ma_machines:
                self.ma_machines[self.add_node_name] = UnixMachine(
                    self.add_node_name,
                    username=self.add_node_username,
                    password=self.cache_node_password,
                )
            if not self.check_rpms_installed(self.ma_machines[self.add_node_name]):
                reason = f"rpms are not installed on {self.add_node_name}"
                return self.fail_test_case(reason)

            self.log.info(f"rpms instaled correctly on {self.add_node_name}")

            # 24. verify hosts file on added node
            command = "cat /etc/hosts | sort"
            identical, result = self.hyperscale_helper.check_identical_output(
                self.mas, self.ma_machines, command
            )
            if not identical:
                reason = f"/etc/hosts file is inconsistent across the cluster nodes {self.mas}"
                return self.fail_test_case(reason)
            self.log.info(f"Hosts file is consistent across the cluster nodes {self.mas} ")

            # 25. check storagepool size is increased after add node
            pool_size_after_add_node = self.hyperscale_helper.get_storage_pool_size(
                self.storage_pool_name
            )
            if not pool_size_after_add_node > self.pool_size_before_add_node:
                raise Exception(
                    f"Pool Size of {self.storage_pool_name} did not change after Add Node"
                )

            # 26. Validating the DDB Expansion
            if not self.hyperscale_helper.validate_ddb_expansion(
                self.storage_pool_name, self.add_node_name
            ):
                reason = f"DDB is not expanded on {self.add_node_name}"
                return self.fail_test_case(reason)
            self.log.info(f"DDB expansion is successful on {self.add_node_name}")

            # 27. checking Live members and Unreachable members
            command = "/usr/local/hedvig/scripts/showmembers.exp | grep -v 'hedvigduro> connect -h' | tr -d '\\r'"
            identical, result = self.hyperscale_helper.check_identical_output(
                self.mas, self.ma_machines, command
            )
            if not identical:
                reason = f"Output for showmembers not identical across existing nodes"
                return self.fail_test_case(reason)
            self.log.info(f"Output for showmembers is identical across existing nodes")

            result = self.hyperscale_helper.verify_showmembers_output(
                result[self.mas[0]], len(self.mas) * 2 + len(self.add_nodes), 0
            )
            if not result:
                reason = f"Failed to verify showmembers output"
                return self.fail_test_case(reason)
            self.log.info(f"Successfully verified showmembers output")

            # Update the newly added node to latest CV
            ma = self.add_node_name
            client = self.commcell.clients.get(ma)
            job_obj = client.push_servicepack_and_hotfix()
            self.log.info(f"Started update job ({job_obj.job_id}) for {ma}")
            if not job_obj.wait_for_completion():
                reason = f"{ma} update job {job_obj.job_id} failed to complete"
                return self.fail_test_case(reason)
            self.log.info(f"{ma} updated to the latest SP")
            
            if self.hsx3_or_above:
                result, reason = HyperscaleSetup.ensure_root_access(
                    commcell=self.commcell, node_hostnames=[self.add_node_name], node_root_password=self.cache_node_password)
                if not result:
                    return self.fail_test_case(reason)
                self.log.info(f"Successfully enabled root on the newly added node after upgrade job")
                
                result = HyperscaleSetup.firewall_add_icmp_rule(
                    host=self.hs_vm_config.ServerHostName,
                    user=self.hs_vm_config.Username,
                    password=self.hs_vm_config.Password,
                    vm_names=self.add_node_vm_names,
                    vm_hostnames=self.add_nodes,
                    root_password=self.cache_node_password)
                if not result:
                    reason = f"Failed to add icmp rule"
                    return self.fail_test_case(reason)
                self.log.info("Successfully enabled ICMP traffic")

            # 28. Perform restore here
            self.policy = self.hyperscale_helper.get_or_create_policy(
                self.storage_pool_name, self.mas[0], self.storage_policy_name
            )
            self.backupset = self.mmhelper_obj.configure_backupset()
            self.subclient_obj = self.mmhelper_obj.configure_subclient(
                content_path=[self.content_path]
            )
            self.log.info("Performing Restore")
            job_obj = self.subclient_obj.restore_out_of_place(
                self.client, self.restore_data_path, [self.content_path]
            )
            if not job_obj.wait_for_completion():
                reason = f"Restore job {job_obj.job_id} has failed {job_obj.pending_reason}"
                return self.fail_test_case(reason)
            self.log.info("Restore job succeeded. Job status %s", job_obj.status)

            # 29. Now verify the restored data
            self.log.info("Verifying the restored data")
            self.hyperscale_helper.verify_restored_data(
                self.client_machine, self.content_path, self.restore_path
            )
            self.log.info(f"Successfully ran the test case")
            self.successful = True

        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(
                "Exception message while executing test case: %s", self.result_string
            )
