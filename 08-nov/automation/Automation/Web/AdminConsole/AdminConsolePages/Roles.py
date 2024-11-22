# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Roles page on the AdminConsole

Class:

    Roles()

Functions:

add_role()                      -- adds a new role to the admin console
edit_role()                     -- Edits a role with the given permissions
action_delete_role()            -- Adds a new role with the given
toggle_given_permissions()      -- Selects the permissions passed as argument
toggle_permission_checkbox()    -- Checks/un-checks the permission checkbox
expand_category()               -- Expands the category to display the permissions under
                                   the category
list_roles()                    -- Lists all the roles
scrape_available_permissions()  -- Method to get list of all available permissions
edit_role_name()                -- Method to edit role name
is_role_exists()                -- Method to check if a role exists
select_role()                   -- Method to visit role details page
get_permissions_tree()          -- Method to get permissions of Role from panel
search_for()                    -- searches a string in the search bar and return all the roles listed
"""
from selenium.webdriver.common.by import By

from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RPanelInfo, RDropDown
from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.Components.core import TreeView
from Web.AdminConsole.Components.dialog import RModalDialog, Form
from Web.AdminConsole.Components.page_container import PageContainer


class Roles:
    """
    Roles page class
    """

    def __init__(self, admin_console):
        self.__rtable = Rtable(admin_console)
        self.__rmodal_dialog = RModalDialog(admin_console)
        self.__rdropdown = RDropDown(admin_console)
        self.__form = Form(admin_console)
        if admin_console:
            self.__rpanel = RPanelInfo(admin_console=admin_console)
            self.__tree = TreeView(admin_console)
            self.admin_console = admin_console
            self.__alert = Alert(admin_console)
            self.driver = admin_console.driver
            self.__page_container = PageContainer(admin_console)

    @PageService()
    def add_role(self,
                 role_name: str,
                 permissions: list,
                 enable_role: bool = True,
                 visible_to_all: bool = False,
                 **kwargs):
        """
        Adds a new role with the given permissions

        Args:
            role_name (str)             : the name of the role
            permissions (list)          : the list of all permissions associated with the role
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
            enable_role    (bool)       : Pass True to select Enable role checkbox, False to deselect
            visible_to_all (bool)       : Pass True to select Visible to all checkbox, False to deselect

            **kwargs:

                service_commcells (list)    : List of service commcell on which this role has to be created (GCM Feature)
                is_tenant   (bool)          : pass true if role is created as a tenant else false

        Returns:
            None
        """
        self.__rtable.access_toolbar_menu('Add role')
        self.__form.fill_text_in_field("name", role_name)
        self.__tree.select_items(permissions)

        if enable_role:
            self.__form.checkbox.check(id="enableRole")
        else:
            self.__form.checkbox.uncheck(id="enableRole")

        if not kwargs.get('service_commcells', None) and not kwargs.get('is_tenant', False):
            if visible_to_all:
                self.__form.checkbox.check(id="visibleToAll")
            else:
                self.__form.checkbox.uncheck(id="visibleToAll")

        if service_commcells := kwargs.get('service_commcells', None):
            self.__rdropdown.select_drop_down_values(drop_down_id='GlobConfigInfoCommCellId', values=service_commcells)

        self.admin_console.submit_form(wait=False)
        self.__alert.check_error_message(30)
        self.admin_console.check_error_message()
        self.admin_console.wait_for_completion()

    def __parse_list(self, permission_tree_list):
        temp = []
        for permission in permission_tree_list:
            if isinstance(permission, dict):
                temp += self.__parse_list(list(permission.values())[0])
            else:
                temp.append(permission)
        return temp

    @PageService()
    def edit_role_name(self, new_name):
        """Method to edit role name"""
        self.__page_container.edit_title(new_name)

    @PageService()
    def edit_role(self, old_role_name, new_role_name, roles_info=None, enable_role=False, visible_to_all=True):
        """
        Edits a role with the given permissions

        Args:
            old_role_name (str) : the current name of the role
            new_role_name (str) : the new name of the role
            roles_info (dict)   : it contains the roles to be added and removed as list
                              E.g. {
                                    "Add":[{"Region Management":["Create Region",
                                                                 "Edit Region"]
                                           },
                                           "Monitoring Policy"
                                    ],
                                    "Remove":["Access Policies",
                                              {"Developer Tools":[{"Datasource":["Add Datasource"]
                                                                  }
                                                                ]
                                              }
                                    ]
                                    }
            enable_role    (bool) : Pass True to select Enable role checkbox, False to deselect
            visible_to_all (bool) : Pass True to select Visible to all checkbox, False to deselect

        Returns:
            None
        """
        self.__rtable.search_for(old_role_name)
        self.__rtable.access_action_item(old_role_name, 'Edit')

        self.__rmodal_dialog.fill_text_in_field("name", new_role_name)

        if roles_info:
            self.__tree.unselect_items(roles_info["Remove"])
            self.__tree.show_all()
            self.__tree.select_items(roles_info["Add"])

        if enable_role:
            self.__rmodal_dialog.checkbox.check(id="enableRole")
        else:
            self.__rmodal_dialog.checkbox.uncheck(id="enableRole")

        if visible_to_all:
            self.__rmodal_dialog.checkbox.check(id="visibleToAll")
        else:
            self.__rmodal_dialog.checkbox.uncheck(id="visibleToAll")

        self.__rmodal_dialog.click_submit(wait=False)
        self.__alert.check_error_message(30)
        self.admin_console.check_error_message()
        self.admin_console.wait_for_completion()

    @PageService()
    def action_delete_role(self, role_name: str, company: str = None):
        """
        Deletes the role with the given name
        Args:
            role_name (str): the name of the role
            company (str)   : name of the company role belongs to

        Returns:
            None
        """
        self.__rtable.select_company(company if company else 'All')
        self.__rtable.access_action_item(role_name, "Delete")
        self.admin_console.click_button('Yes')
        self.admin_console.check_error_message()

    @PageService()
    def toggle_given_permissions(self, permissions_list, select=True):
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
                self.toggle_permission_checkbox(str(permission), select)

            elif isinstance(permission, dict):
                for key, value in permission.items():
                    self.expand_category(str(key))
                    self.toggle_given_permissions(value, select)

            else:
                raise Exception("Invalid permission")

    @WebAction()
    def toggle_permission_checkbox(self, permission, select=True):
        """
        Method to select/deselect a permission.
        Args:
            permission (str) : permission to be selected/deselected
            select (bool)    : pass True or False to select or deselect permission
        """

        permission_checkbox_xpath = f"//div[@title='{permission}']/span[2]/span/input"
        permission_checkbox_element = \
            self.driver.find_element(By.XPATH, permission_checkbox_xpath)

        if select:
            if not permission_checkbox_element.is_selected():
                permission_checkbox_element.click()

        else:
            if permission_checkbox_element.is_selected():
                permission_checkbox_element.click()

    @WebAction()
    def expand_category(self, category):
        """
        Expand the category to access permissions in that category

        Args:
            category (str): Category to be expanded
        """
        expand_permission_xpath = f"//div[@title='{category}']/span[1]"
        category_li_xpath = f"//div[@title='{category}']/.."
        category_li_element = self.driver.find_element(By.XPATH, category_li_xpath)
        category_li_class = category_li_element.get_attribute("class")

        if "ivh-treeview-node-collapsed" in category_li_class:
            self.driver.find_element(By.XPATH, expand_permission_xpath).click()

    @PageService()
    def is_role_exists(self, role_name):
        """Checks if specified role name exists on Roles page"""
        return self.__rtable.is_entity_present_in_column(column_name='Role name', entity_name=role_name)

    @PageService()
    def select_role(self, role):
        """Selects the given role from listing page"""
        self.__rtable.access_link(role)

    @PageService()
    def reset_filters(self):
        """Method to reset the filters applied on the page"""
        self.__rtable.reset_filters()

    @WebAction()
    def list_roles(self, company_name: str = str()):
        """
        Lists all the roles

        Args:
            company_name       (str):      To filter/ fetch roles of a particular company

        Returns:
            Roles List
        """
        if company_name:
            self.__rtable.select_company(company_name)
        return self.__rtable.get_column_data(column_name='Role name', fetch_all=True)

    @WebAction()
    def get_permissions_tree(self):
        """Method to get list of permissions in role

        Returns:
            (dict)  : dict with parent list item key and list of its children value
                      example (permissions panel in role details) - {
                          'permission_category1': ['permission1', 'permission2'],
                          'permission_category2': ['permissionX', ...],
                          ...
                      }
        """
        return RPanelInfo(self.admin_console, "Permissions").get_tree_list()

    @PageService()
    def search_for(self, search_string: str) -> list:
        """
        Method to search a string in the search bar and return all the roles listed
        Args:
            search_string(str): string to search for

        returns:
            list : list of plans matching the string
        """
        self.__rtable.search_for(search_string)
        res = self.__rtable.get_column_data(column_name='Role name')
        return res

