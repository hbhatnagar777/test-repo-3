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
from AutomationUtils.options_selector import CVEntities
from Server.Scheduler import schedulerhelper
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing Testcase to verify Continuous Auxiliary Copy, Data verification job schedules"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Schedule] - Continuous Auxiliary copy and Data Verification job"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.SCHEDULEANDSCHEDULEPOLICY
        self.show_to_user = False

    def setup(self):
        """Setup function of this test case"""
        self._server_tc = ServerTestCases(self)
        self._entities = CVEntities(self)
        self._schedule_creator = schedulerhelper.ScheduleCreationHelper(self)

    def cleanup_secondary_copy(self, storage_policy_obj, copy_name):
        """Cleanup function to remove the created secondary copy"""
        self.log.info(f"Deleting secondary copy created {copy_name}")
        storage_policy_obj.delete_secondary_copy(copy_name=copy_name)

    def run(self):
        """Main function for test case execution"""

        try:

            self._server_tc.log_step(
                """
                            Test Case
                            1. Creates a Continuous Aux-copy Schedule
                            2. Checks whether the respective job got triggered for schedule
                            3. Waits for the next continuous job and checks if that get triggered
                            3. Creates a Continuous Data verification job schedule
                            4. Waits for the next continuous job and checks if that get triggered
                            """, 200)

            # Creating subclient entity on test case subclient
            # Get storage policy created, media agent used
            subclient_prop = self._schedule_creator.entities_setup(self)
            _storage_policy_obj = subclient_prop['storagepolicy']['object']
            _media_agent_name = subclient_prop['storagepolicy']['mediaagent_name']
            _library_name = subclient_prop['storagepolicy']['library_name']
            _copy_name = 'Copy-1'

            # Create secondary copy for Storage policy created above
            _storage_policy_obj.create_secondary_copy(copy_name=_copy_name,
                                                      library_name=_library_name,
                                                      media_agent_name=_media_agent_name)

            self._server_tc.log_step("""Step 1)
                                        Create a Continuous Auxiliary Copy Schedule and wait for Job to trigger""")

            sch_obj = self._schedule_creator.create_schedule('aux_copy',
                                                             schedule_pattern={'freq_type':
                                                                               'Continuous',
                                                                               'job_interval': 5},
                                                             wait_time=30,
                                                             storage_policy=_storage_policy_obj,
                                                             sp_copy=_copy_name,
                                                             media_agent=_media_agent_name
                                                             )

            aux_copy_job = self._schedule_creator.job_manager.job
            _sch_helper_obj = schedulerhelper.SchedulerHelper(sch_obj, self.commcell)
            _sch_helper_obj.continuous_schedule_wait(aux_copy_job)

            self._server_tc.log_step("""Step 2)
                            Create a Continuous Data Verification
                            Schedule and wait for Job to trigger""")

            sch_obj = self._schedule_creator.create_schedule('data_verification',
                                                             schedule_pattern={'freq_type':
                                                                     'Continuous',
                                                                     'job_interval': 5},
                                                             wait_time=30,
                                                             storage_policy=_storage_policy_obj
                                                             )

            data_verification_job = self._schedule_creator.job_manager.job
            _sch_helper_obj = schedulerhelper.SchedulerHelper(sch_obj, self.commcell)
            _sch_helper_obj.continuous_schedule_wait(data_verification_job)

        except Exception as excp:
            self._server_tc.fail(excp)

        finally:
            self.cleanup_secondary_copy(storage_policy_obj=_storage_policy_obj, copy_name=_copy_name)
            self._schedule_creator.cleanup_schedules()
            self._entities.cleanup()