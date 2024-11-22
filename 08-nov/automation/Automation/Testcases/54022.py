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
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper, CommitCondition


class TestCase(CVTestCase):
    """Testcase for system state commit"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "System State Commit"
        self.applicable_os = self.os_list.WINDOWS
        self.show_to_user = False
        self.tcinputs = {
            "NetworkSharePath": None,
            "ShareUsername": None,
            "SharePassword": None,
            "DestinationPath": None,
            "StoragePolicyName": None
        }
        self.client_machine = None
        self.helper = None

    def run(self):
        """Follows the following steps
        1. Create a new backupset
        2. Running a full system state backup
        3. Copy the dummy services files from the network path to the client machine
        4. Running an incremental system state backup
        5. Running an incremental system state backup and committing it when system state
        content is being backed up.
        6. Restoring the read file service exe that was backed up as a part of the succesfull
        incremental backup.
        7. verifying if the file is getting restored and also if from the right time.
        """

        regular_content_path = "C:\\Test"
        systemstate_content_path = "C:\\windows\\assembly\\test"

        try:
            self.helper = FSHelper(self)
            FSHelper.populate_tc_inputs(self, mandatory=False)
            self.log.info("Step 1: Creating a backupset")
            backupset_name = "Test_54022"
            self.helper.create_backupset(backupset_name, delete=False)
            self.helper.create_subclient("default", self.tcinputs['StoragePolicyName'], ["\\"])
            self.helper.update_subclient(storage_policy=self.tcinputs['StoragePolicyName']
                                         , allow_multiple_readers=True, data_readers=10)

            self.log.info("Step 2: Run a full system state backup")
            job_full = self.helper.run_systemstate_backup(backup_type='FULL', wait_to_complete=False)

            self.log.info("Step 3: Get the snapshot ID for that job")
            snapshot_id = self.helper.get_snapshot_id(job_full[0])
            job_full[0].wait_for_completion()
            time.sleep(60)

            self.log.info("Step 4: Check if the snapshot is deleted")
            self.helper.is_snapshot_deleted(snapshot_id)

            self.log.info("Step 5: Copy the service files from network path to client machine")
            self.client_machine.copy_from_network_share(self.tcinputs['NetworkSharePath'], "C:\\dummyservice",
                                                        self.tcinputs['ShareUsername'], self.tcinputs['SharePassword'])

            self.log.info("Step 6: Install the readfileservice")
            output = self.client_machine.execute_command(r"C:\dummyservice\readfilesservice.bat")
            if output.exit_code != 0:
                raise Exception("Error while installing Readfile service")
            else:
                self.log.info("Readfile service installed succesfully")

            self.log.info("Step 7: Run an incremental system state backup")
            self.helper.run_systemstate_backup(backup_type='Incremental', wait_to_complete=True)

            self.log.info("Step 8: Populate regular and system state data")

            if self.client_machine.check_directory_exists(regular_content_path):
                self.client_machine.remove_directory(regular_content_path)
            self.client_machine.create_directory(regular_content_path)
            self.log.info("creating regular files")
            self.client_machine.generate_test_data(file_path=regular_content_path, dirs=1, file_size=100, files=5)

            if self.client_machine.check_directory_exists(systemstate_content_path):
                self.client_machine.remove_directory(systemstate_content_path)
            self.client_machine.create_directory(systemstate_content_path)
            self.log.info("creating system files")
            self.client_machine.generate_test_data(file_path=systemstate_content_path, dirs=2, file_size=100000, files=5)

            self.log.info("Step 9 : Get the current time to be used for comparison with toTime sent during restore")
            current_time = str(int(time.time()))
            self.log.info("current time is %s", current_time)

            self.log.info("Step 10 : Trigger an incremental system state job ")
            job_inc2 = self.helper.run_systemstate_backup(backup_type='Incremental', wait_to_complete=False)

            self.log.info("Step 11 : Get the snapshot ID for the committed job")
            snapshot_id = self.helper.get_snapshot_id(job_inc2[0])

            self.log.info("Step 12 : Commit the system state job when SPF is being backed up")
            while True:
                if self.helper.get_logs_for_job_from_file(job_inc2[0].job_id, "clBackup.log", "Backup SystemProtectedFile component"):
                    self.helper.commit_job(job_inc2[0], 1, CommitCondition.SECONDS)
                    break

            time.sleep(60)
            self.log.info("Step 13: Check if the snapshot is deleted")
            self.helper.is_snapshot_deleted(snapshot_id)

            self.log.info("Step 14 : Restoring the file")
            self.log.info("Restoring the service exe file")
            restore_job = self.backupset.restore_out_of_place(self.client,
                                                              paths=[r'\[System State]\Components\System Protected Files\c\dummyservice\readfilesservice.exe'],
                                                              destination_path=self.tcinputs['DestinationPath'])

            if restore_job.wait_for_completion():

                if self.client_machine.check_file_exists(self.tcinputs['DestinationPath'] +"\\readfilesservice.exe"):
                    self.log.info("Restored file succesfully")
                    self.log.info("Step 15 : Comparing the current time with toTime")
                    result = self.helper.get_logs_for_job_from_file(restore_job.job_id, "clRestore.log", "toTime=")
                    to_time = result.split(r'toTime=\"')[1].split(r'\"')[0]
                    self.log.info("The to time is %s", to_time)
                    if to_time < current_time:
                        self.log.info("Test case executed succesfully")
                    else:
                        raise Exception("The right job is not being picked for restore.")

                else:
                    raise Exception("The file was not restored to the destination.")

            else:
                raise Exception(
                    "The restore job failed with error: {0}".format(restore_job.delay_reason))

        except Exception as excp:
            self.log.error(str(excp))
            self.log.error("TEST CASE FAILED")
            self.status = constants.FAILED
            self.result_string = str(excp)

        finally:
            if self.client_machine:
                self.log.info("Uninstalling the readfile service")
                self.client_machine.execute_command(r"C:\dummyservice\readfilesservice_uninstall.bat")
                self.client_machine.remove_directory("C:\\dummyservice")
                self.log.info("Cleaning up the restored file")
                self.client_machine.remove_directory(regular_content_path)
                self.client_machine.remove_directory(systemstate_content_path)
                self.client_machine.delete_file(
                    self.tcinputs['DestinationPath'] + "\\readfilesservice.exe")
