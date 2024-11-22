from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from Web.AdminConsole.AdminConsolePages.Plans import Plans

"""
This module provides all the methods that can be done of the Sensitive Data Analysis
project page.

Classes:

    SensitiveDataAnalysis() ---> GovernanceApps() ---> object()


SensitiveDataAnalysis  --  This class contains all the methods for action in
    Sensitive Data Analysis Project page and is inherited by other classes to
    perform GDPR related actions

    Functions:

    add_project()                   --  adds a project
    search_for_project()            -- Searches for a given project
    navigate_to_project_details()   -- Navigates to project details page
    navigate_to_project_discover()  -- Navigates to project discover page
    delete_project()                -- Deletes a Project
    add_project_and_advance()       -- Adds a project and advances to datasource creation
    _add_project_helper()           -- Adds a project
    select_project()                -- Selects a project in add project page and advances to datasource creation
"""
from Web.AdminConsole.Components.table import Rtable
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.AdminConsole.GovernanceAppsPages.GovernanceApps import GovernanceApps
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.wizard import Wizard


class SensitiveDataAnalysis(GovernanceApps):
    """
     This class contains all the methods for action in Sensitive Data Analysis page
    """

    def __init__(self, admin_console):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object
        """
        super().__init__(admin_console)
        self.__admin_console = admin_console
        self.driver = self.__admin_console.driver
        self.__admin_console.load_properties(self)
        self.log = self.__admin_console.log
        self.__rtable = Rtable(self.__admin_console)
        self.__rdropdown = RDropDown(self.__admin_console)
        self.__rmodal_dialog = RModalDialog(self.__admin_console)
        self.__rwizard = Wizard(self.__admin_console)
        self.__plan = Plans(self.__admin_console)

    @WebAction()
    def add_project(self, project_name, plan_name, create_plan=False, entities_list=None, select_all=False):
        """
        Adds a project

            Args:
                project_name (str)  - Project name to be added
                plan_name (str)  - Plan name to be selected
                create_plan(bool)   - Should create plan or reuse existing plan
                entities_list(list) - List of sensitive entities
                select_all(bool)    - Selects all entities in the plan
            Raise:
                Exception if project addition failed
        """
        self.log.info('Clicking on Add button')
        self.__admin_console.click_button_using_text(self.__admin_console.props['label.add'])
        self.log.info('Selecting %s data source option' % self.__admin_console.props['label.datasource.file'])
        self.driver.find_element(By.XPATH,
                                 f"//li[@role='menuitem']/span[contains(text(),'"
                                 f"{self.__admin_console.props['label.datasource.file']}')]").click()
        self._add_project_helper(project_name, plan_name, create_plan, entities_list, select_all)
        self.__rwizard.click_cancel()
        self.navigate_to_project_details(project_name)

    @PageService()
    def add_project_and_advance(self, project_name, plan_name, create_plan=False, entities_list=None, select_all=False):
        """
        Adds a project and advances to datasource creation
            Args:
                project_name (str)  - Project name to be added
                plan_name (str)     - Plan name to be selected
                create_plan(bool)   - Should create plan or reuse existing plan
                entities_list(list) - List of sensitive entities
                select_all(bool)    - Selects all sensitive entities
            Raise:
                Exception if project addition failed
        """
        self._add_project_helper(project_name, plan_name, create_plan, entities_list, select_all)
        self.log.info("Clicking on Next")
        self.__admin_console.click_button(self.__admin_console.props['label.next'])

    @PageService()
    def _add_project_helper(self, project_name, plan_name, create_plan, entities_list, select_all):
        """
        Adds a project
            Args:
                project_name (str)  - Project name to be added
                plan_name (str)     - Plan name to be selected
                create_plan(bool)   - Should create plan or reuse existing plan
                entities_list(list) - List of sensitive entities
                select_all(bool)    - Selects all sensitive entities
            Raise:
                Exception if project addition failed
        """
        self.__rwizard.click_icon_button_by_title("Add new project")
        self.log.info("Entering Project name")
        self.__admin_console.fill_form_by_id("projectName", project_name)
        if create_plan is False:
            self.log.info("Selecting Plan: %s" % plan_name)
            self.__rdropdown.select_drop_down_values(values=[plan_name], drop_down_id='plan')
        else:
            self.log.info("Creating new Plan: %s" % plan_name)
            self.__rmodal_dialog.click_icon_by_title(self.__admin_console.props['label.addPlan'])
            self.__plan.create_simplified_ra_plan(plan_name, entities_list, select_all)
        self.log.info("Clicking on Save")
        self.__admin_console.submit_form()
        if self.__admin_console.check_if_entity_exists(
                "xpath", "//*[@class='serverMessage error']"):
            raise Exception(self.driver.find_element(By.XPATH,
                                                     "//*[@class='serverMessage error']").text)

    @PageService()
    def select_project(self, project_name):
        """
        Selects a project in add project page and advances to datasource creation
            Args:
                project_name (str)  - Project name to be added
            Raise:
                Exception if project selection fails
        """
        self.log.info("Entering Project name")
        self.__rdropdown.select_drop_down_values(values=[project_name], drop_down_id='projects')
        self.log.info("Clicking on Next button")
        self.__admin_console.click_button(self.__admin_console.props['label.next'])

    @WebAction()
    def search_for_project(self, project_name):
        """
        Searches for a given project

            Args:
                project_name (str)  - Project name to be searched for

            Returns True/False based on the presence of the Project
        """
        return self.__rtable.is_entity_present_in_column(
            self.__admin_console.props['label.name'], project_name)

    @PageService()
    def navigate_to_project_details(self, project_name):
        """
        Navigates to project details page

            Args:
                project_name (str)  - project name details to be navigated

        """
        self.__rtable.access_action_item(
            project_name, self.__admin_console.props['label.configuration'])

    @PageService()
    def navigate_to_project_discover(self, project_name):
        """
        Navigates to project discover page

            Args:
                project_name (str)  - project name details to be navigated

        """
        self.__rtable.access_action_item(
            project_name, self.__admin_console.props['label.discover'])

    @PageService()
    def delete_project(self, project_name):
        """
        Deletes a project

            Args:
                project_name (str)  - Project name to be deleted

            Raise:
                Exception if project deletion failed
        """
        self.__rtable.access_action_item(
            project_name, self.__admin_console.props['label.delete'])
        self.__rmodal_dialog.click_submit()
        self.__admin_console.check_error_message()
