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
    __init__()                      --  Initialize TestCase class

    setup()                         --  Setup function of this test case

    run()                           --  Run function of this test case

    tear_down()                     --  Tear down function of this test case

    verify_resync_logging()         --  Verify Resync Logging for each of the SIDB store

    verify_idxsidb_resync_history() --	 Verify that IdxSIDBResyncHistory has a row for DDB store with correct reason

    prepare_and_wait_for_resync	()  --  Modify the SIDB Creation Time to 45 days older than its present creation time.

    run_backups()	--  Run backups on all subclients and maintain list of job IDs for each subclient

    configure_tc_environment()  -- Configure testcase environment - library (if required), storage policy, backupset,
                                    subclient

    get_ddb_af_details()        --  Fetch sidb2 listaf command output

    compare_af_details()        --  Compare AF details captured before and after the Resync attempts

    modify_archfilevalidate_sp()    -- Modify stored procedure ArchFileValidate

    cleanup()                   --    Clean up the entities created by this test case

    Steps:
	1. Configure a Dedup Storage Pool with 2 DDB Mas with 1 partition each. Set MM Admin Thread time to 5 mins.
    2. Run 10 jobs on this storage pool with 10 Afs each so that 100 Afs are created. Run first few jobs with new data
        and later jobs with same data.
    3. Run SIDB2 -listaf command and note down number of AFs.
    3. Modify Resync Batch Size on DDBMA1 by setting following regkey - MediaAgent\\SIDBAfDiffBatchSize to 10
    4. Modify ArchFileValidate stored proc to contain following query in stored proc which will randomly return
        failure due to divide by 0 error
        --declare @number_62499 decimal(10,5)
        --set @number_62499 = RAND()
        --if @number_62499 < 0.4 (select 100/0)
    5. Move DDB CreatedTime back by 30 days by running following query
        update idxsidbstore set CreatedTime = CreatedTime - (30*86400) where sidbstoreid=<sidbstoreid>
    6. Wait for MM thread to mark store for resync by periodically checking outcome of following query
        select flags&33554432 as resyn from idxsidbstore where sidbstoreid=<sidbstoreid>
    7. For 3 iterations, after every 6 minutes, check that IdxSIDBResyncHistory table is adding a new row after
        failure of Resync
    8. Check SIDBEngine Logs on DDB MA for presence of following lines
        DoAfDiff 5037 Mismatched sizes - request Afs [500] response Afs [0]. Aborting.
         CVMMIdxSIDBStoreInfo::getAFStatus2() - Unable to get AFInfoList for SIDBStoreId [22138] from MM. RetCode [-1]
        8044  117c  12/11 17:24:29 ### 22138-1-22486-1 DoAfDiff         5024  Failed to get AF Status. iRet [-1]
        8044  1afc  12/11 17:24:59 ### 22138-1-22486-1 Resync           4778  DDB and CS Af diff failed. iRet [53006]
        8044  1afc  12/11 17:24:59 ### 22138-1-22486-1 CResyncHandler::Process    44  Failed to resync. iRet [53006]

    9. Modify stored proc to its normal code and let resync complete. Verify it by following
        IdxSIDBResyncHistory table row.
    10. Again run SIDB2 -listaf command and note down number of AFs
    11. Compare if AFs are same before and after Resync attempts

    Expected Input :
    		"62499":{
    		        "ClientName": "client name",
					"AgentName": "File System",
					"MediaAgentName": "ma name"}

