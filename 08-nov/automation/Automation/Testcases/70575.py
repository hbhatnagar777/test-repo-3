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

    connect_to_db()                    -- connect to cockroachdb cluster

    generate_test_data()               -- To generate the test database and tables

    drop_keyspace()                    -- drop keyspace

    drop_table()                       -- drop table

    validate_restoredata()             -- validate the restored data

    close_dbconnection()               -- close db connection

    setup()         --  initial settings for the test case

    init_tc()       --  initialize browser and redirect to required page

    run()           --  run function of this test case


    Input Example:

    "testCases": {

		"70575": {
			"gateway_node": "",
			"cql_host": "",
			"cql_port": "",
			"plan": "",
			"config_file_path": "",
			"staging_path": "",
		}
    }
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config, logger, constants
from BigDataApps.CassandraUtils.cassandrahelper import CassandraHelper
from Web.AdminConsole.Helper.cassandra_helper import CassandraHelper as CHelper

CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """TestCase to validate cassandra instance creation/backup/restore using restapi"""

    def __init__(self):
        """Initialize TestCase class"""
        super(TestCase, self).__init__()
        self.name = "Instance creation using restapi - Cassandra"
        self.cassandra_server_name = "automated_cassandra_server_70575"
        self.cql_username = None
        self.cql_password = None
        self.cql_port = None
        self.jmx_username = None
        self.jmx_password = None
        self.jmx_port = None
        self.ssl_keystore = None
        self.ssl_keystorepwd = None
        self.ssl_truststore = None
        self.ssl_truststorepwd = None
        self.keyspace = None
        self.tablename = None
        self.rows = []
        self.cassandra = None
        self.helper = None
        self.tcinputs = {
            "gateway_node": None,
            "cql_host": None,
            "cql_port": None,
            "plan": None,
            "config_file_path": None,
            "staging_path": None
        }

    def connect_to_db(self, ssl_enabled=False):
        """initiate connection to cassandra cql host"""
        self.__cassandra = CHelper(self.cql_host,
                                   self.cql_username,
                                   self.cql_password,
                                   self.cql_port,
                                   ssl_enabled=ssl_enabled)

    def generate_test_data(self, keyspace, tablename, rows, clean_data=True):
        """generate test data
        Args:
            keyspace (str)     -- keyspace name
            table (str)        -- table name
            rows []            -- list of row ids
        """
        if clean_data:
            try:
                self.drop_keyspace(keyspace)
            except BaseException:
                pass
            self.__cassandra.createkeyspace(keyspace)
            self.__cassandra.createtable(keyspace, tablename)
        self.__cassandra.populate_test_data(keyspace, tablename, rows)

    def drop_keyspace(self, keyspace):
        """drop keyspace
        Args
            keyspace (str)     -- keyspace name
        """
        self.__cassandra.dropkeyspace(keyspace)

    def drop_table(self, keyspace, table):
        """drop table
        Args
            keyspace (str)     -- keyspace name
            table (str)        -- table name
        """
        self.__cassandra.droptable(keyspace, table)

    def truncate_table(self, keyspace, table):
        """truncate table
        Args
            keyspace (str)     -- keyspace name
            table (str)        -- table name
        """
        self.__cassandra.truncatetable(keyspace, table)

    def validate_restoredata(self, keyspace, table, rows):
        """"validate restore data in DB
        Args:
            keyspace (str)     -- keyspace name
            table (str)        -- table name
            rows []            --  list of row ids

            Raises:
                Exceptions if populating test data failed
        """
        results = self.__cassandra.get_rows(keyspace, table)
        count = 0
        for result in results:
            count += 1
            if (result.id not in rows) or (
                    result.fname != 'test') or (result.lname != 'test'):
                raise BaseException(
                    "restored data does not match with original data")
        if count == len(rows):
            self.log.info("restored data match original data")
        else:
            raise BaseException(
                "number of rows in restored data does not match original data")

    def close_dbconnection(self):
        """close cassandra cluster connection"""
        self.__cassandra.close_connection()

    def setup(self):
        """Initializes object required for this testcase"""
        self.log = logger.get_log()
        self.cql_host = self.tcinputs.get("cql_host")
        self.config_file_path = self.tcinputs.get("config_file_path")
        self.cql_username = CONSTANTS.Bigdata.Cassandra.cql_username
        self.cql_password = CONSTANTS.Bigdata.Cassandra.cql_password
        self.cql_port = self.tcinputs.get("cql_port")
        self.jmx_username = CONSTANTS.Bigdata.Cassandra.jmx_username
        self.jmx_password = CONSTANTS.Bigdata.Cassandra.jmx_password
        self.jmx_port = self.tcinputs.get("jmx_port")
        self.ssl_keystore = CONSTANTS.Bigdata.Cassandra.ssl_keystore
        self.ssl_keystorepwd = CONSTANTS.Bigdata.Cassandra.ssl_keystorepwd
        self.ssl_truststore = CONSTANTS.Bigdata.Cassandra.ssl_truststore
        self.ssl_truststorepwd = CONSTANTS.Bigdata.Cassandra.ssl_truststorepwd
        self.destinationinstance = self.cassandra_server_name + \
            "/" + self.cassandra_server_name
        self.keyspace = 'automationks70575'
        self.tablename = 'automationtb'
        self.keyspace2 = 'automationks705752'
        self.tablename2 = 'automationtb2'
        self.rows = [1, 2, 3, 4, 5]
        self.helper = CassandraHelper(self)

    def run(self):
        """Run function of this testcase"""
        try:
            _desc = """
                This test case will cover Cassandra acceptance test:
                1: connect to db, populate test data
                2: delete existing instance if exist, add new cassandra instance
                3: run full backup
                4: drop keyspace, run restore job and validate the restore result
                5: update data, run inc job
                6. drop keyspace, run restore job and validate the restore result
                7: cleanup test data, drop db connections, delete instance
            """
            self.log.info(_desc)

            self.log.info("step 1: connect to db, populate test data")
            self.connect_to_db()
            self.generate_test_data(
                self.keyspace, self.tablename, self.rows)

            self.log.info("step 2: add cassandra instance")
            self.helper.add_instance()

            self.log.info("Step 3, run full backup job")
            self.helper.run_backup(backup_level="FULL")

            self.log.info(
                "Step 4, drop keyspace, run restore job and validate the restore result")
            self.drop_keyspace(self.keyspace)
            self.helper.run_restore(keyspacename=self.keyspace)
            self.validate_restoredata(
                keyspace=self.keyspace,
                table=self.tablename,
                rows=self.rows)

            self.log.info("Step 5, add new keyspace, run incremental job")
            self.generate_test_data(self.keyspace2, self.tablename, self.rows)
            self.helper.run_backup()

            self.log.info(
                "Step 6, drop keyspace, run restore job and validate the restore result")
            self.drop_keyspace(self.keyspace2)
            self.helper.run_restore(keyspacename=self.keyspace2)
            self.validate_restoredata(
                keyspace=self.keyspace2,
                table=self.tablename,
                rows=self.rows)

            self.log.info("Step 7, cleanup test data and test instances")
            self.helper.delete_instance()
            self.drop_keyspace(self.keyspace)
            self.drop_keyspace(self.keyspace2)
            self.close_dbconnection()

            self.log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
            self.status = constants.PASSED

        except Exception as exp:
            self.log.info(Exception)
            self.log.error('cassandra automation failed: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
