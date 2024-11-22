# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase to perform move mountpath operation.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    _get_mountpath_name(library_id)  --  to get a mountpath name from libraryId

    _restore_verify             --  validates restored data with original data

    _cleanup()                  --  Cleanup the entities created

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    tear_down()                 --  teardown function of this test case

Sample Input:
"54748": {
            "ClientName": "skclient",
            "AgentName": "File System",
            "MediaAgentName": "skma",
    }
"""

from AutomationUtils import (constants, commonutils)
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
        self.name = "MA Acceptance - Move MountPath"
        self.tcinputs = {
            "MediaAgentName": None
        }
        self.disk_library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.subclient_name = None
        self.source_mountpath = None
        self.target_mountpath = None
        self.partition_path = None
        self.content_path = None
        self.dedupehelper = None
        self.library_name = None
        self.mmhelper = None
        self.common_util = None
        self.ma_machine = None
        self.client_machine = None

    def _get_mountpath_name(self, library_id):
        """
        Get a first Mountpath Name from LibraryId
        Agrs:
            library_id (int)  --  Library Id
        Returns:
            First Mountpath name for the given Library id
        """

        query = """ SELECT	MM.MountPathName
                    FROM	MMMountPath MM
                    WHERE	MM.LibraryId = {0}""".format(library_id)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != ['']:
            return cur[0]
        self.log.error("No entries present")
        raise Exception("Invalid LibraryId.")

    def _restore_verify(self, machine, src_path, dest_path):
        """
            Performs the verification after restore

            Args:
                machine          (object)    --  Machine class object.

                src_path         (str)       --  path on source machine that is to be compared.

                dest_path        (str)       --  path on destination machine that is to be compared.

            Raises:
                Exception - Any difference from source data to destination data

        """
        self.log.info("Comparing source:%s destination:%s", src_path, dest_path)
        diff_output = machine.compare_folders(machine, src_path, dest_path)

        if not diff_output:
            self.log.info("Checksum comparison successful")
        else:
            self.log.error("Checksum comparison failed")
            self.log.info("Diff output: \n%s", diff_output)
            raise Exception("Checksum comparison failed")

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
        ma_drive = options_selector.get_drive(self.ma_machine, size=40 * 1024)
        if ma_drive is None:
            raise Exception("No free space for hosting ddb and mount paths")
        self.log.info('selected drive: %s', ma_drive)

        self.partition_path = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'DDB')

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(self.client_machine, size=40 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating data")
        self.log.info('selected drive: %s', client_drive)

        self.source_mountpath = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id),
                                                          'Source_MP_%s' % timestamp_suffix)

        self.target_mountpath = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id),
                                                          'Target_MP_%s' % timestamp_suffix)

        self.content_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'Testdata')
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
        self.client_machine.create_directory(self.content_path)
        self.restore_dest_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'Restoredata')
        if self.client_machine.check_directory_exists(self.restore_dest_path):
            self.client_machine.remove_directory(self.restore_dest_path)
        self.client_machine.create_directory(self.restore_dest_path)

    def run(self):
        """Run function of this test case"""

        try:
            lib_obj = self.mmhelper.configure_disk_library(self.disk_library_name, self.tcinputs['MediaAgentName'],
                                                           self.source_mountpath)
            self.dedupehelper.configure_dedupe_storage_policy(self.storage_policy_name,
                                                              self.disk_library_name,
                                                              self.tcinputs['MediaAgentName'],
                                                              self.partition_path)

            self.backupset = self.mmhelper.configure_backupset(self.backupset_name, self.agent)
            sc_obj = self.mmhelper.configure_subclient(self.backupset_name, self.subclient_name,
                                                       self.storage_policy_name, self.content_path, self.agent)

            # Allow multiple data readers to subclient
            self.log.info("Setting Data Readers=4 on Subclient")
            sc_obj.data_readers = 4
            sc_obj.allow_multiple_readers = True

            for i in range(0, 5):
                # Create unique content
                self.log.info("Generating Data at %s", self.content_path)
                if not self.mmhelper.create_uncompressable_data(self.client_machine, self.content_path, 0.1, 10):
                    self.log.error("unable to Generate Data at %s", self.content_path)
                    raise Exception("unable to Generate Data at {0}".format(self.content_path))
                self.log.info("Generated Data at %s", self.content_path)
                self.log.info("Sleeping for 10 seconds before running backup job.")
                sleep(10)
                self.common_util.subclient_backup(sc_obj, "full",
                                                  advanced_options={'mediaOpt': {'startNewMedia': True}})

            ma_obj = self.commcell.media_agents.get(self.tcinputs['MediaAgentName'])

            mountpath_name = self._get_mountpath_name(lib_obj.library_id)

            mount_path_id = self.mmhelper.get_mount_path_id(mountpath_name)

            src_device_path = self.ma_machine.join_path(
                self.mmhelper.get_device_path(mount_path_id, ma_obj.media_agent_id), mountpath_name)

            # Move MountPath
            move_mountpath_jobid = lib_obj.move_mountpath(mount_path_id, src_device_path, int(ma_obj.media_agent_id),
                                                          self.target_mountpath, int(ma_obj.media_agent_id))
            self.log.info("Move Mountpath Job %s has started.", move_mountpath_jobid.job_id)
            if not move_mountpath_jobid.wait_for_completion():
                self.log.error("Move Mountpath job [%s] has failed with %s.",
                               move_mountpath_jobid.job_id, move_mountpath_jobid.delay_reason)
                raise Exception("Move Mountpath job [{0}] has failed with {1}.".format(
                    move_mountpath_jobid.job_id, move_mountpath_jobid.delay_reason))
            self.log.info("Move Mountpath completed successfully")

            target_device_path = self.ma_machine.join_path(
                self.mmhelper.get_device_path(mount_path_id, ma_obj.media_agent_id), mountpath_name)

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

            # Restore from moved mountpath
            restore_job = sc_obj.restore_out_of_place(self.client, self.restore_dest_path,
                                                      [self.content_path])
            self.log.info("restore job [%s] has started from primary copy.", restore_job.job_id)
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

            dest_path = self.client_machine.join_path(dest_path, 'Testdata')

            self._restore_verify(self.client_machine, self.content_path, dest_path)

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
