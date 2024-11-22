# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase to perform tape media verification

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    _cleanup()                  --  cleanup the entities created

    _check_for_spare_media()    --  Checks if spare group has only two spare media for the given library and spare group

    _get_assigned_media_drive() --  To get assigned media drive

    _get_assigned_media()       --  To get assigned media from the given library and spare group

    _get_no_oml_media()         --  To get no oml media from the given library and spare group

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    tear_down()                 --  teardown function of this test case

Inputs:

    ClientName      --      Client used for creating backupset and subclient

    AgentName       --      iDA used for creating backupset and subclient

    LibraryName     --      Tape library name configure with two sparegroups as prerequisite for this testcase

    MediaAgentName  --      Media agent name configured on the tape library

    DrivePool       --      Drive pool used for creating storage policy

    SpareGroup1     --      Spare Group name with atleast one new media which is never used for backup

    SpareGroup2     --      Spare Group name with atleast one media
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from MediaAgents.MAUtils.mahelper import (MMHelper, DedupeHelper)


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.name = "Tape - Media Verification"
        self.tcinputs = {
            "LibraryName": None,
            "MediaAgentName": None,
            "DrivePool": None,
            "SpareGroup1": None,
            "SpareGroup2": None
        }
        self.tape_library_name = None
        self.drive_pool = None
        self.scratch_pool = None
        self.storage_policy_name = None
        self.backupset_name = None
        self.client_machine = None
        self.content_path = None
        self.no_oml_media = None
        self.assigned_media = None
        self.common_util = None
        self.mmhelper = None
        self.dedupehelper = None

    def _check_for_spare_media(self, spare_group_name):
        """
         Checks if spare group has only two spare media for the given library and spare group

            Args:
             spare_group_name -- spare media group name
        """

        self.log.info("checking if spare group has only two spare media for the library and spare group")

        query = f"""SELECT	MM.MediaId
                    FROM	MMMedia	MM
                    JOIN	MMSpareGroup MSG
                            ON	MSG.SpareGroupId = MM.SpareGroupId
                    JOIN	MMVolume	MV
                            ON	MV.MediaId = MM.MediaId
                    JOIN	MMLibrary	ML
                            ON	ML.LibraryId = MM.LibraryId
                    WHERE	MM.MediaLocation<>3
                            AND	MV.VolumeFlags IN (5)
                            AND	MSG.SpareGroupName = '{spare_group_name}'
                            AND ML.AliasName = '{self.tape_library_name}'"""

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != '':
            return True
        return False

    def _get_assigned_media_drive(self):
        """ To get assigned media drive """

        self.log.info("Gets assigned media drive")

        query = f"""SELECT	MD.AliasName
                    FROM	MMDrive MD
                    JOIN	MMMedia MM
                            ON MD.MediaId = MM.MediaId
                    WHERE	MM.BarCode = '{self.assigned_media}'"""

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != '':
            self.assigned_media_drive = cur[0]
            return cur[0]
        return 0

    def _get_assigned_media(self):
        """ To get assigned media from the given library and spare group """

        self.log.info("Gets assigned media from the library and spare group")
        query = f"""SELECT	MM.MediaId,MM.BarCode
                    FROM	MMMedia	MM
                    JOIN	MMSpareGroup MSG
                            ON	MSG.SpareGroupId = MM.SpareGroupId
                    JOIN	MMVolume	MV
                            ON	MV.MediaId = MM.MediaId
                    JOIN	MMLibrary	ML
                            ON	ML.LibraryId = MM.LibraryId
                    WHERE	MM.MediaLocation<>3
                            AND	MV.VolumeFlags IN (1,2,7)
                            AND ML.AliasName = '{self.tape_library_name}'"""

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != '':
            self.assigned_media = cur[1]
            return int(cur[0])
        return 0

    def _get_no_oml_media(self, spare_group_name):
        """
        To get no oml media from the given library and spare group

            Args:
             spare_group_name -- spare media group name
        """

        self.log.info("Gets no oml media from the given library and spare group")
        query = f"""SELECT	MM.MediaId,MM.BarCode
                    FROM	MMMedia	MM
                    JOIN	MMSpareGroup MSG
                            ON	MSG.SpareGroupId = MM.SpareGroupId
                    JOIN	MMVolume	MV
                            ON	MV.MediaId = MM.MediaId
                    JOIN	MMLibrary	ML
                            ON	ML.LibraryId = MM.LibraryId
                    WHERE	MM.MediaLocation<>3
                            AND	MV.VolumeFlags IN (5)
                            AND MM.LastWriteLibraryId = 0 
                            AND	MSG.SpareGroupName = '{spare_group_name}'
                            AND ML.AliasName = '{self.tape_library_name}'"""

        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != '':
            self.no_oml_media = cur[1]
            return int(cur[0])
        return 0

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
            self.log.error("Error encountered during cleanup: %s", str(exp))
            raise Exception("Error encountered during cleanup: {0}".format(str(exp)))

        self.log.info("********************** CLEANUP COMPLETED *************************")

    def setup(self):
        """Setup function of this test case"""

        options_selector = OptionsSelector(self.commcell)
        self.tape_library_name = self.tcinputs['LibraryName']
        self.drive_pool = self.tcinputs['DrivePool']
        self.storage_policy_name = '%s_policy' % (str(self.id))
        self.backupset_name = '%s_bs' % (str(self.id))
        self.client_machine = options_selector.get_machine_object(self.client)

        self._cleanup()

        # To select drive with space available in client machine
        self.log.info('Selecting drive in the client machine based on space available')
        client_drive = options_selector.get_drive(self.client_machine, size=5 * 1024)
        if client_drive is None:
            raise Exception("No free space to generate content")
        self.log.info('selected drive: %s', client_drive)

        self.content_path = self.client_machine.join_path(client_drive, 'Automation', str(self.id), 'TestData')
        if self.client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
        self.client_machine.create_directory(self.content_path)

        self.mmhelper = MMHelper(self)
        self.dedupehelper = DedupeHelper(self)
        self.common_util = CommonUtils(self)

    def run(self):
        """Run function of this test case"""

        try:
            self.log.info("****************** NO OML Media Verification ******************")
            if self._get_no_oml_media(self.tcinputs['SpareGroup1']):
                self.scratch_pool = self.tcinputs['SpareGroup2']
            elif self._get_no_oml_media(self.tcinputs['SpareGroup2']):
                self.scratch_pool = self.tcinputs['SpareGroup1']
            else:
                raise Exception("No OML Media found")

            tape_lib_obj = self.commcell.disk_libraries.get(self.tape_library_name)

            no_oml_media_loc = self.mmhelper.get_media_location(self.no_oml_media)
            no_oml_media_job = tape_lib_obj.verify_media(self.no_oml_media, no_oml_media_loc)
            self.log.info("Media Verification Job %s for no oml media %s has started.", no_oml_media_job.job_id,
                          self.no_oml_media)
            if not no_oml_media_job.wait_for_completion():
                self.log.error("Media Verification Job [%s] for no oml media %s has failed with %s.",
                               no_oml_media_job.job_id, self.no_oml_media, no_oml_media_job.delay_reason)
                raise Exception("Media Verification Job [{0}] for no oml media {1} has failed with {2}.".format(
                    no_oml_media_job.job_id, no_oml_media_job.delay_reason, self.no_oml_media))
            self.log.info("Media Verification Job completed successfully")

            log_line = 'verify response string is .* does not have a valid media label which means that it was not ' \
                       'written to by this product'

            (matched_line, matched_string) = self.dedupehelper.parse_log(self.commcell.commserv_name,
                                                                        'BlindMediaInventory.log', log_line,
                                                                        jobid=no_oml_media_job.job_id,
                                                                        escape_regex=False, single_file=True)

            if len(matched_string) == 1:
                self.log.info(f"No OML media {matched_string[0]}")
            else:
                self.log.error(f"Expected log line {log_line} for No OML Media was not found.")
                raise Exception(f"Expected log line {log_line} for No OML Media was not found.")

            self.log.info("****************** NO OML Media Verification Completed ******************")

            self.log.info("****************** Assigned Media Verification ******************")
            if self._get_assigned_media():
                assigned_media_loc = self.mmhelper.get_media_location(self.assigned_media)
                assigned_media_job = tape_lib_obj.verify_media(self.assigned_media, assigned_media_loc)
                self.log.info("Media Verification Job %s for assigned media %s has started.", assigned_media_job.job_id,
                              self.assigned_media)
                if not assigned_media_job.wait_for_completion():
                    self.log.error("Media Verification Job [%s] for assigned media %s has failed with %s.",
                                   assigned_media_job.job_id, self.assigned_media, assigned_media_job.delay_reason)
                    raise Exception("Media Verification Job [{0}] for assigned media {1} has failed with {2}.".format(
                        assigned_media_job.job_id, assigned_media_job.delay_reason, self.assigned_media))
                self.log.info("Media Verification Job completed successfully")

                log_line = 'verify response string is .* belongs to this instance of the CommCell'

                (matched_line, matched_string) = self.dedupehelper.parse_log(self.commcell.commserv_name,
                                                                            'BlindMediaInventory.log', log_line,
                                                                            jobid=assigned_media_job.job_id,
                                                                            escape_regex=False, single_file=True)

                if len(matched_string) == 1:
                    self.log.info(f"Assigned media {matched_string[0]}")
                else:
                    self.log.error(f"Expected log line {log_line} for Assigned Media was not found.")
                    raise Exception(f"Expected log line {log_line} for Assigned Media was not found.")

                self.log.info("****************** Assigned Media Verification Completed ******************")
            elif self._check_for_spare_media(self.scratch_pool):
                self.log.info("Generating Data at %s", self.content_path)
                if not self.client_machine.generate_test_data(self.content_path, dirs=1, file_size=1024, files=10):
                    self.log.error("unable to Generate Data at %s", self.content_path)
                    raise Exception("unable to Generate Data at {0}".format(self.content_path))
                self.log.info("Generated Data at %s", self.content_path)

                # create Non-Dedupe storage policy
                self.commcell.storage_policies.add_tape_sp(self.storage_policy_name, self.tape_library_name,
                                                           self.tcinputs["MediaAgentName"],
                                                           self.drive_pool, self.scratch_pool)

                # create backupset
                self.mmhelper.configure_backupset(self.backupset_name, self.agent)

                # create subclient
                subclient1_name = "%s_SC1" % str(self.id)
                sc1_obj = self.mmhelper.configure_subclient(self.backupset_name, subclient1_name,
                                                            self.storage_policy_name, self.content_path,
                                                            self.agent)

                self.common_util.subclient_backup(sc1_obj, "FULL")

                self._get_assigned_media()
                if self._get_assigned_media_drive():
                    self.mmhelper.unload_drive(self.tape_library_name, self.assigned_media_drive)
                assigned_media_loc = self.mmhelper.get_media_location(self.assigned_media)
                assigned_media_job = tape_lib_obj.verify_media(self.assigned_media, assigned_media_loc)
                self.log.info("Media Verification Job %s for assigned media %s has started.", assigned_media_job.job_id,
                              self.assigned_media)
                if not assigned_media_job.wait_for_completion():
                    self.log.error("Media Verification Job [%s] for assigned media %s has failed with %s.",
                                   assigned_media_job.job_id, self.assigned_media, assigned_media_job.delay_reason)
                    raise Exception("Media Verification Job [{0}] for assigned media {1} has failed with {2}.".format(
                        assigned_media_job.job_id, assigned_media_job.delay_reason, self.assigned_media))
                self.log.info("Media Verification Job completed successfully")

                log_line = 'verify response string is .* belongs to this instance of the CommCell'

                (matched_line, matched_string) = self.dedupehelper.parse_log(self.commcell.commserv_name,
                                                                            'BlindMediaInventory.log', log_line,
                                                                            jobid=assigned_media_job.job_id,
                                                                            escape_regex=False, single_file=True)

                if len(matched_string) == 1:
                    self.log.info(f"Assigned media {matched_string[0]}")
                else:
                    self.log.error(f"Expected log line {log_line} for Assigned Media was not found.")
                    raise Exception(f"Expected log line {log_line} for Assigned Media was not found.")

                self.log.info("****************** Assigned Media Verification Completed ******************")
            else:
                raise Exception("No Spare media found")

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
