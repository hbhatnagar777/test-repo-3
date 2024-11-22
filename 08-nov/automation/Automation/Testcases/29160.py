# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Test cases to validate ondemand and schedule jobs when activity control is disabled at client level

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                   --  initialize TestCase class

     run()                        --  run function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities, OptionsSelector
from Server.serverhelper import ServerTestCases
from Server.Scheduler import schedulerhelper
from Server.JobManager.jobmanager_helper import JobManager
from Server.ActivityControl import activitycontrolhelper
from AutomationUtils.idautils import CommonUtils


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Acceptance]:Validate backup,restore jobs when activity disabled client level"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.tcinputs = {
            "SecondClientName": None,
        }

    def run(self):
        """Run function of this test case"""
        try:
            self._log.info("Started executing {0} testcase".format(self.id))
            entities = CVEntities(self)
            server_tc = ServerTestCases(self)
            job_object = JobManager(commcell=self.commcell)
            ida_utils = CommonUtils(self)
            object_acivity = activitycontrolhelper.ActivityControlHelper(self)
            object_schedule = schedulerhelper.ScheduleCreationHelper(self)
            options_selector = OptionsSelector(self.commcell)
            subclient1_name = OptionsSelector.get_custom_str('subclient', '29160_1')
            subclient2_name = OptionsSelector.get_custom_str('subclient', '29160_2')
            # Creating SubClient on Client1
            subclient1_props = entities.create({'subclient': {'name': subclient1_name}})
            _object1 = subclient1_props['subclient']['object']
            # Create SubClient on Client2
            subclient2_props = entities.create({'subclient': {'name': subclient2_name,
                                                'client': self.tcinputs["SecondClientName"]}})
            _object2 = subclient2_props['subclient']['object']
            host_name = self._client.client_hostname
            job_list = []
            _wait_secs = 30

            server_tc.log_step(
                        """
                        Test Case
                        1. Enable option "Queue Jobs if activity is disabled",
                            from Control panel --> Job Manager,
                        2. Disable Backup and Restore Activity Control at any Client level
                            2.1. Start OnDemand / Scheduled Backup and Restore for this Client-1
                            2.2  Start Backup and Restore for other Client-2,
                            for which Activity Control is not Disabled
                            2.3 Enable Activity Control at Client-1
                        """, 200
                        )
            server_tc.log_step("""Step 1)
                                        Enable option "Queue Jobs if activity is disabled
                                        from Control panel --> Job Manager""")
            ida_utils.modify_additional_settings('JobsCompleteIfActivityDisabled', '1')
            server_tc.log_step("""Step 2)
                                        Disable Backup and Restore Activity at Client level""")
            object_acivity.modify_activity('backup', self.client, 'disable')
            object_acivity.modify_activity('restore', self.client, 'disable')
            server_tc.log_step("""Step 2.1)
                                        Start OnDemand Backup on Client1 and client2""")
            job_object.job = ida_utils.subclient_backup(_object1, "FULL", wait=False)
            job_list.append(job_object.job)
            job_object.check_job_status(host_name,
                                        _object1,
                                        self.client.client_name,
                                        entity_name='client',
                                        backup=True,
                                        client_1=True)
            job_object.job = ida_utils.subclient_backup(_object2, "FULL", wait=False)
            job_list.append(job_object.job)
            job_object.check_job_status(host_name,
                                        _object2,
                                        self.tcinputs["SecondClientName"],
                                        entity_name='client',
                                        backup=True,
                                        client_1=False)
            object_acivity.modify_activity('backup', self.client, 'enable')
            for _job in job_list:
                job_object.job = _job
                job_object.wait_for_state('completed')
            server_tc.log_step("""Step 2.2)
                                        Start OnDemand restore on Client1 and client2""")
            job_list.clear()
            job_object.job = ida_utils.subclient_restore_in_place(_object1.content,
                                                                  _object1,
                                                                  wait=False)
            job_list.append(job_object.job)
            job_object.check_job_status(host_name,
                                        _object1,
                                        self.client.client_name,
                                        entity_name='client',
                                        backup=False,
                                        client_1=True)
            job_object.job = ida_utils.subclient_restore_in_place(_object2.content,
                                                                  _object2,
                                                                  False)
            job_list.append(job_object.job)
            job_object.check_job_status(host_name,
                                        _object2,
                                        self.tcinputs["SecondClientName"],
                                        entity_name='client',
                                        backup=False,
                                        client_1=False)
            object_acivity.modify_activity('restore', self.client, 'enable')
            for _job in job_list:
                job_object.job = _job
                job_object.wait_for_state('completed')
            server_tc.log_step("""Step 2.3)
                                        start schedule backup , restore on client1""")
            object_acivity.modify_activity('backup', self.client, 'disable')
            object_acivity.modify_activity('restore', self.client, 'disable')
            job_list.clear()
            schedule_obj = object_schedule.create_schedule('subclient_backup',
                                                           schedule_pattern={
                                                                     'freq_type': 'One_time',
                                                                     'active_start_date':
                                                                     object_schedule.
                                                                     add_minutes_to_datetime()[0],
                                                                     'active_start_time':
                                                                     object_schedule.
                                                                     add_minutes_to_datetime()[1],
                                                                     'time_zone': 'UTC'},
                                                           wait=False,
                                                           subclient=_object1,
                                                           backup_type='Full')
            scheduler_helper_obj = schedulerhelper.SchedulerHelper(schedule_obj, self.commcell)
            job_obj = scheduler_helper_obj.check_job_for_taskid(retry_count=10, retry_interval=40)
            job_object.job = job_obj[0]
            job_list.append(job_object.job)
            options_selector.sleep_time(_wait_secs)
            job_object.check_job_status(host_name,
                                        _object1,
                                        self.client.client_name,
                                        entity_name='client',
                                        backup=True,
                                        client_1=True)
            schedule_obj = object_schedule.create_schedule('subclient_restore_in_place',
                                                           schedule_pattern={
                                                                     'freq_type': 'One_time',
                                                                     'active_start_date':
                                                                     object_schedule.
                                                                     add_minutes_to_datetime()[0],
                                                                     'active_start_time':
                                                                     object_schedule.
                                                                     add_minutes_to_datetime()[1],
                                                                     'time_zone': 'UTC'},
                                                           wait=False,
                                                           subclient=_object1,
                                                           paths=_object1.content)
            scheduler_helper_obj = schedulerhelper.SchedulerHelper(schedule_obj, self.commcell)
            job_obj = scheduler_helper_obj.check_job_for_taskid(retry_count=10, retry_interval=40)
            job_object.job = job_obj[0]
            job_list.append(job_object.job)
            options_selector.sleep_time(_wait_secs)
            job_object.check_job_status(host_name,
                                        _object1,
                                        self.client.client_name,
                                        entity_name='client',
                                        backup=False,
                                        client_1=True)

            object_acivity.modify_activity('backup', self.client, 'enable')
            object_acivity.modify_activity('restore', self.client, 'enable')
            for _job in job_list:
                job_object.job = _job
                job_object.wait_for_state('completed')

        except Exception as exp:
            server_tc.fail(exp)
        finally:
            object_acivity.complete_job_with_activity_enable(job_list, _wait_secs)
            entities.cleanup()
