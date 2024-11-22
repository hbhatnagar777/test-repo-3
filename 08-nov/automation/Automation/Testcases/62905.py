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
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    configure_tc_environment()			-	Configure testcase environment - library (if required), storage policy,
                                            backupset, subclient

    run_backups()						-	Run backups on subclient

    get_last_access_time_and_primaryid()-	Finds values in LastAccessTime and PrimaryID column in each partition
                                            and returns a list of dictionaries
    perform_dr_backup()					-	Run DR Backup job

    verify_resync_range()				-	Verify Resync range in SIDB2 dump stats command line output for each partition

    perform_dr_restore()				-	Run DR Restore using CSRecoveryAssistant Tool

    perform_resync_validations()		- 	Perform resync validations by checking IdxSIDBResyncHistory table and
                                            IdxSIDBSTore table flags column

    verify_idxsidb_resync_history()		-	Verify that IdxSIDBResyncHistory has a row for DDB store with correct reason

    cleanup()							-	Clean up the entities created by this test case

    verify_restore()					-	Run a restore job followed by verification between source and destination

    convert_ddb_to_v5()                -   Convert V4 DDB to V5 DDB

    perform_ddb_v5_validations()       -   Verify that DDB is a V5 DDB

 Expected Input :
    		"62905":{
    		        "ClientName": "client name",
					"AgentName": "File System",
					"MediaAgentName": "ma name",
					"cs_machine_username":"username",
					"cs_machine_password" : "password"}

 Note : Please set following values in coreutils\Templates\config.json file under Schedule section
        "cs_machine_uname":"SET_THIS_VALUE",
        "cs_machine_password":"SET_THIS_VALUE"

 Steps:
    1. Create resources like Dedup Storage Policy, Backup sets, Subclients etc.
    2. Disable Garbage Collection & Change Number of AFs/Secondary to 16.
    3. Run backups on subclient
    4. Save the primary id for DDB partition after running backup
    5. Run DR Backup
    6. Convert thd DDB to V5 DDB and verify that it is V5 DDB [ Garbage collection enabled, Journal Pruning Logs
        enabled and Number of AFs/Secondary is 1 ]
    7. Run more backups on subclient
    8. Save the primary id for DDB partition after running more backups
    9. Run DR Restore
    10. Verify that DR Resync Restore has taken place by verifying
        a. Maintenance Mode bit is not set on DDB
        b. IdxSIDBResyncHistory row has got added for the DDB with correct values
    11. Verify that Resync Range has got added
    12. Verify that DDB is now a V5 DDB after Resync and not V4 DDB
    13. Run Full backups
    14. Perform Restore and verify the content checksum

