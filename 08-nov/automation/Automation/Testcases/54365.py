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
from Server.Scheduler import schedulepolicyhelper
from Server.serverhelper import ServerTestCases
from cvpysdk.policies.schedule_policies import OperationType


class TestCase(CVTestCase):
    """Class for checking acceptance of schedule policy"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Schedule Policy] - Acceptance"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.SCHEDULEANDSCHEDULEPOLICY
        self._schedule_policy = None
        self.show_to_user = False
        self._server_tc = None
        self._entities = None
        self._options = None

    def setup(self):
        """Setup function of this test case"""
        self._server_tc = ServerTestCases(self)
        self._entities = CVEntities(self)
        self._schedule_policy = schedulepolicyhelper.SchedulePolicyHelper(self.commcell)
        self._options = OptionsSelector(self.commcell)

    def run(self):
        """Main function for test case execution"""

        try:

            self._server_tc.log_step(
                """
                            Test Case
                            1) Create a Data Protection Schedule Policy with a certain set of associatons and type and 
                               associate it to a Daily Schedule
                            2) Modify the schedule of the schedule policy by changing the pattern type to automatic 
                               and verify
                            3) Add a new schedule to the schedule policy
                            4) Modify the associations of the schedule policy by adding a new client
                            5) Modify the app group of the schedule policy by adding a new appGroup
                            6) Delete the newly added schedule from the schedule policy
                            7) Delete the schedule policy
                """, 200
            )

            clients = self._options.get_client('all', 2, False)

            client_association = [
                {
                    'clientName': clients[0]
                }
            ]

            client_schedule = [
                {
                    'pattern': {
                        'schedule_name': 'client_schedule',
                        'freq_type': 'Daily'
                    }
                }
            ]

            agent_type = [
                    {
                        "appGroupName": "Protected Files"
                    }
                ]


            self._schedule_policy.schedule_policy_obj = self._schedule_policy.create_schedule_policy(
                'test_SP_{0}'.format(self.id), 'Data Protection', client_association, client_schedule, agent_type)

            schedules_associated = self._schedule_policy.schedule_policy_obj.all_schedules

            self._schedule_policy.modify_schedule_of_policy({'pattern': {'freq_type': 'automatic'}},
                                                            schedule_name=schedules_associated[0].get('schedule_name'))

            self._schedule_policy.add_schedule_to_policy({
                'pattern':
                    {'schedule_name': 'client_schedule2'},
                'options':
                    {'backupLevel': 'Full'}})

            self._schedule_policy.modify_associations([{'clientName': clients[1]}], OperationType.INCLUDE)

            self._schedule_policy.modify_app_group([{'appGroupName': 'DB2'}], OperationType.INCLUDE)

            self._schedule_policy.delete_schedule_from_policy(schedule_name='client_schedule2')

            self._schedule_policy.delete_schedule_policy()


        except Exception as excp:
            self._server_tc.fail(excp)

        finally:
            if self._schedule_policy.schedule_policy_obj:
                self._schedule_policy.delete_schedule_policy()
