# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for cv-hedvig repo checksum validation
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  setup function of this test case

    tear_down()                     --  Tear down function of this test case
      
    parse_cluster_details()         -- Parses the cluster details output
      
    fail_test_case()                -- Prints failure reason, sets the result string
      
    run()                           --  run function of this test case
      

Sample input json
"70797": {
            "Nodes": [
              "MA1",
              "MA2",
              "MA3"
            ],
            "NodeUser": "",
            "NodePassword": "",
            "ExpectedShaValuesCsvPath": "",
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
    """Hyperscale test class for CVFS checksum validation"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for 2x: CVFS checksum validation"
        self.tcinputs = {
            "Nodes": [
              "MA1",
              "MA2",
              "MA3"
            ],
            "NodeUser": "",
            "NodePassword": "",
            "ExpectedShaValuesCsvPath": "",
         }
        self.successful = False

    def setup(self):
        """Initializes test case variables"""

        # MA setup
        self.mas = self.tcinputs["Nodes"]
        self.node_username = self.tcinputs["NodeUser"]
        self.node_password = self.tcinputs["NodePassword"]

        HyperscaleSetup.ensure_root_access(
            commcell=self.commcell, node_hostnames = self.mas, node_root_password=self.node_password)

        self.ma_machines = {}
        for ma_name in self.mas:
            if not self.commcell.clients.has_client(ma_name):
                raise Exception(f"{ma_name} MA doesn't exist")
            # username/password is necessary as MAs will be marked in maintenance mode
            self.log.info(f"Creating machine object for: {ma_name}")
            machine = Machine(ma_name, username=self.node_username, password=self.node_password)
            self.ma_machines[ma_name] = machine

        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)
        result = self.hyperscale_helper.determine_remote_caches(self.mas)
        if len(result) != 1:
            raise Exception(f"Remote caches count invalid: {result}")
        self.cache_node = result[0]
        self.cache_machine: UnixMachine = self.ma_machines[self.cache_node]

        result = self.hyperscale_helper.get_storage_pool_from_media_agents(self.mas)
        if not result:
            raise Exception(f"Couldn't determine the storage pool name from {self.mas}")
        self.storage_pool_name = result

        self.other_mas = [ma for ma in self.mas if ma != self.cache_node]

        self.hsx3_or_above = self.hyperscale_helper.is_hsx_node_version_equal_or_above(
            self.ma_machines[self.cache_node], 3
        )

        self.expected_sha_values_csv_path = self.tcinputs['ExpectedShaValuesCsvPath']

    def tear_down(self):
        """Tear down function for this test case"""
        # Deleting created objects for backup
        if self.successful:
            self.log.info(f"Test case successful.")
        else:
            self.log.warning("Test case failed")
            self.status = constants.FAILED

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
            # 1. Sync the cache so that nodes can be updated to latest SP
            self.log.info("syncing the cache so that nodes can be updated to latest SP")
            sync_job = self.commcell.sync_remote_cache([self.cache_node])
            self.log.info(f"Starting Remote Cache Sync job [{sync_job.job_id}]")
            if not sync_job.wait_for_completion():
                reason = f"Remote Cache Sync Job ({sync_job.job_id}) Failed"
                return self.fail_test_case(reason)
            self.log.info(f"Remote Cache Sync Job ({sync_job.job_id}) Succeeded")
            
            # 2. update all clients to latest
            self.log.info("Updating all MAs to latest")
            for ma in self.mas:
                client = self.commcell.clients.get(ma)
                job_obj = client.push_servicepack_and_hotfix()
                self.log.info(f"Started update job ({job_obj.job_id}) for {ma}")
                if not job_obj.wait_for_completion():
                    reason = f"{ma} update job {job_obj.job_id} failed to complete"
                    return self.fail_test_case(reason)
            
            self.log.info(f"All nodes {self.mas} updated to the latest SP")

            # 3. Check SP Version
            self.log.info("Checking SP version for all nodes")
            identical, outputs = self.hyperscale_helper.verify_sp_version_for_clients(self.mas)
            if not identical:
                reason = f"Nodes have version mismatch {outputs}."
                return self.fail_test_case(reason)
            self.log.info(f"All nodes have same version {outputs[self.mas[0]]}")

            # 4. Parse --check_cluster_status_detail output
            self.log.info("--check_cluster_status_detail")
            if not self.parse_cluster_details():
                reason = "Failed to parse check_cluster_status_detail"
                return self.fail_test_case(reason)
            self.log.info("Parsed check_cluster_status_detail output")

            # 5. Verify nfsstat -m output
            self.log.info("Verifying nfsstat -m output")
            if not self.hyperscale_helper.verify_nfsstat_output(self.mas, self.ma_machines):
                reason = "Failed to verify nfsstat"
                return self.fail_test_case(reason)
            self.log.info("Verified nfsstat -m output")

            # 6. Verify df -kht nfs4 output
            self.log.info("Verifying df -kht nfs4 output")
            if not self.hyperscale_helper.verify_df_kht_nfs4_output(self.mas, self.ma_machines):
                reason = "Failed to verify df -kht nfs4"
                return self.fail_test_case(reason)
            self.log.info("Verified df -kht nfs4 output")

            # 7. Verify whether all hedvig services are up
            self.log.info("Verifying if hedvig services are up")
            result = self.hyperscale_helper.verify_hedvig_services_are_up(self.mas, self.ma_machines)
            if not result:
                reason = "Couldn't verify if hedvig services are up"
                return self.fail_test_case(reason)
            self.log.info("Successfully verified hedvig services are up and running")
            
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

            if self.hsx3_or_above:
                repo_type = 'rocky-8.10'
            else:
                repo_type = 'rhel-7.9'
            if not self.hyperscale_helper.verify_repo_checksum_csv(self.expected_sha_values_csv_path, repo_type, self.cache_machine):
                reason = f'Failed to verify repo checksum pre upgrade'
                return self.fail_test_case(reason)
            self.log.info("Successfully verified repo checksum pre upgrade")

            self.successful = True
            self.log.info(f"CVFS repo checksum validation successful. Test case executed with no errors")

        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
