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

    run()           --  Creates a tablespace, user, table with records
                        Performs Backup, Restore and Validate
                        adds more records - Performs Backup, Restore and Validate
"""
from time import sleep
from cvpysdk.subclient import Subclients
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
        self.name = "Oracle Test Case - Acceptance test for all basic oracle functions"
        self.show_to_user = True
        self.oracle_helper = None
        self.status = constants.FAILED
        self.result_string = "Run of test case 38568 is incomplete"

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.log.info('CS set to %s in test case: %s', self.commcell, self.id)
        self.oracle_helper = OracleHelper(
            self.commcell, self.client, self.instance)
        self.oracle_helper.db_connect(OracleHelper.CONN_SYSDBA)

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Started executing %s Test Case", self.id)

            self.log.info(
                "%(boundary)s %(message)s %(boundary)s",
                {
                    'boundary': "*" * 10,
                    'message': "Initialize helper objects"
                }
            )

            db_status = ''
            for result in self.oracle_helper.db_execute(
                    'select open_mode from v$database'):
                db_status = result[0]
            self.log.info('DB DBID: %s', self.instance.dbid)
            self.log.info('DB Status: %s', db_status)
            self.log.info('DB Version: %s', self.oracle_helper.ora_version)

            if db_status.strip().upper() != 'READ WRITE':
                self.log.exception('Database status is invalid: %s', db_status)
                raise ValueError('Invalid database status: {0}'.format(db_status))

            self.log.info('Create Tablespace and tables')
            ts_name = 'CV_38568'
            user = 'cv_38568_user'
            table_prefix = "CV_TABLE_"
            table_limit = 1
            num_of_files = 1
            row_limit = 10

            data_file_location = self.oracle_helper.db_fetch_dbf_location()

            # create a sample tablespace
            self.oracle_helper.db_create_tablespace(
                ts_name, data_file_location, num_of_files)

            # create user/schema
            self.oracle_helper.db_create_user(user, ts_name)
            # create table and populate with 10 records
            self.oracle_helper.db_create_table(
                ts_name, table_prefix, user, table_limit)

            self.sub_client = self.instance.subclients.get('default')
            storage_policy = self.sub_client.storage_policy

            ###### Create Subclient  #######
            self.subclients = Subclients(self.instance)
            if not self.subclients.has_subclient("FullOnline1"):
                self.log.info(' STEP: Creating Subclient for the Snap Backups')
                self.subclients.add(
                    "FullOnline1", storage_policy, None, "OnlineSnap")
            else:
                self.log.info("Subclient named 'FullSnap1' exists - Skipping creation")

            self.subclient = self.subclients.get("FullOnline1")
            ##### Modifying the properties of the subclient for Snap ###
            self.subclient.set_prop_for_orcle_subclient(storage_policy)

            self.oracle_helper.db_execute('alter system switch logfile')
            self.log.info(' STEP 2: 3: Logfile switch complete...')

            ####################################STEP 4#######################
            self.log.info(
                " STEP 2: 4: Running full backup on database: %s", self.instance.instance_name)
            job = self.subclient.backup(r'full')
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run FULL backup job with error: {0}".format(
                        job.delay_reason))
            self.log.info(
                " STEP 2: 5: Full backup JOB ID: %s", job.job_id)

            self.log.info("Waiting for the restore job to start")
            sleep(15)

            ####################################STEP 5######################
            self.log.info(
                " STEP 2: 6: Running instance level restore from full backup on database: %s",
                self.instance.instance_name)
            # Restoring and recovering from latest backup
            job = self.instance.restore(
                destination_client=self.client.client_name,
                common_options=None,
                oracle_options=None)
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore job with error: {0}".format(
                        job.delay_reason))
            self.log.info(
                " STEP 2: 6: Full database restore JOB ID: %s",
                job.job_id)

            self.oracle_helper.validation(
                ts_name,
                num_of_files,
                user,
                table_prefix +
                "01",
                row_limit)

            ####################################STEP 6#######################
            # populating table with 10 more records
            self.oracle_helper.db_populate_table(
                table_prefix, user, table_limit)

            # Step 2: 7 -- Run incremental backup :
            self.log.info(
                " STEP: Running incremental backup on database: %s",
                self.instance.instance_name)
            job = self.subclient.backup(r'incremental')
            if not job.wait_for_completion():
                raise Exception("Failed to run full backup job with error: {0}"
                                .format(job.delay_reason))
            self.log.info(
                " STEP: Incremental backup JOB ID: %s",
                job.job_id)

            ####################################STEP 7######################
            self.log.info(
                " STEP: Running restore on database from incremental backup: %s",
                self.instance.instance_name)

            # Performs subclient level full restore - All the tablespaces
            # from the latest backup are restored
            job = self.subclient.restore(
                common_options=None,
                destination_client=self.client.client_name,
                oracle_options=None)
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore job with error: {0}".format(
                        job.delay_reason))
            self.log.info(
                " STEP 2: 8: Incremental DB restore JOB ID: %s",
                job.job_id)

            self.oracle_helper.validation(
                ts_name,
                num_of_files,
                user,
                table_prefix +
                "01",
                row_limit)
            #############################################################

            self.status = constants.PASSED
            self.result_string = "Run of test case 38568 has completed successfully"
        except Exception as exp:
            self.log.error("""Testcase failed with exception : %s""", exp)
            self.result_string = "Run of test case 38568 failed"
            self.status = constants.FAILED
