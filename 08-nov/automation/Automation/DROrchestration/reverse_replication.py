# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Abstraction file for helping testcases validate DR functionalities for Reverse Replication
ReverseReplication:
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
from time import sleep
from cvpysdk.drorchestration.drjob import DRJob
from DROrchestration.Core import ReplicationPeriodic, FailoverPeriodic
from DROrchestration._dr_operation import DROperation


class ReverseReplication(DROperation):
    """This class is used to perform reverse replication validations"""
    JobTitle = 'Reverse Replication'

    SourcePhases = {
       "vmware": {'DISABLE_SYNC', 'BACKUP', 'REPLICATION'},
       "vmware_aux": {'DISABLE_SYNC', 'BACKUP', 'REPLICATION', 'AUX_COPY'},
        "vmware_warmsync": set(),
        "vmware_aux_warmsync": set(),
    }

    DestinationPhases = {
        "vmware": set(),
        "vmware_aux": set(),
        "vmware_warmsync": set(),
        "vmware_aux_warmsync": set(),
    }

    def _set_vm_list(self, vm_list: list):
        super()._set_vm_list(vm_list)
        for source_vm, core_args in self._vm_pairs.items():
            self._vm_pairs[source_vm] = {
                'Failover': FailoverPeriodic(**core_args),
                'Replication': ReplicationPeriodic(**core_args),
            }

    @property
    def job_type(self):
        """Returns the expected job type"""
        return 'Reverse Replication'

    def pre_validation(self, **kwargs):
        """Validates the state before DR operation"""
        self.refresh()
        for source in self.vm_list:
            failover = self.vm_pairs[source]['Failover']

            failover.validate_sync_status()
            failover.validate_failover_status()
            rr_schedule_schedule_id = failover._live_sync_pair.reverse_replication_schedule_id
            if not rr_schedule_schedule_id:
                raise Exception(f"No reverse replication schedules found for [{failover._live_sync_pair}]")

            failover.add_test_data(source=False)

    def post_validation(self, **kwargs):
        """Validates this DR operation"""
        self.refresh()
        for source in self.vm_list:
            replication = self.vm_pairs[source]['Replication']
            failover = self.vm_pairs[source]['Failover']

            failover.validate_sync_status()
            failover.validate_failover_status()

            failover.validate_power_state()

            dr_job = DRJob(self._commcell, failover._live_sync_pair.failover_job_id)
            phases = dr_job.get_phases().get(source, [])
            for phase in phases:
                if phase.get('phase_name').name == 'BACKUP' and phase.get('job_id'):
                    replication.validate_backup_job(phase.get('job_id'))
                    replication.evaluate_backup_proxy(failback=True)
                    replication.validate_replication_job()
                    replication.evaluate_replication_proxy(failback=True)
                    break
            else:
                raise Exception(f"Backup phase job ID not found in failback job [{dr_job.job_id}]")

            failover.source_vm.validate_snapshot(integrity_check=True, job_id=dr_job.job_id)

            failover.source_vm.vm.power_on()

            self.log.info('Waiting for 2 minutes to let VM power on')
            sleep(120)
            failover.validate_boot(source=True)
            failover.refresh_vm(source=True)
            failover.validate_hardware(source=True)
            failover.validate_advanced(source=True)

            failover.validate_test_data(source=True)
            failover.source_vm.vm.power_off()

            failover.cleanup_test_data(source=True)
