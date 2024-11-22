# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case to verify replicate now option in monitor page

Sample input:
"58768": {
            "tenant_username": "tenant\\admin",
            "tenant_password": "password",
            "group_name" : "group_name",
            "vms" : [],
       }

"""
from DROrchestration.replication import Replication
from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.DR.group_details import ReplicationDetails
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """Test case to verify replicate now option"""
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        CVTestCase.__init__(self)
        self.name = "Mark For Full Replication Validation"

        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "group_name": None,
            "vms": [],
        }

        self.utils = None
        self.group_name = None
        self.vms = None

        self.admin_console = None
        self.replication_group = None
        self.group_details = None
        self.replication_helper = None

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
            self.vms = self.tcinputs['vms']

            self.replication = Replication(self.commcell, self.group_name)

            self.replication.source_auto_instance.power_on_proxies(
                self.replication.source_auto_instance.proxy_list)
            self.replication.destination_auto_instance.power_on_proxies(
                self.replication.destination_auto_instance.proxy_list)

            self.replication.power_on_vms(source=True)

        except Exception as exp:
            raise CVTestCaseInitFailure(
                f'Failed to initialise testcase {str(exp)}')

    @test_step
    def mark_for_full_replication_validation(self, after_operation=False):
        """ Validations before/after marking for Full Replication"""
        if after_operation:
            self.replication.post_validation(
                job_type='FULL', validate_test_data=True, test_data=False)
        else:
            self.replication.pre_validation()

    @test_step
    def perform_mark_for_full(self):
        """Perform Mark for Full followed by Replicate Now operation"""
        self.login()
        operation_status = self.replication_helper.perform_mark_for_full_replication(self.group_name, vms=self.vms,
                                                                                     operation_level=ReplicationHelper
                                                                                     .Operationlevel.OVERVIEW)
        if not all(operation_status):
            raise CVTestStepFailure(
                f"Mark for Full Replication Operation was NOT successful on all VMs")

        sleep(10)

        job_ids = self.replication_helper.perform_replicate_now(self.group_name, vms=self.vms,
                                                                operation_level=ReplicationHelper
                                                                .Operationlevel.OVERVIEW)
        self.logout()

        self.log.info('Waiting for replication job ID(s) [%s]', job_ids)
        for job in job_ids:
            replication_job = self.commcell.job_controller.get(job)
            replication_job.wait_for_completion()
            self.utils.assert_comparison(replication_job.status, 'Completed')

    def run(self):
        """Starting test case steps"""
        try:
            self.mark_for_full_replication_validation(after_operation=False)
            self.perform_mark_for_full()
            self.mark_for_full_replication_validation(after_operation=True)
        except Exception as err:
            self.utils.handle_testcase_exception(err)

    def tear_down(self):
        """Tears down the TC"""
        try:
            self.logout()
        except Exception as _exception:
            self.log.error(_exception)
