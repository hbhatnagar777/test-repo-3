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

    initialize_sdk_objects   -- use to initialize the sdk required

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

   Prerequisite:
                 Need a client and have 2-3 full backups 24 hours prior to run the case
"""
from cvpysdk.plan import Plan
from cvpysdk.job import JobController
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import TestStep
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """
    Class for Retention verification for Azure AD
    """
    TestStep = TestStep()

    def __init__(self):
        """ Initializes test case class object """
        super().__init__()
        self.name = "Retention Verification"
        self.utils = TestCaseUtils(self)
        self.server_plan_name = None
        self.server_plan_id = None
        self.plan_object = None
        self.copy_id = None
        self.client_name = None

    @TestStep
    def do_backup(self, backup_type=None):
        """
        use to perform the backup job
        Args:
            backup_type          : type of backup to perform
        return:
            None
        """
        self.log.info(f"Started the {backup_type} backup for the client")
        backup_job = self._subclient.backup(backup_level=backup_type)
        self.log.info(f"Backup job  jobid: {backup_job.job_id}")
        backup_job.wait_for_completion()
        self.log.info("Backup job completed")

    @TestStep
    def edit_plan(self, retention_day: int):
        """
         Function to change the retention time and enable the data aging of the Plan
         Args:
             retention_day(int) :  number of days to set retention

        """

        self.log.info("disabling the data aging")
        self.plan_object.enable_data_aging(plan_copy_id=self.copy_id,
                                           is_enable=False)

        self.log.info(f"setting the Retention time of plan to {retention_day} Day")
        self.plan_object.edit_copy(copy_name="Primary", new_retention_days=retention_day)
        self.log.info("enabling the data aging")

        self.plan_object.enable_data_aging(plan_copy_id=self.copy_id,
                                           is_enable=True)

    @TestStep
    def run_data_aging(self):
        """
        function is used to run the data aging job on the commcell
        """

        self.log.info("Running the data aging job")

        da_job = self._commcell.run_data_aging(copy_name="Primary",
                                               is_granular=True,
                                               include_all_clients=True,
                                               storage_policy_name=self.server_plan_name)

        self.log.info("data aging job: %s", da_job.job_id)
        if not da_job.wait_for_completion():
            raise Exception(f"Failed to run data aging with error: {da_job.delay_reason}")

        self.log.info("data aging job Completed")

    @TestStep
    def get_all_backup_jobs(self):
        """
        Get all the completed backup jobs

        Returns:
            List of all the Completed backup job
        """
        self.log.info("getting all the backup job")

        jobs_id = JobController(self._commcell).all_jobs(client_name=self.client_name,
                                                         lookup_time=128,
                                                         job_filter="Backup")

        jobs = []
        for key, value in jobs_id.items():
            if value['status'] == 'Completed':
                jobs.append(key)

        self.log.info(f"list of backup completed jobs are:{jobs}")
        self.log.info(f"number of backup jobs are{len(jobs)}")

        return jobs

    def setup(self):

        self.server_plan_name = self.tcinputs["serverPlanName"]
        self.server_plan_id = self.tcinputs["serverPlanId"]
        self.plan_object = Plan(commcell_object=self._commcell,
                                plan_name=self.server_plan_name,
                                plan_id=self.server_plan_id)
        self.copy_id = self.tcinputs["serverPlanCopyId"]
        self.client_name = self.tcinputs["ClientName"]

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Executing run function")

            # Running a full backup job
            self.do_backup(backup_type="Full")

            job_id = self.get_all_backup_jobs()

            self.edit_plan(retention_day=30)

            self.run_data_aging()

            job_ids_after_data_aging_1 = self.get_all_backup_jobs()

            if len(job_id) == len(job_ids_after_data_aging_1):

                self.log.info("No job get pruned if retetnion is 30 days")

            else:
                raise Exception("Jobs get pruned if retention is 30 days")

            self.edit_plan(retention_day=1)

            self.run_data_aging()

            job_ids_after_data_aging_2 = self.get_all_backup_jobs()

            if len(job_ids_after_data_aging_2) != 0 and len(job_ids_after_data_aging_1) > len(
                    job_ids_after_data_aging_2):
                self.log.info("Retention verification is successful")
                self.log.info(f"Number  of jobs present before running "
                              f"data aging job is: {len(job_ids_after_data_aging_1)} ")

                self.log.info(f"Number of jobs present before running "
                              f"data aging job is: {len(job_ids_after_data_aging_2)} ")
            else:
                self.log.info(f"Number of jobs present before running "
                              f"data aging job is: {len(job_ids_after_data_aging_1)} ")

                self.log.info(f"Number of jobs present before running"
                              f" data aging job is: {len(job_ids_after_data_aging_2)} ")

                raise Exception("Retention verification failed job not pruned")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Teardown function of this test case"""
        self.log.info("Teardown function of this test case started")

        if self.status == constants.PASSED:
            self.log.info("Testcase completed successfully")
            self.edit_plan(retention_day=30)

        else:
            self.log.info("Testcase failed")
