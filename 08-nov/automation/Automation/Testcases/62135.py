# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case for Validation of Replication Group CRUD from VM Group

Sample input:
"62135": {
            "tenant_username" : "tenant\\admin",
            "tenant_password" : "password",
            "ClientName" : "hypervisor",
            "vm_group" : "vm_group_name",
            "source_vms" : ["vm1"],
            "copy_for_replication" : "copy_name",
            "media_agent" : "media_agent_name",
            "recovery_target" : "recovery_target_name",
            "access_node" : "access_node_1",
            "access_node_2" : "access_node_2"
       }

"""
from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.recovery_targets import RecoveryTarget
from DROrchestration.replication import Replication
from DROrchestration.DRUtils.DRConstants import Vendors_Complete, ReplicationType, SiteOption, TimePeriod, VendorTransportModes, Vendor_PolicyType_Mapping, Vendor_Instancename_Mapping
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils import OptionsHelper
from Web.AdminConsole.Helper.dr_helper import ReplicationHelper, DRHelper
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

from Web.AdminConsole.DR.virtualization_replication import ConfigureAWSVM, _AWSVMOptions, ConfigureAzureVM, ConfigureHypervVM, ConfigureVMWareVM


class TestCase(CVTestCase):
    """Test case to verify configuring AWS replication group using secondary/tertiary copy."""

    test_step = TestStep()

    def __init__(self):
        """Initialises the objects and TC inputs"""
        CVTestCase.__init__(self)
        self.name = "Validation of Replication Group CRUD from VM Group"

        self.tcinputs = {
            "tenant_username": None,
            "tenant_password": None,
            "ClientName": None,
            "vm_group": None,
            "source_vms": None,
            "copy_for_replication": None,
            "media_agent": None,
            "recovery_target": None,
            "access_node": None,
            "access_node_2": None,
        }
        self.source_hypervisor = None
        self.vm_group = None
        self.source_vms = None
        self.copy_for_replication = None
        self.media_agent = None
        self.recovery_target = None
        self.access_node = None
        self.access_node_2 = None

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
        self.vm_group = self.tcinputs["vm_group"]
        self.source_vms = self.tcinputs["source_vms"]
        self.copy_for_replication = self.tcinputs["copy_for_replication"]
        self.media_agent = self.tcinputs["media_agent"]
        self.recovery_target = self.tcinputs["recovery_target"]
        self.access_node = self.tcinputs["access_node"]
        self.access_node_2 = self.tcinputs["access_node_2"]
        
        self._replication_type = ReplicationType.Orchestrated
        self._siteoption = SiteOption.HotSite
        self._enable_replication = True

        self._validate_drvm = True
        self._unconditionally_overwrite = True
        self._continue_to_next_priority = True
        self._delay_between_priorities = 5

        self.target_details: RecoveryTarget = self.commcell.recovery_targets.get(self.recovery_target)
        self.dr_helper = DRHelper(self.commcell, self.csdb, self.client)
        self.dr_helper.source_subclient = self.vm_group

        # Source Vendor
        self._source_vendor = Vendor_Instancename_Mapping(self.dr_helper.source_auto_instance.get_instance_name()).name
        self._source_vendor = getattr(Vendors_Complete, self._source_vendor)
        
        # Destination Vendor
        self._destination_vendor = Vendor_PolicyType_Mapping(self.target_details.policy_type).name
        self._destination_vendor = getattr(Vendors_Complete, self._destination_vendor)

        # Frequency - from Plan
        self._frequency_duration, self._frequency_unit = self.dr_helper.get_rpo_from_usercreated_plan()
        
    def _get_advanced_options(self, destination_vendor: str):
        labels = self.admin_console.props
        expected_content = {
            labels["warning.overwriteVM"]: self._unconditionally_overwrite,
            labels["label.priorityInterval"]: f"{self._delay_between_priorities} minutes",
            labels["label.continueOnFailure"]: self._continue_to_next_priority
        }
        match destination_vendor:
            case Vendors_Complete.AWS.value:
                expected_content[labels["header.transportMode"]] = VendorTransportModes.AWS.Automatic.value
                expected_content[labels["label.powerOn.replication"]] = self._validate_drvm
            case _:
                pass
        return expected_content

    @property
    def group_name(self):
        """Returns the replication group name"""
        return f"{self.replication_helper.group_name(self.id)}_{self._source_vendor.name}_{self._destination_vendor.name}"

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
        self.replication_helper.delete_replication_group(self.group_name)

    @test_step
    def configure_replication_group(self):
        """Create an Orchestrated Replication Group"""
        self.admin_console.navigator.navigate_to_replication_groups()
        configure_rg = self.replication_group.configure_virtualization(source_vendor=self._source_vendor.value,
                                                                       destination_vendor=self._destination_vendor.value,
                                                                       replication_type=self._replication_type.value)

        # Type Hinting
        configure_rg: ConfigureAWSVM | ConfigureAzureVM | ConfigureHypervVM | ConfigureVMWareVM

        # General
        configure_rg.content.set_name(self.group_name)
        configure_rg.content.select_production_site_hypervisor(self.source_hypervisor)
        configure_rg.next()

        # Content
        configure_rg.content.select_vm_from_browse_tree(vm_info=self.source_vms,
                                                        expand_folder=False,
                                                        vm_group=self.vm_group)
        configure_rg.next()

        # Storage
        configure_rg.storage_cache.select_copy_for_replication(self.copy_for_replication)
        configure_rg.storage_cache.select_media_agent(self.media_agent)
        configure_rg.next()

        # Recovery Options
        configure_rg.recovery_options.select_recovery_target(self.recovery_target)
        configure_rg.recovery_options.select_access_node(self.access_node)
        configure_rg.recovery_options.select_rto(self._siteoption.value)
        configure_rg.next()

        # TODO : Pre-Post Scripts (Configuration)
        configure_rg.next()

        # VM Overrides
        configure_rg.next()

        # Advanced Options
        configure_rg.advanced_options.unconditionally_overwrite_vm(self._unconditionally_overwrite)
        configure_rg.advanced_options.continue_to_next_priority(self._continue_to_next_priority)
        configure_rg.advanced_options.set_delay_between_priority(self._delay_between_priorities)
        configure_rg.next()

        # Submit group creation request
        configure_rg.finish()

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
    def verify_sync_completion(self):
        """Verifies that the sync has completed on the created replication group"""
        self.replication = Replication(self.commcell, self.group_name)
        self.replication.get_running_replication_jobs()
        self.replication.post_validation(job_type='FULL',
                                         validate_test_data=False,
                                         replication_proxy=[self.access_node.lower()])

    @test_step
    def verify_overview(self):
        """Verifies the details of the replication group in the overview tab"""
        self.replication_helper.verify_overview(group_name=self.group_name,
                                                source_hypervisor=self.source_hypervisor,
                                                recovery_target=self.recovery_target,
                                                source_vendor=self._source_vendor.value,
                                                destination_vendor=self._destination_vendor.value,
                                                replication_type=self._replication_type.name,
                                                vm_group=self.vm_group,
                                                access_node=self.access_node)

    @test_step
    def disable_enable_replication_group(self):
        """Disables the replication group and re-enables it to verify the group status"""
        self.replication_helper.verify_disable_enable_replication_group(group_name=self.group_name,
                                                                        replication_type=self._replication_type.name)

    @test_step
    def verify_configuration(self):
        """Verifies the details of the replication group in the configuration tab"""

        # NOTE : Frequency not set at RG level (Orchestrated Replication)
        self.dr_helper.verify_schedules(group_name=self.group_name,
                                        vm_group=self.vm_group,
                                        repliction_type=self._replication_type.name)

        # Recovery Options validation - Advanced Options
        expected_content = self._get_advanced_options(self._destination_vendor.value)
        self.replication_helper.verify_advanced_options(group_name=self.group_name,
                                                        expected_content=expected_content)

    @test_step
    def validate_access_node_update(self):
        """
        Validates the access node update

        Steps:
            1. Update the access node
            2. Initiate backup and wait for sync completion
            3. Verify the access node used for replication
        """

        # Update Access Node
        self.replication_helper.update_access_node(group_name=self.group_name,
                                                   access_node=self.access_node_2)
        self.logout()

        # NOTE : Implemented to avoid exceptions during function debugging
        self.replication = Replication(self.commcell, self.group_name) if not self.replication else self.replication
        
        # Backup and wait for sync completion
        backup_options = OptionsHelper.BackupOptions(self.replication.auto_subclient)
        backup_options.backup_type = "INCREMENTAL"
        self.replication.auto_subclient.backup(backup_options,
                                               skip_discovery=True,
                                               skip_backup_job_type_check=True)
        sleep(120)  # For Aux
        self.replication.get_running_replication_jobs()

        # Access Node validation
        for vm_pair in self.replication.vm_pairs.values():
            _replication = vm_pair['Replication']
            _replication.evaluate_replication_proxy(replication_proxy=[self.access_node_2.lower()])

        self.login()
    
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

    def run(self):
        """Runs the testcase in order"""
        try:
            self.login()
            self.delete_replication_group()
            self.configure_replication_group()
            self.verify_replication_group_exists()

            self.logout()
            self.verify_sync_completion()
            self.login()

            self.verify_overview()
            self.disable_enable_replication_group()
            self.verify_configuration()

            self.validate_access_node_update()

            self.verify_replication_monitor()
            self.verify_deletion()

        except Exception as _exception:
            self.utils.handle_testcase_exception(_exception)

    def tear_down(self):
        """Tears down the TC"""
        self.logout()

