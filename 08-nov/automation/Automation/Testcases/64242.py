# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright 2023 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase: DR Orchestration: Test failover validations (cross hypervisor - Hyper-V source)

TestCase: Class for executing this test case
Sample JSON: {
    "tenant_username": <username>,
    "tenant_password": <password>,
    "group_name": "Group_1"
}
"""

from Web.Common.exceptions import CVTestCaseInitFailure
from DROrchestration.DRUtils import DRConstants

tc_60508 = __import__('60508')


class TestCase(tc_60508.TestCase):
    """ DR Orchestration: Test failover validations (cross hypervisor - Hyper-V source) """

    def __init__(self):
        super().__init__()
        self.name = "DR Orchestration: Test failover validations (cross hypervisor - Hyper-V source)"

    def setup(self):
        """ Calls the super setup and then validate_source """
        super().setup()
        self.validate_source()

    def validate_source(self):
        """Validates that the source hypervisor is hyper-v"""
        instance_name = self.test_failover.source_auto_instance.get_instance_name()
        if instance_name != DRConstants.Vendors.HYPERV.value.lower():
            raise CVTestCaseInitFailure(f"Source hypervisor is not HyperV: [{instance_name}]")
