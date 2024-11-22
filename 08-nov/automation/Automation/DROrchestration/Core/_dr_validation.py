# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Abstraction file for helping testcases validate DR functionalities for all DR operations
_DROrchestrationValidation(abstract):
    Methods:
        __auto_instance_factory(
            client, agent, instance,
            tcinputs, kwargs):          Creates AutoVSAVSInstance on the basis of inputs and kwargs
        Refer: (VirtualServer.VSAUtils.VirtualServerHelper.AutoVSAVSInstance for tcinputs and kwargs)

"""
import time
from abc import ABCMeta, abstractmethod

from cvpysdk.subclients.virtualserver.livesync.vsa_live_sync import LiveSyncVMPair
from cvpysdk.drorchestration.blr_pairs import BLRPair
from cvpysdk.recovery_targets import RecoveryTarget

from AutomationUtils.logger import get_log
from AutomationUtils.database_helper import CommServDatabase
from DROrchestration.Core.VMOptions import AzureVM as AzureVMOptions
from DROrchestration.Core.VMOptions import AWSVM as AWSVMOptions
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils import VirtualServerUtils, VirtualServerHelper
from VirtualServer.VSAUtils.VMHelper import HypervisorVM


source_vm_options = {
    "VmwareVM": lambda source_vm, drvm_options: {
        "cpuCount": source_vm.no_of_cpu,
        "memory": source_vm.memory,
        "diskCount": source_vm.disk_count,
        "nicCount": source_vm.nic_count,
        "esxHost": source_vm.esx_host,
        "datastore": source_vm.datastore,
        "vmIPAddressOptions": ([{
                                    "ipAddress": ip_address.get("ipAddress", ""),
                                    "subnetMask": ip_address.get("subnetMask", ""),
                                    "defaultGateway": source_vm.guest_default_gateways,
                                    "dnsServers": source_vm.guest_dns,
                                    "dhcpEnabled": ip_address.get("dhcpEnabled", False)
                                } for ip_address in source_vm.guest_ip_rules]
                               if drvm_options.get('advancedRestoreOptions', {}).get('vmIPAddressOptions') else []),
        "computerName": (source_vm.guest_hostname if drvm_options.get('advancedRestoreOptions', {})
                         .get('vmIPAddressOptions') else "")
    },
    "AzureVM": AzureVMOptions.source_vm_options,
    "HyperVVM": lambda source_vm, drvm_options: {
        "cpuCount": source_vm.no_of_cpu,
        "memory": source_vm.memory,
        "diskCount": source_vm.disk_count,
        "nicName": source_vm.NicName,
        "diskPath": source_vm.disk_list,
        "configVersion": source_vm.config_version
    },
    "AmazonVM": AWSVMOptions.source_vm_options
}

destination_vm_options = {
    "VmwareVM": lambda source_vm, vm_options, recovery_target: {
        "cpuCount": source_vm.no_of_cpu,
        "memory": source_vm.memory,
        "diskCount": source_vm.disk_count,
        "nicCount": source_vm.nic_count,
        "esxHost": vm_options.get('esxHost'),
        "datastore": vm_options.get('datastore'),
        "vmIPAddressOptions": ([{
                                    "ipAddress": ip_rule.get("destinationIP", ""),
                                    "subnetMask": ip_rule.get("destinationSubnet", ""),
                                    "defaultGateway": [ip_rule.get("destinationGateway", "")],
                                    "dnsServers": [
                                        ip_rule.get("primaryDNS", ""),
                                        ip_rule.get("alternateDNS", ""),
                                    ],
                                    "dhcpEnabled": ip_rule.get("useDhcp", False)
                                } for ip_rule in vm_options.get('advancedRestoreOptions', {})
                               .get('vmIPAddressOptions', [])] if vm_options.get('advancedRestoreOptions', {})
                               .get('vmIPAddressOptions', []) else []),
        "computerName": vm_options.get('advancedRestoreOptions', {}).get("destComputerName", "")
    },
    "AzureVM": AzureVMOptions.destination_vm_options,
    "HyperVVM": lambda source_vm, vm_options, recovery_target: {
        "cpuCount": source_vm.no_of_cpu,
        "memory": source_vm.memory,
        "diskCount": source_vm.disk_count,
        "nicName": vm_options.get('advancedRestoreOptions').get('nics')[0].get('networkName', {}),
        "diskPath": [recovery_target.vm_folder],
        "configVersion": source_vm.config_version if hasattr(source_vm, 'config_version') else None
    },
    "AmazonVM": AWSVMOptions.destination_vm_options
}


class _DROrchestrationValidation(metaclass=ABCMeta):
    """ Abstract class for DR validation for DR operations """

    def __init__(self, vm_pair_object: LiveSyncVMPair or BLRPair,
                 source_auto_instance: VirtualServerHelper.AutoVSAVSInstance,
                 destination_auto_instance: VirtualServerHelper.AutoVSAVSInstance,
                 vm_options: dict,
                 job_type: str = '',
                 recovery_target: RecoveryTarget = None,
                 csdb: CommServDatabase = None):
        """
        Initialises the class
            Args:
                vm_pair_object (LiveSyncVMPair or BLRPair)      : Pair object for periodic or continuous pair
                source_auto_instance (AutoVSAVSInstance)        : The source hypervisor object
                destination_auto_instance (AutoVSAVSInstance)   : The destination hypervisor object
                vm_options (dict)                               : A dictionary of vm_options
                job_type (str)                                  : The job type of the operation creating this
                recovery_target (RecoveryTarget)                : Recovery target object
                csdb (CommServDatabase)                         : The DB object of CS
        """
        self._live_sync_pair = vm_pair_object
        self._commcell_object = self._live_sync_pair._commcell_object

        self._source_auto_instance = source_auto_instance
        self._source_vm_validation = None
        self._destination_auto_instance = destination_auto_instance
        self._destination_vm_validation = None

        self._vm_options = vm_options
        self._job_type = job_type.lower()
        self._recovery_target = recovery_target
        self._csdb = csdb
        self.test_data_timestamp = None

        self.log = get_log()

        self._source_vm_options = None
        self._destination_vm_options = None

    @staticmethod
    def assert_comparison(value, expected):
        """ Performs a comparison of the value with the expected value """
        return TestCaseUtils.assert_comparison(value, expected)

    @staticmethod
    def assert_includes(value, expected):
        """ Performs an assertion for if the value exists in the expected value """
        return TestCaseUtils.assert_includes(value, expected)

    def refresh(self, hard_refresh=False):
        """Refresh the state of the current VM"""
        self._live_sync_pair.refresh()

        if hard_refresh:
            # Refresh VM options by repopulating source VM object
            # NOTE: Please use hard_refresh only when the source VM is
            # powered on to avoid unnecessary time delay
            del self.source_vm_options
            del self.destination_vm_options
        # Re-create the VM validation objects with VM options
        del self.source_vm
        del self.destination_vm
        self.source_vm
        self.destination_vm

    @property
    def is_dvdf_enabled(self):
        """ Returns: (bool) Whether deploy VM during failover is enabled or not """
        if self.is_warm_sync_enabled:
            return False
        return self._vm_options.get('deployVmWhenFailover', False)

    @property
    def is_warm_sync_enabled(self):
        """ Returns: (bool) Whether warm sync is enabled or not """
        if isinstance(self._live_sync_pair, BLRPair):
            return False
        return self._live_sync_pair.is_warm_sync_pair

    @property
    def vm_pair(self):
        """ Returns: The VM pair cvpysdk object for the VM"""
        return self._live_sync_pair

    @property
    def source_auto_instance(self):
        """ Returns: The auto instance object for source hypervisor """
        return self._source_auto_instance

    @property
    def _source_vm(self):
        """ Returns: The source VM object """
        if self.vm_pair.source_vm not in self.source_auto_instance.hvobj.VMs:
            source_vm_obj = HypervisorVM(self.source_auto_instance.hvobj, self.vm_pair.source_vm)
            self.source_auto_instance.hvobj._VMs[self.vm_pair.source_vm] = source_vm_obj
        return self.source_auto_instance.hvobj.VMs[self.vm_pair.source_vm]

    @property
    def _destination_vm(self):
        """ Returns: The source VM object """
        if self.vm_pair.destination_vm not in self.destination_auto_instance.hvobj.VMs:
            destination_vm_args = {
                "region": self._vm_options.get('advancedRestoreOptions', {}).get('datacenter'),
                "resource_group_name": self._vm_options.get('advancedRestoreOptions', {}).get('esxHost'),
                "storage_account_name": self._vm_options.get('advancedRestoreOptions', {}).get('Datastore'),
            }
            destination_vm_obj = HypervisorVM(self.destination_auto_instance.hvobj, self.vm_pair.destination_vm,
                                              **destination_vm_args)
            self.destination_auto_instance.hvobj._VMs[self.vm_pair.destination_vm] = destination_vm_obj
        return self.destination_auto_instance.hvobj.VMs[self.vm_pair.destination_vm]

    @property
    def source_vm_options(self):
        """
        Creates the source VM options dictionary if the VM is powered on.
        NOTE: This method will power on source VM(if powered off) and then return the VM to original power state,
              if the VM options are not set (refresh/new creation)
        """
        if not self._source_vm_options:
            # If VM is powered off, power on VM, populate source VM options
            is_powered_on = self._source_vm.is_powered_on()
            if not is_powered_on:
                self.log.info("Powering on VM to populate VM options")
                self._source_vm.power_on()
                self._source_vm.wait_for_vm_to_boot()
                self._source_vm.update_vm_info(prop='All', os_info=True, force_update=True)

            self._source_vm_options = (source_vm_options[self._source_vm.
                                       __class__.__name__](self._source_vm, self._vm_options))
        return self._source_vm_options

    @source_vm_options.deleter
    def source_vm_options(self):
        """ Deletes the source VM options (marking refresh) """
        self._source_vm_options = None

    @property
    def destination_vm_options(self):
        """
        Creates the DR VM options dictionary if the VM is powered on
        NOTE: This method will power on source VM(if powered off) and then return the VM to original power state,
              if the VM options are not set (refresh/new creation)
        """
        if not self._destination_vm_options:
            # If VM is powered off, power on VM, populate DR VM options
            is_powered_on = self._source_vm.is_powered_on()
            if not is_powered_on:
                self.log.info("Powering on VM to populate VM options")
                self._source_vm.power_on()
                self._source_vm.wait_for_vm_to_boot()
                self._source_vm.update_vm_info(prop='All', os_info=True, force_update=True)
            self._destination_vm_options = (destination_vm_options[self._destination_vm.
                                            __class__.__name__](self._source_vm, self._vm_options, self.recovery_target))
        return self._destination_vm_options

    @property
    def source_proxy_list(self):
        """ Returns source proxy list """
        return [proxies.lower() for proxies in self.source_auto_instance.proxy_list]

    @property
    def destination_proxy_list(self):
        """ Returns proxies set on destination """

        if self.recovery_target.access_node_client_group:
            # returns proxies list for client group selection at destination
            client_grp_object = self._commcell_object.client_groups.get(self.recovery_target.access_node_client_group)
            clients_object = self._commcell_object.clients
            client_grp_proxies_list = list(set(clients_object.virtualization_access_nodes)
                                           .intersection(set(clients.lower() for clients in client_grp_object.associated_clients)))
            return client_grp_proxies_list
        else:
            # returns proxies list for Automatic and access node selection at destination
            if self.recovery_target.access_node == '':
                return [proxies.lower() for proxies in self.destination_auto_instance.proxy_list]
            else:
                return [self.recovery_target.access_node.lower()]

    @destination_vm_options.deleter
    def destination_vm_options(self):
        """ Deletes the destination VM options (marking refresh) """
        self._destination_vm_options = None

    @property
    def source_vm(self):
        """ Returns: The source VM DR validation object """
        if not self._source_vm_validation:
            self._source_vm_validation = self._source_vm.DrValidation(
                self._source_vm,
                self.source_vm_options
            )
        return self._source_vm_validation

    @source_vm.deleter
    def source_vm(self):
        """ Deletes the source VM DR validation object"""
        self._source_vm_validation = None

    @property
    def destination_auto_instance(self):
        """ Returns: The auto instance object for destination hypervisor """
        return self._destination_auto_instance

    @property
    def destination_vm(self):
        """ Returns: The destination VM helper object"""
        if not self._destination_vm_validation:
            self._destination_vm_validation = self._destination_vm.DrValidation(
                self._destination_vm,
                self.destination_vm_options
            )
        return self._destination_vm_validation

    @destination_vm.deleter
    def destination_vm(self):
        """ Deletes the destination VM DR Validation object"""
        self._destination_vm_validation = None

    @property
    def recovery_target(self):
        """Returns recovery target object"""
        return self._recovery_target

    @property
    def csdb(self):
        """Returns CSDB object"""
        return self._csdb

    @abstractmethod
    def pre_validate_sync_status(self):
        """ Validates the sync status of the live sync pair before the operation """
        return

    @abstractmethod
    def validate_sync_status(self):
        """ Validates the sync status of the live sync pair """
        return

    @abstractmethod
    def validate_power_state(self):
        """ Validates the power state of the source and destination VM """
        return

    @abstractmethod
    def validate_snapshot(self):
        """ Validates the snapshot state of the source and destination VM """
        return

    def refresh_vm(self, source=True, basic_only=False):
        """ Refresh the properties of the VM"""
        vm = self.source_vm.vm if source else self.destination_vm.vm
        if basic_only:
            vm.update_vm_info(force_update=True)
        else:
            vm.update_vm_info(prop='All', os_info=True, force_update=True)
            vm.wait_for_vm_to_boot()

    def check_vm_exist(self, source=False):
        vm = self.source_vm if source else self.destination_vm
        vm.validate_vm_exists()

    def add_test_data(self, source=True):
        """ Adds the test data to the given VM """
        vm = self.source_vm.vm if source else self.destination_vm.vm
        self.refresh_vm(source=source)
        self.test_data_timestamp = str(int(time.time()))
        VirtualServerUtils.add_test_data(vm, folder_name="DRAutomation", timestamp=self.test_data_timestamp)
        self.log.info('Added testdata to %s', vm.vm_name)

    def validate_test_data(self, source=False):
        """ Validates that the test data is present on given VM """
        vm = self.source_vm.vm if source else self.destination_vm.vm
        self.refresh_vm(source=source)
        VirtualServerUtils.validate_test_data(vm, folder_name="DRAutomation", timestamp=self.test_data_timestamp)
        self.log.info('Verified testdata on %s', vm.vm_name)

    def validate_no_test_data(self, source=False):
        """ Validates that the test data doesn't exist on given VM """
        vm = self.source_vm.vm if source else self.destination_vm.vm
        self.refresh_vm(source=source)
        VirtualServerUtils.validate_no_test_data(vm, folder_name="DRAutomation", timestamp=self.test_data_timestamp)
        self.log.info('Verified testdata does not exist on %s', vm.vm_name)

    def cleanup_test_data(self, source=False):
        """ Clean up the test data that is generated on the VM """
        # This check is made to skip the vm validation if the object did not have added test data
        if not self.test_data_timestamp:
            return
        # main
        vm = self.source_vm.vm if source else self.destination_vm.vm
        self.refresh_vm(source=source)
        self.log.info("Cleaning up testdata on %s", vm.vm_name)
        VirtualServerUtils.cleanup_test_data(vm, folder_name="DRAutomation", timestamp=self.test_data_timestamp)
        self.log.info('Cleaned up testdata on %s', vm.vm_name)

    def validate_boot(self, source=False):
        """ Validates that the VM has booted by pinging its reported IP """
        vm = self.source_vm.vm if source else self.destination_vm.vm
        for _ in range(5):
            vm.update_vm_info(force_update=True)
            if VirtualServerUtils.validate_ipv4(vm.ip):
                break
            self.log.info('Waiting for 60 seconds for VM to get IP address')
            time.sleep(60)
        vm.wait_for_vm_to_boot()
        self.log.info('Verified OS boot up %s', vm.vm_name)

    def validate_hardware(self, source=False, **kwargs):
        """ Validate the hardware by comparison of source and destination VM configuration """
        vm = self.source_vm if source else self.destination_vm
        vm.validate_cpu_count()
        vm.validate_memory()
        vm.validate_disk_count(**kwargs)
        vm.validate_network_adapter()
        self.log.info('Verified hardware configuration of %s', vm.vm.vm_name)

    def validate_advanced(self, source=False, **kwargs):
        """ Validate the advanced validations for specific hypervisor """
        vm, other = (self.source_vm, self.destination_vm) if source else (self.destination_vm, self.source_vm)
        vm.advanced_validation(other, **kwargs)
        self.log.info('Verified advanced validations of %s', str(self._live_sync_pair))

    def validate_warm_sync(self, **kwargs):
        """ Validates that the warm sync settings are honoured on the hypervisor before failover/after failback """
        self.destination_vm.validate_warm_sync(**kwargs)
        self.log.info("Warm sync entities have not been created before failover/after failback: %s",
                      str(self._live_sync_pair))


