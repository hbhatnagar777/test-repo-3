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
        IBMi - Verify all IBMi advanced subclient options for  auto-created subclient with regular scan backup.
        Step1, configure BackupSet and Subclients for TC with first set of additional options
        Step2: On client, create a library QAUT54368 with objects
        Step3: Run a full backup for the subclient *IBM and verify if it completes without failures.
        step4: verify the full backup logs and validate all advanced options.
        Step5: On client, Create another library QAUT543681 with objects.
        Step6: Run an incremental job for the subclient and verify if it completes without failures.
        Step7: verify the Inc backup logs and validate all advanced options.
        Step8: Run an differential backup for the subclient and verify if it completes without failures.
        Step9: verify the diff backup logs and validate all advanced options.
        Step10: Clenaup the libraries on client disk
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Verify all IBMi advanced subclient options for " \
                    "auto-created subclient with regular scan backup."
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
            self.scan_type = ScanType.RECURSIVE
            self.subclient_name = "*IBM"
            self.log.info("*** STARTING RUN FOR SC: *IBM with %s SCAN **", self.scan_type.name)
            self.log.info("Step1, configure BackupSet and Subclients for TC")
            self.helper.configure_ibmi_default_sc(backupset_name="backupset_{0}".format(self.id),
                                                     subclient_name=self.subclient_name,
                                                     storage_policy=self.storage_policy,
                                                     scan_type=self.scan_type,
                                                     data_readers=8,
                                                     allow_multiple_readers=True,
                                                     delete=True)
            self.log.info("Update the subclient advanced options")
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
                          'object_level': True
                          }
            self.helper.set_ibmi_sc_options(**sc_options)
            ibm_lib = ["QAUT{0}".format(self.id), "QAUT{0}1".format(self.id)]

            self.log.info("Step2: On client, create a library {0} with objects".format(ibm_lib[0]))
            self.client_machine.populate_lib_with_data(library_name=ibm_lib[0], tc_id=self.id, count=2)

            self.log.info("Step3: Run a full backup for the subclient *IBM "
                          "and verify if it completes without failures.")
            job = self.helper.run_backup(backup_level="Full")[0]
            self.log.info("step4: verify the full backup logs and validate all advanced options.")
            self.helper.verify_ibmi_sc_options(jobid=job.job_id, **sc_options)

            self.log.info("Step5: On client, Create another library {0} with objects.".format(ibm_lib[1]))
            self.client_machine.populate_lib_with_data(library_name=ibm_lib[1], tc_id=self.id, count=2)

            self.log.info("Update the SC with new values for additional options.")
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
                           'object_level': True
                           }
            self.helper.set_ibmi_sc_options(**sc_options1)

            self.log.info("Step6: Run an incremental job for the subclient"
                          " and verify if it completes without failures.")

            job = self.helper.run_backup(backup_level="Incremental")[0]
            self.log.info("Step7: verify the Inc backup logs and validate all advanced options.")
            self.helper.verify_ibmi_sc_options(jobid=job.job_id, **sc_options1)

            self.log.info("Step8: Run a Differential backup for the subclient.")

            job = self.helper.run_backup(backup_level="Differential")[0]

            self.log.info("Step9: verify the Inc backup logs and validate all advanced options.")
            self.helper.verify_ibmi_sc_options(jobid=job.job_id, **sc_options1)

            self.log.info("Step10: Clenaup the libraries on client disk")
            for each in ibm_lib:
                self.client_machine.manage_library(operation='delete', object_name=each)

            self.log.info("**%s SCAN RUN FOR VERIFYING ADDITIONAL OPTIONS OF *IBM COMPLETED SUCCESSFULLY**",
                          self.scan_type.name)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
