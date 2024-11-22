from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Module to manage WIA troubleshooting page
"""

from AutomationUtils import logger
from enum import Enum
from selenium.webdriver.support.ui import Select
from Web.Common.page_object import (
    WebAction,
    PageService
)


class ConfigurationTypes(Enum):
    """Available WIA Configuration"""
    type1 = 'Every 15 seconds for next 7 days'
    type2 = 'Every 5 seconds for next 24 hours'
    type3 = 'Every 10 seconds for next 24 hours'
    type4 = 'Every 15 seconds for next 24 hours'
    type5 = 'Every 5 seconds for next 48 hours'
    type6 = 'Every 10 seconds for next 48 hours'
    type7 = 'Every 15 seconds for next 48 hours'
    type8 = 'Every 5 seconds for next 72 hours'
    type9 = 'Every 10 seconds for next 72 hours'
    type10 = 'Every 15 seconds for next 72 hours'
    type11 = 'Every 15 seconds for next 14 days'
    type12 = 'Every 15 seconds for next 365 days'


class SendTrace(Enum):
    interval1 = '7 days'
    interval2 = '6 days'
    interval3 = '5 days'
    interval4 = '4 days'
    interval5 = '3 days'
    interval6 = '2 days'
    interval7 = '1 day'


class RemoteWia:
    """class to manage WIA"""

    def __init__(self, webconsole):
        """
        Args:
            webconsole (WebConsole): The webconsole object
        """
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver
        self._log = logger.get_log()

    @WebAction()
    def _get_current_status(self):
        """Reads the current WIA Status"""
        return self._driver.find_element(By.ID, "wiastatusid").text

    @WebAction()
    def _get_last_operation_time(self):
        """Reads the last WIA request time"""
        return self._driver.find_element(By.ID, "wialasttimeid").text

    @WebAction()
    def _select_wia_configuration(self, configuration=ConfigurationTypes.type1.value):
        """
        selects the WIA configuration from the drop down list
        :param configuration: configuration type
        """
        config_list = Select(self._driver.find_element(By.ID, "WIACONFIGURATION"))
        config_list.select_by_visible_text(configuration)

    @WebAction()
    def _select_send_trace_days(self, send_trace_interval):
        """
        selects the delay period from the drop down list
        :param send_trace_interval:
        """
        delay_list = Select(self._driver.find_element(By.ID, "WIADELAY"))
        delay_list.select_by_visible_text(send_trace_interval)

    @PageService()
    def get_current_status(self):
        """
        Gets the current STATUS of WIA request
        """
        return self._get_current_status()

    @PageService()
    def get_last_operation_time(self):
        """
        Gets the last WIA request time
        """
        return self._get_last_operation_time()

    @PageService()
    def set_wia_configuration(self, configuration=ConfigurationTypes.type1.value):
        """
        selects the WIA configuration
        :param configuration: configuration type
                              use enum class ConfigurationTypes for available configurations
        """
        self._select_wia_configuration(configuration)

    @PageService()
    def set_send_trace_days(self, send_trace_interval=SendTrace.interval1.value):
        """
        selects the delay period to send trace
        :param send_trace_interval: delay interval,
                                    use enum class SendTrace for available intervals
        """
        self._select_send_trace_days(send_trace_interval)
