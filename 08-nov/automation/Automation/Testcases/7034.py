# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case
Usecase of this testcase ----------------add
TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    validate_jobs() --  validates that 2 jobs are in running state and an extra job is waiting. 

    run_backup_jobs() -- util function to run backup jobs for given subclients. 

    configure_storage_policy() -- util function to create storage policy.

Design Steps:
	1. Configure tape storage say VTL1, and add single tape media inside the library.
	2. Configure a non-dedupe storage policy using VTL1 and set multiplexing as 2.
	3. Configure a new backupset with three sub-clients say SC1, SC2 and SC3 with the number of readers set as 1 on all.
	4. Launch backup job for both sub-clients at the same time and validate that two jobs are running in parallel and third one is waiting for resource.
	5. Restore one of the multiplexed backup jobs and validate the content on the restored destination.
	6. Configure a disk storage say DiskLib1, with single mountpath and number of writers set as 2.
	7. Configure a non-dedupe storage policy using DiskLib1 and set multiplexing as 2.
	8. Configure a new backupset with three sub-clients say SC1, SC2 and SC3 with the number of readers set as 1 on all.
	9. Launch backup job for both sub-clients at the same time and validate that two jobs are running in parallel and third one is waiting for resource.
    10. Restore one of the multiplexed backup jobs and validate the content on the restored destination.

Sample Input:
    "7034": {
                "ClientName": "clientname",
                "MediaAgentName":"mediaagent",
                "TapeLibraryName": "libraryname",
                "AgentName": "File System"
            }
