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

from datetime import datetime
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities
from Server.Scheduler import schedulerhelper
from Server.serverhelper import ServerTestCases
from Install.softwarecache_helper import SoftwareCache


class TestCase(CVTestCase):
    """Class for executing Testcase to verify Monthly Data Aging, Download software schedules"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Schedule] - Continuous - Data aging and Download software job"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.SCHEDULEANDSCHEDULEPOLICY
        self.show_to_user = False

    def setup(self):
        """Setup function of this test case"""
        self._server_tc = ServerTestCases(self)
        self._entities = CVEntities(self)
        self._schedule_creator = schedulerhelper.ScheduleCreationHelper(self)
        self._software_cache = SoftwareCache(self.commcell, self.commcell.commserv_client)

    def run(self):
        """Main function for test case execution"""

        try:

            self._server_tc.log_step(
                """
                            Test Case
                            1. Creates a Continuous Data aging Schedule
                            2. Checks whether the respective job got triggered for schedule
                            3. Waits for the next continuous job and checks if that get triggered
                            3. Creates a Continuous Download software in place schedule
                            4. Waits for the next continuous job and checks if that get triggered
                            """, 200)

            self._server_tc.log_step("""Step 1)
                                        Create a Continuous Data aging Schedule and wait for Job to trigger""")

            sch_obj = self._schedule_creator.create_schedule('data_aging',
                                                             schedule_pattern={'freq_type':
                                                                               'Continuous',
                                                                               'job_interval': 5},
                                                             wait_time=30)

            data_aging_job = self._schedule_creator.job_manager.job
            _sch_helper_obj = schedulerhelper.SchedulerHelper(sch_obj, self.commcell)
            _sch_helper_obj.continuous_schedule_wait(data_aging_job)

            self._server_tc.log_step("""Step 2)
                            Create Continuous Download Software
                            Schedule and wait for Job to trigger""")

            sch_obj = self._schedule_creator.create_schedule('download_software',
                                                             schedule_pattern={'freq_type':
                                                                               'Continuous',
                                                                               'job_interval': 5},
                                                             wait_time=30)

            download_software_job = self._schedule_creator.job_manager.job
            _sch_helper_obj = schedulerhelper.SchedulerHelper(sch_obj, self.commcell)
            _sch_helper_obj.continuous_schedule_wait(download_software_job)


        except Exception as excp:
            self._server_tc.fail(excp)

        finally:
            self._schedule_creator.cleanup_schedules()
            self._software_cache.delete_remote_cache_contents()
