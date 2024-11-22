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
from Web.AdminConsole.Helper.GDPRHelper import GDPR

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Command Center: Table Component integration testcase"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Integration of  React Table grid component in command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.table = None
        self.modal = None
        self.group_name = 'master'
        self.role_name = "Master"
        self.group_name_header = 'Group name'
        self._user_name='admin'
        self.gdpr_obj = None

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_user_groups()
            self.table = Rtable(self.admin_console)
            self.modal = RModalDialog(self.admin_console)
            self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def get_number_of_columns(self):
        """gets number of columns present in react table"""
        self.navigator.navigate_to_user_groups()
        columns = self.table.get_number_of_columns()
        if not columns:
            raise CVTestStepFailure('unable to get columns')

    @test_step
    def get_visible_column_names(self):
        """Get visible Column names from react table"""
        self.navigator.navigate_to_user_groups()
        columns = self.table.get_visible_column_names()
        if self.group_name_header not in columns:
            raise CVTestStepFailure('Group Name not found in column names')

    @test_step
    def get_column_data(self):
        """Get column data from react table"""
        self.navigator.navigate_to_user_groups()
        column_data = self.table.get_column_data(self.group_name_header)
        if not column_data:
            raise CVTestStepFailure('unable to get data for Group name column')

    @test_step
    def access_action_item(self):
        """Selects the action item in react table"""
        self.navigator.navigate_to_user_groups()
        self.table.access_action_item(self.group_name, 'Add users')
        if self.modal.title() != 'Add users':
            raise CVTestStepFailure("Access action item failed. Action item [Add Users] is not clicked on local group")
        self.modal.click_cancel()


    @test_step
    def view_by_title(self):
        """View by title in react table"""
        self.navigator.navigate_to_user_groups()
        self.table.view_by_title('Local group')
        if 'view=localUserGroups' not in self.browser.driver.current_url:
            raise CVTestStepFailure(
                "View by title Tab selection failed, "
                "click on local group in tab didn't display local user groups"
            )

    @test_step
    def access_toolbar_menu(self):
        """Tool bar menu in react table"""
        self.navigator.navigate_to_user_groups()
        self.table.access_toolbar_menu('Add user group')
        if 'addUserGroup' not in self.browser.driver.current_url:
            raise CVTestStepFailure("Access tool bar menu didn't open Add user group page")

    @test_step
    def access_link(self):
        """Access the link from the react table"""
        self.navigator.navigate_to_user_groups()
        self.table.access_link(self.group_name)
        if 'userGroup/' not in self.browser.driver.current_url:
            raise CVTestStepFailure(
                "access link failed, click on group name didn't access user group details page"
            )

    @test_step
    def access_link_by_column(self):
        """search by entity_name and access by link_text in react table"""
        self.navigator.navigate_to_user_groups()
        self.table.access_link_by_column(
            self.group_name,
            self.group_name
        )
        if 'userGroup/' not in self.browser.driver.current_url:
            raise CVTestStepFailure(
                "access link by column failed, click on group name didn't access user group details page"
            )

    @test_step
    def select_rows(self):
        """Select rows in react table"""
        self.navigator.navigate_to_users()
        table = Rtable(self.admin_console, id="usersTable")
        table.search_for(self._user_name)
        table.select_rows([self._user_name])
        # if Invite User button is not present, then it will throw exception
        self.table.access_toolbar_menu("Invite user")
        self.admin_console.wait_for_completion()
        self.admin_console.refresh_page()
        self.admin_console.wait_for_completion()

    @test_step
    def apply_filter_over_column(self):
        """apply filter on given column in react table"""
        self.navigator.navigate_to_user_groups()
        table = Rtable(self.admin_console, id="userGroupTable")
        table.apply_filter_over_column('Group name', self.group_name)
        group_name = self.table.get_column_data('Group name')
        if not group_name or group_name[0].lower() != self.group_name.lower():
            raise CVTestStepFailure(
                f"Filter on column failed, expected [{ self.group_name}],"
                f"received [{group_name[0]}]"
            )

    @test_step
    def clear_column_filter(self):
        """clear filter from column in react table"""

        table = Rtable(self.admin_console, id="userGroupTable")
        table.clear_column_filter('Group name', self.group_name)
        group_name = self.table.get_column_data('Group name')
        cleared = False
        for grp in group_name:
            if grp.lower() != self.group_name.lower():
                cleared = True
                break
        if not cleared:
            raise CVTestStepFailure("Clearing filter failed while removing from input on column Group name")

    @test_step
    def get_table_data(self):
        """get data from the react table"""
        self.navigator.navigate_to_user_groups()
        data = self.table.get_table_data()
        if not data:
            raise CVTestStepFailure(
                f"unable to get data from table"
            )

    @test_step
    def is_entity_present_in_column(self):
        """Check entity present in react table"""
        self.navigator.navigate_to_user_groups()
        if not self.table.is_entity_present_in_column(self.group_name_header, self.group_name):
            raise CVTestStepFailure('unable to check master entity present in column')

    @test_step
    def get_total_rows_count(self):
        """gets total rows count from react table"""
        self.navigator.navigate_to_user_groups()
        count = self.table.get_total_rows_count()
        if count == 0:
            raise CVTestStepFailure("Get total rows count failed with zero count")

    @test_step
    def access_menu_from_dropdown(self):
        """access more menu from dropdown in react table"""
        self.navigator.navigate_to_users()
        self.table.access_menu_from_dropdown('Single user')
        if 'addUser' not in self.browser.driver.current_url:
            raise CVTestStepFailure(
                "Access menu frrom dropdown failed while selecting add-> 'Single user' on Users page")

    @test_step
    def display_hidden_column(self):
        """displays the hidden column in react table"""
        self.navigator.navigate_to_users()
        self.table.display_hidden_column("Enabled")
        columns = self.table.get_visible_column_names()
        if 'Enabled' not in columns:
            raise CVTestStepFailure("Display hidden column failed."
                                    "column with name 'Enabled' is not displayed on Users page")

    @test_step
    def apply_sort_over_column(self):
        """applies sorting order on react table column"""
        self.navigator.navigate_to_users()
        self.table.apply_sort_over_column('User name', ascending=True)
        before_sort = self.table.get_column_data('User name')
        self.table.apply_sort_over_column('User name', ascending=False)
        after_sort = self.table.get_column_data('User name')
        if before_sort == after_sort:
            raise CVTestStepFailure(
                "Apply sort over column failed, as User name column data matches before & after sort")

    @test_step
    def get_grid_action_list(self):
        """gets grid action list available in react table"""
        self.navigator.navigate_to_user_groups()
        action_list = self.table.get_grid_actions_list(self.group_name)
        if len(action_list) == 0:
            raise CVTestStepFailure("Get grid action list failed, returned zero for row in Users page React Table")

    @test_step
    def get_all_column_names(self):
        """gets all column names available in react table"""
        self.navigator.navigate_to_users()
        visible_items = self.table.get_visible_column_names()
        invisible_items = self.table.get_all_column_names()
        if len(invisible_items) == len(visible_items):
            raise CVTestStepFailure("Get all columnm names failed, Didn't fetch hidden column in Users page")

    @test_step
    def set_pagination(self):
        """Sets the pagination on react table"""
        self.navigator.navigate_to_users()
        self.table.set_pagination("10")
        before_pagination = self.table.get_column_data(column_name="User name")
        self.table.set_pagination("50")
        after_pagination = self.table.get_column_data(column_name="User name")
        if len(before_pagination) == len(after_pagination):
            raise CVTestStepFailure(f"Pagination not applied properly or Not having enough users. "
                                    f"Before count : {len(before_pagination)} "
                                    f"After count : {len(after_pagination)} ")

    @test_step
    def validate_type(self):
        """ Sets Type for React tables """
        self.navigator.navigate_to_servers()
        before_selection = self.table.get_total_rows_count()
        self.table.filter_type('All')
        after_selection = self.table.get_total_rows_count()
        if after_selection <= before_selection:
            raise CVTestStepFailure("Type has not been Updated!")

    @test_step
    def expand_row(self):
        """expands row in table"""
        self.navigator.navigate_to_governance_apps()
        self.gdpr_obj.inventory_details_obj.select_file_storage_optimization()
        rtable = Rtable(self.admin_console, id="FSOGrid")
        fso_server = rtable.get_column_data("Name")[0]
        rtable.expand_row(fso_server)
        rsubtable = Rtable(self.admin_console, id="DataSourcesSubGrid-")
        ds_names = rsubtable.get_column_data("Data source name")
        if len(ds_names) == 0:
            raise CVTestStepFailure("Expand didn't happen properly on Fso Server page")

    def run(self):
        """Test case run function"""
        try:

            self.init_tc()
            self.expand_row()
            self.set_pagination()
            self.get_number_of_columns()
            self.get_visible_column_names()
            self.get_column_data()
            self.view_by_title()
            self.get_table_data()
            self.is_entity_present_in_column()
            self.select_rows()



            # Please don't change this order as both are dependent
            self.apply_filter_over_column()
            self.clear_column_filter()

            self.access_toolbar_menu()
            self.get_total_rows_count()
            self.access_menu_from_dropdown()
            self.display_hidden_column()
            self.apply_sort_over_column()
            self.get_grid_action_list()
            self.get_all_column_names()
            self.validate_type()
            self.access_link()
            self.access_link_by_column()
            self.access_action_item()

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            print("")
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
