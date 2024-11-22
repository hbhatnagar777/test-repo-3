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
from MediaAgents.MAUtils.mahelper import MMHelper


class TestCase(CVTestCase):
    """Response file pruning logic verification."""

    def __init__(self):
        """Initializing the required objects"""
        super(TestCase, self).__init__()
        self.name = "Response file pruning logic verification"
        self.applicable_os = self.os_list.WINDOWS
        self.feature = self.features_list.BMR
        self.show_to_user = False
        self.tcinputs = {
            "StoragePolicyName": None
        }
        self.client_machine = None
        self.helper = None

    def validate_data_aging(self, job_id):
        """validate if job got aged"""
        self._log.info("VALIDATION: backup job not yet aged")
        mmhelper = MMHelper(self)
        retcode = mmhelper.validate_job_prune(job_id, 2)
        if retcode:
            self._log.info("Validation success")
        else:
            raise Exception(
                "Backup job {0} is not expected to age".format(job_id)
            )

    def run(self):
        """Point in time restore for 1-touch"""
        try:
            self.helper = FSHelper(self)
            FSHelper.populate_tc_inputs(self, mandatory=False)
            self.log.info("Step 1. Create a backupset and set the storage policy")
            backupset_name = "Test_100.1"
            self.helper.create_backupset(backupset_name, delete=True)
            self.helper.create_subclient("default", self.tcinputs['StoragePolicyName'], ["C:\\Windows\\system32\\drivers\\etc"])
            self.helper.update_subclient(storage_policy=self.tcinputs['StoragePolicyName'],
                                         allow_multiple_readers=True,
                                         data_readers=10, filter_content=["{System Protected Files}"],
                                         content=["C:\\Windows\\system32\\drivers\\etc"])
            self.client_machine.create_registry("FileSystemAgent", 'bEnableSystemStateEssentialComponentFiltering', 1,
                                                reg_type='DWord')

            size = self.client_machine.execute_command(r"(Get-Partition -DriveLetter C).Size")
            reduced_size = int(size.formatted_output) - 10000000
            self.client_machine.execute_command(r'Resize-Partition -DriveLetter "C" -Size {}'.format(reduced_size))

            self.log.info("Step 2. Trigger a full system state backup.")

            job_full = self.helper.run_systemstate_backup(backup_type='Full', wait_to_complete=True)

            job_start_time = job_full[0].summary['jobStartTime']

            job_end_time = job_full[0].summary['lastUpdateTime']

            query1 = 'select created from APP_ExtendedProperties where attrType = 127 and clientId = {0} and backupSet = {1}'\
                .format(self.client.client_id, self.backupset.backupset_id)
            self._csdb.execute(query1)
            resp_file_time = self._csdb.fetch_one_row()
            if resp_file_time:
                self.log.info("The full job has created a response file")
            else:
                raise Exception("The full job hasn't created a response file.")

            self.log.info("Step 3. Run a system state incremental backup")
            job_inc = self.helper.run_systemstate_backup(backup_type='Incremental', wait_to_complete=True)

            self._csdb.execute(query1)
            rows = self._csdb.rows
            if len(rows) == 1:
                self.log.info("The incremental job hasn't created a response file")
            else:
                raise Exception("The incremental job has also created response file ")

            self.log.info("Step 4 : Run a synthetic full backup")
            self.helper.run_systemstate_backup(backup_type='Synthetic_full', wait_to_complete=True)

            self.log.info("Step 5. Run a system state incremental backup")
            self.helper.run_systemstate_backup(backup_type='Incremental', wait_to_complete=True)

            self._csdb.execute(query1)
            rows = self._csdb.rows
            if len(rows) == 1:
                self.log.info("The incremental job hasn't created a response file")
            else:
                raise Exception("The incremental job has also created response file ")

            self.log.info("Step 7 : Case where every backup creates a response file.")

            backupset_name = "Test_100.2"
            self.helper.create_backupset(backupset_name, delete=True)
            self.helper.create_subclient("default", self.tcinputs['StoragePolicyName'], ["C:\\Windows\\system32\\drivers\\etc"])
            self.helper.update_subclient(storage_policy=self.tcinputs['StoragePolicyName'],
                                         allow_multiple_readers=True,
                                         data_readers=10, filter_content=["{System Protected Files}"],
                                         content=["C:\\Windows\\system32\\drivers\\etc"])

            self.log.info("Step 8. Trigger a full system state backup.")

            job_full_2 = self.helper.run_systemstate_backup(backup_type='Full', wait_to_complete=True)
            query2 = 'select created from APP_ExtendedProperties where attrType = 127 and clientId = {0} and backupSet = {1}'\
                .format(self.client.client_id, self.backupset.backupset_id)
            self._csdb.execute(query2)
            resp_file_time = self._csdb.fetch_one_row()
            if resp_file_time:
                self.log.info("The full job has created a response file")
            else:
                raise Exception("The full job hasn't created a response file.")

            self.log.info("Creating a volume on client machine to make sure there is a hardware change")
            size = self.client_machine.execute_command(r"(Get-Partition -DriveLetter C).Size")
            reduced_size = int(size.formatted_output) - 10000000
            self.client_machine.execute_command(r'Resize-Partition -DriveLetter "C" -Size {}'.format(reduced_size))

            self.log.info("Step 9. Run a system state incremental backup")
            job_inc_1 = self.helper.run_systemstate_backup(backup_type='Incremental', wait_to_complete=True)

            job_start_time1 = job_inc_1[0].summary['jobStartTime']

            job_end_time1 = job_inc_1[0].summary['lastUpdateTime']

            self._csdb.execute(query2)
            if len(self._csdb.rows) == 2:
                self.log.info("The incremental job has created a response file")
            else:
                raise Exception("The incremental job hasn't created a response file.")

            self.log.info("Step 10 : Run a synthetic full backup")
            self.helper.run_systemstate_backup(backup_type='Synthetic_full', wait_to_complete=True)

            self.log.info("Resizing the partition back to ensure a response file change")
            available_size = self.client_machine.execute_command(
                r'Get-PartitionSupportedSize -DriveLetter "C"')
            self.client_machine.execute_command(
                r'Resize-Partition -DriveLetter "C" -Size {}'.format(
                    available_size.formatted_output[0][1]))

            self.log.info("Step 11. Run a system state incremental backup")
            job_inc2 = self.helper.run_systemstate_backup(backup_type='Incremental', wait_to_complete=True)

            job_start_time2 = job_inc2[0].summary['jobStartTime']

            job_end_time2 = job_inc2[0].summary['lastUpdateTime']

            time.sleep(3600)

            self.log.info("Step 12 : Run data aging")

            da_job = self.commcell.run_data_aging('Primary', self.tcinputs['StoragePolicyName'])
            self._log.info("data aging job: " + str(da_job.job_id))
            if not da_job.wait_for_completion():
                raise Exception(
                    "Failed to run data aging with error: {0}".format(da_job.delay_reason)
                )
            self._log.info("Data aging job completed.")

            self.log.info("Validation for first case")

            self.validate_data_aging(job_full[0].job_id)

            self.validate_data_aging(job_inc[0].job_id)

            time.sleep(60)

            self._csdb.execute(query1)
            resp_file_time = self._csdb.fetch_one_row()
            rows = self._csdb.rows
            if not len(rows) > 1:
                if job_start_time <= int(resp_file_time[0]) <= job_end_time:
                    self.log.info("The correct response file is retained")

            else:
                raise Exception("The data aging hasn't pruned the response files correctly.")

            self.log.info("Validation for Second case")

            self.validate_data_aging(job_full_2[0].job_id)

            self.validate_data_aging(job_inc_1[0].job_id)

            time.sleep(60)

            self._csdb.execute(query2)
            rows = self._csdb.rows
            if len(rows) == 2:
                if job_start_time1 <= int(rows[0][0]) <= job_end_time1 and job_start_time2 <= int(rows[1][0]) <= job_end_time2:
                    self.log.info("The correct response file is retained")

            else:
                raise Exception("The data aging hasn't pruned the response files correctly.")

        except Exception as excp:
            self.log.error(str(excp))
            self.log.error("TEST CASE FAILED")
            self.status = constants.FAILED
            self.result_string = str(excp)

        finally:
            available_size = self.client_machine.execute_command(
                r'Get-PartitionSupportedSize -DriveLetter "C"')

            self.client_machine.execute_command(
                r'Resize-Partition -DriveLetter "C" -Size {}'.format(
                    available_size.formatted_output[0][1]))

            self.client_machine.remove_registry("FileSystemAgent",
                                                'bEnableSystemStateEssentialComponentFiltering')
