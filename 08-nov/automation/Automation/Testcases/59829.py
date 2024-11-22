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
    
    generate_ifs_data()     --  Generate IFS data on client machine
    
    restore_verify()        -- Run restore and verify the data restored.

    run()                   --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from FileSystem.FSUtils.fshelper import ScanType


class TestCase(CVTestCase):
    """Class for executing
        IBMi - Backup and restore of IFS data with Special characters (&,_,#,$) with Optimized scan
        Step1, configure BackupSet and Subclients for TC
        Step2: On client, create a directory with file names having special characters
        Step3: Run a full backup for the subclient and verify if it completes without failures.
        Step4: Run OOP restore of empty directory and compare.
        Step5: On client, Create few more files with special characters for Inc backup
        Step6: Run an Inc job for the subclient and verify if it completes without failures.
        Step7: run OOP restore of empty directory and compare.
        Step8: On client, Create few more files with special characters for Diff backup.
        Step9: Run an Diff job for the subclient and verify if it completes without failures.
        Step10:Run OOP restore of directory and compare.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Backup and restore of IFS data with Special characters (&,_,#,$) with Optimized scan"
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
        self.src_dir = None
        self.tmp_path = None
        self.scan_type = None

    def generate_ifs_data(self, directory_name, backup_level):
        
        """populates a directory on the client with files.
        Args:
            directory_name  (str)   --  name / full path of the directory to create
            
            backup_level    (str)   --  level of backup
                (Full/Incremental/Differential)

        """
        self.log.info("Populating IFS data for directory {0}".format(directory_name))
        if backup_level == "Full":
            self.log.info("Creating directory %s with objects", directory_name)
            self.client_machine.create_directory(directory_name, force_create=True)
            spl_chars = ["EX+", "EX!", "EX,", "EX%", "EX#", "EX@", "EX=", "EX^", "EX[", "EX]",
                         "EX{", "EX}", "EX\\", "EX\\<", "EX\\(", "EX\\)", "EX\\;", "EX\\>"]
        elif backup_level == "Incremental":
            spl_chars = ["IN&", "IN_1", "IN#", "IN$", "IN+", "IN!", "IN,", "IN%", "IN#", "IN@", "IN=", "IN^",
                         "IN[", "IN]", "IN{", "IN}", "IN\\", "IN\\<", "IN\\(", "IN\\)", "IN\\;", "IN\\>"]
            self.log.info("Adding data under directory : %s", directory_name)
        else:
            spl_chars = ["DIF&", "DIF_1", "DIF#", "DIF$", "DIF+", "DIF!", "DIF,", "DIF%", "DIF#",
                         "DIF@", "DIF=", "DIF^", "DIF[", "DIF]", "DIF{", "DIF}", "DIF\\",
                         "DIF\\<", "DIF\\(", "DIF\\)", "DIF\\;", "DIF\\>"]
        for each in spl_chars:
            self.client_machine.create_file(file_path="{0}/{1}.file".format(directory_name, each),
                                            content=" Automation object for TC#{0}".format(self.id))

    def restore_verify(self, source, destination):
        """
                Initiates restore for data backed up in the given job
                and performs the applicable verifications

                    Args:
                        source              (str)   : Source data path

                        destination        (str)   : destination path for restoring the data
        """
        self.log.info("Starting restore {0} to destination path {1} ".format(source, destination))
        self.helper.restore_out_of_place(destination,
                                         paths=[source],
                                         restore_ACL=False,
                                         preserve_level=0)
        self.helper.compare_ibmi_data(source_path="{0}/*".format(source),
                                      destination_path="{0}/*".format(destination))
        self.client_machine.remove_directory(destination)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.backupset_name = "backupset_{0}".format(self.id)
            self.subclient_name = "subclient_{0}".format(self.id)
            self.src_dir = "/AUTO{0}".format(self.id)
            self.tmp_path = "/AUTOR{0}".format(self.id)
            self.log.info("*** STARTING Optimized scan: Backup and restore of IFS with Special characters (&,_,#,$)**")
            self.log.info("Step1, configure BackupSet and Subclients for TC")
            self.helper.create_backupset(self.backupset_name, delete=True)
            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=[self.src_dir],
                                         scan_type=ScanType.OPTIMIZED,
                                         data_readers=5,
                                         allow_multiple_readers=True,
                                         delete=False)

            self.log.info("Step2: On client, create a directory %s with file names having special characters",
                          self.src_dir)
            self.generate_ifs_data(self.src_dir, "Full")

            self.log.info("Step3: Run a full backup for the subclient and verify if it completes without failures.")
            _ = self.helper.run_backup(backup_level="Full")[0]

            self.log.info("Step4: run OOP restore of empty directory and compare.")
            self.log.info("run OOP restore of empty directory [{0}] to "
                          "directory [{1}] and verify.".format(self.src_dir, self.tmp_path))
            self.restore_verify(source=self.src_dir, destination=self.tmp_path)

            self.log.info("Step5: On client, Create few more files with special characters")
            self.generate_ifs_data(self.src_dir, "Incremental")

            self.log.info("Step6: Run an Inc job for the subclient and verify if it completes without failures.")
            _ = self.helper.run_backup(backup_level="Incremental")[0]

            self.log.info("Step7: run OOP restore of empty directory and compare.")
            self.log.info("run OOP restore of empty directory [{0}] to "
                          "directory [{1}] and verify.".format(self.src_dir, self.tmp_path))
            self.restore_verify(source=self.src_dir, destination=self.tmp_path)

            self.log.info("Step8: On client, Create few more files with special characters for Diff backup")
            self.generate_ifs_data(self.src_dir, "Differential")

            self.log.info("Step9: Run an Diff job for the subclient and verify if it completes without failures.")
            _ = self.helper.run_backup(backup_level="Differential")[0]

            self.log.info("Step10: run OOP restore of directory and compare.")
            self.log.info("run OOP restore of empty directory [{0}] to "
                          "directory [{1}] and verify.".format(self.src_dir, self.tmp_path))
            self.restore_verify(source=self.src_dir, destination=self.tmp_path)

            self.client_machine.remove_directory(self.src_dir)

            self.log.info("**VERIFICATION OF IFS BACKUP AND RESTORE WITH SPECIAL CHARACTERS USING OPTIMIZED SCAN "
                          "COMPLETED SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED