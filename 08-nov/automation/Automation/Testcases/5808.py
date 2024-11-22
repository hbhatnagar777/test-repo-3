# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# gitlab
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase to perform tape media spanning

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    _check_for_spare_media()    --  check if spare group has only two spare media for the given library and spare group

    _validate_volumes_created() --  to validate whether volumes created on both MPs for the given backup job

    _validate_archFile()        --  to validate whether only one ArchFile created on spanning media

    _cleanup()                  --  cleanup the entities created

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    tear_down()                 --  teardown function of this test case

Inputs:

    ClientName      --      Client used for creating backupset and subclient

    AgentName       --      iDA used for creating backupset and subclient

    LibraryName     --      Tape library name configure as prerequisite for this testcase

    MediaAgentName  --      Media agent name configured on the tape library

    DrivePool       --      Drive pool used for creating storage policy

    SpareGroup     --      Spare Group name with atleast two spare media

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
        self.name = "Tape - Media Spanning"
        self.tcinputs = {
            "MediaAgentName": None,
            "LibraryName": None,
            "DrivePool": None,
            "ScratchPool": None,
        }
        self.tape_library_name = None
        self.drive_pool = None
        self.scratch_pool = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.client_machine = None
        self.ma_machine = None
        self.content_path = None
        self.common_util = None
        self.mmhelper = None

    def _check_for_spare_media(self, library_name, sparegroup_name):
        """
        Checks if spare group has only two spare media for the given library and spare group
            Args:
             library_name -- Tape library name

             sparegroup_name -- spare media group name
        """

        self.log.info("checking if spare group has only two spare media")

        query = f"""SELECT	COUNT(MM.MediaId)
                    FROM	MMMedia	MM
                    JOIN	MMSpareGroup MSG
                            ON	MSG.SpareGroupId = MM.SpareGroupId
                    JOIN	MMVolume	MV
                            ON	MV.MediaId = MM.MediaId
                    JOIN	MMLibrary	ML
                            ON	ML.LibraryId = MM.LibraryId
                    WHERE	MM.MediaLocation<>3
                            AND	MV.VolumeFlags IN (5)
                            AND	MSG.SpareGroupName = '{sparegroup_name}'
                            AND ML.AliasName = '{library_name}'"""

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != '' and int(cur[0]) >= 2:
            return True
        return False

    def _validate_volumes_created(self, job_id):
        """
        To validate whether volumes created on both MPs for the given backup job
            Args:
             job_id -- JobId
        """

        self.log.info("validate whether volumes created on both MPs for the backup job")

        query = f"""SELECT	count(distinct  MV.MediaSideId)
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
        query = f"""select	MM.MediaId, count(distinct AF.id)
                    from	archFile AF
                    JOIN	archChunkMapping ACM
                            ON AF.id = ACM.archFileId
                    JOIN	archChunk AC
                            ON	AC.id = ACM.archChunkId
                    JOIN	MMVolume MV
                            ON	MV.VolumeId = AC.volumeId
                    JOIN	MMMedia MM
                            ON	MM.MediaId = MV.MediaId
                    WHERE	MM.LibraryId ={library_id}
                    GROUP BY MM.MediaId"""

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_all_rows()
        if (cur[0][1], cur[1][1]) == ('1', '3') or (cur[0][1], cur[1][1]) == ('3', '1'):
            return True
        return False

    def _cleanup(self):
        """Cleanup the entities created"""

        self.log.info("********************** CLEANUP STARTING *************************")
        try:
            # Delete bkupset
            self.log.info("Deleting BackupSet: %s if exists", self.backupset_name)
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("Deleted BackupSet: %s", self.backupset_name)

            # Delete Storage Policy
            self.log.info("Deleting storage policy: %s if exists", self.storage_policy_name)
            if self.commcell.storage_policies.has_policy(self.storage_policy_name):
                self.commcell.storage_policies.delete(self.storage_policy_name)
                self.log.info("Deleted storage policy: %s", self.storage_policy_name)

            # Run DataAging
            data_aging_job = self.commcell.run_data_aging()
            self.log.info("Data Aging job [%s] has started.", data_aging_job.job_id)
            if not data_aging_job.wait_for_completion():
                self.log.error(
                    "Data Aging job [%s] has failed with %s.", data_aging_job.job_id, data_aging_job.delay_reason)
                raise Exception(
                    "Data Aging job [{0}] has failed with {1}.".format(data_aging_job.job_id,
                                                                       data_aging_job.delay_reason))
            self.log.info("Data Aging job [%s] has completed.", data_aging_job.job_id)

        except Exception as exp:
            self.log.error("Error encountered during cleanup : %s", str(exp))
            raise Exception("Error encountered during cleanup: {0}".format(str(exp)))

        self.log.info("********************** CLEANUP COMPLETED *************************")

    def setup(self):
        """Setup function of this test case"""

        self.tape_library_name = self.tcinputs['LibraryName']
        self.drive_pool = self.tcinputs['DrivePool']
        self.scratch_pool = self.tcinputs['ScratchPool']
        self.storage_policy_name = '%s_policy' % (str(self.id))
        self.backupset_name = '%s_bs' % (str(self.id))
        options_selector = OptionsSelector(self.commcell)
        self.client_machine = options_selector.get_machine_object(self.client)
        self.ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgentName'])

        self._cleanup()

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(self.client_machine, size=5 * 1024)
        if client_drive is None:
            raise Exception("No free space for generating content")
        self.log.info('selected drive: %s', client_drive)

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
            if self._check_for_spare_media(self.tape_library_name, self.scratch_pool):

                self.log.info("Generating Data at %s", self.content_path)
                self.mmhelper.create_uncompressable_data(self.tcinputs["ClientName"], self.content_path, 6)
                self.log.info("Generated Data at %s", self.content_path)

                content_size = int(self.client_machine.get_folder_size(self.content_path))
                self.log.info('Content size generated on client machine : %sMB', content_size)

                if content_size < 4096:
                    raise Exception("Content Size is less than 4GB")
                if content_size > 8192:
                    raise Exception("Content Size is more than 8GB")

                # create Non-Dedupe storage policy
                sp_obj = self.commcell.storage_policies.add_tape_sp(self.storage_policy_name, self.tape_library_name,
                                                           self.tcinputs["MediaAgentName"],
                                                           self.drive_pool, self.scratch_pool)
                sp_primary_obj = sp_obj.get_copy("Primary")
                sp_primary_obj.set_copy_software_compression(False)
                self.log.info("Disabled s/w compression on copy")

                # create backupset
                self.mmhelper.configure_backupset(self.backupset_name, self.agent)

                # create subclient
                subclient1_name = "%s_SC" % str(self.id)
                sc1_obj = self.mmhelper.configure_subclient(self.backupset_name, subclient1_name,
                                                            self.storage_policy_name, self.content_path,
                                                            self.agent)

                # Allow multiple data readers to subclient
                self.log.info("Setting Data Readers=1 on Subclient")
                sc1_obj.data_readers = 1
                sc1_obj.allow_multiple_readers = True

                backup_job = self.common_util.subclient_backup(sc1_obj, "FULL")

                # validate whether volumes created on both MPs for the backup job
                if not self._validate_volumes_created(backup_job.job_id):
                    raise Exception("Mountpath Spanning failed.")

                # validate whether single archFile is created
                tape_lib_obj = self.commcell.disk_libraries.get(self.tape_library_name)
                self._validate_archFile(tape_lib_obj.library_id)

                # Restore
                restore_job = sc1_obj.restore_in_place([self.content_path])
                self.log.info("restore job [%s] has started.", restore_job.job_id)
                if not restore_job.wait_for_completion():
                    self.log.error("restore job [%s] has failed with %s.", restore_job.job_id, restore_job.delay_reason)
                    raise Exception("restore job [{0}] has failed with {1}.".format(restore_job.job_id,
                                                                                    restore_job.delay_reason))
                self.log.info("restore job [%s] has completed.", restore_job.job_id)
            else:
                raise Exception("Given spare group do not have two spare media or had more two.")

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
