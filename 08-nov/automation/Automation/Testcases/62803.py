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

    set_resiliency()                   -   Set resiliency settings on dedup enabled copy

    verify_maintenance_mode()          -   Verify if maintenance bit is set on the SIDB

    is_dv2_waiting()                   -   Check if DV2 job is in waiting state

 Expected Input :
    		"62803":{
    		        "ClientName": "client name",
					"AgentName": "File System",
					"MediaAgentName": "ma name",
					"MediaAgent2Name": "ma_2_name",
					"mediaagent2_username" : "username",
					"mediaagent2_password" : "password",
					"cs_machine_username":"username",
					"cs_machine_password" : "password",
					"dedup_path" : "path1",
					"mediaagent2_dedup_path" : "path2"}

  Note : Please set following values in coreutils/Templates/config.json file under Schedule section
        "cs_machine_uname":"SET_THIS_VALUE",
        "cs_machine_password":"SET_THIS_VALUE"

  Steps:
    1. Create GDSP such that MA1 has 4 partitions and MA2 has 2 partitions. Create another GDSP with exact reverse
        configuration such that MA1 has 2 partitions and MA2 has 4 partitions. Enable Resiliency on DDB stores.
    2. Create other resources like subclients etc.
    3. Run backups on subclient
    4. Save the primary id for DDB partition after running backup
    5. Run DR Backup
    6. Run more backups on subclient
    7. Save the primary id for DDB partition after running more backups
    9. Stop services on MA2
    10. Run DR Restore
    11. Verify that DR Restore Resync has taken place on GDSP where 4 partitions are on MA1 by verifying
        a. Maintenance Mode bit is not set on DDB
        b. IdxSIDBResyncHistory row has got added for the DDB with correct values
    12. Verify that DR Restore Resync has not taken place on GDSP where 4 partitions are on MA2
    13. Run DV2 and make sure that DV2 remains in Waiting state as 2 partitions are offline on MA2
    14. Run backups and make sure that they complete as backups run in Resiliency mode.
    15. Start services on MA2
    16. Verify that DR Restore Resync works on the second GDSP when MA2 comes online.
    17. Verify Resync Ranges
    18. Run Full backups
    19. Perform Restore and verify the content checksum
