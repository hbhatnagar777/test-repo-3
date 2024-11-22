# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case(verify the creation and updation of Azure recovery target
of replication type)

TestCase is the only class defined in this file.

TestCase: Class for executing this test case
Sample JSON: {
                    "tenant_username":<username>
                    "tenant_password":<password>
                   "display_name": "1-DRVM",
                   "hypervisor": "AzureDest",
                   "access_node": "BDCMetrics",
                   "resource_group": "automation",
                   "region": "East US",
                   "availability_zone": "2",
                   "storage_account": "adminwinfiles",
                   "vm_size": "Standard_A1_v2",
                   "disk_type": "Standard HDD",
                   "virtual_network": "admin-linux-vnet\\default",
                   "security_group": "admin-linux-vm-nsg",
                   "create_public_ip": false,
                   "expiration_time": "2 hours",
                   "test_virtual_network": "admin-linux-vnet\\default",
                   "test_vm_size": "Standard_A1_v2",
                   "display_name_2": "DRVM-1",
                   "access_node_2": "drachyd3_3",
                   "availability_zone_2": "3",
                   "disk_type_2": "Standard SSD",
                   "virtual_network_2": "CRRecoveryVnet\\default",
                   "vm_size_2": "Standard_B1s",
                   "security_group_2": "AzureTst1M1-nsg",
                   "expiration_time_2": "3 days",
                   "test_virtual_network_2": "CRRecoveryVnet\\default",
                   "create_public_ip_2": true,
                   "test_vm_size_2": "Standard_B1ls"
}
"""

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import TestStep
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.AdminConsole.DR.recovery_targets import RecoveryTargets, TargetConstants


class TestCase(CVTestCase):
    """This testcase is defined for the verification of creation and update of Azure recovery target"""
    test_step = TestStep()

    def __init__(self):
        """Initialises the class and variables are set to None"""
        super(TestCase, self).__init__()
        self.name = "Azure Recovery target CRUD Test"
        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "hypervisor": None,
            "access_node": None,
            "display_name": None,

            "resource_group": None,
            "region": None,
            "availability_zone": None,
            "storage_account": None,
            "vm_size": None,
            "disk_type": None,
            "virtual_network": None,
            "security_group": None,
            "create_public_ip": False,
            "expiration_time": None,
            "expiration_unit": None,
            "test_virtual_network": None,
            "test_vm_size": None,

            "display_name_2": None,
            "access_node_2": None,
            "availability_zone_2": "3",
            "disk_type_2": None,
            "virtual_network_2": None,
            "vm_size_2": None,
            "security_group_2": None,
            "expiration_time_2": None,
            "expiration_unit_2": None,
            "test_virtual_network_2": None,
            "test_vm_size_2": None,
            "create_public_ip_2": True

        }

        self.browser = None
        self.admin_console = None
        self.utils = None
        self.recovery_targets = None
        self.target = None
        self.edit_target = None

    @property
    def target_name(self):
        """Returns the initial target name for the recovery target"""
        return f'test_auto_tc_{self.id}'

    @property
    def edited_target_name(self):
        """Returns the modified target name"""
        return f'test_auto_edited_tc_{self.id}'

    def login(self):
        """Logs in to the admin console and initialises it"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser,
            machine=self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.goto_adminconsole()
        self.admin_console.login(self.tcinputs['tenant_username'],
                                 self.tcinputs['tenant_password'])
        self.recovery_targets = RecoveryTargets(self.admin_console)

    def logout(self):
        """Logs out from admin console and closes browser"""
        self.admin_console.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)

    def setup(self):
        """Sets up the various variables and initiates the admin console"""
        self.utils = TestCaseUtils(self)
        self.hypervisor = self.tcinputs["hypervisor"]
        self.display_name = self.tcinputs["display_name"]
        self.access_node = self.tcinputs['access_node']
        self.resource_group = self.tcinputs['resource_group']
        self.region = self.tcinputs["region"]
        self.availability_zone = self.tcinputs['availability_zone']
        self.storage_account = self.tcinputs['storage_account']
        self.vm_size = self.tcinputs['vm_size']
        self.disk_type = self.tcinputs['disk_type']
        self.virtual_network = self.tcinputs['virtual_network']
        self.security_group = self.tcinputs['security_group']
        self.expiration_time = self.tcinputs['expiration_time']
        self.expiration_unit = self.tcinputs['expiration_unit']
        self.test_virtual_network = self.tcinputs['test_virtual_network']
        self.test_vm_size = self.tcinputs['test_vm_size']
        self.test_security_group = self.tcinputs['test_security_group']
        self.create_public_ip = self.tcinputs['create_public_ip']

        self.edited_display_name = self.tcinputs['display_name_2']
        self.edited_access_node = self.tcinputs['access_node_2']
        self.edited_availability_zone = self.tcinputs['availability_zone_2']
        self.edited_expiration_time = self.tcinputs['expiration_time_2']
        self.edited_expiration_unit = self.tcinputs['expiration_unit_2']
        self.edited_security_group = self.tcinputs['security_group_2']
        self.edited_test_virtual_network = self.tcinputs['test_virtual_network_2']
        self.edited_disk_type = self.tcinputs['disk_type_2']
        self.edited_virtual_network = self.tcinputs['virtual_network_2']
        self.edited_vm_size = self.tcinputs['vm_size_2']
        self.edited_test_vm_size = self.tcinputs['test_vm_size_2']
        self.edited_test_security_group = self.tcinputs['test_security_group_2']
        self.edited_create_public_ip = self.tcinputs['create_public_ip_2']

    @test_step
    def create_recovery_target(self):
        """Creates a recovery target in the recovery targets page"""
        azure_target = self.recovery_targets.configure_recovery_target(self.admin_console.props['label.replicationTarget'],
                                                                       TargetConstants.MICROSOFT_AZURE,
                                                                       self.target_name)
        azure_target.general.select_destination_hypervisor(self.hypervisor)
        azure_target.general.set_vm_display_name(self.display_name, self.admin_console.props['label.prefix'])
        azure_target.general.select_access_node(self.access_node)
        azure_target.next()
        # Destination Options
        azure_target.select_resource_group(self.resource_group)
        azure_target.select_region(self.region)
        azure_target.select_storage_account(self.storage_account)
        azure_target.select_vm_size(self.vm_size)
        azure_target.select_availability_zone(self.availability_zone)
        azure_target.select_disk_type(self.disk_type)
        azure_target.virtual_network(self.virtual_network)
        azure_target.select_security_group(self.security_group)
        azure_target.create_public_ip(self.create_public_ip)
        azure_target.next()
        # Test failover options
        azure_target.set_expiration_time(self.expiration_time, self.expiration_unit)
        azure_target.virtual_network(self.test_virtual_network)
        azure_target.select_vm_size(self.test_vm_size)
        azure_target.select_security_group(self.test_security_group)
        azure_target.submit()

    @test_step
    def verify_target_creation(self):
        """Verifies the information of the recovery target on the recovery target page table"""
        self.admin_console.navigator.navigate_to_replication_targets()
        details = self.recovery_targets.get_target_details(self.target_name)

        self.utils.assert_comparison(
            details[self.admin_console.props['label.name']], [self.target_name])
        self.utils.assert_comparison(
            details[self.admin_console.props['label.vendor']], [TargetConstants.MICROSOFT_AZURE])
        self.utils.assert_comparison(
            details[self.admin_console.props['label.PolicyType']], [TargetConstants.REPLICATION])
        self.utils.assert_comparison(
            details[self.admin_console.props['label.destinationServer']], [self.hypervisor])

    @test_step
    def verify_target_details(self, after_edit=False):
        """Verifies the target details in the target's detail page"""
        self.admin_console.navigator.navigate_to_replication_targets()
        label = self.admin_console.props
        if not after_edit:
            self.target = self.recovery_targets.access_target(self.target_name)
        else:
            self.target = self.recovery_targets.access_target(self.edited_target_name)
        target_details = self.target.get_target_summary()

        self.utils.assert_comparison(
            target_details[label['label.destinationServer']], self.hypervisor)
        self.utils.assert_comparison(
            target_details[label['label.resourceGroup']], self.resource_group)
        self.utils.assert_comparison(
            target_details[label['label.storageAccount']], self.storage_account)
        self.utils.assert_comparison(
            target_details[label['label.region']], self.region)
        self.utils.assert_comparison(
            target_details[label['label.PolicyType']], TargetConstants.REPLICATION)

        if not after_edit:
            self.utils.assert_comparison(
                target_details[label['label.accessNode']], self.access_node)
            self.utils.assert_comparison(
                target_details[label['label.changeVmDisplayName'] + ' (' + label['label.prefix'] + ')'],
                self.display_name)
            self.utils.assert_includes(
                self.vm_size, target_details[label['label.vmSize']][0])
            self.utils.assert_includes(
                self.virtual_network, target_details[label['label.virtualNetwork']][0])
            self.utils.assert_comparison(
                target_details[label['label.securityGroup']][0], self.security_group)
            self.utils.assert_comparison(
                target_details[label['label.availabilityZone']], self.availability_zone)
            self.utils.assert_comparison(
                target_details[label['label.createPublicIp']],
                "Enabled" if self.create_public_ip else "Disabled")
            self.utils.assert_includes(
                self.test_virtual_network, target_details[label['label.virtualNetwork']][1])
            self.utils.assert_includes(
                self.test_vm_size, target_details[label['label.vmSize']][1])
            self.utils.assert_comparison(
                target_details[label['label.securityGroup']][1], self.test_security_group)
            self.utils.assert_comparison(
                target_details[label['label.expirationTime']], self.expiration_time + " " + self.expiration_unit)

        else:
            self.utils.assert_comparison(
                target_details[label['label.accessNode']], self.edited_access_node)
            self.utils.assert_comparison(
                target_details[label['label.changeVmDisplayName'] + ' (' + label['label.suffix'] + ')'],
                self.edited_display_name)
            self.utils.assert_includes(
                self.edited_vm_size, target_details[label['label.vmSize']][0])
            self.utils.assert_includes(
                self.edited_virtual_network, target_details[label['label.virtualNetwork']][0])
            self.utils.assert_comparison(
                target_details[label['label.securityGroup']][0], self.edited_security_group)
            self.utils.assert_comparison(
                target_details[label['label.createPublicIp']],
                "Enabled" if self.edited_create_public_ip else "Disabled")
            self.utils.assert_includes(
                self.edited_test_virtual_network, target_details[label['label.virtualNetwork']][1])
            self.utils.assert_includes(
                self.edited_test_vm_size, target_details[label['label.vmSize']][1])
            self.utils.assert_comparison(
                target_details[label['label.securityGroup']][1], self.edited_test_security_group)
            self.utils.assert_comparison(
                target_details[label['label.expirationTime']],
                self.edited_expiration_time + " " + label['label.days'])

    @test_step
    def verify_target_fields_disabled(self):
        """Verifies that the edit target page's fields are disabled"""
        self.edit_target = self.target.edit_target(
            self.target_name, TargetConstants.MICROSOFT_AZURE)

        fields_disabled = ["hypervisorsDropdown", "resourceGroupDropdown", "azureRegionDropdown",
                           "storageAccountDropdown"]
        for num, field_id in enumerate(fields_disabled):
            field_disabled = self.edit_target.is_field_disabled(field_id)
            if field_disabled is None:
                raise CVTestStepFailure(f"The field {field_id} is not interactable/existent")
            if not field_disabled:
                raise CVTestStepFailure(
                    f'In Edit VM The field {field_id} is enabled, but must be disabled')
            if num == 0:
                self.edit_target.next()
        self.admin_console.refresh_page()

    @test_step
    def edit_recovery_target(self):
        """Edits the target configuration"""
        self.edit_target.set_recovery_target_name(self.edited_target_name)
        self.edit_target.general.set_vm_display_name(self.edited_display_name, self.admin_console.props['label.suffix'])
        self.edit_target.general.select_access_node(self.edited_access_node)
        self.edit_target.next()
        self.edit_target.select_vm_size(self.edited_vm_size)
        self.edit_target.select_availability_zone(self.edited_availability_zone)
        self.edit_target.select_disk_type(self.edited_disk_type)
        self.edit_target.virtual_network(self.edited_virtual_network)
        self.edit_target.select_security_group(self.edited_security_group)
        self.edit_target.create_public_ip(self.edited_create_public_ip)
        self.edit_target.next()
        self.edit_target.set_expiration_time(self.edited_expiration_time, self.edited_expiration_unit)
        self.edit_target.virtual_network(self.edited_test_virtual_network)
        self.edit_target.select_vm_size(self.edited_test_vm_size)
        self.edit_target.select_security_group(self.edited_test_security_group)
        self.edit_target.submit()

    @test_step
    def delete_recovery_target(self):
        """Tries to delete the recovery target"""
        self.admin_console.navigator.navigate_to_replication_targets()
        if self.recovery_targets.has_target(self.target_name):
            self.recovery_targets.delete_recovery_target(self.target_name)
            self.admin_console.refresh_page()
            if self.recovery_targets.has_target(self.target_name):
                raise CVTestStepFailure("Could not delete recovery target as part of cleanup")

        if self.recovery_targets.has_target(self.edited_target_name):
            self.recovery_targets.delete_recovery_target(self.edited_target_name)
            self.admin_console.refresh_page()
            if self.recovery_targets.has_target(self.edited_target_name):
                raise CVTestStepFailure("Could not delete recovery target as part of tear down")

    def run(self):
        """Executes the testcase"""
        try:
            self.login()
            self.delete_recovery_target()
            self.create_recovery_target()

            self.verify_target_creation()
            self.verify_target_details()
            self.verify_target_fields_disabled()

            self.edit_recovery_target()
            self.verify_target_details(after_edit=True)
            self.delete_recovery_target()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Performs garbage collection for the TC"""
        self.logout()
