# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------

"""
This module provides the function that can be used to configure migration group
"""

import time
from time import sleep
from Web.AdminConsole.Components.table import Table, Rtable
from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.dialog import RModalDialog

class Migration:
    """class for migration page on metallic"""
    
    def __init__(self, admin_console):
        self._admin_console = admin_console
        self.__rtable = Rtable(admin_console)
        self.__rmodaldialog = RModalDialog(admin_console)
        
    @PageService()
    def add_migration_group(self):
        """Add new migration group"""
        self.__rtable.access_toolbar_menu('Create new')
        return MigrationGroup(self._admin_console)
    
    @PageService()
    def access_migration_group(self, migrationgroup):
        """
        Access migration group
        Args:
            migrationgroup        (String)       --    migration group name
        """
        self.__rtable.access_link(migrationgroup)

    @PageService()
    def is_group_exists(self, groupname):
        """
        Check if group exists
        Args:
            migrationgroup        (String)       --    migration group name
        """
        return self.__rtable.is_entity_present_in_column('Group name', groupname)

    @PageService()
    def sync_now(self, migrationgroup):
        """
        sync now for provided migration group
        Args:
            migrationgroup        (String)       --    migration group name
        """
        self.__rtable.access_action_item(migrationgroup, 'Sync now')

    @PageService()
    def pause_migration_group(self, migrationgroup):
        """
        Pause action for provided migration group
        Args:
            migrationgroup        (String)       --    migration group name
        """
        self.__rtable.access_action_item(migrationgroup, 'Pause')
        self.__rmodaldialog.click_submit()
        self._admin_console.wait_for_completion()

    @PageService()
    def cutover_migration_group(self, migrationgroup):
        """
        cutover migration group
        Args:
            migrationgroup        (String)       --    migration group name
        """
        self.__rtable.access_action_item(migrationgroup, 'Cutover')
        self.__rmodaldialog.click_submit()
        self._admin_console.wait_for_completion()

    @PageService()
    def delete_migration_group(self, groupname):
        """
        delete migration group
        Args:
            migrationgroup        (String)       --    migration group name
        """        
        self.__rtable.access_action_item(groupname, 'Delete group')
        self.__rmodaldialog.click_submit()
        self._admin_console.wait_for_completion()

    @PageService()
    def is_group_synced(self, groupname):
        """
        get migration group status
        Args:
            migrationgroup        (String)       --    migration group name
        """
        self.__rtable.search_for(groupname)
        status = self.__rtable.get_column_data('Status')
        if status[0] == 'In sync':
            return True
        else:
            return False

