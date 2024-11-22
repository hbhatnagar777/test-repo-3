from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Model to manager the companies dashboard"""

from Web.Common.page_object import (
    WebAction,
    PageService
)


class Dashboard:
    """
    This class is to manage all the activities on companies dashboard.
    """
    def __init__(self, webconsole):
        """
        Args:
            webconsole (WebConsole): The webconsole object to use
        """
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver

    @WebAction()
    def _get_commcell_count(self):
        """
        Get the commcell count from the companies dashboard
        Returns: Commcell count (INT)
        """
        commcell_count_xp = "//a[@class='service-value cc-count-val center']"
        return int(self._driver.find_element(By.XPATH, commcell_count_xp).text)

    @PageService()
    def get_commcell_count(self):
        """
        Get the commcell count from dashboard
        Returns: Commcell count (INT)
        """
        return self._get_commcell_count()
