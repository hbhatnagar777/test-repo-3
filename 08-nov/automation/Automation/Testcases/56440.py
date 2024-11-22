# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""
Command Center : Adding entities from the Global search bar

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.panel import ModalPanel
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing adding entities from global search test case"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Command Center : Adding entities from the Global search bar"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.fs_helper_obj = None
        self.tcinputs = {
        }

    def setup(self):
        """Setup function of this test case"""

        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator

    def run(self):
        """Main function for test case execution"""

        try:

            entity_dict = {"file server": "Add file server",
                           "Laptop": "Add laptop",
                           "Server group": "Add server group",
                           "Companies": "Add company",
                           "Users": "Add user",
                           "User groups": "Add user group",
                           "VM groups": "Add VM group",
                           "Roles": "Add role",
                           "Hypervisor": "Add hypervisor",
                           "Server back up plan": "Create server backup plan",
                           "Data classification plan": "Create data classification plan",
                           "Laptop plan": "Laptop plan",
                           "Gateway": "Add gateway"}

            for key, value in entity_dict.items():
                self.navigator.add_entity_from_search_bar(key)
                if key in ["Data classification plan", "Laptop plan"]:
                    pass
                else:
                    if value == ModalPanel(self.admin_console).title():
                        self.log.info(f"Able to launch correct panel for {key}")
                    else:
                        raise Exception(f"Panel header does not match for {value}")
                    self.admin_console.cancel_form()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:

            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
