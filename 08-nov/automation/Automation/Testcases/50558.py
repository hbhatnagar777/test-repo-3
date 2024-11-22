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

from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Testcase for system state backup and Vme to VMware"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "blocklevel Virtualize me to VMWare"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.BMR
        self.show_to_user = False
        self.tcinputs = {
            "vCenterServerName": None,
            "vCenterUsername": None,
            "vCenterPassword ": None,
            "isopath": None,
            "Datastore": None,
            "CS_IP": None,
            "CS_Username": None,
            "CS_Password": None,
            "CS_Hostname": None,
        }
        self.helper = FSHelper(TestCase)

    def run(self):
        """Runs System State backup and Virtualize me to VMWare"""
        try:
            self.helper = FSHelper(self)
            self.log.info("Starting the Blocklevel System state testcase for  backup & Restore")
            FSHelper.populate_tc_inputs(self, mandatory=False)
            self.helper.update_subclient(block_level_backup=1)
            self.log.info("Enabled Blocklevel Option")

            self.helper.run_systemstate_backup('Incremental')
            self.log.info("Triggering the Virtualize Me Job")
            restore_job = self.backupset.run_bmr_restore(**self.tcinputs)
            self.log.info(
                "Started Virtualize Me to VMWare with Job ID: %s", str(
                    restore_job.job_id))
            if not restore_job.wait_for_completion():
                raise Exception(
                    "Virtualize me job failed with error: {0}".format(
                        restore_job.delay_reason))
            else:
                self.log.info("Virtualize Me job ran successfully")
                self.log.info("TEST CASE EXECUTED SUCCESSFULLY")

        except Exception as excp:
            self.log.error(str(excp))
            self.log.error("TEST CASE FAILED")
            self.status = constants.FAILED
            self.result_string = str(excp)
