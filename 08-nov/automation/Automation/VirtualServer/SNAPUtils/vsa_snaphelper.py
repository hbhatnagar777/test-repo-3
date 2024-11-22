# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" VSA Snap Helper

classes defined:
    VSASNAPHelper   - wrapper for Snap operations

    VSASNAPHelper:
         __init__()                   --  initializes Snap Helper object


        add_array()                   --  adds array to the array management

        edit_array()                  --  edits the array for snap configs and array access controllers

        delete_array()                -- deletes the array entry from array management

        add_primary_array()             -- adds primary array to the array management

        add_secondary_array()           -- adds secondary array to the array management

        run_aux_copy()                -- run aux copy at storage policy

        run_backup_copy()             -- run backup copy at storage policy

        update_storage_policy()       -- Update storage policy with backup copy
                                         and snapshot catalog options

        delete_bkpcpy_schedule()      -- delete Backup copy schedule

        spcopy_obj()                  -- create storage policy copy object

        snap_operations()             -- Method to run Snap operations

        mount_snap()                  -- Mount a Snapshot

        unmount_snap()                -- Unmount a snapshot

        delete_snap()                 -- deletes a snapshot

        force_delete_snap()           -- force deletes a snapshot

        validate_transport_mode()     -- validate transport mode for backup copy

        unique_control_host()         -- returns the unique control hosts involved in a snap job

        multinode_config()            -- Verify multinode setup configuration

        multinode_verification()      -- verifies multinode intellisnap backup copy

        metro_verification()          -- verifies metro configuration for supported vendors

