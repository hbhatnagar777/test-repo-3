# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Client Helper

classes defined:
    AutoVSAVSClient   - wrapper for VSA Client operations
"""

import math
import os
import re
import socket
import time
from AutomationUtils.machine import Machine
from VirtualServer.VSAUtils import VirtualServerConstants, VirtualServerUtils
from cvpysdk.job import Job
from cvpysdk.recovery_targets import RecoveryTarget
from AutomationUtils import logger

UTILS_PATH = os.path.dirname(os.path.realpath(__file__))


class AutoVSAVSClient(object):
    """
    Main class for performing all VSClient operations

    Methods:
       enable_snap_on_client - Enable intellisnap on client

    """

    def __init__(self, commcell_obj, client):
        """
        Initialize all the class properties of AutoVSAVSClient class

        Args:
            commcell_obj    (obj)   - object of AutovsaCommcell class of VS Helper

            client  (obj)   - object for Client Class in SDK
        """
        self.log = logger.get_log()
        self.auto_commcell = commcell_obj
        self.csdb = commcell_obj.csdb
        self.vsa_client = client
        if isinstance(self.vsa_client, RecoveryTarget):
            self.vsa_client_name = self.vsa_client.destination_hypervisor
        else:
            self.vsa_client_id = self.vsa_client.client_id
            self.vsa_client_name = self.vsa_client.client_name
        self._vsa_admin_client_id = None
        self._vsa_admin_client_name = None
        self.timestamp = None
        self.rep_target_summary = None
        self.vmpolicy = None
        self.isIndexingV2 = True if self.auto_commcell.is_metallic \
            else self.auto_commcell.check_v2_indexing(self.vsa_client_name)
        self.live_mount_migration = False
        self.backup_folder_name = "FULL"

    @property
    def expiration_time(self):
        if self.vmpolicy is not None and self.vmpolicy.vm_policy_type_id == 13:
            days = int(self.vmpolicy.properties().get('daysRetainUntil') - 1)
            hours = int(self.vmpolicy.properties()['waitBeforeMigrationInHours'])
        elif self.vmpolicy is not None:
            days = int(self.vmpolicy.properties().get('daysRetainUntil', 0))
            hours = int(self.vmpolicy.properties()['minutesRetainUntil'])
        else:
            if 'hours' in self.rep_target_summary['Expiration time']:
                hours = int(self.rep_target_summary['Expiration time'].split()[0])
                days = 0
            else:
                days = int(self.rep_target_summary['Expiration time'].split()[0])
                hours = 0

        expiration_time = hours * 60 * 60  # converting to seconds
        if days > 0:
            expiration_time += days * 24 * 60 * 60  # converting to seconds
        return expiration_time

    @property
    def media_agent_name(self):
        if self.vmpolicy is not None:
            media_agent_name = self.vmpolicy.properties()['mediaAgent']['clientName']
        else:
            media_agent_name = self.rep_target_summary['MediaAgent']
        return media_agent_name

    @property
    def vsa_admin_client_id(self):
        if self._vsa_admin_client_id is None:
            self.fetch_admin_client_properties()
        return self._vsa_admin_client_id

    @property
    def vsa_admin_client_name(self):
        if self._vsa_admin_client_name is None:
            self.fetch_admin_client_properties()
        return self._vsa_admin_client_name

    @property
    def datastore_name(self):
        """
        Returns the datastore name set in the VM policy or the Recovery Target

        Returns:
            ds      (str) : Datastore name
        """
        if self.vmpolicy is not None:
            ds = self.vmpolicy.properties()['dataStores'][0]['dataStoreName']
        else:
            ds = self.rep_target_summary['Datastore']
        return ds

    def fetch_admin_client_properties(self):
        """
        Fetch Amazon admin client ID and name from the database and set them.
        """
        client_id = self.vsa_client_id
        query = """SELECT id, name
        FROM APP_Client 
        WHERE id IN (
            SELECT clientId 
            FROM APP_Application  
            WHERE instance IN (
                SELECT attrVal 
                FROM APP_InstanceProp 
                WHERE componentNameId IN (
                    SELECT instance 
                    FROM APP_Application 
                    WHERE clientId = {}
                ) 
                AND attrName = 'Amazon Admin Instance Id'
            )
        );""".format(client_id)

        self.csdb.execute(query)
        result = self.csdb.fetch_one_row(named_columns=True)

        if result:
            self._vsa_admin_client_id = result[0]['id']
            self._vsa_admin_client_name = result[0]['name']
        else:
            self.log.warning("No rows returned from query.")

    def enable_snap_on_client(self):
        """
        enable intellisnap on agent level

        Exception:
                If failed to update the property
        """
        try:
            self.vsa_client.enable_intelli_snap()
            self.log.info(
                "Success - enabled snap on client: [%s]", self.vsa_client_name)

        except Exception as err:
            self.log.error("Failed Enable Snap on client")
            raise Exception("Exception in EnableSnapOnClient:" + str(err))

    def get_mounted_vm_name(self, source_vm_name):
        if self.vmpolicy is not None:
            mounted_vm_name = self.vmpolicy.live_mounted_vm_name
        else:
            if 'VM display name (Add a prefix to the VM name)' in self.rep_target_summary:
                prefix = ""
                if self.rep_target_summary['VM display name (Add a prefix to the VM name)'] != 'Not set':
                    prefix = self.rep_target_summary['VM display name (Add a prefix to the VM name)']
                mounted_vm_name = prefix + source_vm_name
            else:
                suffix = ""
                if self.rep_target_summary['VM display name (Add a suffix to the VM name)'] != 'Not set':
                    suffix = self.rep_target_summary['VM display name (Add a suffix to the VM name)']
                mounted_vm_name = source_vm_name + suffix
        return mounted_vm_name

    def mounted_vm_validation(self, source_vm_names, mounted_vm_names, source_hvobj, hvobj,
                              rep_target_summary=None, **kwargs):

        """ Validation of Live Mount VM and testdata validation

                    Args:
                        hvobj                   (obj)    --  HypervisorHelper object

                        source_hvobj            (obj)   --  Source HypervisorHelper object

                        source_vm_names          (list)    --  list of source VM name

                        mounted_vm_names      (list)  -- list of mounted VMs

                        rep_target_summary  (dict)   -- dictonary containing information of Replication Target

                        **kwargs                     -- Arbitrary keyword arguments
                    Returns :

                        mounted_datastores      (dict)  -- dict of the datastore for Live mounted VM

                        mounted_machine_vmhelpers      (list)  -- list of objects for mounted vms

                    Exception:
                        if it fails to fine the mounted vm and test data validation.



        """

        VirtualServerUtils.decorative_log("Validations while vm is mounted")
        self.log.info(mounted_vm_names)
        mounted_machine_vmhelpers = []
        mounted_datastores = {}
        for vm_index in range(len(source_vm_names)):
            # 1. check if specified network is being used (before expiry time)
            VirtualServerUtils.decorative_log("Checking if specified network is being used")
            # creating VMHelper object for source and client vm
            self.log.info("Creating VMHelper object for source and mounted VM.")
            source_hvobj.VMs = source_vm_names[vm_index]  # self.vsa_client_name
            hvobj.VMs = mounted_vm_names[vm_index]
            source_machine_vmhelper = source_hvobj.VMs[source_vm_names[vm_index]]  # self.vsa_client_name]
            mounted_machine_vmhelper = hvobj.VMs[mounted_vm_names[vm_index]]
            mounted_machine_vmhelpers.append(mounted_machine_vmhelper)
            mounted_datastores[
                mounted_machine_vmhelper.vm_name] = mounted_machine_vmhelper.datastore
            self.log.info("Updating VMHelper object for source vm:{0} and live mounted VM:{1}"
                          .format(source_vm_names[vm_index], mounted_vm_names[vm_index]))
            source_machine_vmhelper.update_vm_info(prop='All', force_update=True)
            self.log.info(kwargs.get("isolated_network"))
            if not kwargs.get("isolated_network"):
                attempt = 0
                while attempt < 5:
                    time.sleep(120)
                    try:
                        mounted_machine_vmhelper.update_vm_info(prop='All',
                                                                os_info=True, force_update=True)
                        if mounted_machine_vmhelper.ip is None or mounted_machine_vmhelper.ip == "":
                            self.log.info("Attempt number %d failed. "
                                          "Waiting for 2 minutes for VM to come up" % attempt)
                            raise Exception
                        else:
                            break
                    except Exception as ex:
                        attempt = attempt + 1
            else:
                mounted_machine_vmhelper.update_vm_info(prop='All', os_info=True, force_update=True,
                                                        isolated_network=kwargs.get("isolated_network"))
            if kwargs.get("isolated_network"):
                if "Lab" not in mounted_machine_vmhelper.network_name:
                    self.log.error(
                        'Live Mounted VM "{0}" NOT FOUND in the specified network "{1}".'
                            .format(mounted_vm_names[vm_index], mounted_machine_vmhelper.network_name))
                    raise Exception
                else:
                    self.log.info(
                        'Success - Live Mounted VM "{0}" found in the specified network: "{1}".'
                            .format(mounted_vm_names[vm_index], mounted_machine_vmhelper.network_name))
            else:
                if rep_target_summary is not None:
                    mounted_network_name = rep_target_summary['Destination network']
                else:
                    if not kwargs.get("mounted_network_name"):
                        mounted_network_name = source_machine_vmhelper.network_name

                if mounted_network_name != mounted_machine_vmhelper.network_name:
                    self.log.error(
                        'Live Mounted VM "{0}" NOT FOUND in the specified network "{1}".'
                            .format(mounted_vm_names[vm_index], mounted_network_name))
                    raise Exception
                # else found in specified network
                self.log.info(
                    'Success - Live Mounted VM "{0}" found in the specified network: "{1}".'
                        .format(mounted_vm_names[vm_index], mounted_network_name))
                # else found in specified network
                self.log.info(
                    'Success - Live Mounted VM "{0}" found in the specified network: "{1}".'
                        .format(mounted_vm_names[vm_index], mounted_network_name))

            # 2. validate test data in live mounted vm which is in network (before expiry time)
            # validating data in source vm and mounted vm
            if not kwargs.get("isolated_network"):
                VirtualServerUtils.decorative_log(" Validating test data between source "
                                                  "VM:{0} and mounted VM:{1} "
                                                  .format(source_vm_names[vm_index],
                                                          mounted_vm_names[vm_index]))

                self.log.info("Creating Machine objects for live mounted VM:{0}".
                              format(mounted_vm_names[vm_index]))

                # checking if test data has been successfully written on mounted vm
                mounted_machine = mounted_machine_vmhelper.machine
                self.log.info("Fetching testdata path in source machine.")
                _vserver_path = os.path.dirname(os.path.dirname(UTILS_PATH))
                controller_machine = Machine(socket.gethostbyname_ex(socket.gethostname())[2][0],
                                             self.auto_commcell.commcell)
                source_testdata_path = controller_machine.join_path(_vserver_path, "TestCases",
                                                                    "TestData", self.timestamp)
                self.log.info("Starting testdata validation.")
                for _driveletter, _drive in mounted_machine_vmhelper.drive_list.items():
                    dest_testdata_path = mounted_machine.join_path(_drive, self.backup_folder_name, "TestData",
                                                                   self.timestamp)
                    self.log.info('Destination testdata path {0}'.format(dest_testdata_path))
                    self.log.info(
                        'Validating test data in "{0}" drive.'.format(_drive))
                    self.fs_testdata_validation(dest_client=mounted_machine,
                                                source_location=source_testdata_path,
                                                dest_location=dest_testdata_path)
                    self.log.info(
                        'Test data in "{0}" drive has been validated.'.format(_drive))
                self.log.info("Test data validation completed successfully.")

        return mounted_datastores, mounted_machine_vmhelpers

    def live_unmount_validation(self, source_vm_names, mounted_vm_names, hvobj,
                                **kwargs):
        """
        Unmount validation of Live mounted/Virtual Lab VMs and datastore.

        source_vm_names (list)    --  list of source VM name

        mounted_vm_names (list)  -- list of mounted VMs

        hvobj (obj)    --  HypervisorHelper object

        kwargs -- Arbitrary keyword arguments

        """

        for vm_index in range(len(source_vm_names)):
            hvobj.VMs = mounted_vm_names[vm_index]
            mounted_machine_vmhelper = hvobj.VMs[mounted_vm_names[vm_index]]
            error_count = 0
            start_time = kwargs.get("start_time")
            expiration_time = self.expiration_time + (30 * 60)  # adding 30 mins extra before checking for unmount
            mount_expiration_time = self.expiration_time
            if kwargs.get("virtual_lab") or (self.live_mount_migration and self.vmpolicy):
                self.log.info("Adding additional 30 mins for migration")
                expiration_time += (30 * 60)  # Adding additional 30 mins

            # Wait time before the Migration is started is 1 hour for Live mount from command center
            if self.live_mount_migration and self.rep_target_summary:
                self.log.info("Wait time before live mount migration is started = 1 hour")

            time_passed = time.time() - start_time
            VirtualServerUtils.decorative_log("Waiting for expiry time to finish")
            diff_in_seconds = expiration_time - time_passed
            diff_in_mins = math.ceil(diff_in_seconds / 60)
            self.log.info("Time left for unmount: {0} minutes.".format(str(diff_in_mins)))
            migration_testdata_validation_complete = False
            _vm_ds = mounted_machine_vmhelper.datastore
            while time_passed < expiration_time:
                # sleeping for remaining time
                self.log.info("Sleeping for 10 minutes.")
                time.sleep(600)
                time_passed = time.time() - start_time
                if kwargs.get("virtual_lab") or self.live_mount_migration:
                    if "_GX_" in _vm_ds:
                        self.log.info("Check if the Live Mounted or Virtual Lab VM got migrated or not")
                        if not kwargs.get("isolated_network"):
                            mounted_machine_vmhelper.update_vm_info(prop='All',
                                                                    os_info=True, force_update=True)
                        else:
                            mounted_machine_vmhelper.update_vm_info(prop='All',
                                                                    os_info=True, force_update=True,
                                                                    isolated_network=True)
                        _vm_ds = mounted_machine_vmhelper.datastore
                    else:
                        self.log.info("VM is migrated. Waiting for Expiration")
                        self.log.info("check VM exist ")
                        vms_in_hypervisor = hvobj.get_all_vms_in_hypervisor()
                        if mounted_vm_names[vm_index] not in vms_in_hypervisor and time_passed < expiration_time:
                            self.log.warning('Vm is unmounted. Error count {}'.format(error_count))
                            if error_count > 3:
                                self.log.error("VM unmounted in {0} seconds".format(time_passed))
                                raise Exception("VM unmounted earlier than expected")
                            error_count += 1

                        # Validate testdata for the migrated VM once after the migration is complete
                        if self.live_mount_migration:
                            if not migration_testdata_validation_complete:
                                self.log.info("Fetching testdata path in source machine.")
                                _vserver_path = os.path.dirname(os.path.dirname(UTILS_PATH))
                                controller_machine = Machine(socket.gethostbyname_ex(socket.gethostname())[2][0],
                                                             self.auto_commcell.commcell)
                                source_testdata_path = controller_machine.join_path(_vserver_path, "TestCases",
                                                                                    "TestData", self.timestamp)
                                mounted_machine = mounted_machine_vmhelper.machine
                                for _drive_letter, _drive in mounted_machine_vmhelper.drive_list.items():
                                    dest_location = mounted_machine.join_path(
                                        _drive,
                                        "TDFSDataToTestWrite",
                                        "TestData",
                                        self.timestamp)
                                    self.fs_testdata_validation(dest_client=mounted_machine,
                                                                source_location=source_testdata_path,
                                                                dest_location=dest_location)

                                migration_testdata_validation_complete = True
                                # reset the timer as the VM would be expired with respect to the migration end time
                                start_time = time.time()
                                time_passed = 0

                    if not (self.live_mount_migration and self.rep_target_summary):
                        if time_passed > mount_expiration_time:
                            self.log.info("Waiting for migration to complete")
                            self.log.info("Time lapsed after VM expiration {0}".format(time_passed -
                                                                                       mount_expiration_time))
                        else:
                            self.log.info("Time lapsed before VM migrates {0}".format(time_passed))
                    self.log.info("Time left for unmount {0}".format(expiration_time - time_passed))

                else:
                    self.log.info("check VM exist ")
                    vms_in_hypervisor = hvobj.get_all_vms_in_hypervisor()
                    if mounted_vm_names[vm_index] not in vms_in_hypervisor and time_passed < expiration_time:
                        self.log.warning('Vm is unmounted. Error count {}'.format(error_count))
                        if error_count > 3:
                            self.log.error("VM unmounted in {0} seconds".format(time_passed))
                            raise Exception("VM unmounted earlier than expected")
                        error_count += 1

            if kwargs.get("virtual_lab") or self.live_mount_migration:
                if "_GX_" not in _vm_ds:
                    if _vm_ds == self.datastore_name:
                        self.log.info("Live Mounted VM / Virtual Lab machine VM {0} got migrated successfully to {1}".
                                      format(mounted_vm_names[vm_index], _vm_ds))
                    else:
                        self.log.info("Live Mounted VM / Virtual Lab machine VM {0} got migrated to wrong DS {1}".
                                      format(mounted_vm_names[vm_index], _vm_ds))
                else:
                    raise Exception("Live Mounted VM / Virtual Lab machine VM {0} didn't migrate successfully from {1}".
                                    format(mounted_vm_names[vm_index], _vm_ds))

    def virtual_lab_validation(self, source_vm_name, hvobj, vmpolicy,
                               live_mount_job=None, source_hvobj=None, **kwargs):

        """Live Mount the client for the specified vm policy name

            Args:
                vmpolicy                (obj)    --  SDK object to LiveMountPolicy class

                hvobj                   (obj)    --  HypervisorHelper object

                live_mount_job          (list)    --  list of (SDK object of Job class or Live Mounted jobID)

                source_vm_name          (list)    --  list of source VM name

                mounted_network_name    (str)    --  optional network if provided

                **kwargs                         : Arbitrary keyword arguments

            Exception:
                if it fails to live mount the vm
        """

        if source_hvobj is None:
            source_hvobj = hvobj
        if not isinstance(source_vm_name, list):
            source_vm_names = [source_vm_name]
        else:
            source_vm_names = source_vm_name

        if not isinstance(live_mount_job, list):
            live_mount_jobs = [live_mount_job]
        else:
            live_mount_jobs = live_mount_job
        self.vmpolicy = vmpolicy

        start_time = time.time()
        vms_in_hypervisor = hvobj.get_all_vms_in_hypervisor()
        mounted_vm_names = []
        for job_index in range(len(live_mount_jobs)):
            if isinstance(live_mount_jobs[job_index], Job):
                live_mount_jobs[job_index] = live_mount_jobs[job_index].job_id

        for each_vm in source_vm_names:
            mounted_vm_names.append(each_vm + "_LM_" + live_mount_jobs[job_index])
            if mounted_vm_names[0] not in vms_in_hypervisor:
                raise Exception("Virtual Lab VM didn't get mounted successfully")
        self.log.info("Virtual Lab VM got mounted successfully")

        self.log.info("Live mounted VM validation")
        mounted_ds, mounted_machine_vmhelpers = self.mounted_vm_validation(source_vm_names,
                                                                           mounted_vm_names,
                                                                           source_hvobj, hvobj,
                                                                           isolated_network=kwargs.get(
                                                                               "isolated_network"),
                                                                           mounted_network_name=kwargs.get(
                                                                               "mounted_network_name"))
        self.log.info(mounted_ds)
        ds_in_hypervisor = hvobj._get_datastore_dict()

        self.log.info("Unmount validation of mounted VM")
        self.live_unmount_validation(source_vm_names, mounted_vm_names, hvobj,
                                     virtual_lab=kwargs.get("virtual_lab"),
                                     isolated_network=kwargs.get("isolated_network"),
                                     start_time=start_time)

        if kwargs.get("snap"):
            for each_ds in mounted_ds.values():
                if each_ds in ds_in_hypervisor:
                    raise Exception("Snap didn't get unmounted")
                else:
                    self.log.info("Snap got unmounted successfully")
        else:
            VirtualServerUtils.decorative_log("Validations after expiration period is over")
            # 3. check if 3dfs got unmounted (after expiry time)
            hv_type = VirtualServerConstants.hypervisor_type
            if source_hvobj.instance_type == hv_type.VIRTUAL_CENTER.value.lower():
                for vm_index in range(len(source_vm_names)):
                    hvobj.VMs = mounted_vm_names[vm_index]
                    mounted_machine_vmhelper = hvobj.VMs[mounted_vm_names[vm_index]]
                    if not kwargs.get("isolated_network"):
                        mounted_machine_vmhelper.update_vm_info(prop='All',
                                                                os_info=True, force_update=True)
                    else:
                        mounted_machine_vmhelper.update_vm_info(prop='All',
                                                                os_info=True, force_update=True,
                                                                isolated_network=True)
                    self.vmware_live_mount_validation(live_mount_jobs, hvobj,
                                                      mounted_ds[ mounted_machine_vmhelper.vm_name])
                    self.log.info("Success.3DFS export got unmounted.Virtual Lab VM got migrated successfully")
                # success message after validation is complete
                self.log.info("Success. Live Mount validation completed with no issues.")

    def live_mount_validation(self,
                              vmpolicy,
                              hvobj,
                              live_mount_job,
                              source_vm_name,
                              rep_target_summary=None,
                              mounted_network_name=None,
                              source_hvobj=None):

        """Live Mount the client for the specified vm policy name

            Args:
                vmpolicy                (obj)    --  SDK object to LiveMountPolicy class

                hvobj                   (obj)    --  HypervisorHelper object

                live_mount_job          (list)    --  list of (SDK object of Job class or Live Mounted jobID)

                source_vm_name          (list)    --  list of source VM name

                mounted_network_name    (str)    --  optional network if provided

                rep_target_summary      (dict)   -- dictonary containing information of Replication Target

                source_hvobj            (obj)    --   Source HypervisorHelper object

            Exception:
                if it fails to live mount the vm
        """
        if vmpolicy is None and rep_target_summary is None:
            self.log.error("provide atleast one of (vmpolicy,rep_target_summary)")
            raise Exception
        if not isinstance(source_vm_name, list):
            source_vm_names = [source_vm_name]
        else:
            source_vm_names = source_vm_name

        if not isinstance(live_mount_job, list):
            live_mount_jobs = [live_mount_job]
        else:
            live_mount_jobs = live_mount_job
        if source_hvobj == None:
            source_hvobj = hvobj

        if len(live_mount_jobs) != len(source_vm_names):
            self.log.error("source_vm_names length is not equal to live_mount_jobs length")
            raise Exception

        # we only need jobIds.so,if Job object has passed storing only jobIds
        for job_index in range(len(live_mount_jobs)):
            if isinstance(live_mount_jobs[job_index], Job):
                live_mount_jobs[job_index] = live_mount_jobs[job_index].job_id
        self.vmpolicy = vmpolicy
        self.rep_target_summary = rep_target_summary
        if vmpolicy is None and rep_target_summary is None:
            self.log.error("provide atleast one of (vmpolicy,rep_target_summary)")
            raise Exception

        if self.vmpolicy:
            self.live_mount_migration = True if self.vmpolicy.properties().get('migrateVMs', 0) else False
        else:
            self.live_mount_migration = True if self.rep_target_summary['Migrate VMs'] == 'Yes' else False

        try:
            # starting time to track expiration period
            start_time = time.time()
            mounted_vm_names = []
            vms_in_hypervisor = hvobj.get_all_vms_in_hypervisor()

            for source_vm_name in source_vm_names:
                mounted_vm_name = self.get_mounted_vm_name(source_vm_name)
                mounted_vm_names.append(mounted_vm_name)
                # check if vm is in vcenter
                if mounted_vm_name in vms_in_hypervisor:
                    self.log.info(
                        "-" * 5 + ' Live Mounted VM: "{0}" found on vcenter: "{1}"'.
                        format(mounted_vm_name, hvobj.server_host_name) + "-" * 5)
                else:
                    self.log.error('"{0}" vm not found in hypervisor'.format(mounted_vm_name))
                    raise Exception

            mounted_datastores, mounted_machine_vmhelpers = self.mounted_vm_validation(
                source_vm_names, mounted_vm_names,
                source_hvobj, hvobj,
                mounted_network_name=mounted_network_name)

            # 2.5 Make sure expiry time is over before proceeding to further validation
            self.live_unmount_validation(source_vm_names, mounted_vm_names, hvobj,
                                         start_time=start_time)

            VirtualServerUtils.decorative_log("Validations after expiration period is over")
            VirtualServerUtils.decorative_log("Checking if VM is unmounted")
            for vm_index, vm_name in enumerate(source_vm_names):
                # 3. check if vm unmounted (after expiry time)
                vms_in_hypervisor = hvobj.get_all_vms_in_hypervisor()
                if mounted_vm_names[vm_index] not in vms_in_hypervisor:
                    self.log.info("VM successfully unmounted from hypervisor {0}.".format(
                        hvobj.server_host_name))
                else:
                    self.log.error('Live Mounted VM {0} not unmounted after expiration time from '
                                   'hypervisor {1}.'.format(mounted_vm_name, hvobj.server_host_name))
                    raise Exception
                # check if source vm exist
                source_vms_in_hypervisor = source_hvobj.get_all_vms_in_hypervisor()
                if source_vm_names[vm_index] not in source_vms_in_hypervisor:
                    self.log.error('source VM {0} does not exist in hypervisor {1}.'
                                   .format(source_vm_names[vm_index], source_hvobj.server_host_name))
                    raise Exception

                hv_type = VirtualServerConstants.hypervisor_type
                if source_hvobj.instance_type == hv_type.VIRTUAL_CENTER.value.lower():
                    for mounted_machine_vmhelper in mounted_machine_vmhelpers:
                        self.vmware_live_mount_validation(live_mount_jobs, hvobj,
                                                          mounted_datastores[mounted_machine_vmhelper.vm_name])

                else:
                    self.hyperv_live_mount_validation(vmpolicy, live_mount_jobs, hvobj)

                # success message after validation is complete
                self.log.info("Success. Live Mount validation completed with no issues.")
        except Exception as err:
            self.log.error("Exception in validating LiveMount: {0}".format(str(err)))
            raise Exception

    def hyperv_live_mount_validation(self, vmpolicy, live_mount_jobs, hvobj):
        """
        Performs HyperV Live Mount Validation
        Args:
            vmpolicy        (obj) - object of Virtual Machine Policy Class
            live_mount_job: (obj) - object of Live Mount job
            hvobj:  (obj) - Hypervisor helper object formounted machine

        Returns:
            raise exception on failure
        """
        media_agent_name = vmpolicy.properties()['proxyClientEntity']['clientName']
        for each_job in live_mount_jobs:
            share_name = self.auto_commcell.get_live_mount_share_name(each_job)
            if share_name != '':
                share_list = hvobj.get_file_shares(media_agent_name)
                for each_share in share_list:
                    if share_name in each_share:
                        self.log.error(
                            "Share {0} does exist , there seems to be an error".format(share_name))
                        raise Exception("Share exist , clean up validation failed")

    def vmware_live_mount_validation(self, live_mount_jobs, hvobj, mounted_datastore, media_agent=None):
        """
        Validates the Live Mounted VMware VM
        Args:

            live_mount_jobs:            (obj) --Object for Live Mount job

            hvobj:                      (obj) --Hypervisor Helper Object of Mounted Machine

            mounted_datastore:          (string) --Datastore of the mounted vm

            media_agent:                (str)   -- 3DFS MA name
        Returns:
            Raise Exception on Live Mount Validation Failure
        """
        active_mounts = False
        if '3DFS' in mounted_datastore:
            active_mounts = self.check_for_active_mounts(live_mount_jobs, media_agent)
        self.datastore_unmount_validation(hvobj, active_mounts, mounted_datastore, media_agent)

    def find_job_id_from_export_xml(self):
        """
        finds the export xml for live mount

        Returns:
            returns job id from export xml
        """
        try:
            from cvpysdk.client import Client
            media_agent_name = self.media_agent_name
            self.log.info("Creating Client object for media agent.")
            media_agent_client = Client(commcell_object=self.auto_commcell.commcell,
                                        client_name=media_agent_name)

            self.log.info("Creating Machine object for media agent.")
            media_agent_machine = Machine(machine_name=media_agent_name,
                                          commcell_object=self.auto_commcell.commcell)

            _cache_path = self.auto_commcell.get_nfs_server_cache(media_agent_name)
            if not _cache_path:
                if media_agent_machine.check_registry_exists('3Dfs', 's3dfsRootDir'):
                    _cache_path = media_agent_machine.get_registry_value('3Dfs', 's3dfsRootDir')
                else:
                    _cache_path = media_agent_client.job_results_directory
            xml_file_path = media_agent_machine.join_path(_cache_path, '3dfs', 'Exports.xml')

            xml_file_str = media_agent_machine.read_file(xml_file_path)
            xml_file_each_line = xml_file_str.split('\n')
            active_job_ids = []
            VirtualServerUtils.decorative_log(
                "Checking Exports.xml in Job Results directory of Media Agent")
            for line in xml_file_each_line:
                if "jobId" in line:
                    match = re.search('[\"]+\d+[\"]', line)
                    if match:
                        active_job_ids.append(match.group().strip('\"'))
            return active_job_ids
        except Exception as err:
            self.log.error("Exception occurred in finding the jobs from XML {0}".format(err))
            raise err

    def check_for_active_mounts(self, live_mount_jobs, media_agent=None):
        """
        Check if there are any active mounts
        Args:
            live_mount_jobs (list)   -- List of SDK object of Live mount job IDs

            media_agent     (str)   --  3DFS MA name
        Returns:
            Raise Exception on if there are active mounts
        """
        try:
            # check for active mounts in DB of media agent
            from cvpysdk.client import Client
            if media_agent:
                media_agent_name = media_agent
            else:
                media_agent_name = self.media_agent_name
            self.log.info("Creating Client object for media agent.")
            media_agent_client = Client(commcell_object=self.auto_commcell.commcell,
                                        client_name=media_agent_name)
            _query = "Select jobId from APP_3DFSVSAExportProps where tdfsServerId = %s and jobId is not NULL" % (
                media_agent_client.client_id)
            self.csdb.execute(_query)
            _results = self.csdb.fetch_all_rows()
            active_mounts = False
            if _results != [['']]:
                active_mounts = True
                self.log.info("Active mounts found on Media Agent.")
            else:
                self.log.info("No active mounts found on Media Agent.")

            # check for job id in active job mounts
            active_job_ids = [item for sublist in _results for item in sublist]
            for each_job in live_mount_jobs:
                if active_mounts and each_job in active_job_ids:
                    self.log.info("Checking for existing mount on Media Agent.")
                    self.log.error(
                        'Job Id {0} still exists in Database of Media Agent {1}.'.
                            format(each_job, media_agent_name))
                    raise Exception
                else:
                    self.log.info("Existing mount not found on Media Agent.")
            return active_mounts
        except Exception as err:
            self.log.error("Exception occurred in checking active mounts from DB {0}".format(err))
            raise err

    def datastore_unmount_validation(self, hvobj, active_mounts, mounted_datastore, media_agent=None):
        """

        Args:

            hvobj                       (obj) - Hypervisor Object of Mounted Machine

            active_mounts               (bool) - active mounts present

            mounted_datastore           (string) -  Datastore of the mounted vm

            media_agent                 (str)   -   3DFS MA name
        Returns:
            Raise exception if datastore is unmounted

        """
        try:
            # 4. check if data store is unmounted (if no active mounts are present)
            VirtualServerUtils.decorative_log("Checking associated datastore")
            if media_agent:
                media_agent_name = media_agent
            else:
                media_agent_name = self.media_agent_name
            mounted_vm_datastore = mounted_datastore
            if not active_mounts:
                self.log.info("Checking whether datastore is unmounted since there are no "
                              "other active mounts.")
                hv_dict = hvobj._get_datastore_dict(True)
                self.log.info("Mounted VM Datastore : {0}".format(mounted_vm_datastore))
                if mounted_vm_datastore in hv_dict:
                    self.log.error(
                        'Datastore "{0}" not unmounted despite media agent "{1}" having no '
                        'active mounts.'.format(mounted_vm_datastore, media_agent_name))
                    raise Exception
                else:
                    self.log.info("Datastore successfully unmounted.")
            else:
                self.log.info("Since there are other active mounts, datastore is "
                              "still mounted.")
        except Exception as err:
            self.log.error("Exception occurred in  cehcking datastore unmount {0}".format(err))
            raise err

    def fs_testdata_validation(self, dest_client, source_location, dest_location, controller_machine=None):
        """
        Does Validation of live mounted vm comparing testdata in source client

        Args:
            dest_client       (obj)   --  Machine class object of destination client

            source_location   (str)   --  testdata path for source vm

            dest_location     (str)   --  testdata path for live mounted vm

            controller_machine  (object):   object of the controller machine

        Exception
                if folder comparison fails
        """
        try:
            self.log.info("Validating the testdata")
            if not controller_machine:
                controller_machine = Machine(socket.gethostbyname_ex(socket.gethostname())[2][0],
                                             self.auto_commcell.commcell)
            attempt = 0
            while attempt < 5:
                try:
                    controller_machine.add_host_file_entry(dest_client.machine_name, dest_client.ip_address)
                    difference = controller_machine.compare_folders(dest_client, source_location,
                                                                    dest_location,
                                                                    ignore_folder=
                                                                    [VirtualServerConstants.PROBLEMATIC_TESTDATA_FOLDER]
                                                                    )
                    break
                except Exception as exp:
                    self.log.info("test data validation attempt {0}".format(attempt))
                    self.log.info("Sleeping for 30 seconds")
                    attempt = attempt + 1
                    time.sleep(30)
                finally:
                    try:
                        controller_machine.remove_host_file_entry(dest_client.machine_name)
                    except:
                        self.log.warning(f"Soft Error, couldn't remove host file entry :{dest_client.machine_name}")
            if attempt >= 5:
                difference = controller_machine.compare_folders(dest_client, source_location,
                                                                dest_location)

            if difference:
                self.log.info("checksum mismatched for files {0}".format(difference))
                raise Exception(
                    "Folder Comparison Failed for Source: {0} and destination: {1}".format(
                        source_location, dest_location))
            self.log.info("Validation completed successfully")

        except Exception as err:
            self.log.exception("Exception in FS Testdata Validation")
            raise err
