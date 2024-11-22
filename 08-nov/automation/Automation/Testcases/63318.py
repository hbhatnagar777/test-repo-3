# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                          --  initialize TestCase class

    setup()                             --  setup method for test case

    tear_down()                         --  tear down method for testcase

    run()                               --  Run function of this test case
"""


from Web.Common.exceptions import CVTestStepFailure
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.core import TreeView, Checkbox
from Server.Security.securityhelper import RoleHelper
from random import sample, choice
from selenium.webdriver.common.by import By

class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Integration of treeview component in command center"
        self.navigator = None
        self.tcinputs = {
        }

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        
        # components        
        self.rtable = Rtable(self.admin_console)
        self.treeview = TreeView(self.admin_console)
        self.checkbox = Checkbox(self.admin_console)
        
        # tree view IDs
        self.tree_view_ids =  ['showSelectedCheckbox', 'selectAllCheckbox', 'treeview search']
        
        # get random categories and permissions to select / deselect
        self.categories = self.commcell.roles.get('Tenant Admin').permissions['category_list']
        self.permissions = sample([perm for perm in self.commcell.roles.get('Tenant Admin').permissions['permission_list'] if '\\' not in perm], 10)
        self.log.info(f'Random Categories  => {self.categories}')
        self.log.info(f'Random Permissions => {self.permissions}')

    def run(self):
        """Run function of this test case"""
        try:
            # Go to Tree View page
            self.navigator.navigate_to_roles()
            self.rtable.access_toolbar_menu('Add role')
            self.admin_console.wait_for_completion()
            
            # validation begins here
            self.log.info('Starting Tree View Validation...')
            
            self.validate_ids()
            
            self.validate_tree_view_checkbox()
            
            # validate tree view child node selection / deselection
            self.validate_selection(self.permissions)
            self.validate_deselection(self.permissions)
            
            # validate tree view parent node selection / deselection
            self.validate_selection(self.categories)
            self.validate_deselection(self.categories)
            
            self.validate_single_item_selection()
            
            # validation ends here
            self.log.info('Tree View Validation Completed!')
            
        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
            
    @test_step
    def validate_ids(self):
        """Test step to validate if ID exists or not changed"""
        status = [bool(self.admin_console.driver.find_elements(By.ID, id)) for id in self.tree_view_ids]
        self.log.info(f'TreeView ID Status => {tuple(zip(self.tree_view_ids, status))}')
        
        if not all(status):
            raise CVTestStepFailure('IDs not matching on TreeView component')
        
        self.log.info('Successfully validated IDs')
        
    @test_step
    def validate_tree_view_checkbox(self):
        """Method to validate SELECT / CLEAR ALL checkboxes"""
        # Below function calls will internally throw exceptions on failure
        self.treeview.show_selected()
        self.treeview.show_all()
        self.treeview.select_all()
        self.treeview.clear_all()      
                
        self.log.info('Checkboxes on Tree View are interactable!')
    
    @test_step
    def validate_selection(self, items):
        """Test step to validate if values can be selected on tree view"""
        self.treeview.select_items(items)

        if not all(self.__item_select_status(items)):
            raise CVTestStepFailure('Failed to select all items on tree view')

        self.log.info('Successfully validated Items selection!')
            
    @test_step
    def validate_deselection(self, items):
        """Test step to validate if values can be de-selected on tree view"""
        self.treeview.unselect_items(items)

        if any(self.__item_select_status(items)):
            raise CVTestStepFailure('Failed to de-select all items on tree view')
        
        self.log.info('Successfully validated Items deselection!')
        
    @test_step
    def validate_single_item_selection(self):
        """Test step to validate if value can be selecting using label"""
        label = choice(self.categories)
        self.log.info(f'Selecting item with label : {label}')
        self.treeview.select_item_by_label(label)
        self.log.info('Successfully validated item selection based on label')
        
    def __item_select_status(self, items):
        """Method to get the status of checkbox selection on treeview"""
        status = [self.checkbox.is_checked(item) for item in items]
        self.log.info(f'Items Selection Status : {tuple(zip(items, status))}')
        
        return status