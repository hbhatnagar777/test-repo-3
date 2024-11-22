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
from AutomationUtils.cvtestcase import CVTestCase
from Database.MySQLUtils.mysqlhelper import MYSQLHelper

class TestCase(CVTestCase):
    """Class for executing MySQL SNAP Redirect restore to
    different instance in the same client testcase"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()

        self.name = "MySQL SNAP Redirect restore to different instance in the same client"
        self.mysql_helper_object = None
        self.tcinputs = {
            'DestinationInstance': None
        }

    def setup(self):
        """setup function for this testcase"""
        # Creating MYSQLHelper Object
        self.log.info("Creating MYSQLHelper class object")
        self.mysql_helper_object = MYSQLHelper(
            self.commcell,
            self.subclient,
            self.instance,
            self.client.client_hostname,
            self.instance.mysql_username)

    def tear_down(self):
        """tear down function to delete automation generated data"""
        self.log.info("Deleting Automation Created databases")
        self.mysql_helper_object.cleanup_test_data("automation")

    def run(self):
        """Main function for test case execution"""

        try:
            destination_instance = self.agent.instances.get(
                self.tcinputs['DestinationInstance'])
            self.mysql_helper_object.blocklevel_redirect_restore(
                destination_instance=destination_instance,
                is_blocklevel=False)

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
