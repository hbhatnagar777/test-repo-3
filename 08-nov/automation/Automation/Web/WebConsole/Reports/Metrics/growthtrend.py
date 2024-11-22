from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Operations related to Growth and trend report page.


GrowthNTrend:

    __init__()                       --  initialize instance of the GrowthNTrend class,
                                         and the class attributes.

    get_entities()                   --  Get all entities present in report

    access_view_details()            --  Access details page of specific entity in report

"""

from AutomationUtils import logger
from Web.WebConsole.webconsole import WebConsole
from Web.Common.page_object import WebAction, PageService


class GrowthNTrend:
    """Access different options for Growth and trend report page"""
    def __init__(self, web_console: WebConsole):
        self._driver = web_console.browser.driver
        self._web_console = web_console
        self._log = logger.get_log()

    @WebAction()
    def _get_entities(self):
        """Get all entities present in growth and trend report page"""
        entities_xpath = "//*[contains(@class, 'grid viewBox')]/div/span"
        return [entity.text.strip() for entity in self._driver.find_elements(By.XPATH, entities_xpath)]

    @WebAction()
    def _click_view_details(self, entity_name):
        """
        Access details page cf specified entity growth and trend report

        Args:
            entity_name            (String)    --  Name of the entity of which growth and
                                                   trend report should be accessed
        """
        view_details_xpath = "//*[contains(@class, 'grid viewBox')]//*[contains(text(), '%s')]" \
                             "/..//a[contains(@class, 'viewdetails')]" % entity_name
        self._driver.find_element(By.XPATH, view_details_xpath).click()

    @PageService()
    def get_entities(self):
        """Get all entities present in growth and trend report"""
        return self._get_entities()

    @PageService()
    def access_view_details(self, entity_name):
        """
        Access details page cf specified entity growth and trend report

        Args:
            entity_name            (String)    --  Name of the entity of which growth and
                                                   trend report should be accessed
        """
        self._click_view_details(entity_name)
        self._web_console.wait_till_load_complete()
