# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Abstraction file for helping testcases validate DR functionalities for Unplanned failover
UnplannedFailover:
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
from cvpysdk.drorchestration.drjob import DRJob

from DROrchestration.Core import FailoverPeriodic, FailoverContinuous
from DROrchestration.Core.replication import ReplicationPeriodic, ReplicationContinuous
from DROrchestration._dr_operation import DROperation
from time import sleep


class UnplannedFailover(DROperation):
    """This class is used to perform Unplanned failover validations"""

    SourcePhases = {
        "vmware": {'POWER_OFF', 'DISABLE_SYNC'},
        "vmware_continuous": {},
        "vmware_warmsync": {'POWER_OFF', 'ENABLE_SYNC', 'REPLICATION', 'DISABLE_SYNC'},
        "vmware_aux_warmsync": {'POWER_OFF', 'ENABLE_SYNC', 'REPLICATION', 'DISABLE_SYNC'},
        "azure resource manager": {'POWER_OFF', 'DISABLE_SYNC'},
        "azure resource manager_dvdf": {'POWER_OFF', 'DISABLE_SYNC'},
        "azure resource manager_warmsync": {'POWER_OFF', 'ENABLE_SYNC', 'REPLICATION', 'DISABLE_SYNC'},
        "azure resource manager_aux_warmsync": {'POWER_OFF', 'ENABLE_SYNC', 'REPLICATION', 'DISABLE_SYNC'},
        "hyper-v": {'POWER_OFF', 'DISABLE_SYNC'},
        "hyper-v_warmsync": {'POWER_OFF', 'ENABLE_SYNC', 'REPLICATION', 'DISABLE_SYNC'},
        "hyper-v_aux_warmsync": {'POWER_OFF', 'ENABLE_SYNC', 'REPLICATION', 'DISABLE_SYNC'},
        "amazon web services": {'POWER_OFF', 'DISABLE_SYNC'},
        "amazon web services_dvdf": {'POWER_OFF', 'DISABLE_SYNC'},
        "amazon web services_warmsync": {'POWER_OFF', 'ENABLE_SYNC', 'REPLICATION', 'DISABLE_SYNC'},
        "amazon web services_aux_warmsync": {'POWER_OFF', 'ENABLE_SYNC', 'REPLICATION', 'DISABLE_SYNC'},
    }

    DestinationPhases = {
        "vmware": {'POWER_ON', 'POST_OPERATION', 'POST_VM_FAILOVER','CREATE_SNAPSHOT', 'DELETE_SNAPSHOT'},
        "vmware_continuous": {},
        "vmware_warmsync": {'POWER_ON', 'POST_OPERATION', 'POST_VM_FAILOVER', 'CREATE_SNAPSHOT', 'DELETE_SNAPSHOT'},
        "vmware_aux_warmsync": {'POWER_ON', 'POST_OPERATION', 'POST_VM_FAILOVER', 'CREATE_SNAPSHOT', 'DELETE_SNAPSHOT'},
        "azure resource manager": {'POWER_ON', 'POST_OPERATION', 'POST_VM_FAILOVER'},
        "azure resource manager_dvdf": {'CREATE_DR_VM', 'POWER_ON', 'POST_OPERATION', 'POST_VM_FAILOVER'},
        "azure resource manager_dvdf_blobsretained": {'CREATE_DR_VM', 'POWER_ON', 'POST_OPERATION'},
        "azure resource manager_warmsync": {'POWER_ON', 'POST_OPERATION', 'POST_VM_FAILOVER'},
        "azure resource manager_aux_warmsync": {'POWER_ON', 'POST_OPERATION', 'POST_VM_FAILOVER'},
        "hyper-v": {'CREATE_SNAPSHOT', 'POWER_ON', 'DELETE_SNAPSHOT', 'POST_OPERATION'},
        "hyper-v_warmsync": {'POST_OPERATION', 'POWER_ON', 'CREATE_SNAPSHOT', 'DELETE_SNAPSHOT'},
        "hyper-v_aux_warmsync": {'POST_OPERATION', 'POWER_ON', 'CREATE_SNAPSHOT', 'DELETE_SNAPSHOT'},
        "amazon web services": {'POWER_ON', 'POST_OPERATION', 'POST_VM_FAILOVER'},
        "amazon web services_dvdf": {'POWER_ON', 'CREATE_DR_VM', 'POST_OPERATION', 'DELETE_SNAPSHOT'},
        "amazon web services_warmsync": {'POWER_ON', 'POST_OPERATION', 'POST_VM_FAILOVER', 'DELETE_SNAPSHOT'},
        "amazon web services_aux_warmsync": {'POWER_ON', 'POST_OPERATION', 'POST_VM_FAILOVER', 'DELETE_SNAPSHOT'},
    }

    def _set_vm_list(self, vm_list: list):
        super()._set_vm_list(vm_list)
        for source_vm, core_args in self._vm_pairs.items():
            if self.is_continuous:
                self._vm_pairs[source_vm] = {
                    'Failover': FailoverContinuous(**core_args),
                    'Replication': ReplicationContinuous(**core_args),
                }
            else:
                self._vm_pairs[source_vm] = {
                    'Failover': FailoverPeriodic(**core_args),
                    'Replication': ReplicationPeriodic(**core_args),
                }

    @property
    def job_type(self):
        """Returns the expected job type"""
        return 'Unplanned Failover'

    def pre_validation(self, **kwargs):
        """Validates the state before DR operation"""
        self.refresh()
        for source in self.vm_list:
            failover = self.vm_pairs[source]['Failover']
            replication = self.vm_pairs[source]['Replication']

            failover.pre_validate_sync_status()

            if replication.is_dvdf_enabled:
                    replication.validate_dvdf()

            if failover.is_warm_sync_enabled:
                failover.validate_warm_sync()
            failover.add_test_data(source=True)
        if self.is_continuous:
            """Waits for RPs to be generated"""
            sleep(300)


    def post_validation(self, **kwargs):
        """Validates this DR operation"""
        self.refresh()
        for source in self.vm_list:
            failover = self.vm_pairs[source]['Failover']
            if not self.is_continuous:
                dr_job = DRJob(self._commcell, failover._live_sync_pair.failover_job_id)
            if failover.is_warm_sync_enabled:
                replication = self.vm_pairs[source]['Replication']
                phases = dr_job.get_phases().get(source, [])
                replication_found = False
                for phase in phases:
                    if phase.get('phase_name').name == 'REPLICATION' and phase.get('job_id'):
                        replication.validate_replication_job(job_id=phase.get('job_id'),
                                                             full_replication=failover.is_warm_sync_enabled)
                        replication_found = True
                if not replication_found:
                    raise Exception(f"Replication phase and job ID not found on DR job [{dr_job.job_id}]")


            failover.validate_power_state()
            failover.validate_sync_status()
            failover.validate_failover_status()

            if failover.is_dvdf_enabled:
                failover.validate_dvdf()

            failover.validate_boot(source=False)
            failover.refresh_vm(source=False)

            failover.validate_snapshot()
            if not self.is_continuous:
                blobs_retained = dr_job.blobs_retained()
                failover.validate_hardware(blobs_retained=blobs_retained, source=False)
            else:
                failover.validate_hardware(source=False)
            failover.validate_advanced(source=False)

            if kwargs.get('test_data', True):
                # In case of continuous pairs, the sync data will always be synced before post_validation reaches here
                if self.is_continuous:
                    failover.validate_test_data(source=False)
                else:
                    failover.validate_no_test_data(source=False)
