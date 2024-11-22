from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the functions or operations that can be performed on the Big Data Apps subclient page

Subclient:

    __new__                             --  based on the subclient type, initialize the class instance accordingly

    __init__                            --  initialize object of the class

    access_overview                     --  Access overview page

    access_configuration                --  Access configuration page

    enable_backup                       --  Enable backup

    disable_backup                      --  Disable backup

    backup                              --  Runs backup using backup option from top menu

    access_backup_history               --  Access backup history from the top menu

    access_restore_history              --  Access restore history from the top menu

    backup_now                          --  Runs backup using back up now option

    access_restore                      --  Access restore from recovery points view

    restore_in_place                    --  Starts a Restore in place job

    edit_plan                           --  Edits the plan

    edit_access_nodes                   --  Method to edit access nodes

    access_backupset                    --  Access the backupset using the breadcrumb link

HDFSSubclient:

    __init__                            --  initialize object of the class

    restore_out_of_place                --  Restore out to place to different cluster

    restore_to_file_system              --  Restore to file system server

KuduSubclient:

   __init__                             --  initialize object of the class

    restore_out_of_place                --  Restore out to place to different cluster

    edit_tables                         --  Method to edit tables
"""
import sys

from Web.AdminConsole.Bigdata.details import Overview, Configuration
from Web.AdminConsole.Components.content import AddContent
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.panel import Backup, DropDown, PanelInfo, RDropDown

from Web.Common.page_object import PageService


class Subclient:
    """
    Functions to operate on subclient page
    """

    def __new__(cls, admin_console, subclient="default", subclient_type=None):
        """Returns the instance of one of the Subclasses based on the subclient details.
            If subclient type is given, initialize the class instance accordingly
                supported subclient type: HDFS / Kudu
            In case of non-supported values, return the generic subclient object
        """
        if subclient_type not in ["HDFS", "Kudu"]:
            subclient_type = ""
        return object.__new__(getattr(sys.modules[__name__], f"{subclient_type}Subclient"))

    def __init__(self, admin_console, subclient="default", subclient_type=None):
        """Initializes instance of the subclient object class
        Args:
            admin_console       --  admin console object
            subclient           --  name of subclient
            subclient_type      --  type of subclient
        """
        self._admin_console = admin_console
        self._subclient = subclient
        self._subclient_type = subclient_type
        self.__table = Table(self._admin_console)
        self.__overview = Overview(self._admin_console)
        self.__configuration = Configuration(self._admin_console)

    @PageService()
    def access_overview(self):
        """Access overview page"""
        self.__configuration.access_overview()

    @PageService()
    def access_configuration(self):
        """Access configuration page"""
        self.__overview.access_configuration()

    @PageService()
    def enable_backup(self):
        """Enable backup"""
        panel = PanelInfo(self._admin_console, title='Activity control')
        panel.enable_toggle("Enable backup")

    @PageService()
    def disable_backup(self):
        """Disable backup"""
        panel = PanelInfo(self._admin_console, title='Activity control')
        panel.disable_toggle("Enable backup")
        self._admin_console.click_button_using_text("Yes")

    @PageService()
    def backup(self, backup_level=Backup.BackupType.FULL):
        """Runs backup using backup option from top menu"""
        self._admin_console.access_menu("Back up")
        return Backup(self._admin_console).submit_backup(backup_level)

    @PageService()
    def access_backup_history(self):
        """Access backup history from the top menu"""
        self.__overview.access_backup_history()

    @PageService()
    def access_restore_history(self):
        """Access restore history from the top menu"""
        self.__overview.access_restore_history()

    @PageService()
    def backup_now(self, backup_level=Backup.BackupType.FULL):
        """Runs backup using back up now option"""
        self._admin_console.select_hyperlink("Back up now")
        return Backup(self._admin_console).submit_backup(backup_level)

    @PageService()
    def access_restore(self):
        """Access restore from recovery points view"""
        self.__overview.access_instance_restore()

    @PageService()
    def restore_in_place(self, restore_content=None, overwrite=None):
        """Starts a Restore in place job
        Args:
            restore_content     (dict)  --  {paths: "paths to be selected for restore",
                                             folder: "access folder before selecting paths"}
                    default - selects all as content to be restored
            overwrite           (bool)  --  Determines if overwrite needs to be enabled
        Returns:
            job id as string
        """
        restore_content = restore_content or {}
        rest = self.__overview.set_restore_content(**restore_content)
        return rest.restore_in_place(overwrite)

    @PageService()
    def edit_plan(self, plan):
        """Edits the plan
        Args:
            plan    (str):   the name of the plan to select
        """
        self.access_configuration()
        panel = PanelInfo(self._admin_console, title="Plan")
        panel.edit_tile()
        dropdown = DropDown(self._admin_console)
        dropdown.select_drop_down_values(drop_down_id="planSummaryDropdown", values=[plan])
        self._admin_console.click_button("Save")

    @PageService()
    def edit_access_nodes(self, access_nodes):
        """Method to edit access nodes
        Args:
            access_nodes       (list)  -- list of access nodes to select
        """
        self.access_configuration()
        panel = PanelInfo(self._admin_console, title="Access nodes")
        panel.edit_tile()
        dropdown = DropDown(self._admin_console)
        dropdown.select_drop_down_values(
            drop_down_id="editHadoopNodeForm_isteven-multi-select_#2882", values=access_nodes)
        self._admin_console.click_button("Save")

    @PageService()
    def access_backupset(self, backupset=None):
        """Access the backupset using the breadcrumb link"""
        self._admin_console.select_breadcrumb_link_using_text(backupset or self._subclient_type)


class HDFSSubclient(Subclient):
    """
        Functions to operate on HDFS subclient page
    """
    def __init__(self, admin_console, subclient="default", subclient_type="HDFS"):
        """Initializes instance of the subclient object class
        Args:
            admin_console       --  admin console object
            subclient           --  name of subclient
            subclient_type      --  type of subclient
        """
        super().__init__(admin_console)
        self._admin_console = admin_console
        self._subclient = subclient
        self._subclient_type = subclient_type
        self._content = AddContent(self._admin_console)

    @PageService()
    def restore_out_of_place(self, destination_path, destination_cluster=None, restore_content=None, overwrite=None):
        """Restore out to place to different cluster
        Args:
            destination_path    (str)   --  path where data needs to be restored
            destination_cluster (str)   --  name of destination cluster
                    default - uses prefilled value from cc
            restore_content     (dict)  --  {paths: "paths to be selected for restore",
                                             folder: "folder to be selected before paths"}
                    default - selects all as content to be restored
            overwrite           (bool)  --  Determines if overwrite needs to be enabled
        Returns:
            job id as string
        """
        restore_content = restore_content or {}
        rest = self.__overview.set_restore_content(**restore_content)
        return rest.restore_out_of_place(destination_path, destination_cluster, overwrite=overwrite)

    @PageService()
    def restore_to_file_system(self, destination_path, destination_server=None, restore_content=None, overwrite=None):
        """Restore to file system server
        Args:
            destination_path    (str)   --  path where data needs to be restored
            destination_server  (str)   --  name of destination server
                    default - uses prefilled value from cc
            restore_content     (dict)  --  {paths: "paths to be selected for restore",
                                             folder: "folder to be selected before paths"}
                    default - selects all as content to be restored
            overwrite           (bool)  --  Determines if overwrite needs to be enabled
        Returns:
            job id as string
        """
        restore_content = restore_content or {}
        rest = self.__overview.set_restore_content(**restore_content)
        return rest.restore_out_of_place(destination_path, destination_server, dropdown_id="destinationClient",
                                         dest_path_id="restoreToDiskPath", overwrite=overwrite)


class KuduSubclient(Subclient):
    """
        Functions to operate on Kudu subclient page
    """

    def __init__(self, admin_console, subclient="default", subclient_type="Kudu"):
        """Initializes instance of the kudu subclient object class
        Args:
            admin_console       --  admin console object
            subclient           --  name of subclient
            subclient_type      --  type of subclient
        """
        super().__init__(admin_console)
        self._admin_console = admin_console
        self._subclient = subclient
        self._subclient_type = subclient_type

    @PageService()
    def restore_out_of_place(self, destination_path, destination_cluster=None,
                             restore_content=None, des_rename=None, overwrite=None):
        """Restore out to place to different cluster
        Args:
            destination_path    (str)   --  path where data needs to be restored
            destination_cluster (str)   --  name of destination cluster
                    default - uses prefilled value from cc
            restore_content     (dict)  --  {paths: "paths to be selected for restore",
                                            folder: "folder to be selected before paths"}
                    default - selects all as content to be restored
            des_rename          (bool)  --  renames tables at destination
                    (add '_restore' suffix for destination table names)
            overwrite           (bool)  --  Determines if overwrite needs to be enabled
        Returns:
            job id as string
        """
        restore_content = restore_content or {}
        rest = self.__overview.set_restore_content(**restore_content)
        if des_rename:
            num = 0
            id = f'{num}'
            while self._admin_console.check_if_entity_exists('id', id):
                value = self._admin_console.driver.find_element(By.ID, id).get_attribute('name')
                self._admin_console.fill_form_by_id(id, f'{value}_restore')
                num += 1
                id = f'{num}'
        return rest.restore_out_of_place(destination_path, destination_cluster, overwrite=overwrite)

    @PageService()
    def edit_tables(self, tables):
        """Method to edit tables
        Args:
            tables       (list)  -- list of tables to select as backup content
        """
        self.access_configuration()
        panel = PanelInfo(self._admin_console, title="Tables")
        panel.edit_tile()
        rdropdown = RDropDown(self._admin_console)
        rdropdown.select_drop_down_values(drop_down_id="kuduSubclientContentTable", values=tables)
        self._admin_console.click_button("Save")
