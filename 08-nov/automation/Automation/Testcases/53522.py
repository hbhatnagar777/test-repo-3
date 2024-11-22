# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Testcase: This test case verifies whether replication job kill produces the needed sync state on the
admin console and then verifies whether the destination VM has been cleaned up on the destination hypervisor

Sample JSON: {
    "tenant_username": <username>,
    "tenant_password": <password>,
    "group_name": "Group_1"
}
"""
import time

from AutomationUtils.cvtestcase import CVTestCase
from DROrchestration.replication import Replication
from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """This class is used to automate the replication job kill"""
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        super().__init__()
        self.name = "Verify that cleanup is perform on the destination and status is set to " + \
                    "“Need Sync” when full VM replication Failed/Killed."
        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "group_name": None,
        }
        self.utils = None

        self.group_name = None

        self.admin_console = None
        self.replication_group = None
        self.replication = None

    def login(self):
        """Logs in to admin console"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                                          self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(self.tcinputs['tenant_username'],
                                 self.tcinputs['tenant_password'])

        self.replication_helper = ReplicationHelper(self.commcell,
                                                    self.admin_console)

        self.replication_group = ReplicationGroup(self.admin_console)

    def logout(self):
        """Logs out of the admin console and closes the browser"""
        self.admin_console.logout_silently(self.admin_console)
        self.admin_console.browser.close_silently(self.admin_console.browser)

    def setup(self):
        """Sets up the Testcase"""
        try:
            self.utils = TestCaseUtils(self)
            self.group_name = self.tcinputs['group_name']
            self.replication = Replication(self.commcell,
                                           replication_group=self.group_name)

            self.replication.source_auto_instance.power_on_proxies(
                self.replication.source_auto_instance.proxy_list)
            self.replication.destination_auto_instance.power_on_proxies(
                self.replication.destination_auto_instance.proxy_list)

        except Exception as exp:
            raise CVTestCaseInitFailure('Failed to initialise testcase') from exp

    @test_step
    def verify_replication_job_kill(self):
        """
        Mark all VMs in replication group for Full replication and then trigger replicate now
        for group and kill replication job
        """
        self.replication_helper.perform_mark_for_full_replication(replication_group=self.group_name,
                                                                  vms=self.replication.vm_list,
                                                                  operation_level=ReplicationHelper.Operationlevel.MONITOR)

        self.admin_console.refresh_page()
        replication_job_ids = self.replication_helper.perform_replicate_now(replication_group=self.group_name,
                                                                           operation_level=ReplicationHelper.Operationlevel.GROUP)
        replication_job = self.commcell.job_controller.get(replication_job_ids[0])

        # wait for 10 minutes to let sync start for VM
        for _ in range(40):
            events = replication_job.get_events()
            for event in events:
                if event.get('eventCodeString') == "91:235":
                    replication_job.kill(wait_for_job_to_kill=True)
                    break
            if replication_job.status.lower() == "killed":
                break
            self.log.info('Waiting for 15 seconds to let sync start for VM')
            time.sleep(15)
        else:
            if replication_job.status.lower() == "completed":
                raise Exception("Replication job completed, but couldn't be killed in time")
            else:
                raise Exception("Could not kill replication job even after 5 minutes of waiting")

        self.log.info('Waiting for 2 minutes to let replication monitor update')
        time.sleep(120)
        for vm_pair_dict in self.replication.vm_pairs.values():
            replication = list(vm_pair_dict.values())[0]
            replication.refresh()

            if replication.vm_pair.status != 'NEEDS_SYNC':
                raise Exception(f"The VM [{replication.vm_pair}] does not have 'Sync pending' status")
            if (self.replication.destination_auto_instance.hvobj
                    .check_vms_exist([replication.destination_vm.vm.vm_name])):
                raise Exception(f"The VM name [{replication.destination_vm.vm.vm_name}] exists on destination "
                                f"hypervisor even after replication job "
                                f"[{replication.vm_pair.last_replication_job}] kill")

    def run(self):
        """Runs the testcase in order"""
        try:
            self.login()
            self.verify_replication_job_kill()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Cleans up the testcase"""
        self.logout()
