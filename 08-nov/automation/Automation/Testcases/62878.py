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

    create_secondary_copy()  --  Creates aux copy
    
    run_backups()   --  runs backup
    
    configure_sub_client()  --  configures subclient
    
    rotate_master_key() --  Rotates encryption master key
    
    log_verification()  --  performsverification from log
    
    compare_log_matching()  --  Compares the log line match count with the previously matched count
    
    log_verification_for_rotation() --  Verifies key rotation from log

    cleanup()  --  Cleanup SC, BS,SP, Library

    tear_down() --  Tear Down Function of this Case

    Input Example:

    "testCases": {


				"62878": {
					"ClientName": "client",
					"AgentName": "File System",
					"MA1": "MAName1",
					"MA2": "MAName2"
					"AWSAccessKey:"",
					"AwsSecretKeyBase64Encrypted":""
				}
                }
                
                
    Note: Client MA1, MA2 have to be unique. Same machine can't be used.
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper

class TestCase(CVTestCase):
    """Encryption master key rotation"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Encryption master key rotation"

        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MA1": None,
            "MA2": None,
            "AWSAccessKey": None,
            "AwsSecretKeyBase64Encrypted": None
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
        self.primary_ddb_path1 = None
        self.primary_ddb_path2 = None
        self.secondary_ddb_path1 = None
        self.secondary_ddb_path2 = None
        self.client_content = None
        self.sp_obj = None
        self.copy_name = None
        self.primary_pool_o = None
        self.secondary_pool_o = None
        self.is_destination_ma_directory_created = None
        self.is_source_ma_directory_created = None
        self.is_client_directory_created = None
        self.last_log_match_count = None
        self.client_content2 = None
        self.subclient = None
        self.job_obj = None
        self.aws_access_key = None
        self.aws_secret_key = None
        self.kms_name = None
        self.kms_details = {}
        self.restore_path = None
        self.is_restore_path_created = None

    def setup(self):
        """Setup function of this test case"""

        self.log.info("This is setup method of the test case")
        self.ma_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)
        self.sp_name = f"automation_{self.id}_sp"
        self.pool_primary_name = f"automation_{self.id}_primary_pool"
        self.pool_secondary_name = f"automation_{self.id}_secondary_pool"
        self.bs_name = f"automation_{self.id}_BS"
        self.sc_name = f"automation_{self.id}_SC"
        self.source_ma = self.tcinputs['MA1']
        self.destination_ma = self.tcinputs['MA2']
        self.client = self.tcinputs['ClientName']
        self.aws_access_key = self.tcinputs["AWSAccessKey"]
        self.aws_secret_key = self.tcinputs["AwsSecretKeyBase64Encrypted"]
        self.kms_name = f"Automation_{self.id}_KMS"
        self.copy_name = "Copy2"
        self.last_log_match_count = 0

        ma_client_list = [self.source_ma,self.destination_ma,self.client]
        if len(set(ma_client_list)) != 3:
            self.log.error("Client, MA1 and MA2 are not unique machines")
            raise Exception("Client MA1 and MA2 have to be unique machines.")

        self.log.info("Creating MediaAgent objects")
        self.source_ma_o = self.commcell.media_agents.get(self.source_ma)
        self.destination_ma_o = self.commcell.media_agents.get(self.destination_ma)

        self.log.info("Getting drives from MediaAgent and client")
        (self.client_machine, self.client_path) = self.ma_helper.generate_automation_path(self.client, 15000)
        (self.source_ma_machine, self.source_ma_path) = self.ma_helper.generate_automation_path(self.source_ma, 15000)
        (self.destination_ma_machine, self.destination_ma_path) = self.ma_helper.generate_automation_path(self.destination_ma, 15000)

        self.log.info("Generating paths")
        self.source_lib_path = self.source_ma_machine.join_path(self.source_ma_path, "SourcsMP")
        self.log.info(f"Source library path: {self.source_lib_path}")

        self.destination_lib_path = self.destination_ma_machine.join_path(self.destination_ma_path, "DestinationMP")
        self.log.info(f"Destination library path: {self.destination_lib_path}")

        self.primary_ddb_path1 = self.source_ma_machine.join_path(self.source_ma_path, "DDB1")
        self.log.info(f"Primary copy DDB path-1: {self.primary_ddb_path1}")

        self.primary_ddb_path2 = self.source_ma_machine.join_path(self.source_ma_path, "DDB2")
        self.log.info(f"Primary copy DDB path-2: {self.primary_ddb_path2}")

        self.secondary_ddb_path1 = self.destination_ma_machine.join_path(self.destination_ma_path, "DestinationDDB1")
        self.log.info(f"Secondary copy DDB path-1: {self.secondary_ddb_path1}")

        self.secondary_ddb_path2 = self.destination_ma_machine.join_path(self.destination_ma_path, "DestinationDDB2")
        self.log.info(f"Secondary copy DDB path-2: {self.secondary_ddb_path2}")

        self.client_content = self.client_machine.join_path(self.client_path, "content")
        self.log.info(f"Client content path: {self.client_content}")

        self.restore_path = self.client_machine.join_path(self.client_path, "restore")
        self.log.info(f"Restore path: {self.restore_path}")

    def create_pool(self, pool_name, library_path, ma, ddb_path1, ddb_path2):
        """
        Creates storage pool
        Args:
            pool_name (str) - Storage Pool name
            library_path (str) - Library path of the stoarge pool
            ma_obj (object) - MediaAgent class object of library and DDB MediaAgent
            ddb_path (str) - Path of Deduplication database
        """
        self.log.info(f"Creating storage pool[{pool_name}]")
        pool_obj = self.commcell.storage_pools.add(pool_name, library_path, ma, ma, ddb_path1)
        self.log.info("Storage pool created successfully")
        pool_copy_o = pool_obj.get_copy()

        self.log.info("Adding 2nd partition")
        self.ddb_engine_o = self.commcell.deduplication_engines.get(pool_obj.storage_pool_name, pool_obj.copy_name)
        store_id = self.ddb_engine_o.all_stores[0]
        self.store_o = self.ddb_engine_o.get(int(store_id[0]))
        self.store_o.add_partition(ddb_path2, ma)
        self.log.info("Partition added successfully")
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

        self.log.info(f"Deleting KMS[{self.kms_name}] if exists")
        if self.commcell.key_management_servers.has_kms(self.kms_name):
            self.log.info(f"KMS[{self.kms_name}] exists, deleting that")
            self.commcell.key_management_servers.delete(self.kms_name)

        self.log.info("Cleanup completed")

    def tear_down(self):
        """Tear Down Function of this Case"""
        self.log.info("This is Tear Down method")

        try:
            self.cleanup()

            if self.is_client_directory_created:
                self.log.info("Deleting the SubClient content directory")
                self.ma_helper.remove_content(self.client_content, self.client_machine)

            if self.is_restore_path_created:
                self.log.info("Deleting restore path")
                self.ma_helper.remove_content(self.restore_path, self.client_machine)

        except Exception as excp:
            self.log.error(f"Cleanup failed with error: {excp}")
            self.result_string = str(f"Cleanup failed. {excp}")

    def run_backups(self):
        """
        Runs backup
        """
        self.log.info("Generating SubClient content")
        self.ma_helper.create_uncompressable_data(self.client, self.client_content, 1)

        # Starting backup
        self.log.info("Starting backup")
        self.job_obj = self.subclient.backup("FULL")
        self.log.info(f"Job started, waiting for the job completion. Job ID: {self.job_obj.job_id}")
        self.ma_helper.wait_for_job_completion(self.job_obj)

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

    def rotate_master_key(self):
        """ Rotates encryption master key"""
        self.log.info("Rotating encryption master key")
        self.primary_pool_copy_o.rotate_encryption_master_key()
        self.log.info("Rotation completed")

    def log_verification(self, log_line_to_match, machine_name, log_file):
        """Performs the log verification
        Args:
            log_line_to_match (str) - pattern to search
            machine_name (str) - client name of the log file
            log_file (str) - log file name
        """
        self.log.info(f"Pattern to match : {log_line_to_match} ")
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            machine_name, log_file, log_line_to_match,
            escape_regex=False, single_file=False)

        if matched_line:
            self.log.info("Log verification passed")
            return len(matched_line)
        else:
            self.log.error("Log verification failed")
            raise Exception("Log verification failed")

    def compare_log_matching(self, previous_match_count, current_match_count):
        """ Compares the log line match count with the previously matched count
        Args:
            previous_match_count (int) - match count till the last job
            current_match_count (int) - match count till the current job
        """

        if current_match_count > previous_match_count:
            self.log.info("Log Verified:: Master key fetched for the last job")
            return

        raise Exception("Log verification failed. No extra log line found for the last job, means, no marster key fetched for the last job")

    def log_verification_for_rotation(self):
        """Verifies key rotation from log"""
        self.log.info("Verifying that key rotation was successful or not from log")
        ptrn = f"Successfully encrypted priKey using a new master key for copyId \[{self.primary_pool_copy_o.copy_id}\]"
        match_count = self.log_verification(ptrn, self.commcell.commserv_client, "AppMgrService.log")
        self.log.info("Key fetch count ( calculated from log ) should be higher than the previous count")
        if match_count> self.last_log_match_count:
            self.log.info("Key fetch count verified successfully. It's increased from the last count")
            self.last_log_match_count = match_count
            return
        self.log.error("Key fetch count ( calculated from log ) should have higher than the previous count. It's not increased, failing the case")
        raise Exception("Key fetch count ( calculated from log ) should have higher than the previous count. It's not increased, failing the case")

    def run(self):
        try:

            self.log.info("Cleaning-up SC,BS,SP,Libraries if exists")
            self.cleanup()

            # Creating storage pool
            self.primary_pool_o, self.primary_pool_copy_o = self.create_pool(self.pool_primary_name, self.source_lib_path, self.source_ma, self.primary_ddb_path1, self.primary_ddb_path2)
            self.is_source_ma_directory_created = True

            self.secondary_pool_o, self.secondary_pool_copy_o = self.create_pool(self.pool_secondary_name, self.destination_lib_path, self.destination_ma, self.secondary_ddb_path1, self.secondary_ddb_path2)
            self.is_destination_ma_directory_created = True

            self.log.info(f"Enabling encryption on storage pool[{self.pool_primary_name}]")
            self.ma_helper.set_encryption(self.primary_pool_copy_o)

            self.log.info(f"Enabling encryption on storage pool[{self.pool_secondary_name}]")
            self.ma_helper.set_encryption(self.secondary_pool_copy_o)

            # Creating SP
            self.log.info(f"Creating storage policy[{self.sp_name}]")
            self.sp_obj = self.commcell.storage_policies.add(self.sp_name, global_policy_name = self.pool_primary_name, number_of_streams=1, global_dedup_policy  = True)
            self.log.info("Storage Policy created successfully")

            # Creating secondary copy
            self.create_secondary_copy(self.pool_secondary_name, self.copy_name)

            self.subclient = self.configure_sub_client(self.bs_name, self.sc_name, self.client_content, self._agent)

            # running backups
            self.is_client_directory_created = True
            self.run_backups()

            # Creating KMS
            self.log.info(f"Creating KMS[{self.kms_name}]")
            self.kms_details = {
                "KEY_PROVIDER_TYPE": "KEY_PROVIDER_AWS_KMS",
                "KMS_NAME": self.kms_name,
                "AWS_ACCESS_KEY": self.aws_access_key,
                "AWS_SECRET_KEY": self.aws_secret_key,
                "AWS_REGION_NAME": "Asia Pacific (Mumbai)",
                "KEY_PROVIDER_AUTH_TYPE": "AWS_KEYS"
            }
            self.commcell.key_management_servers.add(self.kms_details)
            self.log.info("KMS created")

            self.log.info("Mapping the KMS with Pool's primary copy")
            self.primary_pool_copy_o.set_key_management_server(self.kms_name)
            self.log.info("KMS mapping successful")
            self.log_verification_for_rotation()

            self.rotate_master_key()
            self.log_verification_for_rotation()

            self.ma_helper.restart_mm_service()

            self.log.info("Starting restore")
            self.job_obj = self.subclient.restore_out_of_place(self.client, self.restore_path, [self.client_content])
            self.ma_helper.wait_for_job_completion(self.job_obj)
            self.is_restore_path_created = True

            log_line_to_match = f"getMasterKey Decrypting key using master key \[.+\] from key provider \[{self.kms_name}\] for entityId \[{self.primary_pool_copy_o.copy_id}\] entityType \[18\]"
            matched_for_restore = self.log_verification(log_line_to_match, self.commcell.commserv_client, "ArchMgr.log")

            self.ma_helper.restart_mm_service()
            self.rotate_master_key()
            self.log_verification_for_rotation()
            self.ma_helper.restart_mm_service()
            self.run_backups()

            matched_for_backup = self.log_verification(log_line_to_match, self.commcell.commserv_client, "ArchMgr.log")
            self.compare_log_matching(matched_for_restore, matched_for_backup)

            self.ma_helper.restart_mm_service()

            self.log.info("Starting aux copy job")
            self.job_obj = self.sp_obj.run_aux_copy(self.copy_name, all_copies=False)
            self.log.info(f"Job started, waiting for the job completion. Job ID: {self.job_obj.job_id}")
            self.ma_helper.wait_for_job_completion(self.job_obj)

            matched_for_auxcopy = self.log_verification(log_line_to_match, self.commcell.commserv_client, "ArchMgr.log")
            self.compare_log_matching(matched_for_backup, matched_for_auxcopy)

            self.log.info("Test case completed successfully.")

        except Exception as excp:
            self.log.error(f"Failed with error: {excp}")
            self.result_string = str(excp)
            self.status = constants.FAILED