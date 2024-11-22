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

		"62095": {
			"gateway_node": "",
			"cql_host": "",
			"cql_port": "",
			"jmx_port": "",
			"plan": "",
			"config_file_path": "",
			"staging_path": "",
			"archive_path": "",
			"archive_command": ""
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
    """TestCase to validate enable, configure, backup and restore commit logs from admin console - Cassandra"""

    def __init__(self):
        """Initialize TestCase class"""
        super(TestCase, self).__init__()
        self.name = "commit log backup and restores from admin console - Cassandra"
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
        self.rows = 0
        self.cassandra = None
        self.tcinputs = {
            "gateway_node": None,
            "cql_host": None,
            "cql_port": None,
            "jmx_port": None,
            "plan": None,
            "config_file_path": None,
            "staging_path": None,
            "archive_path": None,
            "archive_command": None
        }

    def setup(self):
        """Initializes object required for this testcase"""
        self.cassandra_server_name = "automated_cassandra_server"
        self.utils = TestCaseUtils(self)
        self.cql_username = CONSTANTS.Bigdata.Cassandra.cql_username
        self.cql_password = CONSTANTS.Bigdata.Cassandra.cql_password
        self.jmx_username = CONSTANTS.Bigdata.Cassandra.jmx_username
        self.jmx_password = CONSTANTS.Bigdata.Cassandra.jmx_password
        self.ssl_keystore = CONSTANTS.Bigdata.Cassandra.ssl_keystore
        self.ssl_keystorepwd = CONSTANTS.Bigdata.Cassandra.ssl_keystorepwd
        self.ssl_truststore = CONSTANTS.Bigdata.Cassandra.ssl_truststore
        self.ssl_truststorepwd = CONSTANTS.Bigdata.Cassandra.ssl_truststorepwd
        self.keyspace = 'automationks'
        self.tablename = 'automationtb'
        self.rows = 10

    def init_tc(self):
        """Initialize browser and redirect to required page"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login()
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def run(self):
        """Run function of this test case"""
        try:
            self.init_tc()
            self.cassandra = Cassandra(self.admin_console, self)
            self.cassandra.create_cassandra_instance()
            self.cassandra.discover_node()
            self.cassandra.enable_commitlogs()
            #connect to cql host
            self.cassandra.connect_to_db()

            # create test data, run backup
            self.cassandra.generate_test_data(
                self.keyspace, self.tablename, self.rows)
            self.cassandra.verify_backup()
            self.cassandra.verify_log_backup()

            # drop keyspace, restore data and logs in keyspace view, then validate restored data
            self.cassandra.drop_keyspace(self.keyspace)
            self.cassandra.verify_restore(stagefree=False, sstableloader=False, clusterview=False, restorelogs=True)
            self.cassandra.validate_restoredata(
                self.keyspace, self.tablename, self.rows)

            # drop table, restore data and logs in keyspace view, then validate restored data
            self.cassandra.drop_table(self.keyspace, self.tablename)
            self.cassandra.verify_restore(stagefree=False, sstableloader=False, clusterview=False, restorelogs=True)
            self.cassandra.validate_restoredata(
                self.keyspace, self.tablename, self.rows)

            # drop keyspace, restore data and logs in cluster view, then validate restored data
            self.cassandra.drop_keyspace(self.keyspace)
            self.cassandra.verify_restore(stagefree=False, sstableloader=False, clusterview=True, restorelogs=True)
            self.cassandra.validate_restoredata(
                self.keyspace, self.tablename, self.rows)

            # drop table, restore data and logs in cluster view, then validate restored data
            self.cassandra.drop_table(self.keyspace, self.tablename)
            self.cassandra.verify_restore(stagefree=False, sstableloader=False, clusterview=True, restorelogs=True)
            self.cassandra.validate_restoredata(
                self.keyspace, self.tablename, self.rows)

            # clean up the test data, shutdown DB connection and delete the cassandra
            # pseudo client
            self.cassandra.drop_keyspace(self.keyspace)
            self.cassandra.close_dbconnection()
            self.cassandra.delete_cassandra_instance()

        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            Browser.close_silently(self.browser)
