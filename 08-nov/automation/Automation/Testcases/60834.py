# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Testcase: This test case verifies that the VM deletion from replication monitor and replication group configuration works
Note: Please create a replication group with 1 VM pair for the specific configuration
TestCase: Class for executing this test case
Sample JSON: {
    "tenant_username": "tenant\\admin",
    "tenant_password": "tenantpwd",
    "group_name": "group_60834",
    "second_source_vm": "vm1"
}
"""
from AutomationUtils.cvtestcase import CVTestCase
from DROrchestration.replication import Replication
from DROrchestration.delete_vm import DeleteVM
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils import OptionsHelper
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.DR.group_details import ReplicationDetails
from DROrchestration.DRUtils.DRConstants import Vendors_Complete, Vendor_Instancename_Mapping
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep


class TestCase(CVTestCase):
    """This TC is used to verify VM deletion from replication monitor and replication group configuration"""
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        super(TestCase, self).__init__()
        self.name = "Delete VM from replication Monitor"

        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "group_name": None,
            "second_source_vm": None
        }
        self.utils = None

        self.group_name = None
        self.second_source_vm = None

        self.admin_console = None
        self.replication_helper = None
        self.replication_group = None
        self.group_details = None
        self.replication_monitor = None

        self.replication = None
        self.delete_vm = None
        self.view_mode = None

    def setup(self):
        """Sets up the Testcase"""
        try:
            self.utils = TestCaseUtils(self)

            self.group_name = self.tcinputs['group_name']
            self.second_source_vm : dict | list = self.tcinputs['second_source_vm']

            self.replication = Replication(self.commcell, self.group_name)
            self.delete_vm = DeleteVM(self.commcell, self.group_name)

            self.replication.source_auto_instance.power_on_proxies(
                self.replication.source_auto_instance.proxy_list)
            self.replication.destination_auto_instance.power_on_proxies(
                self.replication.destination_auto_instance.proxy_list)
        except Exception as exp:
            raise CVTestCaseInitFailure('Failed to initialise testcase') from exp

    def login(self):
        """Logs in to admin console"""
        self.admin_console = AdminConsole(BrowserFactory().create_browser_object().open(),
                                          machine=self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(self.tcinputs["tenant_username"],
                                 self.tcinputs["tenant_password"])

        self.replication_helper = ReplicationHelper(self.commcell, self.admin_console)
        self.replication_group = ReplicationGroup(self.admin_console)
        self.group_details = ReplicationDetails(self.admin_console)

    def logout(self):
        """Logs out of the admin console and closes the browser"""
        self.admin_console.logout_silently(self.admin_console)
        self.admin_console.browser.close_silently(self.admin_console.browser)

    @property
    def vendor_name(self):
        """Returns the name of the vendor for the source hypervisor"""
        source_instance_name = self.replication.source_auto_instance.get_instance_name()
        return Vendors_Complete[Vendor_Instancename_Mapping(source_instance_name).name].value

    @test_step
    def add_delete_vm_from_group(self):
        """Adds VM to group from configuration tab and then deletes it from configuration tab"""
        if self.vendor_name == 'VMware vCenter':
            self.view_mode = "VMs and templates"
        self.replication_helper.add_delete_vm_to_group_configuration(group_name=self.group_name,
                                                                     source_vm=self.second_source_vm,
                                                                     vendor_name=self.vendor_name,
                                                                     view_mode=self.view_mode)

    @test_step
    def add_delete_vm_from_monitor(self, delete_destination: bool = True):
        """Add VM from configuration and delete from monitor"""
        source_vms = self.second_source_vm if isinstance(self.second_source_vm, list) else list(self.second_source_vm.values())[0]

        # Adds the VM to group with default options and verify it exists on configuration tab and VM group content
        self.replication_helper.add_vm_to_group_configuration(group_name=self.group_name,
                                                              source_vm=self.second_source_vm,
                                                              vendor_name=self.vendor_name,
                                                              view_mode=self.view_mode)
        self.logout()

        backup_options = OptionsHelper.BackupOptions(self.replication.auto_subclient)
        backup_options.backup_type = "INCREMENTAL"
        self.replication.auto_subclient.backup(backup_options, skip_discovery=True, skip_backup_job_type_check=True)
        self.replication.get_running_replication_jobs()

        del self.delete_vm.vm_pairs
        self.delete_vm.vm_pairs = source_vms

        self.login()

        delete_job_id = self.replication_helper.delete_vm_from_monitor(group_name=self.group_name,
                                                                       source_vms=source_vms,
                                                                       delete_destination=delete_destination)
        self.logout()

        delete_job = self.commcell.job_controller.get(delete_job_id)
        if not delete_job.wait_for_completion():
            raise Exception(f"Delete job [{delete_job_id}] failed to complete")

        self.delete_vm.job_phase_validation(delete_job_id)
        self.delete_vm.post_validation(delete_job_id=delete_job_id, delete_vm_enabled=delete_destination)

    def run(self):
        """Runs the testcase in order"""
        try:
            self.login()
            self.add_delete_vm_from_group()

            self.add_delete_vm_from_monitor(delete_destination=False)

            self.login()
            self.add_delete_vm_from_monitor()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        self.logout()
