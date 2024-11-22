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
        self.name = "System State Commit:Multiple cycles and subclient restores"
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
        4. Install the readfileservice
        5. Populate regular and system state data
        6. Running an incremental system state backup
        7. Commit the system state job when SPF is being backed up
        8. Run an incremental system state backup
        9. Run a synthetic full backup
        10. Populate regular and system state data
        11. Get the current time to be used for comparison with toTime sent during restore
        12. Trigger an incremental system state job
        13. Commit the system state job when SPF is being backed up
        14. Restoring the read file service exe that was backed up as a part of the succesfull
        incremental backup.
        15. verifying if the file is getting restored and also if from the right time.
        16. Restoring the regular file from subclient level and verifying it.
        """

        regular_content_path = "C:\\Test"
        systemstate_content_path = "C:\\windows\\assembly\\test"
        regular_content_path2 = "C:\\Test1"
        systemstate_content_path2 = "C:\\windows\\assembly\\test1"

        try:
            self.helper = FSHelper(self)
            FSHelper.populate_tc_inputs(self, mandatory=False)
            self.log.info("Step 1: Creating a backupset")
            backupset_name = "Test_54183"
            self.helper.create_backupset(backupset_name, delete=False)
            self.helper.create_subclient("default", self.tcinputs['StoragePolicyName'], ["\\"])
            self.helper.update_subclient(storage_policy=self.tcinputs['StoragePolicyName']
                                         , allow_multiple_readers=True, data_readers=10)

            self.log.info("Step 2: Run a full system state backup")
            job_full = self.helper.run_systemstate_backup(backup_type='FULL', wait_to_complete=True)

            self.log.info("Step 3: Copy the service files from network path to client machine")
            self.client_machine.copy_from_network_share(self.tcinputs['NetworkSharePath'], "C:\\",
                                                        self.tcinputs['ShareUsername'], self.tcinputs['SharePassword'],
                                                        use_xcopy= True)

            self.log.info("Step 4: Install the readfileservice")
            output = self.client_machine.execute_command(r"C:\dummyservice\readfilesservice.bat")
            time.sleep(60)
            reg_val = self.client_machine.get_registry_value(
                win_key=r'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\readfilesService', value='DisplayName'
            )
            if reg_val == "readfilesService":
                self.log.info("Readfile service installed succesfully")
            else:
                raise Exception("Error while installing Readfile service")

            self.log.info("Step 5: Populate regular and system state data")
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

            self.log.info("Step 6 : Trigger an incremental system state job ")
            job_inc2 = self.helper.run_systemstate_backup(backup_type='Incremental', wait_to_complete=False)

            self.log.info("Step 7 : Commit the system state job when SPF is being backed up")
            while True:
                if self.helper.get_logs_for_job_from_file(job_inc2[0].job_id, "clBackup.log", "Backup SystemProtectedFile component"):
                    self.helper.commit_job(job_inc2[0], 1, CommitCondition.SECONDS)
                    break

            self.log.info("Step 8: Run an incremental system state backup")
            self.helper.run_systemstate_backup(backup_type='Incremental', wait_to_complete=True)

            self.log.info("Step 9 : Run a synthetic full backup")
            self.helper.run_systemstate_backup(backup_type='Synthetic_full', wait_to_complete=True)

            self.log.info("Step 10: Populate regular and system state data")

            if self.client_machine.check_directory_exists(regular_content_path2):
                self.client_machine.remove_directory(regular_content_path2)
            self.client_machine.create_directory(regular_content_path2)
            self.helper.generate_testdata([".txt"], path=regular_content_path2)

            if self.client_machine.check_directory_exists(systemstate_content_path2):
                self.client_machine.remove_directory(systemstate_content_path2)
            self.client_machine.create_directory(systemstate_content_path2)
            self.log.info("creating system files")
            self.client_machine.generate_test_data(file_path=systemstate_content_path2, dirs=2, file_size=100000, files=5)

            self.log.info("Step 11 : Get the current time to be used for comparison with toTime sent during restore")
            current_time = str(int(time.time()))
            self.log.info("current time is %s", current_time)

            self.log.info("Step 12 : Trigger an incremental system state job ")
            job_inc2 = self.helper.run_systemstate_backup(backup_type='Incremental', wait_to_complete=False)

            self.log.info("Step 13 : Commit the system state job when SPF is being backed up")
            while True:
                if self.helper.get_logs_for_job_from_file(job_inc2[0].job_id, "clBackup.log", "Backup SystemProtectedFile component"):
                    self.helper.commit_job(job_inc2[0], 1, CommitCondition.SECONDS)
                    break

            self.log.info("Step 14 : Restoring the system file")
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
                raise Exception("The restore job failed with error: {0}".format(restore_job.delay_reason))

            self.log.info("Step 16: Restoring the regular file from subclient level")
            restore_job_reg = self.subclient.restore_out_of_place(self.client,
                                                                  paths=[r'C:\Test1\1.txt']
                                                                  , destination_path=self.tcinputs['DestinationPath'])

            if restore_job_reg.wait_for_completion():
                file = '1.txt'
                restored_file = self.client_machine.join_path(self.tcinputs['DestinationPath'], file)
                if self.client_machine.check_file_exists(restored_file):
                    self.log.info("Restored file succesfully")
                    self.log.info("Step 17 : Comparing the current time with toTime")
                    result = self.helper.get_logs_for_job_from_file(restore_job_reg.job_id, "clRestore.log", "toTime=")
                    to_time = result.split(r'toTime=\"')[1].split(r'\"')[0]
                    self.log.info("The to time is %s", to_time)
                    if to_time > current_time:
                        self.log.info("Test case executed succesfully")
                    else:
                        raise Exception("The right job is not being picked for restore.")
                    self.log.info("Cleaning up the restored file")
                    self.client_machine.delete_file(restored_file)
                else:
                    raise Exception("The file was not restored to the destination.")

            else:
                raise Exception("The restore job failed with error: {0}".format(restore_job_reg.delay_reason))

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
                self.client_machine.remove_directory(regular_content_path2)
                self.client_machine.remove_directory(systemstate_content_path2)
                self.client_machine.delete_file(
                    self.tcinputs['DestinationPath'] + "\\readfilesservice.exe")
