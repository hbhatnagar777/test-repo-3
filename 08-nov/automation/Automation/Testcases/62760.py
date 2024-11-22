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

    get_active_files_store()	-- get the active store object for given policy

    get_active_volumes() -- get the volumes to be recovered in add records phase

    get_volumes_to-recover() -- get the volumes present in archChunkToRecoverDDB

    get_failed_chunks() -- get the failed chunks present in archChunkToRecoverDDBFailedChunks

    modify_batch_count_sp() -- modify/revert stored proc that sets volume batch count for recon

    check_for_resync() -- check if resync flag is set on store

    wait_for_resync() -- wait for resync to happen on store

    ddb_subclient_load() -- fetch the DDBBackup subclient

    delete_job() -- delete the specified list of jobs

    run_data_aging() -- run data aging operation

    check_idxsidb_resync_history() -- verify that resync happens as expected by validating against resync_history table


Prerequisites: None

Input JSON:

"62760": {
        "ClientName": "<Client name>",
        "AgentName": "<IDataAgent name>",
        "MediaAgentName": "<Name of MediaAgent>",
        "storage_pool_name": "<name of the storage pool to be reused>" (optional argument),
        "dedup_path": "<path where dedup store to be created>" (optional argument)
        (Must provide LVM dedupe path for Linux MAs),
        "sqluser": "<sql_username>" (optional argument),
        "sqlpasswd": "<sql_password> (optional argument)"
}

Design steps:

1. allocate necessary resources
2. run backups to DDB store
3. run DDBBackup on store
4. run more backups to store after DDBBackup finishes and prune jobs that ran before DDBBackup
5. mark the partitions of the store for recovery, and get the list of volumes present on store
6. start a regular recon on the store
7. wait for recon to start running
8. wait for two minutes after it starts add records phase
9. kill auxcopymgr on CS and CVODS on corresponding MA
10. verify that recon goes pending
11. wait for recon to resume and complete successfully
12. once recon completes cross verify volumes present in ArchChunkToRecoverDDB table with list of volumes taken earlier
13. verify that no chunks were left out by recon in archChunkToRecoverDDBFailedChunks table
14. verify that resync runs on store
15. run backups to store to ensure that it is online
16. deallocate resources

