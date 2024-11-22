# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  Initialize TestCase class

    run()                   --  run function of this test case
"""

from collections import deque

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.FSUtils.fshelper import FSHelper

class TestCase(CVTestCase):
    """Class for executing
        IBMi pre-defined subclient "*ALLUSR" backup and restore with regular scan
        Step1, configure BackupSet and Subclients for TC
        Step2: On client, create a library AUT54370 with objects
        Step3: Run a full backup for the subclient *ALLUSR and verify if it completes without failures.
        Step4: Check Full backup logs to backup command
        Step5: On client, Create another library AUT543701 with objects.
        Step6: On client, Create file object in library AUT54370.
        Step7: Run an incremental job for the subclient and verify if it completes without failures.
        Step8: Check Inc backup logs to confirm backup commands.
        Step9: run OOP restore of both libraries and verify.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Regular scan: Backup of pre-defined subclient *ALLUSR"
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.subclient_name = None
        self.client_machine = None
        self.destlib = None
        self.sc_name = None

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.RECURSIVE
            self.sc_name = "*ALLUSR"
            self.log.info("*** STARTING RUN FOR SC: *ALLUSR with %s SCAN **", self.scan_type.name)
            self.log.info("Step1, configure BackupSet and Subclients for TC")
            self.log.info("Performance libraries and locked libraries are added as filters to *ALLUSR")
            filters = []
            filters.append("/QSYS.LIB/QPFR*.LIB")
            filters.append("/QSYS.LIB/QUSRD*.LIB")
            self.log.info("Save file data is ignored to reduce the backup duration")
            self.helper.configure_ibmi_default_sc(backupset_name="backupset_{0}".format(self.id),
                                                  subclient_name=self.sc_name,
                                                  storage_policy=self.storage_policy,
                                                  scan_type=self.scan_type,
                                                  filter_content=filters,
                                                  data_readers=8,
                                                  savfdta=False,
                                                  allow_multiple_readers=True,
                                                  delete=False)
            usr_lib = []
            usr_lib.append("AUT{0}".format(self.id))
            usr_lib.append("AUT{0}1".format(self.id))
            self.destlib = "AUTORST"

            for each in usr_lib:
                self.client_machine.manage_library(operation='delete', object_name=each)

            self.log.info("Step2: On client, create a library {0} with objects".format(usr_lib[0]))
            self.client_machine.populate_lib_with_data(library_name=usr_lib[0], tc_id=self.id, count=2)

            self.log.info("Step3: Run a full backup for the subclient *ALLUSR "
                          "and verify if it completes without failures.")
            full_job = self.helper.run_backup(backup_level="Full")[0]
            self.log.info("Step4: Check Full backup logs to backup command.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'Processing JOBLOG for',
                                        jobid=full_job.job_id,
                                        expectedvalue='[SAVLIB]:[LIB({0}'.format(usr_lib[0])
                                        )
            self.log.info("Check backup logs to confirm ALLUSR flag is set to true.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'processJobStartMessage',
                                        jobid=full_job.job_id,
                                        expectedvalue='[Backup_AllUser_Enabled] - [1]'
                                        )
            self.log.info("Check scan logs to confirm regular scan is used.")
            self.helper.verify_from_log('cvscan*.log',
                                        'ClientScan::doScan',
                                        jobid=full_job.job_id,
                                        expectedvalue="We are not running Scanless Backup"
                                        )
            self.log.info("Check backup logs to confirm SAVF data is not saved.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'processJobStartMessage',
                                        jobid=full_job.job_id,
                                        expectedvalue="[Backup_SaveFileData_Enabled] - [0]"
                                        )
            self.log.info("Step5: On client, Create another library {0} with objects.".format(usr_lib[1]))
            self.client_machine.populate_lib_with_data(library_name=usr_lib[1], tc_id=self.id, count=2)

            self.log.info("Step6: On client, Create file object in library {0}.".format(usr_lib[0]))
            self.client_machine.create_sourcepf(library=usr_lib[0], object_name='INC{0}'.format(self.id))

            self.log.info("Step7: Run an incremental job for the subclient"
                          " and verify if it completes without failures.")
            inc_job = self.helper.run_backup(backup_level="Incremental")[0]
            self.log.info("Step8: Check Inc backup logs to confirm backup commands.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'Processing JOBLOG for',
                                        jobid=inc_job.job_id,
                                        expectedvalue='[SAVCHGOBJ]:[OBJ(*ALL) LIB({0})'.format(usr_lib[0])
                                        )
            self.log.info("Verify if New library is backedup as full using SAVLIB command.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'Processing JOBLOG for',
                                        jobid=inc_job.job_id,
                                        expectedvalue='[SAVLIB]:[LIB({0}'.format(usr_lib[1])
                                        )
            self.log.info("Step9: run OOP restore of both libraries and verify.")
            for each in usr_lib:
                self.log.info("run OOP restore of library [{0}] to "
                              "library [{1}] and verify.".format(each, self.destlib))
                self.helper.run_restore_verify(slash_format=self.slash_format,
                                                         data_path=self.client_machine.lib_to_path("{0}".format(each)),
                                                         tmp_path=self.client_machine.lib_to_path(self.destlib),
                                                         data_path_leaf=""
                                                         )
                self.client_machine.manage_library(operation='delete', object_name=self.destlib)
                self.client_machine.manage_library(operation='delete', object_name=each)

            self.log.info("**%s SCAN RUN OF *ALLUSR COMPLETED SUCCESSFULLY**", self.scan_type.name)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED