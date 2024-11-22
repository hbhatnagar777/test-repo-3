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

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMware backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "O365 mail client: Advanced option verification"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname, enable_ssl=True)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.log.info("Creating an object for office365 helper")
        self.tcinputs['office_app_type'] = Office365Apps.AppType.exchange_online
        self.office365_obj = Office365Apps(tcinputs=self.tcinputs,
                                           admin_console=self.admin_console,
                                           is_react=True
                                           )

    def run(self):
        """Main function for test case execution"""

        try:
            self.admin_console.close_popup()
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.office365_obj.create_office365_app()
            self.office365_obj.add_user()
            self.office365_obj.run_backup()
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.tcinputs['Name'])
            self.office365_obj.change_plan()
            self.office365_obj.remove_from_content()
            self.office365_obj.exclude_user()
            self.office365_obj.add_azure_app_and_verify()
            self.office365_obj.add_service_account()
            self.office365_obj.verify_connection()
            self.office365_obj.view_jobs()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.tcinputs['Name'])
        self.navigator.navigate_to_plan()
        self.office365_obj.delete_plan(self.tcinputs['NewPlan'])
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
