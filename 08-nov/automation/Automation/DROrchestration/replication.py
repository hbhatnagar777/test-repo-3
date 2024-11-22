# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Abstraction file for helping testcases validate DR functionalities for Replication
Replication:
    Methods:
        vm_list             : The setter function for the VMs to be included as part of operation validation
        pre_validation      : The function to perform validations before the operation is performed
        post_validation     : The function to perform validations after the operation is performed
"""
import time
from enum import Enum

from cvpysdk.exception import SDKException

from DROrchestration.Core import ReplicationPeriodic, ReplicationContinuous
from DROrchestration._dr_operation import DROperation

class Replication(DROperation):
    """This class is used to perform replication validations"""

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
        return 'Replication'

    def pre_validation(self, **kwargs):
        """Validates the state before DR operation"""
        if not self.vm_list:
            raise Exception("VM pairs not added to replication/failover group")
        for source in self.vm_list:
            replication = self.vm_pairs[source]['Replication']
            replication.add_test_data(source=True)

    def wait_for_first_backup(self):
        """
        Waits for all running backup jobs to finish and for all VM pairs
        to be created at least once (at least 1 backup)
        """
        # Attempt 15 times to let backup job trigger and complete
        for _ in range(15):
            try:
                if not all(self._vm_pairs.values()):
                    # VM filter applied
                    vms_left = set(self.vm_list) - set(self.group.live_sync_pairs)
                else:
                    # Get from configuration about all VMs in group
                    vms_left = set(self.restore_options.keys()) - set(self.group.live_sync_pairs)
            except SDKException:
                vms_left = set(self.restore_options.keys())

            # Break out if all VMs are backed up
            if not vms_left:
                self.log.info('All VMs for group [%s] have backed up', self.group.group_name)
                break

            jobs_list = self._commcell.job_controller.active_jobs(client_name=self.group.source_client.client_name,
                                                                  job_filter='Backup,SYNTHFULL',
                                                                  )
            for job_id, job_dict in jobs_list.items():
                if job_dict['subclient_id'] != int(self.group.subclient._subclient_id):
                    continue

                backup_job = self._commcell.job_controller.get(str(job_id))

                vms_backed_up = {vm_dict.get('vmName') for vm_dict in backup_job.get_vm_list()
                                 if vm_dict.get('vmName')}

                # In case no VMs from VM list are backed up by this job, go to next job in loop
                if not vms_left.intersection(vms_backed_up):
                    continue
                vms_left -= vms_backed_up

                self.log.info('Waiting for backup job [%s] to complete', job_id)
                backup_job.wait_for_completion()
                if backup_job.status != 'Completed':
                    raise Exception(f"Backup job [{job_id}] failed to complete")
                self.log.info('Backup job [%s] completed', job_id)

            # Break out if all VMs are backed up
            if not vms_left:
                self.log.info('All VMs for group [%s] have backed up', self.group.group_name)
                break

            # Wait for 5 minutes to let new backup job be triggered
            for _ in range(5):
                jobs_list = self._commcell.job_controller.active_jobs(client_name=self.group.source_client.client_name,
                                                                      job_filter='Backup,SYNTHFULL')
                if jobs_list:
                    break
                self.log.info('Waiting for 1 minute to let a new backup job get triggered %s', str(vms_left))
                time.sleep(60)

        # Wait for live sync to update
        for _ in range(20):
            self.group.subclient.live_sync.refresh()
            if self.group.subclient.live_sync.has_live_sync_pair(self.group.group_name.replace('_ReplicationPlan__ReplicationGroup', '')):
                break
            self.log.info('Waiting for 30 seconds to let live sync update')
            time.sleep(30)
    def get_last_replication_job_id(self):
        """ Returns the last replication job id"""
        for vm_pair_dict in self.vm_pairs.values():
            self.vm_pair = list(vm_pair_dict.values())[0].vm_pair
        return self.vm_pair.last_replication_job

    def get_running_replication_jobs(self):
        """Waits for all VMs in vm list to be replicated/synced"""
        # Attempt 15 times to let replication job trigger and complete
        for _ in range(15):
            vms_to_sync = set()
            for vm_pair_dict in self.vm_pairs.values():
                vm_pair = list(vm_pair_dict.values())[0].vm_pair
                vm_pair.refresh()
                if vm_pair.status not in ['IN_SYNC', 'SYNC_DISABLED', 'SYNC_FAILED']:
                    vms_to_sync.add(vm_pair.source_vm)

            # Break out if all VMs are synced
            if not vms_to_sync:
                self.log.info('All VMs for group [%s] have been replicated', self.group.group_name)
                break
            self.log.info("Waiting for VM pairs %s to sync", str(self.vm_pairs))
            
            replications_triggered = set()
            for vm_pair_dict in self.vm_pairs.values():
                vm_pair = list(vm_pair_dict.values())[0].vm_pair
                vm_pair.refresh()
                if vm_pair.status == 'SYNC_IN_PROGRESS' and vm_pair.last_replication_job:
                    replications_triggered.add(str(vm_pair.last_replication_job))

            for replication_job_id in replications_triggered:
                replication_job = self._commcell.job_controller.get(str(replication_job_id))
                replication_job.wait_for_completion()

                self.log.info('Waiting for replication job [%s] to complete', str(replication_job_id))
                if replication_job.status != 'Completed':
                    raise Exception(f"Replication job [{replication_job_id}] failed to complete")
                self.log.info('Replication job [%s] completed', str(replication_job_id))
                vms_replicated = {vm_dict.get('vmName') for vm_dict in replication_job.get_vm_list()
                                  if vm_dict.get('vmName')}
                vms_to_sync -= vms_replicated

            # Break out if all VMs are synced
            if not vms_to_sync:
                self.log.info('All VMs for group [%s] have been replicated', self.group.group_name)
                break

            # Wait for 15 minutes to let new replication job be triggered
            for _ in range(15):
                replication_triggered = False
                for vm_pair_dict in self.vm_pairs.values():
                    vm_pair = list(vm_pair_dict.values())[0].vm_pair
                    vm_pair.refresh()
                    if vm_pair.status == 'SYNC_IN_PROGRESS':
                        replication_triggered = True
                        break
                if replication_triggered:
                    break
                self.log.info('Waiting for 1 minute to let a new replication job get triggered %s', str(vms_to_sync))
                time.sleep(60)

    def post_validation(self, **kwargs):
        """
        Validates this DR operation
        kwargs : 
                1. backup_job_id (str) : Parent Job ID
                2. validate_test_data (bool) : If test data needs to be validated
                    Default case: Test Data is validated unless specified
                3. test_data (bool) : If DRVM should contain the Test Data
                    Default case: Validates if DRVM contains the Test Data
        """

        if not self.vm_list:
            raise Exception("VM pairs not added to replication/failover group")
        self.refresh()
        for source in self.vm_list:
            replication = self.vm_pairs[source]['Replication']

            replication.validate_power_state()
            replication.validate_sync_status()
            if kwargs.get('backup_job_id'):
                replication.validate_backup_job(backup_job_id=kwargs.get('backup_job_id'))
                replication.evaluate_backup_proxy()

            # If VM pair is DVDF, validate the storage account blobs and VM not present
            if replication.is_dvdf_enabled:
                replication.validate_dvdf()

            # If VM pair is warm sync, perform warm sync validation
            if replication.is_warm_sync_enabled:
                replication.validate_warm_sync()
            else:
                # If VM pair is not warm sync, validate replication job set in monitor
                # TODO : ENUM for Job Type
                job_type = kwargs.get('job_type', 'INCREMENTAL')
                full_replication = True if job_type == 'FULL' else False
                replication.validate_replication_job(full_replication=full_replication)
                replication.validate_replication_job_type(job_type=job_type)
                replication.evaluate_replication_proxy(**kwargs)

            # If the VM pair is not warm sync or DVDF, perform DRVM validations
            if not (replication.is_dvdf_enabled or replication.is_warm_sync_enabled):
                replication.validate_snapshot()
                replication.destination_vm.vm.power_on()

                self.log.info('Waiting for 2 minutes to let VM IP update')
                time.sleep(120)
                replication.validate_boot(source=False)
                replication.refresh_vm(source=False)

                replication.validate_hardware(source=False)
                replication.validate_advanced(source=False)

                if kwargs.get('validate_test_data', True):
                    replication.validate_test_data(source=False) if kwargs.get(
                        'test_data', True) else replication.validate_no_test_data(source=False)

                replication.destination_vm.vm.power_off()
