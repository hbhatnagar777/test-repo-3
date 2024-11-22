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
from AutomationUtils.machine import Machine
from Server.Scheduler import schedulerhelper
from Server.serverhelper import ServerTestCases



class TestCase(CVTestCase):
    """Class for executing Daily Schedule with Random Timezone"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Schedule] - Daily - \"With Random Timezone\""
        self.applicable_os = self.os_list.LINUX
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.SCHEDULEANDSCHEDULEPOLICY
        self.cs_machine_obj = None
        self.show_to_user = False
        self._schedule_creator = None
        self._entities = None
        self._server_tc = None

    def setup(self):
        """Setup function of this test case"""
        self._server_tc = ServerTestCases(self)
        self._entities = CVEntities(self)
        self._schedule_creator = schedulerhelper.ScheduleCreationHelper(self)
        self.cs_machine_obj = Machine(self.commcell.commserv_client)

    def run(self):
        """Main function for test case execution"""

        try:

            self._server_tc.log_step(
                """
                            Test Case
                            1) Randomly Choose a timezone for which the daily schedule will be
                               created
                            2) Create a Daily schedule for a subclient backup with the randomly
                               chosen factors to run daily
                            3) Verify whether the schedule runs successfully
                """, 200
            )
            if not self.commcell.is_linux_commserv:
                self.cs_machine_obj.toggle_time_service()

            # Creating subclient entity on test case client
            subclient_prop = self._schedule_creator.entities_setup(self)
            _subclient_obj = subclient_prop['subclient']['object']

            self._server_tc.log_step("""Step 1)
                            Create Daily Full Backup Schedule with random timezone
                            and wait for Job to trigger""")
            start_date, start_time = self._schedule_creator.add_minutes_to_datetime(
                self.cs_machine_obj.current_time(), 10)

            sched_timezone_name, python_timezone = self._schedule_creator.get_random_tzone()

            sch_obj = self._schedule_creator.create_schedule(
                'subclient_backup',
                schedule_pattern={
                    'freq_type': 'Daily',
                    'active_start_date': start_date,
                    'active_start_time': start_time,
                    'time_zone': sched_timezone_name},
                subclient=_subclient_obj,
                backup_type="Full",
                wait=False)

            sch_helper = schedulerhelper.SchedulerHelper(
                sch_obj, self.commcell)
            sch_helper.timezone = python_timezone
            sch_helper.next_job_wait(2)
            self._schedule_creator.cleanup_schedules()

        except Exception as excp:
            self._server_tc.fail(excp)

        finally:
            self._schedule_creator.cleanup()
