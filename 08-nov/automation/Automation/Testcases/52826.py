# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    get_sql_connection()				    --	get sql connection object

    create_tc_env()						        --  create test case environment

    run_backup_jobs()					        --	run backup jobs

    compute_deletion_candidates()		        --	compute to be deleted jobs & entities

    get_afs_common_in_csdb_ddb()		        --	get AFs which are common in DDB and CSDB for further processing

    delete_jobs()						        --	delete jobs

    change_store_pruning_value()		        --	enable or disable ddb pruning

    check_deleted_entries_in_table()	        --	check given entries are deleted from csdb table

    delete_af_entries()					        --	delete entried from tables

    run_space_reclamation_job_check_resync()    --	Run Space Reclamation job and verify Resync bit is set on DDB

    wait_for_resync_completion()		        --	wait till resync flag is reset

    verify_idxsidb_resync_history()		        --	verify idxsidbresynchistory table rows

    previous_run_cleanup()				        --	cleanup the entities created in previous run

     Sample JSON File:
    "52826": {
				"AgentName": "File System",
				"MediaAgentName": "ma name",
				"ClientName" : "client name"
			}

	Steps:
	    1. Clean up already existing configuration
	    2. Create disk library, dedup enabled storage policy, backupset and subclient
	    3. Run 5 backups on the subclient
	    4. Compute 2 to-be-deleted jobs and corresponding Archive Files and Chunks
	    5. Set MM Config Thread Interval to 5 minutes.
	    6. Set MM Prune Process Interval to 2 minutes.
	    7. Disable DDB store Level Pruning
	    8. Delete 2 jobs and run data aging
	    9. Verify that Archfile, Archchunkmapping and Archfilecopydedup tables have
	       no entries left behind for deleted jobs
	    10. Delete entries from MMDeletedAF table
	    11. Delete entries from  MMDeletedArchFileTracking Table.
	    12. Enable DDB store Level pruning
	    13. Run Space Reclamation job and check if store gets marked for Resync
	    14. Wait for Resync to complete
	    15. Verify IdxSIDBResyncHistory table has a new row with status=0,
	        NumResyncedAFIds = AFIDs corresponding to deleted jobs,
                MaintenanceReason = 9 and ResyncFlags = 1
	    16. Run SIDB listaf command to make sure that resynced AFs are not present in CSDB

