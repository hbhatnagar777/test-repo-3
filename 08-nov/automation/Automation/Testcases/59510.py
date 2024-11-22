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

    setup()         --  initial settings for the test case

    init_tc()       --  initialize browser and redirect to required page

    run()           --  run function of this test case


    Input Example:

    "testCases": {

		"59510": {
			"gateway_node": "",
			"cql_host": "",
			"cql_port": "",
			"jmx_port: "",
			"plan": "",
			"config_file_path": "",
			"staging_path": "",
		}
    }
"""

from Reports.utils import TestCaseUtils

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.cassandra_helper import Cassandra


CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """
    TestCase to validate instance creation, backup and restore for clusters with
    non-default cql/jmx port
    """

    def __init__(self):
        """Initialize TestCase class"""
        super(TestCase, self).__init__()
        self.name = "Backup and restore for cluster with non-default cql/jmx port"
        self.browser = None
        self.admin_console = None
        self.cassandra_server_name = None
        self.cql_username = None
        self.cql_password = None
        self.jmx_username = None
        self.jmx_password = None
        self.ssl_keystore = None
        self.ssl_keystorepwd = None
        self.ssl_truststore = None
        self.ssl_truststorepwd = None
        self.keyspace = None
        self.tablename = None
        self.rows = []
        self.cassandra = None
        self.tcinputs = {
            "gateway_node": None,
            "cql_host": None,
            "cql_port": None,
            "jmx_port": None,
            "plan": None,
            "config_file_path": None,
            "staging_path": None
        }

    def setup(self):
        """Initializes object required for this testcase"""
        self.cassandra_server_name = "automated_cassandra_server_59510"
        self.utils = TestCaseUtils(self)
        self.cql_username = CONSTANTS.Bigdata.Cassandra.cql_username
        self.cql_password = CONSTANTS.Bigdata.Cassandra.cql_password
        self.jmx_username = CONSTANTS.Bigdata.Cassandra.jmx_username
        self.jmx_password = CONSTANTS.Bigdata.Cassandra.jmx_password
        self.ssl_keystore = CONSTANTS.Bigdata.Cassandra.ssl_keystore
        self.ssl_keystorepwd = CONSTANTS.Bigdata.Cassandra.ssl_keystorepwd
        self.ssl_truststore = CONSTANTS.Bigdata.Cassandra.ssl_truststore
        self.ssl_truststorepwd = CONSTANTS.Bigdata.Cassandra.ssl_truststorepwd
        self.destinationinstance = self.cassandra_server_name + \
            "/" + self.cassandra_server_name
        self.keyspace = 'automationks59510'
        self.tablename = 'automationtb'
        self.rows = [1, 2, 3, 4, 5]

    def init_tc(self):
        """Initialize browser and redirect to required report page"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login()
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def run(self):
        """Run function of this testcase"""
        try:
            self.init_tc()
            self.cassandra = Cassandra(self.admin_console, self)
            self.cassandra.create_cassandra_instance()

            # connect to cql host
            self.cassandra.connect_to_db()

            # create test data, run backup
            self.cassandra.generate_test_data(
                self.keyspace, self.tablename, self.rows)
            self.cassandra.verify_backup()

            # db view stage free restore
            self.cassandra.drop_table(self.keyspace, self.tablename)
            self.cassandra.verify_restore(
                destinstance=self.destinationinstance, paths=[
                    self.keyspace], stagefree=True)
            self.cassandra.validate_restoredata(
                self.keyspace, self.tablename, self.rows)

            # db view restore without sstableloader
            self.cassandra.drop_table_inplacerestore(
                destinstance=self.destinationinstance,
                paths=[
                    self.keyspace],
                keyspace=self.keyspace,
                tablename=self.tablename,
                rows=self.rows)

            # discovery nodes and save
            self.cassandra.discover_node()

            # cluster view restore with sstableloader tool
            self.cassandra.drop_keyspace_clusterview_inplacerestore_sstableloader(
                destinstance=self.destinationinstance, paths=[
                    self.keyspace], keyspace=self.keyspace, tablename=self.tablename, rows=self.rows)

            # clean up test data, close DB connection and delete pseudo client
            self.cassandra.drop_keyspace(self.keyspace)
            self.cassandra.close_dbconnection()
            self.cassandra.delete_cassandra_instance()

        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            Browser.close_silently(self.browser)
