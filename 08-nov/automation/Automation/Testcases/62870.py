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
    
    create_pool()   --  Creates storage pool
    
    create_secondary_copy() --  Creates secondary copy
    
    cleanup()   --  Cleanup SC, BS,SP, Library etc

    tear_down() --  Tear Down Function of this Case
    
    run_backups()   --  Runs backup
    
    validate_from_log() --  Performs log validation
    
    configure_sub_client()  --  Configure the sub client
    
    Input Example:

    "testCases": {


				"62870": {
					"ClientName": "client",
					"ClientName2": "client",
					"AgentName": "File System",
					"MA1": "MAName1",
					"MA2": "MAName2"
				}
                }

Please note, Client, Client2, MA1 and MA2 have to be unique machines

"""
import random
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper

class TestCase(CVTestCase):
    """Encryption key cleanup::removing the cache at the end of aux copy job"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Encryption key cleanup::removing the cache at the end of aux copy job"

        self.tcinputs = {
            "ClientName": None,
            "ClientName2": None,
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
        self.is_client2_directory_created = None
        self.job_obj = None

    def setup(self):
        """Setup function of this test case"""

        self.log.info("This is setup method of the test case")
        self.ma_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

        self.sp_name = f"automation_{self.id}_sp"
        self.pool_primary_name = f"automation_{self.id}_primary_pool"
        self.pool_secondary_name = f"automation_{self.id}_secondary_pool"
        self.bs_name = f"automation_{self.id}_BS"
        self.bs_name2 = f"automation_{self.id}_BS_2"
        self.sc_name = f"automation_{self.id}_SC"
        self.sc_name2 = f"automation_{self.id}_SC_2"
        self.source_ma = self.tcinputs['MA1']
        self.destination_ma = self.tcinputs['MA2']
        self.client = self.tcinputs['ClientName']
        self.client2 = self.tcinputs['ClientName2']
        self.copy_name = "Copy2"
        self.agent2 = self.commcell.clients.get(self.client2).agents.get(self.tcinputs["AgentName"])

        ma_client_list = [self.source_ma,self.destination_ma,self.client, self.client2]
        if len(set(ma_client_list)) != 4:
            self.log.error("Client, Client2, MA1 and MA2 are not unique machines")
            raise Exception("Client, Client2, MA1 and MA2 have to be unique machines.")

        self.log.info("Creating MediaAgent objects")
        self.source_ma_o = self.commcell.media_agents.get(self.source_ma)
        self.destination_ma_o = self.commcell.media_agents.get(self.destination_ma)

        self.log.info("Getting drives from MediaAgent and client")
        (self.client_machine, self.client_path) = self.ma_helper.generate_automation_path(self.client, 15000)
        (self.client_machine2, self.client_path2) = self.ma_helper.generate_automation_path(self.client2, 15000)
        (self.source_ma_machine, self.source_ma_path) = self.ma_helper.generate_automation_path(self.source_ma, 15000)
        (self.destination_ma_machine, self.destination_ma_path) = self.ma_helper.generate_automation_path(self.destination_ma, 15000)

        self.log.info("Generating paths")
        self.source_lib_path = self.source_ma_machine.join_path(self.source_ma_path,"SourceMP")
        self.log.info(f"Source library path: {self.source_lib_path}")

        self.destination_lib_path = self.source_ma_machine.join_path(self.destination_ma_path,"DestinationMP")
        self.log.info(f"Destination library path: {self.destination_lib_path}")

        self.primary_ddb_path = self.source_ma_machine.join_path(self.source_ma_path,"DDB")
        self.log.info(f"Primary copy DDB path: {self.primary_ddb_path}")

        self.secondary_ddb_path = self.source_ma_machine.join_path(self.destination_ma_path,"DDB")
        self.log.info(f"Secondary copy DDB path: {self.secondary_ddb_path}")

        self.client_content = self.source_ma_machine.join_path(self.client_path,"Content")
        self.log.info(f"Client content path: {self.client_content}")

        self.client_content2 = self.source_ma_machine.join_path(self.client_path2,"Content")
        self.log.info(f"Client content_2 path: {self.client_content2}")

    def create_pool(self, pool_name, library_path, ma_obj, ddb_path):
        """
        Creates storage pool
        Args:
            pool_name (str) - Storage Pool name
            library_path (str) - Library path of the stoarge pool
            ma_obj (object) - MediaAgent class object of library and DDB MediaAgent
            ddb_path (str) - Path of Deduplication database
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
            copy_name (str) - Secondary copy name
        """
        self.log.info(f"Creating copy [{copy_name}] with storage pool [{pool_name}]")
        self.sp_obj.create_secondary_copy(copy_name,global_policy=pool_name)
        self.log.info(f"Copy[{copy_name}] created successfully")

        self.log.info(f"Removing copy [{copy_name}] from auto copy schedule")
        self.ma_helper.remove_autocopy_schedule(self.sp_name, copy_name)

        self.log.info(f"Disabling space optimization on copy[{copy_name}]")
        copy_o = self.sp_obj.get_copy(copy_name)
        copy_o.space_optimized_auxillary_copy = False

    def cleanup(self):
        """Cleanup SC, BS,SP, Library etc"""

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
        if self.commcell.storage_policies.has_policy(self.pool_primary_name):
            self.log.info(f"Storage Pool [{self.pool_primary_name}] exists, deleting that")
            self.commcell.storage_policies.delete(self.pool_primary_name)

        self.log.info(f"Deleting Storage Pool[{self.pool_secondary_name}] if exists")
        if self.commcell.storage_policies.has_policy(self.pool_secondary_name):
            self.log.info(f"Storage Pool [{self.pool_secondary_name}] exists, deleting that")
            self.commcell.storage_policies.delete(self.pool_secondary_name)

        self.log.info("Cleanup completed")

    def tear_down(self):
        """Tear Down Function of this Case"""
        self.log.info("This is Tear Down method")

        try:
            self.cleanup()

            if self.is_client_directory_created:
                self.log.info("Deleting the SubClient content directory")
                self.ma_helper.remove_content(self.client_path, self.client_machine)

            if self.is_client2_directory_created:
                self.log.info("Deleting the SubClient content directory")
                self.ma_helper.remove_content(self.client_path2, self.client_machine2)

        except Exception as excp:
            self.log.error(f"Cleanup failed with error: {excp}")
            self.result_string = str(f"Cleanup failed. {excp}")

    def run_backups(self, client, client_content, subclient_o):
        """
        Runs backup
        Args:
             client (str) - name of the client
             client_content (str) - client content path
             subclient_o (object) - SubClient class object
        """
        self.log.info("Will run multiple backups")
        i = 5  # Number of jobs to run
        while i > 0:
            self.log.info("Generating SubClient content")
            self.ma_helper.create_uncompressable_data(client, client_content, 1)

            # Starting backup
            self.log.info("Starting backup")
            self.job_obj = subclient_o.backup("FULL")
            self.log.info(f"Job started, waiting for the job completion. Job ID: {self.job_obj.job_id}")
            self.ma_helper.wait_for_job_completion(self.job_obj)
            i = i - 1

    def validate_from_log(self):
        """
        Performs log validation
        """
        ptrn = f"Removed KeyId Map for Job \[{self.job_obj.job_id}\] from  Encryption keys cache. Remaining maps \[0\]"
        self.log.info(f"Searching for the pattern [{ptrn}] on source MediaAgent[{self.source_ma}]")
        (matched_line, matched_string) = self.dedupe_helper.parse_log(self.source_ma, "CipherCache.log", ptrn,escape_regex=False, single_file=False)
        if matched_line:
            self.log.info("Log verification passed")
            return

        self.log.error("Log verification failed")
        raise Exception("Log verification failed")

    def configure_sub_client(self, bs_name, sc_name, client_content, agent):
        """
        Configure the sub client
        Args:
            bs_name(str) - name of the BackupSet
            sc_name(str) - name of the SubClient
            client_content(str) - client content path
            agent(object) - object of Agent class
        """
        self.log.info("Creating backup set")
        agent.backupsets.add(bs_name)

        # Creating sub client
        self.log.info(f"Creating sub-client[{sc_name}]")
        subclient = self.ma_helper.configure_subclient(bs_name, sc_name, self.sp_name, client_content, agent)
        return subclient

    def run(self):
        try:

            self.log.info("Cleaning-up SC,BS,SP,Libraries if exists")
            self.cleanup()

            # Creating storage pool
            self.primary_pool_o, self.primary_pool_copy_o = self.create_pool(self.pool_primary_name, self.source_lib_path, self.source_ma, self.primary_ddb_path)
            self.is_source_ma_directory_created = True

            self.secondary_pool_o, self.secondary_pool_copy_o = self.create_pool(self.pool_secondary_name, self.destination_lib_path, self.destination_ma, self.secondary_ddb_path)
            self.is_destination_ma_directory_created = True

            enc_list = ["Blowfish","TwoFish","Serpent","AES"]
            enc_key = [128,256]

            self.log.info(f"Enabling encryption on storage pool[{self.pool_primary_name}]")
            self.primary_pool_copy_o.set_encryption_properties(re_encryption=True, encryption_type=random.choice(enc_list), encryption_length=random.choice(enc_key))

            self.log.info(f"Enabling re-encryption on storage pool[{self.pool_secondary_name}]")
            self.secondary_pool_copy_o.set_encryption_properties(re_encryption=True,encryption_type=random.choice(enc_list), encryption_length=random.choice(enc_key))

            # Creating SP
            self.log.info(f"Creating storage policy[{self.sp_name}]")
            self.sp_obj = self.commcell.storage_policies.add(self.sp_name, global_policy_name = self.pool_primary_name, number_of_streams=1, global_dedup_policy  = True)
            self.log.info("Storage Policy created successfully")

            # Creating secondary copy
            self.create_secondary_copy(self.pool_secondary_name, self.copy_name)

            self.subclient = self.configure_sub_client(self.bs_name, self.sc_name, self.client_content, self._agent)
            self.subclient2 = self.configure_sub_client(self.bs_name2, self.sc_name2, self.client_content2, self.agent2)

            # running backups
            self.is_client_directory_created = True
            self.run_backups(self.client2, self.client_content2, self.subclient2)

            self.is_client2_directory_created = True
            self.run_backups(self.client, self.client_content, self.subclient)

            self.log.info("Starting aux copy job")
            self.job_obj = self.sp_obj.run_aux_copy(self.copy_name, all_copies=False)
            self.log.info(f"Job started, waiting for the job completion. Job ID: {self.job_obj.job_id}")
            self.ma_helper.wait_for_job_completion(self.job_obj)

            # Validating from log
            self.validate_from_log()
            self.log.info("Test case completed successfully.")

        except Exception as excp:
            self.log.error(f"Failed with error: {excp}")
            self.result_string = str(excp)
            self.status = constants.FAILED