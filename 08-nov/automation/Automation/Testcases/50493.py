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

    run_backup()        -- for running a backup job of given type

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    check_move_in_progress_flag()   -- checks if move flag is set on substore

    check_obsolete_file_created()   -- checks if .obsolete file has been created on source path

    get_split_folder()      -- returns the path to split folder on DDB MA

    get_full_store_path()   -- returns physical path to store on DDB MA

Prerequisites: None

Note regarding sql credentials :

    In order to ensure security,
    sql credentials have to be passed to the TC via config.json file under CoreUtils/Templates

    populate the following fields in config file as required,
    "SQL": {
        "Username": "<SQL_SERVER_USERNAME>",
        "Password": "<SQL_SERVER_PASSWORD>"
    }

    At the time of execution the creds will be automatically fetched by TC.

Input JSON:

"50493": {
        "ClientName": "<Client name>",
        "AgentName": "<IDataAgent name>",
        "MediaAgentName1": "<Name of MediaAgent>",
        "MediaAgentName2": "<Name of MediaAgent>",
        "storage_pool_name": "<name of the storage pool to be reused>" (optional argument),
        "dedup_path1": "<path where dedup store to be created>" (optional argument),
        "dedup_path2": "<path where dedup store to be created>" (optional argument)
        (Must provide LVM dedupe path for Linux MAs)
}

Design steps:

1.disable ransomware protection on DDB MA if enabled
2.allocate resources
3.run two full backups with unique content
4.bloat the split folder for DDB with junk data of size 15 gb
5.start DDB move on store
6.wait for move job to start running
7.suspend move job after two minutes
8.check if move in progress flag was set on substore
9.resume the move job and kill it after it has ran for two minutes
10.verify that flag was reset on substore
11.verify that store path has not changed
12.run a full backup on store to confirm store is online
13.start a new DDB move job
14.verify that it completes successfully
15.verify that .obsolete file was created at source path
16.verify that move flag was reset on substore and path has been updated
17.verify that junk folder was also moved as part of move job
18.wait for source path cleanup to happen
19.run a new backup to confirm that store at destination path is online
20.perform cleanup

