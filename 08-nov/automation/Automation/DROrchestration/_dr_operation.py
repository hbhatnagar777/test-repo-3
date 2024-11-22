# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Abstraction file for helping testcases validate DR operation before and after
auto_instance_factory(instance)

DROperation(Abstract):
    Class Variables:
        SourcePhases
        DestinationPhases
        AuxApplicableJobTypes
    Methods:
        __init__(commcell_object, replication_group, vm_list, failover_group)
        power_on_vms(source=True)
        power_off_vms(source=True)
        _set_vm_list(vm_list)
        pre_validation(**kwargs)
        post_validation(**kwargs)
        refresh()
        job_phase_validation(job_id)
    Property:
        is_failover_group
        is_continuous
        group
        restore_options
        source_auto_instance
        destination_auto_instance
        auto_subclient
        recovery_target
        csdb
        vm_list
        vm_pairs
        job_type
"""
from abc import ABCMeta, abstractmethod

from cvpysdk.drorchestration.drjob import DRJob

from AutomationUtils.database_helper import get_csdb
from AutomationUtils.logger import get_log
from VirtualServer.VSAUtils.VirtualServerHelper import AutoVSACommcell, AutoVSAVSClient, AutoVSAVSInstance, \
    AutoVSABackupset, AutoVSASubclient
from VirtualServer.VSAUtils.VMHelper import HypervisorVM


def auto_instance_factory(instance):
    """Creates the auto instance on the basis of the inputs provided"""
    agent = instance._agent_object
    client = agent._client_object
    auto_commcell = AutoVSACommcell(instance._commcell_object, get_csdb())
    auto_client = AutoVSAVSClient(auto_commcell, client)
    return AutoVSAVSInstance(auto_client, agent, instance, tcinputs={})


class DROperation(metaclass=ABCMeta):
    """This class provides abstract methods for all DR operation children classes"""
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
        "hyper-v_vmware": set(),
    }

    ClonePhases = {
        "vmware": set(),
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
        "hyper-v_vmware": set(),
    }

    AuxApplicableJobTypes = [
        'Planned Failover',
        'Failback',
        'Reverse Replication'
    ]

    def __init__(self, commcell_object,
                 replication_group: str = '',
                 vm_list: list = None,
                 failover_group: str = ''):
        """ Initialise the class on the basis of whether it is a replication group or failover group
            Args:
                replication_group (str)         : The name of the replication group
                vm_list (list)                  : The list of all source VMs in replication group
                failover_group (str)            : The name of the failover group
            Note: Either failover_group/replication_group is compulsory
            Note: The list acts like a filter for the VMs in a group
        """
        self._commcell = commcell_object
        self._failover_group = None
        self._replication_group = None
        self._recovery_target = None
        self.log = get_log()
        if replication_group:
            self._replication_group = self._commcell.replication_groups.get(replication_group)
            self._recovery_target = self._commcell.recovery_targets.get(
                self._replication_group.recovery_target)
        elif failover_group:
            self._failover_group = None
            raise NotImplementedError("Not yet implemented for failover groups")
        else:
            raise AttributeError("Attribute 'failover_group' or 'replication_group' is required")

        self._source_auto_instance = None
        self._destination_auto_instance = None
        self._auto_subclient = None

        self._vm_pairs = {vm_name: None for vm_name in vm_list} if vm_list else {}

        self._csdb = get_csdb()

    @property
    def is_failover_group(self):
        """Returns: True if entity is made for Failover group. False, otherwise"""
        return self._failover_group is not None

    @property
    def is_continuous(self):
        """Returns: True if replication group is BLR. False, otherwise"""
        return not self.is_failover_group and self._replication_group.replication_type.name == 'VSA_CONTINUOUS'

    @property
    def group(self):
        """Returns the replication group or failover group cvpysdk object"""
        if self._replication_group:
            return self._replication_group
        return self._failover_group

    @property
    def restore_options(self):
        """Returns a dict of all VMs' restore options"""
        if self.is_failover_group:
            # TODO: Create different objects with different group restore options
            return {}
        group_restore_options = (self.group.restore_options.get('virtualServerRstOption', {})
                                 .get('diskLevelVMRestoreOption', {}))
        vm_list = group_restore_options.get('advancedRestoreOptions', [])
        return {restore_dict.get('name'): {**group_restore_options, 'advancedRestoreOptions': restore_dict}
                for restore_dict in vm_list}

    @property
    def source_auto_instance(self):
        """Creates a source auto instance with provided inputs and kwargs
            Args:
        """
        if not self._source_auto_instance:
            self._source_auto_instance = auto_instance_factory(self.group.source_instance)
        return self._source_auto_instance

    @property
    def destination_auto_instance(self):
        """Creates a destination auto instance with provided inputs and kwargs
            Args:
        """
        if not self._destination_auto_instance:
            self._destination_auto_instance = auto_instance_factory(self.group.destination_instance)
        return self._destination_auto_instance

    @property
    def auto_subclient(self):
        """Returns the auto subclient object for the replication group
        NOTE: ONLY FOR VSA PERIODIC REPLICATION GROUPS
        """
        if not self._auto_subclient:
            subclient = self.group.subclient
            auto_backupset = AutoVSABackupset(self.source_auto_instance, subclient._backupset_object)
            self._auto_subclient = AutoVSASubclient(auto_backupset, subclient)
        return self._auto_subclient

    @property
    def recovery_target(self):
        """Returns the associated recovery target"""
        return self._recovery_target

    @property
    def csdb(self):
        """Returns the csdb object"""
        return self._csdb

    def power_on_vms(self, source=True):
        """
        Powers on the source VMs before
            Args:
        """
        for source_vm in self.vm_list:
            pair_object = list(self.vm_pairs[source_vm].values())[0]
            pair_object.refresh_vm(source=source)

    def power_off_vms(self, source=True):
        """
        Powers off the source VMs before
            Args:
        """
        for source_vm in self.vm_list:
            pair_object = list(self.vm_pairs[source_vm].values())[0]
            vm = pair_object._source_vm if source else pair_object._destination_vm
            vm.power_off()

    def cleanup_testdata(self):
        """ Cleanup the testdata on the controller and source and dest VMs (won't throw any exceptions)"""
        try:
            for pair_objects in self.vm_pairs.values():
                for pair_object in pair_objects.values():
                    pair_object.cleanup_test_data(source=True)
        except Exception as exp:
            self.log.exception("Failed to cleanup testdata: %s", str(exp))

        try:
            for pair_objects in self.vm_pairs.values():
                for pair_object in pair_objects.values():
                    pair_object.cleanup_test_data(source=False)
        except Exception as exp:
            self.log.exception("Failed to cleanup testdata: %s", str(exp))

    def _set_vm_list(self, vm_list):
        """ Base function to implement property setter of vm_list"""
        self.group.refresh()
        for source_vm in vm_list:
            vm_pair = self.group.vm_pairs.get(source_vm)
            if not vm_pair:
                raise Exception(f"No pair with source VM name {source_vm} exists for group {self.group.group_name}")

            restore_options = self.restore_options.get(source_vm)

            self._vm_pairs[source_vm] = {
                'vm_pair_object': vm_pair,
                'source_auto_instance': self.source_auto_instance,
                'destination_auto_instance': self.destination_auto_instance,
                'vm_options': restore_options,
                'job_type': self.job_type,
                'recovery_target' : self.recovery_target,
                'csdb' : self.csdb
            }

    @property
    def vm_list(self):
        """Returns the list of VMs that are going to be used in this operation"""
        return list(self.vm_pairs.keys())

    @property
    def vm_pairs(self):
        """Returns the dictionary of {<source VM name>: <DR core objects>} for each VM pair"""
        # Make all DR core objects
        if self._vm_pairs:
            # VM filter applied
            vm_pairs_to_create = {source_vm for source_vm, vm_pair_obj in self._vm_pairs.items()
                                  if not vm_pair_obj}
        else:
            # VM pairs from monitor for group
            vm_pairs_to_create = set(self.group.live_sync_pairs) - {source_vm
                                                                    for source_vm, vm_pair_obj in self._vm_pairs.items()
                                                                    if vm_pair_obj}
        if vm_pairs_to_create:
            self._set_vm_list(list(vm_pairs_to_create))
        return self._vm_pairs

    @vm_pairs.setter
    def vm_pairs(self, vm_list):
        """Makes new pair objects for all VMs in vm_list"""
        vm_pairs_to_create = set(vm_list) - {source_vm
                                             for source_vm, vm_pair_obj in self._vm_pairs.items()
                                             if vm_pair_obj}
        if vm_pairs_to_create:
            self._set_vm_list(list(vm_pairs_to_create))
        # Remove all VM pairs that are outdated
        for source_vm in self._vm_pairs:
            if source_vm not in vm_list:
                del self._vm_pairs[source_vm]

    @vm_pairs.deleter
    def vm_pairs(self):
        """Resets all the objects in VM pairs"""
        self._vm_pairs = {}

    @property
    @abstractmethod
    def job_type(self):
        """ Returns the type of the job associated to the DR operation """
        return None

    @abstractmethod
    def pre_validation(self, **kwargs):
        """Performs utilities to help validate DR operation"""
        raise NotImplementedError("The pre_validation method is not yet implemented for class")

    @abstractmethod
    def post_validation(self, **kwargs):
        """Validates the DR operation by validating pre-validation additions"""
        raise NotImplementedError("The pre_validation method is not yet implemented for class")

    def refresh(self, hard_refresh=False):
        """Refresh the properties fetched from cvpysdk objects"""
        self.group.refresh()
        for source_vm, vm_pairs in self.vm_pairs.items():
            for dr_object in vm_pairs.values():
                if hard_refresh:
                    dr_object._vm_options = self.restore_options.get(source_vm)
                dr_object.refresh(hard_refresh=hard_refresh)

    def job_phase_validation(self, job_id: str):
        """Validates that the job phases are correct and in the right order"""
        # Skip job phase validations for continuous replication groups
        if self.is_continuous:
            return
        dr_job = DRJob(self._commcell, job_id)

        if dr_job.job_type != self.job_type:
            raise Exception(f"Supplied job ID [{job_id}] is of type [{dr_job.job_type}],"
                            f" expected [{self.job_type}]")

        job_phases = dr_job.get_phases()
        missing_vms = set(self.vm_list) - set(job_phases.keys())
        if missing_vms:
            raise Exception(f"VMs selected for DR operation are not all picked up by DR Job "
                            f"Missing VMs: {','.join(missing_vms)}")
        for source_vm in self.vm_list:
            vm_pair_dict = self.vm_pairs[source_vm]
            # Get any core object from VM pairs dict
            vm_pair = vm_pair_dict[list(vm_pair_dict.keys())[0]]
            blobs_retained = dr_job.blobs_retained()
            source_phases_key = self.group.source_instance.name.lower()
            if self.is_continuous:
                source_phases_key += "_continuous"
            if self.job_type in self.AuxApplicableJobTypes and self.group.copy_for_replication > 1:
                source_phases_key += '_aux'
            if vm_pair.is_dvdf_enabled:
                source_phases_key += "_dvdf"
            if vm_pair.is_warm_sync_enabled:
                source_phases_key += "_warmsync"
            if self.group.is_intelli_snap_enabled:
                source_phases_key += "_snap"

            destination_phases_key = self.group.destination_instance.name.lower()
            if self.is_continuous:
                destination_phases_key += "_continuous"
            if self.job_type in self.AuxApplicableJobTypes and self.group.copy_for_replication > 1:
                destination_phases_key += '_aux'
            if vm_pair.is_dvdf_enabled:
                destination_phases_key += "_dvdf"
            if blobs_retained:
                destination_phases_key += "_blobsretained"
            if vm_pair.is_warm_sync_enabled:
                destination_phases_key += "_warmsync"
            if self.group.is_intelli_snap_enabled:
                destination_phases_key += "_snap"
            expected_source_phases = self.SourcePhases.get(source_phases_key)
            expected_destination_phases = self.DestinationPhases.get(destination_phases_key)
            expected_clone_phases = self.ClonePhases.get(destination_phases_key)

            # hyper-v to vmware cross combination
            if source_phases_key in 'hyper-v' and destination_phases_key in 'vmware':
                cross_phases_key = f"hyper-v_{destination_phases_key}"
                expected_source_phases = self.SourcePhases.get(cross_phases_key)
                expected_destination_phases = self.DestinationPhases.get(cross_phases_key)
                expected_clone_phases = self.ClonePhases.get(cross_phases_key)

            pair_phases = job_phases[source_vm]
            source_phases = set()
            destination_phases = set()
            clone_phases = set()
            for phase in pair_phases:
                if phase['machine_name'] == vm_pair._source_vm.vm_name:
                    source_phases.add(phase['phase_name'].name)
                elif phase['machine_name'] == vm_pair._destination_vm.vm_name:
                    destination_phases.add(phase['phase_name'].name)
                elif phase['machine_name'] in vm_pair.cloned_vms.keys():
                    clone_phases.add(phase['phase_name'].name)
                else:
                    raise Exception(f"Unknown VM [{phase['machine_name']}] found for VM pair in DR job")

            if expected_source_phases and source_phases != expected_source_phases:
                raise Exception(f"Expected source phases does not match source phases "
                                f"Observed: {source_phases} and expected: {expected_source_phases}")

            if expected_destination_phases and destination_phases != expected_destination_phases:
                raise Exception(f"Expected destination phases does not match destination phases "
                                f"Observed: {destination_phases} and expected: {expected_destination_phases}")

            if expected_clone_phases and clone_phases != expected_clone_phases:
                raise Exception(f"Expected destination phases does not match destination phases "
                                f"Observed: {clone_phases} and expected: {expected_clone_phases}")

        self.log.info(f"Job phases validated for job ID - {job_id}")
