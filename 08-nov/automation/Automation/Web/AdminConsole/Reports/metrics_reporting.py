# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on Metrics Reporting page
"""
from AutomationUtils import logger
from Web.AdminConsole.Components.panel import RPanelInfo
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (
    WebAction,
    PageService
)


class _Metrics:
    """Base Metrics class"""

    def __init__(self, admin_console, metrics_type):
        """
        Args:
            admin_console: adminconsole object
            metrics_type(str)    : Private metrics reporting or Cloud metrics reporting
        """
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__details = None
        self.__panel = RPanelInfo(self.__admin_console, metrics_type)
        self._log = logger.get_log()
        self.__metrics_type = metrics_type

    @property
    def details(self):
        if self.__details is None:
            self.__details = self.get_detail()
        return self.__details

    @WebAction()
    def get_detail(self):
        """Retrieves panel details"""
        self.__details = self.__panel.get_details()
        return self.__details

    @property
    def last_collection_time(self):
        """Returns last collection time as visible in page"""
        if 'Last collection time' not in self.details:
            self._log.info(f"Details from Panel: {self.details}")
            raise CVWebAutomationException(
                f'Last collection time not found in {self.__metrics_type} panel'
            )
        return self.details['Last collection time']

    @property
    def last_upload_time(self):
        """Returns last upload time as visible in page"""
        if 'Last upload time' not in self.details:
            self._log.info(f"Details from Panel: {self.details}")
            raise CVWebAutomationException(
                f'Last upload time not found in {self.__metrics_type} panel'
            )
        return self.details['Last upload time']

    @property
    def next_upload_time(self):
        """Returns last Next time as visible in page"""
        if 'Next upload time' not in self.details:
            self._log.info(f"Details from Panel: {self.details}")
            raise CVWebAutomationException(
                f'Next upload time not found in {self.__metrics_type} panel'
            )
        return self.details['Next upload time']

    @PageService()
    def reload_data(self):
        """Refresh page and refetch panel details"""
        self.__driver.refresh()
        self.__admin_console.wait_for_completion()
        self.get_detail()

    @PageService()
    def enable(self, label):
        """enables metrics"""
        self.__panel.enable_toggle(label)
        self.__admin_console.wait_for_completion()

    @PageService()
    def disable(self, label):
        """disables metrics"""
        self.__panel.disable_toggle(label)
        self.__admin_console.wait_for_completion()

    @PageService()
    def upload_now(self):
        """
        Performs Upload Now operation of metrics
        Raises:
            SDKException:
                if response is not success:
        """
        self.__panel.click_button_from_menu('Actions', 'Upload now')
        RModalDialog(self.__admin_console).click_submit()
        self.__admin_console.wait_for_completion()
        self._log.info(f"{self.__metrics_type} upload now operation completed")

    @PageService()
    def access_settings(self):
        """Access Settings"""
        self.__panel.click_button_from_menu('Actions', 'Settings')
        self.__admin_console.wait_for_completion()


class LocalMetricsReporting:
    """class for operations in local metrics reporting"""

    def __init__(self, admin_console, metrics_type):
        """
        Private metrics reporting class
        Args:
            admin_console: adminconsole object
            metrics_type(str): local_metrics
        """
        self.__panel = RPanelInfo(admin_console, metrics_type)

    @PageService()
    def enable_local_metrics(self):
        """enables local metrics"""
        if not self.__panel.is_toggle_enabled(label='Local metrics reporting on CommServe'):
            self.__panel.enable_toggle('Local metrics reporting on CommServe')

    @PageService()
    def disable_local_metrics(self):
        """ disabled local_metrics"""
        if self.__panel.is_toggle_enabled(label='Local metrics reporting on CommServe'):
            self.__panel.disable_toggle('Local metrics reporting on CommServe')


class RemotePrivateMetrics(_Metrics):
    """Class for operations in private Metrics reporting"""

    def __init__(self, admin_console):
        """
        Private metrics reporting class
        Args:
            admin_console: adminconsole object
        """
        super().__init__(admin_console, 'Remote private metrics reporting')

    @property
    def metrics_server_url(self):
        """Returns last Next time as visible in page"""
        if 'Metrics server URL' not in self.details:
            self._log.info(f"Details from Panel: {self.details}")
            raise CVWebAutomationException(
                f'Metrics server URL not found in {self.__metrics_type} panel'
            )
        return self.details['Metrics server URL']

    @property
    def download_url(self):
        """Returns last Next time as visible in page"""
        download_url = None
        download_url = self.metrics_server_url
        download_url += 'downloads/sqlscripts/'
        return download_url

    @property
    def upload_url(self):
        """Returns last Next time as visible in page"""
        upload_url = None
        upload_url = self.metrics_server_url
        upload_url += 'webconsole/'
        return upload_url

    @PageService()
    def disable(self):
        """Disables Remote Private Metrics Reporting"""
        super().disable(label='Remote private metrics reporting')

    @PageService()
    def enable(self):
        """"Enables Remote Private Metrics Reporting"""
        super().enable(label='Remote private metrics reporting')


class CloudMetrics(_Metrics):
    """Class for operations in private Metrics reporting"""

    def __init__(self, admin_console):
        """
        Cloud metrics reporting class
        Args:
            admin_console: adminconsole object
        """
        super().__init__(admin_console, 'Cloud metrics reporting')

    @PageService()
    def enable(self):
        """Enables Cloud Metrics Reporting"""
        super().enable(label='Cloud metrics reporting')

    @PageService()
    def disable(self):
        """Disables Cloud Metrics Reporting"""
        super().disable(label='Cloud metrics reporting')
