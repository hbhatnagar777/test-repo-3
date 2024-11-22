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
		"64494": {
            "access_nodes": [],
            "plan_name": None,
            "yugabytedb_host": None,
            "node_ip": None,
            "api_token": None,
            "universe_name": None,
            "storage_config": None,
            "credential": None,
            "kms_config": None
		}
    }
"""

from Reports.utils import TestCaseUtils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.yugabytedb_helper import YugabyteDB
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep
CONSTANTS = config.get_config()
class TestCase(CVTestCase):
    """
    TestCase to validate instance creation, backup and restore for yugabyteDB cluster
    """
    test_step = TestStep()
    def __init__(self):
        """Initialize TestCase class"""
        super(TestCase, self).__init__()
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
        self.name = "Acceptance test for YugabytedbDB"
        self.browser = None
        self.admin_console = None
        self.yugabytedb_server_name = None
        self.yugabytedb = None
        self.tcinputs = {
            "access_nodes": [],
            "plan_name": None,
            "yugabytedb_host": None,
            "node_ip": None,
            "api_token": None,
            "universe_name": None,
            "storage_config": None,
            "credential": None,
            "kms_config": None
        }
    def setup(self):
        """Initializes object required for this testcase"""
        self.yugabytedb_server_name = "automated_yugabyteDB_64494"
        self.utils = TestCaseUtils(self)
        self.ysql_username = CONSTANTS.Bigdata.YugabyteDB.ysql_username
        self.ysql_password = CONSTANTS.Bigdata.YugabyteDB.ysql_password
        self.ycql_username = CONSTANTS.Bigdata.YugabyteDB.ycql_username
        self.ycql_password = CONSTANTS.Bigdata.YugabyteDB.ycql_password
        self.sslrootcert = CONSTANTS.Bigdata.YugabyteDB.sslrootcert
        self.sqldbname = 'ybautosqldb'
        self.cqldbname = 'ybautocqldb'
        self.destsqldbname = 'ybautosqldb_oopauto'
        self.destcqldbname = 'ybautocqldb_oopauto'
        self.tbname = 'ybautomationtb'
        self.tbname2 = 'ybautomationtb2'
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
            self.init_tc()
            self.yugabytedb = YugabyteDB(self.admin_console, self)
            self.yugabytedb.connect_to_db()
            # populate test data, run full job from instance actions
            self.yugabytedb.populate_test_data(self.sqldbname, self.cqldbname, self.tbname, self.rowids)
            self.yugabytedb.create_yugabytedb_instance()
            self.yugabytedb.backup_from_instance_action(backuptype="FULL")
            # run another full backup after a full job
            self.yugabytedb.backup_from_instance_action(backuptype="FULL")
            self.yugabytedb.drop_db_restore_from_instance_action(
                srcsqldbname=self.sqldbname,
                srccqldbname=self.cqldbname,
                tbname=self.tbname)
            self.yugabytedb.restore_to_newdb_from_instance_action(
                srcsqldbname=self.sqldbname,
                srccqldbname=self.cqldbname,
                tbname=self.tbname)
            # add more data and run incremental job and restore from instance details
            self.yugabytedb.update_test_data(srcsqldbname=self.sqldbname,
                                            srccqldbname=self.cqldbname,
                                              tbname=self.tbname,
                                              rowids=[6, 7])
            self.yugabytedb.backup_from_instance_overview()
            self.yugabytedb.restore_to_newdb_from_instance_RPC(
                srcsqldbname=self.sqldbname,
                srccqldbname=self.cqldbname,
                tbname=self.tbname)
            # delete some data and run incremental job and restore from namespace group actions
            self.yugabytedb.update_test_data(srcsqldbname=self.sqldbname,
                                            srccqldbname=self.cqldbname,
                                              tbname=self.tbname,
                                              rowids=[6, 7],
                                              deletedata=True)
            self.yugabytedb.backup_from_namespacegroup_action()
            self.yugabytedb.restore_to_newdb_from_namespacegroup_actions(
                srcsqldbname=self.sqldbname,
                srccqldbname=self.cqldbname,
                tbname=self.tbname)
            # add new table, and run incremental job from namespace group actions restore from namespace group actions
            self.yugabytedb.populate_test_data(self.sqldbname, self.cqldbname,
                                                tbname=self.tbname2,
                                                rowids=self.rowids,
                                                clean_data=False)
            self.yugabytedb.backup_from_namespacegroup_action()
            self.yugabytedb.new_table_restore_from_namespacegroup_actions(
                srcsqldbname=self.sqldbname,
                srccqldbname=self.cqldbname,
                tbname=self.tbname,
                tbname2=self.tbname2)
            # delete instance, clean up test data and close DB connection
            self.yugabytedb.delete_yugabytedb_instance()
            self.yugabytedb.drop_table(self.sqldbname, self.cqldbname, self.tbname2)
            self.yugabytedb.drop_database(self.sqldbname, self.cqldbname, self.tbname)
            self.yugabytedb.drop_database(self.destsqldbname, self.destcqldbname, self.tbname)
            self.yugabytedb.close_dbconnection()
        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            Browser.close_silently(self.browser)
