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
		"64404": {
            "access_nodes": [],
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

from Reports.utils import TestCaseUtils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.cockroachdb_helper import CockroachDB
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep

CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """
    TestCase to validate instance creation, backup and restore for CockroachDB cluster
    """

    test_step = TestStep()

    def __init__(self):
        """Initialize TestCase class"""
        super(TestCase, self).__init__()
        self.name = "Acceptance test for CockroachDB"
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
            "access_nodes": [],
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

    def setup(self):
        """Initializes object required for this testcase"""
        self.cockroachdb_name = "automated_cockroachDB_64404"
        self.utils = TestCaseUtils(self)
        self.db_username = CONSTANTS.Bigdata.CockroachDB.db_username
        self.db_password = CONSTANTS.Bigdata.CockroachDB.db_password
        self.aws_access_key = CONSTANTS.Bigdata.CockroachDB.aws_access_key
        self.aws_secret_key = CONSTANTS.Bigdata.CockroachDB.aws_secret_key
        self.sslrootcert = CONSTANTS.Bigdata.CockroachDB.sslrootcert
        self.sslcert = CONSTANTS.Bigdata.CockroachDB.sslcert
        self.sslkey = CONSTANTS.Bigdata.CockroachDB.sslkey
        self.dbname = 'automationdb'
        self.destdbname = 'restoredb'
        self.tbname = 'automationtb'
        self.tbname2 = 'automationtb2'
        self.rowids = [1, 2, 3, 4, 5]

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
            _desc = """
                This test case will cover CockroachDB acceptance test:
                1: delete existing instance if exist
                2: create cockrochDB instance,
                3: connect to cockroachDB cluster and populate test data
                4: Run full backup job from instance actions
                5. drop source database, verify in place database restore from instance actions
                6. drop source database, verify in place table restore from instance actions
                7. add more data, run incremental backup job from instance details
                8. drop source table, run in place db restore from instance details RPC
                9. drop source table, run in place table restore from instance details RPC
                10. delete some data, run incremental job from tablegroup actions
                11. truncate source table, run in place db restore from table group actions
                12. truncate source table, run in place table rsetore from table group actions
                13. add new table, run incremental job from table group actions
                14. truncate destination table if exist, run out of place db restore from table group RPC
                15: delete test instances
                16: cleanup test data, drop db connections
            """
            self.log.info(_desc)

            self.init_tc()
            self.cockroachdb = CockroachDB(self.admin_console, self)
            self.cockroachdb.create_cockroachdb_instance()
            self.cockroachdb.connect_to_db()

            # populate test data, run full job from instance actions
            self.cockroachdb.populate_test_data(
                self.dbname, self.tbname, self.rowids)
            self.cockroachdb.backup_from_instance_action(backuptype="FULL")
            self.cockroachdb.in_place_db_restore_from_instance_action(
                srcdbname=self.dbname,
                tbname=self.tbname)

            self.cockroachdb.in_place_tb_restore_from_instance_action(
                srcdbname=self.dbname,
                tbname=self.tbname)

            # add more data and run incremental job from instance details
            self.cockroachdb.update_test_data(dbname=self.dbname,
                                              tbname=self.tbname,
                                              rowids=[6, 7])
            self.cockroachdb.backup_from_instance_overview()
            self.cockroachdb.in_place_db_restore_from_instance_RPC(
                srcdbname=self.dbname,
                tbname=self.tbname)

            self.cockroachdb.in_place_table_restore_from_instance_RPC(
                srcdbname=self.dbname,
                tbname=self.tbname)

            # delete some data and run incremental job from table group actions
            self.cockroachdb.update_test_data(dbname=self.dbname,
                                              tbname=self.tbname,
                                              rowids=[6, 7],
                                              deletedata=True)
            self.cockroachdb.backup_from_tablegroup_action()
            self.cockroachdb.in_place_db_restore_from_tablegroup_actions(
                srcdbname=self.dbname,
                tbname=self.tbname)
            self.cockroachdb.in_place_table_restore_from_tablegroup_actions(
                srcdbname=self.dbname,
                tbname=self.tbname)

            # add new table, and run incremental job from table group actions
            self.cockroachdb.populate_test_data(dbname=self.dbname,
                                                tbname=self.tbname2,
                                                rowids=self.rowids)
            self.cockroachdb.backup_from_tablegroup_action()

            self.cockroachdb.out_of_place_db_restore_from_tablegroup_actions(
                srcdbname=self.dbname,
                tbname=self.tbname2,
                destdbname=self.destdbname)

            # delete instance, clean up test data and close DB connection
            self.cockroachdb.delete_cockroachdb_instance()
            self.cockroachdb.drop_database(self.dbname)
            self.cockroachdb.drop_database(self.destdbname)
            self.cockroachdb.close_dbconnection()

        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            Browser.close_silently(self.browser)
