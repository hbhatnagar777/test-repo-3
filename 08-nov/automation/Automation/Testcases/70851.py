# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase: DR Orchestration: Conversion validation from hot site to warm site and vice versa

TestCase: Class for executing this test case
"70851": {
    "tenant_username": "<username>",
    "tenant_password": "<password>",
    "group_name": "hotsite_ReplicationGroup_name",
    "source_vms": "source vms list"  ->  e.g "source_vms": ["vm1", "vm2"]
}
"""
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import TestStep
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper
from Web.AdminConsole.DR.replication import ReplicationGroup
from DROrchestration.replication import Replication


class TestCase(CVTestCase):
    """This class is used to automate the conversion"""
    test_step = TestStep()

    def __init__(self):
        CVTestCase.__init__(self)
        self.name = "DR Orchestration: Conversion validation from hot site to warm site and vice versa"
        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "group_name": None,
            "source_vms": None
        }
        self.utils = None
        self.group_name = None
        self.source_vms = None
        self.admin_console = None
        self.navigator = None
        self.replication_group = None
        self.recovery_target = None
        self.target_details = None
        self.replication_helper = None
        self.proxies_destination = None
        self.replication = None

    def login(self):
        """Logs in to admin console"""
        self.admin_console = AdminConsole(BrowserFactory().create_browser_object().open(),
                                          machine=self.inputJSONnode
                                          ['commcell']['webconsoleHostname'])
        self.admin_console.login(self.tcinputs['tenant_username'],
                                 self.tcinputs['tenant_password'])
        self.navigator = self.admin_console.navigator
        self.replication_helper = ReplicationHelper(self.commcell, self.admin_console)
        self.replication_group = ReplicationGroup(self.admin_console)

    def logout(self):
        """Logs out of the admin console and closes the browser"""
        self.admin_console.logout_silently(self.admin_console)
        self.admin_console.browser.close_silently(self.admin_console.browser)

    def setup(self):
        """ Calls the super setup """
        self.utils = TestCaseUtils(self)
        self.group_name = self.tcinputs['group_name']
        self.source_vms = self.tcinputs["source_vms"]

    @test_step
    def check_hot_site(self):
        """Checks hot site group or not"""
        self.replication_group = self.commcell.replication_groups.get(self.group_name)
        if self.replication_group.is_warm_sync_enabled:
            raise Exception("Replication Group is warm-site convert to hot-site")
        self.log.info("Replication Group is hot-site")

    @test_step
    def check_warm_site(self):
        """Checks warm site group or not"""
        self.replication_group = self.commcell.replication_groups.get(self.group_name)
        if not self.replication_group.is_warm_sync_enabled:
            raise Exception("Replication Group is in hot-site")
        self.log.info("Replication Group is warm-site")

    @test_step
    def check_sync_status(self):
        """Checks sync status of VMs is "IN SYNC" before converting to warm site"""
        self.login()
        self.navigator.navigate_to_replication_groups()
        self.replication_group.access_group(self.group_name)
        self.replication_helper.verify_replication_monitor(group_name=self.group_name,
                                                           source_vms=self.source_vms)
        self.logout()

    @test_step
    def check_drvm_deletion(self):
        """Validate DR-VM is deleted after conversion"""
        self.replication = Replication(self.commcell, self.group_name)
        self.replication.refresh()
        for source in self.replication.vm_list:
            replication = self.replication.vm_pairs[source]['Replication']
            replication.validate_warm_sync()

    @test_step
    def convert_group_site(self, warm_site: bool = True):
        """ Converts the replication group to Warm/Hot Site group"""
        self.login()
        # Notification
        #   1. Job ID for Hot Site to Warm Site conversion (int)
        #   2. Success message for Warm Site to Hot Site conversion (str)
        notification: int or str = self.replication_helper.convert_group_site(group_name=self.group_name,
                                                                              warm_site=warm_site)

        if warm_site:
            self.log.info(f"Waiting for DRVM Cleanup job ID(s) [{notification}]")
            cleanup_job = self.commcell.job_controller.get(notification)
            cleanup_job.wait_for_completion()
            self.replication_helper.assert_comparison(cleanup_job.status, 'Completed')

        else:
            success_text = self.admin_console.props.get('message.conversionSuccessfulWarmToHot', '')
            self.replication_helper.assert_comparison(notification, success_text)
        self.logout()

    def run(self):
        """Runs the testcase in order"""
        try:
            self.check_sync_status()
            self.check_hot_site()
            self.convert_group_site(warm_site=True)  # hot to warm converison
            self.check_warm_site()
            self.check_drvm_deletion()
            self.convert_group_site(warm_site=False)  # warm to hot converison
            self.check_hot_site()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tears down the TC"""
        self.logout()
