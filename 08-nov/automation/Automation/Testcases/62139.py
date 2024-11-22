
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
    
    create_aws_template_file()  --  Creates AWS Credential template file on KMS access node

    generate_paths()  --    Generates automations paths
    
    log_verification()  -- Matched the log lines passed with the log file
    
    compare_log_matching()  --  Compares the log line match count with the previously matched count
    
    
Test Case Input JSON:

                "62139": {
					"ClientName": "client1",
					"AgentName": "File System",
					"MediaAgent": "ma1",
					"AwsKmsAccessNode": "ma2",
					"AwsAccesKey": "ABC123",
					"AwsSecretKey": "XYX123=="
				}

"""

import time
import re
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import DedupeHelper, MMHelper

class TestCase(CVTestCase):
    """AWS KMS with access Node ( Key file based authentication )"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "AWS KMS with access Node ( Key file based authentication )"

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
        self.is_ma_directory_created = None
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
        self.is_access_node_directory_created = None
        self.KMS_obj = None
        self.library_path = None
        self.AWS_cred_file_profile_name = None
        self.access_node_file_content = None
        self.access_node_mediaagent_obj = None
        self.access_node_machine = None
        self.aws_file_path = None
        self.mediaagent_machine = None
        self.access_node_path = None
        self.aux_copy_name = None

    def setup(self):
        """Setup function of this test case"""
        self.log.info("Starting test case setup")

        utility = OptionsSelector(self.commcell)
        self.ma_helper = MMHelper(self)

        self.storage_policy = "TestCase_"+str(self.id) +"_SP"
        self.backup_set = "TestCase_"+str(self.id) +"_BS"
        self.sub_client = "TestCase_" + str(self.id) + "_SC"
        self.AWS_KMS_name = "TestCase_" + str(self.id) + "_AWS_KMS"
        self.MediaAgent = self.tcinputs['MediaAgent']
        self.AWS_secret_key = self.tcinputs['AwsSecretKey']
        self.AWS_access_key = self.tcinputs['AwsAccesKey']
        self.AWS_KMS_access_node = self.tcinputs['AwsKmsAccessNode']
        self.AWS_cred_file_profile_name ="AutomationAWSKMS"

        self.access_node_file_content = f"[{self.AWS_cred_file_profile_name}]\n" \
                                        f"aws_access_key_id={self.AWS_access_key}\n" \
                                        f"aws_secret_access_key={self.AWS_secret_key}\n"

        if self.MediaAgent.lower() == self.AWS_KMS_access_node.lower():
            raise Exception("MediaAgent and AWS KMS access node can't be same")

        self.client = self.tcinputs['ClientName']
        self.library_name = "TestCase_"+str(self.id) + "_Library"
        self.aux_copy_name ="Copy-2"

        self.MediaAgents_obj = self._commcell.media_agents.get(self.MediaAgent)
        self.access_node_mediaagent_obj = self._commcell.media_agents.get(self.AWS_KMS_access_node)

        self.is_client_directory_created = False
        self.is_ma_directory_created = False
        self.is_access_node_directory_created = False

        self.dedupe_helper = DedupeHelper(self)


    def generate_paths(self):
        """ Generates automations paths """
        self.access_node_machine,self.access_node_path = self.ma_helper.generate_automation_path(self.AWS_KMS_access_node,5000)
        self.aws_file_path = self.access_node_path + "aws.aws"
        self.log.info(f"AWS key file location : {self.aws_file_path}")

        self.client_machine, self.client_path = self.ma_helper.generate_automation_path(self.client, 10000)
        self.client_content = self.client_path + "subclient_content"
        self.log.info("Client content path %s", self.client_content)
        self.restore_path = self.client_path + "restore"
        self.log.info(f"Restore path : {self.restore_path}")

        self.mediaagent_machine, self.ma_path = self.ma_helper.generate_automation_path(self.MediaAgent, 10000)
        self.library_path = self.ma_path + "library"
        self.log.info(f"Library path {self.library_path}")

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

            if self.commcell.disk_libraries.has_library(self.library_name):
                self.log.info("Library [%s] exists, deleting that", self.library_name)
                self.commcell.disk_libraries.delete(self.library_name)
                self.log.info("Library deleted successfully")

            if self.commcell.key_management_servers.has_kms(self.AWS_KMS_name):
                self.log.info("KMS [%s] already exists", self.AWS_KMS_name)
                self.commcell.key_management_servers.delete(self.AWS_KMS_name)
                self.log.info("KMS deleted successfully")

            self.log.info("Cleanup completed")

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

            self.log.info("Disabling Ransomware [%s]", self.MediaAgent)
            self.MediaAgents_obj.set_ransomware_protection(False)

            self.log.info("Disabling Ransomware [%s]", self.AWS_KMS_access_node)
            self.access_node_mediaagent_obj.set_ransomware_protection(False)

            if self.is_client_directory_created:
                self.log.info("Client directory created, deleting that")
                self.ma_helper.remove_content(self.client_path, self.client_machine)

            if self.is_ma_directory_created:
                self.log.info("MediaAgent directed created, deleting that")
                self.ma_helper.remove_content(self.ma_path, self.mediaagent_machine)

            if self.is_access_node_directory_created:
                self.log.info("Access Node directed created, deleting that")
                self.ma_helper.remove_content(self.access_node_path, self.access_node_machine)

            self.log.info("Tear Down completed")

        except Exception as excp:
            self.log.info(f"tear_down:: cleanup failed. {str(excp)}")
            self.result_string = f"tear_down:: cleanup failed. {str(excp)}"

    def create_aws_template_file(self):
        """ Creates AWS Credential template file on KMS access node """
        self.log.info("Creating  AWS cred file on access node")
        self.access_node_machine.create_file(self.aws_file_path, self.access_node_file_content)
        self.is_access_node_directory_created = True

        self.log.info("Creating system variable for AWS template file")
        cmd_system_variable = f"setx -m AWS_SHARED_CREDENTIALS_FILE \"{self.aws_file_path}\""
        self.log.info(f"Command : {cmd_system_variable}")
        output = self.access_node_machine.execute_command(cmd_system_variable)
        self.log.info(f"Command output : {output.output}")
        if re.search("SUCCESS", output.output):
            self.log.info("System variable created successfully")
        else:
            raise Exception("Failed to create the system variable for AWS credential file")

        self.log.info("System variable will be reflected after reboot.")
        self.log.info(f"Rebooting the access node [{self.AWS_KMS_access_node}]")
        self.access_node_machine.reboot_client()

    def log_verification(self, log_line_to_match, machine_name, log_file):
        """Matched the log lines passed with the log file"""
        self.log.info(f"Pattern to match : {log_line_to_match} ")
        (matched_line, matched_string) = self.dedupe_helper.parse_log(
            machine_name, log_file, log_line_to_match,
            escape_regex=False, single_file=False)

        if matched_line:
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
            self.generate_paths()

            # Creating AWS credential template file
            self.create_aws_template_file()

            self.log.info("Creating library[%s]", self.library_name)
            self.commcell.disk_libraries.add(self.library_name, self.MediaAgent, self.library_path)
            self.is_ma_directory_created = True
            self.log.info("Library created successfully")

            self.log.info("Creating storage policy[%s]", self.storage_policy)
            self.storage_policy_obj = self.commcell.storage_policies.add(self.storage_policy, self.library_name, self.MediaAgent)
            self.log.info("Storage Policy created successfully")

            self.log.info("Creating storage policy Primary copy object")
            self.primary_copy_obj = self.storage_policy_obj.get_copy("Primary")

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

            self.log.info("Setting encryption on Primary copy")
            self.ma_helper.set_encryption(self.primary_copy_obj)
            
            # Started a reboot process of access node previously to reflect the system variable. That needs to be online before going forward
            self.log.info(f"Rebooted Access Node previously, waiting for the Access Node[{self.AWS_KMS_access_node}] to come online")
            while True:
                self.access_node_mediaagent_obj.refresh()
                self.log.info(f"Is access node online ? : {self.access_node_mediaagent_obj.is_online}")
                if self.access_node_mediaagent_obj.is_online:
                    self.log.info("Access Node is ready now")
                    break;
                time.sleep(30)
                

            self.log.info("Creating the KMS")

            self.log.info("Creating KMS [%s]", self.AWS_KMS_name)
            kms_details = {
                "KEY_PROVIDER_TYPE": "KEY_PROVIDER_AWS_KMS",
                "AWS_REGION_NAME": "US East (Ohio)",
                "ACCESS_NODE_NAME": self.AWS_KMS_access_node,
                "KMS_NAME": self.AWS_KMS_name,
                "KEY_PROVIDER_AUTH_TYPE": "AWS_CREDENTIALS_FILE",
                "AWS_CREDENTIALS_FILE_PROFILE_NAME":self.AWS_cred_file_profile_name
            }
            
            self.KMS_obj = self.commcell.key_management_servers.add(kms_details)
            self.log.info(f"KMS {self.AWS_KMS_name} created successfully")
            
            self.log.info("Mapping storage policy and KMS[%s]", self.AWS_KMS_name)
            self.primary_copy_obj.set_key_management_server(self.AWS_KMS_name)
            self.log.info("KMS mapping successful")

            self.log.info("Verifying the master key creation request from log on KMS access node [%s]", self.AWS_KMS_access_node)
            log_line_to_match = "AWSKeyProvider::createMasterKey Creating master key with key provider \[" + self.AWS_KMS_name + "\] for entityId \[" + self.primary_copy_obj.copy_id + "\] entityType \[18\]"
            self.log_verification(log_line_to_match, self.AWS_KMS_access_node, "cvd.log")

            self.ma_helper.restart_mm_service()

            self.log.info("Starting backup")
            self.job_obj = self.subclient_obj.backup("FULL")
            self.log.info("Job started. Job ID [%s]", self.job_obj.job_id)
            self.log.info("Waiting for the job to complete")
            self.job_obj.wait_for_completion()

            log_line_to_match = "AWSKeyProvider::getMasterKey Decrypting key using master key \[.+\] from key provider \["+self.AWS_KMS_name+"\] for entityId \["+self.primary_copy_obj.copy_id+"\]"
            matched_for_backup = self.log_verification(log_line_to_match, self.AWS_KMS_access_node, "cvd.log")

            self.ma_helper.restart_mm_service()

            self.log.info("Starting restore job")
            self.job_obj = self.subclient_obj.restore_out_of_place(self.client, self.restore_path, [self.client_content])
            self.log.info("Job started. Job ID [%s]", self.job_obj.job_id)
            self.log.info("Waiting for for job to complete")
            self.job_obj.wait_for_completion()

            log_line_to_match = "AWSKeyProvider::getMasterKey Decrypting key using master key \[.+\] from key provider \["+self.AWS_KMS_name+"\] for entityId \["+self.primary_copy_obj.copy_id+"\]"
            matched_for_restore = self.log_verification(log_line_to_match, self.AWS_KMS_access_node, "cvd.log")

            # There should be at least one more matched log line after the restore job. That confirms that master key fetched for restore also
            self.compare_log_matching(matched_for_backup, matched_for_restore)

            self.log.info("Creating aux copy")
            self.storage_policy_obj.create_secondary_copy("copy-2", self.library_name, self.MediaAgent)
            self.log.info("Aux copy created successfully")

            self.ma_helper.restart_mm_service()

            self.log.info("Starting aux copy job")
            self.job_obj = self.storage_policy_obj.run_aux_copy()
            self.log.info("Aux Job started. Job ID [%s]", self.job_obj.job_id)
            self.job_obj.wait_for_completion()
            self.log.info("Aux copy job completed successfully")

            log_line_to_match = "AWSKeyProvider::getMasterKey Decrypting key using master key \[.+\] from key provider \["+self.AWS_KMS_name+"\] for entityId \["+self.primary_copy_obj.copy_id+"\]"
            matched_for_aux = self.log_verification(log_line_to_match, self.AWS_KMS_access_node, "cvd.log")

            # There should be at least one more matched log line after the restore job. That confirms that master key fetched for aux copy also
            self.compare_log_matching(matched_for_restore, matched_for_aux)

            self.log.info("Test case completed successfully")

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED