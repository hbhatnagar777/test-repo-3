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

import calendar
from dateutil.relativedelta import relativedelta
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities
from AutomationUtils.machine import Machine
from Server.Scheduler import schedulerhelper
from Server.serverhelper import ServerTestCases



class TestCase(CVTestCase):
    """Class for executing Weekly Schedule with Repeat Pattern"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Schedule] - Daily Schedule with App_subclientnextruntime entry removal post data ageing job."
        self.applicable_os = self.os_list.LINUX
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
                            1) Create a One time Schedule on a subclient as Full Backup Job.""", 200)

            if not self.commcell.is_linux_commserv:
                self.cs_machine_obj.toggle_time_service()

            # Creating subclient entity on test case client
            subclient_prop = self._schedule_creator.entities_setup(self)
            _subclient_obj = subclient_prop['subclient']['object']

            self._server_tc.log_step("""Step 3)
                                        Creates a Full Backup one time schedule""")
            start_date, start_time = self._schedule_creator.add_minutes_to_datetime(
                self.cs_machine_obj.current_time(), 10)
            self.log.info(f"start date selected is {start_date}, start time is {start_date}, current machine time is {self.cs_machine_obj.current_time()}")
            sch_obj = self._schedule_creator.create_schedule('subclient_backup',
                                                             schedule_pattern={
                                                                 'freq_type': 'Daily',
                                                                 'active_start_date':
                                                                     start_date,
                                                                 'active_start_time':
                                                                     start_time,
                                                                 'time_zone': 'UTC',
                                                             },
                                                             subclient=_subclient_obj,
                                                             backup_type="Full",
                                                             wait=False)

            sch_helper = schedulerhelper.SchedulerHelper(sch_obj, self.commcell)
            sch_helper._utility.sleep_time(100)
            sch_helper.check_job_for_taskid()
            if sch_helper.jobs:
                self.log.info("Backup successful, for one time schedule.")
                sch_helper._utility.sleep_time(60)
            else:
                raise "One time Schedule did not trigger"

            self.log.info("The One-Time Schedule was triggered, starting post validation steps.")

            self._server_tc.log_step("""Delete the created subsclient and make sure that after running the data 
            ageing job the entry of this subclient is removed from the table.""")
            # Now we will Delete the subclient and will trigger a data ageing job.
            subclient_prop['subclient']['subclients'].delete(subclient_prop['subclient']['name'])
            self.log.info("The subclient deletion was successful, proceeding to run a data ageing job")
            self.commcell.run_data_aging()
            sch_helper._utility.sleep_time(150)
            self.log.info("Data ageing job successful, checking App_subclientnextruntime Table")
            self.log.info(f"Executing command [Select * from App_subclientnextruntime where subclientId = {subclient_prop['subclient']['id']}]")
            check = sch_helper._utility.exec_commserv_query(f"Select * from App_subclientnextruntime where subclientId = {subclient_prop['subclient']['id']}")
            if (len(check[0][0]) != 0):
                self._server_tc.fail("stale entry not cleared from table.")
            self._schedule_creator.cleanup_schedules()

        except Exception as excp:
            self._server_tc.fail(excp)


