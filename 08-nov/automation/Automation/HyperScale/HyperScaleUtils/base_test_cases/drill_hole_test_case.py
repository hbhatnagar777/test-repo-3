# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for HSX/HS1.5 to test absence of drill hole reg keys
Base file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class

    setup()                         --  setup function of this test case

    cleanup()                       --  Cleans up the test case resources and directories

    tear_down()                     --  Tear down function of this test case
      
    get_sp_version_from_cs()        -- Returns SP version as indicated by CS from client name

    check_identical_values()        -- Runs same operation across multiple MAs for output equality.
      
    check_drill_hole_reg_keys()     -- Checks if drill hole reg keys are absent or not

    fail_test_case()                -- Prints failure reason, sets the result string
      
    run()                           --  run function of this test case
      

Sample input json
"62732/62754": {
            "ControlNodes": {
              "MA1": "name",
              "MA2": "name",
              "MA3": "name"
            },
            "StoragePoolName": "name",
            "SqlLogin": login,        (OPTIONAL)
            "SqlPassword": password   (OPTIONAL)
         }

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper

class DrillHoleTestCase(CVTestCase):
    """Hyperscale test class for HSX to test absence of drill hole reg keys"""

    def __init__(self):
        """Initialization function"""
        super().__init__()
        self.name = "Test Case for HSX to test absence of drill hole reg keys"
        self.result_string = ""
        self.control_nodes = {}
        self.ma1 = ""
        self.ma2 = ""
        self.ma3 = ""
        self.mas = []
        self.cache_node = ""
        self.storage_pool_name = ""
        self.hyperscale_helper = None
        self.tcinputs = {
            "ControlNodes": {
                "MA1": None,
                "MA2": None,
                "MA3": None,
            },
            "StoragePoolName": None,
            "SqlLogin": None,
            "SqlPassword": None
        }
        self.successful = False

    def setup(self):
        """Initializes test case variables"""

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
            self.log.info(f"Creating machine object for: {ma_name}")
            machine = Machine(ma_name, self.commcell)
            self.ma_machines[ma_name] = machine

        self.storage_pool_name = self.tcinputs['StoragePoolName']

        self.sql_login = self.tcinputs['SqlLogin']
        self.sql_sq_password = self.tcinputs['SqlPassword']
        
        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

    def tear_down(self):
        """Tear down function for this test case"""
        # Deleting created objects for backup
        if self.successful:
            self.log.info(f"Test case successful. Not cleaning up {self.storage_pool_name}")
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
    
    def check_drill_hole_reg_keys(self):
        """Checks if drill hole reg keys are absent or not
            We want these reg keys to be absent

            Returns:

                result  (bool) -- True if absent, False otherwise

        """

        reg_keys = ['DedupDrillHoles', 'DedupPruneAllowTruncate']
        result, identical = self.hyperscale_helper.get_reg_key_values(self.mas, self.ma_machines, reg_keys)
        if not all(identical):
            self.log.error(f"Did not get identical values for both reg keys: {result}")
            return False
        value = result[reg_keys[0]][0]
        self.log.info(f"Got identical values for both reg keys: {value}")
        if value is None:
            self.log.info("Both reg keys are absent - as required to be.")
            return True
        self.log.error(f"Both reg keys are present and have value: {value}")
        return False

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
            # 1. Create a storage pool, if not already there
            # TODO: instead of taking storage pool name from user, auto figure out from MMSDSStoragePool
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
            
            # 2. Figure out the unique remote cache
            remote_caches = self.hyperscale_helper.determine_remote_caches(self.mas)
            if len(remote_caches) != 1:
                reason = f"Invalid count of remote caches for the given MAs"
                return self.fail_test_case(reason)
            self.cache_node = remote_caches[0]
            self.log.info(f"Found remote cache: {self.cache_node}")

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
            else:
                self.log.info(f"All nodes have same version {outputs[self.mas[0]]}")
            
            # 6. Check if drill hole reg keys are present or not
            self.log.info("Check whether drill hole reg keys aren't present before restarting services")
            output = self.check_drill_hole_reg_keys()
            if not output:
                reason = "Drill hole reg keys are present before restarting services."
                return self.fail_test_case(reason)
            else:
                self.log.info("Drill hole reg keys aren't present before restarting services")

            # 7. Attempt to restart services
            self.log.info("Now restarting services on all MAs")
            self.check_identical_values(self.mas, self.hyperscale_helper.restart_services)
            self.log.info("Restarted services on all MAs")


            # 8. Check if commvault service and processes are up
            self.log.info("Verify if commvault service and processes are up after commvault restart")
            result = self.hyperscale_helper.verify_commvault_service_and_processes_are_up(self.mas, self.ma_machines)
            if not result:
                reason = "Failed to verify if commvault service and processes are up after commvault restart"
                return self.fail_test_case(reason)
            self.log.info(f"Successfully verified commvault service and processes are up after commvault restart")

            # 6. Check if drill hole reg keys are present or not
            self.log.info("Check whether drill hole reg keys aren't present after restarting services")
            output = self.check_drill_hole_reg_keys()
            if not output:
                reason = "Drill hole reg keys are present after restarting services."
                return self.fail_test_case(reason)
            else:
                self.log.info("Drill hole reg keys aren't present after restarting services")

            self.successful = True
            self.log.info(f"Test case successful. Test case executed with no errors")

        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)
