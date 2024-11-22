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

    cleanup()       --  cleans up the entities

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    initial_setup() --  initial setting Up of storage policies, subclients, library

    run_backups()   --  initiates backups for each of the subclients

    identify_chunks()   -- fetches the chunks from that are created by the backup jobs

    identify_paths_of_chunks()  -- identifies the full paths of the chunks created

    makes_alterations() -- control function for making alterations required for each sub-cases

    select_chunks_to_alter() -- selects the chunks that needs to be altered for each sub-case

    alter()     --  performs the required operations (delete/corrupt the files/directories)

    get_sfile() --  for sfile cases, returns the sfile_contianer that needs to be altered

    run_verification_jobs() --  initiates Full DV2 for each of the storage policies

    wait_for_jobs()     --  waits for all the jobs that are passed as list to be completed

    check_bad_chunks()  --  checks the chunks that are marked bad in each sub-case

    check_data_verification_status()    --  checks data verification status of backup jobs

    produce_result()    -- logs the result for each of the sub-cases

TcInputs to be passed in JSON File:
    "59012": {
        "ClientName"    : Name of a Client - Content to be BackedUp will be created here
        "AgentName"     : File System
        "MediaAgentName": Name of a MediaAgent - we create Libraries here
        ***** Optional: If provided, the below entities will be used instead of creating in TC *****
        "use_scalable"  : Whether or not to use Scalable Resource Allocation
        "library_name"  : Name of Existing Library to be Used
        "mount_path"    : Path to be used as MP for Library
        "dedup_path"    : Path to be used for creating Dedupe-Partitions
    }

Steps:

1: Configure the environment: a library, 9 Storage Policies, a BackupSet,9 SubClients

2: Run Backups for all the SubClients

3: Identify the Chunks Created for the respective Jobs

4: Make Alterations to the chunks based on the 6 SubCases we need to test

5: Initiate DV2 for each of DDB Engines

6: Retrieve the Chunks that are marked bad from archChunkDDBDrop table

7: Retrieve the DataVerification Status of Jobs from JMJobDataStats table

8: Check whether they Bad Chunks Marking and DV Status Update for the jobs has worked as expected

