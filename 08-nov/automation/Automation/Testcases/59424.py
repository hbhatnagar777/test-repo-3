# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for OneDrive v2 Client creation with Single Node and Express configuration

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""


import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages.onedrive import OneDrive
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes testcase class object"""
        super(TestCase, self).__init__()
        self.testcaseutils = CVTestCase
        self.name = "OneDrive v2: Client creation with Single Node and Express configuration"
        self.browser = None
        self.navigator = None
        self.admin_console = None
        self.onedrive = None
        self.client_name = None

    def setup(self):
        """Initial configuration for the testcase."""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword'])

            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.tcinputs['Name'] += "_OD_59424"

            self.log.info("Creating an object for office365 helper")
            self.tcinputs['office_app_type'] = OneDrive.AppType.one_drive_for_business
            self.onedrive = OneDrive(self.tcinputs, self.admin_console)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def run(self):
        try:
            self.onedrive.create_office365_app()
            self.onedrive.verify_app_config_values()
            self.onedrive.is_app_associated_with_plan()
        except Exception as err:
            handle_testcase_exception(self, err)

    def tear_down(self):
        try:
            if self.status == constants.PASSED:
                self.log.info("Testcase Passed")
                self.navigator.navigate_to_office365()
                self.onedrive.delete_office365_app(self.tcinputs['Name'])
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
