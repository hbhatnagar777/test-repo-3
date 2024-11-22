# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()             --  Initialize TestCase class

    setup()         --  setup function of this test case

    run()                  --  run function of this test case

    generate_data()   -- Generates the data on the share

    run_subclient_verify()    -- Restores from a subclient and verifies the data restored

"""

from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.machine import Machine
from cvpysdk.job import Job


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.base_path = None
        self.tmp_path = None
        self.backupset_name = None
        self.TestPath = None
        self.restorelocation = None
        self.ClientName = None
        self.config = None
        self.fshelper = None
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "PlanName": None,
            "TestPath": None,
            "RestorePath": None
        }

    def setup(self):
        """Setup function of the testcase
        Initializing Pre-requisites for this testcase """

        self.name = "Overlapping Subclinet Content"
        self.fshelper = FSHelper(self)
        self.fshelper.populate_tc_inputs(self, mandatory=False)
        self.subclient = CommonUtils(self.commcell)

    def wait_for_job_completion(self, job_id):
        """
        Waits for job completion
        Args:
            job_id (str): Job id
        Returns:
            None
        Raises:
            Exception if job was failed
        """
        job_obj = self.commcell.job_controller.get(job_id)

        self.log.info(f"{job_obj.job_type} Job {job_id} has started. Waiting for job completion")

        if not job_obj.wait_for_completion():
            raise Exception(f"{job_obj.job_type} Job {job_id} was {job_obj.status}")

        self.log.info(f"{job_obj.job_type} Job {job_id} successfully completed")

    def generate_data(self, path, file_ext, for_incr=False):
        """
            Generates data on the given path

            Args:
                path (str) : Path where the data has to be generated
                file_ext (str) : Extension of the file. For example(".full", ".tmp")
                for_incr (bool) : True to generate data for incremental
            Returns:
                None
        """

        if not for_incr:
            self.log.info(f"Creating directory: {path}")
            self.client_machine.create_directory(directory_name=path, force_create=True)
        else:
            file_ext = ".incr"

        for file_num in range(10):
            file_path = self.client_machine.join_path(path, f'test{file_num}{file_ext}')
            content = f"This is file {file_num}{file_ext}"
            self.client_machine.create_file(file_path, content)

    def restore_subclient_verify(self, dest_client, dest_path, paths, subclient_obj, restore_tmp=False):
        """
        Run restore for the subclient and also verifies if the data was restored correctly.

        Args:
            dest_client (str): Destination client name
            dest_path (str): Destination path for restore
            paths (str): Paths to be restored
            subclient_obj (object): Subclient object
            restore_tmp (bool): Flag to verify tmp restore. Default is False.

        """
        job = self.subclient.subclient_restore_out_of_place(destination_path=dest_path,
                                                            paths=[paths],
                                                            client=dest_client,
                                                            subclient=subclient_obj)

        self.wait_for_job_completion(job.job_id)

        restored_files = self.client_machine.get_files_in_path(dest_path)
        self.log.info(f"Restored files structure: {restored_files}")

        if restore_tmp:
            expected_files = self.client_machine.get_files_in_path(self.tmp_path)
        else:
            expected_files = self.client_machine.get_files_in_path(folder_path=self.base_path, recurse=False)

        self.log.info(f"Content in restored_files and expected_files: {restored_files}, {expected_files}")

        checksum_result = self.client_machine.compare_checksum(source_path=restored_files,
                                                               destination_path=expected_files)
        if checksum_result[0]:
            self.log.info("Checksum comparison successful")
            self.log.info("First subclient filtered out overlapping files successfully")
        else:
            raise Exception("Error occurred while comparing the checksums")

        if self.client_machine.check_directory_exists(dest_path):
            self.client_machine.remove_directory(dest_path)

    def run(self):
        """Main function for test case execution"""
        try:
            if self.client_machine.check_directory_exists(self.id):
                self.client_machine.remove_directory(self.id)

            self.base_path = self.client_machine.join_path(self.test_path, f'{self.id}_auto')

            self.tmp_path = self.client_machine.join_path(self.base_path, f"{self.id}_tmp")

            self.generate_data(self.base_path, file_ext=".full")

            self.generate_data(self.tmp_path, file_ext=".tmp")

            self.log.info("Force Create Option passed. Deleting existing one and creating new backupset")
            self.fshelper.create_backupset(name=f"Backupset_{self.id}", delete=True)

            self.log.info(f"Creating Subclient 'Subclient_{self.id}' for the  backupset 'Backupset_{self.id}'")
            self.backupset.subclients.add(subclient_name=f"Subclient_{self.id}",
                                          storage_policy=self.tcinputs['PlanName'])

            subclient = self.backupset.subclients.get(f"Subclient_{self.id}")

            self.log.info("Adding content for the subclient 'Subclient_{self.id}'")
            subclient.content = [self.base_path]

            self.log.info(f"Creating Subclient '{self.id}_Subclient' for the  backupset 'Backupset_{self.id}'")
            self.backupset.subclients.add(subclient_name=f"{self.id}_Subclient",
                                          storage_policy=self.tcinputs['PlanName'])

            subclient_new = self.backupset.subclients.get(f"{self.id}_Subclient")

            self.log.info("Adding content for the subclient '{self.id}_Subclient'")
            subclient_new.content = [self.tmp_path]

            job = subclient.backup(backup_level="Full")

            self.wait_for_job_completion(job.job_id)

            self.log.info("Run a restore of the backup data"
                          " and verify correct data is restored")
            self.restore_subclient_verify(dest_client=self.tcinputs['ClientName'],
                                          dest_path=self.tcinputs['RestorePath'],
                                          paths=self.base_path,
                                          subclient_obj=subclient,
                                          restore_tmp=False)

            job2 = subclient_new.backup(backup_level="Full")

            self.wait_for_job_completion(job2.job_id)

            self.log.info("Run a restore of the backup data"
                          " and verify correct data is restored.")
            self.restore_subclient_verify(dest_client=self.tcinputs['ClientName'],
                                          dest_path=self.tcinputs['RestorePath'],
                                          paths=self.tmp_path,
                                          subclient_obj=subclient_new,
                                          restore_tmp=True)

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))

        finally:
            try:
                self.log.info("Cleaning up all the entities created")
                if self.client_machine.check_directory_exists(self.base_path):
                    self.client_machine.remove_directory(self.base_path)
                if self.client_machine.check_directory_exists(self.tcinputs['RestorePath']):
                    self.client_machine.remove_directory(self.tcinputs['RestorePath'])
            except Exception as excp:
                self.log.error('Cleanup failed with error: %s', str(excp))
