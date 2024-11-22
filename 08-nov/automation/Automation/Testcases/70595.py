# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run_restore_verify()              --  Initiates restore of data and validate the restored data

    connect_to_db()                    -- connect to cockroachdb cluster

    generate_test_data()               -- To generate the test database and tables

    update_test_data()                 -- update test data

    add_table()                        -- add test table

    drop_database()                    -- drop database

    validate_restoredata()             -- validate the restored data

    close_dbconnection()               -- close db connection

    setup()         --  initial settings for the test case

    init_tc()       --  initialize browser and redirect to required page

    run()           --  run function of this test case


    Input Example:
    multiple access nodes, "access_nodes" value need be string  "<node1>,<node2>...."

    "testCases": {
        "70595": {
            "access_nodes": None,
            "cockroachdb_host": None,
            "cockroachdb_port": None,
            "use_iamrole": None,
            "plan": None,
            "s3_service_host": None,
            "s3_staging_path": None,
            "use_ssl": None,
            "sslrootcert_on_controller": None,
            "sslcert_on_controller": None,
            "sslkey_on_controller": None
        }
    }
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config, logger, constants
from BigDataApps.CockroachDBUtils.cockroachdbhelper import CockroachDBHelper
from Web.AdminConsole.Helper.cockroachdb_helper import CockroachDBHelper as CDBHelper

CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """
    TestCase to validate instance creation, backup and restore for CockroachDB cluster
    """

    def __init__(self):
        """Initialize TestCase class"""
        super(TestCase, self).__init__()
        self.name = "Acceptance test for CockroachDB using restapi"
        self.browser = None
        self.admin_console = None
        self.cockroachdb_server_name = None
        self.db_username = None
        self.db_password = None
        self.aws_access_key = None
        self.aws_secret_key = None
        self.sslrootcert = None
        self.sslcert = None
        self.sslkey = None
        self.use_iamrole = None
        self.use_ssl = None
        self.database = None
        self.tablename = None
        self.rows = []
        self.cockroachdb = None
        self.tcinputs = {
            "access_nodes": None,
            "cockroachdb_host": None,
            "cockroachdb_port": None,
            "use_iamrole": None,
            "plan": None,
            "s3_service_host": None,
            "s3_staging_path": None,
            "use_ssl": None,
            "sslrootcert_on_controller": None,
            "sslcert_on_controller": None,
            "sslkey_on_controller": None
        }

    def connect_to_db(self, ssl_enabled=True):
        """initiate cockroachdb connection """
        self.__cockroachdb = CDBHelper(
            db_host=self.cockroachdb_host,
            db_username=self.db_username,
            db_password=self.db_password,
            db_port=self.cockroachdb__port,
            ssl_enabled=ssl_enabled,
            sslrootcert=self.sslrootcert_on_controller,
            sslcert=self.sslcert_on_controller,
            sslkey=self.sslkey_on_controller)

    def close_dbconnection(self):
        """close db connection"""
        self.__cockroachdb.close_connection()

    def generate_test_data(self, dbname, tbname, rowids, clean_data=True):
        """
        populate test data
        Args:
            dbname          (str)     --    database name
            tbname           (str)    --    table name
            rowids            (list)    --    list of row ids
            clean_data    (boolean)   --    recreate database and tables if True
        """
        if clean_data:
            self.__cockroachdb.drop_database(dbname)
            self.__cockroachdb.create_database(dbname)
            self.__cockroachdb.create_table(dbname, tbname)
        self.__cockroachdb.add_data(dbname, tbname, rowids)

    def update_test_data(self, dbname, tbname, rowids, deletedata=False):
        """
        update test data
        Args:
            dbname          (str)     --    database name
            tbname           (str)    --    table name
            rowids            (list)    --    list of row ids
            deletedata    (boolean)   --    delete  if True
        """
        self.__cockroachdb.update_data(dbname, tbname, rowids, deletedata)

    def add_table(self, dbname, tbname):
        """add new table
        Args:
            dbname          (str)     --    database name
            tbname           (str)    --    table name
        """
        self.__cockroachdb.create_table(dbname, tbname)

    def drop_database(self, dbname):
        """drop database
        Args:
            dbname          (str)     --    database name
        """
        self.__cockroachdb.drop_database(dbname)

    def run_restore_verify(
            self,
            srcdbname,
            destdbname,
            tablename,
            wait_to_complete=True):
        """Restores database and verify the restored data
        Args:
            srcdbname        (str)    --    source database name
            destdbname       (str)    --    destination database name
            tablename        str)     --    table name
            wait_to_complete  (bool)  --  Specifies whether to wait until restore job finishes.
        """

        origdata = self.__cockroachdb.get_rows(
            dbname=srcdbname, tbname=tablename)
        self.helper.run_restore(srcdbname, destdbname)
        self.validate_restoredata(origdata, destdbname, tablename)

    def validate_restoredata(self, srcdata, dbname, tbname):
        """"validate restore data in DB
        Args:
            srcdata    (list)  - data from original tables
            dbname          (string)    - restore destination databasename
            tbname           (string)   - restore destination tablename
        """
        destresult = self.__cockroachdb.get_rows(dbname, tbname)
        if srcdata == destresult:
            self.log.info("restored data match original data")
        else:
            raise Exception(
                "restored data does not match original data")

    def setup(self):
        """Initializes object required for this testcase"""
        self.log = logger.get_log()
        self.cockroachdb_name = "automated_cockroachDB_70595"
        self.credential_name = "credential_70595"
        self.db_username = CONSTANTS.Bigdata.CockroachDB.db_username
        self.db_password = CONSTANTS.Bigdata.CockroachDB.db_password
        self.aws_access_key = CONSTANTS.Bigdata.CockroachDB.aws_access_key
        self.aws_secret_key = CONSTANTS.Bigdata.CockroachDB.aws_secret_key
        self.sslrootcert = CONSTANTS.Bigdata.CockroachDB.sslrootcert
        self.sslcert = CONSTANTS.Bigdata.CockroachDB.sslcert
        self.sslkey = CONSTANTS.Bigdata.CockroachDB.sslkey
        self.access_nodes = self.tcinputs.get("access_nodes").split(",")
        self.cockroachdb_host = self.tcinputs.get("cockroachdb_host")
        self.plan_name = self.tcinputs.get("plan")
        self.cockroachdb__port = self.tcinputs.get("cockroachdb_port")
        self.use_iamrole = self.tcinputs.get("use_iamrole")
        self.use_ssl = self.tcinputs.get("use_ssl")
        self.s3_service_host = self.tcinputs.get("s3_service_host")
        self.s3_staging_path = self.tcinputs.get("s3_staging_path")
        self.sslrootcert_on_controller = self.tcinputs.get(
            "sslrootcert_on_controller")
        self.sslcert_on_controller = self.tcinputs.get(
            "sslcert_on_controller")
        self.sslkey_on_controller = self.tcinputs.get(
            "sslkey_on_controller")
        self.dbname = 'automationdb'
        self.destdbname = 'restoredb'
        self.tbname = 'automationtb'
        self.tbname2 = 'automationtb2'
        self.rowids = [1, 2, 3, 4, 5]
        self.helper = CockroachDBHelper(self)

    def run(self):
        """Run function of this testcase"""
        try:
            _desc = """
                This test case will cover CockroachDB acceptance test:
                1:  connect to cluster db, populate test data
                2:  create cockrochDB instance,
                3:  populate test data, run full backup job
                4: run restore job and validate the restore result
                5: add new table, run incremental job
                6. run restore job and validate the restore result
                7. clean up test data and test instance
            """
            self.log.info(_desc)

            self.log.info("step 1: connect to db, populate test data")
            self.connect_to_db()
            self.generate_test_data(self.dbname, self.tbname, self.rowids)

            self.log.info("step 2, create new instance")
            self.helper.add_instance()

            self.log.info("Step 3, run full backup job")
            self.helper.run_backup()

            self.log.info(
                "Step 4, run restore job and validate the restore result")
            self.run_restore_verify(
                srcdbname=self.dbname,
                destdbname=self.destdbname,
                tablename=self.tbname)

            self.log.info("Step 5, add new table, run incremental job")
            self.add_table(dbname=self.dbname, tbname=self.tbname2)
            self.update_test_data(dbname=self.dbname,
                                  tbname=self.tbname2,
                                  rowids=self.rowids)
            self.helper.run_backup()

            self.log.info(
                "Step 6, clean destination database, run restore job and validate the restore result")
            self.drop_database(self.destdbname)
            self.run_restore_verify(
                srcdbname=self.dbname,
                destdbname=self.destdbname,
                tablename=self.tbname2)

            self.log.info("Step 7, cleanup test data and test instances")
            self.helper.delete_instance()
            self.drop_database(self.dbname)
            self.drop_database(self.destdbname)
            self.close_dbconnection()

            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            self.status = constants.PASSED

        except Exception as exp:
            self.log.info(Exception)
            self.log.error('cockroachdb automation failed: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
