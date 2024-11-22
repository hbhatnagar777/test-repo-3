from selenium.webdriver.common.by import By

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""All the operations common to column component goes to this file."""

from Web.Common.page_object import WebAction, PageService
from .base import (
    CRComponentViewer
)


class ColumnViewer(CRComponentViewer):
    """Actions common to Column Properties  go here"""

    @property
    def type(self):
        return ''

    @WebAction()
    def __click_hyperlink(self, hyperlink):
        """Clicks hyperlink on a particular cell"""
        link = self._driver.find_element(By.XPATH,
                                         f"{self._x.rsplit('//', 1)[0]}//*[contains(@class, 'k-grid')]//*"
                                         f"[text()='{hyperlink}']")
        link.click()

    @PageService()
    def open_hyperlink_on_cell(self, hyperlink, open_in_new_tab=False):
        """Opens Hyperlink on a cell"""
        self.__click_hyperlink(hyperlink)
        if open_in_new_tab:
            self._driver.switch_to.window(self._driver.window_handles[-1])
        self._adminconsole.wait_for_completion()
