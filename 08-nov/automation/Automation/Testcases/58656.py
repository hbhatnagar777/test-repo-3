# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
Testcase: This test case verifies whether whether VMware replications honors the VM folder, resource pool and the
source and destination network at the target

TestCase: Class for executing this test case
Sample JSON: {
        "ClientName": "vmwhyp",
        "source_vm": "vm",
        "recovery_target": "vmwtarget",
        "storage_name" : "storage",
        "resource_pool": None,
        "vm_folder": None,
        "source_network": None,
        "destination_network": None,
        "source_network_2": None,
        "destination_network_2": None,
        ""
}
"""
from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from DROrchestration.replication import Replication
from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.Helper.dr_helper import DRHelper, ReplicationHelper
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from DROrchestration.DRUtils.DRConstants import Vendors_Complete, ReplicationType, SiteOption, VendorViewModes
from Web.AdminConsole.DR.virtualization_replication import ConfigureVMWareVM, _VMwareVMOptions


class TestCase(CVTestCase):
    """This class is used to automate the VMware replication"""
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        CVTestCase.__init__(self)
        self.name = "Command Center: Live Sync: Honor VM folder, resource pool and N/W selected at the target."

        self.tcinputs = {
            "ClientName": None,
            "source_vm": None,
            "recovery_target": None,
            "primary_storage_name": None,
            "resource_pool": None,
            "vm_folder": None,
            "source_network": None,
            "destination_network": None,
            "source_network_2": None,
            "destination_network_2": None,
        }
        self.source_hypervisor = None
        self.source_vm = None
        self.recovery_target = None
        self.primary_storage_name = None
        self.resource_pool = None
        self.vm_folder = None
        self.source_network = None
        self.destination_network = None
        self.source_network_2 = None
        self.destination_network_2 = None

        self.utils = None

        self.browser = None
        self.admin_console = None
        self.replication_group = None
        self.replication_helper = None

        self.dr_helper = None

    @property
    def group_name(self):
        """Returns the virtualization group name"""
        return ReplicationHelper.group_name(self.id)

    def login(self):
        """Logs in to admin console"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, machine=self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.goto_adminconsole()
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.admin_console.wait_for_completion()

        self.replication_helper = ReplicationHelper(self.commcell, self.admin_console)
        self.replication_group = ReplicationGroup(self.admin_console)

    def logout(self):
        """Logs out of the admin console and closes the browser"""
        self.admin_console.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)

    def setup(self):
        """Sets up the Testcase"""
        try:
            self.utils = TestCaseUtils(self)
            self.source_hypervisor = self.tcinputs['ClientName']
            self.source_vm = self.tcinputs['source_vm']
            self.source_vm_input = sum(self.source_vm.values(), [])
            self.recovery_target = self.tcinputs['recovery_target']
            self.primary_storage_name = self.tcinputs['primary_storage_name']
            self.resource_pool = self.tcinputs['resource_pool']
            self.vm_folder = self.tcinputs['vm_folder']
            self.source_network = self.tcinputs['source_network']
            self.destination_network = self.tcinputs['destination_network']
            self.source_network_2 = self.tcinputs['source_network_2']
            self.destination_network_2 = self.tcinputs['destination_network_2']

            self._source_vendor = Vendors_Complete.VMWARE.value
            self._destination_vendor = Vendors_Complete.VMWARE.value
            self._replication_type = ReplicationType.Periodic
            self._siteoption = SiteOption.HotSite
            self.view_mode = VendorViewModes.VMWARE.VMs.value
            self._unconditionally_overwrite = True

            self.dr_helper = DRHelper(self.commcell, self.csdb, self.client)
        except Exception as exp:
            raise CVTestCaseInitFailure(f'Failed to initialise testcase {str(exp)}')

    @test_step
    def delete_replication_group(self):
        """Deletes the replication group if it exists already"""
        self.replication_helper.delete_replication_group(self.group_name, self.source_vm_input)

    @test_step
    def configure_replication_group(self):
        """Configures the replication group with default options"""
        self.admin_console.navigator.navigate_to_replication_groups()
        vmware_configure = self.replication_group.configure_virtualization(source_vendor=self._source_vendor,
                                                                           destination_vendor=self._destination_vendor,
                                                                           replication_type=self._replication_type.value)

        # Type Hinting
        vmware_configure: ConfigureVMWareVM

        vmware_configure.content.set_name(self.group_name)
        vmware_configure.content.select_production_site_hypervisor(self.source_hypervisor)
        vmware_configure.next()

        # Content
        vmware_configure.content.select_vm_from_browse_tree(self.source_vm, self.view_mode)
        vmware_configure.next()

        # Storage
        _storagecopy = vmware_configure.storage_cache.Storage_Copy
        vmware_configure.storage_cache.select_storage(self.primary_storage_name,
                                                      storage_copy=_storagecopy.Primary.value)
        vmware_configure.next()

        # Recovery Options
        vmware_configure.recovery_options.select_recovery_target(self.recovery_target)
        vmware_configure.recovery_options.select_rto(self._siteoption.value)
        vmware_configure.next()

        # TODO : Pre-Post Scripts (Configuration) if required
        vmware_configure.next()

        # Override Options
        override_vm = vmware_configure.override_options.override_vms(source_vm=self.source_vm_input[0])
        override_vm: _VMwareVMOptions
        override_vm.select_resource_pool(self.resource_pool)
        override_vm.set_vm_folder(self.vm_folder)

        override_vm.advance_options()
        network_settings = override_vm.edit_network()
        network_settings.select_source_network(self.source_network)
        network_settings.select_destination_network(self.destination_network)
        network_settings.save()

        network_settings = override_vm.add_network()
        network_settings.select_source_network(self.source_network_2)
        network_settings.select_destination_network(self.destination_network_2)
        network_settings.save()

        override_vm.save()
        vmware_configure.next()

        # TODO: Test Failover Options
        vmware_configure.next()

        # Advanced Options
        vmware_configure.advanced_options.unconditionally_overwrite_vm(self._unconditionally_overwrite)
        vmware_configure.next()

        vmware_configure.finish()

    @test_step
    def verify_sync_completion(self):
        """Verifies that the sync has completed on the created replication group"""
        self.replication = Replication(self.commcell, self.group_name)
        self.replication.wait_for_first_backup()
        self.replication.get_running_replication_jobs()
        self.replication.post_validation(job_type='FULL', validate_test_data=False)
        self.dr_helper.source_subclient = self.group_name

    @test_step
    def verify_override_settings(self):
        """Verify the overridden settings for the destination VM"""
        vm_name = self.dr_helper.destination_vm_names[0]
        vm = self.dr_helper.destination_vms[vm_name]
        self.utils.assert_includes(vm.parent_vm_folder, self.vm_folder)
        # The resource pool input to the admin console is prefixed by a '/'. However, the folder name received from
        # the hypervisor does not contain this
        self.utils.assert_includes(vm.resource_pool_name, self.resource_pool)

        if self.source_network in vm.network_names:
            raise CVTestStepFailure(f"Source VM network [{self.source_network}] in destination VM [{vm.vm_name}]: "
                                    f"{vm.network_names}")
        if self.source_network_2 in vm.network_names:
            raise CVTestStepFailure(f"Source VM network [{self.source_network_2}] in destination VM [{vm.vm_name}]: "
                                    f"{vm.network_names}")
        self.utils.assert_includes(self.destination_network, vm.network_names)
        self.utils.assert_includes(self.destination_network_2, vm.network_names)

    def run(self):
        """Runs the testcase in order"""
        try:
            self.login()
            self.delete_replication_group()
            self.configure_replication_group()

            self.logout()
            self.verify_sync_completion()

            self.verify_override_settings()

            self.login()
            self.delete_replication_group()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tears down the TC"""
        self.logout()