"""

from __future__ import unicode_literals

import time
from AutomationUtils import logger
from base64 import b64encode
from AutomationUtils.idautils import CommonUtils
from VirtualServer.VSAUtils import VirtualServerUtils


class VSASNAPHelper(object):
    """
    class that act as wrapper for SDK and Testcase

    """

    def __init__(self, commcell, tcinputs, vsa_snapconstants):
        """
        Initialize the  SDK objects

        Args:
            commcell    (obj)   - Commcell object of SDK Commcell class

            csdb        (obj)   - CS Database object from testcase

        """

        self.log = logger.get_log()
        self.commcell = commcell
        self.tcinputs = tcinputs
        self.vsa_snapconstants = vsa_snapconstants
        self.common_utils = CommonUtils(commcell)
        self.schedules = self.commcell.schedules
        self.storage_policy_obj = self.commcell.storage_policies.get(
            self.vsa_snapconstants.auto_subclient.storage_policy)

    def add_array(self, array_vendor_name=None,
                  arrayname=None,
                  username=None,
                  password=None,
                  snap_configs=None,
                  controlhost=None,
                  array_access_nodes_to_add=None,
                  is_ocum=None):
        """
        Method to add array to the array management

        Args:
            array_vendor_name: Vendor name of the array

            arrayname: array name or array serial number to be added

            username: user name to be used for the array

            password: password used to access the array

            snap_configs: snap configuration to be updated while adding the array

            controlhost: control host name to if applicable to access the array

            array_access_nodes_to_add: name of the array access node or nodes

            is_ocum: to be used if the array type is OCUM and it is specific to Netapp vendor

        """
        try:
            vendor_id = self.vsa_snapconstants.execute_query(
                self.vsa_snapconstants.get_vendor_id, {'a': array_vendor_name}, fetch_rows='one')
            if snap_configs is not None:
                config_data = {}
                for config, value in snap_configs.items():
                    master_config_id = self.vsa_snapconstants.execute_query(
                        self.vsa_snapconstants.get_master_config_id,
                        {'a': config, 'b': array_vendor_name},
                        fetch_rows='one')
                    config_data[master_config_id] = value
            else:
                config_data = None
            self.log.info("Adding array management entry for : {0}".format(arrayname))
            error_message = self.commcell.array_management.add_array(array_vendor_name,
                                                                     arrayname,
                                                                     username,
                                                                     password,
                                                                     vendor_id,
                                                                     config_data,
                                                                     controlhost,
                                                                     array_access_nodes_to_add,
                                                                     is_ocum)
            self.log.info("Successfully added the Array with ControlHost id: {0}".format(error_message))

        except Exception as e:
            if e.exception_id == '101':
                self.log.info("{0}".format(e.exception_message))
            else:
                raise Exception(e)

    def edit_array(self,
                   array_name,
                   snap_configs=None,
                   config_update_level=None,
                   level_id=None,
                   array_access_node=None,
                   gad_arrayname=None):
        """Method to Update Snap Configurations and array access nodes for the given array
        Args:
            array_name              (str)     -- Name of the Array

            snap_configs            (dict)     -- Snap Configs in Dict format
            Ex: {"Mount Retry Interval (in seconds)" : "600", "Array Host Aliases" : {"msconfig1" : "add", "msconfig2" : "delete", "New alias Name" : "Old alias name"}}

            config_update_level     (int)     -- update level for the Snap config
            default: "array"
            other values: "subclient", "copy", "client"

            level_id                (int)     -- level Id where the config needs to be
                                                 added/updated, ex: Subclient, client, copy id's
            default: None

            array_access_node       (dict)    -- Array Access Node MA's in dict format with mode
            default: None
            Ex: {"snapautotest3" : "add", "linuxautomation1" : "add", "snapautofc1" : "delete"}

            gad_arrayname : array name for which snap configs to be updated in case of GAD

        """
        if gad_arrayname is not None:
            control_host_id = self.vsa_snapconstants.execute_query(
                self.vsa_snapconstants.get_gad_controlhost_id, {'a': gad_arrayname,
                                                                'b': array_name}, fetch_rows='one')
        else:
            control_host_id = self.vsa_snapconstants.execute_query(
                self.vsa_snapconstants.get_controlhost_id, {'a': array_name}, fetch_rows='one')
        if snap_configs is not None:
            config_data = {}
            for config, value in snap_configs.items():
                master_config_id = self.vsa_snapconstants.execute_query(
                    self.vsa_snapconstants.get_master_config_id,
                    {'a': config, 'b': self.vsa_snapconstants.array_vendor_name},
                    fetch_rows='one')
                config_data[master_config_id] = value
            self.log.info("Updating the Snap Config: '{0}' on Array: '{1}' at : *{2}* level".format(
                snap_configs, array_name, config_update_level)
                         )
        else:
            config_data = None

        if array_access_node is not None:
            self.log.info("Updating Array Access Nodes :{0}".format(array_access_node))

        self.commcell.array_management.edit_array(control_host_id,
                                                  config_data,
                                                  config_update_level,
                                                  level_id=level_id,
                                                  array_access_node=array_access_node)
        if snap_configs is not None:
            self.log.info("Successfully Updated Snap Configs: '{0}' on Array: '{1}'at : *{2}* level".format(
                snap_configs, array_name, config_update_level)
                         )
        if array_access_node is not None:
            self.log.info("Successfully Updated Array Access Nodes :{0}".format(array_access_node))

    def delete_array(self, arrayname):
        """
        Method to Delete the array management entry

        Args:
            arrayname: name of the array to be deleted

        """
        try:
            self.log.info("Deleting the array management entry : {0}".format(
                arrayname))
            control_host_array = self.vsa_snapconstants.execute_query(
                self.vsa_snapconstants.get_controlhost_id, {'a': arrayname},
                fetch_rows='one')
            if control_host_array in [None, ' ', '']:
                self.log.info("""Array Management entry Not found in the database, """
                              """Treating this as Soft Failure""")
            else:
                error_message = self.commcell.array_management.delete_array(control_host_array)
                self.log.info("{0}".format(error_message))

        except Exception as e:
            if e.exception_id == '103':
                self.log.info("{0}".format(e.exception_message))
                self.log.info("Treating this as Soft failure")
            else:
                raise Exception(e)

    def add_primary_array(self):
        """

        Adds Primary array in the array management based on vendor information provided

        """

        VirtualServerUtils.decorative_log("Adding primary array entry for array {}".format(
            self.tcinputs.get('ArrayVendorName')))
        self.add_array(self.tcinputs.get('ArrayVendorName'),
                       self.tcinputs.get('ArrayName'),
                       self.tcinputs.get('ArrayUserName'),
                       b64encode(self.tcinputs.get('ArrayPassword').encode()).decode(),
                       self.vsa_snapconstants.source_config_add_array,
                       self.tcinputs.get('ArrayControlHost', None),
                       self.tcinputs.get('array_access_nodes_to_edit_array', None),
                       self.tcinputs.get('is_ocum', None))

    def add_secondary_array(self):
        """

        Adds secondary array needed for the replication backup to the array management

        """

        VirtualServerUtils.decorative_log("Adding secondary Array entry for array {}".format(
            self.tcinputs.get('ArrayVendorName')))
        self.add_array(self.tcinputs.get('ArrayVendorName'),
                       self.tcinputs.get('ArrayName2'),
                       self.tcinputs.get('ArrayUserName2'),
                       b64encode(self.tcinputs.get('ArrayPassword2').encode()).decode(),
                       self.vsa_snapconstants.source_config_add_array,
                       self.tcinputs.get('ArrayControlHost2', None),
                       self.tcinputs.get('array_access_nodes_to_edit_array', None),
                       self.tcinputs.get('is_ocum', None))

    def run_aux_copy(self, copy_name=None):
        """
        Runs Auxilliary copy for the given storage policy and copy
            Args:
                copy_name       (str)       -- Copy name for which aux copy needs to be run
                default: None

        """

        if self.vsa_snapconstants.ocum_server is None:
            _use_scale = True
        else:
            _use_scale = False

        VirtualServerUtils.decorative_log('Running Aux Copy')
        if copy_name is not None:
            _auxcopy_job = self.storage_policy_obj.run_aux_copy(
                copy_name, use_scale=_use_scale)
        else:
            _auxcopy_job = self.storage_policy_obj.run_aux_copy(use_scale=_use_scale)
        self.log.info("Started Aux copy job with job id: " + str(_auxcopy_job.job_id))

        if not _auxcopy_job.wait_for_completion():
            raise Exception(
                "Failed to run Aux Copy with error: " +
                str(_auxcopy_job.delay_reason)
            )
        if _auxcopy_job.status.lower() != 'completed':
            raise Exception(
                "Aux Copy Job completed with errors, Reason " +
                str(_auxcopy_job.delay_reason)
            )
        self.log.info(f'Aux Copy Job {_auxcopy_job.job_id} Completed Successfully')

    def run_backup_copy(self, metro_verify=False, multinode_verify=False, ctrlhost_array=None, snap_job_id=None):
        """
        Run Offline Backup copy on the storage policy

        Args:
            metro_verify    (bool): specifies if metro mount verification is needed or not

            multinode_verify (bool): specifies if multinode mount verification is needed or not

            ctrlhost_array  (list): control host of the primary or secondary array

            snap_job_id     (int) : snap job id which is getting mounted

        """

        VirtualServerUtils.decorative_log("Backup Copy")
        _backup_copy_job = self.storage_policy_obj.run_backup_copy()
        self.log.info(f'Started Backup Copy WF Job {_backup_copy_job.job_id}')

        if multinode_verify:
            self.multinode_verification(_backup_copy_job, snap_job_id)

        if metro_verify:
            self.metro_verification(_backup_copy_job, snap_job_id, ctrlhost_array)

        if not _backup_copy_job.wait_for_completion():
            raise Exception(
                "Failed to run Backup Copy with error : " +
                str(_backup_copy_job.delay_reason)
            )
        if _backup_copy_job.status.lower() != 'completed':
            raise Exception(
                "Backup Copy Job completed with errors, Reason " +
                str(_backup_copy_job.delay_reason)
            )

        self.vsa_snapconstants.auto_subclient.backupcopy_job_id = self.common_utils.get_backup_copy_job_id(
            self.vsa_snapconstants.auto_subclient.backup_job.job_id)
        self.log.info(f'Backup Copy job  {_backup_copy_job} successfully completed')

    def update_storage_policy(self,
                              source_copy_precedence_for_bkpcopy=None,
                              source_copy_precedence_for_catalog=None):
        """
        Update Storage policy snapshot options
        Agrs:
            source_copy_precedence_for_bkpcopy  (int)   source copy precedence for backup copy

            source_copy_precedence_for_catalog  (int)   source copy precedence for Catalog

            """

        if source_copy_precedence_for_bkpcopy is None:
            source_copy_precedence_for_bkpcopy = 1
        if source_copy_precedence_for_catalog is None:
            source_copy_precedence_for_catalog = 1

        if self.vsa_snapconstants.ocum_server is None:
            _is_ocum = False
        else:
            _is_ocum = True

        VirtualServerUtils.decorative_log("Updating storage policy Options")
        for copy_name, copy_property in self.storage_policy_obj.copies.items():
            for _property in copy_property:
                if _property == 'copyPrecedence' and copy_property[_property] not in [1, 2]:
                    self.vsa_snapconstants.secondary_copies.append(copy_property[_property])
                if copy_property[_property] == source_copy_precedence_for_bkpcopy:
                    source_copy_name_for_bkpcopy = copy_name
                if copy_property[_property] == source_copy_precedence_for_catalog:
                    source_copy_name_for_catalog = copy_name

        options = {
            'enable_backup_copy': True,
            'source_copy_for_snap_to_tape': source_copy_name_for_bkpcopy,
            'enable_snapshot_catalog': False,
            'source_copy_for_snapshot_catalog': source_copy_name_for_catalog,
            'is_ocum': _is_ocum,
            'disassociate_sc_from_backup_copy': None
        }

        self.storage_policy_obj.update_snapshot_options(**options)

    def delete_bkpcpy_schedule(self):
        """delete backup copy schedule as it interferes with the test case flow"""

        self.schedules.refresh()
        schedule_name = self.storage_policy_obj.storage_policy_name + ' snap copy'
        if self.schedules.has_schedule(schedule_name):
            self.log.info("Deleting backup copy schedule :{0}".format(schedule_name))
            self.schedules.delete(schedule_name)
            self.log.info("Successfully Deleted backup copy schedule :{0}".format(schedule_name))
        else:
            self.log.info("Schedule with name: {0} does not exists".format(schedule_name))

    def spcopy_obj(self, copy_precedence):
        """ Create storage Policy Copy object
        Arg:
            copy_precedence        (int)         -- Copy precedence of copy
        Return:
            object  --  storage policy copy object
        """

        for name, copy_property in self.storage_policy_obj.copies.items():
            for _property in copy_property:
                if _property == 'copyPrecedence' and copy_property[_property] == int(copy_precedence):
                    copy_name = name
        spcopy = self.storage_policy_obj.get_copy(copy_name)
        return spcopy

    def snap_operations(self, jobid, copy_id, mode, client_name=None, mountpath=None,
                        do_vssprotection=True, user_credentials=None, server_name=None,
                        instance_details=None):
        """ Common Method for Snap Operations
            Args :
                jobid             (int)  : jobid for the Snap operation

                copy_id           (int)  : copy id from which the snap operations needs to be done

                client_name       (str)  : name of the destination client, default: None

                MountPath         (str)  : MountPath for Snap operation, default: None

                do_vssprotection  (bool) : enable vss protection snap during mount

                mode              (str)  : mode can be mount,unmount,force_unmount,delete,force_delete,
                                           revert,reconcile

                user_credentials  (dict) : dict containing userName of vcenter

                server_name       (str)  : vcenter name

                instance_details  (dict) : dict containing apptypeId, InstanceId, InstanceName

            Return :
                object : Job object of Snap Operation job
        """

        self.log.info("Getting SMVolumeId using JobId: {0} and Copy id: {1}".format(
            jobid, copy_id))
        volumeid = self.vsa_snapconstants.execute_query(self.vsa_snapconstants.get_volume_id,
                                                        {'a': jobid, 'b': copy_id})
        self.log.info("SMvolumeId is : {0}".format(volumeid))
        self.log.info("destination client name is :{0}".format(client_name))
        self.log.info("mountpath is {0}".format(mountpath))
        if volumeid[0][0] in [None, ' ', '']:
            if mode in ['mount', 'unmount', 'force_unmount', 'revert']:
                raise Exception("VolumeID is Empty, Looks like it is deleted or never been\
                                created, Cannot proceed with Snap operation")
            elif mode in ['delete', 'force_delete']:
                self.log.info("VolumeID is Empty, Looks like it is already deleted,\
                              treating it as soft failure")
        else:
            if mode == 'mount':
                job = self.commcell.array_management.mount(volumeid,
                                                           client_name,
                                                           mountpath,
                                                           do_vssprotection,
                                                           user_credentials,
                                                           server_name,
                                                           instance_details)
            elif mode == 'unmount':
                job = self.commcell.array_management.unmount(volumeid)
            elif mode == 'force_unmount':
                job = self.commcell.array_management.force_unmount(volumeid)
            elif mode == 'revert':
                job = self.commcell.array_management.revert(volumeid)
            elif mode == 'delete':
                job = self.commcell.array_management.delete(volumeid)
            elif mode == 'force_delete':
                job = self.commcell.array_management.force_delete(volumeid)
            else:
                raise Exception("Failed to get Snap Operation Type")

            self.log.info("Started  job: {0} for Snap Operation".format(job.job_id))
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run job: {0} for Snap operation with error: {1}".format(
                        job.job_id, job.delay_reason)
                )
            if job.status.lower() != 'completed':
                raise Exception(
                    "job: {0} for snap operation is completed with errors, Reason: {1}".format(
                        job.job_id, job.delay_reason)
                )
            self.log.info("successfully completed Snap operation of jobid :{0}".format(
                job.job_id))
            time.sleep(30)
            return job

    def mount_snap(self, jobid, copy_precedence, do_vssprotection=False,
                   user_credentials=None, server_name=None, instance_details=None):
        """ Mounts Snap of the given jobid
            Args:
                jobid               (int)   : jobid for mount operation

                copy_precedence     (int)   : copy precedence

                do_vssprotection    (bool)  : Performs VSS protected mount

                user_credentials    (dict)  : dict containing userName of vcenter

                server_name         (str)   : vcenter name

                instance_details    (dict)  : dict containing apptypeId, InstanceId, InstanceName

            Return:
                object              : job object of Snap operation job
        """

        if server_name is None:
            server_name = self.tcinputs.get('VcenterName', None)
        if user_credentials is None:
            user_credentials = {
                "userName":self.tcinputs.get('VcenterUserName', None)
                }
        if instance_details is None:
            instance_details = {
                "apptypeId": int(self.vsa_snapconstants.auto_instance.vsa_agent._agent_id),
                "instanceId": int(self.vsa_snapconstants.auto_instance.vsa_instance_id),
                "instanceName": self.vsa_snapconstants.auto_instance.vsa_instance_name
                }
        spcopy = self.spcopy_obj(copy_precedence)
        self.log.info("Mounting snapshot of jobid : {0} from Copy: {1}".format(jobid, spcopy._copy_name))
        return self.snap_operations(jobid,
                                    spcopy.copy_id, mode='mount',
                                    client_name=self.tcinputs.get('mount_ma', None),
                                    mountpath=self.tcinputs.get('Host', None),
                                    do_vssprotection=do_vssprotection,
                                    user_credentials=user_credentials,
                                    server_name=server_name,
                                    instance_details=instance_details)

    def unmount_snap(self, jobid, copy_precedence):
        """ UnMounts Snap of the given jobid
            Args:
                jobid               (int)   : jobid for mount operation

                copy_precedence     (int)   : copy precedence

            Return:
                object      : job object of Snap operation job
        """
        spcopy = self.spcopy_obj(copy_precedence)
        self.vsa_snapconstants.mountpath_val = self.vsa_snapconstants.execute_query(
            self.vsa_snapconstants.get_mount_path,
            {'a': jobid, 'b': spcopy.copy_id}
        )
        self.log.info("UnMounting snapshot of jobid : {0} from Copy: {1}".format(jobid, spcopy._copy_name))
        return self.snap_operations(jobid, spcopy.copy_id, mode='unmount')

    def delete_snap(self, jobid, copy_precedence, is_mirror=False, source_copy_precedence_for_mirror=False):
        """ Deletes Snap of the given jobid
            Args:
                jobid               (int)   : jobid for mount operation

                copy_precedence     (int)   : copy precedence

                is_mirror           (bool)    : if mirror snap needs to be deleted

                source_copy_precedence_for_mirror  (int) : copy precedence of mirror copy

            Return:
                object : job object of Snap operation job
        """
        if is_mirror:
            spcopy = self.spcopy_obj(source_copy_precedence_for_mirror)
        else:
            spcopy = self.spcopy_obj(copy_precedence)
        self.log.info("Deleting snapshot of jobid : {0} from Copy: {1}".format(
            jobid, spcopy._copy_name))
        return self.snap_operations(jobid, spcopy.copy_id, mode='delete')

    def force_delete_snap(self, jobid, copy_precedence):
        """ Force Deletes Snap of the given jobid
            Args:
                jobid               (int)   : jobid for mount operation

                copy_precedence     (int)   : copy precedence

            Return:
                object      : job object of Snap operation job
        """

        spcopy = self.spcopy_obj(copy_precedence)
        self.log.info("Force Deleting snapshot of jobid : {0} from Copy: {1}".format(
            jobid, spcopy._copy_name))
        return self.snap_operations(jobid, spcopy.copy_id, mode='force_delete')

    def validate_transport_mode(self, transport_mode):
        """ Validate transport mode for backup copy job
            Args:
                transport_mode      (str)   : transport mode for backup copy

            Raises:
                Exception:
                    if transport mode failed to match

        """
        if transport_mode != "":
            self.log.info("Validating if transport mode is {0}".format(transport_mode))
            if transport_mode not in self.vsa_snapconstants.auto_commcell.find_job_transport_mode(
                self.vsa_snapconstants.auto_subclient.backupcopy_job_id):
                raise Exception("Transport mode verification failed")
            else:
                self.log.info(f"Transport mode verification successful for mode: {transport_mode}")
        else:
            self.log.info("Validation of transport mode is not required")

    def unique_control_host(self, job):
        """Method to fetch unique control host for a job
                Args:

                    job                       (object)     --- job id for which unique control hosts to be fetched

                Returns:

                    unique_controlhost_id       (list)  -- unique control host id for the jobid

                """
        controlhost_id = self.vsa_snapconstants.execute_query(
            self.vsa_snapconstants.get_control_host, {'a': job})
        unique_controlhost_id = []
        for ctlhost in controlhost_id:
            if ctlhost not in unique_controlhost_id:
                unique_controlhost_id.append(ctlhost)
        self.log.info(f"Control hosts are {unique_controlhost_id}")
        return unique_controlhost_id

    def multinode_config(self):
        """Verify multinode setup configuration
        """

        if len(self.vsa_snapconstants.auto_subclient.vm_list) < 5:
            raise Exception(
                "Number of source VM are less than 5, Correct the configuration to have "
                "5 source vms atleast for multiNode backup verification..")
        else:
            self.log.info(f"Source VM's added are: {self.vsa_snapconstants.auto_subclient.vm_list}")
        if len(self.vsa_snapconstants.auto_subclient.subclient.subclient_proxy) < 3:
            raise Exception(
                "Number of Proxy MAs are less than 3, Correct the configuration to have "
                "3 proxy MAs atleast for multiNode backup verification..")
        else:
            self.log.info(f"Proxy MA's added are: {self.vsa_snapconstants.auto_subclient.subclient.subclient_proxy}")

    def multinode_verification(self, _backup_copy_job, snap_job_id):
        """Verify vsa multinode backup copy

        Args:
            _backup_copy_job  (int): Parent Backup copy jobid

            snap_job_id     (int) : snap job id which is getting mounted
        """

        time.sleep(15)
        # get parent subclient backup copy job id from work flow job id.
        bkpcopy_job_id = self.vsa_snapconstants.execute_query(self.vsa_snapconstants.get_bkpcopy_parent_jid,
                                                              {'a': _backup_copy_job.job_id,
                                                               'b': snap_job_id})
        self.log.info(f'Parent backup copy Job ID is {bkpcopy_job_id}')
        if _backup_copy_job.status.lower() in ['running', 'waiting', 'queued']:
            wait_time = 0
            hosts = []
            subclient_proxies = len(self.vsa_snapconstants.auto_subclient.subclient.subclient_proxy)
            while True:
                host_ids = self.vsa_snapconstants.execute_query(self.vsa_snapconstants.get_mounthost_id,
                                                                {'a': bkpcopy_job_id[0][0],
                                                                 'b': 59})
                if host_ids[0][0] not in [None, ' ', '']:
                    for i in range(len(host_ids)):
                        if host_ids[i][0] not in hosts:
                            self.log.info(f"*****host id: {host_ids[i][0]} is used for mount*****")
                            hosts.append(host_ids[i][0])
                self.log.info("sleeping for one minute to find more mount proxies")
                time.sleep(60)
                wait_time += 1
                used_proxies = len(hosts)
                if used_proxies == subclient_proxies or _backup_copy_job.status.lower() in ['completed'] or wait_time > 30:
                    self.log.info(f"Number of proxies used are same as defined number of proxies at subclient \n"
                                  f" OR waiting time to find more mount proxies is exhausted, \n"
                                  f" OR the backup copy workflow job is completed , exiting!!")
                    break

            if used_proxies != subclient_proxies:
                raise Exception(
                    "Number of proxies used are *NOT* same as defined number of proxies at subclient, "
                    "failing the multinode verification"
                )
            else:
                self.log.info(
                    f"multinode verification is completed. \n Number of proxies used for "
                    f"backup copy are: {hosts} \n where as the number of proxies added "
                    f" in the subclient content are: {self.vsa_snapconstants.auto_subclient.subclient.subclient_proxy} "
                )

        else:
            raise Exception(
                f'Multinode Verification failed for job {bkpcopy_job_id}'
            )

    def metro_verification(self, _backup_copy_job, snap_job_id, ctrlhost_array):
        """Verify metro config verification
        Args:
            _backup_copy_job  (int): Parent Backup copy jobid

            ctrlhost_array  (list): control host of the primary or secondary array

            snap_job_id     (int) : snap job id which is getting mounted
        """

        time.sleep(15)
        # get parent subclient backup copy job id from work flow job id.
        bkpcopy_job_id = self.vsa_snapconstants.execute_query(self.vsa_snapconstants.get_bkpcopy_parent_jid,
                                                              {'a': _backup_copy_job.job_id,
                                                               'b': snap_job_id})
        self.log.info(f'Parent backup copy Job ID is {bkpcopy_job_id}')
        if _backup_copy_job.status.lower() in ['running', 'waiting', 'queued']:
            wait_time = 0
            while True:
                volumeid = self.vsa_snapconstants.execute_query(self.vsa_snapconstants.get_mountvolume_id,
                                                                {'a': bkpcopy_job_id[0][0],
                                                                 'b': 59})
                if volumeid[0][0] not in [None, ' ', '']:
                    mnt_controlhost_id = self.vsa_snapconstants.execute_query(
                        self.vsa_snapconstants.get_bkpcopy_mount_control_host, {'a': bkpcopy_job_id[0][0]})
                    if ctrlhost_array[0][0] == mnt_controlhost_id[0][0]:
                        self.log.info(
                            f"Snap is mounted from Array {mnt_controlhost_id[0][0]} as expected. "
                            f"let's wait for backup copy to complete.")
                    else:
                        raise Exception(
                            "Snapshot is not mounted from expected Array")
                    break
                else:
                    self.log.info("Snap is not yet mounted. Sleeping for a minute")
                    time.sleep(60)
                    wait_time += 1
                if wait_time > 30:
                    raise Exception(
                        f"Snapshot of jobid: {_backup_copy_job.job_id} is not yet mounted,"
                        "please check the CVMA logs"
                    )
        else:
            raise Exception(
                f'Metro mount Verification failed for job {bkpcopy_job_id}'
            )
