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
    __init__()                          --  initialize TestCase class

    setup()                             --  initial setup for this test case

    validate_toggle()                   --  method to validate toggles in panel

    validate_edit_tile_entity()         --  method to validate edit tile entity

    validate_edit_tile()                --  method to validate edit tile

    validate_panel_info()               --  Method to validate panel information fetched

    companies_panel_info()              --  Method to test companies panel information

    run()                               --  run function of this test case


"""
from time import sleep
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.panel import PanelInfo
from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """ Class for executing Basic acceptance Test for panel info validation test case """
    test_step = TestStep()

    def __init__(self):
        """ Initializes test case class object """
        super(TestCase, self).__init__()
        self.name = "Basic Integration test case for Panel in AdminConsole"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.angular_table = None
        self.panel = None

    def setup(self):
        """ initial setup for this test case """
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.angular_table = Table(self.admin_console)

    @test_step
    def validate_toggle(self, panel_object, label):
        """ method to validate toggles in panel """
        panel_object.enable_toggle(label)
        panel_object.disable_toggle(label)

    @test_step
    def validate_edit_tile_entity(self, entity_name):
        """ method to validate edit tile entity"""
        # header.label.general = General
        PanelInfo(self.admin_console,
                  self.admin_console.props['header.label.general']).edit_tile_entity(entity_name)

    @test_step
    def validate_edit_tile(self):
        """ method to validate edit tile """
        # header.label.emailSettings=Email settings
        PanelInfo(self.admin_console,
                  self.admin_console.props['header.label.emailSettings']).edit_tile()

    @test_step
    def validate_panel_info(self, panel_name=None):
        """ Method to validate panel information fetched """
        sleep(5)
        if panel_name:
            panel_details = PanelInfo(self.admin_console, panel_name).get_details()
        else:
            panel_details = PanelInfo(self.admin_console).get_details()
        for key, value in panel_details.items():
            if not key or not value:
                self.log.info("Panel detail:%s", panel_details)
                raise CVTestStepFailure(f'Details are not fetched correctly for {panel_name} panel')
        return panel_details

    @test_step
    def companies_panel_info(self):
        """ Method to test companies panel information """
        self.navigator.navigate_to_companies()
        companies = self.angular_table.get_column_data('Name')
        if companies:
            self.angular_table.access_link(companies[0])
            self.admin_console.access_tab(self.admin_console.props['header.overview'])
            self.validate_panel_info(self.admin_console.props['header.label.general'])
            # label.nav.navigationPreferences = Navigation preferences
            panel_details = PanelInfo(
                self.admin_console,
                self.admin_console.props['label.nav.navigationPreferences']).get_details()
            for value in panel_details:
                if not value:
                    self.log.info("Panel detail:%s", panel_details)
                    raise CVTestStepFailure('Details are not fetched correctly for Navigation preferences panel')
            # label.enableAutoDiscover=Auto discover applications
            self.validate_toggle(
                PanelInfo(self.admin_console, self.admin_console.props['header.label.general']),
                self.admin_console.props['label.showDLP'])
            self.validate_edit_tile_entity(self.admin_console.props['label.companyAlias'])

    def run(self):
        """Main function for test case execution"""
        try:
            self.companies_panel_info()
        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
