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
    """Class for executing Testcase to verify Daily Data Aging, Download software schedules"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Data aging and Download Software Schedule - Daily"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.SCHEDULEANDSCHEDULEPOLICY
        self.show_to_user = False

    def setup(self):
        """Setup function of this test case"""
        self._server_tc = ServerTestCases(self)
        self._entities = CVEntities(self)
        self._schedule_creator = schedulerhelper.ScheduleCreationHelper(self)

    def run(self):
        """Main function for test case execution"""

        try:

            self._server_tc.log_step(
                """
                            Test Case
                            1. Creates a Daily Data aging, Download software schedule
                            2. checks whether the respective job got triggered for schedule
                """, 200)

            self._server_tc.log_step("""Step 1)
                                        Create Daily Data aging Schedule and wait for Job to trigger""")

            self._schedule_creator.create_schedule('data_aging',
                                                   schedule_pattern={
                                                       'freq_type': 'Daily',
                                                       'active_start_date': self._schedule_creator.
                                                       add_minutes_to_datetime()[0],
                                                       'active_start_time': self._schedule_creator.
                                                       add_minutes_to_datetime()[1],
                                                       'time_zone': 'UTC'},
                                                   )

            self._server_tc.log_step("""Step 2)
                            Create Daily Download Software
                            Schedule and wait for Job to trigger""")

            self._schedule_creator.create_schedule('download_software',
                                                   schedule_pattern={
                                                       'freq_type': 'Daily',
                                                       'active_start_date': self._schedule_creator.
                                                       add_minutes_to_datetime()[0],
                                                       'active_start_time': self._schedule_creator.
                                                       add_minutes_to_datetime()[1],
                                                       'time_zone': 'UTC'},
                                                   )

        except Exception as excp:
            self._server_tc.fail(excp)

        finally:
            self._schedule_creator.cleanup_schedules()
