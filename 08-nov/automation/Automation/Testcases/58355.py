# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase to perform force delete mountpath

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    _validate_library_delete()  --  To validate whether library is deleted from MMLibrary

    _validate_deleted_mplist_sidb()    --  To validate whether force deleted mountpath were sent to DDB

    _validate_mountpath_delete_type()   --  To validate mountpath deletion type

    _get_sidb_list()   --  Gets all sidb store id linked to mountpath data

    _validate_deleted_mp2ddb()   --  To validate whether mountpath to DDB entries populated in MMDeletedMPToDDB

    _validate_mmtask()  --   To validate whether mountpath entry populated in MMTask

    _validate_mmvol_deleted()   --  To validate whether volumes are deleted from MMVolume

    _validate_mmmp_delete()    --  To validate whether mountpath is deleted from MMMountPath

    _validate_dv2_job_launch()  --  To validate whether quick DV2 job was launched on the associated DDBs

    _validate_force_delete_mountpath()    --  To validate whether mountpath was force deleted

    _get_volume_list()         --  Gets all volumes linked to mountpath

    _get_mountpath_info()       --  Gets top first mountpath info from library id

    _force_delete_mountpath()    --  Force deletes the specified mountpath

    _cleanup()                  --  cleanup the entities created

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    tear_down()                 --  teardown function of this test case

    Input Example:
            "58355": {
                "ClientName": "Client1",
                "AgentName": "File System",
                "MediaAgentName": "MediaAgent1"
            }
