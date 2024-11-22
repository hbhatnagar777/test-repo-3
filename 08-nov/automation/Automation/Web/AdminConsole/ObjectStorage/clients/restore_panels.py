# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module implements the methods that fill in various restore options
    in_place()          --  submits inplace restore

    out_of_place()      --  submits out of place restore

    to_disk()           --  submits restore to disk

"""
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.page_object import PageService


class RestoreOptions(RModalDialog):

    def __click_overwrite_newer(self):
        """clicks overwrite only newer files radio button"""
        self._admin_console.select_radio(
            self._admin_console.props['label.overwriteIfFileInBackupIsNewer']
        )

    def __set_disk_path(self, path):
        """
        Sets disk path
        Args:
            path (str): path to restore
        """
        self._admin_console.fill_form_by_id("destinationPathRTD", path)

    @PageService()
    def in_place(self, overwrite=True):
        """
        submits inplace restore
        Args:
            overwrite (bool): Overwrite files unconditionally
        Returns
            (str): Restore Job id

        """
        if not overwrite:
            self.__click_overwrite_newer()
        self.click_submit(wait=False)
        _jobid = self._admin_console.get_jobid_from_popup()
        self._admin_console.wait_for_completion()
        return _jobid

    @PageService()
    def out_of_place(self, destination_client, dest_path, overwrite=True):
        """
        submits out of place restore
        Args:
            destination_client (str): client name
            dest_path (str)         : desitnation path
            overwrite (bool)        : Overwrite files unconditionally

        Returns
            (str): Restore Job id

        """
        self.select_dropdown_values('restoreModeType', [self._admin_console.props['label.OOPRestore']])

        if not overwrite:
            self.__click_overwrite_newer()

        self.select_dropdown_values('cloudStorageAppOutOfPlaceRestore', [destination_client])
        self.fill_text_in_field('destinationPathOOP', dest_path)

        self.click_submit(wait=False)
        _jobid = self._admin_console.get_jobid_from_popup()
        self._admin_console.wait_for_completion()
        return _jobid

    @PageService()
    def to_disk(self, destination_client, dest_path, overwrite=True):
        """
        submits restore to disk
        Args:
            destination_client (str): client name
            dest_path (str)         : desitnation path
            overwrite (bool)        : Overwrite files unconditionally

        Returns
            (str): Restore Job id

        """
        self.select_dropdown_values('restoreModeType', [self._admin_console.props['label.rtdRestore']])

        if not overwrite:
            self.__click_overwrite_newer()

        self.select_dropdown_values('cloudStorageAppRestoreToDisk', [destination_client])
        self.fill_text_in_field('destinationPathOOP', dest_path)

        self.click_submit(wait=False)
        _jobid = self._admin_console.get_jobid_from_popup()
        self._admin_console.wait_for_completion()
        return _jobid
