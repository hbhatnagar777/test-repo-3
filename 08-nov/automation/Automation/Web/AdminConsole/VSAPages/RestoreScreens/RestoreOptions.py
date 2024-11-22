# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Restore Option Section on the Restore Wizard of VSA Hypervisors

"""
from selenium.webdriver.common.by import By
from VirtualServer.VSAUtils.VirtualServerConstants import HypervisorDisplayName
from Web.AdminConsole.Components.dialog import RModalDialog


class RestoreOptions:
    """
    class to handle restore options section on restore wizard screens
    """

    def __init__(self, wizard, restore_options, admin_console):
        self.wizard = wizard
        self.__restore_options = restore_options
        self.__admin_console = admin_console
        self.config()

    def config(self):
        if not getattr(self.__restore_options, "use_live_recovery", False):
            self.power_on_after_restore()
        self.unconditional_overwrite()
        self.notify_on_job_completion()
        # use end_user attribute to control the flow for end-user case
        if self.__restore_options.type in [HypervisorDisplayName.VIRTUAL_CENTER,
                                           HypervisorDisplayName.MS_VIRTUAL_SERVER] and \
                not self.__restore_options.end_user:
            if self.__restore_options.restore_type == 'Out of place' and not getattr(self.__restore_options, 'restore_to_recovery_target', False):
                self.reuse_vm_client()
                self.generate_new_guid()
            if getattr(self.__restore_options, 'use_live_recovery', False) and not getattr(self.__restore_options, 'restore_to_recovery_target', False):
                if not getattr(self.__restore_options, "live_recovery_restore_type", False):
                    self.live_recovery()
            self.disk_provisioning()
        if self.__restore_options.type in [HypervisorDisplayName.VIRTUAL_CENTER, HypervisorDisplayName.AMAZON_AWS] and \
                not self.__restore_options.end_user:
            self.transport_mode()
        if self.__restore_options.type in [HypervisorDisplayName.Google_Cloud] and \
                self.__restore_options.restore_type != 'In place' and \
                    self.__restore_options.end_user:
            self.reuse_vm_client()
        if self.__restore_options.end_user:
            self.wizard.click_submit()
        else:
            self.wizard.click_next()

    def power_on_after_restore(self, value=None):
        """
        Enable or disable power on vm after restore option
        Args:
            value: (boolean) True/False

        """
        power_on_after_restore = False
        if value:
            power_on_after_restore = value
        if self.__restore_options.power_on_after_restore:
            power_on_after_restore = self.__restore_options.power_on_after_restore
        if power_on_after_restore:
            self.wizard.toggle.enable(id='powerOn')
        else:
            self.wizard.toggle.disable(id='powerOn')

    def unconditional_overwrite(self, value=None):
        """
        option to enable/disable unconditional overwrite option
        Args:
            value: (boolean) True/False

        """
        unconditional_overwrite = False
        if value:
            unconditional_overwrite = value
        if self.__restore_options.unconditional_overwrite:
            unconditional_overwrite = self.__restore_options.unconditional_overwrite
        if unconditional_overwrite:
            self.wizard.toggle.enable(id='overwrite')
            RModalDialog(admin_console=self.__admin_console, title='Confirm overwrite option').click_submit()
        else:
            self.wizard.toggle.disable(id='overwrite')

    def reuse_vm_client(self, value=None):
        """
        option to use vmclient during restore
        Args:
            value: (boolean) True/False

        """
        reuse_vm_client = False
        if value:
            reuse_vm_client = value
        if self.__restore_options.reuse_existing_vm_client:
            reuse_vm_client = self.__restore_options.reuse_existing_vm_client
        if reuse_vm_client:
            self.wizard.toggle.enable(id='reuseVmClient')
        else:
            self.wizard.toggle.disable(id='reuseVmClient')

    def notify_on_job_completion(self, value=None):
        """
        option to notify on job completion after restore
        Args:
            value: (boolean) True/False

        """
        notify_on_job_completion = False
        if value:
            notify_on_job_completion = value
        if self.__restore_options.notify_on_job_completion:
            notify_on_job_completion = self.__restore_options.notify_on_job_completion
        if notify_on_job_completion:
            self.wizard.toggle.enable(id='notify')
        else:
            self.wizard.toggle.disable(id='notify')

    def live_recovery(self, value=None):
        """
        option to use live recovery during restore
        Args:
            value: (boolean) True/False

        """
        self.expand_advanced_options()
        live_recovery = False
        if value:
            live_recovery = value
        if self.__restore_options.use_live_recovery:
            live_recovery = self.__restore_options.use_live_recovery
        if live_recovery:
            self.wizard.toggle.enable(id='liveRecovery')
            self.configure_live_recovery()
        else:
            self.wizard.toggle.disable(id='liveRecovery')

    def configure_live_recovery(self):
        """
        configure liver recovery options if liver recovery is enabled
        Returns:
            None
        """
        if self.__restore_options.live_recovery_datastore:
            self.wizard.select_drop_down_values(id='DataStoreDropdown', values=[self.__restore_options.
                                                  live_recovery_datastore])
        if self.__restore_options.live_recovery_delay_migration:
            self.wizard.fill_text_in_field(id='DelayMigrationField', text=self.__restore_options.
                                             live_recovery_delay_migration)

    def generate_new_guid(self, value=None):
        """
        option to specify wether to enable new guid for the restored vm
        Args:
            value: (boolean) True/False

        """
        self.expand_advanced_options()
        generate_new_guid = False
        if value:
            generate_new_guid = value
        if self.__restore_options.generate_new_guid:
            generate_new_guid = self.__restore_options.generate_new_guid
        if self.__restore_options.type == HypervisorDisplayName.MS_VIRTUAL_SERVER:
            if generate_new_guid:
                self.wizard.select_radio_button(label="Copy the virtual machine with a new unique GUID")
            else:
                self.wizard.select_radio_button(label="Restore the virtual machine with an existing unique GUID")
        else:
            if generate_new_guid:
                self.wizard.toggle.enable(id='generateNewGuid')
            else:
                self.wizard.toggle.disable(id='generateNewGuid')

    def expand_advanced_options(self):
        """
        expand the advanced options panel
        Returns:

        """
        panel_id = 'diskProvisioningPanel'
        ele = self.__admin_console.driver.find_element(By.ID, panel_id)
        if 'panel-closed' in ele.get_attribute('class').split():
            ele.click()

    def transport_mode(self, value=None):
        """
        select transport mode option for restore
        Args:
            value: (str) type of transport mode

        """
        self.expand_advanced_options()
        transport_mode = 'Auto'
        if value:
            transport_mode = value
        if self.__restore_options.transport_mode:
            transport_mode = self.__restore_options.transport_mode
        self.wizard.select_drop_down_values(id='transportMode', values=[transport_mode])

    def disk_provisioning(self, value=None):
        """
        select type of disk provisioning
        Args:
            value: (str) type of provisioning

        """
        self.expand_advanced_options()
        disk_provisioning = 'Original'
        if value:
            disk_provisioning = value
        if self.__restore_options.disk_provisioning:
            disk_provisioning = self.__restore_options.disk_provisioning
        self.wizard.select_drop_down_values(id='diskProvisioningDropdown', values=[disk_provisioning])