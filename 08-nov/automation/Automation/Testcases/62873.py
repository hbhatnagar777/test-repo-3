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

    create_pool()  --  Creates secondary copy

    create_secondary_copy()  --  Creates secondary copy

    cleanup()  --  Cleanup SC, BS,SP, Library

    tear_down() --  Tear Down Function of this Case
    
    run_backups() -- Runs backup
    
    get_key_id_of_first_job()  --  Fetch the AF ID list of first backup job
    
    validate_from_log()  --  Performs validation from log
    
    configure_sub_client()  -- Configure the sub client
    
    set_mm_config_value()  --  Set MMConfig value of config MMCONFIG_AUXCOPY_COPY_FIRST_FULL_FOR_NEW_SUBCLIENT
    
    get_af_id_count()  --  Fetch AF ID count of last 4 jobs
    
    wait_for_ma_online()  --  Waits MediaAgent to come online
    
    get_key_id_count()  --  Fetch keyID count of last 4 jobs
    

    Input Example:

    "testCases": {
				"62873": {
					"ClientName1": "client1",
					"ClientName2": "client2",
					"ClientName3": "client3",
					"ClientName4": "client4",
					"ClientName5": "client5",
					"AgentName": "File System",
					"MA1": "MediaAgent1",
					"MA2": "MediaAgent2"
					}
                }
                
                
                
                
    Note : There should not any other aux copy using the source MA while running this case. This case may be failed on that case.
    
"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper

