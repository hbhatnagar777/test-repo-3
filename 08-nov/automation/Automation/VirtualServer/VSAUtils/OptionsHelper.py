# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
main file for selecting all the options for all backups and restore

Class:
BackupOptions - Class defined for setting all backup options
"""

import os
import re
from datetime import datetime

from cvpysdk.job import Job
from abc import ABC
from AutomationUtils import logger
from AutomationUtils import machine
from AutomationUtils.options_selector import OptionsSelector
from VirtualServer.VSAUtils.VirtualServerConstants import on_premise_hypervisor, hypervisor_type, HypervisorDisplayName
from . import VirtualServerHelper, VirtualServerUtils, VirtualServerConstants



class BackupOptions(object):
    """
    Main class which handles all backup level options
    """

    def __init__(self, auto_vsasubclient):
        """
        Initializes all basic properties of performing backup
        """
        self.auto_vsasubclient = auto_vsasubclient
        self._backup_type = "FULL"
        self._backup_method = "REGULAR"
        self.testdata_path = None
        self.copy_precedence = "0"
        self.failed_vm_only = False
        self.granular_recovery = self.auto_vsasubclient.subclient.metadata
        self.overwrite = False
        self.use_impersonation = False
        self.restore_backup_job_id = None
        self.run_incr_before_synth = False
        self.copy_precedence_applicable = False
        self.granular_recovery_for_backup_copy = False
        self.run_backup_copy_immediately = True
        self._app_aware = False
        self.incr_level = 'BEFORE_SYNTH'
        self._advance_options = {}
        self.cleanup_testdata_before_backup = True
        self.backup_job = None
        self.modify_data = False
        self.delete_data = False
        self.set_disk_props = False
        self.arch_file_id_used = {}
        self._power_off_unused_vms = None
        self._validation = True
        self._validation_skip_all = True
        self._snapshot_rg = None
        self.run_pre_backup_config_checks = auto_vsasubclient.config.Virtualization.run_vm_config_check \
            if hasattr(auto_vsasubclient.config.Virtualization, "run_vm_config_check") else True
        self.pre_backup_config_checks = VirtualServerConstants. \
            get_pre_backup_validation_checks(auto_vsasubclient.auto_vsainstance.vsa_instance_name)
        self.vm_setting_options = {}
        self.vm_disk_filter_options = {}

    @property
    def validation_skip_all(self):
        """
        Returns if all the validation needs to be skipped
        """
        return self._validation_skip_all

    @validation_skip_all.setter
    def validation_skip_all(self, value):
        """
        Assigning if validation needs to be done
        Args:
                value       (bool):  True if all validations and data copy needs to be skipped
                                        False if copy of data and all restores are run
        """
        self._validation_skip_all = value

    @property
    def validation(self):
        """
        Returns if validation has to be performed
        """
        return self._validation

    @validation.setter
    def validation(self, value):
        """
        Assigning if validation needs to be done
        Args:
                value       (bool):   True if validation needs to be done
                                        False if validation need not be done
        """
        self._validation = value

    @property
    def power_off_unused_vms(self):
        """
        Gets if the unusd vms are will be powered off or not
        """
        if type(self._power_off_unused_vms) != bool:
            self._power_off_unused_vm = not on_premise_hypervisor(
                self.auto_vsasubclient.auto_vsainstance.vsa_instance_name)
        return self._power_off_unused_vms

    @power_off_unused_vms.setter
    def power_off_unused_vms(self, value=False):
        """
        sets if the unused vms are will be powered off or not

        Args:
                value    (bool)   -  sets if the unused vms are will be powered off or not
        """
        self._power_off_unused_vms = value

    @property
    def data_set(self):
        """
        sets the path where the data set needs to be created
        It is read only attribute
        """
        return self.testdata_path

    @data_set.setter
    def data_set(self, path):
        """
        sets the path where the data set needs to be created

        args:
                path    (str)   - path where data needs to be created
        """
        self.testdata_path = path
        self.backup_folder_name = self.testdata_path.split("\\")[-1]

    @property
    def backup_type(self):
        """
        Type of backup to be performed
        It is read only attribute
        """

        return self._backup_type

    @backup_type.setter
    def backup_type(self, option):
        """
        Type of backup to be performed

        Args:
            option  (str)   -- Type of backup to be performed

                Possible values : FULL, INCREMENTAL, DIFFERENTIAL, SYNTHETIC_FULL

        """
        self._backup_type = option

    @property
    def backup_method(self):
        """
        Backup Method like app or crash consistent
        It is read only attribute
        """
        return self._backup_method

    @backup_method.setter
    def backup_method(self, option):
        """
        Backup Method like app or crash consistent

        Args:
                option  - App consistent or Crash consistent
        """
        self._backup_method = option

    @property
    def backup_failed_vm(self):
        """
        Backup the VM failed in Full Backup
        It is read only attribute
        """
        return self.failed_vm_only

    @backup_failed_vm.setter
    def backup_failed_vm(self, value):
        """
        Backup the VM failed in Full Backup

        Args:
                value (bool)     True or False based on needs to be set ot not
        """
        self.failed_vm_only = value

    @property
    def run_incremental_backup(self):
        """
        Run Incremental bakcup before synthic full
        It is read only attribute
        """
        return self.run_incr_before_synth

    @run_incremental_backup.setter
    def run_incremental_backup(self, value):
        """
        Run Incremental backup before synthetic full
        Args:
            value   (bool)  - based on Incremental need to be run or not
        """
        self.run_incr_before_synth = False
        self.incr_level = value

    @property
    def collect_metadata(self):
        """
        Enable granular recovery for backup
        It is read only attribute
        """
        return self.granular_recovery

    @collect_metadata.setter
    def collect_metadata(self, value):
        """
        Enable granular recovery for backup
        Args:
                value   (bool) - based on value need to be set or not

        """
        self.granular_recovery = value
        self.auto_vsasubclient.subclient.metadata = self.granular_recovery

    @property
    def collect_metadata_for_bkpcopy(self):
        """
        Enable granular recovery for backup copy
        It is read only attribute
        """
        return self.granular_recovery_for_backup_copy

    @collect_metadata_for_bkpcopy.setter
    def collect_metadata_for_bkpcopy(self, value):
        """
        Enable granular recovery for backup copy
        Args:
            value   (bool) - based on value need to be set or not

        """
        self.granular_recovery_for_backup_copy = value

    @property
    def run_backupcopy_immediately(self):
        """
        Run backup copy immediately after snap backup
        It is read only attribute
        """
        return self.run_backup_copy_immediately

    @run_backupcopy_immediately.setter
    def run_backupcopy_immediately(self, value):
        """
        Run backup copy immediately after snap backup
        Args:
            value   (bool) - based on value need to be set or not

        """
        self.run_backup_copy_immediately = value

    @property
    def Application_aware(self):
        """
        Run backup copy immediately after snap backup
        It is read only attribute
        """
        return self._app_aware

    @Application_aware.setter
    def Application_aware(self, value):
        """
        Run backup copy immediately after snap backup
        Args:
            value   (bool) - based on value need to be set or not

        """
        self._app_aware = value

    @property
    def advance_options(self):
        """
        Setting up Advanced property for the file level backup
        Returns:
            _advance_options (str):     Advanced property fot backup
        """
        return self._advance_options

    @advance_options.setter
    def advance_options(self, value):
        """

        Args:
            value (dict) :       Dictionary for advanced option

        Returns:

        """
        self._advance_options = value

    @property
    def snapshot_rg(self):
        """
        Returns the RG for taking snapshot in

        Returns:
            snapshot_rg     (str):  value of snapshot RG

        """
        return self._snapshot_rg

    @snapshot_rg.setter
    def snapshot_rg(self, value=False):
        """
        Sets the RG for taking snapshot in

        Args:
            value   (str):  value for snapshot RG
        """
        self._snapshot_rg = value


class RestoreOptions(object):
    """
        Base class which handles all the option restores

        set_destination_client()    - set the co-coordinator as the default destination client
                                                                            if not specified by user

        set_restore_path()            - set the path with maximum space as  default restore path  for
                                                                file level restore if not set as user

        """

    def __init__(self, subclient):
        self.auto_subclient = subclient
        self.log = logger.get_log()
        self._copy_precedence = 0
        self._overwrite = False
        self.use_impersonation = False
        self.copy_precedence_applicable = False
        self._start_time = 0
        self._end_time = 0
        self._dest_client_name = None
        self.is_ma_specified = False
        self._browse_from_snap = False
        self._browse_from_backupcopy = False
        self._browse_from_auxcopy = False
        self._dest_host_name = None
        self._destination_client = None
        self.client_machine = None
        self.impersonate_user_name = None
        self._restore_path = None
        self.browse_ma_host_name = None
        self._snap_proxy = None
        self._browse_ma_client_name, self._browse_ma_id = self.auto_subclient.browse_ma
        self.restore_job = None
        self._testcase_no_in_path = True
        self._is_part_of_thread = False
        self.validate_restore_workload = False
        self._automatic_proxy = False
        self.backup_folder_name = None
        self.timestamp = None
        self.testdata_path = None
        self.snap_restore = False
        self.validate_browse_ma_and_cp = False
        self.restore_proxy = None
        self.restore_job_id = None
        self.restore_client = None

    @property
    def data_set(self):
        """
        sets the path where the data set needs to be created
        It is read only attribute
        """
        return self.testdata_path

    @data_set.setter
    def data_set(self, path):
        """
        sets the path where the data set needs to be created

        args:
                path    (str)   - path where test data is located
        """
        self.testdata_path = path
        self.timestamp = os.path.basename(os.path.normpath(path))

    @property
    def testcase_no_path(self):
        """
        Testcase number appended in testpath
        It is read only attribute
        """
        return self._testcase_no_in_path

    @testcase_no_path.setter
    def testcase_no_path(self, value=True):
        """
        Setting if testcase number in restore path
        Args:
            value (bool) - Setting if testcase number in restore path, True or False
        """

        self._testcase_no_in_path = value

    @property
    def is_part_of_thread(self):
        """
        If the restore part of thread based restore
        It is read only attribute
        """
        return self._is_part_of_thread

    @is_part_of_thread.setter
    def is_part_of_thread(self, value=True):
        """
        Setting if the restore is thread based restore or not
        Args:
            value (bool) - Setting if the restore is thread based restore, True or False
        """

        self._is_part_of_thread = value

    @property
    def destination_client(self):
        """
        Return destination client where disk are to be restored .
        It is read only attribute
        """
        return self._dest_client_name

    @destination_client.setter
    def destination_client(self, client_name):
        """
        set the particular client as destination client for disk restore

        Args:
        client_name     (str)   - client_name as configured in cs
        """
        self._destination_client = self.auto_subclient.auto_commcell.commcell.clients.get(client_name)
        self._dest_client_name = client_name
        self._dest_host_name = self._destination_client.client_hostname
        self.set_restore_path()

    @property
    def copy_precedence(self):
        """
        copy precedence from which disk restore needs to be performed
        It is read only attribute
        """
        return self._copy_precedence

    @copy_precedence.setter
    def copy_precedence(self, value=None):
        """
        set the copy precedence from which disk restore needs to be performed
        Args:
            value (int) - The copy precedence of the copy from which
                            disk restore needs to be performed eg: 1
        """

        self.copy_precedence_applicable = True
        self._copy_precedence = value

    @property
    def browse_from_snap(self):
        """
        The property returns true if browse happened from snap
        It is read only attribute
        """
        return self._browse_from_snap

    @browse_from_snap.setter
    def browse_from_snap(self, value):
        """
        Property needs to be set if browse needs to be done from snap copy
        Args:
            value   (bool) - True if it needs to browse from snap
        """
        self.copy_precedence_applicable = value
        self.copy_precedence = int(self.auto_subclient.auto_commcell.find_snap_copy_id(
            self.auto_subclient.storage_policy_id))
        self._browse_from_snap = value

    @property
    def browse_from_backup_copy(self):
        """
        The property returns true if browse happened from backup copy
        It is read only attribute
        """
        return self._browse_from_backupcopy

    @browse_from_backup_copy.setter
    def browse_from_backup_copy(self, value):
        """
        Property needs to be set if browse needs to be done from backup copy
        Args:
            value   (bool) - True if needs to browse from backup copy
        """
        self.copy_precedence_applicable = value
        self.copy_precedence = int(self.auto_subclient.auto_commcell.find_primary_copy_id(
            self.auto_subclient.storage_policy_id))
        self._browse_from_backupcopy = value

    @property
    def browse_from_aux_copy(self):
        """
        The property returns true if browse happened from auxiliary copy
        It is read only attribute
        """
        return self._browse_from_auxcopy

    @browse_from_aux_copy.setter
    def browse_from_aux_copy(self, value):
        """
        Property needs to be set if browse needs to be done from auxiliary copy
        Args:
            value   (bool) - True if needs to browse from auxiliary copy
        """
        self.copy_precedence_applicable = value
        self.copy_precedence = int(self.auto_subclient.auto_commcell.find_aux_copy_id(
            self.auto_subclient.storage_policy_id))

    @property
    def browse_from_restore_job(self):
        """
        Returns the job from which disk was restored
        it is read only attribute
        """
        return self._start_time, self._end_time

    @browse_from_restore_job.setter
    def browse_from_restore_job(self, job_id):
        """
        set the Job id from which the disk restore needs to be done
        Args:
            job_id (int)    - Backup job id from disk restore needs to be done
        """
        _job = Job(self.auto_subclient.auto_subclient.commcell, job_id)
        self._start_time = _job.start_time
        self._end_time = _job.end_time

    @property
    def browse_ma(self):
        """
        Returns the browse MA from which the disk restore is performed
        It is read only attribute
        """
        return self._browse_ma_client_name

    @browse_ma.setter
    def browse_ma(self, ma_name):
        """
        Set the browse MA from which the disk restore is performed
        Args:
            ma_name (str)   - MA Name from which disk restore needs to be performed
        """
        if not ma_name or not ma_name.strip():
            self.is_ma_specified = False
            self.log.info("Browse Ma is not specified. Setting it to default Ma")
            self._browse_ma_client_name, self._browse_ma_id = self.auto_subclient.browse_ma
            return
        else:
            self.is_ma_specified = True
            client = self.auto_subclient.auto_commcell.commcell.clients.get(ma_name)
            self._browse_ma_client_name = client.client_name
            self.browse_ma_host_name = client.client_hostname
            self._browse_ma_id = client.client_id

    @property
    def unconditional_overwrite(self):
        """
        returns if unconditional overwrite disk in place is set for disk restore
        It is read only attribute
        """
        return self._overwrite

    @unconditional_overwrite.setter
    def unconditional_overwrite(self, value):
        """
        set unconditional overwrite disk in place is set for disk restore
        Args:
            value (bool)    - True if it needs to overwrite disk in place
        """
        self._overwrite = value

    @property
    def impersonate_user(self):
        """
        returns the user if restored was triggered with some specific user
        It is read only attribute
        """
        return self.impersonate_user_name

    @impersonate_user.setter
    def impersonate_user(self, user_name):
        """
        set the user if restored was to be triggered with some specific user
        Args:
            user_name   (str)   - user with which the restore needs to be performed
        """
        self.impersonate_user_name = user_name
        self.use_impersonation = True

    @property
    def restore_path(self):
        """
        Returns the Restore path where disk is restored
        It is read only attribute
        """
        return self._restore_path

    @restore_path.setter
    def restore_path(self, value):
        """
        Set the restore path where the disk needs to be restored
        Args:
            value   (str) - Restore path where disk needs to be restored
                            default :C:\CVAutoamtion
        """

        self._restore_path = value

    @property
    def snap_proxy(self):
        """
        Returns value of snap proxy
        it is read only attribute
        """
        return self._snap_proxy

    @snap_proxy.setter
    def snap_proxy(self, value):
        """
        set the value of snap proxy in restores

        Args:
            value   (str) - value of snap proxy need to be set
        """
        self._snap_proxy = value

    def set_destination_client(self):
        """
        set the default destination client ifg not given by user and path to restore in that client

        Exception:
            if client si not part of CS
        """
        try:
            if self._dest_client_name is None:
                if bool(self.auto_subclient.subclient.subclient_proxy):
                    self._dest_client_name = self.auto_subclient.subclient.subclient_proxy[0]
                else:
                    self._dest_client_name = self.auto_subclient.auto_vsainstance.co_ordinator
                client = self.auto_subclient.auto_commcell.commcell.clients.get(
                    self._dest_client_name)
                self._dest_host_name = client.client_hostname
            self.set_restore_path()

        except Exception as err:
            self.log.exception("An error occurred in SetDestinationClient ")
            raise err

    def set_restore_path(self):
        """
        set the restore path as CVAutomation in the drive with maximum storage space

        Exception:
            if failed to get storage details
            if failed to create directory
        """
        try:
            _temp_storage_dict = {}
            self.client_machine = machine.Machine(self._dest_client_name,
                                                  self.auto_subclient.auto_commcell.commcell)
            if self.client_machine.get_registry_value(
                "MediaAgent", "sHyperScaleImageidentifier"):
                _dir_path = "//tmp//CVAutomation"
            else:
                storage_details = self.client_machine.get_storage_details()
                if self.client_machine.os_info.lower() in 'unix, linux':
                    _drive_regex = "^/dev/*"
                else:
                    _drive_regex = "^[a-zA-Z]$"

                for _drive, _size in storage_details.items():
                    if re.match(_drive_regex, _drive) and not (
                            self.client_machine.os_info.lower() in 'unix, linux' and 'cvblk_mounts' in _size[
                                'mountpoint']):
                        _temp_storage_dict[_drive] = _size["available"]

                _maximum_storage = max(_temp_storage_dict.values())
                results = list(filter(lambda x: x[1] == _maximum_storage, _temp_storage_dict.items()))

                if self.client_machine.os_info.lower() in 'unix, linux':
                    mountpath = storage_details[results[0][0]]['mountpoint']
                    _dir_path = self.client_machine.join_path(mountpath, "CVAutomation")
                else:
                    _dir_path = (results[0])[0] + ":\\CVAutomation"

            if not self.client_machine.check_directory_exists(_dir_path):
                self.client_machine.create_directory(_dir_path)

            self._restore_path = _dir_path

        except Exception as err:
            self.log.exception("An Error occurred in PopulateRestorePath ")
            raise err


class FileLevelRestoreOptions(RestoreOptions):
    """
    Main class which handles all the option of file level restore

    init:

    subclient - (obj)    - subclient object of the cs

    set_destination_client()    - set the co-ordinator as the default destination client
                                                                        if not specified by user


    """

    def __init__(self, subclient):
        super(FileLevelRestoreOptions, self).__init__(subclient)
        self._preserve_level = 4
        self.fs_acl = "ACL_DATA"
        self.granular_recovery = self.auto_subclient.subclient.metadata
        self.browse_ma_host_name = None
        self._fbr_ma = None
        self.skip_block_level_validation = True
        self.smbrestore = None
        self.set_destination_client()
        self._cleanup_time = 0

    @property
    def cleanup_time(self):
        """
        returns the cleanup time for block level browse
        """
        return self._cleanup_time

    @cleanup_time.setter
    def cleanup_time(self, value):
        """
        Sets the cleanup time for the block level cleanup.
        minimum is 10 minutes
        Args:
                value   (bool) - cleanup time

        """
        if value <= 10:
            self._cleanup_time = 10
        else:
            self._cleanup_time = value

    @property
    def metadata_collected(self):
        """
        Enable granular recovery for backup
        It is read only attribute
        """
        return self.granular_recovery

    @metadata_collected.setter
    def metadata_collected(self, value):
        """
        Enable granular recovery for backup
        Args:
                value   (bool) - based on value need to be set or not

        """
        self.granular_recovery = value
        self.auto_subclient.subclient.metadata = value

    @property
    def fbr_ma(self):
        """
        Enable granular recovery for backup
        It is read only attribute
        """
        return self._fbr_ma

    @fbr_ma.setter
    def fbr_ma(self, value):
        """
        Enable granular recovery for backup
        Args:
                value   (bool) - based on value need to be set or not

        """
        self._fbr_ma = value

    @property
    def preserve_level(self):
        """
        The property returns default preserve level for file level restores
        It is read only attribute
        """
        return self._preserve_level

    @preserve_level.setter
    def preserve_level(self, value):
        """
        Property needs to be set if restore has to be done with  different preserve level
        Args:
            value   (int) - represent preserve level need to be set
        """
        self._preserve_level = value

    @property
    def restore_acl(self):
        """
        Return whether acl permission is set while restore . It is read only attribute
        """
        return self.fs_acl

    @restore_acl.setter
    def restore_acl(self, value):
        """
        Args:
             value: set whether acl permission need to be restored
        """
        self.fs_acl = value


class DiskRestoreOptions(RestoreOptions):
    """
    Main file for disk restore options in Automation

    set_destination_client()    - set the co-ordinator as the default destination client
                                                                        if not specified by user


    """

    def __init__(self, subclient):
        """
        Initializes all basic properties of performing Disk restore

        Args:
            subclient - (obj)    - subclient object of the cs
        """
        super(DiskRestoreOptions, self).__init__(subclient)

        self._convert_disk_to = None
        self._destination_pseudo_client = None
        self.set_destination_client()
        self._disk_browse_ma = None

    @property
    def convert_disk_to(self):
        """
        returns the extension to which the disk was converted in disk restore if set
        It is read only attribute
        """
        return self._convert_disk_to

    @convert_disk_to.setter
    def convert_disk_to(self, value):
        """
        set the extension to which the disk needs to be  converted in disk restore
        Args:
            value   (str)   - extension to which it needs to be converted
                                    eg:vmdk
        """
        self._convert_disk_to = value

    @property
    def disk_browse_ma(self):
        """
        returns the browse ma needed to use  in disk restore if set
        It is read only attribute
        """
        return self._disk_browse_ma

    @disk_browse_ma.setter
    def disk_browse_ma(self, value):
        """
        set the browse ma for disk restore
        Args:
            value   (str)   - media agent name
        """
        self._disk_browse_ma = value

    @property
    def destination_client(self):
        """
        Return destination client where disk are to be restored .
        It is read only attribute
        """
        return self._dest_client_name

    @destination_client.setter
    def destination_client(self, client_name):
        """
        set the particular client as destination client for disk restore

        Args:
        client_name     (str)   - Pseudo client_name as configured in cs
        """
        self._destination_pseudo_client = client_name[0]
        self._destination_client = self.auto_subclient.auto_commcell.commcell.clients.get(client_name[1])
        self._dest_client_name = self._destination_client.client_name
        self._dest_host_name = self._destination_client.client_hostname


class AttachDiskRestoreOptions(RestoreOptions):
    """
    Main file for attach disk restore options in Automation

    set_destination_client()    - set the co-ordinator as the default destination client
                                                                        if not specified by user


    """

    def __init__(self, subclient, testcase):
        """
        Initializes all basic properties of performing Atach Disk restore

        Args:
            subclient - (obj)    - subclient object of the cs

            inputs   - (object)   - testcase object
        """
        super(AttachDiskRestoreOptions, self).__init__(subclient)
        self.inputs = testcase.tcinputs
        self.testcase = testcase
        self.vcenter = {}
        self._destination_vcenter = None
        self._vcuser = None
        self._vcpass = None
        self._dest_client_name = None
        self._disk_browse_ma = None
        self.populate_attach_disk_restore_option()

    @property
    def disk_browse_ma(self):
        """
        returns the browse ma needed to use  in disk restore if set
        It is read only attribute
        """
        return self._disk_browse_ma

    @disk_browse_ma.setter
    def disk_browse_ma(self, value):
        """
        set the browse ma for disk restore
        Artgs:
            value   (str)   - media agent name
        """
        self._disk_browse_ma = value

    def populate_attach_disk_restore_option(self):
        """
        populate all the defaults for the attach disk restore

        Exception:
            if failed to set tags for attach disk restore

        """
        try:
            instance_name = self.auto_subclient.auto_vsainstance.vsa_instance_name

            def openstack():
                self.power_on_after_restore = True
                vm_list = self.auto_subclient.vm_list
                self.log.info("Populating require info for : Attach Volume Restore Options")
                self.destination_client = self.inputs.get(
                    "DestinationClient",
                    self.auto_subclient.auto_vsaclient.vsa_client_name)

                dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                    self.auto_subclient.auto_commcell, self._destination_client)
                destination_project_name = self.inputs.get("destination_project_name", None)
                Source_Security_Grp = self.inputs.get("Source_Security_Grp")
                DestinationZone = self.inputs.get("DestinationZone")
                self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(dest_auto_vsaclient,
                                                                                    self.testcase.agent,
                                                                                    self.testcase.instance)

                self.proxy_client = self.dest_auto_vsa_instance.co_ordinator

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj
                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        (self.auto_subclient.hvobj.VMs[each_vm]))
                self.log.info("Obtaining the Host, Cluster, esx, datacenter and datastore options: ")
                # setting server in the VSA Client
                if (("Host" not in self.inputs) and
                        ("Datastore" not in self.inputs)):

                    self.restoreObj = self.dest_client_hypervisor.compute_free_resources(vm_list[0],
                                                                                         project_name=destination_project_name,
                                                                                         securityGroups=Source_Security_Grp,
                                                                                         esxHost=DestinationZone)
                    self.host = self.restoreObj["esxServerName"]
                    self.datastore = self.restoreObj["Datastore"]
                    self.esxHost = self.restoreObj["esxHost"]
                    self.cluster = self.restoreObj["Cluster"]
                    self.datacenter = self.restoreObj["Datacenter"]
                else:
                    self.host = self.inputs["Host"]
                    self.datastore = self.inputs["Datastore"]

                self.dest_machine = machine.Machine(self.proxy_client,
                                                    self.auto_subclient.auto_commcell.commcell)

                self.vcenter['vcenter'] = self.auto_subclient.auto_vsainstance.vsa_instance.server_host_name[0]
                self.vcenter['password'] = VirtualServerUtils.encode_base64(
                    self.auto_subclient.auto_vsainstance.password).decode()
                self.vcenter['user'] = self.auto_subclient.auto_vsainstance.user_name

            def vmware():
                self.vcenter['vcenter'] = self.auto_subclient.auto_vsainstance.vsa_instance.server_host_name[0]
                self.vcenter['password'] = VirtualServerUtils.encode_base64(
                    self.auto_subclient.auto_vsainstance.password).decode()
                self.vcenter['user'] = self.auto_subclient.auto_vsainstance.user_name
                if self.auto_subclient.subclient.subclient_proxy:
                    self._dest_client_name = self.auto_subclient.subclient.subclient_proxy[0]
                else:
                    self._dest_client_name = self.auto_subclient.auto_vsainstance.vsa_co_ordinator

            def amazon():
                if self.auto_subclient.subclient.subclient_proxy:
                    self._dest_client_name = self.auto_subclient.subclient.subclient_proxy[0]
                else:
                    self._dest_client_name = self.auto_subclient.auto_vsainstance.vsa_co_ordinator

            hv_dict = {hypervisor_type.OPENSTACK.value.lower(): openstack,
                       hypervisor_type.VIRTUAL_CENTER.value.lower(): vmware,
                       hypervisor_type.AMAZON_AWS.value.lower(): amazon}

            (hv_dict[instance_name])()

        except Exception as err:
            self.log.exception("An error occurred in setting hypervisor tags in Attach disk restore")
            raise err


class FullVMRestoreOptions(RestoreOptions):
    """
    Main class for full restore options in Automation
    """

    def __init__(self, subclient, testcase, populate_restore_inputs=True):
        """
        Initialize all class variables for Full VM restore

        init:

        subclient - (obj)    - subclient object of the cs

        inputs   - (dict)   - entire input dictionary passed for automation

        populate_restore_inputs -   (bool)  - Populate the restore options
                                              default=True

        populate_hypervisor_restore_inputs()    - populate all the smart defaults
        """
        super(FullVMRestoreOptions, self).__init__(subclient)
        self.inputs = testcase.tcinputs
        self.testcase = testcase
        self.perform_disk_validation = False
        self.advanced_restore_options = {}
        self.power_on = False
        self.dest_client_hypervisor = None
        self.in_place = False
        self.is_patch_restore = False
        self.add_to_failover = False
        self._destination_client = None
        self.network = "New Network Interface"
        self.destination_path = ""
        self.Resource_Group = None
        self.Storage_account = None
        self.vm_size = None
        self.createPublicIP = None
        self.zone = None
        self.dest_auto_vsa_instance = None
        self._source_ip = None
        self._destination_ip = None
        self._restore_backup_job = None
        self.source_vm_details = dict()
        self._disk_option = 'Original'
        self.restoreAsManagedVM = True
        self.data_center = None
        self.security_groups = None
        self.region = None
        self.volume_type = None
        self.iops = None
        self.throughput = None
        self._dest_computer_name = None
        self._av_zone = 'Auto'
        self.validate_vm_storage_policy = False
        self._vm_storage_policy = None
        if populate_restore_inputs:
            self.populate_hypervisor_restore_inputs()
        self._source_client_hypervisor = None
        self.is_destination_host_cluster = False
        self.is_destination_ds_cluster = False
        self.restore_validation_options = {}
        self._do_restore_validation_options = {}
        self._revert = False
        # Options for Live Recovery Restore
        self.volume_level_restore = None
        self.redirectWritesToDatastore = ""
        self.delayMigrationMinutes = 0
        # Options for Amazon Validation.
        self.ec2_instance_type = None
        self.encryptionKey = "Original"
        self.encryptionKeyArn = None
        self.network_interface = "New Network Interface"
        self.instance_boot_mode = None
        self.disk_ds_options = None
        self.host = None
        self.datastore = None
        self.vm_restore_prefix = self.auto_subclient.vm_restore_prefix
        self.vm_tags = None
        self.aws_vpc_recovery_validation = False
        # vcloud options
        self.owner = None
        self.destination_network = None
        self.standalone = False

    @property
    def restore_backup_job(self):
        return self._restore_backup_job

    @restore_backup_job.setter
    def restore_backup_job(self, job_id):
        self._restore_backup_job = Job(self.auto_subclient.auto_commcell.commcell, job_id)
        self.advanced_restore_options['from_time'] = str(datetime.strftime(datetime.strptime(
            self._restore_backup_job.start_time, "%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S"))
        self.advanced_restore_options['to_time'] = str(datetime.strftime(datetime.strptime(
            self._restore_backup_job.end_time, "%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S"))

    @property
    def power_on_after_restore(self):
        """
        Returns value of Power VM set in Full VM restore
        it is read only attribute
        """
        return self.power_on

    @power_on_after_restore.setter
    def power_on_after_restore(self, value):
        """
        set the value of power on option in Full VM restore

        Args:
            value   (bool)  - True if poweron option need to be set
        """
        self.power_on = value

    @property
    def source_client_hypervisor(self):
        """
        Returns HV Object of source
        it is read only attribute
        """
        return self._source_client_hypervisor

    @source_client_hypervisor.setter
    def source_client_hypervisor(self, value):
        """
        set the object of source Hypervisor

        Args:
            value   (object)  - the source hv object to be set
        """
        self._source_client_hypervisor = value

    @property
    def in_place_overwrite(self):
        """
        Returns value of Overwrite set in Full VM restore
        it is read only attribute
        """
        return self.in_place

    @in_place_overwrite.setter
    def in_place_overwrite(self, value):
        """
        set the value of overwrite option in Full VM restore

        Args:
            value   (bool)  - True if overwrite option need to be set
        """
        self.in_place = value
        self._overwrite = value

    @property
    def revert(self):
        """
        Returns value of revert set in Full VM restore
        """
        return self._revert

    @revert.setter
    def revert(self, value):
        """
        set the value of revert option in Full VM restore

        Args:
            value   (bool)  - True if revert option need to be set
        """
        self._revert = value

    @property
    def disk_option(self):
        """
        Returns value of Disk provision type set in Full VM restore
        it is read only attribute
        """
        return self._disk_option

    @disk_option.setter
    def disk_option(self, value):
        """
        set the value of Disk provision type in Full VM restore

        Args:
            value   (String)  - Disk provision type
        """
        self._disk_option = value

    @property
    def availability_zone(self):
        """
        Returns value of Disk provision type set in Full VM restore
        it is read only attribute
        """
        return self._av_zone

    @availability_zone.setter
    def availability_zone(self, value):
        """
        set the value of Disk provision type in Full VM restore

        Args:
            value   (String)  - Disk provision type
        """
        self._av_zone = value

    @property
    def register_with_failover(self):
        """
        Returns value of Overwrite set in Full VM restore
        it is read only attribute
        """
        return self.add_to_failover

    @register_with_failover.setter
    def register_with_failover(self, value):
        """
        This registers VM with Failover cluster

        Args:
            Value    (bool)     - True -  Register with Failover
                default:False

        """
        self.add_to_failover = value

    @property
    def restore_browse_ma(self):
        """
        Returns value of  media agent set in Full VM restore
        it is read only attribute
        """
        return self.advanced_restore_options.get('media_agent', None)

    @restore_browse_ma.setter
    def restore_browse_ma(self, value):
        """
        set the value of media agent in Full VM restore

        Args:
            value   (bool)  - True if poweron option need to be set
        """
        self.advanced_restore_options['media_agent'] = value

    @property
    def snap_proxy(self):
        """
        Returns value of  snap proxy set in Full VM restore
        it is read only attribute
        """
        return self.advanced_restore_options.get('snap_proxy', None)

    @snap_proxy.setter
    def snap_proxy(self, value):
        """
        set the value of snap proxy  in Full VM restore

        Args:
            value   (bool)  - True if poweron option need to be set
        """
        self.advanced_restore_options['snap_proxy'] = value

    def _process_inputs(self, attr_to_set, user_input):
        """
        will process all the inputs from user and set it as calss variable
        Args:
            attr_to_set    (str)    - property need to eb set as class variable

            user_input    (str)    - property  to be set as class variable that is passed from user

        Exception:
            if the property is not given in user input
        """
        try:
            if user_input in self.inputs.keys():
                setattr(self, attr_to_set, self.inputs[user_input])
            else:
                self.log.info("The Tag %s is not specified by the user" % user_input)
                setattr(self, attr_to_set, None)

        except Exception as err:
            self.log.exception("An Aerror occurred in setting hypervisor tags")
            raise err

    def populate_hypervisor_restore_inputs(self):
        """
        populate all the hypervisor defaults for the full VM restore

        Exception:
            if failed to compute default VSA Client

            if failed to compute proxy and Datastores and Host

        """
        try:
            instance_name = self.auto_subclient.auto_vsainstance.vsa_instance_name

            def hyperv():
                proxy_host_list = []

                vm_list = self.auto_subclient.vm_list

                # setting Virtualization client
                self.destination_client = self.inputs.get(
                    "DestinationClient", self.inputs["ClientName"])
                if "DestinationClient" in self.inputs:
                    _agent = self._destination_client.agents.get(self.inputs['AgentName'])
                    if "DestinationInstance" in self.inputs:
                        _instance = _agent.instances.get(self.inputs['DestinationInstance'])
                    else:
                        _instance = _agent.instances.get(self.inputs['InstanceName'])
                    dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                        self.auto_subclient.auto_commcell, self._destination_client)
                    self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(dest_auto_vsaclient,
                                                                                        _agent, _instance)
                else:
                    self.dest_auto_vsa_instance = self.auto_subclient.auto_vsainstance

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj
                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        (self.auto_subclient.hvobj.VMs[each_vm]))

                # setting server in the VSA Client
                if "RestoreHyperVServer" not in self.inputs:
                    host_dict = {}
                    proxy_list = self.dest_auto_vsa_instance.proxy_list
                    for each_proxy in proxy_list:
                        host_name = self.auto_subclient.auto_commcell.get_hostname_for_client(each_proxy)
                        proxy_host_list.append(host_name)
                        host_dict[each_proxy] = host_name

                    self.proxy_client, datastore, self.network = self.dest_client_hypervisor.compute_free_resources(
                        proxy_list, host_dict, vm_list)

                else:
                    self.proxy_client = self.inputs["RestoreHyperVServer"]

                self.dest_machine = machine.Machine(self.proxy_client,
                                                    self.auto_subclient.auto_commcell.commcell)

                # setting Destination path in VSA Client
                if "DestinationPath" not in self.inputs:
                    _dir_path = os.path.join(datastore, "\\CVAutomation")
                    if not self.dest_machine.check_directory_exists(_dir_path):
                        self.dest_machine.create_directory(_dir_path)

                else:
                    destination_path = self.inputs["DestinationPath"]
                    _dir_path = os.path.join(destination_path, "\\CVAutomation")
                    if not self.dest_machine.check_directory_exists(_dir_path):
                        self.dest_machine.create_directory(_dir_path)

                self.destination_path = _dir_path

            def vcloud():
                vm_list = self.auto_subclient.vm_list

                if "DestinationClient" not in self.inputs:
                    self._dest_client_name = self.inputs["ClientName"]
                    self.dest_auto_vsa_instance = self.auto_subclient.auto_vsainstance
                else:
                    self.destination_client = self.inputs.get("DestinationClient")
                    _agent = self._destination_client.agents.get(self.inputs['AgentName'])

                    if "DestinationInstance" in self.inputs:
                        _instance = _agent.instances.get(self.inputs["DestinationInstance"])
                    else:
                        _instance = _agent.instances.get(self.inputs["InstanceName"])
                    dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                        self.auto_subclient.auto_commcell, self._destination_client
                    )
                    self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(dest_auto_vsaclient, _agent,
                                                                                        _instance)

                self.automatic_proxy = self.inputs.get('automatic', False)
                self.proxy_client = self.inputs.get('proxy_client', None)
                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj

                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        self.auto_subclient.hvobj.VMs[each_vm])

            def vmware():
                vm_list = self.auto_subclient.vm_list
                # setting Virtualization client
                if "DestinationClient" not in self.inputs:
                    self.destination_client = self.inputs["ClientName"]
                    self.dest_auto_vsa_instance = self.auto_subclient.auto_vsainstance
                else:
                    self.destination_client = self.inputs.get(
                        "DestinationClient")
                    _agent = self._destination_client.agents.get(self.inputs['AgentName'])
                    if "DestinationInstance" in self.inputs:
                        _instance = _agent.instances.get(self.inputs['DestinationInstance'])
                    else:
                        _instance = _agent.instances.get(self.inputs['InstanceName'])
                    dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                        self.auto_subclient.auto_commcell, self._destination_client)
                    self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(dest_auto_vsaclient,
                                                                                        _agent,
                                                                                        _instance)

                self.automatic_proxy = self.inputs.get('automatic', False)
                if 'proxy_client' in self.inputs:
                    self.proxy_client = self.inputs.get('proxy_client')

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj
                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        (self.auto_subclient.hvobj.VMs[each_vm]))

                # setting Datastore and ESX in the VSA Client
                self._host = []
                for _vm in self.dest_client_hypervisor.VMs:
                    _vm = 'del' + _vm
                    _restored_vm = self.dest_client_hypervisor.find_vm(_vm)
                    if _restored_vm[0]:
                        if _restored_vm[0] == 'Multiple':
                            self.log.exception("%s is present in multiple ESX", _vm)
                            raise Exception
                        if len(self._host) > 0:
                            if self._host[0] != _restored_vm[1]:
                                _org = self.dest_client_hypervisor.find_esx_parent(self._host[0])
                                _new = self.dest_client_hypervisor.find_esx_parent(_restored_vm[1])
                                if "domain" in _org[0] and _new[0]:
                                    if _org[1] == _new[1]:
                                        continue
                                self.log.exception("Restore vms are existing in multiple ESX. Please clean and rerun")
                                raise Exception
                        self._host = [_restored_vm[1]]
                        self._datastore = _restored_vm[2]
                if len(self._host) > 0:
                    if self.inputs.get('Network') and self.inputs.get('Host') == self._host[0]:
                        self._network = self.inputs["Network"]
                    else:
                        self._network = self.dest_client_hypervisor._get_host_network(self._host[0])
                else:
                    if (("Datastore" not in self.inputs.keys()) or
                            ("Host" not in self.inputs.keys())):
                        self._datastore, self._host, self._cluster, self._datacenter, self._network = \
                            self.dest_client_hypervisor.compute_free_resources(vm_list)
                    else:
                        self._datastore = self.inputs["Datastore"]
                        self._host = [self.inputs["Host"]]
                        if 'Network' in self.inputs.keys():
                            self._network = self.inputs["Network"]
                        else:
                            self._network = self.dest_client_hypervisor._get_host_network(self._host[0])

            def fusion_compute():
                proxy_host_list = []
                self.power_on_after_restore = True
                vm_list = self.auto_subclient.vm_list

                # setting Virtualization client
                self.destination_client = self.inputs.get(
                    "DestinationClient",
                    self.auto_subclient.auto_vsaclient.vsa_client_name)

                dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                    self.auto_subclient.auto_commcell, self._destination_client)

                self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(dest_auto_vsaclient,
                                                                                    self.testcase.agent,
                                                                                    self.testcase.instance)

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj
                self.proxy_client = self.dest_auto_vsa_instance.co_ordinator

                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        (self.auto_subclient.hvobj.VMs[each_vm]))

                # setting server in the VSA Client
                if (("Host" not in self.inputs) and
                        ("Datastore" not in self.inputs)):

                    self.datastore, self.host = self.dest_client_hypervisor.compute_free_resources(vm_list,
                                                                                                   self.proxy_client)

                else:
                    self.host = self.inputs["Host"]
                    self.datastore = self.inputs["Datastore"]

            def AzureRM():
                vm_list = self.auto_subclient.vm_list

                # setting Virtualization client
                self.destination_client = self.inputs.get(
                    "DestinationClient", self.inputs.get("ClientName",
                                                     self.auto_subclient.auto_vsaclient.vsa_client_name))
                if "DestinationClient" in self.inputs:
                    _agent = self._destination_client.agents.get(self.inputs['AgentName'])
                    if "DestinationInstance" in self.inputs:
                        _instance = _agent.instances.get(self.inputs['DestinationInstance'])
                    else:
                        _instance = _agent.instances.get(self.inputs['InstanceName'])
                    dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                        self.auto_subclient.auto_commcell, self._destination_client)
                    self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(dest_auto_vsaclient,
                                                                                        _agent, _instance)
                else:
                    self.dest_auto_vsa_instance = self.auto_subclient.auto_vsainstance

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj
                self.disk_type_dict = {}
                self.subscripid = self.dest_client_hypervisor.subscription_id
                self.proxy_client = self.dest_auto_vsa_instance.co_ordinator
                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        (self.auto_subclient.hvobj.VMs[each_vm]))
                    self.disk_type_dict[each_vm] = self.inputs.get(
                        "restoreAsManagedVM", self.auto_subclient.hvobj.VMs[each_vm].managed_disk)
                # setting server in the VSA Client
                if (("Resourcegroup" not in self.inputs) and
                        ("Storageaccount" not in self.inputs)):

                    esx_host, datastore, datacenter = self.dest_client_hypervisor.compute_free_resources(vm_list)
                    self.Resource_Group = esx_host
                    self.Storage_account = datastore
                    self.datacenter = datacenter

                else:
                    self.Resource_Group = self.inputs["Resourcegroup"]
                    self.Storage_account = self.inputs["Storageaccount"]
                    self.datacenter = self.dest_client_hypervisor.get_storage_account_location(self.Storage_account)
                self.log.info("Restore location details : Resource Group = {0}, Storage Account = {1},"
                              "Datacenter/Region = {2}".format(
                    self.Resource_Group, self.Storage_account, self.datacenter))
                for each_vm in vm_list:
                    self.auto_subclient.hvobj.VMs[each_vm].restore_storage_acc = self.Storage_account
                if "NetworkDisplayName" in self.inputs:
                    self.network = self.inputs["NetworkDisplayName"]
                if "NetworkResourceGroup" in self.inputs:
                    self.networkrsg = self.inputs["NetworkResourceGroup"]
                else:
                    self.networkrsg = None
                self.subnet_id = self.inputs.get("subnet_id", "")
                if "Region" in self.inputs:
                    self.region = self.inputs["Region"]
                else:
                    self.region = self.datacenter
                if "restoreAsManagedVM" in self.inputs:
                    self.restoreAsManagedVM = self.inputs["restoreAsManagedVM"]
                if "instanceSize" in self.inputs:
                    self.instanceSize = self.inputs['instanceSize']
                else:
                    self.instanceSize = None
                if "CreatePublicIP" in self.inputs:
                    self.createPublicIP = (self.inputs['CreatePublicIP'].lower() == 'true')
                else:
                    self.createPublicIP = None
                if "VMSize" in self.inputs:
                    self.vm_size = self.inputs['VMSize']
                else:
                    self.vm_size = None

            def Azurestack():
                vm_list = self.auto_subclient.vm_list

                # setting Virtualization client
                self.destination_client = self.inputs.get(
                    "DestinationClient",
                    self.auto_subclient.auto_vsaclient.vsa_client_name)

                dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                    self.auto_subclient.auto_commcell, self._destination_client)

                self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(dest_auto_vsaclient,
                                                                                    self.testcase.agent,
                                                                                    self.testcase.instance)

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj

                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        (self.auto_subclient.hvobj.VMs[each_vm]))

                # setting server in the VSA Client
                if (("Resourcegroup" not in self.inputs) and
                        ("Storageaccount" not in self.inputs)):

                    esx_host, datastore = self.dest_client_hypervisor.compute_free_resources(vm_list)
                    self.Resource_Group = esx_host
                    self.Storage_account = datastore

                else:
                    self.Resource_Group = self.inputs["Resourcegroup"]
                    self.Storage_account = self.inputs["Storageaccount"]

            def oraclevm():
                vm_list = self.auto_subclient.vm_list
                self.destination_client = self.inputs.get(
                    "virtualizationClient",
                    self.auto_subclient.auto_vsaclient.vsa_client_name)

                dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                    self.auto_subclient.auto_commcell, self._destination_client)

                self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(
                    dest_auto_vsaclient,
                    self.testcase.agent,
                    self.testcase.instance)

                self.proxy_client = self.dest_auto_vsa_instance.co_ordinator

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj
                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        (self.auto_subclient.hvobj.VMs[each_vm]))

                # setting server in the VSA Client
                if (("Host" not in self.inputs) and
                        ("Datastore" not in self.inputs)):

                    self.host, self.datastore = self.dest_client_hypervisor.compute_free_resources(
                        vm_list)
                    for each_vm in vm_list:
                        if self.datastore not in self.dest_client_hypervisor.VMs[
                            each_vm].server_repos:
                            raise Exception(
                                "Restore operation can not be performed to the repository {0} "
                                "since the VM {1} is hosted on the server {2} "
                                "for which the suggested repo is not shared with".format(
                                    self.datastore, each_vm,
                                    self.dest_client_hypervisor.VMs[each_vm].server_name))
                else:
                    self.host = self.inputs["Host"]
                    self.datastore = self.inputs["Datastore"]

            def openstack():
                self.power_on_after_restore = True
                vm_list = self.auto_subclient.vm_list

                self.destination_client = self.inputs.get(
                    "DestinationClient",
                    self.auto_subclient.auto_vsaclient.vsa_client_name)

                dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                    self.auto_subclient.auto_commcell, self._destination_client)
                destination_project_name = self.inputs.get("destination_project_name", None)
                Source_Security_Grp = self.inputs.get("Source_Security_Grp")
                DestinationZone = self.inputs.get("DestinationZone")
                self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(dest_auto_vsaclient,
                                                                                    self.testcase.agent,
                                                                                    self.testcase.instance)

                self.proxy_client = self.dest_auto_vsa_instance.co_ordinator

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj
                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        (self.auto_subclient.hvobj.VMs[each_vm]))

                # setting server in the VSA Client
                if (("Host" not in self.inputs) and
                        ("Datastore" not in self.inputs)):

                    self.restoreObj = self.dest_client_hypervisor.compute_free_resources(vm_list[0],
                                                                                         project_name=destination_project_name,
                                                                                         securityGroups=Source_Security_Grp,
                                                                                         esxHost=DestinationZone)
                    self.host = self.restoreObj["esxServerName"]
                    self.datastore = self.restoreObj["Datastore"]
                    self.cluster = self.restoreObj["Cluster"]
                else:
                    self.host = self.inputs["Host"]
                    self.datastore = self.inputs["Datastore"]

                self.dest_machine = machine.Machine(self.proxy_client,
                                                    self.auto_subclient.auto_commcell.commcell)

            def rhev():
                self.power_on_after_restore = True
                vm_list = self.auto_subclient.vm_list

                self.destination_client = self.inputs.get(
                    "DestinationClient",
                    self.auto_subclient.auto_vsaclient.vsa_client_name)

                dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                    self.auto_subclient.auto_commcell, self._destination_client)

                self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(dest_auto_vsaclient,
                                                                                    self.testcase.agent,
                                                                                    self.testcase.instance)

                self.proxy_client = self.dest_auto_vsa_instance.co_ordinator

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj
                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        (self.auto_subclient.hvobj.VMs[each_vm]))

                # setting server in the VSA Client

                if "cluster" in self.inputs:
                    self.cluster = self.inputs['cluster']
                    if "storage" in self.inputs:
                        self.storage = self.inputs['storage']
                    else:
                        self.log.info("storage has to be specified as cluster is specified in inputs ")

                else:
                    self.restoreObj = self.dest_client_hypervisor.compute_free_resources(vm_list)
                    self.cluster = self.restoreObj[0]
                    self.repository = self.restoreObj[1]

                self.dest_machine = machine.Machine(self.proxy_client,
                                                    self.auto_subclient.auto_commcell.commcell)

            def alicloud():
                self.power_on_after_restore = True
                vm_list = self.auto_subclient.vm_list

                self.destination_client = self.inputs.get(
                    "virtualizationClient",
                    self.auto_subclient.auto_vsaclient.vsa_client_name)

                dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                    self.auto_subclient.auto_commcell, self._destination_client)

                self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(
                    dest_auto_vsaclient,
                    self.testcase.agent,
                    self.testcase.instance)

                self.proxy_client = self.dest_auto_vsa_instance.co_ordinator

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj
                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        (self.auto_subclient.hvobj.VMs[each_vm]))

                if (("AvailabilityZone" not in self.inputs) and
                        ("Network" not in self.inputs) and
                        ("SecurityGroups" not in self.inputs)):

                    self._availability_zone, self._network, \
                    self._security_groups = self.dest_client_hypervisor.compute_free_resources(
                        self.proxy_client)

                else:
                    self._availability_zone = self.inputs['AvailabilityZone']
                    self._network = self.inputs['Network']
                    self._security_groups = self.inputs['SecurityGroups']

            def amazon():
                vm_list = self.auto_subclient.vm_list
                # setting Virtualization client
                self.destination_client = self.inputs.get(
                    "DestinationClient",
                    self.auto_subclient.auto_vsaclient.vsa_client_name)

                dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                    self.auto_subclient.auto_commcell, self._destination_client)

                self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(
                    dest_auto_vsaclient,self.auto_subclient.auto_vsainstance.vsa_agent, self.auto_subclient.auto_vsainstance.vsa_instance, tcinputs=self.inputs,
                    **self.auto_subclient.auto_vsainstance.kwargs)

                if "proxy_client" in self.inputs:
                    self.proxy_client = self.inputs['proxy_client']
                else:
                    self.proxy_client = self.dest_auto_vsa_instance.co_ordinator
                self.automatic_proxy = self.inputs.get('automatic', False)
                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj
                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        (self.auto_subclient.hvobj.VMs[each_vm]))
                    if "data_center" not in self.inputs:
                        self.data_center = self.dest_client_hypervisor.VMs[each_vm].aws_region
                    else:
                        self.data_center = self.inputs['data_center']

                self._dest_client_name = self.destination_client

            def oci():
                vm_list = self.auto_subclient.vm_list
                # setting Virtualization client
                self.destination_client = self.inputs.get(
                    "DestinationClient",
                    self.auto_subclient.auto_vsaclient.vsa_client_name)

                dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                    self.auto_subclient.auto_commcell, self._destination_client)

                self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(
                    dest_auto_vsaclient, self.auto_subclient.auto_vsainstance.vsa_agent, self.auto_subclient.auto_vsainstance.vsa_instance, self.inputs,
                    **self.auto_subclient.auto_vsainstance.kwargs)

                self.proxy_client = self.dest_auto_vsa_instance.co_ordinator

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj
                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        (self.auto_subclient.hvobj.VMs[each_vm]))
                self._dest_client_name = self.destination_client

            def nutanix():
                vm_list = self.auto_subclient.vm_list

                # setting Virtualization client
                self.destination_client = self.inputs.get(
                    "DestinationClient",
                    self.auto_subclient.auto_vsaclient.vsa_client_name)

                dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                    self.auto_subclient.auto_commcell, self._destination_client)

                self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(
                                                                        dest_auto_vsaclient,
                                                                        self.testcase.agent,
                                                                        self.testcase.instance,
                                                                        **self.auto_subclient.auto_vsainstance.kwargs)

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj
                self.proxy_client = self.dest_auto_vsa_instance.co_ordinator

                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        (self.auto_subclient.hvobj.VMs[each_vm]))

                # setting server in the VSA Client
                if ("Container" not in self.inputs):
                    datastore = self.dest_client_hypervisor.compute_free_resources(vm_list)
                    self.container = datastore

                else:
                    self.container = self.inputs["Container"]

            def googlecloud():
                vm_list = self.auto_subclient.vm_list
                self.destination_client = self.inputs.get(
                    "DestinationClient",
                    self.auto_subclient.auto_vsaclient.vsa_client_name)

                _agent = self._destination_client.agents.get(self.inputs['AgentName'], self.testcase.agent)
                if "DestinationInstance" in self.inputs:
                    _instance = _agent.instances.get(self.inputs['DestinationInstance'])
                else:
                    _instance = _agent.instances.get(self.inputs['InstanceName'])

                dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                    self.auto_subclient.auto_commcell, self._destination_client)

                self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(dest_auto_vsaclient,
                                                                                    _agent, _instance)

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj
                self.validate_restore_workload = True
                if self.inputs.get("automatic"):
                    self.validate_restore_workload = self.inputs['automatic']
                if self.validate_restore_workload:
                    self.proxy_client = self.destination_client
                else:
                    self.proxy_client = self.dest_auto_vsa_instance.co_ordinator

                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        (self.auto_subclient.hvobj.VMs[each_vm]))

                # setting server in the VSA Client
                esx_host = self.inputs.get("Zone",
                                           self.dest_client_hypervisor.get_vm_zone(vm_list[0]))
                self.zone = esx_host
                self.project_id = self.inputs.get(
                    "ProjectID",
                    self.auto_subclient.hvobj.project)
                self.destination_network = self.inputs.get('destination_network')
                self.networks_nic = self.inputs.get("NetworkNic")
                self.subnetwork_nic = self.inputs.get("NetworkSubnetNic")
                self.replica_zone = self.inputs.get("replicaZone")
                self.vm_custom_metadata = self.inputs.get("vmCustomMetadata")
                self.create_public_ip = self.inputs.get("createPublicIP")
                self.public_ip_address = self.inputs.get("publicIPaddress")
                self.private_ip_address = self.inputs.get("privateIPaddress")

            def xen():
                vm_list = self.auto_subclient.vm_list

                # setting Virtualization client
                self.destination_client = self.inputs.get(
                    "DestinationClient",
                    self.auto_subclient.auto_vsaclient.vsa_client_name)

                dest_auto_vsaclient = VirtualServerHelper.AutoVSAVSClient(
                    self.auto_subclient.auto_commcell, self._destination_client)

                self.dest_auto_vsa_instance = VirtualServerHelper.AutoVSAVSInstance(dest_auto_vsaclient,
                                                                                    self.testcase.agent,
                                                                                    self.testcase.instance)

                self.dest_client_hypervisor = self.dest_auto_vsa_instance.hvobj
                self.proxy_client = self.dest_auto_vsa_instance.co_ordinator

                for each_vm in vm_list:
                    self.dest_client_hypervisor.VMs[each_vm] = self.auto_subclient.__deepcopy__(
                        (self.auto_subclient.hvobj.VMs[each_vm]))

                # setting server in the VSA Client
                if ("xen_server" not in self.inputs) and \
                        ("storage" not in self.inputs):
                    self.xen_server, self.storage = self.dest_client_hypervisor.compute_free_resources(vm_list)
                else:
                    self.xen_server = self.inputs["xen_server"]
                    self.storage = self.inputs["storage"]

            hv_dict = {hypervisor_type.MS_VIRTUAL_SERVER.value.lower(): hyperv,
                       hypervisor_type.VIRTUAL_CENTER.value.lower(): vmware,
                       hypervisor_type.Vcloud.value.lower(): vcloud,
                       hypervisor_type.Fusion_Compute.value.lower(): fusion_compute,
                       hypervisor_type.ORACLE_VM.value.lower(): oraclevm,
                       hypervisor_type.AZURE_V2.value.lower(): AzureRM,
                       hypervisor_type.Azure_Stack.value.lower(): Azurestack,
                       hypervisor_type.OPENSTACK.value.lower(): openstack,
                       hypervisor_type.Rhev.value.lower(): rhev,
                       hypervisor_type.Alibaba_Cloud.value.lower(): alicloud,
                       hypervisor_type.AMAZON_AWS.value.lower(): amazon,
                       hypervisor_type.ORACLE_CLOUD_INFRASTRUCTURE.value.lower(): oci,
                       hypervisor_type.Nutanix.value.lower(): nutanix,
                       hypervisor_type.Google_Cloud.value.lower(): googlecloud,
                       hypervisor_type.Xen.value.lower(): xen}

            (hv_dict[instance_name])()

        except Exception as err:
            self.log.exception("An error occurred in setting hypervisor tags")
            raise err

    @property
    def source_ip(self):
        """
        Returns IP of the source vm
        """
        return self._source_ip

    @source_ip.setter
    def source_ip(self, value):
        """
        Assigning Source IP from the input
        Args:
                value   (str) - IP of the source VM
        """
        self._source_ip = value

    @property
    def destination_ip(self):
        """
        Returns IP of the destination vm
        """
        return self._destination_ip

    @destination_ip.setter
    def destination_ip(self, value):
        """
        Assigning Source IP from the input
        Args:
                value   (str) - IP of the destination VM
        """
        self._destination_ip = value

    @property
    def destination_client(self):
        """
        Return destination client where disk are to be restored .
        It is read only attribute
        """
        return self._dest_client_name

    @destination_client.setter
    def destination_client(self, client_name):
        """
        set the particular client as destination client for disk restore

        Args:
            client_name     (str)   - Pseudo client_name as configured in cs
        """
        self._destination_pseudo_client = client_name
        self._destination_client = self.auto_subclient.auto_commcell.commcell.clients.get(
            client_name)
        self._dest_client_name = self._destination_client.client_name
        self._dest_host_name = self._destination_client.client_hostname

    @property
    def dest_computer_name(self):
        """
        Returns Hostname of the destination vm
        """
        return self._dest_computer_name

    @dest_computer_name.setter
    def dest_computer_name(self, value):
        """
        Assigning Hostname from the input
        Args:
                value   (str) - Hostname of the destination VM
        """
        self._dest_computer_name = value

    @property
    def automatic_proxy(self):
        """
        Returns boolean value for automatic access node.
        It returns True if proxy workload distribution is enabled.
        """
        return self._automatic_proxy

    @automatic_proxy.setter
    def automatic_proxy(self, value):
        """
        Assigning proxy client based on the value.
        Args:
            value       (bool) : value for enabling/disabling automatic proxy
        """

        self._automatic_proxy = value
        if self._automatic_proxy:
            self.validate_restore_workload = True
            self.proxy_client = self.destination_client
        else:
            if self.destination_client == self.inputs["ClientName"] and len(
                    self.auto_subclient.subclient.subclient_proxy) > 0:
                self.proxy_client = self.auto_subclient.subclient.subclient_proxy[0]
            else:
                self.proxy_client = self.dest_auto_vsa_instance.co_ordinator


class LiveSyncOptions(FullVMRestoreOptions):
    """Main class for Live Sync options in Automation"""

    def __init__(self, subclient, testcase):
        """
        To Initialize LiveSyncOptions class

        Args:

            subclient   (obj)   -   object of AutoVSASubclient class in VirtualServerHelper

            testcase    (obj)   -   Testcase object

        """
        super(LiveSyncOptions, self).__init__(subclient, testcase)

        self._schedule_name = self.inputs.get('ScheduleName') or OptionsSelector.get_custom_str('Schedule')
        self._distribute_vm_workload = None
        self.live_sync_direct = False  # Only for VMware
        self.destination_client = None
        self.live_sync_name = None

    @property
    def schedule_name(self):
        """Returns the name of the schedule"""
        return self._schedule_name

    @schedule_name.setter
    def schedule_name(self, schedule_name):
        """
        To set the schedule name

        Args:
            schedule_name   (str)   -- Name of the schedule

        """
        self._schedule_name = schedule_name

    @property
    def distribute_vm_workload(self):
        """Returns the value of distribute vm workload"""
        return self._distribute_vm_workload

    @distribute_vm_workload.setter
    def distribute_vm_workload(self, workload):
        """
        To set the vm workload value

        Args:
            workload    (int)   -- Virtual machines to be used per job

        """
        self._distribute_vm_workload = workload

    @property
    def datastore_info(self):
        """

        Returns datastore
        Read Only attribute
        Returns:
            datastore (str) : datastore for restore options

        """
        return self._datastore

    @property
    def network_info(self):
        """

        Returns network
        Returns:
            network (str) : network for restore options
        """
        return self._network

class VSAMetallicOptions(object):
    """
    class to handle all testcase inputs
    """

    def __init__(self, tc_inputs):
        self.tc_inputs = tc_inputs
        self.log = logger.get_log()
        self._app_type = None
        self._BYOS = False
        self._backup_gatewayname = None
        self._backup_gateway = None
        self._remote_username = None
        self._remote_userpassword = None
        self._proxy_name = None
        self._proxy_client_name = None
        self._proxy_remote_username = None
        self._proxy_remote_userpassword = None
        self._subscription_id = None
        self._tenant_id = None
        self._new_tenant = None
        self._hyp_client_name = None
        self._hyp_host_name = None
        self._hyp_user_name = None
        self._hyp_pwd = None
        self._hyp_credential_name = None
        self._existing_hypervisor = None
        self._content_type = None
        self._content_category = None
        self._content_list = []
        self._tenant_content_list = []
        self._existing_storage = None
        self._new_storage_name = None
        self._storage_target_type = None
        self._storage_backup_gateway = None
        self._keep_only_on_premise = None
        self._storage_path = None
        self._nw_storage_uname = None
        self._nw_storage_pwd = None
        self._existing_storage_cloud = None
        self._cloud_storage_account = None
        self._cloud_storage_provider = None
        self._cloud_storage_tier = None
        self._cloud_storage_region = None
        self._storage_credential_name = None
        self._storage_credential_account = None
        self._storage_credential_password = None
        self._cloud_storage_name = None
        self._cloud_access_key_or_account_name = None
        self._secret_access_key = None
        self._bucket_container = None
        self._opt_existing_plan = None
        self._opt_new_plan = None  # planName
        self._one_month_plan = False
        self._custom_plan = False
        self._local_retention = None
        self._local_retention_unit = None
        self._backup_frequency = None
        self._cloud_retention = None
        self._cloud_retention_unit = None
        self._snap_retention = None
        self._snap_backup = None
        self._backup_frequency_unit = None
        self._existing_hypervisor = None
        self._backup_now = False
        self._aws_authentication_type = None
        self._region = None
        self._gateway_os_platform = None
        self._aws_vpc_id = None
        self._aws_subnet_id = None
        self._aws_storage_class = None
        self._aws_hypervisor_region = None
        self._vm_group_name = None
        self._oci_policy_compartment = None
        self._aws_role_arn = None
        self.aws_admin_role_arn = None
        self.aws_admin_account_configured = False
        self.aws_stacks_created = []
        self.oci_stacks_created = []
        self._install_through_authcode = False
        self.access_node_os = None
        self.deploy_helper = None

        # Secondary Cloud Storage Copy
        self._secondary_storage_cloud = None
        self._secondary_storage_credential_account = None
        self._secondary_storage_credential_password = None
        self._secondary_cloud_storage_account = None
        self._secondary_cloud_storage_region = None
        self._secondary_cloud_storage_provider = None
        self._existing_secondary_cloud = None
        self._secondary_storage_credential_name = None

        # Kubernetes specific
        self._k8s_deployment_method = None

        # Only use on-premises storage
        self._skip_cloud_storage = None

    @property
    def install_through_authcode(self):
        """
        get the value to check if we need to install through authcode
        Returns:
            (boolean) whether to install using authcode or not
        """
        if not self._install_through_authcode:
            self._install_through_authcode = self.tc_inputs.get("install_through_authcode", None)
        return self._install_through_authcode

    @install_through_authcode.setter
    def install_through_authcode(self, value):
        """
        set it to true, to use authcode during installation
        Args:
            value: (boolean)

        Returns:
            None
        """
        self._install_through_authcode = value

    @property
    def BYOS(self):
        """
        get whether it is a BYOS setup
        Returns:
            (boolean) if it is BYOS
        """
        return self._BYOS

    @BYOS.setter
    def BYOS(self, value):
        """
        set to true if it is BYOS(Bring Your Own Setup) setup
        Args:
            value: (boolean)
        """
        self._BYOS = value

    @property
    def aws_role_arn(self):
        """
        get the arn of the aws role
        Returns:
            (str) arn of the role
        """
        return self._aws_role_arn

    @aws_role_arn.setter
    def aws_role_arn(self, value):
        """
        set the arn of the role
        Args:
            value: (str)

        Returns:
            None
        """
        self._aws_role_arn = value

    @property
    def oci_policy_compartment(self):
        """
        compartment id of the oci policy
        """
        if not self._oci_policy_compartment:
            self._oci_policy_compartment = self.tc_inputs.get("policy_compartment", None)
        return self._oci_policy_compartment

    @oci_policy_compartment.setter
    def oci_policy_compartment(self, value):
        """
        set oci compartment policy
        Args:
            value: (str) id of the compartment
        Returns : None
        """
        self._oci_policy_compartment = value

    @property
    def vm_group_name(self):
        """
        name of the vm group
        """
        if not self._vm_group_name:
            self._vm_group_name = self.tc_inputs.get("SubclientName", None)
        if not self._vm_group_name:
            self._vm_group_name = self.tc_inputs.get('vm_group_name', None)
        return self._vm_group_name

    @vm_group_name.setter
    def vm_group_name(self, value):
        """
        set the vm-group name
        Args:
            value: (str) vm-group name
        Returns : None
        """
        self._vm_group_name = value

    @property
    def aws_hypervisor_region(self):
        """
        get the region name of the hypervisor client
        Returns:
            (str) region name
        """
        if not self._aws_hypervisor_region:
            self._aws_hypervisor_region = self.tc_inputs.get("aws_hypervisor_region", None)
        return self._aws_hypervisor_region

    @aws_hypervisor_region.setter
    def aws_hypervisor_region(self, value):
        """
        set hypervisor region for aws
        Args:
            value: (str) region name

        Returns: None

        """
        self._aws_hypervisor_region = value

    @property
    def aws_storage_class(self):
        """
        get the storage type of cloud storage
        Returns:
            (str) storage type
        """
        if not self._aws_storage_class:
            self._aws_storage_class = self.tc_inputs.get("aws_storage_class", None)
        return self._aws_storage_class

    @aws_storage_class.setter
    def aws_storage_class(self, value):
        """
        set the storage type for the cloud storage
        Args:
            value: (str) storage type

        Returns: None

        """
        self._aws_storage_class = value

    @property
    def aws_subnet_id(self):
        """
        subnet id for the aws gateway
        Returns:
            (str) id of the subnet in which aws gateway should be available
        """
        if not self._aws_subnet_id:
            self._aws_subnet_id = self.tc_inputs.get("aws_subnet_id", None)
        return self._aws_subnet_id

    @aws_subnet_id.setter
    def aws_subnet_id(self, value):
        """
        set the subnet for the backup gateway
        Args:
            value: (str) subent id

        Returns: None

        """
        self._aws_subnet_id = value

    @property
    def aws_vpc_id(self):
        """
        vpc for the aws gateway
        Returns:
            (str) id of the vpc in which aws gateway should be available
        """
        if not self._aws_vpc_id:
            self._aws_vpc_id = self.tc_inputs.get("aws_vpc_id", None)
        return self._aws_vpc_id

    @aws_vpc_id.setter
    def aws_vpc_id(self, value):
        """
        set the vpc for the backup gateway
        Args:
            value: (str) vpc id

        Returns: None

        """
        self._aws_vpc_id = value

    @property
    def gateway_os_platform(self):
        """
        os platoform for the aws gateway
        Returns:
            (str) os platform
        """
        if not self._gateway_os_platform:
            self._gateway_os_platform = self.tc_inputs.get("gateway_os_platform", None)
        return self._gateway_os_platform

    @gateway_os_platform.setter
    def gateway_os_platform(self, value):
        """
        sets the os platform for aws gateway
        Args:
            value: (str) name of the os platform

        Returns:
            None
        """
        self._gateway_os_platform = value

    @property
    def region(self):
        """
        region name under which gateway should be in
        Returns:
            (str) name of the region
        """
        if not self._region:
            self._region = self.tc_inputs.get('region', None)
        return self._region

    @region.setter
    def region(self, value):
        """
        set the aws gateway region
        Args:
            value: (str) name of the region

        Returns:
            None
        """
        self._region = value

    @property
    def aws_authentication_type(self):
        """
        type of authentication to user for aws
        Returns:
            (str) authentication type
        """
        if not self._aws_authentication_type:
            self._aws_authentication_type = self.tc_inputs.get('aws_authentication_type', None)
        return self._aws_authentication_type

    @aws_authentication_type.setter
    def aws_authentication_type(self, value):
        """
        method to set the aws authentication type
        Args:
            value : (str)   type of authentication
        """
        self._aws_authentication_type = value

    @property
    def app_type(self):
        """
        application type (eg VM&KUBERNETES, DATABASE, FILE SYSTEM)
        Returns:
            (str) application type
            read only attribute
        """
        if not self._app_type:
            self._app_type = self.tc_inputs.get('appType', 'UNDEFINED')
        return self._app_type

    @app_type.setter
    def app_type(self, value):
        """
        sets the application type (eg VM&KUBERNETES, DATABASE, FILE SYSTEM)
        Args:
            value : (str) application type
        """
        self._app_type = value

    @property
    def subscription_id(self):
        """
        subscription id is an id for azure cloud subscription to access the account
        Returns:
            (str) subscription Id
            read only attribute
        """
        if not self._subscription_id:
            self._subscription_id = self.tc_inputs.get('subscription_id', None)
        return self._subscription_id

    @subscription_id.setter
    def subscription_id(self, value):
        """
        subscription id is a id for azure cloud subscription to access the account
        Args:
            value: (str) subscription id
        """
        self._subscription_id = value

    @property
    def tenant_id(self):
        """
        tenant id of the tenant for the azure account
        Returns:
            (str) tenant id
        """
        if not self._tenant_id:
            self._tenant_id = self.tc_inputs.get('tenant_id', None)
        return self._tenant_id

    @tenant_id.setter
    def tenant_id(self, value):
        """
        tenant id of the tenant for the azure account
        Args:
            value: (str)
        """
        self._tenant_id = value

    @property
    def backup_gatewayname(self):
        """
        name of the backup gateway
        Returns:
            (str) backup_gateway hostname or ip
            read only property
        """
        if not self._backup_gatewayname:
            self._backup_gatewayname = self.tc_inputs.get('backup_gatewayname', None)
        return self._backup_gatewayname

    @backup_gatewayname.setter
    def backup_gatewayname(self, value):
        """
        name of the backup gateway
        Args:
            value: (str) backup gateway hostname or ip
        """
        self._backup_gatewayname = value

    @property
    def remote_username(self):
        """
        username for the backup gateway machine
        Returns:
            (str) username for backup gateway machine
        """
        if not self._remote_username:
            self._remote_username = self.tc_inputs.get('remote_username', None)
        return self._remote_username

    @remote_username.setter
    def remote_username(self, value):
        """
        username for the backup gateway machine
        Args:
            value: (str)
        """
        self._remote_username = value

    @property
    def remote_userpassword(self):
        """
        password for the backup gateway machine
        Returns:
            (str) password for backup gateway
        """
        if not self._remote_userpassword:
            self._remote_userpassword = self.tc_inputs.get('remote_userpassword', None)
        return self._remote_userpassword

    @remote_userpassword.setter
    def remote_userpassword(self, value):
        """
        password for the backup gateway machine
        Args:
            value: (str) backup gateway machine
        """
        self._remote_username = value

    @property
    def proxy_name(self):
        """
        hostname or ip of the host machine of hyperv where vms are present on
        Returns:
            (str) hostname or ip of the host machine
        """
        if not self._proxy_name:
            self._proxy_name = self.tc_inputs.get('proxy_name', None)
        return self._proxy_name

    @proxy_name.setter
    def proxy_name(self, value):
        """
        hostname or ip of the host machine of hyperv where vms are present on
        Args:
            value: (str) hostname or ip of the host machine
        """
        self._proxy_name = value

    @property
    def proxy_client_name(self):
        """
        Gets the client name of the hyper-v proxy configured.

        Returns:
            (str) client name of the hyper-v proxy configured.
        """
        if not self._proxy_client_name:
            self._proxy_client_name = self.tc_inputs.get('proxy_client_name', None)
        return self._proxy_client_name

    @proxy_client_name.setter
    def proxy_client_name(self, value):
        """
        Client name of the hyper-v proxy configured.

        Args:
            value: (str) client name of the hyper-v proxy configured.
        """
        self._proxy_client_name = value

    @property
    def proxy_remote_username(self):
        """
        username of the proxy machine for hyperv
        Returns:
            (str) username of the proxy machine
        """
        if not self._proxy_remote_username:
            self._proxy_remote_username = self.tc_inputs.get('proxy_remote_username', None)
        return self._proxy_remote_username

    @proxy_remote_username.setter
    def proxy_remote_username(self, value):
        """
        username of the proxy machine for hyperv
        Args:
            value: (str) username of the proxy machine
        """
        self._proxy_remote_username = value

    @property
    def proxy_remote_userpassword(self):
        """
        password of the proxy machine for hyperv
        Returns:
            (str) password of the proxy machine
        """
        if not self._proxy_remote_userpassword:
            self._proxy_remote_userpassword = self.tc_inputs.get('proxy_remote_userpassword', None)
        return self._proxy_remote_userpassword

    @proxy_remote_userpassword.setter
    def proxy_remote_userpassword(self, value):
        """
        password of the proxy machine for hyperv
        Args:
            value: (str) password for the proxy machine
        """
        self._proxy_remote_userpassword = value

    @property
    def new_tenant(self):
        """
        Returns:
            (str) tenant name
        """
        if not self._new_tenant:
            self._new_tenant = self.tc_inputs.get('newTenant', None)
        return self._new_tenant

    @new_tenant.setter
    def new_tenant(self, value):
        """
        name of the tenant
        Args:
            value:  (str) tenant name
        """
        self._new_tenant = value

    @property
    def backup_now(self):
        """
        perform backup right after configuration
        Returns:
            (bool) either to back up or not
        """
        if not self._backup_now:
            self._backup_now = self.tc_inputs.get('backupNow', None)
        return self._backup_now

    @backup_now.setter
    def backup_now(self, value):
        """
        perform backup right after configuration
        Args:
            value: (bool) either to perform or not
        """
        self._backup_now = value

    @property
    def opt_existing_plan(self):
        """
        use an existing plan during configuration
        Returns:
            (str) name of the existing plan
        """
        if not self._opt_existing_plan:
            self._opt_existing_plan = self.tc_inputs.get('optExistingPlan', None)
        return self._opt_existing_plan

    @opt_existing_plan.setter
    def opt_existing_plan(self, value):
        """
        use an existing plan during configuration
        Args:
            value: (str) name of the plan
        """
        self._opt_existing_plan = value

    @property
    def opt_new_plan(self):
        """
        create a new plan
        Returns:
            (str) name of the new plan to be created
        """
        if not self._opt_new_plan:
            self._opt_new_plan = self.tc_inputs.get('optNewPlan', None)
        return self._opt_new_plan

    @opt_new_plan.setter
    def opt_new_plan(self, value):
        """
        option to create a new plan
        Args:
            value: (str) name of the new plan to be created
        """
        self._opt_new_plan = value

    @property
    def one_month_plan(self):
        """
        select the one month plan
        Returns:
            (bool) whether to select one month plan or not
        """
        if not self._one_month_plan:
            self._one_month_plan = self.tc_inputs.get('oneMonthPlan', None)
        return self._one_month_plan

    @one_month_plan.setter
    def one_month_plan(self, value):
        """
        select the one month plan
        Args:
            value: (bool) wether to select one month plan or not
        """
        self._one_month_plan = value

    @property
    def backup_frequency(self):
        """
        backup frequency during custom plan creation
        Returns:
            (str) string converted number
        """
        if not self._backup_frequency:
            self._backup_frequency = self.tc_inputs.get('backupFrequency', None)
        return self._backup_frequency

    @backup_frequency.setter
    def backup_frequency(self, value):
        """
        backup frequency during custom plan creation
        Args:
            value: (str) number converted to string
        """
        self._backup_frequency = value

    @property
    def backup_frequency_unit(self):
        """
        unit of backup frquency (eg days, months, years .. etc)
        Returns:
            (str) backup frequency unit
        """
        if not self._backup_frequency_unit:
            self._backup_frequency_unit = self.tc_inputs.get('backupFrequencyUnit', None)
        return self._backup_frequency_unit

    @backup_frequency_unit.setter
    def backup_frequency_unit(self, value):
        """
        unit of backup frequency
        Args:
            value: (str) eg(days, months, years ..etc)
        """
        self._backup_frequency_unit = value

    @property
    def snap_retention(self):
        """
        snap retention during custom plan creation
        Returns:
            (str) snap retention (number as string type)
        """
        if not self._snap_retention:
            self._snap_retention = self.tc_inputs.get('snapRetention', None)
        return self._snap_retention

    @snap_retention.setter
    def snap_retention(self, value):
        """
        snap retention during custom plan creation
        Args:
            value : (str) local retention
        """
        self._snap_retention = value

    @property
    def snap_backup(self):
        """
        Whether intellisnap should be enabled or not during VM Group Creation.

        Returns:
            snap_backup :   (bool) Intellisnap Backup or Streaming Backup
        """
        if not self._snap_backup:
            self._snap_backup = self.tc_inputs.get('snapBackup', None)
        return self._snap_backup

    @snap_backup.setter
    def snap_backup(self, value):
        """
        Whether intellisnap should be enabled or not during VM Group Creation.

        Args:
            snap_backup :   (bool) Intellisnap Backup or Streaming Backup
        """
        self._snap_backup = value

    @property
    def local_retention(self):
        """
        local retention during custom plan creation
        Returns:
            (str) local retention (number as string type)
        """
        if not self._local_retention:
            self._local_retention = self.tc_inputs.get('localRetention', None)
        return self._local_retention

    @local_retention.setter
    def local_retention(self, value):
        """
        local retention during custom plan creation
        Args:
            value : (str) local retention
        """
        self._local_retention = value

    @property
    def local_retention_unit(self):
        """
        unit of local retention (eg days, months, years .. etc)
        Returns:
            (str) local retention unit
        """
        if not self._local_retention_unit:
            self._local_retention_unit = self.tc_inputs.get('localRetentionUnit', None)
        return self._local_retention_unit

    @local_retention_unit.setter
    def local_retention_unit(self, value):
        """
        unit of local retention (eg days, months, years .. etc)
        Args:
            value: (str) set the local retention unit
        """
        self._local_retention_unit = value

    @property
    def cloud_retention(self):
        """
        cloud retention during custom plan creation
        Returns:
            (str) cloud retention (number as string type)
        """
        if not self._cloud_retention:
            self._cloud_retention = self.tc_inputs.get('cloudRetention', None)
        return self._cloud_retention

    @cloud_retention.setter
    def cloud_retention(self, value):
        """
        cloud retention during custom plan creation
        Args:
            value: (str) cloud retention (number as string type)
        """
        self._cloud_retention = value

    @property
    def cloud_retention_unit(self):
        """
        unit of cloud retention (eg days, months, years .. etc)
        Returns:
            (str) cloud retention unit
        """
        if not self._cloud_retention_unit:
            self._cloud_retention_unit = self.tc_inputs.get('cloudRetentionUnit', None)
        return self._cloud_retention_unit

    @cloud_retention_unit.setter
    def cloud_retention_unit(self, value):
        """
        unit of cloud retention (eg days, months, years .. etc)
        Args:
            value: (str) cloud retention unit
        """
        self._cloud_retention_unit = value

    @property
    def custom_plan(self):
        """
        option to create custom plan
        Returns:
            (bool) select the custom plan or not
        """
        if not self._custom_plan:
            self._custom_plan = self.tc_inputs.get('customPlan', None)
        return self._custom_plan

    @custom_plan.setter
    def custom_plan(self, value):
        """
        option to create custom plan
        Args:
            value: (bool) whether to create a custom plan or not
        """
        self._custom_plan = value

    @property
    def secret_access_key(self):
        """
        access key to be used during storage configuration
        Returns:
            (str) set the secret key
        """
        if not self._secret_access_key:
            self._secret_access_key = self.tc_inputs.get('secretAccessKey', None)
        return self._secret_access_key

    @secret_access_key.setter
    def secret_access_key(self, value):
        """
        access key to be used during storage configuration
        Args:
            value: (str) secret access key
        """
        self._secret_access_key = value

    @property
    def bucket_container(self):
        """
        name of the bucket to be used for storage
        Returns:
            (str) details of the bucket
        """
        if not self._bucket_container:
            self._bucket_container = self.tc_inputs.get('bucketContainer', None)
        return self._bucket_container

    @bucket_container.setter
    def bucket_container(self, value):
        """
        name of the bucket to be used for storage
        Args:
            value: (str) details of the bucket
        """
        self._bucket_container = value

    @property
    def cloud_access_key_or_account_name(self):
        """
        access key for the cloud (for aws)
        account name for the cloud(for other clouds)
        Returns:
            (str) access key or account name for the cloud
        """
        if not self._cloud_access_key_or_account_name:
            self._cloud_access_key_or_account_name = self.tc_inputs.get('cloudAccessKeyorAzureAccountName', None)
        return self._cloud_access_key_or_account_name

    @cloud_access_key_or_account_name.setter
    def cloud_access_key_or_account_name(self, value):
        """
        access key for the cloud (for aws)
        account name for the cloud(for other clouds)
        Args:
            value: (str) access key or account name for the cloud
        """
        self._cloud_access_key_or_account_name = value

    @property
    def storage_path(self):
        """
        storage path for the storage configuration
        Returns:
            (str) storage path
        """
        if not self._storage_path:
            self._storage_path = self.tc_inputs.get('storagePath')
        return self._storage_path

    @storage_path.setter
    def storage_path(self, value):
        """
        storage path for the the storage configuration
        Args:
            value: (str) storage path
        """
        self._storage_path = value

    @property
    def existing_storage_cloud(self):
        """
        select the existing storage cloud
        Returns:
            (str) option to select the existing cloud storage
        """
        if not self._existing_storage_cloud:
            self._existing_storage_cloud = self.tc_inputs.get('existingStorageCloud')
        return self._existing_storage_cloud

    @existing_storage_cloud.setter
    def existing_storage_cloud(self, value):
        """
        select the existing storage cloud
        Args:
            value: (str) existing storage cloud
        """
        self._existing_storage_cloud = value

    @property
    def cloud_storage_account(self):
        """
        select an existing cloud account to create library
        Returns:
            (str) option to select the existing account
        """
        if not self._cloud_storage_account:
            self._cloud_storage_account = self.tc_inputs.get('cloudStorageAccount', None)
        return self._cloud_storage_account

    @cloud_storage_account.setter
    def cloud_storage_account(self, value):
        """
        select an existing cloud account to create library
        Args:
            value: (str) cloud account name
        """
        self._cloud_storage_account = value

    @property
    def secondary_cloud_storage_account(self):
        """
        Select an existing cloud account to create secondary library
        Returns:
            (str) option to select the existing account
        """
        if not self._secondary_cloud_storage_account:
            self._secondary_cloud_storage_account = self.tc_inputs.get('secondaryCloudStorageAccount', None)
        return self._secondary_cloud_storage_account

    @secondary_cloud_storage_account.setter
    def secondary_cloud_storage_account(self, value):
        """
        Select an existing cloud account to create secondary library
        Args:
            value: (str) cloud account name
        """
        self._secondary_cloud_storage_account = value

    @property
    def cloud_storage_provider(self):
        """
        cloud provider during library creation
        Returns:
            (str) option to select cloud provider
        """
        if not self._cloud_storage_provider:
            self._cloud_storage_provider = self.tc_inputs.get('cloudStorageProvider', None)
        return self._cloud_storage_provider

    @cloud_storage_provider.setter
    def cloud_storage_provider(self, value):
        """
        cloud provider during library creation
        Args:
            value: (str) option to select cloud provider
        """
        self._cloud_storage_provider = value

    @property
    def secondary_cloud_storage_provider(self):
        """
        Cloud provider during secondary library creation
        Returns:
            (str) option to select secondary cloud provider
        """
        if not self._secondary_cloud_storage_provider:
            self._secondary_cloud_storage_provider = self.tc_inputs.get('secondaryCloudStorageProvider', None)
        return self._secondary_cloud_storage_provider

    @secondary_cloud_storage_provider.setter
    def secondary_cloud_storage_provider(self, value):
        """
        Cloud provider during secondary library creation
        Args:
            value: (str) option to select secondary cloud provider
        """
        self._secondary_cloud_storage_provider = value

    @property
    def cloud_storage_tier(self):
        """
        cloud provider during library creation
        Returns:
            (str) option to select cloud tier
        """
        if not self._cloud_storage_tier:
            self._cloud_storage_tier = self.tc_inputs.get('cloudTier', None)
        return self._cloud_storage_tier

    @cloud_storage_tier.setter
    def cloud_storage_tier(self, value):
        """
        cloud provider during library creation
        Args:
            value: (str) option to select cloud tier
        """
        self._cloud_storage_tier = value

    @property
    def cloud_storage_region(self):
        """
        region to be selected during cloud library creation
        Returns:
            (str) name of the region
        """
        if not self._cloud_storage_region:
            self._cloud_storage_region = self.tc_inputs.get('cloudStorageRegion', None)
        return self._cloud_storage_region

    @cloud_storage_region.setter
    def cloud_storage_region(self, value):
        """
        region to be selected during cloud library creation
        Args:
            value: (str) name of the region
        """
        self._cloud_storage_region = value

    @property
    def secondary_cloud_storage_region(self):
        """
        Region to be selected during secondary cloud library creation
        Returns:
            (str) name of the region
        """
        if not self._secondary_cloud_storage_region:
            self._secondary_cloud_storage_region = self.tc_inputs.get('secondaryCloudStorageRegion', None)
        return self._secondary_cloud_storage_region

    @secondary_cloud_storage_region.setter
    def secondary_cloud_storage_region(self, value):
        """
        Region to be selected during secondary cloud library creation
        Args:
            value: (str) name of the region
        """
        self._secondary_cloud_storage_region = value

    @property
    def storage_credential_name(self):
        """
        Name for the credentials used for creating a new storage.

        Returns:
            (str) name of the region
        """
        if not self._storage_credential_name:
            self._storage_credential_name = self.tc_inputs.get('storageCredentialName', None)
        return self._storage_credential_name

    @storage_credential_name.setter
    def storage_credential_name(self, value):
        """
        Name for the credentials used for creating a new storage.

        Args:
            value: (str) name of the region
        """
        self._storage_credential_name = value

    @property
    def secondary_storage_credential_name(self):
        """
        Name for the credentials used for creating a new secondary storage.

        Returns:
            (str) name of the credential
        """
        if not self._secondary_storage_credential_name:
            self._secondary_storage_credential_name = self.tc_inputs.get('secondaryStorageCredentialName', None)
        return self._secondary_storage_credential_name

    @secondary_storage_credential_name.setter
    def secondary_storage_credential_name(self, value):
        """
        Name for the credentials used for creating a new secondary storage.

        Args:
            value: (str) name of the credential
        """
        self._secondary_storage_credential_name = value

    @property
    def storage_credential_account(self):
        """
        Name for the credentials used for creating a new storage.

        Returns:
            (str) name of the region
        """
        if not self._storage_credential_account:
            self._storage_credential_account = self.tc_inputs.get('storageCredentialAccount', None)
        return self._storage_credential_account

    @storage_credential_account.setter
    def storage_credential_account(self, value):
        """
        Name for the credentials used for creating a new storage.

        Args:
            value: (str) name of the region
        """
        self._storage_credential_account = value

    @property
    def secondary_storage_credential_account(self):
        """
        Storage credential account used for creating a new secondary storage.

        Returns:
            (str) name of the credential account
        """
        if not self._secondary_storage_credential_account:
            self._secondary_storage_credential_account = self.tc_inputs.get('secondaryStorageCredentialAccount', None)
        return self._secondary_storage_credential_account

    @secondary_storage_credential_account.setter
    def secondary_storage_credential_account(self, value):
        """
        Storage credential account used for creating a new secondary storage.

        Args:
            value: (str) name of the credential account
        """
        self._secondary_storage_credential_account = value

    @property
    def storage_credential_password(self):
        """
        Name for the credentials used for creating a new storage.

        Returns:
            (str) name of the region
        """
        if not self._storage_credential_password:
            self._storage_credential_password = self.tc_inputs.get('storageCredentialPassword', None)
        return self._storage_credential_password

    @storage_credential_password.setter
    def storage_credential_password(self, value):
        """
        Name for the credentials used for creating a new storage.

        Args:
            value: (str) name of the region
        """
        self._storage_credential_password = value

    @property
    def secondary_storage_credential_password(self):
        """
        Password for the credentials used for creating a new storage.

        Returns:
            (str) Password value
        """
        if not self._secondary_storage_credential_password:
            self._secondary_storage_credential_password = self.tc_inputs.get('secondaryStorageCredentialPassword', None)
        return self._secondary_storage_credential_password

    @secondary_storage_credential_password.setter
    def secondary_storage_credential_password(self, value):
        """
        Password for the credentials used for creating a new storage.

        Args:
            value: (str) Password value
        """
        self._secondary_storage_credential_password = value

    @property
    def cloud_storage_name(self):
        """
        name of the cloud library
        Returns:
            (str)  name of the library
        """
        if not self._cloud_storage_name:
            self._cloud_storage_name = self.tc_inputs.get('newCloudLibName', None)
        return self._cloud_storage_name

    @cloud_storage_name.setter
    def cloud_storage_name(self, value):
        """
        name of the cloud library
        Args:
            value: (str) name of the library
        """
        self._cloud_storage_name = value

    @property
    def nw_storage_uname(self):
        """
        username for the network storage machine
        Returns:
            (str) username for the network storage machine
        """
        if not self._nw_storage_uname:
            self._nw_storage_uname = self.tc_inputs.get('nwStorageUname', None)
        return self._nw_storage_uname

    @nw_storage_uname.setter
    def nw_storage_uname(self, value):
        """
        username for the network storage machine
        Args:
            value: (str) username of the machine
        """
        self._nw_storage_uname = value

    @property
    def nw_storage_pwd(self):
        """
        password for the network storage machine
        Returns:
            (str) password of the network storage machine
        """
        if not self._nw_storage_pwd:
            self._nw_storage_pwd = self.tc_inputs.get('nwStoragePwd', None)
        return self._nw_storage_pwd

    @nw_storage_pwd.setter
    def nw_storage_pwd(self, value):
        """
        password for the network storage machine
        Args:
            value: (str) password of the network storage machine
        """
        self._nw_storage_pwd = value

    @property
    def new_storage_name(self):
        """
        name of the newly created storage
        Returns:
            (str) name of the storage
        """
        if not self._new_storage_name:
            self._new_storage_name = self.tc_inputs.get('newStorageName', None)
        return self._new_storage_name

    @new_storage_name.setter
    def new_storage_name(self, value):
        """
        name of the storage to be created
        Args:
            value: (str) name of the storage
        """
        self._new_storage_name = value

    @property
    def storage_target_type(self):
        """
        storage target type , either to cloud or disk
        Returns:
            (str) storage target type
        """
        if not self._storage_target_type:
            self._storage_target_type = self.tc_inputs.get('storageTargetType', 'Disk location')
        return self._storage_target_type

    @storage_target_type.setter
    def storage_target_type(self, value):
        """
        storage target type
        Args:
            value: (str) storage target type
        """
        self._storage_target_type = value

    @property
    def storage_backup_gateway(self):
        """
        name of the backup gateway to be used during backup gateway
        Returns:
            (str) backup gateway for storage
        """
        if not self._storage_backup_gateway:
            self._storage_backup_gateway = self.tc_inputs.get('storageBackupGateway', None)
        return self._storage_backup_gateway

    @storage_backup_gateway.setter
    def storage_backup_gateway(self, value):
        """
        name of the backup gateway used during backup to this storage
        Args:
            value: (str) backup gateway during backup to this storage
        """
        self._storage_backup_gateway = value

    @property
    def existing_storage(self):
        """
        name of the existing storage
        Returns:
            (str) select existing storage name
        """
        if not self._existing_storage:
            self._existing_storage = self.tc_inputs.get('optExistingStorage', None)
        return self._existing_storage

    @existing_storage.setter
    def existing_storage(self, value):
        """
        name of the existing storage
        Args:
            value: (str) name of the existing storage
        """
        self._existing_storage = value

    @property
    def existing_hypervisor(self):
        """
        name of the existing hypervisor
        Returns:
            (str) select existing hypervisor name
        """
        if not self._existing_hypervisor:
            self._existing_hypervisor = self.tc_inputs.get('optExistinghypervisor', None)
        return self._existing_hypervisor

    @existing_hypervisor.setter
    def existing_hypervisor(self, value):
        """
        name of the existing hypervisor
        Args:
            value: (str) name of the existing hypervisor
        """
        self._existing_hypervisor = value

    @property
    def hyp_client_name(self):
        """
        name of the hypervisor client on the CS
        Returns:
            (str) hypervisor name
        """
        if not self._hyp_client_name:
            self._hyp_client_name = self.tc_inputs.get('hyp_client_name', None)
        return self._hyp_client_name

    @hyp_client_name.setter
    def hyp_client_name(self, value):
        """
        name of the hypervisor client on the CS
        Args:
            value: (str) name of the hypervisor client
        """
        self._hyp_client_name = value

    @property
    def hyp_host_name(self):
        """
        hostname of the hypervisor client machine
        Returns:
            (str) hostname of the hypervisor
        """
        if not self._hyp_host_name:
            self._hyp_host_name = self.tc_inputs.get('hyp_host_name')
        return self._hyp_host_name

    @hyp_host_name.setter
    def hyp_host_name(self, value):
        """
        hostname of the hypervisor client machine
        Args:
            value: (str) host name of the hypervisor client machine
        """
        self._hyp_host_name = value

    @property
    def hyp_user_name(self):
        """
        username of the hypervisor client machine
        Returns:
            (str) username of the hypervisor client machine
        """
        if not self._hyp_user_name:
            self._hyp_user_name = self.tc_inputs.get('hyp_user_name', None)
        return self._hyp_user_name

    @hyp_user_name.setter
    def hyp_user_name(self, value):
        """
        username of the hypervisor client machine
        Args:
            value: (str) username of the hypervisor
        """
        self._hyp_user_name = value

    @property
    def hyp_pwd(self):
        """
        password for the hypervisor host machine
        Returns:
            (str) password for the hypervisor host machine
        """
        if not self._hyp_pwd:
            self._hyp_pwd = self.tc_inputs.get('hyp_pwd', None)
        return self._hyp_pwd

    @hyp_pwd.setter
    def hyp_pwd(self, value):
        """
        password for the hypervisor client machine
        Args:
            value: (str) password
        """
        self._hyp_pwd = value

    @property
    def hyp_credential_name(self):
        """
        password for the hypervisor host machine
        Returns:
            (str) password for the hypervisor host machine
        """
        if not self._hyp_credential_name:
            self._hyp_credential_name = self.tc_inputs.get('hypCredentialName', None)
        return self._hyp_credential_name

    @hyp_credential_name.setter
    def hyp_credential_name(self, value):
        """
        password for the hypervisor client machine
        Args:
            value: (str) password
        """
        self._hyp_credential_name = value

    @property
    def existing_hypervisor(self):
        """
        password for the hypervisor host machine
        Returns:
            (str) password for the hypervisor host machine
        """
        if not self._existing_hypervisor:
            self._existing_hypervisor = self.tc_inputs.get('existingHypervisor', None)
        return self._existing_hypervisor

    @existing_hypervisor.setter
    def existing_hypervisor(self, value):
        """
        password for the hypervisor client machine
        Args:
            value: (str) password
        """
        self._existing_hypervisor = value

    @property
    def backup_gateway(self):
        """
        backup gateway for performing backup (proxy)
        Returns:
            (str) backup gateway name
        """
        if not self._backup_gateway:
            self.backup_gateway = self.tc_inputs.get('optExistingGateway')
        return self._backup_gateway

    @backup_gateway.setter
    def backup_gateway(self, value):
        """
        set the backup gateway
        Args:
            value: (str) backup gateway name
        """
        self._backup_gateway = value

    @property
    def content_list(self):
        """
        content for the subclient content
        Returns:
            (list) list of the vms or other type based on content type selected
            read only property
        """
        if not self._content_list:
            self._content_list = self.tc_inputs.get('contentList', None)
            if self._content_list and not isinstance(self._content_list, list):
                self._content_list = self._content_list.split(',')
        return self._content_list

    @property
    def tenant_content_list(self):
        """
        tenant account content for the subclient content for cross account configuration
        Returns:
            (list) list of the vms or other type based on content type selected
            read only property
        """
        if not self._tenant_content_list:
            self._tenant_content_list = self.tc_inputs.get('tenant_content_list', None)
            if self._tenant_content_list and not isinstance(self._tenant_content_list, list):
                self._tenant_content_list = self._tenant_content_list.split(',')
        return self._tenant_content_list

    @tenant_content_list.setter
    def tenant_content_list(self, value):
        """
        sets the tenant account content list for cross account configuraiton
        Args:
            value: (list) list of items in subclient content

        Returns:

        """
        self._tenant_content_list = value

    @content_list.setter
    def content_list(self, value):
        """
        content to be used for subclient content
        Args:
            value: (list) list of items in subclient content
        """
        self._content_list = value

    @property
    def content_type(self):
        """
        type of content for the subclient (eg vms or datastores .. )
        Returns:
            (str) content type   (eg vms, datastores etc)
            read only attribute
        """
        if not self._content_type:
            self._content_type = self.tc_inputs.get('contentType', None)
        return self._content_type

    @content_type.setter
    def content_type(self, value):
        """
        sets the content type for subclient content
        Args:
            value : (str) type of content (eg vms , datastores etc)
        """
        self._content_type = value

    @property
    def content_category(self):
        """
        category of content for the subclient (Content / Rule )
        Returns:
            (str) content category   (Content/ Rule)
            read only attribute
        """
        if not self._content_category:
            self._content_category = self.tc_inputs.get('contentCategory', 'Content')
        return self._content_category

    @content_category.setter
    def content_category(self, value):
        """
        sets the content type for subclient content
        Args:
            value : (str) type of content (eg vms , datastores etc)
        """
        self._content_category = value

    @property
    def secondary_storage_cloud(self):
        """
        Specify option if secondary cloud storage has to be selected/created
        """
        if not self._secondary_storage_cloud:
            self._secondary_storage_cloud = self.tc_inputs.get('secondaryStorageCloud', False)
        return self._secondary_storage_cloud

    @secondary_storage_cloud.setter
    def secondary_storage_cloud(self, value):
        """
        Specify option if secondary cloud storage has to be selected/created
        """
        self._secondary_storage_cloud = value

    @property
    def existing_secondary_cloud(self):
        """
        Name of existing secondary cloud storage
        """
        if not self._existing_secondary_cloud:
            self._existing_secondary_cloud = self.tc_inputs.get('existingSecondaryCloud', False)
        return self._existing_secondary_cloud

    @existing_secondary_cloud.setter
    def existing_secondary_cloud(self, value):
        """
        Name of existing secondary cloud storage
        """
        self._existing_secondary_cloud = value

    @property
    def return_to_hub(self):
        """
        Option to return to hub in summary page
        """
        if not self._return_to_hub:
            self._return_to_hub = self.tc_inputs.get('returnToHub', False)
        return self._return_to_hub

    @return_to_hub.setter
    def return_to_hub(self, value):
        """
        Option to return to hub in summary page
        """
        self._return_to_hub = value

    @property
    def keep_only_on_premise(self):
        """
        To skip cloud storage selection
        """
        if not self._keep_only_on_premise:
            self._keep_only_on_premise = self.tc_inputs.get('keepOnlyOnPremise', False)
        return self._keep_only_on_premise

    @keep_only_on_premise.setter
    def keep_only_on_premise(self, value):
        """
        Option to return to hub in summary page
        """
        self._keep_only_on_premise = value

    @property
    def k8s_deployment_method(self):
        """
        Option to return to hub in summary page
        """
        if not self._k8s_deployment_method:
            self._k8s_deployment_method = self.tc_inputs.get('k8sDeploymentMethod', None)
        return self._k8s_deployment_method

    @k8s_deployment_method.setter
    def k8s_deployment_method(self, value):
        """
        Option to return to hub in summary page
        """
        self._k8s_deployment_method = value

    @property
    def skip_cloud_storage(self):
        """
        get the value to check if we need to skip cloud storage and use only on-premise storage
        Returns:
            (boolean) whether to skip cloud storage or not
        """
        if not self._skip_cloud_storage:
            self._skip_cloud_storage = self.tc_inputs.get("_skip_cloud_storage", None)
        return self._skip_cloud_storage

    @skip_cloud_storage.setter
    def skip_cloud_storage(self, value):
        """
        set it to true, to skip cloud storage and use only on-premise storage
        Args:
            value: (boolean)

        Returns:
            None
        """
        self._skip_cloud_storage = value

class VSAWebRestoreOptions(ABC):
    """
    abstract class that has common restore options
    for all vsa hypervisors
    """
    def __init__(self):

        # extra options
        self.end_user = False

        # Destination Page options
        self.restore_type = 'Out of place'
        self.restore_as = None
        self.destination_hypervisor = None
        self.access_node = 'Automatic'
        self.different_vcenter = False

        # virtual machine page options
        self.suffix = ''
        self.prefix = 'del'

        # Restore Options page options
        self.power_on_after_restore = True
        self.unconditional_overwrite = True
        self.reuse_existing_vm_client = False
        self.notify_on_job_completion = False
        self.extension_restore_policy = None
        super(VSAWebRestoreOptions, self).__init__()


class VMwareWebRestoreOptions(VSAWebRestoreOptions):
    """
    class for vmware specific restore options
    overwrite default options in parent class as required
    """
    def __init__(self):
        super(VMwareWebRestoreOptions, self).__init__()
        self.type = HypervisorDisplayName.VIRTUAL_CENTER
        self.restore_as = HypervisorDisplayName.VIRTUAL_CENTER

        #virtual_machine options
        self.vm_info = None

        #Restore Options page options
        self.generate_new_guid = False
        self.transport_mode = 'Auto'
        self.disk_provisioning = 'Original'
        self.use_live_recovery = False
        self.live_recovery_datastore = None
        self.live_recovery_delay_migration = None


class AlicloudWebRestoreOptions(VSAWebRestoreOptions):
    """
    class for alibaba cloud specific restore options
    overwrite default options in parent class as required
    """
    def __init__(self):
        super(AlicloudWebRestoreOptions, self).__init__()
        self.type = HypervisorDisplayName.Alibaba_Cloud
        #virtual machine options
        self.vm_info = None


class VCloudWebRestoreOptions(VSAWebRestoreOptions):
    """
    vCloud restore options, will overwrite options in parent class.
    """

    def __init__(self, init_data=None):
        super(VCloudWebRestoreOptions, self).__init__()
        if init_data is None:
            init_data = {}
        self.restore_as = HypervisorDisplayName.Vcloud.value
        self.type = HypervisorDisplayName.Vcloud.value
        for key in init_data.keys():
            setattr(self, key, init_data[key])


class AWSWebRestoreOptions(VSAWebRestoreOptions):
    """
    class for alibaba cloud specific restore options
    overwrite default options in parent class as required
    """
    def __init__(self):
        super(AWSWebRestoreOptions, self).__init__()
        self.type = HypervisorDisplayName.AMAZON_AWS
        #virtual machine options
        self.vm_info = None
        self.transport_mode = 'Auto'

class GCPWebRestoreOptions(VSAWebRestoreOptions):
    """
    Class for GCP specific restore options
    Overwrite default options in parent class as required
    """

    def __init__(self):
        super(GCPWebRestoreOptions, self).__init__()
        self.type = HypervisorDisplayName.Google_Cloud
        self.restore_as = HypervisorDisplayName.Google_Cloud
        self.zone_name = None
        self.project_id_name = None
        self.vm_info = None
        self.instance_subnet = None
        self.instance_network = None

class OCIWebRestoreOptions(VSAWebRestoreOptions):
    """
    class for alibaba cloud specific restore options
    overwrite default options in parent class as required
    """
    def __init__(self):
        super(OCIWebRestoreOptions, self).__init__()
        self.type = HypervisorDisplayName.ORACLE_CLOUD_INFRASTRUCTURE
        self.restore_as = "Oracle Cloud Infrastructure"

        #virtual machine options
        self.vm_info = None
        self.region = None

class AzureWebRestoreOptions(VSAWebRestoreOptions):
    """
    class for azure specific restore options
    overwrite default options in parent class as required
    """
    def __init__(self):
        super(AzureWebRestoreOptions, self).__init__()
        self.type = HypervisorDisplayName.MICROSOFT_AZURE
        self.restore_as = "Azure Resource Manager"

        #virtual_machine options
        self.vm_info = None


class HVWebRestoreOptions(VSAWebRestoreOptions):
    """
        class for alibaba cloud specific restore options
        overwrite default options in parent class as required
        """

    def __init__(self):
        super(HVWebRestoreOptions, self).__init__()
        self.type = HypervisorDisplayName.MS_VIRTUAL_SERVER
        # virtual machine options
        self.vm_info = None
        self.use_live_recovery = False
        self.generate_new_guid = True
        self.disk_provisioning = "Auto"
class XenWebRestoreOptions(VSAWebRestoreOptions):
    """
    class for xenserver specific restore options
    overwrite default options in parent class as required
    """
    def __init__(self):
        super(XenWebRestoreOptions, self).__init__()
        self.type = HypervisorDisplayName.XEN_SERVER
        self.restore_as = HypervisorDisplayName.XEN_SERVER.value

        #virtual_machine options
        self.vm_info = None


class FusionComputeWebRestoreOptions(VSAWebRestoreOptions):
    """
    Class for FusionCompute specific restore options. 
    Overwrites default optins in parent class as required.
    """
    def __init__(self, init_data={}):
        super(FusionComputeWebRestoreOptions, self).__init__()
        self.type = HypervisorDisplayName.FUSIONCOMPUTE
        for key in init_data.keys():
            setattr(self, key, init_data[key])


class NutanixAHVWebRestoreOptions(VSAWebRestoreOptions):
    """
        class for nutanix ahv specific restore options
        overwrite default options in parent class as required
        """

    def __init__(self):
        super(NutanixAHVWebRestoreOptions, self).__init__()
        self.type = HypervisorDisplayName.Nutanix
        # virtual machine options
        self.vm_info = None
        self.generate_new_guid = True
        self.restore_network = None
        self.storage_container = None
