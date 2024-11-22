# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase to perform AuxCopy with Encryption

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    _cleanup()                  --  cleanup the entities created in this/previous run

    _validate_encryption_on_copy()  --  validates whether encryption flag set on copy extendedFlags in
                                        archgroupcopy table

    _get_archFiles_for_auxjob() --  gets rows for given auxcopy job id that are populated in archchunktoreplicate table

     _validate_aging()          --  validate where mmdeletedaf table entries are cleaned

     _set_prune_process_interval    --  sets config param 'MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS' with interval value

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    tear_down()                 --  teardown function of this test case

Sample JSON:
    "47527": {
        "ClientName": "Name of Client",
        "PrimaryCopyMediaAgent": "Name of Source MA",
        "SecondaryCopyMediaAgent": "Name of Destination MA",
        "AgentName": "File System"
    }
    Note: Both the MediaAgents can be the same machine
"""

import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from MediaAgents.MAUtils.mahelper import (MMHelper, DedupeHelper)


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "AuxCopy with Encryption"
        self.tcinputs = {
            "PrimaryCopyMediaAgent": None,
            "SecondaryCopyMediaAgent": None
        }
        self.options_selector = None
        self.primary_pool_name = None
        self.secondary_pool_name = None
        self.plan_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.pool_name = None
        self.backupset = None
        self.subclient = None
        self.plan = None
        self.primary_mountpath = None
        self.secondary_mountpath = None
        self.primary_partition_path = None
        self.primary_partition_path2 = None
        self.secondary_partition_path = None
        self.secondary_partition_path2 = None
        self.content_path = None
        self.dedupehelper = None
        self.mmhelper = None
        self.common_util = None
        self.primary_ma_machine = None
        self.secondary_ma_machine = None
        self.client_machine = None

    def _validate_encryption_on_copy(self, copy_id):
        """
        validates whether encryption flag set on copy extendedFlags in archgroupcopy table
        Args:
            copy_id (int) -- copy id to validate on
        Return:
            (Bool) True/False
        """

        query = f"select count(1) from archgroupcopy where extendedflags&1024 = 1024 and id = {copy_id}"
        self.log.info("QUERY: {0}".format(query))
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: {0}".format(cur))
        if cur != ['']:
            if int(cur[0]) == 1:
                return True
        return False

    def _get_archFiles_for_auxjob(self, job_id):
        """
            Gets rows for given auxcopy job id that are populated in archchunktoreplicate table
            Args:
                job_id (str) -- AuxCopy job id
            Return:
                list of reader id
        """

        query = f"SELECT COUNT(1) FROM ArchChunkToReplicate WHERE AdminJobId = {job_id}"
        self.log.info(f"QUERY: {query}")
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self._log.info(f"RESULT: {cur[0]}")
        if cur[0] != ['']:
            return int(cur[0])
        self._log.error("Unable to fetch rows for the given job id")
        raise Exception("Unable to fetch rows for the given job id")

    def _validate_aging(self):
        """Validate whether mmdeletedaf, mmdeletedarchfiletracking table entries are cleaned."""
        interval = 0
        flag = 1
        # increasing wait interval for 30 mins as automation setups might have many sidbstores and processing
        # all of them might take time
        while flag and interval < 60*30:
            time.sleep(30)
            interval = interval + 30
            query = f"""SELECT	COUNT(*), DAF.SIDBStoreId
                    FROM	MMDeletedAF DAF WITH (READUNCOMMITTED)
                    JOIN	archGroupCopy AGC 
                            ON DAF.SIDBStoreId = AGC.SIDBStoreId
                    JOIN	archGroup AG
                            ON AG.id = AGC.archGroupId
                    WHERE	AG.name = '{self.pool_name}'
                    GROUP BY DAF.SIDBStoreId"""
            self.log.info(f"QUERY: {query}")
            self.csdb.execute(query)
            archfile_count = self.csdb.fetch_all_rows()
            query = f"""SELECT	COUNT(*), DAF.SIDBStoreId
                    FROM	MMDeletedArchFileTracking DAF WITH (READUNCOMMITTED)
                    JOIN	archGroupCopy AGC
                            ON DAF.SIDBStoreId = AGC.SIDBStoreId
                    JOIN	archGroup AG
                            ON AG.id = AGC.archGroupId
                    WHERE	AG.name = '{self.pool_name}'
                    GROUP BY DAF.SIDBStoreId"""
            self.log.info(f"QUERY: {query}")
            self.csdb.execute(query)
            archfiletracking_count = self.csdb.fetch_all_rows()
            if archfile_count[0][0] == '' and archfiletracking_count[0][0] == '':
                flag = 0
            else:
                if archfile_count[0][0] != '':
                    self.log.info(f"POLL ---- Number of entries for DDB-{archfile_count[0][1]} in mmdeletedaf =[{archfile_count[0][0]}]")
                if archfiletracking_count[0][0] != '':
                    self.log.info(f"POLL ---- Number of entries for DDB-{archfiletracking_count[0][1]} in mmdeletedarchfiletracking =[{archfiletracking_count[0][1]}]")
        if not flag:
            return True
        else:
            return False

    def _set_prune_process_interval(self, value, n_min=10):
        """
        sets config param 'MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS' with interval value
        Args:
            value (int): time in minutes to set as config param value

            n_min (int): minimum value that can be set for this config
        """
        self.log.info(f"Setting pruning process interval to {value}")
        self.mmhelper.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', n_min, value)

    def _cleanup(self):
        """Cleanup the entities created in this/Previous Run"""
        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)

            # Delete backupset
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info(f"Deleting BackupSet: {self.backupset_name} if exists")
                self.backupset = self.agent.backupsets.get(self.backupset_name)
                self.subclient = self.backupset.subclients.get(self.subclient_name)
                if self.backupset.subclients.has_subclient(self.subclient_name):
                    self.subclient.plan = None
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info(f"Deleted BackupSet: {self.backupset_name}")

            # Delete plan
            self.log.info(f"Deleting plan: {self.plan_name} if exists")
            if self.commcell.plans.has_plan(self.plan_name):
                self.commcell.plans.delete(self.plan_name)
                self.log.info(f"Deleted plan: {self.plan_name}")

            # Delete pools
            self.log.info(f"Deleting primary pool: {self.primary_pool_name} if exists")
            if self.commcell.storage_pools.has_storage_pool(self.primary_pool_name):
                self.commcell.storage_pools.delete(self.primary_pool_name)
                self.log.info(f"Deleted primary pool: {self.primary_pool_name}")

            self.log.info(f"Deleting secondary pool: {self.secondary_pool_name} if exists")
            if self.commcell.storage_pools.has_storage_pool(self.secondary_pool_name):
                self.commcell.storage_pools.delete(self.secondary_pool_name)
                self.log.info(f"Deleted secondary pool: {self.secondary_pool_name}")

            self.log.info(f"Deleting pool: {self.pool_name} if exists")
            if self.commcell.storage_pools.has_storage_pool(self.pool_name):
                self.commcell.storage_pools.delete(self.pool_name)
                self.log.info(f"Deleted pool: {self.pool_name}")

            # Run DataAging
            data_aging_job = self.commcell.run_data_aging()
            self.log.info(f"Data Aging job [{data_aging_job.job_id}] has started.")
            if not data_aging_job.wait_for_completion():
                self.log.error(
                    f"Data Aging job [{data_aging_job.job_id}] has failed with {data_aging_job.delay_reason}.")
                raise Exception(
                    "Data Aging job [{0}] has failed with {1}.".format(data_aging_job.job_id,
                                                                       data_aging_job.delay_reason))
            self.log.info(f"Data Aging job [{data_aging_job.job_id}] has completed.")
            self.log.info("********************** CLEANUP COMPLETED *************************")
        except Exception as exp:
            self.log.warning(f"Error encountered during cleanup : {exp}")

    def setup(self):
        """Setup function of this test case"""

        self.options_selector = OptionsSelector(self.commcell)
        self.mmhelper = MMHelper(self)
        self.dedupehelper = DedupeHelper(self)
        self.common_util = CommonUtils(self)
        self.primary_pool_name = f'{self.id}_primary_pool'
        self.secondary_pool_name = f'{self.id}_secondary_pool'
        self.pool_name = f'{self.id}_pool'
        self.plan_name = f'{self.id}_plan'
        self.backupset_name = f'{self.id}_BS'
        self.subclient_name = f'{self.id}_SC'

        self.primary_ma_machine, primary_ma_path = self.mmhelper.generate_automation_path(self.tcinputs['PrimaryCopyMediaAgent'], 25*1024)
        self.secondary_ma_machine, secondary_ma_path = self.mmhelper.generate_automation_path(self.tcinputs['SecondaryCopyMediaAgent'], 25*1024)
        self.client_machine, client_path = self.mmhelper.generate_automation_path(self.tcinputs['ClientName'], 25*1024)

        self.primary_mountpath = self.primary_ma_machine.join_path(primary_ma_path, 'MP')
        self.primary_partition_path = self.primary_ma_machine.join_path(primary_ma_path, 'DDB')
        self.primary_partition_path2 = self.primary_ma_machine.join_path(primary_ma_path, 'DDB2')

        self.secondary_mountpath = self.secondary_ma_machine.join_path(secondary_ma_path, 'MP')
        self.secondary_partition_path = self.secondary_ma_machine.join_path(secondary_ma_path, 'CopyDDB')
        self.secondary_partition_path2 = self.secondary_ma_machine.join_path(secondary_ma_path, 'CopyDDB2')

        self.content_path = self.client_machine.join_path(client_path, 'TestData')

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Cleaning up the entities from older runs")
            self._cleanup()

            # creating primary and secondary storage pools
            self.commcell.storage_pools.add(self.primary_pool_name, self.primary_mountpath, self.tcinputs['PrimaryCopyMediaAgent'],
                                            [self.tcinputs['PrimaryCopyMediaAgent'], self.tcinputs['PrimaryCopyMediaAgent']],
                                            [self.primary_partition_path, self.primary_partition_path2])

            self.commcell.storage_pools.add(self.secondary_pool_name, self.secondary_mountpath, self.tcinputs['SecondaryCopyMediaAgent'],
                                            [self.tcinputs['SecondaryCopyMediaAgent'], self.tcinputs['SecondaryCopyMediaAgent']],
                                            [self.secondary_partition_path, self.secondary_partition_path2])

            self.log.info("Creating plan")
            self.plan = self.commcell.plans.add(self.plan_name, "Server", self.secondary_pool_name)

            # disabling the schedule policy
            self.log.info('Disabling the schedule policy')
            self.plan.schedule_policies['data'].disable()

            # Enable default enc on client
            self.client.set_encryption_property('ON_CLIENT', 'BLOWFISH', '256')

            # create first secondary copy
            copy1 = f'{self.id}_copy1'
            self.log.info("Creating the copy 1")
            self.plan.storage_policy.create_dedupe_secondary_copy(copy1, self.secondary_pool_name, self.tcinputs['SecondaryCopyMediaAgent'],
                                                                  self.secondary_partition_path +
                                                                   self.options_selector.get_custom_str(),
                                                                  self.tcinputs['SecondaryCopyMediaAgent'])

            copy1_obj = self.plan.storage_policy.get_copy(copy1)

            # create second secondary copy
            copy2 = f'{self.id}_copy2'
            self.log.info("Creating the copy 2")
            self.plan.storage_policy.create_dedupe_secondary_copy(copy2, self.secondary_pool_name,
                                                                  self.tcinputs['SecondaryCopyMediaAgent'],
                                                                  self.secondary_partition_path +
                                                                  self.options_selector.get_custom_str(),
                                                                  self.tcinputs['SecondaryCopyMediaAgent'])

            copy2_obj = self.plan.storage_policy.get_copy(copy2)

            # create pool
            self.commcell.storage_pools.add(self.pool_name, self.secondary_mountpath + '2',
                                                                     self.tcinputs['SecondaryCopyMediaAgent'],
                                                                     [self.tcinputs['SecondaryCopyMediaAgent'], self.tcinputs['SecondaryCopyMediaAgent']],
                                                                     [self.secondary_partition_path +
                                                                     self.options_selector.get_custom_str(),
                                                                          self.secondary_partition_path +
                                                                         self.options_selector.get_custom_str()])

            # creating plan copy pointing to pool
            copy3 = f'{self.id}_copy3'
            self._log.info(f"Adding secondary copy pointing to pool: {copy3}")
            self.plan.storage_policy.create_secondary_copy(copy3, self.pool_name, self.tcinputs['SecondaryCopyMediaAgent'])
            self.log.info("Added the secondary copy..")
            copy3_obj = self.plan.storage_policy.get_copy(copy3)

            # Enable parallel copy
            copy3_obj.parallel_copy = True

            # Removing association with System Created Automatic Auxcopy schedule
            self.log.info("Removing association with System Created Autocopy schedule on above created copy")
            self.mmhelper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, copy1)
            self.mmhelper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, copy2)
            self.mmhelper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, copy3)

            # add backupset
            self.log.info(f"Adding the backup set [{self.backupset_name}]")
            self.backupset = self.mmhelper.configure_backupset(self.backupset_name)
            self.log.info(f"Backup set Added [{self.backupset_name}]")

            # add subclient
            self.log.info(f"Adding the subclient set [{self.subclient_name}]")
            self.subclient = self.backupset.subclients.add(self.subclient_name)
            self.log.info(f"Subclient set Added [{self.subclient_name}]")

            # Add plan and content to the subclient
            self.log.info("Adding plan to subclient")
            self.subclient.plan = [self.plan, [self.content_path]]

            # Create unique content
            self.log.info(f"Generating Data at {self.content_path}")
            if not self.client_machine.generate_test_data(self.content_path, dirs=1, file_size=(100 * 1024), files=10):
                self.log.error(f"unable to Generate Data at {self.content_path}")
                raise Exception("unable to Generate Data at {0}".format(self.content_path))
            self.log.info(f"Generated Data at {self.content_path}")

            # Backup Job J1
            job1_obj = self.common_util.subclient_backup(self.subclient, "full")
            time.sleep(60)

            # Backup Job J2
            job2_obj = self.common_util.subclient_backup(self.subclient, "full")
            time.sleep(60)


            # Run Aux copy Job
            auxcopy_job = self.plan.storage_policy.run_aux_copy()
            self.log.info(f"Auxcopy job [{auxcopy_job.job_id}] has started.")
            if not auxcopy_job.wait_for_completion():
                self.log.error(f"Auxcopy job [{auxcopy_job.job_id}] has failed with {auxcopy_job.delay_reason}.")
                raise Exception(f"Auxcopy job [{0}] has failed with {1}.".format(auxcopy_job.job_id,
                                                                                auxcopy_job.delay_reason))
            self.log.info(f"Auxcopy job [{auxcopy_job.job_id}] has completed.")

            # Validating encryption flag set on extendedFlags in archgroupcopy table
            if self._validate_encryption_on_copy(copy3_obj.copy_id):
                self.log.info("Encryption flag set on copy")
            else:
                self.log.error("Encryption flag not set on copy")

            # delete copy created to pool
            self.log.info("Deleting storage policy copy pointed to pool")
            self.plan.storage_policy.delete_secondary_copy(copy3)

            # Recreating SP copy pointing to same pool
            self._log.info(f"Adding secondary copy pointing to same pool: {copy3}")
            self.plan.storage_policy.create_secondary_copy(copy3, self.pool_name, self.tcinputs['SecondaryCopyMediaAgent'])
            copy3_obj = self.plan.storage_policy.get_copy(copy3)

            # Enable parallel copy
            copy3_obj.set_parallel_copy(True)

            # ReRun Aux copy Job
            auxcopy_job = self.plan.storage_policy.run_aux_copy()
            self.log.info(f"Auxcopy job [{auxcopy_job.job_id}] has started.")
            if not auxcopy_job.wait_for_completion():
                self.log.error(f"Auxcopy job [{auxcopy_job.job_id}] has failed with {auxcopy_job.delay_reason}.")
                raise Exception("Auxcopy job [{0}] has failed with {1}.".format(auxcopy_job.job_id,
                                                                                auxcopy_job.delay_reason))
            self.log.info(f"Auxcopy job [{auxcopy_job.job_id}] has completed.")

            # Validating Aux copy job
            self.log.info("Querying ArchChunkToReplicate table to see if entries were created for this auxcopy job")
            if self._get_archFiles_for_auxjob(auxcopy_job.job_id) == 0:
                self.log.info("Successfully skipped archive files for dash aux when present in"
                              "mmdeletedaf table for same storeID")
            else:
                self.log.error("Failed to skipped archive files for dash aux when present in"
                               "mmdeletedaf table for same storeID")
                raise Exception("ERROR   Result:Fail for check to skip archive files for dash aux when present in "
                                "mmdeletedaf table for same storeID")

            # setting prune process interval to 2 mins
            self._set_prune_process_interval(2, 1)

            # Run Granular DataAging
            data_aging_job = self.commcell.run_data_aging(storage_policy_name = self.plan.storage_policy.storage_policy_name,
                                                          is_granular=True, include_all_clients=True)
            self.log.info(f"First Data Aging job [{data_aging_job.job_id}] has started.")
            if not data_aging_job.wait_for_completion():
                self.log.error(
                    f"Data Aging job [{data_aging_job.job_id}] has failed with {data_aging_job.delay_reason}.")
                raise Exception(
                    "Data Aging job [{0}] has failed with {1}.".format(data_aging_job.job_id,
                                                                       data_aging_job.delay_reason))
            self.log.info(f"Data Aging job [{data_aging_job.job_id}] has completed.")
            time.sleep(60)

            # Run Granular DataAging - Second
            data_aging_job = self.commcell.run_data_aging(storage_policy_name = self.plan.storage_policy.storage_policy_name,
                                                          is_granular=True, include_all_clients=True)
            self.log.info(f"Second Data Aging job [{data_aging_job.job_id}] has started.")
            if not data_aging_job.wait_for_completion():
                self.log.error(
                    f"Data Aging job [{data_aging_job.job_id}] has failed with {data_aging_job.delay_reason}.")
                raise Exception(
                    "Data Aging job [{0}] has failed with {1}.".format(data_aging_job.job_id,
                                                                       data_aging_job.delay_reason))
            self.log.info(f"Data Aging job [{data_aging_job.job_id}] has completed.")

            # Validate Aging
            if self._validate_aging():
                self.log.info("Entries in mmdeleteaf, mmdeletedarchfiletracking cleanup succeeded")
            else:
                self.log.error("Entries in mmdeleteaf, mmdeletedarchfiletracking cleanup Failed")
                raise Exception("Entries in mmdeleteaf, mmdeletedarchfiletracking cleanup Failed")

            # Reverting pruning process interval to 60 mins
            self._set_prune_process_interval(60)

            # Picking jobs J1 and J2 for recopy on copy2
            copy2_obj.recopy_jobs(job1_obj.job_id + ", " + job2_obj.job_id)

            # Run Aux copy Job
            auxcopy_job = self.plan.storage_policy.run_aux_copy()
            self.log.info(f"Auxcopy job [{auxcopy_job.job_id}] has started.")
            if not auxcopy_job.wait_for_completion():
                self.log.error(f"Auxcopy job [{auxcopy_job.job_id}] has failed with {auxcopy_job.delay_reason}.")
                raise Exception("Auxcopy job [{0}] has failed with {1}.".format(auxcopy_job.job_id,
                                                                                auxcopy_job.delay_reason))
            self.log.info(f"Auxcopy job [{auxcopy_job.job_id}] has completed.", auxcopy_job.job_id)

            # Validating encryption flag set on extendedFlags in archgroupcopy table
            if self._validate_encryption_on_copy(copy3_obj.copy_id):
                self.log.info("Encryption flag set on copy")
            else:
                self.log.error("Encryption flag not set on copy")

            # Validating Restores from three copies
            #   Restore from copy1
            restore_job = self.subclient.restore_in_place([self.content_path], copy_precedence=2)
            self.log.info(f"restore job [{restore_job.job_id}] has started from [{copy1}].")
            if not restore_job.wait_for_completion():
                self.log.error(f"restore job [{restore_job.job_id}] has failed with {restore_job.delay_reason}.")
                raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                                restore_job.delay_reason))
            self.log.info(f"restore job [{restore_job.job_id}] has completed from [{copy1}].")
            time.sleep(60)


            #   Restore from copy2
            restore_job = self.subclient.restore_in_place([self.content_path], copy_precedence=3)
            self.log.info(f"restore job [{restore_job.job_id}] has started from [{copy2}].")
            if not restore_job.wait_for_completion():
                self.log.error(f"restore job [{restore_job.job_id}] has failed with {restore_job.delay_reason}.")
                raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                                restore_job.delay_reason))
            self.log.info(f"restore job [{restore_job.job_id}] has completed from [{copy2}].")
            time.sleep(60)


            #   Restore from copy3
            restore_job = self.subclient.restore_in_place([self.content_path], copy_precedence=4)
            self.log.info(f"restore job [{restore_job.job_id}] has started from [{copy3}].")
            if not restore_job.wait_for_completion():
                self.log.error(f"restore job [{restore_job.job_id}] has failed with {restore_job.delay_reason}.")
                raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                                restore_job.delay_reason))
            self.log.info(f"restore job [{restore_job.job_id}] has completed from [{copy3}].")

        except Exception as exp:
            self.log.error(f'Failed to execute test case with error: {exp}')
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down function of this test case"""
        # revert back dedupe default setting on client
        self.client.set_dedup_property('clientSideDeduplication', 'USE_SPSETTINGS')

        # Reverting pruning process interval to 60
        self._set_prune_process_interval(60)

        if self.status == constants.FAILED:
            self.log.warning("TC Failed. Please go through the logs for debugging. Cleaning up the entities")
        self._cleanup()
