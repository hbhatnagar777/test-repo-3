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

    log_verification() -- Matched the log lines passed with the log file

    compare_log_matching() -- Compares the log line match count with the previously matched count


    Input Example:

    "testCases": {
				"62140": {
					"ClientName": "client1",
					"AgentName": "File System",
					"MediaAgent": "ma1",
					"AwsKmsAccessNode": "awsclient1",
				}
                }

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from MediaAgents.MAUtils.mahelper import MMHelper, DedupeHelper


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "AWS KMS with access Node ( IAM based authentication )"

        self.is_client_directory_created = None
        self.is_ma_directory_created = None
        self.status = constants.PASSED
        self.kms_details = None
        self.ma_helper = None
        self.dedupe_helper = None
        self.client_name = None
        self.media_agent_name = None
        self.aws_kms_acess_node = None

        self.sp_name = None
        self.library_name = None
        self.sc_name = None
        self.bs_name = None
        self.kms_name = None
        self.copy_name = None
        self.ma_machine = None
        self.ma_path = None
        self.client_machine = None
        self.client_path = None
        self.library_path = None
        self.ddb_path = None
        self.sc_content = None
        self.restore_path = None
        self.ma_obj = None
        self.client_ma_obj = None
        self.aws_access_node_ma_obj = None
        self.storage_policy_obj = None
        self.primary_copy_obj = None
        self.backup_set_obj = None
        self.aws_access_node_ma_obj = None
        self.job_obj = None
        self.subclient_obj = None

    def setup(self):
        """Setup function of this test case"""

        self.log.info("This is setup method")
        self.ma_helper = MMHelper(self)
        self.dedupe_helper = DedupeHelper(self)

        self.client_name = self.tcinputs['ClientName']
        self.media_agent_name = self.tcinputs['MediaAgent']
        self.aws_kms_acess_node = self.tcinputs['AwsKmsAccessNode']

        self.sp_name = f"TestCase_{self.id}_SP"
        self.library_name = f"TestCase_{self.id}"
        self.sc_name = f"TestCase_{self.id}_SC"
        self.bs_name = f"TestCase_{self.id}_BS"
        self.kms_name = f"TestCase_{self.id}_KMS"
        self.copy_name = "Copy-2"

        self.ma_machine, self.ma_path = self.ma_helper.generate_automation_path(self.media_agent_name, 10000)
        self.client_machine, self.client_path = self.ma_helper.generate_automation_path(self.client_name, 5000)

        self.library_path = self.ma_path + "lib"
        self.log.info(f"Library path: {self.library_path}")
        self.ddb_path = self.ma_path + "DDB"
        self.log.info(f"DDB Path: {self.ddb_path}")
        self.sc_content = self.client_path + "content"
        self.log.info(f"Sub-client content path: {self.sc_content}")
        self.restore_path = self.client_path + "restore"
        self.log.info(f"Restore path: {self.restore_path}")

        self.log.info("Creating MediaAgent objects")
        self.ma_obj = self.commcell.media_agents.get(self.media_agent_name)
        self.client_ma_obj = self.commcell.media_agents.get(self.client_name)
        self.aws_access_node_ma_obj = self.commcell.media_agents.get(self.aws_kms_acess_node)

    def cleanup(self):
        """ Cleanup method of this test case"""
        try:
            self.log.info("Starting cleanup")
            if self.agent.backupsets.has_backupset(self.bs_name):
                self.log.info(f"BackupSet [{self.bs_name}] exists, deleting that")
                self._agent.backupsets.delete(self.bs_name)
                self.log.info("Backup set deleted successfully")

            if self.commcell.storage_policies.has_policy(self.sp_name):
                self.log.info(f"Storage policy [{self.sp_name}] exists, deleting that")
                self.log.info("Re-associating all sub clients before deleting the SP")
                self.sp_obj_to_reassociate = self.commcell.storage_policies.get(self.sp_name)
                self.sp_obj_to_reassociate.reassociate_all_subclients()
                self.log.info(f"Deleting the SP {self.sp_name}")
                self.commcell.storage_policies.delete(self.sp_name)
                self.log.info("Storage policy deleted successfully")

            if self.commcell.disk_libraries.has_library(self.library_name):
                self.log.info(f"Library [{self.library_name}] exists, deleting that")
                self.commcell.disk_libraries.delete(self.library_name)
                self.log.info("Library deleted successfully")

            if self.commcell.key_management_servers.has_kms(self.kms_name):
                self.log.info(f"KMS [{self.kms_name}] already exists")
                self.commcell.key_management_servers.delete(self.kms_name)
                self.log.info("KMS deleted successfully")

            self.log.info("Cleanup completed")

        except Exception as excp:
            self.log.error(f"cleanup:: cleanup failed. {str(excp)}")
            self.result_string = f"cleanup:: cleanup failed. {str(excp)}"

    def tear_down(self):
        """ This is tear down method"""
        self.log.info("Starting tear down method")

        if self.status != constants.FAILED:
            self.log.info("Test case PASSED, deleting BS,SP,Library")
            self.cleanup()

        self.log.info("Disabling Ransomware [%s]", self.media_agent_name)
        self.ma_obj.set_ransomware_protection(False)

        if self.is_client_directory_created:
            self.log.info("Client directory created, deleting that")
            self.ma_helper.remove_content(self.client_path, self.client_machine)

        self.log.info("Tear down completed")

    def log_verification(self, log_line_to_match, machine_name, log_file):
        """Matched the log lines passed with the log file
        :param
            log_line_to_match (str) -- pattern to match
            machine_name ( object of Machine class ) -- machine of the log location
            log_file ( str ) -- log file name
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
            self.status = constants.FAILED
            raise Exception("Log verification failed")

    def compare_log_matching(self, previous_match_count, current_match_count):
        """ Compares the log line match count with the previously matched count"""
        if current_match_count > previous_match_count:
            self.log.info("Log Verified:: Master key fetched for the last job")
            return

        raise Exception(
            "Log verification failed. No extra log line found for the last job, means, no marster key fetched for the last job")

    def run(self):
        try:
            self.log.info("This is run method")

            self.cleanup()

            self.log.info(f"Creating library[{self.library_name}]")
            self.commcell.disk_libraries.add(self.library_name, self.media_agent_name, self.library_path)
            self.is_ma_directory_created = True
            self.log.info("Library created successfully")

            self.log.info(f"Creating Storage Policy[{self.sp_name}]")
            self.storage_policy_obj = self.commcell.storage_policies.add(self.sp_name, self.library_name,
                                                                         self.media_agent_name, self.ddb_path,
                                                                         dedup_media_agent=self.media_agent_name)
            self.log.info("Successfully created storage policy")

            self.log.info("Creating storage policy Primary copy object")
            self.primary_copy_obj = self.storage_policy_obj.get_copy("Primary")

            self.log.info(f"Creating BackupSet [{self.bs_name}]")
            self.backup_set_obj = self.agent.backupsets.add(self.bs_name)
            self.log.info("Backup set created successfully")

            self.log.info(f"Creating sub-client [{self.sc_name}]", )
            self.subclient_obj = self.backup_set_obj.subclients.add(self.sc_name, self.sp_name)
            self.log.info("Sub client creation successful")

            self.log.info("Generating SubClient content")
            self.ma_helper.create_uncompressable_data(self.client_name, self.sc_content, 3)
            self.is_client_directory_created = True
            self.log.info("Content generation completed")

            self.subclient_obj.content = [self.sc_content]
            self.log.info("successfully added content to subclient")

            
            self.log.info("Powering-on the access node if power management enabled")
            if self.aws_access_node_ma_obj._is_power_management_enabled:
                self.aws_access_node_ma_obj.power_on()
               
            
            self.log.info(f"Creating KMS [{self.kms_name}]")
            self.kms_details = {
                "KEY_PROVIDER_TYPE": "KEY_PROVIDER_AWS_KMS",
                "ACCESS_NODE_NAME": self.aws_kms_acess_node,
                "KMS_NAME": self.kms_name,
                "KEY_PROVIDER_AUTH_TYPE": "AWS_IAM"
            }

            self.log.info(f"KMS creation input : {str(self.kms_details)}")
            self.commcell.key_management_servers.add(self.kms_details)
            self.log.info("KMS created successfully")
            
            self.log.info("Setting encryption on Primary copy")
            self.ma_helper.set_encryption(self.primary_copy_obj)
            
            self.log.info(f"Mapping storage policy and KMS[{self.kms_name}]")
            self.primary_copy_obj.set_key_management_server(self.kms_name)
            self.log.info("KMS mapping successful")

            self.log.info(
                f"Verifying the master key creation request from log on KMS access node [{self.aws_kms_acess_node}]")
            log_line_to_match = "AWSKeyProvider::createMasterKey Creating master key with key provider \[" + self.kms_name + "\] for entityId \[" + self.primary_copy_obj.copy_id + "\] entityType \[18\]"
            self.log_verification(log_line_to_match, self.aws_kms_acess_node, "cvd.log")

            self.ma_helper.restart_mm_service()

            self.log.info("Starting backup")
            self.job_obj = self.subclient_obj.backup("FULL")
            self.log.info("Job started. Job ID [%s]", self.job_obj.job_id)
            self.log.info("Waiting for the job to complete")
            self.job_obj.wait_for_completion()

            log_line_to_match = "AWSKeyProvider::getMasterKey Decrypting key using master key \[.+\] from key provider \[" + self.kms_name + "\] for entityId \[" + self.primary_copy_obj.copy_id + "\]"
            matched_for_backup = self.log_verification(log_line_to_match, self.aws_kms_acess_node, "cvd.log")

            self.ma_helper.restart_mm_service()

            self.log.info("Starting restore job")
            self.job_obj = self.subclient_obj.restore_out_of_place(self.client_name, self.restore_path,
                                                                   [self.sc_content])
            self.log.info(f"Job started. Job ID [{self.job_obj.job_id}]")
            self.log.info("Waiting for for job to complete")
            self.job_obj.wait_for_completion()

            log_line_to_match = "AWSKeyProvider::getMasterKey Decrypting key using master key \[.+\] from key provider \[" + self.kms_name + "\] for entityId \[" + self.primary_copy_obj.copy_id + "\]"
            matched_for_restore = self.log_verification(log_line_to_match, self.aws_kms_acess_node, "cvd.log")

            self.compare_log_matching(matched_for_backup, matched_for_restore)

            self.log.info("Creating aux copy")
            self.storage_policy_obj.create_secondary_copy(self.copy_name, self.library_name, self.media_agent_name)
            self.log.info("Aux copy created successfully")

            self.ma_helper.restart_mm_service()

            self.log.info("Starting aux copy job")
            self.job_obj = self.storage_policy_obj.run_aux_copy()
            self.log.info(f"Aux Job started. Job ID [{self.job_obj.job_id}]")
            self.job_obj.wait_for_completion()
            self.log.info("Aux copy job completed successfully")

            log_line_to_match = "AWSKeyProvider::getMasterKey Decrypting key using master key \[.+\] from key provider \[" + self.kms_name + "\] for entityId \[" + self.primary_copy_obj.copy_id + "\]"
            matched_for_aux = self.log_verification(log_line_to_match, self.aws_kms_acess_node, "cvd.log")

            self.compare_log_matching(matched_for_restore, matched_for_aux)

            self.log.info("Test case completed successfully")

        except Exception as excp:
            self.status = constants.FAILED
            self.result_string = str(excp)
            self.log.error(str(excp))
