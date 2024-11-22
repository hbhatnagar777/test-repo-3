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
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Class for executing
        IBMi - Verify backup cycle Full-Differential -Differential for IFS and LFS data
        Step1, configure BackupSet and Subclient with IFS data with regular scan.
        Step2, Run backup full + Differential and verify the data with a restore
        Step3, Run backup Differential and verify the data with a restore
        Step4, configure BackupSet and Subclient with LFS data with regular scan.
        Step5, Run backup full + Differential and verify the data with a restore
        Step6, Run backup Differential and verify the data with a restore
        Step7, configure BackupSet and Subclient with LFS data with Regular scan and Object level backup.
        Step8, Run backup full + Differential and verify the data with a restore
        Step9, Run backup Differential and verify the data with a restore
        Step10, Cleanup the data created on the disk.

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Verify backup cycle Full-Differential-Differential for IFS and LFS data"
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
        self.tmp_path = None
        self.srcdir = None
        self.srclib = None
        self.destlib = None

    def start_backup(self, backup_level):
        """
        start backup of the subclient
        Args:
        backup_level            (str)   --  level of backup
                (Full/Incremental/Differential)
        """
        _ = self.helper.run_backup(backup_level=backup_level)[0]

    def generate_ifs_data(self, directory_name, prefix, delete):
        """populates a directory on the client with files.
        Args:
            directory_name  (str)   --  name / full path of the directory to create
            delete          (bool)  : delete before populating the data
            prefix           (str)   : prefix of file names to be created.
        """
        self.log.info("Populating IFS data for directory {0}".format(directory_name))
        self.client_machine.populate_ifs_data(directory_name=directory_name,
                                              tc_id=self.id,
                                              count=5,
                                              prefix=prefix,
                                              delete=delete)

    def generate_lfs_data(self, library, backup_level):
        """populates Library file system data on the client with objects.
        Args:
            library                 (str)   -- Name of the library
            backup_level            (str)   --  level of backup
                (Full/Incremental/Differential)
        """

        if backup_level == "Full":
            self.log.info("Creating library %s with objects", library)
            self.client_machine.populate_lib_with_data(library_name=library, tc_id=self.id, count=5, prefix="F")
        elif backup_level == "Incremental":
            object_name = ['INCPF1', "INCPF2", "INCPF3"]
            self.log.info("Adding data under library: %s", library)
            for objs in object_name:
                self.client_machine.create_sourcepf(library=library, object_name=objs)
        elif backup_level == "Differential":
            object_name = ['DIFPF1', "DIFPF2", "DIFPF3"]
            self.log.info("Adding data under library: %s", library)
            for objs in object_name:
                self.client_machine.create_sourcepf(library=library, object_name=objs)
        else:
            self.log.info("Backup level %s is invalid", backup_level)

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

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.RECURSIVE
            self.log.info("*** STARTING VALIDATION OF BACKUP CYCLE with DIFF & DIFF FOR IFS and LFS DATA ***")
            self.log.info("Step1, configure BackupSet and Subclient with IFS content.")
            backupset_name = "backupset_{0}".format(self.id)
            self.helper.create_backupset(name=backupset_name, delete=False)
            self.subclient_name = "subclient_IFS_{0}".format(self.id)
            self.srcdir = "/AUTO{0}".format(self.id)
            self.tmp_path = "/AUTOR{0}".format(self.id)
            self.log.info("Create subclient for IFS with %s", self.scan_type.name)
            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=[self.srcdir],
                                         scan_type=self.scan_type,
                                         delete=True)
            self.generate_ifs_data(self.srcdir, "F", delete=True)
            self.start_backup(backup_level="FULL")
            self.generate_ifs_data(self.srcdir, "I", delete=False)
            self.start_backup(backup_level="Differential")
            self.restore_verify(source=self.srcdir, destination=self.tmp_path)
            self.generate_ifs_data(self.srcdir, "D", delete=False)
            self.start_backup(backup_level="Differential")
            self.restore_verify(source=self.srcdir, destination=self.tmp_path)
            self.log.info("Verified IFS backup and restore with diff + diff backup cycle with %s", self.scan_type.name)
            self.client_machine.remove_directory(self.srcdir)
            self.client_machine.remove_directory(self.tmp_path)

            self.log.info("Configure BackupSet and Subclient with LFS content")
            self.subclient_name = "subclient_LFS_{0}".format(self.id)
            self.srclib = "TC{0}".format(self.id)
            self.destlib = "TR{0}".format(self.id)
            scans = ["Library_Level", "Object_Level"]
            for each in scans:
                self.log.info("Create subclient for LFS with {0}".format(each))
                self.helper.create_subclient(name=self.subclient_name,
                                             storage_policy=self.storage_policy,
                                             content=[self.client_machine.lib_to_path(self.srclib)],
                                             scan_type=self.scan_type,
                                             delete=True)
                if each == "Object_Level":
                    self.log.info("Enabling Object level backup")
                    self.helper.set_object_level_backup(True)
                self.generate_lfs_data(library=self.srclib, backup_level="Full")
                self.start_backup(backup_level="FULL")
                self.generate_lfs_data(library=self.srclib, backup_level="Incremental")
                self.start_backup(backup_level="Differential")
                self.client_machine.manage_library(operation='delete', object_name=self.destlib)
                self.restore_verify(source=self.client_machine.lib_to_path(self.srclib),
                                    destination=self.client_machine.lib_to_path(self.destlib))
                self.generate_lfs_data(library=self.srclib, backup_level="Differential")
                self.start_backup(backup_level="Differential")
                self.client_machine.manage_library(operation='delete', object_name=self.destlib)
                self.restore_verify(source=self.client_machine.lib_to_path(self.srclib),
                                    destination=self.client_machine.lib_to_path(self.destlib))
                self.log.info("Verified LFS backup and restore with diff + diff backup cycle with %s",
                              self.scan_type.name)

            self.client_machine.manage_library(operation='delete', object_name=self.srclib)
            self.client_machine.manage_library(operation='delete', object_name=self.destlib)

            self.log.info("**LFS, IFS REGULAR SCAN BACKUP CYCLE WITH DIFF + DIFF IS SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED