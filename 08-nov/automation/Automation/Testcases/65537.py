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

    init_tc()       -- Initial configuration for the test case using command center

    clean_test_environment() --  To perform cleanup operation before setting the environment and
                                 after testcase completion

    setup()         --  setup function of this test case

    configure_tc_environment() -- Create storage pool, storage policy and associate to subclient

    run_backups() -- Run backups on subclients based on number of jobs required

    run_backup() -- Runs backup by generating new content to get unique blocks for dedupe backups

    identify_chunks()   -- fetches the chunks from that are created by the backup jobs

    identify_paths_of_chunks()  -- identifies the full paths of the chunks created

    makes_alterations() -- control function for making alterations required for each sub-cases

    select_chunks_to_alter() -- selects the chunks that needs to be altered for each sub-case

    alter()     --  performs the required operations (delete/corrupt the files/directories)

    get_sfile() --  for sfile cases, returns the sfile_contianer that needs to be altered

    set_regkey() -- method to set regkey nSynthfullDoQuery on media agent

    run_verification_jobs() --  initiates Full DV2 for each of the storage policies

    run_synthetic_full_job() --  run synthetic full jobs

    check_data_verification_status()    --  checks data verification status of backup jobs

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Sample Input:
    "65537": {
          "ClientName": "client anme",
          "MediaAgentName": "Media Agent Name",
          "AgentName": "File System"
          **Optional**
          "mount_path": "mount path"
          "dedup_path": "dedupe path"
          "content_path": "content path"
        }

