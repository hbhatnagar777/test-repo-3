#!/usr/bin/python
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
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.page_container import PageContainer
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test for react drop down component"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = \
            'Basic Integration test case for React drop-down component in AdminConsole Automation'
        self.browser = None
        self.admin_console = None
        self.__navigator = None
        self.react_dropdown = None
        self.react_table = None
        self.page_container = None

    def setup(self):
        """ initial setup for this test case """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser,
                                              self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.__navigator = self.admin_console.navigator
            self.react_dropdown = RDropDown(self.admin_console)
            self.react_table = Rtable(self.admin_console)
            self.page_container = PageContainer(self.admin_console)
            self.__navigator.navigate_to_users()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def validate_drop_down_select(self, drop_down_id, list_of_values):
        """
        method to validate if the values are selected in drop-down or not

        Args:
            drop_down_id    (str)       -- Drop down id

            list_of_values  (list)      -- list of values to validate against

        """
        values_selected = self.react_dropdown.get_selected_values(drop_down_id)
        if not set(values_selected)-set(list_of_values) == set(list_of_values)-set(values_selected):
            raise CVTestStepFailure("All values were not selected in the dropdown")
        self.log.info("All provided values were selected")


    @test_step
    def add_user_dropdown(self):
        """ method to verify react dropdown in user add page"""
        self.react_table.access_menu_from_dropdown('Single user')
        user_group_list = self.react_dropdown.get_values_of_drop_down('userGroups')
        self.log.info("User group list from drop-down: %s", user_group_list)
        if len(user_group_list) < 2:
            raise CVTestStepFailure(
                "At-least 2 user groups are required to verify multi select drop down")
        self.react_dropdown.select_drop_down_values(
            values=[user_group_list[-1], user_group_list[-2]],
            drop_down_id='userGroups')
        self.validate_drop_down_select('userGroups', [user_group_list[-1], user_group_list[-2]])
        self.react_dropdown.deselect_drop_down_values(
            values=[user_group_list[-1]],
            drop_down_id='userGroups'
        )

    @test_step
    def add_region_dropdown(self):
        """ method to verify react dropdown in region add page"""
        self.__navigator.navigate_to_regions()
        self.react_table.access_toolbar_menu('Add region')
        region_type = self.react_dropdown.get_values_of_drop_down('type')
        self.log.info("Region type list from drop-down: %s", region_type)
        if len(region_type) == 0:
            raise CVTestStepFailure(
                "Region type is empty")
        self.react_dropdown.select_drop_down_values(
            values=[region_type[-1]],
            drop_down_id='type')
        self.validate_drop_down_select('type', [region_type[-1]])

    def run(self):
        """ Main function for test case execution """
        try:
            self.add_user_dropdown()
            self.add_region_dropdown()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
