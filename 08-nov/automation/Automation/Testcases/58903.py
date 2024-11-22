# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case to verify creating and updating vmware replication type recovery target

Sample input:
"58903": {
                 "destination_hypervisor":"hypervisor_name",
                  "vm_display_name":"display_name",
                  "access_node": "access_node_name",
                  "security_value": "security",
                  "destination_host_path": "path",
                  "sp_value": "Storage_policy",
                  "datastore": "datastore_value",
                  "resource_pool": "pool_name",
                  "VM_path": "path",
                  "destination_network": "dest_network_value",
                  "expiration_value": integer,
                  "media_agent": "media_agent_value",
                  "gateway_path": "path",
                  "gateway_network": "network_name",
                  "vm_display_name_2": "display_name_2",
                  "access_node_2": "access_node_name_2",
                  "destination_network_2": "path",
                  "expiration_value_2": integer
            }
"""
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper
from Web.Common.page_object import TestStep
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.DR.recovery_targets import RecoveryTargets, TargetConstants
from Web.Common.exceptions import CVTestStepFailure
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """ Test case to verify creating and updating VMware recovery target. """
    test_step = TestStep()

    def __init__(self):
        """ Initialises the objects and TC inputs """
        super(TestCase, self).__init__()

        self.name = "command center Navigation"
        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "destination_hypervisor": None,
            "vm_display_name": None,
            "access_node": None,
            "security_value": None,
            "destination_host_path": None,
            "sp_value": None,
            "resource_pool": None,
            "VM_path": None,
            "destination_network": None,
            "expiration_value": None,
            "expiration_unit": None,
            "media_agent": None,
            "gateway_network": None,
            "datastore": None,
            "gateway_path": None,
            "vm_display_name_2": None,
            "access_node_2": None,
            "destination_network_2": None,
            "expiration_value_2": None,
            "expiration_unit_2": None
        }
        self.browser = None
        self.admin_console = None
        self.recovery_target_name = None
        self.application_type = None
        self.utils = None
        self.navigator = None
        self.recovery_targets = None
        self.replication_helper = None
        self.target_details = None
        self.vmware_recovery_target = None

    def setup(self):
        """  Sets up the Testcase  """
        self.utils = TestCaseUtils(self)
        self.target_name = "Auto_target_"+self.id
        self.destination_hypervisor = self.tcinputs["destination_hypervisor"]
        self.vm_display_name = self.tcinputs["vm_display_name"]
        self.access_node = self.tcinputs["access_node"]
        self.security_value = self.tcinputs["security_value"]
        self.destination_host_path = self.tcinputs["destination_host_path"]
        self.storage_policy = self.tcinputs["sp_value"]
        self.datastore = self.tcinputs["datastore"]
        self.resource_pool = self.tcinputs["resource_pool"]
        self.vm_folder_path = self.tcinputs["VM_path"]
        self.destination_network = self.tcinputs["destination_network"]
        self.expiration_value = self.tcinputs["expiration_value"]
        self.expiration_unit = self.tcinputs["expiration_unit"]
        self.media_agent = self.tcinputs["media_agent"]
        self.gateway_network = self.tcinputs["gateway_network"]
        self.gateway_template_path = self.tcinputs["gateway_path"]
        self.target_application_type = TargetConstants.REPLICATION
        self.edited_target_name = 'Auto_edit_' + self.id
        self.edited_vm_display_name = self.tcinputs["vm_display_name_2"]
        self.edited_access_node = self.tcinputs["access_node_2"]
        self.edited_destination_network = self.tcinputs["destination_network_2"]
        self.edited_expiration_value = self.tcinputs["expiration_value_2"]
        self.edited_expiration_unit = self.tcinputs["expiration_unit_2"]

    def login(self):
        """ Logs in to admin console """
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.inputJSONnode['commcell']['webconsoleHostname'])
        self.admin_console.login(
            self.tcinputs['tenant_username'],
            self.tcinputs['tenant_password'])
        self.navigator = self.admin_console.navigator
        self.recovery_targets = RecoveryTargets(self.admin_console)
        self.replication_helper = ReplicationHelper(self.commcell, self.admin_console)

    def logout(self):
        """Logs out from the admin console"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    @test_step
    def delete_recovery_target(self):
        """Delete recovery target if it exists"""
        self.navigator.navigate_to_replication_targets()
        if self.recovery_targets.has_target(self.target_name):
            self.recovery_targets.delete_recovery_target(target_name=self.target_name)
        if self.recovery_targets.has_target(self.edited_target_name):
            self.recovery_targets.delete_recovery_target(target_name=self.edited_target_name)
        self.admin_console.refresh_page()
        self.log.info("Recovery target  %s deleted!" % self.target_name)

    @test_step
    def create_recovery_target(self):
        """ To create a recovery target"""
        vmware_target = self.recovery_targets.configure_recovery_target(self.admin_console.props['label.replicationTarget'],
                                            TargetConstants.VMWARE_VCENTER, self.target_name)
        vmware_target.general.select_destination_hypervisor(self.destination_hypervisor)
        vmware_target.general.set_vm_display_name(self.vm_display_name, self.admin_console.props['label.prefix'])
        vmware_target.general.select_access_node(self.access_node)
        vmware_target.general.select_security(self.security_value)
        vmware_target.next()
        # Destination Options
        vmware_target.set_destination_host(self.destination_host_path)
        vmware_target.select_vm_storage_policy(self.storage_policy)
        vmware_target.select_datastore(self.datastore)
        vmware_target.select_resource_pool(self.resource_pool)
        vmware_target.set_vm_folder(self.vm_folder_path)
        vmware_target.select_destination_network(self.destination_network)
        vmware_target.next()
        # Test fail over options
        vmware_target.set_expiration_time(self.expiration_value, self.expiration_unit)
        vmware_target.select_mediaagent(self.media_agent)
        vmware_target.click_migrate_vms()
        vmware_target.select_configure_isolated_network()
        vmware_target.click_configure_gateway(self.gateway_template_path, self.gateway_network)
        self.log.info("Configure %s recovery target success" % self.target_name)
        vmware_target.submit()

    @test_step
    def verify_target_creation(self):
        """Verify recovery targets page has correct details associated"""
        self.navigator.navigate_to_replication_targets()
        details = self.recovery_targets.get_target_details(self.target_name)
        self.replication_helper.assert_comparison(details[self.admin_console.props['label.name']], [self.target_name])
        self.replication_helper.assert_comparison(details[self.admin_console.props['label.libraryVendorName']], [TargetConstants.VMWARE_VCENTER])
        self.replication_helper.assert_comparison(details[self.admin_console.props['label.PolicyType']], [self.target_application_type])
        self.replication_helper.assert_comparison(details[self.admin_console.props['label.destinationServer']], [self.destination_hypervisor])
        self.log.info("Verified recovery target table details!")

    @test_step
    def verify_target_details(self, after_edit = False):
        """Verify recovery target details are expected"""
        self.navigator.navigate_to_replication_targets()
        label = self.admin_console.props
        if not after_edit:
            self.target_details = self.recovery_targets.access_target(self.target_name)
        else:
            self.target_details = self.recovery_targets.access_target(self.edited_target_name)
        summary = self.target_details.get_target_summary()

        self.replication_helper.assert_comparison(summary[label['label.destinationServer']], self.destination_hypervisor)
        self.replication_helper.assert_comparison(summary[label['label.PolicyType']], self.target_application_type)
        self.replication_helper.assert_comparison(summary[label['label.destinationHost']], self.destination_host_path.split("/")[-1])
        self.replication_helper.assert_comparison(summary[label['label.vmStoragePolicy']], self.storage_policy)
        self.replication_helper.assert_comparison(summary[label['label.dataStore']], self.datastore)
        self.replication_helper.assert_comparison(summary[label['label.resourcePool']], self.resource_pool)
        self.replication_helper.assert_comparison(summary[label['label.vmFolder']], self.vm_folder_path.split("/")[-1])

        if not after_edit:
            self.replication_helper.assert_comparison(summary[label['label.accessNode']], self.access_node)
            self.replication_helper.assert_comparison(summary[label['label.changeVmDisplayName'] + ' (' + label['label.prefix'] + ')'],
                                                      self.vm_display_name)
            self.replication_helper.assert_comparison(summary[label['label.destinationNetworkModal']], self.destination_network)
            self.replication_helper.assert_comparison(summary[label['label.nav.mediaAgent']], self.media_agent)
            self.replication_helper.assert_comparison(summary[label['label.isolatedNetwork']], label['label.yes'])
            self.replication_helper.assert_comparison(summary[label['label.gatewayTemplate']], self.gateway_template_path.split("/")[-1])
            self.replication_helper.assert_comparison(summary[label['label.gatewayNetwork']], self.gateway_network)
            self.replication_helper.assert_comparison(summary[label['label.migrateVMs']], self.admin_console.props['label.yes'])

        else:
            self.replication_helper.assert_comparison(summary[label['label.accessNode']], self.edited_access_node)
            self.replication_helper.assert_comparison(summary[label['label.changeVmDisplayName'] + ' (' + label['label.suffix'] + ')'],
                                                      self.edited_vm_display_name)
            self.replication_helper.assert_comparison(summary[label['label.destinationNetworkModal']], self.edited_destination_network)
            self.replication_helper.assert_comparison(summary['MediaAgent'], self.media_agent)
            self.replication_helper.assert_comparison(summary[label['label.migrateVMs']], label['label.no'])
            self.replication_helper.assert_comparison(summary[label['label.existingNetwork']], self.gateway_network)

    @test_step
    def verify_non_editable_fields(self):
        """Verify specific fields are not editable in edit panel"""
        expected_non_editable_fields = ['hypervisorsDropdown', 'destinationHost',
                                        'storagePolicyDropdown', 'DataStoreDropdown', 'resourcePoolDropdown', 'destinationFolder']
        self.edit_target = self.target_details.edit_target()
        for num, each_field in enumerate(expected_non_editable_fields):
            field_disabled = self.edit_target.is_field_disabled(each_field)
            if not field_disabled:
                raise CVTestStepFailure("[%s] field is editable in Edit panel of [%s] target, "
                                        "Please check this should not be editable!" %
                                        (each_field, self.target_name))
            if num == 0:
                self.edit_target.next()
        self.admin_console.refresh_page()

    @test_step
    def edit_recovery_target(self):
        """Edits the target configuration"""
        self.edit_target.set_recovery_target_name(self.edited_target_name)
        self.edit_target.general.set_vm_display_name(self.edited_vm_display_name, self.admin_console.props['label.suffix'])
        self.edit_target.general.select_access_node(self.edited_access_node)
        self.edit_target.next()
        self.edit_target.select_destination_network(self.edited_destination_network)
        self.edit_target.next()
        self.edit_target.set_expiration_time(self.edited_expiration_value, self.edited_expiration_unit)
        self.edit_target.select_configure_existing_network(self.gateway_network)
        self.edit_target.submit()
        self.log.info("Updated recovery target successfully!")

    def run(self):
        """ Runs the testcase in order """
        try:
            self.login()
            self.delete_recovery_target()
            self.create_recovery_target()
            self.verify_target_creation()
            self.verify_target_details()
            self.verify_non_editable_fields()
            self.edit_recovery_target()
            self.verify_target_details(after_edit=True)
            self.delete_recovery_target()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """Tears down the Test Case"""
        self.logout()

