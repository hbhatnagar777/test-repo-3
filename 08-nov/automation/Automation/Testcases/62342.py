# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  Setup function of this test case

    tear_down()                 --  Tear down function for this testcase

    run()                       --  run function of this test case

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.MySQLUtils.mysqlhelper import MYSQLHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Percona Server backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test for Percona Server backup and restore"
        self.mysql_helper = None

    def setup(self):
        """Setup function of this test case"""
        self.mysql_helper = MYSQLHelper(
            self.commcell,
            self.subclient,
            self.instance,
            self.client.client_hostname,
            self.instance.mysql_username)

    def tear_down(self):
        """Tear down function for this testcase"""
        if self.mysql_helper:
            self.log.info("Deleting Automation Created Tables")
            self.mysql_helper.cleanup_test_data(database_prefix='automation_')

    def run(self):
        """Run function for test case execution"""

        try:
            self.mysql_helper.acceptance_test_case_traditional(mysql_variant_name="Percona")

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
