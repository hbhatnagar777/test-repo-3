# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Abstraction file for helping testcases validate DR functionalities for Test failover
TestFailover:
    Methods:
"""
import re
from DROrchestration.Core import TestFailoverPeriodic, TestFailoverContinuous
from DROrchestration._dr_operation import DROperation
from cvpysdk.drorchestration.drjob import DRJob


class TestFailover(DROperation):
    """Class used for validating Test failover operations"""

    SourcePhases = {
        "vmware_warmsync": {},
        "azure resource manager_warmsync": {},
        "hyper-v_warmsync": {},
        "amazon web services_warmsync": {"RESTORE_VM"},
    }

    DestinationPhases = {
        "vmware": {},
        "vmware_aux": {},
        "vmware_continuous": {},
        "vmware_warmsync": {},
        "azure resource manager": {},
        "azure resource manager_aux": {},
        "azure resource manager_dvdf": {},
        "azure resource manager_aux_dvdf": {},
        "azure resource manager_warmsync": {},
        "hyper-v": {},
        "hyper-v_aux": {},
        "hyper-v_warmsync": {},
        "amazon web services": {'GET_VM_INFO'},
        "amazon web services_aux": {'GET_VM_INFO'},
        "amazon web services_warmsync": {},
        "hyper-v_vmware": {'GET_VM_INFO'},
    }

    ClonePhases = {
        "vmware": {"LIVE_MOUNT"},
        "vmware_aux": {},
        "vmware_continuous": {},
        "vmware_warmsync": {},
        "azure resource manager": {},
        "azure resource manager_aux": {},
        "azure resource manager_dvdf": {"CLONE_VM", "REFRESH_VM"},
        "azure resource manager_aux_dvdf": {"CLONE_VM", "REFRESH_VM"},
        "azure resource manager_warmsync": {},
        "hyper-v": {},
        "hyper-v_aux": {},
        "hyper-v_warmsync": {},
        "amazon web services": {"CLONE_VM", "REFRESH_VM", "POWER_ON"},
        "amazon web services_aux": {"CLONE_VM", "REFRESH_VM", "POWER_ON"},
        "amazon web services_warmsync": {"GET_VM_INFO", "REFRESH_VM", "POWER_ON"},
        "hyper-v_vmware": {'CREATE_VM', 'REFRESH_VM', 'POWER_ON'},
    }

    def _set_vm_list(self, vm_list: list):
        super()._set_vm_list(vm_list)
        for source_vm, core_args in self._vm_pairs.items():
            if self.is_continuous:
                self._vm_pairs[source_vm] = {
                    'TestFailover': TestFailoverContinuous(**core_args),
                }
            else:
                self._vm_pairs[source_vm] = {
                    'TestFailover': TestFailoverPeriodic(**core_args),
                }

    @property
    def job_type(self):
        """Returns the expected job type"""
        if self.is_continuous:
            return "VM Test Failover (Continuous)"
        else:
            return "Test Failover"

    def get_job_ids(self, cloned_vm_name):
        """Returns Test Failover Job Ids"""
        pattern = "\S*-Clone-(\d*)"
        return re.match(pattern, cloned_vm_name).groups()[0]

    def update_clone_details(self, clone_vms: dict):
        """Updates the clone VM details"""
        for source_vm in self.vm_list:
            cloned_vm_names = [
                clone_vm['Name'] for clone_vm in clone_vms[source_vm]]
            test_failover : TestFailoverPeriodic | TestFailoverContinuous = self.vm_pairs[source_vm]['TestFailover']
            test_failover.destination_auto_instance.hvobj.VMs = cloned_vm_names
            test_failover.cloned_vms_metadata = clone_vms.get(source_vm, list())
            test_failover.cloned_vms = [test_failover.destination_auto_instance.hvobj.VMs[clone] for clone in cloned_vm_names]

    def update_testfailovervm_details(self, testfailover_vm):
        """Updates the continuous replication testfailover VM names"""
        for source_vm in self.vm_list:
            if self.is_continuous:
                self._vm_pairs[source_vm]['TestFailover'].destination_auto_instance.hvobj.VMs = [testfailover_vm]
                self._vm_pairs[source_vm]['TestFailover'].set_testfailovervm = self._vm_pairs[source_vm]['TestFailover'].destination_auto_instance.hvobj.VMs[testfailover_vm]

    def pre_validation(self):
        """Validates the state before DR operation"""
        self.refresh()
        for source in self.vm_list:
            test_failover : TestFailoverPeriodic | TestFailoverContinuous = self.vm_pairs[source]['TestFailover']
            test_failover.pre_validate_sync_status()
            if self.is_continuous:
                test_failover.add_test_data(source=True)

    def post_validation(self, post_expiration=False):
        """Validates this DR operation"""
        self.refresh()
        for source in self.vm_list:
            test_failover : TestFailoverPeriodic | TestFailoverContinuous = self.vm_pairs[source]['TestFailover']

            if not post_expiration:
                if not self.is_continuous:
                    dr_job = list(set([self.get_job_ids(cloned_vm)
                                       for cloned_vm in test_failover.cloned_vms.keys()]))

                    [self.job_phase_validation(job_id) for job_id in dr_job]

                test_failover.validate_power_state()
                test_failover.validate_sync_status()
                test_failover.validate_failover_status()

                test_failover.refresh_vm(source=True)

                test_failover.validate_hardware()
                test_failover.validate_advanced(skip_storage_check=True)
                if self.is_continuous:
                    test_failover.validate_test_data(source=False)

            # TODO : Validate resource deletion after cleanup
            test_failover.validate_expiration(post_expiration=post_expiration)
