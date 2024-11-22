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
    __init__()            --  initialize TestCase class

    setup()               --  setup function of this test case

    cleanup()       --  cleanup the entities created in this/previous run

    create_non_dedup_entities()     --  create entities required to perform non-dedupe operations.

    create_dedup_entities()     --  create entities required to perform dedupe operations.

    configure_env()    --      creation of entities

    non_dedup_backup_jobs()     --      performs non-dedup backup jons

    dedup_backup_jobs()     --      performs dedup backup jobs

    dedup_aux_copy_job()    --      performs dedup aux copy job

    non_dedup_restore()     --      performs restore from non-dedup pool copy

    dedup_restores()        --      performs restore from dedup pool copies

    verify_chunks_present_or_not()    --    verifies if the chunks present or not

    check_pruning_completion_status()   --  checks if the pruning is completed or not from log files for dedup

    physical_verification_of_chunks()   --  verifies if the chunks present or not physically.

    run()                 --  run function of this test case

    run_backup()          -- runs the backup of specified type

    tear_down()           --  tear down function of this test case

Inputs to be passed in JSON File:
    "70357": {
        "ClientName": "Name of client",
        "AgentName": "File System",
        "PrimaryCopyMediaAgent":"MA to host Primary Copy",
        "SecondaryCopyMediaAgent":"MA to host Secondary Copy",
        "S3CloudBucket": "cloud bucket",
        "S3Region": "cloud region",
        "S3AccessKey": "cloud access key",
        "S3SecretKey": "cloud secret key",
        "CloudVendor": "cloud vendor"
        ***************OPTIONAL******************
        "dedup_path": "path where dedup store to be created",
        "copy_dedup_path": "path where dedup store to be created for auxcopy",
    }
    ************************         NOTE:         ***************************
    *************************************************************************************
    ** 1. BOTH THE MEDIA AGENTS CAN BE SAME                                   **
    *************************************************************************************

Steps:

1: Configure the environment: create a backupset,
                                (storage, plan, subclient1) for non-dedup,
                                (storage, plan, subclient2, secondary-copy) for dedup
2: Run Backups on the subclient1 and subclient2 in order: F_I_I_F_SF

3: Run AuxCopy on pool created for dedup.

4: Restore from primary copy of th pool created for non-dedupe
    Restore from primary and secondary copy of pool created for dedupe

5: CleanUp the environment

6: Perform data aging.

7: Verification of physical deletion of non-dedup chunks after pruning

