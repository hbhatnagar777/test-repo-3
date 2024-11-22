# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright 2020 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase: DR Orchestration: Client Group: Planned Failover and Failback validations

TestCase: Class for executing this test case
Sample JSON: {
    "tenant_username": <username>,
    "tenant_password": <password>,
    "group_name": "Group_1"
    "client_grp_set": "Client_group_1"
}
"""

from Web.AdminConsole.Helper.dr_helper import ReplicationHelper
from Web.Common.page_object import TestStep


tc_59152 = __import__('59152')


class TestCase(tc_59152.TestCase):
    """ Planned Failover and Failback validations for Client Group feature"""
    test_step = TestStep()

    def __init__(self):
        super().__init__()
        self.name = "DR Orchestration: Client Group: Planned Failover and Failback validations"
        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "group_name": None,
            "access_node_group_set": None
        }
        self.replication_group = None
        self.recovery_target = None
        self.target_details = None

    def setup(self):
        """ Calls the super setup and then validate_source """
        super().setup()
        self.replication_group = self.commcell.replication_groups.get(self.group_name)
        self.recovery_target = self.replication_group.recovery_target
        self.target_details = self.commcell.recovery_targets.get(self.recovery_target)

    @test_step
    def validate_target_access_node_group(self):
        """validates recovery target access node as set access node group"""
        target_access_node_group = self.target_details.access_node_client_group
        if target_access_node_group:
            expected_access_node_group = self.tcinputs['access_node_group_set']
            ReplicationHelper.assert_comparison(target_access_node_group, expected_access_node_group)
            self.log.info("Recovery target has expected access node group")
        else:
            raise Exception("Access node group is not set on target")

    def run(self):
        """Runs the testcase in order"""
        self.validate_target_access_node_group()
        super().run()
