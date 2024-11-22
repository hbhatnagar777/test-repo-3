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
    __init__()                              --  initialize TestCase class

    setup()                                 --  setup function of this test case

    run()                                   --  run function of this test case

    tear_down()                             --  tear down function of this test case

    configure_tc_environment()              -- Configure testcase environment

    modify_subclient_properties()           --  Modify subclient properties like number of streams

    generate_data_run_backup()              --  Generate subclient content and run given type of backup on subclient

    clean_test_environment()		    --  Clean up test environment

    get_last_access_time_and_primaryid()    --	Finds values in LastAccessTime and PrimaryID column in each partition

    set_last_access_time_and_primaryid()    --	Sets values in LastAccessTime and PrimaryID column for each partition

    get_ddb_subc_association()              --  Get DDB Engine associated to a specific subclient id for a specific
                                                copy id

    sidb_stats()                            --	Execute sidb2 stats command and get output

    validate_ma_resync()                    --  Validate that MA side resync has added a Resync Range to DDB

    verify_resync_history()                 --  Check that there are no rows in IdxSIDBResyncHistory table for the DDB

    validate_ma_resync_failure()            --  Validate error messages in SIDBEngine Logs after MA resync failure
                                                due to > 5 days old CSDB timestamp

    run_and_verify_pending_backup()         --  Run backup job when DDB is in inconsistent state and make sure that
                                                backup fails

Steps :
    Expected Input :
    		"59597":{
    		        "ClientName": "client name",
					"AgentName": "File System",
					"MediaAgentName": "ma name"}

