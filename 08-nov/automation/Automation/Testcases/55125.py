# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""
Verifying the type filter on File Servers page

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

"""
from cvpysdk.commcell import Commcell

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.file_servers_helper import FileServersMain
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Verify File Servers page type filter works as expected"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.fs_helper_obj = None
        self.tcinputs = {

        }

    def setup(self):
        user = self.inputJSONnode['commcell']['commcellUsername'],
        pwd = self.inputJSONnode['commcell']['commcellPassword']
        if self.tcinputs.get('commcell'):
            user = self.tcinputs.get('commcell').get('username')
            pwd = self.tcinputs.get('commcell').get('password')
            hostname = self.tcinputs.get('commcell').get('hostname')
            self.commcell = Commcell(hostname, user, pwd)

        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(user, pwd)

        self.fs_helper_obj = FileServersMain(self.admin_console, self.commcell)

    def run(self):

        try:

            self.fs_helper_obj.validate_type_filter()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:

            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
