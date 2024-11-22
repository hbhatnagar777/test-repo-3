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

    create_pool() -- Creates storage pool

    create_secondary_copy()  --  Creates aux copy

    cleanup() -- performs cleanps for the test case entities

    tear_down() --  Tear Down Function of this Case

    run_backups() -- Runs multiple backup

    validate_from_log() -- Performs validation from log

    set_mm_config_value() -- Set MMConfig value of config MMCONFIG_AUXCOPY_COPY_FIRST_FULL_FOR_NEW_SUBCLIENT

    configure_sub_client() -- Configure the sub client



    Input Example:

    "testCases": {

				"62871": {
					"ClientName": "client",
					"AgentName": "File System",
					"MA1": "MAName1",
					"MA2": "MAName2"
				}
                }
                
                
    Note: There should not be any aux copy job running on source MA while executing this case. That may cause failure to this case.
    
"""

import random
import time
import threading
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper

class TestCase(CVTestCase):
    """Encryption key cleanup while 2 aux copy jobs are running"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Encryption key cleanup while 2 aux copy jobs are running"

        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MA1": None,
            "MA2": None
        }

        self.sp_name = None
        self.pool_primary_name = None
        self.pool_secondary_name = None
        self.sc_name = None
        self.bs_name = None
        self.source_ma = None
        self.destination_ma = None
        self.source_ma_o = None
        self.destination_ma_o = None
        self.ma_helper = None
        self.dedupe_helper = None
        self.client = None
        self.client_machine = None
        self.client_path = None
        self.source_ma_machine = None
        self.source_ma_path = None
        self.destination_ma_machine = None
        self.destination_ma_path = None
        self.source_lib_path = None
        self.destination_lib_path = None
        self.primary_ddb_path = None
        self.secondary_ddb_path = None
        self.client_content = None
        self.sp_obj = None
        self.copy_name = None
        self.copy_name2 = None
        self.copy_name3 = None
        self.primary_pool_o = None
        self.secondary_pool_o = None
        self.is_destination_ma_directory_created = None
        self.is_source_ma_directory_created = None
        self.is_client_directory_created = None
        self.bs_name2 = None
        self.sc_name2 = None
        self.client_content2 = None
        self.client2 = None
        self.agent2 = None
        self.subclient = None
        self.subclient2 = None
        self.secondary_pool_o2 = None
        self.secondary_pool_copy_o2 = None
        self.pool_secondary_name2 = None
        self.destination_lib_path2 = None
        self.secondary_ddb_path2 = None

        self.secondary_pool_o3 = None
        self.secondary_pool_copy_o3 = None
        self.pool_secondary_name3 = None
        self.destination_lib_path3 = None
        self.secondary_ddb_path3 = None

        self.is_client_directory_created2 = None

    def setup(self):
        """Setup function of this test case"""

        self.log.info("This is setup method of the test case")
        self.ma_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)
        
        self.source_ma = self.tcinputs['MA1']
        self.destination_ma = self.tcinputs['MA2']
        self.client = self.tcinputs['ClientName']
        self.client2 = self.tcinputs['ClientName2']
        self.sp_name = f"automation_{self.id}_sp_{self.source_ma}_{self.destination_ma}"
        self.pool_primary_name = f"automation_{self.id}_primary_pool_{self.source_ma}"
        self.pool_secondary_name = f"automation_{self.id}_secondary_pool_{self.destination_ma}"
        self.pool_secondary_name2 = f"automation_{self.id}_secondary_pool_2_{self.destination_ma}"
        self.pool_secondary_name3 = f"automation_{self.id}_secondary_pool_3_{self.destination_ma}"
        self.bs_name = f"automation_{self.id}_BS"
        self.bs_name2 = f"automation_{self.id}_BS_2"
        self.sc_name = f"automation_{self.id}_SC"
        self.sc_name2 = f"automation_{self.id}_SC_2"
        self.copy_name = "Copy2"
        self.copy_name2 = "Copy3"
        self.copy_name3 = "Copy4"
        self.agent2 = self.commcell.clients.get(self.client2).agents.get(self.tcinputs["AgentName"])

        ma_client_list = [self.source_ma, self.destination_ma, self.client]
        if len(set(ma_client_list)) != 3:
            self.log.error("Client, MA1 and MA2 are not unique machines")
            raise Exception("Client MA1 and MA2 have to be unique machines.")

        self.log.info("Creating MediaAgent objects")
        self.source_ma_o = self.commcell.media_agents.get(self.source_ma)
        self.destination_ma_o = self.commcell.media_agents.get(self.destination_ma)

        self.log.info("Getting drives from MediaAgent and client")
        (self.client_machine, self.client_path) = self.ma_helper.generate_automation_path(self.client, 15000)
        (self.client_machine2, self.client_path2) = self.ma_helper.generate_automation_path(self.client2, 15000)
        (self.source_ma_machine, self.source_ma_path) = self.ma_helper.generate_automation_path(self.source_ma, 15000)
        (self.destination_ma_machine, self.destination_ma_path) = self.ma_helper.generate_automation_path(
            self.destination_ma, 15000)

        self.log.info("Generating paths")
        self.source_lib_path = self.source_ma_machine.join_path(self.source_ma_path,"SourceMP")
        self.log.info(f"Source library path: {self.source_lib_path}")

        self.destination_lib_path = self.destination_ma_machine.join_path(self.destination_ma_path, "DestinationMP1")
        self.log.info(f"Destination library path: {self.destination_lib_path}")

        self.destination_lib_path2 = self.destination_ma_machine.join_path(self.destination_ma_path, "DestinationMP2")
        self.log.info(f"Destination library path: {self.destination_lib_path2}")

        self.destination_lib_path3 = self.destination_ma_machine.join_path(self.destination_ma_path, "DestinationMP3")
        self.log.info(f"Destination library path: {self.destination_lib_path3}")

        self.primary_ddb_path = self.source_ma_machine.join_path(self.source_ma_path, "DDB")
        self.log.info(f"Primary copy DDB path: {self.primary_ddb_path}")

        self.secondary_ddb_path = self.destination_ma_machine.join_path(self.destination_ma_path, "DDB1")
        self.log.info(f"Secondary copy DDB path for copy {self.copy_name}: {self.secondary_ddb_path}")

        self.secondary_ddb_path2 = self.destination_ma_machine.join_path(self.destination_ma_path, "DDB2")
        self.log.info(f"Secondary copy DDB path for copy {self.copy_name2}: {self.secondary_ddb_path2}")

        self.secondary_ddb_path3 = self.destination_ma_machine.join_path(self.destination_ma_path, "DDB3")
        self.log.info(f"Secondary copy DDB path for copy {self.copy_name3}: {self.secondary_ddb_path3}")

        self.client_content = self.client_machine.join_path(self.client_path, "Content")
        self.log.info(f"Client content path: {self.client_content}")

        self.client_content2 = self.client_machine2.join_path(self.client_path2,"Content")
        self.log.info(f"Client content_2 path: {self.client_content2}")

    def create_pool(self, pool_name, library_path, ma_obj, ddb_path):
        """
        Creates secondary copy
        Args:
            pool_name (str) - Storage Pool name
            library_path (str) - Librray path for the pool
            ma_obj(Object) - object of MediaAgent class that will be used for library and DDB1
            ddb_path(str) - DDB location
        """

        self.log.info(f"Creating storage pool[{pool_name}]")
        pool_obj = self.commcell.storage_pools.add(pool_name, library_path, ma_obj, ma_obj, ddb_path)
        self.log.info("Storage pool created successfully")
        pool_copy_o = pool_obj.get_copy()
        return pool_obj, pool_copy_o

    def create_secondary_copy(self, pool_name, copy_name):
        """
        Creates secondary copy
        Args:
            pool_name (str) - Storage Pool name
            copy_name ( str) - Secondary copy name
        """

        self.log.info(f"Creating copy [{copy_name}] with storage pool [{pool_name}]")
        self.sp_obj.create_secondary_copy(copy_name, global_policy=pool_name)
        self.log.info(f"Copy[{copy_name}] created successfully")

        self.log.info(f"Removing copy [{copy_name}] from auto copy schedule")
        self.ma_helper.remove_autocopy_schedule(self.sp_name, copy_name)

        self.log.info(f"Disabling space optimization on copy[{copy_name}]")
        copy_o = self.sp_obj.get_copy(copy_name)
        copy_o.space_optimized_auxillary_copy = False

    def cleanup(self):
        """Cleanup SC, BS,SP, Library """

        self.log.info(f"Deleting BackupSet[{self.bs_name}] if exists")
        if self._agent.backupsets.has_backupset(self.bs_name):
            self.log.info(f"BackupSet[{self.bs_name}] exists, deleting that")
            self._agent.backupsets.delete(self.bs_name)

        self.log.info(f"Deleting BackupSet[{self.bs_name2}] if exists")
        if self.agent2.backupsets.has_backupset(self.bs_name2):
            self.log.info(f"BackupSet[{self.bs_name2}] exists, deleting that")
            self.agent2.backupsets.delete(self.bs_name2)

        self.log.info("Deleting Storage Policy if exists")
        if self.commcell.storage_policies.has_policy(self.sp_name):
            self.log.info(f"Storage Policy[{self.sp_name}] exists")
            self.log.info("Re-associating all sub clients before deleting the SP")
            self.sp_obj_to_reassociate = self.commcell.storage_policies.get(self.sp_name)
            self.sp_obj_to_reassociate.reassociate_all_subclients()
            self.log.info(f"Deleting the SP {self.sp_name}")
            self.commcell.storage_policies.delete(self.sp_name)

        self.log.info(f"Deleting Storage Pool[{self.pool_primary_name}] if exists")
        if self.commcell.storage_pools.has_storage_pool(self.pool_primary_name):
            self.log.info(f"Storage Pool [{self.pool_primary_name}] exists, deleting that")
            self.commcell.storage_pools.delete(self.pool_primary_name)

        self.log.info(f"Deleting Storage Pool[{self.pool_secondary_name}] if exists")
        if self.commcell.storage_pools.has_storage_pool(self.pool_secondary_name):
            self.log.info(f"Storage Pool [{self.pool_secondary_name}] exists, deleting that")
            self.commcell.storage_pools.delete(self.pool_secondary_name)

        self.log.info(f"Deleting Storage Pool[{self.pool_secondary_name2}] if exists")
        if self.commcell.storage_pools.has_storage_pool(self.pool_secondary_name2):
            self.log.info(f"Storage Pool [{self.pool_secondary_name2}] exists, deleting that")
            self.commcell.storage_pools.delete(self.pool_secondary_name2)

        self.log.info(f"Deleting Storage Pool[{self.pool_secondary_name3}] if exists")
        if self.commcell.storage_pools.has_storage_pool(self.pool_secondary_name3):
            self.log.info(f"Storage Pool [{self.pool_secondary_name3}] exists, deleting that")
            self.commcell.storage_pools.delete(self.pool_secondary_name3)

        self.log.info("Cleanup completed")

    def tear_down(self):
        """Tear Down Function of this Case"""
        self.log.info("This is Tear Down method")

        try:

            self.set_mm_config_value(1)

            if self.status != constants.FAILED:
                self.log.info("Test case completed, deleting BS, SP")
                self.cleanup()
            else:
                self.log.info("Test case failed, NOT deleting SC, BS, SP")

            if self.is_client_directory_created:
                self.log.info("Deleting the SubClient content directory")
                self.ma_helper.remove_content(self.client_content, self.client_machine)

            if self.is_client_directory_created2:
                self.log.info("Deleting the SubClient content directory")
                self.ma_helper.remove_content(self.client_content2, self.client_machine2)

        except Exception as excp:
            self.log.error(f"Cleanup failed with error: {excp}")
            self.result_string = str(f"Cleanup failed. {excp}")

    def run_backups(self, client, client_content, subclient_o):
        """
        Runs multiple backup

        Args:
            client(str) - name of the client
            client_content(str) - path for client content
            subclient_o(Object) - object of Subclient class
        """

        self.log.info("Will run multiple backups")
        i = 3  # Number of jobs to run
        while i > 0:
            self.log.info("Generating SubClient content")
            self.ma_helper.create_uncompressable_data(client, client_content, 1)

            # Starting backup
            self.log.info("Starting backup")
            self.job_obj = subclient_o.backup("FULL")
            self.log.info(f"Job started, waiting for the job completion. Job ID: {self.job_obj.job_id}")
            self.ma_helper.wait_for_job_completion(self.job_obj)

            i = i - 1

    def validate_from_log(self, job_id):
        """
        Performs validation from log

        Args:
            job_id (int): Job ID
        """

        matched_line = None
        ptrn = f"Removed KeyId Map for Job \[{job_id}\] from  Encryption keys cache. Remaining maps \[[0-2]\]"
        
        self.log.info(f"Searching for the pattern [{ptrn}] on source MediaAgent[{self.source_ma}]")
        (matched_line, matched_string) = self.dedupe_helper.parse_log(self.source_ma, "CipherCache.log", ptrn,
                                                                      escape_regex=False, single_file=False)
        if matched_line is not None:
            self.log.info("Found the following line(s):")
            for l in matched_line:
                self.log.info(l)
            if len(matched_line) !=1:
                self.log.error(f"There should be exactly 1 log line with this pattern matched. Found {len(matched_line)}")
                raise Exception(f"There should be exactly 1 log line with this pattern matched. Found {len(matched_line)}")
            self.log.info(f"Log verification completed for job[{job_id}]")
        else:
            self.log.error(f"Log line not found. Pattern: {ptrn}")
            raise Exception(f"Log line not found. Pattern: {ptrn}")

    def configure_sub_client(self, bs_name, sc_name, client_content, agent):
        """ Configure the sub client
        Args:
            bs_name(str) - name of backup set
            sc_name(str) - name of sub client
            client_content(str) - location for lcient content
            agent(Object) - object of Agent class
        """

        self.log.info("Creating backup set")
        agent.backupsets.add(bs_name)

        # Creating sub client
        self.log.info(f"Creating sub-client[{sc_name}]")
        subclient = self.ma_helper.configure_subclient(bs_name, sc_name, self.sp_name, client_content, agent)
        return subclient

    def set_mm_config_value(self, value):
        """
        Set MMConfig value of config MMCONFIG_AUXCOPY_COPY_FIRST_FULL_FOR_NEW_SUBCLIENT
        Args:
            value (int): value that needs to be set
        """

        self.log.info(f"Setting MMCONFIG_AUXCOPY_COPY_FIRST_FULL_FOR_NEW_SUBCLIENT to {value} on MMConfigs")
        self.ma_helper.update_mmconfig_param("MMCONFIG_AUXCOPY_COPY_FIRST_FULL_FOR_NEW_SUBCLIENT",0,value)
        self.log.info("Completed")

    def run(self):
        try:

            self.log.info("Cleaning-up SC,BS,SP,Libraries if exists")
            self.cleanup()

            # Creating storage pool
            self.primary_pool_o, self.primary_pool_copy_o = self.create_pool(self.pool_primary_name,
                                                                             self.source_lib_path, self.source_ma,
                                                                             self.primary_ddb_path)
            self.is_source_ma_directory_created = True

            self.secondary_pool_o, self.secondary_pool_copy_o = self.create_pool(self.pool_secondary_name,
                                                                                 self.destination_lib_path,
                                                                                 self.destination_ma,
                                                                                 self.secondary_ddb_path)
            self.is_destination_ma_directory_created = True
            self.secondary_pool_o2, self.secondary_pool_copy_o2 = self.create_pool(self.pool_secondary_name2,
                                                                                 self.destination_lib_path2,
                                                                                 self.destination_ma,
                                                                                 self.secondary_ddb_path2)

            self.secondary_pool_o3, self.secondary_pool_copy_o3 = self.create_pool(self.pool_secondary_name3,
                                                                                   self.destination_lib_path3,
                                                                                   self.destination_ma,
                                                                                   self.secondary_ddb_path3)
                                                                                   
            self.log.info("Enabling encryption on storage pools")
            self.ma_helper.set_encryption(self.primary_pool_copy_o)
            self.ma_helper.set_encryption(self.secondary_pool_copy_o)
            self.ma_helper.set_encryption(self.secondary_pool_copy_o2)
            self.ma_helper.set_encryption(self.secondary_pool_copy_o3)

            # Creating SP
            self.log.info(f"Creating storage policy[{self.sp_name}]")
            self.sp_obj = self.commcell.storage_policies.add(self.sp_name, global_policy_name=self.pool_primary_name, global_dedup_policy=True)
            self.log.info("Storage Policy created successfully")

            # Creating secondary copy
            self.create_secondary_copy(self.pool_secondary_name, self.copy_name)
            self.create_secondary_copy(self.pool_secondary_name2, self.copy_name2)
            self.create_secondary_copy(self.pool_secondary_name3, self.copy_name3)

            self.subclient = self.configure_sub_client(self.bs_name, self.sc_name, self.client_content, self._agent)
            self.subclient2 = self.configure_sub_client(self.bs_name2, self.sc_name2, self.client_content2, self.agent2)

            # running backups
            #self.run_backups(self.client2, self.client_content2, self.subclient2)
            t1 = threading.Thread(target=self.run_backups, args=(self.client2, self.client_content2, self.subclient2,))
            self.is_client_directory_created = True

            #self.run_backups(self.client, self.client_content, self.subclient)
            t2 = threading.Thread(target=self.run_backups, args=(self.client, self.client_content, self.subclient,))
            self.is_client_directory_created2 = True
            
            self.log.info("Starting threads to run backup on each sub clients")
            self.log.info("Will wait till all the threads completed")
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            self.log.info("Threads completed")
            
            self.set_mm_config_value(0)

            self.log.info(f"Starting aux copy job for copy[{self.copy_name}]")
            self.job_obj1 = self.sp_obj.run_aux_copy(self.copy_name, all_copies=False, streams=1)
            self.log.info(f"Job started. Job ID: {self.job_obj1.job_id}")
           
            time.sleep(90)
            
            self.log.info(f"Starting aux copy job for copy[{self.copy_name2}]")
            self.job_obj2 = self.sp_obj.run_aux_copy(self.copy_name2, all_copies=False, streams=1)
            self.log.info(f"Job started. Job ID: {self.job_obj2.job_id}")
            
            time.sleep(90)

            self.log.info(f"Starting aux copy job for copy[{self.copy_name3}]")
            self.job_obj3 = self.sp_obj.run_aux_copy(self.copy_name3, all_copies=False, streams=1)
            self.log.info(f"Job started. Job ID: {self.job_obj3.job_id}")

            if self.ma_helper.wait_for_job_completion(self.job_obj1) and self.ma_helper.wait_for_job_completion(self.job_obj2) and self.ma_helper.wait_for_job_completion(self.job_obj3):
                self.log.info("All 3 the aux copy job completed successfully")

            # Sometimes the no end time is returned by the API immediately after completing the job. Adding a sleep of 10 sec
            time.sleep(10)
            self.job_obj1.refresh()
            self.job_obj2.refresh()
            self.job_obj3.refresh()

            self.log.info(f"Job: {self.job_obj1.job_id} end time: {self.job_obj1.end_time}")
            self.log.info(f"Job: {self.job_obj2.job_id} end time: {self.job_obj2.end_time}")
            self.log.info(f"Job: {self.job_obj3.job_id} end time: {self.job_obj3.end_time}")

            # Validating from log
            self.validate_from_log(self.job_obj1.job_id)
            self.validate_from_log(self.job_obj2.job_id)
            self.validate_from_log(self.job_obj3.job_id)

            self.log.info("Test case completed successfully.")

        except Exception as excp:
            self.log.error(f"Failed with error: {excp}")
            self.result_string = str(excp)
            self.status = constants.FAILED
