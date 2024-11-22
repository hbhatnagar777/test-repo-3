# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""
from AutomationUtils.cvtestcase import CVTestCase
from Database.SplunkApplication.splunk import Splunk
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from cvpysdk.job import Job
from cvpysdk.client import Client


class TestCase(CVTestCase):
    """
    Class for executing basic test case for creating new splunk client and performing
    backup and recovery and verifying the same.
    """
    test_step = TestStep()

    def __init__(self):
        """
        init method of the test-case class which defines test-case arguments
        """
        super(TestCase, self).__init__()
        self.second_job = None
        self.first_job = None
        self.second_eventcount = None
        self.first_eventcount = None
        self.clientobj = None
        self.backupset_object = None
        self.job_id = None
        self.admin_console = None
        self.index_name = None
        self.index_obj = None
        self.client_obj = None
        self.name = "Splunk iDA,Basic Acceptance Backup and Restore"
        self.splunk_object = None
        self.tcinputs = {
            "NewClientName": None,
            "MasterNode": None,
            "MasterUri": None,
            "UserName": None,
            "Password": None,
            "SplunkHomePath": None,
            "Plan": None,
            "Nodes": None,  # list of slave nodes:[slave1, slave2]
            "Slave1Ip": None,
            "Slave1Port": None,
            "Slave1SplunkUsername": None,
            "Slave1SplunkPassword": None,
        }

    def setup(self):
        """
        Creates a new Splunk Client on CS and adds a new index to Splunk cluster
        """
        self.splunk_object = Splunk(self)
        self.log.info("Starting Splunk Client Creation")
        self.client_obj = self.splunk_object.cvoperations.add_splunk_client()
        if self.client_obj is None:
            raise Exception("New Splunk Client Creation Failed")
        self.log.info("Splunk Client Creation Successful")
        self.index_obj = self.splunk_object.add_splunk_index()
        if self.index_obj is None:
            raise Exception("New Splunk Index Creation Failed")
        self.log.info("Splunk Index Creation Successful")
        self.clientobj = Client(commcell_object=self.commcell, client_name=self.tcinputs['MasterNode'])
        self.clientobj.add_additional_setting(
            "FileSystemAgent",
            "bReadLiveVolumeForSplunkBackupCopy",
            "BOOLEAN",
            "True"
        )
        self.log.info("Successfully added the Additional Settings")

    @test_step
    def perform_backup(self):
        """
        Updates Content of New client with the newly created index and performs backup
        """
        try:
            self.index_name = self.index_obj["name"]
            self.log.info("Starting Backup Job")
            nodes = self.tcinputs.get("Nodes")
            self.splunk_object.cvoperations.update_client_nodes(self.client_obj, nodes)
            self.splunk_object.cvoperations.update_client_content(self.client_obj, [self.index_name])
            self.log.info(f"Updated client content for index: {self.index_name}")
            _, job_id = self.splunk_object.cvoperations.run_backup(self.client_obj)
            if job_id is not None:
                self.first_job = Job(self.commcell, job_id)
                self.first_job.wait_for_completion()
                self.first_eventcount = self.index_obj["totalEventCount"]
                self.log.info("Backup job Successful")
        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def perform_point_in_time_restore_from_first_full_job(self):
        """
        Performs a point-in-time restore from the first incremental backup job.
        """
        try:
            self.log.info("Performing Point-in-Time Restore from the First Full Backup Job")

            self.splunk_object.delete_index()
            self.log.info(f"Index {self.index_name} has been deleted")
            self.splunk_object.cvoperations.run_restore(self.client_obj, [self.index_name],
                                                        from_time=self.first_job.start_time,
                                                        to_time=self.first_job.end_time)
            self.log.info("Point-in-Time Restore from the First Full Backup Job Successful")
            self.splunk_object.make_after_restore_configuration()
            self.splunk_object.cvoperations.verify_restore(self.first_eventcount, self.index_name)
        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def add_new_buckets_and_run_incremental_job_again(self):
        """
        Adds new buckets to the Splunk index and runs an incremental backup job again.
        """
        try:
            self.log.info("Adding New Buckets to Splunk Index")
            self.index_name = self.index_obj["name"]
            index_obj1 = self.splunk_object.add_data_to_index(self.index_name, num_of_buckets=1)
            self.log.info("New Buckets Added Successfully")
            self.log.info("Performing Rolling Restart")
            self.splunk_object.splunk_rolling_restart()
            self.log.info("Rolling Restart Completed")
            self.log.info("Running Incremental Backup Job Again")
            nodes = self.tcinputs.get("Nodes")
            self.splunk_object.cvoperations.update_client_nodes(self.client_obj, nodes)
            self.splunk_object.cvoperations.update_client_content(self.client_obj, [self.index_name])
            _, job_id = self.splunk_object.cvoperations.run_backup(self.client_obj, backup_type="Incremental")
            if job_id is not None:
                self.second_job = Job(self.commcell, job_id)
                self.second_job.wait_for_completion()
                self.second_eventcount = index_obj1["totalEventCount"]
                self.log.info("Incremental Backup Job Again Successful")
        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def run_incremental_job_without_adding_new_indexes_or_buckets(self):
        """
        Runs an incremental backup job without adding new indexes or buckets.
        """
        try:
            self.log.info("Running Incremental Backup Job Again Without Adding New Indexes or Buckets")
            self.splunk_object.cvoperations.run_backup(self.client_obj, backup_type="Incremental")
            self.log.info("Incremental Backup Job Again Without Adding New Indexes or Buckets Successful")
        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def perform_point_in_time_restore_from_second_incremental_job(self):
        """
        Performs a point-in-time restore from the second incremental backup job.
        """
        try:
            self.log.info("Performing Point-in-Time Restore from the second Incremental Backup Job")
            self.splunk_object.delete_index()
            self.log.info(f"Index {self.index_name} has been deleted")
            self.splunk_object.cvoperations.run_restore(self.client_obj, [self.index_name],
                                                        from_time=self.second_job.start_time,
                                                        to_time=self.second_job.end_time)
            self.log.info("Point-in-Time Restore from the second Incremental Backup Job Successful")
            self.splunk_object.make_after_restore_configuration()
            self.splunk_object.cvoperations.verify_restore(self.second_eventcount, self.index_name)
        except Exception as e:
            raise CVTestStepFailure(e)

    def cleanup(self):
        self.log.info("Starting Cleanup Job")
        self.clientobj.delete_additional_setting(
            "FileSystemAgent",
            "bReadLiveVolumeForSplunkBackupCopy"
        )
        self.splunk_object.cvoperations.cleanup(self.client_obj)
        self.splunk_object.cleanup_index(self.index_name)
        self.log.info("Cleanup Job Successful")

    def run(self):
        """
        Run function of this test case
        """
        self.perform_backup()
        self.perform_point_in_time_restore_from_first_full_job()
        self.add_new_buckets_and_run_incremental_job_again()
        self.run_incremental_job_without_adding_new_indexes_or_buckets()
        self.perform_point_in_time_restore_from_second_incremental_job()
        self.cleanup()
