from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to Admin Console Login page
LoginPage : This class provides methods for Admin console login related operations

LoginPage
=========

    login()     -- Login to AdminConsole by using the username and password specified

    logout()    -- To logout of AdminConsole

"""

from Web.AdminConsole.Components.AdminConsoleBase import AdminConsoleBase
from Web.Common.page_object import PageService


class LoginPage(AdminConsoleBase):
    """
    Class for commvault's registration page

    """

    @PageService(hide_args=True)
    def login(self, user_name=None, password=None, stay_logged_in=False):
        """
        Login to AdminConsole by using the username and password specified

        Args:
            user_name       (str)   -- username to be used to login

            password        (str)   -- password to be used to login

            stay_logged_in  (bool)  -- select/deselect the keep me logged in checkbox

        """

        if self.check_if_entity_exists("link", "More information"):
            self.select_hyperlink("More information")
            self.driver.find_element(By.ID, "overridelink").click()
            self.wait_for_completion()

        if "Certificate error" in self.driver.title:
            self.driver.find_element(By.ID, 'invalidcert_continue').click()
            self.wait_for_completion()

        self.fill_form_by_id("username", user_name)

        # To click on continue button if exists
        if self.check_if_entity_exists('id', 'continuebtn'):
            self.driver.find_element(By.ID, "continuebtn").click()
            self.wait_for_completion()

        self.fill_form_by_id("password", password)

        if stay_logged_in:
            self.checkbox_select("stayactivebox")
        else:
            self.checkbox_deselect("stayactivebox")

        # To click on login
        self.select_hyperlink('Login')
        self.wait_for_completion()

        # If product in evaluation click on ok
        if self.check_if_entity_exists("xpath", "//div[@class='button-container']/button"):
            self.log.info("Product is in Evaluation. Clicking on Okay")
            self.driver.find_element(By.XPATH, "//div[@class='button-container']/button").click()
            self.log.info("Clicked on Okay")
            self.wait_for_completion()
        self.log.info("Login successful")
        self.wait_for_completion()

    @PageService()
    def logout(self):
        """To Logout from admin console"""
        self.driver.find_element(By.ID, "user-account-name").click()
        self.wait_for_completion()
        self.driver.find_element(By.XPATH, "//li//a[@href='logout.do']").click()
        self.wait_for_completion()
