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
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Online system state restore."""

    def __init__(self):
        """Initializing the required objects"""
        super(TestCase, self).__init__()
        self.name = "Online system state restore"
        self.applicable_os = self.os_list.WINDOWS
        self.tcinputs = {
            "NetworkSharePath": None,
            "ShareUsername": None,
            "SharePassword": None,
            "StoragePolicyName": None
        }
        self.client_machine = None
        self.helper = None

    def run(self):
        """Online system state restore"""
        try:
            self.helper = FSHelper(self)
            FSHelper.populate_tc_inputs(self, mandatory=False)
            self.log.info("Step 1. Create a backupset and set the storage policy")
            backupset_name = "Test_29678"
            self.helper.create_backupset(backupset_name, delete=False)
            self.helper.create_subclient("default", self.tcinputs['StoragePolicyName'], ["\\"])
            self.helper.update_subclient(storage_policy=self.tcinputs['StoragePolicyName'])

            self.log.info("Step 2. Copy the dummy service files from the specified network share to the client machine")

            self.client_machine.copy_from_network_share(self.tcinputs['NetworkSharePath'], "C:\\",
                                                        self.tcinputs['ShareUsername'], self.tcinputs['SharePassword'])
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

            self.log.info("Step 5. Uninstall the readfile service")
            self.client_machine.execute_command(r"C:\dummyservice\readfilesservice_uninstall.bat")

            self.log.info("Step 6. Will do a full system restore")
            restore_job = self.backupset.restore_in_place(
                paths=['\\', r'\[System State]\Components\Registry', r'\[System State BCD]'])

            if restore_job.wait_for_completion():
                self.log.info("Step 6. Will reboot the client")
                self.client_machine.reboot_client()
                time.sleep(600)
                self.log.info("Step 7. Check if the service has been restored")
                attempts = 0
                while attempts != 5:
                    try:
                        service_name = self.client_machine.get_registry_value(
                            win_key=r'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\readfilesService',
                            value='DisplayName')
                        if service_name == 'readfilesService':
                            self.log.info("Test case executed succesfully")
                            break

                        raise Exception("The restore wasn't successfull")

                    except Exception as excp:
                        time.sleep(300)
                        attempts = attempts + 1
                        if attempts > 5:
                            raise Exception(excp)

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
                self.log.info("Cleaning up the service files")
                self.client_machine.remove_directory("C:\\dummyservice")
