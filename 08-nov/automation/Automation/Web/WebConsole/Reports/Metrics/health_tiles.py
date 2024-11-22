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

from Web.WebConsole.Reports.Metrics.components import HealthTable
from Web.WebConsole.Reports.Metrics.health import HealthConstants


class _Tile(ABC):
    def __init__(self, webconsole):

        self._driver = webconsole.browser.driver
        self._webconsole = webconsole
        self._browser = webconsole.browser
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
        title = self._driver.find_element(By.XPATH, "//div[@data-name='" + self._tile_name + "']")
        hover = ActionChains(self._driver).move_to_element(title)
        hover.perform()

    @WebAction()
    def _click_hide_tile(self):
        """
        click hide tiles from the report
        """
        xpath = "//div[@data-name='%s']//following-sibling::li[@data-ng-click='hideTile()']" % (
            self._tile_name
        )
        hide_tile = self._driver.find_element(By.XPATH, xpath)
        self._browser.click_web_element(hide_tile)

    @WebAction()
    def _click_view_detail(self):
        """
        click view detail of the report
        """
        index_of_driver = len(self._driver.window_handles) - 1  # Find number of driver
        self._mouse_hover_tile()
        xpath = "//div[@data-name='%s']//following-sibling::li[@data-ng-click='viewDetails()']" % \
                (
                    self._tile_name
                )
        view_details = self._driver.find_element(By.XPATH, xpath)
        self._browser.click_web_element(view_details)
        if index_of_driver < len(self._driver.window_handles) - 1 : 
            self._driver.switch_to.window(self._driver.window_handles[index_of_driver + 1])

    @WebAction()
    def _click_alert(self):
        """
        Click the alert
        """
        xpath = "//div[@data-name='%s']//following-sibling::li[@data-ng-click='addAlert()']" % (
            self._tile_name
        )
        hover_alert = self._driver.find_element(By.XPATH, xpath)
        self._browser.click_web_element(hover_alert)

    @WebAction()
    def _get_outcome(self):
        """Get the outcome message from the given report
        Returns:
            text: Outcome of the report"""
        outcome_text = self._driver.find_element(By.XPATH, 
            "//div[@data-name='" + self._tile_name + "']/div[contains(@class, 'tileDetail')]")
        return outcome_text.text

    @WebAction()
    def _get_remarks(self):
        """Get the Remarks message for the given Health Report
        Returns:
            text: Remarks of the given report"""
        remarks_text = self._driver.find_element(By.XPATH, 
            "//div[@data-name='" + self._tile_name + "']/div[@class='remarks']/label")
        return remarks_text.text

    @WebAction()
    def _get_status(self):
        """Gets the status of the given report
        Returns:
            status: Status of the report.
        """
        health_status_label = self._driver.find_element(By.XPATH, 
            "//div[@data-name='" + self._tile_name + "']/div[@id='tileHeader']//label")
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
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_alert(self):
        """
        Access alert from the report
        """
        self._mouse_hover_tile()
        self._click_alert()

    @PageService()
    def get_health_status(self):
        """Get the status of the given report
        Returns:
            status: Status of given report."""
        return self._get_status()


class PruneDBAgentLogs(_Tile):
    """Actions specific to Tile Prune Database Agent Logs comes here"""

    def tile_name(self):
        return 'Security Assessment'

    @PageService()
    def is_disabled(self):
        """Gets Data aging setting status for pruning db agent logs"""
        outcome_txt = self.get_outcome()
        exp_txt = 'Prune all database agent logs only by days retention rule option: '
        if outcome_txt.split(exp_txt)[1] == 'Disabled':
            return True
        return False


class GenericTile(_Tile):
    """Abstract class(_Tile) methods can be used by this class"""
    def __init__(self, web_console, tile_name):
        self._tile_name = tile_name
        super().__init__(web_console)

    def tile_name(self):
        """Return tile name"""
        return self._tile_name


class ValueAssessmentParams:
    """ Parameters available in Value Assessment Report"""
    self_service = 'Self-Service'


class ValueAssessment(_Tile):
    """Actions specific to Tile Prune Database Agent Logs comes here"""

    def tile_name(self):
        return 'Value Assessment'

    def get_param_table(self, param_name):
        """
        Use this get access on health param format table
        Args:
            param_name (ValueAssessmentParams): parameter available in class ValueAssessmentParams

        Returns:
            HealthTable object
        """
        return HealthTable(self._webconsole, 'CommCell Details', param_name)


class Subclients_SP_Assoc(_Tile):
    """Actions specific to Tile Subclients without Storage Policy Association"""

    def tile_name(self):
        return 'Subclients without Storage Policy Association'

    def get_entity_counts(self):
        """Returns client and subclient counts from the outcome"""
        outcome_txt = self.get_outcome()
        entities = {}
        if outcome_txt:
            entities['Subclient']= int(outcome_txt.split(' ')[0])
            entities['client'] = int(outcome_txt.split(' ')[3])
            return entities
        else:
            raise CVWebAutomationException(f'Outcome text is empty in tile [{self.tile_name}]')


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
        return outcome_txt.split('.')[1].split('run with ')[1].split(' path')[0]

    def get_backupset_count(self):
        """return backupset count"""
        outcome_txt = self.get_outcome()
        return int(outcome_txt.split('.')[2].split('retain ')[1].split(' metadata')[0])
