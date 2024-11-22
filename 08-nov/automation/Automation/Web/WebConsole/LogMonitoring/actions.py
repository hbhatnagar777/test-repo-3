from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed from the
Actions dropdown on the search page in log monitoring application in WebConsole

Actions:
    __init__()                     -- initializes Actions helper object
    _click_actions()               -- Opens the Actions dropdown on a search page
    _delete_search()               -- Clicks on the delete search option
    _click_ok()                    -- Clicks on the ok button for delete and erase search popup
    _erase_data()                  -- Erases the search data from web console
    delete_search()                -- Deletes the search and all entities related to that search
    erase_data()                   -- Erases the search data from web console
    create_alert()                 -- Creates an alert over the search
    save_to_dashboard()            -- Selects save to dashboard option from the Actions dropdown
    create_schedule()              -- Creates a schedule over the search

Dashboard:
    __init__()                      -- Initializes the dashboard class object
    set_dashboard_name()            -- Sets the dashboard name while saving to dashboard
    click_save_to_dashboard()       -- Clicks on the option to save to dashboard/default dashboard
    click_save_dashboard_button()   -- Clicks on the save button
    set_search_name()               -- Sets the search name while saving to dashboard

Alert:
    __init__()                      -- Initializes the alert class object
    click_create_alert()            -- Clicks on the option to create an alert
    set_alert_name()                -- Sets the alert name
    set_alert_search()              -- Sets the search name
    set_alert_email()               -- Sets the email for alert creation
    close_alert_popup()             -- Closes the pop up for alert creation
    click_save()                    -- Saves the alert

Schedule:
    __init__()                      -- Initializes the schedule class object
    click_schedule()                -- Clicks on the option to create a schedule
    set_schedule_name()             -- Sets the schedule name
    set_schedule_email()            -- Sets the email for schedule creation
    close_schedule_popup()          -- Closes the pop up for schedule creation
    click_save()                    -- Saves the schedule
"""
from Web.Common.page_object import WebAction, PageService
from Web.WebConsole.LogMonitoring.navigator import Navigator


class Actions(object):
    """Handles the operations under Actions dropdown on search page in log monitoring app"""
    def __init__(self, webconsole):
        """Initializes Actions class object"""
        self._webconsole = webconsole
        self._browser = webconsole.browser
        self._driver = webconsole.browser.driver
        self._nav = Navigator(self._webconsole)

    @WebAction(delay=5)
    def _click_actions(self):
        """
        Opens the Actions dropdown on a search page in Log Monitoring Application

        """
        self._driver.find_element(By.XPATH, r"//a[text() = 'Actions']").click()

    @PageService()
    def create_alert(self, alert_name, email):
        """
        Creates an alert over the search
        """
        alert = Alert(self._webconsole)
        self._webconsole.scroll_up()
        self._click_actions()
        alert.click_create_alert()
        self._webconsole.wait_till_load_complete()
        self._nav.switch_frame()
        alert.set_alert_name(alert_name)
        alert.set_alert_email(email)
        alert.click_save()
        self._webconsole.wait_till_load_complete()
        self._driver.switch_to.default_content()
        alert.close_alert_popup()
        self._webconsole.wait_till_load_complete()

    @WebAction()
    def _delete_search(self):
        """
        Clicks on the delete search option
        """
        self._driver.find_element(By.XPATH, r"//span[text() = 'Delete Search']").click()

    @WebAction()
    def _click_ok(self):
        """
        Clicks on the ok button for delete and erase search popup
        """
        self._driver.find_element(By.XPATH, 
            r"//button[@class='buttonContents okSaveClick vw-btn vw-btn-primary']").click()

    @WebAction()
    def _erase_data(self):
        """
        Erases the search data from web console
        """
        self._driver.find_element(By.XPATH, r"//span[text() = 'Erase']").click()

    @PageService()
    def delete_search(self):
        """
        Deletes the search and all entities related to that search
        """
        self._click_actions()
        self._delete_search()
        self._click_ok()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def erase_data(self):
        """
        Erases the search data from web console
        """
        self._click_actions()
        self._erase_data()
        self._click_ok()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def save_to_dashboard(self, search_name, dashboard_name=None):
        """
        Selects the save to dashboard option from the
        Actions dropdown on a search page in Log Monitoring Application

        Args:
            search_name: search name for the search to be saved
            dashboard_name: dashboard name for the user created dashboard

        Example:
            ("search1","dash1")

        """
        dash = Dashboard(self._webconsole)
        self._click_actions()
        dash.click_save_to_dashboard()
        self._webconsole.wait_till_load_complete()
        self._nav.switch_frame()
        dash.set_search_name(search_name)
        if dashboard_name is not None:
            dash.set_dashboard_name(dashboard_name)
        dash.click_save_dashboard_button()
        self._driver.switch_to.default_content()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def create_schedule(self, schedule_name, email):
        """
        Creates a schedule on the given search

        Args:
            schedule_name: alert name for the alert to be created
            email: email id of the recipient for the alert

        Example:
            ("search1","alert1","abc@gmail.com")

        """
        schedule = Schedule(self._webconsole)
        self._click_actions()
        schedule.click_schedule()
        self._webconsole.wait_till_load_complete()
        self._nav.switch_frame()
        schedule.set_schedule_name(schedule_name)
        schedule.set_schedule_email(email)
        schedule.click_save()
        self._webconsole.wait_till_load_complete()
        self._driver.switch_to.default_content()
        schedule.close_schedule_popup()
        self._webconsole.wait_till_load_complete()


class Dashboard:
    """
    Handles the operations on dashboards on Log Monitoring
    """
    def __init__(self, webconsole):
        """Initializes Dashboard class object"""
        self._webconsole = webconsole
        self._browser = webconsole.browser
        self._driver = webconsole.browser.driver

    @WebAction()
    def set_dashboard_name(self, dash_name):
        """
        Sets dashboard name while saving a search to dashboard

        Args:
            dash_name: name of the dashboard to be set
        """
        dashboard_set_name_input = self._driver.find_element(By.ID, "dashBoardTitle")
        dashboard_set_name_input.clear()
        dashboard_set_name_input.send_keys(dash_name)

    @WebAction()
    def click_save_to_dashboard(self):
        """
        Clicks on the option to save to dashboard/default dashboard
        """
        self._driver.find_element(By.XPATH, r"//li[@id = 'saveSearchToDashboard']").click()

    @WebAction()
    def click_save_dashboard_button(self):
        """Clicks on the save button for save to dashboard"""
        self._driver.find_element(By.ID, "okButton").click()

    @WebAction()
    def set_search_name(self, search_name):
        """
        Sets the search name
        Args:
            search_name: search name to be set
        Example:
            "search"
        """
        search_input = self._driver.find_element(By.XPATH, r"//input[@id = 'title']")
        search_input.clear()
        search_input.send_keys(search_name)


class Alert:
    """
    Handles the operations on Alerts on Log Monitoring
    """
    def __init__(self, webconsole):
        """Initializes Alert class object"""
        self._webconsole = webconsole
        self._browser = webconsole.browser
        self._driver = webconsole.browser.driver

    @WebAction()
    def click_create_alert(self):
        """
        Clicks on the option to create an alert
        """
        self._driver.find_element(By.XPATH, r"//span[text() = 'Create Alert']").click()

    @WebAction()
    def set_alert_name(self, alert_name):
        """
        Sets the alert name

        Args:
            alert_name: name of the alert to be created
        """
        name = self._driver.find_element(By.XPATH, r"//input[@id = 'alertName']")
        name.clear()
        name.send_keys(alert_name)

    @WebAction()
    def set_alert_search(self, search_name):
        """
        Sets the search name

        Args:
            search_name: name of the search to be saved for alert creation
        """
        self._driver.find_element(By.XPATH, r"//input[@id = 'title']").send_keys(search_name)

    @WebAction()
    def set_alert_email(self, email):
        """
        Sets the email for alert creation

        Args:
            email: email to be saved for alert creation
        """
        self._driver.find_element(By.XPATH, r"//input[@id = 'recipient']").send_keys(email)

    @WebAction()
    def close_alert_popup(self):
        """
        Closes the pop up for alert creation
        """
        self._driver.find_element(By.XPATH, 
            r"//a[@class='ui-dialog-titlebar-close ui-corner-all']").click()

    @WebAction()
    def click_save(self):
        """
        Saves the alert
        """
        self._driver.find_element(By.ID, "okButton").click()


class Schedule:
    """
    Handles the operations on Schedules on Log Monitoring
    """

    def __init__(self, webconsole):
        """Initializes schedule class object"""
        self._webconsole = webconsole
        self._browser = webconsole.browser
        self._driver = webconsole.browser.driver

    @WebAction()
    def click_schedule(self):
        """
        Clicks on the option to create a schedule
        """
        self._driver.find_element(By.XPATH, r"//span[text() = 'Schedule']").click()

    @WebAction()
    def set_schedule_name(self, schedule_name):
        """
        Sets the schedule name

        Args:
            schedule_name: name of the schedule to be created
        """
        name = self._driver.find_element(By.XPATH, r"//input[@id = 'description']")
        name.clear()
        name.send_keys(schedule_name)

    @WebAction()
    def set_schedule_email(self, email):
        """
        Sets the email for schedule creation

        Args:
            email: email to be saved for schedule creation
        """
        self._driver.find_element(By.XPATH, r"//input[@id = 'emails']").send_keys(email)

    @WebAction()
    def close_schedule_popup(self):
        """
        Closes the pop up for schedule creation
        """
        self._driver.find_element(By.XPATH, "//span[@class='ui-icon ui-icon-closethick']").click()

    @WebAction()
    def click_save(self):
        """
        Saves the schedule
        """
        self._driver.find_element(By.ID, "okButton").click()
