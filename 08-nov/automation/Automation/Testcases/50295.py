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

        configure_sc()          --  Configure predefined SC and another SC with content

        generate_inc_data()     --  Generate Incremental data on client machine.

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
        IBMi- LFS wildcard filter behavior check with library level and object level backups
            Configure SC with some user libraries with wildcard content.
            Run full backup of the Subclient.
            Generate incremental data with objects picked in full backup changed
            run Incremental backup of the Subclient.
            Perform OOP restore and verify if proper content is picked by backup
            Configure SC with some user libraries with wildcard content and enable object level backup.
            Run full backup of the Subclient.
            Generate incremental data with objects picked in full backup changed
            run Incremental backup of the Subclient.
            Perform OOP restore and verify if proper content is picked by backup
            Configure SC with some user libraries using object level path with wildcard content.
            Enable object level backup
            Run full backup of the Subclient.
            Generate incremental data with objects picked in full backup changed
            run Incremental backup of the Subclient.
            Perform OOP restore and verify if proper content is picked by backup
            Run Cleanup on client machine.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi- LFS wildcard filter behavior check with library level and object level backups"
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
        self.bkp_objs = None
        self.bkp_libs = None
        self.content = None
        self.content1 = None
        self.filter = None
        self.filter1 = None

    def init_tc(self):
        """
        Initalize the TC variables with required values.
        """
        self.dest_lib = "AUTR{0}".format(self.id)
        self.usr_lib = ["R{0}".format(self.id),
                        "D{0}".format(self.id),
                        "O2P",
                        "T{0}2".format(self.id),
                        "T{0}3".format(self.id),
                        "T{0}4".format(self.id),
                        "F{0}2".format(self.id),
                        "F{0}3".format(self.id),
                        "F{0}4".format(self.id)]

        self.bkp_libs = ["T{0}2".format(self.id),
                         "F{0}2".format(self.id),
                         "F{0}3".format(self.id)]

        self.content = []
        for each in self.usr_lib:
            self.content.append(self.client_machine.lib_to_path(each))

        self.filter = ["/QSYS.LIB/[R,D]*.LIB",
                       "/QSYS.LIB/O?P.LIB",
                       "/QSYS.LIB/T{0}[3-4].LIB".format(self.id),
                       "/QSYS.LIB/F{0}[!2-3].LIB".format(self.id)]

        self.bkp_objs = ["/QSYS.LIB/T{0}.LIB/DIR3.FILE".format(self.id),
                         "/QSYS.LIB/T{0}.LIB/FUL2.FILE".format(self.id),
                         "/QSYS.LIB/T{0}.LIB/FUL3.FILE".format(self.id),
                         "/QSYS.LIB/T{0}.LIB/TESTAB.FILE".format(self.id)]

        self.content1 = ["/QSYS.LIB/T{0}.LIB/DIR1.FILE".format(self.id),
                         "/QSYS.LIB/T{0}.LIB/DIR2.FILE".format(self.id),
                         "/QSYS.LIB/T{0}.LIB/DIR3.FILE".format(self.id),
                         "/QSYS.LIB/T{0}.LIB/FUL1.FILE".format(self.id),
                         "/QSYS.LIB/T{0}.LIB/FUL2.FILE".format(self.id),
                         "/QSYS.LIB/T{0}.LIB/FUL3.FILE".format(self.id),
                         "/QSYS.LIB/T{0}.LIB/TESTAA.FILE".format(self.id),
                         "/QSYS.LIB/T{0}.LIB/TESTAB.FILE".format(self.id),
                         "/QSYS.LIB/T{0}.LIB/INC1.FILE".format(self.id),
                         "/QSYS.LIB/T{0}.LIB/INC2.FILE".format(self.id),
                         "/QSYS.LIB/T3{0}.LIB/DIR1.FILE".format(self.id),
                         "/QSYS.LIB/T3{0}.LIB/DIR2.FILE".format(self.id),
                         "/QSYS.LIB/T3{0}.LIB/DIR3.FILE".format(self.id)]

        self.filter1 = ["/QSYS.LIB/T{0}.LIB/DIR[1-2].FILE".format(self.id),
                        "/QSYS.LIB/T{0}.LIB/FUL[!2-3].FILE".format(self.id),
                        "/QSYS.LIB/T{0}.LIB/TES?AA.FILE".format(self.id),
                        "/QSYS.LIB/T{0}.LIB/INC*.FILE".format(self.id),
                        "/QSYS.LIB/T3{0}.LIB/***".format(self.id)]

    def configure_sc(self, opt_type):
        """
               Configure predefined and another subclient with content
               Args:
                   opt_type              (str)          -- Type of backup
        """
        self.log.info("Configuring subclient for %s", opt_type)

        if opt_type == "LIB_LEVEL":
            for each in self.usr_lib:
                self.client_machine.manage_library(operation='delete', object_name=each)
                self.client_machine.populate_lib_with_data(library_name=each, tc_id=self.id, count=1)
            self.subclient_name = "subclient_{0}".format(self.id)
            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=self.content,
                                         filter_content=self.filter,
                                         scan_type=self.scan_type,
                                         data_readers=8,
                                         allow_multiple_readers=True,
                                         delete=True)

        elif opt_type == "OBJ_LEVEL":
            for each in self.usr_lib:
                self.client_machine.manage_library(operation='delete', object_name=each)
                self.client_machine.populate_lib_with_data(library_name=each, tc_id=self.id, count=1)
            self.helper.set_object_level_backup()

        elif opt_type == "OBJ_LEVEL1":
            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=self.content1,
                                         filter_content=self.filter1,
                                         scan_type=self.scan_type,
                                         data_readers=5,
                                         allow_multiple_readers=True,
                                         delete=True)
            self.helper.set_object_level_backup()
            self.client_machine.manage_library(object_name="T{0}".format(self.id))
            self.client_machine.manage_library(object_name="T3{0}".format(self.id))
            obj_names = ["DIR1", "DIR2", "DIR3", "FUL1", "FUL2", "FUL3", "TESTAA", "TESTAB", "INC1", "INC2"]
            for each in obj_names:
                self.client_machine.create_sourcepf(library="T{0}".format(self.id), object_name=each)
            obj_names = ["DIR1", "DIR2", "DIR3"]
            for each in obj_names:
                self.client_machine.create_sourcepf(library="T3{0}".format(self.id), object_name=each)

    def generate_inc_data(self):
        """
            Generate Incremental data on client machine.
        """
        self.log.info("Generating incremental data on client machine")

        for each in self.usr_lib:
            self.client_machine.create_sourcepf(library=each, object_name='CINC')

    def restore_verify(self, opt_type="LIB_LEVEL"):
        """
            Initiates OOP restore for content and verify the restored data and objects reporting ...
            Args:
                   opt_type              (str)          -- which kind of restore to perform
        """
        self.log.info("Run OOP restore of eligible content and verify.")

        if opt_type == "LIB_LEVEL" or opt_type == "OBJ_LEVEL":
            for each in self.bkp_libs:
                self.log.info("run OOP restore of library [{0}] to library [{1}] and verify.".format(each,
                                                                                                     self.dest_lib))
                self.client_machine.manage_library(operation='delete', object_name=self.dest_lib)

                self.job = self.helper.restore_out_of_place(
                    destination_path=self.client_machine.lib_to_path("{0}".format(self.dest_lib)),
                    paths=[self.client_machine.lib_to_path("{0}".format(each))],
                    restore_ACL=False,
                    preserve_level=0)
                self.helper.compare_ibmi_data(
                    source_path="{0}/*".format(self.client_machine.lib_to_path("{0}".format(each))),
                    destination_path="{0}/*".format(self.client_machine.lib_to_path("{0}".format(self.dest_lib))))
                self.client_machine.manage_library(operation='delete', object_name=self.dest_lib)

        if opt_type == "OBJ_LEVEL1":
            for each in self.bkp_objs:
                self.log.info("run OOP restore of object [{0}] to library [{1}] and verify.".format(each,
                                                                                                    self.dest_lib))
                self.client_machine.manage_library(operation='delete', object_name=self.dest_lib)
                self.job = self.helper.restore_out_of_place(
                    destination_path=self.client_machine.lib_to_path("{0}".format(self.dest_lib)),
                    paths=[each],
                    restore_ACL=False,
                    preserve_level=0)
                self.client_machine.manage_library(operation='delete', object_name=self.dest_lib)

    def cleanup(self):
        """
            Cleanup the data on client machine
        """
        for each in self.usr_lib:
            self.client_machine.manage_library(operation='delete', object_name=each)
        self.client_machine.manage_library(operation='delete', object_name=self.dest_lib)
        self.client_machine.manage_library(operation='delete', object_name="T{0}".format(self.id))
        self.client_machine.manage_library(operation='delete', object_name="T3{0}".format(self.id))

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
            backupset_name = "backupset_{0}_{1}".format(self.id, self.IBMiMode)
            self.init_tc()
            self.helper.create_backupset(name=backupset_name)
            self.scan_type = ScanType.RECURSIVE
            self.log.info("*** STARTING VALIDATION OF WILDCARD CONTENT WITH LFS ***")
            self.log.info("***********************************************************")
            self.log.info("Starting validation of Wildcard content for LFS with library level backup")
            self.log.info("***********************************************************")
            self.configure_sc(opt_type="LIB_LEVEL")
            self.job = self.helper.run_backup(backup_level="Full")[0]
            self.generate_inc_data()
            self.job = self.helper.run_backup()[0]
            self.restore_verify(opt_type="LIB_LEVEL")
            self.log.info("Starting validation of wildcard content with object level backup")
            self.configure_sc(opt_type="OBJ_LEVEL")
            self.job = self.helper.run_backup(backup_level="Full")[0]
            self.generate_inc_data()
            self.job = self.helper.run_backup()[0]
            self.restore_verify(opt_type="OBJ_LEVEL")
            self.log.info("Starting validation of wildcard objects as content with object level backup")
            self.configure_sc(opt_type="OBJ_LEVEL1")
            self.job = self.helper.run_backup(backup_level="Full")[0]
            self.generate_inc_data()
            self.job = self.helper.run_backup()[0]
            self.restore_verify(opt_type="OBJ_LEVEL1")
            self.cleanup()
            self.log.info("**IBMi: VALIDATION OF USING WILDCARD CONTENT FOR LFS HAS COMPLETED SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
