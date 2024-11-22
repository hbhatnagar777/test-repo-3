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

    new_content()       -- generates data of specified size in given directory

    deallocate_resources()      -- deallocates all the resources created for testcase environment

    allocate_resources()        -- allocates all the necessary resources for testcase environment

    previous_run_cleanup()      -- for deleting the left over backupset and storage policy from the previous run

    run_backup_job()        -- for running a backup job of given type

    delete_job()       -- deletes all the jobs whose job ids are given in argument list

    run_data_aging()        -- runs data aging at granular storage policy level for given storage policy

    is_dedupe_enabled()     -- checks whether the given storage policy has deduplication enabled

    set_store_pruning()     -- enables/disables store pruning based on boolean input provided

    get_deleted_af_count()      -- gets the count of mmdeleteaf entries for a given store

    check_error_codes()     -- checks whether all entries in mmdeleteaf contain the user specified error code



    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

This testcase disables physical pruning at store level and checks if pruning occurs or not.

Prerequisites: None

Input JSON:

"49421": {
        "ClientName": "<Client name>",
        "AgentName": "<IDataAgent name>",
        "MediaAgentName": "<Name of MediaAgent>",
        "storage_pool_name": "<name of the storage pool to be reused>" (optional argument),
        "gdsp_name": "<name of gdsp to be reused>" (optional argument),
        "library_name": "<name of the Library to be reused>" (optional argument),
        "mount_path": "<path where the data is to be stored>" (optional argument),
        "dedup_path": "<path where dedup store to be created>" (optional argument)
        (Must provide LVM dedupe path for Linux MAs)
}

Design steps:

1. Allocate necessary resources and generate data to be backed up
2. set pruning interval to 2 mins for commcell
3. run three full backup jobs
    i. store level physical pruning is enabled by default
    ii. policy uses single partition ddb

4. delete first backup job
5. get deletedAF_count from CSDB
6. run data aging function
7. run a fourth full backup job
8. set retry_count -> 0
9. while retry_count < 3 and deletedAF_count != 0:
    9.1 run data aging
    9.2 increment retry_count and wait for a small interval

10. if deletedAF_count is not zero, then
        pruning did not occur, TC failed
    else deletedAF_count is zero, then
        pruning has occurred, continue

11. disable physical pruning at store level
12. delete second and third jobs
13. repeat steps 8 and 9
14. if deletedAF_count is not zero, then
        pruning did not occur, TC has succeeded
    else deletedAF_count is zero, then
        pruning has occurred, TC failed

15. enable pruning at store level
16. reset pruning interval to default value
17. deallocate resources that were created

