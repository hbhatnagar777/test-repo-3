# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Testcase to validate Playback with multiple backup streams

TestCase:
    __init__()                       --  Initializes the TestCase class

    setup()                          --  All testcase objects are initializes in this method

    run()                            --  Contains the core testcase logic and it is the one executed

    tear_down()                      --  Cleans the data created for Indexing validation
"""

import traceback
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from Server.JobManager.jobmanager_helper import JobManager
from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):

    """Verify Playback with multiple backup streams"""

    def __init__(self):
        """Initializes the TestCase class"""
        super(TestCase, self).__init__()
        self.name = "Indexing - Playback with multiple backup streams"
        self.tcinputs = {
            'SubclientContent': None,
            'StoragePolicy': None,
            'DestinationPath': None
        }

        self.subclient_content = None
        self.restore_destination_path = None
        self.storage_policy = None
        self.index_class_obj = None
        self.cl_machine = None
        self.indexingtestcase = None
        self.backupset_obj = None
        self.subclient_obj = None
        self.common_utils_obj = None

    def setup(self):
        """All testcase objects are initializes in this method"""
        try:

            self.cl_machine = Machine(self.client)

            # subclient content
            self.subclient_content = [self.tcinputs.get('SubclientContent')]
            self.restore_destination_path = self.tcinputs.get('DestinationPath')
            self.storage_policy = self.tcinputs.get('StoragePolicy')

            # Index Cache details
            self.index_class_obj = IndexingHelpers(self.commcell)
            self.indexingtestcase = IndexingTestcase(self)

            self.log.info("Creating backupset and subclient..")
            self.backupset_obj = self.indexingtestcase.create_backupset(
                name='backupset_multiple_streams',
                for_validation=False)

            self.subclient_obj = self.indexingtestcase.create_subclient(
                name="sc1",
                backupset_obj=self.backupset_obj,
                storage_policy=self.storage_policy,
                content=self.subclient_content,
                register_idx=False)

            self.common_utils_obj = CommonUtils(self)
            self.subclient_obj.allow_multiple_readers = True
            self.subclient_obj.data_readers = 50

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed

        Steps:
            1 - Run full backup job 50 streams wait for its completion
            2 - Run Incremental backup 50 streams wait for its completion
            3 - Run single stream synthetic full backup job and wait for its completion
            4 - Run out of place restore from the synthetic full job and verify data restored
            5 - At the end of the testcase, delete the data restored from synthetic full
                as part of cleanup

        """

        try:
            # Starting the testcase
            self.log.info("Started executing {0} testcase ".format(self.id))

            self.log.info('************* Running backup jobs *************')
            # Starting full backup and not waiting for that
            full_job_obj = self.common_utils_obj.subclient_backup(
                self.subclient_obj, backup_type="Full", wait=False)
            jmobject_full = JobManager(full_job_obj)

            jmobject_full.wait_for_state(
                expected_state="completed", retry_interval=480, time_limit=9000)

            # Generating test data before starting incremental backup job
            new_path = f"{str(self.subclient_content[0])}{self.cl_machine.os_sep}Folder100"
            self.log.info(" new_path is: {0} \n ".format(new_path))
            self.log.info("Generating test data...")
            self.cl_machine.generate_test_data(
                new_path, dirs=10, files=10, file_size=1024,
                hlinks=False, slinks=False, hslinks=False, sparse=False)

            # Starting Incremental backup and waiting for that
            incr_job = self.common_utils_obj.subclient_backup(
                self.subclient_obj, backup_type="Incremental", wait=False)
            incr_job_obj = JobManager(incr_job)
            incr_job_obj.wait_for_state(
                expected_state="completed", retry_interval=420, time_limit=3000)

            # Starting synthetic full backup job and not waiting for that
            single_stream_sfull = self.common_utils_obj.subclient_backup(
                self.subclient_obj, backup_type="Synthetic_full", wait=False)
            jmobject_ss_sfull = JobManager(single_stream_sfull)
            self.log.info("Started single stream synthetic full backup..")

            self.log.info("Waiting for completion of single stream synthetic full job")
            jmobject_ss_sfull.wait_for_state(
                expected_state="completed", retry_interval=300, time_limit=300)
            self.log.info("single stream synthetic full job completed successfully")

            self.log.info("Starting out of place restore job, But not waiting for that..")
            sfull_restore_job_obj = self.common_utils_obj.subclient_restore_out_of_place(
                destination_path=self.restore_destination_path,
                paths=self.subclient_content,
                client=self.client.client_name,
                subclient=self.subclient_obj,
                wait=False)
            self.log.info("Started out of place restore job..")
            jmobject_sfull_restore = JobManager(sfull_restore_job_obj)
            self.log.info("Waiting for the completion of restore job..")
            jmobject_sfull_restore.wait_for_state(
                expected_state="completed",
                retry_interval=480,
                time_limit=9000)
            self.log.info("restore job completed successfully..")

            # Checking folder size of the subclient content and destination path in MBs..
            sc_content_size = self.cl_machine.get_folder_size(
                str(self.subclient_content[0]), in_bytes=False)
            self.log.info("Folder size of subclient content: {0} MBs".format(sc_content_size))
            restored_data_size = self.cl_machine.get_folder_size(
                self.restore_destination_path, in_bytes=False)
            self.log.info("Folder size of the destination path: {0} MBs".format(restored_data_size))

            if sc_content_size == restored_data_size:
                self.log.info(" All the data has been restored as expected..")
            else:
                self.log.info(" All the data has not been restored..Please check it out..")
                raise Exception('Size does not match with source '
                                'after restoring the data from SFULL job')

        except Exception as exp:
            self.log.error("Test case failed with error: {0}".format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Cleans the data created for Indexing validation"""
        try:
            # Removing destination directory at the end of the testcase
            self.log.info("Removing destination directory at the end of the testcase..")
            removedir_retcode = self.cl_machine.remove_directory(
                directory_name=self.restore_destination_path,
                days=0
            )
            if removedir_retcode:
                self.log.info("Directory removed successfully..")
            else:
                self.log.info("Issue while trying to remove directory..")

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)
