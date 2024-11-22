import time

from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Module to manage Health Tiles.
"""
from abc import ABC
from abc import abstractmethod

from selenium.webdriver.common.action_chains import ActionChains
from Web.Common.page_object import (WebAction, PageService)
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Reports.health import HealthConstants


class _Tile(ABC):
    def __init__(self, admin_console):

        self._admin_console = admin_console
        self.driver = admin_console.driver
        self._tile_name = self.tile_name()

    @abstractmethod
    def tile_name(self):
        """
        Override this as variable inside subclass and return the
        title name

        The name has to be the exact name displayed on the
        health tile
        """
        raise NotImplementedError

    @WebAction()
    def _mouse_hover_tile(self):
        """
        Mouse hovers over the specified web element
        """
        title = self.driver.find_element(By.XPATH, "//a[text()='" + self._tile_name + "']")
        hover = ActionChains(self.driver).move_to_element(title)
        hover.perform()

    @WebAction()
    def _click_hide_tile(self):
        """
        click hide tiles from the report
        """
        xpath = "//a[text()='%s']/ancestor::div[contains(@class,'tile-header')]" \
                "//div[@title='Hide tile']" % \
                self._tile_name
        hide_tile = self.driver.find_element(By.XPATH, xpath)
        hide_tile.click()

    @WebAction()
    def _click_view_detail(self):
        """
        click view detail of the report
        """
        index_of_driver = len(self.driver.window_handles) - 1  # Find number of driver
        self._mouse_hover_tile()
        xpath = "//a[text()='%s']/ancestor::div[contains(@class,'tile-header')]" \
                "//div[@title='View details']" % \
                self._tile_name
        view_details = self.driver.find_element(By.XPATH, xpath)
        view_details.click()
        if index_of_driver < len(self.driver.window_handles) - 1:
            self.driver.switch_to.window(self.driver.window_handles[index_of_driver + 1])

    @WebAction()
    def _click_alert(self):
        """
        Click the alert
        """
        xpath = "//a[text()='%s']/ancestor::div[contains(@class,'tile-header')]" \
                "//div[@title='Create alert']" % \
                self._tile_name
        hover_alert = self.driver.find_element(By.XPATH, xpath)
        hover_alert.click()

    @WebAction()
    def _get_outcome(self):
        """Get the outcome message from the given report
        Returns:
            text: Outcome of the report"""
        xpath = "//a[text()='" + self._tile_name + "']/ancestor::div[contains(@class,'tile-header')]/" \
                "../div[@class='tile-content']"
        val = self.driver.find_element(By.XPATH, xpath)
        if val.text:
            return val.text
        else:
            raise CVWebAutomationException(f"The outcome is unknown for report : {self._tile_name}"  )

    @WebAction()
    def _get_remarks(self):
        """Get the Remarks message for the given Health Report
        Returns:
            text: Remarks of the given report
        """
        remarks_text = self.driver.find_element(By.XPATH, 
            "//a[text()='" + self._tile_name + "']/ancestor::div[contains(@class,'tile-header')]"
            "/..//p[@class='remark-item']")
        return remarks_text.text

    @WebAction()
    def _get_status(self):
        """Gets the status of the given report
        Returns:
            status: Status of the report.
        """
        health_status_label = self.driver.find_element(By.XPATH, 
            "//a[text()='"+self._tile_name+"']/ancestor::div[contains(@class,'tile-header')]")
        health_status_class = health_status_label.get_attribute('class')
        if 'critical' in health_status_class:
            return HealthConstants.STATUS_CRITICAL
        elif 'warning' in health_status_class:
            return HealthConstants.STATUS_WARNING
        elif 'good' in health_status_class:
            return HealthConstants.STATUS_GOOD
        elif 'info' in health_status_class:
            return HealthConstants.STATUS_INFO
        else:
            raise CVWebAutomationException("The status is unknown for report %s" % self._tile_name)

    @PageService()
    def hide(self):
        """
        Hide the tile from Health page
        Returns:
            bool: True for already hidden, False otherwise
        """
        self._mouse_hover_tile()
        self._click_hide_tile()

    @PageService()
    def get_outcome(self):
        """
        Get the outcome message from the given report
        Returns:
            text: Outcome of the report
        """
        return self._get_outcome()

    @PageService()
    def get_remark(self):
        """
        Get remarks of the report
        Returns:
            text: Remarks of the report
        """
        return self._get_remarks()

    @PageService()
    def access_view_details(self):
        """
        Access view detail from the report
        """
        self._mouse_hover_tile()
        self._click_view_detail()
        time.sleep(5)

    @PageService()
    def access_alert(self):
        """
        Access alert from the report
        """
        self._mouse_hover_tile()
        self._click_alert()
        self._admin_console.wait_for_completion()

    @PageService()
    def get_health_status(self):
        """Get the status of the given report
        Returns:
            status: Status of given report.
        """
        return self._get_status()


class GenericTile(_Tile):
    """Abstract class(_Tile) methods can be used by this class"""
    def __init__(self, admin_console, tile_name):
        self._tile_name = tile_name
        super().__init__(admin_console)

    def tile_name(self):
        """Return tile name"""
        return self._tile_name


class DRBackup(_Tile):
    """Disaster Recovery Backup tile"""
    def tile_name(self):
        return 'Disaster Recovery Backup'

    def get_last_run_date(self):
        """returns last DR backup run time"""
        outcome_txt = self.get_outcome()
        return outcome_txt.split('.')[0].split('ran on ')[1]

    def get_path(self):
        """returns local/UNC"""
        outcome_txt = self.get_outcome()
        return outcome_txt.split('[')[1].split(' path')[0]

    def get_backupset_count(self):
        """return backupset count"""
        outcome_txt = self.get_outcome()
        return int(outcome_txt.split('retain ')[1].split(' metadata')[0])


class SLA(_Tile):
    """Disaster Recovery Backup tile"""
    def tile_name(self):
        return 'SLA'

    def get_sla_percent(self):
        """return sla percent"""
        outcome_txt = self.get_outcome()
        return float(outcome_txt.split('%')[0])