"""
import time
from AutomationUtils import constants, cvhelper
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "resync - validate and prune"
        self.tcinputs = {
            "MediaAgentName": None,
           }

        # Local variables
        self.backupset_name = None
        self.subclient_name = None
        self.backupset_obj = None
        self.subclient_obj = None
        self.mediaagentname = ""
        self.ma_machineobj = None
        self.dedup_path = None
        self.storage_policy_name = None
        self.library_name = None
        self.content_path = None
        self.client_system_drive = None
        self.ma_drive = None
        self.mount_path = None
        self.machineobj = None
        self.dedup_obj = None
        self.mmhelper_obj = None
        self.result_string = ""
        self.copyid = None
        self.engineid = None
        self.sql_password = None
        self.prune_process_interval = None
        self.sp_obj = None
        self.ddb_store_obj = None
        self.sp_copy_obj = None
        self.maintenance_interval = None

    def setup(self):
        """Setup function of this test case"""
        optionobj = OptionsSelector(self.commcell)
        suffix = str(self.mediaagentname)[:] + "_" + str(self.client.client_name)[:]
        self.mediaagentname = self.tcinputs["MediaAgentName"]
        self.machineobj = Machine(self.client)
        self.client_system_drive = optionobj.get_drive(self.machineobj)
        self.ma_machineobj = Machine(self.mediaagentname, self.commcell)
        self.ma_drive = optionobj.get_drive(self.ma_machineobj)
        timestamp_suffix = OptionsSelector.get_custom_str()
        self.dedup_path = self.ma_machineobj.join_path(self.ma_drive, "DDB_%s_%s"%(self.id , timestamp_suffix))
        self.storage_policy_name = "SP_%s_%s"%(self.id, suffix)
        self.library_name = "lib_%s_%s"%(self.id, suffix)
        self.backupset_name = "bkpset_%s_%s"%(self.id, suffix)
        self.subclient_name = "subc_%s_%s"%(self.id, suffix)
        self.mount_path = self.ma_machineobj.join_path(self.ma_drive, self.library_name)
        self.content_path = self.machineobj.join_path(self.client_system_drive, "content_%s_%s"%(self.id, suffix))
        self.dedup_obj = DedupeHelper(self)
        self.mmhelper_obj = MMHelper(self)
        self.prune_process_interval = 2
        self.maintenance_interval = 5

    def get_sql_connection(self):
        """
        Initialize the SQL connection object
        """
        cs_machine = Machine(self.commcell.commserv_client)
        encrypted_pass = cs_machine.get_registry_value(r"Database", "pAccess")
        self.sql_password = cvhelper.format_string(self.commcell, encrypted_pass).split("_cv")[1]

    def create_tc_env(self):
        """
        Create test case environment consisting of a library, dedup policy, backupset and subclient
        """
        #Create Library using Mountpath

        self.log.info("Configuring Library %s", self.library_name)
        self.mmhelper_obj.configure_disk_library(self.library_name, self.mediaagentname, self.mount_path)

        self.log.info("Configuring Dedup Storage Policy %s", self.storage_policy_name)
        self.sp_obj = self.dedup_obj.configure_dedupe_storage_policy(self.storage_policy_name, self.library_name,
                                                                self.mediaagentname, self.dedup_path)
        self.log.info("Configuring Backupset %s", self.backupset_name)
        self.backupset_obj = self.mmhelper_obj.configure_backupset(self.backupset_name)

        self.log.info("Configuring Subclient %s", self.subclient_name)
        self.subclient_obj = self.mmhelper_obj.configure_subclient(self.backupset_name, self.subclient_name,
                                                                   self.storage_policy_name, self.content_path)

        if self.machineobj.check_directory_exists(self.content_path):
            self.machineobj.remove_directory(self.content_path)
        self.machineobj.create_directory(self.content_path)

        self.log.info("Setting number of streams to [%s]", 4)
        self.subclient_obj.data_readers = 4

        self.log.info("Setting multiple data readers to [True]")
        self.subclient_obj.allow_multiple_readers = True

        self.copyid = self.mmhelper_obj.get_copy_id(self.storage_policy_name, 'Primary')
        self.sp_copy_obj = self.sp_obj.get_copy('Primary')
        self.get_sql_connection()



    def run_backup_jobs(self, backuptype="Incremental", count=2):
        """
        Run a backup job on subclient
        Args:
        backuptype (str)    --  Backup type , Incremental by default.
        count (int)         --  How many such backup jobs

        Return:
        Dictionary containing JobID as key and list of ArchFiles with filetype=1 as values.
        List containing JobIDs
        """
        job_af_dict = {}
        for _ in range(0, count):
            try:
                self.mmhelper_obj.create_uncompressable_data(self.client.client_name, self.content_path, 0.5, 1)
                job_obj = self.subclient_obj.backup(backuptype)
                self.log.info("Successfully initiated a %s backup job on subclient with jobid - %s", backuptype,
                              job_obj.job_id)
                try:
                    if job_obj.wait_for_completion() is False:
                        raise Exception("Backup job %s did not complete in given timeout"%job_obj.job_id)
                except Exception as ex:
                    self.log.error("Failed to wait till job completes - %s", str(ex))
                    raise Exception("Wait for job completion did not work as expected. Exiting the test case.")
            except Exception as exc:
                self.log.error("Failed to run backup job on subclient - %s", str(exc))
            self.log.info("Successfully completed a backup job on subclient with jobid - %s", job_obj.job_id)
            #Run query to fetch ArchFiles
            query = "select id from archfile where jobid = %s and filetype = 1"%job_obj.job_id
            self.log.info("Query: %s", query)
            self.csdb.execute(query)
            afs_list = self.csdb.fetch_all_rows()
            self.log.info(afs_list)
            job_af_dict[int(job_obj.job_id)] = [int(x[0]) for x in afs_list]
            self.log.info("Successfully inserted afs_list %s for job id - %s", str(job_af_dict[int(job_obj.job_id)]),
                                                                                   job_obj.job_id)

        return  job_af_dict

    def compute_deletion_candidates(self, job_af_dict):
        """
        Compute the list of jobs to be deleted and corresponding AFs and Chunks
        Args:
            job_af_dict (dict)      --  Dictionary containing Jobs as key and AFs as Values

        Return:
            List of Jobs to be deleted
            List of AFs to be deleted
            List of chunks to be deleted
        """
        job_list = []
        tobe_deleted_afs = []
        for key in job_af_dict.keys():
            job_list.append(key)
        #sort the list and take last 2
        job_list.sort()
        #Delete last 2 jobs
        if len(job_list) < 2:
            self.log.error("Too few jobs were run for testing this feature")
            raise Exception("Not even 2 jobs were run on this store - failing the test case")
        tobe_deleted_jobs = job_list[-2:]
        #get AFs corresponding to deletion candidate jobs
        for af in job_af_dict[tobe_deleted_jobs[0]]:
            tobe_deleted_afs.append(af)
        for af in job_af_dict[tobe_deleted_jobs[1]]:
            tobe_deleted_afs.append(af)
        tobe_deleted_afs = self.get_afs_common_in_csdb_ddb(tobe_deleted_afs, self.engineid, 0)

        af_list_str = [str(af) for af in tobe_deleted_afs]
        #get chunks correspondingt to deletion candidate jobs
        query = "select archchunkid from archchunkmapping where archfileid in (%s)"%(','.join(af_list_str))
        self.log.info("Query: %s", query)
        self.csdb.execute(query)
        all_chunks = self.csdb.fetch_all_rows()
        self.log.info(all_chunks)
        tobe_deleted_chunks = [ int(x[0]) for x in all_chunks]

        self.log.info("tobe_deleted_jobs = %s \n tobe_deleted_afs = %s \n tobe_deleted_chunks = %s",
                      tobe_deleted_jobs, tobe_deleted_afs, tobe_deleted_chunks)
        return tobe_deleted_jobs, tobe_deleted_afs, tobe_deleted_chunks


    def get_afs_common_in_csdb_ddb(self, list_of_afs, engine_id, group):
        """
        Checks if given list of archive files is present in sidb listaf output for given engine id / partition pair

        Args:
            list_of_afs (list)      -   List of Archive Files whose presence is to be checked in sidb listaf output
            engine_id   (int)       -   SIDB Engine ID
            group   (int)           -   group id [ 0 , 1 and so on ]

        Returns:
            List of AFs which match in both CSDB and DDB
        """
        #wait till ddb partition is down
        sidb_afid_match_list = []
        self.dedup_obj.wait_till_sidb_down(str(engine_id), self.ma_machineobj.client_object, group)
        listaf_output = self.dedup_obj.execute_sidb_command("listaf", engine_id, group,
                                                            self.ma_machineobj.client_object)
        self.log.info("SIDB ListAF Output => %s", listaf_output[1])
        #Output for reference
        #AfId[623555], Primary[0], Secondary[560], Deleted[0]
        #AfId[623556], Primary[0], Secondary[480], Deleted[0]
        output_lines = listaf_output[1].split('\n')
        sidb_afid_list = []
        for line in output_lines:
            if line.startswith('AfId'):
                sidb_afid_list.append(int(line.split(',')[0].split('[')[1].strip(']')))

        self.log.warning("Picking only those AFS as deletion candidates which are both in SIDB and CSDB")
        sidb_afid_match_list = list(set(sidb_afid_list) & set(list_of_afs))

        self.log.info("AFs which are both in SIDB and CSDB are => %s", str(sidb_afid_match_list))
        return sidb_afid_match_list

    def delete_jobs(self, job_list, data_aging_iterations = 1):
        """
        Delete the jobs in job_list and run data aging.

        Args:
            job_list                (list)  -   List of jobs to be deleted
            data_aging_iterations   (int)   -   How many times data aging job should be run

        """
        for delete_job in job_list:
            self.log.info('Deleting backup job [%s]', delete_job)
            self.sp_copy_obj.delete_job(str(delete_job))
        for _ in range(0, data_aging_iterations):
            data_aging_job = self.commcell.run_data_aging('Primary', self.storage_policy_name)
            self.log.info("data aging job: %s", data_aging_job.job_id)
            if not data_aging_job.wait_for_completion():
                self.log.info("Failed to run data aging with error: %s", data_aging_job.delay_reason)
            time.sleep((self.prune_process_interval + 1) * 60)

    def change_store_pruning_value(self, ddb_store_obj, enable=True):
        """
        Enable / Disable Pruning on Store

        Args:
            ddb_store_obj (obj) -   Store object representing the DDB on which operation is to be performed
            enable  (boolean)   -   Enable or Disable pruning on store
        """
        self.log.info("Setting Pruning on Store %s to --> %s", ddb_store_obj.store_id, enable)
        ddb_store_obj.enable_store_pruning = enable



    def check_deleted_entries_in_table(self, table, column, list_of_entries, retry_limit=1):
        """
        Checks that all ArchFile & ArchChunk entries from the given lists are absent

        Args:
            table               (str)       --  Table on which to perform
            column              (str)       --  Which column to look up list_of_entries for while deletion
            list_of_entities    (list)      --  List of entities to be removed from Table
            retry_limit         (int)       --  Number of retries to be done every mm prune process interval minute

        Returns:
            None
            Raises exception if entries are still present after retrying
        """
        for i in range(0, retry_limit):
            self.log.info("Check %s table for entries - %s", table, str(list_of_entries))
            query = "select * from %s where %s in (%s)"%(table, column,  ','.join([str(x) for x in list_of_entries]))
            self.log.info("QUERY : %s", query)
            self.csdb.execute(query)
            query_output = self.csdb.fetch_all_rows()
            self.log.info("QUERY OUTPUT ==> %s", str(query_output))
            if query_output[0][0] != '':
                self.log.error("Non-Empty output found : %s", str(query_output[0][0]))
                if i+1 == retry_limit:
                    raise Exception("%s Table is not empty even after reaching retry limit."%table)
                else:
                    self.log.warning("Sleeping for %s minutes and checking %s table again",
                                     self.prune_process_interval, table)
                    time.sleep(60*self.prune_process_interval)
            else:
                self.log.error("Empty output found : %s", str(query_output[0][0]))
                break

    def delete_af_entries(self, table, af_list):
        """"
        Delete AF list from table provided
        Args:
            table       (str)       --      Name of the SQL table
            af_list     (list)      --      List of AFs

        """
        self.log.info("Deleting %s from table - %s", str(af_list), table)
        query = "Delete from %s where archfileid in (%s)"%(table, ','.join([str(x) for x in af_list]))
        self.log.info("QUERY : %s", query)
        self.mmhelper_obj.execute_update_query(query, self.sql_password, "sqladmin_cv")

    def run_space_reclamation_job_check_resync(self):
        """
        Runs space reclamation job on DDB Store and check if stores are marked for resync
        """
        self.log.info("Starting Space Reclamation Job")
        job_obj = self.sp_obj.run_ddb_verification("Primary", "Full", "DDB_DEFRAGMENTATION")
        self.log.info("Check resync flag when job enters Defrag Phase")

        attempts = 600
        self.log.info("Checking at 1 second interval if Space Reclamation job has entered given phase")
        while attempts > 0:
            job_phase = job_obj.phase
            # self.log.info("Job Phase - {job_phase}")
            if job_phase.lower() == "defragment data":
                self.log.info("Job has entered the required Defragment Data phase. Suspending the job.")
                break
            else:
                time.sleep(1)
                attempts -= 1

        if attempts <= 0:
            self.log.error("Space Reclamation job did not enter desired phase even after 10 minutes. Raising Exception")
            raise Exception(
                f"Space Reclamation Job {job_obj.job_id} did not enter desired phase even after 10 minutes")
        else:
            self.log.info("Verifying the presence of Resync Flag after 10 seconds")
            time.sleep(10)
            if not self.dedup_obj.is_ddb_flag_set(self.ddb_store_obj, 'IDX_SIDBSTORE_FLAGS_DDB_NEEDS_AUTO_RESYNC'):
                raise Exception("Store is not marked for Resync after launching Space Reclamtion Job.")
            else:
                self.log.info("DDB Store %s is marked for resync", self.engineid)
        job_obj.wait_for_completion()

    def wait_for_resync_completion(self, timeout_mins=15):
        """
        wait until resync bit gets cleared from the store

        Args:
            timeout_mins (int)     --  Timeout after which exception will be raised if store is still in Resync mode
        """
        timeout = timeout_mins
        while timeout_mins > 0:
            if self.dedup_obj.is_ddb_flag_set(self.ddb_store_obj, 'IDX_SIDBSTORE_FLAGS_DDB_NEEDS_AUTO_RESYNC'):
                self.log.info("DDB store %s is still marked for resync ...", self.engineid)
                self.log.info("Checking after 2 minutes")
                time.sleep(120)
                timeout_mins -= 2
            else:
                self.log.info("DDB Store %s is not marked for resync ...", self.engineid)
                return True

        raise Exception("DDB Store %s has not been resynced even after %s minutes"%(self.engineid, timeout))

    def verify_idxsidb_resync_history(self, expected_num_afids):
        """
        Verify that IdxSIDBResyncHistory has a row for DDB store with correct reason

        Args:
            expected_num_afids  (int)   --  Expected number of AFIDs in NumResyncedAFIDs column

        """
        failure = False
        query = "select top 1 * from IdxSIDBResyncHistory where sidbstoreid=%s order by addedtime desc"%self.engineid
        self.log.info("QUERY : %s", query)
        self.csdb.execute(query)
        resync_row = self.csdb.fetch_one_row()
        self.log.info("RESYNC ROW ==> %s", resync_row)
        #Example
        #SIDBStoreId	CommcellId	MaintenanceTime	ResyncFlags	AttemptNo	MaintenanceReason	MaintenanceReasonDesc
        #368 2	1616052775	1	1	9	Archive file validation is in progress. Invalid archive files will be pruned.
        if resync_row[0] == '':
            self.log.error("No rows returned by the query .. Returning failure ..")
            return not failure

        if int(resync_row[8]) == 0:
            self.log.info("Successfully verified completion of Resync as Status = 0")
        else:
            self.log.error("Resync process did not complete successfully as Status = %s", resync_row[8])
            failure = True

        if int(resync_row[3]) == 1:
            self.log.info("Successfully verified ResyncFlags = 1")
        else:
            self.log.error("ResyncFlags value is not correct : Expected = 1 Actual = %s", resync_row[3])
            failure = True

        if int(resync_row[5]) == 9:
            self.log.info("Successfully verified MaintenanceReason = 9")
        else:
            self.log.error("MaintenanceReason value is not correct : Expected = 9 Actual = %s", resync_row[5])
            failure = True

        if int(resync_row[9]) == expected_num_afids:
            self.log.info("Successfully verified NumResyncedAFIDs column value to be : %s", expected_num_afids)
        else:
            self.log.error("NumResyncedAFIDs value is not correct : Expected = %s Actual = %s",
                           expected_num_afids, resync_row[9])
            failure = True

        return not failure

    def previous_run_cleanup(self):
        """
        Cleanup entities created in previous run

        """
        if self.agent.backupsets.has_backupset(self.backupset_name):
            self.log.info("Deleting backupset %s", self.backupset_name)
            self.agent.backupsets.delete(self.backupset_name)
        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.log.info("Deleting storage policy  %s", self.storage_policy_name)
            self.commcell.storage_policies.delete(self.storage_policy_name)
        if self.commcell.disk_libraries.has_library(self.library_name):
            self.log.info("Deleting library %s", self.library_name)
            self.commcell.disk_libraries.delete(self.library_name)
        if self.machineobj.check_directory_exists(self.content_path):
            self.machineobj.remove_directory(self.content_path)


    def run(self):
        """Run function of this test case"""
        try:
            # Cleanup previous TC environment - let TC fail if cleanup fails
            # This is because correct NumResyncedAFID calculation won't be possible if TC reuses stale DDB
            self.previous_run_cleanup()

            # Create TC environment
            self.create_tc_env()

            #Run 5 backups - each with 500 MB data
            job_af_mapping = self.run_backup_jobs("Incremental", 5)
            #Compute ArchFile & Chunks for jobs to be deleted  using CSDB
            self.ddb_store_obj  = self.dedup_obj.get_ddb_mapping_for_subclient(self.subclient_obj.subclient_id,
                                                                               self.storage_policy_name, "Primary")
            self.engineid = self.ddb_store_obj.store_id

            tobe_deleted_jobs, tobe_deleted_afs, tobe_deleted_chunks = self.compute_deletion_candidates(job_af_mapping)

            #Check if these ArchFiles are present in DDB. Consider only those ArchFiles which are in DDB for further
            #processing


            #Disable Pruning on DDB Store. Set MM Prune Process Interval Mins = 5 mins
            self.mmhelper_obj.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES',
                                                    self.maintenance_interval, self.maintenance_interval)
            self.mmhelper_obj.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS',
                                                    self.prune_process_interval, self.prune_process_interval)

            self.change_store_pruning_value(self.ddb_store_obj, False)
            #Delete 2 Jobs and run Data Aging 2 times
            self.delete_jobs(tobe_deleted_jobs, 2)

            #Check if ArchFile, ArchChunkMapping , ArchChunk have no entries for these ArchFiles/chunks
            self.check_deleted_entries_in_table('ArchFile', "id", tobe_deleted_afs,2)
            self.check_deleted_entries_in_table('ArchFileCopyDedup', "archfileid",  tobe_deleted_afs,2)
            self.check_deleted_entries_in_table('ArchChunk', "id", tobe_deleted_chunks,2)

            #Check if MMDeletedAF has those entries - Delete those entries
            self.delete_af_entries('MMDeletedAF', tobe_deleted_afs)
            #Check if MMDeletedArchFileTracking has those entries - Delete those entries
            self.delete_af_entries('MMDeletedArchFileTracking', tobe_deleted_afs)
            #Check if ArchFile, ArchChunkMapping, ArchChunk, MMDeletedAF and MMDeletedArchFileTracking tables have
            # no entries
            self.check_deleted_entries_in_table('ArchFile', "id", tobe_deleted_afs, 2)
            self.check_deleted_entries_in_table('ArchFileCopyDedup', "archfileid", tobe_deleted_afs, 2)
            self.check_deleted_entries_in_table('ArchChunk', "id", tobe_deleted_chunks, 2)
            self.check_deleted_entries_in_table('MMDeletedAF', "archfileid", tobe_deleted_afs, 2)
            self.check_deleted_entries_in_table('MMDeletedArchFileTracking', "archfileid", tobe_deleted_afs, 2)

            #Run Space Reclamation
            #TODO: We don't expect this TC to run for < SP22. If it comes to that, Update the CSDB table manually.
            #Check that store has got marked for Resync
            #Wait for Space Reclamation to Finish
            self.change_store_pruning_value(self.ddb_store_obj, True)
            self.run_space_reclamation_job_check_resync()

            #Sleep for at least 8 minutes
            self.wait_for_resync_completion()

            #Check if IdxSIDBResyncHistory has required row
            csdb_status = self.verify_idxsidb_resync_history(len(tobe_deleted_afs))
            #Check if DDB has these ArchFiles - those should not be present
            sidb_status = self.get_afs_common_in_csdb_ddb(tobe_deleted_afs, self.engineid, 0)
            failure = False
            if csdb_status:
                self.log.info("IdxSIDBResyncHistory table verification successful.")
            else:
                self.log.error("IdxSIDBResyncHistory table verification failed.")
                failure = True

            if sidb_status==[]:
                self.log.info("SIDB ListAF output verification successful.")
            else:
                self.log.info("SIDB ListAF output verification failed.")
                failure = True

            if failure:
                raise Exception("Testcase failed at verification phase.")
            else:
                self.log.info("Test case completed successfully.")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info("In tear down method ...")

        try:
            self.previous_run_cleanup()
        except Exception as exp:
            self.log.info("Cleanup failed even after successful execution - %s", str(exp))
