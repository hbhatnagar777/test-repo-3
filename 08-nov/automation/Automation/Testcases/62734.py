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

    __init__()      --   initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.ServerHelper import ServerHelper
from Web.AdminConsole.Components.table import Rfilter
from Web.Common.cvbrowser import BrowserFactory


class TestCase(CVTestCase):
    """ basic acceptance test case for view logs """

    def __init__(self):
        """Initializing the Test case file """
        super(TestCase, self).__init__()
        self.name = "Functional test cases for command center -view logs option"
        self.factory = None
        self.browser = None
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.clientname = None
        self.logstoverify = None
        self.admin_console = None
        self.server_helper = None
        self.tcinputs = {
            'client_name': None,
            'logstoverify':None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.clientname  = self.tcinputs['client_name']
        self.logstoverify = self.tcinputs['logstoverify'].split(",")
        self.factory = BrowserFactory()
        self.browser = self.factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
    
    def run(self):
        try:
            self.server_helper = ServerHelper(admin_console= self.admin_console)       
            viewlogspanel = self.server_helper.view_logs(self.clientname )
            self.server_helper.validate_viewlogs([self.logstoverify[0]],viewlogspanel)
            self.server_helper.view_logs(self.clientname )
            self.server_helper.validate_viewlogs(self.logstoverify,viewlogspanel)
            self.server_helper.view_logs(self.clientname )
            self.server_helper.viewlogs_add_filter_validate(
                'Name',self.logstoverify[0].replace(".log",""),Rfilter.contains,viewlogspanel)
            self.log.info("Successfully completed test case execution")

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """To clean-up the test case environment created"""
        self.browser.close()
