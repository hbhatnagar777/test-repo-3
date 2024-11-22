# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Testcase: DR Orchestration: Planned Failover and Failback validations

TestCase: Class for executing this test case
Sample JSON: {
    "tenant_username": <username>,
    "tenant_password": <password>,
    "group_name": "Group_1"
}
"""

from DROrchestration import PlannedFailover, Failback

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.DR.group_details import ReplicationDetails
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """This class is used to automate phase 3 of Zeal Automation"""
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        CVTestCase.__init__(self)
        self.name = "DR Orchestration: Planned Failover and Failback validations"
        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "group_name": None,
        }

        self.utils = None
        self.group_name = None

        self.admin_console = None
        self.replication_group = None
        self.group_details = None
        self.replication_helper = None

        self.planned_failover = None
        self.failback = None

    def login(self):
        """Logs in to admin console"""
        self.admin_console = AdminConsole(BrowserFactory().create_browser_object().open(),
                                          machine=self.inputJSONnode
                                          ['commcell']['webconsoleHostname'])
        self.admin_console.login(self.tcinputs['tenant_username'],
                                 self.tcinputs['tenant_password'])

        self.replication_group = ReplicationGroup(self.admin_console)
        self.group_details = ReplicationDetails(self.admin_console)
        self.replication_helper = ReplicationHelper(self.commcell, self.admin_console)

    def logout(self):
        """Logs out of the admin console and closes the browser"""
        self.admin_console.logout_silently(self.admin_console)
        self.admin_console.browser.close_silently(self.admin_console.browser)

    def setup(self):
        """Sets up the Testcase"""
        try:
            self.utils = TestCaseUtils(self)
            self.group_name = self.tcinputs['group_name']
            self.planned_failover = PlannedFailover(self.commcell, self.group_name)
            self.failback = Failback(self.commcell, self.group_name)

            self.planned_failover.source_auto_instance.power_on_proxies(
                self.planned_failover.source_auto_instance.proxy_list)
            self.planned_failover.destination_auto_instance.power_on_proxies(
                self.planned_failover.destination_auto_instance.proxy_list)

            self.planned_failover.power_on_vms(source=True)
            self.planned_failover.refresh(hard_refresh=True)
            self.failback.refresh(hard_refresh=True)
        except Exception as exp:
            raise CVTestCaseInitFailure('Failed to initialise testcase') from exp

    @test_step
    def planned_failover_validation(self, after_operation=False):
        """ Validations before/after the planned failover"""
        if after_operation:
            self.planned_failover.post_validation()
        else:
            self.planned_failover.pre_validation()

    @test_step
    def perform_failover(self, retain_blob=True):
        """Perform the planned failover operation for all VMs in group"""
        self.login()
        job_id = self.replication_helper.perform_planned_failover(self.group_name, retain_blob, vms=None,
                                                                  operation_level=ReplicationHelper
                                                                  .Operationlevel.GROUP)
        self.logout()

        self.log.info('Waiting for group level planned failover job ID [%s]', job_id)
        failover_job = self.commcell.job_controller.get(job_id)
        failover_job.wait_for_completion()
        self.utils.assert_comparison(failover_job.status, 'Completed')
        self.planned_failover.job_phase_validation(job_id)

    @test_step
    def failback_validations(self, after_operation=False):
        """ Validations before/after the failback"""
        if not self.failback.is_failback_supported():
            return
        if after_operation:
            self.failback.post_validation()
        else:
            self.failback.pre_validation()

    @test_step
    def perform_failback(self):
        """Perform the failback operation for all VMs in group"""
        if self.failback.is_failback_supported():
            # Perform failback on VMs if they are not cross hypervisor to hyper-v
            self.login()
            job_id = (self.replication_helper
                      .perform_failback(self.group_name,
                                        operation_level=ReplicationHelper.Operationlevel.GROUP))
            self.logout()

            self.log.info('Waiting for failback job ID [%s]', job_id)
            failback_job = self.commcell.job_controller.get(job_id)
            failback_job.wait_for_completion()
            self.utils.assert_comparison(failback_job.status, 'Completed')
            self.failback.job_phase_validation(failback_job.job_id)
        else:
            # Undo failover on VMs if they are hyper-v
            self.login()
            job_id = (self.replication_helper
                      .perform_undo_failover(self.group_name,
                                             operation_level=ReplicationHelper.Operationlevel.GROUP))
            self.logout()

            self.log.info('Waiting for group level failback job ID [%s]', job_id)
            undo_failover_job = self.commcell.job_controller.get(job_id)
            undo_failover_job.wait_for_completion()
            self.utils.assert_comparison(undo_failover_job.status, 'Completed')

    def run(self):
        """Runs the testcase in order"""
        try:
            self.planned_failover_validation(after_operation=False)
            self.perform_failover()
            self.planned_failover_validation(after_operation=True)

            self.failback_validations(after_operation=False)
            self.perform_failback()
            self.failback_validations(after_operation=True)
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tears down the TC"""
        try:
            self.logout()
            self.planned_failover.cleanup_testdata()
            self.failback.cleanup_testdata()
            self.planned_failover.power_off_vms(source=False)
        except Exception as _exception:
            self.log.error(_exception)