"""
import time, re
import pyodbc
from cvpysdk import deduplication_engines
from AutomationUtils import config
from AutomationUtils.options_selector import OptionsSelector, constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "DDB Resync - Resync should not prune Afs if batch size received is different from CS side"
        self.tcinputs = {
            "MediaAgentName": None
        }

        self.ma_name = None
        self.dedup_path = None
        self.client_machine_obj = None
        self.client_system_drive = None
        self.ma_machine_obj = None
        self.ma_library_drive = None
        self.library_name = None
        self.mountpath =None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.content_path = None
        self.restore_path = None
        self.bkpset_obj = None
        self.mahelper_obj = None
        self.dedup_helper_obj = None
        self.storage_pool_name = None
        self.optionobj = None
        self.sidb_store = None
        self.subclient_list = []
        self.storage_pool_list = []
        self.storage_policy_list = []
        self.content_path_list = []
        self.backup_jobs_dict = {}
        self.original_stored_proc = ""
        self.ma_client = None
        self.af_details_after_resync = ""
        self.af_details_before_resync = ""

    def setup(self):
        """Setup function of this test case"""

        self.optionobj = OptionsSelector(self.commcell)
        self.ma_name = self.tcinputs.get('MediaAgentName')
        self.dedup_path = self.tcinputs.get('dedup_path')

        self.client_machine_obj = Machine(self.client)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine_obj, 30)
        self.ma_machine_obj = Machine(self.ma_name, self.commcell)
        self.ma_library_drive = self.optionobj.get_drive(self.ma_machine_obj, 30)
        self.ma_client = self.commcell.clients.get(self.ma_name)
        self.library_name = f"LIB_TC_{self.id}_{self.ma_name}"
        self.mountpath = self.ma_machine_obj.join_path(self.ma_library_drive, self.id, "MP")

        self.storage_policy_name = f"SP_TC_{self.id}_{self.ma_name}"

        if not self.dedup_path and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")

        if not self.dedup_path:
            self.dedup_path = self.ma_machine_obj.join_path(self.ma_library_drive, f"{self.id}", "DDB")
        else:
            self.dedup_path = self.ma_machine_obj.join_path(self.dedup_path, f"{self.id}", "DDB")

        self.backupset_name = f"BkpSet_TC_{self.id}"
        self.subclient_name = f"Subc_TC_{self.id}"
        self.content_path = self.client_machine_obj.join_path(self.client_system_drive, self.id, "Content")
        self.restore_path = self.client_machine_obj.join_path(self.client_system_drive, self.id, "Restore")
        self.mahelper_obj = MMHelper(self)
        self.dedup_helper_obj = DedupeHelper(self)


    def configure_tc_environment(self):
        """
        Configure testcase environment - library (if required), storage policy, backupset, subclient
        """
        if self.client_machine_obj.check_directory_exists(self.content_path):
            self.log.info("Deleting already existing content directory [%s]", self.content_path)
            self.client_machine_obj.remove_directory(self.content_path)
        self.client_machine_obj.create_directory(self.content_path)
        if not self.ma_machine_obj.check_directory_exists(self.mountpath):
            self.log.info("Creating mountpath directory [%s]", self.mountpath)
            self.ma_machine_obj.create_directory(self.mountpath)
        self.log.info("Creating Library [%s]", self.library_name)
        if self.commcell.disk_libraries.has_library(self.library_name):
            self.log.info("Library [%s] already exists. Reusing the Library.", self.library_name)
        else:
            self.mahelper_obj.configure_disk_library(self.library_name, self.ma_name, self.mountpath)
            self.log.info("Library [%s] created successfully.", self.library_name)

        self.log.info("Configuring Backupset - [%s]", self.backupset_name)
        self.bkpset_obj = self.mahelper_obj.configure_backupset(self.backupset_name)
        self.log.info("Successfully configured Backupset - [%s]", self.backupset_name)

        self.log.info("Configuring Storage Pool for this test.")
        storage_pool_name = f"{self.storage_policy_name}_POOL"
        dedup_path = self.ma_machine_obj.join_path(self.dedup_path, storage_pool_name, "1")
        dedup_path_2 = self.ma_machine_obj.join_path(self.dedup_path, storage_pool_name, "2")
        if not self.ma_machine_obj.check_directory_exists(dedup_path):
            self.log.info("Creating dedup directory [%s]", dedup_path)
            self.ma_machine_obj.create_directory(dedup_path)

        self.log.info("Creating Dedup Storage Pool [%s]", storage_pool_name)
        if not self.commcell.storage_policies.has_policy(storage_pool_name):
            self.storage_pool_list.append(
                self.dedup_helper_obj.configure_global_dedupe_storage_policy(
                    global_storage_policy_name=storage_pool_name,
                    library_name=self.library_name,
                    media_agent_name=self.ma_name,
                    ddb_path=dedup_path,
                    ddb_media_agent=self.ma_name))
            self.log.info("Successfully created Dedup Storage Pool [%s]", storage_pool_name)
            self.log.info("Adding Partition to storage pool [%s]", storage_pool_name)
            if not self.ma_machine_obj.check_directory_exists(dedup_path_2):
                self.log.info("Creating dedup directory for 2nd partition [%s]", dedup_path_2)
                self.ma_machine_obj.create_directory(dedup_path_2)
        else:
            self.log.info("Dedup Storage Pool already exists - [%s]", storage_pool_name)
            self.storage_pool_list.append(self.commcell.storage_policies.get(storage_pool_name))

        copy_id = self.storage_pool_list[0].get_copy('Primary_Global').copy_id

        # SIDB Engine Details
        dedup_engines_obj = deduplication_engines.DeduplicationEngines(self.commcell)
        if dedup_engines_obj.has_engine(storage_pool_name, 'Primary_Global'):
            dedup_engine_obj = dedup_engines_obj.get(storage_pool_name, 'Primary_Global')
            dedup_stores_list = dedup_engine_obj.all_stores
            self.sidb_store = dedup_engine_obj.get(dedup_stores_list[0][0])

        # adding partition 2
        self.storage_pool_list[0].add_ddb_partition(copy_id, str(self.sidb_store.store_id),
                                                          dedup_path_2, self.ma_name)
        for itr in range(1,4):
            storage_policy_name = f"{self.storage_policy_name}_{itr}"
            #Creating Dedpendent SP
            if self.commcell.storage_policies.has_policy(storage_policy_name):
                self.log.info("Deleting Dependent SP - [%s]", storage_policy_name)
                self.commcell.storage_policies.delete(storage_policy_name)
            self.log.info("Creating Dependent SP - [%s]", storage_policy_name)
            self.storage_policy_list.append(self.commcell.storage_policies.add(
                                                storage_policy_name=storage_policy_name,
                                                library=self.library_name,
                                                media_agent=self.ma_name,
                                                global_policy_name=storage_pool_name,
                                                dedup_media_agent="",
                                                dedup_path=""))
            sp_copy = self.storage_policy_list[itr-1].get_copy('Primary')
            self.log.info("setting copy retention: 1 day, 0 cycle")
            sp_copy.copy_retention = (1, 0, 1)

            self.log.info("Creating subclient for using SIDB Store ID - [%s]", self.sidb_store.store_id)
            subclient_name = f"{self.subclient_name}_{itr}"
            content_path = self.client_machine_obj.join_path(self.content_path, subclient_name)
            if self.client_machine_obj.check_directory_exists(content_path):
                self.log.info("Removing existing content directory [%s] from client", content_path)
                self.client_machine_obj.remove_directory(content_path)

            self.log.info("Creating content directory [%s] for subclient - [%s]", content_path, subclient_name)
            self.client_machine_obj.create_directory(content_path)
            self.content_path_list.append(content_path)
            self.subclient_list.append(self.mahelper_obj.configure_subclient(self.backupset_name, subclient_name,
                                                                       storage_policy_name, content_path))
            self.log.info("Setting number of streams to 4")
            self.subclient_list[itr-1].data_readers = 4
            self.subclient_list[itr-1].allow_multiple_readers = True
            self.backup_jobs_dict[subclient_name]=[]

    def run_backups(self, num_backups = 5):
        """
        Run backups on all subclients and maintain list of job IDs for each subclient

        Args:
            num_backups (int)       --  How many backup iterations to run on all subclients
        """
        for bkps in range(1, num_backups+1):
            self.log.info("Running backup iteration - [%s]", bkps)
            for itr in range(0, len(self.subclient_list)):
                if bkps == 1:
                    self.log.info("Generating content for subclient [%s] at [%s]", self.subclient_list[itr].name,
                                  self.content_path_list[itr])
                    self.mahelper_obj.create_uncompressable_data(self.tcinputs['ClientName'],
                                                                 self.content_path_list[itr], 0.5)
                self.log.info("Starting backup on subclient %s", self.subclient_list[itr].name)
                job = self.subclient_list[itr].backup("Full")
                self.backup_jobs_dict[self.subclient_list[itr].name].append(job)
                if not job.wait_for_completion():
                    raise Exception(f"Failed to run backup job with error: {job.delay_reason}")
                self.log.info("Backup job [%s] on subclient [%s] completed", job.job_id, self.subclient_list[itr].name)


    def cleanup(self):
        """
        Clean up the entities created by this test case
        """
        try:
            self.log.info("Cleaning up FileSystem subclients by deleting the backupset [%s]", self.backupset_name)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.log.info("Deleting backupset %s", self.backupset_name)
                self.agent.backupsets.delete(self.backupset_name)

            self.log.info("Cleaning up content directories of these subclients")
            for itr in range(1, 4):
                subclient_name = f"{self.subclient_name}_{itr}"
                content_path = self.client_machine_obj.join_path(self.content_path, subclient_name)
                if self.client_machine_obj.check_directory_exists(content_path):
                    self.log.info("Deleting already existing content directory [%s]", content_path)
                    self.client_machine_obj.remove_directory(content_path)
            self.log.info("Cleaning up Restore Path")
            if self.client_machine_obj.check_directory_exists(self.restore_path):
                self.log.info("Deleting already existing restore directory [%s]", self.restore_path)
                self.client_machine_obj.remove_directory(self.restore_path)

            self.log.info("Cleaning up dependent storage policies")
            for itr in range(1, 4):
                if self.commcell.storage_policies.has_policy(f"{self.storage_policy_name}_{itr}"):
                    self.log.info("Deleting Dependent SP - [%s]", f"{self.storage_policy_name}_{itr}")
                    self.commcell.storage_policies.delete(f"{self.storage_policy_name}_{itr}")

            self.log.info("Cleaning up storage pools")
            if self.commcell.storage_policies.has_policy(f"{self.storage_policy_name}_POOL"):
                self.log.info("Deleting Storage Pool - [%s]", f"{self.storage_policy_name}_POOL")
                self.commcell.storage_policies.delete(f"{self.storage_policy_name}_POOL")

        except Exception as exp:
            self.log.warning("**********Cleanup before test run failed. Still continuing with test run. "
                             "Perform manual cleanup and re-run if any failure is observed."
                             " ERROR : %s**********", exp)



    def prepare_and_wait_for_resync(self):
        """
        Modify the SIDB Creation Time to 45 days older than its present creation time. Also delete IdxSIDBResyncHistory
        rows for these SIDBStores if there exist any.

        """
        is_successful = True
        sidb_stores = self.sidb_store.store_id

        self.log.info("Changing Resync Batch size to 10 on MA - [%s]", self.ma_name)
        self.ma_client.add_additional_setting("MediaAgent", "SIDBAfDiffBatchSize", 'INTEGER', '10')

        self.log.info("Changing Creation Time of SIDB Store to 45 days older than original creation time.")
        query = f"update IdxSIDBStore set CreatedTime = CreatedTime - {86400*45} where sidbstoreid in ({sidb_stores})"
        self.log.info("QUERY => %s", query)
        self.optionobj.update_commserve_db(query)

        self.log.info("Deleting IdxSIDBResyncHistory table rows for these SIDB stores if any")
        query = f"Delete from IdxSIDBResyncHistory where sidbstoreid in ({sidb_stores})"
        self.log.info("QUERY => %s", query)
        self.optionobj.update_commserve_db(query)

        self.log.info("Modifying MM Admin Thread Interval to 5 minutes")
        self.mahelper_obj.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5, 5)

        self.log.info("Now wait until Resync takes place for at least 1 store or maximum 15 minutes")

        resync_count = 0
        for cycle in range(1, 4):
            resync_done = False
            self.log.info("Resync Cycle - [%s]", cycle)

            for itr in range(1,15):
                query = f"select count(1) from IdxSIDBResyncHistory where sidbstoreid in ({sidb_stores}) " \
                        f"and ResyncStatus != -1"
                self.log.info("QUERY : %s", query)
                self.csdb.execute(query)
                resync_history = self.csdb.fetch_one_row()
                self.log.info(resync_history)
                #If Resync Status = -1, it indicates that DDB has not compelted resync yet. We should wait until
                #Resync is complete so that Resync Row has all the correct information for future validations
                if int(resync_history[0]) == cycle:
                    self.log.info("IdxSIDBResyncHistory table is populated with required number of rows - [%s]"
                                  " for this store.", cycle)
                    self.log.info(resync_history)
                    resync_done = True
                    resync_count += 1
                    break
                else:
                    self.log.info("Checking IdxSIDBResyncHistory table after 1 minute. Attempt Number - [%s]", itr)
                    time.sleep(60)

            if not resync_done:
                self.log.error("Resync did not happen even after 15 minutes. Will check in next cycle.")
                raise Exception("Resync did not happen in given timeout for cycle - [%s]", cycle)
            else:
                self.log.info("IdxSIDBResyncHistory table has valid rows for target SIDB Engines. "
                              "Sleeping for 1 minute before verifying IdxSIDBUSageHistoryTable")
                time.sleep(60)
                if self.verify_idxsidb_resync_history(sidb_stores, [53006, 5, 11, 0, cycle]):
                    self.log.info("Successfully verified Resync failure due to mismatched BatchSize")
                else:
                    self.log.info("Failed to verify Resync Failure due to mismatched BatchSize")
                    self.log.info("Found incorrect entries in IdxSIDBResyncHistory table row.")
                    self.result_string += f"Failed to verify Resync Failure in attempt - [{cycle}]"
                    is_successful = False
                    break
        return is_successful


    def verify_idxsidb_resync_history(self, engine_id, verification_list):
        """
        Verify that IdxSIDBResyncHistory has a row for DDB store with correct reason

        Args:
            engine_id           (int)   --  SIDB Engine Id
            verification_list  (list)   --  List of values in following columns for verifying resync history
                                            [Status, ResyncFlags, MaintenanceReason, NumResyncedAFIDs, AttemptNo]

        """
        failure = False
        query = f"select top 1 * from IdxSIDBResyncHistory where sidbstoreid={engine_id} order by addedtime desc"
        self.log.info("QUERY : %s", query)
        self.csdb.execute(query)
        resync_row = self.csdb.fetch_one_row()
        self.log.info("RESYNC ROW ==> %s", resync_row)
        #Example
        #SIDBStoreId	CommcellId	MaintenanceTime	ResyncFlags	AttemptNo	MaintenanceReason	MaintenanceReasonDesc
        #1	2	1570680091	5	1	11	Controlled archive file validation is in progress.
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

        if int(resync_row[9]) == verification_list[3]:
            self.log.info("Successfully verified NumResyncedAFIDs as - %s", verification_list[3])
        else:
            self.log.error("Failed to verify NumResyncedAFIDs : Expected - [%s] & Actual - [%s]", verification_list[3],
                           resync_row[9])
            failure = True

        if int(resync_row[4]) == verification_list[4]:
            self.log.info("Successfully verified AttemptNo. as - [%s]", verification_list[4])
        else:
            self.log.error("Failed to verify Resync Status : Expected - [%s] & Actual - [%s]", verification_list[4],
                           resync_row[4])
            failure = True

        return not failure

    def verify_resync_logging(self):
        """
        Verify Resync Logging for each of the SIDB store

        Returns:
            Boolean True/False based on whether verifications were successful or they failed
        """
        success_status = True
        log_file = "SIDBEngine.log"
        log_validation_str_list = [f'Unable to get AFInfoList for SIDBStoreId [{self.sidb_store.store_id}] from MM. RetCode [-1]',
                                   'DDB and CS Af diff failed. iRet [53006]']


        store_id = self.sidb_store.store_id
        #DoAfDiff 5037 Mismatched sizes - request Afs [500] response Afs [0]. Aborting.
        #Unable to get AFInfoList for SIDBStoreId [22138] from MM. RetCode [-1]
        #DDB and CS Af diff failed. iRet [53006]
        self.log.info("Log Validations for SIDB store [%s]", store_id)
        for log_line in range(1, len(log_validation_str_list)+1):
            #Verify that bad primary range got added
            log_validation_str1 = f"{store_id}-0-"
            log_validation_str2 = f"{store_id}-1-"
            self.log.info("Verifying String - [ %s ]", log_validation_str_list[log_line-1])
            matched_lines, matched_strings = self.dedup_helper_obj.parse_log(
                self.ma_name, log_file, log_validation_str_list[log_line-1])
            if matched_lines:
                self.log.info(matched_lines)
                for line in matched_lines:
                    if line.count(log_validation_str1) or line.count(log_validation_str2):
                        self.log.info("***Successfully verified***")
            else:
                self.log.error("Log validation failure for SIDB Store - [%s]", store_id)
                self.result_string  += f"Log Verification Failed : SIDB : {store_id}\n"
                success_status = False

        return success_status



    def modify_archfilevalidate_sp(self, induce_error=True):
        """
        Modify stored procedure ArchFileValidate

        induce_error    (Boolean)   --  If True, Modify Stored Procedure to induce error, revert to original otherwise
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
        error_injection_already_exist = False
        if not induce_error:
            self.log.info("Reverting the stored procedure to original code")
            new_sp = self.original_stored_proc
            if new_sp.count('---AUTOMATION CODE ADDED BY TC---'):
                self.log.warning("Original Stored Proc contains Code Added by TC. Removing the error inducing code")
                new_sp = new_sp.replace('---AUTOMATION CODE ADDED BY TC---', '')
                new_sp = new_sp.replace('declare @random_number decimal(10,5)', '')
                new_sp = new_sp.replace('set @random_number = RAND()', '')
                new_sp = new_sp.replace('if @random_number < 0.4 (select 100/0)', '')
                new_sp = new_sp.replace('---AUTOMATION CODE ADDED BY TC---', '')
        else:
            output = con.execute('exec sp_helptext ?', ('ArchFileValidate',)).fetchall()
            con.close()
            outputlines = """"""
            for line in output:
                if line[0].count('declare @random_number decimal(10,5)') or line[0].count('---AUTOMATION CODE ADDED BY TC---'):
                    error_injection_already_exist = True
                outputlines = outputlines + (line[0])
            self.original_stored_proc = outputlines
            self.log.info("Fetched original stored procedure")
            self.log.info("%s\n%s\n%s", '*' * 80, self.original_stored_proc, '*' * 80)
            if not error_injection_already_exist:
                self.log.info("Locating the line after which error code will be injected")
                outputlist = outputlines.split(
                    '--If this is for reconstruction then find the jobStartTime of the store from JM table.')
                new_sp = f"""{outputlist[0]} """ + """--If this is for reconstruction then find the jobStartTime of the store from JM table.
                    ---AUTOMATION CODE ADDED BY TC---
                    declare @random_number decimal(10,5) 
                    set @random_number = RAND() 
                    if @random_number < 0.4 (select 100/0)
                    ---AUTOMATION CODE ADDED BY TC---""" + f"""{outputlist[1]}"""
            else:
                self.log.warning("Error injection code already exists in Stored Procedure ArchFileValidate")

        if not error_injection_already_exist:
            self.log.info("Modifying Stored Procedure ArchFileValidate")
            create_strings = re.findall('create procedure', new_sp, re.IGNORECASE)
            for create_string in create_strings:
                new_sp = new_sp.replace(create_string, 'alter procedure')
                self.log.info("Modified Stored Procedure with ALTER PROCEDURE statement =====\n%s\n======", new_sp)
                break
            self.mahelper_obj.execute_update_query(new_sp, db_password=sql_passwd, db_user=sql_user)
        else:
            self.log.warning("Stored Procedure ArchFileValidate already has error injection code. "
                             "Hence not altering Stored Procedure")

    def get_ddb_af_details(self):
        """
        Fetch sidb2 listaf command output

        Returns:
            output of sidb2 listaf command
        """

        if self.dedup_helper_obj.wait_till_sidb_down(str(self.sidb_store.store_id),
                                                 self.commcell.clients.get(self.ma_name)):
            self.log.info("SIDB2 process for engine %s has gone down", self.sidb_store.store_id)
            output = self.dedup_helper_obj.execute_sidb_command('listaf', int(self.sidb_store.store_id),
                                                                        '0', self.ma_name)
            self.log.info("********%s********", output[1])
            if output[0] == 0:
                return output[1]
            else:
                self.log.error("Fetching AF Details from DDB failed")
                raise Exception(f"Failure in fetching AF Details for SIDB2 - [{self.sidb_store.store_id}]")
        else:
            self.log.error("SIDB2 process for engine %s has not gone down in default wait period")
            raise Exception(f"SIDB2 process for engine has not gone down in default wait period "
                            f"- [{self.sidb_store.store_id}]")

    def compare_af_details(self):
        """
        Compare AF details captured before and after the Resync attempts

        Returns:
            True if both the outputs are same, False otherwise
        """
        if self.af_details_before_resync == self.af_details_after_resync:
            self.log.info("Successfully verified that AFs before and after Resync operation are same")
            return True
        else:
            self.log.error("Failure : AFs before and after Resync operation are not same.")
            self.result_string += "Failure during verification of AFs in DDB before & after Resync operation"
            return False

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Performing cleanup before test case run")
            self.cleanup()
            self.configure_tc_environment()
            self.run_backups(8)
            self.af_details_before_resync = self.get_ddb_af_details()
            self.modify_archfilevalidate_sp(True)

            if not self.prepare_and_wait_for_resync():
                self.status = constants.FAILED
            else:
                self.log.info("IdxSIDBResyncHistory Verification Succeeded.")

            if not self.verify_resync_logging():
                self.status = constants.FAILED
            else:
                self.log.info("Resync Log Verification Succeeded.")

            self.af_details_after_resync = self.get_ddb_af_details()

            if not self.compare_af_details():
                self.status = constants.FAILED
            else:
                self.log.info("SIDB2 AFs Comparision Succeeded.")

            if self.status == constants.FAILED:
                self.log.error("Test case failure : [%s]", self.result_string)
                raise Exception(self.result_string)
            else:
                self.log.info("Test case completed successfully")

        except Exception as exp:
            self.status = constants.FAILED
            self.log.error('Failed to execute test case with error: %s', (str(exp)))

    def tear_down(self):
        """Tear down function of this test case"""
        if self.original_stored_proc != "":
            self.modify_archfilevalidate_sp(False)
        if self.ma_client:
            self.log.info("Deleting Regkey [SIDBAfDiffBatchSize] from MA - [%s]", self.ma_name)
            self.ma_client.delete_additional_setting("MediaAgent", "SIDBAfDiffBatchSize")
        try:
            self.cleanup()
        except Exception as ex:
            self.log.error(f"Failed to perform cleanup {ex}")


