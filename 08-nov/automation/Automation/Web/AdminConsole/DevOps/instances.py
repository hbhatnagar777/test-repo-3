from Web.AdminConsole.Components.wizard import Wizard

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Instances file has the functions to operate on app page in Git Apps.

Instances:

    select_all_instances_view         --     Select All instances view in Git apps page

    access_instance                   --     Access Instance

    add_azuredevops_instance          --     Add Azure DevOps App

    add_github_instance               --     Add GitHub App

    access_backup_history             --     Access backup history

    access_restore_history            --     Access restore history

    access_restore                    --     Access restore of specified Instance

    is_instance_exists                --     Check if Instance exists

    delete_instance                   --     Delete Instance

AzureDevOps:

    add_azure_details                 --    Add azure details in the client creation form

GitHub:

    add_git_details                   --    Add git details in the client creation form

"""
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import DropDown
from Web.AdminConsole.Components.panel import RDropDown
from Web.Common.page_object import PageService, WebAction
from Web.Common.exceptions import CVWebAutomationException


class Instances:
    """
    Instances class has the functions to operate on Apps page in Git Apps.
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__table = Table(admin_console)
        self.__rtable = Rtable(admin_console)

    @WebAction()
    def __click_add_app(self, app_type):
        """Click on the given app type icon in Add Git Apps Panel"""
        self._admin_console.click_by_id(app_type)

    @PageService()
    def select_all_instances_view(self):
        """Select All instances view in Git apps page"""
        self.__table.view_by_title('All')

    @PageService()
    def access_instance(self, instance):
        """
        Access Instance
        Args:
            instance                         (String)       --    App name
        """
        self.__rtable.access_link(instance)

    @PageService()
    def add_azuredevops_instance(self):
        """Add Azure DevOps App"""
        self.__rtable.access_toolbar_menu('Add app')
        self.__click_add_app('34')
        self._admin_console.click_by_id("Submit")
        return AzureDevOps(self._admin_console)

    @PageService()
    def add_github_instance(self):
        """Add GitHub App"""
        self.__rtable.access_toolbar_menu('Add app')
        self.__click_add_app('33')
        self._admin_console.click_by_id("Submit")
        return GitHub(self._admin_console)

    @PageService()
    def access_backup_history(self, instance):
        """
        Access backup history
        Args:
            instance                       (String)       --     App name
        """
        self.__table.access_action_item(instance, 'Backup history')

    @PageService()
    def access_restore_history(self, instance):
        """
        Access restore history
        Args:
            instance                       (String)       --     App name
        """
        self.__table.access_action_item(instance, 'Restore history')

    @PageService()
    def access_restore(self, instance='default'):
        """
        Access restore of specified Instance
        Args:
            instance                   (String)          --     App name
        """
        self.__table.access_action_item(instance, 'Restore')

    @PageService()
    def is_instance_exists(self, instance):
        """Check if Instance exists"""
        return self.__rtable.is_entity_present_in_column('Name', instance)

    @PageService()
    def delete_instance(self, instance):
        """
        Delete app
        Args:
            instance                       (String)       --     Instance name
        """
        self.__rtable.access_action_item(instance, "Delete")
        self._admin_console.fill_form_by_id('confirmText','DELETE')
        self._admin_console.click_button('Delete')
        self._admin_console.wait_for_completion()


