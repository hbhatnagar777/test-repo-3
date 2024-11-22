# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations on Global search bar.

Class:

    GlobalSearchHelper()

Functions:

    verify_action_launches_panel()      -   verifies the global search actions that opens a panel
    verify_action_redirects()           -   verifies the global search actions that redirects to a new page
    verify_page_header()                -   verifies if the header text is present on the panel/page
    verify_fs_hypervisor_actions()      -   verifies the actions for FS servers
    verify_server_group_actions()       -   verifies the actions for server groups
    verify_user_actions()               -   verifies the actions for users
    verify_user_group_actions()         -   verifies the actions for user groups
    verify_company_actions()            -   verifies the actions for companies
    verify_vm_actions()                 -   verifies the actions for VM
    verify_vm_group_actions()           -   verifies the actions for VM groups
    validate_global_entity_search()     -   checks if an entity is present in global search result
    validate_add_entities()             -   verifies the /ADD functionality from global search
    add_single_user()                   -   method to add a new test user
    add_user_groups()                   -   method to add a new test user group
    add_server_back_up_plan()           -   method to add a new test server backup plan
    add_roles()                         -   method to add a new test role
    add_companies()                     -   method to add a new test company
    add_server_group()                  -   method to add a new test server group

"""

from Web.AdminConsole.Components.panel import RModalPanel, RDropDown
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.core import TreeView
from Web.Common.exceptions import CVWebAutomationException
from datetime import datetime


class GlobalSearchHelper:
    """Admin console helper for global search operations"""

    def __init__(self, admin_console):
        """
                Helper for global search related actions

                Args:

                    admin_console   (object)    -- admin_console object

        """

        self.__admin_console = admin_console
        self.__navigator = self.__admin_console.navigator
        self.__driver = self.__admin_console.driver
        self.log = self.__admin_console.log
        self.__panel = RModalPanel(self.__admin_console)
        self.__table = Table(self.__admin_console)
        self.__wizard = Wizard(self.__admin_console)
        self.__admin_console.load_properties(self)

    def verify_action_launches_panel(self, action_dict: dict, entity: str, display_name: str):
        """
        Method to verify if action launches correct panel

            Args:
                action_dict     (dict) -    contains action as key and [panel name, panel operation] as value
                e.g. {"Restart services": ['Confirm', "No"]}
                entity           (str) -    Type of entity to perform the actions
                display_name     (str) -    display name of the entity

        """
        for action, header in action_dict.items():

            self.__navigator.manage_entity_from_search_bar(entity, display_name, action, reset=True)
            self.__admin_console.wait_for_completion()
            if header[0] == self.__panel.title():
                self.log.info(f"{entity} action {action} launches correct panel")
                self.__admin_console.click_button_using_text(header[1])
                self.__admin_console.wait_for_completion()
            else:
                raise CVWebAutomationException(f"{entity} action {action} does not launch correct panel")

    def verify_action_redirects(self, action_dict: dict, entity: str, display_name: str):
        """
        Method to verify action redirects to correct page

            Args:
                action_dict     (dict) -    contains action as key and [panel name, panel operation] as value
                e.g. {"Restart services": ['Confirm', "No"]}
                entity           (str) -    Type of entity to perform the actions
                display_name     (str) -    display name of the entity

        """
        for action, header in action_dict.items():

            self.__navigator.manage_entity_from_search_bar(entity, display_name, action, reset=True)
            self.__admin_console.wait_for_completion()
            if self.verify_page_header(header):
                self.log.info(f"{entity} action {action} launches correct page")

                if self.__admin_console.check_if_entity_exists("xpath",
                                                               "//button[contains(.,'Cancel')]"):
                    self.__admin_console.click_button_using_text("Cancel")
                elif self.__admin_console.check_if_entity_exists("xpath",
                                                                 "//button[contains(.,'No')]"):
                    self.__admin_console.click_button_using_text("No")
                else:
                    pass
                self.__admin_console.wait_for_completion()
            else:
                raise CVWebAutomationException(f"{entity} action {action} does not launch correct page")

    def verify_page_header(self, header_text: str) -> bool:
        """
        method to check if the header text is present on the panel/page

            Args:
                header_text (str)   -   header string displayed on the panel/page

            Returns :
                (bool)  -   True if header text is present on the page else false
        """

        if self.__admin_console.check_if_entity_exists("xpath",
                                                       f"//h1[contains(text(),'{header_text}')]"):
            return True
        elif self.__admin_console.check_if_entity_exists("xpath",
                                                        f"//h2[contains(text(),'{header_text}')]"):
            return True
        elif self.__admin_console.check_if_entity_exists("xpath",
                                                        f"//h4[contains(text(),'{header_text}')]"):
            return True
        elif self.__admin_console.check_if_entity_exists("xpath",
                                                        f"//h5[contains(text(),'{header_text}')]"):
            return True
        else:
            return False

    def verify_fs_hypervisor_actions(self, display_name, entity_flag=0):
        """
        Method to verify global search launches correct panel for actions of file servers

        Args:

            display_name   (str):  Display name of file server

            entity_flag    (int): Pass 0 for file server, 1 for hypervisor

        """
        # action_panels_dict contains action and panel header value pairs for actions that launch a panel
        actions_panels_dict = {"Add software": "Add software",
                               "Edit plan association": "Edit plan",
                               "Restore": "Restore",
                               "Back up": "Backup",
                               "Uninstall software": "Uninstall software",
                               "Release license": "Release license"
                               }
        # actions_redirect_dict contains action and page header value pairs for actions that redirect to a page
        actions_redirect_dict = {"View jobs": "Job history",
                                 "Update software": "Confirm software update",
                                 "Check readiness": "Check readiness",
                                 "Send logs": "Send log files of",
                                 "Retire": "Confirm retire client"}

        if entity_flag == 0:
            entity = "File servers"
        elif entity_flag == 1:
            entity = "Hypervisors"
        else:
            raise CVWebAutomationException("Invalid entity flag")

        self.verify_action_launches_panel(actions_panels_dict, entity, display_name)
        self.verify_action_redirects(actions_redirect_dict, entity, display_name)

    def verify_server_group_actions(self, server_group: str, delete_flag: bool = True):
        """
        Method to verify server group actions

        Args:

            server_group        (str):  Name of server group
            delete_flag     (bool): flag to decide whether to delete the entity

        """

        # actions_dict contains action as key and [panel name, panel operation] as value
        actions_dict = {
            self.__admin_console.props["action.commonAction.upgradeSoftware"]:
                [self.__admin_console.props["header.upgradeSoftware"], "No"],
            self.__admin_console.props["action.commonAction.repairSoftware"]:
                [self.__admin_console.props["header.repairSoftware"], "No"],
            self.__admin_console.props["label.manageTags"]:
                [self.__admin_console.props["label.manageTags"], "Cancel"],
            self.__admin_console.props["action.commonAction.changeCompany"]:
                [self.__admin_console.props["header.company.editCompany"], "Cancel"],
            self.__admin_console.props["action.commonAction.pushNetworkConf"]:
                [self.__admin_console.props["label.confirmPushNetworkConfiguration"], "Cancel"],
            self.__admin_console.props["label.globalActions.restartServices"]:
                [self.__admin_console.props["label.confirmAction"], "No"],
            self.__admin_console.props["label.globalActions.delete"]:
                [self.__admin_console.props["header.deleteClientGroup"], "Yes" if delete_flag else "No"]
            }

        # actions_redirect_dict contains action and page header value pairs for actions that redirect to a page
        actions_redirect_dict = {
            self.__admin_console.props["label.globalActions.editClientGroupAssociations"]:
                self.__admin_console.props["label.globalActions.editClientGroupAssociations"],
            self.__admin_console.props["label.clone"]: self.__admin_console.props["label.clone"],
            self.__admin_console.props["label.viewJobs"]: self.__admin_console.props["label.jobHistory"],
            self.__admin_console.props["action.commonAction.sendLogs"]:
                self.__admin_console.props["label.pageHeader"]
                 }

        self.verify_action_redirects(actions_redirect_dict, "Server groups", server_group)
        self.verify_action_launches_panel(actions_dict, "Server groups", server_group)

    def verify_user_actions(self, user: str, delete_flag: bool = True):
        """
        Method to verify user actions

        Args:

            user        (str):  Name of user
            delete_flag     (bool): flag to decide whether to delete the entity

        """

        # actions_dict contains action as key and [panel name, panel operation] as value
        actions_dict = {self.__admin_console.props["label.globalActions.delete"]:
                [self.__admin_console.props["label.confirmDelete"], "Yes" if delete_flag else "No"]}
        self.verify_action_launches_panel(actions_dict, "Users", user)

    def verify_user_group_actions(self, user_group: str, delete_flag: bool = True):
        """
        Method to verify user group actions

        Args:

            user_group      (str):  Name of user group
            delete_flag     (bool): flag to decide whether to delete the entity

        """

        # actions_dict contains action as key and [panel name, panel operation] as value
        actions_dict = {self.__admin_console.props["label.globalActions.addUsers"]:
                            [self.__admin_console.props["label.globalActions.addUsers"],"Cancel"],
                        self.__admin_console.props["label.globalActions.delete"]:
                            [self.__admin_console.props["label.confirmDelete"], "Yes" if delete_flag else "No"]
                        }
        self.verify_action_launches_panel(actions_dict, "User groups", user_group)

    def __delete_company(self, company_name: str):
        """
        Method to delete company

        Args:
            company_name    (str):  Name of the company
        """
        self.__navigator.manage_entity_from_search_bar("Companies", company_name, "Delete", reset=True)
        self.__admin_console.wait_for_completion()
        self.__admin_console.fill_form_by_name("confirmText", "Permanently delete company with data loss")
        self.__admin_console.click_button_using_text("Delete")
        self.__admin_console.wait_for_completion()

    def verify_company_actions(self, company_name: str, delete_flag: bool = True):
        """
        Method to verify user group actions

        Args:

            company_name      (str):  Name of company
            delete_flag     (bool): flag to decide whether to delete the entity

        """
        # actions_dict contains action as key and [panel name, panel operation] as value
        actions_dict = {self.__admin_console.props["label.manageTags"]:
                [self.__admin_console.props["label.manageTags"], "Cancel"],
                        "Deactivate": [self.__admin_console.props["label.deactivateTitle"], "Yes"]}

        if not delete_flag:
            actions_dict.update({self.__admin_console.props["label.globalActions.delete"]
                                 : [self.__admin_console.props["action.delete"], "Cancel"]})
            self.__navigator.manage_entity_from_search_bar("Companies", company_name,'Activate', reset=True)
        self.verify_action_launches_panel(actions_dict, "Companies", company_name)
        if delete_flag:
            self.__delete_company(company_name)

    def verify_vm_actions(self, vm_name):
        """
        Method to verify virtual machine actions

        Args:

            vm_name     (str):  Name of the virtual machine

        """

        # actions_dict contains action and panel header value pairs for actions that launch a panel
        actions_dict = {"Configure replication": "Select replication group"}

        # actions_redirect_dict contains action and page header value pairs for actions that redirect to a page
        actions_redirect_dict = {"Restore": "Select restore type",
                                 "View jobs": "Job history",
                                 "View active mounts": "Active mounts"}

        self.verify_action_launches_panel(actions_dict, "Virtual machines", vm_name)
        self.verify_action_redirects(actions_redirect_dict, "Virtual machines", vm_name)

    def verify_vm_group_actions(self, vm_group_name):
        """
        Method to verify virtual machine group actions

        Args:

            vm_group_name (str)     : VM group name

        """

        # actions_dict contains action and panel header value pairs for actions that launch a panel
        actions_dict = {"Back up": "Select backup level"}

        # actions_redirect_dict contains action and page header value pairs for actions that redirect to a page
        actions_redirect_dict = {"View jobs": "Job history",
                                 "Delete": "Confirm delete"}

        self.verify_action_launches_panel(actions_dict, "VM groups", vm_group_name)
        self.verify_action_redirects(actions_redirect_dict, "VM groups", vm_group_name)

    def validate_global_entity_search(self, entity_type: str, entity_name: str) -> bool:
        """
        Method for validating entity search from global search

        Args:
            entity_type (str):  type of the entity to be searched
            entity_name (str):  name of the entity to be searched
        """
        result = self.__navigator.get_category_global_search(entity_type, entity_name)
        self.log.info(f"entities listed in global search : {result}")
        if result:
            if (entity_name in entity for entity in result):
                return True
            else:
                raise CVWebAutomationException(f"entity not listed under {entity_type}")
        else:
            raise CVWebAutomationException(f"{entity_type} not listed in global search result")

    def validate_add_entities(self, entity_type: str, **parameters) -> str:
        """
        Method to add entities using /add from global search

        Args:
            entity_type    (str):   type of entity to add
            parameters  (kwargs):   required parameters for the corresponding add method.

        Returns:
            entity  (str):  Name of the entity created
        """
        function = entity_type.replace(" ", '_').lower()
        self.__navigator.add_entity_from_search_bar(entity_type)
        self.__admin_console.wait_for_completion()
        if function.lower() in ['single_user', 'user_groups', 'server_back_up_plan', 'companies', 'server_group', 'roles']:
            entity = getattr(self, 'add_' + function)(**parameters)
            return entity
        else:
            raise CVWebAutomationException("Please pass a valid entity_type")

    def add_single_user(self, user_name: str = None, email: str = None, password: str = None) -> str:
        """
        Method to add test users

        Args:
            user_name   (str):  name of the user
            email       (str):  email of the user
            password    (str):  password for the user

        Returns:
            (str)   --  name of the user created
        """
        if not user_name:
            user_name = "GS_test_user_"+ datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')
        if not email:
            email = f"GS_{user_name}@test.com"
        if not password:
            password = "######"
        try:
            self.__admin_console.fill_form_by_id("fullName", user_name)
            self.__admin_console.fill_form_by_id("localUserName", user_name)
            self.__admin_console.fill_form_by_id("localEmail", email)
            self.__admin_console.fill_form_by_id("password", password)
            self.__admin_console.fill_form_by_id("confirmPassword", password)
            self.__admin_console.submit_form()
            self.__admin_console.wait_for_completion()
            return user_name
        except Exception as e:
            raise CVWebAutomationException(f"Unable to create User : {e}")

    def add_user_groups(self, group_name: str = None) -> str:
        """
        Method to add test user groups

        Args:
            group_name  (str):  name of the user group

        return:
            (str)   --  name of the user group created
        """
        if not group_name:
            group_name = "GS_test_user_group" + datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')

        try:
            self.__admin_console.fill_form_by_id("name", group_name)
            self.__admin_console.submit_form()
            self.__admin_console.wait_for_completion()
            return group_name
        except Exception as e:
            raise CVWebAutomationException(f"Unable to create User group : {e}")

    def add_server_back_up_plan(self, storage: str, plan_name: str = None) -> str:
        """
        Method to add  test plans

        Args:
            storage     (str):  name of the storage to be used for plan
            plan_name   (str):  name of the plan

        returns:
            (str)   --  name of the plan created
        """
        if not plan_name:
            plan_name = "GS_test_plan" + datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')

        try:
            self.__admin_console.fill_form_by_name("planName", plan_name)
            self.__admin_console.click_button(value="Next")

            self.__admin_console.click_button("Add copy")
            RDropDown(self.__admin_console).select_drop_down_values(values=[storage], drop_down_id='storageDropdown')
            self.__admin_console.click_button(value="Save")
            self.__wizard.click_next()

            self.__admin_console.click_button(value="Submit")
            self.__admin_console.wait_for_completion()
            return plan_name
        except Exception as e:
            raise CVWebAutomationException(f"Unable to create plans : {e}")

    def add_roles(self, role_name: str = None, permissions: list = None) -> str:
        """
        method to create test roles

        Args:
            role_name   (str):  name of the role
            permissions (str):  permissions to be added to the role

        returns:
            (str)   --  name of the role created
        """
        if not role_name:
            role_name = "GS_test_role" + datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')
        if not permissions:
            permissions = ['Alert']

        try:
            self.__admin_console.fill_form_by_name("name", role_name)
            TreeView(self.__admin_console).select_items(permissions)
            self.__admin_console.submit_form()
            self.__admin_console.wait_for_completion()
            return role_name
        except Exception as e:
            raise CVWebAutomationException(f"Unable to create roles : {e}")

    def add_companies(self, company_name: str = None) -> str:
        """
        Method to create test companies

        Args:
            company_name    (str):  name of the company

        returns:
            (str)   --  name of the company created
        """
        if not company_name:
            company_name = "GS_test_company" + datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')

        try:
            self.__wizard.fill_text_in_field(label=self.__admin_console.props['Companies']['label.companyName'],
                                                 text=company_name)
            self.__wizard.fill_text_in_field(label=self.__admin_console.props['Companies']['label.companyAlias'],
                                             text=company_name)
            self.__wizard.click_next()
            self.__wizard.click_button(self.__admin_console.props['Skip'])
            self.__wizard.disable_toggle('Configure plan')
            self.__wizard.click_button("Submit")
            self.__admin_console.wait_for_completion()
            return company_name
        except Exception as e:
            raise CVWebAutomationException(f"Unable to create roles : {e}")

    def add_server_group(self, group_name: str = None) -> str:
        """
        Method to create a test server group

        Args:
            group_name  (str):   name of the server group

        returns:
            (str)   --  name of the server group created
        """
        if not group_name:
            group_name = "GS_test_server_group" + datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')

        try:
            self.__admin_console.fill_form_by_id('name', group_name)
            self.__admin_console.click_button(value="Save")
            self.__admin_console.wait_for_completion()
            return group_name
        except Exception as e:
            raise CVWebAutomationException(f"Unable to create server groups : {e}")