"""
from time import sleep
from cvpysdk.job import JobController
from AutomationUtils import constants, commonutils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
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
        self.name = "Disable Pruning at Store Level"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.mount_path = None
        self.dedup_store_path = None
        self.content_path = None
        self.gdsp_name = None
        self.storage_pool_name = None
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.job_controller = None
        self.opt_selector = None
        self.gdsp_copy_id = None
        self.sidb_id = None
        self.testcase_path = None
        self.cs_machine = None
        self.client_machine = None
        self.sql_password = None
        self.media_agent = None
        self.media_agent_machine = None
        self.client = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.storage_pool = None
        self.library = None
        self.gdsp = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.store = None
        self.gdsp_copy = None
        self.primary_copy = None
        self.is_user_defined_storpool = False
        self.is_user_defined_gdsp = False
        self.is_user_defined_lib = False
        self.is_user_defined_mp = False
        self.is_user_defined_dedup = False

    def setup(self):
        """Setup function of this test case"""
        if self.tcinputs.get("storage_pool_name"):
            self.is_user_defined_storpool = True
        if self.tcinputs.get("gdsp_name"):
            self.is_user_defined_gdsp = True
        if self.tcinputs.get("library_name"):
            self.is_user_defined_lib = True
        if self.tcinputs.get("mount_path"):
            self.is_user_defined_mp = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

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

        drive_path_client = self.opt_selector.get_drive(self.client_machine, 25*1024)
        self.testcase_path_client = "%s%s" % (drive_path_client, self.id)
        self.content_path = self.client_machine.join_path(
            self.testcase_path_client, "content_path")

        if self.is_user_defined_gdsp:
            self.gdsp_name = self.tcinputs["gdsp_name"]
            self.gdsp = self.commcell.storage_policies.get(self.gdsp_name)
        elif self.is_user_defined_storpool:
            self.storage_pool_name = self.tcinputs["storage_pool_name"]
            self.storage_pool = self.commcell.storage_pools.get(self.storage_pool_name)
            self.gdsp_name = self.storage_pool.global_policy_name
            self.gdsp = self.commcell.storage_policies.get(self.gdsp_name)

        else:
            self.gdsp_name = "{0}_GDSP{1}".format(str(self.id), suffix)

        if self.is_user_defined_lib:
            self.log.info("Existing library name supplied")
            self.library_name = self.tcinputs.get("library_name")
        else:
            self.library_name = "{0}_lib{1}".format(str(self.id), suffix)

        drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine, 25*1024)
        self.testcase_path_media_agent = "%s%s" % (drive_path_media_agent, self.id)

        self.testcase_path_client = "%s%s" % (drive_path_client, self.id)
        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")

        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")

        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")

        if self.is_user_defined_mp:
            self.log.info("custom mount path supplied")
            self.mount_path = self.media_agent_machine.join_path(self.tcinputs["mount_path"], self.id)
        else:
            if not self.is_user_defined_lib:
                self.mount_path = self.media_agent_machine.join_path(
                    self.testcase_path_media_agent, "mount_path")

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path = self.media_agent_machine.join_path(self.tcinputs["dedup_path"], self.id)
        else:
            self.dedup_store_path = self.media_agent_machine.join_path(
                self.testcase_path_media_agent, "dedup_store_path")

        # sql connections
        self.sql_password = commonutils.get_cvadmin_password(self.commcell)

        # job controller
        self.job_controller = JobController(self.commcell)

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

        if not self.is_user_defined_gdsp:
            if self.commcell.storage_policies.has_policy(self.gdsp_name):
                self.commcell.storage_policies.delete(self.gdsp_name)
                self.log.info("GDSP deleted")
            else:
                self.log.info("GDSP does not exist.")

        if not self.is_user_defined_gdsp and not self.is_user_defined_storpool:
            # here the storage pool is automatically created by gdsp and therefore has the same name as gdsp.
            if self.commcell.storage_pools.has_storage_pool(self.gdsp_name):
                self.commcell.storage_pools.delete(self.gdsp_name)
                self.log.info("Storage pool deleted")
            else:
                self.log.info("Storage pool does not exist.")

        self.commcell.disk_libraries.refresh()
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
            self.log.info("content_path deleted")
        else:
            self.log.info("content_path does not exist.")

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
        # create library if not provided
        if not (self.is_user_defined_lib or self.is_user_defined_storpool or self.is_user_defined_gdsp):
            self.library = self.mm_helper.configure_disk_library(
                self.library_name, self.media_agent, self.mount_path)

        # create gdsp if not provided
        if not self.is_user_defined_gdsp and not self.is_user_defined_storpool:
            self.gdsp = self.dedup_helper.configure_global_dedupe_storage_policy(
                global_storage_policy_name=self.gdsp_name,
                library_name=self.library_name,
                media_agent_name=self.media_agent,
                ddb_path=self.dedup_store_path,
                ddb_media_agent=self.media_agent)

            # adding second partition to the ddb store
            self.gdsp_copy = self.gdsp.get_copy(copy_name="Primary_Global")
            self.gdsp_copy_id = self.gdsp_copy.storage_policy_id
            new_ddb_path = self.media_agent_machine.join_path(self.dedup_store_path, "partition2")
            self.sidb_id = \
                self.dedup_helper.get_sidb_ids(copy_name="Primary_Global", sp_id=self.gdsp.storage_policy_id)[0]
            self.gdsp.add_ddb_partition(copy_id=self.gdsp_copy_id,
                                        sidb_store_id=self.sidb_id,
                                        sidb_new_path=new_ddb_path,
                                        media_agent=self.media_agent)

        # create dependent storage policy
        self.storage_policy = self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name,
                                                                 library=self.library_name,
                                                                 media_agent=self.media_agent,
                                                                 global_policy_name=self.gdsp_name,
                                                                 dedup_media_agent=self.media_agent,
                                                                 dedup_path=self.dedup_store_path)

        # create backupset and subclient
        self.backup_set = self.mm_helper.configure_backupset(self.backupset_name,
                                                             self.agent)
        self.subclient = self.mm_helper.configure_subclient(self.backupset_name,
                                                            self.subclient_name,
                                                            self.storage_policy_name,
                                                            self.content_path,
                                                            self.agent)

        # create primary copy object for storage policy
        self.primary_copy = self.storage_policy.get_copy(copy_name="primary")
        self.sidb_id = \
            self.dedup_helper.get_sidb_ids(copy_name="primary", sp_id=self.storage_policy.storage_policy_id)[0]

        # add data to subclient content
        self.new_content(dir_path=self.client_machine.join_path(self.content_path, "new1"), dir_size=1)

        # set multiple readers for subclient
        self.subclient.data_readers = 4
        self.subclient.allow_multiple_readers = True

    def run_backup(self, job_type):
        """
        run a backup job for the subclient specified in Testcase

            Args:
                job_type        (str)       backup job type(FULL, synthetic_full, incremental, etc.)

        returns job id(int)
        """
        self.log.info("starting %s backup job...", job_type)
        job = self.subclient.backup(backup_level=job_type)

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup with error: {1}".format(job_type, job.delay_reason)
            )
        self.log.info("Backup job: %s completed successfully", job.job_id)

        return job.job_id

    def delete_job(self, job_list):
        """
        deletes all jobs whose job ids are passed as argument

            Args:
                job_list        (list/iterator)     list of job ids of jobs to be deleted

        returns None
        """
        if not job_list:
            self.log.error("no jobs specified for deletion!")
            return

        for job in job_list:
            self.log.info("deleting job %s ...", job)
            self.primary_copy.delete_job(job)

    def get_deleted_af_count(self, sidb_store_id):
        """
        returns the count of deletedAF entries in MMDeleteAF for given store

            Args:
                sidb_store_id       (int/str)       store_id

        returns count(int) of such entries
        """
        query = f"select count(*) from MMDeletedAF where SIDBStoreId = {sidb_store_id}"
        self.csdb.execute(query)
        count = int(self.csdb.fetch_one_row()[0])
        self.log.info(f"QUERY OUTPUT : {count}")
        return count

    def run_data_aging(self, time_in_secs=60):
        """
        runs data aging function at granular level for the policy specified in Testcase

            Args:
                time_in_secs        (int)       number of seconds program should wait for aging to take effect

        returns None
        """
        retry = 0
        query = """select count(*) from JMAdminJobInfoTable where opType=10"""
        self.csdb.execute(query)
        data_aging_jobs_running = self.csdb.fetch_one_row()[0]
        self.log.info(f"QUERY OUTPUT : {data_aging_jobs_running}")
        while data_aging_jobs_running != '0' and retry < 10:
            sleep(60)
            retry += 1
            self.csdb.execute(query)
            data_aging_jobs_running = self.csdb.fetch_one_row()[0]
            self.log.info(f"QUERY OUTPUT : {data_aging_jobs_running}")
        if data_aging_jobs_running != '0' and retry == 10:
            self.log.error("a data aging job is already running... bailing out..")
            raise Exception("failed to initiate data aging job..")

        retry = 0
        flag = False
        da_job = None
        while retry < 3:
            da_job = self.commcell.run_data_aging(copy_name='Primary',
                                                  storage_policy_name=self.storage_policy_name,
                                                  is_granular=True,
                                                  include_all_clients=True)
            retry += 1
            self.log.info("data aging job: %s", da_job.job_id)
            flag = da_job.wait_for_completion(timeout=180)
            if not flag:
                self.log.error("Failed to run data aging with error: %s", da_job.delay_reason)
            else:
                break

        if not flag:
            raise Exception("Failed to run data aging...")
        self.log.info("Data aging job completed.")
        sleep(time_in_secs)

    def is_dedupe_enabled(self, copy=None):
        """
        checks whether deduplication is enabled on the give storage policy copy

            Args:
                copy        (instance)       policy copy object

        returns Boolean
        """
        copy._get_copy_properties()
        dedupe_flags = copy._copy_properties.get('dedupeFlags').get('enableDeduplication')
        if dedupe_flags != 0:
            return True
        return False

    def set_store_pruning(self, store_id, enabled=True):
        """
        enables/disables physical pruning at store level for given store

            Args:
                store_id        (int/str)       sidb store id for given policy
                enabled         (boolean)       True: enables pruning(set by default)
                                                False: disables pruning at store level

        returns None
        """
        if enabled:
            query = f"update idxSIDBStore set flags = flags|536870912 where SIDBStoreId = {store_id}"
        else:
            query = f"update idxSIDBStore set flags = flags&~536870912 where SIDBStoreId = {store_id}"

        self.mm_helper.execute_update_query(query, self.sql_password, "sqladmin_cv")

    def check_error_codes(self, sidb_store_id, error_code):
        """
        checks whether the specified error codes have been set for all entries of a given store in MMDeleteAF table

            Args:
                sidb_store_id       (int/str)       store id of store whose entries are to be checked
                error_code          (int/str)       error code to be checked in MMDeleteAF table

        returns None
        """
        query = f"select failureerrorcode from mmdeletedaf where sidbstoreid ={sidb_store_id} and status != 2"
        self.csdb.execute(query)
        error_codes = self.csdb.rows
        self.log.info(f"QUERY OUTPUT : {error_codes}")
        for code in error_codes:
            if int(code[0]) != error_code:
                self.log.error("error code mismatch.. unexpected error code..")
                raise Exception("unexpected failure error codes found...")

        self.log.info("error codes for all corresponding mmdeleteaf entries match... expected result..")

    def run(self):
        """Run function of this test case"""
        try:
            # previous run cleanup
            self.previous_run_clean_up()

            # allocating necessary resources
            self.allocate_resources()

            # checking if dedup enabled
            if self.is_dedupe_enabled(copy=self.primary_copy):
                self.log.info("dedup enabled..!")
            else:
                self.log.error("dedup not enabled..!")
                raise Exception(f"dedup not enabled on storage policy {self.storage_policy_name}")

            # set pruning thread time interval
            self.mm_helper.update_mmpruneprocess(db_user="sqladmin_cv", db_password=self.sql_password,
                                                 min_value=2, mmpruneprocess_value=2)

            # run 3 jobs, 1 full and two incrementals
            jobs = []

            job_id = self.run_backup("FULL")
            jobs.append(job_id)
            self.new_content(dir_path=self.client_machine.join_path(self.content_path, "new2"), dir_size=1)
            job_id = self.run_backup("Incremental")
            jobs.append(job_id)
            self.new_content(dir_path=self.client_machine.join_path(self.content_path, "new3"), dir_size=1)
            job_id = self.run_backup("Incremental")
            jobs.append(job_id)

            # delete first job
            self.delete_job(jobs[0:1])

            # get deleteaf count
            old_count = self.get_deleted_af_count(self.sidb_id)

            # run data aging
            self.run_data_aging()

            # run a third incremental job
            self.new_content(dir_path=self.client_machine.join_path(self.content_path, "new4"), dir_size=1)
            job_id = self.run_backup("Incremental")
            jobs.append(job_id)

            # repeat until deleteaf count reaches 0 : run data aging and wait
            retry = 0
            count = self.get_deleted_af_count(self.sidb_id)

            while retry < 3 and count != 0:
                self.run_data_aging()
                count = self.get_deleted_af_count(self.sidb_id)
                retry += 1

            # validate that pruning occurred
            if count != 0:
                self.log.error("pruning did not occur! TC failed!")
                raise Exception("store pruning enabled, yet pruning did not occur! TC failed!")
            self.log.info("MMDeleteAF entries successfully pruned..")
            self.log.info("success! store pruning is enabled...initial deletedAFcount: %d  "
                          "final deletedAFcount: %d", old_count, count)

            # disable pruning on store
            self.set_store_pruning(store_id=self.sidb_id, enabled=False)

            # delete second and third job
            self.delete_job(jobs[1:3])

            # run data aging and see if MMDeleteAf entries are getting pruned
            retry = 0
            count = self.get_deleted_af_count(self.sidb_id)

            while retry < 3 and count != 0:
                self.run_data_aging()
                count = self.get_deleted_af_count(self.sidb_id)
                retry += 1

            # validate that pruning has not occurred
            if count == 0:
                self.log.error(
                    "pruning occurred! TC failed! could not disable store pruning! initial_deletedAFcount: %d  "
                    "final_deletedAFcount: %d", old_count, count)
                raise Exception("pruning occurred! TC failed! could not disable store pruning!")
            self.log.info("success! store pruning is disabled, initial_deletedAFcount: %d  "
                          "final_deletedAFcount: %d", old_count, count)

            # run data forecast report
            self.storage_policy.run_data_forecast()
            self.log.info("Data Forecast ran successfully...")
            sleep(180)

            # check error codes
            self.check_error_codes(sidb_store_id=self.sidb_id, error_code=65124)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""

        # resetting default values for store pruning and pruning interval
        self.mm_helper.update_mmpruneprocess(db_user="sqladmin_cv", db_password=self.sql_password)
        self.set_store_pruning(store_id=self.sidb_id, enabled=False)

        self.log.info("Performing unconditional cleanup")
        # removing initialized resources
        self.log.info("********* clean up **********")
        try:
            self.deallocate_resources()
            self.log.info("clean up COMPLETED")
        except Exception as exp:
            self.log.error("clean up ERROR %s", exp)
