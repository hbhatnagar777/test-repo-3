# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Testcase: This test case verifies the feature VMware reverse replication

TestCase: Class for executing this test case
Sample JSON: {
        "tenant_username": <username>,
        "tenant_password": <password>,
        "group_name": "Group_1"
}
"""
from AutomationUtils.cvtestcase import CVTestCase
from DROrchestration import ReverseReplication
from Reports.utils import TestCaseUtils
from Web.AdminConsole.DR.monitor import ReplicationMonitor
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()
    _RPO_HOURS = 5

    def __init__(self):
        """Initialises the objects and TC inputs"""
        CVTestCase.__init__(self)
        self.name= "VMware: Validate reverse replication"

        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "group_name": None
        }

        self.utils = None
        self.group_name = None

        self.admin_console = None
        self.monitor = None

        self.reverse_replication = None
        self.reverse_schedule = None

    def login(self):
        """Logs in to admin console"""
        self.admin_console = AdminConsole(BrowserFactory().create_browser_object().open(),
                                          machine=self.inputJSONnode
                                          ['commcell']['webconsoleHostname'])
        self.admin_console.login(self.tcinputs['tenant_username'],
                                 self.tcinputs['tenant_password'])

        self.monitor = ReplicationMonitor(self.admin_console)

    def logout(self):
        """Logs out of the admin console and closes the browser"""
        self.admin_console.logout_silently(self.admin_console)
        self.admin_console.browser.close_silently(self.admin_console.browser)

    def setup(self):
        """Sets up the Testcase"""
        try:
            self.utils = TestCaseUtils(self)
            self.group_name = self.tcinputs['group_name']

            self.reverse_replication = ReverseReplication(self.commcell, self.group_name)
            self.reverse_replication.refresh(hard_refresh=True)
            self.reverse_replication.power_on_vms(source=False)
            self.reverse_replication.power_off_vms(source=True)
        except Exception as exp:
            raise CVTestCaseInitFailure(f'Failed to initialise testcase {str(exp)}')

    @test_step
    def enable_reverse_replication(self):
        """Enables the reverse replication in the replication monitor"""
        self.admin_console.navigator.navigate_to_replication_monitor()
        self.monitor.enable_reverse_replication(self.reverse_replication.vm_list[0], self.group_name)

    @test_step
    def verify_reverse_replication_configuration(self):
        """Verifies that the schedule exists with the correct RPO and UI shows it too"""
        self.admin_console.refresh_page()
        edit_schedule = self.monitor.reverse_replication_schedule(self.reverse_replication.vm_list[0],
                                                                  self.group_name)
        reverse_schedule_name = edit_schedule.get_schedule_name()
        schedule_frequency = edit_schedule.get_repeat_frequency()
        self.utils.assert_comparison(schedule_frequency, f'{self._RPO_HOURS} hours,0 minutes')
        edit_schedule.cancel()

        self.reverse_schedule = self.commcell.schedules.get(reverse_schedule_name)
        self.utils.assert_comparison(self.reverse_schedule._pattern['freq_subday_interval'],
                                     self._RPO_HOURS * 3600)

    @test_step
    def verify_reverse_sync_completion(self):
        """Verifies that the reverse sync job has completed"""
        # TODO: Trigger using Command center
        reverse_sync_job_id = self.reverse_schedule.run_now()
        job_obj = self.commcell.job_controller.get(reverse_sync_job_id)
        self.log.info('Waiting for reverse replication job ID [%s]', reverse_sync_job_id)
        job_obj.wait_for_completion()
        self.utils.assert_comparison(job_obj.status, 'Completed')
        self.reverse_replication.job_phase_validation(reverse_sync_job_id)

    @test_step
    def verify_monitor_status(self):
        """Verifies that the monitor shows the right status"""
        self.admin_console.navigator.navigate_to_replication_monitor()
        vm_details = self.monitor.get_replication_group_details(self.reverse_replication.vm_list[0], self.group_name)

        self.utils.assert_comparison(vm_details['Status'], ['Reverse replication enabled'])
        self.utils.assert_comparison(vm_details['Failover status'], ['Failover complete'])

    @test_step
    def verify_delete_reverse_replication(self):
        """
        Deletes the reverse replication, verifies monitor status and verifies schedule deletion
        """
        edit_schedule = self.monitor.reverse_replication_schedule(self.reverse_replication.vm_list[0], self.group_name)
        edit_schedule.delete()

        self.commcell.schedules.refresh()
        if self.commcell.schedules.has_schedule(schedule_name=self.reverse_schedule.schedule_name):
            raise CVTestStepFailure(f'Reverse replication schedule '
                                    f'[{self.reverse_schedule.schedule_name}] still exists after '
                                    f'schedule deletion from command center')
        vm_details = self.monitor.get_replication_group_details(self.reverse_replication.vm_list[0], self.group_name)
        self.utils.assert_comparison(vm_details['Status'], ['Sync disabled'])
        self.utils.assert_comparison(vm_details['Failover status'], ['Failover complete'])

    def run(self):
        """Runs the testcase in order"""
        try:
            self.login()
            self.enable_reverse_replication()
            self.verify_reverse_replication_configuration()
            self.logout()

            self.reverse_replication.pre_validation()
            self.verify_reverse_sync_completion()
            self.reverse_replication.post_validation()

            self.login()
            self.verify_monitor_status()
            self.verify_delete_reverse_replication()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tears down the TC"""
        try:
            self.logout()
        except:
            pass
