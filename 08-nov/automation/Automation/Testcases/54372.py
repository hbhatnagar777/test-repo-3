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
        IBMi pre-defined subclient "*ALLDLO" backup and restore with regular scan
        Step1, configure BackupSet and Subclients for TC
        Step2: On client, create a folder AUT54372 with documents
        Step3: Run a full backup for the subclient *ALLDLO and verify if it completes without failures.
        Step4: Check Full backup logs to backup command
        Step5: On client, Create another folder AUT543701 with objects.
        Step6: On client, Create a document in folder AUT54370.
        Step7: Run an incremental job for the subclient and verify if it completes without failures.
        Step8: Check Inc backup logs to confirm backup commands.
        Step9: run OOP restore of both libraries and verify.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Regular scan: Backup of pre-defined subclient *ALLDLO"
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
            self.log.info("Step1, configure BackupSet and Subclients for TC")
            self.log.info("Performance libraries and locked libraries are added as filters to *ALLDLO")
            self.helper.configure_ibmi_default_sc(backupset_name="backupset_{0}".format(self.id),
                                                  subclient_name=self.subclient_name,
                                                  storage_policy=self.storage_policy,
                                                  scan_type=self.scan_type,
                                                  data_readers=5,
                                                  allow_multiple_readers=True,
                                                  delete=False)
            usr_flr = []
            usr_flr.append("A{0}".format(self.id))
            usr_flr.append("A{0}1".format(self.id))

            for each in usr_flr:
                self.client_machine.manage_folder(operation='delete', folder_name=each)
                self.client_machine.manage_folder(operation='delete', folder_name="R{0}".format(each))

            self.log.info("Step2: On client, create a folder {0} with documents".format(usr_flr[0]))
            self.client_machine.populate_QDLS_data(folder_name=usr_flr[0], tc_id=self.id, count=5)

            self.log.info("Step3: Run a full backup for the subclient *ALLDLO "
                          "and verify if it completes without failures.")
            full_job = self.helper.run_backup(backup_level="Full")[0]
            self.log.info("Step4: Check Full backup logs to backup command.")
            self.log.info("Check backup logs to confirm QDLS flag is set to true.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'processJobStartMessage',
                                        jobid=full_job.job_id,
                                        expectedvalue="[Backup_ALLDLO_Enabled]"
                                        )
            self.log.info("Step5: On client, Create another folder {0} with documents.".format(usr_flr[1]))
            self.client_machine.populate_QDLS_data(folder_name=usr_flr[1], tc_id=self.id, count=5)

            self.log.info("Step6: On client, Create extra document in folder {0}.".format(usr_flr[0]))
            self.client_machine.create_file(file_path="/QDLS/{0}/INC.DOC".format(usr_flr[0]),
                                            content=" Incremental- Automation object for TC#{0}".format(self.id))
            self.log.info("Step7: Run an incremental job for the subclient "
                          " *ALLDLO  and verify if it completes without failures.")
            inc_job = self.helper.run_backup(backup_level="Incremental")[0]
            self.log.info("Step8: Check Inc backup logs to confirm backup commands.")
            self.log.info("Check backup logs to confirm QDLS flag is set to true.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'processJobStartMessage',
                                        jobid=inc_job.job_id,
                                        expectedvalue="[Backup_ALLDLO_Enabled]"
                                        )
            self.log.info("Step9: run OOP restore of both folders and compare.")
            for each in usr_flr:
                src_path="/QDLS/{0}".format(each)
                self.destpath="/QDLS/R{0}".format(each)
                self.log.info("run OOP restore of folder [{0}] to "
                              "folder [{1}] and verify.".format(each, "R{0}".format(each)))
                self.helper.restore_out_of_place(self.destpath,
                                                 paths=[src_path],
                                                 restore_ACL=False,
                                                 preserve_level=0)
                self.helper.compare_ibmi_data(source_path=src_path, destination_path=self.destpath)
                self.client_machine.manage_folder(operation='delete', folder_name=each)
                self.client_machine.manage_folder(operation='delete', folder_name="R{0}".format(each))

            self.log.info("**%s SCAN RUN OF *ALLUSR COMPLETED SUCCESSFULLY**", self.scan_type.name)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED