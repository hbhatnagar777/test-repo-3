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

    tear_down()                     --  Tear down function of this test case

    parse_which_commit_output()     -- Parses the ./whichCommit.sh output

    get_which_commit_output()       -- Retrieves the ./whichCommit.sh output for all MAs

    parse_cluster_details()         -- Parses the cluster details output

    fail_test_case()                -- Prints failure reason, sets the result string

    run()                           --  run function of this test case

Sample input json
"64165": {
            "ControlNodes": [
                "MA1",
                "MA2",
                "MA3"
            ],
            "CacheNode": {
                "username": "username",
                "password": "password"
            },
            "AddNode": {
                "names": ["name",]
                "username": "username",
                "password": "password",
            },
            "StoragePoolName": "name",
            "SqlLogin": login, (OPTIONAL)
            "SqlPassword": password (OPTIONAL)
        }
"""

import atexit
import re
import time
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import MMHelper
from MediaAgents.MAUtils.hyperscale_setup import HyperscaleSetup
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from HyperScale.HyperScaleUtils.vm_io import VmIo
from HyperScale.HyperScaleUtils.esxManagement import EsxManagement
from AutomationUtils.vmoperations import VmOperations
from AutomationUtils.unix_machine import UnixMachine
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.config import get_config
from AutomationUtils import constants
from pyVim import connect

# The following keys must be present under HyperScale key
# in config.json file
vmconfig_help = '''
"HyperScale": {
    ...,
    "VMConfig": {
        "ServerHostName": "Host name of the VM server",
        "Username": "Login user for the VM server",
        "Password": "password for the user"
    },
    "Credentials": {
        "User": "default username",
        "Password": "default password"
    }
}
'''


class TestCase(CVTestCase):
    """Hyperscale test class for HSX Add node setup creation"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.cache_node_username = None
        self.cache_node_password = None
        self.name = "Test Case for Add node HSX"
        self.result_string = ""
        self.username = ""
        self.password = ""
        self.cache_node = ""
        self.control_nodes = {}
        self.ma1 = ""
        self.ma2 = ""
        self.ma3 = ""
        self.mas = []
        self.storage_pool_name = ""
        self.new_storage_pool_name = ""
        self.sql_sq_password = ""
        self.sql_login = ""
        self.hyperscale_helper = None
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
        self.iso_key = ""
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
                "names":[],
                "username":'',
                "password":''
            },
            "CacheNode": {
                "name": "",
                "username": "",
                "password": ""
            },
            "StoragePoolName": "",
            "SqlLogin": "",
            "SqlPassword": ""
        }
        self.successful = False

    def setup(self):
        """Initializes test case variables"""
        self.cs_hostname = self.inputJSONnode['commcell']['webconsoleHostname']
        self.username = self.inputJSONnode["commcell"]["commcellUsername"]
        self.password = self.inputJSONnode["commcell"]["commcellPassword"]

        # Add node setup
        self.add_nodes = self.tcinputs["AddNode"]["names"]
        self.add_node_username = self.tcinputs["AddNode"]["username"]
        self.add_node_password = self.tcinputs["AddNode"]["password"]

        # Cache node setup
        self.cache_node = self.tcinputs["CacheNode"]["name"]
        self.cache_node_username = self.tcinputs["CacheNode"]["username"]
        self.cache_node_password = self.tcinputs["CacheNode"]["password"]
        self.rpm_path = "/ws/ddb/cvmanager/cds_rpm"

        # MA setup
        self.mas = self.tcinputs["ControlNodes"]
        self.ma_machines = {}
        self.vm_names = {}
        self.available_nodes = self.mas + self.add_nodes
        for ma_name in self.available_nodes:
            self.vm_names[ma_name] = self.tcinputs.get(
                'VMNames', {}).get(ma_name, ma_name)

        self.add_node_name = self.add_nodes[0]

        # CSDB
        self.config = get_config()
        tcinputs_sql_login = self.tcinputs.get('SqlLogin')
        tcinputs_sql_password = self.tcinputs.get('SqlPassword')
        if tcinputs_sql_login == '':
            # go for default credentials
            if not hasattr(self.config.SQL, 'Username'):
                raise Exception(
                    f"Please add default 'Username' to SQL in config.json file OR provide SqlLogin in TC inputs")
            self.sql_login = self.config.SQL.Username
            if not hasattr(self.config.SQL, 'Password'):
                raise Exception(
                    f"Please add default 'Password' to SQL in config.json")
            self.sql_sq_password = self.config.SQL.Password
        else:
            # received a sql username from user
            self.sql_login = tcinputs_sql_login
            self.sql_sq_password = tcinputs_sql_password
        self.hyperscale_helper = HyperScaleHelper(
            self.commcell, self.csdb, self.log)

        self.snapshot_key = self.tcinputs.get("SnapshotKey", "2.2212")
        self.snapshot_name = HyperscaleSetup.get_snapshot_details(self.snapshot_key)[
            0]

        # VM setup
        if not hasattr(self.config.HyperScale, 'VMConfig') or not hasattr(self.config.HyperScale, 'Credentials'):
            raise Exception(
                f"Please add VMConfig and Credentials to HyperScale in config.json file as {vmconfig_help}")

        self.hs_vm_config = self.config.HyperScale.VMConfig

        self.storage_pool_name = self.tcinputs.get('StoragePoolName')
        self.new_storage_pool_name = f"{self.storage_pool_name}New"

    def setup_ma_machines(self, ma_list, username, password):
        """Creates the machine objects
            Args:
                ma_list     ([str])     --  The list of MediaAgents
                username    (str)       --  The username
                password    (str)       --  The password
            Returns:
                None
        """
        for ma in ma_list:
            self.ma_machines[ma] = UnixMachine(ma, username=username, password=password)

    def tear_down(self):
        """Tear down function for this test case"""
        if self.successful:
            self.log.info(
                f"Test case successful.")
        else:
            self.log.warning("The run was not successful")
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
            self.mas, self.ma_machines, command)
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
        identical, result = self.hyperscale_helper.check_identical_output(
            self.mas, self.ma_machines, command)
        if not result:
            self.log.error(f"Unable to get cluster details")
            return False
        self.log.info("Cluster details were parsed")
        return True

    def fail_test_case(self, reason):
        """Prints failure reason, sets the result string
            Args:
                reason         (str)   --  Failure reason
        """
        self.log.error(reason)
        self.result_string = reason
        self.status = constants.FAILED
        self.successful = False

    def run(self):
        """ run function of this test case"""
        try:
            # Clean up MA from the CS
            HyperscaleSetup.cleanup_media_agents_from_cs(
                cs_host=self.cs_hostname,
                cs_user=self.username,
                cs_password=self.password,
                ma_list=self.available_nodes,
                skip_ma_deletion=False,
                skip_sc_deletion=False
            )

            # 5. Revert snapshot
            HyperscaleSetup.revert_snapshot(self.hs_vm_config.ServerHostName, self.hs_vm_config.Username,
                                            self.hs_vm_config.Password, [self.vm_names[ma] for ma in self.available_nodes], snapshot_key=self.snapshot_key)
            time.sleep(60)

            # 8. Create a storage pool, if not already there
            if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.log.info(
                    f"Creating storage pool {self.storage_pool_name}")
                HyperscaleSetup.run_cluster_install_task(
                    self.hs_vm_config.ServerHostName, self.hs_vm_config.Username,
                    self.hs_vm_config.Password, self.cs_hostname, self.username,
                    self.password, [self.vm_names[ma] for ma in self.mas], self.mas, self.storage_pool_name)
                self.log.info(
                    f"Created storage pool {self.storage_pool_name}")
            else:
                reason = f"FATAL: Storage pool {self.storage_pool_name} exists - did cleanup failed?"
                return self.fail_test_case(reason)
            
            self.setup_ma_machines(self.mas, self.cache_node_username, self.cache_node_password)
            self.commcell.clients.refresh()
            self.commcell.media_agents.refresh()

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
            result = self.hyperscale_helper.verify_hedvig_services_are_up(
                self.mas, self.ma_machines)
            if not result:
                reason = "Couldn't verify if hedvig services are up"
                return self.fail_test_case(reason)
            self.log.info(
                "Successfully verified hedvig services are up and running")

            # 4. Check if remote cache is present on cache_node
            self.log.info(
                f"Checking if remote cache is present on {self.cache_node}")
            result = self.hyperscale_helper.is_remote_cache_present(
                self.cache_node)
            if not result:
                reason = f"Cache node {self.cache_node} doesn't have the remote cache setup."
                return self.fail_test_case(reason)
            self.log.info(f"Cache node {self.cache_node} has the remote cache")

            # 5. Sync the cache so that nodes can be updated to latest SP
            self.log.info(
                "syncing the cache so that nodes can be updated to latest SP")
            sync_job = self.commcell.sync_remote_cache([self.cache_node])
            self.log.info(
                f"Starting Remote Cache Sync job [{sync_job.job_id}]")
            if not sync_job.wait_for_completion():
                reason = f"Remote Cache Sync Job ({sync_job.job_id}) Failed"
                return self.fail_test_case(reason)
            self.log.info(
                f"Remote Cache Sync Job ({sync_job.job_id}) Succeeded")

            # 6. update all clients to latest
            self.log.info("Updating all MAs to latest")
            for ma in self.mas:
                client = self.commcell.clients.get(ma)
                job_obj = client.push_servicepack_and_hotfix()
                self.log.info(
                    f"Started update job ({job_obj.job_id}) for {ma}")
                if not job_obj.wait_for_completion():
                    reason = f"{ma} update job {job_obj.job_id} failed to complete"
                    return self.fail_test_case(reason)
            self.log.info(f"All nodes {self.mas} updated to the latest SP")

            # 7. Check SP Version
            self.log.info("Checking SP version for all nodes")
            identical, outputs = self.hyperscale_helper.verify_sp_version_for_clients(
                self.mas)
            if not identical:
                self.log.error(
                    f"Nodes have version mismatch {outputs}. Proceeding")
            self.log.info(
                f"All nodes have same version {outputs[self.mas[0]]}")

            # 8.b  Renaming the storagepool
            self.storage_pool_name = self.hyperscale_helper.update_storage_policy(self.storage_pool_name,
                                                                                  self.new_storage_pool_name,
                                                                                  self.sql_login,
                                                                                  self.sql_sq_password)
            
            self.successful = True
        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