"""
import re
from time import sleep
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
from AutomationUtils import config


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
        self.name = "Testcase to verify DDB move kill operation"
        self.tcinputs = {
            "MediaAgentName1": None,
            "MediaAgentName2": None
        }
        self.cs_name = None
        self.mount_path = None
        self.dedup_store_path1 = None
        self.dedup_store_path2 = None
        self.dedup_store_path3 = None
        self.content_path = None
        self.restore_path = None
        self.storage_pool_name = None
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.opt_selector = None
        self.store = None
        self.substore = None
        self.sidb_id = None
        self.testcase_path = None
        self.cs_machine = None
        self.client_machine = None
        self.sql_username = None
        self.sql_password = None
        self.media_agent1 = None
        self.media_agent_obj1 = None
        self.media_agent_machine1 = None
        self.media_agent2 = None
        self.media_agent_obj2 = None
        self.media_agent_machine2 = None
        self.client = None
        self.testcase_path_client = None
        self.testcase_path_media_agent1 = None
        self.testcase_path_media_agent2 = None
        self.storage_pool = None
        self.library = None
        self.gdsp_name = None
        self.gdsp = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.dedupe_engine = None
        self.primary_copy = None
        self.secondary_copy = None
        self.tertiary_copy = None
        self.is_user_defined_storpool = False
        self.is_user_defined_dedup1 = False
        self.is_user_defined_dedup2 = False
        self.is_ransomware_enabled = False
        self.backup_job = None
        self.dv2_job = None
        self.move_job = None
        self.result_string = ""

    def setup(self):
        """Setup function of this test case"""
        if self.tcinputs.get("storage_pool_name"):
            self.is_user_defined_storpool = True
        if self.tcinputs.get("dedup_path1"):
            self.is_user_defined_dedup1 = True
        if self.tcinputs.get("dedup_path2"):
            self.is_user_defined_dedup2 = True

        self.cs_name = self.commcell.commserv_client.name
        self.media_agent1 = self.tcinputs["MediaAgentName1"]
        self.media_agent2 = self.tcinputs["MediaAgentName2"]
        suffix = str(self.media_agent1) + "_" + str(self.client.client_name)

        self.storage_policy_name = "{0}_SP{1}".format(str(self.id), suffix)
        self.backupset_name = "{0}_BS{1}".format(str(self.id), suffix)
        self.subclient_name = "{0}_SC{1}".format(str(self.id), suffix)
        self.mm_helper = MMHelper(self)
        self.dedup_helper = DedupeHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = Machine(self.client)
        self.media_agent_obj1 = self.commcell.media_agents.get(self.media_agent1)
        self.media_agent_obj2 = self.commcell.media_agents.get(self.media_agent2)
        self.media_agent_machine1 = Machine(self.media_agent1, self.commcell)
        self.media_agent_machine2 = Machine(self.media_agent2, self.commcell)

        if not self.is_user_defined_dedup1 and "unix" in self.media_agent_machine1.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for given Unix MA1!..")
            raise Exception("LVM enabled dedup path not supplied for given Unix MA1!..")

        if not self.is_user_defined_dedup2 and "unix" in self.media_agent_machine2.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for given Unix MA2!..")
            raise Exception("LVM enabled dedup path not supplied for given Unix MA2!..")

        drive_path_client = self.opt_selector.get_drive(
            self.client_machine)
        self.testcase_path_client = "%s%s" % (drive_path_client, self.id)
        self.content_path = self.client_machine.join_path(
            self.testcase_path_client, "content_path")

        if self.is_user_defined_storpool:
            self.storage_pool_name = self.tcinputs["storage_pool_name"]
            self.storage_pool = self.commcell.storage_pools.get(self.storage_pool_name)
            self.gdsp = self.commcell.storage_policies.get(self.storage_pool.global_policy_name)

        else:
            self.gdsp_name = "{0}_GDSP{1}".format(str(self.id), suffix)

        self.library_name = "{0}_lib{1}".format(str(self.id), suffix)

        drive_path_media_agent1 = self.opt_selector.get_drive(
            self.media_agent_machine1)
        self.testcase_path_media_agent1 = "%s%s" % (drive_path_media_agent1, self.id)

        drive_path_media_agent2 = self.opt_selector.get_drive(
            self.media_agent_machine2)
        self.testcase_path_media_agent2 = "%s%s" % (drive_path_media_agent2, self.id)

        self.testcase_path_client = "%s%s" % (drive_path_client, self.id)
        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")

        if self.client_machine.check_directory_exists(self.content_path):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")

        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")

        self.mount_path = self.media_agent_machine1.join_path(
            self.testcase_path_media_agent1, "mount_path")

        if self.is_user_defined_dedup1:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path1 = self.media_agent_machine1.join_path(self.tcinputs["dedup_path1"], self.id)
        else:
            self.dedup_store_path1 = self.media_agent_machine1.join_path(
                self.testcase_path_media_agent1, "dedup_store_path", "1")

        if self.is_user_defined_dedup2:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path2 = self.media_agent_machine2.join_path(self.tcinputs["dedup_path2"], self.id)
        else:
            self.dedup_store_path2 = self.media_agent_machine2.join_path(
                self.testcase_path_media_agent2, "dedup_store_path", "2")

        self.dedup_store_path3 = self.media_agent_machine1.join_path(self.dedup_store_path1, "new_ddb")

        # sql connections
        self.sql_username = config.get_config().SQL.Username
        self.sql_password = config.get_config().SQL.Password

    def new_content(self, machine, dir_path, dir_size):
        """
        generates new incompressible data in given directory/folder

            Args:
                machine         (object)    machine object for client on which we are creating content
                dir_path        (str)       full path of directory/folder in which data is to be added
                dir_size        (float)     size of data to be created(in GB)

        returns None
        """
        if machine.check_directory_exists(dir_path):
            machine.remove_directory(dir_path)
        machine.create_directory(dir_path)
        self.opt_selector.create_uncompressable_data(client=machine,
                                                     size=dir_size,
                                                     path=dir_path)

    def deallocate_resources(self):
        """removes all resources allocated by the Testcase"""
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
            self.log.info("content_path deleted")
        else:
            self.log.info("content_path does not exist.")

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
            # here the storage pool is automatically created by gdsp and therefore has the same name as gdsp.
            if self.commcell.storage_policies.has_policy(self.gdsp_name):
                self.commcell.storage_policies.delete(self.gdsp_name)
                self.log.info("gdsp deleted")
                self.commcell.disk_libraries.refresh()
            else:
                self.log.info("gdsp does not exist.")

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
        if not self.media_agent_machine1.check_directory_exists(self.dedup_store_path1):
            self.media_agent_machine1.create_directory(self.dedup_store_path1)
            self.log.info("store path 1 created")
        else:
            self.log.info("store path 1 directory already exists")

        if not self.media_agent_machine2.check_directory_exists(self.dedup_store_path2):
            self.media_agent_machine2.create_directory(self.dedup_store_path2)
            self.log.info("store path 2 created")
        else:
            self.log.info("store path 2 directory already exists")

        if not self.media_agent_machine1.check_directory_exists(self.dedup_store_path3):
            self.media_agent_machine1.create_directory(self.dedup_store_path3)
            self.log.info("store path 3 created")
        else:
            self.log.info("store path 3 directory already exists")

        # create library if not provided
        if not self.is_user_defined_storpool:
            self.library = self.mm_helper.configure_disk_library(
                self.library_name, self.media_agent1, self.mount_path)

        # create gdsp if not provided
        if not self.is_user_defined_storpool:
            self.gdsp = self.dedup_helper.configure_global_dedupe_storage_policy(
                global_storage_policy_name=self.gdsp_name,
                library_name=self.library_name,
                media_agent_name=self.media_agent1,
                ddb_path=self.dedup_store_path1,
                ddb_media_agent=self.media_agent1)

        # create dependent storage policy
        self.storage_policy = self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name,
                                                                 library=self.library_name,
                                                                 media_agent=self.media_agent1,
                                                                 global_policy_name=self.gdsp_name,
                                                                 dedup_media_agent=self.media_agent2,
                                                                 dedup_path=self.dedup_store_path1)

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

        # set multiple readers for subclient
        self.subclient.data_readers = 4
        self.subclient.allow_multiple_readers = True

        # set enc on primary copy BlowFish 128
        self.gdsp.get_copy("Primary_Global").set_encryption_properties(re_encryption=True, encryption_type="BlowFish",
                                                                       encryption_length=128)

    def run_backup(self, job_type):
        """
        run a backup job for the subclient specified in Testcase

            Args:
                job_type        (str)       backup job type(FULL, synthetic_full, incremental, etc.)

        returns job id(int)
        """
        job = self.subclient.backup(backup_level=job_type)
        self.log.info("starting backup %s job with job id - %s", job_type, job.job_id)

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup with error: {1}".format(job_type, job.delay_reason)
            )
        self.log.info("Backup job: %s completed successfully", job.job_id)

        return job.job_id

    def check_move_in_progress_flag(self, substore_id):
        """
        checks if move flag is set on given substore

        Args:
            substore_id     str     substore id

        returns Boolean
        """
        query = f"""select flags&64 from idxSIDBSubStore where SubStoreId = {substore_id}"""
        self.csdb.execute(query)
        flag = self.csdb.fetch_all_rows()
        if flag[0][0] == '64':
            return True
        return False

    def check_obsolete_file_created(self, client, path):
        """
        checks if .obsolete file was created at given path

        Args:
            client      object      client machine instance
            path        str         path to split folder
        """
        return client.check_file_exists(path)

    def get_split_folder(self, ma_machine, store_path, store_id):
        """
        returns split folder path for given store

        Args:
            ma_machine      object      DDB media agent instance
            store_path      str         SIDB path of store
            store_id        str         SIDB store id
        """
        full_store_path = self.get_full_store_path(ma_machine, store_path, store_id)
        files_and_folders = ma_machine.get_folders_in_path(full_store_path, recurse=False)
        regex = re.compile(".*Split.*")
        split_folder = list(filter(regex.match, files_and_folders))
        return split_folder[0]

    def get_full_store_path(self, ma_machine, store_path, store_id):
        """
                returns physical folder path for given store

                Args:
                    ma_machine      object      DDB media agent instance
                    store_path      str         SIDB path of store
                    store_id        str         SIDB store id
        """
        return ma_machine.join_path(store_path, "CV_SIDB", '2', str(store_id))

    def run(self):
        """Run function of this test case"""
        try:
            # if source MA has windows OS, then remove ransomware protection to bloat ddb with junk data
            self.log.info("checking if source MA is unix machine..")
            if "unix" not in self.media_agent_machine1.os_info.lower():
                self.log.info("source MA is a windows machine so we need to disable ransomware protection..")
                self.is_ransomware_enabled = \
                    self.mm_helper.ransomware_protection_status(self.media_agent_obj1.media_agent_id)
                if self.is_ransomware_enabled:
                    # set the interval minutes between disk space updates to 5 minutes
                    query = """ update MMConfigs
                                set value = 5
                                where name = 'MMS2_CONFIG_STRING_MAGNETIC_CONFIG_UPDATE_INTERVAL_MIN'"""
                    self.log.info("EXECUTING QUERY %s", query)
                    self.opt_selector.update_commserve_db(
                        query, user_name=self.sql_username, password=self.sql_password)
                    self.log.info("interval minutes between disk space updates set to 5 minutes")

                    self.media_agent_obj1.set_ransomware_protection(False)
                    self.log.info("ransomware protection disabled intentionally")
                    self.log.info("waiting for 360 seconds...")
                    sleep(360)
                else:
                    self.log.info("ransomware protection is already disabled on source MA..")

            # previous run cleanup
            self.previous_run_clean_up()

            # allocating necessary resources
            self.allocate_resources()

            # adding new content and running a full backup iteratively
            for index in range(2):
                # add data to subclient content
                self.log.info("adding content to subclient..")
                self.new_content(machine=self.client_machine,
                                 dir_path=self.client_machine.join_path(self.content_path, "new", str(index)),
                                 dir_size=2)
                # run full backup
                job = self.run_backup("Full")

            # getting engine details
            self.dedupe_engine = self.commcell.deduplication_engines.get(self.gdsp_name, "Primary_Global")
            self.store = self.dedupe_engine.get(self.dedupe_engine.all_stores[0][0])
            self.substore = self.store.get(self.store.all_substores[0][0])
            # get access path details for substore
            old_path = self.substore.path
            self.log.info("store path on source as per CSDB : %s", old_path)

            # get the path for split folder on ddb_ma
            split_folder_path = self.get_split_folder(self.media_agent_machine1, self.substore.path,
                                                      self.store.store_id)
            self.log.info("split folder path on source : %s", split_folder_path)

            self.log.info("checking if source MA is unix machine..")
            if "unix" not in self.media_agent_machine1.os_info.lower():
                self.log.info("source MA is a windows machine so we need add permissions on ddb folders..")
                # adding permissions so that we can modify ddb folders
                self.media_agent_machine1.modify_ace(user='Everyone', path=split_folder_path, permission='FullControl',
                                                     action='Allow', folder=True, inheritance=2)
                self.log.info("giving user full access on following path %s", split_folder_path)

            # bloat partition location with junk data to increase duration of move operation
            self.log.info("bloating DDB folders using junk data..")
            self.new_content(machine=self.media_agent_machine1,
                             dir_path=self.media_agent_machine1.join_path(split_folder_path, "junk_data"),
                             dir_size=15)

            # add back ransomware protection after it was disabled in case of windows MA
            self.log.info("checking if source MA is unix machine..")
            if "unix" not in self.media_agent_machine1.os_info.lower():
                self.media_agent_obj1.set_ransomware_protection(True)
                self.log.info("ransomware protection enabled intentionally")
                self.log.info("waiting for 360 seconds...")
                sleep(360)
                self.is_ransomware_enabled = \
                    self.mm_helper.ransomware_protection_status(self.media_agent_obj1.media_agent_id)

            # start ddb move job on partition
            self.move_job = self.store.move_partition(dest_path=self.dedup_store_path2,
                                                      dest_ma_name=self.media_agent2,
                                                      substoreid=self.substore.substore_id)
            self.log.info("""started normal ddb move job [%s] on substore [%s] to location [%s] on MA [%s] from
                            location [%s] on MA [%s]""",
                          self.move_job.job_id, self.substore.substore_id, self.dedup_store_path2, self.media_agent2,
                          self.dedup_store_path1, self.media_agent1)

            # check for job to hit running state
            self.log.info("wait for move job to reach running status..")
            self.log.info(self.move_job.status)
            while self.move_job.status != "Running":
                self.log.info(self.move_job.status)
                self.log.info("sleeping for 5 secs..")
                sleep(5)
            self.log.info(self.move_job.status)
            # wait for move job to suspend other operations and then suspend move job
            self.log.info("move job is now running.. letting it run for 2 minutes..")
            sleep(120)

            self.log.info("suspending move job : %s", self.move_job.job_id)
            self.move_job.pause(wait_for_job_to_pause=True)

            # check if move in progress flag is set on ddb and sidb suspended flag is set on substore
            if self.check_move_in_progress_flag(self.substore.substore_id):
                self.log.info("move in progress flag has been set on substore..")
            else:
                raise Exception("move in progress flag was not set on substore..")

            # resuming move job
            self.log.info("resuming move job : %s", self.move_job.job_id)
            self.move_job.resume()
            while self.move_job.status != "Running":
                self.log.info(self.move_job.status)
                self.log.info("sleeping for 5 secs..")
                sleep(5)
            self.log.info(self.move_job.status)

            # let the move job run for 2 minutes
            self.log.info("move job has resumed and is now running.. letting it run for 2 minutes..")
            sleep(120)

            # killing move job
            self.log.info("killing move job : %s", self.move_job.job_id)
            self.move_job.kill(wait_for_job_to_kill=True)

            self.log.info("sleeping for 1 minute..")
            sleep(60)
            self.substore.refresh()

            # check if move flag is reset on ddb
            if not self.check_move_in_progress_flag(self.substore.substore_id):
                self.log.info("move in progress flag has been reset after killing move job..")
            else:
                raise Exception("move in progress flag was not reset after killing move job.. unexpected..")

            # get access path details for substore after killing move
            path = self.substore.path
            self.log.info("store path as per CSDB : %s", path)

            # verify that path has not been changed as per expectations
            if path == self.dedup_store_path1:
                self.log.info("store path has not changed as move job was killed..")
            else:
                raise Exception("unexpected store path changed even though move job was killed..")

            # run a new backup job to verify that store is online and accessible
            self.log.info("running backup to verify that store is available after killing move job..")
            self.new_content(machine=self.client_machine,
                             dir_path=self.client_machine.join_path(self.content_path, "new", "123"),
                             dir_size=2)
            job = self.run_backup("Full")

            # start second ddb move job on partition
            self.move_job = self.store.move_partition(dest_path=self.dedup_store_path2,
                                                      dest_ma_name=self.media_agent2,
                                                      substoreid=self.substore.substore_id)
            self.log.info("""started normal ddb move job [%s] on substore [%s] to location [%s] on MA [%s] from
                                        location [%s] on MA [%s]""",
                          self.move_job.job_id, self.substore.substore_id, self.dedup_store_path2, self.media_agent2,
                          self.dedup_store_path1, self.media_agent1)

            # wait for move job to complete
            if not self.move_job.wait_for_completion():
                raise Exception(
                    f"Failed to run DDB move with error: {self.move_job.delay_reason}"
                )
            self.log.info("DDB move job: %s completed successfully", self.move_job.job_id)

            self.substore.refresh()

            # check for presence of .obsolete file
            self.log.info("verifying if .obsolete file was created at source : MA [%s] location [%s]",
                          self.media_agent1, split_folder_path)
            if self.check_obsolete_file_created(self.media_agent_machine1,
                                                self.media_agent_machine1.join_path(split_folder_path, ".obsolete")):
                self.log.info(".obsolete file present on source MA..")
            else:
                self.log.error("file not found..")
                raise Exception(".obsolete file not present at source MA..")

            # check if move flag is reset on ddb
            if not self.check_move_in_progress_flag(self.substore.substore_id):
                self.log.info("move in progress flag has been reset post move..")
            else:
                raise Exception("move in progress flag was not reset post move.. unexpected..")

            # get access path details for substore after move
            new_path = self.substore.path
            self.log.info("store path on destination as per CSDB : %s", new_path)

            # verify that path has been changed as per expectations
            if new_path == self.dedup_store_path2:
                self.log.info("destination path of store matches the value provided by user..")
            else:
                raise Exception("unexpected destination path..")

            # get the path for split folder on ddb_ma
            new_split_folder_path = self.get_split_folder(self.media_agent_machine2, self.dedup_store_path2,
                                                          self.store.store_id)
            self.log.info("split folder path at destination MA : %s", new_split_folder_path
                          )
            # verify that junk file got transferred to the new path
            if self.media_agent_machine2.check_directory_exists(
                    self.media_agent_machine2.join_path(new_split_folder_path, "junk_data")):
                self.log.info("verified that junk folder embedded into store also got transferred to destination")
            else:
                raise Exception("junk folder inside store was not moved.. unexpected for a blind move..")

            # source path cleanup validation
            # modify config param MMS2_CONFIG_DEDUP_NUMBEROFDAYS_KEEP_SOURCE_DDB_AFTER_MOVE
            # so that cleanup takes place
            # by default cleanup happens immediately as param is set to 0
            self.log.info(
                "waiting for source path cleanup to happen.. [by default, this happens immediately after move]")
            for i in range(20):
                self.log.info("wait 1 more minute for cleanup to happen..")
                sleep(60)
                if self.media_agent_machine1.check_directory_exists(split_folder_path):
                    self.log.error("cleanup has not occurred yet..")
                else:
                    break
                if i == 19:
                    raise Exception("timed out waiting for source path cleanup..")
            self.log.info("source path cleanup took place..")

            # run a new backup job to verify that store is online and accessible
            self.new_content(machine=self.client_machine,
                             dir_path=self.client_machine.join_path(self.content_path, "new", "123"),
                             dir_size=2)
            job = self.run_backup("Full")

            self.log.info("All Validations Completed.. Testcase executed successfully..")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if "unix" not in self.media_agent_machine1.os_info.lower():
            if not self.is_ransomware_enabled:
                self.media_agent_obj1.set_ransomware_protection(True)
                self.log.info("ransomware protection enabled post execution..")
        if self.move_job and (self.move_job.state != "Completed" and self.move_job.state != "Killed"):
            self.move_job.kill(wait_for_job_to_kill=True)
            self.log.info(
                "the killing the following ddb move job as part of teardown : [%s]",
                self.move_job.job_id)
        # removing initialized resources
        try:
            self.deallocate_resources()
        except BaseException:
            self.log.warning("Cleanup Failed, please check setup ..")
