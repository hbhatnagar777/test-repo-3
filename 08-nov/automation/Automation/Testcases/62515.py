# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase: DR Orchestration: Unplanned Failover and Undo failover validations (cross hypervisor - vmware source)

TestCase: Class for executing this test case
Sample JSON: {
    "tenant_username": <username>,
    "tenant_password": <password>,
    "group_name": "Group_1"
}
"""
from Web.Common.exceptions import CVTestCaseInitFailure
from DROrchestration.DRUtils import DRConstants

tc_58673 = __import__('58673')


class TestCase(tc_58673.TestCase):
    """ Unplanned Failover and Undo failover validations (cross hypervisor - vmware source) """
    def __init__(self):
        super().__init__()
        self.name = "DR Orchestration: Planned Failover and Failback validations (cross hypervisor - vmware source)"

    def setup(self):
        """ Calls the super setup and then validate_source """
        super().setup()
        self.validate_source()

    def validate_source(self):
        """Validates that the source hypervisor is vmware"""
        instance_name = self.unplanned_failover.source_auto_instance.get_instance_name()
        if instance_name != DRConstants.Vendors.VMWARE.value.lower():
            raise CVTestCaseInitFailure(f"Source hypervisor is not VMware: [{instance_name}]")