"""

from AutomationUtils import (constants, commonutils)
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from MediaAgents.MAUtils.mahelper import MMHelper, DedupeHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.name = "Force delete mountpath"
        self.tcinputs = {
            "MediaAgentName": None
        }
        self.disk_library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.mountpath1 = None
        self.mountpath2 = None
        self.mountpath3 = None
        self.partition_path = None
        self.content_path = None
        self.restore_dest_path = None
        self.client_machine = None
        self.ma_machine = None
        self.common_util = None
        self.mmhelper = None
        self.dedupehelper = None
        self.wf_obj = None

    def _validate_library_delete(self, library_id):
        """
            To validate whether library is deleted from MMLibrary

                Args:
                 library_id (int) -- Library Id
        """
        self.log.info("validating whether library is deleted from MMLibrary")

        query = f"""
                    SELECT 1
                    FROM MMLibrary WITH(NOLOCK)
                    WHERE LibraryId = {library_id}
                """
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] == '1':
            self.log.error("validating library is deleted from MMLibrary failed")
            raise Exception("validating library is deleted from MMLibrary failed")
        self.log.info("Library is deleted from MMLibrary")

    def _validate_deleted_mplist_sidb(self, mountpath_list):
        """
            To validate whether force deleted mountpath were sent to DDB

                Args:
                 mountpath_list (list) -- list of mountpath_id
        """
        self.log.info("validating whether force deleted mountpath were sent to DDB")

        log_line = fr"""Disabled mount paths \[{mountpath_list[0]}:1 {mountpath_list[1]}:1 \]"""

        matched_string = self.dedupehelper.parse_log(self.tcinputs['MediaAgentName'], 'SIDBEngine.log', log_line,
                                                     escape_regex=False, single_file=True)[1]
        if matched_string:
            self.log.info("Force deleted mountpath were sent to DDB as %s", matched_string[0])
        else:
            self.log.error("Expected log line %s not found", log_line)
            raise Exception("Expected log line {0} not found".format(log_line))

    def _validate_mountpath_delete_type(self, mountpath_id, delete_type):
        """
            To validate mountpath deletion type

                Args:
                 mountpath_id (int) -- mountpath id

                 delete_type (int) -- deletion type (2-Physical_cleanup, 3-DB_cleanup)
        """
        self.log.info("validating mountpath deletion type")

        log_line = fr"Mountpath\[{mountpath_id}\] needs force delete confirmation return code\[{delete_type}.*"

        matched_string = self.dedupehelper.parse_log(self.commcell.commserv_name, 'EvMgrS.log', log_line,
                                                     escape_regex=False, single_file=True)[1]
        if matched_string:
            self.log.info("Force deletion type verified from log : %s", matched_string[0])
        else:
            self.log.error("Expected log line %s for force delete not found.", log_line)
            raise Exception("Expected log line {0} for force delete not found.".format(log_line))

    def _validate_deleted_mp2ddb(self, mountpath_id, sidb_list):
        """
            To validate whether mountpath to DDB entries populated in MMDeletedMPToDDB

                Args:
                 mountpath_id (int) -- mountpath_id

                 sidb_list (list) -- list of sidb store ids
        """
        self.log.info("Validating whether mountpath to DDB entries populated in MMDeletedMPToDDB")

        query = f"""
                    SELECT 1
                    FROM MMDeletedMPToDDB WITH(NOLOCK)
                    WHERE MountPathId = {mountpath_id}
                    AND	SIDBStoreId {'= %s' % sidb_list[0] if len(sidb_list) == 1 else 'IN %s' % str(tuple(sidb_list))}
                """
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != '1':
            self.log.error("Validating mountpath to DDB entries populated in MMDeletedMPToDDB failed")
            raise Exception("Validating mountpath to DDB entries populated in MMDeletedMPToDDB failed")
        self.log.info("Mountpath to DDB entries populated in MMDeletedMPToDDB")

    def _validate_mmvol_deleted(self, vol_list):
        """
            To validate whether volumes are deleted from MMVolume

                Args:
                 vol_list (list) -- list of volume ids
        """
        self.log.info("validating whether volumes are deleted from MMVolume")

        query = f"""
                    SELECT 1
                    FROM MMVolume WITH(NOLOCK)
                    WHERE VolumeId  {'= %s' % vol_list[0] if len(vol_list) == 1 else 'IN %s' % str(tuple(vol_list))}
                """
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] == '1':
            self.log.error("validating volumes are deleted from MMVolume failed")
            raise Exception("validating volumes are deleted from MMVolume failed")
        self.log.error("Volumes are deleted from MMVolume")

    def _validate_mmmp_delete(self, mountpath_id):
        """
            To validate whether mountpath is deleted from MMMountPath

                Args:
                 mountpath_id (int) -- mountpath id
        """
        self.log.info("validating whether mountpath is deleted from MMMountPath")

        query = f"""
                    SELECT 1
                    FROM MMMountPath WITH(NOLOCK)
                    WHERE MountPathId = {mountpath_id}
                """
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] == '1':
            self.log.error("validating mountpath is deleted from MMMountPath failed")
            raise Exception("validating mountpath is deleted from MMMountPath failed")
        self.log.info("Mountpath is deleted from MMMountPath")

    def _validate_mmtask(self, mountpath_name, delete_type):
        """
            To validate whether mountpath entry populated in MMTask

                Args:
                 mountpath_name (str) -- mountpath_name

                 delete_type (int) -- deletion type (2-Physical_cleanup, 3-DB_cleanup)
        """
        self.log.error("Validating whether mountpath entry populated in MMTask")

        query = f"""
                    SELECT 1
                    FROM MMTask WITH(NOLOCK)
                    WHERE MetaData.value('(/EVGui_DeletedMPDetails/@MountPath)[1]', 'varchar(max)') 
                    = '{mountpath_name}'
                """
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if (cur[0] != '1' and delete_type == 2) or (cur[0] == '1' and delete_type == 3):
            self.log.error("Validating mountpath entry populated in MMTask failed")
            raise Exception("Validating mountpath entry populated in MMTask failed")
        self.log.info("Mountpath entry populated in MMTask")

    def _validate_dv2_job_launch(self, mountpath_id, sidb_status):
        """
            To validate whether quick DV2 job was launched on the associated DDBs

                Args:
                 mountpath_id (int) -- mountpath id
                 sidb_status (int) -- indicate the store status  (1-Active Store, 2-Sealed Store, 3-Corrupted Store)
        """
        self.log.info("validating DV2 job launch")

        log_line = fr"DV2 JobsList.* started for Force delete MPs .*MountPath id=\"{mountpath_id}\".*"

        matched_string = self.dedupehelper.parse_log(self.commcell.commserv_name, 'EvMgrS.log', log_line,
                                                     escape_regex=False, single_file=True)[1]
        if (matched_string and (sidb_status == 1)) or (not matched_string and (sidb_status in (2, 3))):
            self.log.info("Validation success for DV2 Launch")
            if matched_string:
                self.log.info("Matched string - %s", matched_string[0])
        else:
            self.log.error("Validation failed for DV2 Launch")
            raise Exception("Validation failed for DV2 Launch")

    def _validate_force_delete_mountpath(self, mountpath_info, delete_type, sidb_list, volume_list, sidb_status):
        """
            To validate whether mountpath was force deleted
                Args:
                 mountpath_info (list) -- list of mountpath_id, mountpath_name

                 delete_type (int) -- deletion type (2-Physical_cleanup, 3-DB_cleanup)

                 sidb_list (list) -- list of sidb store ids

                 volume_list (list) -- list of volume ids

                 sidb_status (int) -- status of the sidb (1-Active Store, 2-Sealed Store, 3-Corrupted Store)
        """
        self.log.info("Validating force delete mountpath")
        self._validate_mountpath_delete_type(mountpath_info[0], delete_type)
        self._validate_deleted_mp2ddb(mountpath_info[0], sidb_list)
        self._validate_mmvol_deleted(volume_list)
        self._validate_mmmp_delete(mountpath_info[0])
        self._validate_mmtask(mountpath_info[1], delete_type)
        self._validate_dv2_job_launch(mountpath_info[0], sidb_status)

    def _get_volume_list(self, mountpath_id):
        """
            Gets all volumes linked to mountpath
            Args:
                mountpath_id (int)  --  Mountpath Id
            Returns:
                list - volume linked to mountpath
        """
        self.log.info("Getting volumes linked to mountpath")

        query = f"""
                    SELECT DISTINCT MV.VolumeId
                    FROM MMVolume MV WITH(NOLOCK), MMMountPath MP WITH(NOLOCK)
                    WHERE MV.MediaSideId = MP.MediaSideId
                    AND MP.MountPathId = {mountpath_id}
                """

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_all_rows()
        if cur[0] != ['']:
            cur = [x[0] for x in cur]
            self.log.info("RESULT: %s", cur)
            return cur
        self.log.error("No volumes linked to mountpath")
        raise Exception("No volumes linked to mountpath")

    def _get_sidb_list(self, mountpath_id):
        """
            Gets all sidb store id linked to mountpath data
            Args:
                mountpath_id (int)  --  Mountpath Id
            Returns:
                list - sidb store id linked to mountpath data
        """
        self.log.info("Getting sidb store id linked to mountpath")

        query = f"""
                    SELECT DISTINCT MV.SIDBStoreId
                    FROM MMVolume MV WITH(NOLOCK), MMMountPath MP WITH(NOLOCK)
                    WHERE MV.MediaSideId = MP.MediaSideId
                    AND MP.MountPathId = {mountpath_id}
                    AND MV.SIDBStoreId > 0
                    AND MV.VolumeFlags <> 6 
                """
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_all_rows()
        if cur[0] != ['']:
            cur = [int(x[0]) for x in cur]
            self.log.info("RESULT: %s", cur)
            return cur
        self.log.error("No sidb linked to mountpath")
        raise Exception("No sidb linked to mountpath")

    def _get_mountpath_info(self, library_id):
        """
        Gets top first mountpath info from library id
        Args:
            library_id (int)  --  Library Id

        Returns:
            list - (mountpath_id, mountpath_name)
                    First mountpath info  for the given library id
        """

        self.log.info("Getting  first mountpath info from library id")

        query = f"""
                    SELECT	MM.MountPathId,  MDC.Folder + '/' + MM.MountPathName
                    FROM	MMMountPath MM WITH(NOLOCK), MMMountPathToStorageDevice MPSD WITH(NOLOCK)
                            , MMDeviceController MDC WITH(NOLOCK)
                    WHERE	MM.LibraryId = {library_id} and MM.MountPathId = MPSD.MountPathId 
                            and MDC.DeviceId = MPSD.DeviceId
                    ORDER BY MM.MountPathId DESC
                """
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur)
        if cur != ['']:
            return [int(cur[0]), cur[1]]
        self.log.error("No mountpath entries present")
        raise Exception("Invalid LibraryId")

    def _force_delete_mountpath(self, mountpath):
        """ Force deletes the specified mountpath

            Args:
                mountpath (str)  --  name of the mountpath to delete
        """
        self.log.info("Force Deleting mountpath %s", mountpath)
        request_json = {
            "EVGui_ConfigureStorageLibraryReq":
                {
                    "isConfigRequired": 1,
                    "library": {
                        "opType": 1024,
                        "mediaAgentName": self.tcinputs['MediaAgentName'],
                        "libraryName": self.disk_library_name,
                        "mountPath": mountpath
                    }
                }
        }

        self.commcell.qoperation_execute(request_json)

    def _cleanup(self):
        """Cleanup the entities created"""

        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            # Delete backupset
            self.log.info("Deleting BackupSet: %s if exists", self.backupset_name)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Deleted BackupSet: %s", self.backupset_name)

            # Delete Storage Policy
            self.log.info("Deleting storage policy: %s if exists", self.storage_policy_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
                self.log.info("Deleted storage policy: %s", self.storage_policy_name)

            # Delete Library
            self.log.info("Deleting library: %s if exists", self.disk_library_name)
            if self.commcell.disk_libraries.has_library(self.disk_library_name):
                self.commcell.disk_libraries.delete(self.disk_library_name)
                self.log.info("Deleted library: %s", self.disk_library_name)

        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception("Error encountered during cleanup: {0}".format(str(exp)))

        self.log.info("********************** CLEANUP COMPLETED *************************")

    def setup(self):
        """Setup function of this test case"""

        options_selector = OptionsSelector(self.commcell)
        self.disk_library_name = '%s_disklib-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                                   self.tcinputs['ClientName'])
        self.storage_policy_name = '%s_policy-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                                    self.tcinputs['ClientName'])
        self.backupset_name = '%s_bs-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                           self.tcinputs['ClientName'])
        self.client_machine = Machine(self.client)
        self.ma_machine = Machine(self.tcinputs['MediaAgentName'], self.commcell)

        self._cleanup()

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(self.client_machine, size=25 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating content")
        self.log.info('selected drive: %s', client_drive)

        # DDB partition path
        if self.tcinputs.get("PartitionPath") is not None:
            self.partition_path = self.tcinputs['PartitionPath']
        else:
            if self.ma_machine.os_info.lower() == 'unix':
                self.log.error("LVM enabled DDB partition path must be an input for the unix MA.")
                raise Exception("LVM enabled partition path not supplied for Unix MA!..")

        # To select drive with space available in Media agent machine
        self.log.info('Selecting drive in the Media agent machine based on space available')
        ma_drive = options_selector.get_drive(self.ma_machine, size=25 * 1024)
        if ma_drive is None:
            raise Exception("No free space for hosting ddb and mount paths")
        self.log.info('selected drive: %s', ma_drive)

        self.partition_path = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'DDB')

        self.mountpath1 = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP1')
        self.mountpath2 = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP2')
        self.mountpath3 = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP3')

        self.content_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'TestData')
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
        self.client_machine.create_directory(self.content_path)
        self.restore_dest_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'RestoreData')
        if self.client_machine.check_directory_exists(self.restore_dest_path):
            self.client_machine.remove_directory(self.restore_dest_path)
        self.client_machine.create_directory(self.restore_dest_path)

        self.mmhelper = MMHelper(self)
        self.dedupehelper = DedupeHelper(self)
        self.common_util = CommonUtils(self)

    def run(self):
        """Run function of this test case"""

        try:
            # Generating content
            self.mmhelper.create_uncompressable_data(self.tcinputs["ClientName"], self.content_path, 1.0)

            # Create disk library
            disk_lib_obj = self.mmhelper.configure_disk_library(self.disk_library_name,
                                                                self.tcinputs['MediaAgentName'], self.mountpath1)
            mp1_info = self._get_mountpath_info(disk_lib_obj.library_id)

            # Create dedupe storage policy
            self.dedupehelper.configure_dedupe_storage_policy(self.storage_policy_name, self.disk_library_name,
                                                              self.tcinputs['MediaAgentName'], self.partition_path)
            # Create backupset
            self.mmhelper.configure_backupset(self.backupset_name, self.agent)

            # Create subclient
            subclient_name = "%s_SC1" % str(self.id)
            sc_obj = self.mmhelper.configure_subclient(self.backupset_name, subclient_name, self.storage_policy_name,
                                                       self.content_path, self.agent)

            # Allow multiple data readers to subclient
            self.log.info("Setting Data Readers to 10 on Subclient")
            sc_obj.data_readers = 10
            sc_obj.allow_multiple_readers = True

            # Run Full backup job
            self.common_util.subclient_backup(sc_obj, "FULL")

            # Add another mountpath to library
            self.mmhelper.configure_disk_mount_path(disk_lib_obj, self.mountpath2, self.tcinputs['MediaAgentName'])

            # Disable workflow 'DeleteLibraryMountPathAuthorization'
            if self.commcell.workflows.has_workflow('DeleteLibraryMountPathAuthorization'):
                self.wf_obj = self.commcell.workflows.get('DeleteLibraryMountPathAuthorization')
                self.log.info("Workflow DeleteLibraryMountPathAuthorization original flag value %s before disabling",
                              self.wf_obj.flags)
                self.log.info("Now Disabling workflow DeleteLibraryMountPathAuthorization")
                self.wf_obj.disable()
                self.log.info("Workflow DeleteLibraryMountPathAuthorization has flag value %s after disabling",
                              self.wf_obj.flags)
                if self.wf_obj.flags & 1 != 1:
                    self.log.error("Workflow DeleteLibraryMountPathAuthorization is not disabled")
                    raise Exception("Workflow DeleteLibraryMountPathAuthorization is not disabled")

            # Force delete mountpath1
            sidb_list1 = self._get_sidb_list(mp1_info[0])
            vol_list1 = self._get_volume_list(mp1_info[0])
            self._force_delete_mountpath(self.mountpath1)

            # validate physical cleanup of mountpath1 deletion
            physical_cleanup = 2
            active_store = 1
            self._validate_force_delete_mountpath(mp1_info, physical_cleanup, sidb_list1, vol_list1, active_store)

            # Run Full backup job
            self.common_util.subclient_backup(sc_obj, "FULL")

            # Set read only access on mountpath2
            disk_lib_obj.mount_path = self.mountpath2
            ma_obj = self.commcell.media_agents.get(self.tcinputs['MediaAgentName'])
            mp2_info = self._get_mountpath_info(disk_lib_obj.library_id)
            device_id = self.mmhelper.get_device_id(mp2_info[0])
            device_controller_id = self.mmhelper.get_device_controller_id(mp2_info[0], ma_obj.media_agent_id)
            self.log.info("Setting read only access on mountpath")
            disk_lib_obj.change_device_access_type(mp2_info[0], device_id, device_controller_id,
                                                   int(ma_obj.media_agent_id), 4)

            # add another mountpath to library
            self.mmhelper.configure_disk_mount_path(disk_lib_obj, self.mountpath3, self.tcinputs['MediaAgentName'])

            sidb_list2 = self._get_sidb_list(mp2_info[0])
            vol_list2 = self._get_volume_list(mp2_info[0])
            # seal the stores
            for store_id in sidb_list2:
                self.dedupehelper.seal_ddb(self.storage_policy_name, 'Primary', store_id)
            # Force delete mountpath2
            self._force_delete_mountpath(self.mountpath2)

            # validate DB-only cleanup of mountpath2 deletion
            db_cleanup = 3
            sealed_store = 2
            self._validate_force_delete_mountpath(mp2_info, db_cleanup, sidb_list2, vol_list2, sealed_store)

            # Run Full backup job
            self.common_util.subclient_backup(sc_obj, "FULL")

            # validate deleted mp list on SIDB Engine
            self._validate_deleted_mplist_sidb([mp1_info[0], mp2_info[0]])

            # Restore out of place
            restore_job = sc_obj.restore_out_of_place(self.client, self.restore_dest_path, [self.content_path])
            self.log.info("restore job [%s] has started.", restore_job.job_id)
            if not restore_job.wait_for_completion():
                self.log.error("restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
                raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                                restore_job.delay_reason))
            self.log.info("restore job [%s] has completed.", restore_job.job_id)

            # Verify restored data
            if self.client_machine.os_info == 'UNIX':
                dest_path = commonutils.remove_trailing_sep(self.restore_dest_path, '/')
            else:
                dest_path = commonutils.remove_trailing_sep(self.restore_dest_path, '\\')

            dest_path = self.client_machine.join_path(dest_path, "TestData")

            self.log.info("Comparing source:%s destination:%s", self.content_path, dest_path)
            # comparing content data with restored data
            if self.client_machine.compare_folders(self.client_machine, self.content_path, dest_path):
                self.log.error("Restored data is different from content data")
                raise Exception("Restored data is different from content data")
            self.log.info("Restored data is same as content data")

            mp3_info = self._get_mountpath_info(disk_lib_obj.library_id)
            sidb_list3 = self._get_sidb_list(mp3_info[0])
            vol_list3 = self._get_volume_list(mp3_info[0])

            # corrupt the store
            for store_id in sidb_list3:
                self.dedupehelper.mark_substore_for_recovery(self.storage_policy_name, 'Primary', store_id)

            # Force delete mountpath3
            self._force_delete_mountpath(self.mountpath3)
            self.commcell.disk_libraries.refresh()

            # validate physical cleanup of mountpath1 deletion
            physical_cleanup = 2
            corrupt_store = 3
            self._validate_force_delete_mountpath(mp3_info, physical_cleanup, sidb_list3, vol_list3, corrupt_store)

            # validate library delete as part of last mp deletion
            self._validate_library_delete(disk_lib_obj.library_id)

        except Exception as exp:
            self.log.error('Failed to execute test case with error:%s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down function of this test case"""

        # Enable workflow 'DeleteLibraryMountPathAuthorization'
        if self.commcell.workflows.has_workflow('DeleteLibraryMountPathAuthorization'):
            self.wf_obj = self.commcell.workflows.get('DeleteLibraryMountPathAuthorization')
            self.log.info("Workflow DeleteLibraryMountPathAuthorization flag value %s before enabling",
                          self.wf_obj.flags)
            self.log.info("Now Enabling workflow DeleteLibraryMountPathAuthorization")
            self.wf_obj.enable()
            self.log.info("Workflow DeleteLibraryMountPathAuthorization has flag value %s after enabling",
                          self.wf_obj.flags)

        # Remove content and restored data
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
        if self.client_machine.check_directory_exists(self.restore_dest_path):
            self.client_machine.remove_directory(self.restore_dest_path)

        self._cleanup()
