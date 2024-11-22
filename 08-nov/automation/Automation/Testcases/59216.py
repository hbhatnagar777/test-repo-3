# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case to verify Azure replication group creation and primary copy job completion

Sample input:
"59216": {
            "tenant_username": <username>,
            "tenant_password": <password>,
            "ClientName": "hypervisor",
            "source_vms": ["vm1", "vm2"], # (2 VMs Required)
            "recovery_target":"test-3",
            "primary_storage_name" : "Storage1",
            "drvm_name" : "vm1_drvm",
            "resource_group": "DR-Destination",
            "region" : "Central India",
            "storage_account": "drdestinationdiag",
            "vm_size": "Standard_B1ls",
            "virtual_network": "DR-Destination-vnet",
            "availability_zone": 1,
            "availability_zone_2": 2,
            "security_group": "azureProxy-nsg",
            "vm_size_2": "Standard_B1s",
            "virtual_network_2": "DR-Testing-vnet",
            "security_group_2": "azurelinuxproxy-nsg"
       }

"""
from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.recovery_targets import RecoveryTarget
from DROrchestration.replication import Replication
from DROrchestration.DRUtils.DRConstants import Vendors_Complete, ReplicationType, SiteOption, TimePeriod, VendorTransportModes
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper, DRHelper
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.DR.virtualization_replication import ConfigureAzureVM, _AzureVMOptions
from Web.AdminConsole.DR.group_details import EditAzureVirtualMachine


class TestCase(CVTestCase):
    """Test case to verify configuring AWS replication group using primary copy."""

    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        CVTestCase.__init__(self)
        self.name = "Azure - Zeal Replication group CRUD test with Primary copy"

        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "ClientName": None,
            "source_vms": [],
            "recovery_target": None,
            "primary_storage_name": None,
            "drvm_name": None,
            "resource_group": None,
            "region": None,
            "storage_account": None,
            "vm_size": None,
            "virtual_network": None,
            "security_group": None,
            "availability_zone": None,
            "availability_zone_2": None,
            "vm_size_2": None,
            "virtual_network_2": None,
            "security_group_2": None
        }
        self.source_hypervisor = None
        self.source_vms = None
        self.recovery_target = None
        self.transport_mode = None
        self.primary_storage_name = None

        self.drvm_name = None
        self.resource_group = None
        self.region = None
        self.storage_account = None
        self.vm_size = None
        self.virtual_network = None
        self.security_group = None
        self.availability_zone = None
        self.availability_zone_2 = None
        self.vm_size_2 = None
        self.virtual_network_2 = None
        self.security_group_2 = None

        self.utils = None

        self.browser = None
        self.admin_console = None
        self.replication_helper = None
        self.replication_group = None
        self.group_details = None

        self.target_details = None
        self.replication = None
        self.dr_helper = None

    def setup(self):
        """Sets up the Testcase"""
        self.utils = TestCaseUtils(self)
        self.source_hypervisor = self.tcinputs["ClientName"]
        self.source_vms = self.tcinputs["source_vms"]
        self.recovery_target = self.tcinputs["recovery_target"]
        self.primary_storage_name = self.tcinputs["primary_storage_name"]
        self.drvm_name = self.tcinputs["drvm_name"]
        self.resource_group = self.tcinputs["resource_group"]
        self.region = self.tcinputs["region"]
        self.storage_account = self.tcinputs["storage_account"]
        self.vm_size = self.tcinputs["vm_size"]
        self.availability_zone = self.tcinputs["availability_zone"]
        self.virtual_network = self.tcinputs["virtual_network"]
        self.security_group = self.tcinputs["security_group"]
        self.availability_zone_2 = self.tcinputs["availability_zone_2"]
        self.vm_size_2 = self.tcinputs["vm_size_2"]
        self.virtual_network_2 = self.tcinputs["virtual_network_2"]
        self.security_group_2 = self.tcinputs["security_group_2"]

        self._storage_list = [self.primary_storage_name]

        self._source_vendor = Vendors_Complete.AZURE.value
        self._destination_vendor = Vendors_Complete.AZURE.value
        self._replication_type = ReplicationType.Periodic
        self._siteoption = SiteOption.HotSite
        self._enable_replication = True

        self._frequency_duration = 4
        self._frequency_unit = TimePeriod.HOURS
        self._frequency_duration_edit = 8
        self._frequency_unit_edit = TimePeriod.DAYS

        self._unconditionally_overwrite = True
        self._continue_to_next_priority = True
        self._delay_between_priorities = 5

        self.target_details: RecoveryTarget = self.commcell.recovery_targets.get(
            self.recovery_target)
        self.dr_helper = DRHelper(self.commcell, self.csdb, self.client)

    def _validate_override_options(self, observed_values : dict | list, expected_values : dict | list):
        """Helper function for validating the override options"""
        validation_keys = ["drvm_name", "resource_group",  "region",
                           "storage_account", "vm_size", "availability_zone",
                           "virtual_network", "security_group"]

        observed_values_dict = {key: value for key, value in zip(validation_keys, observed_values)} if isinstance(observed_values, list) else observed_values
        expected_values_dict = {key: value for key, value in zip(validation_keys, expected_values)} if isinstance(expected_values, list) else expected_values

        self.replication_helper.validate_details(self._destination_vendor,
                                                 observed_values=observed_values_dict,
                                                 expected_values=expected_values_dict)

    def _verify_vm_details(self, observed_field_detatils: dict, after_edit: bool, vm_id: int):
        """Verifies the details of the VM on the edit page"""
        if vm_id == 2:
                drvm_name = f"{self.target_details.vm_prefix}{self.source_vms[vm_id - 1]}{self.target_details.vm_suffix}"
                expected_values = [drvm_name, self.target_details.resource_group,  self.target_details.region,
                                   self.target_details.storage_account, self.target_details.vm_size,
                                   self.target_details.availability_zone, self.target_details. virtual_network,
                                   self.target_details.security_group]
                self._validate_override_options(observed_values=observed_field_detatils, expected_values=expected_values)

        elif after_edit:
            drvm_name = self.drvm_name if vm_id == 1 else f"{self.target_details.vm_prefix}{self.source_vms[vm_id - 1]}{self.target_details.vm_suffix}"
            expected_values = [drvm_name, self.resource_group, self.region,
                               self.storage_account, self.vm_size_2, self.availability_zone_2,
                               self.virtual_network_2, self.security_group_2]
            self._validate_override_options(observed_values=observed_field_detatils, expected_values=expected_values)

        else:
            drvm_name = self.drvm_name if vm_id == 1 else f"{self.target_details.vm_prefix}{self.source_vms[vm_id - 1]}{self.target_details.vm_suffix}"
            expected_values = [drvm_name, self.resource_group, self.region,
                               self.storage_account, self.vm_size, self.availability_zone, self.virtual_network,
                               self.security_group]
            self._validate_override_options(observed_values=observed_field_detatils, expected_values=expected_values)

    @property
    def group_name(self):
        """Returns the replication group name"""
        return self.replication_helper.group_name(self.id)

    def login(self):
        """Logs in to admin console"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser,
                                              self.inputJSONnode['commcell']['webconsoleHostname'])
            self.admin_console.login(self.tcinputs['tenant_username'],
                                     self.tcinputs['tenant_password'])

            self.replication_helper = ReplicationHelper(self.commcell,
                                                        self.admin_console)
            self.replication_group = ReplicationGroup(self.admin_console)

        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def logout(self):
        """Logs out from the admin console"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)

    @test_step
    def delete_replication_group(self):
        """Deletes the replication group if it exists already"""
        self.replication_helper.delete_replication_group(self.group_name,
                                                         self.source_vms)

    @test_step
    def configure_replication_group(self):
        """Create a replication group with a single copy and overrides"""
        self.admin_console.navigator.navigate_to_replication_groups()
        azure_configure = self.replication_group.configure_virtualization(source_vendor=self._source_vendor,
                                                                          destination_vendor=self._destination_vendor,
                                                                          replication_type=self._replication_type.value)

        # Type Hinting
        azure_configure: ConfigureAzureVM

        # General
        azure_configure.content.set_name(self.group_name)
        azure_configure.content.select_production_site_hypervisor(self.source_hypervisor)
        azure_configure.next()

        # Content
        azure_configure.content.select_vm_from_browse_tree(self.source_vms, expand_folder=False)
        azure_configure.next()

        # Storage
        _storagecopy = azure_configure.storage_cache.Storage_Copy
        azure_configure.storage_cache.select_storage(self.primary_storage_name,
                                                     storage_copy=_storagecopy.Primary.value)
        azure_configure.next()

        # Recovery Options
        azure_configure.recovery_options.select_recovery_target(self.recovery_target)
        azure_configure.recovery_options.set_frequency(frequency_duration=self._frequency_duration,
                                                       frequency_period=self._frequency_unit.value)
        azure_configure.recovery_options.select_rto(self._siteoption.value)
        azure_configure.recovery_options.replication_on_group_creation(self._enable_replication)
        azure_configure.next()

        # TODO : Pre-Post Scripts (Configuration)
        azure_configure.next()

        # Override Options
        override_options = azure_configure.override_options.override_vms(source_vm=self.source_vms[0])
        override_options: _AzureVMOptions

        override_options.set_vm_display_name(self.drvm_name)
        override_options.select_resource_group(self.resource_group)
        override_options.select_region(self.region)
        override_options.select_storage_account(self.storage_account)
        override_options.select_vm_size(self.vm_size)
        override_options.select_availability_zone(self.availability_zone)
        override_options.virtual_network(self.virtual_network)
        override_options.select_security_group(self.security_group)
        override_options.save()

        for idx, vm_name in enumerate(self.source_vms):
            self.vm_noedit_details = azure_configure.override_options.get_azure_vm_details(vm_name)
            if idx == 0:
                expected_values = [self.drvm_name, self.resource_group, self.region,
                                   self.storage_account, self.vm_size, self.availability_zone, self.virtual_network, self.security_group]
                self._validate_override_options(observed_values=self.vm_noedit_details.get("field_values"),
                                                expected_values=expected_values)

            else:
                # Prefix and Suffix are mutually exclusive therefore, only one of them will be present and the other will be a null string
                drvm_name = f"{self.target_details.vm_prefix}{vm_name}{self.target_details.vm_suffix}"
                expected_values = [drvm_name, self.target_details.resource_group, self.target_details.region,
                                   self.target_details.storage_account, self.target_details.vm_size,
                                   self.target_details.availability_zone, self.target_details. virtual_network,
                                   self.target_details.security_group]
                self._validate_override_options(observed_values=self.vm_noedit_details.get("field_values"),
                                                expected_values=expected_values)

        azure_configure.next()

        # Advanced Options
        azure_configure.advanced_options.unconditionally_overwrite_vm(self._unconditionally_overwrite)
        azure_configure.advanced_options.continue_to_next_priority(self._continue_to_next_priority)
        azure_configure.advanced_options.set_delay_between_priority(self._delay_between_priorities)
        azure_configure.next()

        # Submit group creation request
        azure_configure.finish()

    @test_step
    def verify_replication_group_exists(self):
        """Verify replication group exists in Replication Groups page"""
        group_state = 'Enabled' if self._enable_replication else 'Disabled'
        self.replication_helper.verify_replication_group_exists(group_name=self.group_name,
                                                                source_hypervisor=self.source_hypervisor,
                                                                target_name=self.recovery_target,
                                                                site=self._siteoption.name,
                                                                replication_type=self._replication_type.name,
                                                                group_state=group_state)

    @test_step
    def verify_vm_group_exists(self):
        """Verify configured replication group exists in Protect->Virtualization->VM groups"""
        self.replication_helper.verify_vm_group_exists(group_name=self.group_name,
                                                       vendor_name=self._source_vendor,
                                                       source_hypervisor=self.source_hypervisor,
                                                       partial_match=True)

    @test_step
    def verify_sync_completion(self):
        """Verifies that the sync has completed on the created replication group"""
        self.replication = Replication(self.commcell, self.group_name)
        self.replication.wait_for_first_backup()
        self.replication.get_running_replication_jobs()
        self.replication.post_validation(job_type='FULL',
                                         validate_test_data=False)
        self.dr_helper.source_subclient = self.group_name

    @test_step
    def verify_overview(self):
        """Verifies the details of the replication group in the overview tab"""
        self.replication_helper.verify_overview(group_name=self.group_name,
                                                source_hypervisor=self.source_hypervisor,
                                                recovery_target=self.recovery_target,
                                                source_vendor=self._source_vendor,
                                                destination_vendor=self._destination_vendor,
                                                replication_type=self._replication_type.name)

    @test_step
    def disable_enable_replication_group(self):
        """Disables the replication group and re-enables it to verify the group status"""
        self.replication_helper.verify_disable_enable_replication_group(self.group_name)

    @test_step
    def verify_configuration(self):
        """Verifies the details of the replication group in the configuration tab"""

        # Initial Frequency validation
        self.replication_helper.verify_frequency(group_name=self.group_name,
                                                 frequency_duration=self._frequency_duration,
                                                 frequency_unit=self._frequency_unit.value)

        # Frequency edit and validation [Incl Schedule validation]
        self.replication_helper.edit_frequency(group_name=self.group_name,
                                               frequency_duration=self._frequency_duration_edit,
                                               frequency_unit=self._frequency_unit_edit.value,
                                               navigate=False)
        self.replication_helper.verify_frequency(group_name=self.group_name,
                                                 frequency_duration=self._frequency_duration_edit,
                                                 frequency_unit=self._frequency_unit_edit.value,
                                                 navigate=False)
        self.dr_helper.verify_schedules(group_name=self.group_name,
                                        frequency_duration=self._frequency_duration_edit,
                                        frequency_unit=self._frequency_unit_edit.value)

        # Frequency reset and schedule validation
        self.replication_helper.edit_frequency(group_name=self.group_name,
                                               frequency_duration=self._frequency_duration,
                                               frequency_unit=self._frequency_unit.value,
                                               navigate=False)
        self.dr_helper.verify_schedules(group_name=self.group_name,
                                        frequency_duration=self._frequency_duration,
                                        frequency_unit=self._frequency_unit.value)

        # Storage validation
        self.replication_helper.verify_storage(group_name=self.group_name,
                                               storage_list=self._storage_list,
                                               navigate=False)

        # Recovery Options validation - Advanced Options
        labels = self.admin_console.props
        expected_content = {
            labels["warning.overwriteVM"]: self._unconditionally_overwrite,
            labels["label.priorityInterval"]: f"{self._delay_between_priorities} minutes",
            labels["label.continueOnFailure"]: self._continue_to_next_priority
        }
        self.replication_helper.verify_advanced_options(group_name=self.group_name,
                                                        expected_content=expected_content)

        # Recovery Options validation - VM Override details validation
        vm_details_expected = {
            vm_name: {
                labels["label.destinationVm"]: f"{self.target_details.vm_prefix}{vm_name}{self.target_details.vm_suffix}",
                labels["label.resourceGroup"]: self.target_details.resource_group,
                labels["label.storageAccount"]: self.target_details.storage_account,
                labels["label.vmSize"]: self.target_details.vm_size
            }
            for vm_name in self.source_vms[1:]
        }
        vm_details_expected[self.source_vms[0]] = {
            labels["label.destinationVm"]: self.drvm_name,
            labels["label.resourceGroup"]: self.resource_group,
            labels["label.storageAccount"]: self.storage_account,
            labels["label.vmSize"]: self.vm_size

        }

        self.replication_helper.verify_configuration_vm_details(group_name=self.group_name,
                                                                source_vms=self.source_vms,
                                                                expected_content=vm_details_expected)

    @test_step
    def verify_replication_monitor(self):
        """Verify replication monitor table contains configured replication group"""
        self.replication_helper.verify_replication_monitor(group_name=self.group_name,
                                                           source_vms=self.source_vms,
                                                           frequency_duration=self._frequency_duration,
                                                           frequency_unit=self._frequency_unit.name)

    @test_step
    def verify_deletion(self):
        """Verify replication group, vm group and schedules are deleted"""
        self.delete_replication_group()
        sleep(180)
        self.replication_helper.verify_group_deletion(self.group_name)

    @test_step
    def verify_edit_vm_details(self, after_edit=False, vm_id=1, vm_details_validation: bool = True,
                               disabled_field_validation: bool = True, navigate: bool = True):
        """Verifies the data on the edit VM page"""
        observed_field_detatils = self.replication_helper.get_edit_vm_details(group_name=self.group_name,
                                                                              vm_name=self.source_vms[vm_id - 1],
                                                                              vendor_name=self._destination_vendor,
                                                                              navigate=navigate)

        # VM Details validation
        if vm_details_validation:
            self._verify_vm_details(observed_field_detatils=observed_field_detatils.get("field_values"), after_edit=after_edit, vm_id=vm_id)

        # Disabled Field validation
        if disabled_field_validation:
            self.replication_helper.verify_disabled_fields(observed_field_statuses=observed_field_detatils.get("field_statuses"))

    @test_step
    def edit_vm_details(self, vm_id=1, navigate: bool = True):
        """Modify the group details to check if the detail change is registered on Command Center"""
        edit_vm: EditAzureVirtualMachine = self.replication_helper.edit_vm(self.group_name,
                                                                         self.source_vms[vm_id - 1],
                                                                         self._destination_vendor,
                                                                         navigate=navigate)
        edit_vm.select_availability_zone(self.availability_zone_2)
        edit_vm.select_virtual_network(self.virtual_network_2)
        edit_vm.select_security_group(self.security_group_2)
        edit_vm.select_vm_size(self.vm_size_2)
        edit_vm.save()

    def run(self):
        """Runs the testcase in order"""
        try:
            self.login()
            self.delete_replication_group()
            self.configure_replication_group()
            self.verify_replication_group_exists()
            self.verify_vm_group_exists()

            self.logout()
            self.verify_sync_completion()
            self.login()

            self.verify_overview()
            self.disable_enable_replication_group()
            self.verify_configuration()

            self.verify_edit_vm_details(after_edit=False, vm_id=1)
            self.verify_edit_vm_details(after_edit=False, vm_id=2, navigate=False)

            self.edit_vm_details(navigate=False)

            self.verify_edit_vm_details(after_edit=True, vm_id=1, navigate=True)
            self.verify_edit_vm_details(after_edit=True, vm_id=2, navigate=False)

            self.verify_replication_monitor()
            self.verify_deletion()

        except Exception as _exception:
            self.utils.handle_testcase_exception(_exception)

    def tear_down(self):
        """Tears down the TC"""
        self.logout()
