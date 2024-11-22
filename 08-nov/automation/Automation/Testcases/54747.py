# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase to perform storage validation operation.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    _get_drive_id(library_id)   --  to get driveId from libraryId

    run()                       --  run function of this test case

Sample Input:
"54747": {
            "ClientName": "skclient",
            "AgentName": "File System",
            "MediaAgentName": "skma",
    }
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils.mahelper import (MMHelper, DedupeHelper)


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "MP Acceptance - MountPath Validation"
        self.tcinputs = {
            "MediaAgentName": None
        }

    def _get_drive_id(self, library_id):
        """
        Get DriveId from libraryId
        Agrs:
            library_id (int)  --  LibraryId Id
        Returns:
            Drive Id for the given Library Id
        """

        query = """ SELECT	MD.DriveId
                    FROM	MMDrive MD
                    JOIN	MMMediaSide MMS
                            ON	MMS.MediaId = MD.MediaId
                    JOIN	MMMountPath MP
                            ON	MMS.MediaSideId = MP.MediaSideId
                    WHERE	MP.LibraryId = {0}""".format(library_id)
        self.log.info("QUERY: %s", query)
        self.csdb.execute(query)
        cur = self.csdb.fetch_one_row()
        self.log.info("RESULT: %s", cur[0])
        if cur[0] != ['']:
            value = int(cur[0])
            return value
        self.log.error("No entries present")
        raise Exception("Invalid LibraryId")

    def run(self):
        """Run function of this test case"""

        disk_library_name = "%s_disklib" % str(self.id)

        try:
            options_selector = OptionsSelector(self.commcell)
            ma_machine = options_selector.get_machine_object(self.tcinputs['MediaAgentName'])
            # To select drive with space available in Media agent machine
            self.log.info('Selecting drive in the Media agent machine based on space available')
            ma_drive = options_selector.get_drive(ma_machine, size=5 * 1024)
            if ma_drive is None:
                raise Exception("No free space for hosting mountpath")
            self.log.info('selected drive: %s', ma_drive)
            mountpath = ma_machine.join_path(ma_drive, 'Automation', str(self.id), 'MP')

            # Delete Library
            self.log.info("Deleting library: %s if exists", disk_library_name)
            if self.commcell.disk_libraries.has_library(disk_library_name):
                self.commcell.disk_libraries.delete(disk_library_name)
                self.log.info("Deleted library: %s", disk_library_name)

            # create Disk Library
            lib_obj = MMHelper(self).configure_disk_library(disk_library_name, self.tcinputs['MediaAgentName'],
                                                            mountpath)

            drive_id = self._get_drive_id(lib_obj.library_id)

            # Storage Validation
            storage_validation_jobid = lib_obj.validate_mountpath(drive_id, self.tcinputs["MediaAgentName"])
            self.log.info("Storage Validation Job %s has started.", storage_validation_jobid.job_id)
            if not storage_validation_jobid.wait_for_completion():
                self.log.error("Storage validation job [%s] has failed with %s.", storage_validation_jobid.job_id,
                               storage_validation_jobid.delay_reason)
                raise Exception("Storage validation job [{0}] has failed with {1}."
                                .format(storage_validation_jobid.job_id, storage_validation_jobid.delay_reason))

            parse_result = DedupeHelper(self).parse_log(self.commcell.commserv_name, 'LibraryOperation.log',
                                                        '\[Successfully.*', jobid=storage_validation_jobid.job_id,
                                                        escape_regex=False)
            self.log.info("Storage Validation Result: %s", parse_result[1])

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        self.log.info("********************** CLEANUP STARTING *************************")

        # Delete Library
        self.log.info("Deleting library: %s if exists", disk_library_name)
        if self.commcell.disk_libraries.has_library(disk_library_name):
            self.commcell.disk_libraries.delete(disk_library_name)
            self.log.info("Deleted library: %s", disk_library_name)

        self.log.info("********************** CLEANUP COMPLETED *************************")
