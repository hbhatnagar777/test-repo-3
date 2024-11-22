# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase: DR Orchestration: Warm Sync: Unplanned Failover and Undo failover validations

TestCase: Class for executing this test case
"62581": {
    "tenant_username": "<username>",
    "tenant_password": "<password>",
    "group_name": "Warm Replication_Group_name"
}
"""
from Web.Common.page_object import TestStep
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper
tc_58673 = __import__('58673')


class TestCase(tc_58673.TestCase):
    """ Warm Sync: Unplanned Failover and Undo failover validations """
    test_step = TestStep()

    def __init__(self):
        super().__init__()
        self.name = "DR Orchestration: Warm Sync: Unplanned Failover and Undo failover validations"
        self.replication_group = None

    def setup(self):
        """ Calls the super setup """
        super().setup()
        self.replication_group = self.commcell.replication_groups.get(self.group_name)

    @test_step
    def check_warm_site(self):
        """Checks warm site group or not"""
        if not self.replication_group.is_warm_sync_enabled:
            raise Exception("Replication Group is hot-site convert to warm-site")
        else:
            self.log.info("Replication Group is warm-site")

    @test_step
    def perform_undo_failover(self):
        """Perform the undo failover operation for all VMs in group"""
        # Support available for all vendors
        self.login()
        self.replication_helper: ReplicationHelper
        job_id = (self.replication_helper
                  .perform_undo_failover(self.group_name,
                                         operation_level=ReplicationHelper.Operationlevel.GROUP))
        self.logout()

        self.log.info(
            'Waiting for group level undo failover job ID [%s]', job_id)
        undo_failover_job = self.commcell.job_controller.get(job_id)
        undo_failover_job.wait_for_completion()
        self.utils.assert_comparison(undo_failover_job.status, 'Completed')
        self.undo_failover.job_phase_validation(job_id)

    def undo_failover_validations(self, after_operation=False):
        """ Validations before/after the undo failover (Warm Sync)"""
        # Support available for all vendors
        if after_operation:
            self.undo_failover.post_validation()
        else:
            self.undo_failover.pre_validation()

    def run(self):
        """Runs the testcase in order"""
        self.check_warm_site()
        super().run()
