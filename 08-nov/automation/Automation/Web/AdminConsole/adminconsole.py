# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
All the actions common to Adminconsole application go here

Class:

    AdminConsole() -> _AdminConsoleBase() -> object()

Functions:

account_activity()             -- Click on account activity option in user settings drop down
"""

import time

from selenium.webdriver.common.by import By

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

from Web.AdminConsole.Components.AdminConsoleBase import _AdminConsoleBase
from Web.AdminConsole.AdminConsolePages.LoginPage import LoginPage
from Web.AdminConsole.Components.Navigator import _Navigator

_CONSTANTS = config.get_config()


class AdminConsole(_AdminConsoleBase):
    """
    Handle's the operations on the Adminconsole

    Examples:

     Recommended way to use the Adminconsole class is as below::

        factory = BrowserFactory()
        browser = factory.create_browser_object()
        browser.open()

        adminconsole1 = Adminconsole(browser, "machine_name")
        adminconsole1.login()  # pass the creds as args to override config file

        # your code goes here

        adminconsole.logout()
        browser.close()

     Adminconsole has a context manager implementation which has to be used as below ::

        factory = BrowserFactory()
        with factory.create_browser_object() as browser:

            # Adminconsole login with default creds from config file
            with Adminconsole(browser, "machine_name") as adminconsole:
                # since 'with' block is used, you are already on the apps page
                # when you hit this line
                adminconsole.your_operations()
                # logout is automatically called by the end of this block

            #Adminconsole login with creds when explicitly specified
            with Adminconsole(browser, "machine", username="ViewAll", password="view") as ac:
               ac.your_operations()

        # browser's close method would be automatically invoked

    """

    def __init__(self,
                 web_browser,
                 machine,
                 username=_CONSTANTS.ADMIN_USERNAME,
                 password=_CONSTANTS.ADMIN_PASSWORD,
                 enable_ssl=False,
                 global_console=None,
                 console_type=None):
        """
        Credentials supplied during creation on Adminconsole class is only
        used when login is done using `with` statement. Its not using by
        login function in any way.

        Args:
            web_browser (Browser): The browser object to use.
            machine (str): Name of the webconsole machine,
                eg. cloud.commvault.com
            username (str): username to use when ``with`` resource block is
                used for login, by default taken from the config file if
                not supplied
            password (str): password to use when ``with`` resource block is
                used for logout operation, by default taken from the config
                file if not supplied
            enable_ssl (boolean): True if 'https' has to be used, False has
                to be set for 'http'
            global_console (Boolean): if True: global console base URL will be formed
                                      else: adminconsole base URL will be formed
            console_type (str): Type of console to be used for login

            console_type Usage:

            * Enum ConsoleTypes defined in adminconsoleconstants can be used for providing input to console_type

                >>> ConsoleTypes.CLOUD_CONSOLE.value
        """
        self.browser = web_browser
        self.driver = web_browser.driver
        self.machine_name = machine
        self.username = username
        self.password = password
        if console_type:
            self.base_url = console_type
        elif global_console:
            self.base_url = "%s://%s/global/"
        else:
            self.base_url = "%s://%s/adminconsole/"
        if enable_ssl:
            self.base_url = self.base_url % ("https", self.machine_name)
        else:
            self.base_url = self.base_url % ("http", self.machine_name)
        self._LOG = logger.get_log()
        super().__init__(self.driver, self.browser)
        self.__navigator = None
        self._is_tfa_login = None

    def __enter__(self):
        self.login(self.username, self.password)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        AdminConsole.logout_silently(self)
        return False

    def __str__(self):
        return f"<Adminconsole host=[{self.machine_name}] id=[{id(self)}]>"

    @property
    def navigator(self):
        if self.__navigator is None:
            self.__navigator = _Navigator(self)
        return self.__navigator

    @property
    def is_tfa_login(self):
        """Return the bool value if the Login was TFA enabled"""
        return self._is_tfa_login

    @is_tfa_login.setter
    def is_tfa_login(self, val):
        """Setter for TFA login"""
        self._is_tfa_login = val

    @WebAction()
    def _open_sso_disabled_login_page(self):
        """Open SSO Disabled login page"""
        self.driver.get(self.base_url + "login?skipSSO=true")
        self.wait_for_completion()

    @WebAction()
    def _open_sso_enabled_login_page(self):
        """Open SSO Enabled login page"""
        self.driver.get(self.base_url)
        self.wait_for_completion()

    @WebAction()
    def _click_username_dropdown(self):
        """ Method to expand user settings drop down """
        user_settings_drop_down = self.driver.find_element(
            By.XPATH, "//div[@class='header-user-settings-anchor']"
        )
        user_settings_drop_down.click()

    @WebAction()
    def _click_logout(self):
        """ Method to click on logout option in user settings drop down"""
        logout = self.driver.find_element(By.XPATH, "//*[@id='user-header-logout']")
        logout.click()

    @WebAction()
    def __get_login_name(self):
        """Get name of the user logged in"""
        username = self.driver.find_element(
            By.XPATH, "//div[@id='header-user-settings-dropdown-anchor']//span[@class='header-user-settings-name']"
        )
        return username.text

    @WebAction(log=False)
    def _is_logout_page(self):
        """Check if current page is logout page"""
        return self.driver.title == "Command Center"

    @WebAction()
    def __close_warning_dialog(self):
        """close warning dialog shown after user login"""
        # close unwanted dialog showing after login like disaster recovery/License expiry etc
        close_btn = (f"//div[contains(@class,'modal confirm-dialog fade')]/*//a[contains(@class,'modal__close-btn')] |"
                     f"//div[@id='LicenseModal']//button")
        if self.check_if_entity_exists("xpath", close_btn):
            self.driver.find_element(By.XPATH, close_btn).click()
            time.sleep(2)

    @PageService()
    def account_activity(self):
        """ Method to click on account activity option in user settings drop down"""
        self._click_username_dropdown()
        activity = self.driver.find_element(By.XPATH, "//*[@id='user-header-accActivity']")
        activity.click()
        self.wait_for_completion()

    @PageService(hide_args=True)
    def login(
            self,
            username=_CONSTANTS.ADMIN_USERNAME,
            password=_CONSTANTS.ADMIN_PASSWORD,
            enable_sso=_CONSTANTS.WebConsole.SSO_LOGIN,
            stay_logged_in=_CONSTANTS.WebConsole.STAY_LOGGED_IN,
            max_tries=_CONSTANTS.WebConsole.LOGIN_MAX_TRIES,
            service_commcell=None,
            on_prem_redirect_hostname=None,
            close_popup = True,
            saml = False,
            pin_generator = None,
            hide_stay_logged_in=False
    ):
        """Login to Adminconsole

        Credentials supplied during creation on Adminconsole class is only
        used when login is done using ``with`` statement. Its not using by
        login function in any way.

        Args:
            username (str): username to login with, if its not supplied the
                default username saved on the config file is used.
            password (str): password to login with, if not supplied it would
                use the default password using on the config file
            enable_sso (bool): If enabled login won't enter username or password,
                and Login button will not be clicked
            stay_logged_in (boolean): Checks the 'Stay Logged In' when 'True',
                leaves it as it is if 'False'. Default value is set from the
                config file.
            max_tries (int): Maximum number of login attempts, if case of any
                webdriver exceptions
            service_commcell(str): Performs router login at provided service commcell if configured/available
            on_prem_redirect_hostname (str) : On-Prem hostname to check login redirection
            close_popup (str) : Close any open pop-up
            pin_generator (func): Callable to get the tfa pin
            hide_stay_logged_in (bool) : stay_logged_in checkbox is hidden
        """
        stay_logged_in = stay_logged_in or _CONSTANTS.SECURITY_TEST
        for i_try in range(max_tries):
            try:
                if enable_sso is False:
                    self._open_sso_disabled_login_page()
                    LoginPage(self).login(username, password, saml, stay_logged_in,
                                          service_commcell=service_commcell,
                                          on_prem_redirect_hostname=on_prem_redirect_hostname,
                                          pin_generator=pin_generator,
                                          hide_stay_logged_in=hide_stay_logged_in)
                else:
                    self._open_sso_enabled_login_page()
                    self.wait_for_completion()
                self.end_time_load = time.time()
                time.sleep(2)  # Button load screen disappears earlier
                break
            except CVTimeOutException as ex:  # Timeout will be retried
                if max_tries == i_try + 1:
                    raise ex
                self._LOG.error(
                    "FH Unable to login, retrying again, received "
                    "error [%s]" % str(ex)
                )
        if close_popup:
            self.close_popup()
        self.__close_warning_dialog()

    @PageService(react_frame=False)
    def logout(self):
        """Logout from Adminconsole"""
        if not _CONSTANTS.SECURITY_TEST:
            if not self._is_logout_page():
                self._click_username_dropdown()
                time.sleep(1)
                self._click_logout()
                time.sleep(1)
                self.wait_for_completion()
            else:
                raise CVWebAutomationException(
                    "Unable to logout from [%s] page" % self.driver.current_url)

    @staticmethod
    def logout_silently(adminconsole):
        """
        Use this logout for resource cleanup inside finally statement
        when you don't want any exception to be raised causing a testcase
        failure.

        This logout is never to be used to check the working of
        Adminconsole logout

        Args:
             adminconsole (AdminConsole): Adminconsole object
        """
        try:
            if adminconsole is not None:
                adminconsole.logout()
        except Exception as err:
            _LOG = logger.get_log()
            err = ";".join(str(err).split("\n"))
            _LOG.warning(f"Silent logout received exception; {err}")

    @PageService()
    def get_login_name(self):
        """Get name of the user currently logged in

        To get the username passed during login, use the self.username variable
        """
        return self.__get_login_name()

    @PageService()
    def goto_adminconsole(self):
        """ To go to adminconsole home page"""
        self._open_sso_disabled_login_page()

    @WebAction()
    def __get_service_commcell_name(self):
        """Get name of the service commcell currently selected"""
        return self.driver.find_element(By.XPATH, '//*[@id="commcell-dropdown"]/span[1]').text

    @PageService()
    def get_service_commcell_name(self):
        """Get name of the service commcell currently selected"""
        return self.__get_service_commcell_name()

    def clear_perfstats(self):
        """Clear the API stats and browser network stats based on the config"""
        if self.performance_test:
            self.browser.clear_browser_networkstats()
            if self._nwlogger:
                self.browser.switch_to_first_tab()
                self.browser.accept_alert("del")
                self.browser.switch_to_latest_tab()
