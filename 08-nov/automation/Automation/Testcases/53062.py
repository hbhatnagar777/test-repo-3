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
from datetime import datetime


class TestCase(CVTestCase):
    """Class for executing
        IBMi - Verify all IBMi advanced subclient options with optimized scan backup
        Step1, configure BackupSet and Subclient with one set of advanced options for TC
        Step2: On client, create a library TC58688.
        Step3: Run a full backup for the subclient.
        Step4: verify the full backup logs and validate all advanced options.
        Step5: Run a Inc backup for the subclient.
        Step6: verify the Inc backup logs and validate all advanced options.
        Step7: Run a Differential backup for the subclient.
        Step8: verify the Differential backup logs and validate all advanced options.
        Step9: Update the SC with new values for additional options.
        Step10: Run a full backup for the subclient.
        Step11: verify the full backup logs and validate all advanced options.
        Step12: Run a Inc backup for the subclient.
        Step13: verify the Inc backup logs and validate all advanced options.
        Step14: Run a Differential backup for the subclient.
        Step15: verify the Differential backup logs and validate all advanced options.
        Step16: Cleanup the libraries from client disk.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Verify all IBMi advanced subclient options with optimized scan backup"
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

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.OPTIMIZED

            self.log.info("*** STARTING RUN FOR SC ADDITIONAL OPTIONS VALIDATION ***")
            self.log.info("Step1, configure BackupSet and Subclient with optimized scan + advanced options for TC")
            backupset_name = "backupset_{0}".format(self.id)
            self.helper.create_backupset(name=backupset_name, delete=False)
            self.subclient_name = "Subclient_{0}".format(self.id)
            srclib = "TC{0}".format(self.id)
            content = [self.client_machine.lib_to_path(srclib)]

            self.helper.create_subclient(name=self.subclient_name,
                                         storage_policy=self.storage_policy,
                                         content=content,
                                         scan_type=self.scan_type,
                                         delete=True)
            sc_options = {'savact': '*LIB',
                          'savactwait': 10,
                          'dtacpr': '*NO',
                          'dedupe_on_ibmi': False,
                          'updhst': False,
                          'accpth': '*SYSVAL',
                          'tgtrls': self.client_machine.get_ibmi_version(),
                          'pvtaut': False,
                          'qdta': False,
                          'splfdta': False,
                          'savfdta': False,
                          'object_level': False
                          }
            self.helper.set_ibmi_sc_options(**sc_options)
            self.log.info("Step2: On client, create a library TC58688.")
            self.client_machine.populate_lib_with_data(library_name=srclib, tc_id=self.id, count=5, prefix="A")
            self.log.info("Step3: Run a full backup for the subclient.")
            job = self.helper.run_backup(backup_level="Full")[0]
            self.log.info("Step4: verify the full backup logs and validate all advanced options.")
            self.helper.verify_ibmi_sc_options(jobid=job.job_id,
                                               **sc_options)
            self.log.info("Step5: Run a Incremental backup for the subclient.")
            self.client_machine.create_sourcepf(library=srclib, object_name='INC1')
            job = self.helper.run_backup(backup_level="Incremental")[0]
            self.log.info("Step6: verify the Inc backup logs and validate all advanced options.")
            self.helper.verify_ibmi_sc_options(jobid=job.job_id,
                                               **sc_options)
            self.log.info("Step7: Run a Differential backup for the subclient.")
            self.client_machine.create_sourcepf(library=srclib, object_name='DIFF1')
            job = self.helper.run_backup(backup_level="Differential")[0]
            self.log.info("Step8: verify the Differential backup logs and validate all advanced options.")
            self.helper.verify_ibmi_sc_options(jobid=job.job_id,
                                               **sc_options)

            self.log.info("Step9: Update the SC with new values for additional options.")
            sc_options1 = {'savact': '*SYSDFN',
                           'savactwait': 210,
                           'dtacpr': '*LOW',
                           'dedupe_on_ibmi': True,
                           'updhst': True,
                           'accpth': '*YES',
                           'tgtrls': self.client_machine.get_ibmi_version("*SUPPORTED"),
                           'pvtaut': True,
                           'qdta': True,
                           'splfdta': True,
                           'savfdta': True,
                           'object_level': False
                           }
            self.helper.set_ibmi_sc_options(**sc_options1)
            self.log.info("Step10: Run a full backup for the subclient.")
            job = self.helper.run_backup(backup_level="Full")[0]
            self.log.info("Step11: verify the full backup logs and validate all advanced options.")
            self.helper.verify_ibmi_sc_options(jobid=job.job_id,
                                               **sc_options1)
            self.log.info("Step12: Run a Inc backup for the subclient.")
            self.client_machine.create_sourcepf(library=srclib, object_name='INC2')
            job = self.helper.run_backup(backup_level="Incremental")[0]
            self.log.info("Step13: verify the Inc backup logs and validate all advanced options.")
            self.helper.verify_ibmi_sc_options(jobid=job.job_id,
                                               **sc_options1)
            self.log.info("Step14: Run a Differential backup for the subclient.")
            self.client_machine.create_sourcepf(library=srclib, object_name='DIFF2')
            job = self.helper.run_backup(backup_level="Differential")[0]
            self.log.info("Step15: verify the Differential backup logs and validate all advanced options.")
            self.helper.verify_ibmi_sc_options(jobid=job.job_id,
                                               **sc_options1)
            self.log.info("Step16: Cleanup libraries from client disk")
            self.client_machine.manage_library(operation='delete', object_name=srclib)

            self.log.info("**%s SCAN RUN VALIDATION OF SC OPTIONS COMPLETED SUCCESSFULLY**", self.scan_type.name)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
