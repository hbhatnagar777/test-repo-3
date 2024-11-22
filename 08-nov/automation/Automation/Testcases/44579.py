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
    __init__()                  --  initialize TestCase class

    setup()                     --  Setup function of this test case

    tear_down()                 --  Tear down function for this testcase

    run()                       --  run function of this test case

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Database.MySQLUtils.mysqlhelper import MYSQLHelper


class TestCase(CVTestCase):
    """Class for executing MySQL proxy backup - Do not truncate logs on proxy test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Proxy Backup for MySQL - Do not truncate logs on proxy"
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
        self.log.info("Deleting Automation Created Tables")
        self.mysql_helper.cleanup_database_contents()


    def run(self):
        """Run function for test case execution"""

        try:
            self.mysql_helper.proxy_testcase("DO_NOT_TRUNCATE_LOGS_ON_PROXY")

        except Exception as excp:
            self.log.error('Failed with error: %s', excp)
            self.result_string = excp
            self.status = constants.FAILED
