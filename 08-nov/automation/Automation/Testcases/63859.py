# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()  --  initialize TestCase class

    run()  --  run function of this test case

    setup()  --  Setup function of this test case

    cleanup()  --  Cleanup SC, BS,SP, Library

    tear_down() --  Tear Down Function of this Case
    
    validate_cleanup()  --  Validates the ArchFileSIDBKeys cleanup from log
    
    run_backup()  --  Validates the ArchFileSIDBKeys cleanup from log
    
    delete_jobs()  --  Deletes randon jobs
    
    update_store_creation()  --  Updates the CSDB to make the store eligible for cleanup
    

    Input Example:

    "testCases": {
				"63859": {
					"ClientName": "client1",
					"AgentName": "File System",
					"MA1":"ma1",
					"MA2":"ma2"
				}
                }
"""
import time
import datetime
import random
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
from AutomationUtils import config

class TestCase(CVTestCase):
    """ArchFileSIDBKeys table cleanup verification basic case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "ArchFileSIDBKeys table cleanup verification basic case"

        self.primary_ma = None
        self.secondary_ma = None
        self.library1 = None
        self.library2 = None
        self.storage_policy = None
        self.backupset = None
        self.sub_client = None
        self.storage_policy_obj = None
        self.backup_set_obj = None
        self.subclient_obj= None
        self.primary_copy_obj = None

        self.primary_ma_machine = None
        self.secondary_ma_machine = None
        self.client_machine = None
        self.primary_ma_path = None
        self.secondary_ma_path = None
        self.client_path = None

        self.library1_path = None
        self.library2_path = None
        self.ddb1_path = None
        self.ddb2_path = None
        self.client_content1 = None
        self.result_string = None
        
        self.cleanup_thread_interval = None

        self.tcinputs = {
            "MA1": None,
            "MA2": None,
            "ClientName": None,
            "AgentName": None,
        }

        self.ma_helper = None
        self.dedupehelper = None
        self.client_directory_created = None
        
        self.job_list = []


    def setup(self):
        """Setup function of this test case"""
        
        self.primary_ma = self.tcinputs["MA1"]
        self.secondary_ma = self.tcinputs["MA2"]
        self.client = self.tcinputs['ClientName']

        self.log.info("Verifying that all clients are unique")
        client_list = [self.primary_ma, self.secondary_ma, self.client]
        if (len(set(client_list))) != 3:
            self.log.info("MAs and clients have to be unique")
            raise Exception("MAs and clients have to be unique. Found duplicate")

        self.log.info("Generating automation names ( library, SP, BS, SC etc)")
        self.library1 = f"Automation_{str(self.id)}_library1"
        self.library2 = f"Automation_{str(self.id)}_library2"
        self.storage_policy = f"Automation_{str(self.id)}_SP"
        self.backupset = f"Automation_{str(self.id)}_BS1"
        self.sub_client = f"Automation_{str(self.id)}_SC1"

        self.ma_helper = MMHelper(self)
        self.dedupehelper = DedupeHelper(self)

        self.log.info("Creating machine objects and generating automation folder")
        ( self.primary_ma_machine, self.primary_ma_path) = self.ma_helper.generate_automation_path(self.primary_ma)
        ( self.secondary_ma_machine, self.secondary_ma_path) = self.ma_helper.generate_automation_path(self.secondary_ma)
        ( self.client_machine, self.client_path) = self.ma_helper.generate_automation_path(self.client)

        self.log.info("Generating automation paths")
        self.library1_path = self.primary_ma_path+"Library1"
        self.log.info(f"Library1 path: {self.library1_path}")

        self.library2_path = self.secondary_ma_path+"Library2"
        self.log.info(f"Library2 path: {self.library2_path}")

        self.ddb1_path = self.primary_ma_path+"DDBPart1"
        self.log.info(f"DDB partition-1 path: {self.ddb1_path}")

        self.ddb2_path = self.secondary_ma_path+"DDBPart2"
        self.log.info(f"DDB partition-2 path: {self.ddb2_path}")

        self.client_content1 = self.client_path+"content1"
        self.log.info(f"Content-1 path: {self.client_content1}")

        self.result_string = ""
        self.client_directory_created = False

        self.client_ma_obj = self.commcell.media_agents.get(self.client)
        
        self.cleanup_thread_interval = "5"


    def cleanup(self):
            """Cleanup SC, BS,SP, Library """

            self.log.info("Starting cleanup")

            self.log.info(f"Deleting BackupSet [{self.backupset}] if exists")
            if self._agent.backupsets.has_backupset(self.backupset):
                self.log.info(f"BackupSet[{self.backupset}] exists, deleting that")
                self._agent.backupsets.delete(self.backupset)

            self.log.info("Deleting Storage Policy if exists")
            if self.commcell.storage_policies.has_policy(self.storage_policy):
                self.log.info("Storage Policy[%s] exists, deleting that", self.storage_policy)
                self.log.info("Reassociating all sub clients before deleting the SP")
                self.sp_obj_to_reassociate = self.commcell.storage_policies.get(self.storage_policy)
                self.sp_obj_to_reassociate.reassociate_all_subclients()
                self.log.info("Deleting the SP now")
                self.commcell.storage_policies.delete(self.storage_policy)

            self.log.info("Deleting library[%s] if exists", self.library1)
            if self.commcell.disk_libraries.has_library(self.library1):
                self.log.info("Library[%s] exists, deleting that", self.library1)
                self.commcell.disk_libraries.delete(self.library1)

            self.log.info("Deleting library[%s] if exists", self.library2)
            if self.commcell.disk_libraries.has_library(self.library2):
                self.log.info("Library[%s] exists, deleting that", self.library2)
                self.commcell.disk_libraries.delete(self.library2)

            self.log.info("Cleanup completed")

    def tear_down(self):
        """Tear Down Function of this Case"""

        self.log.info("This is Tear Down method")
        try:

            if self.status == constants.FAILED:
                self.log.info("Test case failed, not deleting Library, SP, BS, SC")
            else:
                self.log.info("Test case completed successfully, starting cleanup")
                self.cleanup()

            if self.client_directory_created:
                self.log.info("Client directory created")
                self.client_ma_obj.set_ransomware_protection(False)
                self.ma_helper.remove_content(self.client_path, self.client_machine)

        except Exception as excp:
            self.log.error("Cleanup failed")
            self.result_string = self.result_string+" Cleanup FAILED."+str(excp)

    def validate_cleanup(self):
        """Validates the ArchFileSIDBKeys cleanup from log"""
        self.log.info("Starting the validation")

        time_out_min=120
        start_time =  datetime.datetime.now()
        
        self.log.info("Frequency for Mark & Sweep set for 1 hour, will sleep for 30min before start checking")
        time.sleep(30*60)
        
        query_to_execute = f"select count(*) from archFileSIDBKeysPruningLogs where SIDBStoreId = {self.sidb_store_ids[0]}"
        self.log.info("Will execute the following query to fetch the deleted ArchFile count")
        self.log.info(query_to_execute)
        
        while ((datetime.datetime.now() - start_time).total_seconds()) < (time_out_min*60):
            self.log.info("Sleeping for 120 sec")
            time.sleep(120)
            self.csdb.execute(query_to_execute)
            count = int(self.csdb.fetch_one_row()[0])
            self.log.info(f"Deleted ArchFile count:{count}")
            if count > 0:
                self.log.info("Verification passed")
                return
            
        raise Exception(f"waited for {time_out_min} min but no deleted ArchFile found on archFileSIDBKeysPruningLogs")

    def run_backup(self, subclient_obj, client_content):
    
            count = 10
            
            while count >0:
                # Deleting the old data and will generate new data
                if self.client_directory_created:
                    self.log.info("Deleting the old data and will generate new data")
                    self.ma_helper.remove_content(client_content, self.client_machine)
                
                self.log.info("Generating client content")
                self.ma_helper.create_uncompressable_data(self.client, client_content, 1)
                self.client_directory_created = True
                
                self.log.info(f"Starting backup on Sub Client [{subclient_obj.name}]")
                job_obj = subclient_obj.backup("FULL")
                self.log.info(f"Job started, waiting for the job completion. Job ID: {job_obj.job_id} ")
                self.ma_helper.wait_for_job_completion(job_obj)
                
                self.job_list.append(job_obj.job_id)
                count = count -1

    def delete_jobs(self):
        self.log.info("Starting job deletion")
        count = random.randint(4,9)
        self.log.info(f"Will be deleting {count} jobs randomly")
        
        while count >0:
            random_job = random.choice(self.job_list)
            self.log.info(f"Deleting job {random_job}")
            self.primary_copy_obj.delete_job(random_job)
            self.job_list.remove(random_job)
            
            count = count -1
            
        self.log.info("Job deletion completed")
        
    def update_store_creation(self):
        """Updates the CSDB to make the store eligible for cleanup"""
        
        self.log.info(f"Waiting for {int(self.cleanup_thread_interval)*2} mins so that entry gets created on MMEntityProp table for the DDB store")
        
        time.sleep(int(self.cleanup_thread_interval)*2*60)
        
        self.log.info("Updating creation time in DB. DB credentials will be fetched from config.json")
        query_to_execute=f"""
                update MMEntityProp
                set intVal = dbo.GetUnixTime(DATEADD(day, -99, GETUTCDATE()))
                where propertyName='DDBEncKeyLastPruneTime'
                and EntityType=3
                and EntityId={str(self.sidb_store_ids[0])}
                """

        self.log.info("Executing the following query")
        self.log.info(query_to_execute)

        output = self.ma_helper.execute_update_query(query_to_execute, config.get_config().SQL.Password, config.get_config().SQL.Username )
        self.log.info(f"SQL output [{output}]")

    def run(self):
        try:

            self.log.info("Starting cleanup of previous run")
            self.cleanup()

            self.log.info("Creating reg key MediaManager\ bEnablePruneInvalidArchFileSIDBKey=1 on CS")
            self.commcell.add_additional_setting("MediaManager","bEnablePruneInvalidArchFileSIDBKey","INTEGER","1")

            self.log.info("Creating reg key MediaManager\ EncKeysCleanupIntervalInMinutes=5 on CS")
            self.commcell.add_additional_setting("MediaManager", "EncKeysCleanupIntervalInMinutes", "INTEGER", self.cleanup_thread_interval)

            self.log.info("Restarting MediaManager service")
            self.ma_helper.restart_mm_service()
            self.log.info("Waiting for 60 seconds for MediaManager to come online")
            time.sleep(60)

            self.log.info(f"Creating library [{self.library1}] on MediaAgent [{self.primary_ma}]")
            self.commcell.disk_libraries.add(self.library1, self.primary_ma, self.library1_path)
            self.primary_ma_directory_created = True

            self.log.info(f"Creating library [{self.library2}] on MediaAgent [{self.secondary_ma}]")
            self.commcell.disk_libraries.add(self.library2, self.secondary_ma, self.library2_path)
            self.secondary_ma_directory_created = True

            self.log.info(f"Creating storage policy [{self.storage_policy}]")
            self.storage_policy_obj = self.commcell.storage_policies.add(self.storage_policy, self.library1, self.primary_ma,self.ddb1_path,dedup_media_agent=self.primary_ma)

            self.log.info("Adding 2nd DDB partition to Primary copy")
            self.sidb_store_ids = self.dedupehelper.get_sidb_ids(self.storage_policy_obj.storage_policy_id, "Primary")
            self.log.info("SIDB Store ID %s", str(self.sidb_store_ids))
            self.primary_copy_obj = self.storage_policy_obj.get_copy("Primary")
            self.storage_policy_obj.add_ddb_partition(str(self.primary_copy_obj.get_copy_id()), str(self.sidb_store_ids[0]),
                                          self.ddb2_path, self.secondary_ma)
            self.log.info("2nd DDB partition added successfully")

            self.log.info("Enabling encryption on Primary copy")
            self.primary_copy_obj.set_encryption_properties(re_encryption=True, encryption_type="BlowFish", encryption_length=128)
            self.log.info("Encryption enabled successfully")
            
            self.log.info(f"Creating BackupSet [{self.backupset}]")
            self.backup_set_obj = self._agent.backupsets.add(self.backupset)

            self.log.info("Creating SubClient")
            self.subclient_obj = self.ma_helper.configure_subclient(self.backupset, self.sub_client, self.storage_policy,
                                                                [self.client_content1])

            #Running multiple backups on each sublients
            self.run_backup(self.subclient_obj, self.client_content1)
            
            # Deleting a few jobs
            self.delete_jobs()
            
            self.log.info("Starting data aging job")
            da_job = self.commcell.run_data_aging()
            self.log.info(f"Job started, waiting for the job completion. Job ID: {da_job.job_id} ")
            self.ma_helper.wait_for_job_completion(da_job)
            
            self.update_store_creation()
            
            self.log.info("Settings M&S frequency t 1 hour for this store")
            output = self.dedupehelper.set_mark_and_sweep_interval(str(self.sidb_store_ids[0]), 1)
            self.log.info(f"Command output [{str(output)}]")            

            self.validate_cleanup()

            self.log.info("Creating aux copy")
            self.storage_policy_obj.create_secondary_copy("Copy2", self.library2, self.secondary_ma)
            self.aux_copy_obj = self.storage_policy_obj.get_copy("Copy2")
            self.log.info(f"Removing copy from auto copy schedule")
            self.ma_helper.remove_autocopy_schedule(self.storage_policy, "Copy2")

            self.log.info("Disabling encryption on aux copy ( plain text)")
            self.aux_copy_obj.set_encryption_properties(re_encryption=True, encryption_type="BlowFish", encryption_length=128)

            self.log.info("Starting aux copy")
            self.aux_job = self.storage_policy_obj.run_aux_copy()
            self.log.info(f"Job started, waiting for the job completion. Job ID: {self.aux_job.job_id} ")
            self.aux_job.wait_for_completion()
            self.log.info("Aux copy job completed successfully")

            self.log.info("Test case completed successfully.")

        except Exception as excp:
            self.log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
