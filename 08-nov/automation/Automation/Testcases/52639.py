# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright 2020 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from cvpysdk.drorchestration.failovergroups import FailoverGroup

from AutomationUtils import constants
from DROrchestration.cvtestcase_failover_group import CVTestCaseFailoverGroup


class TestCase(CVTestCaseFailoverGroup):
    """Class for executing Basic acceptance Test of NDMP backup and Restore test case

    This test runs the following things from the Failover Group.
    * Runs planned failover
    * Runs undo failover

    Input:
        "52639": {
            "failoverGroupName": "Failover Group Name",
            "VirtualizationClient": "Hypervisor Hostname"

            "ClientName": "Hypervisor Name",
            "AgentName": "Agent Name",
            "InstanceName": "Instance Name",

            "vmUsername": "Username of the VM (optional)",
            "vmPassword": "Password of the VM (optional)"
        }
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VirtualServer-AdminConsole-FailoverGroups-PlannedFailover-UndoFailover"
        self.id = "52639"

        self.tcinputs = {
            "failoverGroupName": "",
            "VirtualizationClient": "",
            "ClientName": "",
            "AgentName": "",
            "InstanceName": ""
        }

    def run(self):
        """Main function for test case execution"""

        # does checks before running the test
        if not isinstance(self._failover_group, FailoverGroup):
            self.log.error(
                "`self._failover_group` is not a `FailoverGroup` object.")
            self.status = constants.FAILED
            return

        # Sub-tests will raise proper exceptions if an error occurs.
        try:
            self._do_unplanned_failover()
            self._do_undo_failover()
        except Exception as exp:
            self.log.error(str(exp))
            self.status = constants.FAILED
            return

        self.status = constants.PASSED