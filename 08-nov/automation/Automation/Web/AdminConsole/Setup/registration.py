# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to Commvault registration page
Registration : This class provides methods for registration related operations

Registration
============

    fill_user_details()                 --  Fills the user details for a new user

    fill_contact_details()              --  Fills the contact details of the user

    fill_mailing_address()              --  Fills in the mailing address of the user

    register_account()                  --  To fill the registration details

    _wait_for_registration_completion() -- To wait for the registration process to complete

"""
from time import sleep

from selenium.common.exceptions import NoSuchElementException
from Web.AdminConsole.Components.AdminConsoleBase import AdminConsoleBase
from Web.Common.page_object import PageService


class Registration(AdminConsoleBase):
    """
    Class for commvault's registration page

    """

    @PageService(hide_args=True)
    def fill_user_details(self, email, password, activation_code=None):
        """
        Fills in the user details during registration
        Args:
            email               (str):   the email ID of the user

            password            (str):   the password of the user

            activation_code     (str):   the code to activate the registration

        Returns:
            None

        """
        self.fill_form_by_id("username", email)
        self.fill_form_by_id("password", password)
        self.fill_form_by_id("confirmPassword", password)
        if self.check_if_entity_exists("name", "activationCode"):
            self.fill_form_by_id("activationCode", activation_code)
        self.click_button("Next")
        self.wait_for_completion()
        self.check_error_message()

    @PageService(hide_args=True)
    def fill_contact_details(self, first_name, last_name, company_name, phone_number):
        """
        Fills in the contact details during registration

        Args:
            first_name:     (str):   first name of the user

            last_name       (str):   last name of the user

            company_name    (str):   company name

            phone_number    (str):   the complete phone no with country and area code
                Example:    001-002-1234567890

        Returns:
            None

        """
        self.fill_form_by_id("firstName", first_name)
        self.fill_form_by_id("lastName", last_name)
        self.fill_form_by_id("companyName", company_name)
        country_code, area_code, phone = phone_number.split("-")

        self.fill_form_by_id("countryCode", country_code)
        self.fill_form_by_id("areaCode", area_code)
        self.fill_form_by_id("phoneNumber", phone)

        self.click_button("Next")
        self.wait_for_completion()
        self.check_error_message()

    @PageService(hide_args=True)
    def fill_mailing_address(self, address1, address2, city, state, postal_code, country):
        """
        Fills in the mailing address details during registration

        Args:
            address1        (str):   line 1 of the address

            address2        (str):   line 2 of the address

            city            (str):   name of the city

            state           (str):   name of the state

            postal_code     (str):   postal code of the place

            country         (str):   name of the country

        Returns:
            None

        """
        self.fill_form_by_id("address1", address1)
        self.fill_form_by_id("address2", address2)
        self.fill_form_by_id("city", city)
        self.fill_form_by_id("state", state)
        self.fill_form_by_id("postalCode", postal_code)
        self.select_value_from_dropdown("country", country)
        self.submit_form(wait=False)
        self._wait_for_registration_completion()

    @PageService(hide_args=True)
    def register_existing_account(
            self,
            email=None,
            password=None,
            activation_code=None):
        """
        To fill the registration details

        Args:
            email           (str)   -- Email address to register account

            password        (str)   -- Password for the account

            activation_code (str)   -- Activation code received in the mail

        """
        self.wait_for_completion()
        if not self.check_if_entity_exists("link", "Use existing account"):
            raise NoSuchElementException(
                "There is no option to register using an existing account.")
        self.select_hyperlink("Use existing account")
        self.fill_form_by_id('cloudEmail', email)
        self.fill_form_by_id('cloudPassword', password)
        if self.check_if_entity_exists("name", "activationCode"):
            self.fill_form_by_id('activationCode', activation_code)

        # To click on the register button
        self.submit_form()

        # To wait for the registration to complete
        self._wait_for_registration_completion()

    def _wait_for_registration_completion(self):
        """
        To wait for the registration process to complete

        """
        while self.check_if_entity_exists('xpath', "//div[text()='Processing...']"):
            pass

        # To check if registration succeeded or not
        self.check_error_message()

        if self.check_if_entity_exists('xpath', "//div[@class='ok']"):
            # To wait for the page redirect to complete
            self.wait_for_completion()


class ZealRegistration:
    """This page represents the registration pages viewed during zeal trial user registration"""
    def __init__(self, admin_console):
        self._admin_console = admin_console

    @PageService(hide_args=True)
    def fill_user_details(self, email, password):
        """Enters the user details needed for registering a user for Zeal"""
        self._admin_console.fill_form_by_id('uname', email)
        self._admin_console.fill_form_by_id('pass', password)
        self._admin_console.fill_form_by_id('confirm', password)
        self._admin_console.click_by_id('createNewAccount_button_#4355')
        from AutomationUtils.logger import get_log
        from Web.Common.exceptions import CVWebAutomationException
        log = get_log()
        log.info('Sleeping for 120 seconds to let the CS process user registration')
        sleep(120)
        if self._admin_console.driver.title != "Login":
            raise CVWebAutomationException("User was not redirected to Login page after user registration")
