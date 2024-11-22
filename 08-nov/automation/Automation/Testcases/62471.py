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

    verify_resync_status()          --	 Verify Resync status for each of the SIDB store

    verify_resync_logging()         --  Verify Resync Logging for each of the SIDB store

    verify_idxsidb_resync_history() --	 Verify that IdxSIDBResyncHistory has a row for DDB store with correct reason

    set_last_access_time_and_primaryid()  --  Sets values in LastAccessTime and PrimaryID column for each partition

    prepare_and_wait_for_resync	()  --  Modify the SIDB Creation Time to 45 days older than its present creation time.

    prepare_stores_for_timestamp_mismatch() --  Computes the LastAccessTime & PrimaryID values for Split 0.

    get_last_access_time_and_primaryid()    --	 Finds values in LastAccessTime and PrimaryID column in each partition

    verify_backup_restore_post_resync() --	Verify backup and restore for first storage pool where resync completed.

    run_backups()	--  Run backups on all subclients and maintain list of job IDs for each subclient

    configure_tc_environment()  -- Configure testcase environment - library (if required), storage policy, backupset,
                                    subclient

    Steps:
    1. Create 3 dedup storage pools & storage policies with 2 partitions on the given MA
    2. Create a backupset on client with 3 subclients, each one associated with 1 storage policy
    3. Run 2 backups of 1 GB each on each subclient
    4. Capture details about PrimaryID & LastAccessTime for Group 0 of each of the 3 stores
    5. Run 2 more backups of 1 GB each on each subclient
    6. Repeat step 4
    7. Perform modifications in PrimaryID and LastAccessTime of store such that
        a. store0 : LastAccessTime in CSDB moved back by 3 days & PrimaryID set to the one recorded in step 4
        b. store1 : LastAccessTime in CSDB moved back by 6 days & PrimaryID set to the one recorded in step 4
        c. store2 : LastAccessTime in CSDB is moved ahead by 3 days & PrimaryID set to greater than the one recorded
                    in step 6
    8. Modify CreatedTime of store to current date minus 40 days
    9. Wait for Resync to take place by checking IdxSIDBResyncHistory table for an entry for each store
        a. Store 0 : Status = 0
        b. Store 1 : Status = 53042
        c. Store 2 : Status = 53027
    10. Verify following once Resync is confirmed
        a. store0 : MA side resync has taken place and bad primary range has got added. IdxSIDBResyncHistory has got
                    updated by monthly resync which brought up the SIDB process. Backups & Restore of same data work
                    without any issues.
        b. store1 : Sanity check failure was reported and monthly resync did not complete
        c. store2 : Sanity check failure was reported and monthly resync did not complete. Store was marked corrupt.

    Expected Input :
    		"62471":{
    		        "ClientName": "client name",
					"AgentName": "File System",
					"MediaAgentName": "ma name"}

