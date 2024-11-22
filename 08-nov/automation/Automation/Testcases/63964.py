
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  Setup method for this test case

    cleanup()       -- cleanup method for this test case

    tear_down()             -- performs tear down tasks

    run()           --  run function of this test case

    restart_mm_service()    -- restarts MediaManager service

    log_verification()  --  Finds the pattern on log file

    compare_log_matching()  -- Compares the log line match count with the previously matched count

Test Case Input JSON:

            "63964": {
					"ClientName": "client1",
					"AgentName": "File System",
					"MediaAgent": "ma1",
					"KMIPCertificatePath":"c:\\f1\\cert.crt",
					"KMIPKeyFilePath":"c:\\f1\\clientkey.key",
					"KMIPCACertificatePath":"c:\\f1\\CaCertificate.pem",
					"KMIPCertPasswordBase64":"sdsadasDJ"
					"KMIPPort":"9002",
					"KMIPHost":"123.123.123.123"
				}


Note : This test case restarts MediaManager service on CS. 

"""

import time
import random
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper
from cvpysdk.exception import SDKException

class TestCase(CVTestCase):
    """KMIP KMS without access Node"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "KMIP KMS without access Node"

        self.ma_helper = None
        self.storage_policy = None
        self.backup_set = None
        self.sub_client = None
        self.client = None
        self.library_name = None
        self.client_machine = None
        self.client_drive = None
        self.client_path = None
        self.client_content = None
        self.is_client_directory_created = None
        self.is_ma_directory_created = None
        self.MediaAgents_obj = None
        self.MediaAgent = None
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
        self.kmip_cert = None
        self.kmip_cert_pass = None
        self.kmip_key = None
        self.kmip_ca_cert = None
        self.kmip_port = None
        self.kmip_host = None
        self.kmip_kms_name = None
        self.result_string = None
        self.mediaagent_machine = None
        self.ddb_path = None
        self.storage_pool_obj = None

    def setup(self):
        """Setup function of this test case"""
        self.log.info("Starting test case setup")

        utility = OptionsSelector(self.commcell)
        self.ma_helper = MMHelper(self)
        self.storage_pool = f"TestCase_{self.id}_Pool"
        self.storage_policy = f"TestCase_{self.id}_SP"
        self.backup_set = f"TestCase_{self.id}_BS"
        self.sub_client = f"TestCase_{self.id}_SC"
        self.kmip_kms_name = f"TestCase_{self.id}_KMIP_KMS"
        self.MediaAgent = self.tcinputs['MediaAgent']
        self.kmip_cert = self.tcinputs["KMIPCertificatePath"]
        self.kmip_key = self.tcinputs["KMIPKeyFilePath"]
        self.kmip_ca_cert = self.tcinputs["KMIPCACertificatePath"]
        self.kmip_cert_pass = self.tcinputs["KMIPCertPasswordBase64"]
        self.kmip_port = self.tcinputs["KMIPPort"]
        self.kmip_host= self.tcinputs["KMIPHost"]
        self.result_string = ""

        self.client = self.tcinputs['ClientName']
        self.library_name = "TestCase_"+str(self.id) + "_Library_"+self.MediaAgent

        self.MediaAgents_obj = self._commcell.media_agents.get(self.MediaAgent)

        self.is_client_directory_created = False
        self.is_ma_directory_created = False
        self.dedupe_helper = DedupeHelper(self)

        self.copy_name = "Copy-2"

        (
            self.mediaagent_machine,
            self.ma_path,
        ) = self.ma_helper.generate_automation_path(self.MediaAgent, 15000)
        self.library_path = self.ma_path + "library"
        self.ddb_path = self.ma_path + "DDB"

        (
            self.client_machine,
            self.client_path,
        ) = self.ma_helper.generate_automation_path(self.client, 15000)
        self.client_content = self.client_path + "subclient_content"
        self.restore_path = self.client_path + "restore"


    def cleanup(self):
        """ Cleanup method of this test case"""
        try:
            self.log.info("Starting cleanup")
            if self._agent.backupsets.has_backupset(self.backup_set):
                self.log.info("BackupSet [%s] exists, deleting that", self.backup_set)
                self._agent.backupsets.delete(self.backup_set)
                self.log.info("Backup set deleted successfully")

            if self.commcell.storage_policies.has_policy(self.storage_policy):
                self.log.info("Storage policy [%s] exists, deleting that", self.storage_policy)
                self.commcell.storage_policies.delete(self.storage_policy)
                self.log.info("Storage policy deleted successfully")

            if self.commcell.storage_pools.has_storage_pool(self.storage_pool):
                self.log.info(f"Storage pool [{self.storage_pool}] exists, deleting that")
                self.commcell.storage_pools.delete(self.storage_pool)
                self.log.info("Storage pool deleted successfully")

            if self.commcell.disk_libraries.has_library(self.library_name):
                self.log.info("Library [%s] exists, deleting that", self.library_name)
                self.commcell.disk_libraries.delete(self.library_name)
                self.log.info("Library deleted successfully")

            if self.commcell.key_management_servers.has_kms(self.kmip_kms_name):
                self.log.info("KMS [%s] already exists", self.kmip_kms_name)
                self.commcell.key_management_servers.delete(self.kmip_kms_name)
                self.log.info("KMS deleted successfully")

        except Exception as excp:
            self.log.error(f"cleanup:: cleanup failed. {str(excp)}")
            self.result_string = self.result_string + f"cleanup:: cleanup failed. {str(excp)}"

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
            self.result_string = self.result_string + f"tear_down:: cleanup failed. {str(excp)}"

    def log_verification(self, log_line_to_match, machine_name, log_file):
        """Finds the pattern on log file
        Args:
            log_line_to_match ( str) - log pattern to match
            machine_name (str) - client name to find the log
            log_file (str) - log file name to find the patern
        """
        
        self.log.info(f"Pattern to match : {log_line_to_match} ")
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            machine_name, log_file, log_line_to_match,
            escape_regex=False, single_file=False)

        if matched_line:
            self.log.info("Matched line(s)")
            self.log.info(str(matched_line))
            self.log.info("Log verification passed")
            return len(matched_line)
        else:
            self.log.error("Log verification failed")
            self.status = constants.FAILED
            raise Exception("Log verification failed")

    def compare_log_matching(self, previous_match_count, current_match_count):
        """ Compares the log line match count with the previously matched count"""
        if current_match_count > previous_match_count:
            self.log.info("Log Verified:: Master key fetched for the last job")
            return

        raise Exception("Log verification failed. No extra log line found for the last job, means, no marster key fetched for the last job")


    def run(self):
        """Run method of this test case"""

        try:
            self.cleanup()

            self.log.info("Creating the KMS")

            self.log.info("Creating KMS [%s]", self.kmip_kms_name)

            enc_key_list = [128,256]
            
            kms_details = {
                "KEY_PROVIDER_TYPE": "KEY_PROVIDER_KMIP",
                "KMS_NAME": self.kmip_kms_name,
                "KEY_PROVIDER_AUTH_TYPE": "KMIP_CERTIFICATE",
                "KMIP_CERTIFICATE_PATH": self.kmip_cert,
                "KMIP_CERTIFICATE_KEY_PATH": self.kmip_key,
                "KMIP_CA_CERTIFICATE_PATH": self.kmip_ca_cert,
                "KMIP_CERTIFICATE_PASS": self.kmip_cert_pass,
                "KMIP_HOST": self.kmip_host,
                "KMIP_PORT": self.kmip_port,
                "KMIP_ENC_KEY_LENGTH":random.choice(enc_key_list)
            }

            self.KMS_obj = self.commcell.key_management_servers.add(kms_details)
            self.log.info(f"KMS {self.kmip_kms_name} created successfully")

            self.log.info("Creating library[%s]", self.library_name)
            self.commcell.disk_libraries.add(self.library_name, self.MediaAgent, self.library_path)
            self.is_ma_directory_created = True
            self.log.info("Library created successfully")

            self.log.info(f"Creating storage pool [{self.storage_pool}]")
            self.commcell.storage_pools.add(self.storage_pool, self.library_path, self.MediaAgent, self.MediaAgent, self.ddb_path)
            self.log.info("Storage pool created successfully")

            self.log.info("Creating storage policy[%s]", self.storage_policy)
            self.storage_policy_obj = self.commcell.storage_policies.add(self.storage_policy, global_policy_name = self.storage_pool)
            self.log.info("Storage Policy created successfully")

            self.log.info("Creating object of StoragePolicy class for storage pool")
            self.storage_pool_obj = self.commcell.storage_policies.get(self.storage_pool)

            self.log.info("Creating storage pool Primary copy object")
            self.primary_copy_obj = self.storage_pool_obj.get_copy("Primary")

            self.log.info("Setting encryption on Primary copy")
            self.primary_copy_obj.copy_reencryption = (True, "TWOFISH", 128, False)

            self.log.info("Mapping storage policy and KMS[%s]", self.kmip_kms_name)
            self.primary_copy_obj.set_key_management_server(self.kmip_kms_name)
            self.log.info("KMS mapping successful")

            self.log.info("Verifying the master key creation request by parsing log on on CS")
            log_line_to_match = "KMIPKeyProvider::createMasterKey Creating master key with key provider \["+self.kmip_kms_name+"\] for entityId \["+self.primary_copy_obj.copy_id+"\] entityType \[18\]"
            self.log.info("Trying to find the line [%s] for validation", log_line_to_match)

            self.log_verification(log_line_to_match, self.commcell.commserv_client.client_name, "AppMgrService.log")

            self.log.info("Creating BackupSet [%s]", self.backup_set)
            self.backup_set_obj = self.agent.backupsets.add(self.backup_set)
            self.log.info("Backup set created successfully")
            
            self.log.info("Creating sub client [%s]", self.sub_client)
            self.subclient_obj = self.backup_set_obj.subclients.add(self.sub_client, self.storage_policy)
            self.log.info("Sub client creation successful")

            self.log.info("Generating SubClient content")
            self.ma_helper.create_uncompressable_data(self.client, self.client_content, 3)
            self.is_client_directory_created = True
            self.log.info("Content generation completed")

            self.subclient_obj.content = [self.client_content]
            self.log.info("successfully added content to subclient")

            self.ma_helper.restart_mm_service()

            self.log.info("Starting backup")
            self.job_obj = self.subclient_obj.backup("FULL")
            self.log.info("Job started. Job ID [%s]", self.job_obj.job_id)
            self.log.info("Waiting for the job to complete")
            self.ma_helper.wait_for_job_completion(self.job_obj)

            log_line_to_match = "KMIPKeyProvider::getMasterKey Getting master key from key provider \["+self.kmip_kms_name+"\] for entityId \["+self.primary_copy_obj.copy_id+"\] entityType \[18\] UID"
            matched_for_backup = self.log_verification(log_line_to_match, self.commcell.commserv_client.client_name, "AppMgrService.log")

            self.ma_helper.restart_mm_service()

            self.log.info("Starting restore job")
            self.job_obj = self.subclient_obj.restore_out_of_place(self.client, self.restore_path, [self.client_content])
            self.log.info("Job started. Job ID [%s]", self.job_obj.job_id)
            self.log.info("Waiting for job to complete")
            self.ma_helper.wait_for_job_completion(self.job_obj)

            matched_for_restore = self.log_verification(log_line_to_match, self.commcell.commserv_client.client_name, "AppMgrService.log")
            self.compare_log_matching(matched_for_backup, matched_for_restore)

            self.log.info("Creating aux copy")
            self.storage_policy_obj.create_secondary_copy(self.copy_name, self.library_name, self.MediaAgent)
            self.log.info("Aux copy created successfully")

            self.ma_helper.restart_mm_service()

            self.log.info("Starting aux copy job")
            self.job_obj = self.storage_policy_obj.run_aux_copy()
            self.log.info(f"Aux Job started. Job ID [{self.job_obj.job_id}]")
            self.ma_helper.wait_for_job_completion(self.job_obj)
            self.log.info("Aux copy job completed successfully")

            matched_for_aux = self.log_verification(log_line_to_match, self.commcell.commserv_client.client_name, "AppMgrService.log")
            self.compare_log_matching(matched_for_restore, matched_for_aux)

            self.log.info("Test case completed successfully")

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED