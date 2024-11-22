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
from Server.Scheduler import schedulerhelper, schedulerconstants
from Server.serverhelper import ServerTestCases


class TestCase(CVTestCase):
    """Class for executing REST APIs for agent operations"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Schedule] - Daily - All Backup Types & Restore Types"
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
                            1. Creates a Daily full, incremental, differential,
                               synth full backup schedule
                            2. checks whether the respective job got triggered for schedule
                            3. Creates a Daily restore in place schedule
                            4. Checks whether the job got triggered for this schedule
                            5.  Creates a Daily restore out of place schedule
                            6. Checks whether the job got triggered for this schedule
                """, 200)

            # Creating subclient entity on test case subclient
            subclient_prop = self._schedule_creator.entities_setup(self)
            _subclient_obj = subclient_prop['subclient']['object']
            _subclient_content = subclient_prop['subclient']['content']

            backup_types = schedulerconstants.SCHEDULE_BACKUP_TYPES

            for backup_type in backup_types:
                self._server_tc.log_step("""Step {0})
                            Create Daily {1} Backup Schedule and wait for Job to trigger"""
                                         .format(backup_types.index(backup_type) + 1, backup_type))

                self._schedule_creator.create_schedule('subclient_backup',
                                                       schedule_pattern={
                                                           'freq_type': 'Daily',
                                                           'active_start_date':
                                                           self._schedule_creator.
                                                           add_minutes_to_datetime()[0],
                                                           'active_start_time':
                                                           self._schedule_creator.
                                                           add_minutes_to_datetime()[1],
                                                           'time_zone': 'UTC'},
                                                       subclient=_subclient_obj,
                                                       backup_type=backup_type)

            self._server_tc.log_step("""Step 5)
                            Create Daily restore in place
                            Schedule and wait for Job to trigger""")

            self._schedule_creator.create_schedule('subclient_restore_in_place',
                                                   schedule_pattern={
                                                       'freq_type': 'Daily',
                                                       'active_start_date':
                                                       self._schedule_creator.
                                                       add_minutes_to_datetime()[0],
                                                       'active_start_time':
                                                       self._schedule_creator.
                                                       add_minutes_to_datetime()[1],
                                                       'time_zone': 'UTC'},
                                                   subclient=_subclient_obj,
                                                   paths=_subclient_content)

            self._server_tc.log_step("""Step 6)
                                        Create Daily restore out of place
                                        Schedule and wait for Job to trigger""")

            self._schedule_creator.create_schedule('subclient_restore_out_of_place',
                                                   schedule_pattern={
                                                       'freq_type': 'Daily',
                                                       'active_start_date':
                                                       self._schedule_creator.
                                                       add_minutes_to_datetime()[0],
                                                       'active_start_time':
                                                       self._schedule_creator.
                                                       add_minutes_to_datetime()[1],
                                                       'time_zone': 'UTC'},
                                                   subclient=_subclient_obj,
                                                   destination_path=_subclient_content[0] + r'\52994Restore',
                                                   paths=_subclient_content)

        except Exception as excp:
            self._server_tc.fail(excp)

        finally:
            self._schedule_creator.cleanup_schedules()
            self._entities.cleanup()
