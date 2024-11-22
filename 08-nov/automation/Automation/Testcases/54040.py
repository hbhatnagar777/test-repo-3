# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------
"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.Helper.LoginHelper import LoginMain
from Web.AdminConsole.Helper.file_servers_helper import FileServersMain
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """ basic acceptance test case for file servers page """

    def __init__(self):
        """Initializing the Test case file """
        super(TestCase, self).__init__()
        self.name = "Admin console File servers Acceptance"
        self.factory = None
        self.browser = None
        self.driver = None
        self.login_obj = None
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.file_servers_obj = None

        self.tcinputs = {
            'client_name': None,
            'backupset_name': None,
            'subclient_name': None,
            'backup_level': None,
            'restore_file': None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.factory = BrowserFactory()
        self.browser = self.factory.create_browser_object()
        self.browser.open()
        self.driver = self.browser.driver
        self.log.info("Creating the self.login object")
        self.login_obj = LoginMain(self.driver, self.csdb)
        self.login_obj.login(self.inputJSONnode['commcell']['commcellUsername'],
                             self.inputJSONnode['commcell']['commcellPassword']
                             )
        self.file_servers_obj = FileServersMain(self)

    def run(self):
        try:
            self.file_servers_obj.set_server_details(self.tcinputs['client_name'], self.tcinputs['backupset_name'],
                                                     self.tcinputs['subclient_name'])
            self.file_servers_obj.file_server_action_check_readiness()
            self.log.info(" Successfully executed the check readiness operation from the client")

            self.file_servers_obj.file_server_action_backup_subclient(self.tcinputs['backup_level'])
            self.log.info("Successfully executed the backup operation from the client")

            self.file_servers_obj.file_server_action_restore(self.tcinputs['restore_file'])
            self.log.info("Successfully executed the Restore operation from the client")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """To clean-up the test case environment created"""
        self.browser.close()
