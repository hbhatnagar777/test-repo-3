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

    previous_run_cleanup() -- for deleting the left over
    backupset and storage policy from the previous run

    get_active_files_store() -- gets store object so you can properly get store id

    create_resources()  -- create the entities needed for testcase

    get_chunks_af() -- this function will get the archFiles and chunks of the supplied job id

    get_chunk_details() -- takes job id and returns dict with sfile sizes

    drilled_hole_check() -- make sure all drilled sfile sizes are smaller than original

    restore_job_verify() -- restore job verification for the testcase

    wait_for_phase3_pruning() -- check if phase 3 pruning has taken place

    run_backup() -- runs a backup job

    get_table_row_count() -- runs query on given table name

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

This testcase verifies if the physical pruning
is taking place or not, even if one chunk
belonging to the backup job is pruned
using drill hole method this testcase will pass.

input json file arguments required:
                "47021": {
                        "ClientName": "name of the client machine ",
                        "AgentName": "File System",
                        "dedup_path": "/mat36MP1/automationDDBs",
                        "MediaAgentName": "name of the media agent "
                        }

            dedup_path is only necessary when running on a linux mediaagent

Design Steps:
1.1	Change mm prune process interval to 2 min
1.2 check if any reg key to disable drill hole has been set - if yes remove it.
2.	Create resources
    To increase the chances of drill hole deletion happening,
        we generate 100 subdirectories, each with 10 MB of unique data.
        we set subclient content as each of those 100 subdirectories
        data for second backup job - we change subclient content by removing every other subdirectory

4.	Subclient level: data reader streams : 1

4.1	First backup job , get the sidb id,
        archfiles., chunks -> first backup job
4.2	Delete every alternate folder from subclient content path
4.3	Second backup job
4.4	Delete first backup job
5.  verify phase 2 pruning occurred
6.  add reg key to force MS to run next time sidb2 comes up
7.  run backup to force sidb2 to come up
8.  remove reg key
Checks for drill hole
9.  verify phase 3 pruning ran
10.	verify holes drilled by parsing sidbphysicaldeletes log
11. verify usagehistory shows pending deletes went to 0
12.  check for reduction in size of all chunk sfiles with holes drilled
13.  compare original source content data to restored data

