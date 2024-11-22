from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Module has features which are present in report settings page.


SearchSettings:

    __init__()                           --  initialize instance of the SearchSetting class,
                                             and the class attributes.

    is_advanced_search_configured ()     --  Checks whether advanced search is configured.

    get_data_analytics_enabled_clients() --  Retrieves the list of clients which have data
                                             analytics enabled.

"""

from selenium.common.exceptions import NoSuchElementException
from Web.Common.page_object import WebAction, PageService


class SearchSettings:
    """ SearchSettings has methods to operate on analytics engine for reports content search."""
    def __init__(self, web_console):
        self._driver = web_console.browser.driver
        self._web_console = web_console

    @WebAction()
    def get_index_server_name(self):
        """ Retrieves the index server client on which have data analytics enabled.

        Returns:
            list: List of clients.

        """
        try:
            clients = self._driver.find_element(By.XPATH, 
                "//select[@class='analyticsEngine']/option[@selected]").text
        except NoSuchElementException:
            return None

        return clients

    @PageService()
    def is_advanced_search_configured(self):
        """ Checks whether advanced search is configured.

        Returns:
            bool: True if advanced search is configured, False otherwise.

        """
        clients = self.get_index_server_name()
        return True if clients else False
