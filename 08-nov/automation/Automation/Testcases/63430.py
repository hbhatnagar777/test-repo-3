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

    run_backups()   -- run backup

    run_auxcopy()   -- run auxcopy per copy

    run_auxcopy_validations()    --  runs the validations for auxcopy

    identify_chunks()           -- identifies the chunks to be altered

    identify_paths_of_chunks()  -- identify path of the chunks

    make_alterations()          -- alter the chunks

    run_verification_jobs()     -- Run DV2

    check_data_verification_status()  -- verify the status of DV2 failed chunks

    do_restores()   -- do restores

    run()           --  run function of this test case

    cleanup()     --  tear down function of this test case

TcInputs to be passed in JSON File:

    "ClientName": "name of the client machine without as in commserve",
    "AgentName": "File System",
    "PrimaryCopyMediaAgent":   Name of a MediaAgent machine - we create primary copy here
    "SecondaryCopyMediaAgent": Name of a MediaAgent machine - we create secondary copy here

    Optional values:
    "PrimaryCopyMP": path where primary copy library is to be created
    "SecondaryCopyMP": path where secondary copy library is to be created
    "PrimaryCopyDDBPath": path where dedup store to be created [for linux MediaAgents,
                                        User must explicitly provide a
                                        dedup path that is inside a Logical Volume.
                                        (LVM support required for DDB)]
    "SecondaryCopyDDBPath": path where dedup store to be created for auxcopy [for linux MediaAgents,
                                        User must explicitly provide a
                                        dedup path that is inside a Logical Volume.
                                        (LVM support required for DDB)]
    Note: Both the MediaAgents can be the same machine

Steps:

1: Configure the environment: create a pool, plan-with Primary, pool for Secondary Copy,
                              a BackupSet,two SubClients

2: Run 2 backup jobs each for each of the subclients

3: For subclient1,job1 corrupt 4 random sfiles containers. For subclient2, job1 delete 4 chunkmetadata

4: Run FULL DV2

5: Run 2 more backups for subclient1, subclient2

6: Run INCR DV2.

7. Do Auxcopy with 'skip failed verification jobs'. Verify that the chunks which got corrupted are not picked for copy

8: Do restores from Latest jobs from secondary copy