"""

import time
from AutomationUtils import constants, commonutils, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils import mahelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "drill hole testcase: verifies " \
                    "if the drill hole pruning process is occurring or not"

        self.tcinputs = {
            "MediaAgentName": None
        }

        self.mount_path = None
        self.dedup_store_path = None
        self.dedup_path_base = None
        self.restore_path = None
        self.content_path = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.client_machine = None
        self.media_agent = None
        self.media_agent_machine = None
        self.opt_selector = None
        self.sidb_id = None
        self.testcase_path = None
        self.testcase_path_client = None
        self.backup_set = None
        self.subclient = None
        self.is_user_defined_lib = False
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False
        self.testcase_factor = None
        self.ma_client = None
        self.storage_pool = None
        self.storage_pool_name = None
        self.store_obj = None
        self.content_folders = None
        self.ddb_path = None
        self.sql_password = None
        self.plan_name = None
        self.plan = None
        self.backupset = None
        self.subclient = None

    def setup(self):
        """sets up the variables to be used in testcase"""

        self.storage_pool_name = f'{str(self.id)}_POOL_{self.tcinputs.get("MediaAgentName")}'
        self.backupset_name = f'{str(self.id)}_BS_{self.tcinputs.get("MediaAgentName")}'
        self.subclient_name = f'{str(self.id)}_SC_{self.tcinputs.get("MediaAgentName")}'
        self.plan_name = f'{str(self.id)}_PLAN_{self.tcinputs.get("MediaAgentName")}'
        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = machine.Machine(
            self.client.client_name, self.commcell)
        self.media_agent = self.tcinputs["MediaAgentName"]
        self.media_agent_machine = machine.Machine(
            self.tcinputs["MediaAgentName"], self.commcell)
        drive_path_client = self.opt_selector.get_drive(self.client_machine, 25 * 1024)
        drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine, 25 * 1024)
        self.testcase_path_client = f'{drive_path_client}{self.id}'
        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")
        self.restore_path = self.client_machine.join_path(self.testcase_path_client, "restore_path")
        self.mount_path = self.media_agent_machine.join_path(drive_path_media_agent, "mount_path")
        self.ddb_path = self.media_agent_machine.join_path(drive_path_media_agent, "DDBs")

        # sql connections
        self.sql_password = commonutils.get_cvadmin_password(self.commcell)

    def previous_run_clean_up(self):
        """delete previous run items"""
        self.log.info("********* previous run clean up **********")
        try:
            # delete source content path
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the old source content.")
            else:
                self.log.info("source content directory does not exist.")

            # delete the restored directory
            if self.client_machine.check_directory_exists(self.restore_path):
                self.client_machine.remove_directory(self.restore_path)
                self.log.info("Deleted the old restored data.")
            else:
                self.log.info("Restore directory does not exist.")

            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.backupset = self.agent.backupsets.get(self.backupset_name)
                if self.backupset.subclients.has_subclient(self.subclient_name):
                    self.subclient = self.backupset.subclients.get(self.subclient_name)
                    self.log.info(f'disassociating any plans from subclient {self.subclient_name}')
                    self.subclient.plan = None
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info(f'deleted backupset {self.backupset_name}')
            if self.commcell.plans.has_plan(self.plan_name):
                self.commcell.plans.delete(self.plan_name)
                self.log.info(f'deleted plan {self.plan_name}')
            if self.commcell.storage_pools.has_storage_pool(self.storage_pool_name):
                self.commcell.storage_pools.delete(self.storage_pool_name)
                self.log.info(f'deleted pool {self.storage_pool_name}')
            self.log.info("previous run clean up COMPLETED")
        except Exception as exp:
            self.log.info("previous run clean up ERROR")
            self.log.info(f'ERROR:{exp}')

    def get_active_files_store(self):
        """returns active store object for files iDA"""

        self.commcell.deduplication_engines.refresh()
        dedup_engines_obj = self.commcell.deduplication_engines
        if dedup_engines_obj.has_engine(self.storage_pool_name, 'Primary'):
            dedup_engine_obj = dedup_engines_obj.get(self.storage_pool_name, 'Primary')
            dedup_stores_list = dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                self.store_obj = dedup_engine_obj.get(dedup_store[0])

    def create_resources(self):
        """create the resources for the testcase"""

        # create source content path
        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")
        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")

        # create restore path
        if self.client_machine.check_directory_exists(self.restore_path):
            self.log.info("restore path directory already exists")
            self.client_machine.remove_directory(self.restore_path)
            self.log.info("existing restore path deleted")
        self.client_machine.create_directory(self.restore_path)
        self.log.info("restore path created")

        # create first ddb partition path
        if self.tcinputs.get('dedup_path'):
            self.is_user_defined_dedup = True
        if not self.is_user_defined_dedup and "unix" in self.media_agent_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for a linux MA!")
            raise Exception("LVM enabled dedup path not supplied for a linux MA!")
        if self.is_user_defined_dedup:
            self.dedup_path_base = self.media_agent_machine.join_path(self.tcinputs["dedup_path"],
                                                                      "DDBs", f'tc_{self.id}')
        else:
            self.dedup_path_base = self.media_agent_machine.join_path(self.ddb_path, f'tc_{self.id}')
        self.dedup_store_path = self.media_agent_machine.join_path(self.dedup_path_base, "partition1")
        self.mm_helper.update_mmpruneprocess(db_user="sqladmin_cv", db_password=self.sql_password,
                                             min_value=2, mmpruneprocess_value=2)
        self.log.info("mmprune process interval set to two minutes")

        # remove the disable drill hole reg key if it exists
        self.ma_client = self.commcell.clients.get(self.media_agent)
        self.ma_client.delete_additional_setting("MediaAgent", "DedupDrillHoles")
        if self.media_agent_machine.check_registry_exists(
                'MediaAgent', 'DedupDrillHoles'):
            self.media_agent_machine.remove_registry(
                'MediaAgent', value='DedupDrillHoles')
            self.log.info("removed regkey to disable drillholes!")

        # create Storage Pool
        self.storage_pool = self.commcell.storage_pools.add(self.storage_pool_name, self.mount_path,
                                                            self.media_agent, self.media_agent, self.dedup_store_path)

        # create plan
        self.commcell.storage_pools.refresh()
        self.log.info(f'Creating the plan {self.plan_name}')
        self.plan = self.commcell.plans.add(self.plan_name, "Server", self.storage_pool_name)
        self.commcell.plans.refresh()
        self.log.info(f'Plan {self.plan_name} created')

        # disabling the schedule policy
        self.plan.schedule_policies['data'].disable()

        # get store object
        self.get_active_files_store()
        self.sidb_id = self.store_obj.store_id

        # add partition for dedupe engine
        part2_dir = self.media_agent_machine.join_path(self.dedup_path_base, "partition2")
        if not self.media_agent_machine.check_directory_exists(part2_dir):
            self.media_agent_machine.create_directory(part2_dir)
        self.log.info("adding partition for the dedup store")
        self.plan.storage_policy.add_ddb_partition(self.storage_pool.get_copy().copy_id, str(self.store_obj.store_id),
                                                   part2_dir, self.media_agent)

        # create backupset
        self.backup_set = self.mm_helper.configure_backupset(self.backupset_name, self.agent)

        # generate 100 subdirectories as source content, each with 10 MB of data
        iterations = 0
        while iterations < 100:
            try:
                self.mm_helper.create_uncompressable_data(self.client.client_name,
                                                          self.content_path,
                                                          0.01,
                                                          num_of_folders=1, file_size=10000)
                time.sleep(1)
                iterations += 1
            except:
                self.log.info("something went wrong in creating the source data")
                if iterations >= 10:
                    self.log.info("we created enough data, so continue with the case")
                    break
                else:
                    raise Exception("didnt create enough source content, failing the case")

        # create list of subdirectories to be used as subclient content
        self.content_folders = sorted(
            self.client_machine.get_folders_in_path(self.content_path, recurse=False)
        )
        content_size = self.client_machine.get_folder_size(self.content_path)
        self.log.info(f'number of source content folders before first backup: {len(self.content_folders)}')
        self.log.info(f'size of source content path before first backup: {content_size}')

        # create subclient
        self.subclient = self.backup_set.subclients.add(self.subclient_name)
        self.subclient.data_readers = 1

        # add plan to the subclient
        self.log.info("adding plan to subclient")
        self.subclient.plan = [self.plan, self.content_folders]

    def get_chunks_af(self, job):
        """
            this function will get the archFiles and chunks of the supplied job id.

            Arguments:
                job - job object for which details need to be checked.

            Returns:
                chunks associated with the job, archFiles associated with the job
        """
        query = f"""SELECT    archchunkid 
                FROM      archchunkmapping 
                WHERE     archfileid 
                IN       ( SELECT    id 
                FROM      archfile 
                WHERE     jobid={job.job_id} AND filetype=1)"""

        self.log.info(f'EXECUTING QUERY {query}')
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(f"QUERY OUTPUT : {res}")
        chunks_job = []
        for count, item in enumerate(res):
            chunks_job.append(int(item[0]))
        self.log.info(f'got the chunks belonging to the backup job {job.job_id}')
        self.log.info(f'Chunks are: {chunks_job}')

        query = f"SELECT    id " \
                f"FROM      archFile " \
                f"WHERE     jobId={job.job_id} "
        self.log.info(f'EXECUTING QUERY {query}')
        self.csdb.execute(query)
        res = self.csdb.fetch_all_rows()
        self.log.info(f"QUERY OUTPUT : {res}")
        arch_files_job = []
        for count, item in enumerate(res):
            arch_files_job.append(int(item[0]))
        self.log.info(f"got the archfiles belonging to the backup job {job.job_id}")
        self.log.info(f"Archfiles are:{arch_files_job}")

        return chunks_job, arch_files_job

    def get_chunk_details(self, job):
        """
            -goal here is to record all the chunks and sfiles and their respective sizes for job1, pre-drilling

            Arguments:
                job - first backup job id

            returns:
                chunk_dict
        """
        # dict where each key is a chunkid
        # it will hold a list of 3 elements:
        # chunk_location(str), chunk_size(float), sfile_dict(dict)
        chunk_dict = {}
        os_sep = self.media_agent_machine.os_sep
        chunk_list = self.mm_helper.get_chunks_for_job(job.job_id)

        # first get details for each chunk and store in a dictionary
        for itr in range(len(chunk_list)):
            chunk_location = chunk_list[itr][0] + os_sep + chunk_list[itr][1] + os_sep + 'CV_MAGNETIC' + os_sep + \
                             chunk_list[itr][2] + os_sep + 'CHUNK_' + chunk_list[itr][3]
            chunk_size = self.media_agent_machine.get_folder_size(chunk_location)

            # store chunk's list of sfiles and their details in dictionary
            # each key is an sfile, and value is a list of 2 elements, sfile_location(str) and sfile_size(float)
            sfile_dict = {}
            sfile_list = self.media_agent_machine.get_files_in_path(chunk_location)
            for sfile_location in sfile_list:
                if "unix" in self.media_agent_machine.os_info.lower():
                    sfile_name = sfile_location.rpartition('/')[-1]
                else:
                    sfile_name = sfile_location.rpartition('\\')[-1]
                sfile_size = self.media_agent_machine.get_file_size(sfile_location)
                sfile_dict[sfile_name] = [sfile_location, sfile_size]

            chunk_dict[chunk_list[itr][3]] = [chunk_location, chunk_size, sfile_dict]

        return chunk_dict

    def drilled_hole_check(self, drilled_sfiles, chunk_dict):
        """
        make sure all drilled sfile sizes are smaller than original

        Arguments:
            drilled_sfiles - list of chunk id and sfile that got drilled

            chunk_dict - dictionary of sfile sizes before drilling

        Returns:
            drilled - Boolean
        """
        drilled = True
        for drilled_hole_chunk in drilled_sfiles:
            # chunk with hole drilled = drilled_hole_chunk[0]
            # sfile in that chunk with hole drilled = drilled_hole_chunk[1]
            # sfile location = chunk_dict[drilled_hole_chunk[0]][2][sfile_name][0]
            # orig sfile size = chunk_dict[drilled_hole_chunk[0]][2][sfile_name][1]
            # new sfile size = get_folder_size(sfile location)
            if len(str(drilled_hole_chunk[1])) == 1:
                sfile_name = 'SFILE_CONTAINER_00' + str(drilled_hole_chunk[1])
            else:
                sfile_name = 'SFILE_CONTAINER_0' + str(drilled_hole_chunk[1])
            sfile_size_post = self.media_agent_machine.get_file_size(chunk_dict[drilled_hole_chunk[0]][2]
                                                                     [sfile_name][0], size_on_disk=True)
            if sfile_size_post >= chunk_dict[drilled_hole_chunk[0]][2][sfile_name][1]:
                drilled = False
                self.log.info(f'drilled chunk {drilled_hole_chunk[0]} {sfile_name} old size: '
                              f'{chunk_dict[drilled_hole_chunk[0]][2][sfile_name][1]},'
                              f' and new size: 'f'{sfile_size_post} has not shrunk in size')
            else:
                self.log.info(f'drilled chunk {drilled_hole_chunk[0]} {sfile_name} shrunk in size from '
                              f'{chunk_dict[drilled_hole_chunk[0]][2][sfile_name][1]} to '
                              f'{sfile_size_post} as expected')
        return drilled

    def restore_job_verify(self, subclient, restore_path, content_folders):
        """
            restore job verification for the testcase

            Arguments:
                subclient - subclient object on which restore job to be run

                restore_path - location to do out of place restore

                content_folders - list of folders which are content of subclient

            Returns:
                None

        """
        restore_job = subclient.restore_out_of_place(
            self.client.client_name, restore_path, content_folders)
        self.log.info("Restore job: " + str(restore_job.job_id))
        if not restore_job.wait_for_completion():
            if restore_job.status.lower() == "completed":
                self.log.info(f"job {restore_job.job_id} complete")
            else:
                raise Exception(f"Job {restore_job.job_id} Failed with {restore_job.delay_reason}")

        self.log.info("VERIFYING IF THE RESTORED FILES ARE SAME OR NOT")
        restored_folders = self.client_machine.get_folders_in_path(restore_path)
        self.log.info("Comparing the files using MD5 hash")
        if len(restored_folders) == len(content_folders):
            restored_folders.sort()
            content_folders.sort()
            for original_folder, restored_folder in zip(
                    content_folders, restored_folders):
                if self.client_machine.compare_folders(
                        self.client_machine, original_folder, restored_folder):
                    self.log.info("Result: Fail")
                    raise ValueError(
                        "The restored folder is "
                        "not the same as the original content folder")
                else:
                    self.log.info("file hashes are equal")
            self.log.info("Result: Pass")
        else:
            self.log.info("Result: Fail")
            raise Exception("The number of restored files does not match the number of content files")

    def wait_for_phase3_pruning(self, store_id):
        """
            check if phase 3 pruning has taken place

            Arguments:
                store_id - store id of the ddb store for which pruning to be checked.

            Returns:
                True - if phase 3 pruning occurred.
                False - if pruning did not occur.
        """
        pruning_done = False
        for i in range(10):
            self.log.info(f"data aging + sleep for 240 seconds: RUN {i + 1}")

            job = self.mm_helper.submit_data_aging_job(
                copy_name="Primary",
                storage_policy_name=self.plan.storage_policy.storage_policy_name,
                is_granular=True, include_all=False,
                include_all_clients=True,
                select_copies=True,
                prune_selected_copies=True)

            self.log.info(f"Data Aging job: {str(job.job_id)}")
            if not job.wait_for_completion():
                raise Exception(f"Job {job.job_id} Failed with {job.delay_reason}")
            self.log.info(f'Data aging job {str(job.job_id)} completed')
            matched_lines = self.dedup_helper.validate_pruning_phase(store_id, self.tcinputs['MediaAgentName'])
            self.log.info(matched_lines)

            if matched_lines:
                self.log.info(matched_lines)
                self.log.info(f"Successfully validated the phase 3 pruning on sidb - {store_id}")
                pruning_done = True
                break
            else:
                self.log.info(f"No phase 3 pruning activity on sidb - {store_id} yet. Checking after 240 seconds")
                time.sleep(240)

        if not pruning_done:
            self.log.error("Pruning is not over even after 40 minutes")

        return pruning_done

    def run_backup(self, backup_type="FULL", delete_alternative=False):
        """
           this function runs backup and can also modify source content.

        Args:
            backup_type (str): type of backup to run
                Default - FULL

            delete_alternative (bool): to run a backup by deleting alternate content, set True
                Default - False

        Returns:
        (object) -- returns job object to backup job
        """
        if delete_alternative:
            # modify source content by removing every other folder
            temp_folders = []
            # change the content on the subclient for the second backup job
            for i in range(0, len(self.content_folders), 2):
                temp_folders.append(self.content_folders[i])
            self.content_folders = temp_folders
            self.log.info(f'number of source content folders before second backup: {len(self.content_folders)}')
            self.log.info("deleted every alternate folder from the content list ")
            self.log.info("maximises the chance of drill hole taking place while pruning ")

            # add the modified content folders list to subclient
            self.log.info("MODIFIED content folders list added as content to the subclient")
            self.subclient.content = self.content_folders

        self.log.info(f"Running {backup_type} backup...")
        job = self.subclient.backup(backup_type)
        self.log.info(f"Backup job: {job.job_id}")
        if not job.wait_for_completion():
            raise Exception(f"Failed to run {backup_type} backup with error: {job.delay_reason}")
        self.log.info("Backup job completed.")
        return job

    def get_table_row_count(self, table, storeid):
        """ Get distinct AF count for the given table
            Args:
                storeid (object) - storeid
                table (str) - tablename to get count
            Returns:
                num_rows    (int) - number of rows
        """
        query = f"select count(distinct archfileid) from {table} where sidbstoreid  = {storeid} "
        self.log.info(f"Query => {query}")
        self.csdb.execute(query)
        num_rows = int(self.csdb.fetch_one_row()[0])
        self.log.info(f"Output ==> {num_rows}")
        return num_rows

    def run(self):
        """Run function of this test case"""
        try:
            error_flag = []
            self.previous_run_clean_up()
            self.create_resources()

            # run first backup, which we need to track for pruning later
            job1 = self.run_backup()
            time.sleep(30)
            # run second backup, which we don't need to track
            # this backup will delete some source content first to better facilitate drilling holes later
            self.run_backup(delete_alternative=True)

            # get chunkids and afids from first job
            cumulative_arch_files_first_job = self.get_chunks_af(job1)[1]
            cumulative_chunks_first_job = self.get_chunks_af(job1)[0]

            # get all the chunks sfile sizes pre-drilling, from job1
            chunk_dict = self.get_chunk_details(job1)

            # delete job 1
            storage_policy_copy = self.plan.storage_policy.get_copy("Primary")
            storage_policy_copy.delete_job(job1.job_id)
            self.log.info(f"deleted the first backup job id - {job1.job_id}")

            self.log.info("-----------data about the first job run--------------")
            self.log.info(f"Total archFiles from jobs {str(set(cumulative_arch_files_first_job))}")
            self.log.info("-----------------------------------------")
            self.log.info(f"Total chunks from jobs {str(set(cumulative_chunks_first_job))}")

            self.log.info("sleeping for 5 seconds")
            time.sleep(5)

            self.log.info("=====================================================")
            self.log.info("SETUP VALIDATION 1:"
                          " Verify if the deleted job files have been moved to MMdeletedAF")

            query = f"SELECT    archFileId " \
                    f"FROM      MMDeletedAF " \
                    f"WHERE     SIDBStoreId={self.sidb_id} "
            self.log.info(f"EXECUTING QUERY {query}")
            self.csdb.execute(query)
            res = self.csdb.fetch_all_rows()
            self.log.info(f"QUERY OUTPUT : {res}")

            mm_deleted_af_list = []
            for count, item in enumerate(res):
                mm_deleted_af_list.append(int(item[0]))

            if set(cumulative_arch_files_first_job) == set(mm_deleted_af_list):
                self.log.info("Result: Pass")
                self.log.info(
                    "archfiles of first job have been transferred to MMdeletedAF")
            else:
                self.log.error("WARNING: archfiles of deleted job have not been moved to MMDeletedAF")

            self.log.info("----------------------------------------------")
            self.log.info("waiting... to trigger MM Prune Process")

            for i in range(2):
                self.log.info(f"data aging + sleep for 5 seconds: RUN {i + 1}")
                job = self.mm_helper.submit_data_aging_job(
                    copy_name="Primary",
                    storage_policy_name=self.plan.storage_policy.storage_policy_name,
                    is_granular=True, include_all=False,
                    include_all_clients=True,
                    select_copies=True,
                    prune_selected_copies=True)
                self.log.info(f"Data Aging job: {str(job.job_id)}")
                if not job.wait_for_completion():
                    if job.status.lower() == "completed":
                        self.log.info(f"job {job.job_id} complete")
                    else:
                        raise Exception(f"Job {job.job_id} Failed with {job.delay_reason}")
                time.sleep(5)

            # confirm phase 2 pruning is finished
            phase2_pruning_done = False
            iterations = 0
            while not phase2_pruning_done and iterations < 7:
                table_count_mmdel = self.get_table_row_count('mmdeletedaf', self.store_obj.store_id)
                self.log.info(f'Count of AFs in mmdeletedaf table for store {self.store_obj.store_id} '
                              f'is {table_count_mmdel}')
                table_count_mmtracking = self.get_table_row_count('mmdeletedarchfiletracking', self.store_obj.store_id)
                self.log.info(f'Count of AFs in mmdelTracking table for store {self.store_obj.store_id} '
                              f'is {table_count_mmtracking}')
                if table_count_mmdel == 0 and table_count_mmtracking == 0:
                    phase2_pruning_done = True
                    self.log.info(f'phase2 pruning finished successfully for store {self.store_obj.store_id}')
                else:
                    self.log.info(f'iteration {iterations}: {self.store_obj.store_id} still has entries in '
                                  f'mmdel tables, wait 5 minutes and try again')
                    iterations += 1
                    time.sleep(300)
            if not phase2_pruning_done:
                self.log.error(f'FAILURE: phase2 pruning didnt finish for store {self.store_obj.store_id}')
                raise Exception("TC FAILED, phase2 pruning didnt finish")

            # add reg key to force MS to get triggered immediately next time sidb2 comes up
            self.log.info("setting DDBMarkAndSweepRunIntervalSeconds additional setting to 120")
            self.ma_client.add_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds",
                                                  "INTEGER", "120")
            self.log.info("sleeping 15 seconds so reg key is set before backup's sidb2 comes up")
            time.sleep(15)
            self.log.info("running new backup just to trigger MS to run immediately")
            self.run_backup()

            # remove reg key that runs Mark and Sweep immediately
            self.log.info("removing DDBMarkAndSweepRunIntervalSeconds additional setting")
            self.ma_client.delete_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds")

            if not self.wait_for_phase3_pruning(self.sidb_id):
                raise Exception("pruning did not happen")

            log_file = "SIDBPhysicalDeletes.log"
            match_regex = [" H "]
            drill_hole_occurrance = False
            drill_hole_records = []
            self.log.info(
                "=======================================================")
            self.log.info("CASE VALIDATION 1: verify if the drill "
                          "hole occurred for the chunks of the first job")
            self.log.info("sleeping for 5 minutes just in case first phase 3 pruning occurence didnt actually prune "
                          "anything yet")
            time.sleep(300)
            matched_lines, matched_strings = self.dedup_helper.parse_log(
                self.tcinputs['MediaAgentName'], log_file, match_regex[0], single_file=True)

            # parse sidbphysicaldeletes for chunk with drilled hole, and append that and sfile number
            for matched_line in matched_lines:
                line = matched_line.split()
                for commonstring in line:
                    for chunkid in cumulative_chunks_first_job:
                        if commonstring == str(chunkid):
                            drill_hole_occurrance = True
                            drill_hole_records.append([str(chunkid), line[line.index(commonstring) + 1]])

            if drill_hole_occurrance:
                self.log.info("Result: Pass Atleast one chunk"
                              " was deleted by using Drill Hole method")
                self.log.info("Chunk IDs with drilled holes are: ")
                for drilled_hole_chunk in drill_hole_records:
                    self.log.info(f"chunk: {drilled_hole_chunk[0]} sfile: {drilled_hole_chunk[1]}")
            else:
                self.log.info("Result: Fail")
                error_flag += ["No Chunk was deleted using"
                               " Drill Hole method: Drill hole did not occur"]

            time.sleep(30)

            self.log.info(
                "========================================================")
            self.log.info("CASE VALIDATION 2: Check for"
                          " phase 3 count in idxSidbUsageHistory Table")
            query = f"SELECT    ZeroRefCount " \
                    f"FROM      IdxSIDBUsageHistory " \
                    f"WHERE     SIDBStoreId = {self.sidb_id} " \
                    f"AND       HistoryType = 0 " \
                    f"ORDER BY(ModifiedTime) DESC "
            self.log.info(f"EXECUTING QUERY {query}")
            self.csdb.execute(query)
            zero_ref_count_case3 = int(self.csdb.fetch_one_row()[0])
            self.log.info(f"QUERY OUTPUT : {zero_ref_count_case3}")

            if zero_ref_count_case3 == 0:
                self.log.info("Result:Pass")
                self.log.info("Pending delete count is 0")
            else:
                self.log.info("Result:Fail")
                self.log.info("Deletion of items with"
                              " no reference is still pending")
                error_flag += ["pending delete count in"
                               " idxSidbUsageHistory Table is not zero"]

            self.log.info(
                "========================================================")
            self.log.info("CASE VALIDATION 3: Checking if"
                          " there is reduction in physical size of the drilled sfiles")

            # compare sfile size before/after drilling to confirm drilled sfile is smaller now
            drilled_hole_smaller = self.drilled_hole_check(drill_hole_records, chunk_dict)

            if drilled_hole_smaller:
                self.log.info("Result: Pass all drilled chunk sfiles have shrunk in size")
            else:
                self.log.info("Result: Fail")
                error_flag += ["drilled chunk sfile did not shrink in size"]

            self.log.info(
                "=============================================================")
            self.log.info("CASE VALIDATION 4: Running a restore job"
                          " for the second backup and verifying the files")

            self.restore_job_verify(
                    self.subclient, self.client_machine.join_path(
                        self.restore_path, self.subclient.name), self.subclient.content)
            if error_flag:
                # if the list is not empty then error was there, fail the test
                # case
                self.log.info(error_flag)
                raise Exception(f"testcase failed - reason {str(error_flag)}")

        except Exception as exp:
            self.log.error(f'Failed to execute test case with error: {exp}')
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """delete all items created for the testcase"""
        try:
            self.log.info("*********************************************")
            self.log.info("Restoring defaults")

            self.log.info(
                "setting back the mmprune process interval to 60 mins")
            self.mm_helper.update_mmconfig_param(
                'MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 10, 60)

            self.log.info("removing DDBMarkAndSweepRunIntervalSeconds additional setting if it exists")
            self.ma_client.delete_additional_setting("MediaAgent", "DDBMarkAndSweepRunIntervalSeconds")

            self.log.info('starting unconditional cleanup')
            self.previous_run_clean_up()

        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info(f"ERROR:{exp}")
