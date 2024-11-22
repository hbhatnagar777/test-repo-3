# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Validate job controls [suspend/resume/kill/view/log/event] of a backup job

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    run()                       --  run function of this test case

    wait_for_state_multi()     --  Wait for job state for multiple job objects

"""

# Test Suite imports
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities, OptionsSelector
from AutomationUtils.idautils import CommonUtils
from Server.serverhelper import ServerTestCases
from Server.JobManager.jobmanager_helper import JobManager

class TestCase(CVTestCase):
    """Class for validating testcase on job related operations"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Acceptance] : Validate job controls [suspend/resume/kill
                        /suspend all/kill all of a backup job """
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True

    def wait_for_state_multi(self, job_manager, jobs, job_state):
        ''' Wait for job state for multiple job objects

        Args:
            job_manager    (object)    -- JobManager class object

            jobs           (list)      -- List of job objects of Job SDK class

            job_state      (str)       -- Job state to wait for.
        '''

        for _job in jobs:
            job_manager.job = _job
            job_manager.wait_for_state(job_state)

    def run(self):
        """Main function for test case execution."""
        try:
            tc = ServerTestCases(self)
            entities = CVEntities(self)
            tc_base = CommonUtils(self)
            utility = OptionsSelector(self.commcell)
            job_manager = JobManager(commcell=self.commcell)
            _seconds = 3

            #-------------------------------------------------------------------------------------
            tc.log_step("""
                        Test Case
                        1)
                            - Create subclient, with relatively higher content size, and execute
                                full backup for the subclient.
                            - Wait for job to go to running state.
                            - Suspend backup job and wait for job to be suspended.
                            - Resume backup job and wait for job to move to running state,
                                and wait for job to complete.
                        2)
                            - Create new subclient and subclient content and start Backup on
                                old subclient and new subclient
                            - Suspend all jobs and wait for jobs to go to suspended state.
                            - Resume all jobs and wait for jobs to go to running state., and
                                wait for job to complete.
                        3)
                            - Start backup for second subclient and wait for job to go in running
                                state.
                            - Kill the backup job and wait for job to be killed.
                        4)
                            - Execute backup jobs on the two subclients, and wait for jobs to go
                                to running state.
                            - Kill all jobs.
                            - Check job status for the backup jobs if they are killed.

                        Cleanup test data""", 200)

            #-------------------------------------------------------------------------------------
            tc.log_step("""Step 1)
                            - Create subclient, with relatively higher content size, and execute
                                full backup for the subclient, and wait for job to be in running
                                state.
                            - Suspend backup job and wait for job to be suspended
                            - Resume backup job and wait for job to move to running state,
                                and wait for job to complete. """)

            subclient_properties = entities.create({'subclient':{'level': 2, 'size': 15}})
            subclient_object = subclient_properties['subclient']['object']
            job_manager.job = tc_base.subclient_backup(subclient_object, "full", False)
            job_manager.wait_for_state(['waiting', 'running'])
            job_manager.modify_job('suspend')
            job_manager.modify_job('resume')
            job_manager.wait_for_state('completed')


            #-------------------------------------------------------------------------------------
            tc.log_step("""Step 2)
                            - Create new subclient and subclient content and start Backup on
                                old subclient and new subclient
                            - Sleep for 3 seconds and get job ids for both the jobs
                            - Suspend all jobs and wait for jobs to go to suspended state
                            - Resume all jobs and wait for jobs to go to running state., and
                                wait for job to complete. """)

            subclient_1_properties = entities.create({'subclient':{'level': 2, 'size': 15}})
            subclient_1_object = subclient_1_properties['subclient']['object']
            job_1 = tc_base.subclient_backup(subclient_object, "full", False)
            job_2 = tc_base.subclient_backup(subclient_1_object, "full", False)
            utility.sleep_time(_seconds)
            job_manager.modify_all_jobs('suspend')
            self.wait_for_state_multi(job_manager, [job_1, job_2], 'suspended')
            job_manager.modify_all_jobs('resume')
            self.wait_for_state_multi(job_manager, [job_1, job_2], 'completed')


            #-------------------------------------------------------------------------------------
            tc.log_step("""Step 3)
                            - Start backup for second subclient.
                            - Kill the backup job and wait for job to be killed. """)

            job_manager.job = tc_base.subclient_backup(subclient_1_object, "full", False)
            job_manager.modify_job('kill')


            #-------------------------------------------------------------------------------------
            tc.log_step("""Step 4)
                            - Execute backup jobs on the two subclients.
                            - Kill all jobs.
                            - Check job status for the backup jobs if they are killed.""")

            job_3 = tc_base.subclient_backup(subclient_object, "full", False)
            job_4 = tc_base.subclient_backup(subclient_1_object, "full", False)
            job_manager.modify_all_jobs('kill')
            self.wait_for_state_multi(job_manager, [job_3, job_4], 'killed')

        except Exception as excp:
            tc.fail(excp)
        finally:
            tc_base.cleanup_jobs()
            entities.cleanup()