"""
import time
from cvpysdk import deduplication_engines
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
        self.name = "DDB Resync - CSDB and DDB Timestamp mismatch threshold of 5 days"
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
        self.sidb_store_list = []
        self.subclient_list = []
        self.storage_pool_list = []
        self.storage_policy_list = []
        self.content_path_list = []
        self.backup_jobs_dict = {}


    def setup(self):
        """Setup function of this test case"""

        self.optionobj = OptionsSelector(self.commcell)
        self.ma_name = self.tcinputs.get('MediaAgentName')
        self.dedup_path = self.tcinputs.get('dedup_path')

        self.client_machine_obj = Machine(self.client)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine_obj, 30)
        self.ma_machine_obj = Machine(self.ma_name, self.commcell)
        self.ma_library_drive = self.optionobj.get_drive(self.ma_machine_obj, 30)

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

        self.log.info("Configuring 3 Storage Pools for this test.")

        for itr in range(1,4):
            storage_pool_name = f"{self.storage_policy_name}_POOL_{itr}"
            storage_policy_name = f"{self.storage_policy_name}_{itr}"
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

            copy_id = self.storage_pool_list[itr-1].get_copy('Primary_Global').copy_id


            #SIDB Engine Details
            dedup_engines_obj = deduplication_engines.DeduplicationEngines(self.commcell)
            if dedup_engines_obj.has_engine(storage_pool_name, 'Primary_Global'):
                dedup_engine_obj = dedup_engines_obj.get(storage_pool_name, 'Primary_Global')
                dedup_stores_list = dedup_engine_obj.all_stores
                self.sidb_store_list.append(dedup_engine_obj.get(dedup_stores_list[0][0]))

            #adding partition 2
            self.storage_pool_list[itr-1].add_ddb_partition(copy_id, str(self.sidb_store_list[itr-1].store_id),
                                                            dedup_path_2, self.ma_name)

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

            self.log.info("Creating subclient for using SIDB Store ID - [%s]", self.sidb_store_list[itr-1].store_id)
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
            self.log.info("Setting number of streams to 5")
            self.subclient_list[itr-1].data_readers = 5
            self.subclient_list[itr-1].allow_multiple_readers = True
            self.backup_jobs_dict[subclient_name]=[]

    def run_backups(self):
        """
        Run backups on all subclients and maintain list of job IDs for each subclient
        """
        for itr in range(0, len(self.subclient_list)):
            self.log.info("Generating content for subclient [%s] at [%s]", self.subclient_list[itr].name,
                          self.content_path_list[itr])
            self.mahelper_obj.create_uncompressable_data(self.tcinputs['ClientName'], self.content_path_list[itr], 0.5)
            self.log.info("Starting backup on subclient %s", self.subclient_list[itr].name)
            job = self.subclient_list[itr].backup("Incremental")
            self.backup_jobs_dict[self.subclient_list[itr].name].append(job)
            if not job.wait_for_completion():
                raise Exception(f"Failed to run backup job with error: {job.delay_reason}")
            self.log.info("Backup job [%s] on subclient [%s] completed", job.job_id, self.subclient_list[itr].name)

    def verify_backup_restore_post_resync(self):
        """
        Verify backup and restore for first storage pool where resync completed.

        """
        self.log.info("Running Full backup on subclient - [%s]", self.subclient_list[0].name)
        job = self.subclient_list[0].backup("Full")

        if not job.wait_for_completion():
            raise Exception(f"Failed to run backup job with error: {job.delay_reason}")
        self.log.info("Backup job [%s] on subclient [%s] completed", job.job_id, self.subclient_list[0].name)

        self.log.info("Running Restore on subclient - [%s]", self.subclient_list[0].name)
        restore_job = self.subclient_list[0].restore_out_of_place(self.client.client_name, self.restore_path,
                                                                  [self.content_path_list[0]])
        self.log.info("Restore job: %s", restore_job.job_id)
        if not restore_job.wait_for_completion():
            if restore_job.status.lower() == "completed":
                self.log.info("job %d complete", restore_job.job_id)
            else:
                raise Exception(f"Job {restore_job.job_id} Failed with {restore_job.delay_reason}")

        self.log.info("Performing Data Validation after Restores")
        difference = self.client_machine_obj.compare_folders(self.client_machine_obj,
                                                             self.content_path_list[0], self.restore_path +
                                                             self.client_machine_obj.os_sep +
                                                             self.subclient_list[0].name)
        if difference:
            self.log.error("Validating Data restored after Timestamp Mismatch Failed for SIDB Store - [%s]",
                           self.sidb_store_list[0].store_id)
            return False

        self.log.info('Data Restore Validation passed after timestamp mismatch for SIDB Store - [%s]',
                      self.sidb_store_list[0].store_id)
        return True

    def get_last_access_time_and_primaryid(self):
        """
        Finds values in LastAccessTime and PrimaryID column in each partition and returns a dictionary
        with following format
        engineid : {
                        [ substoreid : { lastaccesstime : <value>, primaryid : <value>},
                        [ substoreid : { lastaccesstime : <value>, primaryid : <value>}
                    }

        """
        self.log.info("Sleeping for 1 minute as sometimes primary ID update in CSDB takes this time as SIDB does"
                      "not go down immediately after backups")
        time.sleep(60)

        last_access_primary_dict = {}
        for itr in range(0, len(self.sidb_store_list)):
            query = f"select substoreid, lastaccesstime, primaryid from idxsidbsubstore " \
                    f"where sidbstoreid={self.sidb_store_list[itr].store_id} order by substoreid"
            self.log.info("Query ==> %s", query)
            self.csdb.execute(query)
            substore_mapping = self.csdb.fetch_all_rows()
            self.log.info(substore_mapping)
            substore_info_list = []

            for substore_info in substore_mapping:
                substore_details_dict = {'SubStoreId' : int(substore_info[0]), 'LastAccessTime': int(substore_info[1]),
                                         'PrimaryId': int(substore_info[2])}
                substore_info_list.append(substore_details_dict)
                self.log.info("SubstoreId : %s LastAccessTime : %s PrimaryId : %s", substore_info[0], substore_info[1],
                              substore_info[2])
            last_access_primary_dict[self.sidb_store_list[itr].store_id] = substore_info_list

        return last_access_primary_dict

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

            self.log.info("Cleaning up depenednt storage policies")
            for itr in range(1, 4):
                if self.commcell.storage_policies.has_policy(f"{self.storage_policy_name}_{itr}"):
                    self.log.info("Deleting Dependent SP - [%s]", f"{self.storage_policy_name}_{itr}")
                    self.commcell.storage_policies.delete(f"{self.storage_policy_name}_{itr}")

            self.log.info("Cleaning up storage pools")
            for itr in range(1, 4):
                if self.commcell.storage_policies.has_policy(f"{self.storage_policy_name}_POOL_{itr}"):
                    self.log.info("Deleting Storage Pool - [%s]", f"{self.storage_policy_name}_POOL_{itr}")
                    self.commcell.storage_policies.delete(f"{self.storage_policy_name}_POOL_{itr}")

        except Exception as exp:
            self.log.warning("**********Cleanup before test run failed. Still continuing with test run. "
                             "Perform manual cleanup and re-run if any failure is observed."
                             " ERROR : %s**********", exp)


    def prepare_stores_for_timestamp_mismatch(self, current_substore_state, past_substore_state):
        """
        Computes the LastAccessTime & PrimaryID values for Split 0 of each of the storage pools.

        Args:
            current_substore_state (Dict)   : Dictionary returned by get_last_access_time_and_primaryid method
            past_substore_state (Dict)   : Dictionary returned by get_last_access_time_and_primaryid method


        Returns:
             Dictionary containing SubstoreID and Values to be set in LastAccessTime & PrimaryID Columns
             Eg.{   substoreid1 : {'LastAccessTime':1234, 'PirmaryId':5678},
                    substoreid2 : {LastAccessTime':2345, 'PirmaryId':6789}
                }
        """
        target_substore_values_dict = {}

        for itr in range(0, len(self.sidb_store_list)):
            store_id = self.sidb_store_list[itr].store_id
            substore_id = current_substore_state[store_id][0]['SubStoreId']
            self.log.info("Inducing timestamp mismatch error for Store ID - [%s]", store_id)
            if itr == 0:
                self.log.info("Inducing error For First Storage Pool : CSDB < DDB by less than 5 Days")
                #LastAccessTime = Current_LastAccessTime - 4 days
                new_lastaccesstime = current_substore_state[store_id][0]['LastAccessTime']-(86400*4)
                #New PrimaryID = Primary ID after first 2 jobs.
                new_primaryid = past_substore_state[store_id][0]['PrimaryId']
            elif itr == 1:
                self.log.info("Inducing error For Second Storage Pool : CSDB < DDB by greater than 5 Days")
                # LastAccessTime = Current_LastAccessTime - 7 days
                new_lastaccesstime = current_substore_state[store_id][0]['LastAccessTime'] - (86400 * 7)
                # New PrimaryID = Primary ID after first 2 jobs.
                new_primaryid = past_substore_state[store_id][0]['PrimaryId']
            else:
                self.log.info("Inducing error For Third Storage Pool : CSDB > DDB by greater than 2 Days")
                # LastAccessTime = Current_LastAccessTime + 2 days
                new_lastaccesstime = current_substore_state[store_id][0]['LastAccessTime'] + (86400 * 2)
                # New PrimaryID = A random primary ID greater than latest primary ID.
                new_primaryid = current_substore_state[store_id][0]['PrimaryId'] + 10000

            self.log.info("substore = [%s] new_lastaccesstime = [%s] and new_primaryid = [%s]",
                          substore_id, new_lastaccesstime, new_primaryid)

            target_substore_values_dict[substore_id] = {'LastAccessTime': new_lastaccesstime,
                                                        'PrimaryId': new_primaryid}


        return target_substore_values_dict

    def prepare_and_wait_for_resync(self):
        """
        Modify the SIDB Creation Time to 45 days older than its present creation time. Also delete IdxSIDBResyncHistory
        rows for these SIDBStores if there exist any.

        """

        sidb_stores = ','.join([ str(store.store_id) for store in self.sidb_store_list ])
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

        sidb_stores = ','.join([str(store.store_id) for store in self.sidb_store_list])
        resync_done = False
        for itr in range(1,16):
            query = f"select count(1) from IdxSIDBResyncHistory where sidbstoreid in ({sidb_stores}) " \
                    f"and Resyncstatus != -1"
            self.log.info("QUERY : %s", query)
            self.csdb.execute(query)
            resync_history = self.csdb.fetch_one_row()
            self.log.info(resync_history)
            if int(resync_history[0]) == 3:
                self.log.info("IdxSIDBResyncHistory table is populated with at least one row each from these stores.")
                self.log.info(resync_history)
                resync_done = True
                self.log.info("Moving MM Admin Thread Interval back to 15 minutes so that Reconstruction "
                              "does not start immediately")
                self.mahelper_obj.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5, 15)
                break
            else:
                self.log.info("Checking IdxSIDBResyncHistory table after 1 minute. Attempt Number - [%s]", itr)
                time.sleep(60)

        if not resync_done:
            self.log.error("Resync did not happen even after 15 minutes. Failing this case.")
            raise Exception("Resync did not happen even after 15 minutes. Failing this case.")
        else:
            self.log.info("IdxSIDBResyncHistory table has valid rows for target SIDB Engines. Sleeping for 1 minute"
                          "before resumption")
            time.sleep(60)

    def set_last_access_time_and_primaryid(self, substore_info):
        """
        Sets values in LastAccessTime and PrimaryID column for each partition

        Args:
        substore_info (dictionary obj) - dictionary containing substore id and values for lastaccesstime
        and primary id which need to be set

        {substoreid : { lastaccesstime : <value>, primaryid : <value>}}
        """

        for (key, value) in substore_info.items():
            primaryid = value['PrimaryId']
            last_access_time = value['LastAccessTime']
            self.log.info("Updating Substore : %s ==> PrimaryID to %s and LastAccessTime to %s", key,
                          primaryid, last_access_time)
            query = f"update idxsidbsubstore set PrimaryId = {primaryid}, LastAccessTime = {last_access_time}" \
                    f" where substoreid={key}"
            self.log.info("QUERY : %s", query)
            self.optionobj.update_commserve_db(query)

        self.log.info("Successfully set the values for PrimaryId and LastAccessTime for substores")

    def verify_idxsidb_resync_history(self, engine_id, verification_list):
        """
        Verify that IdxSIDBResyncHistory has a row for DDB store with correct reason

        Args:
            engine_id           (int)   --  SIDB Engine Id
            verification_list  (list)   --  List of values in following columns for verifying resync history
                                            [Status, ResyncFlags, MaintenanceReason, NumResyncedAFIDs]

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

        return not failure

    def verify_resync_logging(self, current_substore_state, past_substore_state):
        """
        Verify Resync Logging for each of the SIDB store

        Args:
            current_substore_state (Dict)  : Dictionary returned by get_last_access_time_and_primaryid method
            past_substore_state (Dict)   : Dictionary returned by get_last_access_time_and_primaryid method

        Returns:
            Boolean True/False based on whether verifications were successful or they failed
        """
        success_status = True
        log_file = "SIDBEngine.log"
        log_validation_str_list = ['Sanity check failed. Last open time does not match up.',
                                   'Mismatch in last open time [7.000000 days] is greater than allowed [5 days]. Skipping resync.',
                                   'The DDB is not in correct state to do a resync. ',
                                   'DDB is behind CSDB. Looks like we are using an older DDB. Marking DDB Corrupt.',
                                   'Marked the DDB as corrupted. Corruption Type',
                                   'The DDB is not in correct state to do a resync'
                                   ]

        for itr in range(0, len(self.sidb_store_list)):
            store_id = self.sidb_store_list[itr].store_id
            #2448  9e8   03/12 21:51:53 ### 2106-0-2489-0 ResyncSetLastPriId 14923
            # Added closed range [409 - 801] to bad primary range list. list size [1]
            old_pri_id = past_substore_state[store_id][0]['PrimaryId']
            new_pri_id = current_substore_state[store_id][0]['PrimaryId'] - 1
            bad_primary_range_str = f"Added closed range [{old_pri_id} - {new_pri_id}] to bad primary range list."
            self.log.info("Log Validations for SIDB store [%s]", store_id)
            if itr == 0:
                #Verify that bad primary range got added
                log_validation_str = f"{store_id}-0-"
                self.log.info("Verifying String - [ %s ]", log_validation_str_list[0])
                matched_lines, matched_strings = self.dedup_helper_obj.parse_log(
                    self.ma_name, log_file, log_validation_str_list[0])
                if matched_lines:
                    for line in matched_lines:
                        if line.count(log_validation_str):
                            self.log.info("***Successfully verified***")
                else:
                    self.log.error("Log validation failure for SIDB Store - [%s]", store_id)
                    self.result_string  += f"Log Verification Failed : SIDB : {store_id}\n"
                    success_status = False

                self.log.info("Verifying String - [%s]", bad_primary_range_str)
                matched_lines, matched_strings = self.dedup_helper_obj.parse_log(
                    self.ma_name, log_file, bad_primary_range_str)
                if matched_lines:
                    for line in matched_lines:
                        if line.count(log_validation_str):
                            self.log.info("***Successfully verified***")
                else:
                    self.log.error("Log validation failure for SIDB Store - [%s]", store_id)
                    self.result_string += f"Log Verification Failed : SIDB : {store_id}\n"
                    success_status = False

            elif itr == 1:
                #Verify that bad primary range got added but DDB will stay in invalid state
                log_validation_str = f"{store_id}-0-"
                verify_count = 0
                for itr in range(0,3):
                    self.log.info("Verifying String - [ %s ]", log_validation_str_list[itr])
                    matched_lines, matched_strings = self.dedup_helper_obj.parse_log(
                        self.ma_name, log_file, log_validation_str_list[itr])
                    if matched_lines:
                        for line in matched_lines:
                            if line.count(log_validation_str):
                                self.log.info("***Successfully verified***")
                                verify_count += 1
                                break
                if verify_count != 3:
                    self.log.error("Log validation failure for SIDB Store - [%s]", store_id)
                    self.result_string  += f"Log Verification Failed : SIDB : {store_id}\n"
                    success_status = False

            else:
                #Verify that DDB is marked corrupt due to timestamp mismatch and no primary range got added
                log_validation_str = f"{store_id}-0-"
                verify_count = 0
                for itr in [0, 3, 4, 5]:
                    self.log.info("Verifying String - [ %s ]", log_validation_str_list[itr])
                    matched_lines, matched_strings = self.dedup_helper_obj.parse_log(
                        self.ma_name, log_file, log_validation_str_list[itr])
                    if matched_lines:
                        for line in matched_lines:
                            if line.count(log_validation_str):
                                self.log.info("***Successfully verified***")
                                verify_count += 1
                                break
                if verify_count != 4:
                    self.log.error("Log validation failure for SIDB Store - [%s]", store_id)
                    self.result_string  += f"Log Verification Failed : SIDB : {store_id}\n"
                    success_status = False

        return success_status

    def verify_resync_status(self, current_substore_state):
        """
        Verify Resync status for each of the SIDB store

        Args:
            current_substore_state (Dict)  : Dictionary returned by get_last_access_time_and_primaryid method

        Returns:
            Boolean True/False based on whether verifications were successful or they failed
        """
        success_status = True
        for itr in range(0, len(self.sidb_store_list)):
            store_id = self.sidb_store_list[itr].store_id
            self.log.info("Verifying Resync Status of SIDB - [%s]", store_id)
            if itr == 0:
                self.log.info("CSDB < DDB by less than 5 Days : Expecting Monthly Resync to succeed and MA "
                              "Side Resync to take place")
                if self.verify_idxsidb_resync_history(store_id, [0, 5, 11, 0]):
                    self.log.info("Resync verification success : Substore [%s] in SIDB [%s]",
                                  current_substore_state[store_id][0]['SubStoreId'], store_id)
                else:
                    self.log.error("Resync verification failed : Substore [%s] in SIDB [%s]",
                                  current_substore_state[store_id][0]['SubStoreId'], store_id)
                    success_status = False
                    self.result_string  += f"Resync Verification Failed : SIDB : {store_id}\n"
            elif itr == 1:
                self.log.info("CSDB < DDB by greater than 5 Days : Expecting Monthly Resync to fail and SIDB Store "
                              " to stay in Sanity Check Failure state")
                # LastAccessTime = Current_LastAccessTime - 7 days
                if self.verify_idxsidb_resync_history(store_id, [53042, 5, 11, 0]):
                    self.log.info("Resync verification success : Substore [%s] in SIDB [%s]",
                                  current_substore_state[store_id][0]['SubStoreId'], store_id)
                else:
                    self.log.error("Resync verification failed : Substore [%s] in SIDB [%s]",
                                  current_substore_state[store_id][0]['SubStoreId'], store_id)
                    success_status = False
                    self.result_string  += f"Resync Verification Failed : SIDB : {store_id}\n"
            else:
                self.log.info("CSDB > DDB by greater than 2 Days : Expecting Store to get marked corrupt due to Sanity"
                              " Check Failure")
                # LastAccessTime = Current_LastAccessTime + 2 days
                query = f"select status from idxsidbsubstore where substoreid = " \
                        f"{current_substore_state[store_id][0]['SubStoreId']}"
                self.log.info("QUERY : %s", query)
                self.csdb.execute(query)
                corrupt_store = self.csdb.fetch_one_row()
                self.log.info(corrupt_store)
                if int(corrupt_store[0]) == 1:
                    self.log.info("Substore [%s] in SIDB [%s] is marked corrupt as expected",
                                  current_substore_state[store_id][0]['SubStoreId'], store_id)
                else:
                    self.log.error("Partition is not marked corrupt even when expected")
                    success_status = False
                    self.result_string  += f"Partition Corruption Verification Failed : SIDB : {store_id}\n"

                if self.verify_idxsidb_resync_history(store_id, [53027, 5, 11, 0]):
                    self.log.info("Resync verification success : Substore [%s] in SIDB [%s]",
                                  current_substore_state[store_id][0]['SubStoreId'], store_id)
                else:
                    self.log.error("Resync verification failed : Substore [%s] in SIDB [%s]",
                                  current_substore_state[store_id][0]['SubStoreId'], store_id)
                    success_status= False
                    self.result_string  += f"Resync Verification Failed : SIDB : {store_id}\n"

        return success_status

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Performing cleanup before test case run")
            self.cleanup()
            self.configure_tc_environment()
            self.run_backups()
            primaryid_last_access_dict_first = self.get_last_access_time_and_primaryid()
            self.run_backups()
            primaryid_last_access_dict_second = self.get_last_access_time_and_primaryid()
            error_induction_targets = self.prepare_stores_for_timestamp_mismatch(primaryid_last_access_dict_second,
                                                                                 primaryid_last_access_dict_first)
            self.set_last_access_time_and_primaryid(error_induction_targets)
            self.prepare_and_wait_for_resync()
            if not self.verify_resync_status(primaryid_last_access_dict_second):
                self.status = constants.FAILED
            else:
                self.log.info("Resync Verification Succeeded.")

            if not self.verify_resync_logging(primaryid_last_access_dict_second, primaryid_last_access_dict_first):
                self.status = constants.FAILED
            else:
                self.log.info("Resync Log Verification Succeeded.")

            if not self.verify_backup_restore_post_resync():
                self.status = constants.FAILED
            else:
                self.log.info("Resync Restore Verification Succeeded.")
        except Exception as exp:
            self.status = constants.FAILED
            self.log.error('Failed to execute test case with error: %s', (str(exp)))

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            self.cleanup()
        except Exception as ex:
            self.log.warning(f"Test case cleanup failed - {ex}")


