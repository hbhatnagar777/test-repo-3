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

        update_sc_for_inc()     --  Update SC with new value for additional save while active options

        verify_logs()           --  Verify backup logs on client

        restore_verify()        --  Initiates OOP restore for content and verify the restored data..

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
        IBMi - Verify additional save while active wait options
        for non-VTL, test with Optimized scan and regular scan and object level do as following.
            Configure SC with some user libraries and set the SAVACTWAIT(* *NOCMTBDY *NOMAX).
            Run full backup of the Subclient.
            Verify backup logs on client if correct values are used for backup
            Generate incremental data and modify SAVACTWAIT additional inputs to SAVACTWAIT(* *NOMAX *NOMAX)
            run Incremental backup of the Subclient.
            Verify backup logs on client if correct values are used for backup
            Perform OOP restore and verify the restored data.
            Repeat the test with SYNCLIB for Optimized scan and regular scan library level backup
            Run Cleanup on client machine.
        for VTL , test with regular scan do as following.
            Configure SC with some user libraries and set the SAVACTWAIT(* *NOCMTBDY *NOMAX).
            Run full backup of the Subclient.
            Verify backup logs on client if correct values are used for backup
            Generate incremental data and modify SAVACTWAIT additional inputs to SAVACTWAIT(* *NOMAX *NOMAX)
            Run Incremental backup of the Subclient.
            Verify backup logs on client if correct values are used for backup
            Perform OOP restore and verify the restored data.
            Repeat the test with SYNCLIB backup enabled.
            Run Cleanup on client machine.
        for Parallel VTL, test with regular scan do as following.
            Configure SC with some user libraries and set the SAVACTWAIT(* *NOCMTBDY *NOMAX).
            Run full backup of the Subclient.
            Verify backup logs on client if correct values are used for backup
            Generate incremental data and modify SAVACTWAIT additional inputs to SAVACTWAIT(* *NOMAX *NOMAX)
            Run Incremental backup of the Subclient.
            Verify backup logs on client if correct values are used for backup
            Perform OOP restore and verify the restored data.
            Repeat the test with SYNCLIB backup enabled.
            Run Cleanup on client machine.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Verify additional save while active wait options"
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
            self.client_machine.populate_lib_with_data(library_name=each, tc_id=self.id, count=2)
            self.src_path.append(self.client_machine.lib_to_path(each))
        self.helper.create_subclient(name=self.subclient_name,
                                     storage_policy=self.storage_policy,
                                     content=self.src_path,
                                     scan_type=scan_type,
                                     data_readers=data_readers,
                                     allow_multiple_readers=allow_multiple_readers,
                                     delete=True)
        sc_options = {'pendingRecordChange': self.savact1,
                      'otherPendingChange': self.savact2,
                      'object_level': set_object_level
                      }
        self.helper.set_ibmi_sc_options(**sc_options)
        self.helper.set_ibmi_sc_options(**{'savactwait': 632})
        if self.IBMiMode == "VTLParallel":
            self.log.info("Enable multiple drives option for VTL Backup")
            self.helper.set_vtl_multiple_drives()

    def generate_inc_data(self):
        """
            Generate Incremental data on client machine.
        """
        self.log.info("Generating incremental data on client machine")
        for each in self.usr_lib:
            self.client_machine.create_sourcepf(library=each, object_name='VERIFY')
            self.client_machine.create_sourcepf(library=each, object_name='VERIFY1')

    def update_sc_for_inc(self):
        """"
            Update SC with new value for additional save while active options
        """
        self.savact1 = "*NOMAX"
        sc_options = {'pendingRecordChange': self.savact1}
        self.helper.set_ibmi_sc_options(**sc_options)
        self.helper.set_ibmi_sc_options(**{'savactwait': 632})

    def verify_logs(self):
        """
            Verify backup logs on client
        """
        self.log.info("Verifying backup logs on IBMi client machine for %s", self.IBMiMode)
        if self.IBMiMode == "NON-VTL":
            self.log.info("Verify backup client logs and check if additional save while active values are "
                          "used properly or not")
            self.helper.verify_from_log('cvbkp*.log',
                                        'Processing JOBLOG for',
                                        jobid=self.job.job_id,
                                        expectedvalue="{0} {1}".format(self.savact1, self.savact2))
        elif self.IBMiMode == "VTL" or self.IBMiMode == "VTLParallel":
            self.log.info("VVerify VTL backup client logs and check if additional save while active values are "
                          "used properly or not")
            self.helper.verify_from_log(logfile='cvbkpvtl*.log',
                                        regex='runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue="{0} {1}".format(self.savact1, self.savact2))

    def restore_verify(self):
        """
            Initiates OOP restore for content and verify the restored data..
        """
        self.log.info("Run OOP restore of both libraries and verify.")
        for each in self.usr_lib:
            self.log.info("run OOP restore of library [{0}] to library [{1}] and verify.".format(each, self.destlib))
            self.job = self.helper.restore_out_of_place(
                destination_path=self.client_machine.lib_to_path("{0}".format(each)),
                paths=[self.client_machine.lib_to_path("{0}".format(each))],
                restore_ACL=False,
                preserve_level=0)
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
            self.helper.create_backupset(name=backupset_name, delete=True)
            self.scan_type = [ScanType.RECURSIVE]
            if self.IBMiMode == "NON-VTL":
                self.scan_type.append(ScanType.OPTIMIZED)
                # Change journal scan type is used for Object level backup
                self.scan_type.append(ScanType.CHANGEJOURNAL)
            self.log.info("*** STARTING VALIDATION OF SC OPTION SAVACTWAIT ADDITIONAL VALUES WITH {0}***".
                          format(self.IBMiMode))
            for each in self.scan_type:
                if each.name == "CHANGEJOURNAL":
                    running = "Object level"
                else:
                    running = each.name
                self.log.info("Starting validation of additional SWA inputs with %s", running)
                self.savact1 = "*NOCMTBDY"
                self.savact2 = "*NOMAX"
                self.configure_sc(scan_type=each)
                self.job = self.helper.run_backup(backup_level="Full")[0]
                self.verify_logs()
                self.generate_inc_data()
                self.update_sc_for_inc()
                self.helper.set_ibmi_sc_options(**{'savact': '*SYSDFN'})
                self.job = self.helper.run_backup()[0]
                self.verify_logs()
                self.restore_verify()
                if running != "Object level":
                    self.log.info("Starting validation of additional SWA inputs with SYNCLIB and %s", running)
                    self.savact1 = "*NOCMTBDY"
                    self.configure_sc(scan_type=each)
                    self.helper.enable_synclib()
                    self.job = self.helper.run_backup(backup_level="Full")[0]
                    self.verify_logs()
                    self.generate_inc_data()
                    self.update_sc_for_inc()
                    self.job = self.helper.run_backup()[0]
                    self.verify_logs()
                    self.restore_verify()
                self.cleanup()
                self.log.info("{0} backup has properly used additional save while active options for backup.".
                              format(running))
            self.log.info("**ADDITIONAL SAVACTWAIT VALUES OF SC VALIDATION COMPLETED SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
