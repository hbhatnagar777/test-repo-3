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

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from FileSystem.FSUtils.fshelper import ScanType


class TestCase(CVTestCase):
    """Class for executing
        IBMi - QDLS Backup and restore with Special characters (&,_,#,$)
        Step1, configure BackupSet and Subclients for TC
        Step2: On client, create a folder with documents
        Step3: On client, create a documents with special chars.
        Step4: Run a full backup for the subclient and verify if it completes without failures.
        Step5: run OOP restore of empty folder and compare.
        Step6: On client, Create few more documents with special characters
        Step7: Run an incremental job for the subclient and verify if it completes without failures.
        Step8: run OOP restore of empty folder and compare.
        Step9: On client, Create few more documents with special characters
        Step10: Run an incremental job for the subclient and verify if it completes without failures.
        Step11: run OOP restore of empty folder and compare.
        Step12: On client, Create few more documents with special characters for Diff backup
        Step13: Run an incremental job for the subclient and verify if it completes without failures.
        Step14: run OOP restore of empty folder and compare.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - QDLS Backup and restore with Special characters (&,_,#,$)"
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.backupset_name = None
        self.subclient_name = None
        self.client_machine = None
        self.destpath = None
        self.sc_name = None
        self.src_path = None
        self.destpath = None
        self.scan_type = None
        self.IBMiMode = None

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.RECURSIVE
            self.backupset_name = "backupset_{0}".format(self.id)
            self.subclient_name = "subclient_{0}".format(self.id)
            usr_flr = "A{0}".format(self.id)
            rst_flr = "R{0}".format(self.id)
            self.src_path = "/QDLS/{0}".format(usr_flr)
            self.destpath = "/QDLS/{0}".format(rst_flr)
            self.log.info("*** STARTING RUN FOR SC: Backup and restore of QDLS with Special characters (&,_,#,$)**")
            self.log.info("Step1, configure BackupSet and Subclients for TC")
            self.helper.create_backupset(self.backupset_name, delete=True)
            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=[self.src_path],
                                         scan_type=ScanType.RECURSIVE,
                                         data_readers=2,
                                         allow_multiple_readers=True,
                                         delete=False)
            if self.IBMiMode == "VTLParallel":
                self.log.info("Enable multiple drives option for VTL Backup")
                self.helper.set_vtl_multiple_drives()

            self.log.info("Step2: On client, create a folder %s with documents", usr_flr)
            self.client_machine.populate_QDLS_data(folder_name=usr_flr, tc_id=self.id, count=5)
            self.client_machine.manage_folder(operation='delete', folder_name=rst_flr)

            self.log.info("Step3: On client, create a documents with special chars ")

            spl_chars = ["EX+", "EX!", "EX,", "EX%", "EX#", "EX@", "EX=", "EX^", "EX[", "EX]",
                         "EX{", "EX}", "EX\\", "EX\\<", "EX\\(", "EX\\)", "EX\\;", "EX\\>"]
            for each in spl_chars:
                self.client_machine.create_file(file_path="/QDLS/{0}/{1}.DOC".format(usr_flr, each),
                                                content=" Automation object for TC#{0}".format(self.id))

            self.log.info("Step4: Run a full backup for the subclient and verify if it completes without failures.")
            _ = self.helper.run_backup(backup_level="Full")[0]

            self.log.info("Step5: run OOP restore of empty folder and compare.")
            self.log.info("run OOP restore of empty folder [{0}] to "
                          "folder [{1}] and verify.".format(usr_flr, rst_flr))
            self.helper.restore_out_of_place(self.destpath,
                                             paths=[self.src_path],
                                             restore_ACL=False,
                                             preserve_level=0)
            self.helper.compare_ibmi_data(source_path="{0}/*".format(self.src_path),
                                          destination_path="{0}/*".format(self.destpath))
            self.client_machine.manage_folder(operation='delete', folder_name=rst_flr)

            self.log.info("Step6: On client, Create few more documents with special characters")
            spl_chars = ["IN&", "IN_1", "IN#", "IN$", "IN+", "IN!", "IN,", "IN%", "IN#", "IN@", "IN=", "IN^",
                         "IN[", "IN]", "IN{", "IN}", "IN\\", "IN\\<", "IN\\(", "IN\\)", "IN\\;", "IN\\>"]
            for each in spl_chars:
                self.client_machine.create_file(file_path="/QDLS/{0}/{1}.DOC".format(usr_flr, each),
                                                content=" Automation object for TC#{0}".format(self.id))

            self.log.info("Step7: Run an incremental job for the subclient "
                          " and verify if it completes without failures.")
            _ = self.helper.run_backup(backup_level="Incremental")[0]

            self.log.info("Step8: run OOP restore of empty folder and compare.")
            self.log.info("run OOP restore of empty folder [{0}] to "
                          "folder [{1}] and verify.".format(usr_flr, rst_flr))
            self.helper.restore_out_of_place(self.destpath,
                                             paths=[self.src_path],
                                             restore_ACL=False,
                                             preserve_level=0)
            self.helper.compare_ibmi_data(source_path="{0}/*".format(self.src_path),
                                          destination_path="{0}/*".format(self.destpath))
            self.client_machine.manage_folder(operation='delete', folder_name=rst_flr)

            self.log.info("Step9: On client, Create few more documents with special characters")
            spl_chars = ["IN1&", "IN1_1", "IN1#", "IN1$", "IN1+", "IN1!", "IN1,", "IN1%", "IN1#",
                         "IN1@", "IN1=", "IN1^", "IN1[", "IN1]", "IN1{", "IN1}", "IN1\\",
                         "IN1\\<", "IN1\\(", "IN1\\)", "IN1\\;", "IN1\\>"]
            for each in spl_chars:
                self.client_machine.create_file(file_path="/QDLS/{0}/{1}.DOC".format(usr_flr, each),
                                                content=" Automation object for TC#{0}".format(self.id))

            self.log.info("Step10: Run an incremental job for the subclient "
                          " and verify if it completes without failures.")
            _ = self.helper.run_backup(backup_level="Incremental")[0]

            self.log.info("Step11: run OOP restore of empty folder and compare.")
            self.log.info("run OOP restore of empty folder [{0}] to "
                          "folder [{1}] and verify.".format(usr_flr, rst_flr))
            self.helper.restore_out_of_place(self.destpath,
                                             paths=[self.src_path],
                                             restore_ACL=False,
                                             preserve_level=0)
            self.helper.compare_ibmi_data(source_path="{0}/*".format(self.src_path),
                                          destination_path="{0}/*".format(self.destpath))
            self.client_machine.manage_folder(operation='delete', folder_name=rst_flr)

            self.log.info("Step12: On client, Create few more documents with special characters for Diff backup")
            spl_chars = ["DIF&", "DIF_1", "DIF#", "DIF$", "DIF+", "DIF!", "DIF,", "DIF%", "DIF#",
                         "DIF@", "DIF=", "DIF^", "DIF[", "DIF]", "DIF{", "DIF}", "DIF\\",
                         "DIF\\<", "DIF\\(", "DIF\\)", "DIF\\;", "DIF\\>"]
            for each in spl_chars:
                self.client_machine.create_file(file_path="/QDLS/{0}/{1}.DOC".format(usr_flr, each),
                                                content=" Automation object for TC#{0}".format(self.id))

            self.log.info("Step13: Run an incremental job for the subclient "
                          " and verify if it completes without failures.")
            _ = self.helper.run_backup(backup_level="Incremental")[0]

            self.log.info("Step14: run OOP restore of empty folder and compare.")
            self.log.info("run OOP restore of empty folder [{0}] to "
                          "folder [{1}] and verify.".format(usr_flr, rst_flr))
            self.helper.restore_out_of_place(self.destpath,
                                             paths=[self.src_path],
                                             restore_ACL=False,
                                             preserve_level=0)
            self.helper.compare_ibmi_data(source_path="{0}/*".format(self.src_path),
                                          destination_path="{0}/*".format(self.destpath))

            self.client_machine.manage_folder(operation='delete', folder_name=rst_flr)
            self.client_machine.manage_folder(operation='delete', folder_name=usr_flr)

            self.log.info("**VERIFICATION OF QDLS BACKUP AND RESTORE WITH SPECIAL CHARACTERS COMPLETED SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
