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

    configure_sc()          --  Configure predefined and another subclient with content

    verify_logs()           --  Verify client logs for VTL operation

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
        IBMi - VTL backup of pre-defined subclient *LINK and validate subclient default values
        Step1, configure BackupSet and Subclients for VTL TC
        Step2: On client, create a directory /AUTO60103 with objects
        Step3: Run a full backup for the subclient *LINK and verify if it completes without failures.
        Step4: Check Full backup logs to backup command
        Step5: On client, Create another directory /AUTO601031 with objects.
        Step6: On client, Create file object in directory /AUT550103.
        Step7: Run an incremental self.job for the subclient and verify if it completes without failures.
        Step8: Check Inc backup logs to confirm backup commands.
        Step9: run OOP restore of both libraries and verify.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi - VTL backup of pre-defined subclient *LINK and validate subclient default values"
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.subclient_name = None
        self.client_machine = None
        self.dest_dir = None
        self.scan_type = None
        self.subclient_name = None
        self.src_path = None
        self.IBMiMode = None
        self.filters = None
        self.job = None

    def configure_sc(self):
        """
               Configure predefined and another subclient with content
        """
        self.helper.configure_ibmi_default_sc(backupset_name="backupset_{0}".format(self.id),
                                              subclient_name=self.subclient_name,
                                              storage_policy=self.storage_policy,
                                              scan_type=self.scan_type,
                                              filter_content=self.filters,
                                              data_readers=1,
                                              allow_multiple_readers=False,
                                              delete=False)
        self.log.info("adding filters to *LINK subclient to avoid failures from system directories %s", self.filters)

    def verify_logs(self, operation="restore"):
        """
               Verify client logs for VTL operation
               Args:
               operation      (str)            -- Type of operation
               (backup/restore)
        """
        if operation == "backup":
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue='SAV '
                                        )
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue='VOL('
                                        )
            self.helper.verify_from_log('cvbkpvtl*.log',
                                        'runEachCommand',
                                        jobid=self.job.job_id,
                                        expectedvalue='DEV('
                                        )
        else:
            self.helper.verify_from_log('cvrest*.log',
                                        'Submitted job with command ',
                                        jobid=self.job.job_id,
                                        expectedvalue='RST OBJ('
                                        )
            self.helper.verify_from_log('cvrest*.log',
                                        'Submitted job with command ',
                                        jobid=self.job.job_id,
                                        expectedvalue='VOL('
                                        )
            self.helper.verify_from_log('cvrest*.log',
                                        'Submitted job with command ',
                                        jobid=self.job.job_id,
                                        expectedvalue='DEV('
                                        )

    def cleanup(self):
        """
        Cleanup the data on client machine
        """
        self.log.info("Cleanup the directories on client machine.")

        for each in self.src_path:
            self.client_machine.remove_directory(directory_name=each)
        self.client_machine.remove_directory(self.dest_dir)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)
            self.scan_type = ScanType.RECURSIVE
            self.subclient_name = "*LINK"
            self.src_path = ["/AUT{0}".format(self.id), "/AUT{0}1".format(self.id)]
            self.filters = ["/QSR", "/QIBM", "/tmp", "/QFileSvr.400", "/QOpenSys", "/var/commvault"]
            self.dest_dir = "/AUTRSTVTL"

            self.log.info("*** STARTING RUN FOR Pre-defined subclient *LINK backup and restore with VTL **")
            self.log.info("Step1, configure BackupSet and Subclients for VTL TC")
            self.configure_sc()
            self.cleanup()
            self.log.info("Step2: On client, create a directory {0} with objects".format(self.src_path[0]))
            self.client_machine.populate_ifs_data(directory_name=self.src_path[0],
                                                  tc_id=self.id,
                                                  count=10,
                                                  prefix="F",
                                                  delete=True)
            self.log.info("Step3: Run a full backup for the subclient *LINK "
                          "and verify if it completes without failures.")
            self.job = self.helper.run_backup(backup_level="Full")[0]
            # self.job = self.helper.run_backup_verify(self.scan_type, "Full")[0]
            self.log.info("Step4: Verify full backup logs for proper inputs and command with VTL .")
            self.verify_logs("backup")
            self.log.info("Step5: On client, Create another directory {0} with objects.".format(self.src_path[1]))
            self.client_machine.populate_ifs_data(directory_name=self.src_path[1],
                                                  tc_id=self.id,
                                                  count=10,
                                                  prefix="I",
                                                  delete=True)
            self.log.info("Step6: On client, Create few text files under directory {0}.".format(self.src_path[0]))
            self.client_machine.populate_ifs_data(directory_name=self.src_path[0],
                                                  tc_id=self.id,
                                                  count=5,
                                                  prefix="N",
                                                  delete=False)
            self.log.info("Step7: Run an incremental self.job for the subclient"
                          " and verify if it completes without failures.")
            self.job = self.helper.run_backup(backup_level="Incremental")[0]
            self.log.info("Step8: Check Inc backup logs to confirm backup commands.")
            self.verify_logs("backup")

            self.log.info("Step9: run OOP restore of both directories and verify.")
            for each in self.src_path:
                self.client_machine.remove_directory(directory_name=self.dest_dir)
                self.log.info("run OOP restore of directory [{0}] to "
                              "directory [{1}] and verify.".format(each, self.dest_dir))
                self.job = self.helper.restore_out_of_place(self.dest_dir,
                                                            paths=[each],
                                                            restore_ACL=False,
                                                            preserve_level=0)
                self.log.info("Verify restore logs for VTL restore operation")
                self.verify_logs()
                self.helper.compare_ibmi_data(source_path="{0}/*".format(each),
                                              destination_path="{0}/*".format(self.dest_dir))
            self.cleanup()

            self.log.info("**%s SCAN RUN OF *IBM COMPLETED SUCCESSFULLY WITH VTL**", self.scan_type.name)
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
