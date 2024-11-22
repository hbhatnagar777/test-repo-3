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
        IBMi pre-defined subclient "*CFG" backup and restore with regular scan
        Step1, configure BackupSet and pre-defined Subclients for TC
        Step2: On client, Re-create the DEVD object AUTO56653 and delete AUTO566531 if exists
        Step3: Run a full backup for the subclient *CFG and verify if it completes without failures.
        Step4: Check backup logs to confirm stage file SD* has backedup.
        Step5: On client, Create a user profile AUTO566531.
        Step6: Run an incremental job for the subclient and verify it completes without failures.
        Step7: Check backup logs to confirm stage file SD* has backedup.
        Step8: delete DEVD objects AUTO56653 and AUTO566531 from disk.
        Step9: Check logs for restore command and devd objects existence on disk after
            restore AUTO56653 and AUTO566531 and do cleanup
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Regular scan: Backup of pre-defined subclient *CFG"
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

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.RECURSIVE
            self.sc_name = "*CFG"
            self.log.info("*** STARTING RUN FOR SC: {0} with {1} "
                          "SCAN ** ".format(self.sc_name, self.scan_type.name))
            self.log.info("Step1, configure BackupSet and pre-defined Subclients for TC")
            self.helper.configure_ibmi_default_sc(backupset_name="backupset_{0}".format(self.id),
                                                  subclient_name=self.sc_name,
                                                  storage_policy=self.storage_policy,
                                                  scan_type=self.scan_type,
                                                  data_readers=1,
                                                  allow_multiple_readers=False,
                                                  delete=False)
            cfg_obj = []
            cfg_obj.append("AUTO{0}".format(self.id))
            cfg_obj.append("AUTO{0}1".format(self.id))

            self.log.info("Step2: On client, Re-create the DEVD object {0}"
                          " and delete {1} if exists".format(cfg_obj[0], cfg_obj[1]))

            for each in cfg_obj:
                self.client_machine.manage_devopt(operation="delete", object_name="{0}".format(each))
            self.client_machine.manage_devopt(operation="create", object_name="{0}".format(cfg_obj[0]))
            self.log.info("Step3: Run a full backup for the subclient *CFG "
                          " and verify if it completes without failures.")
            full_job = self.helper.run_backup_verify(self.scan_type, "Full")[0]
            self.log.info("Step4: Check backup logs to confirm stage file SD* has backedup.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'Processing JOBLOG for',
                                        jobid=full_job.job_id,
                                        expectedvalue='[SAVOBJ]:[OBJ(SC'
                                        )
            self.log.info("Verify backup logs if scan type [{0}] is used.".format(self.scan_type.name))
            self.helper.verify_from_log('cvbkp*.log',
                                        'processJobStartMessage',
                                        jobid=full_job.job_id,
                                        expectedvalue='[ScanlessBackup] - [0]'
                                        )
            self.log.info("Step5: On client, Create a DEVD object {0}.".format(cfg_obj[1]))
            self.client_machine.manage_devopt(operation="create", object_name="{0}".format(cfg_obj[1]))

            self.log.info("Step6: Run an incremental job for the subclient"
                          " and verify it completes without failures.")
            # NOTE: Incremental backup will backup all CFG objects.
            inc_job = self.helper.run_backup_verify(self.scan_type, "Incremental")[0]
            self.log.info("Step7: Check backup logs to confirm stage file SD* has backedup.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'Processing JOBLOG for',
                                        jobid=inc_job.job_id,
                                        expectedvalue='[SAVOBJ]:[OBJ(SC'
                                        )
            self.log.info("Step7: delete DEVD objects {0} and {1} from disk.".format(cfg_obj[0], cfg_obj[1]))
            cfg_obj_path = []
            for each in cfg_obj:
                self.client_machine.manage_devopt(operation="delete", object_name="{0}".format(each))
                cfg_obj_path.append("/<System Configuration>/{0}.DEVD".format(each))
            self.log.info("Step8: in.place restore of DEVD objects {0} and {1}.".format(cfg_obj[0], cfg_obj[1]))
            rst_job = self.helper.restore_in_place(cfg_obj_path)
            self.log.info("Step9: Check devd objects existence on disk after restore {0} and {1}."
                          "and do cleanup".format(cfg_obj[0], cfg_obj[1]))

            for each in cfg_obj:
                self.client_machine.object_existence(library_name='QSYS',
                                                     object_name="{0}".format(each),
                                                     obj_type='*DEVD'
                                                     )
                self.helper.verify_from_log('cvrest*.log',
                                            'CMDEXEC',
                                            jobid=rst_job.job_id,
                                            expectedvalue='Description for device {0} created'.format(each)
                                            )
                self.client_machine.manage_devopt(operation="delete", object_name="{0}".format(each))

            self.log.info("**%s SCAN RUN OF *CFG COMPLETED SUCCESSFULLY**", self.scan_type.name)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED