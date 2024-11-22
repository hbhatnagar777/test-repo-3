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
    __init__()      					--  initialize TestCase class

    setup()								--	initial setup for this test case

    validate_hyperlink()				--	method to validate hyperlink navigation from panel

    validate_tile_edit()				--	method to validate edit tile

    validate_get_details()				--	Method to validate panel information fetched

    validate_check_hyperlink()          -- Method to validate check hyperlink

    validate_open_hyperlink             -- Method to validate check hyperlink

    run()           					--  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """ Class for executing Basic acceptance Test for react panel info validation test case """
    test_step = TestStep()

    def __init__(self):
        """ Initializes test case class object """
        super(TestCase, self).__init__()
        self.name = "Integration of  React Panel component in command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.panel = None
        self.table = None
        self.client_name = None
        self.details = None

    def setup(self):
        """ Initial setup for this test case """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.table = Rtable(self.admin_console)
            self.client_name = self.commcell.clients.get(self.commcell.commserv_name).display_name
            self.navigator.navigate_to_user_groups()
            usergroups = self.table.get_column_data(self.admin_console.props['label.groupName'])
            if usergroups:
                self.table.access_link(usergroups[0])
                self.panel = RPanelInfo(self.admin_console)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def validate_hyperlink(self, panel_object, hyperlinks):
        """ method to validate hyperlink navigation from panel """
        if hyperlinks and panel_object.check_if_hyperlink_exists_on_tile(hyperlinks[0]):
            panel_object.open_hyperlink_on_tile(hyperlinks[0])

    @test_step
    def validate_get_details(self, panel_name=None):
        """ Method to validate panel information fetched """
        if panel_name:
            panel_details = RPanelInfo(self.admin_console, panel_name).get_details()
        else:
            panel_details = RPanelInfo(self.admin_console).get_details()
        for key in panel_details.items():
            if not key:
                self.log.info("Panel detail:%s", panel_details)
                raise CVTestStepFailure(f'Details are not fetched correctly for {panel_name} panel')
        self.details = panel_details

    @test_step
    def validate_tile_edit(self):
        """ Method to validate edit functionality in panel"""
        self.panel.edit_tile()
        self.admin_console.wait_for_completion()
        dialog = RModalDialog(self.admin_console)
        title = dialog.title()
        if title != self.admin_console.props['pageHeader.editUserGroup']:
            raise CVTestStepFailure("Incorrect dialog is open")

        dialog.click_cancel()

    @test_step
    def validate_check_hyperlink(self):
        """ Method to validate check hyperlink """
        hyperlinks = self.details['Company']
        if not hyperlinks:
            raise CVTestStepFailure("No company hyperlinks present on the user group page")

        if not self.panel.check_if_hyperlink_exists_on_tile(hyperlinks):
            raise CVTestStepFailure(f"Hyperlink {hyperlinks} not present on user group page")

    def validate_open_hyperlink(self):
        """ Method to validate check hyperlink """
        hyperlinks = self.details['Company']
        if hyperlinks:
            self.panel.open_hyperlink_on_tile(hyperlinks)

        url = self.admin_console.driver.current_url.lower()
        if "userGroup" in url:
            raise CVTestStepFailure(f"Failed redirecting from usergroup page; 'userGroup' found in url ({url})")

    def run(self):
        """ Main function for test case execution """
        try:
            self.validate_get_details()
            self.validate_tile_edit()
            self.validate_check_hyperlink()
            self.validate_open_hyperlink()
        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
