# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Abstraction file for helping testcases validate DR functionalities for Undo failover
UndoFailover:
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
from DROrchestration.Core import FailbackPeriodic, FailbackContinuous
from DROrchestration._dr_operation import DROperation


class UndoFailover(DROperation):
    """This class is used to perform Undo failover validations"""

    SourcePhases = {
        "vmware": {'POWER_ON', 'ENABLE_SYNC'},
        "vmware_aux": set(),
        "vmware_continuous": set(),
        "vmware_warmsync": {'POWER_ON', 'ENABLE_SYNC'},
        "vmware_aux_warmsync": {'POWER_ON', 'ENABLE_SYNC'},
        "azure resource manager": set(),
        "azure resource manager_aux": set(),
        "azure resource manager_dvdf": set(),
        "azure resource manager_aux_dvdf": set(),
        "azure resource manager_warmsync": {'POWER_ON', 'ENABLE_SYNC'},
        "azure resource manager_aux_warmsync": {'POWER_ON', 'ENABLE_SYNC'},
        "hyper-v": {'POWER_ON', 'ENABLE_SYNC'},
        "hyper-v_aux": {'POWER_ON', 'ENABLE_SYNC'},
        "hyper-v_warmsync": {'POWER_ON', 'ENABLE_SYNC'},
        "hyper-v_aux_warmsync": {'POWER_ON', 'ENABLE_SYNC'},
        "amazon web services": {},
        "amazon web services_dvdf": {'POWER_ON', 'ENABLE_SYNC'},
        "amazon web services_aux_dvdf": {'POWER_ON', 'ENABLE_SYNC'},
        "amazon web services_warmsync": {'POWER_ON', 'ENABLE_SYNC'},
        "amazon web services_aux_warmsync": {'POWER_ON', 'ENABLE_SYNC'},
    }

    DestinationPhases = {
        "vmware": {'DELETE_SNAPSHOT', 'REVERT_SNAPSHOT', 'SHUTDOWN'},
        "vmware_aux": {'DELETE_SNAPSHOT', 'REVERT_SNAPSHOT', 'SHUTDOWN'},
        "vmware_continuous": set(),
        "vmware_warmsync": {'DELETE_DR_VM', 'DELETE_SNAPSHOT', 'REVERT_SNAPSHOT', 'SHUTDOWN'},
        "vmware_aux_warmsync": {'DELETE_DR_VM', 'DELETE_SNAPSHOT', 'REVERT_SNAPSHOT', 'SHUTDOWN'},
        "azure resource manager": set(),
        "azure resource manager_aux": set(),
        "azure resource manager_dvdf": set(),
        "azure resource manager_aux_dvdf": set(),
        "azure resource manager_warmsync": set(),
        "azure resource manager_aux_warmsync": set(),
        "hyper-v": {'DELETE_SNAPSHOT', 'REVERT_SNAPSHOT', 'SHUTDOWN'},
        "hyper-v_aux": {'DELETE_SNAPSHOT', 'REVERT_SNAPSHOT', 'SHUTDOWN'},
        "hyper-v_warmsync": {'DELETE_DR_VM', 'DELETE_SNAPSHOT', 'REVERT_SNAPSHOT', 'SHUTDOWN'},
        "hyper-v_aux_warmsync": {'DELETE_DR_VM', 'DELETE_SNAPSHOT', 'REVERT_SNAPSHOT', 'SHUTDOWN'},
        "amazon web services": set(),
        "amazon web services_aux": set(),
        "amazon web services_dvdf": {'DELETE_VM', 'SHUTDOWN'},
        "amazon web services_aux_dvdf": {'DELETE_VM', 'SHUTDOWN'},
        "amazon web services_warmsync": {'SHUTDOWN', 'DELETE_DR_VM'},
        "amazon web services_aux_warmsync": {'SHUTDOWN', 'DELETE_DR_VM'},
    }

    def _set_vm_list(self, vm_list: list):
        super()._set_vm_list(vm_list)
        for source_vm, core_args in self._vm_pairs.items():
            if self.is_continuous:
                self._vm_pairs[source_vm] = {
                    'Failback': FailbackContinuous(**core_args),
                }
            else:
                self._vm_pairs[source_vm] = {
                    'Failback': FailbackPeriodic(**core_args),
                }

    @property
    def job_type(self):
        """Returns the expected job type"""
        return 'Undo Failover'

    def pre_validation(self, **kwargs):
        """Validates the state before DR operation"""
        self.refresh()
        for source in self.vm_list:
            failback = self.vm_pairs[source]['Failback']
            failback.pre_validate_sync_status()
            failback.add_test_data(source=False)

    def post_validation(self, **kwargs):
        """Validates this DR operation"""
        self.refresh()
        for source in self.vm_list:
            failback = self.vm_pairs[source]['Failback']

            failback.validate_power_state()
            failback.validate_sync_status()
            failback.validate_failover_status()

            if failback.is_dvdf_enabled:
                failback.validate_dvdf()
            if failback.is_warm_sync_enabled:
                failback.validate_warm_sync(dependent_resources_cleanup=True)
            failback.validate_boot(source=True)
            failback.refresh_vm(source=True)

            failback.validate_snapshot()
            failback.validate_hardware(source=True)
            failback.validate_advanced(source=True)
            failback.validate_no_test_data(source=True)
