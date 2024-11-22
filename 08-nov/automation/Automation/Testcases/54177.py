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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

"""
import re
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper, CommitCondition


class TestCase(CVTestCase):
    """Testcase for system state commit for regular file data"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "System State Commit-Regular files restore"
        self.applicable_os = self.os_list.WINDOWS
        self.show_to_user = False
        self.tcinputs = {
            "DestinationPath": None,
            "StoragePolicyName": None
        }
        self.client_machine = None
        self.helper = None

    def run(self):
        """Follows the following steps
        1. Create a new backupset
        2. Running a full system state backup
        3. Committing the job during system state backup
        4. Committing the job during SPF backup
        5. Restoring the backed up file
        6. Run an incremental system state backup
        7. Getting the dict of collect files and the offsets till which eath of
            it was processed
        8. Get the numcolltot file's path
        9. Getting a processed collect file
        10. Getting contents of collect file till which it was processed
        11. Getting the list of files that have been backed up
        12. Picking the first file and restoring it
        """
        Path = "C:\\Test"
        Path2 = "C:\\Test2"
        systemstate_content_path = "C:\\windows\\assembly\\test"

        try:
            self.helper = FSHelper(self)
            FSHelper.populate_tc_inputs(self, mandatory=False)
            self.log.info("Step 1: Creating a backupset")
            backupset_name = "Test_54177"
            self.helper.create_backupset(backupset_name, delete=True)
            self.helper.create_subclient("default", self.tcinputs['StoragePolicyName'], ["\\"])
            self.helper.update_subclient(storage_policy=self.tcinputs['StoragePolicyName'],
                                         allow_multiple_readers=True, data_readers=10)

            self.log.info("Step 2: Run a full system state backup")
            job = self.helper.run_systemstate_backup(backup_type='FULL', wait_to_complete=True)

            self.log.info("Populating data")
            if self.client_machine.check_directory_exists(Path):
                self.client_machine.remove_directory(Path)
            self.client_machine.create_directory(Path)
            self.helper.generate_testdata([".txt"], path=Path)

            if self.client_machine.check_directory_exists(systemstate_content_path):
                self.client_machine.remove_directory(systemstate_content_path)
            self.client_machine.create_directory(systemstate_content_path)
            self.log.info("creating system files")
            self.client_machine.generate_test_data(file_path=systemstate_content_path, dirs=2, file_size=100000,
                                                   files=5)

            self.log.info("Step 3: Run an incremental system state backup")
            job_inc = self.helper.run_systemstate_backup(backup_type='Incremental', wait_to_complete=False)

            self.log.info("Step 4: Committing the job during SPF backup")
            while True:
                if self.helper.get_logs_for_job_from_file(job_inc[0].job_id, "clBackup.log",
                                                          "Backup SystemProtectedFile component"):
                    self.helper.commit_job(job_inc[0], 1, CommitCondition.SECONDS)
                    break

            self.log.info("Restoring the content backed up")
            restore_job = self.backupset.restore_out_of_place(self.client,
                                                              paths=[r'C:\Test\1.txt']
                                                              , destination_path=self.tcinputs['DestinationPath'])

            self.log.info("Step 5: Restoring the backed up file")
            if restore_job.wait_for_completion():
                file = '1.txt'
                restored_file = self.client_machine.join_path(self.tcinputs['DestinationPath'], file)
                if self.client_machine.check_file_exists(restored_file):
                    self.log.info("Restored file succesfully")
                    self.log.info("Test case executed succesfully")
                    self.log.info("Cleaning up the restored file")
                    self.client_machine.delete_file(restored_file)

                else:
                    raise Exception("The file was not restored to the destination.")

            else:
                raise Exception(
                    "The restore job failed with error: {0}".format(restore_job.delay_reason))

            self.log.info("Restoring regular files from a job committed during regular file backup")

            self.log.info("Populating data")
            if self.client_machine.check_directory_exists(Path2):
                self.client_machine.remove_directory(Path2)
            self.client_machine.create_directory(Path2)
            self.helper.generate_testdata([".xml"], path=Path2, no_of_files=500)
            self.client_machine.generate_test_data(file_path=Path2, dirs=3, file_size=100000, files=5)

            self.log.info("Step 6: Run an incremental system state backup")
            job_inc = self.helper.run_systemstate_backup(backup_type='Incremental', wait_to_complete=False)

            self.helper.commit_job(job_inc[0], 50, CommitCondition.FILES)

            self.log.info("Step 7: Getting the dict of collect files and the offsets till which each of"
                          "it was processed.")
            cvf_dict = self.helper.parse_backup_restart_string(job_inc[0])

            self.log.info("Step 8: Get the numcollincs file's path")
            cvf_path = self.client_machine.join_path(
                self.client.job_results_directory,
                "CV_JobResults\iDataAgent\FileSystemAgent", "2",
                self.subclient.subclient_id,
                "NumColInc{}.cvf")

            self.log.info("Step 9: Getting a processed collect file")
            for cvf_id, offset in cvf_dict.items():
                if offset == -1:  # CVF IS YET TO BE PROCESSED
                    continue

                elif offset == -999:
                    continue
                else:
                    break

            self.log.info("Step 10: Getting contents of collect file till which it was processed")
            entries = self.client_machine.read_file(cvf_path.format(cvf_id), end=offset)

            self.log.info("Step 11: Getting the list of files that have been backed up")
            match = re.findall(r"(?<=\*\?\?).*(?=\|\<FILE\>)", entries)

            self.log.info("Step 12: Picking the first file and restoring it")
            if len(match) != 0:
                file_name = match[0]
            else:
                raise Exception(
                    "No files were found matching the regular expression, implying no files were backed up.")

            self.log.info("Restoring the content backed up")
            restore_job = self.backupset.restore_out_of_place(self.client,
                                                              paths=[file_name]
                                                              , destination_path=self.tcinputs['DestinationPath'])
            if restore_job.wait_for_completion():
                file_split = file_name.split("\\")
                file = file_split[len(file_split) - 1]
                restored_file = self.client_machine.join_path(self.tcinputs['DestinationPath'], file)
                if self.client_machine.check_file_exists(restored_file):
                    self.log.info("Restored file succesfully")
                    self.log.info("Test case executed succesfully")
                    self.log.info("Cleaning up the restored file")
                    self.client_machine.delete_file(restored_file)
                else:
                    raise Exception("The file {} does not exist".format(restored_file))
            else:
                raise Exception("The restore job failed with error: {0}".format(restore_job.delay_reason))

        except Exception as excp:
            self.log.error(str(excp))
            self.log.error("TEST CASE FAILED")
            self.status = constants.FAILED
            self.result_string = str(excp)

        finally:
            if self.client_machine:
                self.client_machine.remove_directory(Path)
                self.client_machine.remove_directory(Path2)
                self.client_machine.remove_directory(systemstate_content_path)


