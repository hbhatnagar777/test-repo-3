# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
AccessControl page on the AdminConsole

Class:
    AccessControl()

Functions:

access_tile_settings()          -- Click on edit link
toggle_given_permissions()      -- Selects the permissions passed as argument
toggle_owner_permission_checkbox()    -- Checks/un-checks the permission checkbox
expand_category()               -- Expands the category to display the permissions under the category
scrape_available_permissions()  -- Method to get list of all available permissions
list_all_current_owner_permissions()    -- Lists all currently selected owner permissions
toggle_automatic_ownership_assignment() -- select automatic ownership options
"""
from selenium.webdriver.common.by import By

from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.dialog import ModalDialog
from Web.Common.exceptions import CVWebAutomationException

class AccessControl:
    """
    AccessControl page class
    """

    def __init__(self, admin_console):
        self.admin_console = admin_console
        self.__driver = self.admin_console.driver
        self.__panel_info = RPanelInfo(self.admin_console, 'Automatic laptop ownership assignment')
        self.__dialog = ModalDialog(self.admin_console)

    @PageService()
    def toggle_given_owner_permissions(self, permissions_list, select=True):
        """
        Method to expand categories and select/deselect permissions

        permissions_list (list): List of permissions to be selected/deselected
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

        select          (bool): Pass True or False to select/deselect permissions
                                 provided in the permissions_list parameter

        """
        for permission in permissions_list:

            if isinstance(permission, str):
                if 'Operations on Storage Policy' in permission:
                    permission = "Operations on Storage Policy \\  Copy"
                self.toggle_owner_permission_checkbox(str(permission), select)

            elif isinstance(permission, dict):
                for key, value in permission.items():
                    self.expand_category(str(key))
                    self.toggle_given_owner_permissions(value, select)

            else:
                raise Exception("Invalid permission")

    @WebAction()
    def toggle_owner_permission_checkbox(self, permission, select=True):
        """
        Method to select/deselect a permission.
        Args:
            permission (str) : permission to be selected/deselected
            select (bool)    : pass True or False to select or deselect permission
        """

        permission_checkbox_xpath = f"//div[@title='{permission}']/span[2]/span/input"
        permission_checkbox_element = \
            self.__driver.find_element(By.XPATH, permission_checkbox_xpath)

        if select:
            if not permission_checkbox_element.is_selected():
                permission_checkbox_element.click()

        else:
            if permission_checkbox_element.is_selected():
                permission_checkbox_element.click()

    @WebAction()
    def access_tile_settings(self):
        """ Method to access tile settings """
        tile_setting_icon = self.__driver.find_element(By.XPATH, 
            f"//cv-tile-component[@data-title='Owner permissions']"
            f"//div[contains(@class,'page-details-box-links')]//a[contains(text(),'Edit')]")
        tile_setting_icon.click()

    @WebAction()
    def expand_category(self, category):
        """
        Expand the category to access permissions in that category

        Args:
            category (str): Category to be expanded
        """
        expand_permission_xpath = f"//div[@title='{category}']/span[1]"
        category_li_xpath = f"//div[@title='{category}']/.."
        category_li_element = self.__driver.find_element(By.XPATH, category_li_xpath)
        category_li_class = category_li_element.get_attribute("class")

        if "ivh-treeview-node-collapsed" in category_li_class:
            self.__driver.find_element(By.XPATH, expand_permission_xpath).click()

    @WebAction()
    def scrape_available_owner_permissions(
            self,
            permission_xpath="//ul[@class='ivh-treeview']/li/div/div/ul/li/div/span[3]"):
        """
            Method to get list of all available owner permissions
            params:
                permission_xpath
            Append All Permissions manually to main categories

        """
        owner_permission_elements = self.__driver.find_elements(By.XPATH, permission_xpath)
        owner_permissions = []

        for element in owner_permission_elements:
            sub_permission_xpath = \
                f"//li/div[@title='{element.text}']/span[3]/../div/ul/li/div/span[3]"
            element.click()
            if element.text and self.__driver.find_elements(By.XPATH, sub_permission_xpath):
                perm_dict = dict()
                perm_dict[element.text] = self.scrape_available_owner_permissions(sub_permission_xpath)
                owner_permissions.append(perm_dict)
            else:
                owner_permissions.append(element.text)
            element.click()

        return owner_permissions

    @WebAction()
    def list_all_current_owner_permissions(self):
        """
        Lists all currently selected owner permissions
              Returns:  current owner permissions List
        """
        current_owner_permissions_list = []

        if(self.admin_console.check_if_entity_exists(
                "xpath",
                "//*[@id='tileContent_Owner permissions']/div[@class='info-place-holder']")):
            return current_owner_permissions_list

        elements = self.__driver.find_elements(By.XPATH, "//*[@id='tileContent_Owner permissions']/ul")
        for elem in elements:
            current_owner_permissions_list.append(elem.find_element(By.XPATH, "./li/span").text)
        current_owner_permissions_list.sort()

        return current_owner_permissions_list

    @PageService()
    def disable_laptop_assign_owners(self):
        """
            Disable automatic laptop ownership assignment
        """
        self.__panel_info.disable_toggle("Assign laptop owners automatically")

    @PageService()
    def edit_laptop_ownership(self):
        """
            edit laptop ownership assignment
        """
        self.__panel_info.edit_tile_entity('Laptop owner options')

    @PageService()
    def cancel_ownership_assignment(self):
        """
            close laptop ownership modal
        """
        self.__dialog.click_cancel()

    @PageService()
    def save_ownership_assignment(self):
        """
            save ownership assignment configuration
        """
        self.__dialog.click_submit()

    @WebAction()
    def select_ownership_choice(self, option, text=None):
        """
        to select ownership option

        Args:
            option ([string]): ownership option label that is to be selected
            text (string): User groups if third option is selected
        """
        # select option
        if text is not None:
            self.__panel_info.select_radio_button_and_type(option=option, type_text=True, text=text)
        else:
            self.__panel_info.select_radio_button_and_type(option=option, type_text=False, text=text)

    @PageService()
    def toggle_automatic_ownership_assignment(self, option="", user_groups=[]):
        """
        Method to edit ownership assignment

        Args:
            option ([int]): ownership assignment choice integer
            enable (bool, optional): whether to enable or disable automatic ownership. Defaults to True.
            user_groups (list, optional): list of user groups for option 3. Defaults to [].

        Raises:
            Exception: No user groups provided
            Exception: Invalid Option Selection
        """
        self.admin_console.click_button(self.admin_console.props['label.laptopOwnerOptions'])
        self.edit_laptop_ownership()
        if option == self.admin_console.props['label.allUserGroups']:
            if not user_groups or len(user_groups) < 1:
                self.cancel_ownership_assignment()
                raise CVWebAutomationException("No user groups provided")
            text = ",".join(user_groups)
            self.select_ownership_choice(option, text)
        elif option == self.admin_console.props['label.allUserProfiles'] or option == \
                self.admin_console.props['label.firstUser']:
            self.select_ownership_choice(option)
        else:
            raise CVWebAutomationException("Invalid Option Selection")
        # save the settings
        self.save_ownership_assignment()
