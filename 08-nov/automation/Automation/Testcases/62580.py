# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase: DR Orchestration: Warm Sync: Planned Failover and Failback validations

TestCase: Class for executing this test case
"62580": {
    "tenant_username": "<username>",
    "tenant_password": "<password>",
    "group_name": "Warm_Replication_Group_name"
}
"""
from Web.Common.page_object import TestStep
tc_59152 = __import__('59152')


class TestCase(tc_59152.TestCase):
    """ Warm Sync: Planned Failover and Failback validations """
    test_step = TestStep()

    def __init__(self):
        super().__init__()
        self.name = "DR Orchestration: Warm Sync: Planned Failover and Failback validations"
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

    def run(self):
        """Runs the testcase in order"""
        self.check_warm_site()
        super().run()
