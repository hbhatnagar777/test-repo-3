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

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Testcase for system state backup and VMe to Hyper-V

        Please use a 2016 and above Hyper-V Host.

    """

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Virtualize me to Hyper-V"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.BMR
        self.show_to_user = False
        self.tcinputs = {
            "VirtualizationClient": None,
            "HyperVHost": None,
            "IsoPath": None,
            "Datastore": None,
            "VmName": None,
            "StoragePolicyName":None,
            "NetworkLabel":None,
            "GuestUser": None,
            "GuestPassword": None
        }

    def run(self):
        """Runs System State backup and Virtualize me to Hyper-V"""
        try:
            self.helper = FSHelper(self)
            FSHelper.populate_tc_inputs(self, mandatory=False)
            self.log.info("Creating a backupset")
            backupset_name = "Test_48744"
            self.helper.create_backupset(backupset_name, delete=False)
            self.helper.create_subclient("default", self.tcinputs['StoragePolicyName'], ["\\"])
            self.helper.update_subclient(storage_policy=self.tcinputs['StoragePolicyName'])
            self.log.info("Starting the System state backup")
            self.helper.run_systemstate_backup('Incremental', wait_to_complete=True)
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

            self.hypervhost_machine = Machine(self.tcinputs['HyperVHost'], self._commcell)
            output = self.helper.bmr_verify_hyperv(self.tcinputs['VmName'], self.tcinputs['GuestUser'],
                                                   self.tcinputs['GuestPassword'])


        except Exception as excp:
            self.log.error(str(excp))
            self.log.error("TEST CASE FAILED")
            self.status = constants.FAILED
            self.result_string = str(excp)
