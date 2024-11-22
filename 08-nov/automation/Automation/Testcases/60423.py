# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    previous_run_cleanup()      --  Delete the left over backupset and storage policy from the previous run

    generate_data_run_backup()  --  Generate data and run backup

    create_resources()          --  Created resources for running the test

    restore_and_verify_content()--  Restores and verifies the content using md5 checksum

    verify_client_versions()    --  Verifies the client & MA versions for this testcase

    create_non_dedup_environment()  --  Create non deduplication enabled test environment

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

This testcase verifies that the backups & restores from V9/V10 clients are working with V11 MA

input json file arguments required:

                        "ClientName": "name of the client machine without as in commserve",
                        "AgentName": "File System",
                        "MediaAgentName": "name of the media agent as in commserve",
                        "ClientUserName": 'user name',
                        "ClientPassword": "password',
                        "library_name": name of the Library to be reused - Optional
                        "dedup_path": path where dedup store to be created - MUST if Media Agent is Unix

                        note --
                                ***********************************
                                if library_name_given then reuse_library

                                else create_library_with_this_mountpath

                                if dedup_path_given -> use_given_dedup_path
                                else it will auto_generate_dedup_path
                                ***********************************


Design Steps:
1. Check that given client is client less than V11 [ V9 or V10 ] and MA is V11
2. Clean up left over configuration if any
3. Create required configuration for testing which includs - library/storage policy/subclient
4. Generate Data and run Full Backup
5. Generate Data and run Incremental Backup
6. Run Synthetic Full Backup
7. Perform Restore operation
8. Compare content and restored data using md5 hash
9. Create non-dedup Storage Policy and associate this storage policy to subclient
10. Run Full Backup
11. Restore and compare content and restored data using md5 hash
"""

from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils import mahelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "MA Backward Compatibility Case - Backups & Restores from older version clients"

        self.tcinputs = {
            "MediaAgentName": None,
            "ClientUserName": None,
            "ClientPassword": None
        }
        self.ma_name = None
        self.non_dedup_restore_path = None
        self.non_dedup_sp = None
        self.mount_path = None
        self.client_username = None
        self.client_password = None
        self.dedup_store_path = None
        self.restore_path = None
        self.content_path = None
        self.library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.mm_helper = None
        self.dedup_helper = None
        self.client_machine = None
        self.media_agent_machine = None
        self.opt_selector = None
        self.storage_policy_id = None
        self.testcase_path = None
        self.testcase_path_client = None
        self.testcase_path_media_agent = None
        self.library = None
        self.storage_policy = None
        self.backup_set = None
        self.subclient = None
        self.is_user_defined_lib = False
        self.is_user_defined_dedup = False

    def setup(self):
        """sets up the variables to be used in testcase"""
        if self.tcinputs.get("library_name"):
            self.is_user_defined_lib = True
        if self.tcinputs.get("dedup_path"):
            self.is_user_defined_dedup = True
        self.client_username = self.tcinputs.get("ClientUserName")
        self.client_password = self.tcinputs.get("ClientPassword")
        self.ma_name = self.tcinputs.get("MediaAgentName")
        suffix = str(self.ma_name)[1:] + str(self.tcinputs["ClientName"])[1:]
        if self.is_user_defined_lib:
            self.log.info("Existing library name supplied")
            self.library_name = self.tcinputs.get("library_name")
        else:
            self.library_name = f"{self.id}_lib{suffix}"
        self.storage_policy_name = f"{self.id}_SP{suffix}"
        self.backupset_name = f"{self.id}_BS{suffix}"
        self.subclient_name = f"{self.id}_SC{suffix}"
        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = machine.Machine(self.client.client_name, username=self.client_username,
                                              password=self.client_password)
        self.media_agent_machine = machine.Machine(self.tcinputs["MediaAgentName"], self.commcell)
        drive_path_client = self.opt_selector.get_drive(self.client_machine)
        self.testcase_path_client = f"{drive_path_client}{self.id}"

        self.non_dedup_sp = f'{self.storage_policy_name}_non_dedup'
        if not self.is_user_defined_dedup and "unix" in self.media_agent_machine.os_info.lower():
            self.log.error("LVM enabled dedup path must be input for Unix MA!..")
            raise Exception("LVM enabled dedup path not supplied for Unix MA!..")
        self.content_path = self.client_machine.join_path(self.testcase_path_client, "content_path")
        self.restore_path = self.client_machine.join_path(self.testcase_path_client, "restore_path")
        self.non_dedup_restore_path = self.client_machine.join_path(self.testcase_path_client,
                                                                    "restore_path_non_dedup")

    def previous_run_clean_up(self):
        """delete previous run items"""
        self.log.info("********* clean up **********")
        try:
            # delete the generated content for this testcase
            # machine object initialised earlier
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the generated data at %s", self.content_path)
            else:
                self.log.info("Content directory %s does not exist.", self.content_path)

            # delete the restored directory
            if self.client_machine.check_directory_exists(self.restore_path):
                self.client_machine.remove_directory(self.restore_path)
                self.log.info("Deleted the restored data at %s", self.restore_path)
            else:
                self.log.info("Restore directory %s does not exist.", self.restore_path)

            if self.client_machine.check_directory_exists(self.non_dedup_restore_path):
                self.client_machine.remove_directory(self.non_dedup_restore_path)
                self.log.info("Deleted the non dedup restored data at %s", self.non_dedup_restore_path)
            else:
                self.log.info("Restore directory %s does not exist.", self.non_dedup_restore_path)

            self.log.info("deleting backupset and SP of the test case")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("backup set deleted")
            else:
                self.log.info("backup set does not exist")

            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
                self.log.info("storage policy %s deleted", self.storage_policy_name)
            else:
                self.log.info("storage policy %s does not exist.", self.storage_policy_name)

            if self.commcell.storage_policies.has_policy(self.non_dedup_sp):
                self.commcell.storage_policies.delete(self.non_dedup_sp)
                self.log.info("storage policy %s deleted", self.non_dedup_sp)
            else:
                self.log.info("storage policy %s does not exist.", self.non_dedup_sp)

            if not self.is_user_defined_lib:
                if self.commcell.disk_libraries.has_library(self.library_name):
                    self.commcell.disk_libraries.delete(self.library_name)
                    self.log.info("Library deleted")
                else:
                    self.log.info("Library does not exist.")
        except Exception as exp:
            self.log.info("previous run clean up ERROR")
            self.log.info("ERROR:%s", exp)

    def generate_data_run_backup(self, data_size_gb = 1.0, backup_type="FULL"):
        """
            run a full backup job after generating data

            Args:
                data_size_gb    (float)     --  Content data size to be generated before running backup
                backup_type     (str)       --  Backup Type

            Returns
                an object of running full backup job
        """
        if data_size_gb > 0:
            if self.opt_selector.create_uncompressable_data(self.client.client_name, self.content_path, data_size_gb,
                                                            1, username=self.client_username,
                                                            password=self.client_password):
                self.log.info("generated unique data for subclient")
            else:
                raise Exception("couldn't generate unique data")

        self.log.info("Starting %s backup job", backup_type)
        job = self.subclient.backup(backup_type)
        self.log.info("Backup job: %s", str(job.job_id))
        if not job.wait_for_completion():
            if job.status.lower() == "completed":
                self.log.info("job %s complete", job.job_id)
            else:
                raise Exception(
                    f"Job {job.job_id} Failed with {job.delay_reason}")
        return job

    def create_resources(self):
        """
        Create resources for running the test case

        """
        # create the required resources for the testcase
        # get the drive path with required free space

        # creating testcase directory, mount path, content path, dedup
        # store path


        self.client_machine.create_directory(self.content_path)
        self.log.info("content path created")
        self.client_machine.create_directory(self.restore_path)
        self.log.info("restore path created")
        self.client_machine.create_directory(self.non_dedup_restore_path)
        self.log.info("non dedup restore path created")

        drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine)
        self.testcase_path_media_agent = self.media_agent_machine.join_path(drive_path_media_agent, self.id)

        if self.is_user_defined_dedup:
            self.log.info("custom dedup path supplied")
            self.dedup_store_path = self.media_agent_machine.join_path(self.tcinputs["dedup_path"], self.id)
        else:
            self.dedup_store_path = self.media_agent_machine.join_path(self.testcase_path_media_agent,
                                                                       "dedup_store_path")

        # create library
        if not self.is_user_defined_lib:
            self.mount_path = self.media_agent_machine.join_path(self.testcase_path_media_agent, "mount_path")
            self.library = self.mm_helper.configure_disk_library(
                self.library_name, self.tcinputs["MediaAgentName"], self.mount_path)

        # create SP
        self.storage_policy = self.dedup_helper.configure_dedupe_storage_policy(
            self.storage_policy_name,
            self.library_name,
            self.tcinputs["MediaAgentName"],
            self.dedup_store_path)

        # create backupset
        self.backup_set = self.mm_helper.configure_backupset(
            self.backupset_name, self.agent)

        # create subclient
        self.log.info("check SC: %s", self.subclient_name)
        if not self.backup_set.subclients.has_subclient(
                self.subclient_name):
            self.subclient = self.mm_helper.configure_subclient(
                self.backupset_name,
                self.subclient_name,
                self.storage_policy_name,
                self.content_path,
                self.agent)
            self.log.info("created subclient %s", self.subclient_name)
        else:
            self.log.info("subclient %s exists", self.subclient_name)
            self.subclient = self.backup_set.subclients.get(
                self.subclient_name)

        # set the subclient data reader / streams to one
        self.log.info("set the data readers for subclient %s to 2", self.subclient_name)
        self.subclient.data_readers = 2

    def restore_and_verify_content(self, restore_dir):
        """
        Restores and compares the restored data

        Args;

        restore_dir     (str)   --      Restore Directory
        """
        self.log.info("Running a restore job for the backed up content and verifying the files")
        restore_job = self.subclient.restore_out_of_place(self.client.client_name,
                                                          restore_dir, [self.content_path])
        self.log.info("Restore job: %s", str(restore_job.job_id))
        if not restore_job.wait_for_completion():
            if restore_job.status.lower() == "completed":
                self.log.info("job %s complete", restore_job.job_id)
            else:
                raise Exception(f"Job {restore_job.job_id} Failed with {restore_job.delay_reason}")

        self.log.info("VERIFYING IF THE RESTORED FILES ARE SAME OR NOT")
        restored_files = sorted(self.client_machine.get_files_in_path(restore_dir))
        content_files = sorted(self.client_machine.get_files_in_path(self.content_path))
        self.log.info("Comparing the files using MD5 hash")
        if len(restored_files) == len(content_files):
            for original_file, restored_file in zip(content_files, restored_files):
                if not self.client_machine.compare_files(self.client_machine, original_file, restored_file):
                    self.log.error("Result: Fail")
                    raise ValueError("The restored file is "
                                     "not the same as the original content file")
        else:
            self.log.error("All content files have not been restored.")
            raise Exception("Number of Content files and Restored files are not the same.")

        self.log.info("All the restored files are same as the original content files")


    def verify_client_versions(self):
        """
        Verify that Client Version is below V11 and MA version is V11
        """
        self.log.info("Check client version is one among V9 or V10")
        client_versions=['9.0', '10 R2']
        if self.client.version.strip() in client_versions:
            self.log.info("Client Version is %s", self.client.version.strip())
            self.log.info("VALIDATION : Successfully verified that Client is V9/V10 Client")
        else:
            self.log.error("VALIDATION : Client Version Verification Failed")
            raise Exception(f"Client Version Expected : 9 / 10 Actual : {self.client.version}")

        self.log.info("Check MA version is V11")

        ma_client = self.commcell.clients.get(self.ma_name)
        ma_versions = ['11']
        if ma_client.version.strip() not in ma_versions:
            self.log.info("VALIDATION : MA Version Verification Failed")
            raise Exception(f"MA Version Expected : 11 Actual : {ma_client.version}")
        self.log.info("VALIDATION : Successfully verified that MA is V11")

    def create_non_dedup_environment(self):
        """
        Creates non-dedup test environment for same subclient
        """
        self.log.info("Creating a Non-Dedup storage policy - %s", self.non_dedup_sp)
        self.mm_helper.configure_storage_policy(self.non_dedup_sp, self.library_name, self.ma_name)
        self.log.info("Changing subclient storage policy to - %s", self.non_dedup_sp)
        self.subclient.storage_policy = self.non_dedup_sp

    def run(self):
        """Run function of this test case"""
        try:
            self.verify_client_versions()
            self.previous_run_clean_up()
            self.create_resources()
            # run the first Full backup job with 1 GB data
            self.generate_data_run_backup()
            self.log.info("====VALIDATION : Full Backup Succeeded===")
            # run the second backup job
            self.generate_data_run_backup(1.0, "incremental")
            self.log.info("====VALIDATION : Incremental Backup Succeeded===")
            # run the third backup job
            self.generate_data_run_backup(0, backup_type="Synthetic_full")
            self.log.info("====VALIDATION : Synth Full Backup Succeeded===")

            #Run the Restore job
            self.restore_and_verify_content(self.restore_path)
            self.log.info("===VALIDATION : Restore from Dedup Backup Succeeded==")
            self.log.info("Result: Pass")

            #Assign subclient to NonDedup SP
            self.create_non_dedup_environment()
            #Run the backup job
            self.generate_data_run_backup(1.0)
            self.log.info("====VALIDATION : Non-Dedup FULL Backup Succeeded===")
            #Run the restore job
            self.restore_and_verify_content(self.non_dedup_restore_path)
            self.log.info("===VALIDATION : Restore from Non-Dedup Backup Succeeded==")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """delete all items created for the testcase"""
        try:
            self.log.info("*********************************************")
            self.previous_run_clean_up()
            self.log.info("post run clean up successful")

        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info("ERROR:%s", exp)
