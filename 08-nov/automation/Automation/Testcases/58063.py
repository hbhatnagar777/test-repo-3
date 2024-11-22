# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

"""

from cvpysdk.deployment.deploymentconstants import DownloadPackages
from cvpysdk.deployment.deploymentconstants import DownloadOptions

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config
from AutomationUtils.machine import Machine
from Web.Common.page_object import handle_testcase_exception
from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    """Class for downloading software job when disk is full"""

    def __init__(self):

        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Negative Scenario - Download when disk is full"
        self.machine_obj = None
        self.no_space_drive = None
        self.tcinputs = {
            "drive_path": None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.machine_obj = Machine(
            machine_name=self.commcell.commserv_name,
            commcell_object=self.commcell)
        self.no_space_drive = self.tcinputs["drive_path"]

    def run(self):
        """Main function for test case execution"""
        try:

            path = self.no_space_drive.split(":")[0]

            drive_space = self.machine_obj.get_storage_details()[path]['available']
            self.log.info("available space %s", drive_space)
            available_drive_space = drive_space - 500
            self.log.info("space %s", available_drive_space)
            extra_files_path = self.machine_obj.join_path(self.no_space_drive,"files")

            if available_drive_space > 200:
                # Filling up the drive with random files to make the drive to have less disk space
                file_size = (available_drive_space * 1000 / 50) - 1000
                flag = self.machine_obj.generate_test_data(file_path=extra_files_path,
                                                           file_size=int(file_size),
                                                           dirs=5,
                                                           files=10)
                self.log.info("returned output: %s", flag)
                if not flag:
                    raise Exception("Failed to fill up space")

            job = self.commcell.download_software(
                options=DownloadOptions.LATEST_SERVICEPACK.value,
                os_list=[DownloadPackages.WINDOWS_64.value])

            self.log.info("Job %s started for downloading packages", job.job_id)

            JobManager(job, self.commcell).wait_for_state('failed')

            self.log.info("job delay reason: %s", job.delay_reason)

            # freeing up the space in drive by deleting the random files
            if self.machine_obj.check_directory_exists(extra_files_path):
                self.machine_obj.remove_directory(extra_files_path)

            job_status = job.delay_reason
            self.log.info("JobFailingReason: %s", job_status)

            self.log.info("space %s", available_drive_space)

            # resubmitting the job

            resubmitted_job = job.resubmit()
            self.log.info("Job %s started for downloading packages", resubmitted_job.job_id)

            JobManager(resubmitted_job, self.commcell).wait_for_state()

        except Exception as exp:
            handle_testcase_exception(self, exp)
