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

        init_tc()               --  Initalize the TC variables

        configure_sc()          --  Configure SC with content and filters.

        generate_data()         --  Generate data on client machine.

        restore_verify()        --  Initiates OOP restore for content and verify the Advanced restore options

        cleanup()               --  Cleanup the data on client machine

        run()                   --  run function of this test case
"""

from collections import deque

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Class for executing
        IBMi- Validation of LFS exception content addition after backup behaviour check with library level and
        object level backups

            Configure SC with some user libraries with wildcard content, wildcard filters and wildcard exception content
            Run full backup of the Subclient.
            Update the SC with additional exception content.
            Run Incremental backup of the subclient.
            Perform OOP restore and verify if proper content is picked by backup
            Configure SC with some user libraries with wildcard content, wildcard filters and wildcard exception content
                and enable object level backup.
            Run full backup of the Subclient.
            Update the SC with additional exception content.
            Run Incremental backup of the subclient.
            Perform OOP restore and verify if proper content is picked by backup
            Configure SC with some user libraries with wildcard object level content, wildcard object level filters
                and wildcard object level exception content.
            Enable object level backup
            Run full backup of the Subclient.
            Update the SC with additional exception content.
            Run Incremental backup of the subclient.
            Perform OOP restore and verify if proper content is picked by backup
            Run Cleanup on client machine.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi- Validation of LFS exception content addition after backup behaviour check with " \
                    "library level and object level backups"
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.tcinputs = {
            "IBMiMode": None,
            "whichPython": None
        }
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.subclient_name = None
        self.client_machine = None
        self.dest_lib = None
        self.sc_name = None
        self.job = None
        self.scan_type = None
        self.IBMiMode = None
        self.usr_lib = None
        self.content = None
        self.filter = None
        self.exception = None
        self.validate = None
        self.usr_obj = None
        self.job_inc = None

    def init_tc(self):
        """
        Initalize the TC variables with required values.
        """
        self.dest_lib = "AUTR{0}".format(self.id)
        # self.content = []
        self.exception = []
        self.filter = []
        self.validate = []
        self.usr_lib = []
        self.usr_obj = []
        self.content = [["/QSYS.LIB/TC{0}0.LIB".format(self.id),
                         "/QSYS.LIB/L?{0}.LIB".format(self.id)],
                        ["/QSYS.LIB/TC{0}1.LIB".format(self.id),
                         "/QSYS.LIB/O?{0}.LIB".format(self.id)],
                        ["/QSYS.LIB/TC{0}2.LIB".format(self.id),
                         "/QSYS.LIB/FT3{0}.LIB/DIR[1-3].FILE".format(self.id)]
                        ]
        self.filter = [["/QSYS.LIB/L*"],
                       ["/QSYS.LIB/O*"],
                       ["/QSYS.LIB/F*"]]
        self.exception = [["/QSYS.LIB/L[R,D]*.LIB"],
                          ["/QSYS.LIB/O[R,D]*.LIB"],
                          ["/QSYS.LIB/FT3{0}.LIB/***".format(self.id),
                           "/QSYS.LIB/FT{0}.LIB/DIR[1-2].FILE".format(self.id)]]
        self.usr_lib = [["LD{0}".format(self.id), "TC{0}0".format(self.id)],
                        ["OD{0}".format(self.id), "TC{0}1".format(self.id)],
                        ["FT3{0}".format(self.id), "TC{0}2".format(self.id)]]
        self.usr_obj = ["DIR1", "DIR2","DIR3"]

    def configure_sc(self, opt_type):
        """
               Configure subclient with content and filters
               Args:
                   opt_type              (int)          -- Type of backup
        """
        self.log.info("Configuring subclient..")

        self.subclient_name = "subclient_{0}_{1}".format(self.id, opt_type)
        self.helper.create_subclient(name=self.subclient_name,
                                     storage_policy=self.storage_policy,
                                     content=self.content[opt_type],
                                     filter_content=self.filter[opt_type],
                                     exception_content=self.exception[opt_type],
                                     scan_type=self.scan_type,
                                     data_readers=8,
                                     allow_multiple_readers=True,
                                     delete=True)
        if opt_type != 0:
            self.helper.set_object_level_backup()

    def generate_data(self, opt_type):
        """
            Generate data on client machine.
            Args:
                   opt_type              (int)          -- Type of backup
        """
        self.log.info("Generating data on client machine")

        for each in self.usr_lib[opt_type]:
            self.client_machine.populate_lib_with_data(library_name=each, tc_id=self.id, count=0)
            self.client_machine.create_sourcepf(library=each, object_name="constant")
            for objs in self.usr_obj:
                self.client_machine.create_sourcepf(library=each, object_name=objs)

    def generate_incdata(self, opt_type):
        """
            Generate data on client machine.
            Args:
                   opt_type              (int)          -- Type of backup
        """
        self.log.info("Generating Incremental data on client machine")
        for each in self.usr_lib[opt_type]:
            self.client_machine.delete_file_object(library=each, object_name="DIR1")
            self.client_machine.create_sourcepf(library=each, object_name="DIR1")
            self.client_machine.create_sourcepf(library=each, object_name="INC1")

    def restore_verify(self, opt_type):
        """
            Initiates OOP restore for content and verify the restored data and objects reporting ...
            Args:
                   opt_type              (int)          -- Type of restore to perform
        """
        self.log.info("Run OOP restore and make sure content is not picked after removing exceptions")

        self.client_machine.manage_library(operation='delete', object_name=self.dest_lib)
        self.job = self.helper.restore_out_of_place(
            destination_path=self.client_machine.lib_to_path("{0}".format(self.dest_lib)),
            paths=["{0}/DIR1.FILE".format(self.client_machine.lib_to_path(self.usr_lib[opt_type][0]))],
            restore_ACL=False,
            preserve_level=0,
            from_time=self.job_inc.start_time,
            to_time=self.job_inc.end_time,
            **{'wait_to_complete': False})
        self.job.wait_for_completion()
        if not self.job.status.lower() == "failed":
            raise Exception(
                "Restore job status is not failed, job has status: {0}".format(self.job.status))
        else:
            self.log.info("Exception content {0}/DIR1.FILE hasn't picked and Restore has successfully "
                          "failed".format(self.client_machine.lib_to_path(self.usr_lib[opt_type][0])))
        self.client_machine.manage_library(operation='delete', object_name=self.dest_lib)

    def cleanup(self, opt_type):
        """
            Cleanup the data on client machine
             Args:
                   opt_type              (int)          -- Type of restore to perform
        """
        for each in self.usr_lib[opt_type]:
            self.client_machine.manage_library(operation='delete', object_name=each)
        self.client_machine.manage_library(operation='delete', object_name=self.dest_lib)

    def run(self):
        """
            Main function for test case execution
        """
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)
            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.init_tc()
            self.helper.create_backupset(name="backupset_{0}_{1}".format(self.id, self.IBMiMode))
            self.scan_type = ScanType.RECURSIVE
            self.log.info("*** STARTING VALIDATION OF WILDCARD EXCEPTIONS WITH LFS ***")

            for each in [0, 1, 2]:
                if each == 0:
                    process = "Library level"
                elif each == 1:
                    process = "Object level with library level path"
                elif each == 2:
                    process = "Object level with object level path"
                self.log.info("***********************************************************")
                self.log.info("Starting validation of adding exception after backup for LFS with {0}".format(process))
                self.log.info("***********************************************************")
                self.generate_data(each)
                self.configure_sc(each)
                self.job = self.helper.run_backup(backup_level="Full")[0]
                self.log.info("updating the subclient to remove exception content")
                self.helper.update_subclient(exception_content=["/none"])
                self.job_inc = self.helper.run_backup(backup_level="Incremental")[0]
                self.restore_verify(each)
                self.cleanup(each)
            self.log.info("**IBMi: VALIDATION OF REMOVAL OF EXCEPTION CONTENT AFTER BACKUP FOR LFS "
                          "HAS COMPLETED SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
