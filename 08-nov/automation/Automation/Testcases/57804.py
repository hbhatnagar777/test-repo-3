# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case
This test case will verify if it is Trueup job with system state, the job will convert the SPF to Full

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper



class TestCase(CVTestCase):
    """Testcase for system state trueup"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Testcase for system state trueup"
        self.applicable_os = self.os_list.WINDOWS
        self.show_to_user = False
        self.tcinputs = {

            "StoragePolicyName":None
        }
        self.client_machine = None
        self.helper = None

    def run(self):
        """Follows the following steps:
        1. Create a new backupset & generate regular files
        2. Trigger a full system state backup.
        3. Trigger an incremental system state backup.
        4. Trigger a synthetic full system state backup.
        5. Trigger an incremental system state backup with single stream.
        6. Validate trueup ran with system state  as Full.
        7. Repeat steps 4 to 6 with incremental backup having multiple streams.
        """

        regular_content_path = "C:\\Test"



        try:
            self.helper = FSHelper(self)
            FSHelper.populate_tc_inputs(self, mandatory=False)
            self.log.info("Step 1: Creating a backupset")
            backupset_name = "Test_57804"
            self.helper.create_backupset(backupset_name, delete=False)
            self.helper.create_subclient("default", self.tcinputs['StoragePolicyName'], [regular_content_path])
            self.helper.update_subclient(storage_policy=self.tcinputs['StoragePolicyName']
                                         , allow_multiple_readers=True, data_readers=10,
                                         content=[regular_content_path])


            if self.client_machine.check_directory_exists(regular_content_path):
                self.client_machine.remove_directory(regular_content_path)
            self.client_machine.create_directory(regular_content_path)
            self.log.info("creating regular files")
            self.client_machine.generate_test_data(file_path=regular_content_path, dirs=1, file_size=100, files=5)
            self.log.info("Step 2: Run a full system state backup")
            job_full = self.helper.run_systemstate_backup(backup_type='FULL', wait_to_complete=True)
            self.log.info("Step 3 : Trigger an incremental system state job ")
            job_inc2 = self.helper.run_systemstate_backup(backup_type='Incremental', wait_to_complete=True)
            self.log.info("Step 4 : Run a synthetic full backup")
            self.helper.run_systemstate_backup(backup_type='Synthetic_full', wait_to_complete=True)
            self.helper.update_subclient(storage_policy=self.tcinputs['StoragePolicyName']
                                         , allow_multiple_readers=False, data_readers=1,
                                         filter_content=[""])
            self.log.info("Step 5 : Trigger an incremental system state job ")
            job_inc2 = self.helper.run_systemstate_backup(backup_type='Incremental', wait_to_complete=True)
            self.log.info("Checking if trueup ran or not ")
            self.log.info("validate Trueup function called.")
            retval = self.helper.validate_trueup(job_inc2[0])
            if retval:
                self.log.info("True up Ran for this %s Job or not.", job_inc2[0].job_id)
                if self.helper.get_logs_for_job_from_file(job_inc2[0].job_id, "clBackup.log",
                                                          "This is a TrueUp job, the System State backup will be running as full"):
                        self.log.info("Inc job converted full successfully for Trueup job")
                else:
                    raise Exception("Trueup Job not converted full for System state")
            else:
                raise Exception("True up did not run this job, failing the test case")
            self.log.info("Step 6 : Run another synthetic full backup")
            self.helper.run_systemstate_backup(backup_type='Synthetic_full', wait_to_complete=True)
            self.helper.update_subclient(storage_policy=self.tcinputs['StoragePolicyName']
                                         , allow_multiple_readers=True, data_readers=10)
            self.log.info("Step 7 : Trigger an incremental system state job with Multi stream")
            job_inc3 = self.helper.run_systemstate_backup(backup_type='Incremental', wait_to_complete=True)
            self.log.info("Checking if trueup ran or not ")
            self.log.info("validate Trueup function called.")
            retval = self.helper.validate_trueup(job_inc3[0])
            if retval:
                self.log.info("True up Ran for this %s Job or not.", job_inc3[0].job_id)
                if self.helper.get_logs_for_job_from_file(job_inc3[0].job_id, "clBackup.log",
                                                          "This is a TrueUp job, the System State backup will be running as full"):
                    self.log.info("Inc job converted full successfully for Trueup job")
                else:
                    raise Exception("Trueup Job not converted full for System state")
            else:
                raise Exception("True up did not run this job, failing the test case")

        except Exception as excp:
            self.log.error(str(excp))
            self.log.error("TEST CASE FAILED")
            self.status = constants.FAILED
            self.result_string = str(excp)
        finally:
            if self.client_machine:
                self.client_machine.remove_directory(regular_content_path)
