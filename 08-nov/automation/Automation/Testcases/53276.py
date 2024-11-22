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

from dateutil.relativedelta import relativedelta
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities
from AutomationUtils.machine import Machine
from Server.Scheduler import schedulerhelper
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing Daily Schedule with End time specified"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Schedule] - Daily - \"End by <timestamp>\" and \"End after <n times>\""
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
                            1) Create a Daily Schedule with repeat every 1 day and end date as the
                            third day from the current day for a full backup job on any subclient
                            2) Create a Daily Schedule with repeat every 1 day
                            and end after 2 times.
                            """, 200
            )

            self.cs_machine_obj.toggle_time_service()

            # Creating subclient entity on test case client
            subclient_prop = self._schedule_creator.entities_setup(self)
            _subclient_obj = subclient_prop['subclient']['object']

            self._server_tc.log_step("""Step 1)
                            Create Daily Full Backup Schedule with active end date on the third
                            day from current date""")

            start_date, start_time = self._schedule_creator.add_minutes_to_datetime(
                self.cs_machine_obj.current_time(), 10)

            sch_obj = self._schedule_creator.create_schedule('subclient_backup',
                                                             schedule_pattern={
                                                                 'freq_type': 'Daily',
                                                                 'active_start_date':
                                                                     start_date,
                                                                 'active_start_time':
                                                                     start_time,
                                                                 'active_end_date':
                                                                     (self.cs_machine_obj.
                                                                      current_time()
                                                                      + relativedelta(days=2)).
                                                                     strftime('%m/%d/%Y'),
                                                                 'time_zone': 'UTC'
                                                             },
                                                             subclient=_subclient_obj,
                                                             backup_type="Full",
                                                             wait=False)

            sch_helper = schedulerhelper.SchedulerHelper(sch_obj, self.commcell)
            sch_helper.next_job_wait(4)
            self._schedule_creator.cleanup_schedules()

            self._server_tc.log_step("""Step 2)
                                        Create Daily Inc Backup Schedule with end after 2 times""")
            start_date, start_time = self._schedule_creator.add_minutes_to_datetime(
                self.cs_machine_obj.current_time(), 10)

            sch_obj = self._schedule_creator.create_schedule('subclient_backup',
                                                             schedule_pattern={
                                                                 'freq_type': 'Daily',
                                                                 'active_start_date':
                                                                     start_date,
                                                                 'active_start_time':
                                                                     start_time,
                                                                 'end_after': 2,
                                                                 'time_zone': 'UTC'
                                                             },
                                                             subclient=_subclient_obj,
                                                             wait=False)

            sch_helper = schedulerhelper.SchedulerHelper(sch_obj, self.commcell)
            sch_helper.next_job_wait(3)
            self._schedule_creator.cleanup_schedules()

        except Exception as excp:
            self._server_tc.fail(excp)

        finally:
            self._schedule_creator.cleanup()