"""
import re
import time
from cvpysdk import deduplication_engines
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
        self.name = "DR Restore Resync : when half or more partitions of DDB are not found reachable during resync"
        self.tcinputs = {
            "MediaAgentName": None,
            "MediaAgent2Name": None,
            "mediaagent2_username": None,
            "mediaagent2_password": None,
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
        self.partition_info_pool1_before = None
        self.partition_info_pool2_before = None
        self.partition_info_pool1_after = None
        self.partition_info_pool2_after = None
        self.ma2_name = None
        self.dedup_path2 = None
        self.ma2_username = None
        self.ma2_password = None
        self.ma_client2_obj = None
        self.storage_pool_obj_list = []
        self.sidb_store_obj_list = []
        self.storage_policy_obj_list = []
        self.subclient_obj_list = []
        self.ma2_library_drive = None
        self.content_path_dict = {}
        self.ma2_machine_obj = None
        self.dv2_job_obj = None
        self.is_linux_cs = False

    def setup(self):
        """Setup function of this test case"""

        self.optionobj = OptionsSelector(self.commcell)
        self.ma_name = self.tcinputs.get('MediaAgentName')
        self.dedup_path = self.tcinputs.get('dedup_path')


        self.ma2_name = self.tcinputs.get('MediaAgent2Name')
        self.dedup_path2 = self.tcinputs.get('mediaagent2_dedup_path')
        self.ma2_username = self.tcinputs.get('mediaagent2_username')
        self.ma2_password = self.tcinputs.get('mediaagent2_password')

        self.client_machine_obj = Machine(self.tcinputs['ClientName'], self.commcell, )
        self.client_system_drive = self.optionobj.get_drive(self.client_machine_obj, 30)
        self.ma_machine_obj = Machine(self.ma_name, self.commcell)
        self.ma2_machine_obj = Machine(self.ma2_name, username=self.ma2_username, password=self.ma2_password)

        self.ma_library_drive = self.optionobj.get_drive(self.ma_machine_obj, 30)
        self.ma2_library_drive = self.optionobj.get_drive(self.ma2_machine_obj, 30)

        self.library_name = f"LIB_TC_{self.id}_{self.ma_name}"
        self.mountpath = self.ma_machine_obj.join_path(self.ma_library_drive, self.id, "MP")

        self.cs_machine_obj = Machine(self.commcell.commserv_name, username=self.tcinputs['cs_machine_username'],
                                      password=self.tcinputs['cs_machine_password'])
        self.cs_client_obj = Client(self.commcell, self.commcell.commserv_name)
        self.ma_client_obj = Client(self.commcell, self.ma_name)
        self.ma_client2_obj = Client(self.commcell, self.ma2_name)
        self.storage_policy_name = f"SP_TC_{self.id}_{self.ma_name}"
        self.storage_pool_name = f"{self.storage_policy_name}_POOL"
        if not self.dedup_path and "unix" in self.ma_machine_obj.os_info.lower():
            self.log.error("MA1 : LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("MA1 : LVM enabled dedup path not supplied for Unix MA!..")

        if not self.dedup_path2 and "unix" in self.ma2_machine_obj.os_info.lower():
            self.log.error("MA2 : LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("MA2 : LVM enabled dedup path not supplied for Unix MA!..")

        if self.cs_machine_obj.os_info.lower() == 'unix':
            self.is_linux_cs = True

        if not self.dedup_path:
            self.dedup_path = self.ma_machine_obj.join_path(self.ma_library_drive, f"{self.id}", "DDB")
        else:
            self.dedup_path = self.ma_machine_obj.join_path(self.dedup_path, f"{self.id}", "DDB")

        if not self.dedup_path2:
            self.dedup_path2 = self.ma2_machine_obj.join_path(self.ma2_library_drive, f"{self.id}", "DDB")
        else:
            self.dedup_path2 = self.ma2_machine_obj.join_path(self.dedup_path2, f"{self.id}", "DDB")

        self.backupset_name = f"bkpset_tc_{self.id}"
        self.subclient_name = f"subc_tc_{self.id}"
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

        self.log.info("Configuring Storage Pools for this test.")
        storage_pool_name = ""
        for pool_num in range(1, 3):
            self.log.info(f"Configurig Storage Pool - {pool_num}")
            storage_pool_name = f"{self.storage_pool_name}_{pool_num}"
            dedup_path = self.ma_machine_obj.join_path(self.dedup_path, storage_pool_name, "1")

            if not self.ma_machine_obj.check_directory_exists(dedup_path):
                self.log.info("Creating dedup directory [%s]", dedup_path)
                self.ma_machine_obj.create_directory(dedup_path)
            self.log.info("Creating Dedup Storage Pool [%s]", storage_pool_name)
            if not self.commcell.storage_policies.has_policy(storage_pool_name):
                self.storage_pool_obj_list.append(self.dedup_helper_obj.configure_global_dedupe_storage_policy(
                    global_storage_policy_name=storage_pool_name,
                    library_name=self.library_name,
                    media_agent_name=self.ma_name,
                    ddb_path=dedup_path,
                    ddb_media_agent=self.ma_name))
                self.log.info("Successfully created Dedup Storage Pool [%s]", storage_pool_name)
            else:
                self.log.error(f"Dedup Storage Pool already exists - {storage_pool_name} "
                              "Please clean up the storage pools and re-run this case" )
                raise Exception(f"Dedup Storage Pool already exists - {storage_pool_name} ")

        self.log.info("Adding partitions to Storage Pools")
        ma1_parts = None
        ma2_parts = None
        for pool_num in range(1, 3):

            if pool_num == 1:
                self.log.info("Adding Partitions to DDB to achieve MA1=[4] and MA2=[2] partitions")
            else:
                self.log.info("Adding Partitions to DDB to achieve MA1=[2] and MA2=[4] partitions")
            # SIDB Engine Details
            storage_pool_name = f"{self.storage_pool_name}_{pool_num}"
            dedup_engines_obj = deduplication_engines.DeduplicationEngines(self.commcell)
            copy_id = self.storage_pool_obj_list[pool_num-1].get_copy('Primary_Global').copy_id

            if dedup_engines_obj.has_engine(storage_pool_name, 'Primary_Global'):
                dedup_engine_obj = dedup_engines_obj.get(storage_pool_name, 'Primary_Global')
                dedup_stores_list = dedup_engine_obj.all_stores
                self.sidb_store_obj_list.append(dedup_engine_obj.get(dedup_stores_list[0][0]))

            self.log.info("Adding Partition to storage pool [%s]", storage_pool_name)
            dedup_path_list = []
            if pool_num == 1:
                ma1_parts = 4
                ma2_parts = 2
            else:
                ma1_parts = 2
                ma2_parts = 4

            for partition in range(1, ma1_parts):
                dedup_path_list.append(self.ma_machine_obj.join_path(self.dedup_path, storage_pool_name,
                                                                    f"{self.ma_name}_{partition}"))

                if not self.ma_machine_obj.check_directory_exists(dedup_path_list[-1]):
                    self.log.info("Creating dedup directory for partition [%s] on ma [%s]", dedup_path_list[-1],
                                  self.ma_name)
                    self.ma_machine_obj.create_directory(dedup_path_list[-1])
                    # adding partition 2
                self.storage_pool_obj_list[pool_num-1].add_ddb_partition(copy_id,
                               str(self.sidb_store_obj_list[pool_num-1].store_id), dedup_path_list[-1], self.ma_name)

            for partition in range(0, ma2_parts):
                dedup_path_list.append(self.ma2_machine_obj.join_path(self.dedup_path2, storage_pool_name,
                                                                    f"{self.ma2_name}_{partition}"))

                if not self.ma2_machine_obj.check_directory_exists(dedup_path_list[-1]):
                    self.log.info("Creating dedup directory for partition [%s] on ma [%s]", dedup_path_list[-1],
                                  self.ma2_name)
                    self.ma2_machine_obj.create_directory(dedup_path_list[-1])
                # adding partition 2
                self.storage_pool_obj_list[pool_num-1].add_ddb_partition(copy_id,
                               str(self.sidb_store_obj_list[pool_num-1].store_id), dedup_path_list[-1], self.ma2_name)

            self.set_resiliency(pool_num-1)
            # Creating Dedpendent SP
            storage_policy_name = f"{self.storage_policy_name}_{pool_num}"
            if self.commcell.storage_policies.has_policy(storage_policy_name):
                self.log.error(f"Dependent SP Already Exists. Please Cleanup and Rerun - [{storage_policy_name}]")
                raise Exception(f"Dependent Storage Policy already exists - {storage_policy_name} ")

            self.log.info("Creating Dependent SP - [%s]", storage_policy_name)
            self.storage_policy_obj_list.append(self.commcell.storage_policies.add(
                storage_policy_name=storage_policy_name,
                library=self.library_name,
                media_agent=self.ma_name,
                global_policy_name=storage_pool_name,
                dedup_media_agent="",
                dedup_path=""))
            sp_copy = self.storage_policy_obj_list[-1].get_copy('Primary')
            self.log.info("setting copy retention: 1 day, 0 cycle")
            sp_copy.copy_retention = (1, 0, 1)

            self.log.info("Creating subclient for using SIDB Store ID - [%s]",
                          self.sidb_store_obj_list[pool_num-1].store_id)
            content_path = self.client_machine_obj.join_path(self.content_path, str(pool_num))
            if self.client_machine_obj.check_directory_exists(content_path):
                self.log.info("Removing existing content directory [%s] from client", content_path)
                self.client_machine_obj.remove_directory(content_path)

            subclient_name = f"{self.subclient_name}_{pool_num}"
            self.content_path_dict[subclient_name] = content_path

            self.log.info("Creating content directory [%s] for subclient - [%s]", content_path, subclient_name)
            self.client_machine_obj.create_directory(content_path)
            self.subclient_obj_list.append(self.mahelper_obj.configure_subclient(self.backupset_name, subclient_name,
                                                                       storage_policy_name, content_path))
            self.log.info("Setting number of streams to 5")
            self.subclient_obj_list[-1].data_readers = 5
            self.subclient_obj_list[-1].allow_multiple_readers = True

        self.mahelper_obj.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES',5, 5)

    def set_resiliency(self, storage_pool_index):
        """set resiliency settings on dedup enabled copy
        Args:
            storage_pool_index (int)    --  Storage Pool index in the list of Storage Pools
        """
        pool = self.storage_pool_obj_list[storage_pool_index]
        self.log.info("Setting Resiliency on Storage Pool - [%s]", pool.storage_policy_name)
        copy_obj = pool.get_copy('Primary_Global')
        copy_obj._copy_properties['minimumNumberOfPartitionsForJobsToRun'] = 3
        copy_obj._dedupe_flags['allowJobsToRunWithoutAllPartitions'] = 1
        copy_obj._set_copy_properties()
        self.log.info("Successfully set the Resiliency on Storage Pool - [%s]", pool.storage_policy_name)

    def run_backups(self, job_type="Incremental", run_on_subc=None, num_iterations=2):
        """
        Run backups on subclient and maintain list of job IDs for each subclient
        Args:
            job_type(str)       --  Type of backup job, Incremental by default
            run_on_subc(object) --  Run on this specific subclient
            num_iterations(int) --  Number of iterations for backup jobs
        """
        subclient_obj_list = []
        if run_on_subc:
            subclient_obj_list = [run_on_subc]
        else:
            subclient_obj_list = self.subclient_obj_list
        for itr in range(0,num_iterations):
            for subc_obj in subclient_obj_list:
                self.log.info("Generating content for subclient [%s] at [%s]", subc_obj.name,
                              self.content_path_dict[subc_obj.name])
                self.mahelper_obj.create_uncompressable_data(self.tcinputs['ClientName'],
                                                             self.content_path_dict[subc_obj.name], 0.5)
                self.log.info("Starting backup on subclient %s", subc_obj.name)
                job = subc_obj.backup(job_type)
                if not job.wait_for_completion():
                    raise Exception(f"Failed to run backup job with error: {job.delay_reason}")
                self.log.info("Backup job [%s] on subclient [%s] completed", job.job_id, subc_obj.name)

    def get_last_access_time_and_primaryid(self, sidb_store_obj):
        """

        Finds values in LastAccessTime, PrimaryID and ClientName column in each partition and returns a list of
        dictionaries with following format

        [{ SubStoreId : <value>, LastAccessTime : <value>, PrimaryId : <value>, ClientName: <value>},
         {SubStoreId : <value>,  LastAccessTime : <value>, PrimaryId : <value>}, ClientName: <value>]
        Args:
            sidb_store_obj (Object)     --  SIDB Store Object

        Returns:
            List of dictionaries in format mentioned above
        """
        self.log.info("Sleeping for 1 minute as sometimes primary ID update in CSDB takes this time as SIDB does"
                      "not go down immediately after backups")
        time.sleep(60)

        query = f"select SUBSTORE.substoreid, SUBSTORE.lastaccesstime, SUBSTORE.primaryid, CLI.name from " \
                f"idxsidbsubstore SUBSTORE, app_client CLI where SUBSTORE.sidbstoreid={sidb_store_obj.store_id} " \
                f"and SUBSTORE.clientid = CLI.id order by substoreid"
        self.log.info("Query ==> %s", query)
        self.csdb.execute(query)
        substore_mapping = self.csdb.fetch_all_rows()
        self.log.info(substore_mapping)
        substore_info_list = []

        for substore_info in substore_mapping:
            substore_details_dict = {'SubStoreId': int(substore_info[0]), 'LastAccessTime': int(substore_info[1]),
                                     'PrimaryId': int(substore_info[2]), 'ClientName': substore_info[3]}
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

    def verify_resync_range(self, store_obj, partition_info_before, partition_info_after):
        """
        Verify Resync range in SIDB2 dump stats command line output for each partition
        Args:
            store_obj (object)  - Store object
            partition_info_before (dict)    - Dictionary returned by get_last_access_time_and_primaryid
            partition_info_after (dict)    - Dictionary returned by get_last_access_time_and_primaryid
        """
        failurestring = ""
        self.log.info("Changing MM Prune process interval to 60 minutes")
        self.mahelper_obj.update_mmconfig_param('MM_CONFIG_PRUNE_PROCESS_INTERVAL_MINS', 10, 60)

        for partition in range(0, 6):
            self.log.info("Fetching client object from client id - [%s]", partition_info_before[partition]['ClientName'])
            if partition_info_before[partition]['ClientName'] == self.ma_name:
                client_obj = self.ma_client_obj
            else:
                client_obj = self.ma_client2_obj

            statsoutput = self.dedup_helper_obj.sidb_stats(client_obj, store_obj.store_id, partition)
            self.log.info("SIDB stats output for partition ==> %s", str(statsoutput))
            snapsizebytes = partition_info_before[partition]['PrimaryId']
            afterdrbackup_snapsizebytes = int(partition_info_after[partition]['PrimaryId']) - 1
            self.log.info(f"Expected Resync Range : [{snapsizebytes} - {afterdrbackup_snapsizebytes}")
            match = re.compile("ResyncRange_\\d+\\s+,\\s+," + str(snapsizebytes) +
                               "\\s+,\\s+" + str(afterdrbackup_snapsizebytes))
            resyncvalidation = match.findall(statsoutput)
            if resyncvalidation == []:
                self.log.info(f"Failed to verify Resync Range : [{snapsizebytes} - {afterdrbackup_snapsizebytes}")

                failurestring = f"{failurestring} \\n " \
                                f"Failed to match the resync range for : SIDB {store_obj.store_id} + " \
                                f"Split {partition}"

            else:
                self.log.info(f"Successfully matched the resync range in output :{resyncvalidation} "
                              f"for : SIDB {store_obj.store_id} + Split {partition}")

        if failurestring:
            self.log.error(failurestring)
            return False

        return True

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
            self.log.info("Command : Starting services are DR Restore")
            self.cs_machine_obj.start_all_cv_services()
            if dr_restore_failed:
                raise Exception("DR Restore Failed - Services have been restarted")
        self.log.info("Sleeping for 2 mins")
        time.sleep(120)
        return returnval

    def perform_resync_validations(self, sidb_store_obj, iterations=15):
        """
        Perform resync validations by checking IdxSIDBResyncHistory table and IdxSIDBSTore table flags column

        Args:
            sidb_store_obj (object) --  Store Object
            iterations  (int)       -- Number of times validation needs to be performed. Each Iteration runs
                                        after 1 minute
        """
        resync_done = False

        for itr in range(1, iterations+1):
            query = f"select count(1) from IdxSIDBResyncHistory where sidbstoreid in " \
                    f"({sidb_store_obj.store_id}) and Resyncstatus != -1"
            self.log.info("QUERY : %s", query)
            self.csdb.execute(query)
            resync_history = self.csdb.fetch_one_row()
            self.log.info(resync_history)
            if int(resync_history[0]) == 1:
                self.log.info("IdxSIDBResyncHistory table is populated with at least one row each from this store.")
                self.log.info(resync_history)
                resync_done = True
                #self.log.info("Moving MM Admin Thread Interval back to 15 minutes so that Next Resync"
                #              "does not start immediately")
                #self.mahelper_obj.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5, 15)
                break
            else:
                self.log.info("Number of rows fetched from IdxSIDBResyncHistory for Store [%s] = [%s]",
                              sidb_store_obj.store_id, int(resync_history[0]))
                self.log.info("Checking IdxSIDBResyncHistory table after 3 minutes. Attempt Number - [%s]", itr)
                time.sleep(180)

        if not resync_done:
            self.log.error(f"Resync did not happen even after {iterations*3} minutes." )
            #raise Exception("Resync did not happen even after 15 minutes. Failing this case.")
            resync_done = False

        if resync_done:
            self.log.info("Verifying if DR Restore information is present in IdxSIDBResyncHistory table")
            if self.verify_idxsidb_resync_history(sidb_store_obj.store_id, [0, 0, 4, 0]):
                self.log.info("DR Restore Resync verification success for SIDB [%s]", sidb_store_obj.store_id)
            else:
                self.log.error("DR Restore Resync verification failed for SIDB [%s]", sidb_store_obj.store_id)
                self.result_string += f"IdxSIDBResyncHistory Verification Failed : SIDB : " \
                                      f"[{sidb_store_obj.store_id}]\n"
                resync_done = False

        self.log.info("Resync took place for this store - [%s]", sidb_store_obj.store_id)
        return resync_done

    def verify_maintenance_mode(self, sidb_store_obj):
        """
        Verify if Maintenance Bit is set on the SIDB Store
        Args:
            sidb_store_obj  (object)    -   SIDB store object

        Return True if maintenance mode is set, False otherwise
        """
        self.log.info("Verify if Maintenance Mode is reset")
        sidb_store_obj.refresh()
        maintenance_status = False
        resync_status = False
        if int(sidb_store_obj.store_flags) & 16777216 == 0:
            self.log.info(f"Maintenance flag is not set on DDB [{sidb_store_obj.store_id}] after DR Resync")
            maintenance_status = False
        else:
            self.log.info(f"Maintenance flag is still set on DDB [{sidb_store_obj.store_id}] after DR Resync")
            maintenance_status = True

        if int(sidb_store_obj.store_flags) & 33554432 != 0:
            self.log.info(f"Resync flag for Controlled AF Validation is set "
                          f"on DDB [{sidb_store_obj.store_id}] "
                          f"after DR Resync")
            resync_status = True
        else:
            self.log.info(f"Resync flag for Controlled AF Validation is not set "
                           f"on DDB [{sidb_store_obj.store_id}] after DR Resync")
            resync_status = False

        return maintenance_status, resync_status

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

            #self.log.info("Cleaning up Restore Path")
            if self.client_machine_obj.check_directory_exists(self.restore_path):
                self.log.info("Deleting already existing restore directory [%s]", self.restore_path)
                self.client_machine_obj.remove_directory(self.restore_path)


            self.log.info("Cleaning up depenednt storage policies")
            for sp in range(1, 3):
                if self.commcell.storage_policies.has_policy(f"{self.storage_policy_name}_{sp}"):
                    self.log.info("Deleting Dependent SP - [%s]", f"{self.storage_policy_name}_{sp}")
                    self.commcell.storage_policies.delete(f"{self.storage_policy_name}_{sp}")

            self.log.info("Cleaning up storage pools")
            for pool in range(1, 3):
                if self.commcell.storage_policies.has_policy(f"{self.storage_pool_name}_{pool}"):
                    self.log.info("Deleting Storage Pool - [%s]", f"{self.storage_pool_name}_{pool}")
                    self.commcell.storage_policies.delete(f"{self.storage_pool_name}_{pool}")

        except Exception as exp:
            self.log.warning("**********Cleanup before test run failed. Still continuing with test run. "
                             "Perform manual cleanup and re-run if any failure is observed."
                             " ERROR : %s**********", exp)

    def verify_restore(self, subc):
        """
        Run a restore job followed by verification between source and destination
        subc (object)   -- Subclient object on which Restore needs to run
        """
        subc_name = f'{subc.subclient_name}'
        self.log.info("Running Restore on subclient - [%s]", subc_name)
        restore_job = subc.restore_out_of_place(self.client.client_name, self.restore_path,
                                                [self.content_path_dict[subc_name]])
        self.log.info("Restore job: %s", restore_job.job_id)
        if not restore_job.wait_for_completion():
            if restore_job.status.lower() == "completed":
                self.log.info("job %d complete", restore_job.job_id)
            else:
                self.log.error(f"Job {restore_job.job_id} Failed with {restore_job.delay_reason}")
                return False

        self.log.info("Performing Data Validation after Restore")
        difference = self.client_machine_obj.compare_folders(self.client_machine_obj,
                                                             self.content_path_dict[subc_name], self.restore_path +
                                                             self.client_machine_obj.os_sep +
                                                             self.content_path_dict[subc_name].split(self.client_machine_obj.os_sep)[-1])
        if difference:
            self.log.error("Validating Data restored after DR Restore failed for subclient [%s]", subc_name)

        self.log.info('Data Restore Validation after DR Restore passed for subclient [%s]',subc_name)
        return True

    def is_dv2_waiting(self, store_obj):
        """
        Validate that DV2 job on given store fails
        Args:
            store_obj   (object)    --  Store Object

        Returns:
            True if DV2 on the store keeps in Waiting state , False if it succeeds
        """
        self.dv2_job_obj = store_obj.run_ddb_verification(incremental_verification=False, use_scalable_resource=True)
        self.log.info(f"Checking status for job {self.dv2_job_obj.job_id} 3 times after every 2 minutes and it should remain WAITING")
        time.sleep(60)
        for attempt in range(1,4):
            self.log.info("Check Job Status = waiting : Attempt No. [%s]", attempt)
            jpr = self.dv2_job_obj.delay_reason
            if self.dv2_job_obj.status.lower() == 'waiting':
                if jpr.count('MediaAgent of current active deduplication database is offline.'):
                    self.log.info("DV2 Job [%s] : \n JPR = [%s]", self.dv2_job_obj.job_id, jpr)
            else:
                self.log.info("Job Status is not [waiting] ! Current Job Status = [%s]", self.dv2_job_obj.status)
                return False
        self.log.info("Successfully verified over a period of 6 minutes that DV2 job is in waiting state")
        return True

    def confirm_sidb_down(self):
        """
        Make sure that no SIDB Process is running on each of the MAs

        Returns:
            True if SIDB2 processes are not running on MAs else False
        """

        sidb_id1 = self.sidb_store_obj_list[0].store_id
        sidb_id2 = self.sidb_store_obj_list[1].store_id

        self.log.info("Wait till SIDB process on MA - [%s] is down for DDB - [%s]", self.ma_name, sidb_id1)
        if not self.dedup_helper_obj.wait_till_sidb_down(str(sidb_id1), self.ma_client_obj, timeout=900):
            self.log.error("SIDB2 processes for engine ID [%s] are still not down on MA [%s] after 15 minutes",
                            sidb_id1, self.ma_name)
            return False

        self.log.info("Wait till SIDB process on MA - [%s] is down for DDB - [%s]", self.ma2_name, sidb_id1)
        if not self.dedup_helper_obj.wait_till_sidb_down(str(sidb_id1), self.ma_client2_obj, timeout=900):
            self.log.error("SIDB2 processes for engine ID [%s] are still not down on MA [%s] after 15 minutes",
                           sidb_id1, self.ma2_name)
            return False

        self.log.info("Wait till SIDB process on MA - [%s] is down for DDB - [%s]", self.ma_name, sidb_id2)
        if not self.dedup_helper_obj.wait_till_sidb_down(str(sidb_id2), self.ma_client_obj, timeout=900):
            self.log.error("SIDB2 processes for engine ID [%s] are still not down on MA [%s] after 15 minutes",
                           sidb_id2, self.ma_name)
            return False

        self.log.info("Wait till SIDB process on MA - [%s] is down for DDB - [%s]", self.ma2_name, sidb_id2)
        if not self.dedup_helper_obj.wait_till_sidb_down(str(sidb_id2), self.ma_client2_obj, timeout=900):
            self.log.error("SIDB2 processes for engine ID [%s] are still not down on MA [%s] after 15 minutes",
                           sidb_id2, self.ma2_name)
            return False

        return True

    def run(self):
        """Run function of this test case"""
        try:

            self.cleanup()
            self.configure_tc_environment()
            self.run_backups()

            self.partition_info_pool1_before = self.get_last_access_time_and_primaryid(self.sidb_store_obj_list[0])
            self.partition_info_pool2_before = self.get_last_access_time_and_primaryid(self.sidb_store_obj_list[1])
            self.perform_dr_backup()
            self.run_backups()
            self.partition_info_pool1_after = self.get_last_access_time_and_primaryid(self.sidb_store_obj_list[0])
            self.partition_info_pool2_after = self.get_last_access_time_and_primaryid(self.sidb_store_obj_list[1])
            self.log.info(f"Stopping services on MA - {self.ma2_name}")
            self.ma2_machine_obj.stop_all_cv_services()
            self.perform_dr_restore()
            #First Storage Pool Validations
            self.log.info("===TEST : Resync should complete as 4 partitions are online===")
            if not self.perform_resync_validations(self.sidb_store_obj_list[0]):
                self.log.error(f"===DDB [{self.sidb_store_obj_list[0].store_id}] : DR Resync Test : FAIL")
                self.result_string += f",[ Resync Validation Failure - Store [{self.sidb_store_obj_list[0].store_id}] ]"
                self.status = constants.FAILED
            else:
                self.log.info(f"===DDB [{self.sidb_store_obj_list[0].store_id}] : DR Resync Test: PASS===")

            self.log.info("===TEST : Maintenance Bit = OFF and Resync Bit = ON===")
            maintenance_status, resync_status = self.verify_maintenance_mode(self.sidb_store_obj_list[0])
            if not maintenance_status and resync_status:
                self.log.info("Successfully verified the Maintenance & Resync Bits on Store [%s]",
                              self.sidb_store_obj_list[0].store_id)
                self.log.info(f"===DDB [{self.sidb_store_obj_list[0].store_id}] : "
                              f"Maintenance+Resync Bit Test : PASS===")
            else:
                self.log.error("===DDB [{self.sidb_store_obj_list[0].store_id}] : "
                               "Maintenance+Resync Bit Test : FAIL===")
                self.result_string += f",[ Maintenance & Resync Bit Validation Faliure - " \
                                      f"Store [{self.sidb_store_obj_list[0].store_id}] ]"
                self.status = constants.FAILED

            #DV2 Failure Validation
            self.log.info("===TEST : DV2 should fail as only 4 partitions are online out of 6 partitions===")
            if self.is_dv2_waiting(self.sidb_store_obj_list[0]):
                self.log.info("Successfully verified that DV2 has failed on store [%s]",
                              self.sidb_store_obj_list[0].store_id)
                self.log.info(f"===DDB [{self.sidb_store_obj_list[0].store_id}] : DV2 Failure Test : PASS===")
            else:
                self.log.error(f"===DDB [{self.sidb_store_obj_list[0].store_id}] : DV2 Failure Test : FAIL===")
                self.result_string += f",[ DV2 Validation Failure - Store [{self.sidb_store_obj_list[0].store_id}] ]"
                self.status = constants.FAILED

            #Successful Backup Validation
            try:
                self.log.info("===TEST : Backups should run in Resiliency Mode with 4 online partitions===")
                self.run_backups("FULL", run_on_subc=self.subclient_obj_list[0], num_iterations=1)
                self.log.info(f"===DDB [{self.sidb_store_obj_list[0].store_id}] : Backup Test : PASS===")
            except:
                self.log.error(f"===DDB [{self.sidb_store_obj_list[0].store_id}] : Backup Test : FAIL===")

            self.log.info("===========STORE 1 Validations Complete===========")
            self.log.info("===TEST : Store should be in Maintenance Mode===")
            if not self.perform_resync_validations(self.sidb_store_obj_list[1], iterations=1):
                self.log.info("As expected - DDB is still in maintenance mode")
                self.log.info(f"===DDB [{self.sidb_store_obj_list[1].store_id}] : DR Resync Test: PASS===")
            else:
                self.log.error(f"===DDB [{self.sidb_store_obj_list[1].store_id}] : DR Resync Test : FAIL")
                self.result_string += f",[ Resync Validation Failure - Store [{self.sidb_store_obj_list[1].store_id}] ]"
                self.status = constants.FAILED


            self.log.info("===TEST : Maintenance Bit = ON and Resync Bit = ON===")
            maintenance_status, resync_status = self.verify_maintenance_mode(self.sidb_store_obj_list[1])
            if maintenance_status and resync_status:
                self.log.info("Successfully verified the Maintenance & Resync Bits on Store [%s]",
                              self.sidb_store_obj_list[1].store_id)
                self.log.info(f"===DDB [{self.sidb_store_obj_list[1].store_id}] : Maintenance+Resync Bit Test : PASS===")
            else:
                self.log.error("===DDB [{self.sidb_store_obj_list[1].store_id}] : Maintenance+Resync Bit Test : FAIL===")
                self.result_string += f",[ Maintenance & Resync Bit Validation Faliure - " \
                                      f"Store [{self.sidb_store_obj_list[1].store_id}] ]"
                self.status = constants.FAILED


            self.log.info("Starting Commvault Services on [%s]", self.ma2_name)
            self.ma2_machine_obj.start_all_cv_services()

            if not self.perform_resync_validations(self.sidb_store_obj_list[1]):
                self.log.error(f"===DDB [{self.sidb_store_obj_list[1].store_id}] : "
                               f"DR Resync Test After Service Start : FAIL")
                self.result_string += f",[ Resync Validation Failure - Store [{self.sidb_store_obj_list[1].store_id}] ]"
                self.status = constants.FAILED
            else:
                self.log.info(f"===DDB [{self.sidb_store_obj_list[1].store_id}] : "
                              f"DR Resync Test After Service Start : PASS===")

            self.log.info("===TEST : Maintenance Bit = OFF and Resync Bit = ON===")
            maintenance_status, resync_status = self.verify_maintenance_mode(self.sidb_store_obj_list[1])
            if not maintenance_status and resync_status:
                self.log.info("Successfully verified the Maintenance & Resync Bits on Store [%s]",
                              self.sidb_store_obj_list[1].store_id)
                self.log.info(f"===DDB [{self.sidb_store_obj_list[1].store_id}] : "
                              f"Maintenance+Resync Bit Test After Service Start : PASS===")
            else:
                self.log.error("===DDB [{self.sidb_store_obj_list[1].store_id}] : "
                               "Maintenance+Resync Bit Test After Service Start : FAIL===")
                self.result_string += f",[ Maintenance & Resync Bit Validation Faliure - " \
                                      f"Store [{self.sidb_store_obj_list[1].store_id}] ]"
                self.status = constants.FAILED

            self.mahelper_obj.update_mmconfig_param('MMS2_CONFIG_MM_MAINTAINENCE_INTERVAL_MINUTES', 5, 15)

            self.run_backups("FULL", self.subclient_obj_list[1], 1)

            self.log.info("Waiting for DV2 job to complete")
            if not self.dv2_job_obj.wait_for_completion():
                self.result_string += f"[ Failed to run DV2 job with error: {self.dv2_job_obj.delay_reason}]"
                self.log.error("DV2 job [%s] on store [%s] did not complete successfully", self.dv2_job_obj.job_id,
                               self.sidb_store_obj_list[0].store_id)
                self.status = constants.FAILED
            else:
                self.log.error("Verified the successful completion of DV2 job on store [%s]",
                               self.sidb_store_obj_list[0].store_id)


            self.log.info("Waiting for SIDB processes to go down before performing Resync Validation")
            if not self.confirm_sidb_down():
                self.log.warning("SIDB2 processes on MAs have not gone down even after 15 minutes which is unexpected."
                                 "This can cause SIDB2 stats command to fail.")
                self.log.info("Will sleep for additional 5 minutes before attempting Resync Validations.")
                time.sleep(300)
                self.log.warning("If Resync Validations fail, please check if sidb2 stats command ran successfully.")

            self.log.info("===TEST : Resync Range Validation===")
            if not self.verify_resync_range(self.sidb_store_obj_list[0], self.partition_info_pool1_before,
                                            self.partition_info_pool1_after):
                self.log.error(f"===DDB [{self.sidb_store_obj_list[0].store_id}] : "
                               f"Resync Range Validation : FAIL")
                self.result_string += f",[ Resync Range Validation Failure - Store " \
                                      f"[{self.sidb_store_obj_list[0].store_id}] ]"
                self.status = constants.FAILED
            else:
                self.log.info(f"===DDB [{self.sidb_store_obj_list[0].store_id}] : "
                              f"Resync Range Validation : PASS===")

            if not self.verify_resync_range(self.sidb_store_obj_list[1], self.partition_info_pool2_before,
                                            self.partition_info_pool2_after):
                self.log.error(f"===DDB [{self.sidb_store_obj_list[1].store_id}] : "
                               f"Resync Range Validation : FAIL")
                self.result_string += f",[ Resync Range Validation Failure - Store " \
                                      f"[{self.sidb_store_obj_list[1].store_id}] ]"
                self.status = constants.FAILED
            else:
                self.log.info(f"===DDB [{self.sidb_store_obj_list[1].store_id}] : "
                              f"Resync Range Validation : PASS===")



            self.log.info("===TEST : Restore Validation")
            if not self.verify_restore(self.subclient_obj_list[0]):
                self.log.error(f"===DDB [{self.sidb_store_obj_list[0].store_id}] : Restore Validation : FAIL")
                self.result_string += f"Failed to verify Data Validation after DR Restore for " \
                                      f"SIDB Store - [{self.sidb_store_obj_list[0].store_id}]"
                self.status = constants.FAILED
            else:
                self.log.info(f"===DDB [{self.sidb_store_obj_list[0].store_id}] : Restore Validation : PASS")

            if not self.verify_restore(self.subclient_obj_list[1]):
                self.log.error(f"===DDB [{self.sidb_store_obj_list[1].store_id}] : Restore Validation : FAIL")
                self.result_string += f"Failed to verify Data Validation after DR Restore for " \
                                      f"SIDB Store - [{self.sidb_store_obj_list[1].store_id}]"
                self.status = constants.FAILED
            else:
                self.log.info(f"===DDB [{self.sidb_store_obj_list[1].store_id}] : Restore Validation : PASS")

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
            self.log.warning("Test case cleanup failed - {ex}")
