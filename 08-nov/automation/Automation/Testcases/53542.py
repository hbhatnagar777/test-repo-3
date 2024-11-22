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

import random
from AutomationUtils.options_selector import CVEntities
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Server.Scheduler import schedulerhelper, schedulerconstants
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing Monthly Relative Schedule"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Schedule] - Monthly Relative - \"nth Weekday/Weekend Day\""
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.SCHEDULEANDSCHEDULEPOLICY
        self.show_to_user = False

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
                            1) Randomly Choose from two factors relative time (first,second, third
                               etc) and relative weekday (monday, tuesday, weekday etc)
                            2) Create a Monthly schedule for a subclient backup with the randomly
                               chosen factors to run once a month
                            3) Verify whether the schedule runs successfully
                """, 200)

            self.cs_machine_obj.toggle_time_service()

            # Creating subclient entity on test case client
            subclient_prop = self._schedule_creator.entities_setup(self)
            _subclient_obj = subclient_prop['subclient']['object']

            self._server_tc.log_step("""Step 1)
                                        Randomly Choose from two factors relative time
                                        (first,second, third
                                        etc) and relative weekday (monday, tuesday, weekday etc)"""
                                     )

            relative_day = random.choice(list(schedulerconstants.RELATIVE_DAY.keys()))
            week_day = random.choice(list(schedulerconstants.WEEK_DAY.keys()))

            start_date, start_time = self._schedule_creator.add_minutes_to_datetime(
                self.cs_machine_obj.current_time(), 10)

            self._server_tc.log_step("""Step 2)
                                        Create a Monthly schedule for a subclient backup with the
                                        randomly chosen factors to run once a month"""
                                     )

            sch_obj = self._schedule_creator.create_schedule('subclient_backup',
                                                             schedule_pattern={
                                                                 'freq_type': 'Monthly_Relative',
                                                                 'active_start_date':
                                                                     start_date,
                                                                 'active_start_time':
                                                                     start_time,
                                                                 'relative_time': relative_day,
                                                                 'relative_weekday': week_day,
                                                                 'time_zone': 'UTC'
                                                             },
                                                             subclient=_subclient_obj,
                                                             backup_type="Full",
                                                             wait=False)

            sch_helper = schedulerhelper.SchedulerHelper(sch_obj, self.commcell)
            sch_helper.next_job_wait(2)
            self._schedule_creator.cleanup_schedules()

        except Exception as excp:
            self._server_tc.fail(excp)

        finally:
            self._schedule_creator.cleanup()
