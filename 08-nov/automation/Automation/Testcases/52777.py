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

from cvpysdk.drorchestration.replicationmonitor import ReplicationMonitor

from AutomationUtils import constants
from DROrchestration.cvtestcase_replication_monitor import CVTestCaseReplicationMonitor


class TestCase(CVTestCaseReplicationMonitor):
    """Class for executing Basic acceptance Test of NDMP backup and Restore test case

    This test runs the following things from the Replication Monitor.
    * Runs testboot

    Input:
        "52777": {
            "vmName": "Source VM Name",
            "VirtualizationClient": "Hypervisor Hostname",
            "failoverGroupId": "Failover Group ID"

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
        self.name = "VirtualServer-AdminConsole-ReplicationMonitor-Testboot"
        self.id = "52777"

        # Required input parameters from the input JSON file
        self.tcinputs = {
            "vmName": "",
            "VirtualizationClient": "",
            "failoverGroupId": "",
            "ClientName": "",
            "AgentName": "",
            "InstanceName": ""
        }

    def run(self):
        """Main function for test case execution"""

        # does checks before running the test
        if not isinstance(self._replication_monitor, ReplicationMonitor):
            self.log.error(
                "self.replication_monitor is not a ReplicationMonitor object.")
            self.status = constants.FAILED
            return

        # Sub-tests will raise proper exceptions if an error occurs.
        try:
            self._do_testboot()
        except Exception as exp:
            self.log.error(str(exp))
            self.status = constants.FAILED
            return

        self.status = constants.PASSED