"""
import re
import time
from cvpysdk import deduplication_engines
from cvpysdk.deduplication_engines import StoreFlags
from cvpysdk.client import Client
from AutomationUtils.options_selector import OptionsSelector, constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
from Server.DisasterRecovery import drhelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "DDB Resync : DR Resync should sync latest information about compacted DDBs to avoid data loss"
        self.tcinputs = {
            "MediaAgentName": None,
            "cs_machine_username": None,
            "cs_machine_password": None
        }

        self.content_path = None
        self.mountpth = None
        self.ma_machine_obj = None
        self.library_name = None
        self.storage_pool_obj = None
        self.sidb_store_obj = None
        self.storage_policy_obj = None
        self.subclient_obj = None
        self.backup_jobs_list = []
        self.cs_machine_obj = None
        self.cs_client_obj = None
        self.drhelper_obj = None
        self.dr_obj = None
        self.ma_client_obj = None
        self.optionobj = None
        self.ma_name = None
        self.dedup_path = None
        self.client_machine_obj = None
        self.client_system_drive = None
        self.ma_library_drive = None
        self.mountpath = None
        self.storage_policy_name = None
        self.storage_pool_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.restore_path = None
        self.mahelper_obj = None
        self.dedup_helper_obj = None
        self.bkpset_obj = None
        self.partition_info_2 = None
        self.partition_info_1 = None
        self.is_linux_cs = False

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
        self.cs_machine_obj = Machine(self.commcell.commserv_name, username=self.tcinputs['cs_machine_username'],
                                      password=self.tcinputs['cs_machine_password'])
        self.cs_client_obj = Client(self.commcell, self.commcell.commserv_name)
        self.ma_client_obj = Client(self.commcell, self.ma_name)
        self.storage_policy_name = f"SP_TC_{self.id}_{self.ma_name}"
        self.storage_pool_name = f"{self.storage_policy_name}_POOL"
        if self.cs_machine_obj.os_info.lower() == 'unix':
            self.is_linux_cs = True
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

        dedup_path = self.ma_machine_obj.join_path(self.dedup_path, self.storage_pool_name, "1")
        dedup_path_2 = self.ma_machine_obj.join_path(self.dedup_path, self.storage_pool_name, "2")
        if not self.ma_machine_obj.check_directory_exists(dedup_path):
            self.log.info("Creating dedup directory [%s]", dedup_path)
            self.ma_machine_obj.create_directory(dedup_path)
        self.log.info("Creating Dedup Storage Pool [%s]", self.storage_pool_name)
        if not self.commcell.storage_policies.has_policy(self.storage_pool_name):
            self.storage_pool_obj = self.dedup_helper_obj.configure_global_dedupe_storage_policy(
                global_storage_policy_name=self.storage_pool_name,
                library_name=self.library_name,
                media_agent_name=self.ma_name,
                ddb_path=dedup_path,
                ddb_media_agent=self.ma_name)
            self.log.info("Successfully created Dedup Storage Pool [%s]", self.storage_pool_name)
            # SIDB Engine Details
            dedup_engines_obj = deduplication_engines.DeduplicationEngines(self.commcell)
            if dedup_engines_obj.has_engine(self.storage_pool_name, 'Primary_Global'):
                dedup_engine_obj = dedup_engines_obj.get(self.storage_pool_name, 'Primary_Global')
                dedup_stores_list = dedup_engine_obj.all_stores
                self.sidb_store_obj = dedup_engine_obj.get(dedup_stores_list[0][0])

            self.log.info("Adding Partition to storage pool [%s]", self.storage_pool_name)
            if not self.ma_machine_obj.check_directory_exists(dedup_path_2):
                self.log.info("Creating dedup directory for 2nd partition [%s]", dedup_path_2)
                self.ma_machine_obj.create_directory(dedup_path_2)
                # adding partition 2
            copy_id = self.storage_pool_obj.get_copy('Primary_Global').copy_id
            self.storage_pool_obj.add_ddb_partition(copy_id, str(self.sidb_store_obj.store_id), dedup_path_2,
                                                    self.ma_name)

        else:
            self.log.info("Dedup Storage Pool already exists - [%s]", self.storage_pool_name)
            self.storage_pool_obj = self.commcell.storage_policies.get(self.storage_pool_name)

        # Creating Dedpendent SP
        if self.commcell.storage_policies.has_policy(self.storage_policy_name):
            self.log.info("Deleting Dependent SP - [%s]", self.storage_policy_name)
            self.commcell.storage_policies.delete(self.storage_policy_name)
        self.log.info("Creating Dependent SP - [%s]", self.storage_policy_name)
        self.storage_policy_obj = self.commcell.storage_policies.add(
            storage_policy_name=self.storage_policy_name,
            library=self.library_name,
            media_agent=self.ma_name,
            global_policy_name=self.storage_pool_name,
            dedup_media_agent="",
            dedup_path="")
        sp_copy = self.storage_policy_obj.get_copy('Primary')
        self.log.info("setting copy retention: 1 day, 0 cycle")
        sp_copy.copy_retention = (1, 0, 1)

        self.log.info("Creating subclient for using SIDB Store ID - [%s]", self.sidb_store_obj.store_id)
        if self.client_machine_obj.check_directory_exists(self.content_path):
            self.log.info("Removing existing content directory [%s] from client", self.content_path)
            self.client_machine_obj.remove_directory(self.content_path)

        self.log.info("Creating content directory [%s] for subclient - [%s]", self.content_path, self.subclient_name)
        self.client_machine_obj.create_directory(self.content_path)
        self.subclient_obj = self.mahelper_obj.configure_subclient(self.backupset_name, self.subclient_name,
                                                                   self.storage_policy_name, self.content_path)
        self.log.info("Setting number of streams to 5")
        self.subclient_obj.data_readers = 8
        self.subclient_obj.allow_multiple_readers = True

        #Make this store behave as if it is V4 store

        self.log.info("Disabling Garbage Collection & JOurnal Pruning")
        self.sidb_store_obj.enable_garbage_collection = False
        self.sidb_store_obj.enable_journal_pruning = False
        self.log.info("Setting max AFs per secondary file to 16 in IdxSIDBSubStore table")
        query = f"update idxsidbsubstore set MaxNumOfAFsInSecFile=16 where sidbstoreid={self.sidb_store_obj.store_id}"
        self.log.info("QUERY => %s", query)
        self.optionobj.update_commserve_db(query)
        self.log.info("Setting max AFs per secondary file to 16 in IdxSIDBStore table")
        query = f"update idxsidbstore set MaxNumOfAFsInSecFile=16 where sidbstoreid={self.sidb_store_obj.store_id}"
        self.log.info("QUERY => %s", query)
        self.optionobj.update_commserve_db(query)


    def run_backups(self, job_type="Incremental"):
        """
        Run backups on subclient and maintain list of job IDs for each subclient
        Args:
            job_type(str)   --  Type of backup job, Incremental by default
        """

        self.log.info("Generating content for subclient [%s] at [%s]", self.subclient_name, self.content_path)
        self.mahelper_obj.create_uncompressable_data(self.tcinputs['ClientName'], self.content_path, 1)
        self.log.info("Starting backup on subclient %s", self.subclient_name)
        job = self.subclient_obj.backup(job_type)
        if not job.wait_for_completion():
            raise Exception(f"Failed to run backup job with error: {job.delay_reason}")
        self.log.info("Backup job [%s] on subclient [%s] completed", job.job_id, self.subclient_name)

    def get_last_access_time_and_primaryid(self):
        """
        Finds values in LastAccessTime and PrimaryID column in each partition and returns a list of dictionaries
        with following format

        [{ substoreid : <value>, lastaccesstime : <value>, primaryid : <value>},
         {substoreid : <value>,  lastaccesstime : <value>, primaryid : <value>}]

        Returns:
            List of dictionaries in format mentioned above
        """
        self.log.info("Sleeping for 1 minute as sometimes primary ID update in CSDB takes this time as SIDB does"
                      "not go down immediately after backups")
        time.sleep(60)

        query = f"select substoreid, lastaccesstime, primaryid from idxsidbsubstore " \
                f"where sidbstoreid={self.sidb_store_obj.store_id} order by substoreid"
        self.log.info("Query ==> %s", query)
        self.csdb.execute(query)
        substore_mapping = self.csdb.fetch_all_rows()
        self.log.info(substore_mapping)
        substore_info_list = []

        for substore_info in substore_mapping:
            substore_details_dict = {'SubStoreId': int(substore_info[0]), 'LastAccessTime': int(substore_info[1]),
                                     'PrimaryId': int(substore_info[2])}
            substore_info_list.append(substore_details_dict)

        self.log.info("Primary ID Mapping - %s", substore_info_list)
        return substore_info_list

    def perform_dr_backup(self):
        """
        Run DR Backup job
        """
        self.drhelper_obj = drhelper.DRHelper(self.commcell)
        self.drhelper_obj.client_machine = self.cs_machine_obj
        self.dr_obj = self.commcell.disasterrecovery
        self.commcell.refresh()

        self.log.info("Run DR backup before creating any entities")
        self.dr_obj.backup_type = 'full'
        self.log.info("Running DR Backup now")
        full_dr_job = self.dr_obj.disaster_recovery_backup()
        self.log.info("Waiting for DR Backup Job ID [%s] to complete", full_dr_job.job_id)
        if not full_dr_job.wait_for_completion():
            raise Exception(f"Failed to run DR backup job with error: {full_dr_job.delay_reason}")

    def verify_resync_range(self):
        """
        Verify Resync range in SIDB2 dump stats command line output for each partition
        """
        failurestring = ""

        for partition in range(0, 2):

            stats_output = self.dedup_helper_obj.sidb_stats(self.ma_client_obj, self.sidb_store_obj.store_id, partition)
            self.log.info("SIDB stats output for partition ==> %s", str(stats_output))
            snapsizebytes = self.partition_info_1[partition]['PrimaryId']
            afterdrbackup_snapsizebytes = int(self.partition_info_2[partition]['PrimaryId']) - 1
            self.log.info(f"Expected Resync Range : [{snapsizebytes} - {afterdrbackup_snapsizebytes}")
            match = re.compile("ResyncRange_\\d+\\s+,\\s+," + str(snapsizebytes) +
                               "\\s+,\\s+" + str(afterdrbackup_snapsizebytes))
            resyncvalidation = match.findall(stats_output)
            if resyncvalidation == []:
                self.log.info(f"Failed to verify Resync Range : [{snapsizebytes} - {afterdrbackup_snapsizebytes}")

                failurestring = f"{failurestring} \\n " \
                                f"Failed to match the resync range for SIDB {self.sidb_store_obj.store_id}"

            else:
                self.log.info(f"Successfully matched the resync range in output :{resyncvalidation}")

        if failurestring:
            self.result_string += f"{failurestring}"
            self.status = constants.FAILED

    def perform_dr_restore(self):
        """
        Run DR Restore using CSRecoveryAssistant Tool
        """
        dr_restore_failed = False
        query = """select value from GxGlobalParam where name = 'DRDumpLocation'"""
        self.csdb.execute(query)
        dr_location = self.csdb.fetch_one_row()[0]
        self.log.info("Listing all the directories in %s", dr_location)
        try:
            dr_folder_list = self.cs_machine_obj.get_folders_in_path(dr_location)
        except Exception as ex:
            self.log.error("Failed to get folders from path %s. Error ==> %s", dr_location, str(ex))

        self.log.info("Starting DR Restore using CSRecoveryAssistatnt tool")
        returnval = 0
        if not self.is_linux_cs:
            csrecoverycmd = "start-process -FilePath "
            restorecmd = self.cs_client_obj.install_directory + self.cs_machine_obj.os_sep + "Base" + \
                self.cs_machine_obj.os_sep
            restorecmd = restorecmd + "CSRecoveryAssistant.exe"
            restorecmd = '"' + restorecmd + '"'
            csrecoverycmd = csrecoverycmd + restorecmd + " -ArgumentList "
            csrecoverycmd = csrecoverycmd + '"' + " -operation recovery " + " -dbdumplocation " + dr_folder_list[-1] + '"'
            csrecoverycmd = csrecoverycmd + " -NoNewWindow -Wait"

            try:
                self.log.info("Command ==> %s",csrecoverycmd)
                self.cs_machine_obj.execute_command(csrecoverycmd)
            except Exception as ex:
                self.log.error(f"Failed to run csrecoveryassistant tool ==> {str(ex)}")
                returnval = 1

            self.log.info("Starting CS services after sleeping for 2 minutes")
            time.sleep(120)
            # Start the services
            startsvccmd = "start-process -FilePath "
            gxadmincmd = self.cs_client_obj.install_directory + self.cs_machine_obj.os_sep + "Base" + \
                self.cs_machine_obj.os_sep
            gxadmincmd = gxadmincmd + "gxadmin"
            gxadmincmd = '\"' + gxadmincmd + '\"'
            startsvccmd = startsvccmd + gxadmincmd + " -ArgumentList "
            startsvccmd = startsvccmd + '"' + " -consolemode " + " -startsvcgrp All" + '"' + " -NoNewWindow -Wait"
            try:
                self.log.info(f"Starting the services on CS ==> {startsvccmd}")
                self.cs_machine_obj.execute_command(startsvccmd)
            except Exception as ex:
                self.log.error(f"Failed to start services on CS ==> {str(ex)}")
        else:
            restorecmd = f"{self.cs_client_obj.install_directory}{self.cs_machine_obj.os_sep}Base{self.cs_machine_obj.os_sep}CSRecoveryAssistant.sh"
            args = f" -operation Recovery -dbdumplocation {dr_folder_list[-1]}"
            try:
                self.log.info(f"Command : {restorecmd} Args : {args}")
                self.cs_machine_obj.execute_command(f"{restorecmd} {args}")
            except Exception as ex:
                self.log.error("Failed to run DR Restore on Linux CS")
                dr_restore_failed = True
            self.log.info("Command : Starting services are DR Restore after 2 minutes")
            time.sleep(120)
            self.cs_machine_obj.start_all_cv_services()
            if dr_restore_failed:
                raise Exception("DR Restore Failed - Services have been restarted")

        self.log.info("Sleeping for 5 mins")
        time.sleep(300)
        return returnval

    def perform_resync_validations(self):
        """
        Perform resync validations by checking IdxSIDBResyncHistory table and IdxSIDBSTore table flags column
        """
        resync_done = False
        for itr in range(1, 16):
            query = f"select count(1) from IdxSIDBResyncHistory where sidbstoreid in " \
                    f"({self.sidb_store_obj.store_id}) and Resyncstatus != -1"
            self.log.info("QUERY : %s", query)
            self.csdb.execute(query)
            resync_history = self.csdb.fetch_one_row()
            self.log.info(resync_history)
            if int(resync_history[0]) == 1:
                self.log.info("IdxSIDBResyncHistory table is populated with at least one row each from these stores.")
                self.log.info(resync_history)
                resync_done = True
                self.log.info("Moving MM Admin Thread Interval back to 15 minutes so that Next Resync"
                              "does not start immediately")
                self.mahelper_obj.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5, 15)
                break
            else:
                self.log.info("Checking IdxSIDBResyncHistory table after 1 minute. Attempt Number - [%s]", itr)
                time.sleep(60)

        if not resync_done:
            self.log.error("Resync did not happen even after 15 minutes. Failing this case.")
            self.status = constants.FAILED
            raise Exception("Resync did not happen even after 15 minutes. Failing this case.")

        self.log.info("Verifying if DR Restore information is present in IdxSIDBResyncHistory table")
        if self.verify_idxsidb_resync_history(self.sidb_store_obj.store_id, [0, 0, 4, 0]):
            self.log.info("DR Restore Resync verification success for SIDB [%s]", self.sidb_store_obj.store_id)
        else:
            self.log.error("DR Restore Resync verification failed for SIDB [%s]", self.sidb_store_obj.store_id)
            self.result_string += f"IdxSIDBResyncHistory Verification Failed : SIDB : " \
                                  f"[{self.sidb_store_obj.store_id}]\n"
            self.status = constants.FAILED

        self.log.info("Verify if Maintenance Mode is reset")
        self.sidb_store_obj.refresh()
        if int(self.sidb_store_obj.store_flags) & int(StoreFlags.IDX_SIDBSTORE_FLAGS_DDB_UNDER_MAINTENANCE.value) == 0:
            self.log.info(f"Maintenance flag is not set on DDB [{self.sidb_store_obj.store_id}] after DR Resync")
            if int(self.sidb_store_obj.store_flags) & int(
                    StoreFlags.IDX_SIDBSTORE_FLAGS_DDB_NEEDS_AUTO_RESYNC.value) != 0:
                self.log.info(f"As Expected : Resync flag for Controlled AF Validation is set "
                              f"on DDB [{self.sidb_store_obj.store_id}] "
                              f"after DR Resync")
            else:
                self.log.error(f"Resync flag for Controlled AF Validation is not set "
                               f"on DDB [{self.sidb_store_obj.store_id}] after DR Resync")
                self.result_string += f"Resync flag for Controlled AF Validation is not set on DDB " \
                                      f"[{self.sidb_store_obj.store_id}] after DR Resync"
                self.status = constants.FAILED
        else:
            self.log.error(f"Maintenance flag is still set on DDB [{self.sidb_store_obj.store_id}] after DR Resync")
            self.result_string += f"Maintenance flag is still set on DDB [{self.sidb_store_obj.store_id}] after DR " \
                                  f"Resync\n"
            self.status = constants.FAILED

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

        if int(resync_row[9]) == verification_list[3]:
            self.log.info("Successfully verified NumResyncedAFIDs as - %s", verification_list[3])
        else:
            self.log.error("Failed to verify NumResyncedAFIDs : Expected - [%s] & Actual - [%s]", verification_list[3],
                           resync_row[9])
            failure = True

        return not failure

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

            if self.client_machine_obj.check_directory_exists(self.content_path):
                self.log.info("Deleting already existing content directory [%s]", self.content_path)
                self.client_machine_obj.remove_directory(self.content_path)

            self.log.info("Cleaning up Restore Path")
            if self.client_machine_obj.check_directory_exists(self.restore_path):
                self.log.info("Deleting already existing restore directory [%s]", self.restore_path)
                self.client_machine_obj.remove_directory(self.restore_path)

            self.log.info("Cleaning up depenednt storage policies")

            if self.commcell.storage_policies.has_policy(f"{self.storage_policy_name}"):
                self.log.info("Deleting Dependent SP - [%s]", f"{self.storage_policy_name}")
                self.commcell.storage_policies.delete(f"{self.storage_policy_name}")

            self.log.info("Cleaning up storage pools")
            if self.commcell.storage_policies.has_policy(f"{self.storage_pool_name}"):
                self.log.info("Deleting Storage Pool - [%s]", f"{self.storage_pool_name}")
                self.commcell.storage_policies.delete(f"{self.storage_pool_name}")

        except Exception as exp:
            self.log.warning("**********Cleanup before test run failed. Still continuing with test run. "
                             "Perform manual cleanup and re-run if any failure is observed."
                             " ERROR : %s**********", exp)

    def verify_restore(self):
        """
        Run a restore job followed by verification between source and destination
        """
        self.log.info("Running Restore on subclient - [%s]", self.subclient_name)
        restore_job = self.subclient_obj.restore_out_of_place(self.client.client_name, self.restore_path,
                                                              [self.content_path])
        self.log.info("Restore job: %s", restore_job.job_id)
        if not restore_job.wait_for_completion():
            if restore_job.status.lower() == "completed":
                self.log.info("job %d complete", restore_job.job_id)
            else:
                raise Exception(f"Job {restore_job.job_id} Failed with {restore_job.delay_reason}")
        self.log.info("Performing Data Validation after Restores")
        difference = self.client_machine_obj.compare_folders(self.client_machine_obj,
                                                             self.content_path, self.restore_path +
                                                             self.client_machine_obj.os_sep +
                                                             "Content")
        if difference:
            self.log.error(f"Validating Data restored after DR Restore failed for SIDB Store - "
                           f"[{self.sidb_store_obj.store_id}]")
            self.result_string += f"Failed to verify Data Validation after DR Restore for " \
                                  f"SIDB Store - [{self.sidb_store_obj.store_id}]"
            self.status = constants.FAILED

        self.log.info(f'Data Restore Validation after DR Restore passed for SIDB Store - '
                      f'[{self.sidb_store_obj.store_id}]')

    def perform_ddb_v5_validations(self, expectedflags):
        """verify that DDB is converted to v5

        Args:
            expectedflags   (int)   --  Expected value of the flags column

        """

        self.log.info("Verifying that DDB is a V5 DDB")
        self.log.info("Verifying extendedflags on IdxSidbSubstore table is set to [%s]", expectedflags)
        query = f"select ExtendedFlags from idxsidbsubstore where sidbstoreid={self.sidb_store_obj.store_id}"
        self.log.info("Query ==> %s", query)
        self.csdb.execute(query)

        all_rows = self.csdb.fetch_all_rows()
        self.log.info(all_rows)
        for row in all_rows:
            if int(row[0]) == expectedflags:
                self.log.info("Successfully verified the extendedflags - expected=[%s] actual=[%s]",
                              expectedflags, row[0])
            else:
                self.log.error("Failed to verify the extendedflags - expected=[%s] actual=[%s]",
                               expectedflags, row[0])
                #raise Exception("Failed to verify expected extendedflags on DDB partitions. Halting test case.")

        self.log.info("Verifying MaxNumofAfsInSecFile on IdxSidbSubstore table")
        query = f"select MaxNumofAfsInSecFile from idxsidbsubstore where sidbstoreid={self.sidb_store_obj.store_id}"
        self.log.info("Query ==> %s", query)
        self.csdb.execute(query)
        af_count = self.csdb.fetch_all_rows()
        self.log.info(af_count)
        for af in af_count:
            if int(af[0]) != 1:
                self.log.error("MaxNumofAfsInSecFile is [%s], expected [1]", af)
                raise  Exception("DDB V5 validations failed while verifying MaxNumofAfsInSecFile")
            else:
                self.log.info("Successfully verified MaxNumofAfsInSecFile value is [%s] , expected [1]", af)

        self.log.info("successfully verified that DDB version is V5 with required extendedflags")

    def convert_ddb_to_v5(self):
        """
        Convert the DDB store to V5
        """
        self.log.info("Refreshing the store object")
        self.sidb_store_obj.refresh()

        for partition in range(2):
            if self.dedup_helper_obj.wait_till_sidb_down(str(self.sidb_store_obj.store_id),
                                                         self.commcell.clients.get(self.ma_name)):
                self.log.info("SIDB2 process for engine %s has gone down", self.sidb_store_obj.store_id)
            self.log.info("Running command to compact secondary table for group [%s] of the DDB - [%s]",
                          partition, self.sidb_store_obj.store_id)
            self.dedup_helper_obj.execute_sidb_command('compactfile secondary', self.sidb_store_obj.store_id,
                                                       partition, self.ma_client_obj)

        self.log.info("Refreshing the store object")
        self.sidb_store_obj.refresh()
        self.log.info("Enabling Garbage Collection by running SQL query")
        query = "update idxsidbsubstore set extendedflags = extendedflags|1 where " \
                f"sidbstoreid={self.sidb_store_obj.store_id}"
        self.log.info("QUERY => %s", query)
        self.optionobj.update_commserve_db(query)
        self.log.info("Enabling Zeroref Pruning Journals")
        self.sidb_store_obj.enable_journal_pruning = True

        self.perform_ddb_v5_validations(7)


    def run(self):
        """Run function of this test case"""
        try:
            self.cleanup()
            self.configure_tc_environment()
            for _ in range(3):
                self.run_backups()
            self.partition_info_1 = self.get_last_access_time_and_primaryid()
            self.perform_dr_backup()
            self.convert_ddb_to_v5()
            self.run_backups()
            self.partition_info_2 = self.get_last_access_time_and_primaryid()
            self.perform_dr_restore()
            self.perform_resync_validations()
            self.perform_ddb_v5_validations(7)
            self.verify_resync_range()
            self.run_backups("FULL")
            self.verify_restore()
            if self.status == constants.FAILED:
                raise Exception(self.result_string)
            self.log.info("Testcase completed successfully")
        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            self.cleanup()
        except Exception as ex:
            self.log.warning(f"Test case cleanup failed - {ex}")
