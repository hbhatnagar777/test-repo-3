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

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.drbackup_helper import DRValidateHelper
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object """
        super(TestCase, self).__init__()
        self.name = "validate DR Backup Schedule Settings"
        self.browser = None
        self.admin_console = None
        self.drbackup_helper = None

    def setup(self):
        """Setup function of this test case"""
        self.log.info("executing testcase")
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.drbackup_helper = DRValidateHelper(
            admin_console=self.admin_console,
            commcell=self.commcell,
            client_name=self.commcell.commserv_client
        )

    def run(self):
        """Run function of this test case"""
        try:
            self.drbackup_helper.validate(test_list={'validate_drbackup_schedule': {},
                                                     'validate_drbackup_repeat_schedule': {}})

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        self.browser.close()
