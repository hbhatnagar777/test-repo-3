# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Local Storage Tab on Metallic

"""
from Web.AdminConsole.Components.dialog import RModalDialog
import time

from Web.AdminConsole.Helper.VSAMetallicHelper import VSAMetallicHelper
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.Common.exceptions import (
    CVWebAutomationException
)


class LocalStorage:
    """
    Class for local storage Page
    """

    def __init__(self, wizard, admin_console, metallic_options):
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__wizard = wizard
        self.__rdialog = RModalDialog(admin_console)
        self.log = self.__admin_console.log
        self.metallic_options = metallic_options
        self.metallic_components = VSAMetallicHelper.getInstance(admin_console)
        self.config()

    def config(self):
        if self.metallic_options.existing_storage:
            self.select_previously_configured_local_storage()
        elif self.metallic_options.new_storage_name:
            self.add_new_storage_location()
        else:
            self.backup_directly_to_cloud()
        self.__admin_console.wait_for_completion()
        self.__wizard.click_next()

    @PageService()
    def select_previously_configured_local_storage(self):
        """
        Select previously created local storage option

        Returns:
            None
        """
        self.log.info(f"Selecting previously configured local storage named [{self.metallic_options.existing_storage}]")
        self.__wizard.select_drop_down_values(
            id="metallicLocalStorageDropdown",
            values=[self.metallic_options.existing_storage]
        )

    @PageService()
    def add_new_storage_location(self):
        """
        Create a new local storage

        Args:
            options:    (dict)  options for new local storage creation

        Returns:
            None
        """
        self.log.info("Creating new local storage")
        self.__wizard.click_add_icon()
        local_storage_dailog = RModalDialog(self.__admin_console, title='Add local storage')
        local_storage_dailog.fill_text_in_field(element_id='name', text=self.metallic_options.new_storage_name)
        local_storage_dailog.select_link_on_dialog(text="Add")
        self.add_backup_location()
        local_storage_dailog.click_button_on_dialog("Save")
        self.retry_local_storage_submission(local_storage_dailog)

    @PageService()
    def add_backup_location(self):
        """
        fills the backup location dailog
        """
        backup_location_dailog = RModalDialog(self.__admin_console, title='Add backup location')
        backup_location_dailog.select_dropdown_values(
            drop_down_id="mediaAgent",
            values=[self.metallic_options.storage_backup_gateway]
        )
        self.__select_storage_target(value=self.metallic_options.storage_target_type)

    @PageService()
    def backup_directly_to_cloud(self):
        """
        select backup directly to cloud option
        Returns:
            None
        """
        self.log.info("Selecting backup directly to cloud option")
        self.__wizard.enable_toggle(label=self.__admin_console.props["label.onlyCloudBackupEnabled"])

    @WebAction()
    def __select_storage_target(self, value='Local'):
        """
        configuring for network or disk storage
        Args:
            value   (str)   :   Local or Network

        Returns:
            None
        """

        backup_location_dailog = RModalDialog(self.__admin_console, title='Add backup location')
        if self.metallic_options.access_node_os != 'unix':
            if value not in ['Local', 'Network']:
                raise CVWebAutomationException(f"Invalid backup location type passed : [{value}]")
            if value == 'Network':
                backup_location_dailog.select_radio_by_id(radio_id="networkRadioDisk")
                backup_location_dailog.fill_text_in_field(
                    element_id='credential.userName-custom-input',
                    text=self.metallic_options.nw_storage_uname
                )
                backup_location_dailog.fill_text_in_field(
                    element_id='credential.password-custom-input',
                    text=self.metallic_options.nw_storage_pwd
                )
            else:
                backup_location_dailog.select_radio_by_id(radio_id="localRadioDisk")

        backup_location_dailog.fill_text_in_field(element_id='path', text=self.metallic_options.storage_path)
        time.sleep(5)
        backup_location_dailog.click_button_on_dialog("Add")

    def retry_local_storage_submission(self, dialog):
        """
        retry submitting the cloud storage
        """
        try:
            title = dialog.title()
            if title == 'Add local storage':
                self.log.info('sleeping for 2 min and retry storage submission')
                time.sleep(120)
                dialog.click_submit()
                self.__admin_console.check_error_message()
        except Exception as exp:
            self.log.info("this is a soft error")
            self.log.warning(exp)