9: CleanUp the Environment
"""
from random import randint
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
        super().__init__()
        self.name = 'Marking Bad Chunks by DV2 for DiskLibraries'
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.utility = None
        self.mm_helper = None
        self.ma_machine = None
        self.dedupe_helper = None
        self.client_machine = None
        self.ma_path = None
        self.ddb_path = None
        self.mount_path = None
        self.client_path = None
        self.content_path = None
        self.library_name = None
        self.subclient_name = None
        self.backupset_name = None
        self.storage_policy_name = None
        self.subclients = []
        self.sidb_stores = []
        self.backup_jobs = []
        self.chunk_lists = []
        self.volume_sets = []
        self.sub_cases = []
        self.query_results = []
        self.chunk_mark_flags = []
        self.storage_policies = []
        self.verification_jobs = []
        self.effected_chunk_sets = []
        self.verification_statuses = []
        self.use_scalable = True
        self.is_user_defined_mp = False
        self.is_user_defined_lib = False
        self.is_user_defined_dedup = False
        self.result_string = ''
        self.status = constants.PASSED

    def setup(self):
        """Setup function of this test case"""
        self.ma_machine = Machine(self.tcinputs.get('MediaAgentName'), self.commcell)
        self.client_machine = Machine(self.client.client_name, self.commcell)
        self.utility = OptionsSelector(self.commcell)

        if not self.tcinputs.get('use_scalable', True):
            self.use_scalable = False
        if self.tcinputs.get('library_name'):
            self.is_user_defined_lib = True
        if self.tcinputs.get('mount_path'):
            self.is_user_defined_mp = True
        if self.tcinputs.get('dedup_path'):
            self.is_user_defined_dedup = True
        if not self.is_user_defined_mp or not self.is_user_defined_dedup:
            ma_drive = self.utility.get_drive(self.ma_machine, 10240)
            self.ma_path = self.ma_machine.join_path(ma_drive, f'test_{self.id}')

        client_drive = self.utility.get_drive(self.client_machine, 10240)
        self.client_path = self.client_machine.join_path(client_drive, f'test_{self.id}')
        self.content_path = self.client_machine.join_path(self.client_path, 'Content')
        self.backupset_name = f'{self.id}_BS'
        self.subclient_name = f'{self.id}_SC_'
        self.storage_policy_name = f'{self.id}_SP_'
        if self.is_user_defined_lib:
            self.log.info("Existing library name supplied")
            self.library_name = self.tcinputs.get("library_name")
        else:
            self.library_name = '%s%s%s' % (str(self.id), '_Lib_',
                                            str(self.tcinputs.get('MediaAgentName'))[1:])
            if not self.is_user_defined_mp:
                self.mount_path = self.ma_machine.join_path(self.ma_path, 'MP')
            else:
                self.log.info("custom mount_path supplied")
                self.mount_path = self.ma_machine.join_path(
                    self.tcinputs.get('mount_path'), f'test_{self.id}', 'MP')
        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.ddb_path = self.ma_machine.join_path(self.tcinputs.get("dedup_path"),
                                                      f'test_{self.id}', "DDBs")
        else:
            self.ddb_path = self.ma_machine.join_path(self.ma_path, "DDBs")

        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)
        # Note: Currently, we would mark chunk bad even if CMD is missing.
        # We will fix in SP25, to avoid marking chunk bad. Change this case accordingly then
        self.sub_cases = ['1st SFile Missing', 'Last SFile Missing', 'Random SFile Missing',
                          'Chunk Missing', 'Volume Missing', 'SFile IDX Missing',
                          'ChunkMeta Corrupted', 'ChunkMeta Missing', 'O Size SFile']

    def cleanup(self):
        """CleansUp the Entities"""
        self.log.info('************************ Clean Up Started *********************************')
        try:
            self.log.info('Deleting BackupSet if exists')
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
            self.log.info('Deleting Storage Policies if exists')
            for index in range(9, 0, -1):
                if self.commcell.storage_policies.has_policy(f'{self.storage_policy_name}{index}'):
                    self.commcell.storage_policies.get(
                        f'{self.storage_policy_name}{index}').reassociate_all_subclients()
                    self.commcell.storage_policies.delete(f'{self.storage_policy_name}{index}')
            if not self.is_user_defined_lib:
                self.log.info('Deleting Library if exists')
                if self.commcell.disk_libraries.has_library(self.library_name):
                    self.commcell.disk_libraries.delete(self.library_name)
            self.mm_helper.remove_content(self.mount_path, self.ma_machine, suppress_exception=True)
            self.mm_helper.remove_content(self.ddb_path, self.ma_machine, suppress_exception=True)
        except Exception as exe:
            self.log.warning('CleanUp Failed: ERROR: %s', str(exe))

    def run(self):
        """Run Function of this case"""
        self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
        self.cleanup()
        try:
            self.initial_setup()
            self.run_backups()
            self.wait_for_jobs(self.backup_jobs)
            self.identify_chunks()
            self.identify_paths_of_chunks()
            self.make_alterations()
            self.run_verification_jobs()
            self.wait_for_jobs(self.verification_jobs)
            self.check_bad_chunks()
            self.check_data_verification_status()
            self.produce_result()
        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error('EXCEPTION Occurred : %s', str(exe))

    def tear_down(self):
        """Tear Down Function of this case"""
        self.mm_helper.remove_content(self.content_path, self.client_machine, suppress_exception=True)
        if self.status != constants.FAILED:
            self.log.info('Test Case PASSED. Cleaning Up the Entities')
        else:
            self.log.warning('Test Case FAILED. Please review the TC and Commcell logs. Cleaning Up the Entities')
        self.cleanup()
        if self.ma_machine.os_info.lower() == 'windows':
            self.log.info('Enabling Ransomware protection on MA')
            self.commcell.media_agents.get(
                self.tcinputs.get('MediaAgentName')).set_ransomware_protection(True)

    def initial_setup(self):
        """Initial setting Up of Storage policies, SubClients, Library"""
        for index in range(1, 10):
            self.mm_helper.create_uncompressable_data(
                self.client_machine,
                self.client_machine.join_path(self.content_path, f'Data{index}'), 0.8, 1)

        if not self.is_user_defined_lib:
            self.mm_helper.configure_disk_library(self.library_name,
                                                  self.tcinputs.get('MediaAgentName'),
                                                  self.mount_path)

        for index in range(1, 10):
            self.storage_policies.append(self.dedupe_helper.configure_dedupe_storage_policy(
                f'{self.storage_policy_name}{index}', self.library_name,
                self.tcinputs.get('MediaAgentName'),
                self.ma_machine.join_path(self.ddb_path, f'Dir{index}'),
                self.tcinputs.get('MediaAgentName')))
            # get sidb store id's
            self.sidb_stores.append(self.dedupe_helper.get_sidb_ids(
                self.storage_policies[-1].storage_policy_id, 'Primary')[0])
            copy_id = self.storage_policies[-1].get_copy('Primary').copy_id
            # limit max chunk size on the copy to produce more chunks
            query = 'update MMDataPath set ChunkSizeMB = 100 where CopyId = {0}'.format(copy_id)
            self.utility.update_commserve_db(query)

        self.mm_helper.configure_backupset(self.backupset_name)
        for index in range(1, 10):
            self.subclients.append(self.mm_helper.configure_subclient(
                self.backupset_name, f'{self.subclient_name}{index}',
                f'{self.storage_policy_name}{index}',
                self.client_machine.join_path(self.content_path, f'Data{index}')))

        self.mm_helper.update_mmconfig_param('MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN', 5, 5)
        self.mm_helper.update_mmconfig_param('MMS2_CONFIG_STRING_MARK_JOBS_BAD', 0, 0)
        self.mm_helper.update_mmconfig_param('MMCONFIG_MARK_JOB_VERIFICATION_FAILED_FOR_READ_ERRORS', 0, 1)
        if self.ma_machine.os_info.lower() == 'windows':
            self.log.info('Disabling Ransomware protection on MA')
            self.commcell.media_agents.get(
                self.tcinputs.get('MediaAgentName')).set_ransomware_protection(False)

    def run_backups(self):
        """Runs Backup Jobs on the subclients"""
        self.log.info('Running Full Backups')
        for index in range(9):
            self.backup_jobs.append(self.subclients[index].backup())
            self.log.info('Backup Job(Id: %s) Started. (SubClient: %s, Policy: %s, StoreId: %s)',
                          self.backup_jobs[index].job_id, f'{self.subclient_name}{index}',
                          f'{self.storage_policy_name}{index}', self.sidb_stores[index])
        self.log.info('Completed Initiating all Full Backups')

    def identify_chunks(self):
        """Identifies the Chunks Created for the Backup Jobs and forms a 2D List"""
        self.log.info("Fetching the Chunks for BackupJobs from the DB")
        for index in range(9):
            query = '''select
                Folder,MMMountPath.MountPathName, MMVolume.VolumeName, archChunk.id
            from
                archFile,archChunkMapping, archChunk,MMVolume, MMMountPath,
                MMMountPathToStorageDevice, MMDeviceController
            where
                archFile.jobId = {0}
                and archFile.id = archChunkMapping.archFileId
                and archChunkMapping.archChunkId = archChunk.id
                and archChunk.volumeId = MMVolume.VolumeId
                and MMVolume.CurrMountPathId = MMMountPath.MountPathId
                and MMMountPath.MountPathId = MMMountPathToStorageDevice.MountPathId
                and MMMountPathToStorageDevice.DeviceId = MMDeviceController.DeviceId
            '''.format(self.backup_jobs[index].job_id)
            self.csdb.execute(query)
            self.query_results.append(self.csdb.fetch_all_rows())
            self.log.info('Chunks for Job-%s: %s',
                          self.backup_jobs[index].job_id, str(self.query_results[index]))

    def identify_paths_of_chunks(self):
        """Forms Folder Paths from the query result"""
        for query_result in self.query_results:
            chunk_list = []
            volume_set = set()
            for row in query_result:
                chunk_list.append((row[3], self.ma_machine.join_path(row[0], row[1], 'CV_MAGNETIC',
                                   row[2], f'CHUNK_{row[3]}')))
                volume_set.add((row[2],
                                self.ma_machine.join_path(row[0], row[1], 'CV_MAGNETIC', row[2])))
            self.chunk_lists.append(chunk_list)
            self.volume_sets.append(volume_set)
            if self.ma_machine.os_info.lower() == 'windows':
                for volume in volume_set:
                    self.ma_machine.modify_ace('Everyone', volume[1],
                                               'DeleteSubdirectoriesAndFiles',
                                               'Deny', remove=True, folder=True)
                    self.ma_machine.modify_ace('Everyone', volume[1], 'Delete',
                                               'Deny', remove=True, folder=True)

    def make_alterations(self):
        """Alters Chunks and Volumes According to Cases"""
        for sub_case in range(1, 10):
            self.log.info('Alterations for SubCase : %d', sub_case)
            effected_chunks = set()
            chunk_list = self.chunk_lists[sub_case - 1]
            volume_set = self.volume_sets[sub_case - 1]
            if sub_case != 5:
                effected_chunks = self.select_chunks_to_alter(chunk_list)
            self.log.info('Alterations %d : %s', sub_case, self.sub_cases[sub_case - 1])
            if sub_case == 1:
                self.alter('SFILE_CONTAINER_first', chunk_list, effected_chunks, 0, 0, 0)
            if sub_case == 2:
                self.alter('SFILE_CONTAINER_last', chunk_list, effected_chunks, 0, 0, 0)
            if sub_case == 3:
                self.alter('SFILE_CONTAINER_random', chunk_list, effected_chunks, 0, 0, 0)
            elif sub_case == 4:
                self.alter('', chunk_list, effected_chunks, 0, 1, 0)
            elif sub_case == 5:
                limit = 1
                effected_volumes = set()
                length = len(chunk_list)
                log_line = ''
                log_line_2 = ''
                for volume in volume_set:
                    volume_eligible = False
                    for index in range(length):
                        if volume[0] in chunk_list[index][1]:
                            file = self.ma_machine.join_path(chunk_list[index][1],
                                                             'SFILE_CONTAINER.idx')
                            if self.ma_machine.check_file_exists(file):
                                volume_eligible = True
                                effected_chunks.add(index)
                                log_line_2 += f'{chunk_list[index][0]}, '
                    if volume_eligible:
                        effected_volumes.add(volume[1])
                        log_line += f'{volume[0]}, '
                    if limit == len(effected_volumes):
                        break
                self.log.info('Effected Volumes: %s', log_line)
                self.log.info('Effected Chunks : %s', log_line_2)
                for volume in effected_volumes:
                    self.ma_machine.remove_directory(volume)
            elif sub_case == 6:
                self.alter('SFILE_CONTAINER.idx', chunk_list, effected_chunks, 0, 0, 0)
            elif sub_case == 7:
                self.alter('CHUNK_META_DATA_', chunk_list, effected_chunks, 1, 0, 1)
            elif sub_case == 8:
                self.alter('CHUNK_META_DATA_', chunk_list, effected_chunks, 0, 0, 1)
            elif sub_case == 9:
                self.alter('SFILE_CONTAINER_zero_random', chunk_list, effected_chunks, 1, 0, 0)
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
                if self.ma_machine.check_file_exists(self.ma_machine.join_path(chunk_list[index][1],
                                                     'SFILE_CONTAINER.idx')):
                    effected_chunks.add(index)
                    log_line += f'{chunk_list[index][0]}, '
        self.log.info('Effected Chunks : %s', log_line)
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
            file_effected = self.ma_machine.join_path(folder_list[index][1], file)
            if append_id:
                file_effected += folder_list[index][0]
            if corrupt == 0 and directory == 0:
                # file deletion cases sfile or sfileidx or cmd
                self.ma_machine.delete_file(file_effected)
            elif corrupt == 0 and directory == 1:
                # directory missing cases chunk or volume
                self.ma_machine.remove_directory(file_effected)
            else:
                # file corrupted cases sfile or sfileidx or cmd
                file_size = 0 if 'zero' in file_to_be_altered else None
                self.ma_machine.create_file(file_effected, 'This file has been corrupted', file_size)

    def get_sfile(self, sfile, chunk_path):
        """Returns a sfile from the given Chunk Directory"""
        files = self.ma_machine.get_files_in_path(chunk_path)
        sfiles = [
            file.split(self.ma_machine.os_sep)[-1] for file in files if 'SFILE_CONTAINER_' in file]
        if sfile.split('_')[-1] == 'first':
            return sorted(sfiles)[0]
        if sfile.split('_')[-1] == 'random':
            return sfiles[randint(0, len(sfiles)-1)]
        return sorted(sfiles)[-1]

    def run_verification_jobs(self):
        """Runs the Verification Jobs"""
        self.log.info('Running the Verification Jobs')
        log_line = ''
        for policy in self.storage_policies:
            engine = self.commcell.deduplication_engines.get(policy.storage_policy_name, 'Primary')
            store = engine.get(engine.all_stores[0][0])
            job = store.run_ddb_verification(incremental_verification=False,
                                             quick_verification=False, use_scalable_resource=self.use_scalable)
            self.verification_jobs.append(job)
            log_line += f'{policy.storage_policy_name}: {job.job_id}, '
        self.log.info('Jobs : %s', log_line)

    def wait_for_jobs(self, job_list):
        """Waits Till all Jobs in list are Completed

        Args:
            job_list(list):     List of jobs
        """
        self.log.info("Waiting for the Jobs to be completed")
        for job in job_list:
            job.wait_for_completion()
        self.log.info('Jobs Completed')

    def check_bad_chunks(self):
        """Checks the Chunks Marked as Bad or Not"""
        query = '''select archChunkId, SIDBStoreId from archChunkDDBDrop
                where SIDBStoreId in (%s)''' % (','.join(self.sidb_stores))
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        dropped_chunks = set()
        for row in rows:
            dropped_chunks.add((row[0], row[1]))
        sub_case = 0
        for chunk_set in self.effected_chunk_sets:
            self.log.info('SubCase: %d(StoreId:%s)', sub_case + 1, self.sidb_stores[sub_case])
            marked_count = 0
            log_line = ''
            for index in chunk_set:
                chunk_and_sidb = (self.chunk_lists[sub_case][index][0], self.sidb_stores[sub_case])
                if chunk_and_sidb in dropped_chunks:
                    log_line += f'{self.chunk_lists[sub_case][index][0]}, '
                    marked_count += 1
            self.log.info('Chunks: %s : Marked as Bad', log_line)
            sub_case += 1
            if marked_count == len(chunk_set):
                self.chunk_mark_flags.append(1)
            elif marked_count == 0:
                self.chunk_mark_flags.append(-1)
            else:
                self.chunk_mark_flags.append(0)

    def check_data_verification_status(self):
        """Checks the DataVerification Status of the Backup Jobs"""
        for job in self.backup_jobs:
            query = '''select distinct archCheckStatus
            from JMJobDataStats
            where jobId = {0}'''.format(job.job_id)
            self.csdb.execute(query)
            rows = self.csdb.fetch_all_rows()
            result = [row[0] for row in rows]
            self.verification_statuses.append(result)
        self.log.info('Job DV STATUS %s:', str(self.verification_statuses))

    def produce_result(self):
        """Produces Result"""
        self.log.info('********************* VALIDATIONS **********************')
        # 1: All Chunks Marked, -1: All Not Marked, 0: Few Marked
        expected_chunk_mark_flags = [1, 1, 1, 1, 1, 1, -1, -1, 1]
        # JMJobDataStatsEntries: 6: DV Failed, 5: Success, 0: Not Picked, Other- Partial or Unknown
        expected_statuses = ['6', '6', '6', '6', '6',  '6', '6', '6', '6']
        self.result_string = ''
        for sub_case in range(1, 10):
            case_string_1 = f'SUB_CASE {sub_case}: {self.sub_cases[sub_case - 1]} '
            case_string_2 = case_string_1
            if expected_chunk_mark_flags[sub_case - 1] == self.chunk_mark_flags[sub_case - 1]:
                case_string_1 += ': MARKING CHUNKS: VALIDATION: PASSED'
                self.log.info(case_string_1)
            else:
                case_string_1 += ': MARKING CHUNKS: VALIDATION: FAILED'
                self.log.error(case_string_1)
                self.result_string += f'{case_string_1}\n'
            # job dv
            if (expected_statuses[sub_case - 1] in self.verification_statuses[sub_case - 1]) \
                    or (sub_case == 6 and expected_statuses[sub_case - 1] not in self.verification_statuses[sub_case - 1]):
                case_string_2 += ': DV STATUS: VALIDATION: PASSED'
                self.log.info(case_string_2)
            else:
                case_string_2 += ': DV STATUS: VALIDATION: FAILED'
                self.log.error(case_string_2)
                self.result_string += f'{case_string_2}\n'
        if self.result_string:
            self.status = constants.FAILED
