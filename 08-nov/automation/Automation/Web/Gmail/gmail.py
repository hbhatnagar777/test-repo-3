from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to Gmail page
Gmail : This class provides methods for Gmail page related operations

Gmail
=====

    _click_use_another_account()    -- To click on the use another account on the Gmail page

    _fill_password_field()          -- To click on the password filed

    _click_gmail_account_logo()     -- To click on gmail account logo

    _click_select_all()             -- To click on select all on the Gmail page

    _click_delete_icon()            -- To click on the delete icon on Gmail page

    _select_first_mail()            -- To select the first mail on the Gmail page

    navigate_to_gmail()             -- To navigate to the Gmail page

    login()                         -- To Login to the gmail page

    logout()                        -- To logout from the gmail page

    check_if_inbox_is_present()     -- To check if inbox is present or not

    search_for_mail_from_sender()   -- Searches inbox for mail from the sender

    delete_all_mail_from_sender()   -- Deletes all the mails from the sender

    select_latest_mail_from_sender()-- Selects the latest mail from sender

"""

from selenium.webdriver.common.keys import Keys

from Web.AdminConsole.Components.AdminConsoleBase import AdminConsoleBase
from Web.Common.page_object import PageService, WebAction


class Gmail(AdminConsoleBase):
    """Class for Gmail Page"""
    def __init__(self, driver=None):
        """
        Gmail class initialization

        driver      (obj)   -- Browser driver object

        """
        super(Gmail, self).__init__(driver)
        self.driver = driver
        self._username = None

    @PageService()
    def navigate_to_gmail(self):
        """To navigate to the google mail page"""
        self.navigate('https://mail.google.com')
        self.log.info('Successfully navigated to the Gmail page')

    @WebAction()
    def _click_use_another_account(self):
        """To click on the use another account on the Gmail page"""
        self.driver.find_element(By.XPATH, "//p[text()='Use another account']").click()
        self.wait_for_completion()

    @WebAction()
    def _fill_password_field(self, password):
        """
        To fill the password field on the Gmail login page

        Args:
            password    (str)   -- Password to be entered on the Gmail login page

        """
        password_field = self.driver.find_element(By.XPATH, "//input[@name='password']")
        password_field.clear()
        password_field.send_keys(password + Keys.ENTER)
        self.wait_for_completion()

    @PageService(hide_args=True)
    def login(self, username=None, password=None):
        """
        To Login to the gmail page

        Args:
            username    (str)   -- Email ID of the user

            password    (str)   -- Password of the account

        """
        self._username = username

        if self.check_if_entity_exists('xpath', "//a[@title='Inbox']"):
            self.log.info('Already logged in to Gmail')
            return

        # To select 'sign in' if page is redirected to sign in page
        if self.check_if_entity_exists('xpath', "//a[text()='Sign In']"):
            self.select_hyperlink('Sign In')

        # To click 'use another account' if choose an account page is opened
        if self.check_if_entity_exists('xpath', "//p[text()='Use another account']"):
            self._click_use_another_account()

        # To fill the email or phone number field
        if self.check_if_entity_exists('id', 'identifierId'):
            self.fill_form_by_id('identifierId', username + Keys.ENTER)

        # To fill the password field
        if self.check_if_entity_exists('xpath', "//input[@name='password']"):
            self._fill_password_field(password)

        try:
            self.check_if_inbox_is_present()
            self.log.info('Successfully logged in to Gmail Account for user: "%s"', username)
        except Exception as exp:
            raise Exception('Failed to login to Gmail') from exp

    @WebAction()
    def _click_gmail_account_logo(self):
        """To click on the Gmail account logo"""
        self.driver.find_element(By.XPATH, 
            f"//a[contains(@aria-label,'{self._username}')]").click()
        self.wait_for_completion()

    @PageService()
    def logout(self):
        """To logout from the gmail page"""
        try:
            self.navigate_to_gmail()
            self._click_gmail_account_logo()
            self.select_hyperlink('Sign out')
            self.log.info('Successfully logged out from the Gmail account')
        except Exception:
            raise Exception('Failed to logout, not able to find "Sign out"')

    @WebAction()
    def check_if_inbox_is_present(self):
        """To check if Gmail inbox is present or not"""
        try:
            self.driver.find_element(By.XPATH, "//a[@title='Inbox']")
        except Exception:
            self.log.error('Not able to locate inbox after login')
            raise Exception('Login failed Gmail asks for security questions')

    @WebAction()
    def search_for_mail_from_sender(self, sender=None):
        """
        Searches inbox for mail from the given sender

        Args:
            sender      (str)   -- Full Email ID of the sender

        """
        # To search the inbox for mails from the sender
        search = self.driver.find_element(By.XPATH, "//input[@placeholder='Search mail']")
        search.clear()
        search.send_keys(sender + Keys.ENTER)

    @WebAction()
    def _click_select_all(self):
        """To click on the select all checkbox"""
        try:
            self.driver.find_element(By.XPATH, 
                "//div[@class='aeH']/div[2]//div[@aria-label='Select']/div/span").click()
            self.wait_for_completion()
        except Exception:
            raise Exception('Not able to locate SelectAll checkbox in gmail')

    @WebAction()
    def _click_delete_icon(self):
        """To click on the delete icon"""
        try:
            self.driver.find_element(By.XPATH, 
                "//div[@class='aeH']/div[2]//div[@aria-label='Delete']").click()
            self.wait_for_completion()
        except Exception:
            raise Exception('Not able to locate Delete icon in gmail')

    @PageService()
    def delete_all_mail_from_sender(self, sender=None):
        """
        Deletes all the mail from the sender

        Args:
            sender      (str)   -- Full Email ID of the sender

        """
        # To search the inbox for mails from the sender
        self.search_for_mail_from_sender(sender)

        # To check if there any any mails from the sender or not
        if not self.check_if_entity_exists(
                'xpath',
                "//div[@class='aeF']/div/div[2]/div[5]//tbody/tr[1]/td[5]"):
            self.log.info('No mails from the sender to delete')
            return

        # To select the Select All checkbox
        self._click_select_all()

        # To click on the delete button
        self._click_delete_icon()
        self.log.info('Successfully deleted all the mails from the sender:"%s"', sender)

        # To check if inbox is present
        self.check_if_inbox_is_present()

    @WebAction()
    def _select_first_mail(self):
        """To select the first mail in the inbox"""
        try:
            self.driver.find_element(By.XPATH, 
                "//div[@class='aeF']/div/div[2]/div[5]//tbody/tr[1]/td[5]").click()
            self.wait_for_completion()
        except Exception:
            raise Exception(f'No mail found to select')

    @PageService()
    def select_latest_mail_from_sender(self, sender):
        """
        Selects the latest mail from sender

        Args:
            sender      (str)   -- Full Email ID of the sender

        """
        # To search the inbox for mails from the sender
        self.search_for_mail_from_sender(sender)

        # To select the first mail from the search results if any
        self._select_first_mail()
        self.log.info('Successfully selected the latest mail from the sender:"%s"', sender)
