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

    verify_sc_defaults()    -- Verify the client logs for subclient default values for VTL backup

    run()                   --  run function of this test case
"""

from collections import deque

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Class for executing
         IBMi - VTL backup and restore of pre-defined subclient *ALLUSR and validate subclient defaults
        Step1, configure BackupSet and Subclients for TC with VTL storage polciy
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
        self.name = " 	IBMi - VTL backup and restore of pre-defined subclient *ALLUSR and validate subclient defaults"
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
        self.scan_type = None
        self.job = None

    def verify_sc_defaults(self, jobid, backup_level="Full"):
        """
        Verify the client logs for subclient default values for VTL backup

                    Args:
                        jobid              (str)           -- Job id

                        backup_level      (str)            -- level of backup
                        (Full/Incremental/Differential)
        """
        self.log.info("Validating logs for {0} backup".format(backup_level))
        self.log.info("Verifying log for default values with SAVACT")
        self.helper.verify_from_log('cvbkpvtl*.log',
                                    'runEachCommand',
                                    jobid=jobid,
                                    expectedvalue="SAVACT(*LIB)")
        self.log.info("Verifying log for default values with SAVACTWAIT")
        self.helper.verify_from_log('cvbkpvtl*.log',
                                    'runEachCommand',
                                    jobid=jobid,
                                    expectedvalue="SAVACTWAIT(0 *LOCKWAIT *LOCKWAIT)")
        self.log.info("Verifying log for default values with ACCPTH")
        self.helper.verify_from_log('cvbkpvtl*.log',
                                    'runEachCommand',
                                    jobid=jobid,
                                    expectedvalue="ACCPTH(*SYSVAL)")
        self.log.info("Verifying log for default values with SAVFDTA")
        self.helper.verify_from_log('cvbkpvtl*.log',
                                    'runEachCommand',
                                    jobid=jobid,
                                    expectedvalue="SAVFDTA(*YES)")
        self.log.info("Verifying log for default values with SPLFDTA")
        self.helper.verify_from_log('cvbkpvtl*.log',
                                    'runEachCommand',
                                    jobid=jobid,
                                    expectedvalue="SPLFDTA(*NONE)")

        self.log.info("Verifying log for default values with QDTA")
        self.helper.verify_from_log('cvbkpvtl*.log',
                                    'runEachCommand',
                                    jobid=jobid,
                                    expectedvalue="TGTRLS(*CURRENT)")
        self.log.info("Verifying log for default values with DTACPR")
        self.helper.verify_from_log('cvbkpvtl*.log',
                                    'runEachCommand',
                                    jobid=jobid,
                                    expectedvalue="DTACPR(*NO)")
        self.log.info("Verifying log for default values with TGTRLS")
        self.helper.verify_from_log('cvbkpvtl*.log',
                                    'runEachCommand',
                                    jobid=jobid,
                                    expectedvalue="QDTA(*NONE)")
        self.log.info("Verifying log for default values with PVTAUT")
        self.helper.verify_from_log('cvbkpvtl*.log',
                                    'runEachCommand',
                                    jobid=jobid,
                                    expectedvalue="PVTAUT(*NO)")
        self.log.info("Verifying log for default values with UPDHST")
        self.helper.verify_from_log('cvbkpvtl*.log',
                                    'runEachCommand',
                                    jobid=jobid,
                                    expectedvalue="UPDHST(*NO)")

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
            self.log.info("*** STARTING RUN FOR SC: *ALLUSR with VTL storage policy **")
            self.log.info("Step1, configure BackupSet and Subclients for TC with VTL storage policy")
            self.log.info("Performance libraries and locked libraries are added as filters to *ALLUSR")
            filters = ["/QSYS.LIB/QPFR*.LIB", "/QSYS.LIB/QUSRD*.LIB"]
            self.log.info("Save file data is ignored to reduce the backup duration")
            self.helper.configure_ibmi_default_sc(backupset_name="backupset_{0}".format(self.id),
                                                  subclient_name=self.sc_name,
                                                  storage_policy=self.storage_policy,
                                                  scan_type=self.scan_type,
                                                  filter_content=filters,
                                                  delete=True)
            usr_lib = ["AUT{0}".format(self.id), "AUT{0}1".format(self.id)]
            self.destlib = "AUTORST"

            for each in usr_lib:
                self.client_machine.manage_library(operation='delete', object_name=each)

            self.log.info("Step2: On client, create a library {0} with objects".format(usr_lib[0]))
            self.client_machine.populate_lib_with_data(library_name=usr_lib[0], tc_id=self.id, count=2)

            self.log.info("Step3: Run a full backup for the subclient *ALLUSR "
                          "and verify if it completes without failures.")
            self.job = self.helper.run_backup(backup_level="Full")[0]
            self.log.info("Step4: Check Full backup logs to backup command.")
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue="SAVLIB LIB(")
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue="DEV(")
            self.log.info("step5: Check scan logs to confirm subclient default values are used.")
            self.verify_sc_defaults(self.job.job_id)

            self.log.info("Step6: On client, Create another library {0} with objects.".format(usr_lib[1]))
            self.client_machine.populate_lib_with_data(library_name=usr_lib[1], tc_id=self.id, count=2)

            self.log.info("Step7: On client, Create file object in library {0}.".format(usr_lib[0]))
            self.client_machine.create_sourcepf(library=usr_lib[0], object_name='INC{0}'.format(self.id))

            self.log.info("Step8: Run an incremental job for the subclient"
                          " and verify if it completes without failures.")
            self.job = self.helper.run_backup(backup_level="Incremental")[0]
            self.log.info("Step9: Check Inc backup logs to confirm backup commands.")
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue="SAVCHGOBJ")
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue="{0}".format(usr_lib[0]))
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue="{0}".format(usr_lib[1]))
            self.log.info("Step10: run OOP restore of both libraries and verify.")
            for each in usr_lib:
                self.log.info("run OOP restore of library [{0}] to "
                              "library [{1}] and verify.".format(each, self.destlib))
                self.job = self.helper.restore_out_of_place(
                    destination_path=self.client_machine.lib_to_path("{0}".format(each)),
                    paths=[self.client_machine.lib_to_path("{0}".format(each))],
                    restore_ACL=False,
                    preserve_level=0)
                self.client_machine.manage_library(operation='delete', object_name=self.destlib)
                self.client_machine.manage_library(operation='delete', object_name=each)
                self.log.info("Verify restore logs for proper restore command")
                self.helper.verify_from_log('cvrest*.log',
                                            'executeRestore',
                                            jobid=self.job.job_id,
                                            expectedvalue=each)
                self.helper.verify_from_log('cvrest*.log',
                                            'executeRestore',
                                            jobid=self.job.job_id,
                                            expectedvalue="DEV(")
                self.helper.verify_from_log('cvrest*.log',
                                            'executeRestore',
                                            jobid=self.job.job_id,
                                            expectedvalue="VOL(")

            self.log.info("**VTL BACKUP AND RESTORE OF *ALLUSR COMPLETED SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
