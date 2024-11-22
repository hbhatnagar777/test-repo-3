# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods that can be done on the application groups page.

Classes:

    AppGroups   --  This class contains all the methods for action in application groups page

    K8sAppGroup --  This class contains all methods for actions in add application group wizard

AppGroups:

    select_app_group()			--	Opens the application group with the given name

    add_application_group_from_cluster_details()    --   from cluster details, add a new application
                                                    group

    add_application_group()      --   from application group tab, add new application group

    action_backup_app_groups()   --  Backs up the given application group

    action_delete_app_groups()   --  Deletes the given application groups

    action_restore_app_group()   --  Restores the given applicationgroup

    action_jobs_app_group()      --  Opens the jobs page of the application group

    has_app_group()              --  check if application group exists

    get_details_by_app_group()   -- get table content filtered by application group

    enable_snap()                -- option to enable snap on client application creation.

K8sAppGroup:

    set_cluster()               --  Set the cluster from dropdown if present

    set_appgroup_name()         --  Set the application group name in form

    select_plan()               --  Select plan from plan dropdown

    enable_snap()			    --	Enable snap toggle

    add_backup_content()        --  Add content in add application group step

    add_filter_content()        --  Add filters in add application group step

    save()                      --  Click on save button

    next()                      --  Click on next button

"""
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Components.browse import RContentBrowse
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.panel import Backup, RDropDown
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.K8s.content import KubernetesContent
from Web.Common.page_object import PageService
from Web.Common.exceptions import CVWebAutomationException


class AppGroups:
    """
    Class for the application groups page
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self._admin_console.load_properties(self, unique=True)
        self.__table = Rtable(admin_console)
        self.__alert = Alert(admin_console)
        self.__page_container = PageContainer(admin_console)

    @PageService()
    def select_app_group(self, app_group_name):
        """
        Opens the Application group with the given name

        Args:
            app_group_name (str) :  the name of the application group to open

        """
        if self.has_app_group(app_group_name):
            self.__table.access_link(app_group_name)
        else:
            raise CVWebAutomationException(f"Application group with name [{app_group_name}] does not exist")

    @PageService()
    def select_add_application_group(self):
        """
        Opens add application group wizard from application groups page
        """

        self.__page_container.access_page_action(
            name=self._admin_console.props['AppGroups']['pageHeader.addApplication']
        )
        self._admin_console.wait_for_completion()

    @PageService()
    def action_backup_app_groups(self, app_group_name, backup_type):
        """
        Starts a backup of the given type for the specified collection

        Args:
           app_group_name (str)  : the name of the VM group to backup
           backup_type (BackupType)    : the type of backup to run, among the type in Backup.
                                        BackupType enum

        Returns:
            the backup job ID
        """
        self.__table.access_action_item(
            app_group_name, self._admin_console.props['K8sClusters']['action.commonAction.backup'])
        backup = Backup(self)
        return backup.submit_backup(backup_type)

    @PageService()
    def action_delete_app_groups(self, app_group_name):
        """
        Deletes an app group with the given name

        Args:
            app_group_name (str) : the application group to delete
        """

        if self.has_app_group(app_group_name):
            self.__table.access_action_item(app_group_name, self._admin_console.props['label.globalActions.delete'])
            self._admin_console.click_button(self._admin_console.props['label.yes'])
            self.__alert.close_popup()
            if self.has_app_group(app_group_name):
                raise CVWebAutomationException(f"Application group with name [{app_group_name}] did not get deleted")
        else:
            raise CVWebAutomationException(f"Application group with name [{app_group_name}] does not exist to delete")

    @PageService()
    def action_restore_app_groups(self, app_group_name):
        """
        Opens the restore page of the vm group from the server details page

        Args:
            app_group_name (str):  the VM group to restore

        """
        self.__table.access_action_item(app_group_name, self._admin_console.props['label.restore'])

    @PageService()
    def action_jobs_app_groups(self, app_group_name):
        """
        Lists all the jobs of the specific application group

        Args:
            app_group_name (str): the application group whose jobs should be opened
        """
        self.__table.access_action_item(app_group_name, self._admin_console.props['action.jobs'])

    @PageService()
    def has_app_group(self, app_group):
        """
        Check if app group exists
        Args:
            app_group               (str):   app group name

        Returns                    (bool): True if vm group exists or False otherwise
        """
        self.__table.reload_data()
        return self.__table.is_entity_present_in_column(
            self._admin_console.props['AppGroups']['label.serverName'], app_group
        )

    @PageService()
    def get_details_by_app_group(self, app_group):
        """
        Get table content filtered by vm group
        Args:
            app_group               (str):  app group name

        Returns:                   (Dict): table content of specified vm group

        """
        if self.has_app_group(app_group):
            return self.__table.get_table_data()
        raise CVWebAutomationException("VM group [%s] not found in vm groups page" % app_group)

    @PageService()
    def enable_snap(self):
        """
        enable Snap for kubernetes cluster on  application creation
         """
        self._admin_console.enable_toggle(index=0)
        self._admin_console.wait_for_completion()


