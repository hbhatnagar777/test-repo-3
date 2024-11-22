# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Testcase: DR Orchestration: Test-boot validations

TestCase: Class for executing this test case
Sample JSON: {
        "tenant_username": <username>,
        "tenant_password": <password>,
        "group_name": "group_1",
}
"""

from AutomationUtils.cvtestcase import CVTestCase
from DROrchestration.test_boot import TestBoot
from Reports.utils import TestCaseUtils
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.DR.group_details import ReplicationDetails
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper
from Web.AdminConsole.DR.monitor import ReplicationMonitor
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """This class is used to automate Test-boot of Zeal Automation"""
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        CVTestCase.__init__(self)
        self.name = "DR Operation: Test Boot validations"
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
        self.replication_monitor = None
        self.testboot = None

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
        self.replication_monitor = ReplicationMonitor(self.admin_console)

    def logout(self):
        """Logs out of the admin console and closes the browser"""
        self.admin_console.logout_silently(self.admin_console)
        self.admin_console.browser.close_silently(self.admin_console.browser)

    def setup(self):
        """Sets up the Testcase"""
        try:
            self.utils = TestCaseUtils(self)
            self.group_name = self.tcinputs['group_name']
            self.testboot = TestBoot(self.commcell, self.group_name)

        except Exception as exp:
            raise CVTestCaseInitFailure(f'Failed to initialise testcase {str(exp)}')

    @test_step
    def testboot_validation(self, after_operation=False):
        """ Validations before/after the Test boot"""
        if (self.testboot.destination_auto_instance.vsa_instance
                .instance_name.lower() not in ['vmware', 'hyper-v']):
            raise CVTestCaseInitFailure('Hypervisor not in Vmware and Hyper-V')

        if after_operation:
            self.testboot.post_validation()
        else:
            self.testboot.pre_validation()

    @test_step
    def perform_testboot_operation(self):
        """Perform the test boot operation from monitor level"""
        self.login()
        self.admin_console.navigator.navigate_to_replication_monitor()
        job_id = self.replication_monitor.test_boot_vm(self.testboot.vm_list, self.group_name)
        job_obj = self.commcell.job_controller.get(job_id)
        self.logout()

        self.log.info('Waiting for Job [%s] to complete', job_id)
        job_obj.wait_for_completion()
        self.utils.assert_comparison(job_obj.status, 'Completed')
        self.testboot.job_phase_validation(job_id)
        self.log.info('Successfully validated phases for Job : [%s]', job_id)

    def run(self):
        """Runs the testcase in order"""
        try:
            self.testboot_validation(after_operation=False)
            self.perform_testboot_operation()
            self.testboot_validation(after_operation=True)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tears down the TC"""
        try:
            self.logout()
        except Exception as _exception:
            self.log.error(_exception)
