from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Operations related to manage alerts page.


AlertsSettings:

    __init__()                           --  initialize instance of the AlertSettings class,
                                             and the class attributes.

    delete_alerts()                      --  delete alerts

    cleanup_alerts()          --  Deletes alerts containing specific string in alert
                                             name
"""
from time import sleep

from selenium.webdriver.common.keys import Keys

from AutomationUtils import logger
from selenium.common.exceptions import NoSuchElementException
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.cte import ConfigureAlert
from Web.Common.page_object import WebAction, PageService


class AlertSettings:
    """ Trigger/delete/enable/disable alerts from these modules """
    def __init__(self, web_console: WebConsole):
        self._driver = web_console.browser.driver
        self._web_console = web_console
        self._log = logger.get_log()

    @WebAction()
    def _select_alerts(self, alerts):
        """
        Select alerts
        Args:
            alerts(list):list of alert names
        """
        for each_alert in alerts:
            try:
                self._driver.find_element(By.XPATH, 
                    "//*[contains(@title,'" + each_alert + "')]/../td[@class='selectionCB "
                                                           "alarmActions']/div").click()
            except NoSuchElementException:
                raise NoSuchElementException("Alert [%s] is not found in alert settings page "
                                             "to select", each_alert)

    @WebAction()
    def _click_delete(self):
        """click delete"""
        self._driver.find_element(By.XPATH, "(//button[@id='deleteBtn'])[1]").click()

    @WebAction()
    def _accept_delete_alert_warning(self):
        """Accept delete warning"""
        self._driver.switch_to.alert.accept()

    @WebAction()
    def _click_edit_alert(self, alert_name):
        """Click on alert"""
        try:
            xp = "//a[@data-name='%s']" % alert_name
            self._driver.find_element(By.XPATH, xp).click()
        except NoSuchElementException:
            raise NoSuchElementException("[%s] alert is not found in alert's setting page"
                                         % alert_name)

    @WebAction()
    def _select_alert_containing(self, alert_string):
        """
        Select all schedules containing string
        Args:
            alert_string                   (String)       --      String present in alert name
        """
        schedules = self._driver.find_elements(By.XPATH, 
            "//*[contains(@title,'" + alert_string + "')]/../td[@class='selectionCB alarmActions']/div")
        if not schedules:
            raise NoSuchElementException("No alerts are found with name containing [%s]" %
                                         alert_string)
        for each_schedule in schedules:
            each_schedule.click()

    @WebAction()
    def __find_alert(self, alert, alert_level):
        """Finds whether the given alert is present at the given level"""
        alerts = self._driver.find_elements(By.XPATH, 
            "//table[@id='alarmTable0_table']//tbody//tr//td[@data-label='Name']")
        for each in alerts:
            if all(word in each.text for word in [alert, alert_level]):
                if each.find_element(By.XPATH, 
                        "following-sibling::td[@data-label='Status']/span/span").get_attribute("title") == 'Enabled':
                    return True
                return False

    @WebAction()
    def __fetch_email(self, alert, alert_level):
        """Fetches the email address of the given alert at a given level"""
        email = self._driver.find_element(By.XPATH, f"//table[@id='alarmTable0_table']//tbody//tr"
                                                   f"//td[contains(@title,'{alert_level}')"
                                                   f" and contains(@title,'{alert}')]"
                                                   f"/following-sibling::td[@data-label='Email']")
        return email.text

    @WebAction()
    def _get_filter_objects(self):
        """ Gets the filter objects"""
        filter_inp_xpath = "//input[contains(@class, 'inLineFilter')]"
        return self._driver.find_elements(By.XPATH, filter_inp_xpath)

    @WebAction()
    def _get_column_names(self):
        """Gets the column names"""
        enabled_columns_xp = "//div[@id='tableWrapper']//th"
        return [column.text for column in self._driver.find_elements(By.XPATH, enabled_columns_xp)]

    @WebAction()
    def __click_trigger_alert(self):
        """ Clicks trigger alert """
        self._driver.find_element(By.XPATH, "//button[@id='triggerBtn']").click()

    @WebAction()
    def _is_filter_enabled(self):
        """ Check if filter is enabled """
        filter_xp = "//tr[contains(@id,'filterRow')]"
        filter_inp = self._driver.find_elements(By.XPATH, filter_xp)
        if filter_inp:
            return filter_inp[0].is_displayed()
        return False

    @WebAction()
    def _enter_filter_text(self, filters, column_number, value):
        """Enters text to filter panel"""
        filters[column_number].clear()
        filters[column_number].send_keys(value)
        filters[column_number].send_keys(Keys.RETURN)
        sleep(2)

    @PageService()
    def edit_alert(self, alert_name):
        """
        Edit alert
        Args:
            alert_name                    (String)       --         alert name

        Returns:
            ConfigureAlert object
        """
        self._click_edit_alert(alert_name)
        return ConfigureAlert(self._web_console)

    @PageService()
    def cleanup_alerts(self, alert_string):
        """
        delete alerts containing specific string in alert name

        Args:
            alert_string                   (string)      --     alert name to be selected

        """
        try:
            self._select_alert_containing(alert_string)
        except NoSuchElementException:
            return
        self._log.info("Deleting alerts containing [%s] string in alert name", alert_string)
        self._click_delete()
        sleep(3)
        self._accept_delete_alert_warning()
        self._web_console.wait_till_load_complete()

    @PageService()
    def delete_alerts(self, alerts):
        """
        Delete alerts
        Args:
            alerts(list):list of alert names
        """
        self._log.info("Deleting alerts:%s", str(alerts))
        self._select_alerts(alerts)
        self._click_delete()
        sleep(3)
        self._accept_delete_alert_warning()
        self._web_console.wait_till_load_complete()

    @PageService()
    def is_alert_enabled(self, alert, alert_level="worldwide"):
        """ Looks up the Alerts configuration page to get a specific alert

        Args:
            alert   (str)       : The name of the alert

            alert_level (str)   : The level of the alert
                Defaults to "worldwide".

                Other valid levels are
                    *  "CommCell"
                    *  any valid client group, Eg: "automate_client_group"

        Returns:
                bool - True if the alert at the given alert level is present, else False
        """
        return self.__find_alert(alert, alert_level)

    @PageService()
    def fetch_email_address(self, alert, alert_level="worldwide"):
        """

        Args:
            alert   (str)       : The name of the alert

            alert_level (str)   : The level of the alert
                Defaults to "worldwide".

                Other valid levels are
                    *  "CommCell"
                    *  any valid client group, Eg: "automate_client_group"

        Returns:
            str -   email address

        """

        return self.__fetch_email(alert, alert_level)

    @PageService()
    def enable_filter(self):
        """ enables filter on the table """
        if self._is_filter_enabled() is not True:
            filter_icon_xp = "//*[@id='alarmTable0_FilterButton']"
            self._driver.find_element(By.XPATH, filter_icon_xp).click()

    @PageService()
    def set_filter(self, column_name, value):
        """
        Send string in filter. this will enable filter if not enabled
        :param column_name: name of the column to set filter
        :param value: value to be sent in filter
        """
        self.enable_filter()
        filters = self._get_filter_objects()
        try:
            column_number = self._get_column_names().index(column_name)
        except ValueError as excep:
            raise ValueError(
                str(excep) +
                "Column %s doesnt exist in table" % column_name
            )
        self._enter_filter_text(filters, column_number, value)

    @PageService()
    def trigger_alert(self, alerts):
        """ Trigger alerts

        Args:
            alerts(list):list of alert names

        """
        self._select_alerts(alerts)
        self.__click_trigger_alert()
        sleep(2)
        self._accept_delete_alert_warning()
        self._web_console.wait_till_load_complete()

