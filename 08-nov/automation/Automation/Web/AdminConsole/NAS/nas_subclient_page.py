#!/usr/bin/env python

"""
This module provides all the methods that can be done of the NAS_File_Servers Details page.


Classes:

    NAS_SubclientPage ---> NAS_Client_Details() --->  ---> LoginPage --->
    AdminConsoleBase() ---> object()


NAS_Client_Details  --  This class contains all the methods for action in NAS_Client Details page
                  and is inherited by other classes to perform NAS Client related actions

    Functions:



"""

from Web.AdminConsole.Components.panel import Backup
from Web.Common.page_object import PageService


class NASSubclientPage:
    """
    This class contains all the methods for actions in NAS SubClient Details page
    """

    @PageService()
    def delete_nas_subclient(self):
        """
        Deletes NAS SubClient
        """
        self.log.info("Attempting to Delete subClient")
        self.select_hyperlink("Delete")
        self.wait_for_completion()
        self.click_button("Yes")

    @PageService()
    def backup_now(self, subclient_name, backup_type):
        """
        Runs Backup on subClient

        backup_type (BackupType)   :   Backup type to be run, among the type in Backup.BackupType enum

        Returns (int) : the backup job ID
        """
        self.select_hyperlink("Back up now")
        self.log.info("Attempting to Run " + backup_type + "Backup on subClient:" + subclient_name)
        backup = Backup(self)
        return backup.submit_backup(backup_type)

    @PageService()
    def restore(self, subclient_name):
        """
        Run Restores from subclient page
        """

        self.log.info("Running Restore for subclient -- " + subclient_name)
        self.select_hyperlink("Restore")
