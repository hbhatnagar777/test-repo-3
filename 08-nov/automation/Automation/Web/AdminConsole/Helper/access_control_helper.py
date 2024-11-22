from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations on System - > Access Control page.

Class:

  AccessControlHelper()

Functions:

initial_owner_permissions()                 -- Save the initial owner permissions before doing any of our changes
edit_owner_permission()                     -- Edits the owner permissions
verify_owner_permissions()                  -- Verifies permissions are selected/deselected
revert_owner_permissions()                  -- Revert owner permissions to the state before test case was run
get_available_permissions()                 -- Gets all available owner permissions
_generate_sample_list()                     -- Gets a random selection of elements from the given list
_generate_random_categories()               -- Generates a random list of categories
generate_random_permissions()               -- Generates a random list of owner permissions
generate_permission_json()                  -- Finds out the proper dict path and generates it for given list
remove_head_categories()                    -- Remove those permissions which are already there in initial
randomly_generate_owner_permissions()       -- Generate permissions exclusive of any existing permissions
"""

from random import choice, sample
from Web.AdminConsole.AdminConsolePages.access_control import AccessControl
from Web.AdminConsole.Components.panel import ModalPanel


class AccessControlHelper:
    """ Helper for Access Control page """

    def __init__(self, admin_console):
        """ Initializes the access control helper module """
        self.admin_console = admin_console
        self.navigator = admin_console.navigator
        self.driver = admin_console.driver
        self.log = admin_console.log
        self.__list_of_new_owner_permissions = None
        self.__list_of_owner_permissions_to_edit = None
        self.access_control_obj = None
        self.__all_permissions = None
        self.__all_categories = None
        self.__current_owner_permissions_list = None
        self.__initial_owner_permissions_list = None
        self.__panel = ModalPanel(admin_console)

    def initial_owner_permissions(self):
        """
        Generates the list of owner permissions in proper format
        Returns: List of the initial owner permissions before testcase changed it

        """
        self.access_control_obj = AccessControl(self.admin_console)

        perm_list = self.access_control_obj.list_all_current_owner_permissions()
        self.__initial_owner_permissions_list = self.generate_permission_json(perm_list, self.__all_permissions)

        return self.__initial_owner_permissions_list

    def edit_owner_permission(self, permissions, select=True):
        """
            Edits the owner permissions by selecting or deselecting them
        Args:
            permissions: List of permissions to be added/removed from current owner permissions
            select: Select/Deselect the checkbox(Default: True)
        """

        self.access_control_obj = AccessControl(self.admin_console)
        self.access_control_obj.access_tile_settings()

        self.access_control_obj.toggle_given_owner_permissions(permissions, select)

        self.__panel.submit()

    def verify_owner_permissions(self, permissions):
        """
        Method to validate owner permissions.
        Args:
            permissions (list): List of permissions to verify
        """
        self.__current_owner_permissions_list = self.access_control_obj.list_all_current_owner_permissions()

        if 'All permissions' in permissions:
            self.log.info("Checking if owner permission 'All permissions' is present")
            if 'All permissions' not in self.__current_owner_permissions_list:
                raise Exception("'All permissions' was not associated")
        else:
            for permission in permissions:
                if isinstance(permission, str):
                    self.log.info("Checking if owner permission %s is present", permission)
                    if permission not in self.__current_owner_permissions_list:
                        raise Exception(f"Owner permission {permission} was not associated")
                elif isinstance(permission, dict):
                    for key, value in permission.items():
                        self.verify_owner_permissions(value)

    def revert_owner_permissions(self, permissions):
        """
        Method to revert owner permissions to the state before test case was run
        Args:
            permissions (list): List of permissions to revert back to
        """
        self.access_control_obj = AccessControl(self.admin_console)
        self.access_control_obj.access_tile_settings()

        # Find and remove all selected permissions by toggling 'All permissions' checkbox
        permission_checkbox_xpath = "//div[@title='All permissions']/span[2]/span/input"
        permission_checkbox_element = \
            self.driver.find_element(By.XPATH, permission_checkbox_xpath)
        if permission_checkbox_element.is_selected():
            # If all are selected simple deselect all
            permission_checkbox_element.click()
        else:
            if not permission_checkbox_element.is_selected():
                # If all is not selected then click once to select all and then click again to deselect all
                permission_checkbox_element.click()
                permission_checkbox_element.click()

        if not permissions:
            self.__panel.submit()
        else:
            self.access_control_obj.toggle_given_owner_permissions(permissions)
            self.__panel.submit()

    def get_available_owner_permissions(self):
        """ Get all categories and permissions listed on the edit owner permissions pane """
        self.access_control_obj = AccessControl(self.admin_console)
        self.access_control_obj.access_tile_settings()
        self.__all_permissions = self.access_control_obj.scrape_available_owner_permissions()
        # Append 'All permissions' to the list as one of the available options
        self.__all_permissions.append('All permissions')
        self.__panel.cancel()

    @classmethod
    def _generate_sample_list(cls, source_list):
        """Generates a sample with random elements from the given list

        Args:
            source_list (list): List of any items from which you need a random sample

        Returns:
            sample_list(list) : List of random items
        """
        list_length = len(source_list)
        no_of_items = choice(range(0, list_length))
        sample_list = sample(source_list, no_of_items)
        return sample_list

    def _generate_random_categories(self):
        """Generates a list of random categories to be selected"""
        all_categories = []
        for item in self.__all_permissions:
            if isinstance(item, str):
                all_categories.append(item)
            elif isinstance(item, dict):
                for key in item:
                    all_categories.append(key)

        self.__all_categories = self._generate_sample_list(all_categories)

    def generate_random_owner_permissions(self, all_permissions=None):
        """Generates a list of random permissions to be selected

        Args:
            all_permissions (list): List of permissions from which random permissions are
                                    to be selected
                             E.g.[
                                    "Access Policies",
                                    {"Developer Tools":["Workflow",
                                                        {"Datasource":["Add Datasource",
                                                                        "Edit Datasource"]
                                                        }]
                                    },
                                    {"Monitoring Policy":["Edit Monitoring Policy",
                                                          "Search Share"]
                                    }
                                ]
        Returns:
                random_list (list) : List of random permissions
        """
        random_list = []
        leaf_permissions = []
        if not all_permissions:
            all_permissions = self.__all_permissions

        for permission in all_permissions:
            if isinstance(permission, dict):
                perm_dict = dict()
                for key, value in permission.items():
                    if key in self.__all_categories:
                        random_list.append(key)
                    else:
                        sub_list = self.generate_random_owner_permissions(value)
                        if sub_list:
                            perm_dict[key] = sub_list
                            random_list.append(perm_dict)
            elif isinstance(permission, str):
                leaf_permissions.append(permission)

        if leaf_permissions:
            if 'All permissions' not in leaf_permissions:
                random_list = self._generate_sample_list(leaf_permissions)

        # If All permissions is selected then only keep that and remove all others
        if 'All permissions' in random_list:
            random_list = ['All permissions']

        return random_list

    def generate_permission_json(self, selected_owner_permissions_list, available_owner_permissions):
        """ Finds out the proper dict path and generates it for given list
            args:
                  untouched_owner_permissions_list (list)
                  Eg: ['Commcell','Edit Workflows']

            This method wil convert it into:
            [   'Commcell',
                {'Developer Tools':
                            [{'Workflow': 'Edit Workflow'}]
                }
            ]

            returns a new list with proper keys
        """
        new_list = []
        for permission in available_owner_permissions:
            if isinstance(permission, str) and permission in selected_owner_permissions_list:
                new_list.append(permission)
                selected_owner_permissions_list.remove(permission)
            elif isinstance(permission, dict):
                perm_dict = dict()
                for key, value in permission.items():
                    if isinstance(key, str) and key in selected_owner_permissions_list:
                        new_list.append(key)
                        selected_owner_permissions_list.remove(key)
                    else:
                        sub_new_list = self.generate_permission_json(selected_owner_permissions_list, value)
                        if sub_new_list:
                            perm_dict[key] = sub_new_list
                            new_list.append(perm_dict)

        return new_list

    def remove_head_categories(self):
        """
        Prevent editing any child permission if there already exists some child permission of that parent
        """
        head = []
        for ele in self.__initial_owner_permissions_list:
            if isinstance(ele, dict):
                for key in ele:
                    head.append(key)
            elif isinstance(ele, str):
                head.append(ele)

        copy_perm = self.__list_of_new_owner_permissions.copy()

        for index, ele in enumerate(self.__list_of_new_owner_permissions):
            if isinstance(ele, str):
                if ele in head:
                    copy_perm.remove(ele)
            elif isinstance(ele, dict):
                for key in ele.keys():
                    if key in head:
                        copy_perm.pop(copy_perm.index(self.__list_of_new_owner_permissions[index]))

        self.__list_of_new_owner_permissions = copy_perm

    def randomly_generate_owner_permissions(self):
        """
            Generate a list of owner permissions exclusive of any existing permission
        """
        self._generate_random_categories()
        self.__list_of_new_owner_permissions = self.generate_random_owner_permissions()
        self.remove_head_categories()

        return self.__list_of_new_owner_permissions