"""
import re
from time import sleep
import pyodbc
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils import config
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
from cvpysdk.deduplication_engines import StoreFlags


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
        self.name = "DDB Recon case - Validate recon completion after killing AuxCopyMgr"\
                    " and CVODS during Add records phase"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.cs_name = None
        self.mount_path = None
        self.dedup_store_path = None
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
        self.library = None
        self.gdsp_name = None
        self.gdsp = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.store = None
        self.dedupe_engine = None
        self.primary_copy = None
        self.is_user_defined_storpool = False
        self.is_user_defined_dedup = False
        self.ddbbackup_subclient = None
        self.original_stored_proc = ""

    def setup(self):
        """Setup function of this test case"""
        if self.tcinputs.get("storage_pool_name"):
            self.is_user_defined_storpool = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True

        self.cs_name = self.commcell.commserv_client.name
        self.cs_machine = Machine(self.cs_name, self.commcell)
        self.media_agent = self.tcinputs["MediaAgentName"]
        suffix = str(self.media_agent) + "_" + str(self.client.client_name)

        self.storage_policy_name = f"{str(self.id)}_SP{suffix}"
        self.backupset_name = f"{str(self.id)}_BS{suffix}"
        self.subclient_name = f"{str(self.id)}_SC{suffix}"
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

        else:
            self.gdsp_name = "{0}_GDSP{1}".format(str(self.id), suffix)

        self.library_name = "{0}_lib{1}".format(str(self.id), suffix)

        drive_path_media_agent = self.opt_selector.get_drive(
            self.media_agent_machine)
        self.testcase_path_media_agent = "%s%s" % (drive_path_media_agent, self.id)

        self.testcase_path_client = "%s%s" % (drive_path_client, self.id)
        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")
        self.restore_path = self.client_machine.join_path(self.testcase_path_client, "restore_path")

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
        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")

        if self.media_agent_machine.check_directory_exists(self.dedup_store_path):
            self.log.info("store path directory already exists")
        else:
            self.media_agent_machine.create_directory(self.dedup_store_path)

        # create library if not provided
        if not self.is_user_defined_storpool:
            self.library = self.mm_helper.configure_disk_library(
                self.library_name, self.media_agent, self.mount_path)

        # create gdsp if not provided
        if not self.is_user_defined_storpool:
            self.gdsp = self.dedup_helper.configure_global_dedupe_storage_policy(
                global_storage_policy_name=self.gdsp_name,
                library_name=self.library_name,
                media_agent_name=self.media_agent,
                ddb_path=self.dedup_store_path,
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
        self.subclient = self.mm_helper.configure_subclient(self.backupset_name, self.subclient_name,
                                                            self.storage_policy_name, self.content_path,
                                                            self.agent)

        # create primary copy object for storage policy
        self.primary_copy = self.storage_policy.get_copy(copy_name="primary")

        # creating content
        self.new_content(dir_path=self.content_path, dir_size=1)

        # set enc on primary copy BlowFish 128
        self.log.info("setting encryption on primary")
        self.gdsp.get_copy("Primary_Global").set_encryption_properties(re_encryption=True,
                                                                       encryption_type="BlowFish",
                                                                       encryption_length=128)

        # set multiple readers for subclient to increase volume count
        self.subclient.data_readers = 10
        self.subclient.allow_multiple_readers = True

    def run_backup(self, subclient, job_type, start_new_media=False):
        """
        run a backup job for the subclient specified in Testcase

            Args:
                subclient       (instance)  instance of subclient object
                job_type        (str)       backup job type(FULL, synthetic_full, incremental, etc.)
                start_new_media (boolean)   flag to enable/disable start new media option for backup job

        returns job id(int)
        """
        self.log.info("starting %s backup job...", job_type)
        job = subclient.backup(backup_level=job_type,
                                    advanced_options={'mediaOpt': {'startNewMedia': start_new_media}})
        self.log.info("starting %s backup job %s...", job_type, job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run backup job with error: {0}".format(job.delay_reason)
            )
        self.log.info("backup job: %s completed successfully", job.job_id)

        return job.job_id

    def get_active_files_store(self):
        """returns active store object for files iDA"""
        self.commcell.deduplication_engines.refresh()
        engine = self.commcell.deduplication_engines.get(self.gdsp_name, 'primary_global')
        if engine:
            return engine.get(engine.all_stores[0][0])
        return 0

    def get_active_volumes(self, store_id):
        """
        returns list of volumes for given SIDBStoreID

        Args:
            store_id        str     SIDBStoreID for store being specified

        Returns List object containing volume ids
        """
        self.log.info("fetching active volumes that will be recovered by add records phase..")
        query = f"""select volumeId from MMVolume 
                    where SIDBStoreId = {store_id} and 
                    lastBackupTime <> 0 and 
                    physicalBytesMB <> 0 and
                    CreationTime > (select LastSnapTime from idxSIDBSubStore where SIDBStoreID = {store_id})"""
        self.csdb.execute(query)
        return self.csdb.fetch_all_rows()

    def get_volumes_to_recover(self, job_id):
        """
        returns list of volumes for given recon job id

        Args:
            job_id        str     job id of recon job being queried

        Returns List object containing volume ids
        """
        self.log.info("fetching volumes from archChunkToRecoverDDB..")
        query = f"""select volumeid from archChunkToRecoverDDB where adminjobid = {job_id}"""
        self.csdb.execute(query)
        return self.csdb.fetch_all_rows()

    def get_failed_chunks(self, job_id):
        """
        returns Boolean depending on if any failed chunks are present

        Args:
            job_id        str     job id of recon job being queried

        Returns Boolean
            True - if there are no volumes present
            False - if there are volumes present
        """
        self.log.info("checking if there are failed chunks for recon in archChunkToRecoverDDBFailedChunks..")
        query = f"""select volumeid from archChunkToRecoverDDBFailedChunks where adminjobid = {job_id}"""
        self.csdb.execute(query)
        value = self.csdb.fetch_all_rows()[0][0]
        if value == '':
            return False
        else:
            return True

    def modify_batchcount_sp(self, set_value=True):
        """
        Modify stored procedure ArchChunkToRecoverDDBInsert

        Args:
            set_value    (Boolean)   --  If True, Modify Stored Procedure, else revert to original code
        """
        new_sp = ""
        sql_user = self.tcinputs.get('sqluser')
        sql_passwd = self.tcinputs.get('sqlpasswd')
        if not sql_user:
            sql_user = config.get_config().SQL.Username
        if not sql_passwd:
            sql_passwd = config.get_config().SQL.Password
        server_str = f"{self.commcell.commserv_client.client_name}"
        if self.commcell.commserv_client.os_info.lower().count('windows'):
            server_str = f"{server_str}\\commvault"
        con = pyodbc.connect('DRIVER={SQL Server}; ' + f'Server={server_str}; database=CommServ; '
                                                       f'UID={sql_user}; PWD={sql_passwd}')
        change_already_exist = False
        if not set_value:
            self.log.info("Reverting the stored procedure to original code")
            new_sp = self.original_stored_proc
            if new_sp.count('DECLARE @maxVolumes INT = 5'):
                self.log.warning("Original Stored Proc contains Code Added by TC. Removing the changed code")
                new_sp = new_sp.replace('DECLARE @maxVolumes INT = 5', 'DECLARE @maxVolumes INT = 1000')
                new_sp = re.sub("create procedure", "alter procedure", new_sp, flags=re.IGNORECASE)
                self.mm_helper.execute_update_query(new_sp, db_password=sql_passwd, db_user=sql_user)

        else:
            output = con.execute('exec sp_helptext ?', ('ArchChunkToRecoverDDBInsert',)).fetchall()
            con.close()
            outputlines = """"""
            for line in output:
                if line[0].count('DECLARE @maxVolumes INT = 5'):
                    change_already_exist = True
                outputlines = outputlines + (line[0])
            self.original_stored_proc = outputlines
            self.log.info("Fetched original stored procedure")
            self.log.info("%s\\n%s\\n%s", '*' * 80, self.original_stored_proc, '*' * 80)
            if not change_already_exist:
                self.log.info("Locating the line after which error code will be injected")
                outputlist = outputlines.split(
                    'DECLARE @maxVolumes INT = 1000')
                new_sp = f"""{outputlist[0]} """ + """DECLARE @maxVolumes INT = 5""" + f"""{outputlist[1]}"""
            else:
                self.log.warning("altered code already exists in Stored Procedure ArchFileValidate")
        if not change_already_exist:
            self.log.info("Modifying Stored Procedure ArchChunkToRecoverDDBInsert")
            new_sp = re.sub("create procedure", "alter procedure", new_sp, flags=re.IGNORECASE)
            self.mm_helper.execute_update_query(new_sp, db_password=sql_passwd, db_user=sql_user)
        else:
            self.log.warning("Stored Procedure ArchChunkToRecoverDDBInsert already has changed code. "
                             "Hence not altering Stored Procedure")

    def check_for_resync(self):
        """
        checks if resync in progress flag has been set on store or not

        Returns Boolean
        """
        store_id = self.store.store_id
        query = f"""select flags&{StoreFlags.IDX_SIDBSTORE_FLAGS_DDB_NEEDS_AUTO_RESYNC.value} 
                    from IdxSIDBStore where sidbstoreid in ({store_id})"""
        self.log.info("QUERY : %s", query)
        self.csdb.execute(query)
        resync_flag = int(self.csdb.fetch_one_row()[0])
        if resync_flag == StoreFlags.IDX_SIDBSTORE_FLAGS_DDB_NEEDS_AUTO_RESYNC.value:
            self.log.info("resync flag has been set on store %s", store_id)
            return True
        else:
            self.log.error("resync flag has not been set on store %s", store_id)
            return False

    def update_mmconfig_param(self, param_name, nmin, value):
        """
        Update MM Config parameter value.

        Args:
            param_name  (str)   -   name of the MMConfig paramater
            nmin        (int)   -   minimum value of the parameter
            value       (int)   -   value to be set
        """

        query = f"update mmconfigs set nmin={nmin}, value={value} where name='{param_name}'"
        self._log.info("QUERY: %s", query)
        self.mm_helper.execute_update_query(query, self.sql_password, self.sql_username)

    def ddb_subclient_load(self):
        """
        retrieves the ddbbackup subclient object for corresponding MA in use

        Raises:
            Exceptions
                if DDBBackup subclient does not exist.

        """
        # check if DDBBackup subclient exists, if it doesn't fail the testcase
        default_backup_set = self.commcell.clients.get(
            self.tcinputs.get("MediaAgentName")).agents.get(
                "File System").backupsets.get(
                    "defaultBackupSet")

        if default_backup_set.subclients.has_subclient("DDBBackup"):
            self.log.info("DDBBackup subclient exists")
            self.log.info(
                "Storage policy associated with the DDBBackup subclient is %s",
                default_backup_set.subclients.get("DDBBackup").storage_policy)
            self.ddbbackup_subclient = default_backup_set.subclients.get(
                "DDBBackup")
        else:
            raise Exception("DDBBackup Subclient does not exist:FAILED")

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
        while data_aging_jobs_running != '0' and retry < 10:
            sleep(60)
            retry += 1
            self.csdb.execute(query)
            data_aging_jobs_running = self.csdb.fetch_one_row()[0]
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

    def wait_for_resync(self):
        """
        wait for resync to start and populate IdxSIDBResyncHistory table
        """
        store_id = self.store.store_id
        self.log.info("Modifying MM Admin Thread Interval to 5 minutes")
        self.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5, 5)

        self.log.info("Now wait until Resync takes place or maximum 15 minutes")
        resync_done = False
        for itr in range(1, 16):
            query = f"select count(1) from IdxSIDBResyncHistory where sidbstoreid in ({store_id}) " \
                    f"and Resyncstatus != -1"
            self.log.info("QUERY : %s", query)
            self.csdb.execute(query)
            resync_history = self.csdb.fetch_one_row()
            if int(resync_history[0]) == 1:
                self.log.info("IdxSIDBResyncHistory table is populated with at least one row for store.")
                self.log.info(resync_history)
                resync_done = True
                self.log.info("Moving MM Admin Thread Interval back to 15 minutes so that Reconstruction "
                              "does not start immediately")
                self.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5, 15)
                break
            else:
                self.log.info("Checking IdxSIDBResyncHistory table after 1 minute. Attempt Number - [%s]", itr)
                sleep(60)

        if not resync_done:
            self.log.error("Resync did not happen even after 15 minutes. Failing this case.")
            raise Exception("Resync did not happen even after 15 minutes. Failing this case.")
        else:
            self.log.info("IdxSIDBResyncHistory table has valid rows for target SIDB Engine. Sleeping for 1 minute"
                          "before resumption")
            sleep(60)

    def verify_idxsidb_resync_history(self, engine_id, verification_list):
        """
        Verify that IdxSIDBResyncHistory has a row for DDB store with correct reason

        Args:
            engine_id           (int)   --  SIDB Engine Id
            verification_list  (list)   --  List of values in following columns for verifying resync history
                                            [Status, ResyncFlags, MaintenanceReason]

        """
        failure = False
        query = f"select top 1 * from IdxSIDBResyncHistory where sidbstoreid={engine_id} order by addedtime desc"
        self.log.info("QUERY : %s", query)
        self.csdb.execute(query)
        resync_row = self.csdb.fetch_one_row()
        self.log.info("RESYNC ROW ==> %s", resync_row)
        # Example
        # SIDBStoreId	CommcellId	MaintenanceTime	ResyncFlags	AttemptNo	MaintenanceReason	MaintenanceReasonDesc
        # 1	2	1570680091	5	1	11	Controlled archive file validation is in progress.
        if resync_row[0] == '':
            self.log.error("No rows returned by the query .. Returning failure ..")
            return not failure

        if int(resync_row[8]) == verification_list[0]:
            self.log.info("Successfully verified Resync Status as - [%s]", verification_list[0])
        else:
            self.log.error("Failed to verify Resync Status : Expected - [%s] & Actual - [%s]", verification_list[0],
                           resync_row[8])
            failure = True

        if int(resync_row[3]) == verification_list[1]:
            self.log.info("Successfully verified ResyncFlags as - [%s]", verification_list[1])
        else:
            self.log.error("Failed to verify ResyncFlags : Expected - [%s] & Actual - [%s]", verification_list[1],
                           resync_row[3])
            failure = True

        if int(resync_row[5]) == verification_list[2]:
            self.log.info("Successfully verified MaintenanceReason as - [%s]", verification_list[2])
        else:
            self.log.error("Failed to verify MaintenanceReason : Expected - [%s] & Actual - [%s]",
                           verification_list[2], resync_row[5])
            failure = True

        return not failure

    def run(self):
        """Run function of this test case"""
        try:
            # previous run cleanup
            self.previous_run_clean_up()
            # allocating necessary resources
            self.allocate_resources()

            # add data to subclient content
            self.new_content(dir_path=self.client_machine.join_path(self.content_path, "new", str(1)),
                             dir_size=2)
            # run full backups
            # mark media as full or start new media for few jobs
            job1 = self.run_backup(job_type="Full", subclient=self.subclient, start_new_media=True)

            # getting engine details
            self.dedupe_engine = self.commcell.deduplication_engines.get(self.gdsp_name, "Primary_Global")
            self.store = self.dedupe_engine.get(self.dedupe_engine.all_stores[0][0])
            self.substore = self.store.get(self.store.all_substores[0][0])

            # add data to subclient content
            self.new_content(dir_path=self.client_machine.join_path(self.content_path, "new", str(2)),
                             dir_size=2)
            # run full backups
            # mark media as full or start new media for few jobs
            job2 = self.run_backup(job_type="Full", subclient=self.subclient, start_new_media=True)

            # run DDB backup
            self.ddb_subclient_load()
            ddbbackup_job = self.run_backup(job_type="Full", subclient=self.ddbbackup_subclient)

            # run backups to store
            for index in range(3, 6):
                # add data to subclient content
                self.new_content(dir_path=self.client_machine.join_path(self.content_path, "new", str(index)),
                                 dir_size=2)
                # run full backups
                # mark media as full or start new media for few jobs
                job = self.run_backup(job_type="Full", subclient=self.subclient, start_new_media=True)

            # set batch count for volumes to smaller value using stored proc
            self.modify_batchcount_sp(set_value=True)

            # delete first set of jobs
            self.delete_job([job1, job2])

            # run data aging
            self.run_data_aging(time_in_secs=120)

            # get all volumes for given store
            present_volumes = self.get_active_volumes(self.store.store_id)
            self.log.info(
                "active volumes that were written post DDBBackup and are to appended during Add records phase: %s",
                str(present_volumes))

            # run full recon
            self.media_agent_obj = self.commcell.clients.get(self.media_agent)
            self.dedup_helper.wait_till_sidb_down(str(self.store.store_id), self.media_agent_obj)
            self.substore.mark_for_recovery()
            recon_job = self.store.recover_deduplication_database(full_reconstruction=False, scalable_resources=True)

            # wait till recon reaches add records phase
            for i in range(120):
                if recon_job.phase == "Add Records":
                    self.log.info("add records phase has started..")
                    break
                elif i == 119:
                    self.log.error("recon add records phase did not start even after 20 minutes..")
                    raise Exception("timed out waiting for add records phase..")
                else:
                    self.log.info("waiting for add records phase to start.. sleeping for 10 seconds..")
                    sleep(10)

            # take down auxcopymgr process on MA
            sleep(60)
            self.log.info("killing auxcopymgr/CVODS process on CS to stall recon..")
            self.cs_machine.kill_process(process_name="AuxCopyMgr")
            self.media_agent_machine.kill_process(process_name="CVODS")

            # verify that recon goes pending/waiting
            for i in range(60):
                if recon_job.status.lower() == 'pending':
                    self.log.info("recon job has been stalled..")
                    break
                else:
                    self.log.info("waiting for recon job to go pending..")
                self.log.info("sleeping for 10 secs while waiting for job to go pending..")
                sleep(10)
                if i == 59:
                    self.log.error("job has not yet gone pending..")
                    raise Exception("Recon job did not go pending even after 10 mins..")

            # wait for recon job to start running again reduce retry interval
            sleep(120)
            recon_job.resume()
            self.log.info("resuming recon job..")

            for i in range(30):
                if recon_job.status.lower() == 'running':
                    self.log.info("recon job has resumed..")
                    break
                elif i == 29:
                    self.log.error("recon job has not yet resumed even after 10 minutes..")
                    raise Exception("timed out waiting for add recon to resume..")
                else:
                    self.log.info("waiting for recon to resume.. sleeping for 20 seconds..")
                    sleep(20)

            # wait for recon job to complete
            if not recon_job.wait_for_completion():
                raise Exception(
                    f"Failed to run recon with error: {recon_job.delay_reason}"
                )
            self.log.info("recon job: %s completed successfully", recon_job.job_id)

            # get all volumes from archChunkToRecoverDDB table
            volumes_to_recover = self.get_volumes_to_recover(recon_job.job_id)
            self.log.info("volumes that were recovered by recon job as per entries in archChunkToRecoverDDB table: %s",
                          str(volumes_to_recover))

            # verify that all volumes were picked
            if present_volumes == volumes_to_recover:
                self.log.info("all active volumes picked for full recon..")
            else:
                self.log.error("all active volumes were not picked by recon..")
                raise Exception("recon job did not pick all active volumes..")

            # verify that there are no failed chunks for recon
            if self.get_failed_chunks(recon_job.job_id):
                self.log.error("failed chunks present for recon job..")
                raise Exception("recon was not 100% successfull.. failed chunks present..")
            else:
                self.log.info("no failed chunks present.. recon was successful..")

            # wait for DDB resync
            for i in range(10):
                if self.check_for_resync():
                    break
                elif i == 9:
                    self.log.error("resync flag was not set on store even after 5 minutes..")
                    raise Exception("store was not marked for resync..")
                else:
                    self.log.info("wait 30 more secs for resync flag to be set..")
                    sleep(30)
            self.log.info("store has been marked for resync..")
            self.log.info("we will now wait for resync to take place..")
            self.wait_for_resync()
            if self.verify_idxsidb_resync_history(self.store.store_id, [0, 5, 13]):
                self.log.info("Resync verification success for SIDB [%s]", self.store.store_id)
            else:
                self.log.error("Resync verification failed for SIDB [%s]", self.store.store_id)
                self.result_string += f"IdxSIDBResyncHistory Verification Failed : SIDB : " \
                                      f"[{self.store.store_id}]\n"

            # run backup to verify that store is up and running
            self.new_content(dir_path=self.client_machine.join_path(self.content_path, "new123"),
                             dir_size=5)
            # run full backups
            job = self.run_backup(job_type="Full", subclient=self.subclient, start_new_media=True)

            self.log.info("All Validations Completed.. Testcase executed successfully..")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.original_stored_proc != "":
            self.modify_batchcount_sp(set_value=False)
        # removing initialized resources
        try:
            self.deallocate_resources()
        except BaseException:
            self.log.warning("Cleanup Failed, please check setup ..")
