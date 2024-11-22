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
                        Performs Backup, Drops Table
                        Restores the table and Validates table records.
"""
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import machine
from Database.OracleUtils.oraclehelper import OracleHelper


class TestCase(CVTestCase):
    """
    Test case class used to run a given test
    """

    def __init__(self):
        """TestCase constructor"""
        super(TestCase, self).__init__()
        self.name = "Oracle Test Case 52658 - Snap Partial Datafile Restore"
        self.show_to_user = True
        self.oracle_helper = None
        self.status = constants.FAILED
        self.result_string = "Run of test case 52658 is incomplete"
        self.tcinputs = {
            "SnapEngine": None,
            "OracleOptions": None
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
            "52658", storage_policy, self.tcinputs['SnapEngine'], 2, True, True, False, 0, False)

    def run(self):
        """Main function for test case execution"""

        try:

            self.log.info("Started executing %s Test Case", self.id)
            ts_name = 'CV_52658'
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

            # Dropping datafile with the suffix 1 after the backup
            client_machine_object = machine.Machine(self.client)
            df_to_be_restored = '{0}{1}{2}.dbf'.format(
                self.oracle_helper.db_fetch_dbf_location(), ts_name, 1)
            client_machine_object.delete_file(df_to_be_restored)
            self.log.info("Datafile in the Tablespace %s deleted", ts_name)

            ins_name = self.instance.instance_name
            file_option = {
                "sourceItem": [
                    "SID: {0}   Tablespace: CV_52658 Datafile: {1}".format(
                        ins_name,
                        df_to_be_restored)]}

            self.log.info(
                "Running instance level snap restore from full snap backup on database: %s",
                self.instance.instance_name)

            paths = {
                'sourcePaths': ["{0}".format(df_to_be_restored)]
            }
            self.tcinputs['OracleOptions'].update(paths)

            # Restoring and recovering from latest backup
            # Performs an instance level snap full restore - All the tablespaces from
            # the latest backup are restored
            job = self.instance.restore(
                destination_client=self.client.client_name,
                destination_instance=self.instance.instance_name,
                files=file_option,
                common_options=None,
                oracle_options=self.tcinputs['OracleOptions'], tag='SNAP')
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

            self.status = constants.PASSED
            self.result_string = "Run of test case 52658 has completed successfully"
        except Exception as exp:
            self.log.error("""Testcase failed with exception : %s""", exp)
            raise
