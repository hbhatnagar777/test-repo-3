# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that the workflow "Disaster recovery backup" runs a DR backup job and the
backup job completes successfully without errors and with valid data.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    get_dr_job()                --  Runs a backup job and adds the job to Indexing validation

    check_dr_afiles()           --  Checks if the DR job has both the data and the index afiles
    required to do successful restore operation

"""

import traceback
import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase

from Server.Workflow.workflowhelper import WorkflowHelper
from Server.JobManager.jobmanager_helper import JobManager

from cvpysdk.job import JobController
from cvpysdk.job import Job


class TestCase(CVTestCase):
    """This testcase verifies that the workflow "Disaster recovery backup" runs a DR backup job
    and the backup job completes successfully without errors and with valid data."""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Workflow - Disaster recovery backup job'

        self.dr_wf = None
        self.cs_name = None
        self.cs = None
        self.job_controller = None

    def setup(self):
        """All testcase objects are initializes in this method"""

        try:
            self.dr_wf = WorkflowHelper(self, 'Disaster Recovery Backup')
            self.cs_name = self.commcell.commserv_name
            self.cs = self.commcell.commserv_client
            self.job_controller = JobController(self.commcell)

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed"""

        try:
            self.log.info("Started executing {0} testcase".format(self.id))

            self.log.info('Starting DR backup workflow')
            self.dr_wf.execute()
            self.log.info('DR backup workflow completed successfully')

            attempts = 1
            new_dr_job = None

            while attempts <= 5:
                time.sleep(10)
                self.log.info('Checking if DR backup job has started. Attempt [{0}/5]'.format(
                    attempts))
                new_dr_job = self.get_dr_job(finished=False)

                if new_dr_job:
                    break
                else:
                    attempts += 1
                    continue

            if not new_dr_job:
                raise Exception('Workflow didn\`t start DR backup job after 50 seconds attempts')

            self.log.info('New DR backup job started. Job ID [{0}]'.format(new_dr_job.job_id))
            new_dr_job_jm = JobManager(new_dr_job, self.commcell)
            new_dr_job_jm.wait_for_state('completed')

            self.log.info('Verifying if the DR job has all the required afiles for restore.')
            if self.check_dr_afiles(new_dr_job.job_id):
                self.log.info('New DR backup job completed with valid afiles')
            else:
                raise Exception('New DR backup job is missing valid afiles')

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception(exp)

    def get_dr_job(self, finished=False):
        """Gets the DR job history for the running and completed jobs.

            Args:
                finished        (bool)      --  Decides whether to get completed job or not.
                (Default: False)

            Returns:
                (obj)   --      Job class object
                (none)  --      otherwise

        """

        dr_jobs = []

        if finished:
            all_jobs_dict = self.job_controller.finished_jobs(
                client_name=self.cs_name.lower(), lookup_time=48)
        else:
            all_jobs_dict = self.job_controller.active_jobs()

        for job_id, props in all_jobs_dict.items():
            if props['job_type'] == 'CS DR Backup':
                if finished and props['status'].lower() != 'completed':
                    continue
                dr_jobs.append(job_id)

        last_dr_job = max(dr_jobs) if dr_jobs else None

        if last_dr_job is None:
            return None
        else:
            return Job(self.commcell, last_dr_job)

    def check_dr_afiles(self, new_job_id):
        """Checks if the DR job has both the data and the index afiles required to do
        successful restore operation

            Args:
                new_job_id      (str)       --      The DR job ID to validate afiles for

            Returns:
                True    --      if afiles are valid
                False   --      otherwise

        """

        self.csdb.execute('select count(distinct filetype) from archfile where appid = 1 '
                          'and isValid = 1 and jobId = {0}'.format(new_job_id))

        row = self.csdb.fetch_one_row()
        if not row:
            raise Exception('The new DR backup job did not complete with valid afiles')

        if int(row[0]) == 2:
            self.log.info('DR job has all valid afiles and completed successfully')
            return True
        else:
            self.log.error('DR job does not have all the afiles')
            return False
