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

    check_defaults ()       -- check default values

    run()                   --  run function of this test case
"""

from collections import deque

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
    """Class for executing
        IBMi Validate default values for advanced options of auto-created and manually created subclients
        Step1, configure BackupSet and use a pre-defined Subclients for TC
        Step2: On client, Re-create the file QSYS/{0}
                and delete QSYS/{1} if exists
        Step3: Run a full backup for the subclient *HST log
        step4: Check backup logs to verify default options are set properly or not.
        Step5: Create a new subclient and add a library as content.
        step6: Run a full backup for the manually created subclient
        step7: Check backup logs to verify default options are set properly or not.
        Step8: cleanup libraries and objects created by TC.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "IBMi - Validate default values for advanced " \
                    "options of auto-created and manually created subclients"

        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.helper = None
        self.storage_policy = None
        #self.tcinputs = None
        self.client_machine = None
        self.slash_format = None

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.RECURSIVE
            self.subclient_name = "*HST log"
            self.log.info("*** STARTING RUN FOR SC: *QHST with %s SCAN **", self.scan_type.name)
            self.log.info("Step1, configure BackupSet and pre-defined Subclients for TC")
            self.helper.configure_ibmi_default_sc(backupset_name="backupset_{0}".format(self.id),
                                                  subclient_name=self.subclient_name,
                                                  storage_policy=self.storage_policy,
                                                  scan_type=self.scan_type,
                                                  data_readers=4,
                                                  allow_multiple_readers=True,
                                                  delete=True)
            hstobj = []
            hstobj.append("QHST{0}".format(self.id))
            hstobj.append("QHST{0}1".format(self.id))

            self.log.info("Step2: On client, Re-create the file QSYS/{0}"
                          " and delete QSYS/{1} if exists".format(hstobj[0], hstobj[1]))
            qhst_path = []
            for each in hstobj:
                self.client_machine.delete_file_object(library="QSYS", object_name="{0}".format(each))
                qhst_path.append("{0}{1}{2}.FILE".format(self.test_path, self.slash_format, each))
            self.client_machine.create_sourcepf(library="QSYS", object_name="{0}".format(hstobj[0]))
            self.log.info("Step3: Run a full backup for the subclient *HST log")
            full_job = self.helper.run_backup_verify(self.scan_type, "Full")[0]

            self.log.info("step4: Check backup logs to verify default options are set properly or not.")

            self.helper.verify_sc_defaults(job=full_job.job_id)

            self.log.info("Step5: Create a new subclient and add a library as content.")

            self.subclient_name = "Subclient_{0}".format(self.id)
            srclib = "T{0}".format(self.id)
            content = [self.client_machine.lib_to_path(srclib)]
            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=content,
                                         scan_type=self.scan_type,
                                         delete=True)

            self.client_machine.populate_lib_with_data(library_name=srclib, tc_id=self.id, count=5, prefix="A")

            self.log.info("step6: Run a full backup for the manually created subclient")
            full_job = self.helper.run_backup(backup_level="Full")[0]

            self.log.info("step7: Check backup logs to verify default options are set properly or not.")
            self.helper.verify_sc_defaults(job=full_job.job_id)

            self.log.info("Step8: cleanup.")
            self.client_machine.manage_library(operation='delete', object_name='srclib')
            self.log.info("**%s SCAN RUN OF QHST COMPLETED SUCCESSFULLY**", self.scan_type.name)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED