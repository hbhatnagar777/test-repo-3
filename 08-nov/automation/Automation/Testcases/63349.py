# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase to perform move mountpath to existing device operation.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    _get_mountpath_info()       --  get the most recent mountpath info added to the library

    _validate_non_default_flag()    --  validating whether non default flag was set on source mountpath

    _validate_old_device_delete()   --  validating whether old device was deleted

    _validate_device_change()       --  validating whether source mountpath is moved to target device

    _db_validation()            --  DB Validation for move to existing device

    _validate_new_device()      --  validating whether mountpaths moved to new device

    _validate_single_default_mp()   --  validating whether only single mountpath was not set with non default flag

    _db_validation_move_new_location()  --  validating whether non default flag was set on source mountpath

    _physical_validation()      --  physical validation of source and target mountpath after move

    _restore_validation()       --  restore validation after move

    _cleanup()                  --  cleanup the entities created

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    tear_down()                 --  teardown function of this test case

Sample Input:
"63349": {
            "ClientName": "Client1",
            "AgentName": "File System",
            "MediaAgentName": "MediaAgent1",
    }
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from MediaAgents.MAUtils.mahelper import (MMHelper, DedupeHelper)
from time import sleep


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Move MountPath to existing device"
        self.tcinputs = {
            "MediaAgentName": None
        }
        self.disk_library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.partition_path = None
        self.content_path = None
        self.dedupehelper = None
        self.library_name = None
        self.mmhelper = None
        self.common_util = None
        self.ma_machine = None
        self.client_machine = None

    def _get_mountpath_info(self, library_id):
        """
            Get the most recent mountpath info added to the library
            Args:
                library_id (int)  --  Id of library

            Returns:
                Most recent mountpath id and name added to the library
        """

        query = f"""
                    SELECT	MM.MountPathId,  MM.MountPathName
                    FROM	MMMountPath MM WITH(NOLOCK)
                    WHERE	MM.LibraryId = {library_id}
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

    def _validate_non_default_flag(self, source_mountpath, target_mountpath):
        """
            Validating whether non default flag was set on source mountpath
            Args:
                source_mountpath (str)  --  Id of source mountpath

                target_mountpath (str)  --  Id of target mountpath
        """
        self.log.info("validating whether non default flag was set on source mountpath")

        query = f"""
                    SELECT 1
                    FROM MMMountPath WITH(NOLOCK)
                    WHERE MountPathId = {source_mountpath} 
                    AND Attribute&262144 = 262144 --MNTPTH_ATTRIB_IS_NON_DEFAULT_MOUNT_PATH 
                """
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != '1':
            self.log.error("validating whether non default flag was set on source mountpath failed")
            raise Exception("validating whether non default flag was set on source mountpath failed")
        self.log.info("Non default flag was set on source mountpath")

        self.log.info("validating whether non default flag was not set on target mountpath")
        query = f"""
                    SELECT 1
                    FROM MMMountPath WITH(NOLOCK)
                    WHERE MountPathId = {target_mountpath} 
                    AND Attribute&262144 = 0 --MNTPTH_ATTRIB_IS_NON_DEFAULT_MOUNT_PATH 
                """
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != '1':
            self.log.error("validating whether non default flag was not set on target mountpath failed")
            raise Exception("validating whether non default flag was not set on target mountpath failed")
        self.log.info("Non default flag was not set on target mountpath")

    def _validate_old_device_delete(self, old_device_id):
        """
            Validating whether old device was deleted
            Args:
                old_device_id (str)  --  Id of source mountpath's old device
        """
        self.log.info("validating whether old device was deleted")
        query = f"""
                    SELECT 1
                    FROM MMDevice WITH(NOLOCK)
                    WHERE DeviceId = {old_device_id} 
                """
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] == '1':
            self.log.error("validating whether old device was deleted failed")
            raise Exception("validating whether old device was deleted failed")
        self.log.info("Old device was deleted")

    def _validate_device_change(self, source_mountpath_id, target_mp_device_id):
        """
            Validating whether source mountpath is moved to target device
            Args:
                source_mountpath_id (str)  --  Id of source mountpath

                target_mp_device_id (str)  --  Id of target mountpath's device
        """
        self.log.info("validating whether source mountpath is moved to target device")

        new_device_id = self.mmhelper.get_device_id(source_mountpath_id)

        if new_device_id != target_mp_device_id:
            self.log.error("validating whether source mountpath is moved to target device failed")
            raise Exception("validating whether source mountpath is moved to target device failed")
        self.log.info("Source mountpath is moved to target device")

    def _db_validation(self, source_mountpath, target_mountpath):
        """
            DB Validation for move to existing device
            Args:
                source_mountpath (str)  --  Id of source mountpath

                target_mountpath (str)  --  Id of target mountpath
        """
        self.log.info("DB Validation for move to existing device")
        self._validate_non_default_flag(source_mountpath[0], target_mountpath[0])
        self._validate_device_change(source_mountpath[0], target_mountpath[1])
        self._validate_old_device_delete(source_mountpath[1])

    def _validate_new_device(self, library_id, old_device_id):
        """
            Validating whether mountpaths moved to new device
            Args:
                library_id (str)  --  Id of library

                old_device_id (str)  --  Id of old device
        """
        self.log.info("validating whether mountpaths moved to new device")

        query = f"""
                    SELECT COUNT(1)
                    FROM MMMountPath MP WITH(NOLOCK), MMMountPathToStorageDevice MPSD WITH(NOLOCK)
                    WHERE MP.MountPathId = MPSD.MountPathId
                    AND MP.LibraryId = {library_id} 
                    AND MPSD.DeviceId = {old_device_id} 
                """
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != '0':
            self.log.error("validating whether mountpaths moved to new device failed")
            raise Exception("validating whether mountpaths moved to new device failed")
        self.log.info("Mountpaths moved to new device")

    def _validate_single_default_mp(self, library_id):
        """
            Validating whether only single mountpath was not set with non default flag
            Args:
                library_id (str)  --  Id of library
        """
        self.log.info("validating whether only single mountpath was not set with non default flag")

        query = f"""
                    SELECT COUNT(1)
                    FROM MMMountPath WITH(NOLOCK)
                    WHERE LibraryId = {library_id} 
                    AND Attribute&262144 = 0 --MNTPTH_ATTRIB_IS_NON_DEFAULT_MOUNT_PATH 
                """
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != '1':
            self.log.error("validating whether only single mountpath was not set with non default flag failed")
            raise Exception("validating whether only single mountpath was not set with non default flag failed")
        self.log.info("Only single mountpath was not set with non default flag")

    def _db_validation_move_new_location(self, library_id, old_device_id):
        """
            Validating whether non default flag was set on source mountpath
            Args:
                library_id (str)  --  Id of library

                old_device_id (str)  --  Id of old device
        """
        self.log.info("DB Validation for move to new location")
        self._validate_single_default_mp(library_id)
        self._validate_new_device(library_id, old_device_id)
        self._validate_old_device_delete(old_device_id)

    def _physical_validation(self, src_device_path, target_device_path):
        """
            Physical validation of source and target mountpath after move
            Args:
                src_device_path (str)  --  path of source mountpath

                target_device_path (str)  --  path of target mountpath
        """
        self.log.info("Physical validation of source and target mountpath after move")

        self.log.info("wait for 6 minutes to allow rename of the source path")
        sleep(360)

        # Check if .obsolete file exists on original source path if not check on renamed source path
        if not self.ma_machine.check_file_exists(self.ma_machine.join_path(src_device_path, '.obsolete')):
            src_device_path = '%s_RENAMED' % src_device_path
            if not self.ma_machine.check_file_exists(self.ma_machine.join_path(src_device_path, '.obsolete')):
                self.log.error(".obsolete file is missing on source path")
                raise Exception(".obsolete file is missing on source path")
        self.log.info(".obsolete file present on source path")

        # Physical chunks validation
        if self.ma_machine.compare_folders(self.ma_machine, src_device_path,
                                           target_device_path, ['media', 'mountpath', '.obsolete']):
            self.log.error("Chunks are different on source and destination after move mountpath")
            raise Exception("Chunks are different on source and destination after move mountpath")
        self.log.info("Chunks are same on source and destination after move mountpath")

    def _restore_validation(self, content_path, bkp_content_folder):
        """
            Restore validation after move
            Args:
                content_path (str)  --  path of content to restore

                bkp_content_folder (str)  --  folder of content restored
        """
        self.log.info("Restore validation after move")
        # Restore from moved mountpath
        if self.client_machine.check_directory_exists(self.restore_dest_path):
            self.client_machine.remove_directory(self.restore_dest_path)

        restore_job = self.sc_obj.restore_out_of_place(self.client, self.restore_dest_path,
                                                       [content_path])
        self.log.info("restore job [%s] has started.", restore_job.job_id)
        if not restore_job.wait_for_completion():
            self.log.error("restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
            raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                            restore_job.delay_reason))
        self.log.info("restore job [%s] has completed.", restore_job.job_id)

        # Verify restored data

        dest_path = self.client_machine.join_path(self.restore_dest_path, bkp_content_folder)

        self.log.info("Comparing source:%s destination:%s", content_path, dest_path)
        diff_output = self.client_machine.compare_folders(self.client_machine, content_path, dest_path)

        if not diff_output:
            self.log.info("Checksum comparison successful")
        else:
            self.log.error("Checksum comparison failed")
            self.log.info("Diff output: \n%s", diff_output)
            raise Exception("Checksum comparison failed")

    def _run_backup(self, content_path):
        """
            Create unique content and run incremental backup
            Args:
                content_path (str)  --  path to generate test data
        """
        self.log.info("Generating Data at %s", content_path)
        if not self.mmhelper.create_uncompressable_data(self.client_machine, content_path, 0.1, 10):
            self.log.error("unable to Generate Data at %s", content_path)
            raise Exception("unable to Generate Data at {0}".format(content_path))
        self.log.info("Generated Data at %s", content_path)
        self.log.info("Sleeping for 10 seconds before running backup job.")
        sleep(10)
        self.common_util.subclient_backup(self.sc_obj, "incremental",
                                          advanced_options={'mediaOpt': {'startNewMedia': True}})

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
            self.log.info("Deleting Storage Policy: %s if exists", self.storage_policy_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
                self.log.info("Deleted Storage Policy: %s", self.storage_policy_name)

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
        timestamp_suffix = options_selector.get_custom_str()
        self.disk_library_name = '%s_disklib-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                                   self.tcinputs['ClientName'])
        self.storage_policy_name = '%s_policy-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                                   self.tcinputs['ClientName'])
        self.backupset_name = '%s_bs-ma(%s)-client(%s)' % (str(self.id), self.tcinputs['MediaAgentName'],
                                                                   self.tcinputs['ClientName'])
        self.subclient_name = '%s_SC' % str(self.id)
        self.ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgentName'])
        self.client_machine = options_selector.get_machine_object(self.tcinputs['ClientName'])
        self.mmhelper = MMHelper(self)
        self.dedupehelper = DedupeHelper(self)
        self.common_util = CommonUtils(self)

        self._cleanup()

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

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(self.client_machine, size=25 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating data")
        self.log.info('selected drive: %s', client_drive)

        self.source_mountpath_1 = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id),
                                                            'Source_MP1_%s' % timestamp_suffix)
        self.source_mountpath_2 = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id),
                                                            'Source_MP2_%s' % timestamp_suffix)
        self.target_mountpath = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id),
                                                          'Target_MP_%s' % timestamp_suffix)
        self.target_mountpath_new_location = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id),
                                                                       'Target_MP_New_Location_%s' % timestamp_suffix)

        self.content_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'Testdata')
        self.bkp_content_src_mp_1 = self.client_machine.join_path(self.content_path, 'bkp_content_src_mp_1')
        self.bkp_content_src_mp_2 = self.client_machine.join_path(self.content_path, 'bkp_content_src_mp_2')
        self.bkp_content_target_mp = self.client_machine.join_path(self.content_path, 'bkp_content_target_mp')
        self.restore_dest_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'Restoredata')

        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)

        if self.client_machine.check_directory_exists(self.restore_dest_path):
            self.client_machine.remove_directory(self.restore_dest_path)

    def run(self):
        """Run function of this test case"""

        try:
            lib_obj = self.mmhelper.configure_disk_library(self.disk_library_name, self.tcinputs['MediaAgentName'],
                                                           self.source_mountpath_1)
            self.dedupehelper.configure_dedupe_storage_policy(self.storage_policy_name,
                                                              self.disk_library_name,
                                                              self.tcinputs['MediaAgentName'],
                                                              self.partition_path)

            self.backupset = self.mmhelper.configure_backupset(self.backupset_name, self.agent)
            self.sc_obj = self.mmhelper.configure_subclient(self.backupset_name, self.subclient_name,
                                                            self.storage_policy_name, self.content_path, self.agent)

            # Allow multiple data readers to subclient
            self.log.info("Setting Data Readers=4 on Subclient")
            self.sc_obj.data_readers = 4
            self.sc_obj.allow_multiple_readers = True

            # Create unique content and run incremental backup
            self._run_backup(self.bkp_content_src_mp_1)

            media_agent_id = self.commcell.media_agents.get(self.tcinputs['MediaAgentName']).media_agent_id

            # Get source mountpath 1 info
            source_mp_1_info = self._get_mountpath_info(lib_obj.library_id)
            source_mp_1_device_id = self.mmhelper.get_device_id(source_mp_1_info[0])
            source_mp_1_device_cntrl_id = self.mmhelper.get_device_controller_id(source_mp_1_info[0], media_agent_id)

            # Set read only access on source mountpath 1
            lib_obj.mount_path = self.source_mountpath_1
            self.log.info("Setting read only access on source mountpath 1")
            lib_obj.change_device_access_type(source_mp_1_info[0], source_mp_1_device_id, source_mp_1_device_cntrl_id,
                                              int(media_agent_id), 4)

            # Add another mountpath to library
            self.mmhelper.configure_disk_mount_path(lib_obj, self.source_mountpath_2, self.tcinputs['MediaAgentName'])

            # Create unique content and run incremental backup
            self._run_backup(self.bkp_content_src_mp_2)

            # Get source mountpath 2 info
            source_mp_2_info = self._get_mountpath_info(lib_obj.library_id)
            source_mp_2_device_id = self.mmhelper.get_device_id(source_mp_2_info[0])
            source_mp_2_device_cntrl_id = self.mmhelper.get_device_controller_id(source_mp_2_info[0], media_agent_id)

            # Set read only access on source mountpath 2
            self.log.info("Setting read only access on source mountpath 2")
            lib_obj.mount_path = self.source_mountpath_2
            lib_obj.change_device_access_type(source_mp_2_info[0], source_mp_2_device_id, source_mp_2_device_cntrl_id,
                                              int(media_agent_id), 4)

            # Add another mountpath to library
            self.mmhelper.configure_disk_mount_path(lib_obj, self.target_mountpath, self.tcinputs['MediaAgentName'])

            # Create unique content and run incremental backup
            self._run_backup(self.bkp_content_target_mp)

            # Get target mountpath info
            target_mp_info = self._get_mountpath_info(lib_obj.library_id)
            target_mp_device_id = self.mmhelper.get_device_id(target_mp_info[0])

            source_mp_1_device_path = self.ma_machine.join_path(self.source_mountpath_1, source_mp_1_info[1])

            # Move MountPath to move source_mountpath_1 to source_mountpath_2
            move_mountpath_jobid = lib_obj.move_mountpath(source_mp_1_info[0], self.source_mountpath_1,
                                                          int(media_agent_id),
                                                          self.source_mountpath_2, int(media_agent_id),
                                                          source_mp_2_device_id)
            self.log.info("Move Mountpath Job %s has started to move [%s] to existing device [%s].",
                          move_mountpath_jobid.job_id, self.source_mountpath_1, self.source_mountpath_2)
            if not move_mountpath_jobid.wait_for_completion():
                self.log.error("Move Mountpath job [%s] has failed with %s.",
                               move_mountpath_jobid.job_id, move_mountpath_jobid.delay_reason)
                raise Exception("Move Mountpath job [{0}] has failed with {1}.".format(
                    move_mountpath_jobid.job_id, move_mountpath_jobid.delay_reason))
            self.log.info("Move Mountpath completed successfully")

            source_mp_1_new_device_path = self.ma_machine.join_path(self.source_mountpath_2, source_mp_1_info[1])

            # Move Mountpath Validation
            self._db_validation([source_mp_1_info[0], source_mp_1_device_id],
                                [source_mp_2_info[0], source_mp_2_device_id])
            self._physical_validation(source_mp_1_device_path, source_mp_1_new_device_path)
            self._restore_validation(self.bkp_content_src_mp_1, 'bkp_content_src_mp_1')

            source_mp_1_device_path = source_mp_1_new_device_path
            source_mp_1_device_id = source_mp_2_device_id
            source_mp_2_device_path = self.ma_machine.join_path(self.source_mountpath_2, source_mp_2_info[1])

            # Move MountPath to move consolidated source_mountpath_2 to target_mountpath
            move_mountpath_job_list = lib_obj.move_mountpath(source_mp_2_info[0], self.source_mountpath_2,
                                                             int(media_agent_id),
                                                             self.target_mountpath, int(media_agent_id),
                                                             target_mp_device_id)

            for move_mountpath_jobid in move_mountpath_job_list:
                self.log.info("Move Mountpath Job %s has started to move consolidated [%s] to existing device [%s].",
                              move_mountpath_jobid.job_id, self.source_mountpath_2, self.target_mountpath)
                if not move_mountpath_jobid.wait_for_completion():
                    self.log.error("Move Mountpath job [%s] has failed with %s.",
                                   move_mountpath_jobid.job_id, move_mountpath_jobid.delay_reason)
                    raise Exception("Move Mountpath job [{0}] has failed with {1}.".format(
                        move_mountpath_jobid.job_id, move_mountpath_jobid.delay_reason))
                self.log.info("Move Mountpath completed successfully")

            source_mp_1_new_device_path = self.ma_machine.join_path(self.target_mountpath, source_mp_1_info[1])

            # Move Mountpath Validation
            self._db_validation([source_mp_1_info[0], source_mp_1_device_id],
                                [target_mp_info[0], target_mp_device_id])
            self._physical_validation(source_mp_1_device_path, source_mp_1_new_device_path)
            self._restore_validation(self.bkp_content_src_mp_1, 'bkp_content_src_mp_1')

            source_mp_2_new_device_path = self.ma_machine.join_path(self.target_mountpath, source_mp_2_info[1])

            # Move Mountpath Validation
            self._db_validation([source_mp_2_info[0], source_mp_2_device_id],
                                [target_mp_info[0], target_mp_device_id])
            self._physical_validation(source_mp_2_device_path, source_mp_2_new_device_path)
            self._restore_validation(self.bkp_content_src_mp_2, 'bkp_content_src_mp_2')

            source_mp_1_device_path = source_mp_1_new_device_path
            source_mp_2_device_path = source_mp_2_new_device_path

            target_mp_device_path = self.ma_machine.join_path(self.target_mountpath, target_mp_info[1])

            # Move MountPath to move target_mountpath to new location
            move_mountpath_job_list = lib_obj.move_mountpath(target_mp_info[0], self.target_mountpath,
                                                             int(media_agent_id),
                                                             self.target_mountpath_new_location,
                                                             int(media_agent_id))

            for move_mountpath_jobid in move_mountpath_job_list:
                self.log.info("Move Mountpath Job %s has started to move consolidated [%s] to new location [%s].",
                              move_mountpath_jobid.job_id, self.target_mountpath, self.target_mountpath_new_location)
                if not move_mountpath_jobid.wait_for_completion():
                    self.log.error("Move Mountpath job [%s] has failed with %s.",
                                   move_mountpath_jobid.job_id, move_mountpath_jobid.delay_reason)
                    raise Exception("Move Mountpath job [{0}] has failed with {1}.".format(
                        move_mountpath_jobid.job_id, move_mountpath_jobid.delay_reason))
                self.log.info("Move Mountpath completed successfully")

            # Move Mountpath Validation
            self._db_validation_move_new_location(lib_obj.library_id, target_mp_device_id)

            source_mp_1_new_device_path = self.ma_machine.join_path(self.target_mountpath_new_location,
                                                                    source_mp_1_info[1])
            self._physical_validation(source_mp_1_device_path, source_mp_1_new_device_path)
            self._restore_validation(self.bkp_content_src_mp_1, 'bkp_content_src_mp_1')

            source_mp_2_new_device_path = self.ma_machine.join_path(self.target_mountpath_new_location,
                                                                    source_mp_2_info[1])
            self._physical_validation(source_mp_2_device_path, source_mp_2_new_device_path)
            self._restore_validation(self.bkp_content_src_mp_2, 'bkp_content_src_mp_2')

            target_mp_new_device_path = self.ma_machine.join_path(self.target_mountpath_new_location, target_mp_info[1])
            self._physical_validation(target_mp_device_path, target_mp_new_device_path)
            self._restore_validation(self.bkp_content_target_mp, 'bkp_content_target_mp')

            # Run a full backup after move to new location
            self.common_util.subclient_backup(self.sc_obj, "full")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down function of this test case"""

        if self.status != constants.FAILED:
            self.log.info("Testcase shows successful execution, cleaning up the test environment ...")
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
            if self.client_machine.check_directory_exists(self.restore_dest_path):
                self.client_machine.remove_directory(self.restore_dest_path)
            self._cleanup()
        else:
            self.log.error("Testcase shows failure in execution, not cleaning up the test environment ...")
