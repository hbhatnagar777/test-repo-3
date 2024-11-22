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
        IBMi -Verify newly added subclient content is backed up by inc/diff backup job
        Step1, configure BackupSet and Subclient with IFS data with regular scan.
        Step2, Run backup full + add new content to SC and perform incremental backup
        step3, restore and verify if new SC content is picked by backup.
        Step4, Add new content to SC and run backup differential
        step5, restore and verify if new SC content is picked by backup.
        Step6, configure BackupSet and Subclient with LFS data with regular scan.
        Step7, Run backup full + Add new content to SC and run incremental
        step8, restore and verify if new SC content is picked by backup.
        Step9, Add new content to SC and run backup differential
        step10, restore and verify if new SC content is picked by backup.
        Step11, configure BackupSet and Subclient with LFS data with Regular scan and Object level backup.
        Step12, Run backup full + Add new content to SC and run incremental
        step13, restore and verify if new SC content is picked by backup.
        Step14, Add new content to SC and run backup differential and verify the data with a restore
        step15, restore and verify if new SC content is picked by backup.
        Step16, Cleanup the data created on the disk.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi -Verify newly added subclient content is backed up by inc/diff backup job"
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
        self.src_dir = None
        self.src_lib = None
        self.dest_lib = None
        self.IBMiMode = None

    def start_backup(self, backup_level):
        """
        start backup of the subclient
        Args:
        backup_level            (str)   --  level of backup
                (Full/Incremental/Differential)
        """
        job = self.helper.run_backup(backup_level=backup_level)[0]

    def generate_ifs_data(self):
        """populates a directory on the client with files.
        """
        for each in self.src_dir:
            self.log.info("Populating IFS data for directory {0}".format(each))
            self.client_machine.populate_ifs_data(directory_name=each,
                                                  tc_id=self.id,
                                                  count=2,
                                                  prefix="F",
                                                  delete=True)

    def generate_lfs_data(self):
        """populates Library file system data on the client with objects.
        """
        for each in self.src_lib:
            self.log.info("Creating library %s with objects", each)
            self.client_machine.populate_lib_with_data(library_name=each, tc_id=self.id, count=5, prefix="F")

    def restore_verify(self, source, destination, fstype="IFS"):
        """
                Initiates restore for data backed up in the given job
                and performs the applicable verifications

                    Args:
                        source              (list)   : Source data path

                        destination        (str)   : destination path for restoring the data

                        fstype             (str)    : fstype of restore source
        """
        self.log.info("Starting restore {0} to destination path {1} ".format(source, destination))
        for each in source:
            if fstype == "LFS":
                self.log.info("Deleting destination library {0} to restore {1}".format(self.dest_lib, each))
                self.client_machine.manage_library(operation='delete', object_name=self.dest_lib)
            self.helper.restore_out_of_place(destination,
                                             paths=[each],
                                             restore_ACL=False,
                                             preserve_level=0)
            self.helper.compare_ibmi_data(source_path="{0}/*".format(each),
                                          destination_path="{0}/*".format(destination))

    def cleanup(self):
        """
            Cleanup the data on client machine
        """
        for each in self.src_lib:
            self.client_machine.manage_library(operation='delete', object_name=each)
        self.client_machine.manage_library(operation='delete', object_name=self.dest_lib)
        for each in self.src_dir:
            self.client_machine.remove_directory(each)
        self.client_machine.remove_directory(self.tmp_path)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.RECURSIVE
            self.log.info("*** STARTING RUN FOR VALIDATING NEW SC CONTENT PICKED BY INC/DIFF BACKUPS ***")
            self.log.info("Step1, configure BackupSet and Subclient with IFS content.")
            backupset_name = "backupset_{0}".format(self.id)
            self.helper.create_backupset(name=backupset_name, delete=False)
            self.subclient_name = "subclient_IFS_{0}".format(self.id)
            self.src_dir = ["/AUTO{0}".format(self.id),
                            "/AUTO{0}1".format(self.id),
                            "/AUTO{0}2".format(self.id)]
            self.tmp_path = "/AUTOR{0}".format(self.id)
            self.log.info("Create subclient for IFS with %s", self.scan_type.name)
            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=[self.src_dir[0]],
                                         scan_type=self.scan_type,
                                         delete=True)
            if self.IBMiMode == "VTLParallel":
                self.log.info("Enable multiple drives option for VTL Backup")
                self.helper.set_vtl_multiple_drives()
            self.generate_ifs_data()
            self.start_backup(backup_level="FULL")

            self.helper.update_subclient(content=[self.src_dir[0], self.src_dir[1]])
            self.start_backup(backup_level="Incremental")
            self.restore_verify(source=[self.src_dir[1]], destination=self.tmp_path)

            self.helper.update_subclient(content=self.src_dir)
            self.start_backup(backup_level="Differential")
            self.restore_verify(source=[self.src_dir[2]], destination=self.tmp_path)
            self.log.info("Verified IFS backup and restore with new subclient contentis picked with %s", self.scan_type)
            self.log.info("Backup of IFS new SC content verification is successful")

            self.log.info("Configure BackupSet and Subclient with LFS content")
            self.subclient_name = "subclient_LFS_{0}".format(self.id)
            self.src_lib = ["TC{0}".format(self.id),
                           "TC{0}1".format(self.id),
                           "TC{0}2".format(self.id)]
            self.dest_lib = "TR{0}".format(self.id)
            scans = ["Library_Level"]
            if self.IBMiMode == "NON-VTL":
                scans.append("Object_Level")
            for each in scans:
                self.log.info("Create subclient for LFS with {0}".format(each))
                self.helper.create_subclient(name=self.subclient_name,
                                             storage_policy=self.storage_policy,
                                             content=[self.client_machine.lib_to_path(self.src_lib[0])],
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

                self.helper.update_subclient(content=[self.client_machine.lib_to_path(self.src_lib[0]),
                                                      self.client_machine.lib_to_path(self.src_lib[1])])
                self.start_backup(backup_level="Incremental")
                self.restore_verify(source=[self.client_machine.lib_to_path(self.src_lib[1])],
                                    destination=self.client_machine.lib_to_path(self.dest_lib),
                                    fstype="LFS")
                self.helper.update_subclient(content=[self.client_machine.lib_to_path(self.src_lib[0]),
                                                      self.client_machine.lib_to_path(self.src_lib[1]),
                                                      self.client_machine.lib_to_path(self.src_lib[2])])
                self.start_backup(backup_level="Differential")
                self.restore_verify(source=[self.client_machine.lib_to_path(self.src_lib[2])],
                                    destination=self.client_machine.lib_to_path(self.dest_lib),
                                    fstype="LFS")
                self.log.info("Verified LFS backup and restore with new Subclient content with %s", self.scan_type)
            self.log.info("Backup of LFS new SC content verification is successful")
            self.cleanup()
            self.log.info("**LFS, IFS REGULAR SCAN BACKUP HAS PICKED NEW CONTENT ON DISK SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
