# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase: DR Orchestration: Warm Sync: Test Failover validations

TestCase: Class for executing this test case
"62581": {
    "tenant_username": "<username>",
    "tenant_password": "<password>",
    "group_name": "Replication_Group_name"
}
"""
from Web.Common.exceptions import CVTestCaseInitFailure
from cvpysdk.drorchestration.replication_groups import ReplicationGroup as ReplicationGroupSDK

tc_60508 = __import__('60508')


class TestCase(tc_60508.TestCase):
    """ Warm Sync: Test Failover validations """

    def __init__(self):
        super().__init__()
        self.name = "DR Orchestration: Warm Sync: Test Failover validations"

    def setup(self):
        """ Calls the super setup """
        super().setup()
        self.validate_group()

    def validate_group(self):
        """Validates the group"""
        _replication_group = ReplicationGroupSDK(self.commcell, self.group_name)
        if not _replication_group.is_warm_sync_enabled:
            raise CVTestCaseInitFailure(f"Group [{self.group_name}] is not a Warm Sync group")