"""
import re, time
import shutil
from cvpysdk import deduplication_engines
from AutomationUtils import constants
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
        self.name = "DDB Resync - MA Side AutoResync after timestamp mismatch"
        self.tcinputs = {
            "MediaAgentName": None,
        }
        self.library_name = None
        self.mountpath = None
        self.ma_name = None
        self.storage_policy_name = None
        self.storage_policy_obj = None
        self.backupset_name = None
        self.subclient_name = None
        self.mahelper_obj = None
        self.client_machine_obj = None
        self.ma_machine_obj = None
        self.ma_library_drive = None
        self.dedup_path = None
        self.content_path = None
        self.subclient_obj = None
        self.bkpset_obj = None
        self.sp_obj = None
        self.store_obj = None
        self.client_system_drive = None
        self.dedup_helper_obj = None
        self.backup_job_list = []
        self.volumes_list = []
        self.volume_physical_size_dict = {}
        self.mm_admin_thread = None
        self.volume_update_interval = None
        self.user_lib = False
        self.user_sp = False
        self.restore_path = None
        self.cleanup_job_obj = None
        self.optionobj = None

    def setup(self):
        """Setup function of this test case"""
        self.optionobj = OptionsSelector(self.commcell)
        self.ma_name = self.tcinputs['MediaAgentName']
        timestamp_suffix = OptionsSelector.get_custom_str()

        self.client_machine_obj = Machine(self.client)
        self.client_system_drive = self.optionobj.get_drive(self.client_machine_obj, 15)
        self.ma_machine_obj = Machine(self.ma_name, self.commcell)
        self.ma_library_drive = self.optionobj.get_drive(self.ma_machine_obj, 15)

        self.library_name = "Lib_TC_%s"%self.id
        self.mountpath = self.ma_machine_obj.join_path(self.ma_library_drive, self.id)


        self.storage_policy_name = "SP_TC_%s"%self.id
        self.dedup_path = self.ma_machine_obj.join_path(self.ma_library_drive, "DDBs",
                                                        "TC%s_%s" % (self.id, timestamp_suffix))
        self.backupset_name = "BkpSet_TC_%s"%self.id
        self.subclient_name = "Subc_TC_%s"%self.id
        self.content_path = self.client_machine_obj.join_path(self.client_system_drive, self.id)
        self.restore_path = "%s_%s"%(self.content_path, "restored")

    def verify_resync_history(self, engine_id):
        """
        Check that there are no rows in IdxSIDBResyncHistory table for the DDB
        Args:
            engine_id (int) -   DDB Engine ID
        Returns:
            True if there are no rows in IdxSIDBResyncHistory table for the DDB , False otherwise
        """
        query = "select * from idxsidbresynchistory where sidbstoreid=%s " % engine_id
        self.log.info("Query ==> %s", query)
        self.csdb.execute(query)
        resync_history = self.csdb.fetch_all_rows()
        if resync_history[0] == ['']:
            self.log.info("No Resync History row found for SIDB %s as expected"%engine_id)
            return True
        else:
            self.log.info("Resync History row found for SIDB %s which is not expected"%engine_id)
            self.log.info(str(resync_history))
            return False

    def configure_tc_environment(self):
        """
        Configure testcase environment - library (if required), storage policy, backupset, subclient
        """
        self.log.info("===STEP: Configuring TC Environment===")
        self.mahelper_obj = MMHelper(self)
        self.dedup_helper_obj = DedupeHelper(self)
        if self.client_machine_obj.check_directory_exists(self.content_path):
            self.log.info("Deleting already existing content directory [%s]", self.content_path)
            self.client_machine_obj.remove_directory(self.content_path)
        self.client_machine_obj.create_directory(self.content_path)

        if not self.user_lib and not self.user_sp:
            if not self.ma_machine_obj.check_directory_exists(self.mountpath):
                self.log.info("Creating mountpath directory [%s]", self.mountpath)
                self.ma_machine_obj.create_directory(self.mountpath)
            self.log.info("Creating Library [%s]", self.library_name)
            if self.commcell.disk_libraries.has_library(self.library_name):
                self.log.info("Library [%s] already exists. Reusing the Library.", self.library_name)
            else:
                self.mahelper_obj.configure_disk_library(self.library_name, self.ma_name, self.mountpath)
                self.log.info("Library [%s] created successfully.", self.library_name)
                #Reset flag 128 on the library & set DedupeDrillHoles to 0 on MA
        else:
            if self.user_lib:
                self.log.info("Skipping Library creation as user has provided Library [%s]", self.library_name)
                self.log.info("Checking if user provided Library exists")
                if not self.commcell.disk_libraries.has_library(self.library_name):
                    self.log.error("User Provided Library does not exist. Erroring out.")
                    raise Exception(f"User Provided Library [{self.library_name}] does not exist. "
                                    f"Please provide correct library name")

        self.log.info("Configuring Storage Policy [%s]", self.storage_policy_name)
        self.sp_obj = self.dedup_helper_obj.configure_dedupe_storage_policy(
            self.storage_policy_name, self.library_name, self.ma_name, self.dedup_path)
        self.log.info("Successfully configured Storage Policy [%s]", self.storage_policy_name)

        #TODO : Add a Partition to make it multi-partition Dedup Policy
        dedup_engines_obj = deduplication_engines.DeduplicationEngines(self.commcell)
        if dedup_engines_obj.has_engine(self.storage_policy_name, 'Primary'):
            dedup_engine_obj = dedup_engines_obj.get(self.storage_policy_name, 'Primary')
            dedup_stores_list = dedup_engine_obj.all_stores
            for dedup_store in dedup_stores_list:
                self.store_obj = dedup_engine_obj.get(dedup_store[0])
                self.log.info("Disabling Garbage Collection on DDB Store == %s", dedup_store[0])
                self.store_obj.enable_garbage_collection = False


        self.log.info("Configuring Backupset [%s]", self.backupset_name)
        self.bkpset_obj = self.mahelper_obj.configure_backupset(self.backupset_name)
        self.log.info("Successfully configured Backupset [%s]", self.backupset_name)

        self.log.info("Configuring Subclient [%s]", self.subclient_name)
        self.subclient_obj = self.mahelper_obj.configure_subclient(self.backupset_name, self.subclient_name,
                                                                   self.storage_policy_name, self.content_path)
        self.log.info("Successfully configured Subclient [%s]", self.subclient_name)

        self.log.info("Setting Number of Streams to 10 and Allow Multiple Data Readers to True")
        self.modify_subclient_properties(10, True)


    def modify_subclient_properties(self, num_streams=None, multiple_readers=None):
        """
        Modify subclient properties like number of streams and allow multiple data readers

        Args:
            num_streams (int) - Number of streams
            multiple_readers(boolean) - Boolean value for setting multiple data readers value

        """
        if num_streams is not None:
            self.log.info("Setting number of streams to [%s]", num_streams)
            self.subclient_obj.data_readers = num_streams
        if multiple_readers is not None:
            self.log.info("Setting multiple data readers to [%s]", multiple_readers)
            self.subclient_obj.allow_multiple_readers = multiple_readers

    def generate_data_run_backup(self, size_in_gb, backup_type="Incremental", copy_data=False, copy_from_dir=""):
        """
            Generate subclient content and run given type of backup on subclient
        Args:
            size_in_gb (int)      -- Content Size in GB
            backup_type (str)     -- Backup Type [ Full or Incremental etc. ]
            mark_media_full(bool) -- Boolean Flag to decide if volumes are to be marked full after backup completion
            generate_data (bool)  -- Boolean Flag to decide if new data to be generated  or existing data to be copied
        Return:
            Returns content dir for job
        """
        self.log.info("Generating content of size [%s] at location [%s]", size_in_gb, self.content_path)
        content_dir = ""
        if not copy_data:
            content_dir = "%s%s%s" % (self.content_path, self.client_machine_obj.os_sep, size_in_gb)
            if size_in_gb:
                self.mahelper_obj.create_uncompressable_data(self.client.client_name, content_dir, size_in_gb)
        else:
            target_content_dir = "%s_%s"%(copy_from_dir, "_copied")
            self.client_machine_obj.create_directory(target_content_dir)
            self.log.info("Generatig duplicate content by copying from - %s", copy_from_dir)
            files_list = self.client_machine_obj.get_items_list(copy_from_dir)
            for file_num in range(len(files_list)):
                if file_num%2:
                    file_to_copy = files_list[file_num]
                    shutil.copyfile(file_to_copy, "%s%s%s"%(target_content_dir, self.client_machine_obj.os_sep,
                                                            file_to_copy.split(self.client_machine_obj.os_sep)[-1]))
            content_dir = target_content_dir


        job_obj = self.subclient_obj.backup(backup_type)

        self.log.info("Successfully initiated a [%s] backup job on subclient with jobid [%s]", backup_type,
                      job_obj.job_id)
        if not job_obj.wait_for_completion():
            self.log.warning("Killing job as it has not completed in given timeout. Reason - [%s]", job_obj.delay_reason)
            raise Exception(f"Backup job{job_obj.job_id} did not complete in given timeout - "
                            f"Reason [{job_obj.delay_reason}]")

        self.log.info("Successfully completed the backup job with jobid [%s]", job_obj.job_id)
        self.backup_job_list.append(job_obj)
        return content_dir

    def clean_test_environment(self):
        """
        Clean up test environment
        """
        try:
            self.log.info("Killing backup jobs if any")
            if self.cleanup_job_obj:
                self.log.info("Killing job - [%s]", self.cleanup_job_obj.job_id)
                self.cleanup_job_obj.kill(True)
        except:
            self.log.warning("Failed to cleanup job - [%s]. Please manually kill the job", self.cleanup_job_obj.job_id)
        try:
            self.log.info("Deleting BackupSet")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
        except Exception as excp:
            self.log.info("***Failure in deleting backupset during cleanup. "
                          "Treating as soft failure as backupset will be reused***")
        try:
            if not self.user_sp:
                self.log.info("Deleting Storage Policy")
                if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                    self.commcell.storage_policies.delete(self.storage_policy_name)
            else:
                self.log.info("Keeping storage policy intact as it was a user provided storage policy")
        except Exception as excp:
            self.log.info("***Failure in deleting storage policy during cleanup. "
                          "Treating as soft failure as stroage policy will be reused***")
        try:
            if not self.user_lib:
                self.log.info("Deleting Library")
                if self.commcell.disk_libraries.has_library(self.library_name):
                    self.commcell.disk_libraries.delete(self.library_name)
            else:
                self.log.info("Keeping library intact as it was a user provided library")
        except Exception as excp:
            self.log.info("***Failure in deleting library during cleanup. "
                          "Treating as soft failure as library will be reused***")

        if self.client_machine_obj.check_directory_exists(self.content_path):
            self.client_machine_obj.remove_directory(self.content_path)
            self.log.info("Deleted the Content Directory.")
        else:
            self.log.info("Content directory does not exist.")

        if self.client_machine_obj.check_directory_exists(self.restore_path):
            self.client_machine_obj.remove_directory(self.restore_path)
            self.log.info("Deleted the Restore Directory.")
        else:
            self.log.info("Restore directory does not exist.")

    def get_last_access_time_and_primaryid(self, engine_id):
        """
            Finds values in LastAccessTime and PrimaryID column in each partition and returns a dictionary
            with following format
            substoreid : { lastaccesstime : <value>, primaryid : <value>}

            Args:
                engine_id (int) : SIDB Engine ID whose information needs to be fetched
        """

        query = "select substoreid, lastaccesstime, primaryid from idxsidbsubstore " \
                "where sidbstoreid=%s order by substoreid"%engine_id
        self.log.info("Query ==> %s", query)
        self.csdb.execute(query)
        substore_mapping = self.csdb.fetch_all_rows()
        self.log.info(substore_mapping)
        substore_info_dict = {}
        for substore_info in substore_mapping:
            substore_info_dict[int(substore_info[0])] = {'LastAccessTime':substore_info[1],
                                                         'PrimaryId':substore_info[2]}
            self.log.info("SubstoreId : %s LastAccessTime : %s PrimaryId : %s",
                          substore_info[0], substore_info[1], substore_info[2])
        return substore_info_dict

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
            query = "update idxsidbsubstore set PrimaryId = %s, LastAccessTime = %s where substoreid=%s"%\
                    (primaryid, last_access_time, key)
            self.log.info("QUERY : %s", query)
            self.optionobj.update_commserve_db(query)
        self.log.info("Successfully set the values for PrimaryId and LastAccessTime for substores")

    def get_ddb_subc_association(self, subc_id, sp_copy_id):
        """
        Get DDB Engine associated to a specific subclient id for a specific copy id

        Args:
            subc_id     (int)   --  subclient id
            sp_copy_id  (int)   --  storage policy copy id


        Returns:
            An integer which is the sidb store id associated with the given subclient on given copy
        """
        query = "select sidbstoreid from archsubclientcopyddbmap where appid=%s and " \
                " copyid=%s"%(subc_id, sp_copy_id)
        self.log.info("Query ==> %s", query)
        self.csdb.execute(query)
        sidb_engine_id = self.csdb.fetch_one_row()[0]
        self.log.info(sidb_engine_id)
        return int(sidb_engine_id)

    def sidb_stats(self, operation, engineid, groupnumber, ddbma_machine_object, output_file=None):
        """Execute sidb2 stats command and get output

        Args:
            operation (str)     -- sidb2 command option like compact or reindx or validate

            engineid (int)      -- sidbstore id

            groupnumber (int)   -- sidb partition number ( eg. single partition
                                    ddb has partition0 where as double partition ddb has
                                    partition0 and partition1)

            ddbmaobject (Client or String) -- Machine object for DDB MA or Client Name

            output_file (str)   -- output file to which command output will be redirected

        Returns:
            String - output of command execution
        """
        self.dedup_helper_obj.wait_till_sidb_down(str(engineid), self.commcell.clients.get(self.ma_name), timeout=600)
        ddbma_clientobj = ddbma_machine_object.client_object

        basedir = "%s%sBase%s"%(ddbma_clientobj.install_directory, ddbma_machine_object.os_sep,
                                ddbma_machine_object.os_sep)
        sidb2cmd = "\"%ssidb2\""%(basedir)
        command = ""
        # If WIN MA, enclose in double quotes
        if ddbma_clientobj.os_info.lower().count('windows') > 0:
            command = "%s -%s  -i %s -split %s"%(sidb2cmd, operation, engineid, groupnumber)
        if ddbma_clientobj.os_info.lower().count('linux') > 0:
            # If LINUX MA, use stdbuf -o0
            command = "stdbuf -o0 %s %s -i %s -split %s"%(sidb2cmd, operation, engineid, groupnumber)

        if output_file:
            command = "%s %s"%(command, output_file)
        self._log.info(command)
        ddbma_clientobj.execute_command(command)

        if ddbma_machine_object.check_file_exists(output_file):
            stats_output = ddbma_machine_object.read_file(output_file)
            # delete the temporary file
            ddbma_machine_object.delete_file(output_file)
        else:
            self.log.error("Unable to find output file for SIDB Stats")
            raise Exception(f"Unable to find SIDB stats output file {output_file} on client "
                            f"{ddbma_clientobj.client_name}")

        self.log.info("***************SIDB STATS OUTPUT***************")
        self.log.info(stats_output)

        return stats_output

    def validate_ma_resync(self, engine_id, primaryid_accesstime_before, primaryid_accesstime_after):
        """
        Validate that MA side resync has added a Resync Range to DDB by parsing SIDB stats output

        Args:
            engine_id                   (int)   --  SIDB Engine ID
            primaryid_accesstime_before (dict)  --  Dictionary containing substore ID with corresponding PrimaryID &
                                                    LastAccessTime captured before introducing timestamp mismatch

            primaryid_accesstime_after  (dict)  --  Dictionary containing substore ID with corresponding PrimaryID &
                                                    LastAccessTime captured after introducing timestamp mismatch

        Returns:
           FailureString which is empty if SIDB stats output has correct resync range, or error otherwise
        """

        failure_string = ""
        partition_id = 0
        for partition, info in primaryid_accesstime_before.items():
            primary_id_before = info['PrimaryId']
            primary_id_after  = int(primaryid_accesstime_after[partition]['PrimaryId'])-1

            output_file = self.ma_machine_obj.join_path("%s%s"%(self.ma_library_drive,
                                                      "%s_%s_%s.csv"%(engine_id, partition, primary_id_before)))


            self.log.info("Going to match following resync range in sidb2 stats for EngineId ==> %s Partition ==> %s"
                          "ResyncRange_\\d+\\s+,\\s+,%s\\s+,\\s+%s",engine_id, partition, primary_id_before,
                                                                     primary_id_after)
            stats_output = self.sidb_stats("dump stats", engine_id, partition_id, self.ma_machine_obj, output_file)

            match = re.compile("ResyncRange_\\d+\\s+,\\s+," + str(primary_id_before) +
                               "\\s+,\\s+" + str(primary_id_after))
            resyncvalidation = match.findall(stats_output)
            if resyncvalidation == []:
                self.log.error("Failed to match the resync range in output ==> "
                               "ResyncRange_\\d+\\s+,\\s+,%s\\s+,\\s+%s", primary_id_before, primary_id_after)
                raise Exception(f"Failed to match the resync range for engineid {engine_id} in output"  )
            else:
                self.log.info("Successfully matched the resync range in output %s", resyncvalidation)
            partition_id+=1
        return failure_string

    def validate_ma_resync_failure(self, engine_id):
        """Validate error messages in SIDBEngine Logs after MA resync failure due to > 5 days old CSDB timestamp

        Args:
                engine_id (int)     --  Engine ID for which logs need to be parsed
        Returns:
                True / False based on whether log parsing was successful
        """
        log_lines = ["Sanity check failed. Last open time does not match up.",
                     "Mismatch in last open time [10.000000 days] is greater than allowed [5 days]. Skipping resync." ]
        engine_filter = f"{engine_id}-0-"
        validation_status = True

        for log_line in log_lines:
            self.log.info("Verifying String - [ %s ]", log_line)
            matched_lines, matched_strings = self.dedup_helper_obj.parse_log(self.ma_name, "SIDBEngine.log", log_line)
            match_count = 0
            if matched_lines:
                for line in matched_lines:
                    if line.count(engine_filter):
                        self.log.info("***Successfully verified log line***")
                        self.log.info(line)
                        match_count += 1
                        validation_status &= True
                        break
                if match_count == 0:
                    validation_status &= False
            else:
                self.log.error("***Failed to Verify log line***")
                validation_status &= False

        if not validation_status:
            self.log.error("Failed to verify Sanity Check Failure logs in case of timestamp mismatch with CSDB < DDB "
                           "by more than 5 day")
            raise Exception("Failed to verify Sanity Check Failure logs in case of timestamp mismatch with CSDB < DDB "
                           "by more than 5 day")
        self.log.info("Successfully verified log line which suggest that DDB correctly entered Sanity Check Failed error"
                      " in case of timestamp mismatch with CSDB < DDB by more than 5 days")

    def run_and_verify_pending_backup(self):
        """
        Run backup job when DDB is in inconsistent state and make sure that backup fails

        """

        jpr = "Encountered a network error. Could not connect to the DDB process on the target"
        job_obj = self.subclient_obj.backup("FULL")
        self.cleanup_job_obj = job_obj
        timeout = 300
        while timeout > 0 and job_obj.phase.lower() != 'backup':
            self.log.info("Waiting for job [%s] to enter backup phase", job_obj.job_id)
            time.sleep(10)
            timeout -= 10

        if timeout > 0:
            self.log.info("Job [%s] is in backup phase", job_obj.job_id)
        else:
            self.log.info("Job [%s] did not enter backup phase", job_obj.job_id)
            raise Exception(f"Job [{job_obj.job_id}] did not enter backup phase")

        timeout=300
        self.log.info("Checking if job has entered Pending state")
        while timeout > 0 and job_obj.status.lower() != 'pending':
            self.log.info("Waiting for job [%s] to show status as pending. Current Job Status = %s", job_obj.job_id, job_obj.status.lower())
            time.sleep(10)
            timeout -= 10

        if timeout <= 0:
            self.log.info("Job [%s] has not gone pending", job_obj.job_id)
            raise Exception(f"Job [{job_obj.job_id}] has not gone Pending even after introducing MA side timestamp mismatch "
                            "with CSDB < DDB by great than 5 days" )

        self.log.info("Job [%s] has entered pending state. Checking JPR", job_obj.job_id)

        if job_obj.delay_reason.count(jpr):
            self.log.info("Successfully verified that Job [%s] is in pending state with correct JPR  after introducing "
                          "MA side timestamp mismatch with CSDB < DDB by greater than 5 days - [%s]",
                          job_obj.job_id, job_obj.delay_reason)
            self.log.info("Killing the job [%s] as verification is complete", job_obj.job_id)
            job_obj.kill(True)
        self.cleanup_job_obj = None

    def run(self):
        """Run function of this test case"""
        try:
            self.clean_test_environment()
            #STEP : Configure TC environment

            self.configure_tc_environment()
            self.log.info("============PHASE 1 : Run backups & query LastAccessTime1 and PrimaryID1 ============")
            #STEP : Run couple of Backups
            for i in range(0, 2):
                self.generate_data_run_backup(0.5)

            engine_id = self.get_ddb_subc_association(self.subclient_obj.subclient_id,
                                                      self.mahelper_obj.get_copy_id(self.storage_policy_name,
                                                                                    'Primary'))
            #STEP : Fetch Lastaccesstime for the partitions
            self.dedup_helper_obj.wait_till_sidb_down(str(engine_id), self.commcell.clients.get(self.ma_name),
                                                      timeout=600 )
            primaryid_accesstime_1 = self.get_last_access_time_and_primaryid(engine_id)

            self.log.info("============PHASE 2 : Run backups & query LastAccessTime2 and PrimaryID2 ============")
            #STEP : Run 1 Backup
            self.generate_data_run_backup(1)
            self.dedup_helper_obj.wait_till_sidb_down(str(engine_id), self.commcell.clients.get(self.ma_name),
                                                      timeout=600 )
            #STEP : Fetch Lastaccesstime for the partitions
            primaryid_accesstime_2 = self.get_last_access_time_and_primaryid(engine_id)
            primary_count_2  = int(self.dedup_helper_obj.get_primary_objects(self.backup_job_list[-1].job_id))
            self.log.info("Total Primary IDs added by job %s = %s", self.backup_job_list[-1].job_id, primary_count_2)

            #STEP : Set LastAccessTime = LastAccessTime1 and PrimaryID = PrimaryID1 for all partitions
            self.set_last_access_time_and_primaryid(primaryid_accesstime_1)
            #STEP : Run new backup for same data
            self.generate_data_run_backup(0, "FULL")
            primary_count_3  = int(self.dedup_helper_obj.get_primary_objects(self.backup_job_list[-1].job_id))
            self.log.info("Total Primary IDs added by job %s = %s",self.backup_job_list[-1].job_id, primary_count_3)

            self.log.info("============PHASE 3 : Validations============")

            #Validate that SIDB Stats output shows correct Resync Range
            failure_str = self.validate_ma_resync(engine_id, primaryid_accesstime_1, primaryid_accesstime_2)
            if failure_str != "":
                self.log.error("Resync range validation in SIDB failed with error")
                raise Exception(failure_str)

            #Validate that no rows got added in IdxSIDBResyncHistory table
            if not self.verify_resync_history(engine_id):
                self.log.error("MA side resync ended up adding IdxSIDBResyncHistory row for DDB Store %s", engine_id)
                raise Exception("IdxSIDBResyncHistory Validation Failed for DDB store %s", engine_id)

            #Check that new primary entries are added even when new backup job backs up same data
            #Validate that Primary Count in SecondLast job == Primary Count in last job
            if primary_count_3 == primary_count_2:
                self.log.info("Successfully verified that primary count added by FULL job is same as "
                              "previous Incremental --> So no dedup happened even though data was same")
            else:
                self.log.info("Primary count added by FULL job is not same as previous Incremental. Failing testcase")
                raise Exception(f"Primary Count [{primary_count_2}] by FULL Job is not same as "
                                f"Primary Count[{primary_count_3}] by last Incremental Job")

            #Restore the complete data and perform data validation

            restore_job = self.subclient_obj.restore_out_of_place(self.client.client_name,
                                                                  self.restore_path, [self.content_path])
            if restore_job.wait_for_completion():
                self.log.info('Restore Job: %s Completed', restore_job.job_id)
            else:
                raise Exception(f'Restore job [{restore_job.job_id}]Failed' )

            self.log.info('Validating Restored Data from Secondary Copy')
            difference = self.client_machine_obj.compare_folders(self.client_machine_obj,
                                                                 self.content_path, self.restore_path +
                                                                 self.client_machine_obj.os_sep +
                                                                 self.content_path.split(
                                                                     self.client_machine_obj.os_sep)[1] )
            if difference:
                raise Exception('Validating Data restored after Timestamp Mismatch Failed')


            #Check what happens when CSDB < DDB by more than 5 days
            self.log.info("Case : CSDB < DDB by more than 5 days")
            # STEP : Set LastAccessTime = LastAccessTime3 - 10 days and PrimaryID = PrimaryID3 for all partitions
            self.log.info("Setting LastAccessTime to Current Time - 10 days")
            primaryid_accesstime_3 = self.get_last_access_time_and_primaryid(engine_id)
            for (key, value) in primaryid_accesstime_3.items():
                new_accesstime = int(value['LastAccessTime']) - (86400*10)
                self.log.info(f"Changing LastAccessTime from {value['LastAccessTime']}"
                              f" to {new_accesstime}")
                primaryid_accesstime_3[key]['LastAccessTime'] = str(new_accesstime)

            self.set_last_access_time_and_primaryid(primaryid_accesstime_3)
            # STEP : Run new backup for same data
            self.run_and_verify_pending_backup()
            # STEP : Verify MA Side Resync Failure via log line validation
            self.validate_ma_resync_failure(engine_id)
            self.log.info('Validation Phase SUCCESS')
            self.log.info("SUCCESS : Test case completed successfully")
        except Exception as exp:
            self.status = constants.FAILED
            self.result_string = str(exp)
            self.log.error('Failed to execute test case with error: %s', (str(exp)))

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            self.log.info("Killing backup jobs if any")
            if self.cleanup_job_obj:
                self.log.info("Killing job - [%s]", self.cleanup_job_obj.job_id)
                self.cleanup_job_obj.kill(True)
                self.cleanup_job_obj = None
        except:
            self.log.warning("Failed to cleanup job - [%s]. Please manually kill the job", self.cleanup_job_obj.job_id)

        try:
            self.clean_test_environment()
        except Exception as ex:
            self.log.warning(f"Failed to clean up with error - {ex}")
            
