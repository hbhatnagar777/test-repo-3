# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the functions or operations that can be performed on the Big Data Apps backupset page

Backupset:

    __new__                         --  based on the backupset name, initialize the class instance accordingly

    __init__                        --  initialize object of the class

    edit_plan                       --  Edits the plan on the backupset page

    access_subclient                --  Access specified subclient and returns its object

    access_restore                  --  Initiate subclient level restore

    backup                          --  Initiate subclient level backup

    access_backup_history           --  Accesses backup history

    access_restore_history          --  Accesses restore history

    delete_subclient                --  Deletes subclient from subclient level menu

    delete_backupset                --  Deletes backupset from top menu

HDFSBackupset:

    __init__                        --  initialize object of the class

    add_subclient                   --  Method to add new subclient

KuduBackupset:

    __init__                        --  initialize object of the class

    add_subclient                   --  Method to add new subclient
"""
import sys

from Web.AdminConsole.Bigdata.details import Overview
from Web.AdminConsole.Components.content import AddContent
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Components.panel import Backup, DropDown, PanelInfo, RDropDown

from Web.Common.page_object import PageService


class Backupset:
    """
    Functions to operate on backupset page
    """

    def __new__(cls, admin_console, backupset=None):
        """Returns the instance of one of the Subclasses based on the backupset details.
            If backupset name is given, initialize the class instance accordingly
                supported backupset subclasses: HDFS / Kudu
            In case of non-supported values, return the generic backupset object
        """
        if backupset not in ["HDFS", "Kudu"]:
            backupset = ""
        return object.__new__(getattr(sys.modules[__name__], f"{backupset}Backupset"))

    def __init__(self, admin_console, backupset=None):
        """Initializes instance of the backupset object class
        Args:
            admin_console       --  admin console object
            backupset           --  name of backupset or hadoop app
        """
        self._admin_console = admin_console
        self._backupset = backupset
        self.__overview = Overview(self._admin_console)
        self.__table = Table(self._admin_console)

    @PageService()
    def edit_plan(self, plan):
        """
        Edits the plan
        Args:
            plan    (str):   the name of the plan to select
        Raises:
              Exception:
                if there is an error with selecting a plan
        """
        panel = PanelInfo(self._admin_console, title="Plan")
        panel.edit_tile()
        dropdown = DropDown(self._admin_console)
        dropdown.select_drop_down_values(drop_down_id="planSummaryDropdown", values=[plan])
        self._admin_console.click_button("Save")

    @PageService()
    def access_subclient(self, subclient="default"):
        """Access specified subclient and returns its object"""
        self.__table.access_link(subclient)
        from Web.AdminConsole.Bigdata.subclient import Subclient
        return Subclient(self._admin_console, subclient, subclient_type=self._backupset)

    @PageService()
    def access_restore(self, sc_name='default'):
        """
        Initiate subclient level restore
        Args:
            sc_name                      (String)       --    Subclient name
        """
        self.__overview.access_restore(name=sc_name)
        from Web.AdminConsole.Bigdata.subclient import Subclient
        return Subclient(self._admin_console, sc_name, subclient_type=self._backupset)

    @PageService()
    def backup(self, sc_name='default', backup_level=Backup.BackupType.FULL):
        """
        Initiate subclient level backup
        Args:
            sc_name                      (String)       --    Subclient name
            backup_level                 (String)       --    Specify backup level from constant
                                                              present in OverView class
        """
        self.__overview.backup_now(name=sc_name, backup_level=backup_level)

    @PageService()
    def access_backup_history(self, subclient=None):
        """
        Access backup history
        Args:
            subclient                    (String)       --     subclient name
                    default - None, access from top menu else from subclient level
        """
        if subclient is None:
            self._admin_console.select_hyperlink("Backup history")
        else:
            self.__overview.access_backup_history(instance=subclient)

    @PageService()
    def access_restore_history(self, subclient=None):
        """Access restore history
        Args:
            subclient                    (String)       --     subclient name
                    default - None, access from top sub menu else from subclient level
        """
        if subclient is None:
            self._admin_console.select_hyperlink("Restore history")
        else:
            self.__overview.access_restore_history(instance=subclient)

    @PageService()
    def delete_subclient(self, subclient):
        """Deletes subclient from subclient level menu
        Args:
            subclient                    (String)       --     subclient name
        """
        self.__table.access_action_item(subclient, 'Delete')

    @PageService()
    def delete_backupset(self):
        """Deletes backupset from top menu"""
        self._admin_console.select_hyperlink("Delete")


class HDFSBackupset(Backupset):
    """
        Functions to operate on HDFS backupset page
    """
    def __init__(self, admin_console, backupset="HDFS"):
        """Initializes instance of the hdfs backupset object class
        Args:
            admin_console       --  admin console object
            backupset           --  name of backupset or hadoop app
        """
        super().__init__(admin_console, backupset)
        self._admin_console = admin_console
        self._backupset = backupset
        self._content = AddContent(self._admin_console)

    @PageService()
    def add_subclient(self, sc_name, contents, access_nodes=None, plan=None):
        """Method to add new subclient
        Args:
            sc_name         (str)   --  name of the hdfs subclient
            contents        (list)  --  data to be backed up by new sub client created
            access_nodes    (list)  --  list of access nodes to select
                        default - inherited from instance level
            plan            (str)   --  plan to be used
                        default - inherited from instance level
        """
        self._admin_console.select_hyperlink('Add subclient')
        self._admin_console.fill_form_by_id('contentGroupName', sc_name)
        dropdown = DropDown(self._admin_console)
        # select None is case-sensitive
        dropdown.select_drop_down_values(drop_down_id="createFsContentGroup_isteven-multi-select_#687886",
                                         values=access_nodes)
        dropdown.select_drop_down_values(drop_down_id="planSummaryDropdown", values=[plan])
        self._content.edit_content(contents)
        self._admin_console.check_error_message()


class KuduBackupset(Backupset):
    """
        Functions to operate on Kudu backupset page
    """

    def __init__(self, admin_console, backupset="Kudu"):
        """Initializes instance of the Kudu backupset object class
        Args:
            admin_console       --  admin console object
            backupset           --  name of backupset or hadoop app
        """
        super().__init__(admin_console, backupset)
        self._admin_console = admin_console
        self._backupset = backupset

    @PageService()
    def add_subclient(self, sc_name, tables, plan_name):
        """Method to add new subclient
        Args:
            sc_name     (str)   -- name of the kudu subclient
            tables      (list)  -- list of kudu tables
            plan_name   (str)   -- plan name to select
        """
        self._admin_console.select_hyperlink('Add subclient')
        self._admin_console.fill_form_by_id('subclientName', sc_name)
        rdropdown = RDropDown(self._admin_console)
        rdropdown.select_drop_down_values(drop_down_id="kuduSubclientContentTable", values=tables)
        rdropdown.select_drop_down_values(drop_down_id="plan", values=[plan_name])
        self._admin_console.click_button('Save')
        self._admin_console.check_error_message()
