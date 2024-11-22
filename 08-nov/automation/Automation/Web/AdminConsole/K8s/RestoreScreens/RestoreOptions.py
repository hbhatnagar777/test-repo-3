# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Restore Option Section on the Restore Wizard of Kubernetes

"""
from selenium.webdriver.common.by import By
from Web.AdminConsole.Components.dialog import RModalDialog


class RestoreOptions:
    """
    class to handle restore options section on Kubernetes restore wizard screens
    """

    def __init__(self, wizard, unconditional_overwrite, inplace, source_modifier, modifier_list, admin_console):
        self.wizard = wizard
        self.__admin_console = admin_console
        self.unconditional_overwrite = unconditional_overwrite
        self.inplace = inplace
        self.source_modifier = source_modifier
        self.modifier_list = modifier_list
        self.config()

    def config(self):

        self.enable_unconditional_overwrite()
        if self.modifier_list:
            self.select_modifiers()
        self.wizard.click_next()

    def enable_unconditional_overwrite(self):
        """
        option to enable/disable unconditional overwrite option

        """

        if self.unconditional_overwrite:
            self.wizard.toggle.enable(id='overwrite')
            RModalDialog(admin_console=self.__admin_console, title='Confirm overwrite option').click_submit()
        else:
            self.wizard.toggle.disable(id='overwrite')

    def select_modifiers(self):
        """
        Choose modifiers from source/destination depending on init inputs

        """

        # Expand Advanced options
        self.expand_advanced_options()

        # If restore is of type "out of place", we can choose modifiers from Destination cluster as well

        if not self.inplace and not self.source_modifier:
            self.wizard.select_radio_button(id='destinationModifierRadio')
        else:
            self.wizard.select_radio_button(id='sourceModifierRadio')

        # Choose modifiers as in modifier list

        self.wizard.select_drop_down_values(id='restoreModifierList', values=self.modifier_list)

    def expand_advanced_options(self):
        """
        expand the advanced options panel
        Returns:

        """
        panel_id = 'diskProvisioningPanel'
        ele = self.__admin_console.driver.find_element(By.ID, panel_id)
        if 'panel-closed' in ele.get_attribute('class').split():
            ele.click()


