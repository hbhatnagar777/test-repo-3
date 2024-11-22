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

    run()           --  run function of this test case
"""
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.OracleUtils.oraclehelper import OracleHelper, OracleDMHelper


class TestCase(CVTestCase):
    """
    Test case class used to run a given test
    """

    def __init__(self):
        """TestCase constructor"""
        super(TestCase, self).__init__()
        self.name = "Oracle Test Case 52945 - Acceptance test for all basic oracle functions"
        self.product = self.products_list.ORACLE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = False
        self.commserver_name = None
        self.oracle_helper = None
        self.status = constants.FAILED
        self.result_string = "Run of test case 52945 is incomplete"
        self.tcinputs = {
            "client_ip": None,
            "port": 1521,
            "schema": None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.log = logger.get_log()
        self.log.info('CS set to {0} in test case: {1}'.format(self.commcell,
                                                               self.id))

    def run(self):
        """Main function for test case execution"""
        numeric_policy_name = "numeric_52945"
        char_policy_name = "char_52945"
        varchar_policy_name = "varchar_52945"
        inputs = self.tcinputs
        try:
            self.log.info("Started executing {0} Test Case on CS: {1}"
                          .format(self.id, self.commcell))

            self.log.info(
                " {0} Initialize helper objects {1} ".format("*" * 10, "*" * 10))

            client_host = inputs['client_ip']

            self.oracle_helper = OracleHelper(
                self.commcell, client_host, self.instance)

            # Step 1 -- Run full backup and restore
            # If service name is different from instance name, set it like below
            # self.oracle_helper.ora_service_name = inputs['service_name']
            self.oracle_helper.ora_host_name = client_host
            self.oracle_helper.ora_port = inputs['port']
            schema_name = inputs['schema']
            self.oracle_helper.db_connect()

            ### creating oracle data masking helper object ###
            oracle_dm_helper = OracleDMHelper(self.oracle_helper)
            db_status = self.oracle_helper.get_db_status()
            self.log.info('   DB DBID: {0}'.format(self.instance.dbid))
            self.log.info('   DB Status: {0}'.format(db_status))
            self.log.info('   DB Version: {0}'.format(
                self.oracle_helper.ora_version))

            if db_status.strip().upper() != 'READ WRITE':
                self.log.exception(
                    'Database status is invalid: {}'.format(db_status))
                raise ValueError('Invalid database status: '.format(db_status))

            ### Calling respective data masking methods ###
            number_type_status = oracle_dm_helper.numeric_type_masking(
                numeric_policy_name, schema_name=schema_name)
            self.log.info(
                "Numeric masking status : {0}".format(number_type_status))
            char_type_status = oracle_dm_helper.char_varchar_type_masking(
                column_type=1, policy_name=char_policy_name, schema_name=schema_name)
            self.log.info("char masking status :{0}".format(char_type_status))
            varchar_type_status = oracle_dm_helper.char_varchar_type_masking(
                column_type=2, policy_name=varchar_policy_name, schema_name=schema_name)
            self.log.info("varchar masking status :{0}".format(
                varchar_type_status))

            ### test case success validation based data masking results ###
            if number_type_status and char_type_status and varchar_type_status:
                self.status = constants.PASSED
                self.result_string = "Run of test case 52945 has completed successfully"
                self.log.info(
                    "Run of test case 52945 has completed successfully")
            else:
                self.status = constants.FAILED
                self.result_string = "Run of test case 52945 has failed"
                self.log.info("Run of test case 52945 has failed")
            oracle_dm_helper.masking_data_cleanup()
        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            oracle_dm_helper.masking_data_cleanup()
