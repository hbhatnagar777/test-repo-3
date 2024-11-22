# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations for Disaster Recovery

Class:

  DRHelper()

Functions:

"""
from time import sleep
from enum import Enum
from cvpysdk.exception import SDKException
from cvpysdk.commcell import Commcell
from cvpysdk.client import Client
from cvpysdk.schedules import Schedule
from AutomationUtils.database_helper import CommServDatabase
from AutomationUtils.logger import get_log
from DROrchestration.DRUtils.DRConstants import ReplicationType, SiteOption, TimePeriod, Vendors_Complete
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils import VirtualServerHelper
from VirtualServer.VSAUtils.LiveSyncUtils import LiveSyncUtils
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.DR.test_failover_vms import TestFailoverVMs
from Web.AdminConsole.DR.replication import ReplicationGroup
from Web.AdminConsole.DR.group_details import ReplicationDetails, EditAWSVirtualMachine
from Web.AdminConsole.DR.monitor import ReplicationMonitor
from Web.AdminConsole.VSAPages.vm_groups import VMGroups
from cvpysdk.plan import Plan
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type


class ReplicationHelper:
    """This class is a wrapper used to perform replication common tasks in testcases"""

    class ConfigureGroupMap(Enum):
        VMWARE = 'configure_vmware'
        AZURE = 'configure_azure'
        HYPERV = 'configure_hyperv'
        AWS = 'configure_aws'

    class Operationlevel(Enum):
        """Enum Class for replication operation level"""
        GROUP = 0
        MONITOR = 1
        OVERVIEW = 2
        CONFIGURATION = 3

    class ReplicationType(Enum):
        """Enum Class for replication type to ID mapping"""
        Periodic = 'PERIODIC'
        Orchestrated = 'BACKUP'
        Continuous = 'CONTINUOUS'

    def __init__(self, commcell_object: Commcell, admin_console: AdminConsole):
        """Initialise all classes from commcell object and admin console object"""
        self.commcell = commcell_object
        self._admin_console = admin_console
        self._log = get_log()
        self._navigator = self._admin_console.navigator

        self.vm_groups = VMGroups(self._admin_console)
        self.replication_groups = ReplicationGroup(self._admin_console)
        self.group_details = ReplicationDetails(self._admin_console)
        self.replication_monitor = ReplicationMonitor(self._admin_console)
        self.test_failover_details = TestFailoverVMs(self._admin_console)

        self._admin_console.load_properties(self)
        self._labels = self._admin_console.props

    @staticmethod
    def group_name(tc_id):
        """Returns the group name for the given testcase #"""
        return f'Group_TC_{tc_id}'

    @staticmethod
    def get_plan_name(group_name: str):
        """Returns the plan name of the replication group"""
        return f"{group_name}_ReplicationPlan"

    @staticmethod
    def get_schedule_name(group_name: str, replication_type: str = ReplicationType.Periodic.name):
        """Returns the schedule name associated with the replication group"""
        schedule_name = ReplicationGroup.get_schedule_name_by_replication_group(group_name) if replication_type == ReplicationType.Periodic.name else group_name
        return schedule_name

    @staticmethod
    def get_schedule_policy_name(group_name: str):
        """Returns the schedule Policy name associated with the replication group"""
        return group_name + '_ReplicationPlan Schedule policy'

    @staticmethod
    def assert_comparison(value, expected):
        """
        Alias for assert_comparison from testcaseutils class
        value       (any): Existent value
        expected    (any): Expected value to be compared with
        """
        TestCaseUtils.assert_comparison(value, expected)

    @staticmethod
    def assert_includes(value, array):
        """
        Alias for assert_includes from testcaseutils class
        value       (any): Existent value
        array       (any): Any array/iterable to be searched for
        """
        TestCaseUtils.assert_includes(value, array)

    def _navigate_and_access_group(self, group_name: str):
        """Navigate to Replication Groups and access the group"""
        self._navigator.navigate_to_replication_groups()
        self.replication_groups.access_group(group_name)

    def add_vm_to_group_configuration(self, group_name: str, source_vm: dict | list, vendor_name: Vendors_Complete.VMWARE.value, view_mode=None):
        """
        Adds virtual machines to a group in the admin console.

        Args:
            group_name (str): The name of the group to add virtual machines to.
            source_vm (dict | list): The virtual machine to add. Can be a dictionary (with path) or a list.

        Raises:
            CVTestStepFailure: If the expected value of the source VM does not match the collected value.
        """
        self._navigate_and_access_group(group_name=group_name)
        self.group_details.access_configuration_tab()

        # Add VM to group
        self.group_details.configuration.add_virtual_machines(source_vms=source_vm, vendor_name=vendor_name,
                                                              view_mode=view_mode)
        self._admin_console.refresh_page()

        # Verify the VM is added to the group
        source_vm_name = source_vm[0] if isinstance(source_vm, list) else list(source_vm.values())[0][0]
        new_vm_details = self.group_details.configuration.get_vm_details(source_vm_name)
        if new_vm_details['Source VM'] != source_vm_name:
            raise CVTestStepFailure(
                f"Expected value of Source VM {source_vm_name} does not match "
                f"the collected value {new_vm_details['Source VM']}")

        self._log.info(f"VM added to group and validated")

    def delete_vm_from_group_configuration(self, group_name: str, source_vm: dict | list):
        """
        Deletes virtual machines from the configuration tab of the group in the admin console.

        Args:
            group_name (str): The name of the group to delete virtual machines from.
            source_vm (dict | list): The virtual machine to delete. Can be a dictionary (with path) or a list.

        Raises:
            CVTestStepFailure: If the virtual machine could not be deleted successfully.
        """
        self._navigate_and_access_group(group_name=group_name)
        self.group_details.access_configuration_tab()
        source_vm_name = source_vm[0] if isinstance(source_vm, list) else list(source_vm.values())[0][0]

        # Remove VM from group
        self.group_details.configuration.remove_virtual_machines(source_vm_name)
        self._admin_console.refresh_page()

        # Verify the VM is removed from the group
        try:
            self.group_details.configuration.get_vm_details(source_vm_name)
            raise CVTestStepFailure("VM could not be deleted successfully")
        except Exception as _exception:
            self._log.info(f"VM deleted from group successfully and validated")

    def add_delete_vm_to_group_configuration(self, group_name: str, source_vm: dict | list, vendor_name: Vendors_Complete.VMWARE.value, view_mode=None):
        """
        Adds and deletes virtual machines to/from a group in the admin console.

        Args:
            group_name (str): The name of the group to add/delete virtual machines from.
            source_vm (dict | list): The virtual machine to add/delete. Can be a dictionary (with path) or a list.
            vendor_name (str): The vendor name

        Raises:
            CVTestStepFailure: If the expected value of the source VM does not match the collected value.
            CVTestStepFailure: If the virtual machine could not be deleted successfully.
        """
        self.add_vm_to_group_configuration(group_name, source_vm, vendor_name, view_mode=view_mode)
        self.delete_vm_from_group_configuration(group_name, source_vm)

    def perform_planned_failover(self, replication_group, retain_blob, vms=None, operation_level=Operationlevel.GROUP):
        """
            Performs an unplanned failover operation
            Args:
                replication_group   (string)   --   Name of the replication group
                vms   (list)   --   VM's present in the replication group on
                                    which the operation should perform
                retain_blob    --   For Azure destination during failover whether blobs to be retained or not
                operation_level  (string)   --   OperationLevel Enum
            Returns:    Returns the job id of the unplanned failover operation
        """
        if vms is None:
            vms = []
        if operation_level == self.Operationlevel.MONITOR:
            self._navigator.navigate_to_replication_monitor()
            return self.replication_monitor.planned_failover(vms, replication_group)

        self._navigate_and_access_group(replication_group)
        if operation_level == self.Operationlevel.OVERVIEW:
            self.group_details.access_monitor_tab()
            return self.replication_monitor.planned_failover(vms, None)
        if operation_level == self.Operationlevel.GROUP:
            return self.group_details.planned_failover(retain_blob)
        raise CVTestStepFailure("Invalid options provided. Please check!")

    def perform_unplanned_failover(self, replication_group, retain_blob=True, vms=None, operation_level=Operationlevel.GROUP):
        """
            Performs an unplanned failover operation
            Args:
                replication_group   (string)   --   Name of the replication group
                retain_blob    --   For Azure destination during failover whether blobs to be retained or not
                vms   (list)   --   VM's present in the replication group on which
                                    the operation should perform
                operation_level  (string)   --   OperationLevel Enum
            Returns:    Returns the job id of the unplanned failover operation
        """
        if vms is None:
            vms = []
        if operation_level == self.Operationlevel.MONITOR:
            self._navigator.navigate_to_replication_monitor()
            return self.replication_monitor.unplanned_failover(vms, replication_group)

        self._navigate_and_access_group(replication_group)
        if operation_level == self.Operationlevel.OVERVIEW:
            self.group_details.access_monitor_tab()
            return self.replication_monitor.unplanned_failover(vms, None)
        if operation_level == self.Operationlevel.GROUP:
            return self.group_details.unplanned_failover(retain_blob)

        raise CVTestStepFailure("Invalid options provided. Please check!")

    def perform_failback(self, replication_group, vms=None, operation_level=Operationlevel.GROUP):
        """
            Performs an unplanned failover operation
            Args:
                replication_group   (string)   --   Name of the replication group
                vms   (list)   --   VM's present in the replication group
                                    on which the operation should perform
                operation_level  (Enum)   --   OperationLevel Enum
            Returns:    Returns the job id of the unplanned failover operation
        """

        if vms is None:
            vms = []
        if operation_level == self.Operationlevel.MONITOR:
            self._navigator.navigate_to_replication_monitor()
            return self.replication_monitor.failback(vms, replication_group)

        self._navigate_and_access_group(replication_group)
        if operation_level == self.Operationlevel.OVERVIEW:
            self.group_details.access_monitor_tab()
            return self.replication_monitor.failback(vms, None)
        if operation_level == self.Operationlevel.GROUP:
            return self.group_details.failback()
        raise CVTestStepFailure("Invalid options provided. Please check!")

    def perform_undo_failover(self, replication_group, vms=None, operation_level=Operationlevel.GROUP,
                              destination_vms=None, is_continuous=False):
        """
            Performs an undo failover operation
            Args:
                replication_group   (string)   --   Name of the replication group
                vms   (list)   --   VM's present in the replication group
                                    on which the operation should perform
                operation_level  (Enum)   --   OperationLevel Enum
                destination_vms (list)  --  List of names of DR VM's
                is_continuous   (bool)  -- Set True if pair is of continuous type
            Returns:    Returns the job id of the undo failover operation
        """

        if vms is None:
            vms = []
        if operation_level == self.Operationlevel.MONITOR:
            self._navigator.navigate_to_replication_monitor()
            if is_continuous:
                self._navigator.navigate_to_continuous_replication()
                for vm in range(0, len(vms)):
                    self.continuous_monitor.resume(vms[vm], destination_vms[vm])
                return
            else:
                return self.replication_monitor.undo_failover(vms, replication_group)

        self._navigate_and_access_group(replication_group)
        if operation_level == self.Operationlevel.OVERVIEW:
            self.group_details.access_monitor_tab()
            if is_continuous:
                for vm in range(0, len(vms)):
                    self.continuous_monitor.resume(vms[vm], destination_vms[vm])
                return
            else:
                return self.replication_monitor.undo_failover(vms, None)
        if operation_level == self.Operationlevel.GROUP:
            if is_continuous:
                self.group_details.resume()
                return
            else:
                return self.group_details.undo_failover()
        raise CVTestStepFailure("Invalid options provided. Please check!")

    def perform_test_failover(self, replication_group, vms=None, operation_level=Operationlevel.GROUP):
        """
            Performs an Test Failover operation
            Args:
                replication_group   (string)   --   Name of the replication group
                vms   (list)   --   VM's present in the replication group on
                                    which the operation should perform
                operation_level  (string)   --   OperationLevel Enum
            Returns:    Returns the job id of the Test Failover operation
        """
        if vms is None:
            vms = []
        if operation_level == self.Operationlevel.MONITOR:
            self._navigator.navigate_to_replication_monitor()
            job_list = [self.replication_monitor.test_failover(vm, replication_group) for vm in vms]
            return job_list

        self._navigate_and_access_group(replication_group)
        if operation_level == self.Operationlevel.OVERVIEW:
            self.group_details.access_monitor_tab()
            job_list = [self.replication_monitor.test_failover(vm, None) for vm in vms]
            return job_list

        if operation_level == self.Operationlevel.GROUP:
            job_list = [self.group_details.test_failover()]
            return job_list

        raise CVTestStepFailure("Invalid options provided. Please check")

    def perform_replicate_now(self, replication_group, vms: list = None, operation_level=Operationlevel.OVERVIEW):
        """
            Performs Replicate Now operation
            Args:
                replication_group   (string)   --   Name of the replication group
                vms   (list)   --   VM's present in the replication group on
                                    which the operation should perform
                operation_level  (string)   --   OperationLevel Enum
            Returns:    Returns the job id of the Replicate Now operation
        """
        if vms is None:
            vms = []
        if operation_level == self.Operationlevel.MONITOR:
            self._navigator.navigate_to_replication_monitor()
            job_list = [self.replication_monitor.replicate_now(vm, replication_group) for vm in vms]
            return job_list

        self._navigate_and_access_group(group_name=replication_group)
        if operation_level == self.Operationlevel.OVERVIEW:
            self.group_details.access_monitor_tab()
            job_list = [self.replication_monitor.replicate_now(vm, None) for vm in vms]
            return job_list

        if operation_level == self.Operationlevel.GROUP:
            job_list = [self.group_details.replicate_now()]
            return job_list

        raise CVTestStepFailure("Invalid options provided. Please check")

    def view_test_failover_vms(self, replication_group, vms: list = [], operation_level=Operationlevel.GROUP):
        """
        View Test Failover VMs

        Args:
            replication_group (string): Name of the replication group.
            vms (list): Source VMs on which the operation should be performed.
            operation_level (string): OperationLevel Enum.

        Returns:
            dict: A dictionary containing the source VMs as key and the corresponding cloned VMs

        Raises:
            CVTestStepFailure: If invalid options are provided.
        """
        cloned_vms = dict()

        if operation_level == self.Operationlevel.MONITOR:
            self._navigator.navigate_to_replication_monitor()
            for vm in vms:
                cloned_vms.update(self.replication_monitor.view_test_failover_vms([vm], replication_group))
        elif operation_level == self.Operationlevel.OVERVIEW:
            for vm in vms:
                self._navigate_and_access_group(replication_group)
                self.group_details.access_monitor_tab()
                cloned_vms.update(self.replication_monitor.view_test_failover_vms([vm], None))
        elif operation_level == self.Operationlevel.GROUP:
            self._navigate_and_access_group(replication_group)
            cloned_vms.update(self.group_details.view_test_failover_vms(vms))
        else:
            raise CVTestStepFailure("Invalid options provided. Please check!")

        return cloned_vms

    def delete_test_failover_clones(self, replication_group, source_vms: list = [], cloned_vms: list = [], operation_level=Operationlevel.GROUP):
        """
        Deletes the cloned VMs
            Args:
                replication_group   (string)   --   Name of the replication group
                source_vms   (list)   --   Source VM names in the replication group on which the operation should be perform
                cloned_vms   (list)   --   List of 'cloned VM names' to be deleted
                operation_level  (string)   --   OperationLevel Enum
            Logic:
                1. Navigate to Replication Monitor
                2. If the cloned vm names are not provided, get the cloned VM names from source VMs
                3. Delete the cloned VMs
        """
        _cloned_vms_data = self.view_test_failover_vms(
            replication_group, source_vms, operation_level)
        if not cloned_vms:
            # Fetch the cloned VM names
            cloned_vms = [[_property['Name'] for _property in value] for key, value in _cloned_vms_data.items()]

            # Flatten the list
            cloned_vms = [item for sublist in cloned_vms for item in (sublist if isinstance(sublist, list) else [sublist])]

        # Delete the cloned VMs
        [self.test_failover_details.delete_vm(_cloned_vm) for _cloned_vm in cloned_vms]

    def perform_mark_for_full_replication(self, replication_group, vms: list = None, operation_level=Operationlevel.OVERVIEW):
        """
            Performs Replicate Now operation
            Args:
                replication_group   (string)   --   Name of the replication group
                vms   (list)   --   VM's present in the replication group on
                                    which the operation should perform
                operation_level  (string)   --   OperationLevel Enum
            Returns:    Returns the job id of the Replicate Now operation
        """
        status_text = self._labels["notification.replication.VSAREP_PENDING"]
        status_list = list()
        if vms is None:
            vms = []

        if operation_level == self.Operationlevel.MONITOR:
            self._navigator.navigate_to_replication_monitor()
            status_list = [self.replication_monitor.mark_for_full_replication(vm, replication_group) for vm in vms]
        elif operation_level == self.Operationlevel.OVERVIEW:
            self._navigate_and_access_group(replication_group)
            self.group_details.access_monitor_tab()
            status_list = [self.replication_monitor.mark_for_full_replication(vm, None) for vm in vms]
        else:
            raise CVTestStepFailure("Invalid options provided. Please check")

        status_list = list(map(lambda status: status == status_text, status_list))
        return status_list

    def convert_group_site(self, group_name: str, warm_site: bool = True):
        """
        Convert group to Warm Site or Hot Site
        """
        self._navigator.navigate_to_replication_groups()
        self.replication_groups.access_group(group_name)
        notification_text = self.group_details.overview.summaryOperations.enable_or_disable_warm_sync(enable=warm_site)
        return notification_text

    def delete_replication_group(self, group_name: str, source_vms: list = None):
        """
        Delete the replication group and delete all the VMs associated to it
        group_name          (str): The replication group name
        source_vms          (list): The list of source VMs that are to be de-configured
                                    and deleted from command center
        """
        self._navigator.navigate_to_replication_groups()
        self._admin_console.refresh_page()
        if self.replication_groups.has_group(group_name):
            self.replication_groups.delete_group(group_name)
            sleep(10)
            self._admin_console.refresh_page()
            if self.replication_groups.has_group(group_name):
                raise CVTestStepFailure(f'Replication group [{group_name}] could not be deleted')
            self._log.info("Replication group [%s] deleted successfully", group_name)

        # Delete all the source VMs if passed
        if source_vms:
            for source_vm in source_vms:
                if self.commcell.clients.has_client(source_vm):
                    self.commcell.clients.delete(source_vm)

    def delete_vm_from_monitor(self, group_name: str, source_vms: list, delete_destination=True, operation_level=Operationlevel.OVERVIEW):
        """
        Deletes the VM from the replication monitor
        group_name          (str): The replication group name
        source_vms          (list): The list of source VMs that are to be deleted
        delete_destination  (bool): Whether to delete the destination VMs or not
        operation_level     (Enum): OperationLevel Enum

        Returns:    Returns the job id of the delete operation

        Raises:
            CVTestStepFailure: If invalid options are provided.
        """
        if operation_level == self.Operationlevel.MONITOR:
            self._navigator.navigate_to_replication_monitor()
            job_id = self.replication_monitor.delete(source=source_vms,
                                                     replication_group=group_name,
                                                     delete_destination=delete_destination)

        elif operation_level == self.Operationlevel.OVERVIEW:
            self._navigate_and_access_group(group_name=group_name)
            self.group_details.access_monitor_tab()
            job_id = self.group_details.monitorTab.remove_virtual_machines(source_vms=source_vms,
                                                                           delete_destination=delete_destination)

        else:
            raise CVTestStepFailure("Invalid options provided. Please check")

        return job_id

    def edit_vm(self, group_name: str, vm_name: str, vendor_name: str, navigate: bool = True):
        """Edits the VM details"""
        self._navigate_and_access_group(group_name=group_name) if navigate else None
        self.group_details.access_configuration_tab()

        return self.group_details.configuration.edit_virtual_machines(vm_name, vendor_name)

    def get_edit_vm_details(self, group_name: str, vm_name: str, vendor_name: str, 
                            field_values=True, field_statuses=True, navigate: bool = True):
        """Gets the details from the edit section"""
        self._navigate_and_access_group(group_name=group_name) if navigate else None
        self.group_details.access_configuration_tab()

        observed_field_values = self.group_details.configuration.get_vm_override_details(source_vm=vm_name,
                                                                                         vm_type=vendor_name,
                                                                                         field_values=field_values,
                                                                                         field_statuses=field_statuses)
        return observed_field_values

    def edit_frequency(self, group_name: str, frequency_duration: int, frequency_unit: str = TimePeriod.HOURS.value, navigate: bool = True):
        """edits the frequency in the configuration tab"""
        self._navigate_and_access_group(group_name=group_name) if navigate else None
        self.group_details.overview.rpoOperations.edit_replication_frequency(frequency_duration=frequency_duration, frequency_unit=frequency_unit)

    def add_storage(self, group_name: str, storage_name: str, storage_pool: str,
                    retention=2, retention_type="Week(s)"):
        """add storage in the configuration tab"""
        self._navigator.navigate_to_replication_groups()
        self.replication_groups.access_group(group_name)

        self.group_details.overview.storageOperations.add_storage(storage_name, storage_pool, retention, retention_type)

    def verify_overview(self, group_name: str, source_hypervisor: str, recovery_target: str,
                        source_vendor: str, destination_vendor: str,
                        replication_type: str, enable_replication: bool = True, warm_sync: str = False,
                        **kwargs):
        """Verifies the details of the replication group in the overview tab"""
        self._navigator.navigate_to_replication_groups()
        self.replication_groups.access_group(group_name)

        summary : dict = self.group_details.overview.summaryOperations.get_summary_details()

        observed_source_vendor, observed_destination_vendor = summary.get(self._labels["label.libraryVendorName"], " -> ").split(" -> ")

        self.assert_comparison(summary.get(self._labels["label.lifeCyclePolicy"]), recovery_target)
        self.assert_comparison(observed_source_vendor, source_vendor)
        self.assert_comparison(observed_destination_vendor, destination_vendor)
        self.assert_comparison(summary.get(self._labels["label.replicationType"]), f"{replication_type} replication")
        self.assert_comparison(summary.get(self._labels["label.enableLiveSync"]), enable_replication)
        self.assert_comparison(summary.get(self._labels["label.warmSiteRecovery"]), warm_sync)

        if replication_type == ReplicationType.Periodic.name:
            # Periodic Replication
            self.assert_comparison(summary.get(self._labels["label.sourceHypervisor"]), source_hypervisor)
        elif replication_type == ReplicationType.Orchestrated.name:
            # Orchestrated Replication 
            self.assert_comparison(summary.get(self._labels["label.source"]), f"{kwargs.get('vm_group', '')} ({source_hypervisor})")
            self.assert_comparison(summary.get(self._labels["label.accessNode"]), kwargs.get("access_node", ""))
            self.assert_comparison(summary.get(self._labels["label.autoUpdateVMs"]), kwargs.get("auto_update_vms", "No"))
        else:
            raise CVTestStepFailure("Invalid replication type provided")

    def verify_disable_enable_replication_group(self, group_name: str, replication_type=ReplicationType.Periodic.name):
        """Disables the replication group and re-enables it to verify the group status"""
        self._navigator.navigate_to_replication_groups()
        self.replication_groups.access_group(group_name)

        self.group_details.overview.summaryOperations.enable_disable_replication_group(enable=False)

        # Verify replication group has been disabled
        replication_group_status = self.group_details.overview.summaryOperations.get_summary_details().get(self._labels["label.enableLiveSync"])
        self.assert_comparison(replication_group_status, False)

        """ Verify Disable of Site Replication schedule """
        if replication_type != ReplicationType.Continuous.name:
            schedule_name = self.get_schedule_name(group_name=group_name,
                                                   replication_type=replication_type)
            schedule = self.commcell.schedules.get(schedule_name=schedule_name)
            if schedule.is_disabled:
                self._log.info("Schedule : "f'{schedule_name}'" is disabled")
            else:
                raise CVTestStepFailure(
                    f' The schedule :{schedule_name} is enabled, but must be disabled')

        self._admin_console.refresh_page()
        self.group_details.overview.summaryOperations.enable_disable_replication_group(enable=True)
        replication_group_status = self.group_details.overview.summaryOperations.get_summary_details().get(self._labels["label.enableLiveSync"])
        self.assert_comparison(replication_group_status, True)

        """  Verify Site Replication schedule is enabled """
        if replication_type != ReplicationType.Continuous.name:
            schedule.refresh()
            if not schedule.is_disabled:
                self._log.info("Schedule : "f'{schedule_name}'" is enabled")
            else:
                raise CVTestStepFailure(
                    f' The schedule :{schedule_name} is disabled, but must be enabled')

    def verify_disabled_fields(self, observed_field_statuses):
        """Verifies that the disabled fields are disabled or not"""
        if self.group_details.configuration.vendor_vm is None:
            raise CVTestStepFailure("Vendor VM configuration is not available")

        expected_disabled_fields = self.group_details.configuration.vendor_vm.expected_disabled_fields
        observed_disabled_fields = {key: value for key, value in observed_field_statuses.items() if value == True}

        self.assert_comparison(observed_disabled_fields, expected_disabled_fields)

    def verify_advanced_options(self, group_name: str, expected_content: dict, navigate : bool = True):
        """Verifies the advanced details of the replication group in the advanced tab"""
        self._navigate_and_access_group(group_name=group_name) if navigate else None
        self.group_details.access_advanced_tab()

        observed_advanced_options = self.group_details.advancedTab.advanced_options.get_advanced_options_details()
        self.assert_comparison(observed_advanced_options, expected_content)

    def verify_configuration_vm_details(self, group_name: str,
                                        source_vms: list,
                                        expected_content: dict = None,
                                        navigate: bool = True):
        """Verifies the advanced details of the replication group in the configuration tab"""
        self._navigate_and_access_group(group_name=group_name) if navigate else None
        self.group_details.access_configuration_tab()

        vm_details = self.group_details.configuration.get_all_vm_details()[1]

        # Basic validation
        observed_vms = [i.get("Source VM") for i in vm_details.values()]
        if not (set(observed_vms) == set(source_vms)):
            raise Exception(f"Expected VMs - [{source_vms}] ; Observed VMs - [{observed_vms}]")

        # Advanced validation
        if expected_content:
            for vm_detail in vm_details.values():
                source_vm = vm_detail.get("Source VM", "")
                for key, value in expected_content.get(source_vm).items():
                    self.assert_comparison(vm_detail.get(key, ""), value)

    def verify_replication_group_exists(self, group_name: str, source_hypervisor: str,
                                        target_name: str,
                                        site: str = SiteOption.HotSite.name,
                                        replication_type: str = ReplicationType.Periodic.name,
                                        group_state: str = "Enabled"):
        """
        Verifies that the replication group exists
        group_name          (str): The replication group name
        source_hypervisor   (str): The source hypervisor display name as shown in command center
        target_name         (str): The name of the target the replication group is associated to
        """
        self._navigator.navigate_to_replication_groups()
        self._admin_console.refresh_page()

        if not self.replication_groups.has_group(group_name):
            raise CVTestStepFailure(f'Replication group [{group_name}] does not exist')
        group_row = self.replication_groups.get_replication_group_details_by_name(group_name)

        self.assert_comparison(group_row[self._labels["label.groupName"]][0], group_name)
        self.assert_comparison(group_row[self._labels["label.source"]][0], source_hypervisor)
        self.assert_comparison(group_row[self._labels["label.destination"]][0], target_name)
        self.assert_comparison(group_row[self._labels["header.type"]][0], self._labels[f"label.virtualMachine{site}AppType"])
        self.assert_includes(replication_type, group_row[self._labels["label.replicationType"]][0])
        self.assert_comparison(group_row[self._labels["header.state"]][0], group_state)

        self._log.info('Replication group [%s] exists and with correct information', group_name)

    def verify_frequency(self, group_name: str, frequency_duration : int = 4, frequency_unit : str = TimePeriod.HOURS.value, navigate : bool = True):
        """
        Verifies that the frequency of backup schedule is met with expected values
        group_name          (str): The replication group name
        frequency           (str): The frequency of backup schedule eg: '4 Hour(s)'
        """
        self._navigate_and_access_group(group_name=group_name) if navigate else None

        rpo_details = self.group_details.overview.rpoOperations.get_rpo_details()
        expected_rpo_text = f"{self._labels['label.incrementalFrequencyText']} {frequency_duration} {frequency_unit.lower()}"
        self.assert_comparison(rpo_details['Replication frequency'], expected_rpo_text)

        self._log.info("Replication group [%s]'s frequency matches the expected value", group_name)

    def verify_storage(self, group_name: str, storage_list: list, navigate: bool = True):
        """
        Verifies that the storage are met with expected values
        group_name          (str): The replication group name
        storage_list        (list): The list of all associated storages
        """
        self._navigate_and_access_group(group_name=group_name) if navigate else None

        # Storage Name checks
        storage_details = set(self.group_details.overview.storageOperations.get_storage_names())
        storage_missing = list(set(storage_list) - storage_details)
        if storage_missing:
            raise CVTestStepFailure(
                f'Expected storage list is missing the values [{",".join(storage_missing)}]')

        self._log.info(
            "Replication group [%s]'s storages match the expected values", group_name)

    def verify_vm_group_exists(self, group_name: str, vendor_name: str, source_hypervisor: str, partial_match: bool = False):
        """
        Verifies the VM groups page to see if the VM group exists with the group name with
        the correct settings
        group_name          (str): The replication group name
        vendor_name         (str): The vendor name eg: 'VMware', 'Microsoft Azure',
                                   'Microsoft Hyper-V', 'Amazon'
        source_hypervisor   (str): The source hypervisor display name as shown in command center
        partial_match       (bool): If set to True, the VM group name is partially matched
        """
        self._navigator.navigate_to_vm_groups()
        self._admin_console.refresh_page()

        # INFO : Handling the case for VM Group Name -> {group_name}_{user_name}
        group_details = self.vm_groups.search_vmgroup(group_name)
        if len(group_details['Name']) > 1:
            raise CVTestStepFailure('The get details returned multiple rows. '
                                    'This is most likely due to search failure.')

        self.assert_comparison(group_details['Name'][0], group_name) if not partial_match else self.assert_includes(group_name, group_details['Name'][0])
        self.assert_comparison(group_details['Vendor'][0], vendor_name)
        self.assert_comparison(group_details['Hypervisor'][0], source_hypervisor)
        self.assert_comparison(group_details['Plan'][0], f'{group_name}_ReplicationPlan')

        self._log.info('Verified the VM group associated with replication group [%s]', group_name)

    def verify_replication_monitor(self, group_name: str, source_vms: list,
                                   frequency_duration: int = 4, frequency_unit : str = TimePeriod.HOURS.name,
                                   sla_status: str = 'Met', status: str = 'In sync',
                                   replication_type: str = ReplicationType.Periodic.name):
        """
        Verifies that the replication monitor table contains the replication group
        with the correct details
        group_name          (str):  The replication group name
        source_vm           (list): The list of source VM names that are to be deleted
        frequency           (str):  The frequency of backup schedule eg: '4 hours' or '4 Hour(s)'
        sla_status          (str):  The SLA status of the replication group
                                    eg: 'Met', 'Not Met', 'Not applicable'
        status              (str):  The sync status of the replication group eg: 'In Sync',
                                    'Sync Pending', 'Sync Disabled'
        """
        self._navigator.navigate_to_replication_monitor()
        for source_vm in source_vms:
            table_content = self.replication_monitor.get_replication_group_details(source_vm, group_name)
            self.assert_comparison(table_content[self._labels['label.selectSource']][0], source_vm)
            self.assert_comparison(table_content[self._labels["label.slaStatus"]][0], sla_status)
            self.assert_comparison(table_content[self._labels['label.replicationGroup']][0], group_name)
            self.assert_comparison(table_content[self._labels['header.syncStatus']][0], status)

            match replication_type:
                case ReplicationType.Periodic.name:
                    self.assert_comparison(table_content[self._labels["header.frequency"]][0].lower(), f"{frequency_duration} {frequency_unit}".lower())
                case ReplicationType.Orchestrated.name:
                    _observed_frequency = table_content[self._labels["header.frequency"]][0].lower()
                    self.assert_comparison(frequency_duration, self._frequency_in_minutes())

    def verify_group_deletion(self, group_name: str, replication_type: str=ReplicationType.Periodic.name):
        """
        Verifies that the VM group and schedule associated with the replication group
        are deleted if replication group is deleted
        group_name          (str): The replication group name
        """
        self._navigator.navigate_to_vm_groups()
        self._admin_console.refresh_page()

        if replication_type != ReplicationType.Orchestrated.name:
            vm_group_details = self.vm_groups.search_vmgroup(group_name)
            if len(vm_group_details['Name']) > 0:
                raise CVTestStepFailure(
                    f'VM group with the name [{group_name}]'
                    f' still exists after replication group deletion')

        self.commcell.schedules.refresh()
        if self.commcell.schedules.has_schedule(self.get_schedule_name(group_name)):
            raise CVTestStepFailure(
                f'Schedule with the name [{self.get_schedule_name(group_name)}]'
                f' still exists after replication group deletion')

        self._log.info('Verified that the schedule and vm group associated with replication group is deleted')


    def validate_details(self, vendor, observed_values:dict, expected_values:dict):
        """
        Validates the details of a vendor's observed values against expected values.

        Args:
            vendor (str): The name of the vendor.
            observed_values (dict): A dictionary containing the observed values.
            expected_values (dict): A dictionary containing the expected values.
        """

        match vendor:
            case Vendors_Complete.AWS.value:
                assert_comparison_keys = {"drvm_name", "availability_zone", "encryption_key", "iam_role", "network", "security_group", "instance_type"}
                assert_includes_keys = {"volume_type"}
            case Vendors_Complete.AZURE.value:
                assert_comparison_keys = {"drvm_name", "resource_group",  "region", "storage_account", "availability_zone",
                                           "virtual_network"}
                assert_includes_keys = {"vm_size", "security_group"}
            case Vendors_Complete.HYPERV.value:
                assert_comparison_keys = {"drvm_name", "network"}
                assert_includes_keys = set()
            case Vendors_Complete.VMWARE.value:
                assert_comparison_keys = {"drvm_name", "vm_storage_policy", "datastore", "resource_pool"}
                assert_includes_keys = {"destination_host"}
            case default:
                assert_comparison_keys = set()
                assert_includes_keys = set()
        for key in assert_comparison_keys:
            self.assert_comparison(observed_values.get(key), expected_values.get(key))
        for key in assert_includes_keys:
            self.assert_includes(observed_values.get(key), expected_values.get(key))

    def update_access_node(self, group_name: str, access_node: str):
        """
        Updates the access node (Orchestrated replication)

        Args:
            group_name (str): The name of the replication group.
            access_node (str): The access node to be set.
        """
        self._navigate_and_access_group(group_name=group_name)
        self.group_details.overview.summaryOperations.update_access_node(access_node)      


