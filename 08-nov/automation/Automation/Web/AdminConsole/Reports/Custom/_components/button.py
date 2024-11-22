from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""All the operations common to Button component goes to this file."""

from Web.Common.page_object import (
    WebAction,
    PageService
)
from .base import CRComponentViewer


class ButtonViewer(CRComponentViewer):
    """Actions common to Button Viewer goes here"""

    @property
    def type(self):
        return ''

    @WebAction()
    def _get_id_from_component_title(self, title):
        """Get component ID from component Title"""
        web_obj = self._driver.find_element(By.XPATH,
            f"//*[.='{title}']/parent::button")
        return web_obj.get_attribute("id")

    @WebAction()
    def _button_state(self):
        """Returns the button state for the attribute disabled"""
        button = self._driver.find_element(By.XPATH, self._x)
        return button.get_attribute("disabled")

    @WebAction()
    def __press_button(self):
        """Presses the button"""
        button = self._driver.find_element(By.XPATH, self._x)
        button.click()

    @PageService()
    def is_button_enabled(self):
        """
        Returns (bool): True if button is enabled

        """
        state = self._button_state()
        return False if state == "true" else True

    @PageService()
    def click_button(self):
        """Clicks the button"""
        self.__press_button()
