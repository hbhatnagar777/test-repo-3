# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Testcase: DR Orchestration: Test Failover validations

TestCase: Class for executing this test case
Sample JSON: {
    "tenant_username": None,
    "tenant_password": None,
    "group_name": "Group_1",
}
"""

from collections import defaultdict
from time import sleep
from DROrchestration import TestFailover

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
        self.name = "DR Orchestration: Test Failover validations"
        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "group_name": None
        }

        self.utils = None
        self.group_name = None
        self.source_vms = None

        self.admin_console = None
        self.replication_group = None
        self.group_details = None
        self.replication_helper = None
        self.cloned_vms = defaultdict(list)

        self.test_failover = None

    def login(self):
        """Logs in to admin console"""
        self.admin_console = AdminConsole(BrowserFactory().create_browser_object().open(),
                                          machine=self.inputJSONnode
                                          ['commcell']['webconsoleHostname'])
        self.admin_console.login(self.tcinputs['tenant_username'],
                                 self.tcinputs['tenant_password'])

        self.replication_group = ReplicationGroup(self.admin_console)
        self.group_details = ReplicationDetails(self.admin_console)
        self.replication_helper = ReplicationHelper(self.commcell,
                                                    self.admin_console)

    def logout(self):
        """Logs out of the admin console and closes the browser"""
        self.admin_console.logout_silently(self.admin_console)
        self.admin_console.browser.close_silently(self.admin_console.browser)

    def setup(self):
        """Sets up the Testcase"""
        try:
            self.utils = TestCaseUtils(self)
            self.group_name = self.tcinputs['group_name']

            self.test_failover = TestFailover(self.commcell, self.group_name)
            self.source_vms = self.test_failover.vm_list

            self.test_failover.source_auto_instance.power_on_proxies(
                self.test_failover.source_auto_instance.proxy_list)
            self.test_failover.destination_auto_instance.power_on_proxies(
                self.test_failover.destination_auto_instance.proxy_list)

        except Exception as exp:
            raise CVTestCaseInitFailure(
                f'Failed to initialise testcase {str(exp)}')

    def update_clone_details(self):
        self.view_test_failover_vms()
        self.test_failover.update_clone_details(self.cloned_vms)

    @test_step
    def view_test_failover_vms(self):
        """Views the Test Failover VMs"""
        self.login()
        self.cloned_vms = self.replication_helper.view_test_failover_vms(self.group_name,
                                                                         vms=self.source_vms,
                                                                         operation_level=ReplicationHelper.Operationlevel.GROUP)
        self.logout()

    @test_step
    def test_failover_validation(self, after_operation=False, post_expiration=False):
        """ Validations before/after the Test Failover"""
        self.update_clone_details()
        if after_operation:
            self.test_failover.post_validation(post_expiration=post_expiration)
        else:
            self.test_failover.pre_validation()

    @test_step
    def perform_test_failover(self):
        """Perform the Test Failover operation for all VMs in group"""
        self.login()
        job_ids = self.replication_helper.perform_test_failover(self.group_name, vms=self.source_vms,
                                                                operation_level=ReplicationHelper
                                                                .Operationlevel.GROUP)
        self.logout()

        self.log.info('Waiting for Test Failover job ID(s) [%s]', job_ids)
        for job in job_ids:
            # INFO : Job Phase validation -> Implemented in Post Validation
            test_failover_job = self.commcell.job_controller.get(job)
            test_failover_job.wait_for_completion()
            self.utils.assert_comparison(test_failover_job.status, 'Completed')

    @test_step
    def delete_test_failover_clones(self):
        """Deletes the cloned VMs"""
        self.login()
        self.replication_helper.delete_test_failover_clones(self.group_name,
                                                            source_vms=self.source_vms,
                                                            operation_level=ReplicationHelper.Operationlevel.GROUP)
        self.logout()

    def run(self):
        """Runs the testcase in order"""
        try:
            self.test_failover_validation(after_operation=False)
            self.perform_test_failover()
            self.test_failover_validation(after_operation=True, post_expiration=False)
            self.delete_test_failover_clones()
            self.test_failover_validation(after_operation=True, post_expiration=True)
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tears down the TC"""
        try:
            self.logout()
        except Exception as _exception:
            self.log.error(_exception)
