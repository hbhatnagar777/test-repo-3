# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright 2020 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase: DR Orchestration: Planned Failover and Failback validations (cross hypervisor - hyperV source)

TestCase: Class for executing this test case
Sample JSON: {
    "tenant_username": <username>,
    "tenant_password": <password>,
    "group_name": "Group_1"
}
"""

from Web.Common.exceptions import CVTestCaseInitFailure
from DROrchestration.DRUtils import DRConstants

tc_59152 = __import__('59152')


class TestCase(tc_59152.TestCase):
    """ Planned Failover and Failback validations (cross hypervisor - hyperV source) """

    def __init__(self):
        super().__init__()
        self.name = "DR Orchestration: Planned Failover and Failback validations (cross hypervisor - hyperV source)"

    def setup(self):
        """ Calls the super setup and then validate_source """
        super().setup()
        self.validate_source()

    def validate_source(self):
        """Validates that the source hypervisor is hyperv"""
        instance_name = self.planned_failover.source_auto_instance.get_instance_name()
        if instance_name != DRConstants.Vendors.HYPERV.value.lower():
            raise CVTestCaseInitFailure(f"Source hypervisor is not HyperV: [{instance_name}]")