# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""Main file for executing this test case(verify the recovery target for Hyper-V)

TestCase is the only class defined in this file.

TestCase: Class for executing this test case
Sample JSON: {
            "tenant_username": <username>,
            "tenant_password": <password>,
            "hypervisor": "HyperV_name",
            "access_node": "node1" ,
            "storage_account" : "path1",
            "network" : "network1",
            "access_node_2": "node2",
            "storage_account_2": "path2",
            "network_2": "network2"

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
    """This testcase is for the verification and update of HyperV recovery target"""
    test_step = TestStep()

    def __init__(self):
        """Initialises the class and variables are set to None"""
        super(TestCase, self).__init__()
        self.name = "HyperV Recovery Target CRUD Test"
        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "hypervisor": None,
            "display_name":None,
            "access_node": None,
            "destination_path":None,
            "network": None,
            "expiration_time": None,
            "display_name_2": None,
            "destination_path_2": None,
            "network_2": None,
            "expiration_time_2": None,
            "register_vm": None,
            "register_vm_2": None
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
        return f'Auto_{self.id}'

    @property
    def edited_target_name(self):
        """Returns the modified target name"""
        return f'Auto_edited_{self.id}'

    def login(self):
        """Logs in to the admin console and initialises it"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                            machine=(self.inputJSONnode['commcell']['webconsoleHostname']))
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
        self.destination_path = self.tcinputs['destination_path']
        self.network = self.tcinputs['network']
        self.expiration_time = self.tcinputs['expiration_time']
        self.register_vm = self.tcinputs['register_vm']

        self.edited_display_name = self.tcinputs["display_name_2"]
        self.edited_destination_path = self.tcinputs['destination_path_2']
        self.edited_register_vm = self.tcinputs['register_vm_2']
        self.edited_network = self.tcinputs['network_2']
        self.edited_expiration_time = self.tcinputs['expiration_time_2']

    @test_step
    def create_recovery_target(self):
        """Creates a recovery target in the recovery targets page"""
        self.admin_console.navigator.navigate_to_replication_targets()
        hyperv_target = self.recovery_targets.configure_recovery_target(self.admin_console.props['label.replicationTarget'],
                                                                    TargetConstants.MICROSOFT_HYPERV,
                                                                    self.target_name)
        hyperv_target.general.select_destination_hypervisor(self.hypervisor)
        hyperv_target.general.set_vm_display_name(self.display_name, self.admin_console.props['label.prefix'])
        hyperv_target.general.select_access_node(self.access_node)
        hyperv_target.next()
        # Destination Options
        hyperv_target.set_destination_folder(self.destination_path)
        hyperv_target.register_vm_with_failover(self.register_vm)
        hyperv_target.select_network(self.network)
        hyperv_target.next()
        # Test failover options
        hyperv_target.set_expiration_time(self.expiration_time)
        hyperv_target.submit()

    @test_step
    def verify_target_creation(self):
        """Verifies the information of the recovery target on the recovery target page table"""
        self.admin_console.navigator.navigate_to_replication_targets()
        details = self.recovery_targets.get_target_details(self.target_name)
        # comparison
        self.utils.assert_comparison(
            details[self.admin_console.props['label.name']], [self.target_name])
        self.utils.assert_comparison(
            details[self.admin_console.props['label.libraryVendorName']], [TargetConstants.MICROSOFT_HYPERV])
        self.utils.assert_comparison(
            details[self.admin_console.props['label.PolicyType']], [TargetConstants.REPLICATION])
        self.utils.assert_comparison(
            details[self.admin_console.props['label.destinationServer']], [self.hypervisor])

    @test_step
    def delete_recovery_target(self):
        """Tries to delete the recovery target"""
        self.admin_console.navigator.navigate_to_replication_targets()
        if self.recovery_targets.has_target(self.edited_target_name):
            self.recovery_targets.delete_recovery_target(self.edited_target_name)
            self.admin_console.refresh_page()
            if self.recovery_targets.has_target(self.edited_target_name):
                raise CVTestStepFailure("Could not delete recovery target")

        if self.recovery_targets.has_target(self.target_name):
            self.recovery_targets.delete_recovery_target(self.target_name)
            self.admin_console.refresh_page()
            if self.recovery_targets.has_target(self.target_name):
                raise CVTestStepFailure("Could not delete recovery target as part of cleanup")

    @test_step
    def verify_target_details(self, after_edit=False):
        """Verifies the target details in the target's detail page"""
        label = self.admin_console.props
        if not after_edit:
            self.target = self.recovery_targets.access_target(self.target_name)
        target_details = self.target.get_target_summary()

        # Common for both
        self.utils.assert_comparison(target_details[label['label.destinationServer']],
                                     self.hypervisor)
        self.utils.assert_comparison(target_details[label['label.PolicyType']], TargetConstants.REPLICATION)

        if not after_edit:
            self.utils.assert_comparison(target_details[label['label.accessNode']], self.access_node)
            self.utils.assert_comparison(
                target_details[label['label.changeVmDisplayName'] + ' (' + label['label.prefix'] + ')'],
                self.display_name)
            self.utils.assert_comparison(target_details[label['label.destinationFolder']],
                                         self.destination_path)
            self.utils.assert_comparison(target_details[label['label.registerVm']],
                                         label['label.yes'] if self.register_vm else label['label.no'])
            self.utils.assert_comparison(target_details[label['label.vCloudNic']],
                                         self.network)
        else:
            self.utils.assert_comparison(target_details[label['label.accessNode']], self.access_node)
            self.utils.assert_comparison(
                target_details[label['label.changeVmDisplayName'] + ' (' + label['label.suffix'] + ')'],
                self.edited_display_name)
            self.utils.assert_comparison(target_details[label['label.destinationFolder']],
                                         self.edited_destination_path)
            self.utils.assert_comparison(target_details[label['label.registerVm']],
                                         label['label.yes'] if self.edited_register_vm else label['label.no'])
            self.utils.assert_comparison(target_details[label['label.vCloudNic']],
                                         self.edited_network)

    @test_step
    def verify_target_fields_disabled(self):
        """Verifies that the edit target page's fields are disabled"""
        self.edit_target = self.target.edit_target(self.target_name,
                                                   TargetConstants.MICROSOFT_HYPERV)
        fields_disabled = 'hypervisorsDropdown'
        field_disabled = self.edit_target.is_field_disabled(fields_disabled)
        if field_disabled is None:
            raise CVTestStepFailure(f"The field {fields_disabled} is not interactable/existent")
        if not field_disabled:
            raise CVTestStepFailure(f'In Edit VM The field {fields_disabled} '
                                    f'is enabled, but must be disabled')

    @test_step
    def edit_recovery_target(self):
        """Edits the target configuration"""
        self.edit_target.set_recovery_target_name(self.edited_target_name)
        self.edit_target.general.set_vm_display_name(self.edited_display_name, self.admin_console.props['label.suffix'])
        self.edit_target.next()
        self.edit_target.set_destination_folder(self.edited_destination_path)
        self.edit_target.register_vm_with_failover(self.edited_register_vm)
        self.edit_target.select_network(self.edited_network)
        self.edit_target.next()
        self.edit_target.set_expiration_time(self.edited_expiration_time)
        self.edit_target.submit()

    def run(self):
        """Executes the testcase"""
        try:
            self.login()
            self.delete_recovery_target()
            self.create_recovery_target()  # for creating target
            self.verify_target_creation()  # for verifying its creation
            self.verify_target_details()  # verifying its details before editing
            self.verify_target_fields_disabled()  # run to validate non editable fields
            self.edit_recovery_target()  # for editing recovery target
            self.verify_target_details(after_edit=True)  # verifying edited fields
            self.delete_recovery_target()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Performs garbage collection for the TC"""
        self.logout()