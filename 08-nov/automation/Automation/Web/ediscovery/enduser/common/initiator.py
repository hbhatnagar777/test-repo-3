# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""It is the entry point for this app. Hosts functions for signing in/signing out to the site.

Initiator is the only class defined in this module.

Initiator: Creates a browser session on demand & provides login/logout methods.

Initiator:

     __init__()             --  Constructor for this class.

    create_driver_object()  --  Creates a webdriver object.

    login()                 --  Performs login operation.

    logout()                --  Signs out from the site.
"""
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from dynamicindex.utils.constants import ONE_MINUTE
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTimeOutException
from AutomationUtils import config, logger
from .validation import Validation
from .locators import MainPageLocators
from .locators import LoginPageLocators


class Initiator(object):
    """Starts a browser session & sets the various configuration values defined."""

    def __init__(self):
        """Initializes this class."""

        self.driver = None
        self.logger = logger.get_log()

    def create_driver_object(self):
        """Creates a webdriver object."""
        factory = BrowserFactory()
        browser = factory.create_browser_object()
        browser.open()
        self.driver = browser.driver

    def login(self, username, password):
        """Performs login operation.

        Args:
            username    (str)  --  Username of the user to be logged in.

            password    (str)  --  Password of the user to be logged in.

        Raises:
            CVTimeOutException:
                When the site doesn't load.

                If Commvault logo can't be accessed.
        """
        browser_config_values = config.get_config().BrowserConstants
        local_config_values = config.get_config().Ediscovery.EnduserSite
        project_config_values = config.get_config().Ediscovery
        validation = Validation(self.driver)
        url = local_config_values.SEARCHURL
        page_load_timeout = project_config_values.PAGE_LOAD_TIMEOUT
        command_timeout = browser_config_values.IMPLICIT_WAIT_TIME
        self.logger.info("Going to open the webpage: %s", url)
        self.driver.get(url)
        self.logger.info('Waiting for the page to load.')
        wait = WebDriverWait(self.driver, float(page_load_timeout))
        try:
            wait.until(EC.presence_of_element_located(LoginPageLocators.LOGIN_MENU))
        except TimeoutException:
            raise CVTimeOutException(page_load_timeout, "Couldn't locate login menu")
        else:
            self.logger.info("User to be logged in: %s", username)
            username_element = self.driver.find_element(*LoginPageLocators.USERNAME_FIELD)
            password_element = self.driver.find_element(*LoginPageLocators.PASSWORD_FIELD)
            username_element.send_keys(username)
            password_element.send_keys(password)
            login_element = self.driver.find_element(*LoginPageLocators.LOGIN_BUTTON)
            self.logger.info("Clicking on the login button.")
            login_element.click()
            validation.wait_to_load()
            css_element = self.driver.find_element(*MainPageLocators.LOGO_IMAGE)
            text_element = self.driver.find_element(
                *MainPageLocators.APPLICATIONINITIALIZED_TEXT)
            if(EC.visibility_of(css_element) and EC.visibility_of(text_element)):
                self.logger.info("Application initialized successfully.")
            else:
                raise CVTimeOutException(command_timeout, "Couldn't find Commvault logo")
            self.logger.info(
                "Welcome %s",
                self.driver.find_element(
                    *
                    MainPageLocators.LOGGEDIN_USER_TEXT).text)

    def logout(self):
        """Signs out from the site."""
        sleep_seconds = ONE_MINUTE/12
        validation = Validation(self.driver)
        validation.close_search_tabs()
        self.logger.info("Clicking on the logout button.")
        self.driver.find_element(*MainPageLocators.LOGOUT_BUTTON).click()
        self.logger.info("Sleeping for %d seconds", sleep_seconds)
        time.sleep(sleep_seconds)
