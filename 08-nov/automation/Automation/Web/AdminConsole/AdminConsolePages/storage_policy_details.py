# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to storage policies details in AdminConsole
StoragePolicyDetails : This class provides methods for storage policies details related operations

StoragePolicyDetails:

    add_copy()          -- To add a new storage copy for the storage policy

    select_copy()       -- selects the storage copy with the given name

"""
from selenium.webdriver.common.by import By

from Web.Common.page_object import WebAction


class StoragePolicyDetails:
    """
    This class provides the function or operations that can be
    performed on the Storage policies Page of the Admin Console
    """

    def __init__(self, admin_console):
        self.admin_console = admin_console
        self.driver = self.admin_console.driver
        self.log = self.admin_console.log

    @WebAction()
    def add_copy(
            self,
            copy_name=None,
            storage_pool=None,
            full_backup_frequency=None,
            throttle_network=None,
            data_aging=True,
            retention='30',
            all_backups=False,
            backup_selection=None,
            aux_copy=None
    ):
        """
        To add a new storage copy

        Args:
            copy_name           (str)   -- Name for the storage copy

            storage_pool        (str)   -- Storage pool for the storage copy

            full_backup_frequency (str) -- Backup frequency for Full backups

            throttle_network    (str)   -- Throttle value in terms of MB/HR

            data_aging          (bool)  -- To enable/disable data aging
                                            default: True

            retention           (str)   -- Retention period for the copy created (Infinite|Number of days)
                                            default: '30'

            all_backups         (bool)  -- To select all backups for the copy
                                            default: False

            backup_selection    (str)   -- backup selection date

            aux_copy            (str)   -- Aux copy for the storage copy

        """
        self.admin_console.select_hyperlink('Add')
        self.admin_console.fill_form_by_id('storagePoolName', copy_name)
        self.admin_console.select_value_from_dropdown('Storagepool', storage_pool)

        if full_backup_frequency:
            self.admin_console.checkbox_select('selectedCopyCheck')
            self.admin_console.select_value_from_dropdown('selectiveCopy', full_backup_frequency)

        if throttle_network:
            self.admin_console.checkbox_select('isThrottleCheck')
            element = self.driver.find_element(By.XPATH, 
                r"//input[@type='number'][@ng-model='throttleValue']")
            element.clear()
            element.send_keys(throttle_network)

        self.driver.find_element(By.XPATH, 
            r"//button[@data-ng-click='saveGeneralTab()']").click()

        if self.admin_console.is_element_present("//span[contains(text(),'Retention')]"):
            if data_aging:
                self.admin_console.toggle_enable('Data Aging')
                if "infinite" in retention.lower():
                    self.admin_console.checkbox_select('isInfiniteCheck')
                else:
                    element = self.driver.find_element(By.XPATH, 
                        r"//input[@name='input'][@ng-model='retentionValue']")
                    element.clear()
                    element.send_keys(retention)
            else:
                self.admin_console.disable_toggle(index=0)  ## toggle disable is deprecated replacing the usage

            self.driver.find_element(By.XPATH, 
                r"//button[@data-ng-click='saveRetentionTab()']").click()

        if all_backups:
            self.admin_console.checkbox_select("allBackUpsCheckFinal")
        elif backup_selection:
            if self.admin_console.check_if_entity_exists('id', 'allBackUpsCheckFinal'):
                self.admin_console.checkbox_deselect("allBackUpsCheckFinal")
            element = self.driver.find_element(By.XPATH, 
                r"//span[contains(text(),'Backups on and after')]/../..//div/input")
            element.clear()
            element.send_keys(backup_selection)

        if aux_copy:
            self.admin_console.checkbox_select('allAuxCopy')
            self.admin_console.select_value_from_dropdown('repeatSelect', aux_copy)

        self.admin_console.click_button('Save')

    @WebAction()
    def select_copy(self, copy_name):
        """
        selects the storage copy with the given name

        Args:
            copy_name   (str)   -- Name of the storage copy to be selected

        """
        # self.search_for(copy_name)
        self.admin_console.select_hyperlink(copy_name)
