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

    initial_setup() --  initial setting Up of storage policies, subclients, library

    get_active_files_store() -- returns active store object for files iDA

    run_backups()            --  initiates backups for each of the subclients

    identify_chunks()        -- fetches the chunks from that are created by the backup jobs

    identify_paths_of_chunks() -- identifies the full paths of the chunks created

    makes_corruptions()        -- control function for making corruptions required for each sub-cases

    select_chunks_to_corrupt() -- selects the chunks that needs to be corrupted for each sub-case

    corrupt()     --  performs the required operations (corrupt the sfile at specified offset)

    get_sfile()   --  for sfile cases, returns the sfile_contianer that needs to be corrupted

    run_verification_jobs() --  initiates Full DV2 for each of the storage policies

    wait_for_jobs()         --  waits for all the jobs that are passed as list to be completed

    check_bad_chunks()      --  checks the chunks that are marked bad in each sub-case

    check_arch_check_status()   --  checks data verification status of backup jobs

    create_primary_dump()       --  creates Dumps for Primary Tables of the Stores

    validate_bad_chunk()        --  validate if bad block is correctly marked or not

    pick_bad_blocks()           --  get the Good and Bad Blocks for given SubCase

    compare_bad_block_offset()  --  check if corrupted offset lies in the Bad Block

    produce_result() -- logs the result for each of the sub-cases

    tear_down()      --  tear down function of this test case

TcInputs to be passed in JSON File:
    "59572": {
        "ClientName"    : Name of a Client - Content to be BackedUp will be created here
        "AgentName"     : File System
        "MediaAgentName": Name of a MediaAgent - we create Libraries here
        ***** Optional: If provided, the below entities will be used instead of creating in TC *****
        "library_name"  : Name of Existing Library to be Used
        "mount_path"    : Path to be used as MP for Library
        "dedup_path"    : Path to be used for creating Dedupe-Partitions
    }

Steps:

1: Configure the environment: a library, 5 Storage Policies, a BackupSet,5 SubClients

2: Run Backups for all the SubClients

3: Identify the Chunks Created for the respective Jobs

4: Make Corruptions to the chunks based on the 5 SubCases we need to test

5: Initiate DV2 for each of DDB Engines

6: Retrieve the Chunks that are marked bad from archChunkDDBDrop table

7: Retrieve the DataVerification Status of Jobs from JMJobDataStats table

8: Dump Primary Tables and retrieve the bad blocks

9: Check whether they Bad Chunks Marking, DV Status Update, Marking Bad Blocks for the jobs has worked as expected

