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

    init_tc()        -- initialize the admin console and browse classes

    run()           --  run function of this test case

Assumptions while running the testcase:
    1. This TC tests browse functionality on the CS client's FS agent
    2. Create a FS subclient with the following as content and have successful backup
    3. Have a directory structure like below in backed up content:
        E:->FOLDER1:
        E:->FOLDER1->FOLDERA->FOLDERB-> <SOME FILES>
        E:->FOLDER1->FOLDERA-><DELETED FILE>

        E:->FOLDER2:
        E:->FOLDER2->FOLDERC-> <TWO OR MORE FILES>

        E:-> <SOME FILES> -- if paging needs to be validated,
                            have more files at this level like 100

"""
from selenium.common.exceptions import ElementClickInterceptedException

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.browse import Browse
from Web.AdminConsole.Components.panel import ModalPanel
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Command Center: Table Component integration testcase TC 58048"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command Center Browse component integration TC 58048"
        self.browser = None
        self.admin_console = None
        self.browse = None
        self.modal_panel = None
        self.folders = None
        self.table = None
        self.client_name = None
        self.items_level_1 = None
        self.items_level_2 = None
        self.navigator = None
        self.tcinputs = {
            "SubClientName": None
        }

    def init_tc(self):
        """ Initial configuration for the test case"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']["commcellUsername"],
                                     password=self.inputJSONnode['commcell']["commcellPassword"])
            self.navigator = self.admin_console.navigator
            self.browse = Browse(self.admin_console)
            self.table = Table(self.admin_console)
            self.modal_panel = ModalPanel(self.admin_console)
            self.client_name = self.commcell.clients.get(self.commcell.commserv_name).display_name

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    @test_step
    def navigate_to_browse_page(self):
        """Navigates to file servers page and picks restore from actions"""
        self.navigator.navigate_to_file_servers()
        self.table.access_link(self.client_name)
        self.table.access_link(self.tcinputs['SubClientName'])
        self.admin_console.access_action(self.admin_console.props['action.restore'])

    @test_step
    def get_browse_data(self):
        """gets the data displayed in the browse page"""
        self.items_level_1 = self.browse.get_column_data('Name')
        if not self.items_level_1:
            raise CVTestStepFailure("Empty browse page or files/folders not displayed")
        sizes = self.browse.get_column_data('Size')
        if not sizes:
            raise CVTestStepFailure("Empty browse page or sizes of items not displayed")

    @test_step
    def access_folder(self):
        """Validates accessing folder in browse page"""
        self.browse.access_folder(self.items_level_1[0])
        if self.items_level_1[0] in self.browse.get_column_data('Name'):
            raise CVTestStepFailure('Not able to access folder {0}'.format
                                    (self.items_level_1[0]))

    @test_step
    def select_one_and_multiple_items(self):
        """Validates selecting of one item and multiple items in browse
        Clicks on last few items to validate if paging is handled"""
        self.items_level_2 = self.browse.get_column_data('Name')
        self.browse.select_for_restore([self.items_level_2[0]])
        self.browse.submit_for_restore()
        self.modal_panel.cancel()
        length = len(self.items_level_2)
        self.browse.select_for_restore([self.items_level_2[length-1],
                                        self.items_level_2[length-2]])
        self.browse.submit_for_restore()
        self.modal_panel.cancel()

    @test_step
    def select_all_items(self):
        """Validates selecting all items in browse page"""
        self.browse.clear_all_selection()
        self.browse.select_for_restore(all_files=True)
        self.browse.submit_for_restore()
        self.modal_panel.cancel()
        self.browse.clear_all_selection()

    @test_step
    def show_latest_backup(self):
        """Validates if show latest backup option works"""
        self.browse.show_latest_backups()
        self.get_browse_data()
        self.access_folder()

    @test_step
    def select_deleted_items(self):
        """Validates if select deleted items option works"""
        self.navigate_to_browse_page()
        self.get_browse_data()
        self.access_folder()
        self.browse.select_deleted_items_for_restore(self.items_level_2[0], '\\')
        self.browse.submit_for_restore()
        self.modal_panel.cancel()

    @test_step
    def select_paths(self):
        """validates if expanding folder and expanding folder until file works"""
        self.navigate_to_browse_page()
        self.browse.select_path_for_restore(
            self.items_level_1[0]+'\\'+self.items_level_2[1])
        self.browse.submit_for_restore()
        self.modal_panel.cancel()
        self.browse.clear_all_selection()
        folder = self.browse.get_column_data('Name')
        self.browse.access_folder(folder[0])
        file = self.browse.get_column_data('Name')
        self.navigate_to_browse_page()
        self.browse.select_path_for_restore(
            self.items_level_1[0] + '\\' + self.items_level_2[1]
            + '\\' + folder[0], file_folders=file[0])
        self.browse.submit_for_restore()
        self.modal_panel.cancel()

    @test_step
    def submit_restore(self):
        """Validates if restore button can be clicked"""
        self.navigate_to_browse_page()
        self.access_folder()
        self.select_one_and_multiple_items()
        self.browse.submit_for_restore()
        self.modal_panel.cancel()

    @test_step
    def clear_all(self):
        """Validates if clear all selection works"""
        try:
            self.browse.select_for_restore(all_files=True)
            self.browse.clear_all_selection()
            self.browse.submit_for_restore()
        except ElementClickInterceptedException:
            pass

    def run(self):
        try:

            self.init_tc()
            self.navigate_to_browse_page()
            self.get_browse_data()
            self.access_folder()
            self.select_one_and_multiple_items()
            self.select_all_items()
            self.show_latest_backup()
            self.select_deleted_items()
            self.select_paths()
            self.submit_restore()
            self.clear_all()

        except Exception as err:
            handle_testcase_exception(self, err)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

