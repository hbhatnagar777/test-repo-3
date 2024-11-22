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
        IBMi - VTL backup and restore of pre-defined subclient *ALLDLO
        Step1: configure BackupSet and Subclients for TC with VTL storage policy.
        Step2: On client, create a folder with documents for Full backup.
        Step3: Run a full backup for the subclient *ALLDLO with VTL storage policy
        Step4: Check Full backup logs on client and verify if proper backup command is used
        Step5: On client, Create another folder with documents for Incremental backup.
        Step6: On client, Create extra document in folder in first folder.
        Step7: Run an incremental job for the subclient with VTL storage policy
        Step8: Check Inc backup logs on client and verify if proper backup command is used
        Step9: On client, Create another folder with documents for differential backup.
        Step10: On client, Create extra document in folder first folder.
        Step11: Run an Differential job for the subclient
        Step12: Check Inc backup logs to confirm backup commands.
        Step13: Run OOP restore of all three folders and compare the data and verify
                restore logs if proper command is used. Then perform cleanup on client.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - VTL backup and restore of pre-defined subclient *ALLDLO"
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.subclient_name = None
        self.client_machine = None
        self.destpath = None
        self.sc_name = None
        self.scan_type = None
        self.job = None

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.RECURSIVE
            self.subclient_name = "*ALLDLO"
            self.log.info("*** STARTING RUN FOR SC: *ALLDLO with %s SCAN **", self.scan_type.name)
            self.log.info("Step1, configure BackupSet and Subclients for TC with VTL storage policy")
            self.log.info("Performance libraries and locked libraries are added as filters to *ALLDLO")
            self.helper.configure_ibmi_default_sc(backupset_name="backupset_{0}".format(self.id),
                                                  subclient_name=self.subclient_name,
                                                  storage_policy=self.storage_policy,
                                                  scan_type=self.scan_type,
                                                  data_readers=5,
                                                  allow_multiple_readers=True,
                                                  delete=False)
            usr_flr = ["V{0}".format(self.id), "V{0}1".format(self.id), "V{0}2".format(self.id)]

            for each in usr_flr:
                self.client_machine.manage_folder(operation='delete', folder_name=each)
                self.client_machine.manage_folder(operation='delete', folder_name="R{0}".format(each))

            self.log.info("Step2: On client, create a folder {0} with documents".format(usr_flr[0]))
            self.client_machine.populate_QDLS_data(folder_name=usr_flr[0], tc_id=self.id, count=5)

            self.log.info("Step3: Run a full backup for the subclient *ALLDLO with VTL "
                          "and verify if it completes without failures.")
            self.job = self.helper.run_backup(backup_level="Full")[0]
            self.log.info("Step4: Check Full backup logs to backup command.")
            self.log.info("Check backup logs to confirm proper QDLS backup command is executed.")
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue='SAVDLO')
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue='FLR(*ANY)')
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue='DEV(')
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue='VOL(')
            self.log.info("Step5: On client, Create another folder {0} with documents.".format(usr_flr[1]))
            self.client_machine.populate_QDLS_data(folder_name=usr_flr[1], tc_id=self.id, count=5)

            self.log.info("Step6: On client, Create extra document in folder {0}.".format(usr_flr[0]))
            self.client_machine.create_file(file_path="/QDLS/{0}/INC.DOC".format(usr_flr[0]),
                                            content=" Incremental- Automation object for TC#{0}".format(self.id))
            self.log.info("Step7: Run an incremental job for the subclient "
                          " *ALLDLO  and verify if it completes without failures.")
            self.job = self.helper.run_backup(backup_level="Incremental")[0]
            self.log.info("Step8: Check Inc backup logs to confirm backup commands.")
            self.log.info("Check backup logs to confirm QDLS flag is set to true.")
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue='SAVDLO')
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue='VOL(')

            self.log.info("Step9: On client, Create another folder {0} with documents.".format(usr_flr[2]))
            self.client_machine.populate_QDLS_data(folder_name=usr_flr[2], tc_id=self.id, count=5)

            self.log.info("Step10: On client, Create extra document in folder {0}.".format(usr_flr[0]))
            self.client_machine.create_file(file_path="/QDLS/{0}/DIFF.DOC".format(usr_flr[0]),
                                            content=" Incremental- Automation object for TC#{0}".format(self.id))
            self.log.info("Step11: Run an Differential job for the subclient "
                          " *ALLDLO  and verify if it completes without failures.")
            self.job = self.helper.run_backup(backup_level="Differential")[0]
            self.log.info("Step12: Check Inc backup logs to confirm backup commands.")
            self.log.info("Check backup logs to confirm QDLS backup command.")
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue='SAVDLO')
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue='VOL(')

            self.log.info("Step13: run OOP restore of both folders and compare.")
            for each in usr_flr:
                src_path = "/QDLS/{0}".format(each)
                self.destpath = "/QDLS/R{0}".format(each)
                self.log.info("run OOP restore of folder [{0}] to "
                              "folder [{1}] and verify.".format(each, "R{0}".format(each)))
                self.job = self.helper.restore_out_of_place(self.destpath,
                                                            paths=[src_path],
                                                            restore_ACL=False,
                                                            preserve_level=0)
                self.helper.verify_from_log('cvrest*.log',
                                            'commandForDLORestore',
                                            jobid=self.job.job_id,
                                            expectedvalue='RSTDLO')
                self.helper.verify_from_log('cvrest*.log',
                                            'commandForDLORestore',
                                            jobid=self.job.job_id,
                                            expectedvalue='SAVFLR')
                self.helper.verify_from_log('cvrest*.log',
                                            'commandForDLORestore',
                                            jobid=self.job.job_id,
                                            expectedvalue='RSTFLR')
                self.helper.verify_from_log('cvrest*.log',
                                            'executeRestore',
                                            jobid=self.job.job_id,
                                            expectedvalue='VOL(')
                self.helper.verify_from_log('cvrest*.log',
                                            'executeRestore',
                                            jobid=self.job.job_id,
                                            expectedvalue='DEV(')
                self.helper.compare_ibmi_data(source_path=src_path, destination_path=self.destpath)
                self.client_machine.manage_folder(operation='delete', folder_name=each)
                self.client_machine.manage_folder(operation='delete', folder_name="R{0}".format(each))

            self.log.info("**VTL BACKUP & RESTORE OF QDLS/*ALLDLO COMPLETED SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
