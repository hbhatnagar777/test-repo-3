#!/usr/bin/env python

"""
This module provides all the methods that can be done of the NAS_File_Servers Details page.


Classes:

    NAS_Client_Details() ---> NAS_File_Servers() ---> _Navigator() ---> LoginPage --->
    AdminConsoleBase() ---> object()


NAS_Client_Details  --  This class contains all the methods for action in NAS_Client Details page
    and is inherited by other classes to perform NAS Client related actions

    Functions:
    add_subclient()             --  Allows user to create a NAS Subclient
    run_backup()                --  Allows user to run backups for NAS Subclient
    run_restore()               --  Allows user to run Restores from Subclient Level
    del_subclient()             --  Allows user to delete Subclients
    backup_history()            --  Lists Backup history of subClient
    nas_jobs()                  --  Lists NAS jobs at Client level

"""
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import PageService


class NDMPAgentPage:
    """
    This class contains all the methods for actions in NDMP Agent page
    """
    def __init__(self, admin_console):
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._admin_console.load_properties(self)
        self.__table = Table(self._admin_console)
        
    @PageService()
    def open_sc_prop(self, subclient_name):
        """
        Opens SubClient Properties

        Args:
            subclient_name (str):    Name of the subclient properties to be opened

        """

        self.__table.access_link(subclient_name)
        return True

    @PageService()
    def add_subclient(self, subclient_name, agent, subclient_content, nas_plan):
        """
        Creates a NAS SubClient
        Args:
            subclient_name  (str)    :   Name of the subclient that has to be created

            agent   (str)            :   NDMP or CIFS or NFS iDA

            subclient_content   (str):   Subclient content

            nas_plan    (str)        :   Plan with which the subclient has to be associated

        """

        self.select_hyperlink("Add subclient")
        self.fill_form_by_id("subclientName", subclient_name)
        self.select_value_from_dropdown("backupType", agent)
        self.wait_for_completion()
        self.select_value_from_dropdown("scPlan", nas_plan)
        self.wait_for_completion()
        self.fill_form_by_id("subclientContent", subclient_content)
        self.click_button("Save")
        self.log.info("Creation of subclient: " + subclient_name + "successful")

    @PageService()
    def run_backup(self, subclient_name, backup_type):
        """
        Runs Backup on subClient

        Args:
            subclient_name (str) :   Subclient on which backup has to be run
           backup_type (BackupType)    :   Backup type to be run, among the type in Backup.BackupType enum

        Returns (int) : the backup job ID
        """

        self.log.info("Attempting to Run " + backup_type + " Backup on subClient: " +
                      subclient_name)
        self.__table.access_action_item(subclient_name, "Backup")
        backup = Backup(self)
        return backup.submit_backup(backup_type)

    @PageService()
    def run_restore(self, subclient_name):
        """
        Runs Restore job on subClient

        Args:
            subclient_name (str) : Subclient on which Latest Backed up
                                            data has to be restored

        """

        self.log.info("Attempting to run Restore job for data backed up by subClient: "
                      + subclient_name)
        self.__table.search_for(subclient_name)
        self.select_hyperlink("Restore")

    @PageService()
    def del_subclient(self, subclient_name):
        """
        Deletes NAS SubClient
        Args:
            subclient_name  (str)    :   Name of the subclient which has to be deleted

        """

        self.__table.access_action_item(subclient_name, "Delete")
        self.click_button("Yes")
