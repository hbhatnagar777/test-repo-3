# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file that executes the  Intellisnap basic acceptance test cases for nas client

Intellisnap BasicAcceptance is the only class defined in this file

This class include below cases:
    1.  FULL backup job

    2.  INCREMENTAL backup job after adding test data

    3.  DIFFERENTIAL backup job after adding test data

    4.  Restore out of place to Windows client

    5.  Restore out of place to Unix client

    6.  Restore in place job

    7.  Restore out of place to filer job

    8.  Running backup copy job

    9. Restore in place from backup copy job

    10. Restore in place in incremental job time frame

BasicAcceptance:
    __init__()              --  initializes basicacceptance object

    _get_copy_precedence()  --  returns the copy precedence value

    _run_backup()           --  starts the backup job

    run()                   --  runs the basic acceptance test case
"""


import time

from NAS.NASUtils.nashelper import NASHelper
from NAS.NASUtils.nasclient import NetAPPClient
from AutomationUtils.machine import Machine
from AutomationUtils import logger
from AutomationUtils.options_selector import OptionsSelector


class SnapBasicAcceptance(object):
    """Helper class to run Intellisnap basic acceptance test case for nas client"""

    def __init__(self, test_case_obj, is_cluster=False, is_vdm=False, **kwargs):
        """Initializes snapbasicacceptance object

            Args:
                test_case_obj   (object)    --  test case class object

                is_cluster      (bool)      --  flag to determine if the specified client
                                                    is cluster / vserver / filer
        """
        self.replica_type = kwargs.get('replica_type', None)
        self._inputs = test_case_obj.tcinputs
        self._commcell = test_case_obj.commcell
        self._log = logger.get_log()
        self._subclient = test_case_obj.subclient
        self._commserver_name = self._commcell.commserv_name
        self._csdb = test_case_obj.csdb
        self._nas_helper = NASHelper()
        self._client = test_case_obj.client
        self._is_cluster = is_cluster
        self._storage_policy = self._commcell.storage_policies.get(self._subclient.storage_policy)
        self.client_machine = Machine(self._commserver_name, self._commcell)
        self.mount_path = 'tstmntpath'
        self.mountpath_val = None
        self.mount_status = None
        self.test_data_path = None
        self.get_mount_path = "SELECT MountPath FROM SMVolume WHERE JobId = {a} AND CopyId = {b}"
        self.get_volume_id = "SELECT SMVolumeId FROM SMVolume WHERE jobId in ({a}) AND CopyId = {b}"
        self.get_mount_status = "SELECT MountStatus FROM SMVolume WHERE JobId = {0}"
        self.client_name = self._client.client_name
        self._agent = test_case_obj.agent
        self.impersonate_user = None
        self.impersonate_password = None
        self.proxy = None
        self.automount = False
        self.is_vdm = is_vdm
        self.options_selector = OptionsSelector(self._commcell)
        self.snap_job_list = []
        self.get_vendor_id = "SELECT Id FROM SMVendor WHERE Name = '{0}'"
        self.get_controlhost_id = "SELECT RefId FROM SMHostAlias WHERE AliasName = '{0}'"
        self.get_replica_copy = "SELECT name FROM archGroupCopy WHERE copy = 3 AND archGroupId = {0}"
        self.get_snap_copy = "SELECT name FROM archGroupCopy WHERE copy = 1 AND archGroupId = {0}"
        self.get_backup_copy = "SELECT name FROM archGroupCopy WHERE copy = 2 AND archGroupId = {0}"
        self.storage_policy_copy = None
        self.spcopy = None
        self.mounthost = self._inputs.get('mounthost', None)
        self.mounthostobj = Machine(self.mounthost, self._commcell)

    def delete_replica_copy(self, copy_name=None):
        """Delete Replica Vault or Mirror Copy"""

        if copy_name is None:
            self._log.info("Copy Name is not defined, finding the Existing Replica Copy Name")
            replica_copy_name = self.execute_query(self.get_replica_copy, self._storage_policy.storage_policy_id)
            if replica_copy_name in [None, ' ', '']:
                self._log.info("No Secondary Copy Present, Continue creating new copy")
            else:
                try:
                    self._log.info("*" * 10 + "Disable backup copy & snapshot catalog" + "*" * 10)
                    options = {
                        'enable_backup_copy': False,
                        'source_copy_for_snap_to_tape': None,
                        'enable_snapshot_catalog': False,
                        'source_copy_for_snapshot_catalog': None,
                        'is_ocum': None,
                        'disassociate_sc_from_backup_copy': None
                    }
                    self._storage_policy.update_snapshot_options(**options)
                except Exception as e:
                    self._log.info("Updating Storage policy failed with err: " + str(e))
                self._log.info("deleting Copy : {0}".format(replica_copy_name))
                self._storage_policy.delete_secondary_copy(replica_copy_name)
                self._log.info("Sleeping for 3mins for copy to be deleted")
                time.sleep(180)
                self._log.info("Successfully deleted copy : {0}".format(replica_copy_name))
            
        else:
            try:
                self._log.info("*" * 10 + "Disable backup copy & snapshot catalog" + "*" * 10)
                options = {
                    'enable_backup_copy': False,
                    'source_copy_for_snap_to_tape': None,
                    'enable_snapshot_catalog': False,
                    'source_copy_for_snapshot_catalog': None,
                    'is_ocum': None,
                    'disassociate_sc_from_backup_copy': None
                }
                self._storage_policy.update_snapshot_options(**options)
                self._log.info("deleting Copy : {0}".format(copy_name))
                self._storage_policy.delete_secondary_copy(copy_name)
            except Exception as e:
                self._log.info("deleting Storage policy copy failed with err: " + str(e))
                self._log.info("Treating as soft failure")


    def create_replica_copy(self, replica_type):
        """Create Replica Vault and Mirror Copy"""

        library_name = str(self._inputs['AuxCopyLibrary'])
        media_agent_name = self._inputs['AuxCopyMediaAgent']
        source_copy = "Primary Snap"
        source_array = self._inputs.get('ArrayName', None)

        if replica_type == "pv_replica":
            self.storage_policy_copy = self.options_selector.get_custom_str(presubstr="Vault_Replica_")
            is_mirror_copy = False
            is_snap_copy = True
            self._log.info("*" * 20 + "Creating Copies for PV_Replica Configuration" + "*" * 20)
            self._storage_policy.create_snap_copy(
                self.storage_policy_copy, is_mirror_copy, is_snap_copy, library_name,
                media_agent_name, source_copy, is_replica_copy=True, is_c2c_target=False)
            self._log.info("Successfully created Vault Replica copy")
            self.spcopy = self._storage_policy.get_copy(self.storage_policy_copy)
        elif replica_type == "pm_replica":
            self.storage_policy_copy = self.options_selector.get_custom_str(presubstr="Mirror_Replica_")
            is_mirror_copy = True
            is_snap_copy = True
            self._log.info("*" * 20 + "Creating Copies for PM_Replica Configuration" + "*" * 20)
            self._storage_policy.create_snap_copy(
                self.storage_policy_copy, is_mirror_copy, is_snap_copy, library_name,
                media_agent_name, source_copy, is_replica_copy=True, is_c2c_target=False)
            self._log.info("Successfully created Mirror Replica copy")
            self.spcopy = self._storage_policy.get_copy(self.storage_policy_copy)
        else:
            self._log.info("Not Creating any Replica copies")

        if source_array is not None:
            self._log.info("*" * 20 + "Adding SVM Mappings" + "*" * 20)
            target_vendor = self._inputs.get('TargetVendorName', None)
            tgt_vendor_id = self.execute_query(self.get_vendor_id, target_vendor)
            target_array = self._inputs['ArrayName2']
            src_array_id = self.execute_query(self.get_controlhost_id, source_array)
            tgt_array_id = self.execute_query(self.get_controlhost_id, target_array)
            kwargs = {
                'target_vendor' : target_vendor,
                'tgt_vendor_id' : tgt_vendor_id
                }
            self.spcopy.add_svm_association(src_array_id, source_array, tgt_array_id, target_array,
                                       **kwargs)
            self._log.info("Successfully added SVM association to copy : {0}".format(self.storage_policy_copy)) 

        return self.storage_policy_copy

    def run_aux_copy(self):
        """Run Aux copy"""
        self._log.info("*" * 10 + " Run Aux Copy job " + "*" * 10)
        job = self._storage_policy.run_aux_copy(
            self.storage_policy_copy, str(self._inputs['AuxCopyMediaAgent'])
        )
        self._log.info("Started Aux Copy job with Job ID: " + str(job.job_id))

        if not job.wait_for_completion():
            raise Exception("Failed to run aux copy job with error: " + str(job.delay_reason))

        self._log.info("Successfully finished Aux Copy Job")

    def _run_backup(self, backup_type):
        """Starts backup job"""
        self._log.info("*" * 10 + " Starting Subclient {0} Backup ".format(backup_type) + "*" * 10)
        job = self._subclient.backup(backup_type)
        self._log.info("Started %s backup with Job ID: %s", backup_type, str(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run {0} backup job with error: {1}".format(
                    backup_type, job.delay_reason
                )
            )
        self.snap_job_list.append(job.job_id)
        return job

    def execute_query(self, query, option1):
        """ Executes SQL Queries
            Return:
                    str : first column of the sql output

        """
        self._csdb.execute(query.format(option1))
        return self._csdb.fetch_one_row()[0]

    def execute_query_all_rows(self, query, my_options=None):
        """ Executes SQL Queries
            Args:
                query           (str)   -- sql query to execute

                my_options       (dict)  -- options in the query

            Return:
                    list : all column of the sql output
        """

        if my_options is None:
            self._csdb.execute(query)
        elif isinstance(my_options, dict):
            self._csdb.execute(query.format(**my_options))
        return self._csdb.fetch_all_rows()

    def _get_copy_precedence(self, storage_policy, storage_policy_copy):
        """Returns the copy precedence value"""
        self._csdb.execute(
            "select copy from archGroupCopy where archGroupId in (select id from archGroup where \
            name = '{0}') and name = '{1}'".format(storage_policy, storage_policy_copy))
        cur = self._csdb.fetch_one_row()
        return cur[0]

    def snap_operations(self, jobid, copy_id, _commserver_name=None, mountpath=None,
                        mount=False,
                        unmount=False,
                        revert=False,
                        delete=False,
                        force_delete=False):
        """ Common Method for Snap Operations
            Args :
                jobid : jobid for the Snap operation
                _commserver_name : name of the destination client, default: None
                MountPath : MountPath for Snap operation, default: None
            Return :
                object : Job object of Snap Operation job
        """

        self._log.info("Getting SMVolumeId using JobId: %s and copyId: %s}", format(jobid, copy_id))
        volumeid = self.execute_query_all_rows(self.get_volume_id, {'a': jobid, 'b': copy_id})
        self._log.info("SMvolumeId is : %s", format(volumeid))
        self._log.info("destination client id is :%s", format(_commserver_name))
        self._log.info("mountpath is %s", format(mountpath))
        if mount:
            job = self._commcell.array_management.mount(volumeid,
                                                        _commserver_name,
                                                        mountpath,
                                                        False)
        elif unmount:
            job = self._commcell.array_management.unmount(volumeid)
        elif revert:
            job = self._commcell.array_management.revert(volumeid)
        elif delete:
            job = self._commcell.array_management.delete(volumeid)
        else:
            job = self._commcell.array_management.force_delete(volumeid)

        self._log.info("Started  job : %s for Snap Operation", format(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run   job {0} for Snap operation with error: {1}".format(
                    job.job_id, job.delay_reason)
                )
        if job.status != 'Completed':
            raise Exception(
                "job: {0} for snap operation is completed with errors, Reason: {1}".format(
                    job.job_id, job.delay_reason)
                )

        self._log.info("successfully completed Snap operation of jobid :%s", format(job.job_id))
        time.sleep(30)
        return job

    def mount_snap(self, jobid, copy_name, destclient=None):
        """ Mounts Snap of the given jobid
            Args:
                jobid      : jobid for mount operation
                destclient : Client name on which snap is to be mounted
            Return:
                object : job object of Snap operation job
        """
        self._log.info("Mounting snapshot of jobid : %s", format(jobid))
        mountpath = self.mount_path
        if destclient is None:
            destclient = self._commserver_name
        spcopy = self.spcopy_obj(copy_name)
        return self.snap_operations(jobid, spcopy.copy_id, destclient, mountpath, mount=True)

    def unmount_snap(self, jobid, copy_name):
        """ UnMounts Snap of the given jobid
            Args:
                jobid : jobid for unmount operation
            Return:
                object : job object of Snap operation job
        """
        self._log.info("UnMounting snapshot of jobid : %s", format(jobid))
        spcopy = self.spcopy_obj(copy_name)
        return self.snap_operations(jobid, spcopy.copy_id, unmount=True)

    def revert_snap(self, jobid, copy_name):
        """ Reverts Snap of the given jobid
            Args:
                jobid : jobid for revert operation
            Return:
                object : job object of Snap operation job
        """
        self._log.info("Reverting snapshot of jobid : %s", format(jobid))
        spcopy = self.spcopy_obj(copy_name)
        return self.snap_operations(jobid, spcopy.copy_id, revert=True)

    def delete_snap(self, jobid, copy_name):
        """ Deletes Snap of the given jobid
            Args:
                jobid : jobid for delete operation
            Return:
                object : job object of Snap operation job
        """
        self._log.info("Deleting snapshot of jobid : %s", format(jobid))
        spcopy = self.spcopy_obj(copy_name)
        return self.snap_operations(jobid, spcopy.copy_id, delete=True)

    def force_delete_snap(self, jobid, copy_name):
        """ Deletes Snap of the given jobid
            Args:
                jobid : jobid for delete operation
            Return:
                object : job object of Snap operation job
        """
        self._log.info("Deleting snapshot of jobid : %s", format(jobid))
        spcopy = self.spcopy_obj(copy_name)
        return self.snap_operations(jobid, spcopy.copy_id, force_delete=True)

    def spcopy_obj(self, copy_name):
        """ Create storage Policy Copy object
        Arg:
            copy_name        (str)         -- Copy name
        """
        spcopy = self._storage_policy.get_copy(copy_name)
        return spcopy

    def delete_multiple_snaps(self, jobid, copy_name):
        """ jobid : jobid is the list of jobs to be deleted"""
        spcopy = self.spcopy_obj(copy_name)
        self._log.info("Deleting all snaps at a time %s", jobid)
        return self.snap_operations((','.join(map(str, jobid))), spcopy.copy_id, delete=True)

    def snapshot_cataloging(self):
        """ Runs Offline snapshot cataloging for the given storage policy
        """

        job = self._storage_policy.run_snapshot_cataloging()
        self._log.info("Deferred Catalog workflow job id is : {0}".format(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run  Workflow job {0} for Deferred Catalog with error: {1}".format(
                    job.job_id, job.delay_reason)
                )
        if job.status != 'Completed':
            raise Exception(
                "job: {0} for Snapshot catalog operation is completed with errors".format(
                    job.job_id)
                )
        self._log.info("Successfully completed deferred catalog job: {0}".format(job.job_id))

    def run_backup_copy(self):
        """ RUn Backup Copy for the given storage policy
        """

        self._log.info("*" * 10 + "Running backup copy" + "*" * 10)

        job = self._storage_policy.run_backup_copy()
        self._log.info("Backup copy workflow job id is : %s", format(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run backup copy job with error: " + str(job.delay_reason)
            )
        self._log.info("Successfully finished backup copy workflow Job :%s", format(job.job_id))

        if job.status != 'Completed':
            raise Exception(
                "job: {0} for Backup copy operation is completed with errors, \
                    Reason: {1}".format(job.job_id, job.delay_reason)
            )

    def compare(self, client_obj, destclient_obj, source_dir, dest_dir):
        """ Compare two directories
            Args:
                client_obj : client Object of the Source machine
                destclient_obj : client Object of the Destination machine
                source_dir : Source directory Path
                dest_dir : Destination directory Path
        """

        self._log.info("comparing content")
        self._log.info("source dir: %s", source_dir)
        self._log.info("dest dir : %s", dest_dir)

        difference = []
        difference = client_obj.compare_folders(
            destclient_obj,
            source_dir,
            dest_dir,
            ignore_files=self._nas_helper.ignore_files_list,
            ignore_folder=self._nas_helper.ignore_files_list
            )

        if difference != []:
            self._log.error(
                "Validation failed. List of different files \n%s", format(difference)
            )
            raise Exception(
                "validation failed. Please check logs for more details."
            )
        self._log.info("Compare folder validation was successful")

    def get_fs_os_id(self):
        """ Returns the iDA type value of the subclient """
        self.scid = self._subclient._get_subclient_id()
        query = "select appTypeId from app_application where id={0}"
        fsosid = self.execute_query(query, self.scid)
        return fsosid

    def snapop_validation(
            self, jobid, copy_id, mount=False, revert=False, delete=False, unmount=False, destclient=None):
        """ Common Method for Snap Operation Validations
            Args:
                jobid      : snap backup jobid
                mount      : if given true, will do mount validation
                revert     : if given true, will do revert validation
                delete     : if given true, will do delete validation
                unmount    : if given true, will do unmount validation
                destclient : Client object on which snap operations should be done
        """

        self._log.info("validating snap operation")
        fsosid = self.get_fs_os_id()
        if fsosid != '29':
            volume_path, _ = self.nas_client.get_path_from_content(self._subclient.content[0])
            volume_path = str(volume_path)
        else:
            if self.automount:
                mountpoint = '/automount'
                temp = self._subclient.content[0].split(":")
                self._log.info(temp)
                server = temp[0]
                share = temp[1]
                self.proxy.mount_nfs_share(mountpoint, server, share, cleanup=True, version=None)
                volume_path = mountpoint
            else:
                volume_path = str(self._subclient.content[0])
        if mount or revert:
            mountpath_val = self.execute_query_all_rows(self.get_mount_path, {'a': jobid, 'b': copy_id})
            mount_path = mountpath_val[0][0]
            if destclient is None:
                self.compare(
                    self.client_machine, self.client_machine, mount_path, volume_path)
            else:
                self.compare(
                    destclient, destclient, mount_path, volume_path)
            self._log.info("comparing files/folders was successful")

        elif delete:
            self._log.info("Checking if the snapshot of JobId: %s exists in the DB", format(jobid))
            volumeid = self.execute_query_all_rows(self.get_volume_id, {'a': jobid, 'b': copy_id})
            self._log.info(
                "smvolumeid from DB is: %s", volumeid)
            if volumeid[0][0] in [None, ' ', '']:
                self._log.info("Snapshot is successfully deleted")
            else:
                raise Exception(
                    "Snapshot of jobid: {0} is not deleted yet, please check the CVMA logs".format(
                        jobid)
                    )
            self._log.info("Successfully verified Snapshot cleanup")

        else:
            mountpath_val = self.execute_query_all_rows(self.get_mount_path, {'a': jobid, 'b': copy_id})
            mount_path = mountpath_val[0][0]
            if destclient is None:
                if self.client_machine.check_directory_exists(mount_path):
                    raise Exception("MountPath folder still exists under {0}".format(
                        mount_path))
                else:
                    self._log.info("MountPath folder does not exists ")
            else:
                if destclient.check_directory_exists(mount_path):
                    raise Exception("MountPath folder still exists under {0}".format(
                        mount_path))
                else:
                    self._log.info(
                        "Path %s don't exist on %s", mount_path, destclient.machine_name)

    def mount_validation(self, jobid, copy_name, destclient=None):
        """ Mount Snap validation
            Args :
                jobid      : snap backup jobid
                destclient : destination client on which snap is mounted
        """
        spcopy = self.spcopy_obj(copy_name)
        self.snapop_validation(jobid, spcopy.copy_id, mount=True, destclient=destclient)
        self._log.info("mount validation was successful")

    def revert_validation(self, jobid, copy_name, destclient=None):
        """ Revert Snap validation
            Args :
                jobid      : snap backup jobid
                destclient : destination client on which snap is to be mounted
        """
        if destclient is not None:
            self.mount_snap(jobid, copy_name, destclient.machine_name)
        else:
            self.mount_snap(jobid, copy_name)
        spcopy = self.spcopy_obj(copy_name)
        self.snapop_validation(jobid, spcopy.copy_id, revert=True, destclient=destclient)
        self.unmount_snap(jobid, copy_name)
        self._log.info("revert validation was successful")

    def delete_validation(self, jobid, copy_name):
        """ Delete Snap validation
            Args :
                jobid : snap backup jobid
        """
        spcopy = self.spcopy_obj(copy_name)
        self.snapop_validation(jobid, spcopy.copy_id, delete=True)
        self._log.info("delete validation was successful")

    def unmount_validation(self, jobid, copy_name, destclient=None):
        """ UnMount Snap validation
            Args :
                jobid      : snap backup jobid
                destclient : destination client on which snap is to be unmounted
        """
        spcopy = self.spcopy_obj(copy_name)
        self.snapop_validation(jobid, spcopy.copy_id, unmount=True, destclient=destclient)
        self._log.info("unmount validation was successful")

    def check_mountstatus(self, jobid, unmount=False):
        """ Common function to check mount status
            Args:
                jobid : snap backup jobid
        """

        if unmount:
            while self.mount_status not in ['79', '']:
                self.mount_status = self.execute_query(self.get_mount_status, jobid)
                self._log.info("mount status: jobid :%s is :%s", format(jobid, self.mount_status))
                self._log.info("snapshot is not unmounted yet, checking after 1min")
                time.sleep(60)
                continue
            self._log.info("snapshot of jobid %s is unmounted successfully", format(jobid))

        return self.mount_status

    def unmount_status(self, jobid):
        """ Check Unmount status
            Args:
                jobid : snap backup jobid
        """
        return self.check_mountstatus(jobid, unmount=True)

    def cleanup(self):
        """
            Remove Subclient content
            Remove Restore location
            Remove Mountpath
        """
        volume_path, _ = self.nas_client.get_path_from_content(self._subclient.content[0])
        volume_path = str(volume_path + '\\TestData')
        self.client_machine.remove_directory(volume_path)
        self._log.info("Successfully removed Subclient Content")
        self.client_machine.remove_directory(self.mount_path)
        self._log.info("Successfully removed MountPath")
        snap_copy_name = self.execute_query(self.get_snap_copy, self._storage_policy.storage_policy_id)
        self.delete_multiple_snaps(self.snap_job_list, snap_copy_name)

    def run(self):
        """Executes Intellisnap basic acceptance test case"""
        self._log.info(
            "Will run below test case on: %s subclient", format(str(self._inputs['SubclientName']))
        )

        self._log.info("Number of data readers: " + str(self._subclient.data_readers))
        if self._subclient.data_readers != 3:
            self._log.info("Setting the data readers count to 3")
            self._subclient.data_readers = 3

        self._log.info("Get NAS Client object")
        self.nas_client = self._nas_helper.get_nas_client(self._client, self._agent,
                                                          is_cluster=self._is_cluster)

        self._log.info("Make a CIFS Share connection")
        self.nas_client.connect_to_cifs_share(
            str(self._inputs['CIFSShareUser']), str(self._inputs['CIFSSharePassword'])
        )
        job = self._run_backup("FULL")
        
        for content in self._subclient.content:
            volume_path, _ = self.nas_client.get_path_from_content(content)
            self._nas_helper.copy_test_data(self.nas_client, volume_path)

        job = self._run_backup("INCREMENTAL")

        inc_job_start_time = str(job.start_time)
        inc_job_end_time = str(job.end_time)
        if self._inputs.get('mount_path'):
            self.mount_path = str(self._inputs['mount_path'])
        snap_copy_name = self.execute_query(self.get_snap_copy, self._storage_policy.storage_policy_id)
        self.mount_snap(job.job_id, snap_copy_name, destclient=self.mounthost)
        self.mount_validation(job.job_id, snap_copy_name, destclient=self.mounthostobj)
        self.unmount_snap(job.job_id, snap_copy_name)
        self.unmount_validation(job.job_id, snap_copy_name)

        for content in self._subclient.content:
            volume_path, _ = self.nas_client.get_path_from_content(content)
            self._nas_helper.copy_test_data(self.nas_client, volume_path)

        job = self._run_backup("DIFFERENTIAL")

        options_selector = OptionsSelector(self._commcell)

        size = self.nas_client.get_content_size(self._subclient.content)
        if self._inputs.get('liveBrowse'):
            if self._inputs['liveBrowse'].upper() == 'TRUE':
                fs_options = {'live_browse': True}

        if self._inputs.get("WindowsDestination"):
            windows_client = Machine(self._inputs["WindowsDestination"], self._commcell)
            windows_restore_client, windows_restore_location = self._nas_helper.restore_to_selected_machine(
                options_selector, windows_client=windows_client, size=size
            )

        else:
            windows_restore_client, windows_restore_location = \
                options_selector.get_windows_restore_client(size=size)

        self._log.info("*" * 10 + " Run out of place restore to Windows Client " + "*" * 10)

        job = self._subclient.restore_out_of_place(
            windows_restore_client.machine_name,
            windows_restore_location,
            self._subclient.content,
            fs_options=fs_options
        )
        self._log.info(
            "Started Restore out of place to Windows client job with Job ID: " + str(job.job_id)
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: " + str(job.delay_reason)
            )

        self._log.info("Successfully finished Restore out of place to windows client")

        self._nas_helper.validate_windows_restored_content(
            self.nas_client, windows_restore_client, windows_restore_location, \
                self._subclient.content
        )

        self._log.info("*" * 10 + " Run out of place restore to Linux Client" + "*" * 10)

        if self._inputs.get("LinuxDestination"):
            linux_client = Machine(self._inputs["LinuxDestination"], self._commcell)

            try:
                mount_path = options_selector.get_drive(linux_client, size)
            except OSError:
                self._log.info("No drive found")

            dir_path = mount_path + options_selector._get_restore_dir_name()
            linux_client.create_directory(dir_path)

            self._log.info(
                "Linux Restore Client obtained: %s", linux_client.machine_name
            )
            self._log.info("Linux Restore location: %s", dir_path)
            linux_restore_client = linux_client
            linux_restore_location = dir_path

        else:
            linux_restore_client, linux_restore_location = \
                options_selector.get_linux_restore_client(size=size)

        job = self._subclient.restore_out_of_place(
            linux_restore_client.machine_name,
            linux_restore_location,
            self._subclient.content,
            fs_options=fs_options
        )
        self._log.info(
            "Started restore out of place to linux client job with Job ID: " + str(job.job_id)
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: " + str(job.delay_reason)
            )

        self._log.info("Successfully finished Restore out of place to linux client")

        out = []
        out = windows_restore_client.compare_folders(
            linux_restore_client, windows_restore_location,
            linux_restore_location, ignore_files=self._nas_helper.ignore_files_list)
        if out != []:
            self._log.error(
                "Restore validation failed. List of different files \n%s", format(str(out))
            )
            raise Exception(
                "Restore validation failed. Please check logs for more details."
            )

        self._log.info("Successfully validated restored content")

        self._log.info("*" * 10 + " Run in place restore in incremental jobtime frame " + "*" * 10)
        job = self._subclient.restore_in_place(
            self._subclient.content,
            from_time=inc_job_start_time,
            to_time=inc_job_end_time,
            fs_options=fs_options)

        self._log.info(
            "Started restore in place in incremental jobtime frame job with Job ID: %s", format(
                job.job_id
            )
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore in incremental time frame with error: {0}".format(
                    job.delay_reason
                )
            )

        self._log.info("Successfully finished Restore in place in incremental time frame")

        self._nas_helper.validate_filer_restored_content(
            self.nas_client, windows_restore_client, windows_restore_location, \
                self._subclient.content
        )

        self._log.info("*" * 10 + " Run Restore in place " + "*" * 10)
        job = self._subclient.restore_in_place(self._subclient.content,
                                               fs_options=fs_options)
        self._log.info("Started restore in place job with Job ID: %s", format(str(job.job_id)))

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore in place job with error: {0}".format(job.delay_reason)
            )

        self._log.info("Successfully finished restore in place job")

        self._nas_helper.validate_filer_restored_content(
            self.nas_client, windows_restore_client, windows_restore_location, \
                self._subclient.content
        )

        self._log.info("*" * 10 + " Run out of place restore to Filer " + "*" * 10)
        filer_restore_location = str(self._inputs['FilerRestoreLocation'])

        job = self._subclient.restore_out_of_place(
            self._client.client_name,
            filer_restore_location,
            self._subclient.content,
            fs_options=fs_options)

        self._log.info(
            "Started Restore out of place to filer job with Job ID: %s}", format(job.job_id)
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: {0}".format(job.delay_reason)
            )

        self._log.info("Successfully finished Restore out of place to Filer")

        self._nas_helper.validate_filer_restored_content(
            self.nas_client, windows_restore_client, windows_restore_location,
            self._subclient.content, filer_restore_location
        )

        backup_copy_name = self.execute_query(self.get_backup_copy, self._storage_policy.storage_policy_id)

        self._log.info("*" * 10 + "Running backup copy now" + "*" * 10)

        job = self._storage_policy.run_backup_copy()
        self._log.info("Backup copy workflow job id is : %s", format(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: " + str(job.delay_reason)
            )
        self._log.info("Successfully finished backup copy workflow Job :%s", format(job.job_id))

        if job.status != 'Completed':
            raise Exception(
                "job: {0} for Backup copy operation is completed with errors, Reason: {1}".format(
                    job.job_id, job.delay_reason)
            )

        self._log.info("*" * 10 + " Run in place restore from backup copy " + "*" * 10)
        copy_precedence = self._get_copy_precedence(
            self._subclient.storage_policy, backup_copy_name
        )

        job = self._subclient.restore_in_place(
            self._subclient.content, copy_precedence=int(copy_precedence)
        )

        self._log.info(
            "Started restore in place from backup copy job with Job ID: %s", format(job.job_id)
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to restore from backup copy with error: {0}".format(str(job.delay_reason))
            )

        self._log.info("Successfully finished Restore in place from backup copy")

        self._nas_helper.validate_filer_restored_content(
            self.nas_client, windows_restore_client, windows_restore_location, \
                self._subclient.content
        )
        if self._nas_helper.nas_vendor(self._client) != 'Isilon':
            self._log.info("*" * 10 + " Run deferred cataloging on the storage policy " + "*" * 10)
            self.snapshot_cataloging()

            self._log.info("*" * 10 + "Run out of place restore to Filer from deferred catalog" +
                           "*" * 10)

            copy_precedence = self._get_copy_precedence(
                self._subclient.storage_policy, snap_copy_name
            )
            job = self._subclient.restore_out_of_place(self._client.client_name,
                                                       filer_restore_location,
                                                       self._subclient.content,
                                                       copy_precedence=int(copy_precedence),
                                                       fs_options=fs_options)
            self._log.info(
                "Started Restore out of place to filer job with Job ID: %d", job.job_id
            )
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore out of place job with error:%s", job.delay_reason
                )
            self._log.info("Successfully finished Restore out of place to Filer from catalog")
            self._nas_helper.validate_filer_to_filer_restored_content(
                self.nas_client, self._subclient.content, filer_restore_location
            )
        job = self._run_backup("FULL")

        if isinstance(self.nas_client, NetAPPClient):
            volume_path, _ = self.nas_client.get_path_from_content(self._subclient.content[0])
            self._nas_helper.copy_test_data(self.nas_client, volume_path)
            self.revert_snap(job.job_id, snap_copy_name)
            self.revert_validation(job.job_id, snap_copy_name)
        time.sleep(60)
        self.delete_snap(job.job_id, snap_copy_name)
        self.delete_validation(job.job_id, snap_copy_name)

        self.cleanup()
        self._nas_helper.delete_nre_destinations(windows_restore_client, windows_restore_location)
        self._nas_helper.delete_nre_destinations(linux_restore_client, linux_restore_location)
        
        
    def replication_template(self, replica_type):
        """Executes Intellisnap basic acceptance test for Replication"""
        self._log.info(
            "Will run below test case on: %s subclient", format(str(self._inputs['SubclientName']))
        )
        self._log.info("Number of data readers: " + str(self._subclient.data_readers))
        if self._subclient.data_readers != 3:
            self._log.info("Setting the data readers count to 3")
            self._subclient.data_readers = 3
            
        self._log.info("Get NAS Client object")
        self.nas_client = self._nas_helper.get_nas_client(self._client, self._agent,
                                                          is_cluster=self._is_cluster)

        self._log.info("Make a CIFS Share connection")
        self.nas_client.connect_to_cifs_share(
            str(self._inputs['CIFSShareUser']), str(self._inputs['CIFSSharePassword'])
        )
        
        filer_restore_location = (str(self._inputs['FilerRestoreLocation']))
        
        self.delete_replica_copy()
        replica_copy = self.create_replica_copy(replica_type)
        
        for content in self._subclient.content:
            volume_path, _ = self.nas_client.get_path_from_content(content)
            self._nas_helper.copy_test_data(self.nas_client, volume_path)
            
        full_job = self._run_backup("FULL")
        
        for content in self._subclient.content:
            volume_path, _ = self.nas_client.get_path_from_content(content)
            self._nas_helper.copy_test_data(self.nas_client, volume_path)
        
        inc_job = self._run_backup("INCREMENTAL")
        
        for content in self._subclient.content:
            volume_path, _ = self.nas_client.get_path_from_content(content)
            self._nas_helper.copy_test_data(self.nas_client, volume_path)
            
        diff_job = self._run_backup("DIFFERENTIAL")
        time.sleep(30)

        self.run_aux_copy()
        copy_precedence = self._get_copy_precedence(
            self._subclient.storage_policy, replica_copy
        )

        self.mount_snap(full_job.job_id, replica_copy, destclient=self.mounthost)
        self.mount_validation(full_job.job_id, replica_copy, destclient=self.mounthostobj)
        self.unmount_snap(full_job.job_id, replica_copy)
        self.unmount_validation(full_job.job_id, replica_copy)
        
        options_selector = OptionsSelector(self._commcell)

        size = self.nas_client.get_content_size(self._subclient.content)
        if self._inputs.get('liveBrowse'):
            if self._inputs['liveBrowse'].upper() == 'TRUE':
                fs_options = {'live_browse': True}

        if self._inputs.get("WindowsDestination"):
            windows_client = Machine(self._inputs["WindowsDestination"], self._commcell)
            windows_restore_client, windows_restore_location = self._nas_helper.restore_to_selected_machine(
                options_selector, windows_client=windows_client, size=size
            )
        else:
            windows_restore_client, windows_restore_location = \
                options_selector.get_windows_restore_client(size=size)
        
        self._log.info("*" * 10 + " Run out of place restore to Windows Client from Replica Copy " + "*" * 10)

        job = self._subclient.restore_out_of_place(
            windows_restore_client.machine_name,
            windows_restore_location,
            self._subclient.content,
            copy_precedence=int(copy_precedence),
            fs_options=fs_options
        )
        self._log.info(
            "Started Restore out of place to Windows client job with Job ID: " + str(job.job_id)
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: " + str(job.delay_reason)
            )

        self._log.info("Successfully finished Restore out of place to windows client")

        self._nas_helper.validate_windows_restored_content(
            self.nas_client, windows_restore_client, windows_restore_location, \
                self._subclient.content
        )
        
        self._log.info("*" * 10 + " Run out of place restore to Filer from Replica snap" + "*" * 10)
        filer_restore_location = str(self._inputs['FilerRestoreLocation'])

        job = self._subclient.restore_out_of_place(
            self._client.client_name,
            filer_restore_location,
            self._subclient.content,
            copy_precedence=int(copy_precedence),
            fs_options=fs_options)

        self._log.info(
            "Started Restore out of place to filer job with Job ID: %s}", format(job.job_id)
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: {0}".format(job.delay_reason)
            )

        self._log.info("Successfully finished Restore out of place to Filer")

        self._nas_helper.validate_filer_restored_content(
            self.nas_client, windows_restore_client, windows_restore_location,
            self._subclient.content, filer_restore_location
        )
        
        self._log.info("*" * 10 + "Updating replica copy as source for backup copy & snapshot catalog" + "*" * 10)
        options = {
            'enable_backup_copy': True,
            'source_copy_for_snap_to_tape': replica_copy,
            'enable_snapshot_catalog': True,
            'source_copy_for_snapshot_catalog': replica_copy,
            'is_ocum': None,
            'disassociate_sc_from_backup_copy': None
        }
        self._storage_policy.update_snapshot_options(**options)

        self._log.info("*" * 10 + "Running backup copy from Replica Copy" + "*" * 10)
        self.run_backup_copy()

        self._log.info("*" * 10 + "Run out of place restore to Filer from backupcopy" + "*" * 10)
        backup_copy_name = self.execute_query(self.get_backup_copy, self._storage_policy.storage_policy_id)
        copy_precedence = self._get_copy_precedence(
            self._subclient.storage_policy, backup_copy_name
        )
        
        job = self._subclient.restore_out_of_place(self._client.client_name,
                                                       filer_restore_location,
                                                       self._subclient.content,
                                                       copy_precedence=int(copy_precedence)
                                                       )
        self._log.info(
                "Started Restore out of place to filer job with Job ID: %d", job.job_id
            )
        if not job.wait_for_completion():
            raise Exception(
                    "Failed to run restore out of place job with error:%s", job.delay_reason
            )
        self._log.info("Successfully finished Restore out of place to Filer from backup copy")
        self._nas_helper.validate_filer_to_filer_restored_content(
            self.nas_client, self._subclient.content, filer_restore_location
        )

        options_selector = OptionsSelector(self._commcell)

        size = self.nas_client.get_content_size(self._subclient.content)

        if self._inputs.get("WindowsDestination"):
            windows_client = Machine(self._inputs["WindowsDestination"], self._commcell)
            windows_restore_client, windows_restore_location = self._nas_helper.restore_to_selected_machine(
                options_selector, windows_client=windows_client, size=size
            )
        else:
            windows_restore_client, windows_restore_location = \
                options_selector.get_windows_restore_client(size=size)
                
        self._log.info("*" * 10 + "Run out of place restore to windows client from backupcopy"
                       + "*" * 10)

        job = self._subclient.restore_out_of_place(
            windows_restore_client.machine_name,
            windows_restore_location,
            self._subclient.content,
            copy_precedence=int(copy_precedence)
        )
        self._log.info(
            "Started Restore out of place to Windows client job with Job ID: " + str(job.job_id)
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: " + str(job.delay_reason)
            )

        self._log.info("Successfully finished Restore out of place to windows client from backup copy")

        self._nas_helper.validate_windows_restored_content(
            self.nas_client, windows_restore_client, windows_restore_location, \
                self._subclient.content
        )

        self._log.info("*" * 10 + " Run Restore in place from backup copy " + "*" * 10)
        copy_precedence = self._get_copy_precedence(
            self._subclient.storage_policy, backup_copy_name
        )

        job = self._subclient.restore_in_place(
            self._subclient.content, copy_precedence=int(copy_precedence)
        )

        self._log.info(
            "Started restore in place from backup copy job with Job ID: %s", format(job.job_id)
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to restore from backup copy with error: {0}".format(str(job.delay_reason))
            )

        self._log.info("Successfully finished Restore in place from backup copy")

        self._nas_helper.validate_filer_restored_content(
            self.nas_client, windows_restore_client, windows_restore_location, \
                self._subclient.content
        )

        self._log.info("*" * 10 + " Run deferred cataloging using Replica snap " + "*" * 10)
        self.snapshot_cataloging()

        self._log.info("*" * 10 + "Run out of place restore to Filer from deferred catalog" + "*" * 10)
        copy_precedence = self._get_copy_precedence(
            self._subclient.storage_policy, replica_copy
        )
        job = self._subclient.restore_out_of_place(self._client.client_name,
                                                       filer_restore_location,
                                                       self._subclient.content,
                                                       copy_precedence=int(copy_precedence)
                                                       )
        self._log.info(
                "Started Restore out of place to filer job with Job ID: %d", job.job_id
            )
        if not job.wait_for_completion():
            raise Exception(
                    "Failed to run restore out of place job with error:%s", job.delay_reason
            )
        self._log.info("Successfully finished Restore out of place to Filer from deferred catalog")
        
        self._nas_helper.validate_filer_to_filer_restored_content(
            self.nas_client, self._subclient.content, filer_restore_location
        )

        self.delete_snap(full_job.job_id, replica_copy)
        self.delete_snap(inc_job.job_id, replica_copy)
        self.delete_snap(diff_job.job_id, replica_copy)
        self.delete_validation(diff_job.job_id, replica_copy)
        self.delete_replica_copy(replica_copy)
        
        self.cleanup()
        self._nas_helper.delete_nre_destinations(windows_restore_client, windows_restore_location)
