# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
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
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Testcase for  1-touch backup and VMe to Hyper-V

        Please use a 2012R2 and above Hyper-V Host.

    """

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Virtualize me to Hyper-V"
        self.applicable_os = self.os_list.UNIX
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.BMR
        self.show_to_user = False
        self.tcinputs = {
            "HyperVInstance": None,
            "HyperVHost": None,
            "IsoPath": None,
            "Datastore": None,
            "CommServPassword": None,
            "VmName": None,
            "NetworkLabel":None,
            "UseDhcp": None
        }

    def run(self):
        """Runs 1-touch backup and Virtualize me to Hyper-V"""
        try:
            self.helper = FSHelper(self)
            self.controller = Machine()
            FSHelper.populate_tc_inputs(self, mandatory=False)
            self.tcinputs['CommServUsername'] = self.inputJSONnode['commcell']['commcellUsername']
            self.tcinputs['CommServHostname'] = self.inputJSONnode['commcell']['webconsoleHostname']
            self.tcinputs['CommServName'] = self.commcell.commserv_name
            self.tcinputs['CommServIP'] = self.controller.ip_address
            self.log.info("Starting 1-touch backup")
            self.helper.run_onetouch_backup('Incremental')
            self.log.info("Triggering the Virtualize Me Job")
            restore_job = self.backupset.run_bmr_restore(**self.tcinputs)
            self.log.info(
                "Started Virtualize Me to Hyper-V with Job ID: %s", str(
                    restore_job.job_id))
            if restore_job.wait_for_completion():
                self.log.info("Virtualize Me job ran successfully")
            else:
                raise Exception(
                    "Virtualize me job failed with error: {0}".format(
                        restore_job.delay_reason))
            self.log.info("wait for 7 min until server comes up")
            time.sleep(420)
            self.log.info("Checking if the server booted up successfully")
            self.log.info("Starting Check readiness for destination client")
            self.commcell.clients.refresh()
            time.sleep(60)
            dest_machine = self.commcell.clients.get(self.tcinputs['ClientName'])
            try:
                if dest_machine.is_ready:
                    self.result_string = "Destination machine reachable"
                    self.log.info("Destination Machine is reachable ")
                else:
                    raise Exception('CHECK DESTINATION MACHINE')
            except Exception as excp2:
                self.log.error(str(excp2))
                self.result_string = str(excp2)
        except Exception as excp:
            self.log.error(str(excp))
            self.log.error("TEST CASE FAILED")
            self.status = constants.FAILED
            self.result_string = str(excp)
