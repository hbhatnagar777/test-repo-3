from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Module for React Alert/notification component

Alert
    get_content(wait_time)                      : Gets the alert text
    get_jobid_from_popup(wait_time)             : Gets the job id from pop up
    check_error_message(wait_time, raise_error) : Checks if the alert is displaying any error text
    redirect_from_alert(wait_time)              : Redirect using the link in alert
    close_popup(wait_time)                      : Close the alert popup
"""
import re

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from AutomationUtils.logger import get_log
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import WebAction, PageService


class Alert:
    """Class for handling Mui-Alert react component"""
    def __init__(self, admin_console: AdminConsole) -> None:
        self.__driver = admin_console.driver
        self.__admin_console = admin_console
        self.__xpath = "//*[contains(@class, 'MuiAlert-root')]"

        self.log = get_log()

    @property
    @WebAction(delay=0)
    def _type(self) -> str:
        """Returns the type of alert it is: 'error' | 'info' | 'success' | 'warning'"""
        if not self.__admin_console.check_if_entity_exists('xpath', self.__xpath):
            return ''
        alert_classes = self.__driver.find_element(By.XPATH, self.__xpath).get_attribute('class').lower()
        if 'info' in alert_classes:
            return 'info'
        if 'warning' in alert_classes:
            return 'warning'
        if 'error' in alert_classes:
            return 'error'
        if 'success' in alert_classes:
            return 'success'
        return ''

    @WebAction(delay=0)
    def __read_alert_text(self, wait_time, **kwargs) -> (str, str):
        """
        Reads the text of the alert/toast.

        Args:
            wait_time (int): The maximum time to wait for the alert/toast to appear.

        Keyword Args:
            hyperlink (bool, optional): Include/exclude hyperlink in the alert text. Defaults to False

        Returns:
            tuple: A tuple containing the alert text (str) and the alert type (str).
        """
        xpath_text = self.__xpath + "//*[contains(@class, 'MuiAlert-message')]"
        alert_type, alert_text = "", ""
        try:
            WebDriverWait(self.__driver, wait_time).until(ec.presence_of_element_located((
                By.XPATH, self.__xpath)))
            alert_text = self.__driver.find_element(By.XPATH, xpath_text).text
            alert_type = self._type
            if not alert_text:
                WebDriverWait(self.__driver, wait_time).until(ec.presence_of_element_located((
                    By.XPATH, self.__xpath)))
                alert_text = self.__driver.find_element(By.XPATH, xpath_text).text
                alert_type = self._type
            if kwargs.get('hyperlink', False):
                destination_url = self.__driver.find_element(By.XPATH, f"{xpath_text}//*/a").get_attribute('href')
                alert_text += f" {destination_url}"
            return alert_text, alert_type
        except TimeoutException:
            self.log.warn("Timeout occurred waiting for presence of element")
        return alert_text, alert_type

    @WebAction(delay=0)
    def __click_alert_link(self) -> None:
        """Click on the alert link to get redirected"""
        link_xpath = self.__xpath + "//*[contains(@class, 'MuiAlert-message')]//a"
        if self.__admin_console.check_if_entity_exists('xpath', link_xpath):
            self.__driver.find_element(By.XPATH, link_xpath).click()

    @WebAction(delay=0)
    def __click_close_button(self, wait_time) -> None:
        """Click close button in the alert popup"""
        button_xpath = self.__xpath + "//div[contains(@class, 'MuiAlert-action')]/button[@aria-label='Close']"
        try:
            WebDriverWait(self.__driver, wait_time).until(ec.presence_of_element_located((
                By.XPATH, self.__xpath)))

            if self.__admin_console.check_if_entity_exists('xpath', button_xpath):
                self.__driver.find_element(By.XPATH, button_xpath).click()

        except TimeoutException:
            return

    @PageService()
    def get_content(self, wait_time=60) -> str:
        """
        Gets the alert text

        Args:
            wait_time   (int)   -- time to wait for the popup

        Returns:

            alert_text (str): the alert string
        """
        alert_text, _ = self.__read_alert_text(wait_time)
        return alert_text

    @PageService()
    def get_jobid_from_popup(self, wait_time=60, **kwargs) -> str:
        """
        Gets the job id from the pop-up alert.

        Args:
            wait_time (int): Time in seconds to wait for the job ID.

        Keyword Args:
            hyperlink (bool, optional): Include/exclude hyperlink in the alert text. Defaults to False

        Returns:
            str: The job id for the submitted request.

        Raises:
            CVWebAutomationException: If no alert is popped up to extract the job id.
        """
        alert_text, alert_type = self.__read_alert_text(wait_time, **kwargs)
        if not alert_text:
            alert_text, alert_type = self.__read_alert_text(wait_time, **kwargs)
            if not alert_text:
                raise CVWebAutomationException("No alert is popped up to extract job id")
        if alert_type == 'error':
            raise CVWebAutomationException(alert_text)
        if kwargs.get('hyperlink', False):
            job_id = re.findall(r'jobs/(\d+)', alert_text)[0]
        else:
            job_id = re.findall(r'\d+', alert_text)[0]
        self.log.info("Job %s has started", str(job_id))
        return job_id

    @PageService()
    def check_error_message(self, wait_time=60, raise_error=True) -> str:
        """
        Checks if the alert is displaying any error text
        Args:
            wait_time    (int): Time in seconds to wait for error message
            raise_error (bool): Whether to raise exception if error is spotted
        """
        alert_text, alert_type = self.__read_alert_text(wait_time)
        if alert_type == 'error' and raise_error:
            raise CVWebAutomationException(alert_text)
        if alert_type == 'error':
            return alert_text
        return ''

    @PageService()
    def redirect_from_alert(self, wait_time=60) -> None:
        """
        Redirect by clicking on the link available in alert
        Args:
            wait_time    (int): Time in seconds to wait for alert
        """
        self.__read_alert_text(wait_time)
        self.__click_alert_link()

    @PageService()
    def close_popup(self, wait_time=60) -> None:
        """
        Close the alert popup if present
        Args:
            wait_time    (int): Time in seconds to wait for alert
        """
        self.__click_close_button(wait_time)
