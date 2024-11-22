# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------

"""

This module provides the function or operations that can be performed on the theme customization page
in admin console

Class:
      Theme()

Functions :

    set_logo()                      ->  Method to set the custom logo

    set_color_settings()            -> Method to set the color settings

    reset_theme()                   ->  Method to reset the theme settings

    get_theme_values()              -> Method to get the theme customization values

"""
from selenium.webdriver.common.by import By

from Web.Common.page_object import (WebAction, PageService)


class Theme:
    """Class for theme customization page"""
    
    color_ids_default = {
        'loginAndBannerBg': '#0B2E44',
        'headerColor': '#DDE5ED',
        'headerTextColor': '#0B2E44',
        'navBg': '#FFFFFF',
        'navIconColor': '#0b2e44',
        'pageHeaderText': '#0B2E44',
        'actionBtnBg': '#0B2E44',
        'actionBtnText': '#eeeeee',
        'linkText': '#4B8DCC',
        'iconColor': '#0B2E44'
    }
    custom_css_id = 'customcss'
    login_page_logo_id = 'customLogoFileInput'

    def __init__(self, admin_console):
        self.admin_console = admin_console
        self.driver = admin_console.driver
        self.log = admin_console.log

    @WebAction()
    def _set_commcell_logo(self, logo_file_path):
        """
        Set the commcell logo

        Args:

            logo_file_path(str)     -- file path to the custom logo.    e.g: C:\\test\\Jb_image1.jpg

        Returns:
            None

        Raises:
            Exception:
                -- if failed to set the logo

        """
        self.log.info("Setting the commcell logo")
        logo = self.driver.find_element(By.XPATH, "//input[@type='file']")
        logo.send_keys(logo_file_path)
        self.admin_console.admin_console.click_button('Save')

    @WebAction()
    def _set_custom_color_settings(self, colors_dict):
        """
        set the color settings

        Args:
            colors_dict (dict)  -   dictionary of the color setting id as key and hex string value as input
                                    for example: see Theme.color_ids_default
        Returns:
                None
        Raises:
                Exception:
                    --- if failed to set the color values

        """

        for color_id in colors_dict:
            if color_id in self.color_ids_default:
                self.log.info(f"Setting color for {color_id}")
                self.admin_console.fill_form_by_id(color_id, colors_dict[color_id])
            else:
                self.log.warning(f"Theme color setting {color_id} does not exist, ignoring")

        self.admin_console.click_button('Save')

    @WebAction()
    def _get_theme_customization_values(self):
        """to get the theme customization value"""
        theme_dictionary = {
            color_id: self.driver.find_element(By.ID, color_id).get_attribute('value')
            for color_id in self.color_ids_default
        }
        return theme_dictionary

    @PageService()
    def set_logo(self, logo_file_path):
        """
        Method to set the custom logo

        Args:
            logo_file_path(str)     -- file path to the custom logo.    e.g: C:\\test\\Jb_image1.jpg

        Returns:
            None

        Raises:
            Exception:
                -- if failed to set the logo

        """
        self._set_commcell_logo(logo_file_path)
        self.admin_console.wait_for_completion()
        self.admin_console.check_error_message()

    @PageService()
    def set_color_settings(self, **color_settings):
        """
        Method to set the color settings

        Args:
            color_settings:
                loginAndBannerBg: '#0B2E44',
                headerColor: '#DDE5ED',
                headerTextColor: '#0B2E44',
                navBg: '#FFFFFF',
                navIconColor: '#0b2e44',
                pageHeaderText: '#0B2E44',
                actionBtnBg: '#0B2E44',
                actionBtnText: '#eeeeee',
                linkText: '#4B8DCC',
                iconColor: '#0B2E44'

        Returns:
            None

        Raises:
            Exception:
                -- if failed to set the color settings

        """
        self._set_custom_color_settings(color_settings)
        self.admin_console.wait_for_completion()
        self.admin_console.check_error_message()

    @PageService()
    def reset_theme(self):
        """
        Method to reset the theme customization values

        Returns:
            None

        Raises:
            Exception:
                -- if failed to reset the customization values

        """
        self.admin_console.click_button('Reset to default')
        self.admin_console.click_button('Yes')
        self.admin_console.check_error_message()

    @PageService()
    def get_theme_values(self):
        """
        Get theme color and logo values
        Returns:

            Dictionary with all theme color and logo values
                Eg.-{logo_file_name : ['c:\\test\\test1.jpg'], primary_color_value : ['#a83ba7']}

        """
        theme_dictionary = self._get_theme_customization_values()
        return theme_dictionary
