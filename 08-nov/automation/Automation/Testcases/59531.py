# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Test case for point-in-time BLR replica copy data validation
Sample JSON: {
    "source_name": "machine1",
    "source_volume": "E:",
    "destination_name": "machine2",
    "destination_volume": "F:",
    "copy_volume": "G:"
    "rp_store": "AutomationRPStore"
}
"""
import time
from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Reports.utils import TestCaseUtils
from Web.Common.page_object import TestStep, wait_for_condition
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure


class TestCase(CVTestCase):
    """Class for validating FSBLR point-in-time pair replica copy data validation"""
    test_step = TestStep()

    def __init__(self):
        super().__init__()
        self.name = "FSBLR point-in-time pair - Replica copy data verification"
        self.tcinputs = {
            "source_name": None,
            "source_volume": None,
            "destination_name": None,
            "destination_volume": None,
            "copy_volume": None,
            "rp_store": None,
        }
        self.utils = None
        self.source_name = None
        self.source_volume = None
        self.destination_name = None
        self.destination_volume = None
        self.copy_volume = None

        self.source_client = None
        self.source_machine = None
        self.destination_client = None
        self.destination_machine = None
        self.blr_pair = None

        self.rp_store = None
        self.source_hash_1 = None
        self.source_hash_2 = None

    @wait_for_condition(timeout=300, poll_frequency=10)
    def check_pair_status(self, expected):
        """Waits for the sync status to meet expected value"""
        time.sleep(10)
        if not self.blr_pair:
            self.blr_pair = self.commcell.blr_pairs.get(self.source_name, self.destination_name)
        self.log.info('Waiting for FSBLR pair to reach %s state', expected)
        self.blr_pair.refresh()
        return self.blr_pair.pair_status.name.lower() == expected.lower()

    @property
    def test_path(self):
        """Generate the path at which files are present"""
        if not self.source_machine:
            return ''
        return self.source_machine.join_path(self.source_volume, f'testData_{self.id}_{time.time()}')

    def setup(self):
        """Sets up the variables for the test case"""
        try:
            self.utils = TestCaseUtils(self)

            self.source_name = self.tcinputs['source_name']
            self.source_volume = self.tcinputs['source_volume']

            self.destination_name = self.tcinputs['destination_name']
            self.destination_volume = self.tcinputs['destination_volume']
            self.copy_volume = self.tcinputs['copy_volume']

            self.rp_store = self.tcinputs['rp_store']

            self.source_client = self.commcell.clients.get(self.source_name)
            self.source_machine = Machine(self.source_client)
            self.destination_client = self.commcell.clients.get(self.destination_name)
            self.destination_machine = Machine(self.destination_client)
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
    def generate_test_data(self):
        """Generate data at test_path on source machine"""
        self.source_machine.create_directory(self.test_path, force_create=True)
        if not self.source_machine.generate_test_data(self.test_path, dirs=4, files=4, file_size=65536):
            raise Exception("Could not generate test data on source VM")
        self.log.info('Waiting for 2 minutes to let data sync')
        time.sleep(120)
        if not self.source_hash_1:
            self.source_hash_1 = self.source_machine.get_folder_hash(self.source_volume)
        else:
            self.source_hash_2 = self.source_machine.get_folder_hash(self.source_volume)

    @test_step
    def cleanup_test_data(self):
        """Cleanup data at test_path on all machines"""
        self.source_machine.clear_folder_content(self.source_volume)
        self.destination_machine.clear_folder_content(self.destination_volume)
        self.destination_machine.clear_folder_content(self.copy_volume)

    @test_step
    def validate_test_data(self, copy_volume=False):
        """Validate that the test data is correct on the source and destination machines"""
        if not copy_volume:
            self.blr_pair.stop()
            self.check_pair_status('STOPPED')
            missing_files = self.destination_machine.get_folder_hash(self.destination_volume) - self.source_hash_1
            self.blr_pair.start()
            self.check_pair_status('REPLICATING')
        else:
            missing_files = self.destination_machine.get_folder_hash(self.destination_volume) - self.source_hash_1
        missing_files = [file for file in missing_files if 'SystemVolumeInformation' not in file[0]]
        if missing_files:
            raise CVTestStepFailure(f"Some files are missing from in volume"
                                    f" {self.copy_volume if copy_volume else self.destination_volume}:"
                                    f" {missing_files}")

    @test_step
    def create_blr_pair(self):
        """Configures a point-in-time BLR pair"""
        self.commcell.blr_pairs.refresh()
        rpstore_id = self.commcell.blr_pairs.get_rpstore_id(self.rp_store)
        self.commcell.blr_pairs.create_fsblr_pair(self.source_client.client_id,
                                                  self.destination_client.client_id,
                                                  [self.source_volume],
                                                  [self.destination_volume],
                                                  self.commcell.blr_pairs.RecoveryType.GRANULARV2,
                                                  rpstore_id=rpstore_id,
                                                  rpstore_name=self.rp_store)

    def verify_pair_creation(self):
        """Verifies the creating of a Live BLR pair"""
        self.commcell.blr_pairs.refresh()
        if not self.commcell.blr_pairs.has_blr_pair(self.source_name, self.destination_name):
            raise CVTestStepFailure("The BLR pair is not present on the replication monitor")
        self.blr_pair = self.commcell.blr_pairs.get(self.source_name, self.destination_name)
        self.check_pair_status('Replicating')

    @test_step
    def submit_replica_copy(self):
        """Submit replica copy for BLR pair and wait for job to complete"""
        self.log.info('Waiting for first RP store to be generated')
        for _ in range(3):
            if self.blr_pair.get_recovery_point_stores():
                break
            self.log.info('Sleeping for 5 minutes to let RP store create')
            time.sleep(300)
        else:
            raise CVTestStepFailure('Could not find RP stores for BLR pair')

        self.generate_test_data()

        self.log.info('Waiting for second RP store to be generated')
        for _ in range(3):
            if len(self.blr_pair.get_recovery_point_stores()) > 1:
                break
            self.log.info('Sleeping for 5 minutes to let RP store create')
            time.sleep(300)
        else:
            raise CVTestStepFailure('Could not find RP stores for BLR pair')
        rp_stores = self.blr_pair.get_recovery_point_stores()
        copy_job = self.blr_pair.create_replica_copy([self.destination_volume],
                                                     [self.copy_volume],
                                                     timestamp=rp_stores[0].get('timeStamp'))
        self.log.info('Waiting for job [%s] to complete', copy_job.job_id)
        copy_job.wait_for_completion()
        self.utils.assert_comparison(copy_job.status, 'Completed')

    def run(self):
        """Test steps for the testcase"""
        try:
            self.cleanup_test_data()
            self.delete_pair()

            self.generate_test_data()
            self.create_blr_pair()
            self.verify_pair_creation()

            self.validate_test_data(copy_volume=False)

            self.submit_replica_copy()
            self.validate_test_data(copy_volume=True)

            self.delete_pair()
            self.cleanup_test_data()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
