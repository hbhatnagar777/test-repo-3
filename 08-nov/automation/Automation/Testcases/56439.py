# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""
Command Center : Managing entities from the Global search bar

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.global_search_helper import GlobalSearchHelper
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing managing entities from global search test case"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Command Center : Managing entities from the Global search bar"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.fs_helper_obj = None
        self.tcinputs = {
            "file_server": None,
            "hypervisor": None,
            "server_group": None,
            "user": None,
            "user_group": None,
            "virtual_machine": None,
            "vm_group": None
        }

    def setup(self):
        """Setup function of this test case"""

        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.global_search = GlobalSearchHelper(self.admin_console)

    def run(self):
        """Main function for test case execution"""

        try:
            self.global_search.verify_fs_hypervisor_actions(self.tcinputs['file_server'], 0)
            self.global_search.verify_fs_hypervisor_actions(self.tcinputs['hypervisor'], 1)
            self.global_search.verify_server_group_actions(self.tcinputs['server_group'])
            self.global_search.verify_user_actions(self.tcinputs['user'])
            self.global_search.verify_user_group_actions(self.tcinputs['user_group'])
            self.global_search.verify_vm_actions(self.tcinputs['virtual_machine'])
            self.global_search.verify_vm_group_actions(self.tcinputs['vm_group'])

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:

            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
