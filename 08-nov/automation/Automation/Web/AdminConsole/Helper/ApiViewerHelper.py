# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the functions for API Viewer feature

Classes:

ApiViewer --

    --Functions:

    __init__()  --  Class initializer

    toggle_api_viewer  --  Method to enable or disable API viewer feature

    is_recording  --  Method to check if API recording started

    is_listing_table_present  --  Method to check if API viewer table has opened

    get_current_row_count  --  Method to find current number of rows in table page

    populate_apis  --  A Method to populate some APIs

    display_all_columns  --  Method to show all columns in API viewer table

    test_pagination  --  Method to test pagination

    check_api_types  --  Method to check GET, POST, DELETE, and PUT APIs are listed

    check_do_apis  --  Method to check .do APIs are listed

    check_report_apis  --  Method to check report APIs are listed

    apply_filters  --  Method to check the functioning of filters

    create_view  --  Method to create view

    delete_view  --  Method to delete view

    close_table  --  Method to close API viewer table

"""
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.core import Toggle
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.AdminConsolePages.server_groups import ServerGroups
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from enum import Enum


class ApiViewer:
    """
        Class for the helper file
    """

    def __init__(self, admin_console):

        """
        __init__ function of ApiViewer class
        :param admin_console: logged in admin console object

        """
        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.__dialog = RModalDialog(admin_console)
        self.__server_groups = ServerGroups(admin_console)
        self.__toggle = Toggle(admin_console)
        self.__page_container = PageContainer(admin_console)
        self.__table = Rtable(admin_console, id='apiViewerListPage')

    @PageService()
    def toggle_api_viewer(self):
        """
                Method to enable or disable API viewer feature
        """
        actions = ActionChains(self.__admin_console.driver)
        actions.key_down(Keys.SPACE)
        actions.key_down(Keys.SHIFT)
        actions.send_keys('a')
        actions.key_up(Keys.SHIFT)
        actions.key_up(Keys.SPACE)
        actions.perform()

    @PageService()
    def is_recording(self):
        """
                Method to check if API recording started
        """
        return self.__admin_console.check_if_entity_exists('xpath', '//div[@class="cv-flex blinking" '
                                                                    'and text()="Recording"]')

    @PageService()
    def is_listing_table_present(self):
        """
                Method to check if API viewer table has opened
        """
        return self.__admin_console.check_if_entity_exists('xpath', '//div[@id="APIViewModal"]')

    @PageService()
    def get_current_row_count(self):
        """
                Method to find current number of rows in table page
        """
        rows_xpath = "//div[@id='APIViewModal']//tr[contains(@class, 'k-master-row')]"
        return len(self.__admin_console.driver.find_elements(By.XPATH, rows_xpath))

    @PageService()
    def populate_apis(self):
        """
                A Method to populate some APIs
        """
        self.__navigator.navigate_to_server_groups()
        self.__server_groups.add_manual_server_group("apiviewertest")
        self.__admin_console.click_by_id('configuration')
        self.__toggle.disable(id='dataAgingToggle')
        self.__admin_console.wait_for_completion()
        self.__admin_console.scroll_into_view('//div[@class="popup"]')
        self.__page_container.access_page_action_from_dropdown('Delete', partial_selection=False)
        self.__dialog.click_submit()
        self.__navigator.navigate_to_reports()

    @PageService()
    def display_all_columns(self):
        """
                Method to show all columns in API viewer table
        """
        columns = ['Type', 'API', 'Description', 'Request', 'Response']
        self.__table.display_hidden_column(columns)

    @PageService()
    def test_pagination(self):
        """
                Method to test pagination
        """
        self.__table.set_pagination(500)
        self.__table.set_pagination(10)
        if self.get_current_row_count() != 10:
            return False
        self.__table.set_pagination(5)
        if self.get_current_row_count() != 5:
            return False
        self.__table.set_pagination(20)
        if self.get_current_row_count() != 20:
            return False
        self.__table.go_to_page('next')
        return True

    @PageService()
    def check_api_types(self):
        """
                Method to check GET, POST, DELETE and PUT APIs are listed
        """
        types = ['GET', 'POST', 'PUT', 'DELETE']
        for api_type in types:
            if not self.__table.is_entity_present_in_column('Type', api_type):
                return False, api_type
        return True, None

    @PageService()
    def check_do_apis(self):
        """
                Method to check .do APIs are listed
        """
        if self.__table.get_total_rows_count(search_keyword='.do') == 0:
            return False
        return True

    @PageService()
    def check_report_apis(self):
        """
                Method to check report APIs are listed
        """
        if self.__table.get_total_rows_count(search_keyword='cr/reportsplusengine/') == 0:
            return False
        return True

    @PageService()
    def apply_filters(self):
        """
                Method to check the functioning of filters
        """
        self.__table.clear_search()
        filter_values = ['POST', 'ServerGroup', 'Server group', 'name', 'serverGroupInfo']
        columns = ['Type', 'API', 'Description', 'Request', 'Response']
        api_count = self.__table.get_total_rows_count()
        for column, filter_value in zip(columns, filter_values):
            if column == 'Type':
                criteria = Enum('Comparison', {'EQUALS': 'Equals'})
                self.__table.apply_filter_over_column(column, filter_value, criteria.EQUALS)
            else:
                self.__table.apply_filter_over_column(column, filter_value)
        if not self.__table.get_total_rows_count() < api_count:
            return False
        return True

    @PageService()
    def create_view(self, view_name):
        """
                Method to create view
        """
        self.__table.create_view(view_name)

    @PageService()
    def delete_view(self, view_name):
        """
                Method to delete view
        """
        self.__table.delete_view(view_name)

    @PageService()
    def close_table(self):
        """
                Method to close api viewer table
        """
        self.__dialog.click_close()
