# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Abstraction file for helping testcases validate DR functionalities for test boot
TestBoot:
    Class Variables:
        SourcePhases
        DestinationPhases
    Methods:
        _set_vm_list(vm_list)
        pre_validation()
        post_validation()
    Properties:
        job_type
"""

from DROrchestration.Core import ReplicationPeriodic, ReplicationContinuous
from DROrchestration._dr_operation import DROperation


class TestBoot(DROperation):
    """This class is used to perform Test boot validations"""

    SourcePhases = {
        "vmware": {'DISABLE_SYNC'},
        "vmware_aux": {'DISABLE_SYNC'},
        "vmware_warmsync": set(),
        "vmware_aux_warmsync": set(),
        "vmware_continuous": set(),
        "hyper-v": {'DISABLE_SYNC'},
        "hyper-v_aux": {'DISABLE_SYNC'},
        "hyper-v_warmsync": set(),
        "hyper-v_aux_warmsync": set(),
    }

    DestinationPhases = {
        "vmware": {'DELETE_SNAPSHOT', 'REVERT_SNAPSHOT', 'SHUTDOWN',
                   'POWER_ON', 'DISABLE_NETWORK_ADAPTER', 'CREATE_SNAPSHOT'},
        "vmware_aux": {'DELETE_SNAPSHOT', 'REVERT_SNAPSHOT', 'SHUTDOWN',
                   'POWER_ON', 'DISABLE_NETWORK_ADAPTER', 'CREATE_SNAPSHOT'},
        "vmware_warmsync": set(),
        "vmware_aux_warmsync": set(),
        "vmware_continuous": set(),
        "hyper-v": {'DELETE_SNAPSHOT', 'REVERT_SNAPSHOT', 'SHUTDOWN',
                    'POWER_ON', 'DISABLE_NETWORK_ADAPTER', 'CREATE_SNAPSHOT'},
        "hyper-v_aux": {'DELETE_SNAPSHOT', 'REVERT_SNAPSHOT', 'SHUTDOWN',
                    'POWER_ON', 'DISABLE_NETWORK_ADAPTER', 'CREATE_SNAPSHOT'},
        "hyper-v_warmsync": set(),
        "hyper-v_aux_warmsync": set(),
    }

    def _set_vm_list(self, vm_list: list):
        super()._set_vm_list(vm_list)
        for source_vm, core_args in self._vm_pairs.items():
            if self.is_continuous:
                self._vm_pairs[source_vm] = {
                    'Replication': ReplicationContinuous(**core_args),
                }
            else:
                self._vm_pairs[source_vm] = {
                    'Replication': ReplicationPeriodic(**core_args),
                }

    @property
    def job_type(self):
        """Returns the expected job type"""
        return 'Test Boot'

    def pre_validation(self, **kwargs):
        """Validates the state before DR(Test boot) operation"""
        for source in self.vm_list:
            testboot = self._vm_pairs[source]['Replication']
            testboot.validate_sync_status()  # check sync status is 'in Sync'
            
            testboot.add_test_data(source=True)

    def post_validation(self, **kwargs):
        """Validates this DR operation"""
        self.refresh()
        for source in self.vm_list:
            testboot = self._vm_pairs[source]['Replication']
            testboot.validate_power_state()  # check destination vm is power off
            testboot.validate_sync_status()  # check sync status is not sync disabled
            testboot.validate_no_test_boot_snapshot()  # check test boot snapshot not present after operation
            testboot.validate_snapshot()  # check gx_backup should present in DR VM

            testboot.destination_vm.vm.power_on()
            testboot.validate_boot()
            testboot.validate_no_test_data(source=False)

            # todo - validate network connected
            # testboot.validate_network_connected
            testboot.destination_vm.vm.power_off()
