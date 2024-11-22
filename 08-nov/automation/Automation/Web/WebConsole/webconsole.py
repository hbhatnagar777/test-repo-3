from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""All the actions common to webconsole applications go here"""

import time

from selenium.common.exceptions import (
    NoSuchElementException,
    WebDriverException
)

from AutomationUtils import (
    logger,
    config
)
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import (
    CVTimeOutException,
    CVWebAutomationException
)
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.WebConsole.Apps.apps import AppsPage
from Web.WebConsole.Store import storeapp
from selenium.webdriver.common.keys import Keys

_CONSTANTS = config.get_config()
_STORE_CONFIG = storeapp.get_store_config()


class WebConsole:

    """
    Handle's the operations on the webconsole

    Examples:

     Recommended way to use the WebConsole class is as below::

        factory = BrowserFactory()
        browser = factory.create_browser_object()
        browser.open()

        webconsole1 = WebConsole(browser, "machine_name")
        webconsole1.login()  # pass the creds as args to override config file

        # your code goes here

        webconsole1.logout()
        browser.close()

     WebConsole has a context manager implementation which has to be used as below ::

        factory = BrowserFactory()
        with factory.create_browser_object() as browser:

            # WC login with default creds from config file
            with WebConsole(browser, "machine_name") as webconsole:
                # since 'with' block is used, you are already on the apps page
                # when you hit this line
                webconsole.wait_till_load_complete()
                webconsole.your_operations()
                # logout is automatically called by the end of this block

            # WC login when creds when explicitly specified
            with WebConsole(browser, "machine", username="ViewAll", password="view") as webconsole:
                webconsole.wait_till_load_complete()
                webconsole.your_operations()

        # browser's close method would be automatically invoked

    """
    def __init__(self,
                 web_browser,
                 machine,
                 username=_CONSTANTS.ADMIN_USERNAME,
                 password=_CONSTANTS.ADMIN_PASSWORD,
                 enable_ssl=False):
        """
        Credentials supplied during creation on webconsole class is only
        used when login is done using `with` statement. Its not using by
        login function in any way.

        Args:
            web_browser (Browser): The browser object to use.
            machine (str): Name of the webconsole machine,
            username (str): username to use when ``with`` resource block is
                used for login, by default taken from the config file if
                not supplied
            password (str): password to use when ``with`` resource block is
                used for logout operation, by default taken from the config
                file if not supplied
            enable_ssl (boolean): True if 'https' has to be used, False has
                to be set for 'http'
        """
        self.browser = web_browser
        self._driver = web_browser.driver
        self.machine_name = machine
        self.username = username
        self.password = password
        self.base_url = "%s://%s/webconsole/"
        if enable_ssl:
            self.base_url = self.base_url % ("https", self.machine_name)
        else:
            self.base_url = self.base_url % ("http", self.machine_name)
        self._LOG = logger.get_log()

    def __enter__(self):
        self.login(self.username, self.password)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        WebConsole.logout_silently(self)
        return False

    def __str__(self):
        return f"<WebConsole host=[{self.machine_name}] id=[{id(self)}]>"

    @staticmethod
    def _cookie_value(cookies, token_name):
        cookie_entry = [
            cookie
            for cookie in cookies
            if cookie.get("name") == token_name
        ]
        if len(cookie_entry) == 1:
            return cookie_entry[0].get("value")
        elif len(cookie_entry) > 1:
            possible_entry = [
                cookie
                for cookie in cookie_entry
                if "webconsole" in cookie.get("path", "")
            ]
            if len(possible_entry) == 1:
                return possible_entry[0].get("value")
        raise CVWebAutomationException(
            f"{token_name} not found or ambiguous token "
            f"inside webconsole cookie"
        )

    @property
    def jsessionid(self):
        cookies = self.browser.driver.get_cookies()
        return WebConsole._cookie_value(
            cookies, "JSESSIONID"
        )

    @property
    def csrf(self):
        cookies = self.browser.driver.get_cookies()
        return WebConsole._cookie_value(
            cookies, "csrf"
        )

    @WebAction()
    def _open_sso_disabled_login_page(self, url):
        """Open SSO Disabled login page"""
        self._driver.get(url + "login/index.jsp?disableSSO")

    @WebAction()
    def _open_sso_enabled_login_page(self, url):
        """Open SSO Enabled login page"""
        self._driver.get(url + "login/index.jsp")

    @WebAction()
    def _open_applications_page(self):
        """Open WebConsole applications page"""
        self._driver.get(self.base_url + "applications/")

    @WebAction()
    def _set_username(self, username):
        """Enter username during login"""
        txt_box = self._driver.find_element(By.XPATH, 
            "//input[@id='username']")
        txt_box.send_keys(username)

    @WebAction(hide_args=True)
    def _set_password(self, password):
        """Enter password during login"""
        txt_box = self._driver.find_element(By.XPATH, 
            "//input[@id='password']")
        txt_box.send_keys(password)

    @WebAction()
    def _set_stay_logged_in(self):
        """Enable stay logged in during login"""
        self._driver.find_element(By.ID, "stayLoggedIn").click()

    @WebAction()
    def _click_username_dropdown(self):
        """Click username dropdown opener"""
        user_menu = self._driver.find_element(By.XPATH, 
            "//span[@data-url='/login/username.jsp']")
        user_menu.click()

    @WebAction()
    def _click_continue_button(self):
        """Click Continue button"""
        continue_btn = self._driver.find_element(By.ID, "continuebtn")
        continue_btn.click()

    @WebAction()
    def _click_login(self):
        """Click login button"""
        login_btn = self._driver.find_element(By.ID, "loginbtn")
        login_btn.click()

    @WebAction()
    def _click_logout(self):
        """Click logout button"""
        logout = self._driver.find_element(By.XPATH, 
            "//li[@class='logout']")
        logout.click()

    @WebAction()
    def _click_clear_all_notification(self):
        """Click 'Clear All' notification hyperlink"""
        clear_option = self._driver.find_element(By.XPATH, 
            "//span[text()='Clear All']")
        clear_option.click()

    @WebAction()
    def _click_notification_icon_if_clickable(self):
        """Click notification icon if its visible"""
        try:
            icon = self._driver.find_element(By.ID, "notificationHistoryOpener")
            icon.click()
            return True
        except WebDriverException:
            return False

    @WebAction()
    def _get_all_notifications(self):
        """Get all kind of notifications from webconsole"""
        return [
            n_txt.text for n_txt in self._driver.find_elements(By.XPATH, 
                "//*[@id='notificationHistoryHolder']/ul/li/span[2]"
            )
        ]

    @WebAction()
    def _get_all_error_notifications(self):
        """Read error notification from webconsole's notification dropdown"""
        return [
            n_txt.text for n_txt in self._driver.find_elements(By.XPATH, 
                "//span[contains(@class, 'errorNotification')]"
            )
        ]

    @WebAction()
    def _get_all_unread_error_notifications(self):
        """Get all the unread error notifications"""
        return [
            n_txt.text for n_txt in self._driver.find_elements(By.XPATH, 
                "//span[contains(@class, 'errorNotification') "
                "and contains(@class, 'unreadNotification')]"
            )
        ]

    @WebAction()
    def _get_all_unread_notifications(self):
        """Read unread notifications"""
        return [
            n_txt.text for n_txt in self._driver.find_elements(By.XPATH, 
                "//*[contains(@class, 'unreadNotification')]"
            )
        ]

    @WebAction()
    def _get_all_info_notifications(self):
        """Read all info type notifications from panel"""
        return [
            n_txt.text for n_txt in self._driver.find_elements(By.XPATH, 
                "//*[contains(@class, 'vw-info-notification')]"
            )
        ]

    @WebAction()
    def __get_login_name(self):
        """Get name of the user logged in"""
        username = self._driver.find_element(By.XPATH, 
            "//*[contains(@class, 'userNameValue')]"
        )
        return username.text

    @WebAction()
    def _goto_store_via_url(self):
        """Open Store URL"""
        self._driver.get(self.base_url + "softwarestore/store.do")

    @WebAction()
    def _click_app(self, app_name):
        """Open App from Applications page"""
        link = self._driver.find_element(By.XPATH, 
            "//*[@class='displayText vw-app-text']//*[text()='%s']" %
            str(app_name)
        )
        link.click()

    @WebAction()
    def _validate_creds(self):
        """Read invalid creds message during login"""
        xpath = "//div[contains(@class,'vw-login-message error-box error')]"
        if self._driver.find_element(By.XPATH, xpath):
            err = "Unable to login, received [%s]" % self._driver.find_element(By.XPATH, xpath).text
            raise CVWebAutomationException(err)

    @WebAction(log=False)
    def _is_logout_page(self):
        """Check if current page is logout page"""
        return self._driver.title == "Logout"

    @WebAction(log=False)
    def _is_overlay_screen_displayed(self):
        """Check if overlay screen is visible
        This is the screen used to cover the background when the store
        login popup window opens
        """
        default_wait_time = self.browser.get_implicit_wait_time()
        try:
            self._driver.implicitly_wait(0)
            overlay = self._driver.find_element(By.CLASS_NAME, 
                "ui-widget-overlay"
            )
            return overlay.is_displayed()
        except NoSuchElementException:
            return False
        except Exception as ex:
            self._LOG.warning("Received error while checking for overlay "
                              "loading screen\n[%s]" % str(ex))
            return False
        finally:
            self._driver.implicitly_wait(default_wait_time)

    @WebAction(log=False)
    def _is_background_screen_displayed(self):
        """Check if background screen is visible
        This is the screen used to cover the background on saving, deploying report,
        saving dataset etc.,
        """
        default_wait_time = self.browser.get_implicit_wait_time()
        try:
            self._driver.implicitly_wait(0)
            overlay = self._driver.find_element(By.XPATH, 
                "//div[contains(@class,'modal fade')]"
            )
            return overlay.is_displayed()
        except NoSuchElementException:
            return False
        except Exception as ex:
            log = logger.get_log()
            log.warning("Received error while checking for overlay "
                        "loading screen\n[%s]" % str(ex))
            return False
        finally:
            self._driver.implicitly_wait(default_wait_time)

    @WebAction(log=False)
    def _is_load_mask_displayed(self):
        """Is loadmask screen displayed"""
        js = """
            function isLoadMaskDisplayed() {
                masks = document.getElementsByClassName("loadmask");
                return masks.length > 0;
            }
            return isLoadMaskDisplayed();
        """
        return self._driver.execute_script(js)

    @WebAction(log=False)
    def _is_login_button_spin_load_visible(self):
        """Check if login button spin load is visible"""
        default_wait_time = self.browser.get_implicit_wait_time()
        try:
            self._driver.implicitly_wait(0)
            spin_elem = self._driver.find_element(By.XPATH, 
                "//*[@class='uil-spin']")
            return spin_elem.is_displayed()
        except WebDriverException:
            return False
        finally:
            self._driver.implicitly_wait(default_wait_time)

    @WebAction(log=False)
    def _is_loading_line_displayed(self):
        """Check if the loading line above component is shown"""
        default_wait_time = self.browser.get_implicit_wait_time()
        try:
            self._driver.implicitly_wait(0)
            load_line = self._driver.find_element(By.XPATH, 
                "//*[@class='loading-top hideOnExportFriendly ng-scope']")
            return load_line.is_displayed()
        except WebDriverException:
            return False
        finally:
            self._driver.implicitly_wait(default_wait_time)

    @WebAction(log=False)
    def _is_table_component_loading(self):
        """Is table component loading"""
        try:
            loading_img = self._driver.find_element(By.XPATH, 
                "//*[@class='k-loading-image']"
            )
            return loading_img.is_displayed()
        except WebDriverException:
            return False

    @WebAction(log=False)
    def _is_component_load_displayed(self):
        """Check if the components are faded"""
        js = """
        function isComponentLoadDisplayed() {
            elements = document.getElementsByClassName("maskLayerLabel");
            for (i = 0; i < elements.length; i++) {
                if (elements[i].getAttribute("class").search("ng-hide") < 0) {
                    return true;
                }
            }
            return false;
        }
        return isComponentLoadDisplayed();
        """
        return self._driver.execute_script(js)

    @WebAction()
    def __click_language_dropdown(self):
        """Clicks language drop down"""
        language = self._driver.find_element(By.XPATH, "//*[@data-url='/login/languages.jsp']")
        language.click()

    @WebAction()
    def __select_language(self, locale):
        """Selects language from drop down"""
        language = self._driver.find_element(By.XPATH, "//li[@id='%s']" % locale)
        language.click()

    @PageService()
    def _wait_till_apps_load(self, timeout):
        """Wait till application page is loaded"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self.is_apps_page() is False:
                time.sleep(1)
            else:
                return
        raise CVTimeOutException(
            timeout,
            "Application page did not open",
            self._driver.current_url
        )

    @PageService(log=False)
    def _wait_till_logout_page_load(self, timeout):
        """Wait till logout is complete"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self._is_logout_page() is False:
                time.sleep(1)
            else:
                return
        raise CVTimeOutException(
            timeout,
            "Logout page did not open",
            self._driver.current_url
        )

    @PageService(log=False)
    def _wait_till_login_button_load(self, timeout):
        """Wait till login button's spin load"""
        if not self.is_login_page():
            return
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self._is_login_button_spin_load_visible():
                time.sleep(1)
            else:
                return
        raise CVTimeOutException(
            timeout,
            "Login button spin load",
            self._driver.current_url
        )

    @WebAction(log=False)
    def is_login_page(self):
        """Check if current page is login page"""
        return self._driver.title == "Login"

    @WebAction(log=False)
    def is_apps_page(self):
        """Check if current page is Applications page"""
        return self._driver.title == "Applications"

    @WebAction(log=False)
    def wait_till_loadmask_spin_load(self, timeout=60):
        """Wait till load mask load complete

        This function checks for the blue loading dots which
        is seen on the following
           WW Reports page load
           Dials on Reports dashboard
             and on a couple of other apps like LogMonitoring on WC

        Args:
            timeout (int): Time in seconds after which CVTimeOutException
                exception is raised
        """

        end_time = time.time() + timeout
        while time.time() < end_time:
            if self._is_load_mask_displayed() is False:
                return
            else:
                time.sleep(1)
        raise CVTimeOutException(
            timeout, "Loading screen [loadmask] did not disappear on page",
            self._driver.current_url)

    @WebAction()
    def _click_forgot_password(self):
        """clicks on forgot password"""
        forgot_pwd = self._driver.find_element(By.XPATH, "//a[@href='/webconsole/login/forgotPassword.jsp']")
        forgot_pwd.click()

    @WebAction(hide_args=True)
    def _set_forgot_password(self, password):
        """Enter password during login"""
        txt_box = self._driver.find_element(By.XPATH, "//input[@id='pwd']")
        txt_box.send_keys(password)

    @WebAction(hide_args=True)
    def _set_confirm_password(self, password):
        """Enter confirm password during login"""
        txt_box = self._driver.find_element(By.XPATH, "//input[@id='confirmPassword']")
        txt_box.send_keys(password)

    @WebAction()
    def _get_forgot_pwd_successful_msg(self):
        """ get the forgot password reset is successful message"""
        pwd_reset_label = self._driver.find_element(By.XPATH, "//*/p[@id='forgotpass-title']")
        return pwd_reset_label.text

    @WebAction()
    def _get_reset_password_failure_message(self):
        """verify password reset is successful or not"""
        xpath = "//form/div[@class='form-group'][1]/div[@class='loginMsg error']"
        elem_obj = self._driver.find_element(By.XPATH, xpath)
        return elem_obj.text

    @WebAction()
    def _get_forgot_password_failure_message(self):
        """get password reset message if user name or email adress is not provided"""
        xpath = "//*/div[@class='loginMsg vw-login-message error alert vw-alert-danger']"
        pwd_object = self._driver.find_element(By.XPATH, xpath)
        return pwd_object.text

    @WebAction()
    def _is_password_reset_page(self):
        """Is the current page password reset successfull page"""
        return self._driver.current_url.endswith("resetResult.jsp")

    @WebAction()
    def _is_commcell_dashboard_visible(self):
        """Check if commcell dashboard link is visible in applications page"""
        commcell_dashboard = self._driver.find_elements(By.XPATH, 
            "//*[@class='displayText vw-app-text']//*[text()='CommCell Dashboard']")
        if not commcell_dashboard:
            return False
        return True

    @PageService(log=False)
    def wait_till_table_load(self, timeout=60):
        """Wait till table load"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self._is_table_component_loading():
                time.sleep(1)
            else:
                return
        raise CVTimeOutException(
            timeout,
            "Table loading did not complete",
            self._driver.current_url
        )

    @PageService(log=False)
    def wait_till_overlay_disappears(self, timeout=60):
        """Wait till overlay screen disappear

        The overlay screen is used to cover the background when
        store login popup is opened

        Args:
            timeout (int): Time in seconds after which CVTimeOutException
                exception is raised
        """
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self._is_overlay_screen_displayed():
                time.sleep(1)
            else:
                return
        raise CVTimeOutException(
            timeout,
            "Overlay screen did not disappear",
            self._driver.current_url
        )

    @PageService(log=False)
    def wait_till_window_unfades(self, timeout=60):
        """Wait till the popped up window unfades

        The window is used to cover the background while
        deploying the report, adding dataset.

        Please DO NOT use this method directly or via wait_till_load_complete()
        after clicking save report button , as the save report window unfades quickly
        and deploy report confirmation pops up, thereby waiting for it to unfade.

        Args:
            timeout (int): Time in seconds after which CVTimeOutException
                exception is raised
        """
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self._is_background_screen_displayed():
                time.sleep(1)
            else:
                return
        raise CVTimeOutException(
            timeout,
            "Overlay screen did not disappear",
            self._driver.current_url
        )

    @PageService(log=False)
    def wait_till_load_complete(
            self, timeout=60, overlay_check=False,
            line_check=True, comp_load=True, unfade=False,
            table_load=True):
        """Wait till page it fully loaded

        Use this function as the default function to check if page is loaded.

        Args:
            timeout (int): Waiting interval after which CVTimeOutException
                is raised

            overlay_check (bool): Enable wait_till_overlay_disappears

            line_check (bool): Enable wait_till_line_load

            comp_load (bool): Enables wait_till_component_load

            unfade (bool): Enables wait_till_background_unfades

            table_load (bool): Wait till table loads
        """
        if overlay_check:
            self.wait_till_overlay_disappears(timeout=10)
        self.wait_till_loadmask_spin_load(timeout)
        if line_check:
            self.wait_till_line_load(timeout)
        if comp_load:
            self.wait_till_components_load(timeout)
        if unfade:
            self.wait_till_window_unfades(timeout)
        if table_load:
            self.wait_till_table_load(timeout)

    @PageService(log=False)
    def wait_till_line_load(self, timeout=60):
        """Wait till the blue line disappears before component
        Args:
            timeout (int): Time in seconds after which CVTimeOutException
                exception is raised
        """
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self._is_loading_line_displayed() is True:
                time.sleep(1)  # hidden waiting time for loading to work
            else:
                return
        raise CVTimeOutException(
            timeout, "Overlay screen did not disappear",
            self._driver.current_url)

    @PageService(log=False)
    def wait_till_components_load(self, timeout=60):
        """Check if the loading screen is over any component

        Verifies if the components look faded, seen when CSV export
        icon is clicked on Tables
        Args:
            timeout (int): Time in seconds after which CVTimeOutException
                exception is raised
        """
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self._is_component_load_displayed() is False:
                time.sleep(1)
                return
        raise CVTimeOutException(
            timeout,
            "Component loading screen did not disappear",
            self._driver.current_url
        )

    @PageService(hide_args=True)
    def login(self,
              username=_CONSTANTS.ADMIN_USERNAME,
              password=_CONSTANTS.ADMIN_PASSWORD,
              enable_sso=_CONSTANTS.WebConsole.SSO_LOGIN,
              auto_open_login_page=True,
              stay_logged_in=_CONSTANTS.WebConsole.STAY_LOGGED_IN,
              max_tries=_CONSTANTS.WebConsole.LOGIN_MAX_TRIES,
              timeout=_CONSTANTS.WebConsole.LOGIN_TIMEOUT):
        """Login to webconsole

        Credentials supplied during creation on webconsole class is only
        used when login is done using ``with`` statement. Its not using by
        login function in any way.

        Args:
            username (str): username to login with, if its not supplied the
                default username saved on the config file is used.
            password (str): password to login with, if not supplied it would
                use the default password using on the config file
            enable_sso (bool): If enabled login won't enter username or password,
                and Login button will not be clicked
            auto_open_login_page (bool): Automatically opens the login page
                using driver.get, setting this to False disables the function
                from navigating to login page and starts entering the credentials
                on the currently open page, use this when login page is redirected
                from some other page. If this option is set, the calling code
                has to handle the logic to wait the the target page has loaded.
            stay_logged_in (boolean): Checks the 'Stay Logged In' when 'True',
                leaves it as it is if 'False'. Default value is set from the
                config file.
            max_tries (int): Maximum number of login attempts, if case of any
                webdriver exceptions
            timeout (int): Maximum time to wait for each loading screens during
                login.
        """
        for i_try in range(max_tries):
            try:
                if enable_sso is False:
                    if auto_open_login_page:
                        self._open_sso_disabled_login_page(self.base_url)
                    self._set_username(username)
                    self._click_continue_button()
                    time.sleep(1)
                    self._set_password(password)
                    time.sleep(1)
                    if stay_logged_in or _CONSTANTS.SECURITY_TEST:
                        self._set_stay_logged_in()
                        time.sleep(1)
                    self._click_login()
                else:
                    if auto_open_login_page:
                        self._open_sso_enabled_login_page(self.base_url)
                self._wait_till_login_button_load(timeout)
                time.sleep(2)  # Button load screen disappears earlier
                if self.is_login_page():
                    self._validate_creds()
                if auto_open_login_page:
                    if not self.is_apps_page():
                        self._wait_till_apps_load(timeout)
                break
            except CVTimeOutException as ex:  # Timeout will be retried
                if max_tries == i_try + 1:
                    raise
                self._LOG.error(
                    "FH Unable to login, retrying again, received "
                    "error [%s]" % str(ex)
                )
        self.username = username

    @PageService()
    def logout(self, timeout=60):
        """Logout from webconsole

        Args:
            timeout (int): default time to wait till logout completes
        """
        if not _CONSTANTS.SECURITY_TEST:
            if not self.is_login_page() and not self._is_logout_page():
                self.wait_till_load_complete(overlay_check=True)
                self._click_username_dropdown()
                time.sleep(1)
                self._click_logout()
                time.sleep(1)
                self._wait_till_logout_page_load(timeout)
            else:
                raise CVWebAutomationException(
                    "Unable to logout from [%s] page" % self._driver.current_url)

    @staticmethod
    def logout_silently(webconsole):
        """
        Use this logout for resource cleanup inside finally statement
        when you don't want any exception to be raised causing a testcase
        failure.

        This logout is never to be used to check the working of
        webconsole logout

        Args:
             webconsole (WebConsole): Webconsole object
        """
        try:
            if webconsole is not None:
                webconsole.logout()
        except Exception as err:
            _LOG = logger.get_log()
            err = ";".join(str(err).split("\n"))
            _LOG.warning(f"Silent logout received exception; {err}")

    @PageService()
    def clear_all_notifications(self):
        """Clear all webconsole notifications"""
        if self._click_notification_icon_if_clickable():
            time.sleep(1)
            self._click_clear_all_notification()

    @PageService()
    def get_all_unread_notifications(
            self, expected_count=-1, clear_all=False,
            expected_notifications=None):
        """Read all the unread notifications

        Args:
            expected_count (int): The number of expected notifications, if
                the expected number of notifications are not seen, exception
                is raised. Screenshot is taken without closing the notification
                window

            clear_all (bool): Click the clear all to remove all the notifications
                from the notification list

            expected_notifications (list): List of expected unread notification
                starting from the most recently occurring notification
        """
        notifications = []  # return empty list if icon is not visible
        if self._click_notification_icon_if_clickable():
            time.sleep(1)
            notifications = self._get_all_unread_notifications()
        if len(notifications) != expected_count and expected_count > -1:
            raise CVWebAutomationException(
                "Unexpected number of notifications messages, expected %s "
                ", received [%s]" % (str(expected_count), str(notifications))
            )
        if expected_notifications:
            for expected_message, notification in zip(
                    expected_notifications, notifications):
                if notification != expected_message:
                    raise CVWebAutomationException(
                        f"Expected [{expected_message}] received {notification} "
                        f"notification"
                    )
        if clear_all:
            self._click_clear_all_notification()
        else:
            self._click_notification_icon_if_clickable()
        return notifications

    @PageService()
    def get_all_info_notifications(self):
        """Get all the info type notifications"""
        if self._click_notification_icon_if_clickable():
            time.sleep(1)
            notifications = self._get_all_info_notifications()
            self._click_notification_icon_if_clickable()
            return notifications

        self._LOG.warning("Unable to click on notifications icon")
        return []

    @PageService()
    def get_all_error_notifications(self, raise_error=False, only_unread=False):
        """Read all read/unread notification"""
        if self._click_notification_icon_if_clickable():
            time.sleep(1)
            if only_unread:
                notifications = self._get_all_error_notifications()
            else:
                notifications = self._get_all_unread_error_notifications()
            if raise_error and notifications:
                raise CVWebAutomationException(str(notifications))
            self._click_notification_icon_if_clickable()
            return notifications

        self._LOG.warning("Unable to click on notifications icon")
        return []

    @PageService()
    def get_all_notifications(self):
        """Get all notifications"""
        if self._click_notification_icon_if_clickable():
            time.sleep(1)
            notifications = self._get_all_notifications()
            self._click_notification_icon_if_clickable()
            return notifications

        self._LOG.warning("Unable to click on notifications icon")
        return []

    @PageService()
    def get_login_name(self):
        """Get name of the user currently logged in

        To get the username passed during login, use the self.username variable
        """
        return self.__get_login_name()

    @PageService()
    def goto_mydata(self):
        """Open My Data app"""
        self._click_app("My Data")
        self.wait_till_load_complete()

    @PageService()
    def goto_reports(self):
        """Open reports app"""
        self._click_app("Reports")
        self.wait_till_load_complete()

    @PageService()
    def goto_log_monitoring(self):
        """Open log monitoring app"""
        self._click_app("Monitoring")
        self.wait_till_load_complete()
        self._click_app("Log Monitoring")
        self.wait_till_load_complete()

    @PageService()
    def goto_commcell_dashboard(self):
        """Open CommCell Dashboard app"""
        self._click_app("CommCell Dashboard")
        self.wait_till_load_complete()

    @PageService()
    def goto_download_center(self):
        """Open Download Center app"""
        self._click_app("Download Center")
        self.wait_till_load_complete()

    @PageService(hide_args=True)
    def goto_store(self,
                   direct=False,
                   username=_STORE_CONFIG.PREMIUM_USERNAME,
                   password=_STORE_CONFIG.PREMIUM_USERNAME):
        """Open Store app"""
        from Web.WebConsole.Store import storeapp
        if direct is False:
            self._click_app("Store")
            time.sleep(10)
            storeapp.StoreLogin(self).login(username, password)
        else:
            self._goto_store_via_url()
        self.wait_till_load_complete()
        storeapp.StoreApp(self).wait_till_load_complete()

    @PageService()
    def goto_troubleshooting(self):
        """Open Download Center app"""
        self._click_app("Troubleshooting")
        self.wait_till_load_complete()

    @PageService()
    def goto_applications(self):
        """Open applications page"""
        self._open_applications_page()
        self.wait_till_load_complete()

    @PageService()
    def goto_apps(self):
        """Goto App Studio"""
        self._click_app("Apps")
        self.wait_till_load_complete()
        AppsPage(self).wait_for_load_complete()

    @PageService()
    def set_language(self, language):
        """Changes the webconsole to the given language

        Args:
            language (str)  : The locale id of the language which you want to set.

        """
        self.__click_language_dropdown()
        self.__select_language(language)

    @PageService()
    def goto_webconsole(self):
        """ To go to webconsole home page"""
        self._open_sso_disabled_login_page(self.base_url)

    @PageService()
    def forgot_password(self, user_name):
        """
        Forgot password

        Args:
            user_name (str): username to be used
        """
        self._click_forgot_password()
        self.wait_till_load_complete()
        self._set_username(user_name)
        self._click_login()
        self.wait_till_load_complete()
        if not self._is_password_reset_page():
            err_msg = self._get_forgot_password_failure_message()
            raise CVWebAutomationException(f"Password reset failed with [{err_msg}]")

    @PageService()
    def reset_password(self,
                       password,
                       confirm_password,
                       timeout=_CONSTANTS.WebConsole.LOGIN_TIMEOUT):
        """Reset the password"""
        self._set_forgot_password(password)
        time.sleep(1)
        self._set_confirm_password(confirm_password)
        time.sleep(1)
        self._click_login()  # _click_login is common for both login and reset
        self._wait_till_login_button_load(timeout)
        time.sleep(5)  # Button load screen disappears earlier
        if not self.is_login_page():
            err_msg = self._get_reset_password_failure_message()
            raise CVWebAutomationException(f"Reset password failed with [{err_msg}]")

    @PageService()
    def goto_forms(self):
        """Goto Forms application"""
        self._click_app("Forms")
        self.wait_till_load_complete()

    @PageService()
    def is_commcell_dashboard_visible(self):
        """Check if commcell dashboard link is visible in application page"""
        return self._is_commcell_dashboard_visible()

    @WebAction()
    def scroll_up(self):
        """Scrolls up"""
        self._driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.CONTROL + Keys.HOME)