10: CleanUp the Environment
"""
import random
import pandas as pd
from random import randint
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = 'Block-level Health check during DDB Verification'
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.utility = None
        self.mm_helper = None
        self.ma_machine = None
        self.ctrl_machine = None
        self.dedupe_helper = None
        self.client_machine = None
        self.ma_path = None
        self.ddb_path = None
        self.ctrl_path = None
        self.mount_path = None
        self.client_path = None
        self.content_path = None
        self.library_name = None
        self.subclient_name = None
        self.backupset_name = None
        self.storage_policy_name = None
        self.stores = []
        self.sub_cases = []
        self.subclients = []
        self.backup_jobs = []
        self.chunk_lists = []
        self.volume_sets = []
        self.query_results = []
        self.storage_policies = []
        self.verification_jobs = []
        self.effected_chunk_sets = []
        self.offsets = []
        self.dump_path = []
        self.chunk_sfile = []
        self.primary_dumps = []
        self.chunk_mark_flags = []
        self.verification_statuses = []
        self.bad_blocks_validation = []
        self.is_user_defined_mp = False
        self.is_user_defined_lib = False
        self.is_user_defined_dedup = False
        self.result_string = ''
        self.status = constants.PASSED

    def setup(self):
        """Setup function of this test case"""
        self.ctrl_machine = Machine()
        self.ma_machine = Machine(self.tcinputs.get('MediaAgentName'), self.commcell)
        self.client_machine = Machine(self.tcinputs.get('ClientName'), self.commcell)
        self.utility = OptionsSelector(self.commcell)

        if self.tcinputs.get('library_name'):
            self.is_user_defined_lib = True
        if self.tcinputs.get('mount_path'):
            self.is_user_defined_mp = True
        if self.tcinputs.get('dedup_path'):
            self.is_user_defined_dedup = True

        client_drive = self.utility.get_drive(self.client_machine, 10240)
        self.client_path = self.client_machine.join_path(client_drive, f'test_{self.id}')
        self.content_path = self.client_machine.join_path(self.client_path, 'Content')
        if not self.is_user_defined_mp or not self.is_user_defined_dedup:
            ma_drive = self.utility.get_drive(self.ma_machine, 10240)
            self.ma_path = self.ma_machine.join_path(ma_drive, f'test_{self.id}')
        ctrl_drive = self.utility.get_drive(self.ctrl_machine, 2048)
        self.ctrl_path = self.ctrl_machine.join_path(ctrl_drive, f'test_{self.id}')

        suffix = self.tcinputs.get('MediaAgentName')[::-1]
        self.backupset_name = f'{self.id}_BS_{suffix}'
        self.subclient_name = f'{self.id}_SC_{suffix}'
        self.storage_policy_name = f'{self.id}_SP_{suffix}'
        if self.is_user_defined_lib:
            self.log.info("Existing library name supplied")
            self.library_name = self.tcinputs.get("library_name")
        else:
            self.library_name = f"{self.id}_Lib_{suffix}"
            if not self.is_user_defined_mp:
                self.mount_path = self.ma_machine.join_path(self.ma_path, 'MP')
            else:
                self.log.info("custom mount_path supplied")
                self.mount_path = self.ma_machine.join_path(
                    self.tcinputs.get('mount_path'), f'test_{self.id}', 'MP')
        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.ddb_path = self.ma_machine.join_path(self.tcinputs.get("dedup_path"), f'test_{self.id}', "DDBs")
        else:
            if "unix" in self.ma_machine.os_info.lower():
                self.log.error("LVM enabled dedup path must be input for Unix MA!..")
                raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
            self.ddb_path = self.ma_machine.join_path(self.ma_path, "DDBs")

        self.mm_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

        self.sub_cases = ['DedupeBlock Hdr Corrupt', 'DedupeBlock Data corrupt', 'Tag Hdr Corrupt',
                          'Tag Hdr Data corrupt', 'Random Corruption']

    def run(self):
        """Run Function of this case"""
        self.cleanup()
        try:
            self.initial_setup()
            self.get_active_files_store()
            self.run_backups()
            self.wait_for_jobs(self.backup_jobs)
            self.identify_chunks()
            self.identify_paths_of_chunks()
            self.make_corruptions()
            self.run_verification_jobs()
            self.wait_for_jobs(self.verification_jobs)
            self.check_bad_chunks()
            self.check_arch_check_status()
            self.create_primary_dump()
            self.validate_bad_chunk()
            self.produce_result()
        except Exception as exe:
            self.status = constants.FAILED
            self.result_string = str(exe)
            self.log.error('EXCEPTION Occurred : %s', str(exe))

    def cleanup(self):
        """CleansUp the Entities"""
        self.log.info('************************ Clean Up Started *********************************')
        try:
            self.log.info('Deleting Generated Content, Dumps if exists')
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
            if self.ctrl_machine.check_directory_exists(self.ctrl_path):
                self.ctrl_machine.remove_directory(self.ctrl_path)
            self.log.info('Deleting BackupSet if exists')
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
            self.log.info('Deleting Storage Policies if exists')
            for index in range(5, 0, -1):
                if self.commcell.storage_policies.has_policy(f'{self.storage_policy_name}{index}'):
                    self.commcell.storage_policies.get(
                        f'{self.storage_policy_name}{index}').reassociate_all_subclients()
                    self.commcell.storage_policies.delete(f'{self.storage_policy_name}{index}')
            if not self.is_user_defined_lib:
                self.log.info('Deleting Library if exists')
                if self.commcell.disk_libraries.has_library(self.library_name):
                    self.commcell.disk_libraries.delete(self.library_name)
            share_dump_dir_ma = self.ma_machine.join_path(self.ma_path, 'dump_share')
            if self.ma_machine.check_directory_exists(share_dump_dir_ma):
                self.ma_machine.remove_directory(share_dump_dir_ma)
            self.ma_machine.unshare_directory(f'test_share_{self.id}')
            self.ma_machine.unshare_directory(f'test_share_{self.id}_dump')
        except Exception as exe:
            self.log.warning('CleanUp Failed: ERROR: %s', str(exe))

    def initial_setup(self):
        """Initial setting Up of Storage policies, SubClients, Library"""
        for index in range(1, 6):
            self.mm_helper.create_uncompressable_data(
                self.client_machine, self.client_machine.join_path(self.content_path, f'Data{index}'), 0.8, 1)

        if not self.is_user_defined_lib:
            self.mm_helper.configure_disk_library(self.library_name,
                                                  self.tcinputs.get('MediaAgentName'),
                                                  self.mount_path)

        for index in range(1, 6):
            self.storage_policies.append(self.dedupe_helper.configure_dedupe_storage_policy(
                f'{self.storage_policy_name}{index}', self.library_name,
                self.tcinputs.get('MediaAgentName'),
                self.ma_machine.join_path(self.ddb_path, f'Dir{index}'),
                self.tcinputs.get('MediaAgentName')))

        self.mm_helper.configure_backupset(self.backupset_name)
        for index in range(1, 6):
            self.subclients.append(self.mm_helper.configure_subclient(
                self.backupset_name, f'{self.subclient_name}{index}',
                f'{self.storage_policy_name}{index}',
                self.client_machine.join_path(self.content_path, f'Data{index}')))

        self.mm_helper.update_mmconfig_param('MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN', 5, 5)
        if self.ma_machine.os_info.lower() == 'windows':
            self.log.info('Disabling Ransomware protection on MA')
            self.commcell.media_agents.get(
                self.tcinputs.get('MediaAgentName')).set_ransomware_protection(False)

    def get_active_files_store(self):
        """returns active store object for files iDA"""
        self.commcell.deduplication_engines.refresh()
        for policy in self.storage_policies:
            engine = self.commcell.deduplication_engines.get(policy.storage_policy_name, 'primary')
            if engine:
                self.stores.append(engine.get(engine.all_stores[0][0]))

    def run_backups(self):
        """Runs Backup Jobs on the subclients"""
        self.log.info('Running Full Backups')
        for index in range(5):
            self.backup_jobs.append(self.subclients[index].backup())
            self.log.info('Backup Job(Id: %s) Started. (SubClient: %s, Policy: %s, StoreId: %s)',
                          self.backup_jobs[index].job_id, f'{self.subclient_name}{index}',
                          f'{self.storage_policy_name}{index}', self.stores[index].store_id)
        self.log.info('Completed Initiating all Full Backups')

    def identify_chunks(self):
        """Identifies the Chunks Created for the Backup Jobs """
        self.log.info("Fetching the Chunks for BackupJobs from the DB")
        for index in range(5):
            self.query_results.append(
                self.mm_helper.get_chunks_for_job(
                    self.backup_jobs[index].job_id,
                    self.storage_policies[index].get_copy('Primary').copy_id, afile_type=1))

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
            if self.ma_machine.os_info == 'WINDOWS':
                for volume in volume_set:
                    self.ma_machine.modify_ace('Everyone', volume[1],
                                               'DeleteSubdirectoriesAndFiles', 'Deny', remove=True, folder=True)
                    self.ma_machine.modify_ace('Everyone', volume[1], 'Delete', 'Deny', remove=True, folder=True)

    def make_corruptions(self):
        """Corrupts Chunks and Volumes According to Cases
        DBH = Dedupe Block Hdr
        DBD = Dedupe Block Data
        TH  = Tag Hdr
        THD = Tag Hdr Data
        """
        self.log.info('Fetch Absolute Path of CV_MAGNETIC directory and share it')
        query = f"""select	MountPathName
                from	MMMountPath mp, MMLibrary ml
                where	mp.LibraryId = ml.LibraryId
                and ml.AliasName = '{self.library_name}'"""
        self.log.info("Executing Query: %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", result[0])
        self.ma_machine.share_directory(f'test_share_{self.id}',
                                        self.ma_machine.join_path(self.mount_path, result[0], 'CV_MAGNETIC'))

        for sub_case in range(1, 6):
            self.log.info('Corruptions for SubCase[%d] : %s', sub_case, self.sub_cases[sub_case - 1])
            chunk_list = self.chunk_lists[sub_case - 1]
            effected_chunks_indices = self.select_chunks_to_corrupt(chunk_list)

            randoff = 16 * (random.randint(10, 1000))
            self.offsets = [560, 400, 144, 224, randoff]
            self.corrupt(chunk_list, effected_chunks_indices, self.offsets[sub_case-1])
            self.effected_chunk_sets.append(effected_chunks_indices)
            self.log.info('Corrupted Chunk and SFile pair: %s', self.chunk_sfile[-1])

    def select_chunks_to_corrupt(self, chunk_list):
        """Selects Chunks at random that need to be corrupted

        Args:
            chunk_list (list): List of chunks for a subcase
        Returns:
            (set):  Set of indices of the chunks on which corruptions will be done for the subcase
        """
        limit = 1  # no of chunks to select
        effected_chunks_indices = set()
        length = len(chunk_list)
        log_line = ''
        while limit > len(effected_chunks_indices):
            index = randint(0, length - 1)  # to randomize the selection
            if index not in effected_chunks_indices:
                if self.ma_machine.check_file_exists(self.ma_machine.join_path(chunk_list[index][1],
                                                                               'SFILE_CONTAINER.idx')):
                    effected_chunks_indices.add(index)
                    log_line += f'{chunk_list[index][0]}, '
        self.log.info('Effected Chunks : %s', log_line)
        return effected_chunks_indices

    def corrupt(self, folder_list, effected_indices, offset):
        """Corrupts the Files/Directory

        Args:
            folder_list(list)     : List of folders on which corruptions will be done

            effected_indices(set) : Set of indices of chunks on which the corruptions will be done

            offset                : offset at which the corruption will be made
        """
        for index in effected_indices:
            chunk_path_ma = folder_list[index][1]
            # copy chunk from ma to controller using network path
            chunk_split_path = chunk_path_ma.split(f'CV_MAGNETIC{self.ma_machine.os_sep}')[1]
            chunk_path_unc = self.ma_machine.join_path(f'\\\\{self.ma_machine.machine_name}',
                                                       f'test_share_{self.id}', chunk_split_path)

            self.log.info("Copying chunk[%s] to controller directory: [%s]", chunk_path_ma, self.ctrl_path)
            self.ctrl_machine.copy_folder(
                source_path=chunk_path_unc, destination_path=self.ctrl_path, username='', password='')

            # select an sfile in the chunk for corruption
            sfile = self.get_sfile(chunk_path_ma)

            ctrl_dest_dir = self.ctrl_machine.join_path(self.ctrl_path, f'CHUNK_{folder_list[index][0]}')
            self.log.info("Corrupt SFile[%s] at offset[%d]", self.ctrl_machine.join_path(ctrl_dest_dir, sfile), offset)
            dummy_data_16bytes = bytes("ThisIsCorruption", 'ascii')
            file_obj = open(self.ctrl_machine.join_path(ctrl_dest_dir, sfile), "r+b")
            file_obj.seek(offset)
            file_obj.write(dummy_data_16bytes)
            file_obj.close()

            self.log.info("Remove original sfile on ma and copy corrupted sfile from controller to ma")
            self.ma_machine.delete_file(self.ma_machine.join_path(chunk_path_ma, sfile))
            self.ma_machine.copy_from_local(self.ctrl_machine.join_path(ctrl_dest_dir, sfile), chunk_path_ma)

            self.chunk_sfile.append((folder_list[index][0], int(sfile.split('_')[2])))

    def get_sfile(self, chunk_path):
        """Returns a sfile from the given Chunk Directory

        Args:
            chunk_path (str): Absolute Path of the chunk
        """
        files = self.ma_machine.get_files_in_path(chunk_path)
        sfiles = [file.split(self.ma_machine.os_sep)[-1] for file in files if 'SFILE_CONTAINER_' in file]
        return sfiles[randint(0, len(sfiles) - 1)]  # picks a random sfile

    def run_verification_jobs(self):
        """Runs the Verification Jobs"""
        self.log.info('Running the Verification Jobs')
        log_line = ''
        for index in range(0, len(self.stores)):
            self.stores[index].refresh()
            job = self.stores[index].run_ddb_verification(incremental_verification=False, quick_verification=False)
            self.verification_jobs.append(job)
            log_line += f'{self.storage_policies[index].storage_policy_name}: {job.job_id}, '
        self.log.info('Jobs : %s', log_line)

    def wait_for_jobs(self, job_list):
        """Waits Till all Jobs in list are Completed

        Args:
            job_list(list):     List of jobs
        """
        self.log.info("Waiting for the Jobs to be completed")
        for job in job_list:
            self.log.info("Waiting for Job: %s", job.job_id)
            job.wait_for_completion()
        self.log.info('Jobs Completed')

    def check_bad_chunks(self):
        """Checks the Chunks Marked as Bad or Not"""
        query = f'''select archChunkId, SIDBStoreId from archChunkDDBDrop
                where SIDBStoreId in ({','.join([str(store.store_id) for store in self.stores])})'''
        self.log.info("Executing query: %s", query)
        self.csdb.execute(query)
        rows = self.csdb.fetch_all_rows()
        self.log.info("Result: %s", str(rows))
        dropped_chunks = set()
        for row in rows:
            dropped_chunks.add((row[0], row[1]))
        sub_case = 0
        for chunk_set in self.effected_chunk_sets:
            self.log.info('SubCase %d: %s(StoreId:%s)',
                          sub_case + 1, self.sub_cases[sub_case], self.stores[sub_case].store_id)
            marked_count = 0
            log_line = ''
            for index in chunk_set:
                chunk_and_sidb = (self.chunk_lists[sub_case][index][0], str(self.stores[sub_case].store_id))
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

    def check_arch_check_status(self):
        """Checks the DataVerification Status of the Backup Jobs"""
        for job in self.backup_jobs:
            query = f'''select distinct archCheckStatus
                    from JMJobDataStats
                    where jobId = {job.job_id}'''
            self.log.info("Executing Query: %s", query)
            self.csdb.execute(query)
            rows = self.csdb.fetch_all_rows()
            self.log.info("Result: %s", str(rows))
            result = [row[0] for row in rows]
            self.verification_statuses.append(result)
        self.log.info('Backup job DV status %s:', str(self.verification_statuses))

    def create_primary_dump(self):
        """Creates Dumps for Primary Tables of the Stores"""
        # create dump dir on ma and share it.
        share_dump_dir_ma = self.ma_machine.join_path(self.ma_path, 'dump_share')
        self.ma_machine.create_directory(share_dump_dir_ma, force_create=True)
        self.ma_machine.share_directory(f'test_share_{self.id}_dump', share_dump_dir_ma)
        dump_dir_ma = self.ma_machine.join_path(share_dump_dir_ma, 'dump_path')
        self.log.info("The primary dumps will be created on at: %s", dump_dir_ma)
        self.ma_machine.create_directory(dump_dir_ma)
        for index in range(5):
            self.dedupe_helper.get_sidb_dump(self.tcinputs.get("MediaAgentName"), 'primary',
                                             self.stores[index].store_id,
                                             self.ma_machine.join_path(dump_dir_ma, f'primary_{index}.csv'), split=0)
        # copy the dump to controller
        self.log.info("Completed creating primary dumps. Copying the dump directory to controller")
        dump_path_unc = self.ma_machine.join_path(f'\\\\{self.ma_machine.machine_name}',
                                                  f'test_share_{self.id}_dump', 'dump_path')
        self.ctrl_machine.copy_folder(
            source_path=dump_path_unc, destination_path=self.ctrl_path, username='', password='')
        for index in range(5):
            self.dump_path.append(self.ctrl_machine.join_path(self.ctrl_path, 'dump_path', f'primary_{index}.csv'))
        self.log.info("The primary dumps created & copied: %s", self.dump_path)

    def validate_bad_chunk(self):
        """Validate if bad block is correctly marked or not"""
        off = 0
        for sub_case in range(5):
            good_blocks, bad_blocks = self.pick_bad_blocks(sub_case)
            self.log.info('Bad blocks: %s', bad_blocks)
            self.compare_bad_block_offset(sub_case, off, bad_blocks)
            off = off + 1

    def pick_bad_blocks(self, sub_case):
        """Get the Good and Bad Blocks for given SubCase

        Args:
            sub_case    (int): SubCase for which bad blocks needs to be fetched
        """
        data = pd.read_csv(self.dump_path[sub_case], index_col=False, usecols=[' chunkId ', ' id ',
                                                                               ' flags ', ' objMetaOffset '])
        d_f = pd.DataFrame(data)
        chunk_data = d_f.loc[(d_f[' chunkId '] == int(self.chunk_sfile[sub_case][0]))]
        bad_blocks = []
        good_blocks = []
        for x, row in chunk_data.iterrows():
            if (row[' objMetaOffset '] >> 32) == int(self.chunk_sfile[sub_case][1]):
                if row[' flags '] & 1024:
                    good_blocks.append(row[' id '])  # add id to good blocks
                else:
                    bad_blocks.append(row[' id '])  # add id to bad

        return good_blocks, bad_blocks

    def compare_bad_block_offset(self, index, off, bad_blocks):
        """check if corrupted offset lies in the Bad Block"""
        data = pd.read_csv(self.dump_path[index], index_col=False, usecols=[' id ', ' size ', ' objMetaOffset '])
        d_f1 = pd.DataFrame(data)
        bad_chunk = d_f1.loc[(d_f1[' id '] == int(bad_blocks[0]))]
        obj_meta_offset = int(bad_chunk[' objMetaOffset '].iloc[0])
        size = int(bad_chunk[' size '].iloc[0])
        self.log.info("Bad Block Details: objMetaOffset: [%d], size: [%s]", obj_meta_offset, size)
        if (int(obj_meta_offset & 0xFFFFFFFF)) <= (int(self.offsets[off])) <= \
                (int(obj_meta_offset & 0xFFFFFFFF) + size):
            self.log.info("Offset and bad block comparison passed. Corrupted offset lies in the bad block marked")
            self.bad_blocks_validation.append(True)
        else:
            self.log.error("Offset and bad block comparison failed. Corrupted offset doesn't lie in bad block marked")
            self.bad_blocks_validation.append(False)

    def produce_result(self):
        """Produces Result"""
        self.log.info('********************* VALIDATIONS **********************')
        # 1: All Chunks Marked, -1: All Not Marked, 0: Few Marked
        expected_chunk_mark_flags = [1, 1, 1, 1, 1]
        # JMJobDataStatsEntries: 6: DV Failed, 5: Success, 0: Not Picked, Other- Partial or Unknown
        expected_statuses = ['6', '6', '6', '6', '6']
        for sub_case in range(1, 6):
            case_string_1 = case_string_2 = case_string_3 = f'SUB_CASE {sub_case}: {self.sub_cases[sub_case - 1]}'
            # bad chunks
            if expected_chunk_mark_flags[sub_case - 1] == self.chunk_mark_flags[sub_case - 1]:
                case_string_1 += ': Chunks were marked bad. Validation : PASSED'
                self.log.info(case_string_1)
            else:
                case_string_1 += ': Chunks were not marked bad. Validation : FAILED'
                self.log.error(case_string_1)
                self.result_string += case_string_1
            # bad blocks
            if self.bad_blocks_validation[sub_case - 1]:
                case_string_2 += ': Bad Blocks. Validation: PASSED '
                self.log.info(case_string_2)
            else:
                case_string_2 += ': Bad Blocks. Validation: FAILED'
                self.log.error(case_string_2)
                self.result_string += f'{case_string_2}\n'
            # job dv status
            if expected_statuses[sub_case - 1] in self.verification_statuses[sub_case - 1]:
                case_string_3 += ': Backup Job DV status. Validation: PASSED '
                self.log.info(case_string_3)
            else:
                case_string_3 += ': Backup Job DV status. Validation: FAILED'
                self.log.error(case_string_3)
                self.result_string += f'{case_string_3}\n'
        if self.result_string:
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down Function of this case"""
        if self.status == constants.FAILED:
            self.log.warning("TC Failed. Cleaning up Entities. Please check logs for debugging")
        else:
            self.log.info("TC Passed. Cleaning up the Entities")
        self.cleanup()
        if self.ma_machine.os_info.lower() == 'windows':
            self.log.info('Enabling Ransomware protection on MA')
            self.commcell.media_agents.get(
                self.tcinputs.get('MediaAgentName')).set_ransomware_protection(True)
