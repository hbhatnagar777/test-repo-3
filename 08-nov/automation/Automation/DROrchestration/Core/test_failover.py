# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for helping testcases validate DR functionalities for replication
TestFailover
    Methods:
        validate_hardware():        Validates the hardware status of the test failover VM
"""
from DROrchestration.Core.VMOptions import AzureVM as AzureVMOptions
from DROrchestration.Core.VMOptions import AWSVM as AWSVMOptions
from DROrchestration.Core._dr_validation import _DROrchestrationValidation
from datetime import datetime

cloned_vm_options = {
    "VmwareVM": lambda source_vm, drvm_options, recovery_target: {
        "cpuCount": source_vm.no_of_cpu,
        "memory": source_vm.memory,
        "diskCount": source_vm.disk_count,
        "nicCount": source_vm.nic_count,
        "esxHost": recovery_target.destination_host,
        "datastore": recovery_target.datastore
    },
    "AzureVM": AzureVMOptions.test_failover_vm_options,
    "HyperVVM": lambda source_vm, drvm_options, recovery_target: {
        "cpuCount": source_vm.no_of_cpu,
        "memory": source_vm.memory,
        "diskCount": source_vm.disk_count,
        "nicName": drvm_options.get('advancedRestoreOptions').get('nics')[0].get('networkName', {}),
        "diskPath": [recovery_target.vm_folder],
        "configVersion": source_vm.config_version if hasattr(source_vm, 'config_version') else None
    },
    "AmazonVM": AWSVMOptions.test_failover_vm_options
}


class TestFailoverDBHelper():
    def __init__(self, csdb):
        self._csdb = csdb

    @property
    def csdb(self):
        return self._csdb

    def get_recovery_target_name(self, cloned_vm_name):
        """Returns the recovery target name associated with the VM"""

        query = (f"select name from App_VmAllocationPolicy "
                 f"where id in (select vmAllocationPolicyId "
                 f"from App_VM where name='{cloned_vm_name}')")

        self.csdb.execute(query)
        return self.csdb.fetch_all_rows()[0][0]

    def get_expiration_time(self, cloned_vm_name):
        """Returns the expiration time set for the VM"""

        query = (f"select attrVal from App_ClientProp "
                 f"where componentNameId in (select clientId "
                 f"from App_VM where name='{cloned_vm_name}') "
                 f"and attrName like '%Virtual Machine Reserved Until%'")

        self.csdb.execute(query)

        formatted_expiration_time = datetime.fromtimestamp(
            int(self.csdb.fetch_all_rows()[0][0])).strftime(
            '%d-%b-%y %H:%M')

        return formatted_expiration_time

    def get_cloned_vm_entries(self, cloned_vm_names: list):
        """Returns the entries associated with the VMs"""

        cloned_vm_names_str = "'{}'".format(
            "', '".join(map(str, cloned_vm_names)))

        query = (f"select id from App_VM "
                 f"where name in ( {cloned_vm_names_str} )")

        self.csdb.execute(query)
        return self.csdb.fetch_all_rows()


class TestFailoverPeriodic(_DROrchestrationValidation):
    """ This class is used to provide utility functions for validating Test Failover"""

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._cloned_vms = dict()
        self._cloned_vms_metadata = dict()
        self._helper = None

    @property
    def cloned_vms(self):
        """Returns the list of VMs that are going to be used in this operation"""
        return self._cloned_vms

    @cloned_vms.setter
    def cloned_vms(self, vm_list: list):
        """Populates the cloned VM details"""
        for vm in vm_list:
            vm_options = (cloned_vm_options[self._source_vm.
                          __class__.__name__](self._source_vm, self._vm_options, self.recovery_target))
            self._cloned_vms[vm.vm_name] = vm.DrValidation(
                vm, vm_options, clone_metadata=self.cloned_vms_metadata.get(vm.vm_name, {}))

    @property
    def cloned_vms_metadata(self):
        """Returns the list of VMs that are going to be used in this operation"""
        return self._cloned_vms_metadata

    @cloned_vms_metadata.setter
    def cloned_vms_metadata(self, vm_list: list):
        """Populates the metadata of the Cloned VMs"""
        for vm in vm_list:
            self._cloned_vms_metadata[vm.get('Name')] = vm

    @property
    def helper(self):
        """Returns the helper object"""
        if not self._helper:
            self._helper = TestFailoverDBHelper(self.csdb)
        return self._helper

    def pre_validate_sync_status(self):
        """ Validates the sync status of the live sync pair before Test Failover operation """
        self.refresh()
        if self._live_sync_pair.status not in ['IN_SYNC']:
            raise Exception(
                f"{self._live_sync_pair} is not in 'In sync' status")
        self.log.info('Sync status for VM pair %s verified before Test Failover', str(
            self._live_sync_pair))

    def validate_sync_status(self):
        """ Validates the sync status of the live sync pair """
        self.refresh()
        # Sync Status -> any value except SYNC_DISABLED
        if self._live_sync_pair.status in ['SYNC_DISABLED']:
            raise Exception(
                f"{self._live_sync_pair} is in 'Sync disabled' status")
        self.log.info('Sync status for VM pair %s verified after Test Failover', str(
            self._live_sync_pair))

    def validate_power_state(self):
        """ Validates the power state of the cloned VMs """
        power_status = [cloned_vm.vm.is_powered_on()
                        for name, cloned_vm in self.cloned_vms.items()]
        if not all(power_status):
            raise Exception(
                f"Cloned VM(s) is/are NOT powered ON after Test Failover operation")
        self.log.info('Power states for VM pair %s verified after Test Failover', str(
            self._live_sync_pair))

    def validate_failover_status(self):
        """ Validates the failover status of the live sync pair post Test Failover """
        self.refresh()
        # Failover status does not change post Test Failover
        if self._live_sync_pair.failover_status == 'FAILOVER_COMPLETE':
            raise Exception(
                f"{self._live_sync_pair} - Failover status changed post Test Failover Job")
        self.log.info('Failover status for VM pair %s verified after Test Failover', str(
            self._live_sync_pair))

    def validate_hardware(self, source=False):
        """ Validate the hardware by comparison of source and destination VM configuration """
        for name, vm in self.cloned_vms.items():
            vm.validate_cpu_count()
            vm.validate_memory()
            vm.validate_disk_count()
            vm.validate_network_adapter()
        self.log.info('Verified hardware configuration of %s', vm.vm.vm_name)

    def validate_advanced(self, source=False, **kwargs):
        """ Validate the advanced validations for specific hypervisor """
        for name, vm in self.cloned_vms.items():
            vm.advanced_validation(other=None, **kwargs)
        self.log.info('Verified advanced validations of %s',
                      str(self._live_sync_pair))

    def validate_snapshot(self):
        """ Validates that the snapshot generated by Test Failover is removed """
        pass

    def validate_expiration(self, post_expiration=False):
        entries = self.helper.get_cloned_vm_entries(self.cloned_vms.keys())
        cloned_vm_status = [cloned_vm.vm.hvobj.check_vms_exist(
            [cloned_vm.vm.vm_name]) for cloned_vm in self.cloned_vms.values()]

        if post_expiration:
            # DB Entry Check
            if not (len(entries) == 1 and entries[0][0] == ''):
                raise Exception(
                    f"Cloned VM DB Entries for VM pair {self._live_sync_pair} have NOT been cleaned up")

            # Cloned VM Check
            if any(cloned_vm_status):
                raise Exception(
                    f"Cloned VMs associated with VM pair {self._live_sync_pair} have NOT been cleaned up")

            self.log.info(f"Cloned VMs associated with VM pair {self._live_sync_pair} have been cleaned up from the DB and hypervisor")

        else:
            # DB Entry check
            if not (len(entries) >= 1 and entries[0][0] != ''):
                raise Exception(
                    f"DB Entries for VM pair {self._live_sync_pair} are NOT created")

            # Expiration Time check
            expiration_times = [self.helper.get_expiration_time(cloned_vm) == self.cloned_vms_metadata.get(
                cloned_vm, {}).get('Expiration date') for cloned_vm in self.cloned_vms.keys()]

            if not all(expiration_times):
                raise Exception(
                    f"Expiration time mismatch observed on Cloned VM(s) associated with {self._live_sync_pair}")

            # Cloned VM Check
            if not all(cloned_vm_status):
                raise Exception(
                    f"Cloned VMs associated with VM pair {self._live_sync_pair} have NOT been created")

            self.log.info(f"Expiration time of cloned VMs associated with VM pair {self._live_sync_pair} verified")


class TestFailoverContinuous(_DROrchestrationValidation):

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self._destination_vm = None
        self.set_testfailovervm = None

    @property
    def set_testfailovervm(self):
        """Returns the list of VMs that are going to be used in this operation"""
        return self.testfailovervm_name

    @set_testfailovervm.setter
    def set_testfailovervm(self, testfailovervm_name):
        """Sets the VM list in the replication group"""
        self._destination_vm = testfailovervm_name

    def validate_snapshot(self):
        """ Validates that the snapshot generated by failover is removed """
        self.refresh()
        if self.destination_vm.vm.VMSnapshot != 'CV TEST FAILOVER Snapshot-0':
            raise Exception(f"{self._live_sync_pair} is not having BlrTestFailoverSnap on DR VM after failover")
        else:
            self.log.info('Sucessfully validated BlrFailoverSnap is present on DR VM for pair %s after test failover',
                          str(self._live_sync_pair))

    def pre_validate_sync_status(self):
        """ Validates the sync status of the live sync pair before the test_failover operation """
        self.refresh()
        if self._live_sync_pair.pair_status.name == 'REPLICATING':
            self.log.info(f"Verified replication pair {self._live_sync_pair} is Replicating")
        else:
            raise Exception(f"Failed to proceed with test failover replication pair {self._live_sync_pair} "
                            f"is not Replicating")

    def validate_sync_status(self):
        """ Validates the sync status of the live sync pair """
        self.refresh()
        if self._live_sync_pair.pair_status.name == 'REPLICATING':
            self.log.info(f"Verified replication pair {self._live_sync_pair} is Replicating")
        else:
            raise Exception(f"Failed to validate replication pair {self._live_sync_pair} is not Replicating")

    def validate_failover_status(self):
        """ Validates the failover status of the live sync pair is Failback complete """
        pass

    def validate_power_state(self):
        """ Validates the power state of the source and destination VM """
        self.refresh()
        if self._source_vm.is_powered_on():
            self.log.info(f"Sucessfully verified source VM [{self._source_vm.vm_name}] is in powered on "
                          f"state after test failover")
        else:
            raise Exception(f"Destination VM [{self._source.vm_name}] is powered off after test failover")

        if self._destination_vm.is_powered_on():
            self.log.info(f"Sucessfully validated power on state of the test failover VM "
                          f"[{self._destination_vm.vm_name}]")
        else:
            raise Exception(f"Destination VM [{self._destination_vm.vm_name}] is powered off even after failover")

    def validate_expiration(self, post_expiration=False):
        """ Validates the expiration of test failover VM """
        pass
