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

    restore_verify()        -- Initiates restore for data backed up in the given job
                                and performs the applicable verifications

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
        IBMi - VTL backup and restore of pre-defined subclient: *HST and validate subclient default values.
        Step1, configure BackupSet and pre-defined Subclients for TC
        Step2: On client, Re-create the history file on client machine
        Step3: Run a full backup for the subclient *HST log
        step4: Check backup logs to confirm proper command is used for backup.
        step5: Check scan logs to confirm subclient default values are used.
        Step6: On client, Create another QHST file with a member.
        Step7: Run an incremental job for the subclient
        Step8: Check backup logs to confirm if proper command is used for backup.
        step9: Check scan logs to confirm subclient default values are used.
        Step10: OOP Restore History file objects and verify.
        Step11: Verify client restore logs if proper command is used.
        Step12: check restored objects and cleanup created history file objects.
        Step13: cleanup restored library.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "IBMi - VTL backup and restore of pre-defined subclient: *HST and validate subclient " \
                    "default values."

        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.subclient_name = None
        self.client_machine = None
        self.destlib = None
        self.scan_type = None
        self.sc_name = None
        self.job = None

    def restore_verify(self, source, destination):
        """
                Initiates restore for data backed up in the given job
                and performs the applicable verifications

                    Args:
                        source              (str)   : Source Library

                        destination        (str)   : destination library
        """
        self.log.info("Starting restore {0} to destination library {1} ".format(source, destination))
        self.job = self.helper.restore_out_of_place(destination_path=self.client_machine.lib_to_path(destination),
                                                    paths=[self.client_machine.lib_to_path(source)],
                                                    restore_ACL=False,
                                                    preserve_level=0)
        self.log.info("Verify restore logs to verify parallel backup tapes are used")

        self.helper.compare_ibmi_data(source_path="{0}/*".format(self.client_machine.lib_to_path(destination)),
                                      destination_path="{0}/*".format(self.client_machine.lib_to_path(destination)))
        self.client_machine.manage_library(operation='delete', object_name=destination)

    def verify_sc_defaults(self, jobid, backup_level="Full"):
        """
        Verify the client logs for subclient default values for VTL backup

                    Args:
                        jobid              (str)           -- Job id

                        backup_level      (str)            -- level of backup
                        (Full/Incremental/Differential)
        """
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
        if backup_level == "Full":
            self.log.info("Verifying log for default values with SPLFDTA")
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=jobid,
                                        expectedvalue="SPLFDTA(*NONE)")
        self.log.info("Verifying log for default values with QDTA")
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
            self.sc_name = "*HST log"
            self.log.info("*** STARTING RUN FOR SC: *QHST backup and restore with VTL **")
            self.log.info("Step1, configure BackupSet and pre-defined Subclients for TC")
            self.helper.configure_ibmi_default_sc(backupset_name="backupset_{0}".format(self.id),
                                                  subclient_name=self.sc_name,
                                                  storage_policy=self.storage_policy,
                                                  scan_type=self.scan_type,
                                                  delete=False)
            self.destlib = "QHST{0}".format(self.id)
            destpath = self.client_machine.lib_to_path(self.destlib)
            hstobj = ["QHST{0}".format(self.id), "QHST{0}1".format(self.id)]

            self.log.info("Step2: On client, Re-create the file QSYS/{0}"
                          " and delete QSYS/{1} if exists".format(hstobj[0], hstobj[1]))
            qhst_path = []
            for each in hstobj:
                self.client_machine.delete_file_object(library="QSYS", object_name="{0}".format(each))
                qhst_path.append("{0}{1}{2}.FILE".format(self.test_path, self.slash_format, each))
            self.client_machine.create_sourcepf(library="QSYS", object_name="{0}".format(hstobj[0]))
            self.log.info("Step3: Run a full backup for the subclient *HST log"
                          " and verify if it completes without failures.")
            self.job = self.helper.run_backup_verify(self.scan_type, "Full")[0]
            self.log.info("step4: Check backup logs to confirm SAVOBJ is used.")
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue="SAVOBJ")
            self.log.info("step5: Check scan logs to confirm subclient default values are used.")
            self.verify_sc_defaults(self.job.job_id)
            self.log.info("Step6: On client, Create a file QHST{0}1 with a member.".format(self.id))
            self.client_machine.create_sourcepf(library="QSYS", object_name="{0}".format(hstobj[1]))
            self.log.info("Step7: Run an incremental job for the subclient"
                          "and verify it completes without failures.")
            self.job = self.helper.run_backup_verify(self.scan_type, "Incremental")[0]
            self.log.info("Step8: Check backup logs to confirm SAVOBJ was used.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue="{0}".format(hstobj[1])
                                        )
            self.log.info("step9: Check scan logs to confirm subclient default values are used.")
            self.verify_sc_defaults(jobid=self.job.job_id, backup_level="Incremental")

            self.log.info("Step10: OOP Restore QSYS/{0} & QSYS/{1} objects "
                          "to library {0}.".format(hstobj[0], hstobj[1]))
            self.client_machine.manage_library(operation='delete', object_name='QHST{0}'.format(self.id))
            self.job = self.helper.restore_out_of_place(destination_path=destpath,
                                                        paths=qhst_path)
            self.log.info("Step11: Verify client restore logs if command RSTOBJ is used.")
            self.helper.verify_from_log('cvrest*.log',
                                        'executeRestore',
                                        jobid=self.job.job_id,
                                        expectedvalue="RSTOBJ SAVLIB(QSYS) RSTLIB("
                                        )
            self.helper.verify_from_log('cvrest*.log',
                                        'executeRestore',
                                        jobid=self.job.job_id,
                                        expectedvalue="{0}".format(hstobj[0])
                                        )
            self.helper.verify_from_log('cvrest*.log',
                                        'executeRestore',
                                        jobid=self.job.job_id,
                                        expectedvalue="{0}".format(hstobj[1])
                                        )
            self.helper.verify_from_log('cvrest*.log',
                                        'executeRestore',
                                        jobid=self.job.job_id,
                                        expectedvalue="VOL("
                                        )
            self.helper.verify_from_log('cvrest*.log',
                                        'executeRestore',
                                        jobid=self.job.job_id,
                                        expectedvalue="DEV("
                                        )
            self.helper.verify_from_log('cvrest*.log',
                                        'processOUTQ',
                                        jobid=self.job.job_id,
                                        expectedvalue="end code 0"
                                        )
            self.log.info("Step12: check restored objects and cleanup created history file objects.")
            for each in hstobj:
                self.client_machine.object_existence(library_name='QSYS',
                                                     object_name='{0}'.format(each),
                                                     obj_type='*FILE')
                self.client_machine.delete_file_object(library='QSYS', object_name="{0}".format(each))
            self.log.info("Step13: cleanup restored library.")
            self.client_machine.manage_library(operation='delete', object_name='QHST{0}'.format(self.id))
            self.log.info("*VTL BACKUP and RESTORE OF QHST COMPLETED SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