class DRHelper:
    """This class is a wrapper around the VSA backend entities to help automation Zeal automation
    Examples:
        1. When replication group doesn't exist and you need the source hypervisor object
            dr_helper = DRHelper(self.commcell, self.csdb, self.client)
            hypervisor_object = dr_helper.source_auto_instance.hvobj
        2. When the replication group exists and you need to access the destination hypervisor
            object
            dr_helper = DRHelper(self.commcell, self.csdb, self.client)
            dr_helper.source_subclient = 'Group_name'
            // Works only if the replication job has passed atleast once
            hypervisor_object = dr_helper.destination_auto_instance.hvobj
            // Only those VMs which are synced atleast once
            destination_vm_names = dr_helper.destination_vms
        3. When the replication group exists and you need to access the backup job and replication
            jobs
            dr_helper = DRHelper(self.commcell, self.csdb, self.client)
            dr_helper.source_subclient = 'Group_name'
            backup_job_obj = dr_helper.get_latest_backup_job()
            replication_job_obj = dr_helper.get_latest_replication_job()
    """
    AGENT_NAME = 'virtual server'
    INSTANCE_NAMES = [
        'vmware',
        'azure resource manager',
        'hyper-v',
        'amazon web services'
    ]
    BACKUPSET_NAME = 'defaultbackupset'

    def __init__(self,
                 commcell_object: Commcell,
                 csdb: CommServDatabase,
                 source_client: Client = None,
                 **kwargs):
        """Initialise the class"""
        self.commcell = commcell_object
        self.csdb = csdb
        self.log = get_log()

        self._source_client = None
        self.source_agent = None
        self.source_instance = None
        self.source_backupset = None
        self._source_subclient = None

        self._auto_commcell = None
        self._auto_client = None
        self._auto_instance = None
        self._auto_backupset = None
        self._auto_subclient = None
        self._live_sync_utils = None
        self._source_vms = None
        self._destination_vms = None
        self._replication_group_name = None
        self.__subclient_row = None
        self._schedule = None
        self._backup_job_id = None
        self.source_client = source_client
        self.kwargs = kwargs

    @property
    def source_client(self):
        """Returns the client object"""
        return self._source_client

    @source_client.setter
    def source_client(self, client: Client):
        """Sets the client object from the client name"""
        self._source_client = client
        self.source_agent = self.source_client.agents.get(self.AGENT_NAME)
        for instance_name in self.INSTANCE_NAMES:
            if self.source_agent.instances.has_instance(instance_name):
                self.source_instance = self.source_agent.instances.get(instance_name)
                break
        else:
            raise CVTestStepFailure("No instance of supported hypervisors found")
        self.source_backupset = self.source_instance.backupsets.get(self.BACKUPSET_NAME)

    @property
    def source_subclient(self):
        """returns the subclient object"""
        return self._source_subclient

    @property
    def replication_group_name(self):
        """returns the replication group name"""
        if not self._replication_group_name:
            self._replication_group_name = self.source_subclient.name
        return self._replication_group_name

    @replication_group_name.setter
    def replication_group_name(self, replication_group_name: str):
        """Sets replication group name """
        self._replication_group_name = replication_group_name

    @source_subclient.setter
    def source_subclient(self, group_name: str):
        """Sets the subclient of the replication group"""
        self.source_backupset.subclients.refresh()
        self._source_subclient = self.source_backupset.subclients.get(group_name)

    @property
    def schedule(self):
        """Returns the schedule object for the replication group"""
        schedule_names = [self.replication_group_name, self.source_subclient.name,
                          ReplicationHelper.get_schedule_name(self.source_subclient.name)]
        self.commcell.schedules.refresh()
        if not self._schedule:
            for schedule_name in schedule_names:
                if self.commcell.schedules.has_schedule(schedule_name):
                    self._schedule = self.commcell.schedules.get(schedule_name)
        return self._schedule

    @schedule.setter
    def schedule(self, schedule_name: str):
        """Sets the schedule object in cases where the replication schedule need not be for Zeal
        Note: needs to be set before calling the live_sync_utils object of this class
        """
        self._schedule = self.commcell.schedules.get(schedule_name)

    @property
    def source_auto_instance(self):
        """Returns the Auto VSA instance for the replication group"""
        if not self._auto_instance:
            region = self.kwargs.get('region', None)
            if not region:
                region = (self.source_client.properties['clientProps']['clientRegionInfo']
                          .get('region', {})
                          .get('regionName', None))

            self._auto_commcell = VirtualServerHelper.AutoVSACommcell(
                self.commcell, self.csdb)
            self._auto_client = VirtualServerHelper.AutoVSAVSClient(self._auto_commcell,
                                                                    self.source_client)
            self._auto_instance = VirtualServerHelper.AutoVSAVSInstance(self._auto_client,
                                                                        self.source_agent,
                                                                        self.source_instance)
        return self._auto_instance

    @property
    def source_auto_subclient(self):
        """Returns the Auto VSA instance for the replication group"""
        if not self._auto_subclient:
            auto_instance = self.source_auto_instance
            self._auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance,
                                                                        self.source_backupset)
            self._auto_subclient = VirtualServerHelper.AutoVSASubclient(self._auto_backupset,
                                                                        self.source_subclient)
        return self._auto_subclient

    @property
    def source_vm_names(self):
        """Returns the source VM names which are synced by live sync
        Note: this list differs from the replication group list, as it contains only synced VMs
        """
        return self.live_sync_utils.source_vms

    @property
    def source_vms(self):
        """Returns the source VM helper objects"""
        return self.live_sync_utils.source_vm_objects

    @property
    def live_sync_utils(self):
        """Returns the live sync utils object"""
        if not self._live_sync_utils:
            if not self.replication_group_name:
                self._live_sync_utils = LiveSyncUtils(self.source_auto_subclient,
                                                      self.schedule.schedule_name)
            else:
                self._live_sync_utils = LiveSyncUtils(self.source_auto_subclient,
                                                      self.replication_group_name)

        return self._live_sync_utils

    @property
    def destination_auto_instance(self):
        """Returns the destination AutoVSA Instance object"""
        return self.live_sync_utils.dest_auto_vsa_instance

    @property
    def destination_vm_names(self):
        """Returns the destination VM names as a list"""
        return self.live_sync_utils.destination_vms

    @property
    def destination_vms(self):
        """Returns the destination VM helper objects"""
        return self.live_sync_utils.destination_vm_objects

    @property
    def source_proxies(self):
        """
        Returns a list of the all source proxy names
        Note: only 1 proxy if group has proxy set,
              first proxy as coordinator proxy followed by list of instance proxies
        """
        proxies = self.source_auto_instance.proxy_list
        if self.source_auto_instance.vsa_co_ordinator:
            proxies = ([self.source_auto_instance.vsa_co_ordinator] +
                       [proxy for proxy in proxies if proxy != self.source_auto_instance.vsa_co_ordinator])
        if self._source_subclient and self._source_subclient.subclient_proxy:
            return self._source_subclient.subclient_proxy
        return proxies

    @property
    def destination_proxies(self):
        """
        Returns a list of the all destination proxy names
        Note: only recovery target proxy if defined,
              else returns a list of destination proxies
        """
        if not self._source_subclient:
            raise CVTestStepFailure("Replication group name is not set in DRHelper")
        if self.live_sync_utils.vm_pair.destination_proxy:
            return [self.live_sync_utils.vm_pair.destination_proxy]
        else:
            return self.destination_auto_instance.proxy_list

    def get_latest_backup_job(self, wait_for_completion: bool = False):
        """
        Gets the latest backup job ID and returns the job object
        wait_for_completion (bool): Specify whether the thread should wait for job to complete
                                    before returning the job object
        Returns:    latest backup job's job object if it exists,
                    raises exception otherwise
        """
        for _ in range(15):
            try:
                job = self.source_subclient.find_latest_job(lookup_time=4)
                self._backup_job_id = job.job_id
                self.log.info(f'Found backup job with ID {job.job_id}')
                if wait_for_completion:
                    self.log.info('Waiting for backup job to complete')
                    job.wait_for_completion()
                    ReplicationHelper.assert_comparison(job.status, 'Completed')
                return job
            except SDKException:
                self.log.info(f'Waiting for 60 seconds to let backup job '
                              f'trigger for group {self.source_subclient.name}')
                sleep(60)
        raise CVTestStepFailure(f"No backup job triggered for replication "
                                f"group {self.source_subclient.name}")

    def get_latest_replication_job(self, wait_for_completion: bool = True):
        """
        Gets the latest replication job running for the replication group
        wait_for_completion (bool): Specify whether the thread should wait for job to complete
                                    before returning the job object
        Returns:    latest replication job's job object if it exists or a list of job objects,
                    raises exception otherwise
        """
        source_vms = set(self.live_sync_utils.source_vm_content)
        for _ in range(15):
            job = self.live_sync_utils.get_recent_replication_job(self._backup_job_id,
                                                                  monitor_job=wait_for_completion)
            job_vms = set([vm.get('vmName') for vm in job.get_vm_list()])
            # If all VMs are backed up, return the job object
            source_vms = source_vms - job_vms
            if not source_vms:
                self.log.info('All VMs are synced')
                return job
            self.log.info(f'VMs {source_vms} to be synced.'
                          f'Waiting 1 minute for a new replication job')
            sleep(60)
        else:
            raise CVTestStepFailure('Not all VMs backed up even after 15 replication job waits')

    def verify_replication_job_copy(self, replication_job_id: str, expected_copy_precedence: int):
        """
        Verify that the replication job uses the correct backup job copy
        replication_job_id      (str): Replication job ID
        expected_copy_precedence     (int):  Specify which backup copy is taken for replication job
                                    (1 for primary and 2 for secondary)
        """
        # Check the sub task XML options to see which copy is to be used for replication
        self.schedule.refresh()
        copy_precedence = (self.schedule._task_options['restoreOptions']['browseOption']
        ['mediaOption']['copyPrecedence']['copyPrecedence'])
        ReplicationHelper.assert_comparison(copy_precedence, expected_copy_precedence)
        copy_name = self.schedule._task_options['restoreOptions']['storagePolicy']['copyName']

        # Check the replication job info to see which copy is used
        job = self.commcell.job_controller.get(replication_job_id)
        # job._details['jobDetail']['clientStatusInfo']['vmStatus'][0]['lastSyncedBkpJob'] contains
        # the child job ID
        copy_info_event = [event for event in job.get_events()
                           if event['eventCodeString'] == '13:216']
        if not copy_info_event:
            raise CVTestStepFailure(f'Cannot find which copy is used '
                                    f'for the replication job [{replication_job_id}]')
        ReplicationHelper.assert_includes(copy_name, copy_info_event[0]['description'])

    def get_recovery_target_name_from_db(self, instance_id: str):
        """Returns the recovery target name associated with the VM"""

        query = (f"select name from App_VmAllocationPolicy "
                 f"where id in (select vmAllocationPolicyId "
                 f"from App_VM where GUID='{instance_id}')")

        self.csdb.execute(query)
        return self.csdb.fetch_all_rows()[0][0]

    def get_expiration_time_from_db(self, instance_id: str):
        """Returns the recovery target name associated with the VM"""

        query = (f"select attrVal from App_ClientProp "
                 f"where componentNameId in (select clientId "
                 f"from App_VM where GUID='{instance_id}') "
                 f"and attrName like '%Virtual Machine Reserved Until%'")

        self.csdb.execute(query)
        return self.csdb.fetch_all_rows()[0][0]

    def get_cloned_vm_db_entries(self, instance_ids: list):
        """Returns the recovery target name associated with the VM"""

        instance_ids_str = "'{}'".format("', '".join(map(str, instance_ids)))
        query = (f"select id from App_VM where name in ( {instance_ids_str} )")

        self.csdb.execute(query)
        return self.csdb.fetch_all_rows()

    def get_rpo_from_usercreated_plan(self):
        """Returns the RPO and time period from the plan"""
        _plan = Plan(self.commcell, plan_name='', plan_id=self.source_subclient._planEntity.get('planId'))
        _schedules = _plan._v4_plan_properties.get('rpo', {}).get('backupFrequency', {}).get('schedules')
        _backup_schedule = next((schedule.get('schedulePattern') for schedule in _schedules if schedule.get('backupType') == 'INCREMENTAL'), None)

        _frequency_value = _backup_schedule.get('frequency')
        _frequency_unit = TimePeriod.HOURS
        
        match _backup_schedule.get('scheduleFrequencyType'):
            case 'MINUTES':
                # NOTE : Frequency type is set to MINUTES for Minutes and Hours
                # Current case - for Hours
                _frequency_value = _frequency_value//60
                _frequency_unit = TimePeriod.HOURS
            case 'DAILY':
                _frequency_unit = TimePeriod.DAYS
            case 'WEEKLY':
                _frequency_unit = TimePeriod.WEEKS
        
        return (_frequency_value, _frequency_unit)

    def verify_storage_policy(self, copy_dict: dict):
        """Verifies that the storage policy honouring the replication group settings
            Args:
                copy_dict (dict): A dictionary of <copy_name>:<copy_properties>
                eg:
                    {"primary": {
                        "retention": 14  # in days
                        "storage": "storage_name",
                        "isPrimary": True,
                    }}
        """
        storage_policy = self.commcell.storage_policies.get(self.source_subclient.storage_policy)
        # Verify all copies exist
        ReplicationHelper.assert_comparison(set(copy_dict.keys()), set(storage_policy.copies))

        for copy_name, copy_details in copy_dict.items():
            copy = storage_policy.copies[copy_name]
            ReplicationHelper.assert_comparison(copy.get('isDefault'), copy_details['isPrimary'])
            ReplicationHelper.assert_comparison(copy.get('libraryName', ''), copy_details['storage'].lower())

            copy_obj = storage_policy.get_copy(copy_name)
            ReplicationHelper.assert_comparison(copy_obj.copy_retention.get('days'),
                                                copy_details.get('retention', 14))

    def verify_replication_plan(self, incremental_freq: int, synthetic_full_days=30):
        """Verifies that the replication plan is honouring the replication group settings
            Args:
                incremental_freq (int): SLA in minutes
                synthetic_full_days(int) : Days for Synthetic full- By default - 30
        """
        plan = Plan(self.commcell, '', plan_id=self.source_subclient._planEntity.get('planId'))

        ReplicationHelper.assert_comparison(plan.storage_policy.name.lower(),
                                            self.source_subclient.storage_policy.lower())
        ReplicationHelper.assert_comparison(plan.sla_in_minutes, incremental_freq)
        expected_schedules = {'continuous incremental', 'synthetic fulls'}
        schedules = set([schedule.get('schedule_name', '').lower()
                         for schedule in plan.schedule_policies['data'].all_schedules])
        ReplicationHelper.assert_comparison(schedules, expected_schedules)
        for schedule_name in plan.schedule_policies['data'].all_schedules:
            schedule = plan.schedule_policies['data'].get_schedule(schedule_name=schedule_name['schedule_name'])
            if schedule_name['schedule_name'] == 'Continuous Incremental':
                ReplicationHelper.assert_comparison(schedule['pattern']['freq_interval'], incremental_freq)
            elif schedule_name['schedule_name'] == 'Synthetic Fulls':
                ReplicationHelper.assert_comparison(
                    schedule['options']['backupOpts']['dataOpt']['daysBetweenSyntheticBackup'], synthetic_full_days)

    def verify_schedules_states(self, schedule_list: list, disabled: bool = False):
        """Verifies that the schedules associated to the replication group are in the correct state
            Args:
                schedule_list:  List of schedule names for the replication group
                disabled:       Whether the schedules should be enabled or disabled
        """
        for schedule_name in schedule_list:
            schedule = self.source_subclient.schedules.get(schedule_name=schedule_name)
            ReplicationHelper.assert_comparison(schedule.is_disabled, disabled)

    def _frequency_in_minutes(self, frequency_duration: int, frequency_unit: str = TimePeriod.HOURS.value):
        """Converts the frequency to minutes"""
        match frequency_unit:
            case TimePeriod.MINUTES.value:
                return frequency_duration
            case TimePeriod.HOURS.value:
                return frequency_duration * 60
            case TimePeriod.DAYS.value:
                return frequency_duration * 60 * 24
            case TimePeriod.WEEKS.value:
                return frequency_duration * 60 * 24 * 7
            case TimePeriod.MONTHS.value:
                return frequency_duration * 60 * 24 * 30
            case TimePeriod.YEARS.value:
                return frequency_duration * 60 * 24 * 365
            case default:
                raise CVTestStepFailure(f"Invalid frequency unit {frequency_unit}")

    def verify_schedules(self, group_name: str, frequency_duration: int = 0, frequency_unit: str = TimePeriod.HOURS.value, 
                         vm_group: str = None, repliction_type: str = ReplicationType.Periodic.name):
        """
        Verify the Replication frequency with backup schedule
        group_name          (str): The replication group name
        frequency           (int): The frequency of backup schedule in minutes
        """
        _replication_group_name = group_name
        _schedule_name = ReplicationHelper.get_schedule_name(_replication_group_name, replication_type=repliction_type)

        match repliction_type:
            case ReplicationType.Periodic.name:
                self.source_subclient = group_name
                
                _replication_plan = ReplicationHelper.get_plan_name(_replication_group_name)
                _schedule_list = ['Continuous Incremental', 'synthetic fulls', _schedule_name]

                # Periodic Replication specific validation
                # Replication Plan Verification
                _frequency_in_minutes = self._frequency_in_minutes(frequency_duration, frequency_unit)
                self.verify_replication_plan(incremental_freq=_frequency_in_minutes)
                
                # DB Verification
                query = (f"SELECT attrVal FROM App_PlanProp "
                        f"WHERE componentNameId = (SELECT id FROM App_Plan WHERE name = "
                        f"'{_replication_plan}') AND attrName='RPO In Minutes'")
                self.csdb.execute(query)
                ReplicationHelper.assert_comparison(int(self.csdb.fetch_one_row()[0]), _frequency_in_minutes)
            
            case ReplicationType.Orchestrated.name:
                self.source_subclient = vm_group
                
                _replication_plan = self.source_subclient._planEntity.get('planName')
                # TODO : Null Schedule name requires additional changes on other modules
                _schedule_list = ['synthetic fulls', _schedule_name]
            
            case _:
                raise CVTestStepFailure("Invalid replication type provided")
        
        # Verify Schedule states
        self.verify_schedules_states(schedule_list=_schedule_list, disabled=False)
        self.log.info("Verified the schedules for replication group [%s]", group_name)

        
