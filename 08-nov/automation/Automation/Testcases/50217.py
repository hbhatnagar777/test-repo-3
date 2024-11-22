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

    setup()         --  Setup function for this testcase

    tear_down()     --  Tear down function to delete automation generated data

    run()           --  Main function for test case execution

"""
from AutomationUtils import constants
from AutomationUtils import machine
from AutomationUtils.cvtestcase import CVTestCase
from Database.MySQLUtils.mysqlhelper import MYSQLHelper

class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of MySQL
    BLOCK level Synthfull backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "ACCT1- MySQL Block level Synthetic Full"
        self.mysql_helper_object = None
        self.machine_object = None
        self.tcinputs = {
            'MySQLPortNumber': None
        }
        self.port = None

    def setup(self):
        """setup function for this testcase"""
        self.port = int(self.tcinputs['MySQLPortNumber'])
        # Creating MYSQLHelper Object
        self.log.info("Create MYSQLHelper class object")
        self.mysql_helper_object = MYSQLHelper(
            self.commcell,
            self.subclient,
            self.instance,
            self.client.client_hostname,
            self.instance.mysql_username,
            self.port)
        self.machine_object = machine.Machine(self.client)

    def tear_down(self):
        """tear down function to delete automation generated data"""
        self.log.info("Deleting Automation Created databases")
        self.mysql_helper_object.cleanup_test_data("automation")

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)
            self.mysql_helper_object.snap_prerequirement_check()
            self.mysql_helper_object.snap_blocklevel_testcase(testcase_type="SYNTH_FULL")


        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
