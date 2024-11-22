# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Abstraction file for helping testcases validate DR functionalities for Planned failover
PlannedFailover:
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
from DROrchestration.Core import FailoverPeriodic, ReplicationPeriodic, FailoverContinuous, ReplicationContinuous
from DROrchestration._dr_operation import DROperation
from cvpysdk.drorchestration.drjob import DRJob
from time import sleep


class PlannedFailover(DROperation):
    """This class is used to perform Planned failover validations"""

    SourcePhases = {
        "vmware": {'SHUTDOWN', 'DISABLE_SYNC', 'BACKUP', 'REPLICATION'},
        "vmware_aux": {'SHUTDOWN', 'DISABLE_SYNC', 'BACKUP', 'REPLICATION', 'AUX_COPY'},
        "vmware_continuous": set(),
        "vmware_warmsync": {'SHUTDOWN', 'DISABLE_SYNC', 'BACKUP', 'ENABLE_SYNC', 'REPLICATION'},
        "vmware_aux_warmsync": {'SHUTDOWN', 'DISABLE_SYNC', 'BACKUP', 'ENABLE_SYNC', 'REPLICATION', 'AUX_COPY'},
        "vmware_snap": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'DISABLE_SYNC'},
        "azure resource manager": {'SHUTDOWN', 'DISABLE_SYNC', 'BACKUP', 'REPLICATION'},
        "azure resource manager_aux": {'SHUTDOWN', 'DISABLE_SYNC', 'BACKUP', 'REPLICATION', 'AUX_COPY'},
        "azure resource manager_dvdf": {'SHUTDOWN', 'DISABLE_SYNC', 'BACKUP', 'REPLICATION'},
        "azure resource manager_aux_dvdf": {'SHUTDOWN', 'DISABLE_SYNC', 'BACKUP', 'REPLICATION', 'AUX_COPY'},
        "azure resource manager_warmsync": set(),
        "azure resource manager_aux_warmsync": set(),
        "hyper-v": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'DISABLE_SYNC'},
        "hyper-v_aux": {'SHUTDOWN', 'BACKUP', 'AUX_COPY', 'REPLICATION', 'DISABLE_SYNC'},
        "hyper-v_warmsync": {'SHUTDOWN', 'BACKUP', 'ENABLE_SYNC', 'REPLICATION', 'DISABLE_SYNC'},
        "hyper-v_aux_warmsync": {'SHUTDOWN', 'BACKUP', 'AUX_COPY', 'ENABLE_SYNC', 'REPLICATION', 'DISABLE_SYNC'},
        "amazon web services": {'SHUTDOWN', 'DISABLE_SYNC', 'BACKUP', 'REPLICATION'},
        "amazon web services_aux": {'SHUTDOWN', 'DISABLE_SYNC', 'BACKUP', 'AUX_COPY', 'REPLICATION'},
        "amazon web services_dvdf": {'SHUTDOWN', 'DISABLE_SYNC', 'BACKUP', 'REPLICATION'},
        "amazon web services_aux_dvdf": {'SHUTDOWN', 'DISABLE_SYNC', 'BACKUP', 'AUX_COPY', 'REPLICATION'},
        "amazon web services_warmsync": {'SHUTDOWN', 'DISABLE_SYNC', 'BACKUP', 'ENABLE_SYNC', 'REPLICATION'},
        "amazon web services_aux_warmsync": {'SHUTDOWN', 'DISABLE_SYNC', 'BACKUP', 'AUX_COPY', 'ENABLE_SYNC', 'REPLICATION'},
    }

    DestinationPhases = {
        "vmware": {'CREATE_SNAPSHOT', 'POWER_ON', 'DELETE_SNAPSHOT', 'POST_OPERATION', 'POST_VM_FAILOVER'},
        "vmware_aux": {'CREATE_SNAPSHOT', 'POWER_ON', 'DELETE_SNAPSHOT', 'POST_OPERATION', 'POST_VM_FAILOVER'},
        "vmware_continuous": set(),
        "vmware_warmsync": {'CREATE_SNAPSHOT', 'POWER_ON', 'DELETE_SNAPSHOT', 'POST_OPERATION', 'POST_VM_FAILOVER'},
        "vmware_aux_warmsync": {'CREATE_SNAPSHOT', 'POWER_ON', 'DELETE_SNAPSHOT', 'POST_OPERATION', 'POST_VM_FAILOVER'},
        "vmware_snap": {'CREATE_SNAPSHOT', 'POWER_ON', 'DELETE_SNAPSHOT', 'POST_OPERATION', 'POST_VM_FAILOVER'},
        "azure resource manager": {'POWER_ON', 'POST_OPERATION', 'POST_VM_FAILOVER'},
        "azure resource manager_aux": {'POWER_ON', 'POST_OPERATION', 'POST_VM_FAILOVER'},
        "azure resource manager_dvdf": {'CREATE_DR_VM', 'POWER_ON', 'POST_OPERATION', 'POST_VM_FAILOVER'},
        "azure resource manager_aux_dvdf": {'CREATE_DR_VM', 'POWER_ON', 'POST_OPERATION', 'POST_VM_FAILOVER'},
        "azure resource manager_dvdf_blobsretained": {'CREATE_DR_VM', 'POWER_ON', 'POST_OPERATION'},
        "azure resource manager_aux_dvdf_blobsretained": {'CREATE_DR_VM', 'POWER_ON', 'POST_OPERATION'},
        "azure resource manager_warmsync": {'POWER_ON', 'POST_OPERATION', 'POST_VM_FAILOVER'},
        "azure resource manager_aux_warmsync": {'POWER_ON', 'POST_OPERATION', 'POST_VM_FAILOVER'},
        "hyper-v": {'CREATE_SNAPSHOT', 'POWER_ON', 'DELETE_SNAPSHOT', 'POST_OPERATION'},
        "hyper-v_aux": {'CREATE_SNAPSHOT', 'POWER_ON', 'DELETE_SNAPSHOT', 'POST_OPERATION'},
        "hyper-v_warmsync": {'CREATE_SNAPSHOT', 'POWER_ON', 'DELETE_SNAPSHOT', 'POST_OPERATION'},
        "hyper-v_aux_warmsync": {'CREATE_SNAPSHOT', 'POWER_ON', 'DELETE_SNAPSHOT', 'POST_OPERATION'},
        "amazon web services": {'POWER_ON', 'POST_OPERATION', 'POST_VM_FAILOVER'},
        "amazon web services_aux": {'POWER_ON', 'POST_OPERATION', 'POST_VM_FAILOVER'},
        "amazon web services_dvdf": {'POWER_ON', 'POST_OPERATION', 'DELETE_SNAPSHOT', 'CREATE_DR_VM'},
        "amazon web services_aux_dvdf": {'POWER_ON', 'POST_OPERATION', 'DELETE_SNAPSHOT', 'CREATE_DR_VM'},
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
        return 'Planned Failover'

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
            replication = self.vm_pairs[source]['Replication']

            # Perform job phase validations only for periodic replication
            if not self.is_continuous:
                failover_job_id = str(failover._live_sync_pair.failover_job_id)
                dr_job = DRJob(self._commcell, failover_job_id)
                phases = dr_job.get_phases().get(source, [])
                backup_found = replication_found = False
                blobs_retained = dr_job.blobs_retained()
                for phase in phases:
                    if phase.get('phase_name').name == 'BACKUP' and phase.get('job_id'):
                        replication.validate_backup_job(phase.get('job_id'))
                        replication.evaluate_backup_proxy()
                        backup_found = True
                    if phase.get('phase_name').name == 'REPLICATION' and phase.get('job_id'):
                        replication.validate_replication_job(job_id=phase.get('job_id'),
                                                             full_replication=failover.is_warm_sync_enabled)
                        replication.evaluate_replication_proxy()
                        replication_found = True
                if not backup_found:
                    raise Exception(f"Backup phase and job ID not found on DR job [{dr_job.job_id}]")
                if not replication_found:
                    raise Exception(f"Replication phase and job ID not found on DR job [{dr_job.job_id}]")

            failover.validate_power_state()
            failover.validate_sync_status()
            failover.validate_failover_status()

            if failover.is_dvdf_enabled:
                failover.validate_dvdf()
            failover.validate_boot(source=False)
            failover.refresh_vm(source=False)

            if not self.is_continuous:
                failover.validate_snapshot(job_id=failover_job_id)
                failover.validate_hardware(blobs_retained=blobs_retained, source=False)
            else:
                failover.validate_snapshot()
                failover.validate_hardware(source=False)
            # Skip storage account check for warm sync, as we should not do blobs validation in that case
            failover.validate_advanced(source=False, skip_storage_check=failover.is_warm_sync_enabled)
            failover.validate_test_data(source=False)
