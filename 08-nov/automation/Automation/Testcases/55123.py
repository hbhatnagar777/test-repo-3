# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""
Install a client and verify by running backup and restore for verifying MongoDB caching

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.file_servers_helper import FileServersMain
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Install a client and verify by running backup and restore"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.fs_helper_obj = None
        self.tcinputs = {
            "client_hostname": None,
            "client_os_type": None,
            "client_username": None,
            "client_password": None,
            "client_plan": None
        }

    def setup(self):

        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.fs_helper_obj = FileServersMain(self.admin_console, self.commcell)

    def run(self):

        try:

            self.fs_helper_obj.client_hostname = self.tcinputs['client_hostname']
            self.fs_helper_obj.client_name = self.tcinputs['client_hostname']
            self.fs_helper_obj.os_type = self.tcinputs['client_os_type']
            self.fs_helper_obj.client_username = self.tcinputs['client_username']
            self.fs_helper_obj.client_password = self.tcinputs['client_password']
            self.fs_helper_obj.client_plan = self.tcinputs['client_plan']

            self.fs_helper_obj.install_new_fs_client()
            if self.admin_console._is_logout_page():
                self.admin_console.log.info("Session timed out. Logging in again.")
                self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                         self.inputJSONnode['commcell']['commcellPassword'])
            self.log.info(f"***************************{self.admin_console._is_logout_page()}")
            self.fs_helper_obj.validate_file_server_details(flag=0)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:

            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