8: Verification of physical deletion of dedup chunks after pruning
"""
import copy
import time
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = 'MM SMOKE TEST'
        self.tcinputs = {
            "AgentName": None,
            "ClientName": None,
            "PrimaryCopyMediaAgent": None,
            "SecondaryCopyMediaAgent": None
        }
        self.mm_helper = None
        self.ma_machine_1 = None
        self.ma_machine_2 = None
        self.dedupe_helper = None
        self.client_machine = None
        self.ddb_path = None
        self.ddb_path_2 = None
        self.copy_ddb_path = None
        self.copy_ddb_path_2 = None
        self.ma_1_path = None
        self.ma_2_path = None
        self.non_ddb_mount_path = None
        self.mount_path = None
        self.client_path = None
        self.mount_path_2 = None
        self.content_path = None
        self.nonDDBContentPath = None
        self.restore_path = None
        self.restore_path_primary = None
        self.restore_path_secondary = None
        self.non_dedupe_restore_path = None
        self.cloud_library = None
        self.subclient = None
        self.non_dedup_subclient = None
        self.backupset = None
        self.plan = None
        self.non_dedupe_plan = None
        self.copy_name = None
        self.pool_name = None
        self.non_dedupe_plan_name = None
        self.cloud_pool_name = None
        self.cloud_pool = None
        self.non_dedupe_pool_name = None
        self.container_name = None
        self.subclient_name = None
        self.non_dedup_subclient_name = None
        self.backupset_name = None
        self.plan_name = None
        self.result_string = ""
        self.backup_set_created = False
        self.non_dedupe_entities_created = False
        self.non_dedupe_backup_success = False
        self.non_dedupe_restore_success = False
        self.dedup_entities_created = False
        self.dedup_backup_success = False
        self.dedup_aux_copy_created = False
        self.dedup_aux_copy_success = False
        self.dedup_restore_success = False
        self.dedup_aux_copy_restore_success = False
        self.is_user_defined_dedup = None
        self.is_user_defined_copy_dedup = None
        self.non_dedup_copy_id = None
        self.dedup_copy_id = None
        self.sidb_store_id = None
        self.non_dedup_jobs_chunk_dirs = []
        self.dedup_jobs_chunk_dirs = []
        self.data_aging_job = None

    def setup(self):
        """Setup function of this test case"""
        self.client_machine = Machine(self.tcinputs['ClientName'], self.commcell)
        self.ma_machine_1 = Machine(self.tcinputs['PrimaryCopyMediaAgent'], self.commcell)
        self.ma_machine_2 = Machine(self.tcinputs['SecondaryCopyMediaAgent'], self.commcell)
        utility = OptionsSelector(self.commcell)

        if self.tcinputs.get('dedup_path'):
            self.is_user_defined_dedup = True

        if self.tcinputs.get('copy_dedup_path'):
            self.is_user_defined_copy_dedup = True

        client_drive = utility.get_drive(self.client_machine, 15 * 1024)
        primary_ma_drive = utility.get_drive(self.ma_machine_1, 15 * 1024)
        secondary_ma_drive = utility.get_drive(self.ma_machine_2, 15 * 1024)

        if not self.is_user_defined_dedup and "unix" in self.ma_machine_1.os_info.lower():
            self.log.error(f"LVM enabled dedup path must be input for Source Copy Unix MA [{self.tcinputs['PrimaryCopyMediaAgent']}]!..")
            raise Exception(f"LVM enabled dedup path not supplied for Source Copy Unix MA [{self.tcinputs['PrimaryCopyMediaAgent']}]!..")

        if not self.is_user_defined_copy_dedup and "unix" in self.ma_machine_2.os_info.lower():
            self.log.error(f"LVM enabled dedup path must be input for Destination Copy Unix MA [{self.tcinputs['SecondaryCopyMediaAgent']}]!..")
            raise Exception(f"LVM enabled dedup path not supplied for Destination CopyUnix MA [{self.tcinputs['SecondaryCopyMediaAgent']}]!..")

        self.client_path = self.client_machine.join_path(client_drive, 'test_' + str(self.id))
        self.ma_1_path = self.ma_machine_1.join_path(primary_ma_drive, 'test_' + str(self.id))
        self.ma_2_path = self.ma_machine_2.join_path(secondary_ma_drive, 'test_' + str(self.id))

        self.non_ddb_mount_path = self.ma_machine_1.join_path(self.ma_1_path, 'NonDDB_MP')

        if not self.is_user_defined_dedup:
            self.ddb_path = self.ma_machine_1.join_path(self.ma_1_path, 'DDB')
            self.ddb_path_2 = self.ma_machine_1.join_path(self.ma_1_path, 'DDB_2')
        else:
            parent_ddb_path = self.tcinputs.get('dedup_path')
            self.ddb_path = self.ma_machine_1.join_path(parent_ddb_path, "Dedup_Path_1")
            self.log.info("Using custom dedup path partition 1 for Primary Copy : %s", self.ddb_path)
            self.ddb_path_2 = self.ma_machine_1.join_path(parent_ddb_path, "Dedup_Path_2")
            self.log.info("Using custom dedup path partition 2 for Primary Copy : %s", self.ddb_path_2)

        if not self.is_user_defined_copy_dedup:
            self.copy_ddb_path = self.ma_machine_2.join_path(self.ma_2_path, 'CopyDDB')
            self.copy_ddb_path_2 = self.ma_machine_2.join_path(self.ma_2_path, 'CopyDDB_2')
        else:
            parent_copy_ddb_path = self.tcinputs.get('copy_dedup_path')
            self.copy_ddb_path = self.ma_machine_2.join_path(parent_copy_ddb_path, "Copy_DDB_Partition_1")
            self.log.info("Using custom dedup path partition 1 for Secondary Copy : %s", self.copy_ddb_path)
            self.copy_ddb_path_2 = self.ma_machine_2.join_path(parent_copy_ddb_path, "Copy_DDB_Partition_2")
            self.log.info("Using custom dedup path partition 2 for Secondary Copy : %s", self.copy_ddb_path_2)

        self.mount_path = self.ma_machine_1.join_path(self.ma_1_path, 'MP')
        self.mount_path_2 = self.ma_machine_2.join_path(self.ma_2_path, 'MP2')

        self.content_path = self.client_machine.join_path(self.client_path, 'Content')
        self.nonDDBContentPath = self.client_machine.join_path(self.client_path, 'NonDDBContent')

        self.restore_path = self.client_machine.join_path(self.client_path, 'Restores')
        self.restore_path_primary = self.client_machine.join_path(self.restore_path, 'PrimaryRestore')
        self.restore_path_secondary = self.client_machine.join_path(self.restore_path, 'SecondaryRestore')
        self.non_dedupe_restore_path = self.client_machine.join_path(self.restore_path, 'NonDedupStorageRestore')

        self.copy_name = str(self.id) + '_Copy'
        self.pool_name = str(self.id) + '_Pool'
        self.cloud_pool_name = str(self.id) + '_CloudPool'
        self.non_dedupe_pool_name = str(self.id) + '_NonDedupPool'
        self.container_name = str(self.id) + '_Container'
        self.backupset_name = str(self.id) + '_BS'
        self.subclient_name = str(self.id) + '_SC'
        self.non_dedup_subclient_name = str(self.id) + '_NonDedupSC'
        self.non_dedupe_plan_name = str(self.id) + '_NonDedupPlan'
        self.plan_name = str(self.id) + '_Plan'
        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

    def cleanup(self):
        """Cleans Up the Entities created in the TC"""
        try:
            self.log.info("****************************** Cleanup Started ******************************")
            self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
            self.mm_helper.remove_content(self.nonDDBContentPath, self.client_machine, suppress_exception=True)
            self.mm_helper.remove_content(self.restore_path, self.client_machine, suppress_exception=True)
            self.mm_helper.remove_content(self.non_dedupe_restore_path, self.client_machine, suppress_exception=True)

            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.backupset = self.agent.backupsets.get(self.backupset_name)
                if self.backupset.subclients.has_subclient(self.subclient_name):
                    self.subclient = self.backupset.subclients.get(self.subclient_name)
                    self.subclient.plan = None
                if self.backupset.subclients.has_subclient(self.non_dedup_subclient_name):
                    self.non_dedup_subclient = self.backupset.subclients.get(self.non_dedup_subclient_name)
                    self.non_dedup_subclient.plan = None
                self.log.info("Deleting backupset %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)

            if self.commcell.plans.has_plan(self.non_dedupe_plan_name):
                self.log.info("Deleting plan  %s", self.non_dedupe_plan_name)
                self.commcell.plans.delete(self.non_dedupe_plan_name)

            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info("Deleting plan  %s", self.plan_name)
                self.commcell.plans.delete(self.plan_name)

            if self.commcell.disk_libraries.has_library(self.cloud_pool_name):
                self.log.info("Deleting cloud library  %s", self.cloud_pool_name)
                self.commcell.disk_libraries.delete(self.cloud_pool_name)

            if self.commcell.storage_pools.has_storage_pool(self.non_dedupe_pool_name):
                self.log.info("Deleting pool  %s", self.non_dedupe_pool_name)
                self.commcell.storage_pools.delete(self.non_dedupe_pool_name)

            if self.commcell.storage_pools.has_storage_pool(self.pool_name):
                self.log.info("Deleting pool  %s", self.pool_name)
                self.commcell.storage_pools.delete(self.pool_name)

            self.log.info('****************************** Cleanup Completed ******************************')
        except Exception as exe:
            self.result_string += f'Error in Cleanup Reason: {exe} \n'
            self.status = constants.FAILED
            self.log.error(f'Error in Cleanup Reason: {exe}')

    def create_non_dedup_entities(self):
        """ create entities required to perform non-dedupe operations. """
        try:
            # creating a non-dedup storage pool
            self.log.info("Creating content in non Dedup Content Path")
            self.mm_helper.create_uncompressable_data(self.tcinputs['ClientName'],
                                                      self.nonDDBContentPath, 0.2)

            self.log.info(f"Creating the non dedupe pool [{self.non_dedupe_pool_name}]")
            self.commcell.storage_pools.add(self.non_dedupe_pool_name, self.non_ddb_mount_path,
                                            self.tcinputs['PrimaryCopyMediaAgent'])
            self.log.info(f"Non dedupe pool [{self.non_dedupe_pool_name}] Created.")

            self.log.info(f"Creating the Plan [{self.non_dedupe_plan_name}] for non dedupe storage")
            self.commcell.plans.refresh()
            self.non_dedupe_plan = self.commcell.plans.add(self.non_dedupe_plan_name, "Server",
                                                           self.non_dedupe_pool_name)
            self.log.info(f"Plan [{self.non_dedupe_plan}] created")

            self.log.info("Setting encryptions on non-dedup primary copy")
            non_dedup_copy = self.non_dedupe_plan.storage_policy.get_copy(copy_name="primary")
            non_dedup_copy.set_encryption_properties(re_encryption=True, encryption_type="BlowFish", encryption_length=128)

            self.non_dedup_copy_id = self.mm_helper.get_copy_id(self.non_dedupe_plan.storage_policy.storage_policy_name, "Primary")

            self.log.info('Disabling the schedule policy')
            self.non_dedupe_plan.schedule_policies['data'].disable()

            # add subclient for non dedup storage
            self.log.info(f"Adding the subclient [{self.non_dedup_subclient_name}]")
            self.non_dedup_subclient = self.backupset.subclients.add(self.non_dedup_subclient_name)
            self.log.info(f"Subclient Added [{self.non_dedup_subclient_name}]")

            # adding non dedup plan and content path to non dedup subclient
            self.log.info("Adding non dedup plan to nonDedup subclient")
            self.non_dedup_subclient.plan = [self.non_dedupe_plan, [self.nonDDBContentPath]]

            self.non_dedupe_entities_created = True
            self.result_string += 'CASE 1: Non Dedup Entities Created. \n'
        except Exception as exe:
            error = f'CASE 1: Non Dedup Entities Creation Failed Reason: {exe} \n'
            self.result_string += error
            self.status = constants.FAILED
            self.log.error(error)

    def create_dedup_entities(self):
        """ create entities required to perform dedupe operations. """
        try:
            # 1: Configure the environment
            self.mm_helper.create_uncompressable_data(self.tcinputs['ClientName'],
                                                      self.content_path, 0.25)

            self.log.info(f"Creating the pool [{self.pool_name}]")
            self.commcell.storage_pools.add(self.pool_name, self.mount_path,
                                            self.tcinputs['PrimaryCopyMediaAgent'],
                                            [self.tcinputs['PrimaryCopyMediaAgent'],
                                             self.tcinputs['PrimaryCopyMediaAgent']],
                                            [self.ddb_path, self.ddb_path_2])
            self.log.info(f"Pool [{self.pool_name}] Created.")

            # Create a cloud library
            self.log.info("Creating a cloud library.")
            self.cloud_pool = self.mm_helper.configure_cloud_library(self.cloud_pool_name,
                                                                     self.tcinputs['SecondaryCopyMediaAgent'],
                                                                     self.tcinputs["S3CloudBucket"],
                                                                     self.tcinputs["S3Region"] +
                                                                     "//" +
                                                                     self.tcinputs["S3AccessKey"],
                                                                     self.tcinputs["S3SecretKey"],
                                                                     self.tcinputs["CloudVendor"])
            self.log.info("Created a cloud library.")

            self.commcell.storage_pools.refresh()
            self.commcell.plans.refresh()

            # creation of plan
            self.log.info(f"Plan Present: {self.commcell.plans.has_plan(self.plan_name)}")
            self.log.info(f"Creating the Plan [{self.plan_name}]")
            self.plan = self.commcell.plans.add(self.plan_name, "Server", self.pool_name)
            self.log.info(f"Plan [{self.plan_name}] created")

            self.dedup_copy_id = self.mm_helper.get_copy_id(self.plan.storage_policy.storage_policy_name, "Primary")

            self.sidb_store_id = self.dedupe_helper.get_sidb_ids(self.plan.storage_policy.storage_policy_id, "Primary", True)[0][0]

            if self.plan.storage_policy.has_copy(self.copy_name):
                self.plan.storage_policy.delete_secondary_copy(self.copy_name)

            # disabling the schedule policy
            self.log.info('Disabling the schedule policy')
            self.plan.schedule_policies['data'].disable()

            self.log.info("Setting encryptions on dedup primary copy")
            dedup_primary_copy = self.plan.storage_policy.get_copy(copy_name="primary")
            dedup_primary_copy.set_encryption_properties(re_encryption=True, encryption_type="BlowFish", encryption_length=128)

            # add subclient
            self.log.info(f"Adding the subclient set [{self.subclient_name}]")
            self.subclient = self.backupset.subclients.add(self.subclient_name)
            self.log.info(f"Subclient set Added [{self.subclient_name}]")

            # Add plan and content to the subclient
            self.log.info("Adding plan to subclient")
            self.subclient.plan = [self.plan, [self.content_path]]

            self.log.info(f"Adding the secondary copy [{self.copy_name}]")
            self.plan.storage_policy.create_secondary_copy(self.copy_name, self.cloud_pool_name,
                                                           self.tcinputs['SecondaryCopyMediaAgent'])
            self.log.info(f"secondary copy [{self.copy_name}] added.")

            self.log.info("Setting re-encryption on dedup secondary copy")
            dedup_primary_copy = self.plan.storage_policy.get_copy(copy_name=self.copy_name)
            dedup_primary_copy.set_encryption_properties(re_encryption=True, encryption_type="GOST", encryption_length=256)

            # remove association for storage_policy with system created auto copy schedule
            self.mm_helper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, self.copy_name)

            self.dedup_entities_created = True
            self.result_string += 'CASE 3: Check Dedup Backup Passed \n'
        except Exception as exe:
            self.result_string += f'CASE 3: Check Dedup Backup Failed Reason: {exe} \n'
            self.log.error(f'Check Dedup Backup Failed Reason: {exe}')
            self.status = constants.FAILED

    def configure_env(self):
        """ creation of entities """
        try:
            # add backupset
            self.log.info(f"Adding the backupset [{self.backupset_name}]")
            self.backupset = self.mm_helper.configure_backupset(self.backupset_name)
            self.log.info(f"Backupset Added [{self.backupset_name}]")
            self.backup_set_created = True
        except Exception as exp:
            error = f"CASE 1: Backupset Creation Failed: {exp}"
            self.result_string += error
            self.log.error(error)
            self.status = constants.FAILED

        if self.backup_set_created:
            self.create_non_dedup_entities()
            self.create_dedup_entities()

    def non_dedup_backup_jobs(self):
        """ Backup jobs on non-dedupe storage pool """
        if self.non_dedupe_entities_created:
            try:
                # running the backup job for non dedup
                self.log.info("Running F_I_F_I_SF jobs for non dedup")
                self.run_F_I_F_I_SF_backup_jobs(self.non_dedup_subclient, self.nonDDBContentPath, self.non_dedup_copy_id, False)
                self.log.info("Jobs Completed for non dedup")

                self.non_dedupe_backup_success = True
                self.result_string += f"CASE 2: Non-Dedup Backup Jobs completed successfully. \n"
            except Exception as exe:
                self.status = constants.FAILED
                error = f"CASE 2: Non-Dedup Backup Job Failed due to {exe} \n"
                self.result_string += error
                self.log.error(error)

    def dedup_backup_jobs(self):
        """ Backup jobs on dedupe storage pool """
        if self.dedup_entities_created:
            try:
                # 2: Run Backups on the subclient in order: F_I_F_I_SF
                self.run_F_I_F_I_SF_backup_jobs(self.subclient, self.content_path, self.dedup_copy_id, True)

                self.dedup_backup_success = True
                self.result_string += f"CASE 4: Dedup Backup Jobs completed successfully. \n"
            except Exception as exe:
                self.status = constants.FAILED
                error = f"CASE 4: Dedup Backup Job Failed due to {exe} \n"
                self.result_string += error
                self.log.error(error)

    def dedup_aux_copy_job(self):
        """ Aux copy job on dedupe stroage pool """
        if self.dedup_backup_success:
            try:
                # 3: Run AuxCopy
                self.log.info('Running AuxCopy Job with Scalable Resource Allocation')
                aux_copy_job = self.plan.storage_policy.run_aux_copy()
                self.log.info('Waiting for AuxCopy Job(Id: %s) to Complete', aux_copy_job.job_id)
                if aux_copy_job.wait_for_completion():
                    self.log.info('AuxCopy Completed(Id: %s)', aux_copy_job.job_id)
                    self.dedup_aux_copy_success = True
                    self.result_string += 'CASE 5: Dedup Aux Copy Passed \n'
                else:
                    self.status = constants.FAILED
                    self.result_string += f'CASE 5: Dedup Aux Copy Failed Reason: {aux_copy_job.delay_reason} \n'
                    self.log.error(f'Dedup Aux Copy Failed Reason: {aux_copy_job.delay_reason}')
            except Exception as exe:
                self.status = constants.FAILED
                self.result_string += f'CASE 5: Aux Copy Failed Reason: {exe} \n'
                self.log.error(f'Aux Copy Failed Reason: {exe}')

    def non_dedup_restore(self):
        """ Restore from primary copy of non-dedupe storage pool """
        if self.non_dedupe_backup_success:
            self.log.info('*** Running Restore from non dedup Primary copy ***')
            self.log.info('Initiating Restore Job from Primary of non dedup')
            restore_job = self.non_dedup_subclient.restore_out_of_place(self.client.client_name,
                                                                        self.non_dedupe_restore_path,
                                                                        [self.nonDDBContentPath],
                                                                        copy_precedence=1)
            self.log.info('Waiting for the Restore Job (JobId: %s) to Complete', restore_job.job_id)
            if restore_job.wait_for_completion():
                self.log.info('Restore Job: %s Completed', restore_job.job_id)
                self.non_dedupe_restore_success = True
                self.result_string += 'CASE 6: Non Dedup Restore Passed \n'
            else:
                self.status = constants.FAILED
                self.result_string += f'CASE 6: Non Dedup Restore Failed Reason: {restore_job.delay_reason} \n'
                self.log.error(f'Non Dedup Restore Failed Reason: {restore_job.delay_reason}')

    def dedup_restores(self):
        """ Restore from primary and secondary copy of dedupe storage pool """
        if self.dedup_backup_success:
            self.log.info('*** Running Restore from Primary copy ***')
            self.log.info('Initiating Restore Job from Primary of dedup plan')
            restore_job2 = self.subclient.restore_out_of_place(self.client.client_name,
                                                               self.restore_path_primary,
                                                               [self.content_path],
                                                               copy_precedence=1)
            self.log.info('Waiting for the restore job to complete (JobId: %s)', restore_job2.job_id)
            if restore_job2.wait_for_completion():
                self.log.info('Restore Job: %s Completed', restore_job2.job_id)
                self.dedup_restore_success = True
                self.result_string += 'CASE 7: Dedup Restore From Primary Copy Passed \n'
            else:
                self.status = constants.FAILED
                self.result_string += f'CASE 7: Dedup Restore from Primary Copy Failed Reason: {restore_job2.delay_reason} \n'
                self.log.error(f'Dedup Restore from Primary Copy Failed Reason: {restore_job2.delay_reason}')

        if self.dedup_aux_copy_success:
            self.log.info('Initiating Restore Job from Secondary Cloud Copy of dedup plan')
            restore_job3 = self.subclient.restore_out_of_place(self.client.client_name,
                                                               self.restore_path_secondary,
                                                               [self.content_path],
                                                               copy_precedence=2)
            self.log.info('Waiting for the restore job to complete (JobId: %s)', restore_job3.job_id)
            if restore_job3.wait_for_completion():
                self.log.info('Restore Job: %s Completed', restore_job3.job_id)
                self.dedup_aux_copy_restore_success = True
                self.result_string += 'CASE 8: Dedup Restore From Secondary Copy Passed \n'
            else:
                self.dedup_aux_copy_restore_success = False
                self.status = constants.FAILED
                self.result_string += f'CASE 8: Dedup Restore from Secondary Copy Failed Reason: {restore_job3.delay_reason} \n'
                self.log.error(f'Dedup Restore from Secondary Copy Failed Reason: {restore_job3.delay_reason}')

    def perform_data_aging(self, case_number):
        # Run DataAging
        try:
            self.data_aging_job = self.commcell.run_data_aging()
            self.log.info("Data Aging job [%s] has started.", self.data_aging_job.job_id)
            if not self.data_aging_job.wait_for_completion():
                self.log.error(
                    "Data Aging job [%s] has failed with %s.", self.data_aging_job.job_id, self.data_aging_job.delay_reason)
                self.result_string += f'CASE {case_number}: Data Aging job {self.data_aging_job.job_id} Failed Reason: {self.data_aging_job.delay_reason} \n'
            self.log.info("Data Aging job [%s] has completed.", self.data_aging_job.job_id)
        except Exception as exe:
            self.result_string += f'CASE {case_number}: Data Aging job {self.data_aging_job.job_id} Failed Reason: {exe} \n'

    def verify_chunks_present_or_not(self, chunks_array, case_number, is_dedup=False):
        dedup_or_non_dedupe = None
        if is_dedup:
            dedup_or_non_dedupe = "dedupe chunks"
        else:
            dedup_or_non_dedupe = "non dedupe chunks"
        self.log.info(f"CASE {case_number}: Starting Verification of physical deletion of {dedup_or_non_dedupe}. \n")
        flag = 0
        for i in range(5):
            for chunk_array in chunks_array[i]:
                if len(chunk_array) == 4:
                    chunk_array[3] = 'CHUNK_' + chunk_array[3]
                    chunk_array = chunk_array[:2] + ['CV_MAGNETIC'] + chunk_array[2:]
                    chunk_path = self.ma_machine_1.join_path(*chunk_array)
                    chunk_exists = False
                    if is_dedup:
                        chunk_exists = self.ma_machine_1.check_directory_exists(chunk_path)
                    else:
                        chunk_exists = self.ma_machine_1.check_file_exists(chunk_path)
                    if chunk_exists:
                        self.result_string += f"CASE {case_number}: Verification of physical deletion of {dedup_or_non_dedupe} [{chunk_path}] Failed. \n"
                        self.status = constants.FAILED
                        flag = 1
                        break
                    else:
                        self.log.info(f"Successfully verified physical deletion of chunk {chunk_path}")
            if flag == 1:
                break
        if flag == 0:
            self.result_string += f"CASE {case_number}: Verification of physical deletion of {dedup_or_non_dedupe} after pruning Passed. \n"

    def check_pruning_completion_status(self, dedup_chunk_array):
        chunk_array = dedup_chunk_array[0][0]
        copy_chunk_array = chunk_array.copy()
        copy_chunk_array[3] = 'CHUNK_' + copy_chunk_array[3]
        new_chunk_path = copy_chunk_array[:2] + ['CV_MAGNETIC'] + copy_chunk_array[2:]
        chunk_path = self.ma_machine_1.join_path(*new_chunk_path)
        try:
            statement = f"Deleted folder {chunk_path}"
            (matched_lines, matched_string) = self.dedupe_helper.parse_log(self.tcinputs['PrimaryCopyMediaAgent'], "CVMA.log", regex=statement,
                                                             escape_regex=True, single_file=True)
            if matched_lines:
                self.result_string += f"Case 12: Matching line found, Pruning Validation from log file Passed \n"
                self.log.info(f"Case 12: Matching line found, Pruning Validation from log file Passed \n")
            else:
                self.result_string += f"Case 12: Matching line not found, Pruning Validation from log file failed \n"
                self.log.error(f"Case 12: Matching line not found, Pruning Validation from log file failed \n")
        except Exception as exe:
            self.result_string += f"Case 12: Pruning Validation from log file failed, reason: {exe} \n"
            self.log.error(f"Case 12: Pruning Validation from log file failed, reason: {exe} \n")
            self.status = constants.FAILED

    def physical_verification_of_chunks(self):
        if self.non_dedupe_backup_success:
            try:
                self.log.info("******** Verification of physical deletion of non dedup chunks after pruning ********")
                time.sleep(2*60)
                self.verify_chunks_present_or_not(self.non_dedup_jobs_chunk_dirs, 10, False)
            except Exception as exe:
                self.result_string += f"Case 11: Verification of physical deletion of non dedup chunks after pruning failed, Reason: {exe} \n"
                self.log.error(f"Case 11: Verification of physical deletion of non dedup chunks after pruning failed, Reason: {exe} \n")
                self.status = constants.FAILED
        if self.dedup_backup_success:
            try:
                self.log.info("******** Verification of physical deletion of dedup chunks after pruning ********")
                time.sleep(2*60)
                self.check_pruning_completion_status(self.dedup_jobs_chunk_dirs)
                self.log.info("Waiting for 10 min for the pruning to complete...")
                time.sleep(10*60)
                self.verify_chunks_present_or_not(self.dedup_jobs_chunk_dirs, 13, True)
            except Exception as exe:
                self.result_string += f"Case 14: Verification of physical deletion of dedup chunks after pruning failed, Reason: {exe} \n"
                self.log.error(f"Case 14: Verification of physical deletion of dedup chunks after pruning failed, Reason: {exe} \n")
                self.status = constants.FAILED

    def run(self):
        """Run Function of this case"""
        self.log.info('**************** Cleaning up Entities from older runs ****************')
        # Cleanup entities
        self.cleanup()
        # Data Aging after first clean up
        self.perform_data_aging(0)
        # Configure the environment
        self.configure_env()
        # Perform non dedup backup jobs
        self.non_dedup_backup_jobs()
        # perform dedup backup jobs
        self.dedup_backup_jobs()
        # perform aux copy on dedup
        self.dedup_aux_copy_job()
        # perform restore on non-dedupe storage
        self.non_dedup_restore()
        # perform restore on dedup storage
        self.dedup_restores()

    def run_backup(self, subclient_obj, backup_type):
        """Runs Backup of specified type and waits for job till it completes
                Args:
                        backup_type    (str)  --   Type of backup To Run
                Return:
                        (object)              --   Object of Job Class

        """
        job = subclient_obj.backup(backup_level=backup_type)
        self.log.info(f"Waiting for the backup job to complete (JobId: {job.job_id}) to complete")
        if job.wait_for_completion():
            self.log.info('%s Backup job Completed(Id: %s)', backup_type, job.job_id)
        else:
            raise Exception(f'{backup_type} Backup Job {job.job_id} Failed with JPR: {job.delay_reason}')
        return job

    def run_F_I_F_I_SF_backup_jobs(self, subclient_obj, content_path, copy_id=None, is_dedup=False):
        self.log.info('Running backupJobs in order F_I_F_I_SF')
        full_1 = self.run_backup(subclient_obj, "Full")
        chunks = self.mm_helper.get_chunks_for_job(full_1.job_id, copy_id)
        if is_dedup:
            self.dedup_jobs_chunk_dirs.append(chunks)
        else:
            self.non_dedup_jobs_chunk_dirs.append(chunks)

        self.mm_helper.create_uncompressable_data(self.tcinputs['ClientName'],
                                                  content_path, 0.2)
        incremental_1 = self.run_backup(subclient_obj, "Incremental")
        chunks = self.mm_helper.get_chunks_for_job(incremental_1.job_id, copy_id)
        if is_dedup:
            self.dedup_jobs_chunk_dirs.append(chunks)
        else:
            self.non_dedup_jobs_chunk_dirs.append(chunks)

        full_2 = self.run_backup(subclient_obj, "Full")
        chunks = self.mm_helper.get_chunks_for_job(full_2.job_id, copy_id)
        if is_dedup:
            self.dedup_jobs_chunk_dirs.append(chunks)
        else:
            self.non_dedup_jobs_chunk_dirs.append(chunks)

        self.mm_helper.create_uncompressable_data(self.tcinputs['ClientName'],
                                                  content_path, 0.2)
        incremental_2 = self.run_backup(subclient_obj, "Incremental")
        chunks = self.mm_helper.get_chunks_for_job(incremental_2.job_id, copy_id)
        if is_dedup:
            self.dedup_jobs_chunk_dirs.append(chunks)
        else:
            self.non_dedup_jobs_chunk_dirs.append(chunks)

        synth_job = self.run_backup(subclient_obj, "Synthetic_full")
        chunks = self.mm_helper.get_chunks_for_job(synth_job.job_id, copy_id)
        if is_dedup:
            self.dedup_jobs_chunk_dirs.append(chunks)
        else:
            self.non_dedup_jobs_chunk_dirs.append(chunks)

    def tear_down(self):
        """Tear Down Function of this Case"""
        if self.status == constants.FAILED:
            self.log.warning("TC Failed. Please go through the logs for debugging. Cleaning up the entities")
        self.cleanup()
        # perform data aging
        self.perform_data_aging(9)
        # physical verification of chunks
        self.physical_verification_of_chunks()
        # Result string
        self.log.info("Summary of this TestCase: ")
        self.log.info(self.result_string)
