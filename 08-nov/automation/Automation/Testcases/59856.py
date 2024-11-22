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

    start_backup()          --  start backup of the subclient and verify if inc/diff has completed in scan phase

    generate_ifs_data()     --  populates a directory on the client with files.

    generate_lfs_data()     --  populates Library file system data on the client with objects.

    run()                   --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Class for executing
        IBMi - Scan marking with LFS, IFS and QDLS with Regular scan, Object level backup
        Step1, configure BackupSet and Subclient with IFS data with regular scan.
        Step2, Run backup full and verify if incremental job completes in scan phase when no data is changed.
        Step3, Run backup differential and verify if job completes in scan phase when no data is changed.
        Step4, configure BackupSet and Subclient with LFS data with regular scan.
        Step5, Run backup full and verify if incremental job completes in scan phase when no data is changed.
        Step6, Run backup differential and verify if job completes in scan phase when no data is changed.
        Step7, configure BackupSet and Subclient with LFS data with Object level backup.
        Step8, Run backup full and verify if incremental job completes in scan phase when no data is changed.
        Step9, Run backup differential and verify if job completes in scan phase when no data is changed.
        Step10, configure BackupSet and Subclient with QDLS data with regular scan.
        Step11, Run backup full and verify if incremental job completes in scan phase when no data is changed.
        Step12, Run backup differential and verify if job completes in scan phase when no data is changed.
        Step13, Cleanup the data created on the disk.
    """
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Scan marking with LFS, IFS and QDLS with Regular scan, Object level backup"
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
        self.srcdir = None
        self.srclib = None

    def start_backup(self, backup_level):
        """
        start backup of the subclient
        Args:
        backup_level            (str)   --  level of backup
                (Full/Incremental/Differential)
        """
        job = self.helper.run_backup(backup_level=backup_level)[0]
        if backup_level == "Incremental" or backup_level == "Differential":
            if self.helper.verify_scan_marking(job_id=job.job_id):
                self.log.info("{1} backup ID:{0} has completed in scan phase".format(job.job_id, backup_level))
            else:
                raise Exception("{1} backup ID:{0} has not completed in scan phase".format(job.job_id, backup_level))

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

    def generate_lfs_data(self, library):
        """populates Library file system data on the client with objects.
        Args:
            library                 (str)   -- Name of the library
        """

        self.log.info("Creating library %s with objects", library)
        self.client_machine.populate_lib_with_data(library_name=library, tc_id=self.id, count=5, prefix="F")

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.RECURSIVE
            self.log.info("*** STARTING RUN FOR SC ADDITIONAL OPTIONS validation WITH <ContentFIle> ***")
            self.log.info("Step1, configure BackupSet and Subclient with IFS content.")
            backupset_name = "backupset_{0}".format(self.id)
            self.helper.create_backupset(name=backupset_name, delete=False)
            self.subclient_name = "subclient_IFS_{0}".format(self.id)
            self.srcdir = "/AUTO{0}".format(self.id)
            self.generate_ifs_data(self.srcdir, "F", delete=True)
            self.log.info("Create subclient for IFS with %s", self.scan_type.name)
            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=[self.srcdir],
                                         scan_type=self.scan_type,
                                         delete=True)
            self.start_backup(backup_level="Full")
            self.start_backup(backup_level="Incremental")
            self.start_backup(backup_level="Differential")
            self.log.info("Verified IFS backup completed in scan phase with %s", self.scan_type.name)
            self.client_machine.remove_directory(self.srcdir)

            self.log.info("Configure BackupSet and Subclient with LFS content")
            self.subclient_name = "subclient_LFS_{0}".format(self.id)
            self.srclib = "TC{0}".format(self.id)
            self.generate_lfs_data(library=self.srclib)
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
                self.start_backup(backup_level="Full")
                self.start_backup(backup_level="Incremental")
                self.start_backup(backup_level="Differential")
                self.log.info("Verified that LFS backup completed in scan phase with %s", each)
            self.client_machine.manage_library(operation='delete', object_name=self.srclib)

            self.log.info("Configure BackupSet and Subclient with QDLS content")
            self.subclient_name = "subclient_QDLS_{0}".format(self.id)
            usr_flr = "A{0}".format(self.id)
            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=["/QDLS/{0}".format(usr_flr)],
                                         scan_type=ScanType.RECURSIVE,
                                         data_readers=5,
                                         allow_multiple_readers=True,
                                         delete=True)
            self.log.info("On client, create a folder %s with documents", usr_flr)
            self.client_machine.populate_QDLS_data(folder_name=usr_flr, tc_id=self.id, count=5)
            self.start_backup(backup_level="Full")
            self.start_backup(backup_level="Incremental")
            self.start_backup(backup_level="Differential")
            self.client_machine.manage_folder(operation='delete', folder_name=usr_flr)
            self.log.info("Verified that QDLS backup completed in scan phase")

            self.log.info("**LFS, IFS & QDLS BACKUP HAS COMPLETED SUCCESSFULLY IN SCAN PHASE WHEN NO DATA TO BACKUP**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
