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

    start_backup()          --  start backup of the subclient

    generate_lfs_data()     --  populates Library file system data on the client with objects.

    generate_inc_data()     --  Generate Incremental data on client machine.

    restore_verify()		-- Initiates restore for data backed up in the given job and performs the applicable verifications

    cleanup()       		--	Cleanup the data on client machine

    run()                   --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Class for executing
        IBMi - Validation of LFS backup and restore with content having special characters
        Library Level:
        Step1, configure BackupSet and Subclients for TC
        Step2: On client, create two libraries with names having special characters
        Step3: Run a full backup for the subclient and verify if it completes without failures.
        Step4: On client, Create few more objects with special characters for Inc backup
        Step5: Run an Inc job for the subclient and verify if it completes without failures.
        Step6: run OOP restore of empty library and compare.
        Step7: On client, Create few more files with special characters for Diff backup.
        Step8: Run an Diff job for the subclient and verify if it completes without failures.
        Step9:Run OOP restore of directory and compare.
        Step10, Cleanup the data created on the disk.
        Object Level:
        Step1, configure BackupSet and Subclients for TC
        Step2: On client, create two libraries with names having special characters
        Step3: Run a full backup for the subclient and verify if it completes without failures.
        Step4: On client, Create few more objects with special characters for Inc backup
        Step5: Run an Inc job for the subclient and verify if it completes without failures.
        Step6: run OOP restore of empty library and compare.
        Step7: On client, Create few more files with special characters for Diff backup.
        Step8: Run an Diff job for the subclient and verify if it completes without failures.
        Step9:Run OOP restore of directory and compare.
        Step10, Cleanup the data created on the disk.
        ****Run Library level backup for VTL and Parallel VTL.****
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Validation of LFS backup and restore with content having special characters"
        # Other attributes which will be initialized in FSHelper.populate_tc_inputs
        self.tcinputs = {
            "UserName": None,
            "Password": None,
            "TestPath": None,
            "StoragePolicyName": None
        }
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.subclient_name = None
        self.client_machine = None
        self.scan_type = None
        self.src_dir = None
        self.src_lib = None
        self.dest_lib = None
        self.IBMiMode = None
        self.job = None

    def start_backup(self, backup_level):
        """
        start backup of the subclient
        Args:
        backup_level            (str)   --  level of backup
                (Full/Incremental/Differential)
        """
        job = self.helper.run_backup(backup_level=backup_level)[0]

    def generate_lfs_data(self):
        """populates Library file system data on the client with objects.
        """
        for each in self.src_lib:
            self.log.info("Creating library %s with objects", each)
            self.client_machine.populate_lib_with_data(library_name=each, tc_id=self.id, count=1, prefix="F")
            self.client_machine.create_sourcepf(library=each, object_name="Z_$@#X")
            self.client_machine.create_sourcepf(library=each, object_name='"z_$&#x"')

    def generate_inc_data(self, backup_level="Incremental"):
        """
            Generate Incremental data on client machine.
            Args:
        backup_level            (str)   --  level of backup
                (Incremental/Differential)
        """
        if backup_level == "Incremental":
            self.log.info("Generating incremental data on client machine")
            for each in self.src_lib:
                self.client_machine.create_sourcepf(library=each, object_name="Z_$@#I")
                self.client_machine.create_sourcepf(library=each, object_name='"z_$&#i"')
        elif backup_level == "Differential":
            self.log.info("Generating incremental data on client machine")
            for each in self.src_lib:
                self.client_machine.create_sourcepf(library=each, object_name="Z_$@#D")
                self.client_machine.create_sourcepf(library=each, object_name='"z_$@#d"')

    def restore_verify(self):
        """
                Initiates restore for data backed up in the given job
                and performs the applicable verifications

        """
        self.log.info("Starting restore to destination path {0} ".format(self.dest_lib))
        for each in self.src_lib:
            self.log.info("Deleting destination library {0} to restore {1}".format(self.dest_lib, each))
            self.client_machine.manage_library(operation='delete', object_name=self.dest_lib)
            self.helper.restore_out_of_place(self.client_machine.lib_to_path(self.dest_lib),
                                             paths=[self.client_machine.lib_to_path(each)],
                                             restore_ACL=False,
                                             preserve_level=0)
            self.helper.compare_ibmi_data(source_path="{0}/*".format(self.client_machine.lib_to_path(each)),
                                          destination_path="{0}/*".format(self.client_machine.lib_to_path(
                                              self.dest_lib)))

    def cleanup(self):
        """
            Cleanup the data on client machine
        """
        for each in self.src_lib:
            self.client_machine.manage_library(operation='delete', object_name=each)
        self.client_machine.manage_library(operation='delete', object_name=self.dest_lib)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.RECURSIVE
            self.log.info("*** STARTING RUN FOR VALIDATING LFS CONTENT WITH SPECIAL CHARS BACKUPS ***")
            backupset_name = "backupset_{0}".format(self.id)
            self.helper.create_backupset(name=backupset_name, delete=False)

            self.log.info("Configure BackupSet and Subclient with LFS content")
            self.subclient_name = "subclient_LFS_{0}".format(self.id)
            self.src_lib = ['T_$@#X', '"t_$&#x"']
            self.dest_lib = "TR{0}".format(self.id)
            scans = ["Library_Level"]
            if self.IBMiMode == "NON-VTL":
                scans.append("Object_Level")
            for each in scans:
                self.log.info("Create subclient for LFS with {0}".format(each))
                self.helper.create_subclient(name=self.subclient_name,
                                             storage_policy=self.storage_policy,
                                             content=[self.client_machine.lib_to_path(self.src_lib[0]),
                                                      self.client_machine.lib_to_path(self.src_lib[1])],
                                             scan_type=self.scan_type,
                                             delete=True)
                if self.IBMiMode == "VTLParallel":
                    self.log.info("Enable multiple drives option for VTL Backup")
                    self.helper.set_vtl_multiple_drives()
                if each == "Object_Level":
                    self.log.info("Enabling Object level backup")
                    self.helper.set_object_level_backup(True)
                self.generate_lfs_data()
                self.start_backup(backup_level="FULL")
                self.generate_inc_data(backup_level="Incremental")
                self.start_backup(backup_level="Incremental")
                self.restore_verify()
                self.generate_inc_data(backup_level="Differential")
                self.start_backup(backup_level="Differential")
                self.restore_verify()
                self.log.info("Verified LFS backup and restore with new Subclient content with %s", self.scan_type)
            self.log.info("Backup of LFS new SC content verification is successful")
            self.cleanup()
            self.log.info("**LFS CONTENT WITH SPECIAL CHARS BACKUP AND RESTORE COMPLETED SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
