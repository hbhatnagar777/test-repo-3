from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Module to operate on Dashboards in Metrics Reports.
"""
import urllib.parse
from enum import Enum
from time import sleep, time

from AutomationUtils import logger

from Web.WebConsole.webconsole import WebConsole
from Web.Common.exceptions import (
    CVWebAutomationException,
    CVTimeOutException
)
from Web.Common.page_object import (
    WebAction,
    PageService
)


class Users:
    """
    Class to Manage Users panel in Dashboard
    """

    def __init__(self, webconsole):
        self._driver = webconsole.browser.driver
        self._webconsole = webconsole
        self._log = logger.get_log()

    @WebAction()
    def _get_user_state(self, email_id):
        """
        Checks admin user checkbox status for the given user email id

        Returns :
                 bool    -   True/False
        """
        email_id = urllib.parse.quote(email_id)
        admin_xp = "//td[@data-useremail='" + email_id + "']"
        elems = self._driver.find_elements(By.XPATH, admin_xp)
        # first element is the checkbox to mark admin
        if not elems:
            raise CVWebAutomationException("User doesnt exist in view user panel")
        state = elems[1].get_attribute('data-isadmin')
        if state == "false":
            return False
        else:
            return True

    @WebAction()
    def _get_user_name(self, email_id):
        """get user name for the given user email id"""
        return self._driver.find_element(By.XPATH, "//td[text()='" + email_id + "']/../td[1]").text

    @WebAction()
    def _enter_user_name(self, user_name):
        """enters user name"""
        new_user = self._driver.find_element(By.ID, "userName")
        new_user.clear()
        new_user.send_keys(user_name)

    @WebAction()
    def _enter_email(self, email):
        """enters email"""
        new_user = self._driver.find_element(By.ID, "email")
        new_user.clear()
        new_user.send_keys(email)

    @WebAction()
    def _click_add(self):
        """Clicks add button"""
        xp = self._driver.find_element(By.XPATH, "//button[text() ='Add']")
        xp.click()

    @WebAction()
    def _toggle_admin_checkbox(self, email_id):
        """Toggle admin checkbox"""
        email_id = urllib.parse.quote(email_id)
        elems = self._driver.find_elements(By.XPATH, 
            "//td[@data-useremail='" + email_id + "']/span")
        # first element is the checkbox to mark admin
        self._webconsole.browser.click_web_element(elems[0])

    @WebAction()
    def _click_delete_user(self, email_id):
        """Clicks Delete user in view users panel"""
        email_id = urllib.parse.quote(email_id)
        self._driver.find_element(By.XPATH, 
            "//td[@data-useremail='" + email_id + "']/span[@title='Remove User']").click()
        sleep(10)

    @WebAction()
    def _click_delete_confirmation(self, action):
        """Clicks Yes/No in Delete user confirmation pop-up"""
        elements = self._driver.find_elements(By.XPATH, "// button[text() = '"+action+"']")
        for ele in elements:
            if ele.is_displayed():
                ele.click()
                break
        sleep(10)

    @WebAction()
    def _read_user_emails_associated(self):
        """gets the email of users associated"""
        emails_obj = self._driver.find_elements(By.XPATH, "//td[@class='um-user-label'][2]")
        emails = []
        for each_email in emails_obj:
            if each_email.text:
                emails.append(each_email.text)
        return emails

    @WebAction()
    def _close_users_panel(self):
        """Closes view users Panel"""
        close_button = self._driver.find_element(By.XPATH, "//div[contains(@aria-labelledby,"
                                                          "'um-users-dialog')]//button[@class='ui-close-button']")
        self._webconsole.browser.click_web_element(close_button)

    @WebAction()
    def _click_save_as_csv_button(self):
        """Clicks on Save as csv button"""
        csv_button = self._driver.find_element(By.XPATH, "//button[text()='Save as CSV']")
        self._webconsole.browser.click_web_element(csv_button)

    @PageService()
    def close_users_panel(self):
        """close view user panel"""
        self._close_users_panel()

    @PageService()
    def delete_user(self, email_id):
        """
        Deletes the user
        Args:
            email_id: email id of the user to delete
        """
        self._click_delete_user(email_id)
        self._click_delete_confirmation('Yes')
        self._close_users_panel()

    @PageService()
    def add_user(self, user, email):
        """Adds User"""
        self._enter_user_name(user)
        self._enter_email(email)
        self._click_add()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def is_admin_user(self, email_id):
        """Checks the status of the given user

        Args:
            email_id    (str): email id of the user to check

        Returns:
            bool    -   True/False
        """
        return self._get_user_state(email_id)

    @PageService()
    def close(self):
        """closes users panel"""
        self._close_users_panel()

    @PageService()
    def get_users(self):
        """Returns all the users email id associated with the commcell/company"""
        return self._read_user_emails_associated()

    @PageService()
    def save_as_csv(self):
        """Clicks on save as CSV button"""
        self._click_save_as_csv_button()
        self._webconsole.wait_till_load_complete()
        self._close_users_panel()

    @PageService()
    def make_user_admin(self, email_id):
        """Update user as admin from dashboard

        Args:
            email_id    (str): email id of the user to check

        """
        user_name = self._get_user_name(email_id)
        if self.is_admin_user(email_id):
            self._log.info("user '%s' already an admin user", user_name)
            self._close_users_panel()
            return
        self._toggle_admin_checkbox(email_id)
        self._click_delete_confirmation('Yes')
        self._webconsole.wait_till_load_complete()
        sleep(5)
        self._close_users_panel()
        notify_msg = self._webconsole.get_all_unread_notifications(expected_count=1)
        if notify_msg[0] == "Successfully changed the user '" + str(user_name) + "' to a Role Manager.":
            self._log.info("User %s made as admin Successfully", user_name)
        else:
            raise CVWebAutomationException("Unexpected notification received, notification is : "
                                           + str(notify_msg[0]))

    @PageService()
    def make_user_non_admin(self, email_id):
        """Update user as non_admin from dashboard

        Args:
            email_id    (str): email id of the user to check

        """
        user_name = self._get_user_name(email_id)
        if not self.is_admin_user(email_id):
            self._log.info("user '%s' already a non_admin user", user_name)
            return
        self._toggle_admin_checkbox(email_id)
        self._click_delete_confirmation('Yes')
        self._webconsole.wait_till_load_complete()
        sleep(4)
        self._close_users_panel()
        notif_msg = self._webconsole.get_all_unread_notifications(expected_count=1)
        if notif_msg[0] == "Successfully revoked the Role Manager access from the user '" + str(user_name) + "'.":
            self._log.info("User %s made as non_admin Successfully", user_name)
        else:
            raise CVWebAutomationException("Unexpected notification received, notification is : "
                                           + str(notif_msg[0]))


class DashboardTiles(Enum):
    """Tiles present in Dashboard page"""
    SLA = "30sla"
    Strikes = "strike"
    Health = "health-info"


class Dashboard:
    """
    Dashboard can be used to operate on dashboards in Metrics Reports
    """

    def __init__(self, webconsole: WebConsole):
        self._driver = webconsole.browser.driver
        self._webconsole = webconsole
        self._log = logger.get_log()

    @WebAction()
    def _get_sla_txt(self):
        """Read the text for SLA Panel"""
        return self._driver.find_element(By.ID, 'slaPanel').text

    @WebAction()
    def _get_support_incident_txt(self):
        """Read the support incident active and closed count"""
        xpath = "//a[@title='Support Incidents']/..//a[contains(@class,'summary-counts-value')]"
        incidents = self._driver.find_elements(By.XPATH, xpath)
        return {'Active': incidents[0].text, 'Closed': incidents[1].text}

    @WebAction()
    def _get_customer_action_pending_count(self):
        """
        get count of customer actin pending from metrics SLA
        Returns:
            count (INT) : count in int
        """
        pending_count = self._driver.find_elements(By.XPATH, "//span[@id='pendingCustomerActionClientsVal']")
        if pending_count:
            return int(pending_count[0].text)
        return 0

    @WebAction()
    def _get_msp_action_pending_count(self):
        """
        get the count of msp action pending
        Returns:
            count(INT) : count in int
        """
        msp_count = self._driver.find_elements(By.XPATH, "//span[@id='pendingMSPActionClientsVal']")
        if msp_count:
            return int(msp_count[0].text)
        return  0

    @WebAction()
    def _click_view_details(self, tile_name):
        """Clicks view details section of tiles in Dashboard"""
        self._driver.find_element(By.XPATH, "//a[contains(text(),'" + tile_name + "')]").click()

    @WebAction()
    def _click_menu(self):
        """Clicks Action menu"""
        self._driver.find_element(By.XPATH, "//div[@id='reportButton']").click()

    @WebAction()
    def _click_new_user(self):
        """Clicks new user in actions menu"""
        self._driver.find_element(By.ID, 'addNewUserLink').click()

    @WebAction()
    def _click_view_user(self):
        """Clicks new user in actions menu"""
        self._driver.find_element(By.ID, 'viewUsersLink').click()

    @WebAction()
    def _click_refresh(self):
        """Clicks Refresh"""
        self._driver.find_element(By.XPATH, "//li[@id='refreshCommcellSurveyLink']/span").click()

    @WebAction()
    def _click_more_info(self):
        """Clicks More info"""
        self._driver.find_element(By.XPATH, "//a[@class='viewmore']").click()

    @WebAction()
    def _click_troubleshooting(self):
        """Clicks on Troubleshooting icon"""
        self._driver.find_element(By.ID, 'troubleShooting').click()

    @WebAction()
    def _check_commcell_active_status(self):
        """checks for the icon active status"""
        status = self._driver.find_element(By.XPATH, 
            "//li[contains(@class,'sprite icon-connection-status')]")
        if status.get_attribute('title') == 'Active':
            return True
        return False

    @WebAction()
    def _access_commcell_alerts(self):
        """Access commcell alerts"""
        self._driver.find_element(By.LINK_TEXT, 'CommCell Alerts').click()

    @WebAction()
    def _access_commcell_count(self):
        """ Access Commcell count"""
        self._driver.find_element(By.ID, 'commcell-count').click()

    @WebAction()
    def get_active_support_incident(self):
        """get the active and clsoed ticket count"""
        result = self._get_support_incident_txt()
        return result['Active']

    @WebAction()
    def get_closed_support_incident(self):
        """get the active and clsoed ticket count"""
        result = self._get_support_incident_txt()
        return result['Closed']

    @WebAction()
    def get_customer_action_pending_count(self):
        """
        get the customer action pending count
        Returns:
            count (INT) : count of pending customer action

        """
        customer_pending = self._get_customer_action_pending_count()
        return customer_pending

    @WebAction()
    def get_msp_action_pending_count(self):
        """
        get the MSP action pending count
        Returns:
            count (INT) : count of pending MSP action
        """
        msp_pending = self._get_msp_action_pending_count()
        return msp_pending

    @PageService()
    def get_met_sla(self):
        """returns met sla count and Percentage"""
        met_sla_txt = self._get_sla_txt()
        self._log.info("Dashboard string is :" + str(met_sla_txt))
        temp = met_sla_txt.split("Met SLA : ")[1].split(" (")[0]
        met_sla_client_count = int(temp.replace(',', ''))
        met_sla_percent = int(met_sla_txt.split("(")[1].split("%")[0])
        return met_sla_client_count, met_sla_percent

    @PageService()
    def get_missed_sla(self):
        """returns met sla count and Percentage"""
        missed_sla_txt = self._get_sla_txt()
        self._log.info("Dashboard string is :" + str(missed_sla_txt))
        temp = missed_sla_txt.split("Missed SLA : ")[1].split(" (")[0]
        missed_sla_client_count = int(temp.replace(',', ''))
        missed_sla_percent = int(missed_sla_txt.split("(")[2].split("%")[0])
        return missed_sla_client_count, missed_sla_percent

    @PageService()
    def get_sla_percent(self):
        """Returns overall sla percentage """
        dashboard_percent_string = self._get_sla_txt()
        self._log.info("Dashboard string is :" + str(dashboard_percent_string))
        day30_sla_client_count = int(
            str(dashboard_percent_string.split("SLA is\n")[1].split("%")[0]))
        return day30_sla_client_count

    @PageService()
    def view_detailed_report(self, tile_name=None):
        """Access detailed report page for the given report

        Args:
            tile_name (DashboardTiles): value of tile from DashboardTiles enum class
        """
        self._click_view_details(tile_name)
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_add_user(self):
        """access Add user panel """
        self._click_menu()
        sleep(2)
        self._click_new_user()

    @PageService()
    def access_view_user(self):
        """access view user panel"""
        self._click_menu()
        self._click_view_user()
        self._webconsole.wait_till_load_complete()
        sleep(5)

    @PageService()
    def do_instant_refresh(self):
        """performs instant refresh operation"""
        self._click_menu()
        self._click_refresh()

    @PageService()
    def access_commcell_info(self):
        """Access Commcell Info page"""
        self._click_more_info()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_commcell_count(self):
        """ Access Commcell count tile"""
        self._access_commcell_count()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def access_troubleshooting(self):
        """Access troubleshooting page"""
        self._click_troubleshooting()
        self._webconsole.wait_till_load_complete()

    @PageService()
    def is_commcell_active(self):
        """Checks if commcell is active with signalR connection

        Returns:
            True: if connection is active and False if not
        """
        return self._check_commcell_active_status()

    @PageService()
    def access_commcell_alerts(self):
        """Access commcell alerts"""
        self._access_commcell_alerts()
        self._webconsole.wait_till_load_complete()


class Alert:
    """Class that manipulates Alert"""

    class AlertType(Enum):
        """Enum Class for alert types"""
        COMMCELL_DOWN = "CommCell is down"
        DISK_LIBRARY = "Disk Library"
        DDB_DISK = "DDB Disk"
        INDEX_CACHE = "Index Cache"

    def __init__(self, webconsole):
        self._driver = webconsole.browser.driver
        self._webconsole = webconsole

    @WebAction()
    def __click_alert_me(self):
        """Clicks Alert Me Button"""
        alert_button = self._driver.find_element(By.XPATH, "//*[@id='defaultAlertsContainer']")
        alert_button.click()

    @WebAction()
    def __toggle_alert(self, alert):
        """Toggles the given alert"""

        slider = self._driver.find_element(By.XPATH, 
            f"//*[contains(@title,'{alert}')]/ancestor::div[contains(@class,'alert-list')]"
            f"//*[@class='cv-custom-switch-slider']")
        slider.click()

    @WebAction()
    def __is_toggle_enabled(self, alert):
        """Returns True if enabled else False"""
        toggle = self._driver.find_element(By.XPATH, 
            f"//*[contains(@title,'{alert}')]/ancestor::div[contains(@class,'alert-list')]//input")
        return True if toggle.get_attribute("data-operation") in ["ENABLE", "CREATE"] else False

    @WebAction(log=False)
    def __wait_till_toggle_action_completes(self, alert, timeout=20):
        """Waits till each toggle action completes"""
        end_time = time() + timeout
        while time() < end_time:
            if self._driver.find_elements(By.XPATH, 
                    f"//*[contains(@title,'{alert}')]/ancestor::div[contains(@class,'alert-list')]"
                    "//*[@style='display: none;']"):
                return
        raise CVTimeOutException(timeout, f"Toggle Loading did not disappear for {alert}",
                                 self._driver.current_url)

    @WebAction(log=False)
    def __wait_till_alert_loads(self, timeout=60):
        """Check if the loading screen is over on Alert popup
        Args:
            timeout (int): Time in seconds after which CVTimeOutException
                exception is raised
        """
        end_time = time() + timeout
        while time() < end_time:
            if self._driver.find_elements(By.XPATH, 
                    "//*[@id='defaultAlertDialogBox']"
                    "//*[@id='loading-icon' and @style='display: none;']"
            ):
                return
        raise CVTimeOutException(
            timeout, "'Alert Me' loading screen did not disappear", self._driver.current_url
        )

    @PageService()
    def toggle_alerts(self, alerts, enable=True):
        """Toggles the given list of alerts

        Args:
            alerts (list): List of AlertType Enum Members

            enable (bool): Switches on the toggle if True else switches off
        """
        def throw():
            """Throws exception for invalid inputs"""
            raise TypeError("alert parameter must be a list of AlertType Enum Members")

        if not isinstance(alerts, list):
            throw()
        list(map(lambda alert: throw() if alert not in Alert.AlertType else None, alerts))
        self.__click_alert_me()
        self.__wait_till_alert_loads()
        for each_alert in alerts:
            if self.__is_toggle_enabled(each_alert.value) is enable:
                self.__toggle_alert(each_alert.value)
                self.__wait_till_toggle_action_completes(each_alert.value)
        self._driver.find_element(By.XPATH, "//body").click()