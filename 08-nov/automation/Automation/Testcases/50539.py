# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    _run_backup()   --  initiates the backup job for the specified subclient

    run()           --  run function of this test case
"""

from AutomationUtils.machine import Machine
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of File System backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of File System backup and restore"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True

    def _run_backup(self, backup_type):
        """Initiates backup job and waits for completion"""
        log = logger.get_log()
        log.info("*" * 10 + " Starting Subclient {0} Backup ".format(backup_type) + "*" * 10)
        job = self.subclient.backup(backup_type)
        log.info("Started {0} backup with Job ID: {1}".format(backup_type, str(job.job_id)))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    backup_type, job.delay_reason
                )
            )

        log.info("Successfully finished {0} backup job".format(backup_type))

        return job

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing {0} testcase".format(self.id))

            options_selector = OptionsSelector(self.commcell)

            log.info("Create Machine class object")
            client_machine = Machine(self.client.client_name, self.commcell)

            log.info("Read subclient content")
            log.info("Subclient Content: {0}".format(self.subclient.content))

            drive = options_selector.get_drive(client_machine, size=50)
            if drive is None:
                raise Exception("No free space to generate test data")
            test_data_path = drive + 'TestData'

            log.info("Add test data path to subclient content")
            self.subclient.content += [test_data_path]

            log.info("Generating test data at: {0}".format(test_data_path))
            client_machine.generate_test_data(test_data_path)

            self._run_backup('FULL')

            log.info("Generating test data at: {0}".format(test_data_path))
            client_machine.generate_test_data(test_data_path)

            self._run_backup('INCREMENTAL')

            log.info("Generating test data at: {0}".format(test_data_path))
            client_machine.generate_test_data(test_data_path)

            job = self._run_backup('DIFFERENTIAL')

            log.info("Get backed up content size")
            size = 200
            self.csdb.execute(
                'SELECT totalBackupSize FROM JMBkpStats WHERE jobID = {0}'.format(job.job_id)
            )
            size += int(self.csdb.fetch_one_row()[0]) / (1024 * 1024)
            log.info("Total Backed up size: {0}".format(size))

            windows_restore_client, windows_restore_location = \
                options_selector.get_windows_restore_client(size=size)

            log.info("*" * 10 + " Run out of place restore " + "*" * 10)

            job = self.subclient.restore_out_of_place(
                windows_restore_client.machine_name,
                windows_restore_location, self.subclient.content
            )
            log.info("Started Restore out of place with job id: " + str(job.job_id))

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error: " + job.delay_reason
                )

            log.info("Successfully finished restore out of place")

            log.info("Form windows restore location for Test data")
            windows_restore_location = windows_restore_location + "\\" + "TestData"
            log.info("Windows restore location: %s", windows_restore_location)

            log.info("Validate restored content")
            diff = []
            diff = client_machine.compare_folders(
                windows_restore_client, test_data_path, windows_restore_location
            )

            if diff != []:
                log.error(
                    "Restore Validation failed. List of different files \n{0}".format(diff)
                )
                raise Exception(
                    "Restore out of place validation failed. Please check logs for more details."
                )

            log.info("Restore out of place validation was successful")

            log.info("*" * 10 + " Run Restore in place " + "*" * 10)
            # run restore in place job
            job = self.subclient.restore_in_place([test_data_path])

            log.info("Started restore in place job with job id: " + str(job.job_id))

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore in place job with error: " + job.delay_reason
                )

            log.info("Successfully finished restore in place job")

            log.info("Validate restored content")
            diff = []
            diff = windows_restore_client.compare_folders(
                client_machine, windows_restore_location, test_data_path
            )

            if diff != []:
                log.error(
                    "Restore validation failed. List of different files \n{0}".format(diff)
                )
                raise Exception(
                    "Restore out of place validation failed. Please check logs for more details."
                )

            log.info("Restore in place validation was successful")

            # cleanup phase
            log.info("Will try to remove the test data directory")
            client_machine.remove_directory(test_data_path)
            log.info("Test Data directory removed successfully")

            log.info("Will try to remove the TestData directory from the restored content")

            # windows_restore_location stores the path for TestData directory
            # refer to line: 123
            windows_restore_client.remove_directory(windows_restore_location)

            log.info("TestData directory from the restored content removed successfully")

        except Exception as excp:
            log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
