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

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities, OptionsSelector
from Server.Scheduler import schedulerhelper
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing REST APIs for agent operations"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Schedule] - Continuous - Full Backup & In Place Restore"
        self.applicable_os = self.os_list.LINUX
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.SCHEDULEANDSCHEDULEPOLICY
        self.show_to_user = False

    def setup(self):
        """Setup function of this test case"""
        self._server_tc = ServerTestCases(self)
        self._entities = CVEntities(self)
        self._schedule_creator = schedulerhelper.ScheduleCreationHelper(self)
        self._utility = OptionsSelector(self.commcell)

    def run(self):
        """Main function for test case execution"""

        try:

            self._server_tc.log_step(
                """
                            Test Case
                            1. Creates a Continuous full Schedule
                            2. checks whether the respective job got triggered for schedule
                            3. Waits for the next continuous job and checks if that get triggered
                            3. Creates a Continuous restore in place schedule
                            4. Waits for the next continuous job and checks if that get triggered
                            """, 200
            )

            # Creating subclient entity on test case subclient
            subclient_prop = self._schedule_creator.entities_setup(self)
            _subclient_obj = subclient_prop['subclient']['object']
            _subclient_content = subclient_prop['subclient']['content']

            self._server_tc.log_step("""Step 1)
                        Create Continuous Full Backup Schedule and wait for Job to trigger"""
                                     )


            _bkp_sch_obj = self._schedule_creator.create_schedule('subclient_backup',
                                                                  schedule_pattern={
                                                                      'freq_type':
                                                                      'Continuous',
                                                                      'job_interval': 5,
                                                                  },
                                                                  subclient=_subclient_obj,
                                                                  backup_type='Full', wait_time=30)

            _bkp_job = self._schedule_creator.job_manager.job
            _sch_helper_obj = schedulerhelper.SchedulerHelper(_bkp_sch_obj, self.commcell)
            _sch_helper_obj.continuous_schedule_wait(_bkp_job)

            self._server_tc.log_step("""Step 2)
                        Create Continuous In Place Restore Schedule and wait for Job to trigger"""
                                     )

            _restore_sch_obj = self._schedule_creator.create_schedule('subclient_restore_in_place',
                                                                      schedule_pattern={
                                                                          'freq_type':
                                                                          'Continuous',
                                                                          'job_interval': 5,
                                                                      },
                                                                      subclient=_subclient_obj,
                                                                      paths=_subclient_content,
                                                                      wait_time=30)

            _restore_job = self._schedule_creator.job_manager.job
            _sch_helper_obj = schedulerhelper.SchedulerHelper(_restore_sch_obj, self.commcell)
            _sch_helper_obj.continuous_schedule_wait(_restore_job)

            self._server_tc.log_step("""Step 3)
                                    Create a Backup Schedule and pause it while it is backing up to verify Resume RPO
                                    """
                                     )

            _bkp_sch_obj_retry = self._schedule_creator.create_schedule('subclient_backup',
                                                                  schedule_pattern={
                                                                      'freq_type':
                                                                          'Continuous',
                                                                      'job_interval': 5,
                                                                  },
                                                                  subclient=_subclient_obj,
                                                                  backup_type='Full', wait=False)
            _sch_helper_obj_retry = schedulerhelper.SchedulerHelper(_bkp_sch_obj_retry, self.commcell)
            self._utility.sleep_time(_bkp_sch_obj_retry.continuous['job_interval'])
            _sch_helper_obj_retry.check_job_for_taskid(retry_count=15, retry_interval=15)
            if _sch_helper_obj_retry.jobs:
                self.log.info("Found Jobs for the subclient, Proceeding to Suspend the job.")
                _sch_helper_obj_retry.job_manager.job = _sch_helper_obj_retry.get_latest_job()
                _sch_helper_obj_retry.common_utils.job_list.append(_sch_helper_obj_retry.job_manager.job.job_id)
                self.log.info(f"Suspending job {_sch_helper_obj_retry.job_manager.job.job_id} to validate RPO.")
                _sch_helper_obj_retry.job_manager.modify_job('suspend')
                self._utility.sleep_time(360)
                _sch_helper_obj_retry.job_manager.modify_job('resume')
                self._utility.sleep_time(15)
                _sch_helper_obj_retry.job_manager.wait_for_state('completed')
                prev_jobID = _sch_helper_obj_retry.job_manager.job.job_id
                # now we will again check for jobs if they ran immediately to see if RPO was honored or not.
                jobs = _sch_helper_obj_retry.check_job_for_taskid(retry_count=10, retry_interval=15)
                if _sch_helper_obj_retry.get_latest_job().job_id != prev_jobID:
                    raise Exception("Next job is immediately kicking off and not following RPO.")
            else:
                raise Exception("The Continous job did not get triggered while checking for continous_job_suspend_"
                                "resume_check")

        except Exception as excp:
            self._server_tc.fail(excp)

        finally:
            self._schedule_creator.cleanup_schedules()
            self._entities.cleanup()
