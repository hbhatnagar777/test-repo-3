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

    run()           --  Main function for test case execution

"""
import ast
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.PostgreSQL.PostgresUtils import pgsqlhelper

class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of PostgreSQL
    BLOCK level incremental backup and PIT Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "ACCT1- PostgreSQL Block level Point In Time"
        self.tcinputs = {
            'TestDataSize': None
        }

    def run(self):
        """Main function for test case execution"""

        try:
            if isinstance(self.tcinputs['TestDataSize'], str):
                self.tcinputs['TestDataSize'] = ast.literal_eval(self.tcinputs['TestDataSize'])
            self.log.info("Started executing %s testcase", self.id)

            self.log.info("Checking if the intelliSnap is enabled on subclient or not")
            if not self.subclient.is_intelli_snap_enabled:
                raise Exception("Intellisnap is not enabled for subclient")
            self.log.info("IntelliSnap is enabled on subclient")

            self.log.info("Checking if the Block level backup is enabled on subclient or not")
            if not self.subclient.is_blocklevel_backup_enabled:
                raise Exception("Block level backup is not enabled for subclient")
            self.log.info("Block level backup is enabled on subclient")

            postgres_helper_object = pgsqlhelper.PostgresHelper(
                self.commcell, self.client, self.instance)

            postgres_helper_object.blocklevel_backup_restore(
                self.subclient,
                self.tcinputs['TestDataSize'],
                tc_type="POINT_IN_TIME")

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = str(excp)
            self.status = constants.FAILED
