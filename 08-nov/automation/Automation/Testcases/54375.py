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
        IBMi pre-defined subclient "*LINK" backup and restore with optimized scan
        Step1, configure BackupSet and Subclients for TC
        Step2: On client, create a directory /AUTO54375 with objects
        Step3: Run a full backup for the subclient *LINK and verify if it completes without failures.
        Step4: Check Full backup logs to backup command
        Step5: On client, Create another directory /AUTO543751 with objects.
        Step6: On client, Create file object in directory /AUT54375.
        Step7: Run an incremental job for the subclient and verify if it completes without failures.
        Step8: Check Inc backup logs to confirm backup commands.
        Step9: run OOP restore of both libraries and verify.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - Optimized scan: Backup of pre-defined subclient *LINK"
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.subclient_name = None
        self.client_machine = None
        self.destdir = None

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.OPTIMIZED
            self.subclient_name = "*LINK"
            filters = []
            filters.append("/QSR")
            filters.append("/QIBM")
            filters.append("/tmp")
            filters.append("/QFileSvr.400")
            filters.append("/QOpenSys")
            filters.append("/var/commvault")

            self.log.info("*** STARTING RUN FOR SC: *LINK with %s SCAN **", self.scan_type.name)
            self.log.info("Step1, configure BackupSet and Subclients for TC")
            self.helper.configure_ibmi_default_sc(backupset_name="backupset_{0}".format(self.id),
                                                  subclient_name=self.subclient_name,
                                                  storage_policy=self.storage_policy,
                                                  scan_type=self.scan_type,
                                                  filter_content=filters,
                                                  data_readers=8,
                                                  allow_multiple_readers=True,
                                                  delete=False)
            self.log.info("adding filters to *LINK subclient to avoid failures "
                          "from system directories {0}".format(filters))
            dirs = []
            dirs.append("/AUT{0}".format(self.id))
            dirs.append("/AUT{0}1".format(self.id))
            self.destdir = "/AUTRST"
            for each in dirs:
                self.client_machine.remove_directory(directory_name=each)
            self.client_machine.remove_directory(directory_name=self.destdir)
            self.log.info("Step2: On client, create a directory {0} with objects".format(dirs[0]))
            self.client_machine.populate_ifs_data(directory_name=dirs[0],
                                                  tc_id=self.id,
                                                  count=10,
                                                  prefix="F",
                                                  delete=True)
            self.log.info("Step3: Run a full backup for the subclient *LINK "
                          "and verify if it completes without failures.")
            full_job = self.helper.run_backup(backup_level="Full")[0]
            # full_job = self.helper.run_backup_verify(self.scan_type, "Full")[0]
            self.log.info("Step4: Verify full backup logs for proper inputs are .")
            self.helper.verify_from_log('cvbkp*.log',
                                        'processJobStartMessage',
                                        jobid=full_job.job_id,
                                        expectedvalue='[ScanlessBackup] - [1]'
                                        )
            self.helper.verify_from_log('cvbkp*.log',
                                        'processJobStartMessage',
                                        jobid=full_job.job_id,
                                        expectedvalue='[Backup_Link_Enabled] - [1]'
                                        )
            self.log.info("Step5: On client, Create another directory {0} with objects.".format(dirs[1]))
            self.client_machine.populate_ifs_data(directory_name=dirs[1],
                                                  tc_id=self.id,
                                                  count=10,
                                                  prefix="I",
                                                  delete=True)
            self.log.info("Step6: On client, Create few text files under directory {0}.".format(dirs[0]))
            self.client_machine.populate_ifs_data(directory_name=dirs[0],
                                                  tc_id=self.id,
                                                  count=5,
                                                  prefix="N",
                                                  delete=False)
            self.log.info("Step7: Run an incremental job for the subclient"
                          " and verify if it completes without failures.")
            inc_job = self.helper.run_backup(backup_level="Incremental")[0]
            self.log.info("Step8: Check Inc backup logs to confirm backup commands.")
            self.helper.verify_from_log('cvbkp*.log',
                                        'processJobStartMessage',
                                        jobid=inc_job.job_id,
                                        expectedvalue='[Backup_Link_Enabled] - [1]'
                                        )
            self.log.info("Step9: run OOP restore of both directories and verify.")
            for each in dirs:
                self.log.info("run OOP restore of directory [{0}] to directory [{1}] and verify.".format(each, self.destdir))
                self.helper.restore_out_of_place(self.destdir,
                                                 paths=[each],
                                                 restore_ACL=False,
                                                 preserve_level=0)
                self.helper.compare_ibmi_data(source_path="{0}/*".format(each),
                                              destination_path="{0}/*".format(self.destdir))
                self.client_machine.remove_directory(each)
                self.client_machine.remove_directory(self.destdir)

            self.log.info("**%s SCAN RUN OF *IBM COMPLETED SUCCESSFULLY**", self.scan_type.name)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED