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

from collections import deque

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Class for executing
        IBMi pre-defined subclient "*HST log" backup and restore
        Step1, configure BackupSet and pre-defined Subclients for TC
        Step2: On client, Re-create the file QSYS/{0}
                and delete QSYS/{1} if exists
        Step3: Run a full backup for the subclient *HST log
                and verify if it completes without failures.
        step4: Check backup logs to confirm SAVOBJ was used.
        step5: Check scan logs to confirm regular scan was used.
        Step6: On client, Create a file QHST543661 with a member.
        Step7: Run an incremental job for the subclient
                and verify it completes without failures.
        Step8: Check backup logs to confirm SAVOBJ was used.
        step9: Check scan logs to confirm regular scan was used.
        Step10: OOP Restore QSYS/QHST54366 & QSYS/QHST543661
                objects  to library QHST<TESTCASE>
        Step11: Verify client restore logs if command RSTOBJ is used.
        Step12: check restored objects and cleanup created history file objects.
        Step13: cleanup restored library.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "IBMi - Optimized scan: Backup of pre-defined subclient: *HST"

        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.subclient_name = None
        self.client_machine = None
        self.destlib = None
        self.scan_type = None
        self.sc_name = None

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.OPTIMIZED
            self.sc_name = "*HST log"
            self.log.info("*** STARTING RUN FOR SC: *QHST with %s SCAN **", self.scan_type.name)
            self.log.info("Step1, configure BackupSet and pre-defined Subclients for TC")
            self.helper.configure_ibmi_default_sc(backupset_name="backupset_{0}".format(self.id),
                                                     subclient_name=self.sc_name,
                                                     storage_policy=self.storage_policy,
                                                     scan_type=self.scan_type,
                                                     data_readers=4,
                                                     allow_multiple_readers=True,
                                                     delete=False)
            self.destlib = "QHST{0}".format(self.id)
            self.client_machine.manage_library(operation='delete', object_name=self.destlib)
            destpath = self.client_machine.lib_to_path(self.destlib)
            hstobj = ["QHST{0}".format(self.id), "QHST{0}1".format(self.id)]
            self.log.info("Step2: On client, Re-create the file QSYS/{0}"
                          " and delete QSYS/{1} if exists".format(hstobj[0], hstobj[1]))
            qhst_path = []
            for each in hstobj:
                self.client_machine.delete_file_object(library="QSYS", object_name="{0}".format(each))
                qhst_path.append("{0}{1}{2}.FILE".format(self.test_path, self.slash_format, each))
            self.client_machine.create_sourcepf(library="QSYS", object_name="{0}".format(hstobj[0]))
            self.log.info("Step3: Run a full backup for the subclient *HST log"
                          " and verify if it completes without failures.")
            full_job = self.helper.run_backup_verify(self.scan_type, "Full")[0]
            self.log.info("step4: Check backup logs to confirm SAVOBJ was used.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'Processing JOBLOG for',
                                        jobid=full_job.job_id,
                                        expectedvalue="[SAVOBJ]:[OBJ({0}".format(hstobj[0])
                                        )
            self.log.info("step5: Check scan logs to confirm regular scan was used.")
            self.helper.verify_from_log('cvscan.log',
                                        'ClientScan::doScan',
                                        jobid=full_job.job_id,
                                        expectedvalue="We are running Scanless Backup"
                                        )
            self.log.info("Step6: On client, Create a file QHST{0}1 with a member.".format(self.id))
            self.client_machine.create_sourcepf(library="QSYS", object_name="{0}".format(hstobj[1]))

            self.log.info("Step7: Run an incremental job for the subclient"
                          " and verify if it completes without failures.")

            inc_job = self.helper.run_backup_verify(self.scan_type, "Incremental")[0]
            self.log.info("Step8: Check backup logs to confirm SAVOBJ was used.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'Processing JOBLOG for',
                                        jobid=inc_job.job_id,
                                        expectedvalue="[SAVCHGOBJ]:[OBJ({0}".format(hstobj[1])
                                        )
            self.log.info("step9: Check scan logs to confirm regular scan was used.")
            self.helper.verify_from_log('cvscan*.log',
                                        'ClientScan::doScan',
                                        jobid=inc_job.job_id,
                                        expectedvalue="We are running Scanless Backup."
                                        )
            self.log.info("Step10: OOP Restore QSYS/{0} & QSYS/{1} objects "
                          "to library {0}.".format(hstobj[0], hstobj[1]))
            restore_job = self.helper.restore_out_of_place(destination_path=destpath,
                                                           paths=qhst_path)
            self.log.info("Step11: Verify client restore logs if command RSTOBJ is used.")
            self.helper.verify_from_log('cvrest*.log',
                                        'QaneRsta',
                                        jobid=restore_job.job_id,
                                        expectedvalue="QHST{0}".format(self.id)
                                        )
            self.helper.verify_from_log('cvrest*.log',
                                        'QaneRsta',
                                        jobid=restore_job.job_id,
                                        expectedvalue="OBJ(QHST{0}1".format(self.id)
                                        )
            self.log.info("Step12: check restored objects and cleanup created history file objects.")
            for each in hstobj:
                self.client_machine.object_existence(library_name='QSYS',
                                                     object_name='{0}'.format(each),
                                                     obj_type='*FILE')
                self.client_machine.delete_file_object(library='QSYS', object_name="{0}".format(each))
            self.log.info("Step13: cleanup restored library.")
            self.client_machine.manage_library(operation='delete', object_name='QHST{0}'.format(self.id))
            self.log.info("**%s SCAN RUN OF QHST COMPLETED SUCCESSFULLY**", self.scan_type.name)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
