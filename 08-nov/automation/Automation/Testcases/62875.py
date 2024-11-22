# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()  --  initialize TestCase class

    setup()  --  Setup method for this test case

    cleanup()  -- cleanup method for this test case

    tear_down()  -- performs tear down tasks
    
    log_verification()  --  Matched the log lines passed with the log file
    
    compare_log_matching()  --  Compares the log line match count with the previously matched count
    
    create_pool()  --  Creates storage pool
    
    restart_mm_service()  --  Restarts the Media Manager service
    
    verify_db()  --  Verify from database that the master key ID set correctly

    run()  --  run function of this test case

Test Case Input JSON:

            "62875": {
					"ClientName": "client1",
					"AgentName": "File System",
					"MediaAgent": "ma1",
					"AwsKmsAccessNode": "ma2",
					"AwsAccessKey": "key1",
					"AwsSecretKeyBase64Encrypted": "key2",
					"AWSEncKey":"abcd"
				}

"""

from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
from AutomationUtils import commonutils

class TestCase(CVTestCase):
    """Verify Bring Your Own Key with AWS KMS"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Verify Bring Your Own Key with AWS KMS"

        self.ma_helper = None
        self.storage_policy = None
        self.backup_set = None
        self.sub_client = None
        self.path_prefix = None
        self.client = None
        self.library_name = None
        self.client_machine = None
        self.client_drive = None
        self.client_path = None
        self.client_content = None
        self.is_client_directory_created = None
        self.MediaAgents_obj = None
        self.MediaAgent = None
        self.AWS_access_key = None
        self.AWS_secret_key = None
        self.AWS_KMS_access_node = None
        self.AWS_KMS_name = None
        self.storage_policy_obj = None
        self.restore_path = None
        self.subclient_obj = None
        self.primary_copy_obj = None
        self.backup_set_obj = None
        self.ma_path = None
        self.library_name = None
        self.ma_drive = None
        self.dedupe_helper = None
        self.job_obj = None
        self.copy_name = None
        self.aws_enc_key = None
        self.pool = None
        self.pool_copy_o = None
        self.pool_o = None
        self.library_path = None
        self.ddb_path = None

        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "MediaAgent": None,
            "AwsKmsAccessNode": None,
            "AwsAccessKey": None,
            "AwsSecretKeyBase64Encrypted": None,
            "AWSEncKey": None
        }

    def restart_mm_service(self):
        """ Restarts the Media Manager service"""
        self.log.info(
            "Restarting Media Manager service to flush the cached encryption keys before starting the next job.")
        self.commcell.commserv_client.restart_service("GXMLM(Instance001)")
        self.log.info("Restart completed")

    def setup(self):
        """Setup function of this test case"""
        self.log.info("Starting test case setup")

        self.ma_helper = MMHelper(self)

        self.MediaAgent = self.tcinputs['MediaAgent']
        self.AWS_secret_key = self.tcinputs['AwsSecretKeyBase64Encrypted']
        self.AWS_access_key = self.tcinputs['AwsAccessKey']
        self.AWS_KMS_access_node = self.tcinputs['AwsKmsAccessNode']
        self.aws_enc_key = self.tcinputs["AWSEncKey"]
        
        self.pool = f"TestCase_{self.id}_Pool_{self.MediaAgent}"
        self.storage_policy = f"TestCase_{self.id}_SP_{self.MediaAgent}"
        self.backup_set = f"TestCase_{self.id}_BS"
        self.sub_client = f"TestCase_{self.id}_SC"
        self.AWS_KMS_name = f"TestCase_{self.id}_AWS_KMS"

        if self.MediaAgent.lower() == self.AWS_KMS_access_node.lower():
            raise Exception("MediaAgent and AWS KMS access node can't be same")

        self.client = self.tcinputs['ClientName']
        self.MediaAgents_obj = self._commcell.media_agents.get(self.MediaAgent)

        self.client_machine, self.client_path = self.ma_helper.generate_automation_path(self.client, 5000)
        self.mediaagent_machine, self.ma_path = self.ma_helper.generate_automation_path(self.MediaAgent, 10000)

        self.client_content = self.client_machine.join_path(self.client_path, "subclient_content")
        self.log.info("Client content path %s", self.client_content)

        self.restore_path = self.client_machine.join_path(self.client_path, "restore")
        self.log.info(f"Restore path: {self.restore_path}")

        self.library_path = self.mediaagent_machine.join_path(self.ma_path, "library")
        self.log.info("Library path %s", self.library_path)

        self.ddb_path = self.mediaagent_machine.join_path(self.ma_path, "DDB")
        self.log.info(f"DDB Path: {self.ddb_path}")

        self.is_client_directory_created = False
        self.dedupe_helper = DedupeHelper(self)
        self.copy_name = "Copy-2"

    def cleanup(self):
        """ Cleanup method of this test case"""
        try:
            self.log.info("Starting cleanup")
            if self._agent.backupsets.has_backupset(self.backup_set):
                self.log.info(f"BackupSet [{self.backup_set}] exists, deleting that")
                self._agent.backupsets.delete(self.backup_set)
                self.log.info("Backup set deleted successfully")

            if self.commcell.storage_policies.has_policy(self.storage_policy):
                self.log.info(f"Storage policy [{self.storage_policy}] exists, deleting that")
                self.log.info("Re-associating all sub clients before deleting the SP")
                self.sp_obj_to_reassociate = self.commcell.storage_policies.get(self.storage_policy)
                self.sp_obj_to_reassociate.reassociate_all_subclients()
                self.commcell.storage_policies.delete(self.storage_policy)
                self.log.info("Storage policy deleted successfully")

            if self.commcell.storage_pools.has_storage_pool(self.pool):
                self.log.info(f"Storage Pool [{self.pool}] exists, deleting that")
                self.commcell.storage_pools.delete(self.pool)
                self.log.info("Storage pool deleted successfully")

            if self.commcell.key_management_servers.has_kms(self.AWS_KMS_name):
                self.log.info(f"KMS [{self.AWS_KMS_name}] already exists, deleting that")
                self.commcell.key_management_servers.delete(self.AWS_KMS_name)
                self.log.info("KMS deleted successfully")

            self.log.info("Cleaning up the MasterKey details from database")
            q = f"delete from CommServ..ArchMasterKeyToRevoke" \
                f" where OldMasterKeyId = '{self.aws_enc_key}' " \
                f" or NewMasterKeyId = '{self.aws_enc_key}' ;" \
                " delete from HistoryDB..ArchMasterKeyToRevokeHistory " \
                f" where OldMasterKeyId = '{self.aws_enc_key}' " \
                f" or NewMasterKeyId = '{self.aws_enc_key}' ;" \
                " delete from CommServ..MMEntityProp " \
                " where propertyName='EncBYOKKeyId'" \
                f" and stringVal='{self.aws_enc_key}' " \
                " and EntityType=18 ;"

            self.log.info("Executing the following query")
            self.log.info(q)

            sql_password = commonutils.get_cvadmin_password(self.commcell)
            self.ma_helper.execute_update_query(q, sql_password, "sqladmin_cv")

        except Exception as excp:
            self.log.error(f"cleanup:: cleanup failed. {str(excp)}")
            self.result_string = f"cleanup:: cleanup failed. {str(excp)}"

    def tear_down(self):
        """Tear Down Function of this Case"""
        try:
            self.log.info("This is Tear Down method")

            if self.status != constants.FAILED:
                self.log.info("Test case completed. Deleting SC, BS, SP")
                self.cleanup()
            else:
                self.log.info("Test case failed, not deleting SC, BS, SP")

            if self.is_client_directory_created:
                self.log.info("Client directory created, deleting that")
                self.ma_helper.remove_content(self.client_path, self.client_machine)

        except Exception as excp:
            self.log.info(f"tear_down:: cleanup failed. {str(excp)}")
            self.result_string = f"tear_down:: cleanup failed. {str(excp)}"

    def log_verification(self, log_line_to_match, machine_name, log_file, escape_regx = True):
        """
        Matched the log lines passed with the log file
        Args:
            log_line_to_match (str) -- Log line pattern to match
            machine_name (str) -- Name of the machine where to find the log file
            log_file (str) - Name of the log file where to search the log line
        """
        self.log.info(f"Pattern to match : {log_line_to_match} ")
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            machine_name, log_file, log_line_to_match,
            escape_regex=escape_regx, single_file=False)

        if matched_line:
            self.log.info("Log verification passed")
            return len(matched_line)
        else:
            self.log.error("Log verification failed")
            self.status = constants.FAILED
            raise Exception("Log verification failed")

    def compare_log_matching(self, previous_match_count, current_match_count):
        """
        Compares the log line match count with the previously matched count
        Args:
            previous_match_count (int) -- previously match log line count ot compare
            current_match_count (int) -- current log line count to compare
        """
        if current_match_count > previous_match_count:
            self.log.info("Log Verified:: Master key fetched for the last job")
            return

        raise (
            "Log verification failed. No extra log line found for the last job, means, no marster key fetched for the last job")

    def create_pool(self, pool_name, library_path, ma_obj, ddb_path):
        """
        Creates storage pool
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

    def verify_db(self):
        """Verify from database that the master key ID set correcyly
        """
        self.log.info("Starting database verification")
        q = f"select MasterKeyId from ArchCopyEncProperties where CopyId={self.pool_copy_o.copy_id}"
        self.log.info("Executing the following query")
        self.log.info(q)
        self.csdb.execute(q)
        key = self.csdb.fetch_one_row()[0]
        self.log.info(f"Master key ID found on DB: {key}")
        if key == self.aws_enc_key:
            self.log.info("Verification successful")
            return

        self.log.error(f"Database verification failed. Expected key ID [{self.aws_enc_key}] but found [key]")
        raise Exception(f"Database verification failed. Expected key ID [{self.aws_enc_key}] but found [key]")

    def run(self):
        """Run method of this test case"""

        try:
            self.cleanup()

            self.log.info(f"Creating KMS [{self.AWS_KMS_name}]")
            kms_details = {
                "KEY_PROVIDER_TYPE": "KEY_PROVIDER_AWS_KMS",
                "ACCESS_NODE_NAME": self.AWS_KMS_access_node,
                "KMS_NAME": self.AWS_KMS_name,
                "KEY_PROVIDER_AUTH_TYPE": "AWS_KEYS",
                "AWS_ACCESS_KEY": self.AWS_access_key,
                "AWS_SECRET_KEY": self.AWS_secret_key,
                "BringYourOwnKey": True,
                "KEYS": [self.aws_enc_key,]
            }

            self.KMS_obj = self.commcell.key_management_servers.add(kms_details)
            self.log.info(f"KMS {self.AWS_KMS_name} created successfully")

            (self.pool_o, self.pool_copy_o) = self.create_pool(self.pool, self.library_path, self.MediaAgents_obj, self.ddb_path)

            self.log.info(f"Enabling encryption on storage pool[{self.pool}]")
            self.ma_helper.set_encryption(self.pool_copy_o)

            self.log.info(f"Creating storage policy[{self.storage_policy}]")
            self.storage_policy_obj = self.commcell.storage_policies.add(self.storage_policy, global_policy_name=self.pool,
                                                                         global_dedup_policy=True)
            self.log.info("Storage Policy created successfully")


            self.log.info("Mapping storage policy and KMS[%s]", self.AWS_KMS_name)
            self.pool_copy_o.set_key_management_server(self.AWS_KMS_name)
            self.log.info("KMS mapping successful")

            self.log.info(f"Verifying that master key creation request sent to correct access node [{self.AWS_KMS_access_node}]")
            log_line_to_match = f"createMasterKey Sending key operation request to access node \[[0-9]+ : {self.AWS_KMS_access_node}\]"
            self.log.info("Starting log verification")
            self.log_verification(log_line_to_match, self.commcell.commserv_client, "AppMgrService.log", False)

            self.log.info("Verifying the master key creation request from CS log")
            log_line_to_match = f"pickKeyFromBYOKList Picking a keyId from the list of bring your own keys for key provider [{self.AWS_KMS_name}] for entityId [{self.pool_copy_o.copy_id}] entityType [18]"
            self.log.info("Starting log verification")
            self.log_verification(log_line_to_match, self.commcell.commserv_client, "AppMgrService.log")

            self.verify_db()

            self.log.info("Generating SubClient content")
            self.ma_helper.create_uncompressable_data(self.client, self.client_content, 3)
            self.is_client_directory_created = True
            self.log.info("Content generation completed")

            self.log.info("Creating BackupSet [%s]", self.backup_set)
            self.backup_set_obj = self.agent.backupsets.add(self.backup_set)
            self.log.info("Backup set created successfully")

            self.log.info("Creating sub client [%s]", self.sub_client)
            self.subclient_obj = self.backup_set_obj.subclients.add(self.sub_client, self.storage_policy)
            self.log.info("Sub client creation successful")

            self.subclient_obj.content = [self.client_content]
            self.log.info("successfully added content to subclient")

            self.restart_mm_service()

            self.log.info("Starting backup")
            self.job_obj = self.subclient_obj.backup("FULL")
            self.log.info(f"Job started. Job ID [{self.job_obj.job_id}]")
            self.log.info("Waiting for the job to complete")
            self.ma_helper.wait_for_job_completion(self.job_obj)

            log_line_to_match = f"AWSKeyProvider::getMasterKey Decrypting key using master key [{self.aws_enc_key}] from key provider [{self.AWS_KMS_name}] for entityId [{self.pool_copy_o.copy_id}] entityType [18]"
            matched_for_backup = self.log_verification(log_line_to_match, self.AWS_KMS_access_node, "cvd.log")

            self.restart_mm_service()

            self.log.info("Starting restore job")
            self.job_obj = self.subclient_obj.restore_out_of_place(self.client, self.restore_path,
                                                                   [self.client_content])
            self.log.info("Job started. Job ID [%s]", self.job_obj.job_id)
            self.log.info("Waiting for job to complete")
            self.ma_helper.wait_for_job_completion(self.job_obj)

            matched_for_restore = self.log_verification(log_line_to_match, self.AWS_KMS_access_node, "cvd.log")
            self.compare_log_matching(matched_for_backup, matched_for_restore)

            self.log.info("Test case completed successfully")

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED