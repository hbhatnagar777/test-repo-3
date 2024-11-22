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

    run()           --  run function of this test case

"""


from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants, config
from BigDataApps.YugabyteDBUtils.yugabytedbhelper import YugabyteDB

from Automation.Reports.utils import TestCaseUtils

CONSTANTS = config.get_config()
class TestCase(CVTestCase):
    """
    Class for creating and performing basic operations on a new yugabytedb client
    """

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Testcase for creating and performing basic operations on a new yugabytedb client"
        self.rowids = None
        self.tbname2 = None
        self.tbname = None
        self.sslrootcert = None
        self.ycql_password = None
        self.ycql_username = None
        self.utils = None
        self.ysql_password = None
        self.ysql_username = None
        self.sqldbname = None
        self.cqldbname = None
        self.destsqldbname = None
        self.destcqldbname = None
        self.yugabyte_object = None
        self.tcinputs = {
            'db_host': None,
            'node_ip': None,
            'api_token': None,
            'universe_name': None,
            'config_name': None,
            'plan_name': None,
            'data_access_nodes': None,
            'user_uuid': None,
            'universe_uuid': None,
            'config_uuid': None,
            'kmsconfig_uuid': None
        }

    def setup(self):
        """Initializes object required for this testcase"""
        self.ysql_username = CONSTANTS.Bigdata.YugabyteDB.ysql_username
        self.ysql_password = CONSTANTS.Bigdata.YugabyteDB.ysql_password
        self.ycql_username = CONSTANTS.Bigdata.YugabyteDB.ycql_username
        self.ycql_password = CONSTANTS.Bigdata.YugabyteDB.ycql_password
        self.sslrootcert = CONSTANTS.Bigdata.YugabyteDB.sslrootcert
        self.aws_access_key = CONSTANTS.Bigdata.YugabyteDB.aws_access_key
        self.aws_secret_key = CONSTANTS.Bigdata.YugabyteDB.aws_secret_key
        self.sqldbname = 'ybautosqldb'
        self.cqldbname = 'ybautocqldb'
        self.destsqldbname = 'ybautosqldb_oopauto'
        self.destcqldbname = 'ybautocqldb_oopauto'
        self.tbname = 'ybautomationtb'
        self.tbname2 = 'ybautomationtb2'
        self.rowids = [1, 2, 3, 4, 5]
        self.content = ["/ybautosqldb.sql", "/ybautocqldb.cql"]

    def run(self):
        """ Run function of this test case"""
        try:
            self.log.info("populating test data")
            self.log.info("Creating Yugabytedb Object")
            self.yugabytedb = YugabyteDB(self)
            self.log.info("Yugabytedb Object Creation Successful")
            #connect to db and create sample databases
            self.yugabytedb.connect_to_db()
            self.yugabytedb.populate_test_data(self.sqldbname, self.cqldbname, self.tbname,
                                                                 self.rowids)
            self.log.info("About to start adding new Yugabytedb client")
            client_obj = self.yugabytedb.add_yugabyte_client()
            if client_obj is None:
                raise Exception("New Client Creation Failed")
            self.log.info("Addition of New yugabytedb Client Successful")

            client_details = self.yugabytedb.get_client_details(
            client_obj, backupset_name = "defaultbackupset", subclient_name = "default")

            self.yugabytedb.run_backup(client_obj, client_details)

            self.yugabytedb.drop_db_and_restore(
                srcsqldbname=self.sqldbname,
                srccqldbname=self.cqldbname,
                tbname=self.tbname)

            self.yugabytedb.restore_to_newdb(
                srcsqldbname=self.sqldbname,
                srccqldbname=self.cqldbname,
                tbname=self.tbname)

            # add more data and run incremental job and restore from instance details
            self.yugabytedb.update_test_data(srcsqldbname=self.sqldbname,
                                             srccqldbname=self.cqldbname,
                                             tbname=self.tbname,
                                             rowids=[6, 7])

            self.yugabytedb.run_backup(client_obj, client_details, backup_type='Incremental')

            self.yugabytedb.restore_to_newdb(
                srcsqldbname=self.sqldbname,
                srccqldbname=self.cqldbname,
                tbname=self.tbname)

            self.yugabytedb.update_test_data(srcsqldbname=self.sqldbname,
                                             srccqldbname=self.cqldbname,
                                             tbname=self.tbname,
                                             rowids=[6, 7],
                                             deletedata=True)

            self.yugabytedb.run_backup(client_obj, client_details, backup_type='Incremental')

            self.yugabytedb.restore_to_newdb(
                srcsqldbname=self.sqldbname,
                srccqldbname=self.cqldbname,
                tbname=self.tbname)

            # add new table, and run incremental job from namespace group actions restore from namespace group actions
            self.yugabytedb.populate_test_data(self.sqldbname, self.cqldbname,
                                               tbname=self.tbname2,
                                               rowids=self.rowids,
                                               clean_data=False)

            self.yugabytedb.run_backup(client_obj, client_details, backup_type='Incremental')

            self.yugabytedb.new_table_restore(
                srcsqldbname=self.sqldbname,
                srccqldbname=self.cqldbname,
                tbname=self.tbname,
                tbname2=self.tbname2)

            self.yugabytedb.delete_yugabyte_client()
            self.yugabytedb.drop_table(self.sqldbname, self.cqldbname, self.tbname2)
            self.yugabytedb.drop_database(self.sqldbname, self.cqldbname, self.tbname)
            self.yugabytedb.drop_database(self.destsqldbname, self.destcqldbname, self.tbname)
            self.yugabytedb.close_dbconnection()

            self.log.info("testcase execution completed successfully")
            self.status = constants.PASSED


        except Exception as ex:
            self.log.info(Exception)
            self.log.error('failure in automation case : %s', ex)
            self.result_string = str(ex)
            self.log.info('Test case failed')
            self.status = constants.FAILED
