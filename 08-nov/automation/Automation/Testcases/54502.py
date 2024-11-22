# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case verifies that FSBLR live pair operations are working from APIs
Sample JSON: {
    "source_name": "machine1",
    "source_volume": "E:",
    "destination_name": "machine2",
    "destination_volume": "F:",
    "copy_volumes": ["G:", "H:", "I:"]
}
"""
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from Web.Common.page_object import TestStep, wait_for_condition
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure


class TestCase(CVTestCase):
    """Class for validating FSBLR live pair operations from SDK"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "BLR Live Replication Validation"
        self.tcinputs = {
            "source_name": None,
            "source_volume": None,
            "destination_name": None,
            "destination_volume": None,
            "copy_volumes": [],
        }
        self.utils = None
        self.source_name = None
        self.source_volume = None
        self.destination_name = None
        self.destination_volume = None
        self.copy_volumes = []

        self.source_client = None
        self.destination_client = None
        self.blr_pair = None

    @wait_for_condition(timeout=300, poll_frequency=10)
    def check_pair_status(self, expected):
        """Waits for the sync status to meet expected value"""
        time.sleep(10)
        if not self.blr_pair:
            self.blr_pair = self.commcell.blr_pairs.get(self.source_name, self.destination_name)
        self.log.info('Waiting for FSBLR pair to reach %s state', expected)
        self.blr_pair.refresh()
        return self.blr_pair.pair_status.name.lower() == expected.lower()

    def setup(self):
        """Sets up the variables for the test case"""
        try:
            self.utils = TestCaseUtils(self)

            self.source_name = self.tcinputs['source_name']
            self.source_volume = self.tcinputs['source_volume']

            self.destination_name = self.tcinputs['destination_name']
            self.destination_volume = self.tcinputs['destination_volume']
            self.copy_volumes = self.tcinputs['copy_volumes']

            self.source_client = self.commcell.clients.get(self.source_name)
            self.destination_client = self.commcell.clients.get(self.destination_name)
        except Exception as _exception:
            raise CVTestCaseInitFailure("Failed to initialize testcase") from _exception

    @test_step
    def delete_pair(self):
        """Delete BLR Pair if it already exists"""
        self.commcell.blr_pairs.refresh()
        if self.commcell.blr_pairs.has_blr_pair(self.source_name, self.destination_name):
            self.commcell.blr_pairs.delete(self.source_name, self.destination_name)
            self.log.info('Waiting for 2 minutes FSBLR pair to allow cleanup on replication monitor')
            time.sleep(120)
            self.commcell.blr_pairs.refresh()
            if self.commcell.blr_pairs.has_blr_pair(self.source_name, self.destination_name):
                raise CVTestStepFailure(f"FSBLR pair {self.source_name} -> {self.destination_name} still"
                                        f" exists after deletion")

    @test_step
    def create_blr_pair(self):
        """Configures a live BLR pair"""
        self.commcell.blr_pairs.refresh()
        self.commcell.blr_pairs.create_fsblr_pair(self.source_client.client_id,
                                                  self.destination_client.client_id,
                                                  [self.source_volume],
                                                  [self.destination_volume],
                                                  self.commcell.blr_pairs.RecoveryType.LIVE)

    @test_step
    def verify_pair_creation(self):
        """Verifies the creating of a Live BLR pair"""
        self.commcell.blr_pairs.refresh()
        if not self.commcell.blr_pairs.has_blr_pair(self.source_name, self.destination_name):
            raise CVTestStepFailure("The BLR pair is not present on the replication monitor")

    @test_step
    def verify_pair_status(self):
        """Waits for sometime for pair to add new content and then check its status"""
        # 2) Check Status on pair
        self.check_pair_status('Replicating')

    @test_step
    def verify_resync(self):
        """Performs a re-sync operation and verifies the status"""
        self.blr_pair.resync()
        self.check_pair_status('Re-syncing')
        self.check_pair_status('Replicating')

    @test_step
    def verify_suspend(self):
        """Performs a suspend and verifies the state"""
        self.blr_pair.suspend()
        self.check_pair_status('Suspended')

    @test_step
    def verify_resume(self):
        """Performs a resume operation"""
        self.blr_pair.resume()
        self.check_pair_status('Replicating')

    @test_step
    def verify_stop(self):
        """Performs a stop operation"""
        self.blr_pair.stop()
        self.check_pair_status('Stopped')

    @test_step
    def verify_start(self):
        """Performs a start operation"""
        self.blr_pair.start()
        self.check_pair_status('Replicating')

    @test_step
    def create_replica_copy(self, idx):
        """Create a replica copy for the BLR pair"""
        job_obj = self.blr_pair.create_replica_copy([self.destination_volume], [self.copy_volumes[idx - 1]])
        self.log.info("Waiting for replica copy job to complete: %s", job_obj.job_id)
        job_obj.wait_for_completion()
        self.utils.assert_comparison(job_obj.status, 'Completed')

    def run(self):
        """Main function for test case execution"""
        try:
            self.delete_pair()
            self.create_blr_pair()

            self.verify_pair_creation()
            self.commcell.blr_pairs.refresh()
            self.blr_pair = self.commcell.blr_pairs.get(self.source_name, self.destination_name)
            # Run 3 cycles
            for cycle_num in range(1, 4):
                self.verify_pair_status()

                # 3) Pair operations (Start/Stop / Suspend/Resume ) and validate against status of pair
                # Re-sync
                self.verify_resync()
                # Suspend
                self.verify_suspend()
                # Resume
                self.verify_resume()
                # Stop
                self.verify_stop()
                # Start
                self.verify_start()

                # 5) Run a Replica copy job on pair
                self.create_replica_copy(cycle_num)

            self.delete_pair()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
