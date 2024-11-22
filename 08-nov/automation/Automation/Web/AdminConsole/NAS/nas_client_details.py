from selenium.webdriver.common.by import By
#!/usr/bin/env python

"""
This module provides all the methods that can be done of the NAS_File_Servers Details page.


Classes:

    NAS_Client_Details() ---> NAS_File_Servers() --->  LoginPage --->
    AdminConsoleBase() ---> object()


NASClientDetails  --  This class contains all the methods for action in NAS Client Details page and
 is inherited by other classes to perform NAS Client related actions

    Functions:

    add_software()              --  Allows user to select different iDAs under NAS Client
    release_license()           --  Allows user to Releases Licenses consumed by NAS Client
    add_subclient()             --  Allows user to create a NAS Subclient
    run_backup()                --  Allows user to run backups for NAS Subclient
    run_restore()               --  Allows user to run Restores from Subclient Level
    del_subclient()             --  Allows user to delete Subclients
    backup_history()            --  Lists Backup history of subClient
    nas_jobs()                  --  Lists NAS jobs at Client level
    open_sc_prop()              --  Opens SubClient Properties


"""
from selenium.webdriver.common.by import By


from Web.AdminConsole.Components.panel import Backup
from selenium.webdriver.support.ui import Select

from Web.AdminConsole.Components.table import Table
from Web.Common.page_object import PageService, WebAction


