# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Test Case for HSX 3x SMOKE: Push Updates Validate"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper


class TestCase(CVTestCase):
    def __init__(self):
        super().__init__()
        self.name = "HSX 3x SMOKE: Push Updates Validate"
        self.tcinputs = {
            "Nodes": [],
            "NodeUsername": "",
            "NodePassword": "",
        }
        self.successful = False

    def fail_test_case(self, reason):
        """Prints failure reason, sets the result string

        Args:

            reason         (str)   --  Failure reason

        """
        self.log.error(reason)
        self.result_string = reason

    def tear_down(self):
        """Tear down function for this test case"""
        # Deleting created objects for backup
        if self.successful:
            self.log.info(f"Test case successful.")
        else:
            self.log.warning("Test case has failed")
            self.status = constants.FAILED

    def setup(self):
        self.mas = self.tcinputs["Nodes"]
        self.node_username = self.tcinputs["NodeUsername"]
        self.node_password = self.tcinputs["NodePassword"]

        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)

    def run(self):
        try:
            # 1. Find the RC
            self.log.info("Finding the RC node")
            rc_nodes = self.hyperscale_helper.determine_remote_caches(self.mas)
            if len(rc_nodes) != 1:
                reason = f"Invalid count of remote caches: {rc_nodes}"
                return self.fail_test_case(reason)
            self.cache_node = rc_nodes[0]
            self.log.info(f"Found out the remote cache to be {self.cache_node}")

            # 2. Sync the cache
            self.log.info(
                f"Syncing the cache so that nodes can be updated to latest SP"
            )
            sync_job = self.commcell.sync_remote_cache([self.cache_node])
            self.log.info(f"Starting Remote Cache Sync job [{sync_job.job_id}]")
            if not sync_job.wait_for_completion():
                reason = f"Remote Cache Sync Job ({sync_job.job_id}) Failed"
                return self.fail_test_case(reason)
            self.log.info(f"Remote Cache Sync Job ({sync_job.job_id}) Succeeded")

            # 3. Update MAs to latest
            self.log.info("Updating all MAs to latest")
            for ma in self.mas:
                client = self.commcell.clients.get(ma)
                job_obj = client.push_servicepack_and_hotfix()
                self.log.info(f"Started update job ({job_obj.job_id}) for {ma}")
                if not job_obj.wait_for_completion():
                    reason = f"{ma} update job {job_obj.job_id} failed to complete"
                    return self.fail_test_case(reason)

            self.log.info(f"All nodes {self.mas} updated to the latest SP")

            # 4. Verify if the Commvault version is same across all nodes
            self.log.info("Verify if the Commvault version is same across all nodes")
            identical, result = self.hyperscale_helper.verify_sp_version_for_clients(
                self.mas
            )
            if not identical:
                reason = f"SP version is not same across clients {result}"
                return self.fail_test_case(reason)
            self.log.info(f"Found SP version to be same: {result[self.mas[0]]}")

            self.log.info("Successfully ran the test case")
            self.successful = True

        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception(
                "Exception message while executing test case: %s", self.result_string
            )
