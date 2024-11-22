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
from VirtualServer.DROrchestration.cvtestcase_replication_monitor \
    import CVTestCaseReplicationMonitor


class TestCase(CVTestCaseReplicationMonitor):
    """Class for executing Basic acceptance Test of NDMP backup and Restore test case

    This test runs the following things on an Azure replication from replication monitor.
    * Runs unplanned failover
    * Runs failback
    * Runs planned failover
    * Runs failback

    Inputs:
        "58072": {
            "vmName": "Source VM Name(s)",
            "failoverGroupId": "Failover Group ID",

            "ClientName": "Hypervisor Name",
            "AgentName": "Agent Name",
            "InstanceName": "Instance Name default: azure resource manager"
        }
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Failover and Failback testcase for VSA Replication"
        self.id = "58072"

        # Required input parameters from the input JSON file
        self.tcinputs = {
            "vmName": [],
            "failoverGroupId": "",
            "ClientName": "",
            "AgentName": "",
            "InstanceName": "azure resource manager"
        }

        # Snapshots are not available in AWS
        self._check_snapshots = False

    def setup(self):
        super(TestCase, self).setup()
        self.tcinputs.update({
            "deleteDestVmFromHypervisor": False
        })

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
            self._do_planned_failover()
            self._do_failback()
            self._do_unplanned_failover()
            self._do_failback()
        except Exception as exp:
            self.log.error(str(exp))
            self.status = constants.FAILED
            return

        self.status = constants.PASSED
