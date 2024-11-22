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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.syslog import Syslog
from Web.Common.page_object import handle_testcase_exception

class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test for Events test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Test Case to verify proper working of Events page filters"
        self.browser = None
        self.admin_console = None
        self.syslog_obj = None
        self.tcinputs = {
            "hostname": None,
            "port": None,
            "forward-entities": None
        }

    def setup(self):
        """Setup function of this test case"""
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.syslog_obj = Syslog(self.admin_console)

    def run(self):
        """Main function for test case execution"""
        try:
            self.syslog_obj.navigate_to_syslog()
            self.syslog_obj.add_syslog(self.tcinputs['hostname'], self.tcinputs['port'],
                                       self.tcinputs['forward-entities'])
            self.syslog_obj.validate_syslog_configuration(self.tcinputs['hostname'], self.tcinputs['port'],
                                                          self.tcinputs['forward-entities'])
            self.syslog_obj.disable_syslog()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """ To clean-up the test case environment created """
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
