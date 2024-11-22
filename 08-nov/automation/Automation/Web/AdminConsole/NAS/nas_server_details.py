#!/usr/bin/env python

"""
This module provides all the methods that can be done of the NASServerDetails Details page.


Classes:

    NASServerDetails() ---> Servers() ---> LoginPage --->
    AdminConsoleBase() ---> object()


NASServerDetails  --  This class contains all the methods for action in NAS Client with different
                    Agents, inherited by other classes to perform NAS Client related actions

    Functions:

    add_software()              --  Allows user to select different iDAs under NAS Client
    release_license()           --  Allows user to Releases Licenses consumed by NAS Client
    backup_history()            --  Lists Backup history of subClient
    restore_history()           --  Lists Restore history of subClient
    nas_jobs()                  --  Lists NAS jobs at Client level
    select_agent()              --  Selects any of CIFS, NFS and NDMP Agents
"""


from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import PageService


class NASServerDetails:
    """
    This class contains all the methods for actions in NAS Server pages
    """

    def __init__(self, admin_console):
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._admin_console.load_properties(self)
        self.__table = Table(self._admin_console)
        
    @PageService()
    def add_software(self, server_name):
        """
        Add CIFS and NFS iDAs for NAS Client

        Args:
            server_name (str)    :   Name of the FileServer -- CIFS &  NFS iDAs to be added

        """

        self.log.info("Adding CIFS and NFS iDAs under NAS Client :  " + server_name)
        self.select_hyperlink("Add software")
        self.checkbox_select("windowsIda")
        self.checkbox_select("unixIda")
        self.click_button("Save")

    @PageService()
    def release_license(self):
        """"
        Release CIFS and NFS Licenses
        """

        self.select_hyperlink("Release license")
        self.checkbox_select("Server File System - Linux File System")
        self.click_button("OK")

    @PageService()
    def nas_jobs(self):
        """
        Opens the job history for the client (Backups and Restores)
        """
        self.select_hyperlink("Jobs")

    @PageService()
    def select_agent(self, agent):
        """
        Opens Agents under NAS File Server
        """
        self.__table.access_link(agent)


