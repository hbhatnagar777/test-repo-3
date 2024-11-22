# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright 2020 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase: DR Orchestration: Azure: Planned Failover and Failback validations when blobs not retained

TestCase: Class for executing this test case
Sample JSON: {
    "tenant_username": <username>,
    "tenant_password": <password>,
    "group_name": "Group_1"
}
"""

from Web.Common.exceptions import CVTestCaseInitFailure
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper

tc_59152 = __import__('59152')


class TestCase(tc_59152.TestCase):
    """ DR Orchestration: Azure: Planned Failover and Failback validations when blobs not retained """

    def __init__(self):
        super().__init__()
        self.name = "DR Orchestration: DR Orchestration: Azure: Planned Failover and Failback validations when blobs " \
                    "not retained "

    def setup(self):
        """ Calls the super setup and then validate_source """
        super().setup()

    def run(self):
        """Runs the testcase in order"""
        try:
            self.planned_failover_validation(after_operation=False)
            self.perform_failover(retain_blob=False)
            self.planned_failover_validation(after_operation=True)

            self.failback_validations(after_operation=False)
            self.perform_failback()
            self.failback_validations(after_operation=True)
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)
