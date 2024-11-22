# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to validate
actions in all Solutions pages.

To begin, create an instance of Solution for validation test case.

To initialize the class variables, pass the instance object to the appropriate
definition of AdminConsoleInfo

Call the required definition using the instance object.

        fetch_grid_level_actions -- Gets all grid level actions

        fetch_page_level_actions -- Gets all page level actions from dropdown menu

        navigate_to_solution -- Navigates to the Solutions page based on SolutionType Enum

        validate_actions -- Validates if all grid level actions are present in page detail actions in order

        validate_columns_order -- Validates if all the columns in Solutions page are in order

        validate_grouping -- Validates grouping of page level and grid level actions

"""
from enum import Enum
from Web.AdminConsole.Components.table import Table
from Web.Common.exceptions import CVTestStepFailure


groups = {0: ['Restore', 'Back up', 'Restore history'],
          1: ['Manage plan', 'View jobs', 'Add 3DFS network share', 'Add backup set',
              'Do not back up', 'View active mounts', 'Configure replication', 'Migrate'],
          2: ['Add software', 'Update software', 'Uninstall software', 'Release license',
              'Reconfigure', 'Delete', 'Retire'],
          3: ['Change company'],
          4: ['Check readiness', 'Restart services', 'Send logs', 'View logs']}


class Solutions:
    """ Helper file to provide arguments and handle function call to main file """

    def __init__(self, admin_console, solution):
        """ Initialize method for Solutions

        Args:
                admin_console   (AdminConsole)    --  AdminConsole class object

                solution  (enum)   --   the solution page to navigate to, among the type in Solution.SolutionType enum

        """
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__navigator = admin_console.navigator
        self.log = self.__admin_console.log
        self.table = Table(self.__admin_console)
        self.__solution = solution

    class SolutionType(Enum):
        """Type of solution to navigate to"""
        FileServers = "File servers"
        VirtualMachines = "Virtual machines"
        Hypervisors = "Hypervisors"
        VmGroups = "VM groups"
        Instances = "Instances"
        Databases = "Databases"
        Laptops = "Laptops"
        Exchange = "Exchange"
        Office365 = "Office 365"
        CloudApps = "Cloud apps"
        SharePoint = "Share point"
        ObjectStorage = "Object storage"
        BigData = "Big data"
        Archiving = "Archiving"

    def __check_diff_grid(self, diff_grid):
        """Checks if remaining grid actions are present in details page"""
        if "Restore" in diff_grid:
            diff_grid.remove("Restore")

        if "Manage plan" in diff_grid:
            if self.__admin_console.check_if_entity_exists(
                    "xpath", "//span[text()='Plan']/..//*[contains(text(),'Edit')]"):
                diff_grid.remove("Manage plan")
                self.log.info("Edit plan action exists in details page")
            else:
                raise CVTestStepFailure("Edit plan action doesn't exist in details page")

        if "View jobs" in diff_grid:
            diff_grid.remove("View jobs")
            flag = False
            for action in ['Backup history', 'Restore history', 'Jobs', 'Archive history']:
                if self.__admin_console.check_if_entity_exists(
                        "xpath", f"//div[contains(@class,'main-bar-action')]/span[contains(text(),'{action}')]"):
                    self.log.info(f"{action} action exists in details page")
                    flag = True
                    break
            if not flag:
                raise CVTestStepFailure("View jobs action doesn't exist in details page")

        if "Check readiness" in diff_grid:
            if self.__admin_console.check_if_entity_exists(
                    "xpath", f"//span[contains(text(),'readiness')]"):
                diff_grid.remove("Check readiness")
                self.log.info("Check readiness action exists in details page")
            else:
                raise CVTestStepFailure("Check readiness action doesn't exist in details page")

        for action in diff_grid:
            if action in ["Back up", "readiness", "Archive", "Migrate"]:
                if self.__admin_console.check_if_entity_exists(
                        "xpath", f"//span[contains(text(),'{action}')]"):
                    diff_grid.remove(action)
                    self.log.info(f"{action} action exists in details page")
                else:
                    raise CVTestStepFailure(f"{action} action doesn't exist in details page")

        if diff_grid:
            raise CVTestStepFailure(f"Following grid level actions - "
                                    f"'{diff_grid}' are not present in page level actions")

    def __compare_order(self, grid_actions, page_actions):
        """Checks if Order of grid level actions matches page level actions"""
        if len(grid_actions) != len(page_actions):
            raise CVTestStepFailure(f"{grid_actions} and {page_actions} have different number of actions")
        grid_dict = {value: key for key, value in enumerate(grid_actions)}
        page_dict = {value: key for key, value in enumerate(page_actions)}
        for action, index in grid_dict.items():
            if index != page_dict[action]:
                raise CVTestStepFailure(f"Order of {grid_actions} doesn't match with {page_actions}")
        self.log.info("Order of grid level actions matches page level actions")

    def __validate_grouped_actions(self, grouped_actions):
        """Validates if actions are grouped properly"""
        if len(grouped_actions) > 5:
            raise CVTestStepFailure(f"Groups are more than 5 in {grouped_actions}")
        action_group_index = []
        for group in grouped_actions:
            flag = 0
            for index in range(len(groups)):
                if group[0] in groups[index]:
                    flag = 1
                    action_group_index.append(index)
                    break
            if not flag:
                raise CVTestStepFailure(f"Action {group[0]} is not present in {groups[grouped_actions.index(group)]}")

        for index in range(len(action_group_index) - 1):
            if not action_group_index[index + 1] > action_group_index[index]:
                raise CVTestStepFailure(f"Groups are not ordered properly")

        for index in range(len(action_group_index)):
            for action in grouped_actions[index]:
                if action not in groups[action_group_index[index]]:
                    raise CVTestStepFailure(f"Action {action} is not present in {groups[grouped_actions.index(group)]}")
        self.log.info("All actions are grouped properly")

    def navigate_to_solution(self):
        """Navigates to the Solutions page based on SolutionType Enum"""
        if self.__solution == "File servers":
            self.__navigator.navigate_to_file_servers()
        elif self.__solution == "Virtual machines":
            self.__navigator.navigate_to_virtual_machines()
        elif self.__solution == "Hypervisors":
            self.__navigator.navigate_to_hypervisors()
        elif self.__solution == "VM groups":
            self.__navigator.navigate_to_vm_groups()
        elif self.__solution == "Instances":
            self.__navigator.navigate_to_db_instances()
        elif self.__solution == "Databases":
            self.__navigator.navigate_to_databases()
        elif self.__solution == "Exchange":
            self.__navigator.navigate_to_exchange()
        elif self.__solution == "Office 365":
            self.__navigator.navigate_to_office365()
        elif self.__solution == "Cloud apps":
            self.__navigator.navigate_to_cloud_apps()
        elif self.__solution == "Share point":
            self.__navigator.navigate_to_sharepoint()
        elif self.__solution == "Object storage":
            self.__navigator.navigate_to_object_storage()
        elif self.__solution == "Big data":
            self.__navigator.navigate_to_big_data()
        elif self.__solution == "Archiving":
            self.__navigator.navigate_to_archiving()

    def fetch_grid_level_actions(self, name, group_by=False):
        """Gets all grid level actions"""
        self.navigate_to_solution()
        return self.table.get_grid_actions_list(name, group_by)

    def fetch_page_level_actions(self, name, group_by=False):
        """Gets all page level actions from drop down menu"""
        self.navigate_to_solution()
        self.table.access_link(name)
        self.__admin_console.wait_for_completion()
        return self.__admin_console.get_page_actions_list(group_by)

    def validate_columns_order(self):
        """Validates if all the columns in Solutions page are in order"""
        self.navigate_to_solution()
        validation_dict = {"Last backup": 0, "Application size": 1, "Plan": 2, "SLA status": 3, "Actions": 4}
        if self.__solution == "Archiving":
            validation_dict["Last archive"] = validation_dict.pop("Last backup")

        column_list = self.table.get_visible_column_names()
        if "Last backup" in column_list and "Last backup time" not in column_list:
            self.log.info("Last backup present in columns")
        if column_list.index("Name") == 0:
            self.log.info("Index of Name is 0")
        else:
            raise CVTestStepFailure(f"Index of Name is {column_list.index('Name')}")
        column_dict = {k: v for v, k in enumerate(column_list[-5:])}
        if column_dict == validation_dict:
            self.log.info(f"All the columns are in order")
        else:
            raise CVTestStepFailure(f"Columns {column_list} are not in the expected order "
                                    f"{[column for column, value in validation_dict.items()]}")

    def validate_actions(self, name):
        """Validates if all grid level actions are present in page detail actions in order"""
        list_of_actions = [action for group in list(groups.values()) for action in group]
        grid_actions_list = self.fetch_grid_level_actions(name)
        page_actions_list = self.fetch_page_level_actions(name)
        for index in range(len(grid_actions_list)-1):
            if not list_of_actions.index(grid_actions_list[index+1]) > list_of_actions.index(grid_actions_list[index]):
                raise CVTestStepFailure(f"{grid_actions_list[index+1]} is not in order")
        for index in range(len(page_actions_list)-1):
            if not list_of_actions.index(page_actions_list[index+1]) > list_of_actions.index(page_actions_list[index]):
                raise CVTestStepFailure(f"{page_actions_list[index+1]} is not in order")
        diff_grid_actions = [element for element in grid_actions_list if element not in page_actions_list]
        grid_actions = [element for element in grid_actions_list if element in page_actions_list]
        page_actions = [element for element in page_actions_list if element in grid_actions_list]
        self.__compare_order(grid_actions, page_actions)
        self.__check_diff_grid(diff_grid_actions)

    def validate_grouping(self, name, level):
        """Validates grouping of page level and grid level actions"""
        if level == "grid level":
            grid_actions_groups = self.fetch_grid_level_actions(name, group_by=True)
            self.__validate_grouped_actions(grid_actions_groups)

        if level == "page_level":
            page_actions_groups = self.fetch_page_level_actions(name, group_by=True)
            self.__validate_grouped_actions(page_actions_groups)
