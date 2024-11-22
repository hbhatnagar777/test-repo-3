# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" File for helping testcases validate DR functionalities for Delete VM
DeleteVM:
    Class Variables:
        SourcePhases
        DestinationPhases
    Methods:
        _set_vm_list(vm_list)
        pre_validation(**kwargs)
        post_validation(**kwargs)
        job_phase_validation(job_id)
"""
from DROrchestration.Core import ReplicationPeriodic, ReplicationContinuous
from DROrchestration._dr_operation import DROperation

class DeleteVM(DROperation):
    """This class is used to perform Delete VM validations"""

    SourcePhases = {
        "vmware": {'DISABLE_SYNC'},
        "vmware_aux": set(),
        "vmware_continuous": set(),
        "vmware_warmsync": set(),
        "vmware_aux_warmsync": set(),
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
        "vmware": {'DELETE_VM', 'POWER_OFF'},
        "vmware_aux": set(),
        "vmware_continuous": set(),
        "vmware_warmsync": set(),
        "vmware_aux_warmsync": set(),
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
        return 'Cleanup Destination VM'

    def pre_validation(self, **kwargs):
        """Validates the state before DR operation"""
        return

    def warm_sync_conversion_validation(self, to_warm_site=True, conversion_job_id=''):
        """
        Validates that the conversion to hot site/warm site was successfully done on group, DR site and pair level
        :arg to_warm_site:  (bool) Whether expected value of warm sync is enabled/disabled
        :arg conversion_job_id: (str) The job ID for hot->warm conversion
        """
        self.refresh()

        # Warm site flag is set on group as expected
        if to_warm_site != self.group.is_warm_sync_enabled:
            raise Exception(f"Warm sync state on group: {self.group.is_warm_sync_enabled}, "
                            f"expected warm sync flag: {to_warm_site}")

        for source_vm, vm_pair_dict in self.vm_pairs.items():
            replication = vm_pair_dict['Replication']
            if replication.is_warm_sync_enabled != self.group.is_warm_sync_enabled:
                raise Exception(f"Warm sync flag incorrect for VM pair: {replication.vm_pair}. "
                                f"Observed: {replication.is_warm_sync_enabled}, "
                                f"expected: {self.group.is_warm_sync_enabled}")

            if to_warm_site:
                # If hot->warm conversion, validate VMs are deleted, and job ID has correct phases
                replication.validate_vm_deletion(delete_vm_enabled=True, delete_job_id=conversion_job_id)

    def post_validation(self, **kwargs):
        """Validates this DR operation"""
        self.refresh()
        for source in self.vm_list:
            replication = self.vm_pairs[source]['Replication']
            replication.validate_vm_deletion(**kwargs)

        # Make sure deletion from group's configuration tab is done
        self.group.refresh()
        vms_left_deleted = set(self.vm_list).intersection(set(self.group.restore_options))
        if vms_left_deleted:
            raise Exception(f"VMs still left in replication group even after performing delete:"
                            f" {vms_left_deleted}")

    def job_phase_validation(self, job_id: str):
        """Skip job phase validation if delete VM is disabled"""
        return
        # This code has been commented, because the phase's key for source cannot be fetched from job API calls
        # So, to make a change would need to make a signature change in get_phases function to use replication pair id
        # to make job phase validation
        # dr_job = DRJob(self._commcell, job_id)
        # delete_dest_in_job = (dr_job.task_details.get('subTasks', [{}])[0].get('options', {}).get('adminOpts', {})
        #                       .get('drOrchestrationOption', {}).get('deleteDestVmFromHypervisor', False))
        #
        # if delete_dest_in_job:
        #     super().job_phase_validation(job_id)
