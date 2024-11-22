# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Login page on the AdminConsole

Class:

    LoginPage() -> AdminConsoleBase() -> object()

Functions:

_init_()            -- initialize the class object
set_username()      -- fill the username field with the specified username
set_password()      -- fill the password field with the specified password
submit_login()      -- login to admin console
_check_onprem_redirection() -- Checks if login page redirected to On Prem
login()             -- attempt login to AdminConsole using the username and password provided
forgot_password()   -- attempt to recover the password for the given username
"""
from time import sleep, time
from urllib.parse import urlparse

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By

from Web.Common.exceptions import (
    CVWebAutomationException
)

from Web.Common.page_object import (
    WebAction,
    PageService
)

from AutomationUtils.config import get_config
from AutomationUtils.mail_box import MailBox, EmailSearchFilter


class LoginPage:
    """
    This class provides the operations that can be perfomed on the Login Page of adminconsole
    """

    def __init__(self, admin_console):
        """
        Args:
            admin_console: adminconsole object
        """
        self.__admin_console = admin_console
        self.__driver = admin_console.driver

    @WebAction()
    def _set_username(self, username):
        """Enter username during login"""
        txt_box = self.__driver.find_element(By.XPATH,
                                             "//input[@id='username']")
        txt_box.send_keys(username)

    @WebAction(hide_args=True)
    def _set_password(self, password):
        """Enter password during login"""
        txt_box = self.__driver.find_element(By.XPATH,
                                             "//input[@id='password']")
        txt_box.send_keys(password)

    @WebAction()
    def _set_stay_logged_in(self):
        """Enable stay logged in during login"""
        chk_box = self.__driver.find_element(By.ID, "stayLoggedIn")
        chk_box.click()

    @WebAction(delay=0)
    def _click_continue_button(self):
        """Click Continue button"""
        continue_btn = self.__driver.find_element(By.ID, "continuebtn")
        continue_btn.click()

    @WebAction(log=False, delay=0)
    def is_login_page(self):
        """Check if current page is login page"""
        return self.__driver.title == "Login"

    @WebAction(delay=0)
    def _click_login(self):
        """Click login button"""
        login_btn = self.__driver.find_element(By.ID, "loginbtn")
        login_btn.click()

    @WebAction()
    def _validate_creds(self):
        """Read invalid creds message during login"""
        login_err = self.__driver.find_elements(By.XPATH, "//div[contains(@class, 'MuiAlert-message')]")
        if login_err:
            err = "Unable to login, received [%s]" % login_err[0].text
            raise CVWebAutomationException(err)

    @WebAction()
    def _select_commcell(self, service_commcell=None):
        """
        if the service commcell name is provided in the input:
            Selects the given service commcell from the availble list
        if No service commcell name is provided in the input:
            Selects the first list item from the availble redirects
        if service commcell name is provided is not found in the available list:
            raise Exception

        Args:
            service_commcell (str)  :   Service commcell name where login should happen
        """
        if service_commcell:
            list_elements = self.__driver.find_elements(By.XPATH,
                                                        "//ul[contains(@class,'idpSSORedirectUrlList list-group')]/li")
            count = 0
            for list_element in list_elements:
                if list_element.text.lower() == service_commcell.lower():
                    index = list_elements.index(list_element) + 1
                    elem = self.__driver.find_element(By.XPATH, '//*[@id="idpSsoredirectUrlDetail"]'
                                                                '[' + str(index) + ']/span')
                    elem.click()
                    count = 1
                    break
            if count == 0:
                err = "Service commcell name provided is not found in the available redirect list"
                raise CVWebAutomationException(err)
        else:
            self.__driver.find_element(By.XPATH, '//*[@id="idpSsoredirectUrlDetail"][1]/span').click()

    @WebAction()
    def _check_if_redirect_list_available(self):
        """
        Gets list of redirects available for user, empty list if none

        Returns:
            redirect_list   (list)  -   list of service commcell hostnames available after enter username
        """
        if self.__admin_console.check_if_entity_exists("id", "multiCommcellDropdown"):
            from Web.AdminConsole.Components.panel import RDropDown
            dialog_choices = RDropDown(self.__admin_console).get_values_of_drop_down(drop_down_id="multiCommcellDropdown")
            if len(dialog_choices) <= 1:
                raise CVWebAutomationException("got single/no choice redirect dialog instead of auto redirection!")
            return dialog_choices
        return []

    @PageService()
    def _check_onprem_redirection(self, hostname):
        """
        Checks if login page redirected to On Prem
        Args:
            hostname (str) : Hostname of the On Prem to verify
        """
        hostname_got = urlparse(self.__admin_console.current_url()).netloc
        if hostname.lower() != hostname_got.lower():
            err = f"OnPrem redirection failed. Expected: '{hostname}' Obtained: '{hostname_got}'"
            raise CVWebAutomationException(err)

    @WebAction()
    def _check_stay_logged_in(self, select=True):
        """
        Web action to check or uncheck the stay logged in option
        Args:
            select  (bool)  :   bool representing whether to select or deselect
        """
        checkbox_method = [self.__admin_console.checkbox_deselect, self.__admin_console.checkbox_select][int(select)]
        checkbox_method("stayLoggedIn")

    def login(self, user_name, password, is_saml, stay_logged_in=True, service_commcell=None,
              on_prem_redirect_hostname=None, pin_generator=None, hide_stay_logged_in=False):
        """
        Login to AdminConsole by using the username and password specified

        Args:
            user_name (str) : username to be used to login
            password (str)  : password to be used to login
            stay_logged_in (bool)  : select/deselect the keep me logged in checkbox
            service_commcell (str)   :  service commcell name where user has to login
            on_prem_redirect_hostname (str) : On-Prem hostname to check login redirection
            is_saml (bool)  : Login via SAML
            pin_generator (func) : Function that can return the OTP Pin to enter
            hide_stay_logged_in (bool) : stay_logged_in checkbox is hidden
        """
        self._set_username(user_name)
        self._click_continue_button()
        self.__admin_console.wait_for_completion()
        if on_prem_redirect_hostname:
            self._check_onprem_redirection(on_prem_redirect_hostname)
        redirects_available = self._check_if_redirect_list_available()
        if redirects_available and not is_saml:
            self._select_commcell(service_commcell=service_commcell)
            self.__admin_console.wait_for_completion()
        if is_saml:
            from Web.IdentityProvider.identity_provider_support import AzureSupport, OktaSupport

            WebDriverWait(self.__driver, 60).until(ec.element_to_be_clickable(
                (By.XPATH, "//*[@name='loginfmt' or @id='okta-signin-username']")))
            self.__admin_console.wait_for_completion()
            
            if 'okta' in self.__admin_console.current_url():
                okta_obj = OktaSupport(self.__admin_console, 'OKTA')
                okta_obj.login(user_name, password)
            elif 'azure' in self.__admin_console.current_url():
                azure_obj = AzureSupport(self.__admin_console, 'AZURE')
                azure_obj.login(user_name, password)
            else:
                err = f"SAML login is not supported for this identity provider [{self.__admin_console.current_url()}]"
                raise CVWebAutomationException(err)
            
            self.__admin_console.start_time_load = time()
            self.__admin_console.login_stats = self.__admin_console.browser.get_browser_networkstats()
        else:
            self._set_password(password)
            if hide_stay_logged_in:
                from Web.AdminConsole.Components.core import Checkbox
                checkbox = Checkbox(self.__admin_console)
                if checkbox.is_exists(id='stayLoggedIn'):
                    raise CVWebAutomationException("Stay Logged In checkbox should be hidden.")
            else:
                self._check_stay_logged_in(stay_logged_in)
            self.__admin_console.start_time_load = time()
            self.__admin_console.login_stats = self.__admin_console.browser.get_browser_networkstats()
            if self._check_for_otp_button():
                if not pin_generator:
                    raise Exception("No Pin generator function supplied to login method")
                pin = pin_generator()
                self._set_pin(pin)
                self._click_login()
                sleep(5)
                self.__admin_console.wait_for_completion()
                if self.is_login_page():
                    # handle case where the pin may have expired by the time selenium presses login
                    pin = pin_generator()
                    self._set_pin(pin)
                    self._click_login()
                self.__admin_console.is_tfa_login = True
            else:
                if pin_generator:
                    self._click_login()
                    if self._check_for_QR_code():
                        from pyotp.totp import TOTP
                        otp_details = self._get_QR_details()
                        totp = TOTP(otp_details['key'])
                        self.__admin_console.click_button(value='Return to log in')
                        self.__admin_console.wait_for_completion()
                        self.login(
                            user_name,
                            password,
                            is_saml,
                            stay_logged_in,
                            service_commcell,
                            on_prem_redirect_hostname,
                            pin_generator=lambda: totp.now()
                        )
                    else:
                        raise CVWebAutomationException("No OTP button present for TFA login!")
                else:
                    self._click_login()
            sleep(5)
            self.__admin_console.wait_for_completion()
            if self.is_login_page():
                self._validate_creds()

            if self._check_for_QR_code():
                from pyotp.totp import TOTP
                otp_details = self._get_QR_details()
                totp = TOTP(otp_details['key'])
                self.__admin_console.click_button(value='Return to log in')
                self.__admin_console.wait_for_completion()
                self.login(
                    user_name,
                    password,
                    is_saml,
                    stay_logged_in,
                    service_commcell,
                    on_prem_redirect_hostname,
                    pin_generator=lambda: totp.now()
                )

    @PageService()
    def get_redirects(self, user_name):
        """
        Enters username and gets the time taken for loading and redirects if any

        Args:
            user_name   (str)   -   username of user to get redirects for

        Returns:
            time_taken  (float) -   approx load time for any auto redirection or dialog choice to render
                                    (due to selenium delay, 8 seconds is minimum, but further delays are from product)
            redirects   (list)  -   list of redirects available or auto redirect already taken place
        """
        initial_url = urlparse(self.__admin_console.current_url()).netloc
        self._set_username(user_name)
        self._click_continue_button()
        start = time()
        self.__admin_console.wait_for_completion()
        time_taken = time() - start
        now_url = urlparse(self.__admin_console.current_url()).netloc
        if now_url != initial_url:
            return time_taken, [now_url]
        return time_taken, self._check_if_redirect_list_available()

    @WebAction()
    def _click_forgot_password(self):
        """clicks on forgot password"""
        self.__driver.find_element(By.XPATH, "//a[@href='forgotPassword.jsp']").click()

    @WebAction(log=False)
    def _is_reset_pwd_page(self):
        """Check page is forgot password page"""
        return self.__admin_console.check_if_entity_exists("xpath", "//a[@href='index.jsp']")

    @WebAction()
    def _return_to_signin(self):
        """click on return to signin"""
        self.__driver.find_element(By.XPATH, "//a[@href='index.jsp']").click()

    @PageService()
    def forgot_password(self, user_name):
        """
        To reset the password

        Args:
            user_name (str): username to be used
        """
        self._click_forgot_password()
        self.__admin_console.wait_for_completion()
        self._set_username(user_name)
        self._click_login()
        self.__admin_console.wait_for_completion()
        WebDriverWait(self.__driver, 60).until(ec.presence_of_element_located(
            (By.ID, "forgotpass-title")))
        if self._is_reset_pwd_page():
            self._return_to_signin()
            self.__admin_console.wait_for_completion()

    @WebAction()
    def _click_get_pin(self):
        """Click get pin button"""
        self.__admin_console.click_button(self.__admin_console.props['label.mfa.verificationMethod.otp.button'])

    @WebAction()
    def _set_pin(self, pin):
        """Click set pin button"""
        self.__admin_console.fill_form_by_id('tfaPin', pin)

    def parse_email_tfa(self, user_name):
        """To get OTP from mail box.

        Returns:
            Int: OTP from the mail.
        """
        self.config = get_config().email
        mailbox = MailBox(mail_server=self.config.server,
                          username=self.config.username,
                          password=self.config.password)
        mailbox.connect()
        search_query = EmailSearchFilter(
            f"CommServe Administrator just doubled your safety!")
        pin = mailbox.get_mail_otp(search_query, user_name)
        mailbox.disconnect()
        return pin

    @WebAction()
    def _check_for_return_btn(self):
        """
        Checks if there is any return to login button (when we first login with TFA enabled then page will contain this button)
        if Yes  : Return True
        else    : Return False
        """
        try:
            return self.__driver.find_element(By.ID, 'goLoginBackBtn').is_displayed()
        except:
            return False

    @WebAction()
    def _check_for_otp_button(self):
        """
        Checks if there are any available redirects for the user
        if Yes  : Return True
        else    : Return False
        """
        try:
            return self.__driver.find_element(By.ID, 'tfaPin').is_displayed()
        except:
            return False

    @WebAction()
    def _check_for_QR_code(self):
        """
        Check if there is any QR code picture

        Returns:
            bool: returns true if QR code picture is present else false
        """
        try:
            image_div = self.__driver.find_element(By.XPATH, '//*[@alt="QR code"]')
        except:
            return False
        if image_div.is_displayed():
            if image_div.size['width'] >= 200 and image_div.size['height'] >= 200:
                return True
            else:
                raise CVWebAutomationException(f"QR Code is not rendered properly! Got size: {image_div.size}")
        else:
            raise CVWebAutomationException("QR Code image is not displayed!")

    @WebAction()
    def _get_QR_details(self):
        """
        Reads the TFA details under QR code in the tfa QR code page

        Returns:
            dict    -   return details of account name, secret key, time based
                example:
                qr_date = {
                    'account': 'commvault.idcprodcert.loc:testuser',
                    'key': 'FQMY5UKVDCBNSLRV',
                    'time based': 'Yes'
                }
        """
        qr_data = {}
        for div in self.__driver.find_elements(By.XPATH, "//*[contains(@class, 'MuiGrid-item')]"):
            key, value = div.text.split(":", 1)
            qr_data[key.strip().lower()] = value.strip()
        return qr_data
