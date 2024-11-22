# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""
Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  Creates a tablespace, user, table with records, Validates table records,
                        Performs Backup, Drops Table,Restores the table and Validates table records
                        All the restores performed are FS restores.
"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.OracleUtils.oraclehelper import OracleHelper

class TestCase(CVTestCase):
    """
    Test case class used to run a given test
    """

    def __init__(self):
        """TestCase constructor"""
        super(TestCase, self).__init__()
        self.name = "Oracle Test Case 52634 - FS Table Level Restore"
        self.show_to_user = True
        self.oracle_helper = None
        self.status = constants.FAILED
        self.result_string = "Run of test case 52634 is incomplete"
        self.tcinputs = {
            "SnapEngine": None,
            "OracleOptions": None,
            "commonOptions": None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.log.info('CS set to %s in test case: %s', self.commcell,
                      self.id)
        self.log.info("Initializing the pre-requisites for %s Test Case", self.id)
        self.log.info(
            "%(boundary)s %(message)s %(boundary)s",
            {
                'boundary': "*" * 10,
                'message': "Initialize helper objects"
            }
        )

        ######Establishing Client and Oracle Connection##########
        self.oracle_helper = OracleHelper(
            self.commcell, self.client, self.instance)
        self.oracle_helper.db_connect(OracleHelper.CONN_SYSDBA)

        self.oracle_helper.check_instance_status()
        storage_policy = self.tcinputs.get("storage_policy",
                                           self.instance.subclients.get('default').storage_policy)

        ###### Create Subclient for the Snapbackup content  = Data + Log#######
        self.subclient = self.oracle_helper.create_subclient(
            "52634", storage_policy, self.tcinputs['SnapEngine'], 2, True, True, False, 0, False)

        # Enable Table Browse Option
        if not self.subclient.is_table_browse_enabled:
            self.subclient.enable_table_browse()
            self.log.info("Enable Table Browse Property set to true")
        else:
            self.log.info("Table browse on the subclient is already set")

    def run(self):
        """Main function for test case execution"""

        try:

            self.log.info("Started executing %s Test Case", self.id)
            ts_name = 'CV_52634'
            table_limit = 1
            num_of_files = 1
            row_limit = 10

            self.oracle_helper.create_sample_data(ts_name, table_limit, num_of_files)
            self.oracle_helper.db_execute('alter system switch logfile')
            self.log.info(' STEP 1: Logfile switch complete...')

            self.log.info(" STEP 1: Running table level full backup on database: %s",
                          self.instance.instance_name)
            self.oracle_helper.launch_backup_wait_to_complete(self.subclient, r"full")

            self.oracle_helper.validation(
                ts_name,
                num_of_files,
                "CV_TABLE_01",
                row_limit)

            # drop table
            self.oracle_helper.db_drop_table(ts_name.lower() + '_user', "CV_TABLE_01")

            self.log.info(" STEP 2: Running restore on database: %s", self.instance.instance_name)
            self.log.info(" STEP 2: Running table level snap restore on database: %s",
                          self.instance.instance_name)

            # Performs subclient level snap full restore
            job = self.subclient.restore(
                destination_client=self.client.client_name,
                destination_instance=self.instance.instance_name,
                common_options=self.tcinputs['commonOptions'],
                oracle_options=self.tcinputs['OracleOptions'], tag='SNAP')
            if not job.wait_for_completion():
                raise Exception("Failed to run restore job with error: {0}".format(
                    job.delay_reason))
            self.log.info(" STEP 2: Table Level with FS restore JOB ID: %s", job.job_id)

            self.oracle_helper.validation(
                ts_name,
                num_of_files,
                "CV_TABLE_01",
                row_limit)


            self.status = constants.PASSED
            self.result_string = "Run of test case 52634 has completed successfully"

        except Exception as exp:
            self.log.error("""Testcase failed with exception : %s""", exp)
            raise
