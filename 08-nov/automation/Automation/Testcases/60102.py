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
        IBMi - VTL backup and restore of pre-defined subclient *SECDTA and validate subclient default values
        Step1, configure BackupSet and pre-defined Subclients for TC
        Step2: On client, Re-create the user profile for full
        Step3: Run a full backup for the subclient *SECDTA
        Step4: Check backup logs to confirm stage file SD* has backedup.
        Step5: On client, Create a user profile for incremental backup
        Step6: Run an incremental job for the subclient
        Step7: Check backup logs to confirm stage file SD* has backedup.
        Step8: delete user profiles that are created on disk.
        Step9: Check user profiles existence on disk after restore
        Step10: verify user profiles existence on disk after restore and perform cleanup.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - VTL backup and restore of pre-defined subclient *SECDTA and validate subclient " \
                    "default values"
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.subclient_name = None
        self.client_machine = None
        self.scan_type = None
        self.sc_name = None
        self.job = None

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.RECURSIVE
            self.sc_name = "*SECDTA"
            self.log.info("*** STARTING RUN FOR SC: {0} with {1} "
                          "SCAN ** ".format(self.sc_name, self.scan_type.name))
            self.log.info("Step1, configure BackupSet and pre-defined Subclients for TC with VTL SP")
            self.helper.configure_ibmi_default_sc(backupset_name="backupset_{0}".format(self.id),
                                                  subclient_name=self.sc_name,
                                                  storage_policy=self.storage_policy,
                                                  scan_type=self.scan_type,
                                                  data_readers=1,
                                                  allow_multiple_readers=False,
                                                  delete=False)
            sec_dta = ["AUTV{0}".format(self.id), "AUTV{0}1".format(self.id), "AUTV{0}2".format(self.id)]
            self.log.info("Step2: On client, Re-create the user profile AUTO{0}"
                          " and delete AUTO{0}1 if exists".format(self.id))
            for each in sec_dta:
                self.client_machine.manage_usrprf(operation="delete", object_name=each)
            self.client_machine.manage_usrprf(operation="create", object_name=sec_dta[0])
            self.log.info("Step3: Run a full backup for the subclient {0}"
                          " and verify if it completes without failures.".format(self.sc_name))
            self.job = self.helper.run_backup_verify(self.scan_type, "Full")[0]

            self.log.info("Step4: Check backup logs to confirm stage file SD* has backedup.")
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue='SAVSECDTA')
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue='VOL(')
            self.log.info("Step5: On client, Create a user profile AUTO{0}1.".format(self.id))
            self.client_machine.manage_usrprf(operation="create", object_name=sec_dta[1])
            self.log.info("Step6: Run an incremental job for the subclient"
                          "and verify it completes without failures.")
            # NOTE: Incremental backup will backup all SECDTA.

            self.job = self.helper.run_backup_verify(self.scan_type, "Incremental")[0]
            self.log.info("Step7: Check backup logs to confirm Security data has backedup.")
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue='SAVSECDTA')
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue='VOL(')

            self.log.info("Step8: On client, Create a user profile AUTO{0}1.".format(self.id))
            self.client_machine.manage_usrprf(operation="create", object_name=sec_dta[2])
            self.log.info("Step9: Run an differential job for the subclient"
                          "and verify it completes without failures.")
            # NOTE: Incremental backup will backup all SECDTA.

            self.job = self.helper.run_backup_verify(self.scan_type, "Differential")[0]
            self.log.info("Step10: Check backup logs to confirm Security data has backedup.")
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue='SAVSECDTA')
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue='VOL(')
            self.log.info("Step11: Delete user profiles {0} {1} and {2} from disk.".format(sec_dta[0],
                                                                                           sec_dta[1],
                                                                                           sec_dta[2]))
            sec_dta_path = []
            for each in sec_dta:
                sec_dta_path.append("/<System Security>/{0}.USRPRF".format(each))
                self.client_machine.manage_usrprf(operation="delete", object_name=each)
            self.job = self.helper.restore_in_place(sec_dta_path)

            self.log.info("Step12: Verify restore logs if proper restore command is used")
            self.helper.verify_from_log('cvrest*.log',
                                        'Submitted job with command',
                                        jobid=self.job.job_id,
                                        expectedvalue='(RSTUSRPRF')
            self.helper.verify_from_log('cvrest*.log',
                                        'Submitted job with command',
                                        jobid=self.job.job_id,
                                        expectedvalue=sec_dta[0])
            self.helper.verify_from_log('cvrest*.log',
                                        'Submitted job with command',
                                        jobid=self.job.job_id,
                                        expectedvalue=sec_dta[1])
            self.helper.verify_from_log('cvrest*.log',
                                        'Submitted job with command',
                                        jobid=self.job.job_id,
                                        expectedvalue=sec_dta[2])
            self.helper.verify_from_log('cvrest*.log',
                                        'Submitted job with command',
                                        jobid=self.job.job_id,
                                        expectedvalue='VOL(')
            self.log.info("Step13: verify user profiles existence on disk after restore"
                          " and perform cleanup.")
            for each in sec_dta:
                self.client_machine.object_existence(library_name='QSYS',
                                                     object_name=each,
                                                     obj_type='*USRPRF'
                                                     )
                self.client_machine.manage_usrprf(operation="delete", object_name=each)

            self.log.info("**VTL BACKUP AND RESTORE OF *SECDTA COMPLETED SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
