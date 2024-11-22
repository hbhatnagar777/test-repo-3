# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Recent Download page on the AdminConsole

Classes:

    RecentDownload()

Functions:

        download_recent_item()      -- Downloads the most recent item in the recent download list

"""

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from AutomationUtils import logger

from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Components.table import Rtable


class RecentDownload:
    """
    Class for RecentDownload page
    """

    def __init__(self, admin_page):
        """
        Method to initiate RecentDownload class

        Args:
            admin_page   (Object) :   Admin Page Class object
        """
        self.__admin_console = admin_page
        self.__admin_console.load_properties(self)
        self.__table = Rtable(admin_page)
        self.__driver = admin_page.driver
        self.log = logger.get_log()

    @PageService()
    def download_recent_item(self):
        """Downloads the most recent item in the recent download list"""
        try:
            items_to_download = self.__table.get_column_data("Name")
            if items_to_download:
                item = items_to_download[0]
                self.__table.access_action_item(item, 'Download')
                return item

        except Exception as exp:
            self.log.exception("Error in download_recent_item. %s", str(exp))
            raise exp
