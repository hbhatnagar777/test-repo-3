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

        configure_sc()          --  Configure predefined SC and another SC with content

        generate_inc_data()     --  Generate Incremental data on client machine.

        restore_verify()        --  Initiates OOP restore for content and verify the restored data and objects reporting

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
        IBMi - Verify objects and members count reporting with restores
        for non-VTL, test with Optimized scan and regular scan and object level do as following.
            Configure SC with some user libraries.
            Run full backup of the Subclient.
            Generate incremental data with objects picked in full backup changed
            run Incremental backup of the Subclient.
            Generate incremental data with objects picked in full and previous inc backup changed
            run Incremental backup of the Subclient.
            Perform OOP restore and verify the restored data.
            Verify objects and member reporting with restore job.
            Repeat the test with SYNCLIB for Optimized scan and regular scan library level backup
            Run Cleanup on client machine.
        for VTL , test with regular scan do as following.
            Configure SC with some user libraries.
            Run full backup of the Subclient.
            Generate incremental data with objects picked in full backup changed
            run Incremental backup of the Subclient.
            Generate incremental data with objects picked in full and previous inc backup changed
            run Incremental backup of the Subclient.
            Perform OOP restore and verify the restored data.
            Verify objects and member reporting with restore job.
            Repeat the test with SYNCLIB backup enabled.
            Run Cleanup on client machine.
        for Parallel VTL, test with regular scan do as following.
            Configure SC with some user libraries.
            Run full backup of the Subclient.
            Generate incremental data with objects picked in full backup changed
            run Incremental backup of the Subclient.
            Generate incremental data with objects picked in full and previous inc backup changed
            run Incremental backup of the Subclient.
            Perform OOP restore and verify the restored data.
            Verify objects and member reporting with restore job.
            Repeat the test with SYNCLIB backup enabled.
            Run Cleanup on client machine.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Verify objects and members count reporting with restores"
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
        self.destlib = None
        self.sc_name = None
        self.job = None
        self.scan_type = None
        self.IBMiMode = None
        self.usr_lib = None
        self.src_path = None
        self.savact1 = None
        self.savact2 = None

    def configure_sc(self, scan_type):
        """
               Configure predefined and another subclient with content
               Args:
                   scan_type              (str)          -- Scan Type
        """
        self.log.info("Configuring subclient for %s", scan_type.name)
        if self.IBMiMode == "NON-VTL":
            data_readers = 2
            allow_multiple_readers = True
        else:
            data_readers = 1
            allow_multiple_readers = False
        self.subclient_name = "subclient_{0}".format(self.id)
        self.src_path = []
        set_object_level = False
        if scan_type == ScanType.CHANGEJOURNAL:
            scan_type = ScanType.RECURSIVE
            set_object_level = True
        for each in self.usr_lib:
            self.client_machine.manage_library(operation='delete', object_name=each)
            self.client_machine.populate_lib_with_data(library_name=each, tc_id=self.id, count=5)
            self.src_path.append(self.client_machine.lib_to_path(each))
            self.log.info("Create 15 files starting with A and B under library %s", each)
            for num in range(15):
                self.client_machine.create_sourcepf(library=each, object_name='A{0}'.format(num))
                self.client_machine.create_sourcepf(library=each, object_name='B{0}'.format(num))

        self.helper.create_subclient(name=self.subclient_name,
                                     storage_policy=self.storage_policy,
                                     content=self.src_path,
                                     scan_type=scan_type,
                                     data_readers=data_readers,
                                     allow_multiple_readers=allow_multiple_readers,
                                     delete=True)
        self.helper.set_object_level_backup(set_object_level)
        if self.IBMiMode == "VTLParallel":
            self.log.info("Enable multiple drives option for VTL Backup")
            self.helper.set_vtl_multiple_drives()

    def generate_inc_data(self, run_count=1):
        """
            Generate Incremental data on client machine.
            Args:
                   run_count              (str)          -- which run of Incremental
        """
        self.log.info("Generating incremental data on client machine")

        change_objects = 8 if run_count == 1 else 6
        for each in self.usr_lib:
            if run_count == 1:
                self.client_machine.create_savf(lib=each, size=5000)
            self.log.info("Modifying {0} file members starting with A and B under library {1}".format(run_count, each))
            for num in range(change_objects):
                self.client_machine.create_sourcepf(library=each, object_name='C{0}'.format(num))
                mbr_path = "/QSYS.LIB/{0}.LIB/A{1}.FILE/A{1}.MBR".format(each, num)
                self.client_machine.run_ibmi_command(command="echo '##' >{0}".format(mbr_path))
                mbr_path = "/QSYS.LIB/{0}.LIB/A{1}.FILE/A{1}1.MBR".format(each, num)
                self.client_machine.run_ibmi_command(command="echo '##' >{0}".format(mbr_path))
                mbr_path = "/QSYS.LIB/{0}.LIB/B{1}.FILE/B{1}.MBR".format(each, num)
                self.client_machine.run_ibmi_command(command="echo '##' >{0}".format(mbr_path))

    def restore_verify(self):
        """
            Initiates OOP restore for content and verify the restored data and objects reporting ...
        """
        self.log.info("Run OOP restore of both libraries and verify.")

        for each in self.usr_lib:
            self.log.info("run OOP restore of library [{0}] to library [{1}] and verify.".format(each, self.destlib))
            self.client_machine.manage_library(operation='delete', object_name=self.destlib)
            self.job = self.helper.restore_out_of_place(
                destination_path=self.client_machine.lib_to_path("{0}".format(self.destlib)),
                paths=[self.client_machine.lib_to_path("{0}".format(each))],
                restore_ACL=False,
                preserve_level=0)
            self.log.info("Total files restored are {0}".format(self.job.details['jobDetail']['generalInfo']
                                                                ['totalNumOfFiles']))
            if self.job.details['jobDetail']['detailInfo']['skippedItems'] == 0:
                self.log.info("Restore job has not reported any skipped objects")
            else:
                raise Exception("Restore job has reported skipped objects")
            # if self.job.details['jobDetail']['detailInfo']['totalNumOfFiles'] == 59:
            #     self.log.info("Restore job has reported the object count properly")
            # else:
            #     raise Exception("Restore job has skipped objects")
            self.helper.compare_ibmi_data(
                source_path="{0}/*".format(self.client_machine.lib_to_path("{0}".format(each))),
                destination_path="{0}/*".format(self.client_machine.lib_to_path("{0}".format(self.destlib))))
            self.client_machine.manage_library(operation='delete', object_name=self.destlib)

    def cleanup(self):
        """
            Cleanup the data on client machine
        """
        for each in self.usr_lib:
            self.client_machine.manage_library(operation='delete', object_name=each)
        self.client_machine.manage_library(operation='delete', object_name=self.destlib)

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
            self.destlib = "AUTR{0}".format(self.id)
            self.usr_lib = ["AUT{0}".format(self.id), "AUT{0}1".format(self.id)]
            self.helper.create_backupset(name=backupset_name)
            self.scan_type = [ScanType.RECURSIVE]
            if self.IBMiMode == "NON-VTL":
                self.scan_type.append(ScanType.OPTIMIZED)
                # Change journal scan type is used for Object level backup
                self.scan_type.append(ScanType.CHANGEJOURNAL)
            self.log.info("*** STARTING VALIDATION OF RESTORE OBJECTS REPORTING WITH {0}***".format(self.IBMiMode))
            for each in self.scan_type:
                if each.name == "CHANGEJOURNAL":
                    running = "Object level"
                else:
                    running = each.name
                self.log.info("Starting validation of restore reporting of objects  with %s", running)
                self.configure_sc(scan_type=each)
                self.job = self.helper.run_backup(backup_level="Full")[0]
                self.generate_inc_data(1)
                self.job = self.helper.run_backup()[0]
                self.generate_inc_data(2)
                self.job = self.helper.run_backup()[0]
                self.restore_verify()
                if running != "Object level":
                    self.log.info("Starting validation of restore reporting of objects  with SYNCLIB and %s", running)
                    self.configure_sc(scan_type=each)
                    self.helper.enable_synclib()
                    self.job = self.helper.run_backup(backup_level="Full")[0]
                    self.generate_inc_data()
                    self.job = self.helper.run_backup()[0]
                    self.generate_inc_data(2)
                    self.job = self.helper.run_backup()[0]
                    self.restore_verify()
                self.cleanup()
                self.log.info("{0} Restore has properly reported the object.".format(running))
            self.log.info("**IBMi: VALIDATION OF OBJECT REPORTING HAS COMPLETED SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED