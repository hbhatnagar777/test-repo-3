# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Abstraction file for helping testcases validate DR functionalities for Failback
Failback:
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
from DROrchestration.Core import FailbackPeriodic, ReplicationPeriodic, FailbackContinuous, ReplicationContinuous
from DROrchestration._dr_operation import DROperation
from cvpysdk.drorchestration.drjob import DRJob


class Failback(DROperation):
    """This class is used to perform Failback validations"""

    SourcePhases = {
        "vmware": set(),
        "vmware_aux": set(),
        "vmware_continuous": set(),
        "vmware_warmsync": set(),
        "vmware_aux_warmsync": set(),
        "vmware_snap": set(),
        "azure resource manager": set(),
        "azure resource manager_aux": set(),
        "azure resource manager_dvdf": set(),
        "azure resource manager_aux_dvdf": set(),
        "azure resource manager_warmsync": set(),
        "azure resource manager_aux_warmsync": set(),
        "hyper-v": set(),
        "hyper-v_aux": set(),
        "hyper-v_warmsync": set(),
        "hyper-v_aux_warmsync": set(),
        "amazon web services": set(),
        "amazon web services_aux": set(),
        "amazon web services_dvdf": set(),
        "amazon web services_aux_dvdf": set(),
        "amazon web services_warmsync": set(),
        "amazon web services_aux_warmsync": set(),
    }

    DestinationPhases = {
        "vmware": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'POST_OPERATION', 'ENABLE_SYNC'},
        "vmware_aux": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'POST_OPERATION', 'ENABLE_SYNC'},
        "vmware_continuous": set(),
        "vmware_warmsync": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'POST_OPERATION', 'DELETE_DR_VM', 'ENABLE_SYNC'},
        "vmware_aux_warmsync": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'POST_OPERATION', 'DELETE_DR_VM', 'ENABLE_SYNC'},
        "vmware_snap": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'DELETE_SNAPSHOT', 'POST_OPERATION', 'ENABLE_SYNC'},
        "azure resource manager": set(),
        "azure resource manager_aux": set(),
        "azure resource manager_dvdf": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'DELETE_DR_VM', 'POST_OPERATION', 'ENABLE_SYNC'},
        "azure resource manager_aux_dvdf": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'DELETE_DR_VM', 'POST_OPERATION', 'ENABLE_SYNC'},
        "azure resource manager_warmsync": set(),
        "azure resource manager_aux_warmsync": set(),
        "hyper-v": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'POST_OPERATION', 'ENABLE_SYNC'},
        "hyper-v_aux": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'POST_OPERATION', 'ENABLE_SYNC'},
        "hyper-v_warmsync": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'POST_OPERATION', 'DELETE_DR_VM', 'ENABLE_SYNC'},
        "hyper-v_aux_warmsync": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'POST_OPERATION', 'DELETE_DR_VM', 'ENABLE_SYNC'},
        "amazon web services": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'POST_OPERATION', 'ENABLE_SYNC'},
        "amazon web services_aux": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'POST_OPERATION', 'ENABLE_SYNC'},
        "amazon web services_dvdf": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'POST_OPERATION', 'DELETE_DR_VM', 'ENABLE_SYNC'},
        "amazon web services_aux_dvdf": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'POST_OPERATION', 'DELETE_DR_VM', 'ENABLE_SYNC'},
        "amazon web services_warmsync": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'POST_OPERATION', 'DELETE_DR_VM', 'ENABLE_SYNC'},
        "amazon web services_aux_warmsync": {'SHUTDOWN', 'BACKUP', 'REPLICATION', 'POST_OPERATION', 'DELETE_DR_VM', 'ENABLE_SYNC'},
    }

    def _set_vm_list(self, vm_list: list):
        super()._set_vm_list(vm_list)
        for source_vm, core_args in self._vm_pairs.items():
            if self.is_continuous:
                self._vm_pairs[source_vm] = {
                    'Replication': ReplicationContinuous(**core_args),
                    'Failback': FailbackContinuous(**core_args),
                }
            else:
                self._vm_pairs[source_vm] = {
                    'Replication': ReplicationPeriodic(**core_args),
                    'Failback': FailbackPeriodic(**core_args),
                }

    @property
    def job_type(self):
        """Returns the expected job type"""
        return 'Failback'

    def is_failback_supported(self):
        """ Returns True if Failback is supported else returns False """
        # If Hypervisor is not Hyper-V then return True
        if self.destination_auto_instance.vsa_instance \
                .instance_name.lower() not in ['hyper-v']:
            return True
        elif self.source_auto_instance.vsa_instance \
                .instance_name.lower() not in ['hyper-v']:
            return False
        else:
            for source in self.vm_list:
                failback = self.vm_pairs[source]['Failback']
                if not failback.source_vm.is_failback_supported():
                    return False
            return True

    def pre_validation(self, **kwargs):
        """Validates the state before DR operation"""
        self.refresh()
        for source in self.vm_list:
            failback = self.vm_pairs[source]['Failback']
            failback.pre_validate_sync_status()
            failback.add_test_data(source=False)
            if not self.is_continuous:
                failback.validate_replication_guid(after_failback=False)

    def post_validation(self, **kwargs):
        """Validates this DR operation"""
        self.refresh()
        for source in self.vm_list:
            failback = self.vm_pairs[source]['Failback']
            replication = self.vm_pairs[source]['Replication']

            if not self.is_continuous:
                # TODO : Job ID to be passed in kwargs
                failback_job_id = str(
                    failback._live_sync_pair.failover_job_id) if failback._live_sync_pair.failover_job_id else None

                if not failback.is_warm_sync_enabled:
                    dr_job = DRJob(self._commcell, failback_job_id)
                    phases = dr_job.get_phases().get(source, [])
                    backup_found = replication_found = False
                    for phase in phases:
                        if phase.get('phase_name').name == 'BACKUP' and phase.get('job_id'):
                            replication.validate_backup_job(phase.get('job_id'))
                            failback.evaluate_backup_proxy()
                            backup_found = True
                        if phase.get('phase_name').name == 'REPLICATION' and phase.get('job_id'):
                            replication.validate_replication_job(job_id=phase.get('job_id'))
                            failback.evaluate_replication_proxy()
                            replication_found = True
                    if not backup_found:
                        raise Exception(f"Backup phase and job ID not found on DR job [{dr_job.job_id}]")
                    if not replication_found:
                        raise Exception(f"Replication phase and job ID not found on DR job [{dr_job.job_id}]")
                failback.validate_replication_guid(after_failback=True)
                failback.validate_snapshot(job_id=failback_job_id)

            failback.validate_power_state()
            failback.validate_sync_status()
            failback.validate_failover_status()

            if failback.is_dvdf_enabled:
                failback.validate_dvdf()
            if failback.is_warm_sync_enabled:
                failback.validate_warm_sync(dependent_resources_cleanup=True)

            failback.validate_boot(source=True)
            failback.refresh_vm(source=True)


            failback.validate_hardware(source=True)
            failback.validate_advanced(source=True, is_failover=False)


            failback.validate_test_data(source=True)