9: Cleanup
"""
import time

from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
from random import randint


class TestCase(CVTestCase):
    """Class for executing this test case"""
    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Skip verification failed jobs"
        self.tcinputs = {
            "PrimaryCopyMediaAgent": None,
            "SecondaryCopyMediaAgent": None,
        }
        self.utility = None
        self.mm_helper = None
        self.ma_machine_1 = None
        self.ma_machine_2 = None
        self.dedupe_helper = None
        self.client_machine = None
        self.ddb_path = None
        self.ddb_path2 = None
        self.copy1_ddb_path = None
        self.copy1_ddbpath2 = None
        self.mount_path = None
        self.client_path = None
        self.mount_path_2 = None
        self.content_path = None
        self.primary_ma_path = None
        self.secondary_ma_path = None
        self.storage_pool_name1 = None
        self.storage_pool_name2 = None
        self.pool1 = None
        self.sp_obj_list = []
        self.pool2 = None
        self.subclient = []
        self.subclient_name = None
        self.restore_path = None
        self.copy1_name = None
        self.plan = None
        self.backupset = None
        self.backupset_name = None
        self.plan_name = None
        self.copy_id = None
        self.plan_copy1 = None
        self.dedupe_helper = None
        self.is_user_defined_mp = False
        self.is_user_defined_copy_mp = False
        self.is_user_defined_dedup = False
        self.is_user_defined_copy_dedup = False
        self.backup_jobs = []
        self.chunk_lists = []
        self.volume_sets = []
        self.query_results = []
        self.effected_chunk_sets = []
        self.verification_statuses = []
        self.mmconfig_value = []

    def setup(self):
        """Setup function of this test case"""
        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)
        self.utility = OptionsSelector(self.commcell)
        self.client_machine, self.client_path = self.mm_helper.generate_automation_path(self.client.client_name, 25*1024)
        self.content_path = self.client_machine.join_path(self.client_path, 'content')
        self.storage_pool_name1 = f"{self.id}_Pool1Primary_{self.tcinputs['PrimaryCopyMediaAgent']}"
        self.storage_pool_name2 = f"{self.id}_Pool1Copy1_{self.tcinputs['SecondaryCopyMediaAgent']}"
        self.copy1_name = f"{self.id}_Copy1"
        self.subclient_name = f"{self.id}_SC"
        self.backupset_name = f"{self.id}_BS"
        self.restore_path = self.client_machine.join_path(self.client_path, 'Restores')
        self.plan_name = f"{self.id}_SP_{self.tcinputs['PrimaryCopyMediaAgent']}__{self.tcinputs['SecondaryCopyMediaAgent']}"
        if self.tcinputs.get('PrimaryCopyMP'):
            self.is_user_defined_mp = True
        if self.tcinputs.get('SecondaryCopyMP'):
            self.is_user_defined_copy_mp = True
        if self.tcinputs.get('PrimaryCopyDDBPath'):
            self.is_user_defined_dedup = True
        if self.tcinputs.get('SecondaryCopyDDBPath'):
            self.is_user_defined_copy_dedup = True

        if not self.is_user_defined_mp or not self.is_user_defined_dedup:
            self.ma_machine_1, self.primary_ma_path = self.mm_helper.generate_automation_path(self.tcinputs['PrimaryCopyMediaAgent'], 25*1024)
        if not self.is_user_defined_copy_mp or not self.is_user_defined_copy_dedup:
            self.ma_machine_2, self.secondary_ma_path = self.mm_helper.generate_automation_path(self.tcinputs['SecondaryCopyMediaAgent'], 25*1024)

        if (not self.is_user_defined_dedup and "unix" in self.ma_machine_1.os_info.lower()) or \
                (not self.is_user_defined_copy_dedup and "unix" in self.ma_machine_2.os_info.lower()):
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if not self.is_user_defined_mp:
            self.mount_path = self.ma_machine_1.join_path(self.primary_ma_path, 'MP1')
        else:
            self.log.info("custom mount_path supplied")
            self.mount_path = self.tcinputs['PrimaryCopyMP']

        if not self.is_user_defined_copy_mp:
            self.mount_path_2 = self.ma_machine_2.join_path(self.secondary_ma_path, 'MP2')
        else:
            self.log.info("custom copy_mount_path supplied")
            self.mount_path_2 = self.tcinputs['SecondaryCopyMP']

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            ddb_path = self.tcinputs["PrimaryCopyDDBPath"]
            self.ddb_path = self.ma_machine_1.join_path(ddb_path, "DDBprimary")
            self.ddb_path2 = self.ma_machine_2.join_path(ddb_path, "DDBPrimary2")
        else:
            self.ddb_path = self.ma_machine_1.join_path(self.primary_ma_path, "DDBprimary")
            self.ddb_path2 = self.ma_machine_2.join_path(self.primary_ma_path, "DDBPrimary2")

        if self.is_user_defined_copy_dedup:
            self.log.info("custom copy dedup path supplied")
            copy1_ddb_path = self.tcinputs["SecondaryCopyDDBPath"]
            self.copy1_ddb_path = self.ma_machine_2.join_path(copy1_ddb_path, "DDBcopy1")
            self.copy1_ddbpath2 = self.ma_machine_2.join_path(copy1_ddb_path, "DDBcopy2")
        else:
            self.copy1_ddb_path = self.ma_machine_2.join_path(self.secondary_ma_path, "DDBcopy1")
            self.copy1_ddbpath2 = self.ma_machine_2.join_path(self.secondary_ma_path, "DDBcopy2")

        # disable ransomeware only if it is windows and update mmconfigs so that the changes take effect immediately
        if self.ma_machine_1.os_info.lower() == 'windows':
            query = 'select value from mmconfigs where name=\'MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN\''
            self.log.info(f"Query is : [{query}]")
            self.csdb.execute(query)
            self.mmconfig_value = self.csdb.fetch_one_row()
            self.log.info(f"Query Result is : [{self.mmconfig_value}]")
            self.mm_helper.update_mmconfig_param('MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN',
                                                 nmin=5, value=5)
            self.log.info("Disabling Ransomware protection on MA")
            self.commcell.media_agents.get(
                self.tcinputs.get('PrimaryCopyMediaAgent')).set_ransomware_protection(False)

    def run_backups(self):
        """Runs two backups of subclient1 and subclient2"""
        backup_job = []
        for counter in range(1, 3):
            self.log.info("Submitting Full Backup for subclient %s ", self.subclient[counter-1].subclient_name)
            job = self.subclient[counter-1].backup(backup_level='Full')
            self.backup_jobs.append(job)
            backup_job.append(job)
        for job in backup_job:
            if self.mm_helper.wait_for_job_completion(job):
                self.log.info("Backup Completed :Id - %s", job.job_id)
            else:
                raise Exception(f"Backup job [{job.job_id}] did not complete - [{job.delay_reason}]")
            time.sleep(60)

    def run_auxcopy(self):
        """Runs Auxcopy with skipping verification failed jobs"""
        self.log.info("Submitting AuxCopy job")
        aux_copy_job = self.plan.storage_policy.run_aux_copy(ignore_dv_failed_jobs=True)
        if self.mm_helper.wait_for_job_completion(aux_copy_job):
            self.log.info("AuxCopy Completed :Id - %s", aux_copy_job.job_id)
        else:
            raise Exception(f"Auxcopy job [{aux_copy_job.job_id}] did not complete - [{aux_copy_job.delay_reason}]")
        self.run_auxcopy_validations(aux_copy_job.job_id)

    def run_auxcopy_validations(self, aux_copy_job_id):
        """Runs Auxcopy validations from CSDB from archchunktoreplicatehistory table

        Args:
            aux_copy_job_id (string) :  Auxcopy job id for which validation needs to be done
        """
        # check that only verification passed chunks get populated in archchunktoreplicatehistory tables
        chunk_id = []
        chunk_id_altered = []
        self.log.info('*** CASE 1: ArchChunkToReplicate Population ***')
        query = '''select archchunkid
                                from archchunktoreplicatehistory where AdminJobId = {0} order by archchunkid
                                '''.format(aux_copy_job_id)
        self.log.info(f"Query is : [{query}]")
        self.csdb.execute(query)
        for row_1 in self.csdb.fetch_all_rows():
            self.log.info(f"ChunkID is : [{row_1}]")
            for row_2 in row_1:
                chunk_id.append(row_2)
        for dv_status in self.verification_statuses:
            for dv_status1 in dv_status:
                for dv_status2 in dv_status1:
                    chunk_id_altered.append(dv_status2)
        if set(chunk_id_altered).issubset(set(chunk_id)):
            self.log.info("ArchChunkToReplicateHistory is populated for verification failed ChunkIds %s", chunk_id)
            raise Exception("Case 1 : Failed - Verification failed chunks are picked for Auxcopy")
        else:
            self.log.info("Case 1 : Passed - Verification failed Chunkids are not picked for Auxcopy. "
                          "Chunks picked are %s:", chunk_id)
        self.log.info('*** CASE 2: ArchChunkToReplicate status ***')
        query = '''select distinct status
                        from archchunktoreplicatehistory where AdminJobId = {0}
                        '''.format(aux_copy_job_id)
        self.log.info(f"Query is : [{query}]")
        self.csdb.execute(query)
        row_1 = self.csdb.fetch_one_row()
        self.log.info(f"Query result is : [{row_1}]")
        if int(row_1[0]) == 2 and len(row_1) == 1:
            self.log.info("Case2: Passed - ArchChunkToReplicate status for all chunks is 2")
        else:
            raise Exception("Case 2: Failed - Auxcopy did not complete for all populated chunks")

    def identify_chunks(self):
        """Identifies the Chunks Created for the Backup Jobs and forms a 2D List"""
        self.log.info("Fetching the Chunks for BackupJobs from the DB")
        for index in range(0, 4):
            self.query_results.append(
                self.mm_helper.get_chunks_for_job(
                    self.backup_jobs[index].job_id, self.copy_id,
                    afile_type=1))

    def identify_paths_of_chunks(self):
        """Forms Folder Paths from the query result"""
        for query_result in self.query_results:
            chunk_list = []
            volume_set = set()
            for row in query_result:
                chunk_list.append((row[3], self.ma_machine_1.join_path(row[0], row[1], 'CV_MAGNETIC',
                                   row[2], f'CHUNK_{row[3]}')))
                volume_set.add((row[2],
                                self.ma_machine_1.join_path(row[0], row[1], 'CV_MAGNETIC', row[2])))
            self.chunk_lists.append(chunk_list)
            self.volume_sets.append(volume_set)
            if self.ma_machine_1.os_info.lower() == 'windows':
                for volume in volume_set:
                    self.ma_machine_1.modify_ace('Everyone', volume[1], 'DeleteSubdirectoriesAndFiles', 'Deny',
                                                 remove=True, folder=True)
                    self.ma_machine_1.modify_ace('Everyone', volume[1], 'Delete', 'Deny', remove=True,
                                                 folder=True)

    def make_alterations(self):
        """Alters Chunks and Volumes According to Cases"""
        for sub_case in range(1, 3):
            self.log.info('Alterations for SubCase : %d', sub_case)
            chunk_list = self.chunk_lists[sub_case - 1]
            # sfile container deletion in backup 1 of sc1
            effected_chunks = self.select_chunks_to_alter(chunk_list)
            if sub_case == 1:
                self.alter('SFILE_CONTAINER_random', chunk_list, effected_chunks, 0, 0, 0)
            # chunk meta data deletion in backup 1 of sc2
            elif sub_case == 2:
                self.alter('CHUNK_META_DATA_', chunk_list, effected_chunks, 0, 0, 1)
            self.effected_chunk_sets.append(effected_chunks)

    def select_chunks_to_alter(self, chunk_list):
        """Selects Chunks at random that need to be altered

        Args:
            chunk_list (list): List of chunks for a subcase
        Returns:
            (set):  Set of indices of the chunks on which alterations will be done for the subcase
        """
        limit = 4
        effected_chunks = set()
        length = len(chunk_list)
        log_line = ''
        while limit > len(effected_chunks):
            index = randint(0, length - 1)
            if index not in effected_chunks:
                if self.ma_machine_1.check_file_exists(self.ma_machine_1.join_path(chunk_list[index][1],
                                                                                   'SFILE_CONTAINER.idx')):
                    effected_chunks.add(index)
                    log_line += f'{chunk_list[index][0]}, '
        self.log.info("Effected Chunks : %s", log_line)
        return effected_chunks

    def alter(self, file_to_be_altered, folder_list,
              effected_indices, corrupt=0, directory=0, append_id=0):
        """Deletes or Corrupts the Files/Directory

        Args:
            file_to_be_altered(str): File to be deleted/corrupted
                                    (SFILE_CONTAINER_001/SFILE_CONTAINER.idx/CHUNK_META_DATA)

            folder_list(list)     : List of folders on which alterations will be done

            effected_indices(set) : Set of indices of chunks on which the alterations will be done

            corrupt(int)          : (1-Corruption subcase)/(0-Not corruption subcase)

            directory(int)        : (1-if alteration to be done is deleting a directory)

            append_id(int)        : id of chunk
                                    (for CMD alteration, id is appended to form the name of file.
                                    Ex: CHUNK_META_DATA_10)
        """
        for index in effected_indices:
            file = file_to_be_altered
            if 'SFILE_CONTAINER_' in file_to_be_altered:
                file = self.get_sfile(file_to_be_altered, folder_list[index][1])
            file_effected = self.ma_machine_1.join_path(folder_list[index][1], file)
            if append_id:
                file_effected += folder_list[index][0]
            if corrupt == 0 and directory == 0:
                self.ma_machine_1.delete_file(file_effected)
            elif corrupt == 0 and directory == 1:
                self.ma_machine_1.remove_directory(file_effected)
            else:
                self.ma_machine_1.create_file(file_effected, "This file has been corrupted")

    def get_sfile(self, sfile, chunk_path):
        """Returns a sfile from the given Chunk Directory
        Args:
            sfile (str)     :   Sfile Container eg: SFILE_CONTAINER_
            chunk_path (str) :  path of the chunk
        """
        files = self.ma_machine_1.get_files_in_path(chunk_path)
        sfiles = [
            file.split(self.ma_machine_1.os_sep)[-1] for file in files if 'SFILE_CONTAINER_' in file]
        if sfile.split('_')[-1] == 'first':
            return sorted(sfiles)[0]
        if sfile.split('_')[-1] == 'random':
            return sfiles[randint(0, len(sfiles)-1)]
        return sorted(sfiles)[-1]

    def run_verification_jobs(self, incr):
        """Runs the Verification Jobs
            Args:
                incr(bool): True or False based on whether to run INCR or FULL DV2
        """
        self.log.info("Running the Verification Jobs")
        engine = self.commcell.deduplication_engines.get(self.storage_pool_name1, 'Primary')
        store = engine.get(engine.all_stores[0][0])
        job = store.run_ddb_verification(incremental_verification=incr, quick_verification=False,
                                         use_scalable_resource=True)
        if job.wait_for_completion():
            self.log.info("DV2 Completed :Id - %s", job.job_id)
        else:
            raise Exception(f"DV2 job [{job.job_id}] did not complete - [{job.delay_reason}]")

    def check_data_verification_status(self):
        """Checks the DataVerification Status of the chunks - flags 4 means verification failed chunk"""
        query = '''select archchunkid from archchunkmapping where flags&4=4 and archCopyId = {0} order by archchunkid 
                    '''.format(self.copy_id)
        self.log.info(f"Query is : [{query}]")
        self.csdb.execute(query)
        result = self.csdb.fetch_all_rows()
        self.log.info(f"Query Result is : [{result}]")
        self.verification_statuses.append(result)
        self.log.info("ChunkIds which have failed DV STATUS: %s", str(self.verification_statuses))

    def do_restores(self):
        """Do restores of latest jobs of both subclients from copy precendence 2"""
        restore_jobs = []
        for index in range(1, 3):
            restore_path = self.restore_path + str(index)
            content_path = self.content_path + str(index)
            job = self.subclient[index-1].restore_out_of_place(self.client.client_name,
                                                               restore_path,
                                                               [content_path], copy_precedence=2)
            restore_jobs.append(job)

        for job in restore_jobs:
            if self.mm_helper.wait_for_job_completion(job):
                self.log.info("Restore Job: %s Completed", job.job_id)
            else:
                raise Exception(f"Restore job [{job.job_id}] did not complete - [{job.delay_reason}]")

        self.log.info("Validating Restored Data from 2 subclients from secondary copy")
        for index in range(1, 3):
            restored_path = self.restore_path + self.client_machine.join_path(str(index), 'content') + str(index)
            content_path = self.content_path + str(index)
            difference = self.client_machine.compare_folders(self.client_machine,
                                                             content_path,
                                                             restored_path)
            if difference:
                raise Exception("Validating Data restored from subclient %s Failed" % index)
        self.log.info("Validation SUCCESS")

    def create_resources(self):
        """Create resources needed by the Test Case"""
        try:
            self.cleanup()
            # Configure the environment
            # Creating a storage pool and associate to SP
            self.log.info("Configuring Storage Pool for Primary ==> %s", self.storage_pool_name1)
            if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name1):
                self.pool1 = self.commcell.storage_pools.add(self.storage_pool_name1, self.mount_path,
                                                             self.tcinputs['PrimaryCopyMediaAgent'],
                                                             [self.tcinputs['PrimaryCopyMediaAgent'], self.tcinputs['PrimaryCopyMediaAgent']],
                                                             [self.ddb_path, self.ddb_path2])
            else:
                self.pool1 = self.commcell.storage_pools.get(self.storage_pool_name1)
            self.log.info("Done creating a storage pool for Primary")
            self.commcell.storage_pools.refresh()

            # Create storage pool for secondary copy
            self.log.info("Configuring Secondary Storage Pool for copy1 ==> %s", self.storage_pool_name2)
            if not self.commcell.storage_pools.has_storage_pool(self.storage_pool_name2):
                self.pool2 = self.commcell.storage_pools.add(self.storage_pool_name2, self.mount_path_2,
                                                             self.tcinputs['SecondaryCopyMediaAgent'],
                                                             [self.tcinputs['SecondaryCopyMediaAgent'], self.tcinputs['SecondaryCopyMediaAgent']],
                                                             [self.copy1_ddb_path, self.copy1_ddbpath2])
                self.commcell.storage_pools.refresh()
            else:
                self.pool2 = self.commcell.storage_pools.get(self.storage_pool_name2)

            self.log.info("Done creating a storage pool for secondary copy")
            self.commcell.storage_pools.refresh()

            self.log.info("Configuring Plan ==> %s", self.plan_name)
            if not self.commcell.plans.has_plan(self.plan_name):
                self.plan = self.commcell.plans.add(self.plan_name, "Server", self.storage_pool_name1)
            else:
                self.plan = self.commcell.plans.get(self.plan_name)

            # disabling the schedule policy
            self.plan.schedule_policies['data'].disable()

            self.commcell.plans.refresh()

            # Create secondary copy
            self.log.info("Configuring Secondary Copy 1 using Storage pool==> %s", self.copy1_name)
            self.commcell.storage_pools.refresh()
            time.sleep(10)
            self.commcell.storage_pools.refresh()

            self.plan_copy1 = self.plan.storage_policy.create_secondary_copy(
                copy_name=self.copy1_name,
                library_name=self.storage_pool_name1,
                media_agent_name=self.tcinputs['PrimaryCopyMediaAgent'])
            self.log.info("Secondary copy created.")

            self.mm_helper.remove_autocopy_schedule(self.plan.storage_policy.storage_policy_name, self.copy1_name)

            # add backupset
            self.log.info(f"Adding the backup set [{self.backupset_name}]")
            self.backupset = self.mm_helper.configure_backupset(self.backupset_name)
            self.log.info(f"Backup set Added [{self.backupset_name}]")

            for index in range(1, 3):
                self.log.info(f"Creating the subclient {index}")
                subclient_index = self.backupset.subclients.add(self.subclient_name + str(index))
                self.log.info(f"Created the subclient {index}")

                self.log.info(f"Adding plan to sublient {index}")
                subclient_index.plan = [self.plan, [self.content_path + str(index)]]
                self.log.info(f"Added plan to sublient {index}")

                self.subclient.append(subclient_index)
                self.mm_helper.create_uncompressable_data(self.client.client_name, self.content_path + str(index), 0.4)

        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error('Exception Raised during Creating resources: %s', str(exe))

    def run(self):
        """Run Function of This Case"""
        try:
            self.create_resources()

            # Enable encryption on the storage pool copies
            pool1_copy = self.commcell.storage_policies.get(self.storage_pool_name1).get_copy('Primary')
            pool1_copy.set_encryption_properties(re_encryption=True, encryption_type="BlowFish", encryption_length=128)

            pool2_copy = self.commcell.storage_policies.get(self.storage_pool_name2).get_copy('Primary')
            pool2_copy.set_encryption_properties(re_encryption=True, encryption_type="GOST", encryption_length=256)

            self.copy_id = self.plan.storage_policy.get_copy('Primary').copy_id
            self.log.info("Setting the max Chunk Size on Copies to 100 MB")
            query = 'update MMDataPath set ChunkSizeMB = 100 where CopyId = {0}'.format(self.copy_id)
            self.log.info(f"Query is : [{query}]")
            self.utility.update_commserve_db(query)
            # Run backups for each of the subclients
            self.run_backups()
            # Run one more backup each which refer to the existing jobs
            self.run_backups()
            # Identify and corrupt chunks for job1 and job2 of sc1 and sc2 respectively
            self.identify_chunks()
            self.identify_paths_of_chunks()
            self.make_alterations()
            self.run_verification_jobs(False)  # Full DV2
            # Run one more backup for each of the subclient
            self.run_backups()
            self.run_verification_jobs(True)  # INCR DV2
            self.check_data_verification_status()
            # Run auxcopy and validations with skip verification failed jobs
            self.run_auxcopy()
            # Do restores from the latest job from both subclients from secondary copy
            self.do_restores()
        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error("Exception Raised: %s", str(exe))

    def cleanup(self):
        """Cleanup Function of this Case"""
        try:
            # 6: CleanUp the environment
            for index in range(1, 3):
                self.mm_helper.remove_content(self.content_path + str(index), self.client_machine,
                                              suppress_exception=True)
                self.mm_helper.remove_content(self.restore_path + str(index), self.client_machine,
                                              suppress_exception=True)

            if len(self.subclient) > 0:
                for i in range(len(self.subclient)):
                    self.subclient[i].plan = None

            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.backupset = self.agent.backupsets.get(self.backupset_name)
                for i in range(1, 3):
                    if self.backupset.subclients.has_subclient(self.subclient_name + str(i)):
                        subclient = self.backupset.subclients.get(self.subclient_name + str(i))
                        subclient.plan = None
                self.log.info("Deleting backupset %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)

            if self.commcell.plans.has_plan(self.plan_name):
                self.log.info("Deleting plan  %s", self.plan_name)
                self.commcell.plans.delete(self.plan_name)

            if self.commcell.storage_policies.has_policy(f"{self.storage_pool_name1}"):
                self.log.info("Deleting Storage Pool - [%s]", f"{self.storage_pool_name1}")
                self.commcell.storage_policies.delete(f"{self.storage_pool_name1}")

            if self.commcell.storage_policies.has_policy(f"{self.storage_pool_name2}"):
                self.log.info("Deleting Storage Pool - [%s]", f"{self.storage_pool_name2}")
                self.commcell.storage_policies.delete(f"{self.storage_pool_name2}")

            self.log.info("Refresh pools")
            self.commcell.storage_pools.refresh()
            self.log.info("Refresh Plans")
            self.commcell.plans.refresh()
        except Exception as exe:
            self.log.warning("ERROR in Cleanup. Might need to Cleanup Manually: %s", str(exe))

    def tear_down(self):
        """Tear Down Function of this case"""
        # enable ransomware back only for windows and reset mmconfig to original value
        if self.ma_machine_1.os_info.lower() == 'windows':
            self.log.info("Enabling Ransomware protection on MA")
            self.commcell.media_agents.get(
                self.tcinputs.get('PrimaryCopyMediaAgent')).set_ransomware_protection(True)
            # Resetting original value back
            self.mm_helper.update_mmconfig_param('MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN',
                                                 nmin=5, value=self.mmconfig_value[0])

        if self.status != constants.FAILED:
            self.log.info("Test Case PASSED.")
        else:
            self.log.warning("Test Case FAILED.")
        self.cleanup()
