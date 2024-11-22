# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Content Group page

ContentGroup
    get_content_group_details       --      Access General Details of content group

    edit_contents                   --      Edit content group

    delete_content_path             --      Deletes already selected content paths from the content group edit tile

    submit_backup                   --      submits backup job

    backup_history                  --      Access to Backup history

    get_job_ids                     --      Get Job Ids from backup history  page

    access_restore                  --      Access Restore for Restore Panel

    submit_restore                  --      Submits restore job

    change_scan_type                --      Changes the scan type of non default subclient

    change_instance_auth_type       --      Changes the auth type of the client

"""
from Web.AdminConsole.Components.browse import Browse
from Web.AdminConsole.Components.dialog import RBackup
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.ObjectStorage.clients.restore_panels import RestoreOptions
from Web.Common.page_object import PageService
from Web.AdminConsole.Components.content import AddContent
from Web.AdminConsole.Components.dialog import RModalDialog
import time


class ContentGroup:
    """Class for Content Group details page"""

    def __init__(self, admin_console):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self._table = Table(self._admin_console)
        self._rtable = Rtable(self._admin_console)
        self.props = self._admin_console.props
        self.browse = Browse(self._admin_console)
        self.general_panel = RPanelInfo(self._admin_console, title=self.props['header.general'])
        self.content_panel = RPanelInfo(self._admin_console, title=self.props['header.content'])
        self.scan_panel = RPanelInfo(self._admin_console, title=self.props['header.scan_configuration'])
        self.content = AddContent(self._admin_console)
        self.page_container = PageContainer(self._admin_console)
        self.dialog = RModalDialog(self._admin_console, title='Edit object storage')
        self.cred_dialog = RModalDialog(self._admin_console, title='Add credential')
        self.scan_dialog = RModalDialog(self._admin_console, title='Select the scan type for the backups')

    @PageService()
    def get_content_group_details(self):
        """Access General Details of content group"""
        return self.general_panel.get_details()

    @PageService()
    def edit_contents(self, contents):
        """
        Edit content group
        Args:
            contents (list): content
        """
        self.content_panel.edit_tile()
        self._admin_console.wait_for_completion()
        self.content.edit_content(contents)
        self._admin_console.check_error_message()

    @PageService()
    def delete_content_path(self, path_list):
        """
        Deletes already selected content paths from the content group edit tile
        Args:
            path_list (list): list of paths to be deleted
        """
        if not isinstance(path_list, list):
            raise TypeError(f"Expected a list, got {type(path_list)}")
        self.content_panel.edit_tile()
        self._admin_console.wait_for_completion()
        self.content.delete_content_path(path_list)
        self._admin_console.check_error_message()

    @PageService()
    def change_scan_type(self, scan_type):
        """ Changes the scan type of non default subclient
            Args :
                scan_type (str) : FLAT_MODE / HIERARCHICAL
        """
        self.scan_panel.edit_tile()
        self._admin_console.wait_for_completion()
        self.scan_dialog.select_dropdown_values('scanType', [scan_type])
        self.scan_dialog.click_submit()
        self._admin_console.wait_for_completion()

    @PageService()
    def change_instance_auth_type(self, auth_type, **kwargs):
        """ Changes the auth_type of an instance created using IAM AD auth
            Expected kwargs :
                For  auth_type : Access key and Account name
                    account_name (str) : Account name
                    access_key (str)   : Access key
                For auth_type : IAM AD application
                    ad_account_name (str)  : AD account name

        """
        self.general_panel.edit_tile()
        if auth_type == "IAM VM role":
            self.dialog.select_checkbox(checkbox_id="isManagedIdentity")
        else:
            self.dialog.select_dropdown_values('authenticationMethod', [auth_type])
            self.dialog.click_add()
            credential_name = f'automation-credential-{int(time.time())}'
            self.cred_dialog.fill_text_in_field(element_id="name", text=credential_name)
            self.cred_dialog.fill_text_in_field(element_id='accountName', text=kwargs.get('account_name')[1:])
            self.cred_dialog.fill_text_in_field(element_id='accessKeyId', text=kwargs.get('access_key'))
            self.cred_dialog.click_submit()
            if auth_type == "IAM AD application":
                self.dialog.fill_text_in_field(element_id='adAccountName', text=kwargs.get('ad_account_name'))
        self.dialog.click_submit()

    @PageService()
    def submit_backup(self, backup_type=RBackup.BackupType.INCR):
        """
            submits backup job
            Args:
                backup_type (Backup.BackupType) : backup type
            Returns
                    (str) -- Backup job id

        """
        self.page_container.click_on_button_by_id("BACKUP")
        return RBackup(self._admin_console).submit_backup(backup_type)

    @PageService()
    def backup_history(self):
        """
        Access to Backup history
        """
        self.page_container.click_on_button_by_id("BACKUPHISTORY")

    @PageService()
    def get_job_ids(self, react_page=False):
        """
        Get Job Ids from backup history  page
        Args:
            react_page(bool)    -- react or angular job history page
        Returns
            (list) -- list of Job Ids in backup history
        """
        if react_page:
            job_ids = self._rtable.get_column_data('Job ID')
        else:
            job_ids = self._table.get_column_data('Job Id')
        return job_ids

    @PageService()
    def access_restore(self):
        """
        Access Restore for Restore Panel
        """
        self._admin_console.access_action(self.props['label.globalActions.restore'])
        self._admin_console.wait_for_completion()

    @PageService()
    def submit_restore(self, file_folders):
        """
        Submits restore job
        Args:
            file_folders (list): list of files and folders to be restored

        Returns
          (str):  Restore options object
        """
        self.browse.clear_all_selection()
        self.browse.select_for_restore(file_folders)
        self.browse.submit_for_restore()
        return RestoreOptions(self._admin_console)
