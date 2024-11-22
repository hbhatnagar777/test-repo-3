# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for helping testcases validate DR functionalities for replication
Replication
    Methods:
        validate_sync_status():     Validates the sync status and returns True/False
        validate_power_state():     Validates whether the power state of the VMs is correct
        validate_snapshot():        Validates that the integrity snapshot exists with correct information
"""
import re

from AutomationUtils.constants import backup_level
from DROrchestration.Core._dr_validation import _DROrchestrationValidation
from cvpysdk.drorchestration.drjob import DRJob


class ReplicationPeriodic(_DROrchestrationValidation):
    """ This class is used to provide utility functions for validating replication sync"""

    def pre_validate_sync_status(self):
        """ Validates the sync status of the live sync pair before the operation """
        return

    def validate_sync_status(self):
        """ Validates the sync status of the live sync pair """
        self.refresh()
        if self._live_sync_pair.status != 'IN_SYNC':
            raise Exception(f"{self._live_sync_pair} is not in 'In sync' status")
        self.log.info('Sync status for VM pair %s verified after replication', str(self._live_sync_pair))

    def validate_backup_job(self, parent_job_id):
        """ Validates that this job is the last synced backup job
            Args:
                parent_job_id (str): Job ID of the last backup job
        """
        self.refresh()

        parent_job = self._commcell_object.job_controller.get(parent_job_id)
        child_backup_job_id = None
        for vm_info in parent_job.get_vm_list():
            if vm_info.get('vmName') == self._source_vm.vm_name:
                child_backup_job_id = str(vm_info.get('jobID', ''))
                break

        self.assert_comparison(str(self._live_sync_pair.last_synced_backup_job), str(child_backup_job_id))
        self.log.info('Backup job validation done for %s', self._live_sync_pair)

    def validate_replication_job(self, job_id=None, full_replication=False):
        """ Validates that the replication job size matches backup job size """
        # Make sure the job ID found in DR job phase is the one found on VM pair
        # Make sure that we do not add test data in between incremental backups 
        
        if job_id:
            self.assert_comparison(str(self._live_sync_pair.last_replication_job), str(job_id))

        self.assert_comparison(str(self._live_sync_pair.last_replication_job),
                               str(self._live_sync_pair.latest_replication_job))
        
        if not full_replication:
            replication_job = (self._commcell_object
                           .job_controller.get(str(self._live_sync_pair.latest_replication_job)))
                
            replication_job_stats = [vm for vm in replication_job.get_vm_list()
                                 if vm['vmName'] == self._source_vm.vm_name][0]

            expected_size = 0
            events = replication_job.get_events()

            #We are covering that scenario when there were any other full or incremental backups before an incremental backup.
            # and the replication job is replicating all of those Backup Jobs. So, we are verifying replication job size accordingly.
            
            for event in events:
                if event.get('eventCodeString') == "13:216":
                    job_description = event.get('description')
                    match =  re.search("\[([\d]+)\]", job_description)
                
                    backup_job_id = match.groups()[0]
                    backup_job = (self._commcell_object
                       .job_controller.get(backup_job_id))
                    backup_job_stats = \
                    [vm for vm in backup_job.get_vm_list() if vm['vmName'] == self._source_vm.vm_name]
                    if not backup_job_stats:
                        # If the backup doesn't have the VM as part of the job, skip that for calculation for this VM
                        continue
                    backup_job_stats = backup_job_stats[0]
                    backup_job_size = backup_job_stats.get(
                        'UsedSpace')
                    if backup_job_stats.get('backupLevel') == 1:
                        expected_size = backup_job_size
                        break
                    else:
                        expected_size += backup_job_size

            if replication_job_stats.get('restoredSize') > expected_size + 104857600:
                raise Exception(f"Replication job ID [{replication_job.job_id}] has replicated"
                                f" more data than expected for Incremental backup [{backup_job.job_id}]")
        self.log.info('Replication job validation done for %s', self._live_sync_pair)

    def validate_replication_job_type(self, job_id=None, job_type='INCREMENTAL'):
        """ Validates the replication job type """
        # TODO : Constants for job types

        full_replication_event_code = '1526727252'

        if not job_id:
            job_id = (self._commcell_object.job_controller.get(str(self._live_sync_pair.latest_replication_job))).job_id

        events = self._commcell_object.job_controller.get(str(job_id)).get_events()
        replication_events = [event for event in events if event['eventCode'] == full_replication_event_code]

        # TODO : ENUM for Job Type
        if (len(replication_events) and job_type != 'FULL') or (len(replication_events)==0 and job_type == 'FULL'):
            # 1. Incremental job converted to Full
            # 2. Expected Full Job converted to Incremental -> Least likely
            raise Exception("Job type is incorrect for Job ID [%s]" % job_id)

        self.log.info("Replication job type verified for job ID - [%s] as [%s]", job_id, job_type)
        return True

    def validate_power_state(self):
        """ Validates the power state of the source and destination VM """
        # Note : Power state validation is skipped for Warm Sync and DVDF (Reason : DRVM does not exist)
        if not (self.is_dvdf_enabled or self.is_warm_sync_enabled):
            self.refresh_vm(source=False, basic_only=True)
            if self.destination_vm.vm.is_powered_on():
                raise Exception("Destination VM [%s] is powered on after replication" % self._destination_vm.vm_name)
        self.log.info('Power states for VM pair %s verified after replication', str(self._live_sync_pair))

    def validate_snapshot(self):
        """ Validates that the integrity snapshot generated by sync is correct """
        # Create DRVM validation object and then verify the integrity snapshot of DRVM is correct
        # with the correct job ID
        if not (self.is_dvdf_enabled or self.is_warm_sync_enabled):
            replication_job_id = str(self._live_sync_pair.latest_replication_job)
            self.destination_vm.validate_snapshot(integrity_check=True, job_id=replication_job_id)
        self.log.info('Integrity snapshot for VM pair %s verified after replication', str(self._live_sync_pair))

    def validate_vm_deletion(self, delete_job_id: str = '', delete_vm_enabled: bool = False):
        """ Validates that the VM has been deleted from the monitor """

        # Make sure VM deleted from monitor
        live_sync_pairs = self.vm_pair.live_sync_pair
        live_sync_pairs.refresh()
        if self.vm_pair.vm_pair_name in live_sync_pairs.vm_pairs:
            raise Exception(f"VM {self.vm_pair} still found on replication monitor")

        if delete_job_id:
            # Make sure DR job has delete enabled/disabled as expected
            dr_job = DRJob(self._commcell_object, delete_job_id)
            delete_dest_in_job = (dr_job.task_details.get('subTasks', [{}])[0].get('options', {}).get('adminOpts', {})
                                  .get('drOrchestrationOption', {}).get('deleteDestVmFromHypervisor', False))
            if delete_dest_in_job != delete_vm_enabled:
                raise Exception(f"DR job ID {delete_job_id} doesn't have setting Delete dest VM: {delete_vm_enabled},"
                                f"instead has {delete_dest_in_job}")

        # Make sure VM is deleted from destination hypervisor
        if (delete_vm_enabled and self.destination_auto_instance.hvobj
                .check_vms_exist([self.vm_pair.destination_vm])):
            raise Exception(f"DR VM {self.vm_pair.destination_vm} still exists on destination hypervisor "
                            f"even after delete DR VM was selected")

    def evaluate_backup_proxy(self, failback=False, **kwargs):
        """ Validates the proxy used for last synced backup job for the vm pairs """

        expected_backup_proxy = kwargs.get('backup_proxy', self.destination_proxy_list if failback else self.source_proxy_list)

        # last synced Backup vm list
        backup_job = str(self.vm_pair.last_synced_backup_job)
        backup_job_obj = self._commcell_object.job_controller.get(backup_job)
        backup_vm_list = backup_job_obj.get_vm_list()

        # validates backup proxy for each vm is one from source hypervisor proxies list
        self.log.info("Validating last synced backup job proxy")
        for vm in backup_vm_list:
            bkp_proxy = vm.get("Agent").lower() if vm.get("Agent") else None
            if bkp_proxy is not None and bkp_proxy not in expected_backup_proxy:
                raise Exception(f"Source VM : {vm['vmName']} backup used proxy: {bkp_proxy}, expected"
                                f"proxy to be used: {self.source_proxy_list}")
            elif bkp_proxy is None:
                raise Exception("Backup proxy is None")
            else:
                self.log.info(f"Backup proxy for VM {vm['vmName']} [{bkp_proxy}] validated")

        self.log.info("Backup job %s proxies validated successfully", backup_job)

    def evaluate_replication_proxy(self, failback=False, **kwargs):
        """ Validates the proxy used for last successful replication job for the vm pairs """

        expected_replication_proxy = kwargs.get('replication_proxy', self.source_proxy_list if failback else self.destination_proxy_list)
        
        # last successful Replication vm list
        rep_job = str(self.vm_pair.latest_replication_job)
        rep_job_obj = self._commcell_object.job_controller.get(rep_job)
        rep_vm_list = rep_job_obj.get_vm_list()

        # validates replication job proxy for each vm is one from destination proxies list
        self.log.info("Validating last successful replication job proxy")
        for vm in rep_vm_list:
            rep_proxy = vm.get("Agent").lower() if vm.get("Agent") else None
            if rep_proxy is not None and rep_proxy not in expected_replication_proxy:
                raise Exception(f" Destination VM {vm['destinationVMName']} replication used proxy {rep_proxy} "
                                f"not present in proxy list : {expected_replication_proxy}")
            elif rep_proxy is None:
                raise Exception("Replication proxy is None")
            else:
                self.log.info(f"Replication proxy for VM {vm['vmName']} [{rep_proxy}] validated")

        self.log.info("Replication job %s proxy validated successfully", rep_job)

    def validate_no_test_boot_snapshot(self):
        """ Validates that the test-boot snapshot generated by job is not present in DR-VM"""
        self.refresh_vm(source=False, basic_only=True)
        self.destination_vm.validate_no_testboot_snapshot()
        self.log.info('Test boot snapshot validated for Destination VM %s', str(self._destination_vm.vm_name))

    def validate_network_connected(self):
        """ Validates that the network is in connected state"""
        self.destination_vm.validate_network_connected()
        self.log.info('Network in Destination VM %s is in connected state', str(self._destination_vm.vm_name))

    def validate_dvdf(self):
        """ Validates that the DVDF settings are honoured on the hypervisor after replication"""
        self.destination_vm.validate_dvdf()
        self.log.info('DVDF entities for VM pair %s verified before failover', str(self._live_sync_pair))


class ReplicationContinuous(_DROrchestrationValidation):
    def validate_snapshot(self):
        """ Validates that the snapshot generated by replication is correct """
        pass

    def pre_validate_sync_status(self):
        """ Validates the sync status of the live sync pair after the replication operation """
        pass

    def validate_sync_status(self):
        """ Validates the sync status of the live sync pair """
        pass

    def validate_failover_status(self):
        """ Validates the failover status of the live sync pair is in sync """
        pass

    def validate_power_state(self):
        """ Validates the power state of the source and destination VM """
        pass

    def validate_vm_deletion(self, **kwargs):
        """ Validates the delete pair operation from monitor """
        pass

    def validate_no_test_boot_snapshot(self):
        """ Validates that the test-boot snapshot generated by job is not present in DR-VM"""
        pass

    def validate_network_connected(self):
        """ Validates that the network is in connected state"""
        pass
