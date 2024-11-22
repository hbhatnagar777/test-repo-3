# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on
the License page on the AdminConsole
 
Class:

    License()

Functions:

    get_license_details                     :   Returns license page details

    apply_update_license                    :   Applies/Updates license of the Commcell

    __select_license_file                   : Selects license file from local controller

    __enter_licensepath                     : enters license file path

    get_license_details                     : Returns license page details

    access_license_summary                  : access License summary page from License page

    __access_metallic_agreement             : Click and check the Metallic user agreement

"""
from selenium.webdriver.common.by import By
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.Common.page_object import WebAction, PageService
from Web.WebConsole.Reports.Metrics.licensesummary import LicenseSummary


class License:
    """ Class for License page of AdminConsole """

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__driver = admin_console.driver

    @WebAction()
    def __enter_licensepath(self, file_path):
        """
        enter license file path
        file_path (str) : provide the license file path
        """
        input_element = self.__driver.find_element(By.XPATH, 
            "//label//input[@type='file']")
        input_element.send_keys(file_path)

    @PageService()
    def __select_license_file(self, file_path):
        """ Selects license file from local controller
        file_path (str) : provide the license file path
        """
        rpanel = RPanelInfo(self.__admin_console, "License details")
        buttons = ('Update license', 'Apply license')
        for button in buttons:
            if rpanel.check_if_button_exists_on_tile(button):
                rpanel.click_button(button)
                break
        self.__admin_console.wait_for_completion()
        self.__enter_licensepath(file_path)

    @PageService()
    def get_license_details(self):
        """ Returns license page details """
        rpanel = RPanelInfo(self.__admin_console, "License details")
        details = rpanel.get_details()
        return details

    @PageService()
    def apply_update_license(self, file_path, metallic=False):
        """ Applies/Updates License on the License page
        @Args:
        file_path (str) : provide the license file path
        metallic (boolean) : True if license type is metallic """
        self.__select_license_file(file_path)
        self.__admin_console.wait_for_completion()
        udialog = RModalDialog(self.__admin_console, "Update license")
        udialog.click_submit()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()
        if metallic:
            self.__access_metallic_agreement()

    @PageService()
    def access_license_summary(self, webconsole):
        """
        access License summary page from License page
        """
        rpanel = RPanelInfo(self.__admin_console, "Usage")
        rpanel.open_hyperlink_on_tile("License summary report.")
        self.__admin_console.wait_for_completion()
        log_windows = self.__driver.window_handles
        self.__driver.switch_to.window(log_windows[1])
        self.__admin_console.wait_for_completion()
        lic_summary = LicenseSummary(webconsole)
        lic_summary.access_recalculate()
        for window in log_windows[1:]:
            self.__driver.switch_to.window(window)
            self.__driver.close()
        self.__driver.switch_to.window(log_windows[0])
        self.__admin_console.wait_for_completion()

    @PageService()
    def __access_metallic_agreement(self):
        '''Click and check the Metallic user agreement'''
        mdialog = RModalDialog(
            self.__admin_console, "Metallic Recovery Reserve user agreement")
        self.__admin_console.select_hyperlink(
            "Metallic Recovery Reserve user agreement")
        self.__admin_console.wait_for_completion()
        log_windows = self.__driver.window_handles
        for window in log_windows[1:]:
            self.__driver.switch_to.window(window)
            self.__driver.find_element(By.ID, "truste-consent-button").click()
            self.__admin_console.wait_for_completion()
            self.__driver.close()
        self.__driver.switch_to.window(log_windows[0])
        self.__admin_console.wait_for_completion()
        mdialog.checkbox.check(id='acceptEula')
        self.__admin_console.wait_for_completion()
        mdialog.click_submit()
        self.__admin_console.wait_for_completion()
