# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

It does the following:
Step 1. Create a backupset and set the storage policy
Step 2. Copy the dummy service files from the specified network share to the client machine
Step 3. Install the readfiles service by executing the batch script for installation.
Step 4. Trigger a full system state backup.
Step 5. After the backup is complete wait for 2 mins and get the time to be passed for the restore
Step 6. Uninstall the readfile service
Step 7. Run a system state incremental backup
Step 8. Perform an out of place point in time restore of the service file backed up with system state
Step 9. Verify the file gets restored and set the status of the testcase accordingly.

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

"""
import datetime
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Point in time restore for 1-touch."""

    def __init__(self):
        """Initializing the required objects"""
        super(TestCase, self).__init__()
        self.name = "1-touch offline Interactive - Point in Time Restore"
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
        """Point in time restore for 1-touch"""
        try:
            self.helper = FSHelper(self)
            FSHelper.populate_tc_inputs(self, mandatory=False)
            self.log.info("Step 1. Create a backupset and set the storage policy")
            backupset_name = "Test_43609"
            self.helper.create_backupset(backupset_name, delete=True)
            self.helper.create_subclient("default", self.tcinputs['StoragePolicyName'], ["C:\\dummyservice"])
            self.helper.update_subclient(storage_policy=self.tcinputs['StoragePolicyName'], content=["C:\\dummyservice"])

            self.log.info("Step 2. Copy the dummy service files from the specified network share to the client machine")

            self.client_machine.copy_from_network_share(self.tcinputs['NetworkSharePath'], "C:\\",
                                                        self.tcinputs['ShareUsername'], self.tcinputs['SharePassword'],
                                                        use_xcopy= True)
            self.log.info("Step 3.Install the readfiles service by executing the batch script for installation")
            output = self.client_machine.execute_command(r"C:\dummyservice\readfilesservice.bat")
            time.sleep(60)
            reg_val = self.client_machine.get_registry_value(
                    win_key=r'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\readfilesService', value='DisplayName'
                )
            if reg_val == "readfilesService":
                self.log.info("Readfile service installed succesfully")
            else:
                raise Exception("Error while installing Readfile service")

            self.log.info("Step 4. Trigger a full system state backup.")

            self.helper.run_systemstate_backup(backup_type='Full', wait_to_complete=True)
            self.log.info("Step 5. After the backup is complete get the time to be passed for the restore")
            time.sleep(120)

            current_time = datetime.datetime.utcnow()

            restore_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

            self.log.info("The to time set is %s", restore_time)

            self.log.info("Step 6. Uninstall the readfile service")

            self.client_machine.execute_command(r"C:\dummyservice\readfilesservice_uninstall.bat")

            self.log.info("Step 7. Run a system state incremental backup")
            self.helper.run_systemstate_backup(backup_type='Incremental', wait_to_complete=True)

            self.log.info("Step 8.Will restore the dummy service now")
            restore_job = self.backupset.restore_out_of_place(
                self.client,
                paths=[r'\[System State]\Components\System Protected Files\c\dummyservice\readfilesservice.exe'],
                destination_path=self.tcinputs['DestinationPath'], to_time=restore_time)

            self.log.info("Step 9. Verify the file gets restored and set the status of the testcase accordingly.")
            if restore_job.wait_for_completion():
                if self.client_machine.check_file_exists(self.tcinputs['DestinationPath'] +"\\readfilesservice.exe"):
                    self.log.info("Restored file succesfully")
                    self.log.info("Test case executed succesfully")

            else:
                raise Exception("The restore job failed with error: {0}".format(restore_job.delay_reason))

        except Exception as excp:
            self.log.error(str(excp))
            self.log.error("TEST CASE FAILED")
            self.status = constants.FAILED
            self.result_string = str(excp)

        finally:
            if self.client_machine:
                self.log.info("Uninstalling the readfile service")
                self.client_machine.execute_command(r"C:\dummyservice\readfilesservice_uninstall.bat")
                self.log.info("Cleaning up the restored file")
                self.client_machine.delete_file(self.tcinputs['DestinationPath'] +"\\readfilesservice.exe")
                self.log.info("Cleaning up the service files")
                self.client_machine.remove_directory("C:\\dummyservice")
