# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing operations relating to live sync

classes defined:

    Base class:

        LiveSyncUtils                   -   Act as base class for all Live Sync operations

    Methods:

        validate_live_sync()            -   Validate Live Sync

        get_recent_replication_job()    -   Get latest replication job corresponding to the Live Sync Schedule

        cleanup_live_sync()             -   Delete replicated VM and Live Sync Schedule

        monitor_job_for_completion()    -   Monitors the job completion

        power_off_source_vms()          -   powers of source vms

        validate_test_data()            - validates test data for DR operations

        validate_sync_status()          - validates sync and failover status for DR operations

        add_test_data()                 - Adds test data for vms

        power_off_vms()                - powers off the vms

        cleanup_test_data()            - cleans up the test data

        validate_last_synced_job()      - validate latest synced job is the latest backup job on vmgroups

        validate_replication_job_size() - validate replicated size is equal to backup size

        validate_dvwf()                 - validate vm is not deployed in case deploy on failover is selected

"""
import os
from time import sleep
from enum import Enum
import random
from AutomationUtils import logger
from Server.Scheduler.schedulerhelper import SchedulerHelper
from VirtualServer.VSAUtils import VirtualServerUtils
from VirtualServer.VSAUtils.VirtualServerHelper import AutoVSAVSClient
from VirtualServer.VSAUtils.VirtualServerHelper import AutoVSAVSInstance
from VirtualServer.VSAUtils import OptionsHelper
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type


class LiveSyncUtils:
    """

    Base Class for performing Live Sync related functions.
    """

    class OperationType(Enum):
        """Enum Class for replication operation Type"""
        SYNC = 'Live Sync'
        FAIL_BACK = 'Failback'
        UNDO_FAIL_OVER = 'Undo Failover'
        PLANNED_FAIL_OVER = 'Planned Failover'
        UNPLANNED_FAIL_OVER = 'Unplanned Failover'

    def __init__(self, auto_subclient, schedule_name):
        """
        Initialize common variables for LiveSyncUtils

        Args:

            auto_subclient          -       (AutoVSASubclient)  Auto VSA subclient

            schedule_name:          -       (str)   schedule name of live sync
        """
        self.log = logger.get_log()
        self.schedule_name = schedule_name
        self._auto_subclient = auto_subclient
        auto_subclient.subclient.live_sync.refresh()
        self._live_sync_pair = None
        self.live_sync_pair
        self._vm_pairs = self._live_sync_pair.vm_pairs
        self._vm_pair = None
        self._source_vms = None
        self._destination_vms = None
        self._destination_client = None
        self._agent = None
        self._instance = None
        self._dest_auto_client = None
        self._dest_auto_vsa_instance = None
        self.dest_region = None
        self._schedule = None
        self.source_hvobj = auto_subclient.hvobj
        self._dest_hvobj = None
        self.validation_options = {}

    @property
    def vm_pair(self):
        """

        First vm pair from vm_pairs

        Returns:
            (LiveSyncVMPair) object for vm pair

        """
        if not self._vm_pair:
            self._auto_subclient.subclient.live_sync.refresh()
            self._vm_pair = self._live_sync_pair.get(next(iter(self._vm_pairs)))
        return self._vm_pair

    @property
    def schedule(self):
        """Returns schedule objects"""
        if not self._schedule:
            try:
                self._schedule = self._auto_subclient.auto_vsaclient.vsa_client.schedules.get(self.schedule_name)
            except Exception as err:
                if '_ReplicationPlan__ReplicationGroup' not in self.schedule_name:
                    self._schedule = self._auto_subclient.auto_vsaclient. \
                        vsa_client.schedules.get(self.schedule_name + '_ReplicationPlan__ReplicationGroup')
                else:
                    raise err
        return self._schedule

    @property
    def live_sync_pair(self):
        """

        Get Live Sync Pair

        Returns:
            live_sync_pair  -   (LiveSyncPair) Object for Live Sync Pair

        """
        if not self._live_sync_pair:
            try:
                self._live_sync_pair = self._auto_subclient.subclient.live_sync.get(self.schedule_name)
            except Exception as err:
                if '_ReplicationPlan__ReplicationGroup' in self.schedule_name:
                    self.log.info("Could not find live sync pair with name %s", self.schedule_name)
                    self.log.info("Looking for live sync pair with name %s",
                                  self.schedule_name.replace('_ReplicationPlan__ReplicationGroup', ""))
                    self._live_sync_pair = self._auto_subclient.subclient. \
                        live_sync.get(self.schedule_name.replace('_ReplicationPlan__ReplicationGroup', ""))
                else:
                    raise err
        return self._live_sync_pair

    @property
    def vm_pairs(self):
        """

        Get Live Sync VM pairs

        Returns:
            vm_pairs    -   (LiveSyncVMPairs) Object for Live Sync VM pairs

        """
        return self._vm_pairs

    @property
    def destination_client(self):
        """

        Get destination virtualization client for live sync

        Returns:
            destination_client   -   (Client)  Virtualization client object

        """
        if not self._destination_client:
            self._destination_client = self._auto_subclient.auto_commcell.commcell \
                .clients.get(self.vm_pair.destination_client)
        return self._destination_client

    @property
    def agent(self):
        """

        Get Agent object for Live Sync

        Returns:
            agent       -   (Agent) Agent Object

        """
        if not self._agent:
            self._agent = self.destination_client.agents.get('virtual server')
        return self._agent

    @property
    def instance(self):
        """

        Get Instance object for the Live sync Pair

        Returns:
            instance    -   (Instance) Instance Object

        """
        if not self._instance:
            self._instance = self.agent.instances.get(self.vm_pair.destination_instance)
        return self._instance

    @property
    def dest_auto_client(self):
        """

        Get destination auto client

        Returns:
            dest_auto_client    -   (AutoVSAVSClient) Destination Auto client

        """
        if not self._dest_auto_client:
            self._dest_auto_client = AutoVSAVSClient(self._auto_subclient.auto_commcell, self.destination_client)
        return self._dest_auto_client

    @property
    def dest_hvobj(self):
        """Returns detination HypervisorHelper object"""
        if not self._dest_hvobj:
            self._dest_hvobj = self.dest_auto_vsa_instance.hvobj
        return self._dest_hvobj

    @property
    def source_vm_content(self):
        """
        Gets the list of source VMs that are in the content of the live sync
        (returns all source VM names, whether synced or not)
        Returns:
            source_vms     -   (list) List of source VMs
        """
        return list(self._vm_pairs.keys())

    @property
    def source_vms(self):
        """

        Get list of source VMs in Live Sync

        Returns:
            source_vms     -   (list) List of source VMs

        """
        if not self._source_vms:
            self._source_vms = [self.live_sync_pair.get(vm_pair).source_vm for vm_pair in self._vm_pairs]
        return self._source_vms

    @property
    def source_vm_objects(self):
        """

        Get list of source VMs helper objects in Live Sync

        Returns:
            source_vm_objects     -   (list) List of source VMs helper objects

        """
        if not self._auto_subclient.hvobj.VMs:
            self._auto_subclient.hvobj.VMs = self.source_vms
        return self._auto_subclient.hvobj.VMs

    @property
    def destination_vms(self):
        """

        Get list of destination VMs in Live Sync

        Returns:
            destination_vms     -   (list) List of destination VMs

        """
        if not self._destination_vms:
            self._destination_vms = [self.live_sync_pair.get(vm_pair).destination_vm for vm_pair in self._vm_pairs]
        return self._destination_vms

    @property
    def destination_vm_objects(self):
        """

        Get list of destination VMs helper objects in Live Sync

        Returns:
            destination_vm_objects     -   (list) List of destination VMs helper objects

        """
        if not self.dest_auto_vsa_instance.hvobj.VMs:
            self.dest_auto_vsa_instance.hvobj.VMs = self.destination_vms
        return self.dest_auto_vsa_instance.hvobj.VMs

    @property
    def dest_auto_vsa_instance(self):
        """

        Destination Auto VSA instance

        Returns:
            dest_auto_vsa_instance  -   (AutoVSAVSInstance) Destination Auto VSA Instance

        """
        if not self._dest_auto_vsa_instance:
            self.log.info("Initializing destination AutoVSAVSInstance")
            self._dest_auto_vsa_instance = AutoVSAVSInstance(self.dest_auto_client, self.agent, self.instance,
                                                             region=self.dest_region)
        self._dest_hvobj = self._dest_auto_vsa_instance.hvobj

        return self._dest_auto_vsa_instance

    def monitor_job_for_completion(self, job):
        """
        Waits For the job to complete successfully

        Args:
           job (obj): job object to monitor



        Returns:
            job : Job Object

        Raises error : if job is not completed successfully

        """

        if not job.wait_for_completion():
            raise Exception(
                "Replication Job failed with error: " + job.delay_reason
            )

        if "one or more errors" in job.status.lower():
            self.log.error("Replication  job completed with one or more errors")
            raise Exception("Replication  job completed with one or more errors")

        self.log.info('Replication job: %s completed successfully', job.job_id)

        return job

    def get_recent_replication_job(self, backup_jobid=None, monitor_job=False):
        """
        Args:
            backup_jobid (int): will get the replication job id that ran after backup job

            monitor_job  (bool): monitors job for completion if set to True

        Returns latest replication job, for live sync schedule

        Returns:
            replication_job (Job) : Job Object for latest replication job

        """
        self._auto_subclient.auto_vsaclient.vsa_client.schedules.refresh()
        schedule_helper = SchedulerHelper(self.schedule, self._auto_subclient.auto_commcell.commcell)
        if not backup_jobid:
            sleep(180)
            replication_job = schedule_helper.get_jobid_from_taskid()
        else:
            for index in range(30):  # replication thread is triggered once in 15 minutes
                # Get latest replication job from schedule helper
                temp = schedule_helper.get_jobid_from_taskid()
                if temp and int(temp.job_id) > int(backup_jobid):
                    replication_job = temp
                    break
                if index < 30:
                    self.log.info(
                        f"New Replication job not yet triggered after backup job {backup_jobid} "
                        f"recheck after 30 sec"
                    )
                    sleep(30)
            else:
                raise Exception('New Replication job not triggered after backup job {backup_jobid}')
        if monitor_job:
            return self.monitor_job_for_completion(replication_job)
        return replication_job

    def validate_live_sync(self, replication_run=True, check_replication_size=True, schedule=None, **kwargs):
        """To validate VSA live sync

        Args:

            replication_run (bool)          -       Set to True to check if replication job is triggered
            for the backup,else False, default: True

            check_replication_size (bool)   -       Set to False if incremental job is coverted to full replication

             schedule(object) -- schedule object for replication schedule to be validated

             kwargs(dict)    -- addition options
                                {'skip_test_data': True,
                                 'sourece_vms' : ['vm1','vm2']
                                 }

        Raises:
            Exception

                - If validation fails

        """
        source_vms = kwargs.get('source_vms', self.source_vms)
        for vm_pair in self.vm_pairs:
            if vm_pair not in source_vms:
                continue
            self.log.info('validating VM pair: "%s"', vm_pair)

            source_vm = self._auto_subclient.hvobj.VMs[vm_pair]
            source_vm.update_vm_info('All', os_info=True, force_update=True)
            self.log.info("Vm Pair Props")
            self._vm_pair = self.vm_pair
            vm_pair_obj = self.live_sync_pair.get(vm_pair)
            # To validate sync status
            assert vm_pair_obj.status == 'IN_SYNC', \
                f'VM pair : "{vm_pair}" \n Status: "{vm_pair_obj.status} \n Validation failed"'
            self.log.info('Sync status validation successful')
            if self._vm_pair._properties["VMReplInfoProperties"]:
                for vm_property in self._vm_pair._properties["VMReplInfoProperties"]:
                    if vm_property["propertyId"] == 2207:
                        self.dest_region = vm_property["propertyValue"]
                        self.dest_region = self.dest_region[:-1]
                        break
            replication_job = self._auto_subclient.auto_commcell.commcell.job_controller.get(
                vm_pair_obj.latest_replication_job)
            if replication_run:
                # To validate if replication job completed successfully
                self.validate_last_synced_job(vm_pair)
                backup_job = self._auto_subclient.auto_commcell.commcell.job_controller.get(
                    self._auto_subclient.backup_job.job_id)
                if backup_job.backup_level == 'Incremental' and check_replication_size:
                    self.validate_replication_job_size(backup_job, vm_pair)
            else:
                # To validate if replication job never started
                assert str(vm_pair_obj.last_synced_backup_job) != str(self._auto_subclient.backup_job.job_id), \
                    f"Replication Job started for Synthetic full, failing case"
                self.log.info('Replication run not started for Synthetic, validation successful')

            if not self.validate_dvwf(vm_pair):
                dest_vm_name = self.live_sync_pair.get(vm_pair).destination_vm
                self.dest_auto_vsa_instance.hvobj.VMs = dest_vm_name
                dest_vm = self.dest_auto_vsa_instance.hvobj.VMs[dest_vm_name]

                dest_vm.power_on()
                self.log.info('Successfully powered on VM: "%s"', dest_vm_name)
                self.boot_validation(dest_vm)

                _livesyncsource = self._auto_subclient.LiveSyncVmValidation(source_vm, schedule, replication_job)
                _livesyncdest = self._auto_subclient.LiveSyncVmValidation(dest_vm, schedule, replication_job)

                # hypervisor specific validation
                assert _livesyncsource == _livesyncdest, "Error while validation"

                # To validate test data between source and destination
                skip_test_data = kwargs.get('skip_test_data_validation', False)
                if replication_run and not skip_test_data:
                    for label, drive in dest_vm.drive_list.items():
                        dest_path = source_vm.machine.join_path(
                            drive, self._auto_subclient.backup_folder_name, "TestData", self._auto_subclient.timestamp)
                        self._auto_subclient.fs_testdata_validation(dest_vm.machine, dest_path)
                    self.log.info('Testdata validation successful')

                dest_vm.power_off()
                self.log.info('Successfully powered off VM: "%s"', dest_vm_name)

            self.log.info('Validation successful for VM pair: "%s"', vm_pair)

    def cleanup_live_sync(self, power_off_only=False, delete_schedule=True):
        """

        To clean up live sync operations

        Args:
            power_off_only  (bool): Set it True to power destination vm without deleting
                                    vm and schedule

            delete_schedule (bool): delete the schedule when set to True and power_off_only is False
        Raises:
            Exception

                - If cleanup operation fails

        """

        for vm_pair in self.vm_pairs:
            dest_vm_name = self.live_sync_pair.get(vm_pair).destination_vm
            # Checking Existence of destination VM before deleting, in case the replication was killed
            if self.dest_auto_vsa_instance.hvobj.check_vms_exist([dest_vm_name]):
                self.dest_auto_vsa_instance.hvobj.VMs = dest_vm_name
                dest_vm = self.dest_auto_vsa_instance.hvobj.VMs[dest_vm_name]
                dest_vm.power_off()
                if not power_off_only:
                    # To delete the replicated VM
                    output = dest_vm.delete_vm()
                    if output:
                        self.log.info('Successfully deleted the replicated VM : "%s"', dest_vm_name)
                    else:
                        raise Exception(f'Failed to delete the VM {dest_vm_name} please check the logs')
        if not power_off_only and delete_schedule:
            # To delete the created live sync configuration
            self._auto_subclient.subclient._client_object.schedules.delete(self.schedule_name)
            self.log.info('Successfully deleted the Live sync configuration schedule %s', self.schedule_name)

            self.log.info('Live sync cleanup operation is successful')

    def boot_validation(self, vm_obj):
        """Performs Boot validations on the vm

          Args:
                vm_obj  (object): vmhelper  object for the vm to validated

          Raises error : if Boot validation fails
        """
        self.log.info("Performing boot validation on %s", vm_obj.vm_name)
        vm_obj.power_on()
        wait = 10
        while wait:
            try:
                vm_obj.update_vm_info('All', os_info=True, force_update=True)
            except Exception as exp:
                self.log.info(exp)

            if vm_obj.ip and VirtualServerUtils.validate_ip(vm_obj.ip):
                self.log.info("IP Generated")
                break
            wait -= 1
            self.log.info('Waiting for 60 seconds for the IP to be generated')
            sleep(60)
        else:
            self.log.error('Valid IP not generated within 10 minutes')

            raise Exception(f'Valid IP for VM: {vm_obj.vm_name} not generated within 5 minutes')

    def add_test_data(self, hv_obj, vm_list, sub_client_obj=None):
        """Adds test data to list of vms passed
         Args:

            hv_obj (object): Hypervisor object for the vms

            vm_list (list): list of vms

            sub_client_obj (object): AutoVSASubclient object
                                     default : None

        Raises:
            Exception

                - If test data copy is not successful

        """
        try:
            generate = False
            if not sub_client_obj:
                sub_client_obj = self._auto_subclient
            backup_options = OptionsHelper.BackupOptions(sub_client_obj)
            sub_client_obj.backup_folder_name = backup_options.backup_type
            if sub_client_obj.testdata_path:
                sub_client_obj.controller_machine.remove_directory(sub_client_obj.testdata_path)
            sub_client_obj.testdata_path = VirtualServerUtils.get_testdata_path(
                sub_client_obj.controller_machine)
            sub_client_obj.timestamp = os.path.basename(os.path.normpath(sub_client_obj.testdata_path))
            sub_client_obj.auto_vsaclient.timestamp = sub_client_obj.timestamp
            testdata_size = backup_options.advance_options.get("testdata_size", random.randint(40000, 60000))
            generate = sub_client_obj.controller_machine.generate_test_data(sub_client_obj.testdata_path, 3,
                                                                            5, testdata_size)
            if not generate:
                raise Exception(generate)
            for _vm in vm_list:
                if _vm not in hv_obj.VMs:
                    hv_obj.VMs = _vm
                self.boot_validation(hv_obj.VMs[_vm])
                self.log.info("VM selected is {0}".format(_vm))
                if len(hv_obj.VMs[_vm].disk_list) > 0:
                    for _drive in hv_obj.VMs[_vm].drive_list.values():
                        _testdata_path = hv_obj.VMs[_vm].machine.join_path(_drive,
                                                                           backup_options.backup_type)
                        self.log.info("Cleaning up {}".format(_testdata_path))
                        if hv_obj.VMs[_vm].machine.check_directory_exists(_testdata_path):
                            hv_obj.VMs[_vm].machine.remove_directory(_testdata_path)
                        self.log.info("Copying Test data to Drive {0}".format(_drive))
                        hv_obj.copy_test_data_to_each_volume(_vm, _drive, backup_options.backup_type,
                                                             sub_client_obj.testdata_path)
            self.log.info("Copy test data completed successfully")
        except Exception as err:
            self.log.error("Error while copying test data %s", err)
            if generate:
                sub_client_obj.controller_machine.remove_directory(sub_client_obj.testdata_path)
            raise err

    def validate_test_data(self, source_vm_list=None, op_type=None, extra_options=None):
        """Perform test data validation as per the operation type

           Args:
               source_vm_list (list): list of source vms for which has to be performed
                                    default(None) : All the vms in the replication group
                                                    is validated

               op_type  (Enum) : OperationType Enum
                            default(None): Performs validation for Sync

               extra_options (dict): Addition option

           Raises:
                Exception

                    - If validation fails


        """
        try:
            self.log.info("Performing test data validation")
            if not extra_options:
                extra_options = dict()
            if not source_vm_list:
                source_vm_list = self.vm_pairs
            for vm_pair in source_vm_list:
                self.log.info('Validating VM pair: "%s"', vm_pair)
                if vm_pair not in self.source_hvobj.VMs:
                    self.source_hvobj.VMs = vm_pair
                source_vm = self.source_hvobj.VMs[vm_pair]
                dest_vm_name = self.live_sync_pair.get(vm_pair).destination_vm
                if dest_vm_name not in self.dest_hvobj.VMs:
                    self.dest_hvobj.VMs = dest_vm_name
                dest_vm = self.dest_hvobj.VMs[dest_vm_name]
                test_data_folder = extra_options['folder'] if extra_options.get(
                    'folder') else self._auto_subclient.backup_folder_name
                self.boot_validation(source_vm)
                if not op_type or op_type in [self.OperationType.SYNC, self.OperationType.PLANNED_FAIL_OVER]:
                    self.log.info("Performing test data validation on destination %s", dest_vm_name)
                    self.boot_validation(dest_vm)
                    for each_drive in source_vm.drive_list:
                        dest_path = dest_vm.machine.join_path(source_vm.drive_list[each_drive],
                                                              test_data_folder, "TestData",
                                                              self._auto_subclient.timestamp)
                        self._auto_subclient.fs_testdata_validation(dest_vm.machine, dest_path)

                if op_type in [self.OperationType.UNPLANNED_FAIL_OVER, self.OperationType.UNDO_FAIL_OVER]:
                    self.log.info("Performing test data non existence check on VM %s", dest_vm_name)
                    self.boot_validation(dest_vm)
                    for each_drive in source_vm.drive_list:
                        dest_path = dest_vm.machine.join_path(source_vm.drive_list[each_drive],
                                                              self._auto_subclient.backup_folder_name,
                                                              "TestData", self._auto_subclient.timestamp)
                        if dest_vm.machine.check_directory_exists(dest_path):
                            self.log.error("Test data %s on destination exist after %s", dest_path, op_type.value)
                            raise Exception("Test data non existence check failed")
                        if op_type == self.OperationType.UNDO_FAIL_OVER:
                            if source_vm.machine.check_directory_exists(dest_path):
                                self.log.error("Test data %s on source exist after %s", dest_path, op_type.value)
                                raise Exception("Test data non existence check failed")
                    self.log.info("Test data non existence check passed!")
                if op_type == self.OperationType.FAIL_BACK:
                    self.log.info("Performing test data validation on source %s", vm_pair)
                    for each_drive in source_vm.drive_list:
                        src_path = source_vm.machine.join_path(source_vm.drive_list[each_drive],
                                                               test_data_folder, "TestData",
                                                               self._auto_subclient.timestamp)
                    self._auto_subclient.fs_testdata_validation(source_vm.machine, src_path)

        except Exception as err:
            self.log.error("Validation failed : %s", err)
            raise err

    def validate_sync_status(self, op_type=None, source_vm_list=None):
        """Validates the sync status and failover status

         Args:
               source_vm_list (list): list of source vms for which has to be performed
                                    default(None) : All the vms in the replication group
                                                    is validated

               op_type  (Enum) : OperationType Enum
                            default(None): Performs validation for Sync

                extra_options (dict): Addition option

        """
        self._auto_subclient.subclient.live_sync.refresh()
        if not source_vm_list:
            source_vm_list = self.vm_pairs
        for vm_pair in source_vm_list:
            self.log.info('Validating VM pair: "%s"', vm_pair)
            vm_pair_obj = self.live_sync_pair.get(vm_pair)
            if not op_type or op_type in [self.OperationType.FAIL_BACK, self.OperationType.SYNC,
                                          self.OperationType.UNDO_FAIL_OVER]:
                assert vm_pair_obj.status == 'IN_SYNC', \
                    f'VM pair : "{vm_pair}" \n Status: "{vm_pair_obj.status} \n Validation failed"'
                assert vm_pair_obj.failover_status in ['NONE', 'FAILBACK_COMPLETE'], \
                    f'VM pair : "{vm_pair}" \n Status: "{vm_pair_obj.status} \n Validation failed"'

            if op_type in [self.OperationType.PLANNED_FAIL_OVER, self.OperationType.UNPLANNED_FAIL_OVER]:
                assert vm_pair_obj.status == 'SYNC_DISABLED', \
                    f'VM pair : "{vm_pair}" \n Status: "{vm_pair_obj.status} \n Validation failed"'
            self.log.info("Sync status validation successful for VM pair: %s", vm_pair)

    def power_off_source_vms(self, vm_list=None):
        """ Powers off the source vms

        Args:
            vm_list (list): List of vms
                            default(None): All Source vms are powered off

        """
        if not vm_list:
            vm_list = self.source_vms
        for _vm in vm_list:
            if _vm not in self.source_hvobj.VMs:
                self.source_hvobj.VMs = _vm
            self.source_hvobj.VMs[_vm].power_off()

        self.log.info("Source VMs powered off successfully")

    def power_off_vms(self, source_vms=True, vm_list=None):
        """ Powers off the source vms

        Args:

            source_vms (bool):  Set to True if vms to be powered off are source
                                default(True)
            vm_list (list): List of source vms
                            default(None): All Source vms are powered off

        """
        if not vm_list:
            vm_list = self.source_vms
        for vm in vm_list:
            if source_vms:
                if vm not in self.source_hvobj.VMs:
                    self.source_hvobj.VMs = vm
                self.source_hvobj.VMs[vm].power_off()
            else:
                dest_vm = self.live_sync_pair.get(vm).destination_vm
                if self.dest_hvobj.check_vms_exist([dest_vm]):
                    if dest_vm not in self.dest_hvobj.VMs:
                        self.dest_hvobj.VMs = dest_vm
                    self.dest_hvobj.VMs[dest_vm].power_off()

        self.log.info("VMs {0} powered off successfully".format(vm_list))

    def cleanup_test_data(self, vm_list=None):
        """Cleans up test data added
        Args:
            vm_list (list): List source vms
                            default(None) : All vms is in group

        """
        try:
            if self._auto_subclient.testdata_path:
                self._auto_subclient.controller_machine.remove_directory(self._auto_subclient.testdata_path)
            if not vm_list:
                vm_list = self.source_vms

            for _vm in vm_list:
                if _vm not in self.source_hvobj.VMs:
                    self.source_hvobj.VMs = _vm
                self.boot_validation(self.source_hvobj.VMs[_vm])
                self.log.info("VM selected is %s", _vm)
                if len(self.source_hvobj.VMs[_vm].disk_list) > 0:
                    for _drive in self.source_hvobj.VMs[_vm].drive_list.values():
                        _testdata_path = self.source_hvobj.VMs[_vm].machine. \
                            join_path(_drive,
                                      self._auto_subclient.backup_folder_name)
                        self.log.info("Cleaning up %s", _testdata_path)
                        if self.source_hvobj.VMs[_vm].machine.check_directory_exists(_testdata_path):
                            self.source_hvobj.VMs[_vm].machine.remove_directory(_testdata_path)
        except Exception as err:
            self.log.warning("Test data clean up failed : %s ", err)

    def validate_last_synced_job(self, source_vms=None):
        """Validates the last synced job on vm pair
        Args:
            source_vms (str/list) : string/list of source vms to be validated
                                default(None) : All the vms in group will be validated

        """
        if not source_vms:
            source_vms = self.source_vms
        if isinstance(source_vms, str):
            source_vms = [source_vms]
        for source_vm in source_vms:
            self.log.info("Validating last sync job for vm pair : %s", source_vm)
            vm_pair_obj = self.live_sync_pair.get(source_vm)
            # To validate if replication job completed successfully
            if (self._auto_subclient.auto_commcell.check_v2_indexing(
                    self._auto_subclient.auto_vsaclient.vsa_client.client_name)):
                self.log.info(f"Last synced Backup Job : {vm_pair_obj.last_synced_backup_job}")
                child_jobs = self._auto_subclient.auto_commcell.get_child_jobs(
                    self._auto_subclient.backup_job.job_id)
                assert str(vm_pair_obj.last_synced_backup_job) in child_jobs, \
                    f"Replication job failed to sync latest backup job {self._auto_subclient.backup_job.job_id}"
                self.log.info('Backup job sync successful')

                assert self._auto_subclient.auto_commcell.get_backup_pending_jobs_to_replicate(
                    source_vm) == [''], f"Pending backup jobs to sync for VM: {source_vm}"
            else:
                self.log.info(f"Last synced Backup Job : {vm_pair_obj.last_synced_backup_job}")
                assert str(vm_pair_obj.last_synced_backup_job) == str(self._auto_subclient.backup_job.job_id), \
                    f"Replication job failed to sync latest backup job {self._auto_subclient.backup_job.job_id}"
                self.log.info('Backup job sync successful')

    def validate_replication_job_size(self, backup_job_obj, source_vms=None):
        """
        Validates the replication job size is less then backup job size

        Args:
            source_vms (str/list): source_vms to be validated
                                default(None) : All the vms in group will be validated

            backup_job_obj (object): Backup job obj against which validation is performed

        """
        try:
            if not source_vms:
                source_vms = self.source_vms
            if isinstance(source_vms, str):
                source_vms = [source_vms]
            vm_app_size = self._auto_subclient.get_vm_app_size_from_parent_job(backup_job_obj)
            for source_vm in source_vms:
                self.log.info("Validating replication size for VM Pair %s", source_vm)
                vm_pair_obj = self.live_sync_pair.get(source_vm)
                replication_job = self._auto_subclient.auto_commcell.commcell.job_controller.get(
                    vm_pair_obj.latest_replication_job)
                replication_job_size = None
                for vm_detail in replication_job.get_vm_list():
                    if vm_detail['vmName'] == source_vm:
                        replication_job_size = vm_detail['restoredSize']
                        break
                if replication_job_size is None:
                    raise Exception(
                        f'VM [{source_vm}] not found in replication job [{replication_job.job_id}]'
                    )
                if self._auto_subclient.auto_commcell.check_v2_indexing(
                        self._auto_subclient.auto_vsaclient.vsa_client.client_name):
                    self.log.info("Backup job size:{0} Replication "
                                  "Job size:{1}".format(vm_app_size[source_vm],
                                                        replication_job_size))
                    assert replication_job_size < (vm_app_size[source_vm] + 104857600), \
                        "Replication job has replicated more data than expected for Incremental backup"
                    self.log.info('Data replicated for incremental job validation successful')
                    continue
                self.log.info("Backup job size:{0} Replication "
                              "Job size:{1}".format(backup_job_obj.size_of_application,
                                                    replication_job.size_of_application))
                assert replication_job.size_of_application < (backup_job_obj.size_of_application + 104857600), \
                    "Replication job has replicated more data than expected for Incremental backup"
                self.log.info('Data replicated for incremental job validation successful')
        except Exception as err:
            self.log.error("Validation failed %s", err)
            raise err

    def validate_dvwf(self, source_vms=None):
        """
        Validates if vm is not deployed in case dvwf is selected

        Args:
           source_vms (str/list): source_vms to be validated
                               default(None) : All the vms in group will be validated

        Returns: True if dvwf is selected and validation is successful
                False if not selected

        Exception

            - If validation fails

        """
        if not source_vms:
            source_vms = self.source_vms
        if isinstance(source_vms, str):
            source_vms = [source_vms]
        dest_vm_list = [self.live_sync_pair.get(_vm).destination_vm for _vm in source_vms]
        if self.dest_auto_vsa_instance.vsa_instance_name in [hypervisor_type.AZURE_V2.value.lower()]:
            # validating if the dest vm is present or not if dvdf enabled
            if self.schedule.virtualServerRstOptions['diskLevelVMRestoreOption'][
                                        'deployVmWhenFailover'] == 1:
                for _vm in dest_vm_list:
                    if self.dest_hvobj.check_vms_exist([_vm]):
                        raise Exception("Destination vm = {0} is present".format(_vm))
                self.log.info("Deploy on failover validation successful")
                return True
        return False
