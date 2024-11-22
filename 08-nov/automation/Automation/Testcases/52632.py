# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  Creates a tablespace, user, table with records,
                        Performs Snap Backup, Restore and Validate
                        adds more records - Performs Snap Backup, Restores and Validate
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
        self.name = "Oracle Snap Test Case - Acceptance test for all basic oracle functions"
        self.oracle_helper = None
        self.status = constants.FAILED
        self.result_string = "Run of test case 52632 is incomplete"
        self.tcinputs = {
            "SnapEngine": None
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
            "52632", storage_policy, self.tcinputs['SnapEngine'], 2, True, True, False, 0, False)

    def run(self):
        """Main function for test case execution"""

        try:

            self.log.info("Started executing %s Test Case", self.id)
            ts_name = 'CV_52632'
            table_limit = 1
            num_of_files = 1
            row_limit = 10

            self.oracle_helper.create_sample_data(ts_name, table_limit, num_of_files)
            self.oracle_helper.db_execute('alter system switch logfile')
            self.log.info(' STEP 1: Logfile switch complete...')

            self.log.info(
                " STEP 1: Running full backup on database: %s",
                self.instance.instance_name)
            self.oracle_helper.launch_backup_wait_to_complete(self.subclient, r"full")

            self.log.info("Waiting for the restore job to start")

            self.log.info(
                "Running instance level snap restore from full snap backup on database: %s",
                self.instance.instance_name)

            # Performs an instance level snap full restore - All the
            # tablespaces from the latest backup are restored
            job = self.instance.restore(
                destination_client=self.client.client_name,
                destination_instance=self.instance.instance_name,
                files=None,
                common_options=None,
                browse_options=None,
                oracle_options=None, tag='SNAP')
            if not job.wait_for_completion():
                raise Exception("Failed to run restore job with error: {0}"
                                .format(job.delay_reason))

            self.log.info(
                " STEP 1: Full database snap restore JOB ID: %s",
                job.job_id)

            self.oracle_helper.validation(
                ts_name,
                num_of_files,
                "CV_TABLE_01",
                row_limit)

            # populating table with 10 more records
            self.oracle_helper.db_populate_table(
                "CV_TABLE_", ts_name.lower() + '_user', 1)

            # Step 2 -- Run incremental backup : It's auto converted to full
            self.log.info(
                " STEP 2: Running Snap full backup on database: %s",
                self.instance.instance_name)
            self.oracle_helper.launch_backup_wait_to_complete(self.subclient, r"full")

            self.log.info(
                " STEP 2: Running full restore on database: %s",
                self.instance.instance_name)

            # Performs subclient level snap full restore - All the tablespaces
            # from the latest backup are restored
            job = self.subclient.restore(destination_client=self.client.client_name,
                                         destination_instance=self.instance.instance_name,
                                         files=None,
                                         common_options=None,
                                         browse_options=None,
                                         oracle_options=None, tag='SNAP')
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore job with error: {0}".format(
                        job.delay_reason))
            self.log.info(
                " STEP 2: Incremental->Full DB restore JOB ID: %s", job.job_id)

            self.oracle_helper.validation(
                ts_name,
                num_of_files,
                "CV_TABLE_01",
                2 * row_limit)


            self.status = constants.PASSED
            self.result_string = "Run of test case 52632 has completed successfully"
        except Exception as exp:
            self.log.error("""Testcase failed with exception : %s""", exp)
            raise
