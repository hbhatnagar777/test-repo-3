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

    is_dedupe_enabled()     -- checks whether the given storage policy has deduplication enabled

    check_subclient_prop()      -- checks whether start over has been reflected in all associated subclients
                                    of given policy

    check_store_sealing()       -- check whether associated store of given policy has been sealed

    is_job_type()        -- checks whether a given backup job has the given job type

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

This testcase tests and verifies starover operation at storage policy level.

Prerequisites: None

Input format:

"54199": {
        "ClientName": "<Client name>",
        "AgentName": "<IDataAgent name>",
        "MediaAgentName": "<Name of MediaAgent>",
        "storage_pool_name": "<name of the storage pool to be reused>" (optional argument),
        "dedup_path": "<path where dedup store to be created>" (optional argument)
        (Must provide LVM dedupe path for Linux MAs)
}

Design steps:

1. allocate resources for testcase
2. check if user has specified storage pool
    if yes, then skip step 3

3. if user has not specified storage pool run test on standalone policy (old framework)
    3.1 run 4 iterations of incremental backup jobs
        3.1.1 if iterator == 1 or 3, then
            i. check if the job is a full backup from csdb and from logs

        3.1.2 if iterator == 2 or 4, then
            i. check if the job is an incremental backup from csdb and from logs

        3.1.3 if iterator == 2, then
            i. run start over for standalone policy
            ii. check if subclient has been affected by start over
            ii. check if store has been sealed by start over

4. run testcase for storage pool with gdsp, and two dependent storage policies each with one subclient each
    4.1 run 4 iterations of incremental backup jobs for both subclients
        4.1.1 if iterator == 1 or 3, then
            i. check if the job for first subclient is a full backup from csdb and from logs
            ii. check if the job for second subclient is a full backup from csdb and from logs

        4.1.2 if iterator == 2 or 4, then
            i. check if the job for first subclient is an incremental backup from csdb and from logs
            ii. check if the job for second subclient is an incremental backup from csdb and from logs

        4.1.3 if iterator == 2, then
            i. run start over for gdsp
            ii. check if subclients of both dependent policies have been affected by start over
            ii. check if store of storage pool(gdsp) has been sealed by start over

5. deallocate all resources and exit testcase
"""

from cvpysdk.job import JobController
from AutomationUtils import constants
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
        self.name = "Start-Over case"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.cs_name = None
        self.mount_path = None
        self.dedup_store_path1 = None
        self.dedup_store_path2 = None
        self.content_path1 = None
        self.content_path2 = None
        self.content_path3 = None
        self.gdsp_name = None
        self.storage_pool_name = None
        self.library_name = None
        self.storage_policy_name1 = None
        self.storage_policy_name2 = None
        self.standalone_storage_policy_name = None
        self.backupset_name = None
        self.subclient_name1 = None
        self.subclient_name2 = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.job_controller = None
        self.opt_selector = None
        self.gdsp_copy_id = None
        self.storage_policy_id = None
        self.sidb_id = None
        self.testcase_path = None
        self.cs_machine = None
        self.client_machine = None
        self.media_agent = None
        self.media_agent_machine = None
        self.client = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.storage_pool = None
        self.library = None
        self.gdsp = None
        self.storage_policy1 = None
        self.storage_policy2 = None
        self.standalone_storage_policy = None
        self.backup_set = None
        self.subclient1 = None
        self.subclient2 = None
        self.subclient = None
        self.dedupe_engine = None
        self.gdsp_copy = None
        self.primary_copy1 = None
        self.primary_copy2 = None
        self.is_user_defined_storpool = False
        self.is_user_defined_dedup = False

    def setup(self):
        """Setup function of this test case"""
        if self.tcinputs.get("storage_pool_name"):
            self.is_user_defined_storpool = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        self.cs_name = self.commcell.commserv_client.name
        self.media_agent = self.tcinputs["MediaAgentName"]
        suffix = str(self.media_agent)[:] + "_" + str(self.client.client_name)[:]

        self.storage_policy_name1 = "{0}_SP1{1}".format(str(self.id), suffix)
        self.storage_policy_name2 = "{0}_SP2{1}".format(str(self.id), suffix)
        self.standalone_storage_policy_name = "{0}_SSP{1}".format(str(self.id), suffix)
        self.backupset_name = "{0}_BS{1}".format(str(self.id), suffix)
        self.subclient_name1 = "{0}_SC1{1}".format(str(self.id), suffix)
        self.subclient_name2 = "{0}_SC2{1}".format(str(self.id), suffix)
        self.subclient_name = "{0}_SSC{1}".format(str(self.id), suffix)
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

        if self.is_user_defined_storpool:
            self.storage_pool_name = self.tcinputs["storage_pool_name"]
            self.storage_pool = self.commcell.storage_pools.get(self.storage_pool_name)
            self.gdsp_name = self.storage_pool.global_policy_name
            self.gdsp = self.commcell.storage_policies.get(self.gdsp_name)
        else:
            self.gdsp_name = "{0}_GDSP{1}".format(str(self.id), suffix)

        self.library_name = "{0}_lib{1}".format(str(self.id), suffix)

        drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine)
        self.testcase_path_media_agent = "%s%s" % (drive_path_media_agent, self.id)

        self.testcase_path_client = "%s%s" % (drive_path_client, self.id)
        self.content_path1 = self.client_machine.join_path(self.testcase_path_client, "content_path1")
        self.content_path2 = self.client_machine.join_path(self.testcase_path_client, "content_path2")
        self.content_path3 = self.client_machine.join_path(self.testcase_path_client, "content_path3")

        if self.client_machine.check_directory_exists(self.content_path1):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path1)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")
        self.client_machine.create_directory(self.content_path1)
        self.log.info("content path created")

        if self.client_machine.check_directory_exists(self.content_path2):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path2)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")
        self.client_machine.create_directory(self.content_path2)
        self.log.info("content path created")

        if self.client_machine.check_directory_exists(self.content_path3):
            self.log.info("content path directory already exists")
            self.client_machine.remove_directory(self.content_path3)
            self.log.info("existing content deleted- so it doesn't interfere with dedupe")
        self.client_machine.create_directory(self.content_path3)
        self.log.info("content path created")

        self.mount_path = self.media_agent_machine.join_path(self.testcase_path_media_agent, "mount_path")

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path1 = self.media_agent_machine.join_path(self.tcinputs["dedup_path"], self.id, "_1")
            self.dedup_store_path2 = self.media_agent_machine.join_path(self.tcinputs["dedup_path"], self.id, "_2")
        else:
            self.dedup_store_path1 = self.media_agent_machine.join_path(
                self.testcase_path_media_agent, "dedup_store_path1")
            self.dedup_store_path2 = self.media_agent_machine.join_path(
                self.testcase_path_media_agent, "dedup_store_path2")

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
        """
        removes all resources allocated by the Testcase
        """
        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.agent.backupsets.delete(self.backupset_name)
            self.log.info("backup set deleted")
        else:
            self.log.info("backup set does not exist")

        if self.commcell.storage_policies.has_policy(self.storage_policy_name1):
            self.commcell.storage_policies.delete(self.storage_policy_name1)
            self.log.info("storage policy1 deleted")
        else:
            self.log.info("storage policy1 does not exist.")

        if self.commcell.storage_policies.has_policy(self.storage_policy_name2):
            self.commcell.storage_policies.delete(self.storage_policy_name2)
            self.log.info("storage policy2 deleted")
        else:
            self.log.info("storage policy2 does not exist.")

        if self.commcell.storage_policies.has_policy(self.standalone_storage_policy_name):
            self.commcell.storage_policies.delete(self.standalone_storage_policy_name)
            self.log.info("standalone storage policy deleted")
        else:
            self.log.info("storage policy does not exist.")

        if not self.is_user_defined_storpool:
            if self.commcell.storage_policies.has_policy(self.gdsp_name):
                self.commcell.storage_policies.delete(self.gdsp_name)
                self.log.info("GDSP deleted")
            else:
                self.log.info("GDSP does not exist.")

        if not self.is_user_defined_storpool:
            # here the storage pool is automatically created by gdsp and therefore has the same name as gdsp.
            if self.commcell.storage_pools.has_storage_pool(self.gdsp_name):
                self.commcell.storage_pools.delete(self.gdsp_name)
                self.log.info("Storage pool deleted")
            else:
                self.log.info("Storage pool does not exist.")

        if self.is_user_defined_storpool:
            if self.commcell.disk_libraries.has_library(self.library_name):
                self.commcell.disk_libraries.delete(self.library_name)
                self.log.info("Disk library deleted")
            else:
                self.log.info("Disk library does not exist.")

        # if self.media_agent_machine.check_directory_exists(self.mount_path):
        #     self.media_agent_machine.remove_directory(self.mount_path)
        #     self.log.info("mount path deleted")
        # else:
        #     self.log.info("mount path does not exist.")

        if self.client_machine.check_directory_exists(self.content_path1):
            self.client_machine.remove_directory(self.content_path1)
            self.log.info("content_path1 deleted")
        else:
            self.log.info("content_path1 does not exist.")

        if self.client_machine.check_directory_exists(self.content_path2):
            self.client_machine.remove_directory(self.content_path2)
            self.log.info("content_path2 deleted")
        else:
            self.log.info("content_path2 does not exist.")

        if self.client_machine.check_directory_exists(self.content_path3):
            self.client_machine.remove_directory(self.content_path3)
            self.log.info("content_path3 deleted")
        else:
            self.log.info("content_path3 does not exist.")

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
        """
        creates all necessary resources for testcase to run
        """
        # create dedupe store paths
        if self.media_agent_machine.check_directory_exists(self.dedup_store_path1):
            self.log.info("store path directory already exists")
        else:
            self.media_agent_machine.create_directory(self.dedup_store_path1)
            self.log.info("store path created")

        if self.media_agent_machine.check_directory_exists(self.dedup_store_path2):
            self.log.info("store path directory already exists")
        else:
            self.media_agent_machine.create_directory(self.dedup_store_path2)
            self.log.info("store path created")

        # create library if not provided
        if not self.is_user_defined_storpool:
            self.library = self.mm_helper.configure_disk_library(self.library_name, self.media_agent, self.mount_path)

        # create gdsp if not provided
        if not self.is_user_defined_storpool:
            self.gdsp = self.dedup_helper.configure_global_dedupe_storage_policy(
                global_storage_policy_name=self.gdsp_name,
                library_name=self.library_name,
                media_agent_name=self.media_agent,
                ddb_path=self.dedup_store_path1,
                ddb_media_agent=self.media_agent)

            # adding second partition to the ddb store
            self.gdsp_copy = self.gdsp.get_copy(copy_name="Primary_Global")
            self.gdsp_copy_id = self.gdsp_copy.storage_policy_id
            new_ddb_path = self.media_agent_machine.join_path(self.dedup_store_path1, "partition2")
            self.sidb_id = \
                self.dedup_helper.get_sidb_ids(copy_name="Primary_Global", sp_id=self.gdsp.storage_policy_id)[0]
            self.gdsp.add_ddb_partition(copy_id=self.gdsp_copy_id,
                                        sidb_store_id=self.sidb_id,
                                        sidb_new_path=new_ddb_path,
                                        media_agent=self.media_agent)
            self.gdsp.edit_block_size_on_gdsp(512)
            self.verify_block_size(self.gdsp_name, 512)

        # create dependent storage policy
        self.storage_policy1 = self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name1,
                                                                  library=self.library_name,
                                                                  media_agent=self.media_agent,
                                                                  global_policy_name=self.gdsp_name,
                                                                  dedup_media_agent="",
                                                                  dedup_path="")

        self.verify_block_size(self.gdsp_name, 512)
        self.verify_block_size(self.storage_policy_name1, 512)

        self.storage_policy2 = self.commcell.storage_policies.add(storage_policy_name=self.storage_policy_name2,
                                                                  library=self.library_name,
                                                                  media_agent=self.media_agent,
                                                                  global_policy_name=self.gdsp_name,
                                                                  dedup_media_agent="",
                                                                  dedup_path="")

        # creating a standalone storage policy if storage_pool not specified by user
        self.standalone_storage_policy = \
            self.commcell.storage_policies.add(storage_policy_name=self.standalone_storage_policy_name,
                                               library=self.library_name,
                                               media_agent=self.media_agent,
                                               dedup_media_agent=self.media_agent,
                                               dedup_path=self.dedup_store_path2)

        # create backupset and subclients
        self.backup_set = self.mm_helper.configure_backupset(self.backupset_name, self.agent)
        self.subclient1 = self.mm_helper.configure_subclient(self.backupset_name, self.subclient_name1,
                                                             self.storage_policy_name1, self.content_path1,
                                                             self.agent)
        self.subclient2 = self.mm_helper.configure_subclient(self.backupset_name, self.subclient_name2,
                                                             self.storage_policy_name2, self.content_path2,
                                                             self.agent)
        self.subclient = self.mm_helper.configure_subclient(self.backupset_name, self.subclient_name,
                                                            self.standalone_storage_policy_name, self.content_path3,
                                                            self.agent)

        # creating content
        self.new_content(dir_path=self.content_path1, dir_size=1)
        self.new_content(dir_path=self.content_path2, dir_size=1)
        self.new_content(dir_path=self.content_path3, dir_size=1)

    def verify_block_size(self, policy, size):
        """
        Verify block size on storage policy
        """
        query = f"""SELECT SIBlockSizeKB 
                        FROM archGroup
                        WHERE name = '{policy}'"""
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        block_size = int(self.csdb.fetch_one_row()[0])
        if block_size == size:
            self.log.info(f'Block Level Dedup Factor is accurate on {policy} with size {size}')
        else:
            self.log.error(f'Block Level Dedup Factor not as expected on {policy}. Expected size: {size}'
                           f' Current size: {block_size}')
            raise Exception(f'Block Level Dedup Factor not as expected on {policy}')

    def run_backup(self, subclient, job_type):
        """
        run a backup job for the subclient specified in Testcase

            Args:
                subclient       (instance)      instance of subclient to be backed up
                job_type        (str)           backup job type(FULL, synthetic_full, incremental, etc.)

        returns job id(int)
        """
        self.log.info("starting %s backup job...", job_type)
        job = subclient.backup(backup_level=job_type)

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup with error: {1}".format(job_type, job.delay_reason)
            )
        self.log.info("Backup job: %s completed successfully", job.job_id)

        return job.job_id

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

    def verify_logs(self, client_name, log_file, reg_exp, job_id):
        """
        checks log files for given regex

            Args:
                client_name     (str)       name of the client machine in which the logs reside
                log_file        (str)       name of the log file to be parsed
                reg_exp         (str)       regular expression to be checked for in logs
                job_id          (int/str)   id of the job whose logs are to be parsed

        returns Boolean
        """
        matched_line, matched_string = self.dedup_helper.parse_log(client=client_name,
                                                                   log_file=log_file,
                                                                   regex=reg_exp,
                                                                   jobid=job_id,
                                                                   single_file=False)
        if matched_line:
            self.log.info("SUCCESS  Result :Pass")
            return True
        self.log.error("ERROR   Result:Fail")
        self.log.error("Expected log line not found!")
        return False

    def check_subclient_prop(self, storage_policy):
        """
        checks whether start over has been reflected in subclient properties

            Args:
                storage_policy      (str)       name of the policy whose associated clients are to be checked

        returns None
        """
        query = """select count(*) from APP_Application
                   where dataArchGrpID in (select id from archGroup where name ='""" + storage_policy + "')"
        self.csdb.execute(query)
        no_sub_clients = self.csdb.fetch_one_row()[0]
        query = """select count(*)
                    from APP_SubClientProp
                    WHERE attrName = 'Reason last backup time cleared' and attrVal=44 and componentNameId  in
                    (select id from APP_Application where dataArchGrpID in
                    (select id from archGroup where name ='""" + storage_policy + "'))"
        self.csdb.execute(query)
        value = self.csdb.fetch_one_row()[0]
        if value == no_sub_clients:
            self.log.info("ref time was reset!")
        else:
            self.log.info("ref time was not reset!")
            raise Exception("start over failed to reset ref time for associated clients!")

    def check_store_sealing(self, storage_policy):
        """
        checks whether start over has sealed the store for the given policy

            Args:
                storage_policy      (str)       name of the policy whose associated store is to be checked

        returns None
        """
        query = """select firstbackuptime
                    from idxsidbsubstore
                    WHERE  sidbstoreid  in
                    (select sidbstoreid from archGroupCopy where id in
                    (select defaultcopy from archGroup where name ='""" + storage_policy + "'))"
        self.csdb.execute(query)
        firstbackuptime = self.csdb.fetch_one_row()[0]
        if firstbackuptime == "-1":
            self.log.info("store was sealed!")
        else:
            self.log.info("store was not sealed!")
            raise Exception("start over did not seal store!")

    def is_job_type(self, job_id, job_type):
        """
        checks whether the job specified was of the specified backup type

            Args:
                job_id          (int/str)       id of job to be checked
                job_type        (str)           expected job type (Full or Incremental)

        returns Boolean
        """
        job = self.job_controller.get(job_id)
        if job.backup_level == job_type:
            self.log.info("the job %s is an %s backup.. expected.. ", job_id, job_type)
            return True
        self.log.error("unexpected job type!..")
        return False

    def run(self):
        """Run function of this test case"""
        try:
            # previous run cleanup
            self.previous_run_clean_up()

            # allocating necessary resources
            self.allocate_resources()

            # *****************************************************************************************
            # standalone sp start over
            if not self.is_user_defined_storpool:

                self.primary_copy1 = self.standalone_storage_policy.get_copy(copy_name="primary")
                self.storage_policy_id = self.standalone_storage_policy.storage_policy_id
                self.sidb_id = \
                    self.dedup_helper.get_sidb_ids(copy_name="primary", sp_id=self.storage_policy_id)[0]

                # checking if dedup enabled
                if self.is_dedupe_enabled(copy=self.primary_copy1):
                    self.log.info("dedup enabled..!")
                else:
                    self.log.error("dedup not enabled..!")
                    raise Exception("dedup not enabled on storage policy {}".
                                    format(self.standalone_storage_policy_name))

                for iterator in range(1, 5):
                    self.log.info("iteration no : %d", iterator)
                    self.log.info("submitting backup job...")

                    job_id = self.run_backup(subclient=self.subclient, job_type="Incremental")

                    if iterator in (1, 3):
                        self.log.info("Is it full backup?")
                        if (self.is_job_type(job_id=job_id, job_type="Full") or
                                self.verify_logs(client_name=self.cs_name, log_file="JobManager.log",
                                                 reg_exp="Backup Level [Full]", job_id=job_id)):
                            self.log.info("It is a full backup..")
                        else:
                            self.log.error("Not a full backup..")
                            raise Exception("Job backup level not expected..")

                    if iterator in (2, 4):
                        self.log.info("Is it incremental backup?")
                        if (self.is_job_type(job_id=job_id, job_type="Incremental") or
                                self.verify_logs(client_name=self.cs_name, log_file="JobManager.log",
                                                 reg_exp="Backup Level [Incremental]", job_id=job_id)):
                            self.log.info("It is a incremental backup..")
                        else:
                            self.log.error("Not a incremental backup..")
                            raise Exception("Job backup level not expected..")

                    if iterator == 2:
                        self.log.info("starting over SP")
                        self.standalone_storage_policy.start_over()
                        self.check_subclient_prop(storage_policy=self.standalone_storage_policy_name)
                        self.check_store_sealing(storage_policy=self.standalone_storage_policy_name)

            # ********************************************************************************************************
            # storage pool start over
            self.primary_copy1 = self.storage_policy1.get_copy(copy_name="primary")
            self.primary_copy2 = self.storage_policy2.get_copy(copy_name="primary")
            self.storage_policy_id = self.gdsp.storage_policy_id
            self.sidb_id = \
                self.dedup_helper.get_sidb_ids(copy_name="primary_global", sp_id=self.storage_policy_id)[0]

            # checking if dedup enabled
            if self.is_dedupe_enabled(copy=self.primary_copy1) and self.is_dedupe_enabled(copy=self.primary_copy2):
                self.log.info("dedup enabled..!")
            else:
                self.log.error("dedup not enabled..!")
                raise Exception("dedup not enabled on storage policy!")

            for iterator in range(1, 5):
                self.log.info("iteration no : %d", iterator)
                self.log.info("submitting backup jobs...")

                job_id1 = self.run_backup(subclient=self.subclient1, job_type="Incremental")
                job_id2 = self.run_backup(subclient=self.subclient2, job_type="Incremental")

                if iterator in (1, 3):
                    self.log.info("Is it full backup?")
                    if (self.is_job_type(job_id=job_id1, job_type="Full") or
                            self.verify_logs(client_name=self.cs_name, log_file="JobManager.log",
                                             reg_exp="Backup Level [Full]", job_id=job_id1)):
                        self.log.info("It is a full backup..")
                    else:
                        self.log.error("Not a full backup..")
                        raise Exception("Job backup level not expected..")

                    if (self.is_job_type(job_id=job_id2, job_type="Full") or
                            self.verify_logs(client_name=self.cs_name, log_file="JobManager.log",
                                             reg_exp="Backup Level [Full]", job_id=job_id2)):
                        self.log.info("It is a full backup..")
                    else:
                        self.log.error("Not a full backup..")
                        raise Exception("Job backup level not expected..")

                if iterator in (2, 4):
                    self.log.info("Is it incremental backup?")
                    if (self.is_job_type(job_id=job_id1, job_type="Incremental") or
                            self.verify_logs(client_name=self.cs_name, log_file="JobManager.log",
                                             reg_exp="Backup Level [Incremental]", job_id=job_id1)):
                        self.log.info("It is a incremental backup..")
                    else:
                        self.log.error("Not a incremental backup..")
                        raise Exception("Job backup level not expected..")

                    if (self.is_job_type(job_id=job_id2, job_type="Incremental") or
                            self.verify_logs(client_name=self.cs_name, log_file="JobManager.log",
                                             reg_exp="Backup Level [Incremental]", job_id=job_id2)):
                        self.log.info("It is a incremental backup..")
                    else:
                        self.log.error("Not a incremental backup..")
                        raise Exception("Job backup level not expected..")

                if iterator == 2:
                    self.log.info("starting over SP")
                    self.gdsp.start_over()
                    self.check_subclient_prop(storage_policy=self.storage_policy_name1)
                    self.check_subclient_prop(storage_policy=self.storage_policy_name2)
                    self.check_store_sealing(storage_policy=self.gdsp_name)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        # removing initialized resources
        self.log.info("********* clean up **********")
        try:
            self.deallocate_resources()
            self.log.info("clean up COMPLETED")
        except Exception as exp:
            self.log.error("clean up ERROR %s", exp)