class NASClientDetails:
    """
    This class contains all the methods for actions in NAS Client Details page
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
        """Release CIFS and NFS Licenses"""
        self.select_hyperlink("Release license")
        self.checkbox_select("Server File System - Linux File System")
        self.click_button("OK")

    @PageService()
    def nas_jobs(self):
        """ Opens the job history for the client (Backups and Restores)"""
        self.select_hyperlink("Jobs")

    @PageService()
    def open_sc_prop(self, subclient_name):
        """
        Open SubClient Properties Page

        Args:
            subclient_name (str):    Name of the subclient properties to be opened

        """

        self.__table.access_link(subclient_name)

    @WebAction()
    def __click_proxy_ma(self):
        """Clicks on proxy ma dropdown"""
        proxy_ma_dropdown = self.driver.find_element(By.ID, "proxyMa")
        proxy_ma_dropdown.click()

    @WebAction()
    def __get_proxy_ma_count(self):
        """Fetches the count of proxy MA"""
        return len(Select(self.driver.find_element(By.ID, "proxyMa")).options)

    @WebAction()
    def __has_proxy_ma(self):
        """Returns true if proxy ma dropdown is found"""
        return self.driver.findElements(By.ID("proxyMa")).size() != 0

    @PageService()
    def add_subclient(self, subclient_name, subclient_content, nas_plan, agent="NDMP",
                      proxyma=None, user='######', pwd='######'):
        """
        Creates a NAS SubClient

        Args:
            subclient_name  (str)    : Name of the subclient to be created

            subclient_content   (str): Path on the File Server to be added as backup path

            nas_plan (str)   : Name of the plan used to backup the contents of the subclient

            agent (str)  : NDMP or CIFS or NFS Agent

            proxyma (str)    : Proxy MA used during backup of the subclient

            user (str)   : CIFS user who has access to the CIFS Shares

            pwd (str)    : Password for the CIFS User

        """

        self.select_hyperlink("Add subclient")
        self.fill_form_by_id("subclientName", subclient_name)
        if agent == "NDMP":
            self.select_value_from_dropdown("backupType", agent)
            self.wait_for_completion()
            self.__click_proxy_ma()
            self.wait_for_completion()
            ma_cnt = self.__get_proxy_ma_count()
            self.wait_for_completion()
            if ma_cnt <= 1:
                raise Exception("Error in loading all the MAS for Proxy ")
            else:
                self.log.info("No. of MAs listed for Proxy :" + str(ma_cnt - 1))
                if not proxyma:
                    self.log.info("Proxy MA not passed")
                else:
                    self.log.info("Proxy MA Passed is " + proxyma)
                    self.select_value_from_dropdown("proxyMa", proxyma)
                    self.wait_for_completion()
                    self.log.info("ProxyMA selection of NAS SC successful")
            if self.driver.find_element(By.XPATH, "//*[@id='subclient-general-tab']/div[6]/div/button"):
                self.log.info("Browse button appeared")
            else:
                raise Exception("Browse  button didn't appear after choosing NDMP during "
                                "subclient  creation")

        elif agent == "CIFS":
            self.select_value_from_dropdown("backupType", agent)
            self.wait_for_completion()
            self.log.info("User name and Password appeared for CIFS subclient creation")
            self.fill_form_by_id("cifsLogin", user)
            self.fill_form_by_id("cifsPassword", pwd)
            if self.__has_proxy_ma():
                self.log.info("Proxy MA list appeared")
                self.__click_proxy_ma()
                self.wait_for_completion()
                ma_cnt = self.__get_proxy_ma_count()
                self.wait_for_completion()
                if ma_cnt <= 1:
                    self.log.info("Error in loading all the MAs for CIFS subclient")
                    raise Exception("Error in loading all the MAS for CIFS subclient ")
                else:
                    self.log.info("No. of MAs listed for Proxy :" + str(ma_cnt - 1))
                    if not proxyma:
                        self.log.info("Proxy MA not passed")
                    else:
                        self.select_value_from_dropdown("proxyMa", proxyma)
                        self.wait_for_completion()
                        self.log.info("ProxyMA selection of CIFS subclient successful")

            else:
                self.log.info("Proxy MA list  did not appear during CIFS subclient creation")
                raise Exception("Proxy MA list  did not appear during CIFS subclient creation")

        elif agent == "NFS":
            self.select_value_from_dropdown("backupType", agent)
            self.wait_for_completion()
            if self.__has_proxy_ma():
                self.log.info("Proxy MA list appeared")
                self.__click_proxy_ma()
                self.wait_for_completion()
                ma_cnt = self.__get_proxy_ma_count()
                self.wait_for_completion()
                if ma_cnt <= 1:
                    self.log.info("Error in loading all the MAs for NFS Subclient ")
                    raise Exception("Error in loading all the MAS for NFSSubclient ")
                else:
                    self.log.info("No. of MAs listed for Proxy :" + str(ma_cnt - 1))
                    if not proxyma:
                        self.log.info("Proxy MA not passed")
                    else:
                        self.select_value_from_dropdown("proxyMa", proxyma)
                        self.wait_for_completion()
                        self.log.info("ProxyMA selection of NFS Subclient successful")
            else:
                self.log.info("Proxy MA list  did not appear during NFS subclient creation")
                raise Exception("Proxy MA list  did not appear during NFS subclient creation")
        else:
            self.log.info("Agent not found")
            raise Exception("Agent not found")
        self.select_value_from_dropdown("scPlan", nas_plan)
        self.wait_for_completion()
        self.fill_form_by_id("subclientContent", subclient_content)
        self.wait_for_completion()
        self.click_button("Save")

    @PageService()
    def run_backup(self, subclient_name, backup_type):
        """
        Runs Backup on subClient

        Args:
            subclient_name (str) :   Subclient on which backup has to be run
            backup_type (BackupType)    :   Backup type to be run, among the type in Backup.BackupType enum

        Returns (int) : the backup job ID
        """

        self.log.info("Attempting to Run " + backup_type + " Backup on subClient: " + subclient_name)
        self.__table.access_action_item(subclient_name, "Backup")
        backup = Backup(self)
        return backup.submit_backup(backup_type)

    @PageService()
    def run_restore(self, subclient_name):
        """
        Runs Restore job on subClient

        Args:
            subclient_name  (str)    :   SubClient on which Latest Data Restore to be run

        """

        self.log.info("Attempting to run Restore job for data backed up by subClient: " + subclient_name)
        self.__table.search_for(subclient_name)
        self.__click_restore()
        self.wait_for_completion()

    @PageService()
    def del_subclient(self, subclient_name):
        """
        Deletes NAS SubClient

        Args:
            subclient_name  (str)    :   Name of the subclient which is to be deleted

        """

        self.__table.access_action_item(subclient_name, "Delete")
        self.click_button("Yes")

    @WebAction
    def __click_restore(self):
        """Clicks restore"""
        self.driver.find_element(By.XPATH, "*//a[.='Restore']/..").click()

