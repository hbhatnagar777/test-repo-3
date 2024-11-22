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

        verify_pre_post()       --  Verify pre post command execution on client logs

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
        IBMi - Validation of Pre/Post subclient option scan and backup for all IBMi features
        for non-VTL, test with Optimized scan and regular scan and object level do as following.
            Configure SC with some user libraries.
            Run full backup of the Subclient.
            Verify pre-post command exustion in client logs
            Generate incremental data with objects picked in full backup changed
            run Incremental backup of the Subclient.
            Verify pre-post command exustion in client logs
            Repeat the test with SYNCLIB for Optimized scan and regular scan library level backup
            Run Cleanup on client machine.
        for VTL , test with regular scan do as following.
            Configure SC with some user libraries.
            Run full backup of the Subclient.
            Verify pre-post command exustion in client logs
            Generate incremental data with objects picked in full backup changed
            run Incremental backup of the Subclient.
            Verify pre-post command exustion in client logs
            Repeat the test with SYNCLIB backup enabled.
            Run Cleanup on client machine.
        for Parallel VTL, test with regular scan do as following.
            Configure SC with some user libraries.
            Run full backup of the Subclient.
            Verify pre-post command exustion in client logs
            Generate incremental data with objects picked in full backup changed
            run Incremental backup of the Subclient.
            Verify pre-post command exustion in client logs
            Repeat the test with SYNCLIB backup enabled.
            Run Cleanup on client machine.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Validation of Pre/Post subclient option scan and backup for all IBMi features"
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
        self.helper.create_subclient(name=self.subclient_name,
                                     storage_policy=self.storage_policy,
                                     content=self.src_path,
                                     scan_type=scan_type,
                                     data_readers=data_readers,
                                     allow_multiple_readers=allow_multiple_readers,
                                     delete=True)

        self.helper.set_object_level_backup(set_object_level)
        self.helper.update_pre_post(pre_scan_command="CVLIB/PPOK PRE SCAN",
                                    post_scan_command="CVLIB/PPOK POST SCAN1",
                                    pre_backup_command="CVLIB/PPOK PRE1 BKP",
                                    post_backup_command="CVLIB/PPOK POST1 BKP1")
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

        for each in self.usr_lib:
            self.log.info("Modifying {0} file members starting with A under library {1}".format(run_count, each))
            self.client_machine.create_sourcepf(library=each, object_name='C{0}'.format(run_count))

    def verify_pre_post(self):
        """
            Verify pre post command execution on client logs
        """
        self.log.info("Verify pre post command execution on client logs")
        self.helper.verify_from_log(logfile='cvd*.log',
                                    regex='IBMClientServices',
                                    jobid=self.job.job_id,
                                    expectedvalue="PRE")
        self.helper.verify_from_log(logfile='cvd*.log',
                                    regex='IBMClientServices',
                                    jobid=self.job.job_id,
                                    expectedvalue="SCAN")
        self.helper.verify_from_log(logfile='cvd*.log',
                                    regex='IBMClientServices',
                                    jobid=self.job.job_id,
                                    expectedvalue="PRE1")
        self.helper.verify_from_log(logfile='cvd*.log',
                                    regex='IBMClientServices',
                                    jobid=self.job.job_id,
                                    expectedvalue="SCAN1")
        self.helper.verify_from_log(logfile='cvd*.log',
                                    regex='IBMClientServices',
                                    jobid=self.job.job_id,
                                    expectedvalue="POST")
        self.helper.verify_from_log(logfile='cvd*.log',
                                    regex='IBMClientServices',
                                    jobid=self.job.job_id,
                                    expectedvalue="POST1")
        self.helper.verify_from_log(logfile='cvd*.log',
                                    regex='IBMClientServices',
                                    jobid=self.job.job_id,
                                    expectedvalue="BKP")
        self.helper.verify_from_log(logfile='cvd*.log',
                                    regex='IBMClientServices',
                                    jobid=self.job.job_id,
                                    expectedvalue="BKP1")

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
            self.usr_lib = ["AUT{0}".format(self.id)]
            self.helper.create_backupset(name=backupset_name)
            self.scan_type = [ScanType.RECURSIVE]
            if self.IBMiMode == "NON-VTL":
                self.scan_type.append(ScanType.OPTIMIZED)
                # Change journal scan type is used for Object level backup
                self.scan_type.append(ScanType.CHANGEJOURNAL)
            self.log.info("*** STARTING VALIDATION OF PRE-POST OPTIONS WITH {0}***".format(self.IBMiMode))
            for each in self.scan_type:
                if each.name == "CHANGEJOURNAL":
                    running = "Object level"
                else:
                    running = each.name
                self.log.info("***********************************************************")
                self.log.info("Starting validation of pre/post command execution with %s", running)
                self.log.info("***********************************************************")
                self.configure_sc(scan_type=each)
                self.job = self.helper.run_backup(backup_level="Full")[0]
                self.verify_pre_post()
                self.generate_inc_data(1)
                self.job = self.helper.run_backup()[0]
                self.verify_pre_post()
                if running != "Object level":
                    self.log.info("Starting validation of Pre-Post options with SYNCLIB and %s", running)
                    self.configure_sc(scan_type=each)
                    self.helper.enable_synclib()
                    self.job = self.helper.run_backup(backup_level="Full")[0]
                    self.verify_pre_post()
                    self.generate_inc_data()
                    self.job = self.helper.run_backup()[0]
                    self.verify_pre_post()
                self.cleanup()
                self.log.info("pre-post command execution is verified with {0}.".format(running))
            self.log.info("**IBMi: VALIDATION OF PRE/POST COMMAND EXECUTION HAS COMPLETED SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
