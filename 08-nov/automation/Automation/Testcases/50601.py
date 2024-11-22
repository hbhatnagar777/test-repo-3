# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  Initializes test case class object

    setup()             --  setup method for this testcase

    tear_down()         --  Tear down function

    run()           --  Main function for test case execution

"""
import ast
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper

class TestCase(CVTestCase):
    """Class for executing PostgreSQL BLB backup and Restore with proxy test case """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "PostgreSQL SNAP backup and Restore with proxy"
        self.tcinputs = {
            'TestDataSize': None,
            'ProxyClient': None
        }
        self.postgres_helper_object = None
        self.postgres_server_user_password = None

    def setup(self):
        """ setup method for this testcase """
        self.postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.client, self.instance)
        self.postgres_server_user_password = self.postgres_helper_object.postgres_password
        if isinstance(self.tcinputs['TestDataSize'], str):
            self.tcinputs['TestDataSize'] = ast.literal_eval(self.tcinputs['TestDataSize'])

    def tear_down(self):
        """Tear down function"""
        self.log.info("Deleting Automation Created databases")
        self.postgres_helper_object.cleanup_tc_db(
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_server_user_password,
            "auto")
        self.log.info("Unsetting proxy")
        self.subclient.unset_proxy_for_snap()

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)

            self.log.info("Checking if the intelliSnap is enabled on subclient or not")
            if not self.subclient.is_intelli_snap_enabled:
                raise Exception("Intellisnap is not enabled for subclient")
            self.log.info("IntelliSnap is enabled on subclient")

            self.log.info("Checking if the Block level backup is enabled on subclient or not")
            if not self.subclient.is_blocklevel_backup_enabled:
                raise Exception("Block level backup is not enabled for subclient")
            self.log.info("Block level backup is enabled on subclient")
            self.log.info("Setting proxy")
            self.subclient.set_proxy_for_snap(self.tcinputs['ProxyClient'])

            self.postgres_helper_object.blocklevel_backup_restore(
                self.subclient,
                self.tcinputs['TestDataSize'],
                proxy_client=self.tcinputs['ProxyClient'])

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
