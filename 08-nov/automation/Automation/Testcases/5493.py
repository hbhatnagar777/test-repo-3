# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase to perform magnetic mount path spanning

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    _size_megabytes()           --  converts given size to megabytes

    _validate_volumes_created() --  to validate whether volumes created on both MPs for the given backup job

    _validate_archFile()        --  to validate whether only one ArchFile created on spanning media

    _get_mountpath_id()         --  gets the first mountpath id on library from library id

    _cleanup()                  --  cleanup the entities created

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    tear_down()                 --  teardown function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from MediaAgents.MAUtils.mahelper import MMHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.name = "Magnetic MountPath Spanning"
        self.tcinputs = {
            "MediaAgentName": None
        }
        self.disk_library_name = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.client_machine = None
        self.ma_machine = None
        self.mountpath1 = None
        self.mountpath2 = None
        self.content_path = None
        self.common_util = None
        self.mmhelper = None

    @staticmethod
    def _size_megabytes(input_size, units):
        """
        Converts given size to megabytes
        Args:
            input_size: Input size that need to be converted

            units: Input units
        """
        multiplier = 1
        if any([units == 'Gigabytes', units == 'Gigabyte', units == 'GB']):
            multiplier = 1024
        elif any([units == 'Terabytes', units == 'Terabyte', units == 'TB']):
            multiplier = 1048576
        elif any([units == 'Petabytes', units == 'Petabyte', units == 'PB']):
            multiplier = 1073741824
        else:
            Exception("Please specify correct units")
        return input_size*multiplier

    def _validate_volumes_created(self, job_id):
        """
        To validate whether volumes created on both MPs for the given backup job
            Args:
             job_id -- JobId
        """

        self.log.info("validating whether volumes created on both MPs for the backup job")
        query = f"""SELECT	COUNT(DISTINCT MV.MediaSideId)
                    FROM	MMVolume MV
                    JOIN	archChunk AC
                        ON	MV.VolumeId = AC.volumeId
                    JOIN    archChunkMapping ACM
                        ON  ACM.archChunkId = AC.id
                    WHERE	ACM.jobId = {job_id}"""

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] == '2':
            return True
        return False

    def _validate_archFile(self, library_id):
        """
        To validate whether only one ArchFile created on spanning media
            Args:
             library_id -- libraryId
        """

        self.log.info("validate whether only one ArchFile created on spanning media")

        query = f"""SELECT	MP.MountPathId, COUNT(DISTINCT AF.id)
                    FROM	archFile AF
                    JOIN	archChunkMapping ACM
                            ON AF.id = ACM.archFileId
                    JOIN	archChunk AC
                            ON	AC.id = ACM.archChunkId
                    JOIN	MMVolume MV
                            ON	MV.VolumeId = AC.volumeId
                    JOIN	MMMountPath MP
                            ON	MP.MediaSideId = MV.MediaSideID
                    WHERE	MP.LibraryId ={library_id}
                    GROUP BY MP.MountPathId"""

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_all_rows()
        if (cur[0][1], cur[1][1]) == ('1', '3') or (cur[0][1], cur[1][1]) == ('3', '1'):
            return True
        return False

    def _get_mountpath_id(self, library_id):
        """
        Gets first mountpath id from library id
        Agrs:
            library_id (int)  --  Library Id
        Returns:
            First mountpath id for the given library id
        """

        self.log.info("Getting  first mountpath id from library id")

        query = """ SELECT	MM.MountPathId
                    FROM	MMMountPath MM
                    JOIN    MMLibrary ML
                            ON  ML.LibraryId = MM.LibraryId
                    WHERE	ML.LibraryId = {0}
                    ORDER BY MM.MountPathId DESC""".format(library_id)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != '':
            return int(cur[0])
        self.log.error("No entries present")
        raise Exception("Invalid LibraryId.")

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
        self.disk_library_name = '%s_disklib' % str(self.id)
        self.storage_policy_name = '%s_storage_policy' % str(self.id)
        self.backupset_name = '%s_BS' % str(self.id)
        self.client_machine = options_selector.get_machine_object(self.client)
        self.ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgentName'])

        self._cleanup()

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(self.client_machine, size=10 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating content")
        self.log.info('selected drive: %s', client_drive)

        # To select drive with space available in Media agent machine
        self.log.info('Selecting drive in the Media agent machine based on space available')
        ma_drive = options_selector.get_drive(self.ma_machine, size=10 * 1024)
        if ma_drive is None:
            raise Exception("No free space for hosting ddb and mount paths")
        self.log.info('selected drive: %s', ma_drive)

        self.mountpath1 = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP1')
        self.mountpath2 = self.ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP2')

        self.log.info('Creating content folder on client')
        self.content_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'TestData')
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
        self.client_machine.create_directory(self.content_path)

        self.mmhelper = MMHelper(self)
        self.common_util = CommonUtils(self)

    def run(self):
        """Run function of this test case"""

        try:
            # Generating content
            self.log.info("Generating Data at %s on client machine", self.content_path)
            self.mmhelper.create_uncompressable_data(self.tcinputs["ClientName"], self.content_path, 9.0)
            self.log.info("Generated Data at %s", self.content_path)

            content_size = int(self.client_machine.get_folder_size(self.content_path))
            self.log.info('Content size generated on client machine : %s MB', content_size)

            # Create disk library
            disk_lib_obj = self.mmhelper.configure_disk_library(self.disk_library_name, self.tcinputs['MediaAgentName'],
                                                                self.mountpath1)
            disk_lib_obj.media_agent = self.tcinputs['MediaAgentName']

            # set fill and spill on library
            disk_lib_obj.mountpath_usage = 'FILL_AND_SPILL'
            self.log.info("setting FILL AND SPILL on library done")

            # set prefer mountpath according to MA on library
            disk_lib_obj.set_mountpath_preferred_on_mediaagent(True)
            self.log.info("setting prefer mp according to ma on library done")

            disk_lib_property = disk_lib_obj.free_space
            free_space = self._size_megabytes(round(float(disk_lib_property[:len(disk_lib_property)-2]),2),
                                              disk_lib_property[len(disk_lib_property) - 2:])
            self.log.info("Free space on Mountpath1: %s MB", free_space)

            if content_size > free_space:
                raise Exception("Content Size is more than free space")

            reserved_space = free_space - (content_size / 1.5)
            self.log.info("Reserved space to be set: %s MB", reserved_space)

            # set reserved space on mountpath1
            disk_lib_obj.set_mountpath_reserve_space(self.mountpath1, reserved_space)
            self.log.info("setting reserved space on mountpath1 done")

            # add another mountpath to library
            self.mmhelper.configure_disk_mount_path(disk_lib_obj, self.mountpath2, self.tcinputs['MediaAgentName'])

            # unset preferred on mountpath2
            disk_lib_obj.mount_path = self.mountpath2
            ma_obj = self.commcell.media_agents.get(self.tcinputs['MediaAgentName'])
            mountpath_id = self._get_mountpath_id(disk_lib_obj.library_id)
            device_id = self.mmhelper.get_device_id(mountpath_id)
            device_controller_id = self.mmhelper.get_device_controller_id(mountpath_id, ma_obj.media_agent_id)
            disk_lib_obj.change_device_access_type(mountpath_id, device_id, device_controller_id,
                                                   int(ma_obj.media_agent_id), 6)
            self.log.info("Unset mountpath2 as preferred on mountpath2 done")

            # create Non-Dedupe storage policy
            sp_obj = self.mmhelper.configure_storage_policy(self.storage_policy_name, self.disk_library_name,
                                                            self.tcinputs['MediaAgentName'])

            sp_primary_obj = sp_obj.get_copy("Primary")
            sp_primary_obj.set_copy_software_compression(False)
            self.log.info("Disabled s/w compression on copy")

            # create backupset
            self.mmhelper.configure_backupset(self.backupset_name, self.agent)

            # create subclient
            subclient1_name = "%s_SC1" % str(self.id)
            sc1_obj = self.mmhelper.configure_subclient(self.backupset_name, subclient1_name, self.storage_policy_name,
                                                        self.content_path, self.agent)

            # set single data readers to subclient
            self.log.info("Setting Data Readers=1 on Subclient")
            sc1_obj.allow_multiple_readers = True
            sc1_obj.data_readers = 1

            # Run Full backup job
            backup_job = self.common_util.subclient_backup(sc1_obj, "FULL")

            # validate whether volumes created on both MPs for the backup job
            if not self._validate_volumes_created(backup_job.job_id):
                raise Exception("Mountpath Spanning failed.")

            # validate whether single archFile is created
            self._validate_archFile(disk_lib_obj.library_id)

            # Restore
            restore_job = sc1_obj.restore_in_place([self.content_path])
            self.log.info("restore job [%s] has started.", restore_job.job_id)
            if not restore_job.wait_for_completion():
                self.log.error("restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
                raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                                restore_job.delay_reason))
            self.log.info("restore job [%s] has completed.", restore_job.job_id)

        except Exception as exp:
            self.log.error('Failed to execute test case with error:%s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear Down function of this test case"""

        if self.status != constants.FAILED:
            self.log.info("Testcase shows successful execution, cleaning up the test environment ...")
            self._cleanup()
        else:
            self.log.error("Testcase shows failure in execution, not cleaning up the test environment ...")

        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