class TestCase(CVTestCase):
    """Verify registry key KeyMapAfIdLowWaterMark for encryption key cleanup"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Verify registry key KeyMapAfIdLowWaterMark for encryption key cleanup"

        self.tcinputs = {
            "ClientName1": None,
            "ClientName2": None,
            "ClientName3": None,
            "ClientName4": None,
            "ClientName5": None,
            "AgentName": None,
            "MA1": None,
            "MA2": None
        }

        self.ma_helper = None
        self.dedupe_helper = None

        self.sp_name = None
        self.pool_primary_name = None
        self.pool_secondary_name = None
        self.bs_name = None
        self.sc_name = None
        self.source_ma = None
        self.destination_ma = None
        self.client1 = None
        self.client2 = None
        self.client3 = None
        self.client4 = None
        self.client5 = None
        self.copy_name = None

        self.agent1 = None
        self.agent2 = None
        self.agent3 = None
        self.agent4 = None
        self.agent5 = None

        self.source_ma_o = None
        self.destination_ma_o = None

        self.client_machine1 = None
        self.client_path1 = None
        self.client_machine2 = None
        self.client_path2 = None
        self.client_machine3 = None
        self.client_path3 = None
        self.client_machine4 = None
        self.client_path4 = None
        self.client_machine5 = None
        self.client_path5 = None

        self.commcell_machine = None
        self.commcell_path = None

        self.source_ma_machine = None
        self.source_ma_path = None
        self.destination_ma_machine = None
        self.destination_ma_path = None
        self.destination_ma = None

        self.source_lib_path = None
        self.destination_lib_path = None

        self.primary_ddb_path = None
        self.secondary_ddb_path = None
        self.client_content1 = None
        self.client_content2 = None
        self.client_content3 = None
        self.client_content4 = None
        self.client_content5 = None
        self.file_name = None

        self.primary_pool_o = None
        self.primary_pool_copy_o = None
        self.is_source_ma_directory_created = None
        self.secondary_pool_o = None
        self.secondary_pool_copy_o = None
        self.is_destination_ma_directory_created = None

        self.sp_obj = None
        self.copy_o = None

        self.subclient1 = None
        self.subclient2 = None
        self.subclient3 = None
        self.subclient4 = None
        self.subclient5 = None

        self.job_obj1 = None
        self.is_client_directory_created1 = None
        self.job_obj2 = None
        self.is_client_directory_created2 = None
        self.job_obj3 = None
        self.is_client_directory_created3 = None
        self.job_obj4 = None
        self.is_client_directory_created4 = None
        self.job_obj5 = None
        self.is_client_directory_created5 = None
        self.aux_job_obj = None

    def setup(self):
        """Setup function of this test case"""

        self.log.info("This is setup method of the test case")
        self.ma_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

        self.sp_name = f"automation_{self.id}_sp_{self.source_ma}_{self.destination_ma}"
        self.pool_primary_name = f"automation_{self.id}_primary_pool_{self.source_ma}"
        self.pool_secondary_name = f"automation_{self.id}_secondary_pool_{self.destination_ma}"
        self.bs_name = f"automation_{self.id}_BS"
        self.sc_name = f"automation_{self.id}_SC"
        self.source_ma = self.tcinputs['MA1']
        self.destination_ma = self.tcinputs['MA2']
        self.client1 = self.tcinputs['ClientName1']
        self.client2 = self.tcinputs['ClientName2']
        self.client3 = self.tcinputs['ClientName3']
        self.client4 = self.tcinputs['ClientName4']
        self.client5 = self.tcinputs['ClientName5']
        self.copy_name = "Copy2"

        self.agent1 = self.commcell.clients.get(self.client1).agents.get(self.tcinputs["AgentName"])
        self.agent2 = self.commcell.clients.get(self.client2).agents.get(self.tcinputs["AgentName"])
        self.agent3 = self.commcell.clients.get(self.client3).agents.get(self.tcinputs["AgentName"])
        self.agent4 = self.commcell.clients.get(self.client4).agents.get(self.tcinputs["AgentName"])
        self.agent5 = self.commcell.clients.get(self.client5).agents.get(self.tcinputs["AgentName"])

        ma_client_list = [self.source_ma, self.destination_ma]
        if len(set(ma_client_list)) != 2:
            self.log.error("Source and destination MediaAgent can't be same.")
            raise Exception("Source and destination MediaAgent can't be same.")

        client_list = [ self.client1, self.client2, self.client3, self.client4, self.client5]
        if len(set(client_list)) != 5:
            self.log.error("5 unique clients are required, found duplicate")
            raise Exception("5 unique clients are required, found duplicate")

        self.log.info("Creating MediaAgent objects")
        self.source_ma_o = self.commcell.media_agents.get(self.source_ma)
        self.destination_ma_o = self.commcell.media_agents.get(self.destination_ma)

        self.log.info("Getting drives from MediaAgent and client")
        (self.client_machine1, self.client_path1) = self.ma_helper.generate_automation_path(self.client1, 15000)
        (self.client_machine2, self.client_path2) = self.ma_helper.generate_automation_path(self.client2, 15000)
        (self.client_machine3, self.client_path3) = self.ma_helper.generate_automation_path(self.client3, 15000)
        (self.client_machine4, self.client_path4) = self.ma_helper.generate_automation_path(self.client4, 15000)
        (self.client_machine5, self.client_path5) = self.ma_helper.generate_automation_path(self.client5, 15000)

        # we are not going to use commcell_path, we just need the machine object of commcell machine
        (self.commcell_machine, self.commcell_path) = self.ma_helper.generate_automation_path(self.commcell.commserv_client.client_name, 100)

        (self.source_ma_machine, self.source_ma_path) = self.ma_helper.generate_automation_path(self.source_ma, 15000)
        (self.destination_ma_machine, self.destination_ma_path) = self.ma_helper.generate_automation_path(
            self.destination_ma, 15000)

        self.log.info("Generating paths")
        self.source_lib_path = self.source_ma_machine.join_path(self.source_ma_path, "SourceMP")
        self.log.info(f"Source library path: {self.source_lib_path}")

        self.destination_lib_path = self.destination_ma_machine.join_path(self.destination_ma_path, "DestinationMP1")
        self.log.info(f"Destination library path: {self.destination_lib_path}")

        self.primary_ddb_path = self.source_ma_machine.join_path(self.source_ma_path, "DDB")
        self.log.info(f"Primary copy DDB path: {self.primary_ddb_path}")

        self.secondary_ddb_path = self.destination_ma_machine.join_path(self.destination_ma_path, "DDB1")
        self.log.info(f"Secondary copy DDB path: {self.secondary_ddb_path}")

        self.client_content1 = self.client_machine1.join_path(self.client_path1, "Content")
        self.log.info(f"Client [Client Name: {self.client1}] content path: {self.client_content1}")

        self.client_content2 = self.client_machine2.join_path(self.client_path2, "Content")
        self.log.info(f"Client [Client Name: {self.client2}] content path: {self.client_content2}")

        self.client_content3 = self.client_machine3.join_path(self.client_path3, "Content")
        self.log.info(f"Client [Client Name: {self.client3}] content path: {self.client_content3}")

        self.client_content4 = self.client_machine4.join_path(self.client_path4, "Content")
        self.log.info(f"Client [Client Name: {self.client4}] content path: {self.client_content4}")

        self.client_content5 = self.client_machine5.join_path(self.client_path5, "Content")
        self.log.info(f"Client [Client Name: {self.client5}] content path: {self.client_content5}")

    def create_pool(self, pool_name, library_path, ma_obj, ddb_path):
        """
        Creates secondary copy
        Args:
            pool_name (str) - storage Pool name
            library_path (str) - library location
            ma_obj (object) - object of MediaAgent class
            ddb_path (str) - path for deduplication database
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
        self.log.info(f"Successfully disabled space optimization on copy [{self.copy_name}]")
        return copy_o

    def cleanup(self):
        """Cleanup SC, BS,SP, Library """

        self.log.info(f"Deleting BackupSet[{self.bs_name}] on client[{self.client1}] if exists")
        if self.agent1.backupsets.has_backupset(self.bs_name):
            self.log.info(f"BackupSet[{self.bs_name}] exists, deleting that")
            self.agent1.backupsets.delete(self.bs_name)

        self.log.info(f"Deleting BackupSet[{self.bs_name}] on client[{self.client2}] if exists")
        if self.agent2.backupsets.has_backupset(self.bs_name):
            self.log.info(f"BackupSet[{self.bs_name}] exists, deleting that")
            self.agent2.backupsets.delete(self.bs_name)

        self.log.info(f"Deleting BackupSet[{self.bs_name}] on client[{self.client3}] if exists")
        if self.agent3.backupsets.has_backupset(self.bs_name):
            self.log.info(f"BackupSet[{self.bs_name}] exists, deleting that")
            self.agent3.backupsets.delete(self.bs_name)

        self.log.info(f"Deleting BackupSet[{self.bs_name}] on client[{self.client4}] if exists")
        if self.agent4.backupsets.has_backupset(self.bs_name):
            self.log.info(f"BackupSet[{self.bs_name}] exists, deleting that")
            self.agent4.backupsets.delete(self.bs_name)

        self.log.info(f"Deleting BackupSet[{self.bs_name}] on client[{self.client5}] if exists")
        if self.agent5.backupsets.has_backupset(self.bs_name):
            self.log.info(f"BackupSet[{self.bs_name}] exists, deleting that")
            self.agent5.backupsets.delete(self.bs_name)

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

        self.log.info("Cleanup completed")

    def tear_down(self):
        """Tear Down Function of this Case"""
        self.log.info("This is Tear Down method")

        self.set_mm_config_value(1)

        self.log.info("Setting client side deduplication configuration to \"Use storage policy settings\"")
        self.commcell.clients.get(self.client1).set_dedup_property("clientSideDeduplication", "USE_SPSETTINGS")

        self.log.info(f"Removing reg key cvd\KeyMapAfIdLowWaterMark from {self.source_ma}")
        self.commcell.clients.get(self.source_ma).delete_additional_setting("Cvd", "KeyMapAfIdLowWaterMark")

        self.log.info(f"Removing reg key cvd\KeyMapMaxTimeout from {self.source_ma}")
        self.commcell.clients.get(self.source_ma).delete_additional_setting("Cvd", "KeyMapMaxTimeout")

        self.log.info(f"Removing reg key cvd\\bEncKeyPrintMaps from {self.source_ma}")
        self.commcell.clients.get(self.source_ma).delete_additional_setting("Cvd", "bEncKeyPrintMaps")

        self.log.info(f"Removing reg key cvd\\KeyMapMaxSize from {self.source_ma}")
        self.commcell.clients.get(self.source_ma).delete_additional_setting("Cvd", "KeyMapMaxSize")

        self.log.info(f"Setting CVJobReplicatorODS debug level to 1 on source MA[{self.source_ma}]")
        self.source_ma_machine.set_logging_debug_level("CVJobReplicatorODS", "1")

        self.log.info(f"Setting CVJobReplicatorODS.log file limit to 5mb on source MA[{self.source_ma}]")
        self.source_ma_machine.set_logging_filesize_limit("CVJobReplicatorODS", 5)

        self.log.info("Restarting services of source MA after removing the reg key")
        self.commcell.clients.get(self.source_ma).restart_services(wait_for_service_restart = False)

        self.wait_for_ma_online()

        if self.file_name is not None:
            self.log.info("Checking if the aux copy job priority file exists or not, will delete if it exists")
            if self.commcell_machine.check_file_exists(self.commcell.commserv_client.install_directory + self.commcell_machine.os_sep + "Base" + self.commcell_machine.os_sep + self.file_name):
                self.log.info("Deleting the file that was created to prioritise the aux copy job")
                self.commcell_machine.delete_file(self.commcell.commserv_client.install_directory + self.commcell_machine.os_sep + "Base" + self.commcell_machine.os_sep + self.file_name)
                self.log.info("File deleted successfully")

        try:
            if self.status != constants.FAILED:
                self.log.info("Test case completed, deleting BS, SP")
                self.cleanup()
            else:
                self.log.info("Test case failed, NOT deleting SC, BS, SP")

            if self.is_client_directory_created1:
                self.log.info("Deleting the SubClient content directory")
                self.ma_helper.remove_content(self.client_content1, self.client_machine1)

            if self.is_client_directory_created2:
                self.log.info("Deleting the SubClient content directory")
                self.ma_helper.remove_content(self.client_content2, self.client_machine2)

            if self.is_client_directory_created3:
                self.log.info("Deleting the SubClient content directory")
                self.ma_helper.remove_content(self.client_content3, self.client_machine3)

            if self.is_client_directory_created4:
                self.log.info("Deleting the SubClient content directory")
                self.ma_helper.remove_content(self.client_content4, self.client_machine4)

            if self.is_client_directory_created5:
                self.log.info("Deleting the SubClient content directory")
                self.ma_helper.remove_content(self.client_content5, self.client_machine5)

        except Exception as excp:
            self.log.error(f"Cleanup failed with error: {excp}")
            self.result_string = str(f"Cleanup failed. {excp}")

    def run_backups(self, client, client_content, subclient_o):
        """
        Runs backup
            Args:
                client (str) - name of the client
                client_content ( str) - client content path
                subclient_o (object) - object of SubClient class
        """
        self.log.info("Generating SubClient content")
        self.ma_helper.create_uncompressable_data(client, client_content, 1)

        # Starting backup
        self.log.info("Starting backup")
        job_obj = subclient_o.backup("FULL")
        self.log.info(f"Job started. Job ID: {job_obj.job_id}")
        return job_obj

    def get_key_id_of_first_job(self):
        """
        Fetch the AF ID list of first backup job
        return: keyID (str)
        """
        self.log.info("Getting keyID of the first backup job")
        q = f"select distinct afc.encKeyId  from archFileCopy afc, archChunkMapping map  where afc.archFileId = map.archFileId and  map.jobId in ({self.job_obj1.job_id}) and afc.encKeyId!=0 order by afc.encKeyId asc"
        self.log.info("Executing the following query")
        self.log.info(q)
        self.csdb.execute(q)
        return self.csdb.fetch_one_row()[0]

    def validate_from_log(self):
        """
        Performs validation from log
        """
        matched_line = None
        key_of_1st_job = self.get_key_id_of_first_job()
        self.log.info(f"Key ID of First job: {key_of_1st_job}.  The ArchiveFiles of this keyID should be cleaned")
        ptrn = f"Removing archive file encryption key for keyId \[{key_of_1st_job}\] from the map. cipherRef \[[0-9]*\] refCount\[[0-9]*\]"

        self.log.info(f"Searching for the pattern [{ptrn}] on source MediaAgent[{self.source_ma}]")
        ( matched_line, matched_string ) = self.dedupe_helper.parse_log(self.source_ma, "CipherCache.log", ptrn, escape_regex=False, single_file=False)
        if matched_line is not None:
            self.log.info("Found the following line(s):")
            for l in matched_line:
                self.log.info(l)

            self.log.info(f"Log verification completed")
        else:
            self.log.error(f"Log line not found. Pattern: {ptrn}")
            raise Exception(f"Log line not found. Pattern: {ptrn}")

    def configure_sub_client(self, bs_name, sc_name, client_content, agent):
        """
        Configure the sub client
        Args:
            bs_name (str) - Name of backup set
            sc_name (str) - Name of sub client
            client_content (str) - Directory of client content
            agent (object) - Object of Agent class
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
        self.log.info("MMConfig updated")

    def get_af_id_count(self):
        """
        Fetch AF ID count of last 4 jobs

        Return: KeyID count
        """
        self.log.info("Getting encrypted ArchFile count of last 4 jobs")
        sql_query = f"select count(distinct afc.archFileId) " \
            " from archFileCopy afc, archChunkMapping map " \
            " where afc.archFileId = map.archFileId and " \
            f" map.jobId in ({self.job_obj2.job_id},{self.job_obj3.job_id},{self.job_obj4.job_id},{self.job_obj5.job_id})" \
            f" and afc.encKeyId!=0"

        self.log.info("Executing the following query to find the number of keyIDs on the last 4 jobs")
        self.log.info(sql_query)
        self.csdb.execute(sql_query)
        return self.csdb.fetch_one_row()[0]

    def wait_for_ma_online(self):
        """
        Waits MediaAgent to come online
        """
        count = 60 # will check for 600 seconds
        while count >0:
            self.log.info(f"Waiting for MediaAgent[{self.source_ma}] to come online")
            self.source_ma_o.refresh()
            if self.source_ma_o.is_online:
                self.log.info("MediaAgent is online")
                return;
            time.sleep(10)

        self.log.error("MediaAgent is not online after the restart")
        raise Exception("MediaAgent is not online after the restart")

    def get_key_id_count(self):
        """
        Fetch keyID count of last 4 jobs

        Return: KeyID count
        """
        self.log.info("Getting key ID count of last 4 jobs")
        sql_query = f"select count(distinct afc.encKeyId) " \
            " from archFileCopy afc, archChunkMapping map " \
            " where afc.archFileId = map.archFileId and " \
            f" map.jobId in ({self.job_obj2.job_id},{self.job_obj3.job_id},{self.job_obj4.job_id},{self.job_obj5.job_id})" \
            f" and afc.encKeyId!=0"

        self.log.info("Executing the following query to find the number of keyIDs on the last 4 jobs")
        self.log.info(sql_query)
        self.csdb.execute(sql_query)
        return self.csdb.fetch_one_row()[0]

    def run(self):
        try:
            self.log.info("Cleaning-up SC,BS,SP,Libraries if exists")
            self.cleanup()

            self.log.info(f"Disabling client side deduplication on client[{self.client1}]")
            self.commcell.clients.get(self.client1).set_dedup_property("clientSideDeduplication", "OFF")

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

            self.log.info("Enabling encryption on storage pools")
            self.ma_helper.set_encryption(self.primary_pool_copy_o)
            self.ma_helper.set_encryption(self.secondary_pool_copy_o)

            # Creating SP
            self.log.info(f"Creating storage policy[{self.sp_name}]")
            self.sp_obj = self.commcell.storage_policies.add(self.sp_name, global_policy_name=self.pool_primary_name, global_dedup_policy=True)
            self.log.info("Storage Policy created successfully")

            # Creating secondary copy
            self.copy_o = self.create_secondary_copy(self.pool_secondary_name, self.copy_name)

            self.subclient1 = self.configure_sub_client(self.bs_name, self.sc_name, self.client_content1, self.agent1)
            self.subclient2 = self.configure_sub_client(self.bs_name, self.sc_name, self.client_content2, self.agent2)
            self.subclient3 = self.configure_sub_client(self.bs_name, self.sc_name, self.client_content3, self.agent3)
            self.subclient4 = self.configure_sub_client(self.bs_name, self.sc_name, self.client_content4, self.agent4)
            self.subclient5 = self.configure_sub_client(self.bs_name, self.sc_name, self.client_content5, self.agent5)

            # running backups
            self.job_obj1 = self.run_backups(self.client1, self.client_content1, self.subclient1)
            self.is_client_directory_created1 = True

            self.job_obj2 = self.run_backups(self.client2, self.client_content2, self.subclient2)
            self.is_client_directory_created2 = True

            self.job_obj3 = self.run_backups(self.client3, self.client_content3, self.subclient3)
            self.is_client_directory_created3 = True

            self.job_obj4 = self.run_backups(self.client4, self.client_content4, self.subclient4)
            self.is_client_directory_created4 = True

            self.job_obj5 = self.run_backups(self.client5, self.client_content5, self.subclient5)
            self.is_client_directory_created5 = True

            self.ma_helper.wait_for_job_completion(self.job_obj1)
            self.ma_helper.wait_for_job_completion(self.job_obj2)
            self.ma_helper.wait_for_job_completion(self.job_obj3)
            self.ma_helper.wait_for_job_completion(self.job_obj4)
            self.ma_helper.wait_for_job_completion(self.job_obj5)
            self.log.info("All jobs completed successfully")

            self.log.info(f"Job [{self.job_obj1.job_id}] of client [{self.client1}] needs to be copied first. Creating aux copy job priority file.")
            file_content = f"{self.job_obj1.job_id},2"

            self.file_name = f"SP_{self.sp_obj.storage_policy_id}_SPC_{self.copy_o.get_copy_id()}_Jobs.txt"
            self.log.info(f"File name: {self.file_name}")
            self.log.info(f"File content: {file_content}")

            self.commcell_machine.create_file(self.commcell.commserv_client.install_directory + self.commcell_machine.os_sep + "Base" + self.commcell_machine.os_sep + self.file_name, file_content)
            self.log.info("File created successfully")

            af_id_count = self.get_af_id_count()
            self.log.info(f"Archive File count: {af_id_count}")

            self.log.info(f"Setting reg key KeyMapAfIdLowWaterMark on CVD of MA [{self.source_ma}]")
            self.commcell.clients.get(self.source_ma).add_additional_setting("Cvd", "KeyMapAfIdLowWaterMark", "INTEGER", str(af_id_count))

            self.log.info(f"Setting reg key KeyMapMaxTimeout=6000 on CVD of MA [{self.source_ma}]")
            self.commcell.clients.get(self.source_ma).add_additional_setting("Cvd", "KeyMapMaxTimeout", "INTEGER", "6000")

            self.log.info(f"Setting reg key bEncKeyPrintMaps on CVD of MA [{self.source_ma}]")
            self.commcell.clients.get(self.source_ma).add_additional_setting("Cvd", "bEncKeyPrintMaps", "INTEGER", "1")

            key_id_count = self.get_key_id_count()
            self.log.info(f"KeyID count: {key_id_count}")
            self.log.info(f"Setting reg key KeyMapMaxSize on CVD of MA [{self.source_ma}]")
            self.commcell.clients.get(self.source_ma).add_additional_setting("Cvd", "KeyMapMaxSize", "INTEGER", str(key_id_count))

            self.log.info(f"Setting CVJobReplicatorODS debug level to 10 on source MA[{self.source_ma}]")
            self.source_ma_machine.set_logging_debug_level("CVJobReplicatorODS", "10")

            self.log.info(f"Setting CVJobReplicatorODS.log file limit to 20mb on source MA[{self.source_ma}]")
            self.source_ma_machine.set_logging_filesize_limit("CVJobReplicatorODS", 20)

            self.log.info(f"Restarting services of source MA[{self.source_ma}] after setting the reg key")
            self.commcell.clients.get(self.source_ma).restart_services(wait_for_service_restart = False)

            self.wait_for_ma_online()

            self.set_mm_config_value(0)

            self.log.info(f"Starting aux copy job for copy[{self.copy_name}]")
            self.aux_job_obj = self.sp_obj.run_aux_copy(self.copy_name, all_copies=False, streams=1)
            self.log.info(f"Job started. Job ID: {self.aux_job_obj.job_id}")
            self.ma_helper.wait_for_job_completion(self.aux_job_obj)

            self.validate_from_log()

            self.log.info("Test case completed successfully.")

        except Exception as excp:
            self.log.error(f"Failed with error: {excp}")
            self.result_string = str(excp)
            self.status = constants.FAILED