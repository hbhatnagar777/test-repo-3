# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case to verify Hyper-v replication group creation and secondary copy job completion

Sample input:
"59723": {
            "tenant_username": <username>,
            "tenant_password": <password>,
            "ClientName": "hypervisor",
            "source_vms": ["vm1", "vm2"] # (Minimum 2)
            "recovery_target":"test-3",
            "network" : "Network1",
            "primary_storage_name" : "Storage1",
            "secondary_storage_name": "Storage2",
            "tertiary_storage_name": "Storage3"
       }

"""
from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.recovery_targets import RecoveryTarget
from DROrchestration.replication import Replication
from DROrchestration.DRUtils.DRConstants import Vendors_Complete, ReplicationType, SiteOption, TimePeriod
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.DR.virtualization_replication import ConfigureHypervVM


class TestCase(CVTestCase):
    """Test case to verify configuring Hyper-v replication group using secondary copy."""
    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        CVTestCase.__init__(self)
        self.name = "HyperV - Zeal Replication group CRUD test with Aux copy"

        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "ClientName": None,
            "source_vms": [],
            "recovery_target": None,
            "primary_storage_name": None,
            "secondary_storage_name": None,
            "tertiary_storage_name": None,
            "network": None,
        }
        self.source_hypervisor = None
        self.source_vms = None
        self.recovery_target = None
        self.primary_storage_name = None
        self.secondary_storage_name = None
        self.tertiary_storage_name = None

        self.network = None

        self.utils = None

        self.browser = None
        self.admin_console = None
        self.replication_helper = None
        self.replication_group = None
        self.group_details = None

        self.target_details = None
        self.destination_vm_list = None
        self.replication = None

    def setup(self):
        """Sets up the Testcase"""
        self.utils = TestCaseUtils(self)
        self.source_hypervisor = self.tcinputs["ClientName"]
        self.source_vms = self.tcinputs["source_vms"]
        self.recovery_target = self.tcinputs["recovery_target"]
        self.network = self.tcinputs['network']
        self.primary_storage_name = self.tcinputs["primary_storage_name"]
        self.secondary_storage_name = self.tcinputs["secondary_storage_name"]
        self.tertiary_storage_name = self.tcinputs["tertiary_storage_name"]

        self._storage_list = [self.primary_storage_name,
                              self.secondary_storage_name,
                              self.tertiary_storage_name]

        self._source_vendor = Vendors_Complete.HYPERV.value
        self._destination_vendor = Vendors_Complete.HYPERV.value
        self._replication_type = ReplicationType.Periodic
        self._siteoption = SiteOption.HotSite
        self._enable_replication = True

        self._frequency_duration = 4
        self._frequency_unit = TimePeriod.HOURS
        self._frequency_duration_edit = 8
        self._frequency_unit_edit = TimePeriod.DAYS

        self._validate_drvm = True
        self._unconditionally_overwrite = True
        self._continue_to_next_priority = True
        self._delay_between_priorities = 5

        self.target_details: RecoveryTarget = self.commcell.recovery_targets.get(
            self.recovery_target)

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

            self.replication_helper = ReplicationHelper(self.commcell, self.admin_console)
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
        """Create a replication group with an aux copy and overrides"""
        self.admin_console.navigator.navigate_to_replication_groups()
        hyperv_configure = self.replication_group.configure_virtualization(source_vendor=self._source_vendor,
                                                                           destination_vendor=self._destination_vendor,
                                                                           replication_type=self._replication_type.value)

        # Type Hinting
        hyperv_configure: ConfigureHypervVM

        # General
        hyperv_configure.content.set_name(self.group_name)
        hyperv_configure.content.select_production_site_hypervisor(self.source_hypervisor)
        hyperv_configure.next()

        # Content
        hyperv_configure.content.select_vm_from_browse_tree(self.source_vms, expand_folder=False)
        hyperv_configure.next()

        # Storage
        _storagecopy = hyperv_configure.storage_cache.Storage_Copy
        hyperv_configure.storage_cache.select_storage(self.primary_storage_name,
                                                     storage_copy=_storagecopy.Primary.value)
        hyperv_configure.storage_cache.select_storage(self.secondary_storage_name,
                                                     storage_copy=_storagecopy.Secondary.value)
        hyperv_configure.storage_cache.select_storage(self.tertiary_storage_name,
                                                     storage_copy=_storagecopy.Tertiary.value)
        hyperv_configure.next()

        # Recovery Options
        hyperv_configure.recovery_options.select_recovery_target(self.recovery_target)
        hyperv_configure.recovery_options.set_frequency(frequency_duration=self._frequency_duration,
                                                       frequency_period=self._frequency_unit.value)
        hyperv_configure.recovery_options.select_rto(self._siteoption.value)
        hyperv_configure.recovery_options.replication_on_group_creation(self._enable_replication)
        hyperv_configure.next()

        # TODO : Override Options, if required (for Multi-VM Override)
        hyperv_configure.next()

        # Advanced Options
        hyperv_configure.advanced_options.validate_destination_vm(self._validate_drvm)
        hyperv_configure.advanced_options.unconditionally_overwrite_vm(self._unconditionally_overwrite)
        hyperv_configure.advanced_options.continue_to_next_priority(self._continue_to_next_priority)
        hyperv_configure.advanced_options.set_delay_between_priority(self._delay_between_priorities)
        hyperv_configure.next()

        # Submit group creation request
        hyperv_configure.finish()

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
        self.replication_helper.verify_vm_group_exists(self.group_name,
                                                       self._source_vendor,
                                                       self.source_hypervisor)

    @test_step
    def verify_sync_completion(self):
        """Verifies that the sync has completed on the created replication group"""
        self.replication = Replication(self.commcell, self.group_name)
        self.replication.wait_for_first_backup()
        sleep(120)
        self.replication.get_running_replication_jobs()
        self.replication.post_validation(job_type='FULL', validate_test_data=False)

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

        # Frequency validation
        self.replication_helper.verify_frequency(group_name=self.group_name,
                                                 frequency_duration=self._frequency_duration,
                                                 frequency_unit=self._frequency_unit.value)
        self.replication_helper.edit_frequency(group_name=self.group_name,
                                               frequency_duration=self._frequency_duration_edit,
                                               frequency_unit=self._frequency_unit_edit.value,
                                               navigate=False)
        self.replication_helper.verify_frequency(group_name=self.group_name,
                                                 frequency_duration=self._frequency_duration_edit,
                                                 frequency_unit=self._frequency_unit_edit.value,
                                                 navigate=False)

        # Storage validation
        self.replication_helper.verify_storage(group_name=self.group_name,
                                               storage_list=self._storage_list,
                                               navigate=False)

        # Recovery Options validation - Advanced Options
        labels = self.admin_console.props
        expected_content = {
            labels["label.powerOn.replication"]: self._validate_drvm,
            labels["warning.overwriteVM"]: self._unconditionally_overwrite,
            labels["label.priorityInterval"]: f"{self._delay_between_priorities} minutes",
            labels["label.continueOnFailure"]: self._continue_to_next_priority
        }
        self.replication_helper.verify_advanced_options(group_name=self.group_name,
                                                        expected_content=expected_content)

        # Recovery Options validation - VM Override details validation
        vm_details_expected = {vm_name: {
            labels["label.destinationVm"]: f"{self.target_details.vm_prefix}{vm_name}{self.target_details.vm_suffix}",
            labels["label.esxHostHyperV"]: self.target_details.destination_host,
            labels["label.destinationFolder"]: self.target_details.vm_folder,
        } for vm_name in self.source_vms}

        self.replication_helper.verify_configuration_vm_details(group_name=self.group_name,
                                                                source_vms=self.source_vms,
                                                                expected_content=vm_details_expected)

    @test_step
    def verify_replication_monitor(self):
        """Verify replication monitor table contains configured replication group"""
        self.replication_helper.verify_replication_monitor(group_name=self.group_name,
                                                           source_vms=self.source_vms,
                                                           frequency_duration=self._frequency_duration_edit,
                                                           frequency_unit=self._frequency_unit_edit.name)

    @test_step
    def verify_deletion(self):
        """Verify replication group, vm group and schedules are deleted"""
        self.delete_replication_group()
        sleep(180)
        self.replication_helper.verify_group_deletion(self.group_name)

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

            self.verify_replication_monitor()
            self.verify_deletion()

        except Exception as _exception:
            self.utils.handle_testcase_exception(_exception)

    def tear_down(self):
        """Tears down the TC"""
        self.logout()
