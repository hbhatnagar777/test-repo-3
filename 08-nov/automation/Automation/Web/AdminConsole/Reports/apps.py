# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Apps page file"""
from selenium.webdriver.common.by import By
import time

from Reports.storeutils import StoreUtils

from Web.Common.exceptions import (
    CVWebAutomationException
)
from Web.Common.page_object import (
    PageService,
    WebAction
)
from Web.AdminConsole.Components.wizard import Wizard

_STORE_CONFIG = StoreUtils.get_store_config()


class AppsPage:
    """Apps Page class"""

    def __init__(self, admin_console):
        self.admin_console = admin_console
        self.driver = admin_console.driver
        self.admin_console.load_properties(self)
        self.wizard = Wizard(self.admin_console)

    @WebAction()
    def __get_visible_app_names(self):
        """Get name of the first app"""
        return self.wizard.table.get_column_data(column_name='Name')

    @PageService()
    def lookup_app(self, app_name):
        """Find app"""
        # self.__click_search_field()
        self.wizard.table.search_for(app_name)
        time.sleep(2)
        if app_name not in self.__get_visible_app_names():
            raise CVWebAutomationException(
                f"App [{app_name}] not found, lookup failed"
            )

    @PageService()
    def wait_for_load_complete(self, timeout=60):
        """Wait till loading is complete"""
        self.admin_console.wait_for_completion(wait_time=timeout)

    @PageService()
    def get_apps(self):
        """Get all apps on Apps Page"""
        return self.__get_visible_app_names()

    @PageService
    def import_app_from_file(self, file_path):
        self.wizard.table.import_from_file(file_path)

    @WebAction()
    def __confirm_delete(self):
        """Click Yes on confirmation dialogue"""
        self.admin_console.click_by_xpath("//button[contains(@class, 'MuiButtonBase-root')]/div[text("
                                                      ")='Yes']")

    @PageService()
    def delete(self, app_name):
        """Delete app"""
        self.wizard.table.access_action_item(entity_name=app_name, action_item="Delete")
        time.sleep(2)  # Delay in addition to the WebAction delay
        self.__confirm_delete()
        self.wait_for_load_complete()

    @PageService()
    def launch(self, app_name):
        """Launch app"""
        self.wizard.table.access_action_item(entity_name=app_name, action_item="Launch")
        time.sleep(2)  # Delay in addition to the WebAction delay
        self.wait_for_load_complete()
