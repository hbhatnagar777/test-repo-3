# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

Note regarding sql credentials :

    In order to ensure security,
    sql credentials have to be passed to the TC via config.json file under CoreUtils/Templates

    populate the following fields in config file as required,
    "SQL": {
        "Username": "<SQL_SERVER_USERNAME>",
        "Password": "<SQL_SERVER_PASSWORD>"
    }

    At the time of execution the creds will be automatically fetched by TC.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    new_content()       -- generates data of specified size in given directory

    deallocate_resources()      -- deallocates all the resources created for testcase environment

    allocate_resources()        -- allocates all the necessary resources for testcase environment

    previous_run_cleanup()      -- for deleting the left over backupset and storage policy from the previous run

    run_backup_job()        -- for running a backup job of given type

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    run_auxcopy_job()   --  runs auxcopy job for all copies

    run_restore_job()   --  runs restore job for a given copy precedence

    validate_restore_job()	-- validates restored content with actual content

    delete_job()	-- deletes the specified backup job

    remove_drillhole_flag()	-- disables drillholes on given store

    get_active_files_store()	-- get the active store object for given policy

    update_content()	-- deletes alternate files from path and creates additional content in its place

    run_space_reclaim_job()	-- starts a space reclaim and defrag job

    wait_for_pruning()	-- waiting for phase 3 pruning to start on given store

Prerequisites: None

Input JSON:

"50428": {
        "ClientName": "<Client name>",
        "AgentName": "<IDataAgent name>",
        "MediaAgentName": "<Name of MediaAgent>",
        "storage_pool_name": "<name of the storage pool to be reused>" (optional argument),
        "storage_pool_name2": "<name of the second storage pool to be reused>" (optional argument),
        "dedup_path": "<path where dedup store to be created>" (optional argument)
        (Must provide LVM dedupe path for Linux MAs)
}

Design steps:

1. allocate resources
2. set pruning interval to 2 mins
3. disable dedupdrillholes
4. change retention for primary to -retainArchiverDataForDays 1 -retainBackupDataForCycles 3 -retainBackupDataForDays 1
5. enable DASHfull
6. create three subclients with multiple readers and streams = 4
7. enable encryption on primary copy
8. create secondary copy with re-encrypt GOST 256
9. disable garbage collection on store
10. run full backups on each subclient
11. run dv2 'INCREMENTAL','DDB_AND_DATA_VERIFICATION'
12. verify from logs that DV2 job completed with no data to verify
13. generate some new data, and delete some old
14. wait for backup on subclient 1 to finish
15. run second full backup on sb1
16. make sure bkpjob2, bkpjob3 or bkpjob4 are not in pre-scan or scan state and in running state
17. Run 2nd INCR DV2 with option 'DDB_AND_DATA_VERIFICATION' after job1 has completed, but job2, job4 is still running
18. wait for dv to complete
19. wait for 2nd backup to complete
20. run second full backup on sb2
21. wait for bkp 3, 4, 5 to complete
22. prune job1 and job 2
23. wait for deletedafcount to hit 0
24. verify that pruning started
25. get free space before defrag on mountpath
26. run defrag and ddb space reclaim without OCL
27. get free space after defrag
28. run quick dv2 after defrag
29. verify space was freed on mountpath after defrag
30. run auxcopy job from sub clients 1 and 2
31. restore from defragged jobs for subclients 1 and 2
32. validate the restored data from defragged jobs
33. deallocate resources

