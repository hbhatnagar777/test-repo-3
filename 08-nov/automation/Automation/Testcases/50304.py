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

        init_tc()               --  Initalize the TC variables

        configure_sc()          --  Configure predefined SC and another SC with content

        generate_data()         --  Generate data on client machine.

        restore_verify()        --  Initiates OOP restore for content and verify the Advanced restore options

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
        IBMi- Validation of IFS exception content removal after backup behavior check.
            Configure SC with some user directories with wildcard content, wildcard filters and
                wildcard exception content with IFS content.
            Run full backup of the Subclient.
            Update SC with wildcard exception content.
            Perform Incremental backup.
            Perform OOP restore and verify if proper content is dropped by backup
            Run Cleanup on client machine.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "IBMi- Validation of IFS exception content removal after backup behavior check."
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
        self.dest_dir = None
        self.sc_name = None
        self.job = None
        self.scan_type = None
        self.IBMiMode = None
        self.usr_dir = None
        self.content = None
        self.filter = None
        self.exception = None
        self.validate = None
        self.create = None
        self.job_inc = None

    def init_tc(self):
        """
        Initalize the TC variables with required values.
        """
        self.dest_dir = "/TCR{0}".format(self.id)
        self.exception = []
        self.filter = []
        self.validate = []
        self.create = []
        self.usr_dir = []
        self.content = ["/TC{0}/L?{0}".format(self.id),
                        "/TC{0}/CONSTANT".format(self.id)]
        self.filter = ["/TC{0}/L*".format(self.id)]
        self.exception = ["/TC{0}/L[R,D]*".format(self.id)]
        self.usr_dir = ["/TC{0}/LD{0}".format(self.id), "/TC{0}/CONSTANT".format(self.id)]
        self.validate = ["/TC{0}/LD{0}".format(self.id)]

    def configure_sc(self):
        """
               Configure predefined and another subclient with content
        """
        self.log.info("Configuring subclient..")

        self.subclient_name = "subclient_{0}".format(self.id)
        self.helper.create_subclient(name=self.subclient_name,
                                     storage_policy=self.storage_policy,
                                     content=self.content,
                                     filter_content=self.filter,
                                     scan_type=self.scan_type,
                                     data_readers=8,
                                     allow_multiple_readers=True,
                                     delete=True)

    def generate_data(self):
        """
            Generate Incremental data on client machine.
        """
        self.log.info("Generating data on client machine")
        self.client_machine.populate_ifs_data(directory_name="/TC{0}".format(self.id),
                                              tc_id=self.id,
                                              count=0,
                                              prefix="F",
                                              delete=True)

        for each in self.usr_dir:
            self.client_machine.populate_ifs_data(directory_name=each,
                                                  tc_id=self.id,
                                                  count=5,
                                                  prefix="F",
                                                  delete=True)

    def generate_incdata(self):
        """
            Generate incremental data on client machine.
        """
        self.log.info("Generating Incremental data on client machine")
        for each in self.usr_dir:
            self.client_machine.populate_ifs_data(directory_name=each,
                                                  tc_id=self.id,
                                                  count=5,
                                                  prefix="I",
                                                  delete=False)

    def restore_verify(self):
        """
            Initiates OOP restore for content and verify the restored data and objects reporting ...
        """
        self.log.info("run OOP restore of [{0}] to [{1}] and verify.".format(self.validate[0], self.dest_dir))
        self.job = self.helper.restore_out_of_place(
            destination_path=self.dest_dir,
            paths=["{0}/I{1}".format(self.validate[0], self.id),
                   "{0}/I{1}".format(self.validate[0], self.id)],
            restore_ACL=False,
            preserve_level=0,
            from_time=self.job_inc.start_time,
            to_time=self.job_inc.end_time,
            **{'wait_to_complete': False})
        self.job.wait_for_completion()
        if not self.job.status.lower() == "failed":
            raise Exception(
                "Restore job status is not failed, job has status: {0}".format(self.job.status))
        else:
            self.log.info("Exception content {0} hasn't picked and Restore has successfully "
                          "failed".format(self.exception))

    def cleanup(self):
        """
            Cleanup the data on client machine
        """
        self.client_machine.remove_directory("/TC{0}".format(self.id))
        self.client_machine.remove_directory(self.dest_dir)

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
            self.init_tc()
            self.helper.create_backupset(name="backupset_{0}_{1}".format(self.id, self.IBMiMode))
            self.scan_type = ScanType.RECURSIVE
            self.log.info("*** STARTING VALIDATION OF WILDCARD EXCEPTIONS AFTER BACKUP WITH IFS ***")
            self.generate_data()
            self.configure_sc()
            self.job = self.helper.run_backup(backup_level="Full")[0]
            self.log.info("updating the subclient with exception content {0}".format(self.exception))
            self.helper.update_subclient(exception_content=self.exception)
            self.job_inc = self.helper.run_backup(backup_level="Incremental")[0]
            self.restore_verify()
            self.cleanup()
            self.log.info("**IBMi: VALIDATION OF IFS USING WILDCARD EXCEPTION CONTENT AFTER BACKUP HAS"
                          " COMPLETED SUCCESSFULLY**")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.result_string = str(excp)
            self.log.error('Failed with error: %s', self.result_string)
            self.status = constants.FAILED
