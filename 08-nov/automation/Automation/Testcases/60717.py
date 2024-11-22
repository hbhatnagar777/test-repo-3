# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for HSX OS Upgrade
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
"60717": {
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
            "StoragePoolName": "name",
            "SqlLogin": login,        (OPTIONAL)
            "SqlPassword": password   (OPTIONAL)
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

import time
import re
import atexit
from pyVim import connect

from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.unix_machine import UnixMachine
from AutomationUtils.vmoperations import VmOperations
from HyperScale.HyperScaleUtils.esxManagement import EsxManagement
from HyperScale.HyperScaleUtils.vm_io import VmIo
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.options_selector import OptionsSelector

class TestCase(CVTestCase):
    """Hyperscale test class for HSX OS Upgrade"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for HSX OS Upgrade"
        self.result_string = ""
        self.backupset = ""
        self.subclient_obj = ""
        self.username = ""
        self.password = ""
        self.client = ""
        self.subclient_name = ""
        self.storage_policy = ""
        self.client_name = ""
        self.control_nodes = []
        self.mas = []
        self.storage_pool_name = ""
        self.sql_sq_password = ""
        self.sql_login = ""
        self.storage_policy_name = ""
        self.policy = ""
        self.hyperscale_helper = None
        self.sp_version = ""
        self.tcinputs = {
            "ControlNodes": None,
            "CacheNode": {
                "name": None,
                "vmName": None,
                "username": None,
                "password": None,
            },
            "StoragePoolName": None,
            # SqlLogin: None,       (OPTIONAL)
            # SqlPassword: None     (OPTIONAL)
            "CVApplianceConfigPath": None
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

        # MA setup
        self.control_nodes = self.tcinputs["ControlNodes"]
        self.ma_machines = {}
        for ma_name in self.control_nodes:
            if not self.commcell.clients.has_client(ma_name):
                raise Exception(f"{ma_name} MA doesn't exist")
            self.mas.append(ma_name)
            # username/password is necessary as MAs will be marked in maintenance mode
            self.log.info(f"Creating machine object for: {ma_name}")
            machine = Machine(ma_name, username=self.cache_node_username, password=self.cache_node_password)
            self.ma_machines[ma_name] = machine
        self.vm_ma_names = self.tcinputs.get("VMNames", [name.split('.', 1)[0] for name in self.mas])
        self.cache_machine: UnixMachine = self.ma_machines[self.cache_node]

        self.other_mas = [ma for ma in self.mas if ma != self.cache_node]
        self.other_mas_sds = [f'{ma}sds' for ma in self.other_mas]

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

        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

        # VM setup
        if not hasattr(self.config.HyperScale, 'VMConfig'):
            raise Exception(f"Please add VMConfig to HyperScale in config.json file as {vmconfig_help}")
        self.hs_vm_config = self.tcinputs.get("VMConfig", self.config.HyperScale.VMConfig)
        self.setup_vm_automation()

        self.CVUPGRADEOS_LOG = "cvupgradeos.log"
        self.CV_HV_DEPLOY_LOG = "cv_hv_deploy.log"
        cache_node_obj = self.commcell.clients.get(self.cache_node)
        log_directory = cache_node_obj.log_directory
        self.cache_node_install_directory = cache_node_obj.install_directory
        self.CVUPGRADEOS_LOG_PATH = f"{log_directory}/{self.CVUPGRADEOS_LOG}"
        self.CV_HV_DEPLOY_LOG_PATH = f"{log_directory}/{self.CV_HV_DEPLOY_LOG}"

        self.HVCMD_LOG = ""
        self.sp_version = int(self.commcell.version.split('.')[1])
        if self.sp_version <= 28:
            self.HVCMD_LOG = "hvcmd.log"
        elif self.sp_version >= 32:
            self.HVCMD_LOG = "cv_hv_deploy_debug.log"

        # Set cumulative_hvcmd to True when verifying pre existing logs
        self.cumulative_hvcmd = False
        if self.cumulative_hvcmd:
            self.HVCMD_LOG_PATH = f"{log_directory}/hsupgradedbg/{self.HVCMD_LOG}"
        else:
            if self.sp_version <= 28:
                self.HVCMD_LOG_PATH = f"/tmp/{self.HVCMD_LOG}"
            elif self.sp_version >= 32:
                self.HVCMD_LOG_PATH = f"{log_directory}/{self.HVCMD_LOG}"

        self.YUM_OUT_LOG = "yum.out.log"
        self.YUM_OUT_LOG_PATH = f"{log_directory}/hsupgradedbg/{self.YUM_OUT_LOG}"

        self.CVApplianceConfigPath = self.tcinputs['CVApplianceConfigPath']

    def setup_vm_automation(self):
        """Initializes the VM automation helpers"""
        server_type = VmIo.SERVER_TYPE_ESX
        server_host_name = self.hs_vm_config['ServerHostName'] if 'ServerHostName' in self.hs_vm_config else self.hs_vm_config.ServerHostName
        username =  self.hs_vm_config['Username'] if 'Username' in self.hs_vm_config else self.hs_vm_config.Username
        password = self.hs_vm_config['Password'] if 'Password' in self.hs_vm_config else self.hs_vm_config.Password
        vm_config = {
            'server_type': server_type,
            'server_host_name': server_host_name,
            'username': username,
            'password': password
        }
        self.esx: EsxManagement = VmOperations.create_vmoperations_object(vm_config)
        atexit.register(connect.Disconnect, self.esx.si)
        self.vm_io = VmIo(
            self.cache_node_vm, server_type, server_host_name, username, password, self.esx)

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
            
            # 0. Cleanup previous runs' entities
            self.log.info("Running cleanup before run")
            self.cleanup()

            # cluster becomes unstable if bootup takes more time, so skipping this step
            # self.hyperscale_helper.reboot_and_disable_cd_rom(self.esx, self.vm_ma_names, self.mas)

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

            if not self.hyperscale_helper.verify_repo_checksum(self.CVApplianceConfigPath, self.cache_machine):
                reason = f'Failed to verify repo checksum pre upgrade'
                return self.fail_test_case(reason)
            self.log.info("Successfully verified repo checksum pre upgrade")

            # Part 1: Hedvig upgrade
            # 10a. Backup: create test data
            self.log.info("Proceeding to take backup before Hedvig upgrade")            
            result = self.create_test_data(self.content_path, self.content_gb)
            if not result:
                reason = "Error while creating test data"
                return self.fail_test_case(reason)
            self.log.info("Created test data")

            # 10b. Backup: take full backup
            self.policy = self.hyperscale_helper.get_or_create_policy(self.storage_pool_name, self.other_mas[0], self.storage_policy_name)
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
            else:
                self.log.info("Verified nfsstat -m output")

            # 12c. Verify df -kht nfs4 output
            self.log.info("Verifying df -kht nfs4 output")
            if not self.hyperscale_helper.verify_df_kht_nfs4_output(self.mas, self.ma_machines):
                reason = "Failed to verify df -kht nfs4"
                return self.fail_test_case(reason)
            else:
                self.log.info("Verified df -kht nfs4 output")

            # 12d. Verify whether all hedvig services are up
            self.log.info("Verifying if hedvig services are up")
            result = self.hyperscale_helper.verify_hedvig_services_are_up(self.mas, self.ma_machines)
            if not result:
                reason = "Couldn't verify if hedvig services are up"
                return self.fail_test_case(reason)
            self.log.info("Successfully verified hedvig services are up and running")
            
            # 12a. Save whichCommit output
            which_commit_output = self.get_which_commit_output()
            if not which_commit_output:
                reason = "Failed to get ./whichCommit.sh output"
                return self.fail_test_case(reason)
            self.log.info(f"Saved ./whichCommit.sh output")

            # 12e. Save hedvig-common RPM version
            identical, result = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "rpm -qa | grep hedvig-common")
            rpm_hedvig_common = result
            
            # 12f. Save hedvig-cluster RPM version
            identical, result = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "rpm -qa | grep hedvig-cluster")
            rpm_hedvig_cluster = result            

            # 13a. Get no. of lines in cvupgradeos.log
            self.log.info(f"Getting number of lines in {self.CVUPGRADEOS_LOG}")
            lines_before_os_upgrade = self.hyperscale_helper.get_lines_in_log_file(self.cache_machine, self.CVUPGRADEOS_LOG_PATH)
            self.log.info(f"Number of lines in {self.CVUPGRADEOS_LOG}: {lines_before_os_upgrade}")

            # 13b. Get no. of lines in hvcmd.log (FR 28) or cv_hv_deploy_debug.log (FR 32)
            self.log.info(f"Getting number of lines in {self.HVCMD_LOG}")
            if self.cumulative_hvcmd:
                lines_before_hedvig_upgrade = self.hyperscale_helper.get_lines_in_log_file(self.cache_machine, self.HVCMD_LOG_PATH)
            else:
                lines_before_hedvig_upgrade = 1
            self.log.info(f"Number of lines in {self.HVCMD_LOG}: {lines_before_hedvig_upgrade}")
            
            # 14. setup_vm_automation again as the session times out after 900 seconds
            self.log.info("Setting up VM automation again to avoid timeouts")
            self.setup_vm_automation()

            # 15. Login via console
            self.log.info(f"Logging in to the remote cache node {self.cache_node} via console")
            self.vm_io.send_keys(['MOD_LCTRL', 'MOD_LALT', 'F2'])
            time.sleep(60*2)
            self.vm_io.take_screenshot("after_2_mins_ctrl_alt_f2")
            self.vm_io.send_command(self.cache_node_username)
            time.sleep(3)
            self.vm_io.send_command(self.cache_node_password)
            # sleeping as it takes some time to login
            time.sleep(2)

            # 16. Run upgrade script
            self.log.info("Running the upgrade script")
            self.vm_io.send_command(f"cd {self.cache_node_install_directory}/MediaAgent")
            self.vm_io.send_command("./cvupgradeos.py -upgrade_hedvig_only")
            
            # 17. Finding upgrade sequence
            self.log.info("Finding the upgrade sequence...")
            result = self.hyperscale_helper.upgrade_hedvig_get_upgrade_sequence(
                self.cache_machine, self.CVUPGRADEOS_LOG_PATH, lines_before_os_upgrade, self.mas)
            if not result:
                reason = f"Failed to find the upgrade sequence"
                return self.fail_test_case(reason)
            upgrade_seq, line_no_cvupgos = result
            self.log.info(f"Upgade sequence: {upgrade_seq}")

            # 18. Monitoring hedvig pre-upgrade logs
            self.log.info("Monitoring hedvig pre-upgrade logs on the remote cache node")
            line_no_cvupgos = self.hyperscale_helper.upgrade_hedvig_monitor_initial_logs(
                self.cache_node, self.cache_machine, self.CVUPGRADEOS_LOG_PATH, line_no_cvupgos, upgrade_seq, self.CV_HV_DEPLOY_LOG_PATH)
            if not line_no_cvupgos:
                reason = f"Failed to verify hedvig pre-upgrade logs"
                return self.fail_test_case(reason)
            self.log.info(
                f"Verified hedvig pre-upgrade logs. Proceeding with hedvig upgrade logs")
            
            # 19. Monitoring hedvig upgrade logs
            self.log.info("Monitoring hedvig upgrade logs on the remote cache node")
            line_no_hvcmd = self.hyperscale_helper.upgrade_hedvig_monitor_upgrade_logs(
                self.cache_machine, self.HVCMD_LOG_PATH, lines_before_hedvig_upgrade)
            if not line_no_hvcmd:
                reason = f"Failed to verify hedvig upgrade logs"
                return self.fail_test_case(reason)
            self.log.info(
                f"Verified hedvig upgrade logs. Proceeding with post-upgrade logs")
            
            # 20. Monitoring hedvig post-upgrade logs
            self.log.info("Monitoring hedvig post-upgrade logs on the remote cache node")
            line_no_cvupgos = self.hyperscale_helper.upgrade_hedvig_monitor_final_logs(
                self.cache_machine, self.CVUPGRADEOS_LOG_PATH, line_no_cvupgos, upgrade_seq)
            if not line_no_cvupgos:
                reason = f"Failed to verify hedvig post-upgrade logs"
                return self.fail_test_case(reason)
            self.log.info(f"Verified hedvig post-upgrade logs.")

            # 21a. Compare whichCommit output
            self.log.info(f"Compare whichCommit.sh output post upgrade")
            output = self.get_which_commit_output()
            if not output:
                reason = "Failed to get whichCommit.sh output post upgrade"
                return self.fail_test_case(reason)
            for key in sorted(output.keys()):
                self.log.info(f"Comparing output for {key}")
                result = self.verify_output_changed_post_upgrade(which_commit_output[key], output[key])
                if not result:
                    reason = f"Failed to verify that {key} was changed post upgrade"
                    return self.fail_test_case(reason)
                self.log.info(f"Successfully verified that {key} was changed post upgrade")                
            
            # 21b. Compare hedvig-common RPM version
            self.log.info("Compare hedvig-common RPM version post upgrade")
            identical, result = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "rpm -qa | grep hedvig-common")
            result = self.verify_output_changed_post_upgrade(rpm_hedvig_common, result)
            if not result:
                reason = f"Failed to verify that hedvig-common RPM was changed post upgrade"
                return self.fail_test_case(reason)
            self.log.info(f"Successfully verified that hedvig-common RPM was changed post upgrade")            
                
            # 21c. Compare hedvig-cluster RPM version
            self.log.info("Compare hedvig-cluster RPM version post upgrade")
            identical, result = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "rpm -qa | grep hedvig-cluster")
            result = self.verify_output_changed_post_upgrade(rpm_hedvig_cluster, result)
            if not result:
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

            # 23. Perform restore here
            self.log.info("Performing Restore")
            self.policy = self.hyperscale_helper.get_or_create_policy(self.storage_pool_name, self.other_mas[0], self.storage_policy_name)
            self.backupset = self.mmhelper_obj.configure_backupset()
            self.subclient_obj = self.mmhelper_obj.configure_subclient(content_path=[self.content_path])
            job_obj = self.subclient_obj.restore_out_of_place(self.client, self.restore_data_path, [self.content_path])
            if not job_obj.wait_for_completion():
                reason = f"Restore job has failed {job_obj.pending_reason}"
                return self.fail_test_case(reason)
            self.log.info("Restore job succeeded. Job status %s", job_obj.status)
            
            # 24. Now verify the restored data
            self.log.info("Verifying the restored data")
            self.hyperscale_helper.verify_restored_data(self.client_machine, self.content_path, self.restore_path)

            self.log.info(f"Successfully upgraded the Hedvig RPMs")

            # Part 2: OS Upgrade
            # 1a. Backup: create test data
            self.log.info("Proceeding to take backup before OS upgrade")            
            result = self.create_test_data(self.content_path, self.content_gb)
            if not result:
                reason = "Error while creating test data"
                return self.fail_test_case(reason)
            self.log.info("Created test data")

            # 1b. Backup: take full backup
            self.policy = self.hyperscale_helper.get_or_create_policy(self.storage_pool_name, self.other_mas[0], self.storage_policy_name)
            self.backupset = self.mmhelper_obj.configure_backupset()
            self.subclient_obj = self.mmhelper_obj.configure_subclient(content_path=[self.content_path])
            job_obj = self.subclient_obj.backup("FULL")
            self.log.info(f"Starting backup job [{job_obj.job_id}]")
            if not job_obj.wait_for_completion():
                reason = f"Backup job [{job_obj.job_id}] has failed"
                return self.fail_test_case(reason)
            self.log.info(f"Backup succeeded. Job status {job_obj.status}")

            # 2. Mark MAs in maintenance mode
            self.log.info("Marking media agents in maintenance mode")
            for ma in self.mas:
                ma_obj = self.commcell.media_agents.get(ma)
                ma_obj.mark_for_maintenance(True)
            self.log.info(f"Marked MAs in maintenance mode")

            # 3a. Save current OS Version
            self.log.info("Saving OS version pre upgrade")
            result, outputs = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "cat /etc/redhat-release")
            pre_os_version = outputs

            # 3b. Save current kernel Version
            self.log.info("Saving kernel version pre upgrade")
            result, outputs = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "uname -r")
            pre_kernel_version = outputs

            # 4a. Get no. of lines in cvupgradeos.log
            self.log.info(f"Getting number of lines in {self.CVUPGRADEOS_LOG} before OS upgrade")
            lines_before_os_upgrade = self.hyperscale_helper.get_lines_in_log_file(self.cache_machine, self.CVUPGRADEOS_LOG_PATH)
            self.log.info(f"Number of lines in {self.CVUPGRADEOS_LOG}: {lines_before_os_upgrade}")

            # 4b. Get no. of lines in hvcmd.log
            self.log.info(f"Getting number of lines in {self.HVCMD_LOG} before OS Upgrade")
            if self.cumulative_hvcmd:
                lines_before_hedvig_upgrade = self.hyperscale_helper.get_lines_in_log_file(self.cache_machine, self.HVCMD_LOG_PATH)
            else:
                lines_before_hedvig_upgrade = 1
            self.log.info(f"Number of lines in {self.HVCMD_LOG}: {lines_before_hedvig_upgrade}")

            # 5. setup_vm_automation again as the session times out after 900 seconds
            self.log.info("Setting up VM automation again to avoid timeouts")
            self.setup_vm_automation()

            # 6. Login via console
            self.log.info(f"Logging in to the remote cache node {self.cache_node} via console")
            self.vm_io.send_keys(['MOD_LCTRL', 'MOD_LALT', 'F2'])
            time.sleep(10)
            self.vm_io.send_command(self.cache_node_username)
            self.vm_io.send_command(self.cache_node_password)
            # sleeping as it takes some time to login
            time.sleep(2)

            # 7. Run upgrade script
            self.log.info("Running the upgrade script")
            self.vm_io.send_command(f"cd {self.cache_node_install_directory}/MediaAgent")
            self.vm_io.send_command("./cvupgradeos.py")

            # 8. Finding upgrade sequence
            self.log.info("Finding the upgrade sequence for OS upgrade")
            result = self.hyperscale_helper.upgrade_hedvig_get_upgrade_sequence(
                self.cache_machine, self.CVUPGRADEOS_LOG_PATH, lines_before_os_upgrade, self.mas)
            if not result:
                reason = f"Failed to find the upgrade sequence while performing OS upgrade"
                return self.fail_test_case(reason)
            upgrade_seq, line_no_cvupgos = result
            self.log.info(f"Upgade sequence: {upgrade_seq}")

            # 9. Monitoring OS upgrade prerequisite logs
            line_no_cvupgos = self.hyperscale_helper.upgrade_os_monitor_prereq_logs(
                self.cache_machine, self.CVUPGRADEOS_LOG_PATH, line_no_cvupgos, upgrade_seq)
            if not line_no_cvupgos:
                reason = f"Failed to verify OS upgrade prereq logs"
                return self.fail_test_case(reason)
            self.log.info(f"Prereq logs successfully verified")
                
            self.log.info(f"Now proceeding for OS upgrade. Sending 'y'")
            self.vm_io.send_command('y')
            
            # 10. Monitoring OS upgrade pre-upgrade logs
            line_no_cvupgos = self.hyperscale_helper.upgrade_os_monitor_initial_logs(
                self.cache_machine, self.CVUPGRADEOS_LOG_PATH, line_no_cvupgos, upgrade_seq)
            if not line_no_cvupgos:
                reason = f"Failed to verify OS upgrade begin logs"
                return self.fail_test_case(reason)
            self.log.info(f"OS upgrade begin logs successfully verified")

            # 11. Do we need the upgrade?
            self.log.info("Checking if upgrade will proceed or bail out")
            result, line_no_cvupgos = self.hyperscale_helper.upgrade_os_should_proceed(self.cache_machine, self.CVUPGRADEOS_LOG_PATH, line_no_cvupgos)
            if line_no_cvupgos is None:
                reason = "Failed to determine if upgrade should proceed or not"
                return self.fail_test_case(reason)
            if not result:
                self.log.info("No upgrade required at this point. Returning")
                self.successful = True
                return
            self.log.info("Proceeding with node wise log checking")
            
            # 12. Node wise logs
            for ma in upgrade_seq[:-1]:
                self.log.info(f"Now verifying logs on {ma}")
                line_no_cvupgos = self.hyperscale_helper.upgrade_os_monitor_node_logs(
                    self.ma_machines[ma], self.CVUPGRADEOS_LOG_PATH,
                    self.HVCMD_LOG_PATH, self.cumulative_hvcmd,
                    self.YUM_OUT_LOG_PATH,
                    self.cache_machine, line_no_cvupgos, self.CV_HV_DEPLOY_LOG_PATH)
                if not line_no_cvupgos:
                    reason = f"Couldn't verify logs for node {ma}"
                    return self.fail_test_case(reason)
                self.log.info(f"Successfully verified logs for node {ma}")
            
            # 13. Final node
            self.log.info(f"Now proceeding with self upgrade of {self.cache_node}")
            result = self.hyperscale_helper.upgrade_os_monitor_remote_cache_logs(
                self.cache_machine, self.CVUPGRADEOS_LOG_PATH, line_no_cvupgos,
                self.HVCMD_LOG_PATH, self.cumulative_hvcmd, self.CV_HV_DEPLOY_LOG_PATH)
            if not result:
                reason = f"Couldn't verify logs for node {self.cache_node}"
                return self.fail_test_case(reason)
            self.log.info(f"Successfully verified logs for node {self.cache_node}")
            self.log.info("OS upgrade log checking was successful")
            
            # 14a. Compare OS version
            self.log.info("Comparing OS version post upgrade")
            result, outputs = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "cat /etc/redhat-release")
            self.log.info(f"Previous: {pre_os_version}")

            # 14b. Compare current kernel Version
            self.log.info("Comparing kernel version across nodes post upgrade")
            result, outputs = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "uname -r")
            if not result:
                reason = f"Kernel versions post OS upgrade doesnt match on all nodes"
                self.fail_test_case(reason)
            post_kernel_version = outputs
            self.log.info(f"Kernel version post upgrade: {post_kernel_version}")

            # 14c. Compare current kernel version with the expected kernel version
            self.log.info(f"Comparing current kernel version with expected kernel version")
            result, outputs = self.hyperscale_helper.validate_cluster_kernel_versions(self.ma_machines)
            if not result:
                failed_nodes = [ma_name for ma_name, status in outputs.items() if not status]
                reason = f"Current kernel version doesn't match the expected kernel version on these nodes -> {failed_nodes}"
                self.fail_test_case(reason)
            self.log.info(f"Current kernel version matches the expected kernel versions on all nodes")

            # 14d. Check if commvault service and processes are up
            self.log.info("Verify if commvault service and processes are up post OS upgrade")
            result = self.hyperscale_helper.verify_commvault_service_and_processes_are_up(self.mas, self.ma_machines)
            if not result:
                reason = "Failed to verify if commvault service and processes are up post OS upgrade"
                return self.fail_test_case(reason)
            self.log.info(f"Successfully verified commvault service and processes are up post OS upgrade")

            # 15. Mark MAs out of maintenance mode
            self.log.info("Marking media agents out of maintenance mode")
            for ma in self.mas:
                ma_obj = self.commcell.media_agents.get(ma)
                ma_obj.mark_for_maintenance(False)
            self.log.info(f"Marked MAs out of maintenance mode")

            # 16. Perform restore here
            self.log.info("Performing Restore")
            self.policy = self.hyperscale_helper.get_or_create_policy(self.storage_pool_name, self.other_mas[0], self.storage_policy_name)
            self.backupset = self.mmhelper_obj.configure_backupset()
            self.subclient_obj = self.mmhelper_obj.configure_subclient(content_path=[self.content_path])
            job_obj = self.subclient_obj.restore_out_of_place(self.client, self.restore_data_path, [self.content_path])
            if not job_obj.wait_for_completion():
                reason = f"Restore job has failed {job_obj.pending_reason}"
                return self.fail_test_case(reason)
            self.log.info("Restore job succeeded. Job status %s", job_obj.status)
            
            # 17. Now verify the restored data
            self.log.info("Verifying the restored data")
            self.hyperscale_helper.verify_restored_data(self.client_machine, self.content_path, self.restore_path)

            self.successful = True
            self.log.info(f"Upgrade successful. Test case executed with no errors")

        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