class K8sAppGroup:
    """Class for add application group step"""

    def __init__(self, admin_console):
        self.__dropdown = RDropDown(admin_console)
        self.__table = Rtable(admin_console)
        self.__dialog = RModalDialog(admin_console)
        self.__browse = RContentBrowse(admin_console)
        self.__wizard = Wizard(admin_console)
        self.__content = KubernetesContent(admin_console)
        self.__alert = Alert(admin_console)
        self._admin_console = admin_console
        self._admin_console.load_properties(self)

    def __set_table_object(self, title):
        """Set the table object based on title"""
        self.__table = Rtable(admin_console=self._admin_console, title=title)

    @PageService()
    def set_cluster(self, cluster_name):
        """
        Set cluster
        Args:
            cluster_name        (String)      -- Set k8s cluster
        """
        if self._admin_console.check_if_entity_exists('id', 'clustersDropdown'):
            self.__wizard.select_drop_down_values(id="clustersDropdown", values=[cluster_name])

    @PageService()
    def set_appgroup_name(self, app_name):
        """
        Set application group name
        Args:
            app_name        (String)      -- Set k8s application group name
        """
        self.__wizard.fill_text_in_field(id='appGroupName', text=app_name)

    @PageService()
    def enable_snap(self):
        """
        enable Snap for kubernetes cluster on  application creation
         """
        self._admin_console.enable_toggle(index=0)
        self._admin_console.wait_for_completion()

    @PageService()
    def add_backup_content(self, backup_content=None):
        """Select backup content
        Args:
            backup_content      (dict/str/list)     -- Content to add for backup.
                                                        See _add_content() for examples
        """

        self.__content.add_content(table_header=self._admin_console.props['header.content'], content=backup_content)

    @PageService()
    def add_filter_content(self, filter_content):
        """Add filter content
        Args:
            filter_content      (list)     -- Content to filter.
                                                See _add_content() for examples
        """

        self.__content.enable_exclusion()
        self.__content.add_content(table_header=self._admin_console.props['heading.filters'], content=filter_content)

    @PageService()
    def add_backup_filters(self, backup_filters, onboarding=True):
        """Add Backup filters
        Args:
            backup_filters      (list)     -- Content to filter.
                                                See configure_backup_filters() for examples

             onboarding         (bool)     -- Flag to check if the filters are for onboarding

        """
        self.__content.enable_exclusion()
        self.__content.configure_backup_filters(
            table_header=self._admin_console.props['heading.filters'],
            content=backup_filters,
            onboarding=onboarding
        )

    @PageService()
    def save(self):
        """Click save"""
        self._admin_console.submit_form()
        self._admin_console.wait_for_completion()

    @PageService()
    def next(self):
        """Click next"""
        self.__wizard.click_next()
        self.__alert.check_error_message()
