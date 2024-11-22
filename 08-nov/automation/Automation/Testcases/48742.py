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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
"""
import time
import os
from AutomationUtils.machine import Machine
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import database_helper
from MediaAgents.MAUtils.mahelper import DedupeHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "dedupe MemDB recon case"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.MEDIAAGENT
        self.feature = self.features_list.DEDUPLICATION
        self.show_to_user = True
        self.tcinputs = {
            "MediaAgentUsername": None,
            "MediaAgentPassword": None,
            "MediaAgentName": None,
            "MountPath": None,
            "DedupeStorePath": None,
            "ContentPath": None,
            "RestorePath": None,
            "CSUserName": None,
            "CSPassword": None
        }

    def setup(self):
        """Setup function of this test case"""
        self._log = logger.get_log()

    def run(self):
        """Run function of this test case"""
        try:
            self._log.info("Started executing {0} testcase".format(self.id))
            libraryName = str(self.id) + "_lib"
            self.storagePolicyName = str(self.id) + "_SP"
            backupsetName = str(self.id) + "_BS"
            subclientName = str(self.id) + "_SC"
            self._csdb = database_helper.CommServDatabase(self._commcell)
            self._log.info(self.name)

            self._log.info("********* previous run cleaning up ***********")
            try:
                self._agent.backupsets.delete(backupsetName)
                self.commcell.storage_policies.delete(self.storagePolicyName)
            except:
                self._log.info("previous run(if any) cleanup errors")
                pass

            try:
                drive = os.path.splitdrive(self.tcinputs["ContentPath"])[0]
                testdata = os.path.join(drive, '\\48742data')
                client_machine = Machine(self.tcinputs["ClientName"], self.commcell)
                if not os.path.exists(testdata):
                    client_machine.create_directory(testdata)
                client_machine.generate_test_data(self.tcinputs["ContentPath"], 3, 100)
            except:
                self._log.info("Unable to create addition test data")
                pass

            # create library
            self._log.info("check library: " + libraryName)
            if not self.commcell.disk_libraries.has_library(libraryName):
                self._log.info("adding Library...")
                self.commcell.disk_libraries.add(
                    libraryName,
                    self.tcinputs["MediaAgentName"],
                    self.tcinputs["MountPath"],
                    self.tcinputs["MediaAgentUsername"],
                    self.tcinputs["MediaAgentPassword"])
            else:
                self._log.info("Library exists!")
            self._log.info("Library Config done.")

            # create SP
            self._log.info("check SP: " + self.storagePolicyName)
            if not self.commcell.storage_policies.has_policy(
              self.storagePolicyName):
                self._log.info("adding Storage policy...")
                self.commcell.storage_policies.add(
                    self.storagePolicyName,
                    libraryName,
                    self.tcinputs["MediaAgentName"],
                    self.tcinputs["DedupeStorePath"]+str(time.time()))
            else:
                self._log.info("Storage policy exists!")
            self._log.info("Storage policy config done.")

            # enable MemDB
            self._log.info("Enabling MemDB...")
            self.storage_policy = self.commcell.storage_policies.get(self.storagePolicyName)
            self.storage_policy.update_transactional_ddb(
                True, 'Primary', self.tcinputs['MediaAgentName'])
            self._log.info("MemDB enabled.")

            # create BS
            self._log.info("check BS: " + backupsetName)
            if not self._agent.backupsets.has_backupset(backupsetName):
                self._log.info("adding Backupset...")
                self._agent.backupsets.add(backupsetName)
            else:
                self._log.info("Backupset exists!")
            self._log.info("Backupset config done.")

            # create SC
            self._log.info("check SC: "+subclientName)
            self._log.info("creating backupset object: "+backupsetName)
            self._backupset = self._agent.backupsets.get(backupsetName)
            if not self._backupset.subclients.has_subclient(subclientName):
                self._log.info("adding Subclient...")
                self._subclient = self._backupset.subclients.add(
                    subclientName, self.storagePolicyName)
            else:
                self._log.info("Subclient exists!")

            # add subclient content
            self._log.info("creating subclient object: " + subclientName)
            self._subclient = self._backupset.subclients.get(subclientName)
            self._log.info("setting subclient content to: " + str(
                [self.tcinputs["ContentPath"]]))
            self._subclient.content = [self.tcinputs["ContentPath"]]
            self._log.info("Subclient config done.")

            # enable encyption
            self._log.info("enabling encryption on client")
            self.client.set_encryption_property("ON_CLIENT", key="2", key_len="256")
            self._log.info("enabling encryption on client: Done")

            # initialize dedupehelper class
            dedupe = DedupeHelper(self)

            # Run FULL backup
            self._log.info("Running full backup...")
            for iterator in range(1, 3):
                job = self._subclient.backup("FULL")
                self._log.info("Backup job: " + str(job.job_id))
                if not job.wait_for_completion():
                    raise Exception(
                       "Failed to run FULL backup with error: {0}".format(
                           job.delay_reason))
                self._log.info("Backup job completed.")

            client_machine = Machine(self.tcinputs["ClientName"], self.commcell)
            client_machine.generate_test_data(self.tcinputs["ContentPath"],dirs=1, file_size = 1000, files=5000)


            backup_job, recon_job = dedupe.submit_backup_memdb_recon(
                self._subclient,
                self.storagePolicyName,
                'Primary',
                30)
            if recon_job.job_id == 0:
                raise Exception(
                    "Error while running backup and delta recon."
                )

            self._log.info("*** Validation ***")
            error_flag = []
            self._log.info("CASE 1: IS DELTA RECON? RECONLEVEL == 1")
            reconType = dedupe.get_reconstruction_type(recon_job.job_id)
            if reconType:
                self._log.info("result: Pass")
            else:
                self._log.error("result: Fail")
                error_flag += ["recon level invalid"]

            log_file = "LibraryOperation.log"
            self._log.info("CASE 2: DID RECON VALIDATION SKIP?")
            (matched_line, matched_string) = dedupe.parse_log(
                self.client.client_hostname,
                log_file,
                "Skip Pruning phase and go to DDB verify",
                recon_job.job_id)
            if matched_line:
                self._log.info("Result :Pass")
            else:
                self._log.error("Result: Failed")
                error_flag += ["failed to find: Skip Pruning phase and go to"
                               + "DDB verify"]

            if error_flag:
                raise Exception(
                    error_flag
                )

            self._log.info("running restore job")
            restorejob = self._subclient.restore_out_of_place(
                self.tcinputs["MediaAgentName"],
                self.tcinputs["RestorePath"],
                [self.tcinputs["ContentPath"]], True, True)
            self._log.info("Restore job: " + restorejob.job_id)
            if not restorejob.wait_for_completion():
                raise Exception(
                    "Failed to run FULL backup with error: {0}".format(
                        restorejob.delay_reason))
            self._log.info("restore job completed")

            # cleanup
            try:
                self._log.info("********* cleaning up ***********")
                self._agent.backupsets.delete(backupsetName)
                self.commcell.storage_policies.delete(self.storagePolicyName)
            except Exception:
                self._log.info("something went wrong while cleanup.")
                pass

        except Exception as exp:
            self._log.error('Failed to execute test case with error: '
                            + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        pass
