# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

Sample input:
    "23685":{
        "AgentName": "File System",
        "ClientName": "DHIVM2.testlab.commvault.com",
        "StoragePolicyName": "dhi-sp1",
        "TestPath": "E:\\TestDataFolder",
        "NumberOfFiles": "500",
        "NumberOfSuspends": "5",
        "MAMachineName": "DHIVM2_2",
        "DataReaders": "3",
        "FileSizeMB": "1",
        "ChunkSizeMB": "100"
    }

TestCase: Class for executing this test case

TestCase:
    __init__()                          --  Initialize TestCase class

    setup()                             --  Initializes pre-requisites for this test case.

    run()                               --  run function of this test case

"""

from time import sleep
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.fshelper import ScanType, FSHelper


class TestCase(CVTestCase):
    """Class for executing
        Multi Stream Backup
        This test case does the following
        1: Set number of data readers to 3 and enable Multiple Data Readers for each mount point
        2: Generate Test data
        3: Set Chunk Size to 100 MB and try to do multiple suspend resume after writing one chunk
        4: After multiple suspensions and job completion, verify total backed up items match with original data
        5: Verify the number of data streams launched with the multi reader settings
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Multi Stream Backup - Restartability"
        self.tcinputs = {}
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.client_machine = None
        self.backupset_name = None
        self.subclient_name = None
        self.scan_type = None
        self.agent_type = None
        self.client_name = None
        self.ma_machine_name = None
        self.restore_path = None

    def setup(self):
        self.helper = FSHelper(self)
        self.helper.populate_tc_inputs(self)
        self.ma_machine_name = self.tcinputs.get("MAMachineName", None)
        self.backupset_name = "backupset_" + str(self.id)
        self.subclient_name = "subclient_" + str(self.id)

    def run(self):
        """Main function for test case execution"""
        try:
            # Initialize the Test Case Inputs
            self.log.info("Initializing Test Case Inputs")
            sp_chunk_size = int(self.tcinputs.get("ChunkSizeMB", 100))
            data_readers = int(self.tcinputs.get("DataReaders", 3))
            file_size_mb = int(self.tcinputs.get("FileSizeMB", 1))
            number_of_files = int(self.tcinputs.get("NumberOfFiles", 1000))
            number_of_suspends = int(self.tcinputs.get("NumberOfSuspends", 5))
            test_path = self.test_path + self.slash_format + "TestData_" + str(self.id)
            self.log.info("Set file size to {} MB".format(file_size_mb))
            self.log.info("Set number of data readers to {}".format(data_readers))
            self.log.info("Set number of files to {}".format(number_of_files))
            self.log.info("Set number of suspends to {}".format(number_of_suspends))
            self.log.info("Setting default content for backup to {}".format([test_path]))

            # Begin Execution of Test Case
            self.log.info("Starting Execution of Test case {} with multiple backup streams "
                          "Suspend & Resume".format(self.id))

            # Generate Test Data on Desired Location
            self.log.info("Generating Test Dataset on Location {}".format(test_path))
            cl_machine = Machine(self.client_name, self.commcell)
            if cl_machine.check_directory_exists(directory_path=test_path):
                cl_machine.clear_folder_content(folder_path=test_path)
            cl_machine.generate_test_data(
                file_path=test_path, files=number_of_files, dirs=1, file_size=1024 * file_size_mb, slinks=False,
                hlinks=False, sparse=False, zero_size_file=False)
            self.log.info("Test Data generated.")

            helper = self.helper

            # Create Backupset
            helper.create_backupset(name=self.backupset_name, delete=True)

            # Create Subclient
            helper.create_subclient(name=self.subclient_name, scan_type=ScanType.OPTIMIZED, data_readers=data_readers,
                                    storage_policy=self.storage_policy, allow_multiple_readers=True,
                                    content=[test_path], delete=True)

            # Modify Chunk Size of MA Machine associated to storage policy to the desired chunk size
            chunk_size = sp_chunk_size

            if not helper.modify_chunk_size(ma_machine_name=self.ma_machine_name, size_mb=sp_chunk_size):
                self.log.info("Proceeding with existing chunk size value.")

            # Run a full backup to get approximate wait time between two suspends
            job = helper.run_backup(backup_level="Full", incremental_backup=False, wait_to_complete=True)[0]
            elapsed_time = int(job.details['jobDetail']['detailInfo']['transferTime'])
            self.log.info("Write Time from jobDetails: {}".format(str(elapsed_time)))
            data_size = number_of_files * file_size_mb
            if elapsed_time != -1 and elapsed_time is not None:
                self.log.info("Received Backup Phase Elapsed Time : {} seconds".format(elapsed_time))

                # Wait Time is the approximate time required for one chunk to be written
                # if chunk size was successfully modified, else the time to write the size set at tcinputs (ChunkSize),
                # or 100 MB if not set
                wait_time = (chunk_size * elapsed_time) / data_size
                self.log.info("Setting wait time between suspends to : {} seconds".format(wait_time))
            else:
                self.log.error("Failed to receive Elapsed Time.")
                raise Exception("Elapsed Time not received.")

            # Run backup job which will be suspended and resumed multiple times.
            job = helper.run_backup(backup_level="Full", wait_to_complete=False)[0]
            job_id = str(job.job_id)
            suspend_count = 0

            # Begin the cycle of suspensions and resumes
            self.log.info("Starting multiple suspensions and resumes in job {}".format(job_id))
            try:
                # Loop will run as long as job is not complete
                while job.status and job.status.lower() != "completed":
                    if job.status.lower() in ["pending", "failed"]:

                        # In this case, the job needs to be killed and the test case fails.
                        status = job.status
                        self.log.info("Job went to {} state. Going to kill job.".format(status))
                        job.kill(wait_for_job_to_kill=True)
                        raise Exception("Job went to {} state. Killed job.".format(status))

                    # In case of error occurrence, the job is killed and the test case fails.
                    elif job.delay_reason:
                        self.log.info("Job delayed. Delay Reason: {}".format(job.delay_reason))
                        job.kill(wait_for_job_to_kill=True)
                        raise Exception("Job went to delayed state. Killed job.")

                    # Until the set number of suspends is reached,
                    # the job will keep getting suspended as long as it is in the backup phase
                    elif job.phase and job.phase.lower() == "backup":
                        if suspend_count < number_of_suspends:
                            self.log.info("Waiting for {} seconds before suspending".format(wait_time))
                            sleep(wait_time)
                            job.pause(wait_for_job_to_pause=True)
                            self.log.info("Waiting for {} seconds before Resuming.".format(10))
                            sleep(10)
                            job.resume(wait_for_job_to_resume=True)
                            suspend_count += 1
                            self.log.info("Number of suspends: {}".format(suspend_count))

                    # If Job Phase goes to N/A, the job is completed
                    elif job.phase is None:
                        self.log.info("Exiting loop of suspensions as Job Phase went to None.")
                        break

                    # Job status is neither completed, pending, nor failed and the job phase is not N/A.
                    else:
                        if suspend_count < number_of_suspends:
                            self.log.info("Current Job status = {}, phase = {}".format(job.status, job.phase))

            except Exception as exp:
                self.log.info("Exiting Loop due to exception {}".format(str(exp)))
                self.log.info("Job status: {}".format(job.status))
                self.log.info("Job phase: {}".format(job.phase))

                # In case the failure occurs in suspending/resuming due to job completion already,
                # the test case need not fail and execution can proceed
                if job.status.lower() == 'completed':
                    self.log.info("As job stands completed, proceeding with further execution.")

                # If job fails to be resumed/suspended due to some other error and it is not completed
                else:
                    raise exp

            self.log.info("Total suspends that could be performed: {} "
                          "out of {}.".format(suspend_count, number_of_suspends))

            # In case enough suspensions not performed, testcase will fail
            if suspend_count <= 1:
                self.log.info("Enough suspensions could not be done. Ending Execution")
                raise Exception("Suspend count less than at least 2")

            # Verify the backed up data
            self.log.info("Verifying backed-up data")
            helper.run_find_verify(machine_path=test_path, job=job)

            # Check the number of streams utilized for backup matching the data reader settings
            streams = helper.get_backup_stream_count(job)
            self.log.info("Number of Streams from Job Details: {}".format(str(streams)))
            if streams == -1 or streams is None:
                raise Exception("Failed to get streams information from job {}".format(job_id))

            if streams != data_readers:
                raise Exception("Number of streams - {} not matching "
                                "with number of data readers - {}".format(streams, data_readers))
            else:
                self.log.info("Backup job honors the multi data reader setting and launches {} streams".format(streams))

            self.log.info("Test Case {} Passed.".format(self.id))

        except Exception as exp:
            self.log.error('Multi Stream Backup Multiple Suspend & Resume Test failed with error: %s.', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED

        finally:
            self.log.info("Cleaning up Test Case related items.")
            self.log.info("Deleting backupset {}".format(self.backupset_name))
            backupsets_object = self.instance.backupsets
            backupsets_object.delete(self.backupset_name)
            self.log.info("Backupset {} deleted.".format(self.backupset_name))
            self.log.info("Clearing up test data.")
            cl_machine.remove_directory(directory_name=test_path)
            self.log.info("Test data cleared.")





