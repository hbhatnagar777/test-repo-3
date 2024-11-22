# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for DU Upgrade from CC
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  setup function of this test case

    cleanup()                       --  Cleans up the test case resources and directories

    tear_down()                     --  Tear down function of this test case
      
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
"70455": {
            "Nodes": [
              "MA1",
              "MA2",
              "MA3"
            ],
            "CacheNode": {
              "name": "name",
              "username": "username",
              "password": "password"
            },
            "StoragePoolName": "name",
            "SqlLogin": login,        
            "SqlPassword": password   
         }

"""

import time
import re
import atexit
from pyVim import connect
from typing import Dict
from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.unix_machine import UnixMachine
from AutomationUtils.vmoperations import VmOperations
from HyperScale.HyperScaleUtils.esxManagement import EsxManagement
from HyperScale.HyperScaleUtils.rehydrator import Rehydrator
from HyperScale.HyperScaleUtils.vm_io import VmIo
from Install.install_helper import InstallHelper
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from MediaAgents.MAUtils.hyperscale_setup import HyperscaleSetup
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.unix_ransomware_helper import UnixRansomwareHelper
from cvpysdk.job import Job

class TestCase(CVTestCase):
    """Hyperscale test class for DU Upgrade from CC"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for 2x: Disruptive CVFS only upgrade from CC"
        self.tcinputs = {
            "Nodes": [
              "MA1",
              "MA2",
              "MA3"
            ],
            "CacheNode": {
              "name": "name",
              "username": "username",
              "password": "password"
            },
            "StoragePoolName": "name",
            "SqlLogin": "login",        
            "SqlPassword": "password",
            # "ExpectedShaValuesCsvPath": None,
            # "UpgradeCVFS": None,
            # "UpgradeOS": None,
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
        self.cache_node_vm = self.tcinputs["CacheNode"].get("vmname", self.cache_node)
        if not self.commcell.clients.has_client(self.cache_node):
            raise Exception(f"{self.cache_node} MA doesn't exist")
        self.cache_node_sds = f'{self.cache_node}sds'
        self.cache_node_username = self.tcinputs["CacheNode"]["username"]
        self.cache_node_password = self.tcinputs["CacheNode"]["password"]

        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

        # MA setup
        self.mas = self.tcinputs["Nodes"]
        self.added_nodes = []
        self.refreshed_nodes = []
        self.rw_helpers: Dict[str, UnixRansomwareHelper] = {}
        HyperscaleSetup.ensure_root_access(commcell=self.commcell, node_hostnames=self.mas, node_root_password=self.cache_node_password)
        self.ma_machines = {}
        for ma_name in self.mas:
            if not self.commcell.clients.has_client(ma_name):
                raise Exception(f"{ma_name} MA doesn't exist")
            # username/password is necessary as MAs will be marked in maintenance mode
            self.log.info(f"Creating machine object for: {ma_name}")
            machine = Machine(ma_name, username=self.cache_node_username, password=self.cache_node_password)
            self.ma_machines[ma_name] = machine
            if self.hyperscale_helper.is_added_node(machine):
                self.added_nodes.append(ma_name)
                self.rw_helpers[ma_name] = UnixRansomwareHelper(machine, self.commcell, self.log)
            if self.hyperscale_helper.is_refreshed_node(machine):
                self.refreshed_nodes.append(ma_name)
                self.rw_helpers[ma_name] = UnixRansomwareHelper(machine, self.commcell, self.log)
        self.cache_machine: UnixMachine = self.ma_machines[self.cache_node]

        self.other_mas = [ma for ma in self.mas if ma != self.cache_node]

        self.hsx3_or_above = self.hyperscale_helper.is_hsx_node_version_equal_or_above(
            self.ma_machines[self.cache_node], 3
        )

        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)
        self.hsx3_or_above = self.hyperscale_helper.is_hsx_node_version_equal_or_above(
            self.ma_machines[self.cache_node], 3
        )

        # CSDB
        self.config = get_config()
        tcinputs_sql_login = self.tcinputs.get('SqlLogin')
        tcinputs_sql_password = self.tcinputs.get('SqlPassword')

        if tcinputs_sql_login is None:
            # go for default credentials
            if not hasattr(self.config.SQL, 'Username'):
                raise Exception(f"Please add default 'Username' to SQL in config.json file OR provide SqlLogin in TC inputs")
            self.sql_login = self.config.SQL.Username
            if not hasattr(self.config.SQL, 'Password'):
                raise Exception(f"Please add default 'Password' to SQL in config.json")
            self.sql_sq_password = self.config.SQL.Password
        else:
            # received a sql username from user
            if tcinputs_sql_password is None:
                raise Exception(f"Please provide SqlPassword in TC inputs or remove SqlLogin to fetch credentials from config.json")
            self.sql_login = tcinputs_sql_login
            self.sql_sq_password = tcinputs_sql_password

        # Subclient & Storage setup
        # self.storage_pool_name = f"{self.id}StoragePool"
        self.storage_pool_name = self.tcinputs['StoragePoolName']
        self.client = self.commcell.clients.get(self.client_name)
        self.agent = self.client.agents.get("FILE SYSTEM")
        self.backupset_name = "defaultBackupSet"
        self.backupset = self.agent.backupsets.get(self.backupset_name)
        self.subclient_name = f"{self.id}_subclient"
        self.storage_policy_name = f"{self.id}_{self.mas[0].split('.')[0]}_policy"
        self.mmhelper_obj = MMHelper(self)
        self.options_selector = OptionsSelector(self.commcell)
        self.content_gb = 1
        self.drive = self.options_selector.get_drive(self.client_machine, 2*self.content_gb*1024)
        
        # Backup and restore paths
        self.test_case_path = self.client_machine.join_path(self.drive, "Automation", str(self.id))
        self.test_data_path = self.client_machine.join_path(self.test_case_path, "Testdata")
        self.content_path = self.get_client_content_folder('1', self.content_gb, self.test_data_path)
        # looks like C:\\Automation\\60717\\Testdata\\Data1-1Gb
        self.restore_data_path = self.client_machine.join_path(self.test_case_path, 'Restore')
        self.restore_path = self.get_client_content_folder('1', self.content_gb, self.restore_data_path)

        self.expected_sha_values_csv_path = self.tcinputs.get('ExpectedShaValuesCsvPath')

        self.rehydrator = Rehydrator(self.id)
        self.upgrade_job_id = self.rehydrator.bucket("upgrade_job_id")
        self.pre_which_commit = self.rehydrator.bucket("pre_which_commit")
        self.pre_hedvig_common = self.rehydrator.bucket("pre_hedvig_common")
        self.pre_hedvig_cluster = self.rehydrator.bucket("pre_hedvig_cluster")
        self.pre_os_version = self.rehydrator.bucket("pre_os_version")
        self.pre_kernel_version = self.rehydrator.bucket("pre_kernel_version")

        self.update_cvfs = self.tcinputs.get('UpgradeCVFS', True)
        self.update_os = self.tcinputs.get('UpgradeOS', False)
        self.non_disruptive = self.tcinputs.get('NonDisruptive', False)

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

        if policy_exists:
            self.commcell.storage_policies.delete(self.storage_policy_name)
            self.log.info(f"{self.storage_policy_name} deleted")

        self.cleanup_test_data()
        self.rehydrator.cleanup()

    def tear_down(self):
        """Tear down function for this test case"""
        # Deleting created objects for backup
        if self.successful:
            self.log.info(f"Test case successful. Cleaning up the entities created (except {self.storage_pool_name})")
            self.cleanup()
        else:
            self.log.warning("Not cleaning up as the run was not successful")
            self.status = constants.FAILED

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
        parsed = {tag:value for tag, value in matches}
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
    
    def verify_output_changed_post_upgrade(self, pre_output, post_output, ma_list):
        """Verifies that the output is different post upgrade
        output: {ma1: value1, ma2: value2, ma3: value3}

            Args:

                pre_output  (output)    --  The output before upgrade

                post_output (output)    --  The output after upgrade

                ma_list     (list)      --  List of MA names

            Returns:

                result      (bool)      --  If the output is different or not

        """
        for ma in ma_list:
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

    def enable_rwp_and_validate(self, ma_list, ma_machines):
        """ Enables rwp on added or refreshed node(s) and validates rwp 

            Args:

                ma_list     (list)  --  List of MA names

                ma_machines (dict)  --  MA name -> Machine object
        """

        for ma in ma_list:
            if not self.rw_helpers[ma].ransomware_protection_status():
                self.log.info(f"RWP disabled on {ma}. Enabling...")
                # 6a. Backup fstab file
                self.log.info(f"Backing up fstab file on {ma}")
                result = self.rw_helpers[ma].backup_fstab(self.id)
                if not result:
                    reason = f"Please fix fstab file on {ma} and rerun the case"
                    return False, reason
                self.log.info(f"Backed up fstab on {ma}")
                # 6b. Fire the command
                result = self.rw_helpers[ma].hsx_enable_protection(self.hyperscale_helper)
                if not result:
                    reason = f"Couldn't enable protection for {ma}"
                    return False, reason
                self.log.info(f"Enable protection successful for {ma}")
            self.log.info(f"RWP already enabled on {ma}. Skipping RWP enablement")
        # 6c. RWP validations
        self.log.info("Validating RWP on addded/refreshed nodes")
        result, reason = UnixRansomwareHelper.hsx_rwp_validation_suite(ma_list, ma_machines, self.hyperscale_helper, self.rw_helpers)
        if not result: 
            reason += f"RWP validations failed on the added/refreshed nodes"
            return False, reason
        self.log.info(f"RWP successfully validated on the added/refreshed nodes")
        return True, None

    def run(self):
        """ run function of this test case"""
        try:
            
            # 0. Cleanup previous runs' entities
            self.log.info("Running cleanup before run")
            self.cleanup()

            # 1. Create a storage pool, if not already there
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
            identical, outputs = self.hyperscale_helper.verify_sp_version_for_clients(self.mas)
            if not identical:
                self.log.error(f"Nodes have version mismatch {outputs}. Proceeding")
            else:
                self.log.info(f"All nodes have same version {outputs[self.mas[0]]}")

            # 6. RWP validations on added nodes
            if self.added_nodes:
                result, reason = self.enable_rwp_and_validate(self.added_nodes, self.ma_machines)
                if not result:
                    reason += f" | Failed to validate RWP on added nodes"
                    return self.fail_test_case(reason)
            else:
                self.log.info(f"No added nodes. Skipping RWP validations on added nodes")

            # 7. RWP validations on refreshed nodes
            if self.refreshed_nodes:
                result, reason = self.enable_rwp_and_validate(self.refreshed_nodes, self.ma_machines)
                if not result:
                    reason += f" | Failed to validate RWP on refreshed nodes"
                    return self.fail_test_case(reason)
            else:
                self.log.info(f"No refreshed nodes. Skipping RWP validations on refreshed nodes")
            
            # 8. populate the remote cache with Unix software
            self.log.info(f"Populating remote cache {self.cache_node} with Unix RPMs")
            if int(str(self.commcell.commserv_version)[:2]) >= 36:
                result, message = self.hyperscale_helper.populate_remote_cache_v4(self.cache_node)
            else:
                result, message = self.hyperscale_helper.populate_remote_cache(self.cache_node)
            if not result:
                reason = message
                return self.fail_test_case(reason)
            self.log.info(f"Successfully populated remote cache {self.cache_node} with Unix RPMs")

            if self.expected_sha_values_csv_path:
                if self.hsx3_or_above:
                    repo_type = 'rocky-8.10'
                else:
                    repo_type = 'rhel-7.9'
                if not self.hyperscale_helper.verify_repo_checksum_csv(self.expected_sha_values_csv_path, repo_type, self.cache_machine):
                    reason = f'Failed to verify repo checksum pre upgrade'
                    return self.fail_test_case(reason)
                self.log.info("Successfully verified repo checksum pre upgrade")
            else:
                self.log.info("Skipping repo checksum verification as ExpectedShaValuesCsvPath is missing")

            # 9a. Backup: create test data
            self.log.info("Proceeding to take backup before upgrade")            
            result = self.create_test_data(self.content_path, self.content_gb)
            if not result:
                reason = "Error while creating test data"
                return self.fail_test_case(reason)
            self.log.info("Created test data")

            # 9b. Backup: take full backup
            self.policy = self.hyperscale_helper.get_or_create_policy(self.storage_pool_name, self.other_mas[0], self.storage_policy_name)
            self.backupset = self.mmhelper_obj.configure_backupset()
            self.subclient_obj = self.mmhelper_obj.configure_subclient(content_path=[self.content_path])
            job_obj = self.subclient_obj.backup("FULL")
            self.log.info(f"Starting backup job [{job_obj.job_id}]")
            if not job_obj.wait_for_completion():
                reason = f"Backup job [{job_obj.job_id}] has failed"
                return self.fail_test_case(reason)
            self.log.info(f"Backup succeeded. Job status {job_obj.status}")

            # 10a. Parse --check_cluster_status_detail output
            self.log.info("--check_cluster_status_detail")
            if not self.parse_cluster_details():
                reason = "Failed to parse check_cluster_status_detail"
                return self.fail_test_case(reason)
            self.log.info("Parsed check_cluster_status_detail output")

            # 10b. Verify nfsstat -m output
            self.log.info("Verifying nfsstat -m output")
            if not self.hyperscale_helper.verify_nfsstat_output(self.mas, self.ma_machines):
                reason = "Failed to verify nfsstat"
                return self.fail_test_case(reason)
            else:
                self.log.info("Verified nfsstat -m output")

            # 10c. Verify df -kht nfs4 output
            self.log.info("Verifying df -kht nfs4 output")
            if not self.hyperscale_helper.verify_df_kht_nfs4_output(self.mas, self.ma_machines):
                reason = "Failed to verify df -kht nfs4"
                return self.fail_test_case(reason)
            else:
                self.log.info("Verified df -kht nfs4 output")

            # 11. Verify whether all hedvig services are up
            self.log.info("Verifying if hedvig services are up on all nodes")
            result = self.hyperscale_helper.verify_hedvig_services_are_up(self.mas, self.ma_machines)
            if not result:
                reason = "Couldn't verify if hedvig services are up on all nodes"
                return self.fail_test_case(reason)
            self.log.info("Successfully verified hedvig services are up and running on all nodes")
            
            # 12. Save whichCommit output
            which_commit_output = self.get_which_commit_output()
            if not which_commit_output:
                reason = "Failed to get ./whichCommit.sh output"
                return self.fail_test_case(reason)
            self.pre_which_commit.set(which_commit_output)
            self.log.info(f"Saved ./whichCommit.sh output")

            # 13a. Save hedvig-common RPM version
            identical, result = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "rpm -qa | grep hedvig-common")
            self.pre_hedvig_common.set(result)
            
            # 13b. Save hedvig-cluster RPM version
            identical, result = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "rpm -qa | grep hedvig-cluster")
            self.pre_hedvig_cluster.set(result)

            # 14a. Save current OS Version
            self.log.info("Saving OS version pre upgrade")
            result, outputs = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "cat /etc/os-release")
            self.pre_os_version.set(outputs)

            # 14b. Save current kernel Version
            self.log.info("Saving kernel version pre upgrade")
            result, outputs = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "uname -r")
            self.pre_kernel_version.set(outputs)
            
            # 15. Run upgrade command based on FR version and Config params
            if int(str(self.commcell.commserv_version)[:2]) >= 36:
                upgrade_job = self.hyperscale_helper.trigger_platform_update_v4(
                    self.storage_pool_name, non_disruptive=self.non_disruptive, update_cvfs=self.update_cvfs, update_os=self.update_os)
            else:
                upgrade_job = self.hyperscale_helper.trigger_platform_update(
                    self.storage_pool_name, non_disruptive=self.non_disruptive, update_cvfs=self.update_cvfs, update_os=self.update_os)
            self.upgrade_job_id.set(upgrade_job.job_id)
            self.log.info(f"Job id {self.upgrade_job_id.get()} created for platform update.")
            
            # this upgrade job will take close to 3 to 4 hours
            # there is a chance that the test case will fail below while waiting
            # so for the next run we will directly jump to this line and
            # if the variable upgrade_job is not defined, we will fetch the existing job
            # from the rehydrator
            if 'upgrade_job' not in vars():
                upgrade_job = Job(self.commcell, self.upgrade_job_id.get())
            if not upgrade_job.wait_for_completion():
                reason = f"Platform update job failed. {upgrade_job.delay_reason}"
                return self.fail_test_case(reason)
            self.log.info("Platform update job succeeded")
            
            is_node_rebooting = False
            for status in upgrade_job.details['jobDetail']['clientStatusInfo']['clientStatus']:
                if "rebooting" in status['jMFailureReasonStatus'].lower():
                    is_node_rebooting = True
                    break
            if is_node_rebooting:
                self.hyperscale_helper.wait_for_reboot(self.cache_node)
                self.hyperscale_helper.wait_for_ping_result_to_be(0, self.cache_node)

            # Waiting for SSH to come up
            self.log.info("Sleeping for a few minutes for SSH to come up")
            time.sleep(2*60)
            
            # 16. Compare whichCommit output
            self.log.info(f"Compare whichCommit.sh output post upgrade")
            output = self.get_which_commit_output()
            if not output:
                reason = "Failed to get whichCommit.sh output post upgrade"
                return self.fail_test_case(reason)
            which_commit_output = self.pre_which_commit.get()
            for key in sorted(output.keys()):
                self.log.info(f"Comparing output for {key}")
                # For platform upgrade post refresh node
                if self.refreshed_nodes:
                    result = self.verify_output_changed_post_upgrade(which_commit_output[key], output[key], self.refreshed_nodes)
                # For platform upgrade post add node
                elif self.added_nodes:
                    result = self.verify_output_changed_post_upgrade(which_commit_output[key], output[key], self.added_nodes)
                # For regular platform upgrade
                else:
                    result = self.verify_output_changed_post_upgrade(which_commit_output[key], output[key], self.mas)
                if not self.update_cvfs:
                    self.log.info(f"Skipping comparison check as update_cvfs was not selected")
                    continue
                if not result:
                    reason = f"Failed to verify that {key} was changed post upgrade"
                    return self.fail_test_case(reason)
                self.log.info(f"Successfully verified that {key} was changed post upgrade")                
            
            # Wait for services to come up before verification
            install_helper = InstallHelper(self.commcell, self.cache_machine)
            install_helper.wait_for_services(wait_time=10*60, retry=20, client=self.commcell.clients.get(self.cache_node))
            
            # 17. Check if commvault service and processes are up
            self.log.info("Verify if commvault service and processes are up post upgrade")
            result = self.hyperscale_helper.verify_commvault_service_and_processes_are_up(self.mas, self.ma_machines)
            if not result:
                reason = "Failed to verify if commvault service and processes are up post upgrade"
                return self.fail_test_case(reason)
            self.log.info(f"Successfully verified commvault service and processes are up post upgrade")

            # 18. Perform restore here
            self.log.info("Performing Restore")
            self.policy = self.hyperscale_helper.get_or_create_policy(self.storage_pool_name, self.other_mas[0], self.storage_policy_name)
            self.backupset = self.mmhelper_obj.configure_backupset()
            self.subclient_obj = self.mmhelper_obj.configure_subclient(content_path=[self.content_path])
            job_obj = self.subclient_obj.restore_out_of_place(self.client, self.restore_data_path, [self.content_path])
            if not job_obj.wait_for_completion():
                reason = f"Restore job has failed {job_obj.pending_reason}"
                return self.fail_test_case(reason)
            self.log.info("Restore job succeeded. Job status %s", job_obj.status)
            
            # 19. Now verify the restored data
            self.log.info("Verifying the restored data")
            self.hyperscale_helper.verify_restored_data(self.client_machine, self.content_path, self.restore_path)

            # 20a. Compare OS version
            self.log.info("Comparing OS version post upgrade")
            result, outputs = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "cat /etc/os-release")
            if not result:
                reason = f"OS version not identical across nodes post upgrade"
                return self.fail_test_case(reason)
            self.log.info("OS version identical across nodes post upgrade")

            # 20b. Compare current kernel Version
            self.log.info("Comparing kernel version post upgrade")
            result, outputs = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "uname -r")
            if not result:
                reason = f"Kernel version not identical across nodes post upgrade"
                return self.fail_test_case(reason)
            self.log.info("Kernel version identical across nodes post upgrade")

            self.successful = True
            self.log.info(f"Platform upgrade successful. Test case executed with no errors")

        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
'''
{
  "taskInfo": {
    "task": {
      "taskType": 1,
      "initiatedFrom": 1,
      "ownerId": 1,
      "ownerName": "admin"
    },
    "subTasks": [
      {
        "subTask": {
          "subTaskType": 1,
          "operationType": 4020
        },
        "options": {
          "adminOpts": {
            "updateOption": {
              "commcellId": 2,
              "installUpdateOptions": 80,
              "invokeLevel": 7,
              "updateClientAfterInstallation": true,
              "rebootClient": false,
              "ignoreRunningJobs": true,
              "runDBMaintenance": false,
              "clientAndClientGroups": [
                {
                  "clientGroupId": 7,
                  "clientSidePackage": true,
                  "_type_": 28,
                  "consumeLicense": true
                }
              ],
              "clientGroup": [
                7
              ],
              "installUpdatesJobType": {
                "upgradeClients": true,
                "installUpdates": false
              }
            }
          },
          "commonOpts": {
            "notifyUserOnJobCompletion": false
          }
        }
      }
    ]
  }
}
'''