class MigrationGroup:
    """class for migration group on metallic"""

    def __init__(self, admin_console):
        """
        Args:
        admin_console(AdminConsole): adminconsole object
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._rdropdown = RDropDown(admin_console)
        self._table = Table(admin_console)
        self.sharetype = None
 
    @WebAction()
    def __click_add_option(self, formid, index=0):
        """click + button"""
        xpath = "//*[@id='" + formid + "']//button"
        elems = self._driver.find_elements(By.XPATH, xpath)
        elems[index].click()

    @PageService()
    def configure_pre_requisite(self):
        """
        Review prerequisite, then click Next button 
        """
        self._admin_console.click_button_using_text('Next')
        self._admin_console.wait_for_completion()

    @PageService()
    def configure_access_node(self):
        """
        Install and configure new server, once done, click Next button
        new server install will be added later, for now, just click next button
        and continue
        """
        self._admin_console.click_button_using_text('Next')
        self._admin_console.wait_for_completion()

    @PageService()
    def add_credential(self, credname, username, userpwd):
        """
        add new user credential
        Args:
            credname (str)    :        credential name
            username (str)    :        user name
            userpwd  (str)    :        user password
        """

        self._admin_console.fill_form_by_id('credentialName', credname)
        self._admin_console.fill_form_by_id('username', username)
        self._admin_console.fill_form_by_id('password', userpwd)
        self._admin_console.click_button_using_text('Save')
        self._admin_console.wait_for_completion()
        

    @PageService()
    def configure_source(self, srcfileservername, sharetype, accessnode, shareuser=None, sharepwd=None):
        """
        define source information
        Args:
            srcfileservername (str)    :    source file server name
            sharetype (str)    :    share type,  SMB or NFS
            accessnode  (str)  :    source access node
            shareuser  (str)   :    SMB share user name
            sharepwd  (str)    :    SMB share user password
        """
        sharetypes = [sharetype]
        accessnodes = [accessnode]
        self.sharetype = sharetype
        self._admin_console.fill_form_by_id('sourceFilerName', srcfileservername)
        self._rdropdown.select_drop_down_values(values=sharetypes, drop_down_id='nasTypeDropdown')
        if sharetype == "SMB":
            credname = shareuser + "_62047"
            existingcreds = self._rdropdown.get_values_of_drop_down('sourceCredentialsDropdown')
            if credname not in existingcreds:
                self.__click_add_option('addSourceForm')
                self.add_credential(credname, shareuser, sharepwd) 
            self._rdropdown.select_drop_down_values(values=[credname],
                                                    drop_down_id='sourceCredentialsDropdown')
        self._rdropdown.select_drop_down_values(values=accessnodes,
                                                drop_down_id='sourceAccessNodeDropdown')
        self._admin_console.click_button_using_text('Next')
        self._admin_console.wait_for_completion()

    @PageService()
    def configure_destination(self, storageaccount, region, accessnode, shareuser=None, sharepwd=None):
        """
        define destination information
        Args:
            storageaccount (str)    :    azure storage account name
            region (str)    :    destination region
            accessnode  (str)  :    destination access node
            shareuser  (str)   :    SMB share user name
            sharepwd  (str)    :    SMB share user password
        """
        accessnodes = [accessnode]
        regions = [region]
        self._admin_console.fill_form_by_id('azureAccountName', storageaccount)
        if self.sharetype == "SMB":
            credname = shareuser + "_62047"
            existingcreds = self._rdropdown.get_values_of_drop_down('destinationCredentialsDropdown')
            if credname not in existingcreds:
                self.__click_add_option('addDestionationForm')
                self.add_credential(credname, shareuser, sharepwd)
            self._rdropdown.select_drop_down_values(values=[credname],
                                                    drop_down_id='destinationCredentialsDropdown')
        self._rdropdown.select_drop_down_values(values=regions,
                                                drop_down_id='destinationRegionDropdown')
        self._rdropdown.select_drop_down_values(values=accessnodes,
                                                drop_down_id='destinationAccessNodeDropdown')
        self._admin_console.click_button_using_text('Next')
        self._admin_console.wait_for_completion()

    @PageService()
    def configure_contents(self, srccontent, destcontent):
        """
        define source and destination content path
        Args:
            srccontent (str)    :    source share path
            destcontent (str)    :    destination share path
        """
        self._admin_console.fill_form_by_id('SourcePath1', srccontent)
        sleep(30)
        self._admin_console.fill_form_by_id('DestinationPath1', destcontent)
        sleep(30)
        self._admin_console.click_button_using_text('Next')
        self._admin_console.wait_for_completion()

    @PageService()
    def configure_migration_settings(self, migrationgroupname):
        """
        configure migration grup settings
        Args:
            migrationgroupname (str)    :     migration group name
        """
        self._admin_console.fill_form_by_id('migrationGroupName', migrationgroupname)
        self._admin_console.click_button_using_text('Next')
        self._admin_console.wait_for_completion()
    
    @PageService()
    def configure_summary(self, startmigration=False):
        """check migration summary page, start migration immediately if needed"""
        if startmigration:
            self._admin_console.checkbox_select('migrateImmediatelyTgl')
        self._admin_console.click_button_using_text('Submit')
        self._admin_console.wait_for_completion()        
