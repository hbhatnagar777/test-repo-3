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

    run()           --  Oracle Acceptance Testcase iwth basic backup and restore functions
"""
import sys
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
        self.name = "Oracle Acceptance test case for all basic oracle functions"
        #self.product = self.products_list.ORACLE
        #self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        #self.commserver_name = None
        self.oracle_helper = None
        self.status = constants.FAILED
        self.result_string = "Run of test case 4815 is incomplete"
        self.tcinputs = {
            "client_ip": None,
            "port": 1521
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.log.info('CS set to %s in test case: %s', self.commcell, self.id)

    def run(self):
        """Main function for test case execution"""

        inputs = self.tcinputs
        try:
            self.log.info("Started executing %s Test Case", self.id)

            self.log.info(
                "%(boundary)s %(message)s %(boundary)s",
                {
                    'boundary': "*" * 10,
                    'message': "Initialize helper objects"
                }
            )

            self.log.info(
                "%(boundary)s %(message)s %(boundary)s",
                {
                    'boundary': "*" * 10,
                    'message': "Create SDK objects"
                }
            )

            self.oracle_helper = OracleHelper(
                self.commcell, self.client, self.instance)

            # Step 1 -- Run full backup and restore
            # If service name is different from instance name, set it like below
            # self.oracle_helper.ora_service_name = inputs['service_name']
            self.oracle_helper.ora_host_name = inputs['client_ip']
            self.oracle_helper.ora_port = inputs['port']
            self.oracle_helper.db_connect(OracleHelper.CONN_SYSDBA)
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

            self.oracle_helper.db_execute('alter system switch logfile')
            self.log.info(' STEP 1: Logfile switch complete...')
            self.log.info(
                " STEP 1: Running full backup on database: %s ", self.instance.instance_name)
            job = self.subclient.backup(r'full')
            if not job.wait_for_completion():
                raise Exception("Failed to run FULL backup job with error: {0}"
                                .format(job.delay_reason))
            self.log.info(
                " STEP 1: Full backup JOB ID: %s ", job.job_id)
            self.log.info(
                " STEP 1: Running restore from full backup on database: %s",
                self.instance.instance_name)

            job = self.instance.restore()
            if not job.wait_for_completion():
                raise Exception("Failed to run restore job with error: {0}"
                                .format(job.delay_reason))
            self.log.info(
                " STEP 1: Full DB restore JOB ID: %s", job.job_id)

            # Step 2 -- Run incremental backup and restore
            self.log.info(
                " STEP 2: Running incremental backup on database: %s", self.instance.instance_name)
            job = self.subclient.backup(r'incremental')
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run Incremental backup job with error: {0}" .format(
                        job.delay_reason))
            self.log.info(
                " STEP 2: Incremental backup JOB ID: %s", job.job_id)
            self.log.info(
                " STEP 2: Running incremental restore on database: %s",
                self.instance.instance_name)

            job = self.subclient.restore()
            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore job with error: {0}".format(
                        job.delay_reason))
            self.log.info(
                " STEP 2: Incremental DB restore JOB ID: %s", job.job_id)

            self.status = constants.PASSED
            self.result_string = "Run of test case 4815 has completed successfully"
        except Exception as exp:
            message = """Testcase failed with exception : {0}""".format(str(exp))
            self.log.error(message)
            log_error = "Detailed Exception : {0}".format(sys.exc_info())
            self.log.error(log_error)
            self.result_string = str(exp)
            self.status = constants.FAILED
