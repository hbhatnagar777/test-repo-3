# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    run_backup()    --  runs a backup job by generating new content

    compact_ddb()   --  runs sidb compact command for all partitions on store
"""

import os, time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Recon case for compacted DDB - 16 AF per secondary with Suspend and Resume"
        self.tcinputs = {
            "MediaAgentName": None,
            "PathToUse": None,
            "SqlSaPassword": None
        }
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.path = None
        self.content_path = None
        self.ddb_path = None
        self.mount_path = None
        self.dedupehelper = None
        self.mmhelper = None
        self.client_machine = None
        self.db_password = None
        self.library = None
        self.storage_policy = None
        self.backupset = None
        self.subclient = None
        self.copy = None
        self.store = None
        self.primary_recs_before_recon = None
        self.secondary_recs_before_recon = None
        self.primary_recs_after_recon = None
        self.secondary_recs_after_recon = None

    def setup(self):
        """Setup function of this test case"""
        self.library_name = str(self.id) + "_lib"
        self.storage_policy_name = str(self.id) + "_SP"
        self.backupset_name = str(self.id) + "_BS"
        self.subclient_name = str(self.id) + "_SC"
        self.path = os.path.normpath(self.tcinputs["PathToUse"])
        self.content_path = os.path.join(self.path, "content")
        self.ddb_path = os.path.join(self.path, "DDB")
        self.mount_path = os.path.join(self.path, "MP")
        self.dedupehelper = DedupeHelper(self)
        self.mmhelper = MMHelper(self)
        self.client_machine = Machine(self.tcinputs["ClientName"], self.commcell)
        self.db_password = self.tcinputs['SqlSaPassword']

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Started executing %s testcase", self.id)

            self.log.info(self.name)

            # create library, dedupe sp, backupset and subclient
            self.library = self.mmhelper.configure_disk_library(self.library_name,
                                                                self.tcinputs["MediaAgentName"],
                                                                self.mount_path)

            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.log.info("Deleting storage policy %s", self.storage_policy_name)
                self.commcell.storage_policies.delete(self.storage_policy_name)

            self._log.info("Creating new Storage Policy %s", self.storage_policy_name)
            self.storage_policy = self.dedupehelper.configure_dedupe_storage_policy(
                self.storage_policy_name,
                self.library_name,
                self.tcinputs["MediaAgentName"],
                self.ddb_path)

            self.backupset = self.mmhelper.configure_backupset(self.backupset_name, self.agent)

            self.subclient = self.mmhelper.configure_subclient(self.backupset_name,
                                                               self.subclient_name,
                                                               self.storage_policy_name,
                                                               self.content_path,
                                                               self.agent)

            self.copy = self.storage_policy.get_copy('Primary')
            self.copy.copy_retention = (1, 0, 1)

            self.store = self.dedupehelper.get_sidb_ids(self.storage_policy.storage_policy_id,
                                                        'Primary')

            # update 16 AFs per secondary
            if len(self.store) == 2:
                self.log.info("Setting MaxNumOfAFsInSecFile=16 on IdxSidbSubStore...")
                query = """
                        IF NOT EXISTS (SELECT 1 FROM idxsidbsubstore WHERE maxnumofafsinsecfile=16
                        AND sidbstoreid={0} AND substoreid={1})
                        BEGIN
                        UPDATE IdxSidbSubStore
                        SET MaxNumOfAFsInSecFile = 16
                        WHERE SIDBStoreId = {0} and SubStoreId = {1}
                        END""".format(self.store[0], self.store[1])
                self.log.info("QUERY: %s", query)
                self.mmhelper.execute_update_query(query, self.db_password)
            else:
                raise Exception("expecting a store with single partition")

            # run backups
            for i in range(3):
                self.run_backup('FULL', size=0.5)

            #Make sure that ddb process is not running
            # STEP:Get DDB MA for the given DDB Store
            ddbma_dict = self.dedupehelper.get_ddb_partition_ma(self.store[0])

            for partition in ddbma_dict:
                ddbma_obj = ddbma_dict[partition]
                self.log.info("Check if SIDB is running on %s for engine id %s partition %s",
                          ddbma_dict[partition].client_name,
                          self.store[0], partition)
                if not self.dedupehelper.wait_till_sidb_down(self.store[0], ddbma_obj):
                    self.log.error("SIDBEngine is not down even after timeout of 600 seconds")
                    raise Exception("SIDBEngine not down even after timeout. Returning Failure.")


            # Compact ddb
            self.compact_ddb(self.store[0])

            self.log.info("make sure that store is set to 1 AF per secondary after compacting")
            query = """select MaxNumOfAFsInSecFile from IdxSIDBSubStore
            where SIDBStoreId= {0} and SubStoreId = {1}""".format(self.store[0], self.store[1])
            self._log.info("QUERY : %s", query)
            self.csdb.execute(query)
            cur = self.csdb.fetch_one_row()
            self._log.info("RESULT: %s", str(cur[0]))
            if int(cur[0]) != 1:
                raise Exception("store is not set to 1 AF per secondary.")
            else:
                self.log.info("Store correctly set to 1 AF per secondary.")

            # run more backups after compaction
            for i in range(3):
                self.run_backup('FULL', size=0.5)

            self.log.info("Waiting for 60 seconds for IdxSIDBUsageHistory table updates to happen")
            time.sleep(60)

            # Note primary and secondary recs count
            self.primary_recs_before_recon = self.dedupehelper.get_primary_recs_count(self.store[0], self.db_password)
            self.secondary_recs_before_recon = self.dedupehelper.get_secondary_recs_count(self.store[0],
                                                                                          self.db_password)

            for partition in ddbma_dict:
                ddbma_obj = ddbma_dict[partition]
                self.log.info("Check if SIDB is running on %s for engine id %s partition %s",
                          ddbma_dict[partition].client_name,
                          self.store[0], partition)
                if not self.dedupehelper.wait_till_sidb_down(self.store[0], ddbma_obj):
                    self.log.error("SIDBEngine is not down even after timeout of 600 seconds")
                    raise Exception("SIDBEngine not down even after timeout. Returning Failure.")

            # mark store corrupt
            self.log.info("marking store[%s] substore[%s] for recovery", self.store[0], self.store[1])
            self.storage_policy.mark_for_recovery(self.store[0], self.store[1],
                                                  self.tcinputs['MediaAgentName'], self.ddb_path)
            # run recon
            self.log.info("Starting Full recon...")
            self.storage_policy.run_recon('Primary', self.storage_policy.storage_policy_name, self.store[0],
                                          full_reconstruction=1)
            recon_job = self.dedupehelper.poll_ddb_reconstruction(self.storage_policy.storage_policy_name,
                                                                  'Primary', no_wait=True)

            # check job in add records phase > suspend
            for i in range(120):
                if recon_job.phase == 'Add Records':
                    self.log.info("Suspending recon job: %s in 10 secs", recon_job.job_id)
                    time.sleep(10)
                    recon_job.pause()
                    break
                time.sleep(10)
            else:
                raise Exception("add records phase for recon job %s did not start in 20 mins.", recon_job.job_id)

            # resume recon and wait to complete
            for i in range(60):
                if recon_job.status == 'Suspended':
                    self.log.info("Resuming recon job...")
                    recon_job.resume()
                    if not recon_job.wait_for_completion():
                        raise Exception("Failed to run recon job {0} backup with error: {1}".format(
                            recon_job.job_id, recon_job.delay_reason))
                    break
                time.sleep(10)
            else:
                raise Exception("recon job {0} did not suspend in 10 mins.".format(recon_job.job_id))
            self.log.info("Recon job completed.")

            self.log.info("Waiting for 60 seconds for IdxSIDBUsageHistory table updates to happen")
            time.sleep(60)

            self.primary_recs_after_recon = self.dedupehelper.get_primary_recs_count(self.store[0], self.db_password)
            self.secondary_recs_after_recon = self.dedupehelper.get_secondary_recs_count(self.store[0],
                                                                                         self.db_password)

            self.log.info("validate: pri_before:%s = pri_after:%s", self.primary_recs_before_recon,
                          self.primary_recs_after_recon)
            if self.primary_recs_before_recon == self.primary_recs_after_recon:
                self.log.info("Pass")
            else:
                self.log.error("Fail!")
                raise Exception("primary records before and after full recon - do not match")

            self.log.info("validate: sec_before:%s = sec_after:%s", self.secondary_recs_before_recon,
                          self.secondary_recs_after_recon)
            if self.secondary_recs_before_recon == self.secondary_recs_after_recon:
                self.log.info("Pass")
            else:
                self.log.error("Fail!")
                raise Exception("secondary records before and after full recon - do not match")

            # run data aging to keep the sp from consuming more space
            try:
                self.commcell.run_data_aging('Primary', self.storage_policy_name)
            except Exception as exp:
                pass

        except Exception as exp:
            self._log.error('Failed to execute test case with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        # clean up > remove content
        self.client_machine.remove_directory(os.path.join(self.content_path, r'*'))
        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.log.info("Deleting backupset %s", self.backupset_name)
            self.agent.backupsets.delete(self.backupset_name)
        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.commcell.storage_policies.delete(self.storage_policy_name)


    def run_backup(self, backup_type="FULL", size=1.0):
        """
        this function runs backup by generating new content to get unique blocks for dedupe backups
        Args:
            backup_type (str): type of backup to run
            size (int): size of backup content to generate

        Returns:
        (object) -- returns job object to backup job
        """
        # add content
        self.client_machine.remove_directory(os.path.join(self.content_path, r'*'))
        self.mmhelper.create_uncompressable_data(self.tcinputs["ClientName"],
                                                 self.content_path, size)
        self._log.info("Running %s backup...", backup_type)
        job = self.subclient.backup(backup_type)
        self._log.info("Backup job: %s", job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup with error: {1}".format(backup_type, job.delay_reason)
            )
        self._log.info("Backup job completed.")
        return job

    def compact_ddb(self, store):
        """
        this method runs sidb compact command for each partition on store
        Args:
            store: store id where sidb command needs to be run

        """
        # STEP:Get DDB MA for the given DDB Store
        ddbma_dict = self.dedupehelper.get_ddb_partition_ma(store)

        # Run sidb compact CLI for each partition for given SP
        for partition in ddbma_dict:
            self.log.info("Following DDB MA has been chosen for executing sidb2 compact %s",
                          ddbma_dict[partition].client_name)
            ddbma_obj = ddbma_dict[partition]
            # Note: Make sure that SIDB2 process with this engine_id is not running
            self.dedupehelper.execute_sidb_command('compactfile secondary', store, partition, ddbma_obj)
        self.log.info("done running sidb compact!")