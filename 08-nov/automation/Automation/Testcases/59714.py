# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  Initializes test case class object

    setup()         --  setup method for testcase

    tear_down()     --  tear down function to delete automation generated data

    run()           --  Main function for test case execution

"""
import ast
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper

class TestCase(CVTestCase):
    """Class for executing PGSQL index reconstruction testcase for block level V1 client"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "PGSQL- Index reconstruction testcase for block level V1 client"
        self.tcinputs = {
            'TestDataSize': None
        }
        self.postgres_helper_object = None

    def setup(self):
        """ setup method for testcase """
        self.postgres_helper_object = pgsqlhelper.PostgresHelper(
            self.commcell, self.client, self.instance)
        if isinstance(self.tcinputs['TestDataSize'], str):
            self.tcinputs['TestDataSize'] = ast.literal_eval(self.tcinputs['TestDataSize'])

    def tear_down(self):
        """tear down function to delete automation generated data"""
        self.log.info("Deleting Automation Created databases")
        self.postgres_helper_object.cleanup_tc_db(
            self.client.client_hostname,
            self.instance.postgres_server_port_number,
            self.instance.postgres_server_user_name,
            self.postgres_helper_object._postgres_db_password,
            "auto")

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

            if self.postgres_helper_object.is_index_v2_postgres:
                raise Exception("This testcase requires the client to be Indexing V1")

            self.postgres_helper_object.blocklevel_backup_restore(
                self.subclient,
                self.tcinputs['TestDataSize'],
                tc_type='INDEX_DELETE_BLB')


        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
