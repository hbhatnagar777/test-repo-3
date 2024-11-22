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
54368
from collections import deque

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.FSUtils.fshelper import FSHelper

class TestCase(CVTestCase):
    """Class for executing
        IBMi pre-defined subclient "*IBM" backup and restore with optimized scan
        Step1, configure BackupSet and Subclients for TC
        Step2: On client, create a library QAUT54368 with objects
        Step3: Run a full backup for the subclient *IBM and verify if it completes without failures.
        Step4: Check Full backup logs to backup command
        Step5: On client, Create another library QAUT543681 with objects.
        Step6: On client, Create file object in library QAUT54368.
        Step7: Run an incremental job for the subclient and verify if it completes without failures.
        Step8: Check Inc backup logs to confirm backup commands.
        Step9: run OOP restore of both libraries and verify.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Optimized scan: Backup of pre-defined subclient: *IBM"
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.subclient_name = None
        self.client_machine = None
        self.destlib = None
        self.scan_type=None

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.sc_name = "*IBM"
            self.scan_type = ScanType.OPTIMIZED
            self.log.info("*** STARTING RUN FOR SC: *IBM with %s SCAN **", self.scan_type.name)
            self.log.info("Step1, configure BackupSet and Subclients for TC")
            self.helper.configure_ibmi_default_sc(backupset_name="backupset_{0}".format(self.id),
                                                     subclient_name=self.sc_name,
                                                     storage_policy=self.storage_policy,
                                                     scan_type=self.scan_type,
                                                     data_readers=8,
                                                     allow_multiple_readers=True,
                                                     delete=False)
            ibm_lib = []
            ibm_lib.append("QAUT{0}".format(self.id))
            ibm_lib.append("QAUT{0}1".format(self.id))
            self.destlib = "QAUTRST"

            for each in ibm_lib:
                self.client_machine.manage_library(operation='delete', object_name=each)

            self.log.info("Step2: On client, create a library {0} with objects".format(ibm_lib[0]))
            self.client_machine.populate_lib_with_data(library_name=ibm_lib[0], tc_id=self.id, count=2)

            self.log.info("Step3: Run a full backup for the subclient *IBM "
                          "and verify if it completes without failures.")
            full_job = self.helper.run_backup_verify(self.scan_type, "Full")[0]
            self.log.info("Step4: Check Full backup logs to backup command.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'Processing JOBLOG for',
                                        jobid=full_job.job_id,
                                        expectedvalue='[SAVLIB]:[LIB({0}'.format(ibm_lib[0])
                                        )
            self.helper.verify_from_log('cvbkp*.log',
                                        'processJobStartMessage',
                                        jobid=full_job.job_id,
                                        expectedvalue='[Backup_IBM_Enabled] - [1]'
                                        )
            self.log.info("Check scan logs to confirm optimized scan is used.")
            self.helper.verify_from_log('cvscan*.log',
                                        'ClientScan::doScan',
                                        jobid=full_job.job_id,
                                        expectedvalue="We are running Scanless Backup"
                                        )
            self.log.info("Step5: On client, Create another library {0} with objects.".format(ibm_lib[1]))
            self.client_machine.populate_lib_with_data(library_name=ibm_lib[1], tc_id=self.id, count=2)

            self.log.info("Step6: On client, Create file object in library {0}.".format(ibm_lib[0]))
            self.client_machine.create_sourcepf(library=ibm_lib[0], object_name='INC{0}'.format(self.id))

            self.log.info("Step7: Run an incremental job for the subclient"
                          " and verify if it completes without failures.")
            inc_job = self.helper.run_backup_verify(self.scan_type, "Incremental")[0]
            self.log.info("Step8: Check Inc backup logs to confirm backup commands.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'Processing JOBLOG for',
                                        jobid=inc_job.job_id,
                                        expectedvalue='[SAVCHGOBJ]:[OBJ(*ALL) LIB({0})'.format(ibm_lib[0])
                                        )
            self.log.info("Verify if New library is backedup as full using SAVLIB command.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'Processing JOBLOG for',
                                        jobid=inc_job.job_id,
                                        expectedvalue='[SAVLIB]:[LIB({0}'.format(ibm_lib[1])
                                        )
            self.log.info("Step9: run OOP restore of both libraries and verify.")
            for each in ibm_lib:
                self.log.info("run OOP restore of library [{0}] to "
                              "library [{1}] and verify.".format(each, self.destlib))
                self.helper.run_restore_verify(slash_format=self.slash_format,
                                                         data_path=self.client_machine.lib_to_path("{0}".format(each)),
                                                         tmp_path=self.client_machine.lib_to_path(self.destlib),
                                                         data_path_leaf=""
                                                         )
                self.client_machine.manage_library(operation='delete', object_name=self.destlib)
                self.client_machine.manage_library(operation='delete', object_name=each)

            self.log.info("**%s SCAN RUN OF *IBM COMPLETED SUCCESSFULLY**", self.scan_type.name)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED