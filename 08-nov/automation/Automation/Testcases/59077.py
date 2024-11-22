# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case for creating and validation of a live BLR pair from Command center
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
from Reports.utils import TestCaseUtils
from Web.AdminConsole.DR.monitor import ContinuousReplicationMonitor
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, wait_for_condition
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure


class TestCase(CVTestCase):
    """Class for validating FSBLR live pair operations from command center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Command center - FSBLR live replication validation"
        self.tcinputs = {
            "source_name": None,
            "source_volume": None,
            "destination_name": None,
            "destination_volume": None,
            "copy_volumes": [],
        }
        self.utils = None

        self.admin_console = None
        self.replication_monitor = None

        self.source_name = None
        self.source_volume = None
        self.destination_name = None
        self.destination_volume = None
        self.copy_volumes = []

    @wait_for_condition(timeout=300, poll_frequency=10)
    def check_pair_status(self, expected):
        """Waits for the sync status to meet expected value"""
        time.sleep(10)
        self.log.info('Waiting for FSBLR pair to reach %s state', expected)
        return (self.replication_monitor.sync_status(self.source_name,
                                                     self.destination_name) == expected)

    def login(self):
        """Logs in to command center"""
        self.admin_console = AdminConsole(BrowserFactory().create_browser_object().open(),
                                          self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(
            self.inputJSONnode['commcell']['commcellUsername'],
            self.inputJSONnode['commcell']['commcellPassword'],
        )
        self.replication_monitor = ContinuousReplicationMonitor(self.admin_console)

    def logout(self):
        """Logs out of the command center and closes the browser"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.admin_console.browser)

    def setup(self):
        """Sets up the variables for the test case"""
        try:
            self.utils = TestCaseUtils(self)

            self.source_name = self.tcinputs['source_name']
            self.source_volume = self.tcinputs['source_volume']

            self.destination_name = self.tcinputs['destination_name']
            self.destination_volume = self.tcinputs['destination_volume']
            self.copy_volumes = self.tcinputs['copy_volumes']
        except Exception as _exception:
            raise CVTestCaseInitFailure("Failed to initialize testcase") from _exception

    @test_step
    def delete_pair(self):
        """Delete BLR Pair if it already exists"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        if self.replication_monitor.has_replication_group(self.source_name, self.destination_name):
            self.replication_monitor.delete_pair(self.source_name, self.destination_name)
            self.log.info('Waiting for 2 minutes FSBLR pair to allow cleanup on replication monitor')
            time.sleep(120)
            self.admin_console.refresh_page()
            if self.replication_monitor.has_replication_group(self.source_name, self.destination_name):
                raise CVTestStepFailure(f"FSBLR pair {self.source_name} -> {self.destination_name} still"
                                        f" exists after deletion")

    @test_step
    def create_blr_pair(self):
        """Configures a live BLR pair"""
        self.admin_console.navigator.navigate_to_replication_groups()
        replication_group = ReplicationGroup(self.admin_console)
        blr = replication_group.configure_blr()
        blr.add_block_level_replication(self.source_name, self.destination_name,
                                        [self.source_volume], [self.destination_volume], 0)

    @test_step
    def verify_pair_creation(self):
        """Verifies the creating of a Live BLR pair"""
        self.admin_console.navigator.navigate_to_continuous_replication()
        if not self.replication_monitor.has_replication_group(self.source_name, self.destination_name):
            raise CVTestStepFailure("The BLR pair is not present on the replication monitor")

    @test_step
    def verify_pair_status(self):
        """Waits for sometime for pair to add new content and then check its status"""
        # 2) Check Status on pair
        self.admin_console.navigator.navigate_to_continuous_replication()
        self.check_pair_status('Replicating')

    @test_step
    def verify_resync(self):
        """Performs a re-sync operation and verifies the status"""
        self.replication_monitor.resync(self.source_name, self.destination_name)
        self.check_pair_status('Re-syncing')
        self.check_pair_status('Replicating')

    @test_step
    def verify_suspend(self):
        """Performs a suspend and verifies the state"""
        self.replication_monitor.suspend(self.source_name, self.destination_name)
        self.check_pair_status('Suspended')

    @test_step
    def verify_resume(self):
        """Performs a resume operation"""
        self.replication_monitor.resume(self.source_name, self.destination_name)
        self.check_pair_status('Replicating')

    @test_step
    def verify_stop(self):
        """Performs a stop operation"""
        self.replication_monitor.stop(self.source_name, self.destination_name)
        self.check_pair_status('Stopped')

    @test_step
    def verify_start(self):
        """Performs a start operation"""
        self.replication_monitor.start(self.source_name, self.destination_name)
        self.check_pair_status('Replicating')

    @test_step
    def create_replica_copy(self, idx):
        """Create a replica copy for the BLR pair"""
        replica_copy = self.replication_monitor.create_replica_copy(self.source_name, self.destination_name)
        job_id = replica_copy.submit_replica_job(self.copy_volumes[idx - 1], 0)
        self.logout()
        job_obj = self.commcell.job_controller.get(job_id)
        self.log.info("Waiting for replica copy job to complete: %s", job_obj.job_id)
        job_obj.wait_for_completion()
        self.utils.assert_comparison(job_obj.status, 'Completed')
        self.login()

    def run(self):
        try:
            self.login()
            self.delete_pair()
            self.create_blr_pair()

            self.verify_pair_creation()
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

    def tear_down(self):
        self.logout()
