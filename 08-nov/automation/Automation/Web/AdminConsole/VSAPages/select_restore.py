from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides methods to select any type of restore to be done.


Classes:

    SelectRestore() --> _Navigator() --->  AdminConsoleBase() ---> Object()


SelectRestore --  This class contains all the methods to select any type of restore to be done.
    Functions:

    select_guest_files() -- Opens the guest files restore page
    select_vm_files() -- Opens the virtual machine files restore page
    select_full_vm_restore() -- Opens the full VM restore page
    select_disk_restore() -- Opens the disk level restore page
"""
from Web.AdminConsole.Components.browse import Browse
from Web.AdminConsole.Components.panel import RDropDown
from AutomationUtils import logger
from selenium.webdriver.common.by import By
from Web.Common.page_object import (
    WebAction,
    PageService
)


class SelectRestore:
    """
    This class contains all the methods to select any type of restore to be done.
    """

    def __init__(self, admin_console):
        """ Init """
        self.log = logger.get_log()
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self)
        self.__driver = admin_console.driver
        self.__panel_dropdown_obj = RDropDown(admin_console)

    @WebAction()
    def __select_restore_type(self, restore_type):
        """
        Selects the Restore type"""
        for res in restore_type:
            if self.__admin_console.check_if_entity_exists("xpath", f"//h2[contains(text(),'{res}')]/ancestor::"
                                                                    f"div[contains(@class, 'tile-content-wrapper')]"):
                self.__driver.find_element(By.XPATH, f"//h2[contains(text(),'{res}')]/ancestor::"
                                                     f"div[contains(@class, 'tile-content-wrapper')]").click()
                break

    @WebAction()
    def __select_latest_restore_time(self):
        """
        Selects Latest backup for restore"""
        dropdown_xpath = "//div[contains(text(), 'Showing backup as of')]//" \
                         "ancestor::div[contains(@class, 'action-list-dropdown-wrapper')]//button"
        self.__driver.find_element(By.XPATH, dropdown_xpath).click()

        self.__driver.find_element(By.XPATH, "//div[contains(text(), 'Show latest backup')]//ancestor::button").click()

    @PageService()
    def select_guest_files(self):
        """
        Opens the guest files restore page
        """
        self.__select_restore_type([self.__admin_console.props['label.guestFile']])
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_vm_files(self):
        """
        Opens the virtual machine files restore page
        """
        self.__select_restore_type([self.__admin_console.props['label.fileRestore'],
                                    self.__admin_console.props['label.fileRestoreAMAZON']])
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_live_mount(self):
        """
        opens the live mount page
        """
        self.__select_restore_type([self.__admin_console.props['label.liveMount']])
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_full_vm_restore(self):
        """
        Opens the full VM restore page
        """
        full_vm_list = [self.__admin_console.props['label.fullVM'], self.__admin_console.props['label.fullVMAMAZON']]

        self.__select_restore_type(full_vm_list)
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_live_recovery(self):
        """
        Opens the full VM restore page
        """
        full_vm_list = [self.__admin_console.props['label.liveRecovery']]

        self.__select_restore_type(full_vm_list)
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_disk_restore(self):
        """
        Opens the disk level restore page
        """
        attach_disk_list = [self.__admin_console.props['label.diskLevelRestoreAZURE'], self.__admin_console.props[
            'label.diskLevelRestoreAMAZON'], 'Attach disk to VM']

        self.__select_restore_type(attach_disk_list)
        self.__admin_console.wait_for_completion()

    @PageService()
    def select_source_copy(self, copy_name):
        """
        Selects the copy from which browse and restore has to happen

        Args:
            copy_name   (str):   the name of the copy to browse and restore from

        Raises:
            Exception:
                if the copy could not be selected

        """


        if self.__admin_console.check_if_entity_exists("link", "Select source"):
            self.__admin_console.select_hyperlink("Select source")
            elements = self.__driver.find_elements(By.XPATH, "//a[.='Select source']/../ul/li")
            for element in elements:
                copy_elem = element.find_element(By.XPATH, "./a")
                if copy_elem.text.lower() == copy_name.lower():
                    copy_elem.click()
                    self.__admin_console.wait_for_completion()
                    break
            element = self.__driver.find_element(By.XPATH, "//a[@class='uib-dropdown-toggle "
                                                          "ng-binding dropdown-toggle']")
            if element.text.lower() != copy_name.lower():
                raise Exception("The copy could not be selected.")
        else:
            browse_panel = Browse(self.__admin_console)
            browse_panel.select_adv_options_submit_restore(storage_copy_name=copy_name, database=True)

    @PageService()
    def latest_backups(self):
        """Shows the latest backup"""

        self.__select_latest_restore_time()

    @PageService()
    def select_source_and_media_agent(self, source=None, media_agent=None):
        """
        method to support selection of copy precedence and media agent during browse and restores
        Args:
            source: copy precedence value
            media_agent: media_agent value
        Returns:
            None
        """
        self.__click_settings()
        if media_agent:
            self.__panel_dropdown_obj.select_drop_down_values(
                values=[media_agent], drop_down_id='mediaAgentsList')
        if source:
            self.__panel_dropdown_obj.select_drop_down_values(
                values=[source], drop_down_id='sourcesList', case_insensitive_selection=True)
        self.__admin_console.click_button('OK')

    @WebAction()
    def __click_settings(self):
        """Clicks on the Settings button"""
        self.__admin_console.click_button(value='Change source')
