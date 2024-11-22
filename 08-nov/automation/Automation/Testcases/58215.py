# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Testcase to validate negative test scenarios for multi stream synthetic full

TestCase:
    __init__()                       --  Initializes the TestCase class

    setup()                          --  All testcase objects are initializes in this method

    backupjob_transferred_files()    --  Waits for the number of files to be backed up

    run()                            --  Contains the core testcase logic and it is the one executed

    tear_down()                      --  Cleans the data created for Indexing validation
"""

import traceback
from time import sleep
from AutomationUtils.machine import Machine
from AutomationUtils.cvanomaly_management import CVAnomalyManagement
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from Server.JobManager.jobmanager_helper import JobManager
from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):

    """Verify negative test scenarios for multi stream synthetic full"""

    def __init__(self):
        """Initializes the TestCase class"""
        super(TestCase, self).__init__()
        self.name = "Indexing - Multi stream synthetic full - Negative cases"
        self.tcinputs = {
            'SubclientContent': None,
            'StoragePolicy': None,
            'MediaagentName': None,
            'DestinationPath': None
        }

        self.cs_machine_obj = None
        self.media_agent_name = None
        self.mediaagent_object = None
        self.indexing_anomaly = None
        self.subclient_content = None
        self.restore_destination_path = None
        self.storage_policy = None
        self.index_class_obj = None
        self.index_cache = None
        self.cl_machine = None
        self.indexingtestcase = None
        self.backupset_obj = None
        self.subclient_obj = None
        self.common_utils_obj = None

    def setup(self):
        """All testcase objects are initializes in this method"""
        try:
            self.cs_machine_obj = Machine(self.commcell.clients.get(self.commcell.commserv_name))
            self.media_agent_name = self.tcinputs.get('MediaagentName')
            self.mediaagent_object = Machine(self.commcell.clients.get(self.media_agent_name))
            self.cl_machine = Machine(self.client)
            self.indexing_anomaly = CVAnomalyManagement().get_anomaly_handler(
                'indexing', commcell_object=self.commcell, machine=self.mediaagent_object,
                client_name=self.media_agent_name)

            # subclient content
            self.subclient_content = [self.tcinputs.get('SubclientContent')]
            self.restore_destination_path = self.tcinputs.get('DestinationPath')
            self.storage_policy = self.tcinputs.get('StoragePolicy')

            # Index Cache details
            self.index_class_obj = IndexingHelpers(self.commcell)
            self.index_cache = self.index_class_obj.get_index_cache(
                self.commcell.clients.get(self.media_agent_name))
            self.log.info(" Index cache is : {0} \n ".format(self.index_cache))
            self.indexingtestcase = IndexingTestcase(self)

            self.log.info("Creating backupset and subclient..")
            self.backupset_obj = self.indexingtestcase.create_backupset(name='neagtive_test_ms_sfull',
                                                                        for_validation=False)

            self.subclient_obj = self.indexingtestcase.create_subclient(
                name="sc1",
                backupset_obj=self.backupset_obj,
                storage_policy=self.storage_policy,
                content=self.subclient_content,
                register_idx=False)

            self.common_utils_obj = CommonUtils(self)
            self.subclient_obj.allow_multiple_readers = True
            self.subclient_obj.data_readers = 20

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)

    def backupjob_transferred_files(self, job_obj, min_files=0, wait_time=60):
        """Checks for the number of files transferred during backup job
        Args:
            job_obj     (obj)  --  job object
            min_files   (int)  --  minimum number of files to be transferred
            wait_time   (int)  -- Wait time before trying a new attempt to check
                                  the number of files transferred

        Returns:
            Nothing

        Raises:
            Exception:
                if failed to check the number of files transferred during a backup job
        """
        try:
            attempts = 100
            while True:
                self.log.info("Files transferred: {0}".format(job_obj.num_of_files_transferred))
                if job_obj.num_of_files_transferred > min_files:
                    break
                else:
                    attempts = attempts - 1
                    self.log.info("Attempts made: {0} ".format(100 - attempts))
                    self.log.info("Attempts Remaining: {0} ".format(attempts))
                    sleep(wait_time)
                    if attempts == 0:
                        raise Exception('attemtps edxhausted')
        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed

        Steps:
            1 - Run full backup job
            2 - Run Incremental backup
            3 - Start multi stream synthetic full backup job
            4 - Wait for the job to backup a few files and then suspend and resume
            5 - Kill cvd on media agent, wait for the job to go to pending state and then resume it
            6 - Restart media agent services, wait for the job to go to pending state
                and then resume it
            7 - Delete restore vector, wait for the job to go to pending state and then resume it
            8 - Kill StartSynthfull on CS, Kill log manager and index server on media agent
            9 - Kill CVSynthFullODS on media agent, wait for the job to go to pending state
                and then resume it
           10 - Kill CVJobReplicatorODS on media agent, wait for the job to go to pending state
                and then resume it
           11 - Wait for the job to reach Archive Index phase and then kill log manager
                on media agent
           12 - Wait for the job to reach pending state and then resume it.
                Wait for its completion
           13 - Run out of place restore from the synthetic full job and verify data restored
           14 - At the end of the testcase, delete the data restored from synthetic full
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
                expected_state="completed", retry_interval=300, time_limit=9000)

            # Generating test data before starting incremental backup job
            new_path = f"{str(self.subclient_content[0])}{self.cl_machine.os_sep}Folder100"
            self.log.info(" new_path is: {0} \n ".format(new_path))
            self.log.info("Generating test data...")
            self.cl_machine.generate_test_data(
                new_path, dirs=10, files=10, file_size=1024,
                hlinks=False, slinks=False, hslinks=False, sparse=False)

            # Starting Incremental backup and waiting for that
            self.common_utils_obj.subclient_backup(
                self.subclient_obj, backup_type="Incremental", wait=True)

            # Starting multi stream synthetic full backup job and not waiting for that
            multi_stream_sfull = self.common_utils_obj.subclient_backup(
                self.subclient_obj,
                backup_type="Synthetic_full",
                wait=False,
                advanced_options={
                    'use_multi_stream': True,
                    'use_maximum_streams': False,
                    'max_number_of_streams': 2
                }
            )
            jmobject_ms_sfull = JobManager(multi_stream_sfull)
            self.log.info("Started multi stream synthetic full backup "
                          "and now performing test scenarios..")

            jmobject_ms_sfull.wait_for_phase(
                'Synthetic Full Backup', total_attempts=9000, check_frequency=10)
            jmobject_ms_sfull.wait_for_state(
                expected_state="running", retry_interval=10, time_limit=3000)
            self.log.info("multi stream synthetic full reached Synthetic "
                          "full backup phase and is in running state")

            # Waiting for the multi stream synthetic full job to backup minimum a few items
            self.backupjob_transferred_files(multi_stream_sfull, min_files=0, wait_time=60)
            self.log.info("Started multi stream synthetic full is in "
                          "running state and started backing up items..")

            # Suspend and resume
            self.log.info("Suspending the syntheticfull job...")
            multi_stream_sfull.pause()
            jmobject_ms_sfull.wait_for_state(
                expected_state="suspended", retry_interval=10, time_limit=3000)
            self.log.info(" Suspended the syntheticfull job successfully...")
            self.log.info("sleeping for  1 min before resuming the backup job")
            sleep(60)

            self.log.info("Resuming the syntheticfull job...")
            multi_stream_sfull.resume()
            jmobject_ms_sfull.wait_for_state(
                expected_state="running", retry_interval=10, time_limit=3000)
            self.log.info("Job resumed successfully..")
            self.log.info("sleeping for 1 min after resuming the backup job")
            sleep(60)

            # Killing cvd on Media agent
            try:
                self.log.info("Killing CVD process on Mediaagent..")
                self.indexing_anomaly.kill_cvd()
            except Exception as killcvd:
                self.log.info("Entered exception block..{0} ".format(killcvd))

            self.log.info("Killing CVD process on mediaagent is successfull..")
            self.log.info("Sleeping for 3 minutes after killing cvd on media agent..")
            sleep(180)

            self.log.info("Waiting for the job to go to pending..")
            jmobject_ms_sfull.wait_for_state(expected_state="pending", retry_interval=240,
                                             time_limit=3000)
            self.log.info("Job went to pending state successfully..")

            self.log.info("Resuming the syntheticfull job...")
            multi_stream_sfull.resume()
            jmobject_ms_sfull.wait_for_phase('Synthetic Full Backup', total_attempts=9000,
                                             check_frequency=5)
            jmobject_ms_sfull.wait_for_state(expected_state="running", retry_interval=10,
                                             time_limit=3000)
            self.log.info("Job resumed successfully..")

            self.log.info("sleeping for 60  secs after resuming the backup job")
            sleep(60)

            # Restarting the services on media agent
            self.log.info("Restarting media agent..")
            self.indexing_anomaly.restart_cv_services()
            self.log.info("Sleeping for 5 minutes before performing any other activity..")
            sleep(300)
            self.log.info("Waiting for the job to go to pending..")
            jmobject_ms_sfull.wait_for_state(expected_state="pending", retry_interval=240,
                                             time_limit=3000)
            self.log.info("Job went to pending state successfully..")
            self.log.info("Resuming the syntheticfull job...")
            multi_stream_sfull.resume()
            jmobject_ms_sfull.wait_for_phase(
                'Synthetic Full Backup', total_attempts=9000, check_frequency=5)
            jmobject_ms_sfull.wait_for_state(
                expected_state="running", retry_interval=10, time_limit=3000)
            self.log.info("Job resumed successfully..")
            self.log.info("sleeping for 30 secs after resuming the backup job")
            sleep(30)

            # Deleting restore vector
            self.log.info(" Suspending the syntheticfull job...")
            multi_stream_sfull.pause()
            jmobject_ms_sfull.wait_for_phase(
                'Synthetic Full Backup', total_attempts=9000, check_frequency=5)
            jmobject_ms_sfull.wait_for_state(
                expected_state="suspended", retry_interval=10, time_limit=3000)
            self.log.info(" Suspended the syntheticfull job successfully...")
            self.log.info("sleeping for 60 secs before doing any other activity")
            sleep(60)
            self.log.info("Killing CVODS on Media Agent..")
            self.indexing_anomaly.kill_index_server()
            self.log.info("Deleting restore vector from index cache..")
            self.indexing_anomaly.delete_cvidxdb_temp()
            self.log.info(" Sleeping for 1 mins after removing temp directory..")
            sleep(60)
            self.log.info("restore vector deleted successfully from index cache..")

            self.log.info("Resuming the syntheticfull job...")
            multi_stream_sfull.resume()
            jmobject_ms_sfull.wait_for_phase(
                'Synthetic Full Backup', total_attempts=9000, check_frequency=5)
            jmobject_ms_sfull.wait_for_state(
                expected_state="running", retry_interval=10, time_limit=3000)
            self.log.info("Job resumed successfully..")

            # Waiting for the multi stream synthetic full job to backup minimum a few items
            self.backupjob_transferred_files(multi_stream_sfull, min_files=0, wait_time=60)
            self.log.info("multi stream synthetic full is running and started backing up items..")

            # Killing StartSynthfull on CS
            self.log.info("Killing Start synthfull on CS..")
            self.log.info(self.indexing_anomaly.commserv.client_name)
            self.indexing_anomaly.kill_start_synthfull()

            # Kill log manager and Index server on Media agent
            self.log.info("Killing Log Manager and Index server..")
            self.indexing_anomaly.kill_index_server()

            # Suspending and resuming the backup
            self.log.info(" Suspending the syntheticfull job...")
            multi_stream_sfull.pause()
            jmobject_ms_sfull.wait_for_phase(
                'Synthetic Full Backup', total_attempts=9000, check_frequency=5)
            jmobject_ms_sfull.wait_for_state(
                expected_state="suspended", retry_interval=10, time_limit=3000)
            self.log.info(" Suspended the syntheticfull job successfully...")
            self.log.info("sleeping for 1  mins before resuming the backup job")
            sleep(60)

            self.log.info("Resuming the syntheticfull job...")
            multi_stream_sfull.resume()
            jmobject_ms_sfull.wait_for_phase(
                'Synthetic Full Backup', total_attempts=9000, check_frequency=5)
            jmobject_ms_sfull.wait_for_state(
                expected_state="running", retry_interval=10, time_limit=3000)
            self.log.info("Job resumed successfully..")

            # Waiting for the multi stream synthetic full job to backup minimum a few items
            self.backupjob_transferred_files(multi_stream_sfull, min_files=0, wait_time=60)
            self.log.info("""multi stream synthetic full is in
                           running state and started backing up items..""")

            # Kill CVSynthFullODS on media agent
            self.log.info("Killing CVSynthFullODS process on Media Agent..")
            self.indexing_anomaly.kill_cvsynthfullods()

            self.log.info("Waiting for the job to go to pending..")
            jmobject_ms_sfull.wait_for_state(
                expected_state="pending", retry_interval=10, time_limit=3000)
            self.log.info("Job went to pending state successfully..")

            self.log.info("Resuming the syntheticfull job...")
            multi_stream_sfull.resume()
            jmobject_ms_sfull.wait_for_phase(
                'Synthetic Full Backup', total_attempts=9000, check_frequency=5)
            jmobject_ms_sfull.wait_for_state(
                expected_state="running", retry_interval=10, time_limit=3000)
            self.log.info("Job resumed successfully..")

            # Waiting for the multi stream synthetic full job to backup minimum a few items
            self.backupjob_transferred_files(multi_stream_sfull, min_files=0, wait_time=60)
            self.log.info("""multi stream synthetic full is in
                                       running state and started backing up items..""")

            self.log.info("Sleeping for 30 secs before performing any other activity..")
            sleep(30)

            # Kill CVJobReplicatorODS on media agent
            self.log.info("Killing CVJobReplicatorODS process on Media Agent..")
            self.indexing_anomaly.kill_cvjobreplicatorods()

            self.log.info("Waiting for the job to go to pending..")
            jmobject_ms_sfull.wait_for_state(
                expected_state="pending", retry_interval=10, time_limit=3000)
            self.log.info("Job went to pending state successfully..")

            self.log.info("Resuming the syntheticfull job...")
            multi_stream_sfull.resume()
            jmobject_ms_sfull.wait_for_phase(
                'Synthetic Full Backup', total_attempts=9000, check_frequency=5)
            jmobject_ms_sfull.wait_for_state(
                expected_state="running", retry_interval=10, time_limit=3000)
            self.log.info("Job resumed successfully..")

            # Waiting for the multi stream synthetic full job to backup minimum a few items
            self.backupjob_transferred_files(multi_stream_sfull, min_files=400000, wait_time=60)

            # Waiting for the job to reach Archive Index phase
            jmobject_ms_sfull.wait_for_phase(
                'Archive Index', total_attempts=9000, check_frequency=5)
            jmobject_ms_sfull.wait_for_state(
                expected_state="running", retry_interval=2, time_limit=3000)

            # Killing log manager (Archive Index) in Archive Index phase
            self.log.info("sleeping for 4 secs before killing "
                          "archive Index process on Media agent ")
            sleep(4)
            self.log.info("Killing Archive Index on Media Agent..")
            self.indexing_anomaly.kill_archive_index()

            self.log.info("Waiting for the job to go to pending..")
            jmobject_ms_sfull.wait_for_state(
                expected_state="pending", retry_interval=10, time_limit=3000)
            self.log.info("Job went to pending state successfully..")

            self.log.info("Resuming the syntheticfull job...")
            multi_stream_sfull.resume()
            jmobject_ms_sfull.wait_for_state(
                expected_state="running", retry_interval=10, time_limit=3000)
            self.log.info("Job resumed successfully..")

            self.log.info("Done with performing the negative scenarios "
                          "on multi stream synthetic full backup..")
            self.log.info("Waiting for completion of single stream synthetic full job")
            jmobject_ms_sfull.wait_for_state(
                expected_state="completed", retry_interval=300, time_limit=300)
            self.log.info("multi stream synthetic full job completed successfully")

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
                retry_interval=420,
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