"""
import time
from AutomationUtils import (constants, commonutils)
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import (MMHelper, DedupeHelper)
from AutomationUtils.options_selector import OptionsSelector
# from cvpysdk.storage import MediaAgent
from cvpysdk.policies.storage_policies import StoragePolicyCopy


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Data Multiplex Tape and All"
        # self.MediaAgent = None
        self.MMHelper = None
        self.DedupeHelper = None
        self.tape_library_name = None
        self.disk_library_name = None
        self.tape_lib_obj = None

        self.media_agent_name = None
        self.backupset_name_1 = None
        self.backupset_name_2 = None
        self.storage_policy_name_1 = None
        self.storage_policy_name_2 = None

        self.subclient_name_1 = None
        self.subclient_name_2 = None
        self.subclient_name_3 = None
        self.subclient_name_4 = None
        self.subclient_name_5 = None
        self.subclient_name_6 = None

        self.content_folder = None
        self.content_path_1 = None
        self.content_path_2 = None
        self.content_path_3 = None
        self.content_path_4 = None
        self.content_path_5 = None
        self.content_path_6 = None
        self.restore_dest_path = None
        self.mount_path = None

        self.client_machine = None
        self.ma_machine = None

        self.tcinputs = {
            "ClientName": None,
            "MediaAgentName": None,
            "TapeLibraryName": None
        }


    def setup(self):
        """Setup function of this test case"""
        self.log.info("Starting test case setup")

        options_selector = OptionsSelector(self.commcell)
        self.media_agent_name = self.tcinputs.get('MediaAgentName')
        self.MMHelper = MMHelper(self)
        self.DedupeHelper = DedupeHelper(self)
        self.tape_library_name = self.tcinputs.get('TapeLibraryName')
        self.disk_library_name = '%s_disk_lib' % str(self.id)

        # Storage Policy
        self.storage_policy_name_1 = '%s_storage_policy1' % str(self.id)
        self.storage_policy_name_2 = '%s_storage_policy2' % str(self.id)

        # Backupset
        self.backupset_name_1 = '%s_backup_set1' % str(self.id)
        self.backupset_name_2 = '%s_backup_set2' % str(self.id)

        # Subclients
        self.subclient_name_1 = '%s_subclient1' % str(self.id)
        self.subclient_name_2 = '%s_subclient2' % str(self.id)
        self.subclient_name_3 = '%s_subclient3' % str(self.id)
        self.subclient_name_4 = '%s_subclient4' % str(self.id)
        self.subclient_name_5 = '%s_subclient5' % str(self.id)
        self.subclient_name_6 = '%s_subclient6' % str(self.id)

        self.client_machine = options_selector.get_machine_object(
            self.tcinputs.get('ClientName')
        )
        self.ma_machine = options_selector.get_machine_object(
            self.tcinputs.get('MediaAgentName')
        )

        # select drive in client machine
        self.log.info(
            'Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(
            self.client_machine, size=40 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating data")
        self.log.info('selected drive: %s', client_drive)

        # select drive in media agent machine.
        self.log.info('Selecting drive in the media agent machine based on space available')
        ma_drive = options_selector.get_drive(self.ma_machine, size=40 * 1024)
        if ma_drive is None:
            raise Exception("No space for hosting backup and ddb")
        self.log.info('selected drive: %s', ma_drive)

        # Content Path
        self.content_folder = self.client_machine.join_path(client_drive, 'Automation', str(self.id))
        self.content_path_1 = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id), 'TestData1')
        self.content_path_2 = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id), 'TestData2')
        self.content_path_3 = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id), 'TestData3')
        self.content_path_4 = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id), 'TestData4')
        self.content_path_5 = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id), 'TestData5')
        self.content_path_6 = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id), 'TestData6')

        # Restore Path
        self.restore_dest_path = self.client_machine.join_path(
            client_drive, 'Automation', str(self.id), 'Restoredata')

        # Mount Path
        self.mount_path = self.ma_machine.join_path(
            ma_drive, 'Automation', str(self.id), 'MP')

        # Clean Up
        self._cleanup()

        # Create directory
        self.log.info("creating directories.")
        self.client_machine.create_directory(self.content_path_1)
        self.client_machine.create_directory(self.content_path_2)
        self.client_machine.create_directory(self.content_path_3)
        self.client_machine.create_directory(self.content_path_4)
        self.client_machine.create_directory(self.content_path_5)
        self.client_machine.create_directory(self.content_path_6)
        self.client_machine.create_directory(self.restore_dest_path)
        self.log.info("Created Content folder and restore path on client")

    def validate_jobs(self, job_list):
        """
        Validates that 2 jobs are running and 1 is waiting for resources. 
        Args:
            job_list (list) -- list of job id's, to be checked for running and waiting state.
        """
        self.log.info("Validating jobs status")
        running_job = 0
        waiting_job = 0
        for job in job_list:
            # Check phase for the job.
            while job.phase not in ("Backup", "Archieve Index", None):
                self.log.info(f"Job Phase Reached  ->  {job.phase}")
                if not job.phase:
                    raise Exception("Jobs did not start simultaneously!")
            status = job.status.lower()
            self.log.info("Job status %s", status)
            if status == 'running':
                running_job += 1
            if status == 'waiting':
                waiting_job += 1
        self.log.info(f"Running job count -> {running_job}, Waiting job count {waiting_job}")
        if running_job != 2 or waiting_job != 1:
            raise Exception("Job Validation Failed!")
    
    def restore_verify(self, src_path, dest_path):
        """
            Performs the verification after restore

            Args:
                src_path         (str)       --  path on source machine that is to be compared.

                dest_path        (str)       --  path on destination machine that is to be compared.

            Raises:
                Exception - Any difference from source data to destination data

        """
        self.log.info("Comparing source:%s destination:%s", src_path, dest_path)
        diff_output = self.client_machine.compare_folders(self.client_machine, src_path, dest_path)

        if not diff_output:
            self.log.info("Checksum comparison successful")
        else:
            self.log.error("Checksum comparison failed")
            self.log.info("Diff output: \n%s", diff_output)
            raise Exception("Checksum comparison failed")

    def run_backup_job(self, subclients, content_paths):
        """
        Run full backup job for a given subclients.
        Args:
            subclients (list) -- list of subclients for which backup needs to be run.
            content_paths (list) -- to create new dummy data
        """
        job_list = []
        # Create uncompressable data for all subclients.
        for content_path in content_paths:
            if not self.MMHelper.create_uncompressable_data(self.client_machine, content_path, 0.1, 50):
                self.log.error(
                    "unable to Generate Data at %s", content_path)
                raise Exception(
                    "unable to Generate Data at {0}".format(content_path))
            self.log.info("Generated Data at %s", content_path)
        # Start Backup for all subclients.
        for subclient in subclients:
            self.log.info("Stating backup job for %s", subclient)
            job = subclient.backup(r'full')
            self.log.info("Backup job id %s", job.job_id)
            job_list.append(job)
            self.log.info("Wait for 10 seconds.")
            time.sleep(10)

        self.validate_jobs(job_list)
        for job in job_list:
            if not job.wait_for_completion():
                self.log.info("Failed to run FULL backup job on CS with error: {0}".format(job.delay_reason))
            self.log.info("Backup completed for job id %s", job.job_id)

    def configure_storage_policy(self, storage_policy_name, library_name):
        """
        Util function to create storage policy.
        Args:
            storage policy name (str) -- name to assign to storage policy.
            library name (str) -- library to be used for storage policy.
        """
        self._log.info("check SP: %s", storage_policy_name)
        if not self.commcell.storage_policies.has_policy(storage_policy_name):
            self._log.info("adding Storage policy...")
            storage_policy = self.commcell.storage_policies.add(
                storage_policy_name=storage_policy_name,
                library=library_name,
                media_agent=self.media_agent_name,
                number_of_streams=1
            )
            self._log.info("Storage policy config done.")
            return storage_policy
        self._log.info("Storage policy exists!")
        storage_policy = self.commcell.storage_policies.get(storage_policy_name)
        return storage_policy

    def run(self):
        """Run function of this test case"""
        try:

            # Create non-dedupe storage policy
            self.configure_storage_policy(
                self.storage_policy_name_1,
                self.tape_library_name
            )
            # Set Multiplexing factor as 2
            spcopy_obj = StoragePolicyCopy(self.commcell, self.storage_policy_name_1, "Primary")
            spcopy_obj.set_multiplexing_factor(2)
            self.log.info(f"Set Multiplexing Factor as 2 for {self.storage_policy_name_1}")

            # Creating a new backupset
            self.log.info("creating backupset %s", self.backupset_name_1)
            self.MMHelper.configure_backupset(self.backupset_name_1, self.agent)

            # Subclients
            self.log.info("creating subclient %s", self.subclient_name_1)
            subclient1 = self.MMHelper.configure_subclient(
                self.backupset_name_1, self.subclient_name_1,
                self.storage_policy_name_1, self.content_path_1, self.agent
            )

            self.log.info("creating subclient %s", self.subclient_name_2)
            subclient2 = self.MMHelper.configure_subclient(
                self.backupset_name_1, self.subclient_name_2,
                self.storage_policy_name_1, self.content_path_2, self.agent
            )

            self.log.info("creating subclient %s", self.subclient_name_3)
            subclient3 = self.MMHelper.configure_subclient(
                self.backupset_name_1, self.subclient_name_3,
                self.storage_policy_name_1, self.content_path_3, self.agent
            )
            # Settings readers to 1
            self.log.info("Setting subclinets readers to 1")
            subclient1.data_readers = 1
            subclient1.allow_multiple_readers = True

            subclient2.data_readers = 1
            subclient2.allow_multiple_readers = True

            subclient3.data_readers = 1
            subclient3.allow_multiple_readers = True

            # Backup Job
            self.run_backup_job(
                [subclient1, subclient2, subclient3],
                [self.content_path_1, self.content_path_2, self.content_path_3]
            )
            self.log.info('Backup Operations Complete.')

            # Restore Job
            restore_job = subclient1.restore_out_of_place(self.client, self.restore_dest_path,
                                                         [self.content_path_1])
            self.log.info("restore job [%s] has started from primary copy.", restore_job.job_id)
            if not restore_job.wait_for_completion():
                self.log.error(
                    "restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
                raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                                restore_job.delay_reason))
            self.log.info(
                "restore job [%s] has completed.", restore_job.job_id)
            
            # Verify Restore
            if self.client_machine.os_info == 'UNIX':
                dest_path = commonutils.remove_trailing_sep(self.restore_dest_path, '/')
            else:
                dest_path = commonutils.remove_trailing_sep(self.restore_dest_path, '\\')
            
            dest_path = self.client_machine.join_path(dest_path, 'Testdata1')

            self.restore_verify(self.content_path_1, dest_path)

            # Data Aging Job
            data_aging_job = self.commcell.run_data_aging(storage_policy_name=self.storage_policy_name_1,
                                                          is_granular=True, include_all_clients=True)
            self.log.info(
                "Data Aging job [%s] has started.", data_aging_job.job_id)
            if not data_aging_job.wait_for_completion():
                self.log.error(
                    "Data Aging job [%s] has failed with %s.", data_aging_job.job_id, data_aging_job.delay_reason)
                raise Exception(
                    "Data Aging job [{0}] has failed with {1}.".format(data_aging_job.job_id,
                                                                       data_aging_job.delay_reason))
            self.log.info(
                "Data Aging job [%s] has completed.", data_aging_job.job_id)

            # Configure Disk Library
            self.MMHelper.configure_disk_library(
                library_name=self.disk_library_name,
                mount_path=self.mount_path
            )

            # Non dedupe Storage Policy
            self.configure_storage_policy(
                self.storage_policy_name_2,
                self.disk_library_name
            )

            # Setting Multiplexing Factor as 2
            spcopy_obj = StoragePolicyCopy(self.commcell, self.storage_policy_name_2, "Primary")
            spcopy_obj.set_multiplexing_factor(2)
            self.log.info(f"Set Multiplexing Factor as 2 for {self.storage_policy_name_2}")

            # Backupset
            self.log.info("creating backupset %s", self.backupset_name_2)
            self.MMHelper.configure_backupset(self.backupset_name_2, self.agent)

            # Create Subclient
            self.log.info("creating subclient %s", self.subclient_name_4)
            subclient4 = self.MMHelper.configure_subclient(
                self.backupset_name_2, self.subclient_name_4,
                self.storage_policy_name_2, self.content_path_4, self.agent
            )

            self.log.info("creating subclient %s", self.subclient_name_2)
            subclient5 = self.MMHelper.configure_subclient(
                self.backupset_name_2, self.subclient_name_5,
                self.storage_policy_name_2, self.content_path_5, self.agent
            )

            self.log.info("creating subclient %s", self.subclient_name_3)
            subclient6 = self.MMHelper.configure_subclient(
                self.backupset_name_2, self.subclient_name_6,
                self.storage_policy_name_2, self.content_path_6, self.agent
            )

            # Setting Readers to 1
            self.log.info("Setting subclinets readers to 1")
            subclient4.data_readers = 1
            subclient4.allow_multiple_readers = True

            subclient5.data_readers = 1
            subclient5.allow_multiple_readers = True

            subclient6.data_readers = 1
            subclient6.allow_multiple_readers = True

            # Run backup job
            self.run_backup_job(
                [subclient4, subclient5, subclient6],
                [self.content_path_4, self.content_path_5, self.content_path_6]
            )
            self.log.info('Backup operations set 2 complete.')

            # Restore
            restore_job = subclient4.restore_out_of_place(self.client, self.restore_dest_path,
                                                          [self.content_path_4])
            self.log.info("restore job [%s] has started from primary copy.", restore_job.job_id)
            if not restore_job.wait_for_completion():
                self.log.error(
                    "restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
                raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                                restore_job.delay_reason))
            self.log.info(
                "restore job [%s] has completed.", restore_job.job_id)
            
            # Verify Restore.
            if self.client_machine.os_info == 'UNIX':
                dest_path = commonutils.remove_trailing_sep(self.restore_dest_path, '/')
            else:
                dest_path = commonutils.remove_trailing_sep(self.restore_dest_path, '\\')
            
            dest_path = self.client_machine.join_path(dest_path, 'Testdata4')
            self.restore_verify(self.content_path_4, dest_path)

            # Data Aging Job
            data_aging_job = self.commcell.run_data_aging(storage_policy_name=self.storage_policy_name_2,
                                                          is_granular=True, include_all_clients=True)
            self.log.info(
                "Data Aging job [%s] has started.", data_aging_job.job_id)
            if not data_aging_job.wait_for_completion():
                self.log.error(
                    "Data Aging job [%s] has failed with %s.", data_aging_job.job_id, data_aging_job.delay_reason)
                raise Exception(
                    "Data Aging job [{0}] has failed with {1}.".format(data_aging_job.job_id,
                                                                       data_aging_job.delay_reason))
            self.log.info(
                "Data Aging job [%s] has completed.", data_aging_job.job_id)


        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def _cleanup(self):
        """Cleanup the entities created"""

        self.log.info(
            "********************** CLEANUP STARTING *************************")
        try:
            # Delete backupset
            self.log.info("Deleting BackupSet: %s if exists",
                          self.backupset_name_1)
            if self.agent.backupsets.has_backupset(self.backupset_name_1):
                self.agent.backupsets.delete(self.backupset_name_1)
                self.log.info("Deleted BackupSet: %s", self.backupset_name_1)

            self.log.info("Deleting BackupSet: %s if exists",
                          self.backupset_name_2)
            if self.agent.backupsets.has_backupset(self.backupset_name_2):
                self.agent.backupsets.delete(self.backupset_name_2)
                self.log.info("Deleted BackupSet: %s", self.backupset_name_2)

            # Delete Storage Policy
            self.log.info("Deleting Storage Policy: %s if exists",
                          self.storage_policy_name_1)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name_1):
                self.commcell.storage_policies.delete(self.storage_policy_name_1)
                self.log.info("Deleted Storage Policy: %s",
                              self.storage_policy_name_1)

            self.log.info("Deleting Storage Policy: %s if exists",
                          self.storage_policy_name_2)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name_2):
                self.commcell.storage_policies.delete(self.storage_policy_name_2)
                self.log.info("Deleted Storage Policy: %s",
                              self.storage_policy_name_2)

            # Restore and content folder if created.
            if self.client_machine.check_directory_exists(self.content_folder):
                self.client_machine.remove_directory(self.content_folder)
            self.log.info("Removed Content directory")

            if self.client_machine.check_directory_exists(self.restore_dest_path):
                self.client_machine.remove_directory(self.restore_dest_path)
            self.log.info("Removed Restore directory")

        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception(
                "Error encountered during cleanup: {0}".format(str(exp)))

        self.log.info(
            "********************** CLEANUP COMPLETED *************************")

    def tear_down(self):
        """Tear Down function of this test case"""
        if self.status != constants.FAILED:
            self._cleanup()
        else:
            self.log.error(
                "Testcase shows failure in execution, not cleaning up the test environment ...")
