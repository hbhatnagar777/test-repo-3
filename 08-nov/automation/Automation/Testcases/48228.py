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

    setup()                 --  create fshelper object

    configure_test_case()   --  Handles subclient creation, and any special configurations.

    run()                   --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import ScanType, FSHelper, IndexEnabled
from AutomationUtils import database_helper
from AutomationUtils.database_helper import MSSQL


class TestCase(CVTestCase):
    """Class for executing

            """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Block Level Unpick snap option check with Filer"
        self.applicable_os = self.os_list.UNIX
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = False
        self.tcinputs = {
            "TestPath": None,
            "TestPath2": None,
            "RestorePath":None,
            "StoragePolicyName": None,
            "snapengine": None,
            "CsDbServer": None,
            "CsDbUser": None,
            "CSDbPassword": None
        }
        # Other attributes which will be initialized in
        # FSHelper.populate_tc_inputs
        self.test_path = None
        self.slash_format = None
        self.helper = None
        self.storage_policy = None
        self.client_machine = None
        self.subclient_content = None
        self.tmp_path = None

    def setup(self):
        self.helper = FSHelper(self)

    def configure_test_case(self, index_type):
        """
        Function that handles subclient creation, and any special configurations


        Returns:
            None
        """

        self.log.info("Step2.1, Check Intellisnap is enabled "
                      "on the client or not , if not enable it")

        if not self.client.is_intelli_snap_enabled:
            self.log.info("Intellisnap is not enabled for client, enabling it")
            self.client.enable_intelli_snap()
        self.log.info("Intellisnap For client is enabled")

        self.log.info("Step 2.2, Create subclient for the test case ")

        subclient_name = "subclient_{0}_Recursive_{1}".format(self.id, index_type.name)
        subclient_content = list()
        if index_type.name == 'NOINDEX':
            subclient_content.append(self.test_path)
        else:
            subclient_content.append(self.test_path2)
        self.helper.create_subclient(name=subclient_name, storage_policy=self.storage_policy,
                                     content=subclient_content)
        if index_type.name == "INDEX":
            self.log.info("Enabling Metadata collection")
            self.helper.update_subclient(createFileLevelIndex=True)
        self.log.info("Step 2.3 ,Enable intellisnap on subclient with Snap Engine Option")

        if not self.subclient.is_intelli_snap_enabled:
            self.log.info("Intellisnap is not enabled at subclient level")
            self.subclient.enable_intelli_snap(str(self.snap_engine))

        self.helper.update_subclient(block_level_backup=1)

        self.log.info("Step2.4 , Intellisnap with Block level is enabled on subclient")

    def run(self):
        """Main function for test case execution
            This test case does the following:
                Step1, Create backupset for this testcase if it doesn't exist
                Run the Following for with metadata enabled and without metadata enabled
                        Step2, Configure test case
                            Step2.1, Check Intellisnap is enabled
                                     on the client or not , if not enable it
                            Step 2.2, Create subclient for the test case
                            Step 2.3 ,Enable intellisnap on subclient with Snap Engine Option
                            Step2.4 , Intellisnap with Block level is enabled on subclient

                        Step3, Add full data for the current run.
                        Step4, Run a full backup for the subclient and
                               verify it completes without failures.
                        Step5, Add inc1 data ,Run a inc1 backup for the subclient and
                               set it unpick for backup copy
                        Step6, Add inc2 data ,Run a inc2 backup for the subclient and
                               set it unpick for backup copy
                        Step7, Add inc3, run Incremental snap job with backup copy
                        Step8, Run Volume level restore and verify the result
                        Step9, Run File level restore and verify result
                        Step10, Run an synthfull for the subclient and
                                verify it completes without failures
        """
        try:
            self.log.info("***TESTCASE: %s***", self.name)

            # Initialize test case inputs
            FSHelper.populate_tc_inputs(self)
            # self.csdb = database_helper.CommServDatabase(self.commcell)
            if self.commcell.is_linux_commserv:
                CS_DB_server = "{}".format(self.tcinputs.get('CsDbServer'))
            else:
                CS_DB_server = "{}\\COMMVAULT".format(self.tcinputs.get('CsDbServer'))

            CS_DB_user = self.tcinputs.get('CsDbUser')

            CS_DB_pass = self.tcinputs.get('CSDbPassword')

            if self.test_path.endswith(self.slash_format):
                self.test_path = str(self.test_path).rstrip(self.slash_format)

            self.log.info("Connecting to CS DB")

            mssql = MSSQL(CS_DB_server, CS_DB_user, CS_DB_pass, "CommServ")

            self.log.info("Connection to CS DB is established")

            self.log.info("Step1, Create backupset for this testcase if it doesn't exist")
            backupset_name = "backupset_{0}".format(self.id)
            self.helper.create_backupset(backupset_name, delete=True)

            self.log.info(" Step2, Configure test case")
            for index_type in IndexEnabled:
                self.log.info("Running with {}".format(index_type.name))
                if index_type.name == 'INDEX':
                    continue
                self.configure_test_case(index_type)

                if index_type.name == 'NOINDEX':
                    subclient_content = self.test_path
                else:
                    subclient_content = self.test_path2

                run_path = "{}{}{}_{}".format(subclient_content, self.slash_format, str(self.id),index_type.name)
                full_data_path = "{}{}Full".format(run_path, self.slash_format)

                self.client_machine.remove_directory(run_path)
                self.log.info("Step3, Add full data for the current run.")

                self.log.info("Adding data under %s" % full_data_path)

                self.client_machine.generate_test_data(full_data_path, dirs=5, files=20, file_size=50)

                self.log.info("Step4, Run a full backup for the subclient "
                              "and verify it completes without failures.")
                _ = self.helper.run_backup_verify(backup_level="Full")[0]

                self.helper.backup_copy()

                for i in range(1, 3):
                    inc_data_path = "{}{}inc{}".format(run_path, self.slash_format, i)
                    self.log.info("Adding data under %s" % inc_data_path)
                    self.client_machine.generate_test_data(inc_data_path, dirs=5,
                                                           files=20, file_size=50)
                    self.log.info("Step{}, Run a inc{} backup and verify it "
                                  "completes without failures.".format(4 + i, i))
                    job_inc = self.helper.run_backup_verify()[0]

                    query = "Update JMJobSnapshotStats set disabled = 1 " \
                            "where jobid = {}".format(job_inc.job_id)
                    mssql.execute(query)
                    # self.csdb.execute(query)
                    # self.log.info(self.csdb.rows)
                    self.log.info("Do not pick for backup Copy is set "
                                  "for jobid {}".format(job_inc.job_id))

                self.log.info("Step7, Run Incremental job with backup copy ")
                inc_data_path = "{}{}inc3".format(run_path, self.slash_format)
                self.log.info("Adding data under %s" % inc_data_path)
                self.client_machine.generate_test_data(inc_data_path, dirs=5, files=20, file_size=50)
                _ = self.helper.run_backup_verify()[0]
                self.helper.backup_copy()

                dest_path = "{}{}{}_{}".format(self.restore_path, self.slash_format, self.id, index_type.name)

                self.log.info("Step8, Run Volume level restore and verify the result")

                self.helper.volume_level_restore(run_path, dest_path, self.client_name)

                self.log.info("Step9, Run File level restore and verify result")

                self.helper.run_restore_verify(self.slash_format, run_path,
                                               self.restore_path,
                                               "{}_{}".format(self.id, index_type.name),
                                               proxy_client=self.client_name)
                self.log.info("Step10, Run Synthetic full for the subclient and "
                              "verify it completes without failures")

                self.helper.run_backup_verify(backup_level="Synthetic_full")
            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
