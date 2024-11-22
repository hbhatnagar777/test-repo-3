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

    delete_job()       -- deletes all the jobs whose job ids are given in argument list

    run_data_aging()        -- runs data aging at granular storage policy level for given storage policy

    is_dedupe_enabled()     -- checks whether the given storage policy has deduplication enabled

    get_deleted_af_ids()        -- retrieves the list of all afids in mmdeleteaf corresponding to the given store

    query_mps()     -- retrieves the mp id and mountpath name of all mountpaths associated with a given job

    query_af_ids()      -- retrieves the list of afids related to a given job

    is_mp_pruning_enabled()      -- checks whether pruning is enabled/disabled for given mountpath

    verify_logs()       -- checks whether change in pruning behaviour is reflected in logs

    toggle_mp_pruning()     -- enables/disables pruning on a given mp depending on Boolean given by user

    check_prune_request()       -- checks whether prune request was issued by parsing logs

    check_error_codes()     -- checks whether all entries in mmdeleteaf contain the user specified error code

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

This testcase disables physical pruning at store level and checks if pruning occurs or not.

Prerequisites: None

Input format:

Input JSON:

"53593": {
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
3. run a full backup on the subclient with 4GB of content
4. get the details of all mountpaths associated with the above job,
    also get the ids of all archive files associated with the job
5. check if pruning is enabled by default on all associated mountpaths
6. disable pruning on a selected mountpath
7. confirm the mp_pruning_flag has been set accordingly
8. verify that the change has been reflected in both cvma and mediamanager logs
9. delete the job
10. run data aging
11. check whether all archive files populate the MMDeleteAF table
12. verify whether prune request is sent for the store
13. confirm that only entries corresponding to other mountpaths are being pruned
14. run data forecast on storage policy
15. check that proper error codes are set for entries corresponding to selected mp
16. enable pruning on selected mp
17. confirm the mp_pruning_flag has been set accordingly
18. verify that the change has been reflected in both cvma and mediamanager logs
19. verify whether prune request is sent for the store
20. confirm that all entries related to this mp are pruned
21. reset pruning interval values to default
22. deallocate all test resources

"""

from time import sleep
from AutomationUtils import constants, commonutils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
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
        self.name = "Disable Pruning on MountPath"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.cs_name = None
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
        self.dedupe_engine = None
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
        # self.sql_password = commonutils.get_cvadmin_password(self.commcell)
        self.sql_username = config.get_config().SQL.Username
        self.sql_password = config.get_config().SQL.Password

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

    def previous_run_cleanup(self):
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
            self.library.add_mount_path(mount_path=self.mount_path + "1",
                                        media_agent=self.media_agent)
            self.log.info("creating library with two mountpaths : %s and %s", self.mount_path, self.mount_path + "1")

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

        # set multiple readers for subclient
        self.subclient.data_readers = 8
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

    def delete_job(self, job_id):
        """
        deletes all jobs whose job ids are passed as argument

            Args:
                job_id        (str)     job id of job to be deleted

        returns None
        """
        self.log.info("deleting job %s ...", job_id)
        self.primary_copy.delete_job(job_id)

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

    def get_deleted_af_ids(self, sidb_store_id):
        """
        returns the count of deletedaf entries in MMDeleteaf for given store

            Args:
                sidb_store_id       (int/str)       store_id

        returns afids(set), count(int) of such entries
        """
        query = f"select archfileid from MMDeletedaf where SIDBStoreId = {sidb_store_id}"
        self.csdb.execute(query)
        af_list = self.csdb.rows
        self.log.info(f"QUERY OUTPUT : {af_list}")
        afids = {x[0] for x in af_list}
        count = len(afids)
        return afids, count

    def query_mps(self, job_id):
        """
        gets all the mountpaths associated with the given job

            Args:
                job_id      (int/str)       id of job

        returns mpids(list)
        """
        query = f"""select distinct currmountpathid
                    from mmvolume
                    where volumeid
                    in (select volumeid from archchunk where id
                    in (select archChunkId from archchunkmapping where jobid={job_id}
                    and archcopyid={self.primary_copy.copy_id})) """
        self.csdb.execute(query)
        mp_list = self.csdb.rows
        self.log.info(f"QUERY OUTPUT : {mp_list}")
        mp_ids = [mp_id[0] for mp_id in mp_list]
        if not mp_ids:
            self.log.error("invalid mountpath")
            raise Exception("invalid mountpath.. ")

        self.log.info("mountpath ids : %s", ", ".join(mp_ids))
        mp_paths = []
        for mp_id in mp_ids:
            query = f"""select mdc.Folder
                                from MMMountPathToStorageDevice mpsd, MMDeviceController mdc
                                where mpsd.DeviceId = mdc.DeviceId and mpsd.MountPathId ={mp_id}"""
            self.csdb.execute(query)
            mp_path = self.csdb.fetch_one_row()[0]
            self.log.info(f"QUERY OUTPUT : {mp_path}")
            if mp_path not in mp_paths:
                mp_paths.append(mp_path)
        self.log.info("mountpaths : %s", ", ".join(mp_paths))
        return mp_ids

    def query_af_ids(self, job_id):
        """
        gets all the archive files and their corresponding mps associated with job

            Args:
                job_id      (int/str)       id of job

        returns list of mpid, afid list
        """
        query = f"""select c.currmountpathid,a.archfileid
                    from archChunkMapping a,archChunk b, MMVolume c
                    where c.VolumeId = b.volumeId and b.id = a.archChunkId and a.jobId={job_id}
                    and a.archcopyid={self.primary_copy.copy_id}"""
        self.csdb.execute(query)
        af_list = self.csdb.rows
        self.log.info(f"QUERY OUTPUT : {af_list}")
        afids = {x[0] for x in af_list}
        if not afids:
            self.log.error("invalid afid")
            raise Exception("invalid afid.. ")
        self.log.info("af ids : %s", ", ".join(afids))
        return af_list

    def is_mp_pruning_enabled(self, mp_ids):
        """
        checks whether pruning is enabled on a list of mpids provided

            Args:
                mp_ids      (list)      list of mpids

        returns Boolean
        """
        flag = True
        query = f"""select attribute&8 from mmmountpath
                    where mountpathid in ({','.join([str(mp_id) for mp_id in mp_ids])})"""
        self.csdb.execute(query)
        mp_attributes = self.csdb.rows
        self.log.info(f"QUERY OUTPUT : {mp_attributes}")
        for i, mp_id in enumerate(mp_ids):
            mp_prune_flag = int(mp_attributes[i][0])
            if mp_prune_flag == 0:
                self.log.info("pruning disabled on mp %s...", mp_id)
                flag = False
            else:
                self.log.info("pruning enabled on mp %s...", mp_id)
        return flag

    def verify_logs(self):
        """
        checks mediamanager and cvma logs to see if change in pruning behaviour is reflected there
        """
        try:
            reg_exp = "Sending Start or Stop OnGoing Pruning request to Host"
            matched_line, matched_string = self.dedup_helper.parse_log(client=self.cs_name,
                                                                       log_file="MediaManager.log",
                                                                       regex=reg_exp,
                                                                       single_file=False)
            if not matched_line:
                self.log.error("unable to find requested log..")
                raise Exception("log line not found in mediamanager.log..")

            reg_exp = "CVMMClient API for MMStartStopOnGoingPruningCVMAResp from  completed"
            matched_line, matched_string = self.dedup_helper.parse_log(client=self.media_agent,
                                                                       log_file="CVMA.log",
                                                                       regex=reg_exp,
                                                                       single_file=False)
            if not matched_line:
                self.log.error("unable to find requested log..")
                raise Exception("log line not found in cvma.log..")

        finally:
            return True

    def check_prune_request(self, sidb_id):
        """
        checks media manager log to see if prune request has been sent

            Args:
                sidb_id     (int/str)       store id of corresponding store

        returns Boolean
        """
        reg_exp = f"PRUNE data on SIDB [{sidb_id}]"
        matched_line, matched_string = self.dedup_helper.parse_log(client=self.cs_name,
                                                                   log_file="MediaManager.log",
                                                                   regex=reg_exp,
                                                                   single_file=False)
        if matched_line:
            self.log.info("prune request was sent..")
            return True
        self.log.info("prune request was not sent..")
        return False

    def toggle_mp_pruning(self, mp_id, value=True):
        """
        sets the mp_pruning_property in csdb depending on input

            Args:
                mp_id       (int/str)       id of mountpath
                value       (Boolean)       whether to enable or disable property

        returns None
        """
        if value:
            query = f"update mmmountpath set attribute = attribute|8 where mountpathid={mp_id}"
            self.log.info("enabling mp pruning on mp : %s ", mp_id)
        else:
            query = f"update mmmountpath set attribute = attribute&~8 where mountpathid={mp_id}"
            self.log.info("disabling mp pruning on mp : %s ", mp_id)

        self.mm_helper.execute_update_query(query, self.sql_password, self.sql_username)

    def check_error_codes(self, sidb_store_id, error_code):
        """
        checks whether the specified error codes have been set for all entries of a given store in MMDeleteAF table

            Args:
                sidb_store_id       (int/str)       store id of store whose entries are to be checked
                error_code          (int/str)       error code to be checked in MMDeleteAF table

        returns None
        """
        query = f"select failureerrorcode from mmdeletedaf where sidbstoreid ={sidb_store_id}"
        self.csdb.execute(query)
        error_codes = self.csdb.rows
        self.log.info(f"QUERY OUTPUT : {error_codes}")
        for code in error_codes:
            if int(code[0]) != error_code:
                self.log.info("this is the failureerrorcode we found in mmdeletedaf: %s", int(code[0]))
                self.log.error("error code mismatch.. unexpected error code..")
                raise Exception("unexpected failure error codes found...")
        self.log.info("this is the failureerrorcode we found in mmdeletedaf: %s", int(code[0]))
        self.log.info("error codes for all corresponding mmdeleteaf entries match... expected result..")

    def run(self):
        """Run function of this test case"""
        try:
            # previous run cleanup
            self.previous_run_cleanup()

            # allocating necessary resources
            self.allocate_resources()

            # checking if dedup enabled
            if self.is_dedupe_enabled(copy=self.primary_copy):
                self.log.info("dedup enabled..!")
            else:
                self.log.error("dedup not enabled..!")
                raise Exception("dedup not enabled on storage policy {}".format(self.storage_policy_name))

            # set pruning thread time interval
            self.mm_helper.update_mmpruneprocess(db_user=self.sql_username, db_password=self.sql_password,
                                                 min_value=2, mmpruneprocess_value=2)

            # add data to subclient content
            self.new_content(dir_path=self.client_machine.join_path(self.content_path, "new1"), dir_size=1.0)

            # run 1 full
            job_id = self.run_backup("FULL")

            # query on which mp backup is on, get mp id and folder name
            mp_ids = self.query_mps(job_id)
            mp_count = len(mp_ids)
            # select one mp for disabling pruning, choose first mp in mp_list

            # query afids
            af_list = self.query_af_ids(job_id)
            total_afids_forJob = {x[1] for x in af_list}
            afids_onBadMP = {x[1] for x in af_list if x[0] == mp_ids[0]}
            afids_onGoodMP = {x[1] for x in af_list if x[0] != mp_ids[0]}

            # verify pruning enabled via csdb
            if not self.is_mp_pruning_enabled(mp_ids):
                self.log.error("pruning not enabled by default.. TC failed..")
                raise Exception("mp pruning options not default values..")

            # disable pruning *
            self.toggle_mp_pruning(mp_id=mp_ids[0], value=False)

            # verify pruning disabled via csdb
            if self.is_mp_pruning_enabled(mp_ids):
                self.log.error("pruning not disabled.. TC failed..")
                raise Exception("unable to disable mp pruning..")

            # verify pruning disabled via logs *
            self.verify_logs()
            self.log.info("toggling reflected in logs..")

            # delete job
            self.delete_job(job_id)

            # get afids from mmdeleteaf
            afids_mmdeletedaf_Initial, afid_mmdeletedaf_Initial_count = self.get_deleted_af_ids(sidb_store_id=self.sidb_id)

            if total_afids_forJob == afids_mmdeletedaf_Initial:
                self.log.info("all mmdeleteaf entires match with job.. expected result..")
            else:
                self.log.error("inccorect afids in mmdeleteaf.. unexpected..")
                raise Exception("unexpected afid entries in mmdeleteaf..")

            # run data aging
            for index in range(2):
                self.run_data_aging(time_in_secs=30)
                sleep(300)
            # verify mmdeleteaf entries same as before data aging
            afids_mmdeletedaf_afterPruning, afid_mmdeletedaf_afterPruning_count = self.get_deleted_af_ids(self.sidb_id)
            self.log.info("this is the afids that were on the MP with pruning disabled : %s ", afids_onBadMP)
            self.log.info("this is the afids that were on the MP with pruning enabled : %s ", afids_onGoodMP)
            self.log.info("this is the afids count initially in mmdeletedaf before pruning requests were sent: %s ", afid_mmdeletedaf_Initial_count)
            self.log.info("this is the afids in mmdeletedaf after pruning : %s ", afids_mmdeletedaf_afterPruning)
            self.log.info("this is the afid count in mmdeletedaf after pruning : %s ", afid_mmdeletedaf_afterPruning_count)

            if afids_onBadMP == afids_mmdeletedaf_afterPruning and (afid_mmdeletedaf_Initial_count - len(afids_onGoodMP)) == afid_mmdeletedaf_afterPruning_count:
                self.log.info("no change in mmdeleteaf entries for chosen mp after data aging.. expected result..")
            else:
                self.log.error("changes occured in mmdeleteaf for chosen mp after data aging was run..")
                raise Exception("unexpected changes in mmdeleteaf after running data aging..")

            # verify no prune request sent for store from logs *

            if mp_count == 1:
                for attempt in range(3):
                    if self.check_prune_request(sidb_id=self.sidb_id):
                        self.log.error("prune request sent for store... unexpected..")
                        raise Exception("prune request sent despite mp pruning being disabled..")
                    self.log.info("Checking again after 5 mins")
                    sleep(300)

                self.log.info("no prune request sent for this store.. expected result..")

            # run data forecast
            self.storage_policy.run_data_forecast()
            self.log.info("Data Forecast ran successfully...")

            # wait for forecasting to update error codes
            sleep(180)

            # check failure error codes set by forecast
            self.check_error_codes(sidb_store_id=self.sidb_id, error_code=65123)

            # enable pruning on mp
            self.toggle_mp_pruning(mp_id=mp_ids[0], value=True)

            # verify pruning enabled via csdb
            if not self.is_mp_pruning_enabled(mp_ids):
                self.log.error("pruning not enabled.. TC failed..")
                raise Exception("mp pruning could not be enabled..")

            # verify pruning enabled via logs
            self.verify_logs()
            self.log.info("toggling reflected in logs..")

            # run data aging
            self.run_data_aging(time_in_secs=30)

            # verify pruning request sent for store in logs
            pruning_done = False
            for attempt in range(6):
                pruning_done =  self.check_prune_request(sidb_id=self.sidb_id)
                if pruning_done:
                    self.log.info("prune request sent for store... expected result..")
                    break
                else:
                    self.log.info("Pruning request not sent yet, will check after 5 minutes")
                    sleep(300)

            if not pruning_done:
                self.log.error("no prune request sent for this store.. unexpected result..")
                raise Exception("prune request not sent despite mp pruning being enabled..")

            # verify all mmdeleteaf entries are pruned
            # repeat until deleteaf count reaches 0 : run data aging and wait
            retry = 0
            af_list, count = self.get_deleted_af_ids(self.sidb_id)

            while retry < 3 and count > 1:
                self.run_data_aging(time_in_secs=30)
                af_list, count = self.get_deleted_af_ids(self.sidb_id)
                retry += 1

            # validate that pruning occurred *
            if count != 1 and '' not in af_list:
                self.log.error("failure! pruning did not occur! mp pruning not enabled!")
            else:
                self.log.info("mp pruned successfully..")
                self.log.info("success! mp pruning is enabled... TC completed successfully..")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""

        # resetting default values for store pruning and pruning interval
        self.mm_helper.update_mmpruneprocess(db_user=self.sql_username, db_password=self.sql_password)

        self.log.info("Performing unconditional cleanup")
        # removing initialized resources
        self.log.info("********* clean up **********")
        try:
            self.deallocate_resources()
            self.log.info("clean up COMPLETED")
        except Exception as exp:
            self.log.error("clean up ERROR %s", exp)

