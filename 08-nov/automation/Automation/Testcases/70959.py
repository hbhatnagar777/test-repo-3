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
"70959": {
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

# The following keys must be present under HyperScale key
# in config.json file
vmconfig_help = """
"HyperScale": {
    ...,
    "VMConfig": {
        "ServerHostName": "Host name of the VM server",
        "Username": "Login user for the VM server",
        "Password": "password for the user"
    }
}
"""

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
from HyperScale.HyperScaleUtils.rehydrator import Rehydrator
from HyperScale.HyperScaleUtils.vm_io import VmIo
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.options_selector import OptionsSelector
from cvpysdk.job import Job
from cvpysdk.commcell import Commcell


class TestCase(CVTestCase):
    """Hyperscale test class for Metallic DU Upgrade from CC"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for 2x: Disruptive CVFS only upgrade from CC"
        self.tcinputs = {
            "Nodes": ["MA1", "MA2", "MA3"],
            "CacheNode": {
                "name": "name",
                "username": "username",
                "password": "password",
            },
            "StoragePoolName": "name",
            "SqlLogin": "login",
            "SqlPassword": "password",
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
        self.backup_gateway_host = self.tcinputs["backup_gateway_host"]
        self.backup_gateway_port = self.tcinputs["backup_gateway_port"]
        self.client_machine = Machine(self.client_name, self.commcell)
        self.tenant_commcell = Commcell(
            self.cs_hostname, self.tenant_admin, self.tenant_password
        )

        # Cache node setup
        self.cache_node = self.tcinputs["CacheNode"]["name"]
        self.cache_node_vm = self.tcinputs["CacheNode"].get("vmname", self.cache_node)
        if not self.commcell.clients.has_client(self.cache_node):
            raise Exception(f"{self.cache_node} MA doesn't exist")
        self.cache_node_sds = f"{self.cache_node}sds"
        self.cache_node_username = self.tcinputs["CacheNode"]["username"]
        self.cache_node_password = self.tcinputs["CacheNode"]["password"]

        # MA setup
        self.mas = self.tcinputs["Nodes"]
        self.ma_machines = {}
        for ma_name in self.mas:
            if not self.commcell.clients.has_client(ma_name):
                raise Exception(f"{ma_name} MA doesn't exist")
            # username/password is necessary as MAs will be marked in maintenance mode
            self.log.info(f"Creating machine object for: {ma_name}")
            machine = Machine(
                ma_name,
                username=self.cache_node_username,
                password=self.cache_node_password,
            )
            self.ma_machines[ma_name] = machine
        self.cache_machine: UnixMachine = self.ma_machines[self.cache_node]

        self.other_mas = [ma for ma in self.mas if ma != self.cache_node]

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

        if tcinputs_sql_login is None:
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
            if tcinputs_sql_password is None:
                raise Exception(
                    f"Please provide SqlPassword in TC inputs or remove SqlLogin to fetch credentials from config.json"
                )
            self.sql_login = tcinputs_sql_login
            self.sql_sq_password = tcinputs_sql_password

        # Subclient & Storage setup
        # self.storage_pool_name = f"{self.id}StoragePool"
        self.storage_pool_name = (
            self.cvautoexec_hyperscale_helper.get_storage_pool_from_media_agents(
                self.mas
            )
        )

        cache_node_obj = self.commcell.clients.get(self.cache_node)
        log_directory = cache_node_obj.log_directory
        self.cache_node_install_directory = cache_node_obj.install_directory

        # VM setup
        if not hasattr(self.config.HyperScale, "VMConfig"):
            raise Exception(
                f"Please add VMConfig to HyperScale in config.json file as {vmconfig_help}"
            )
        self.hs_vm_config = self.tcinputs.get(
            "VMConfig", self.config.HyperScale.VMConfig
        )
        self.setup_vm_automation()

        self.CVApplianceConfigPath = self.tcinputs.get("CVApplianceConfigPath")

        self.rehydrator = Rehydrator(self.id)
        self.upgrade_job_id = self.rehydrator.bucket("upgrade_job_id")
        self.pre_which_commit = self.rehydrator.bucket("pre_which_commit")
        self.pre_hedvig_common = self.rehydrator.bucket("pre_hedvig_common")
        self.pre_hedvig_cluster = self.rehydrator.bucket("pre_hedvig_cluster")
        self.pre_os_version = self.rehydrator.bucket("pre_os_version")
        self.pre_kernel_version = self.rehydrator.bucket("pre_kernel_version")

        self.update_cvfs = self.tcinputs.get("UpgradeCVFS", True)
        self.update_os = self.tcinputs.get("UpgradeOS", True)
        self.non_disruptive = self.tcinputs.get("NonDisruptive", False)

    def cleanup(self):
        """Cleans up the test case resources and directories"""

        self.rehydrator.cleanup()

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
        identical, result = self.tenant_hyperscale_helper.check_identical_output(
            self.mas, self.ma_machines, command
        )
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
        cluster_name = self.tenant_hyperscale_helper.get_hedvig_cluster_name(machine)
        if not cluster_name:
            self.log.error("Couldn't get the cluster name")
            return False
        path = "/opt/hedvig/bin/hv_deploy"
        command = f'su -l -c "env HV_PUBKEY=1 {path} --check_cluster_status_detail --cluster_name {cluster_name}" admin'
        identical, result = self.tenant_hyperscale_helper.check_identical_output(
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

    def setup_vm_automation(self):
        """Initializes the VM automation helpers"""
        server_type = VmIo.SERVER_TYPE_ESX
        server_host_name = (
            self.hs_vm_config["ServerHostName"]
            if "ServerHostName" in self.hs_vm_config
            else self.hs_vm_config.ServerHostName
        )
        username = (
            self.hs_vm_config["Username"]
            if "Username" in self.hs_vm_config
            else self.hs_vm_config.Username
        )
        password = (
            self.hs_vm_config["Password"]
            if "Password" in self.hs_vm_config
            else self.hs_vm_config.Password
        )
        vm_config = {
            "server_type": server_type,
            "server_host_name": server_host_name,
            "username": username,
            "password": password,
        }
        self.esx: EsxManagement = VmOperations.create_vmoperations_object(vm_config)
        atexit.register(connect.Disconnect, self.esx.si)
        self.vm_io = VmIo(
            self.cache_node_vm,
            server_type,
            server_host_name,
            username,
            password,
            self.esx,
        )

    def run(self):
        """run function of this test case"""
        try:

            # 1. Check if remote cache is present on cache_node
            self.log.info(f"Checking if remote cache is present on {self.cache_node}")
            result = self.tenant_hyperscale_helper.is_remote_cache_present(
                self.cache_node
            )
            if not result:
                reason = (
                    f"Cache node {self.cache_node} doesn't have the remote cache setup."
                )
                return self.fail_test_case(reason)
            self.log.info(f"Cache node {self.cache_node} has the remote cache")

            # 2. Sync the cache so that nodes can be updated to latest SP
            self.log.info("syncing the cache so that nodes can be updated to latest SP")
            sync_job = self.commcell.sync_remote_cache([self.cache_node])
            self.log.info(f"Starting Remote Cache Sync job [{sync_job.job_id}]")
            if not sync_job.wait_for_completion():
                reason = f"Remote Cache Sync Job ({sync_job.job_id}) Failed"
                return self.fail_test_case(reason)
            self.log.info(f"Remote Cache Sync Job ({sync_job.job_id}) Succeeded")

            # 3. update all clients to latest
            self.log.info("Updating all MAs to latest")
            for ma in self.mas:
                client = self.tenant_commcell.clients.get(ma)
                job_obj = client.push_servicepack_and_hotfix()
                self.log.info(f"Started update job ({job_obj.job_id}) for {ma}")
                if not job_obj.wait_for_completion():
                    reason = f"{ma} update job {job_obj.job_id} failed to complete"
                    return self.fail_test_case(reason)

            self.log.info(f"All nodes {self.mas} updated to the latest SP")

            # 4. Check SP Version
            self.log.info("Checking SP version for all nodes")
            identical, outputs = (
                self.tenant_hyperscale_helper.verify_sp_version_for_clients(self.mas)
            )
            if not identical:
                self.log.error(f"Nodes have version mismatch {outputs}. Proceeding")
            else:
                self.log.info(f"All nodes have same version {outputs[self.mas[0]]}")

            # include retry logic
            # 5. populate the remote cache with Unix software
            self.log.info(f"Populating remote cache {self.cache_node} with Unix RPMs")
            result, message = self.cvautoexec_hyperscale_helper.populate_remote_cache(
                self.cache_node
            )
            if not result:
                reason = message
                return self.fail_test_case(reason)
            self.log.info(
                f"Successfully populated remote cache {self.cache_node} with Unix RPMs"
            )

            if self.CVApplianceConfigPath:
                if not self.tenant_hyperscale_helper.verify_repo_checksum(
                    self.CVApplianceConfigPath, self.cache_machine
                ):
                    reason = f"Failed to verify repo checksum pre upgrade"
                    return self.fail_test_case(reason)
                self.log.info("Successfully verified repo checksum pre upgrade")
            else:
                self.log.info(
                    "Skipping repo checksum verification as CVApplianceConfigPath is missing"
                )

            # 12d. Verify whether all hedvig services are up
            self.log.info("Verifying if hedvig services are up")
            result = self.tenant_hyperscale_helper.verify_hedvig_services_are_up(
                self.mas, self.ma_machines
            )
            if not result:
                reason = "Couldn't verify if hedvig services are up"
                return self.fail_test_case(reason)
            self.log.info("Successfully verified hedvig services are up and running")

            # 12a. Save whichCommit output
            which_commit_output = self.get_which_commit_output()
            if not which_commit_output:
                reason = "Failed to get ./whichCommit.sh output"
                return self.fail_test_case(reason)
            self.pre_which_commit.set(which_commit_output)
            self.log.info(f"Saved ./whichCommit.sh output")

            # 12e. Save hedvig-common RPM version
            identical, result = self.tenant_hyperscale_helper.check_identical_output(
                self.mas, self.ma_machines, "rpm -qa | grep hedvig-common"
            )
            self.pre_hedvig_common.set(result)

            # 12f. Save hedvig-cluster RPM version
            identical, result = self.tenant_hyperscale_helper.check_identical_output(
                self.mas, self.ma_machines, "rpm -qa | grep hedvig-cluster"
            )
            self.pre_hedvig_cluster.set(result)

            # 3a. Save current OS Version
            self.log.info("Saving OS version pre upgrade")
            result, outputs = self.tenant_hyperscale_helper.check_identical_output(
                self.mas, self.ma_machines, "cat /etc/redhat-release"
            )
            self.pre_os_version.set(outputs)

            # 3b. Save current kernel Version
            self.log.info("Saving kernel version pre upgrade")
            result, outputs = self.tenant_hyperscale_helper.check_identical_output(
                self.mas, self.ma_machines, "uname -r"
            )
            self.pre_kernel_version.set(outputs)

            # 15. Login via console
            self.log.info(
                f"Logging in to the remote cache node {self.cache_node} via console"
            )
            self.vm_io.send_keys(["MOD_LCTRL", "MOD_LALT", "F2"])
            time.sleep(60 * 2)
            self.vm_io.take_screenshot("after_2_mins_ctrl_alt_f2")
            self.vm_io.send_command(self.cache_node_username)
            time.sleep(3)
            self.vm_io.send_command(self.cache_node_password)
            # sleeping as it takes some time to login
            time.sleep(2)

            # 16. Run upgrade script
            self.log.info("Running the upgrade script")
            self.vm_io.send_command(
                f"cd {self.cache_node_install_directory}/MediaAgent"
            )
            self.vm_io.send_command("./cvupgradeos.py -upgrade_hedvig_only")

            # time.sleep(600)

            # 16. Run upgrade command based on FR version and Config params
            upgrade_job = self.tenant_hyperscale_helper.trigger_platform_update(
                self.storage_pool_name,
                non_disruptive=self.non_disruptive,
                update_cvfs=self.update_cvfs,
                update_os=self.update_os,
            )
            self.upgrade_job_id.set(upgrade_job.job_id)
            self.log.info(
                f"Job id {self.upgrade_job_id.get()} created for platform update."
            )

            # this upgrade job will take close to 3 to 4 hours
            # there is a chance that the test case will fail below while waiting
            # so for the next run we will directly jump to this line and
            # if the variable upgrade_job is not defined, we will fetch the existing job
            # from the rehydrator
            if "upgrade_job" not in vars():
                upgrade_job = Job(self.commcell, self.upgrade_job_id.get())
            if not upgrade_job.wait_for_completion():
                reason = f"Platform update job failed. {upgrade_job.delay_reason}"
                return self.fail_test_case(reason)
            self.log.info("Platform update job succeeded")

            is_node_rebooting = False
            for status in upgrade_job.details["jobDetail"]["clientStatusInfo"][
                "clientStatus"
            ]:
                if "rebooting" in status["jMFailureReasonStatus"].lower():
                    is_node_rebooting = True
                    break
            if is_node_rebooting:
                self.tenant_hyperscale_helper.wait_for_reboot(self.cache_node)
                self.tenant_hyperscale_helper.wait_for_ping_result_to_be(
                    0, self.cache_node
                )

            # 21a. Compare whichCommit output
            self.log.info(f"Compare whichCommit.sh output post upgrade")
            output = self.get_which_commit_output()
            if not output:
                reason = "Failed to get whichCommit.sh output post upgrade"
                return self.fail_test_case(reason)
            for key in sorted(output.keys()):
                self.log.info(f"Comparing output for {key}")
                result = self.verify_output_changed_post_upgrade(
                    which_commit_output[key], output[key]
                )
                if not result:
                    reason = f"Failed to verify that {key} was changed post upgrade"
                    return self.fail_test_case(reason)
                self.log.info(
                    f"Successfully verified that {key} was changed post upgrade"
                )

            # 14a. Compare OS version
            self.log.info("Comparing OS version post upgrade")
            result, outputs = self.tenant_hyperscale_helper.check_identical_output(
                self.mas, self.ma_machines, "cat /etc/redhat-release"
            )
            self.log.info(f"Previous: {self.pre_os_version.get()}")

            # 14b. Compare current kernel Version
            self.log.info("Comparing kernel version post upgrade")
            result, outputs = self.tenant_hyperscale_helper.check_identical_output(
                self.mas, self.ma_machines, "uname -r"
            )
            self.log.info(f"Previous: {self.pre_kernel_version.get()}")

            self.successful = True
            self.log.info(
                f"Platform upgrade successful. Test case executed with no errors"
            )

        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception(
                "Exception message while executing test case: %s", self.result_string
            )