Steps:
    -> clean the testcase environment
    -> Configure test case environment
        a. Create storage pool with 2 partitions
        b. Create 2 storage policies
        c. Create backupset, subclient and content path
    -> Generate data in content path and run multiple backups on first storage policy -> 1 full, 2 incrementals
    -> Identify chunks for respective jobs
    -> Make altercations to chunks so data is corrupted -> later the sfile containers
    -> Run Full DV2 to mark the chunks bad
    -> Set regkey nSynthfullDoQuery to 0 (disabled) on MA
        > synthfull jobs will not query the DDB in this configuration
        > but we expect synthfull job to fail in this configuration in case there are chunk errors
    -> Run synthetic full job: job should fail with dedupe error
    -> Generate data in content path and run multiple backups on second storage policy -> 1 full, 2 incrementals
    -> Run synthetic full job and make sure job completes successfully -> since there is no chunk corruption
       without querying the DDB because of regkey
    -> Run restore job and make sure it completes successfully
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from MediaAgents.MAUtils.mahelper import MMHelper, DedupeHelper
from AutomationUtils.machine import Machine
from Web.Common.page_object import TestStep, handle_testcase_exception
from random import randint
import time


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""
    test_step = TestStep()

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.name = "Synthetic full and restores with regkey nSynthfullDoQuery"
        self.mmhelper = None
        self.dedup_helper = None
        self.common_util = None
        self.client_machine = None
        self.content_path = None
        self.backupset_name = None
        self.subclient_name = None
        self.storage_pool_name = None
        self.storage_policy_name = None
        self.subclient_obj_list = []
        self.backup_job_list = []
        self.utility = None
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.ddb_path = None
        self.dest_ma = None
        self.ma_machine = None
        self.ma_path = None
        self.storage_pool = []
        self.storage_policy_list = []
        self.content_path_list = []
        self.mount_path = None
        self.ma_client = None
        self.backup_jobs = []
        self.query_results = []
        self.copy_id = None
        self.chunk_lists = []
        self.volume_sets = []
        self.effected_chunk_sets = []
        self.verification_statuses = []
        self.restore_path = None
        self.ma_machine_name = None
        self.mmconfig_value = []
        self.sidb_store_id = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.mmhelper = MMHelper(self)
        self.common_util = CommonUtils(self)
        self.utility = OptionsSelector(self.commcell)
        self.client_machine = Machine(self.client.client_name, self.commcell)
        client_drive = self.utility.get_drive(self.client_machine, 2048)
        client_path = self.client_machine.join_path(client_drive, 'testcontent_' + str(self.id))
        self.restore_path = self.client_machine.join_path(client_path, 'Restores')
        self.ma_machine_name = self.tcinputs['MediaAgentName']
        self.ma_machine = Machine(self.ma_machine_name, self.commcell)

        # Inputs from User
        self.content_path = self.tcinputs.get("content_path")

        if self.tcinputs.get('mount_path'):
            self.is_user_defined_mp = True
        if self.tcinputs.get('source_dedup_path'):
            self.is_user_defined_dedup = True

        if not self.is_user_defined_mp or not self.is_user_defined_dedup:
            ma_1_drive = self.utility.get_drive(self.ma_machine, size=20 * 1024)
            self.ma_path = self.ma_machine.join_path(ma_1_drive, 'test_' + str(self.id))

        if not self.is_user_defined_mp:
            self.mount_path = self.ma_machine.join_path(self.ma_path, "MP")
        else:
            self.mount_path = self.ma_machine.join_path(
                self.tcinputs['mount_path'], 'test_' + self.id, 'MP')

        if not self.is_user_defined_dedup and "unix" in self.ma_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if self.is_user_defined_dedup:
            self.log.info("custom source dedup path supplied")
            self.ddb_path = self.ma_machine.join_path(self.tcinputs["source_dedup_path"],
                                                      'test_' + self.id, "DDB")
        else:
            self.ddb_path = self.ma_machine.join_path(self.ma_path + "DDBs")

        self.log.info(f"Source DDB path : {self.ddb_path}")

        # names of various entities
        self.backupset_name = f"bkpset_tc_{self.id}"
        self.subclient_name = f"subc_tc_{self.id}"
        self.storage_policy_name = f"sp_tc_{self.id}"
        self.storage_pool_name = f"storage_pool_tc_{self.id}"
        self.dedup_helper = DedupeHelper(self)
        self.ma_client = self.commcell.clients.get(self.tcinputs.get("MediaAgentName"))

        # disable ransomeware only if it is windows and update mmconfigs so that the changes take effect immediately
        self.mmhelper.update_mmconfig_param('MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN', 5, 5)
        self.mmhelper.update_mmconfig_param('MMS2_CONFIG_STRING_MARK_JOBS_BAD', 0, 0)
        self.mmhelper.update_mmconfig_param('MMCONFIG_MARK_JOB_VERIFICATION_FAILED_FOR_READ_ERRORS', 0, 1)
        if self.ma_machine.os_info.lower() == 'windows':
            self.log.info('Disabling Ransomware protection on MA')
            self.commcell.media_agents.get(
                self.tcinputs.get('MediaAgentName')).set_ransomware_protection(False)

    @test_step
    def clean_test_environment(self):
        """
        Clean up test environment
        """
        try:
            self.log.info("** STEP: Cleaning up test environment **")

            if self.content_path_list:
                for idx in range(0, len(self.content_path_list)):
                    if self.client_machine.check_directory_exists(self.content_path_list[-1]):
                        self.log.info(f"Deleting already existing content directory {self.content_path_list[idx]}")
                        self.client_machine.remove_directory(self.content_path_list[idx])

            if self.client_machine.check_directory_exists(self.restore_path):
                self.log.info(f"Deleting existing restore directory {self.restore_path}")
                self.client_machine.remove_directory(self.restore_path)

            # check for sp with same name if pre-existing with mark and sweep enabled
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info(f"Deleting backupset {self.backupset_name}")
                self.agent.backupsets.delete(self.backupset_name)

            for num in range(1, 3):
                storage_policy = self.storage_policy_name + f'_{num}'
                if self.commcell.storage_policies.has_policy(storage_policy):
                    self.log.info(f"deleting storage policy: {storage_policy}", )
                    sp_obj = self.commcell.storage_policies.get(storage_policy)
                    sp_obj.reassociate_all_subclients()
                    self.commcell.storage_policies.delete(storage_policy)

            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.log.info(f"deleting storage pool: {self.storage_pool_name}")
                self.commcell.storage_pools.delete(self.storage_pool_name)

            self.commcell.refresh()

            self.log.info("Cleanup completed")

        except Exception as excp:
            self.log.warning(f"***Failure in Cleanup with error {excp}***")

    @test_step
    def configure_tc_environment(self):
        """Create storage pool, storage policy and associate to subclient"""
        self.log.info("** STEP: Configuring Testcase environment **")
        self.storage_pool, self.storage_policy_list, self.content_path_list, self.subclient_obj_list \
            = self.dedup_helper.configure_mm_tc_environment(
            self.ma_machine,
            self.ma_machine_name,
            self.mount_path,
            self.ddb_path,
            2,
            same_path=False,
            num_policies=2
        )
        self.sidb_store_id = self.dedup_helper.get_sidb_ids(
            self.storage_pool.storage_pool_id, 'Primary')[0]

    @test_step
    def run_backups(self, subclient_idx):
        """
        Run backups on subclients based on number of jobs required
        param:
            subclient_idx (int)  : index of the subclient from subclient list from which to run backups
        """
        self.log.info("Running full backup followed by incremental backups")
        self.backup_jobs.append(self.run_backup())
        for _ in range(0, 4):
            job = self.run_backup(backup_type="incremental", subclient_idx=subclient_idx)
            self.backup_jobs.append(job)

    def run_backup(self,
                   backup_type="FULL",
                   size=1,
                   subclient_idx=0):
        """
        This function runs backup by generating new content to get unique blocks for dedupe backups
        Args:
            backup_type (str): type of backup to run
            size (float): size of backup content to generate
            subclient_idx (int)  : index of the subclient from subclient list from which to run backups

        Returns:
            job (object) -- returns job object to backup job
        """
        # add content
        self.mmhelper.create_uncompressable_data(self.tcinputs["ClientName"],
                                                 self.content_path_list[subclient_idx], size)
        self._log.info("Running %s backup...", backup_type)
        job = self.subclient_obj_list[subclient_idx].backup(backup_type)
        self._log.info("Backup job: %s", job.job_id)
        if not job.wait_for_completion(timeout=20):
            raise Exception(
                f"Failed to run {backup_type} backup with error: {job.delay_reason}"
            )
        self._log.info("Backup job completed.")
        return job

    @test_step
    def set_regkey(self):
        """
        Method to set regkey nSynthfullDoQuery on media agent
        """
        self.log.info("Setting regkey nSynthfullDoQuery to 0 (disabled) on media agent")
        self.ma_client.add_additional_setting("MediaAgent", "nSynthfullDoQuery", 'INTEGER', '0')
        self.log.info(f"Successfully set regkey on MA {self.ma_client.name}")

    @test_step
    def identify_chunks(self):
        """Identifies the Chunks Created for the Backup Jobs and forms a 2D List"""
        self.log.info("Fetching the Chunks for BackupJobs from the DB")
        self.copy_id = self.storage_policy_list[0].get_copy('Primary').copy_id
        for index in range(5):
            self.query_results.append(
                self.mmhelper.get_chunks_for_job(
                    self.backup_jobs[index].job_id, self.copy_id,
                    afile_type=1))

    @test_step
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

    @test_step
    def make_alterations(self):
        """Alters Chunks and Volumes According to Cases"""
        for sub_case in range(1, 5):
            self.log.info('Alterations for SubCase : %d', sub_case)
            chunk_list = self.chunk_lists[sub_case - 1]
            # sfile container deletion in backup
            effected_chunks = self.select_chunks_to_alter(chunk_list)

            self.alter('SFILE_CONTAINER_random', chunk_list, effected_chunks, 0, 0, 0)

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
        self.log.info("Effected Chunks : %s", log_line)
        return effected_chunks

    def alter(self,
              file_to_be_altered,
              folder_list,
              effected_indices,
              corrupt=0, directory=0,
              append_id=0):
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
                self.ma_machine.delete_file(file_effected)
            elif corrupt == 0 and directory == 1:
                self.ma_machine.remove_directory(file_effected)
            else:
                self.ma_machine.create_file(file_effected, "This file has been corrupted")

    def get_sfile(self, sfile, chunk_path):
        """Returns a sfile from the given Chunk Directory
        Args:
            sfile (str)     :   Sfile Container eg: SFILE_CONTAINER_
            chunk_path (str) :  path of the chunk
        """
        files = self.ma_machine.get_files_in_path(chunk_path)
        sfiles = [
            file.split(self.ma_machine.os_sep)[-1] for file in files if 'SFILE_CONTAINER_' in file]
        if sfile.split('_')[-1] == 'first':
            return sorted(sfiles)[0]
        if sfile.split('_')[-1] == 'random':
            return sfiles[randint(0, len(sfiles) - 1)]
        return sorted(sfiles)[-1]

    @test_step
    def run_verification_jobs(self, incr):
        """Run the Data Verification Job
            Args:
                incr(bool): True or False based on whether to run INCR or FULL DV2
        """
        self.log.info("Running the Verification Job")
        engine = self.commcell.deduplication_engines.get(self.storage_pool_name, 'Primary')
        store = engine.get(engine.all_stores[0][0])
        job = store.run_ddb_verification(incremental_verification=incr, quick_verification=False,
                                         use_scalable_resource=True)
        self.log.info(f"Job id: {job.job_id}")
        if job.wait_for_completion():
            self.log.info("DV2 Completed :Id - %s", job.job_id)
        else:
            raise Exception(f"DV2 job [{job.job_id}] did not complete - [{job.delay_reason}]")

    @test_step
    def run_synthetic_full_job(self,
                               subclient_idx=0,
                               expect_job_pass=True):
        """Runs the Synthetic full Job"""
        self.log.info('Running the Synthetic full Job: ')
        log_line = ''
        job = self.subclient_obj_list[subclient_idx].backup('synthetic_full')
        log_line += f'{self.subclient_obj_list[subclient_idx].subclient_name}: {job.job_id}, '
        self.log.info(f'Job : {log_line}')
        if expect_job_pass:
            self.log.info(f"Waiting for the Job {job.job_id} to be completed")
            retry_count = 0
            while True:
                time.sleep(30)
                if job.is_finished:
                    self.log.info('Synthfull job completed successfully')
                    break
                if job.status.lower() == 'pending':
                    if retry_count == 3:
                        job.kill(wait_for_job_to_kill=True)
                        self.log.error('Killing Job(Id: %s)', job.job_id)
                        raise Exception(f"Synthfull job {job.job_id} did not complete successfully")
                    job.resume(wait_for_job_to_resume=True)
                    retry_count += 1
                if job.status.lower() == 'waiting' and job.phase.lower() == 'synthetic full backup':
                    if retry_count == 3:
                        job.kill(wait_for_job_to_kill=True)
                        self.log.error('Killing Job(Id: %s)', job.job_id)
                        raise Exception(f"Synthfull job {job.job_id} did not complete successfully")
                    job.pause(wait_for_job_to_pause=True)
                    job.resume(wait_for_job_to_resume=True)
                    retry_count += 1
        else:
            self.log.info(f"Synthfull job {job.job_id} is running, this job is expected to fail")
            retry_count = 0
            while not job.is_finished:
                time.sleep(30)

                # get the current status of the job
                status = job.status.lower()
                phase = job.phase.lower()
                if status == 'waiting' and phase == 'synthetic full backup':
                    self.log.info("Synthfull job failed as expected, passing case")
                    self.log.info(f"Job delay reason: {job.delay_reason}")
                    job.kill(wait_for_job_to_kill=True)
                    break

            if job.status.lower() not in ["failed", "killed", "failed to start", "waiting"]:
                self.log.error(f"Synthfull job id: {job.job_id} completed successfully, but was expected to fail")
                raise Exception(f"Failing case as synthfull job was expected to fail as data is corrupted")
            elif job.status in ["failed to start", "killed"]:
                self.log.error(f"Synthfull job id: {job.job_id} was either killed or failed to start")
                raise Exception(f"Failing case as Synthfull job did not fail due to data corruption as expected")
            else:
                if 'read operation failure' or 'deduplication failure' in job.delay_reason.lower():
                    self.log.info(f"Expected failure, job failure reason: {job.delay_reason}")
                    self.log.info("Synthfull job failed as expected, passing case")
                else:
                    self.log.error(f"Job was killed unexpectedly, {job.delay_reason}")
                    raise Exception("Failing cases as synthfull job was killed unexpectedly")

    @test_step
    def run_restore_and_validate(self):
        """
        Run restore and validate restore failure
        """
        job = self.subclient_obj_list[-1].restore_out_of_place(self.client.client_name,
                                                               self.restore_path,
                                                               [self.content_path_list[-1]])

        if job.wait_for_completion(timeout=10):
            self.log.info(f"Restore job id: {job.job_id} completed successfully")
        elif job.status in ["killed", "failed to start", "failed"]:
            self.log.error(f"Restore job id: {job.job_id} was either killed, failed or failed to start")
            raise Exception(f"Failing case as restore job failed")

    def run(self):
        """
        Main function for test case execution
        """
        try:
            self.clean_test_environment()
            self.configure_tc_environment()
            self.run_backups(subclient_idx=0)
            self.identify_chunks()
            self.identify_paths_of_chunks()
            self.make_alterations()
            self.run_verification_jobs(False)
            self.set_regkey()
            self.run_synthetic_full_job(subclient_idx=0, expect_job_pass=False)
            self.run_backups(subclient_idx=1)
            self.run_synthetic_full_job(subclient_idx=1, expect_job_pass=True)
            self.run_restore_and_validate()

        except Exception as exp:
            self.status = constants.FAILED
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear Down Function of this Case"""
        try:
            self.log.info("Removing registry key")
            self.ma_client.delete_additional_setting("MediaAgent", "nSynthfullDoQuery")
            self.clean_test_environment()
            # enable ransomware back only for windows and reset mmconfig to original value
            if self.ma_machine.os_info.lower() == 'windows':
                self.log.info("Enabling Ransomware protection on MA")
                self.commcell.media_agents.get(
                    self.tcinputs.get('MediaAgentName')).set_ransomware_protection(True)

            if self.status != constants.FAILED:
                self.log.info("Test Case PASSED.")
            else:
                self.log.warning("Test Case FAILED.")

        except Exception as excp:
            self.log.info(f"tear_down:: cleanup failed. {str(excp)}")
