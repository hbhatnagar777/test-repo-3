# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""HS 3.x Smoke Automation: Platform Upgrade via API
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

    parse_cluster_details()         -- Parses the cluster details output
      
    fail_test_case()                -- Prints failure reason, sets the result string
      
    run()                           --  run function of this test case
      

Sample input json
"71063": {
            "Nodes": [
              "MA1",
              "MA2",
              "MA3"
            ],
            "NodeUsername": "",
            "NodePassword": "",
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
from MediaAgents.MAUtils.hyperscale_setup import HyperscaleSetup
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.options_selector import OptionsSelector
from cvpysdk.job import Job

class TestCase(CVTestCase):
    """HS 3.x Smoke Automation: Platform Upgrade via API"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "HS 3.x Smoke Automation: Platform Upgrade via API"
        self.tcinputs = {
            "Nodes": [
              "MA1",
              "MA2",
              "MA3"
            ],
            "NodeUsername": "",
            "NodePassword": "",
            # "UpgradeCVFS": None,
            # "UpgradeOS": None,
            # "NonDisruptive": None,
         }
        self.successful = False

    def setup(self):
        """Initializes test case variables"""

        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)
        self.mas = self.tcinputs["Nodes"]
        if "CacheNode" in self.tcinputs:
            self.cache_node = self.tcinputs['CacheNode']
        else:
            rcs = self.hyperscale_helper.determine_remote_caches(ma_names=self.mas)
            if len(rcs) != 1:
                raise Exception(f"Invalid remote caches: {rcs}")
            self.cache_node = rcs[0]
        
        if "StoragePoolName" in self.tcinputs:
            self.storage_pool_name = self.tcinputs['StoragePoolName']
        else:
            self.storage_pool_name = self.hyperscale_helper.get_storage_pool_from_media_agents(self.mas)
        self.node_username = self.tcinputs["NodeUsername"]
        self.node_password = self.tcinputs["NodePassword"]

        HyperscaleSetup.ensure_root_access(commcell=self.commcell, node_hostnames=self.mas, node_root_password=self.node_password)
        self.ma_machines = {}
        for ma_name in self.mas:
            if not self.commcell.clients.has_client(ma_name):
                raise Exception(f"{ma_name} MA doesn't exist")
            # username/password is necessary as MAs will be marked in maintenance mode
            self.log.info(f"Creating machine object for: {ma_name}")
            machine = Machine(ma_name, username=self.node_username, password=self.node_password)
            self.ma_machines[ma_name] = machine
        self.cache_machine: UnixMachine = self.ma_machines[self.cache_node]

        self.other_mas = [ma for ma in self.mas if ma != self.cache_node]

        self.hsx3_or_above = self.hyperscale_helper.is_hsx_node_version_equal_or_above(
            self.ma_machines[self.cache_node], 3
        )

        self.rehydrator = Rehydrator(self.id)
        self.upgrade_job_id = self.rehydrator.bucket("upgrade_job_id")
        self.pre_which_commit = self.rehydrator.bucket("pre_which_commit")
        self.pre_hedvig_common = self.rehydrator.bucket("pre_hedvig_common")
        self.pre_hedvig_cluster = self.rehydrator.bucket("pre_hedvig_cluster")
        self.pre_os_version = self.rehydrator.bucket("pre_os_version")
        self.pre_kernel_version = self.rehydrator.bucket("pre_kernel_version")

        self.update_cvfs = self.tcinputs.get('UpgradeCVFS', True)
        self.update_os = self.tcinputs.get('UpgradeOS', True)
        self.non_disruptive = self.tcinputs.get('NonDisruptive', False)

    def cleanup(self):
        """Cleans up the test case resources and directories"""
        
        self.rehydrator.cleanup()

    def tear_down(self):
        """Tear down function for this test case"""
        if self.successful:
            self.log.info(f"Test case successful. Cleaning up the entities created")
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
    
    def fail_test_case(self, reason):
        """Prints failure reason, sets the result string

            Args:

                reason         (str)   --  Failure reason

        """
        self.log.error(reason)
        self.result_string = reason
    
    def run(self):
        """ run function of this test case"""
        try:
            
            # 0. Cleanup previous runs' entities
            self.log.info("Running cleanup before run")
            self.cleanup()

            # 1. Check SP Version
            self.log.info("Checking SP version for all nodes")
            identical, outputs = self.hyperscale_helper.verify_sp_version_for_clients(self.mas)
            if not identical:
                self.log.error(f"Nodes have version mismatch {outputs}. Proceeding")
            else:
                self.log.info(f"All nodes have same version {outputs[self.mas[0]]}")
            
            # 2a. Parse --check_cluster_status_detail output
            self.log.info("--check_cluster_status_detail")
            if not self.parse_cluster_details():
                reason = "Failed to parse check_cluster_status_detail"
                return self.fail_test_case(reason)
            self.log.info("Parsed check_cluster_status_detail output")

            # 2b. Verify nfsstat -m output
            self.log.info("Verifying nfsstat -m output")
            if not self.hyperscale_helper.verify_nfsstat_output(self.mas, self.ma_machines):
                reason = "Failed to verify nfsstat"
                return self.fail_test_case(reason)
            else:
                self.log.info("Verified nfsstat -m output")

            # 2c. Verify df -kht nfs4 output
            self.log.info("Verifying df -kht nfs4 output")
            if not self.hyperscale_helper.verify_df_kht_nfs4_output(self.mas, self.ma_machines):
                reason = "Failed to verify df -kht nfs4"
                return self.fail_test_case(reason)
            else:
                self.log.info("Verified df -kht nfs4 output")

            # 2d. Verify whether all hedvig services are up
            self.log.info("Verifying if hedvig services are up")
            result = self.hyperscale_helper.verify_hedvig_services_are_up(self.mas, self.ma_machines)
            if not result:
                reason = "Couldn't verify if hedvig services are up"
                return self.fail_test_case(reason)
            self.log.info("Successfully verified hedvig services are up and running")
            
            # 3a. Save whichCommit output
            which_commit_output = self.get_which_commit_output()
            if not which_commit_output:
                reason = "Failed to get ./whichCommit.sh output"
                return self.fail_test_case(reason)
            self.pre_which_commit.set(which_commit_output)
            self.log.info(f"Saved ./whichCommit.sh output")

            # 3b. Save hedvig-common RPM version
            identical, result = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "rpm -qa | grep hedvig-common")
            self.pre_hedvig_common.set(result)
            
            # 3c. Save hedvig-cluster RPM version
            identical, result = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "rpm -qa | grep hedvig-cluster")
            self.pre_hedvig_cluster.set(result)

            # 3d. Save current OS Version
            self.log.info("Saving OS version pre upgrade")
            result, outputs = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "cat /etc/os-release")
            self.pre_os_version.set(outputs)

            # 3e. Save current kernel Version
            self.log.info("Saving kernel version pre upgrade")
            result, outputs = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "uname -r")
            self.pre_kernel_version.set(outputs)
            
            # 4. Run upgrade command based on FR version and Config params
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
                time.sleep(5*60)
            
            # 5a. Compare hedvig-common RPM version
            self.log.info("Compare hedvig-common RPM version post upgrade")
            identical, result = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "rpm -qa | grep hedvig-common")
            self.log.info(f"Previous: {self.pre_hedvig_common.get()}")
                
            # 5b. Compare hedvig-cluster RPM version
            self.log.info("Compare hedvig-cluster RPM version post upgrade")
            identical, result = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "rpm -qa | grep hedvig-cluster")
            self.log.info(f"Previous: {self.pre_hedvig_cluster.get()}")

            # 5c. Compare OS version
            self.log.info("Comparing OS version post upgrade")
            result, outputs = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "cat /etc/os-release")
            self.log.info(f"Previous: {self.pre_os_version.get()}")

            # 5d. Compare current kernel Version
            self.log.info("Comparing kernel version post upgrade")
            result, outputs = self.hyperscale_helper.check_identical_output(self.mas, self.ma_machines, "uname -r")
            self.log.info(f"Previous: {self.pre_kernel_version.get()}")

            self.successful = True
            self.log.info(f"Platform upgrade successful. Test case executed with no errors")

        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
