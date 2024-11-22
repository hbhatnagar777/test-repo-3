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

from Web.Common.cvbrowser import BrowserFactory, Browser

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.dialog import ModalDialog
from Web.AdminConsole.Components.panel import ModalPanel
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs

from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Command Center: Table Component integration testcase"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command Center Table component integration"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.table = None
        self.modal_dialog = None
        self.modal_panel = None
        self.tcinputs = {
            "ReplicationGroupName": None}

    def init_tc(self):
        """ Initial configuration for the test case. """
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login()
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_replication_groups()
            self.table = Table(self.admin_console)
            self.modal_dialog = ModalDialog(self.admin_console)
            self.modal_panel = ModalPanel(self.admin_console)
            self.grp_name = self.tcinputs['ReplicationGroupName']
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def get_number_of_columns(self):
        """gets number of columns present in table"""
        columns = self.table.get_number_of_columns()
        if not columns:
            raise CVTestStepFailure('unable to get columns')

    @test_step
    def get_visible_column_names(self):
        """Get visible Column names"""
        columns = self.table.get_visible_column_names()
        if 'Group name' not in columns:
            raise CVTestStepFailure('Group name not found in column names')

    @test_step
    def get_column_data(self):
        """Get column data"""
        column_data = self.table.get_column_data('Group name')
        if not column_data:
            raise CVTestStepFailure('unable to get data for Group name column')

    @test_step
    def access_action_item(self):
        """Selects the action item in table"""

        self.table.access_action_item(self.grp_name, 'Send logs')
        self.admin_console.wait_for_completion()
        if self.browser.driver.title != 'Logs':
            raise CVTestStepFailure(
                "access action item failed, Send logs didn't access logs page"
            )

    @test_step
    def view_by_title(self):
        """View by type in grid"""
        self.table.view_by_title('')
        if 'laptopJobs' not in self.browser.driver.current_url:
            raise CVTestStepFailure(
                "View by title drop down failed, "
                "click on laptop job in dropdown didn't access laptop jobs page"
            )

    @test_step
    def access_toolbar_menu(self):
        """Tool bar menu in table"""
        self.navigator.navigate_to_rpstore()
        self.table.access_toolbar_menu('AddRPStoreButton')
        if self.modal_dialog.title() != 'Add storage':
            raise CVTestStepFailure("Access tool bar menu didn't open Add storage dialog")
        self.modal_dialog.click_cancel()

    @test_step
    def access_link(self):
        """Access the link from the table"""
        self.table.access_link(self.grp_name)
        if self.browser.driver.title != "Replication groups detail":
            raise CVTestStepFailure(
                "access link failed, click on Group name didn't access Group detail page"
            )

    @test_step
    def access_link_by_column(self):
        """search by entity_name and access by link_text"""
        self.navigator.navigate_to_replication_groups()
        self.table.access_link_by_column(
            self.grp_name,
            self.grp_name
        )
        if self.browser.driver.title != "Replication groups detail":
            raise CVTestStepFailure(
                "access link by column failed, click on Group name "
                "didn't access Group details page"
            )

    @test_step
    def access_context_action_item(self):
        """Selects the action item in table right click menu"""
        self.navigator.navigate_to_jobs()
        jobs = Jobs(self.admin_console)
        data = self.table.get_column_data('Job Id')
        if not data:
            jobs.access_job_history()
            data = self.table.get_column_data('Job Id')
            if not data:
                raise CVTestStepFailure(
                    "This setup doesn't have 1 active job or 1 job in last 24 hours to "
                    "validate table context menu"
                )
        self.table.access_context_action_item(
            data[0],
            self.admin_console.props['label.viewJobDetails']
        )
        if data[0] not in self.browser.driver.current_url:
            raise CVTestStepFailure(
                f"Context menu in jobs page didn't open Jobs details page of job {data[0]}")

    @test_step
    def select_rows(self):
        """Select rows in table"""
        self.navigator.navigate_to_replication_groups()
        self.table.select_rows([self.grp_name])
        self.table.access_toolbar_menu("Delete")
        self.admin_console.wait_for_completion()
        if self.modal_dialog.title() != 'Delete replication group':
            raise CVTestStepFailure("select rows didn't select row properly")
        self.modal_dialog.click_cancel()

    @test_step
    def apply_filter_over_column(self):
        """apply filter on given column"""
        self.navigator.navigate_to_replication_groups()
        self.table.apply_filter_over_column('Group name', self.grp_name)
        grp_name = self.table.get_column_data('Group name')
        if not grp_name or grp_name[0] != self.grp_name:
            raise CVTestStepFailure(
                f"Filter on column failed, expected [{ self.grp_name}],"
                f"received [{grp_name[0]}]"
            )

    @test_step
    def apply_filter_over_integer_column(self):
        """apply filter on integer type column"""
        self.navigator.navigate_to_failover_groups()
        vm_count = self.table.get_column_data('Number of virtual machines')
        self.table.apply_filter_over_integer_column('Number of virtual machines', vm_count[0])
        vm_count_now = self.table.get_column_data('Number of virtual machines')
        if not vm_count_now or not all(element == vm_count_now[0] for element in vm_count_now):
            raise CVTestStepFailure(
                f"Filter on column failed, expected vm count [{vm_count[0]}],"
                f"but received [{vm_count_now}]"
            )

    @test_step
    def clear_column_filter(self):
        """clear filter from column"""
        self.table.clear_column_filter('Group name')
        server_name = self.table.get_column_data('Group name')
        if len(server_name) == 1:
            raise CVTestStepFailure(
                f"Clear filter on column failed, expected length of filter to be more than 1"
            )

    @test_step
    def get_table_data(self):
        """data in the table"""
        data = self.table.get_table_data()
        if not data:
            raise CVTestStepFailure(
                f"unable to get data from table"
            )

    @test_step
    def is_entity_present_in_column(self):
        """Check entity present"""
        if not self.table.is_entity_present_in_column('Group name', self.grp_name):
            raise CVTestStepFailure('unable to check entity present in column')

    @test_step
    def apply_filter_over_column_selection(self):
        """Apply filter over column list"""
        self.navigator.navigate_to_replication_groups()
        self.table.apply_filter_over_column_selection('Group name', self.grp_name)
        operation1 = self.table.get_column_data('Group name')
        if len(list(set(operation1))) != 1:
            self.log.error(
                f'Expected data [{self.grp_name}] , received after filter {list(set(operation1))}'
            )
            raise CVTestStepFailure('unable to verify apply column over filter list functionality')

    def run(self):
        try:

            self.init_tc()
            self.get_number_of_columns()
            self.get_visible_column_names()
            self.get_column_data()
            self.access_action_item()
            # self.view_by_title()
            self.apply_filter_over_column()
            self.clear_column_filter()
            self.get_table_data()
            self.is_entity_present_in_column()
            self.access_link()
            self.access_link_by_column()
            # self.access_context_action_item()
            self.select_rows()
            self.apply_filter_over_column_selection()
            self.apply_filter_over_integer_column()
            self.access_toolbar_menu()

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
