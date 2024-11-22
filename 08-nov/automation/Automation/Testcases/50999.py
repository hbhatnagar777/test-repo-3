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
        IBMi - Backup and restore of QDLS Folders & Documents with empty folder
        Step1: configure BackupSet and Subclients for Testcase
        Step2: On client, create an empty folder
        Step3: Run a full backup for the subclient and verify if it completes without failures.
        Step4: run OOP restore of empty folder and compare.
        Step5: On client, Create another empty folder EMPTY.
        Step6: Run an incremental job for the subclient and verify if it completes without failures.
        Step7: run OOP restore of empty folder and compare.
        Step8: On client, Create another empty folder EMPTY1.
        Step9: Run an incremental job for the subclient and verify if it completes without failures.
        Step10: run OOP restore of both folders and compare.
        Step11: On client, Create another empty folder EMPTY2.
        Step12: Run an Differential  job for the subclient and verify if it completes without failures.
        Step13: run OOP restore of both folders and compare.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Backup and restore of QDLS Folders & Documents with empty folder"
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
            self.log.info("*** STARTING RUN FOR SC: Backup and restore of QDLS Folders & Documents with "
                          "empty folder **")
            self.log.info("Step1, configure BackupSet and Subclients for TC")
            self.helper.create_backupset(self.backupset_name, delete=True)
            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=[self.src_path],
                                         scan_type=ScanType.RECURSIVE,
                                         data_readers=2,
                                         allow_multiple_readers=True,
                                         delete=True)
            if self.IBMiMode == "VTLParallel":
                self.log.info("Enable multiple drives option for VTL Backup")
                self.helper.set_vtl_multiple_drives()

            self.log.info("Step2: On client, create an empty folder %s ", usr_flr)
            self.client_machine.manage_folder(operation='delete', folder_name=usr_flr)
            self.client_machine.manage_folder(operation='delete', folder_name=rst_flr)
            self.client_machine.manage_folder(operation='create', folder_name=usr_flr)

            self.log.info("Step3: Run a full backup for the subclient "
                          "and verify if it completes without failures.")
            _ = self.helper.run_backup(backup_level="Full")[0]

            self.log.info("Step4: run OOP restore of empty folder and compare.")

            self.log.info("run OOP restore of empty folder [{0}] to "
                          "folder [{1}] and verify.".format(usr_flr, rst_flr))
            self.helper.restore_out_of_place(self.destpath,
                                             paths=[self.src_path],
                                             restore_ACL=False,
                                             preserve_level=0)
            self.helper.compare_ibmi_data(source_path=self.src_path, destination_path=self.destpath)
            self.client_machine.manage_folder(operation='delete', folder_name=rst_flr)

            self.log.info("Step5: On client, Create documents under empty folder %s ", usr_flr)
            self.client_machine.create_file(file_path="/QDLS/{0}/INC.DOC".format(usr_flr),
                                            content=" Automation object for TC#{0}".format(self.id))

            self.log.info("Step6: Run an incremental job for the subclient "
                          " and verify if it completes without failures.")
            _ = self.helper.run_backup(backup_level="Incremental")[0]

            self.log.info("Step7: run OOP restore of empty folder and compare.")
            self.log.info("run OOP restore of empty folder [{0}] to "
                          "folder [{1}] and verify.".format(usr_flr, rst_flr))
            self.helper.restore_out_of_place(self.destpath,
                                             paths=[self.src_path],
                                             restore_ACL=False,
                                             preserve_level=0)
            self.helper.compare_ibmi_data(source_path=self.src_path, destination_path=self.destpath)
            self.client_machine.manage_folder(operation='delete', folder_name=rst_flr)

            self.log.info("Step8: On client, Create another document under  folder {0} ".format(usr_flr))
            self.client_machine.create_file(file_path="/QDLS/{0}/INC1.DOC".format(usr_flr),
                                            content=" Automation object for TC#{0}".format(self.id))

            self.log.info("Step9: Run an incremental job for the subclient and verify if "
                          "it completes without failures.")
            _ = self.helper.run_backup(backup_level="Incremental")[0]

            self.log.info("Step10: run OOP restore of both folders and compare.")
            self.log.info("run OOP restore of empty folder [{0}] to "
                          "folder [{1}] and verify.".format(usr_flr, rst_flr))
            self.helper.restore_out_of_place(self.destpath,
                                             paths=[self.src_path],
                                             restore_ACL=False,
                                             preserve_level=0)
            self.helper.compare_ibmi_data(source_path=self.src_path, destination_path=self.destpath)
            self.client_machine.manage_folder(operation='delete', folder_name=rst_flr)

            self.log.info("Step11: On client, Create another objecr under  folder {0} ".format(usr_flr))
            self.client_machine.create_file(file_path="/QDLS/{0}/DIFF.DOC".format(usr_flr),
                                            content=" Automation object for TC#{0}".format(self.id))

            self.log.info("Step12: Run an Differential  job for the subclient and verify if "
                          "it completes without failures.")
            _ = self.helper.run_backup(backup_level="Differential")[0]

            self.log.info("Step13: run OOP restore of both folders and compare.")
            self.log.info("run OOP restore of empty folder [{0}] to "
                          "folder [{1}] and verify.".format(usr_flr, rst_flr))
            self.helper.restore_out_of_place(self.destpath,
                                             paths=[self.src_path],
                                             restore_ACL=False,
                                             preserve_level=0)
            self.helper.compare_ibmi_data(source_path=self.src_path, destination_path=self.destpath)

            ###****************** ONLY FROM 11.29 ******************###
            self.log.info("*** WITH NO CHANGES INC/DIFF BACKUP OF QDLS SHOULD COMPLETE")
            self.log.info("Step14: Run a full backup and verify if it completes without failures.")
            _ = self.helper.run_backup(backup_level="Full")[0]
            self.log.info("Step15: Run an Incremental backup and verify if it completes without failures.")
            _ = self.helper.run_backup(backup_level="Incremental")[0]
            self.log.info("Step16: Run an differential backup and verify if it completes without failures.")
            _ = self.helper.run_backup(backup_level="Differential")[0]
            self.log.info("*** WITH NO CHANGES INC/DIFF BACKUPS OF QDLS HAS COMPLETED SUCCESSFULLY")
            self.client_machine.manage_folder(operation='delete', folder_name=rst_flr)
            self.client_machine.manage_folder(operation='delete', folder_name=usr_flr)
            
            self.log.info("**VERIFICATION OF QDLS EMPTY FOLDER BACKUP AND RESTORE COMPLETED SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
