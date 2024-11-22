from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Module to manage configuration audit report.
"""
from time import sleep
from selenium.webdriver.common.keys import Keys

from Web.Common.page_object import (WebAction, PageService)
from Web.WebConsole.webconsole import WebConsole


class ConfigurationAuditReport:
    """Module to manage configuration audit report"""

    class EntityType:
        """Select entity type from this class"""
        STORAGE_POLICY = "Storage Policy"
        MEDIA_AGENT = "MediaAgent"
        LIBRARY = "Library"
        COMMCELL_PARAMETERS = "CommCell Parameter"
        CLIENT = "Client"

    def __init__(self, web_console: WebConsole):
        self._web_console = web_console
        self._driver = self._web_console.browser.driver

    @WebAction()
    def _select_entity(self, entity_type):
        """Select entity type"""
        self._driver.find_element(By.XPATH, "//*[@id='entityTypes-selection']").click()
        self._driver.find_element(By.XPATH, 
            "//li[@data-name='{0}']".format(entity_type)).click()
        self._web_console.wait_till_load_complete()

    @WebAction()
    def _select_template_commcell(self, select_top_element, commcell_name=None):
        """Select template commcell"""
        if select_top_element is True:
            self._driver.find_element(By.XPATH, "//*[@class='dropdownimage']").click()
            sleep(2)
            self._driver.find_element(By.ID, 'autoCommcells').send_keys(Keys.ARROW_DOWN + "\n")
        elif commcell_name:
            self._driver.find_element(By.ID, 'autoCommcells').clear()
            self._driver.find_element(By.ID, 'autoCommcells').send_keys(commcell_name)
            sleep(2)
            self._driver.find_element(By.PARTIAL_LINK_TEXT, commcell_name).click()
        self._web_console.wait_till_load_complete()

    @WebAction()
    def _set_template_entity(self, select_top_element, entity_name=None):
        """Set template entity name"""
        if select_top_element is True:
            self._select_top_element_auto_entities()
        else:
            self._set_text_in_auto_entities(entity_name)
        self._web_console.wait_till_load_complete()

    @WebAction()
    def _select_top_element_auto_entities(self):
        """Click auto entities drop down"""
        self._driver.find_element(By.XPATH, "//*[@class='entitiesDropdownImage']").click()
        self._driver.find_element(By.ID, 'autoEntities').send_keys(Keys.ARROW_DOWN + "\n")
        self._web_console.wait_till_load_complete()

    @WebAction()
    def _set_text_in_auto_entities(self, text):
        """Set text in auto entities"""
        self._driver.find_element(By.ID, 'autoEntities').clear()
        self._driver.find_element(By.ID, 'autoEntities').send_keys(text)
        sleep(2)
        self._driver.find_element(By.PARTIAL_LINK_TEXT, text).click()
        self._web_console.wait_till_load_complete()

    def _select_mount_path(self, select_top_element, mount_path=None):
        """Select mount path"""
        self._driver.find_element(By.ID, "availableMountPaths-selection").click()
        sleep(2)
        if select_top_element is True:
            self._driver.find_element(By.XPATH, "//*[@id='mountpath_0']").click()
        else:
            self._driver.find_element(By.XPATH, "//li[text()='%s']" % mount_path).click()
        self._web_console.wait_till_load_complete()

    @PageService()
    def configure_report(self, entity_type, select_top_element, *args):
        """
        Configure report with selected entities
        Args:
            entity_type               (String)   --     Name of entity from class 'EntityType'
            select_top_element        (Bool)   --     True/False if top most elements need to be
            *args:             (String Tuple)    --     arguments specific to entity type
        Examples:
            configure_report(TYPE.LIBRARY, True)    --     Selects top elements in Library entity
            configure_report(TYPE.LIBRARY, False, "TOOTHLESS", "lib1", "c:\\mount_path")
                                                 --    Selects specified elements in Library entity
        """
        _type = ConfigurationAuditReport.EntityType
        self._select_entity(entity_type=entity_type)
        if entity_type in [_type.STORAGE_POLICY, _type.MEDIA_AGENT, _type.LIBRARY, _type.CLIENT]:
            if select_top_element is True:
                self._select_template_commcell(select_top_element)
                self._set_template_entity(select_top_element)
                if entity_type == _type.LIBRARY:
                    self._select_mount_path(select_top_element)
            else:
                self._select_template_commcell(select_top_element, args[0])
                self._set_template_entity(select_top_element, args[1])
                if entity_type == _type.LIBRARY:  # For Library entity on mount path is applicable
                    self._select_mount_path(args[2])
        else:
            # For 'CommCell Parameter' entity only template commcell needed to be selected
            if select_top_element is True:
                self._select_template_commcell(select_top_element)
            else:
                self._select_template_commcell(args[0])
        self._web_console.wait_till_load_complete()
