from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to GmailHelper
GmailHelper : This class provides methods for gmail related operations

GmailHelper
===========
"""
import time
from Web.Common.page_object import WebAction, PageService
from AutomationUtils import logger
from Web.Gmail.gmail import Gmail
from Web.Common.exceptions import CVTimeOutException


class GmailHelper:
    """ Helper file for gmail operations """
    def __init__(self, driver):

        """
        GmailHelper class initialization

        Args:
            driver    (object)    -- object of driver

        """
        self.log = logger.get_log()
        self.gmail = None
        self.driver = driver
        self.gmail = Gmail(self.driver)

    def navigate_to_gmail(self):
        """ To navigate to the Gmail page """

        self.gmail.navigate_to_gmail()
        self.log.info("Successfully navigated to gmail page")

    def login_to_gmail(self, username, password):
        """ To Login to the gmail page """
        self.navigate_to_gmail()
        self.gmail.login(username, password)
        self.log.info('Successfully logged in to Gmail Account for user: "%s"', username)

    def logout(self):
        """
        To logout from the gmail page

        """
        self.gmail.logout()
        self.log.info('Successfully logged out from the Gmail Account')

    @WebAction()
    def _click_on_email(self, email_obj):
        '''Click on email based on subject from sender address'''
        email_obj.click()

    @WebAction()
    def _read_reqired_email(self, subject):
        '''Click on email based on subject from sender address'''
        xpath = "//*/div[@class='xS']/div[@class='xT']/div[@class='y6']/span"
        list_obj = self.driver.find_elements(By.XPATH, xpath)
        for each_object in list_obj:
            if (str(each_object.text)) == subject:
                return each_object

    @PageService()
    def wait_for_email(self, subject, timeout=120):
        """Wait for email to be recieved with given subject"""
        end_time = time.time() + timeout
        while time.time() < end_time:
            if self._read_reqired_email(subject) is None:
                time.sleep(5)
            else:
                return
        raise CVTimeOutException(
            timeout,
            "Timeout occurred while waiting for reset pwd link",
        )

    @WebAction()
    def _get_reset_pwd_link(self):
        '''Get all emails matching the given to, from and subject'''
        link_obj = self.driver.find_element(By.XPATH, "//div/table/tbody/tr/td/a")
        return link_obj.text

    @WebAction()
    def _read_username_password(self):
        '''Get username and password for shares'''
        elem = self.driver.find_element(By.CLASS_NAME, "ads")
        userinfo_obj = elem.find_elements(By.TAG_NAME, "p")[3]
        return userinfo_obj.text

    @WebAction()
    def _delete_gmail(self):
        """
        To delete the selected / opened gmail
        """
        xpath = "//div[@id=':4']/div/div/div/div[2]/div[3]/div"
        self.driver.find_element(By.XPATH, xpath).click()

    @PageService()
    def search_gmail_with_sender(self, sent_from, subject):
        '''search all emails matching the given from and subject'''
        self.gmail.search_for_mail_from_sender(sent_from)
        self.gmail.wait_for_completion()
        self.wait_for_email(subject)
        email_obj = self._read_reqired_email(subject)
        self._click_on_email(email_obj)

    @PageService()
    def get_reset_pwd_link(self):
        '''Get the reset pwd link from gmail'''
        return self._get_reset_pwd_link()

    @PageService()
    def delete_gmail(self, sender):
        """ Deletes the mail from the given sender """
        self._delete_gmail()
        self.log.info('Successfully deleted email from the sender :"%s"', sender)

    @PageService()
    def read_username_password(self, email):
        '''Get the reset pwd link from gmail'''
        userinfo = self._read_username_password()
        if ('User Name: %s' %email not in userinfo) or ('Password' not in userinfo):
            return False
        return True

    @staticmethod
    def logout_silently(helper):
        """
        Use this logout for resource cleanup inside finally statement
        when you don't want any exception to be raised causing a testcase
        failure.

        Args:
            helper : gmail_helper object
        """
        try:
            if helper is not None:
                helper.logout()
        except Exception as err:
            err = ";".join(str(err).split("\n"))
            logger.get_log().warning(f"Silent logout received exception; {err}")