class AzureDevOps:
    """Add Azure DevOps App"""

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__dropdown = DropDown(admin_console)
        self.__rdropdown = RDropDown(admin_console)
        self._wizard = Wizard(admin_console)

    @PageService()
    def add_azure_details(self, access_token, organization_name, access_nodes, plan_name,
                          accessnodes_type, app_name="automation_app", token_name="automation",
                          azure_services=None, staging_path=None, impersonate_user=False, fetch_org=False):
        """
        Add azure details in the client creation form
        Args:
            access_token            (str)   -- personal access token

            organization_name       (str)   -- name of the organization

            access_nodes            (list)  -- list of access nodes to select

            plan_name               (str)   -- plan name to select

            accessnodes_type        (str)  -- type of access nodes to select

            app_name                (str)   -- name of instance/app

            token_name              (str)   -- token name

            azure_services          (list)  --  List of azure services

            staging_path            (str)   -- staging path

            impersonate_user        (dict)  -- impersonation details
                Dictionary contains the keys username and password
                    username    (str)  --   username to be impersonated
                    password    (str)  --   password to be impersonated
                default - False is used for no impersonation
            fetch_org               (bool)  -- org fetch failure will raise exception
        """

        self._wizard.select_plan(plan_name)

        self._wizard.click_next()

        self._admin_console.fill_form_by_id('appName', app_name)
        self._admin_console.fill_form_by_id('tokenName', token_name)
        self._admin_console.fill_form_by_id('accessToken', access_token)

        self._wizard.click_next()

        if accessnodes_type is not None and accessnodes_type.lower() == "unix":
            self._admin_console.select_radio('INCREMENTAL')
        self.__rdropdown.select_drop_down_values(
            drop_down_id='accessNode',
            values=access_nodes)
        if staging_path is not None:
            self._admin_console.fill_form_by_id('stagingPath', staging_path)
        if impersonate_user:
            username = impersonate_user.get('username')
            password = impersonate_user.get('password')
            if username is not None and password is not None:
                self._admin_console.enable_toggle(0, cv_toggle=True)
                self._admin_console.checkbox_deselect("toggleFetchCredentials")
                self._admin_console.fill_form_by_name("userName", username)
                self._admin_console.fill_form_by_name("password", password)
                self._admin_console.click_button_using_text('Save')

        self._wizard.click_next()
        try:
            self.__rdropdown.select_drop_down_values(drop_down_id='organizationName',
                                                     values=[organization_name])
        except Exception as excp:
            if not fetch_org:
                self._admin_console.fill_form_by_id('accountName', organization_name)
            else:
                raise CVWebAutomationException(f"Organization auto fetch failed with {excp}")

        self._wizard.click_submit()
        self._admin_console.wait_for_completion()
        self._admin_console.check_error_message()


class GitHub:
    """Add GitHub App"""

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__dropdown = DropDown(admin_console)
        self.__rdropdown = RDropDown(admin_console)
        self._wizard = Wizard(admin_console)

    @PageService()
    def add_git_details(self, access_token, organization_name, access_nodes, plan_name,
                        accessnodes_type, app_name="automation_app", token_name="automation",
                        host_url="https://api.github.com", account_type=None, staging_path=None,
                        impersonate_user=False, fetch_org=False):
        """
        Add git details in the client creation form
        Args:
            access_token            (str)   -- personal access token

            organization_name       (str)   -- name of the organization

            access_nodes            (list)  -- list of access nodes to select

            plan_name               (str)   -- plan name to select

            accessnodes_type        (str)   -- type of access nodes to select

            account_type            (str)   -- type of the account

            app_name                (str)   -- name of instance/app

            token_name              (str)   -- token name

            host_url                (str)   -- host url of git server

            staging_path            (str)   -- staging path

            impersonate_user        (dict)  -- impersonation details
                Dictionary contains the keys username and password
                    username    (str)  --   username to be impersonated
                    password    (str)  --   password to be impersonated
                default - False is used for no impersonation
            fetch_org               (bool)  -- org fetch failure will raise exception
        """
        self._wizard.select_plan(plan_name)

        self._wizard.click_next()

        if host_url is None:
            host_url = "https://api.github.com"

        self._admin_console.fill_form_by_id('appName', app_name)
        self._admin_console.fill_form_by_id('hostURL', host_url)
        self._admin_console.fill_form_by_id('tokenName', token_name)
        self._admin_console.fill_form_by_id('accessToken', access_token)

        self._wizard.click_next()

        if accessnodes_type is not None and accessnodes_type.lower() == "unix":
            self._admin_console.select_radio('INCREMENTAL')
        self.__rdropdown.select_drop_down_values(
            drop_down_id='accessNode',
            values=access_nodes)
        if staging_path is not None:
            self._admin_console.fill_form_by_id('stagingPath', staging_path)
        if impersonate_user:
            username = impersonate_user.get('username')
            password = impersonate_user.get('password')
            if username is not None and password is not None:
                self._admin_console.enable_toggle(0, cv_toggle=True)
                self._admin_console.checkbox_deselect("toggleFetchCredentials")
                self._admin_console.fill_form_by_name("userName", username)
                self._admin_console.fill_form_by_name("password", password)
                self._admin_console.click_button_using_text('Save')

        self._wizard.click_next()

        if account_type is None:
            account_type = 'Business/Institution'
        self.__rdropdown.select_drop_down_values(drop_down_id='accountType',
                                                 values=[account_type])
        try:
            self.__rdropdown.select_drop_down_values(drop_down_id='organizationName',
                                                     values=[organization_name])
        except Exception as excp:
            if not fetch_org:
                self._admin_console.fill_form_by_id('accountName', organization_name)
            else:
                raise CVWebAutomationException(f"Organization auto fetch failed with {excp}")

        self._wizard.click_submit()
        self._admin_console.wait_for_completion()
        self._admin_console.check_error_message()