"""
from time import sleep
from AutomationUtils import constants, commonutils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils import config
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super().__init__()
        self.name = "This is DV2 and basic defrag TC with backups and DV2 running in parallel and " \
                    "basic defrag and aux run with defrag data and restore from defragged data"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.cs_name = None
        self.mount_path = None
        self.dedup_store_path = None
        self.content_path = None
        self.restore_path = None
        self.storage_pool_name = None
        self.storage_pool_name2 = None
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.opt_selector = None
        self.sidb_id = None
        self.testcase_path = None
        self.cs_machine = None
        self.client_machine = None
        self.sql_username = None
        self.sql_password = None
        self.media_agent = None
        self.media_agent_machine = None
        self.client = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.storage_pool = None
        self.storage_pool2 = None
        self.library = None
        self.library2 = None
        self.gdsp_name = None
        self.gdsp = None
        self.gdsp2 = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.store = None
        self.dedupe_engine = None
        self.primary_copy = None
        self.secondary_copy = None
        self.drillhole_key_added = None
        self.is_user_defined_storpool = False
        self.is_user_defined_dedup = False

    def setup(self):
        """Setup function of this test case"""
        if self.tcinputs.get("storage_pool_name") and self.tcinputs.get("storage_pool_name2"):
            self.is_user_defined_storpool = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        self.cs_name = self.commcell.commserv_client.name
        self.media_agent = self.tcinputs["MediaAgentName"]
        suffix = str(self.media_agent)[:] + "_" + str(self.client.client_name)[:]

        self.storage_policy_name = "{0}_SP{1}".format(str(self.id), suffix)
        self.backupset_name = "{0}_BS{1}".format(str(self.id), suffix)
        self.subclient_name = "{0}_SC{1}".format(str(self.id), suffix)
        self.mm_helper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = Machine(self.client)
        self.media_agent_machine = Machine(self.media_agent, self.commcell)

        if not self.is_user_defined_dedup and "unix" in self.media_agent_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        drive_path_client = self.opt_selector.get_drive(
            self.client_machine)
        self.testcase_path_client = "%s%s" % (drive_path_client, self.id)
        self.content_path = self.client_machine.join_path(
            self.testcase_path_client, "content_path")

        if self.is_user_defined_storpool:
            self.storage_pool_name = self.tcinputs["storage_pool_name"]
            self.storage_pool = self.commcell.storage_pools.get(self.storage_pool_name)
            self.gdsp = self.commcell.storage_policies.get(self.storage_pool.global_policy_name)
            self.storage_pool_name2 = self.tcinputs["storage_pool_name2"]
            self.storage_pool2 = self.commcell.storage_pools.get(self.storage_pool_name2)
            self.gdsp2 = self.commcell.storage_policies.get(self.storage_pool2.global_policy_name)

        else:
            self.gdsp_name = "{0}_GDSP{1}".format(str(self.id), suffix)

        self.library_name = "{0}_lib{1}".format(str(self.id), suffix)

        drive_path_media_agent = self.opt_selector.get_drive(
            self.media_agent_machine)
        self.testcase_path_media_agent = "%s%s" % (drive_path_media_agent, self.id)

        self.testcase_path_client = "%s%s" % (drive_path_client, self.id)
        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")
        self.restore_path = self.client_machine.join_path(self.testcase_path_client, "restore_path")

        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")

        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")

        self.mount_path = self.media_agent_machine.join_path(
            self.testcase_path_media_agent, "mount_path")

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path = self.media_agent_machine.join_path(self.tcinputs["dedup_path"], self.id)
        else:
            self.dedup_store_path = self.media_agent_machine.join_path(
                self.testcase_path_media_agent, "dedup_store_path")



        # sql connections
        self.sql_username = config.get_config().SQL.Username
        self.sql_password = config.get_config().SQL.Password

        # adding regkey to disable drillholes if it doesn't exist
        self.ma_client = self.commcell.clients.get(self.media_agent)
        self.ma_client.delete_additional_setting("MediaAgent", "DedupDrillHoles")
        self.ma_client.add_additional_setting("MediaAgent", "DedupDrillHoles", 'INTEGER', '0')

    def new_content(self, dir_path, dir_size):
        """
        generates new incompressible data in given directory/folder

            Args:
                dir_path        (str)       full path of directory/folder in which data is to be added
                dir_size        (float)     size of data to be created(in GB)

        returns None
        """
        if self.client_machine.check_directory_exists(dir_path):
            self.client_machine.remove_directory(dir_path)
        self.client_machine.create_directory(dir_path)
        self.opt_selector.create_uncompressable_data(client=self.client_machine,
                                                     size=dir_size,
                                                     path=dir_path)

    def deallocate_resources(self):
        """removes all resources allocated by the Testcase"""
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
            self.log.info("content_path deleted")
        else:
            self.log.info("content_path does not exist.")

        if self.client_machine.check_directory_exists(self.restore_path):
            self.client_machine.remove_directory(self.restore_path)
            self.log.info("restore_path deleted")
        else:
            self.log.info("restore_path does not exist.")

        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.agent.backupsets.delete(self.backupset_name)
            self.log.info("backup set deleted")
        else:
            self.log.info("backup set does not exist")

        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.commcell.storage_policies.delete(self.storage_policy_name)
            self.log.info("storage policy deleted")
        else:
            self.log.info("storage policy does not exist.")

        if not self.is_user_defined_storpool:
            if self.commcell.storage_policies.has_policy(self.gdsp_name):
                self.commcell.storage_policies.delete(self.gdsp_name)
                self.log.info("GDSP deleted")
            else:
                self.log.info("GDSP does not exist.")

            if self.commcell.storage_policies.has_policy(self.gdsp_name + '2'):
                self.commcell.storage_policies.delete(self.gdsp_name + '2')
                self.log.info("GDSP 2 deleted")
            else:
                self.log.info("GDSP 2 does not exist.")

        self.log.info("clean up successful")

    def previous_run_clean_up(self):
        """delete the resources from previous run """
        self.log.info("********* previous run clean up **********")
        try:
            self.deallocate_resources()
            self.log.info("previous run clean up COMPLETED")
        except Exception as exp:
            self.log.error("previous run clean up ERROR")
            raise Exception("ERROR:%s", exp)

    def allocate_resources(self):
        """creates all necessary resources for testcase to run"""
        # create dedupe store paths
        if self.media_agent_machine.check_directory_exists(self.dedup_store_path + '1'):
            self.log.info("store path 1 directory already exists")
        else:
            self.media_agent_machine.create_directory(self.dedup_store_path + '1')
            self.log.info("store path 1 created")
        if self.media_agent_machine.check_directory_exists(self.dedup_store_path + '2'):
            self.log.info("store path 2 directory already exists")
        else:
            self.media_agent_machine.create_directory(self.dedup_store_path + '2')
            self.log.info("store path 2 created")

        if not self.is_user_defined_storpool:
            self.library = self.mm_helper.configure_disk_library(
                self.library_name, self.media_agent, self.mount_path)
            self.library2 = self.mm_helper.configure_disk_library(
                self.library_name + '2', self.media_agent, self.mount_path + '2')

        # create gdsp if not provided
        if not self.is_user_defined_storpool:
            self.gdsp = self.dedup_helper.configure_global_dedupe_storage_policy(
                global_storage_policy_name=self.gdsp_name,
                library_name=self.library_name,
                media_agent_name=self.media_agent,
                ddb_path=self.dedup_store_path + '1',
                ddb_media_agent=self.media_agent)
            self.gdsp2 = self.dedup_helper.configure_global_dedupe_storage_policy(
                global_storage_policy_name=self.gdsp_name + '2',
                library_name=self.library_name + '2',
                media_agent_name=self.media_agent,
                ddb_path=self.dedup_store_path + '2',
                ddb_media_agent=self.media_agent)

        # create dependent storage policy
        self.storage_policy = self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name,
                                                                 library=self.library_name,
                                                                 media_agent=self.media_agent,
                                                                 global_policy_name=self.gdsp_name,
                                                                 dedup_media_agent=self.media_agent,
                                                                 dedup_path=self.dedup_store_path,
                                                                 number_of_streams=50)

        # create backupset and subclient
        self.backup_set = self.mm_helper.configure_backupset(self.backupset_name,
                                                             self.agent)
        self.subclient = {}

        for index in range(1, 4):
            self.subclient[index] = self.mm_helper.configure_subclient(self.backupset_name,
                                                                       self.subclient_name + str(index),
                                                                       self.storage_policy_name,
                                                                       self.client_machine.join_path
                                                                       (self.content_path, str(index)),
                                                                       self.agent)
            self.subclient[index].data_readers = 4
            self.subclient[index].allow_multiple_readers = True
            size = 2 if index == 1 else 4
            self.new_content(dir_path=self.client_machine.join_path(self.content_path, str(index)), dir_size=size)

        # create primary copy object for storage policy
        self.primary_copy = self.storage_policy.get_copy(copy_name="primary")

        # create secondary copy for storage policy
        self.secondary_copy = self.mm_helper.configure_secondary_copy(
            sec_copy_name=self.storage_policy_name + "_secondary",
            storage_policy_name=self.storage_policy_name,
            ma_name=self.media_agent,
            global_policy_name=self.gdsp2.storage_policy_name)

        # Remove Association with System Created AutoCopy Schedule
        self.mm_helper.remove_autocopy_schedule(self.storage_policy_name, self.storage_policy_name + "_secondary")

        # set enc on primary copy BlowFish 128
        self.log.info("setting encryption on primary")
        self.gdsp.get_copy("Primary_Global").set_encryption_properties(re_encryption=True,
                                                                       encryption_type="BlowFish",
                                                                       encryption_length=128)

        # set enc on secondary copy GOST 256
        self.log.info("setting re-encryption on secondary")
        self.gdsp2.get_copy("Primary_Global").set_encryption_properties(re_encryption=True,
                                                                        encryption_type="GOST",
                                                                        encryption_length=256)

        # change retention to 1 Day, 3 Cycles, and 1 Day for archived data
        self.log.info("updating retention on primary")
        self.primary_copy.copy_retention = (1, 3, 1)

        # Enable DASHfull
        self.log.info("enabling dashfull for primary")
        self.primary_copy.copy_dedupe_dash_full = True

        # initializing store object
        self.store = self.get_active_files_store()

        # disable garbage collection
        self.log.info("disabling garbage collection to avoid complications in waiting for physical prune")
        self.store.enable_garbage_collection = False

    def run_backup(self, subclient, job_type):
        """
        run a backup job for the subclient specified in Testcase

            Args:
                job_type        (str)       backup job type(FULL, synthetic_full, incremental, etc.)
                subclient       (instance)  subclient object on which backup is to be run on

        Returns:
             job id(int)
        """
        job = subclient.backup(backup_level=job_type)
        self.log.info("starting %s backup job %s...", job_type, job.job_id)
        return job

    def run_aux_copy(self):
        """
        run auxcopy job for the subclient specified in Testcase

            Args:

        Returns:
             job id(int)
        """
        job = self.storage_policy.run_aux_copy(media_agent=self.media_agent)
        self.log.info("starting auxcopy job %s ...", job.job_id)

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run auxcopy job with error: {0}".format(job.delay_reason)
            )
        self.log.info("auxcopy job: %s completed successfully", job.job_id)

        return job.job_id

    def run_restore_job(self, subclient, restore_path="", content_path="", copy_precendence=1):
        """
        run auxcopy job for the subclient specified in Testcase

            Args:
                subclient           (instance)      subclient object
                restore_path        (str)           path extension for restore path
                content_path        (str)           content path for backed up files
                copy_precendence    (int)           precedence of copy to be used for restore

        Returns:
             job id(int)
        """
        job = subclient.restore_out_of_place(self.client.client_name,
                                             self.client_machine.join_path(self.restore_path, restore_path),
                                             self.client_machine.get_files_in_path(content_path),
                                             copy_precedence=copy_precendence)
        self.log.info("starting restore job %s ...", job.job_id)

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore job with error: {0}".format(job.delay_reason)
            )
        self.log.info("restore job: %s completed successfully", job.job_id)

        return job.job_id

    def validate_restore_job(self, content_path="", restore_path=""):
        """
        validates restored content against original content

            Args:
                restore_path        (str)           path extension for restore path
                content_path        (str)           content path for backed up files

        Returns:
             None
        """
        content_files = sorted(
            self.client_machine.get_files_in_path(content_path))
        self.log.info("VERIFYING IF THE RESTORED FILES ARE SAME OR NOT")
        restored_files = self.client_machine.get_files_in_path(
            self.client_machine.join_path(self.restore_path, restore_path))
        self.log.info("Comparing the files using MD5 hash")
        if len(restored_files) == len(content_files):
            restored_files.sort()
            for original_file, restored_file in zip(
                    content_files, restored_files):
                if not self.client_machine.compare_files(
                        self.client_machine, original_file, restored_file):
                    self.log.info("Result: Fail")
                    raise ValueError("The restored file is "
                                     "not the same as the original content file")
        self.log.info("All the restored files "
                      "are same as the original content files")
        self.log.info("Result: Pass")

    def delete_job(self, job):
        """
        deletes job whose job id is passed as argument

            Args:
                job        (int)     job id of job to be deleted

        Returns:
             None
        """
        if isinstance(job, str):
            self.log.info("deleting job %s ...", job)
            self.primary_copy.delete_job(job)

    def remove_drillhole_flag(self, library_id, revert=False):
        """
        this method will remove drill hole flag for all mount paths of a library

        Args:
             library_id - int - library id which has all mount paths to disable drill hole
             revert - boolean - to remove drillhole flag from mountpath [revert = True]
        """
        if not revert:
            self.log.info("removing drill hole flag at mount path level...")
            query = f"""
                    update MMMountPath
                    set Attribute = Attribute & ~128
                    where LibraryId = {library_id}"""
        else:
            self.log.info("reverting drill hole flag at mount path level...")
            query = f"""
                    update MMMountPath
                    set Attribute = Attribute | 128
                    where LibraryId = {library_id}"""
        self.log.info("QUERY: %s", query)
        self.mm_helper.execute_update_query(query, db_password=self.sql_password, db_user=self.sql_username)

    def get_active_files_store(self):
        """returns active store object for files iDA"""
        self.commcell.deduplication_engines.refresh()
        engine = self.commcell.deduplication_engines.get(self.gdsp_name, 'primary_global')
        if engine:
            return engine.get(engine.all_stores[0][0])
        return 0

    def update_content(self):
        """deletes alternate files in content and adds new content to content path"""
        for index in range(1, 3):
            new_target=""
            folders_list = self.client_machine.get_folders_in_path(self.client_machine.join_path(self.content_path, str(index)))
            self.log.info(folders_list)
            if folders_list:
                new_target = folders_list[0]
            self.log.info(f"Deleting every 2nd file from {new_target}")
            self.opt_selector.delete_nth_files_in_directory(self.client_machine, new_target, 2, "delete")
            self.new_content(dir_path=self.client_machine.join_path(self.content_path, str(index), "new"), dir_size=2)

    def run_space_reclaim_job(self, store, defrag_level, with_ocl=False):
        """
        runs space reclaim job on the provided store object

        Args:
            store (object) - store object wher espace reclaim job needs to run

            with_ocl (bool) - set True if the job needs to run with OCL phase

            defrag_level (integer) - level of defragmentation
                                        level_map = {
                                                        1: 80,
                                                        2: 60,
                                                        3: 40,
                                                        4: 20
                                                    }

        Returns:
            (object) job object for the space reclaim job
        """
        space_reclaim_job = store.run_space_reclaimation(level=defrag_level, clean_orphan_data=with_ocl)
        self.log.info("Space reclaim job with OCL[%s]: %s", with_ocl, space_reclaim_job.job_id)
        if not space_reclaim_job.wait_for_completion():
            raise Exception(f"Failed to run DDB Space reclaim with error: {space_reclaim_job.delay_reason}")
        self.log.info("DDB Space reclaim job completed.")
        return space_reclaim_job

    def check_for_phase2_start(self, store_id, primary_count):
        """
        this method checks if phase 2 pruning started on store.
        LOGIC: phase 2 completed: primary count decreased compared to post backup value [primary_count].

        Args:
            store_id (integer)      -   store id on which phase 2 needs to be checked
            primary_count (integer) -   primary records count post all backups and before running data aging

        Returns:
             True/False -   if the phase is started then True else False
        """
        self.log.info("checking if Phase 2 started [logic: current primary count < post backup primary count ]")
        for _ in range(5):
            current_primary_count = int(self.dedup_helper.get_primary_recs_count(store_id, self.sql_password,
                                                                                 db_user=self.sql_username))
            current_zeroref_count = int(self.dedup_helper.get_zeroref_recs_count(store_id, self.sql_password,
                                                                                 db_user=self.sql_username))
            self.log.info("RESULT: primary count[%s] zeroref count[%s]", current_primary_count, current_zeroref_count)

            if current_primary_count < int(primary_count):
                self.log.info("Phase 2 pruning started...")
                return True, current_zeroref_count
            sleep(60)
        self.log.error("timeout reached, Phase 2 pruning did not start")
        return False, 0

    def check_for_phase3_start(self, store_id, zeroref_count):
        """
            this method checks if phase 3 pruning started on store.
            LOGIC: phase 3 completed: zeroref count decreased compared to value during phase2 [zeroref_count].

            Args:
                store_id (integer)      -   store id on which phase 2 needs to be checked
                zeroref_count (integer) -   zeroref records count during phase2 check

            Returns:
                 True/False -   if the phase is started then True else False
        """
        count = 0
        self.log.info("checking if Phase 3 started [logic: phase 2 zeroref count > latest zeroref count]")
        current_zeroref_count = int(self.dedup_helper.get_zeroref_recs_count(store_id, self.sql_password,
                                                                             db_user=self.sql_username))
        while zeroref_count <= current_zeroref_count and count < 15:
            count += 1
            sleep(60)
            current_primary_count = int(self.dedup_helper.get_primary_recs_count(store_id, self.sql_password,
                                                                                 db_user=self.sql_username))
            current_zeroref_count = int(self.dedup_helper.get_zeroref_recs_count(store_id, self.sql_password,
                                                                                 db_user=self.sql_username))
            self.log.info("RESULT: primary count[%s] zeroref count[%s]", current_primary_count, current_zeroref_count)

        if zeroref_count > current_zeroref_count:
            self.log.info("Phase 3 pruning started...")
            return True
        self.log.error("timeout reached, Phase 3 pruning did not start")
        return False

    def wait_for_pruning(self, store_id):
        """
        Wait for Phase 3 pruning on SIDB
        Args:
            store_id    (int)       --      SIDB Engine ID

        Return True if Phase 3 pruning is complete on store_id else False
        """
        pruning_done = False
        for i in range(10):
            self.log.info("data aging + sleep for 240 seconds: RUN %s", (i + 1))

            job = self.mm_helper.submit_data_aging_job(
                copy_name="Primary",
                storage_policy_name=self.storage_policy_name,
                is_granular=True,
                include_all_clients=True,
                select_copies=True,
                prune_selected_copies=True)

            self.log.info("Data Aging job: %s", str(job.job_id))
            if not job.wait_for_completion():
                if job.status.lower() == "completed":
                    self.log.info("job %s complete", job.job_id)
                else:
                    raise Exception(
                        f"Job {job.job_id} Failed with {job.delay_reason}")
            matched_lines = self.dedup_helper.validate_pruning_phase(store_id, self.tcinputs['MediaAgentName'])
            self.log.info(matched_lines)

            if matched_lines:
                self.log.info(matched_lines)
                self.log.info(f"Successfully validated the phase 3 pruning on sidb - {store_id}")
                pruning_done = True
                break
            else:
                self.log.info(f"No phase 3 pruning activity on sidb - {store_id} yet. Checking after 240 seconds")
                sleep(240)


        if not pruning_done:
            self.log.error("Pruning is not over even after 40 minutes")

        return pruning_done

    def run(self):
        """Run function of this test case"""
        try:
            # previous run cleanup
            self.previous_run_clean_up()

            # allocating necessary resources
            self.allocate_resources()

            # checking if dedup enabled
            if self.primary_copy.is_dedupe_enabled():
                self.log.info("dedup enabled..!")
            else:
                self.log.error("dedup not enabled..!")
                raise Exception(f"dedup not enabled on storage policy {self.storage_policy_name}")

            # set pruning interval to 2 mins
            self.mm_helper.update_mmpruneprocess(db_user=self.sql_username, db_password=self.sql_password,
                                                 min_value=2, mmpruneprocess_value=2)

            # set reg key for dedupdrillholes to 0
            self.remove_drillhole_flag(self.library.library_id)

            # run a full backup on each subclient
            bkpjob1 = self.run_backup(subclient=self.subclient[1], job_type="FULL")
            bkpjob2 = self.run_backup(subclient=self.subclient[2], job_type="FULL")
            bkpjob3 = self.run_backup(subclient=self.subclient[3], job_type="FULL")

            # run dv2 'INCREMENTAL','DDB_AND_DATA_VERIFICATION' - completes with nothing to verify
            self.store.refresh()
            self.log.info("starting initial dv2 job with no data to verify..")
            initial_dv2 = self.dedup_helper.run_dv2_job(self.store, "incremental", "complete")

            # verify from logs that DV2 job completed with no data to verify
            self.log.info("verifying that dv2 completed with no data to verify..")
            matched_line, matched_string = self.dedup_helper.parse_log(client=self.cs_name,
                                                                       log_file="JobManager.log",
                                                                       regex='No data need to be copied',
                                                                       jobid=initial_dv2.job_id,
                                                                       single_file=False)
            if matched_line:
                self.log.info("SUCCESS  dv2 finished with : no data need to be verified..")
            else:
                self.log.error("ERROR   Result:Fail")
                raise Exception("dv2 did not proceed in expected manner..")

            # generate some new data, delete some old, keep some old
            self.log.info("updating content on subclients 1 and 2..")
            self.update_content()
            self.log.info("updating content on subclients 1 and 2 finished..")

            # wait for 1st backup to complete
            self.log.info("waiting for backup 1 to complete..")
            bkpjob1.wait_for_completion()
            self.log.info("backup 1 completed..")

            # run full backup on sb1
            bkpjob4 = self.run_backup(subclient=self.subclient[1], job_type="FULL")

            # make sure bkpjob2, bkpjob3 or bkpjob4 are not in pre-scan or scan state
            # and in running state, then start DV2
            retry_count = 0
            while retry_count < 60:
                bkpjob2.refresh()
                if bkpjob2.phase:
                    self.log.info("job : %s --> phase : %s", bkpjob2.job_id, bkpjob2.phase)
                bkpjob4.refresh()
                if bkpjob4.phase:
                    self.log.info("job : %s --> phase : %s", bkpjob4.job_id, bkpjob4.phase)
                else:
                    raise Exception(f"job {bkpjob4.job_id} finished unexpectedly..")

                if bkpjob2.phase == 'Backup' or bkpjob4.phase == 'Backup':
                    self.log.info("At leat 1 job is in backup phase. procceed with DV2")
                    break
                else:
                    self.log.info("None of the jobs are in backup phase. Check after 2 secs")
                    sleep(2)
                    retry_count = retry_count + 1

            # Run 2nd INCR DV2 with option 'DDB_AND_DATA_VERIFICATION' after
            # job1 has completed, but job2, job4 is still running
            # wait for dv to complete
            self.store.refresh()
            self.log.info("starting second incremental quick dv2 job..")
            self.dedup_helper.run_dv2_job(self.store, "incremental", "quick")

            # wait for 2nd backup to complete
            self.log.info("waiting for backup 2 to complete..")
            bkpjob2.wait_for_completion()
            self.log.info("backup 2 completed..")

            # run full backup on sb2
            bkpjob5 = self.run_backup(subclient=self.subclient[2], job_type="FULL")

            # wait for bkp 3, 4, 5 to complete
            self.log.info("waiting for backups 3,4, and 5 to complete..")
            bkpjob3.wait_for_completion()
            bkpjob4.wait_for_completion()
            bkpjob5.wait_for_completion()
            self.log.info("backups 3,4, and 5 completed..")

            # wait for deletedafcount to hit 0
            self.log.info("waiting for pruning to begin on store..")

            primary_recs = self.dedup_helper.get_primary_recs_count(self.store.store_id, db_password=self.sql_password,
                                                                    db_user=self.sql_username)
            # prune job1 and job 2
            self.log.info("deleting backup jobs 1 and 2..")
            self.delete_job(bkpjob1.job_id)
            self.delete_job(bkpjob2.job_id)

            for _ in range(2):
                aging_job = self.mm_helper.submit_data_aging_job(copy_name='Primary',
                                                                 storage_policy_name=self.storage_policy_name)
                aging_job.wait_for_completion()

            if not self.wait_for_pruning(self.store.store_id):
                raise Exception("pruning did not happen")

            self.store.refresh()

            # get free space before defrag
            size_before_defrag = self.media_agent_machine.get_folder_size(self.mount_path)
            self.log.info("size of mountpath before defrag : %f", size_before_defrag)

            # run defrag
            self.log.info("starting space reclaim job..")
            reclamation_job = self.run_space_reclaim_job(store=self.store, defrag_level=4)

            # get free space after defrag
            size_after_defrag = self.media_agent_machine.get_folder_size(self.mount_path)
            self.log.info("size of mountpath after defrag : %f", size_after_defrag)

            # run quick dv2 after defrag
            self.store.refresh()
            self.log.info("starting third full quick dv2 job..")
            quick_dv2_job = self.dedup_helper.run_dv2_job(self.store, "full", "quick")

            # validating that defrag and space reclamation proceeded successfully
            # and verifying the changes in mountpath
            self.log.info("verifying if space reclaim did indeed reclaim space..")
            if size_before_defrag == size_after_defrag:
                self.log.error("Space reclamation did not occur physically..")
                raise Exception("Defrag and space reclamation failed..")
            if size_before_defrag < size_after_defrag:
                self.log.info("Space reclamation completed successfully.. no reclaimable space left out after job.. "
                              "used space on mp is equal to previous used space minus reclaimed space..")

            # run auxcopy
            self.log.info("running auxcopy on policy..")
            self.run_aux_copy()

            # restore from defragged jobs
            for index in range(1, 3):
                self.log.info("starting restore out of place for subclient %d..", index)
                self.run_restore_job(subclient=self.subclient[index], restore_path="sb" + str(index),
                                     content_path=self.client_machine.join_path(self.content_path, str(index)))
                self.log.info("checking if restored content is valid..")
                self.validate_restore_job(restore_path="sb1",
                                          content_path=self.client_machine.join_path(self.content_path, str(index)))

            self.log.info("All Validations Completed.. Testcase executed successfully..")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""

        try:
            # reset drillhole reg key
            self.log.info("Performing unconditional cleanup")
            self.media_agent_machine.update_registry('MediaAgent', value='DedupDrillHoles', data='0',
                                                     reg_type='DWord')
            # reset pruning interval
            self.mm_helper.update_mmpruneprocess(db_user=self.sql_username, db_password=self.sql_password)
            # reverting drillhole flag
            self.remove_drillhole_flag(self.library.library_id, revert=True)

            self.deallocate_resources()
        except Exception as ex:
            self.log.warning(f"Cleanup Failed, please check setup .. {ex}")

