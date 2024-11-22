from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
home page in log monitoring application in the WebConsole

Home is the only class defined in this file

Home:
    __init__()              -- Initializes the Home class object
    _get_count_policy()     -- Gets all the rows of the policy table on LM Home Page
    _click_policy()         -- Selects and opens the given policy from LM home page
    _is_exists_tagname()    -- Check if tag name for ondemand exists on the LM Home Page
    _is_exists_policy()     -- Check if policy name for ondemand exists on the LM Home Page
    get_count_policy()      -- Gets all the rows of the policy table on LM Home Page
    click_policy()          -- Selects and opens the given policy from LM home page
    is_exists_tagname()     -- Check if tag name for ondemand exists on the LM Home Page
    is_exists_policy()      -- Check if policy name for ondemand exists on the LM Home Page

"""
from Web.Common.page_object import WebAction, PageService
from selenium.common.exceptions import NoSuchElementException


class Home(object):
    """
    Handles the operations on home page of Log Monitoring application
    """
    def __init__(self, webconsole):
        """Initializes Home class object"""
        self._webconsole = webconsole
        self._browser = webconsole.browser
        self._driver = webconsole.browser.driver

    @WebAction()
    def _get_count_policy(self, policy_name):
        """
        Gets all the rows of the policy table on LM Home Page

        Args:
            policy_name: name of the policy for which count has to be retrieved
        """
        policy_elem = self._driver.find_element(By.XPATH, "//a[text()='"+policy_name+"']")
        count = policy_elem.find_element(By.XPATH, "../../../following-sibling::td").text
        return count

    @WebAction()
    def select_time_range(self):
        """
        Opens the Time Range dropdown from Log Monitoring Application

        """
        self._driver.find_element(By.XPATH, r"//a[@id = 'all']").click()

    @WebAction()
    def _click_policy(self, policy_name):
        """
        Selects and opens the given policy from LM home page

        Args:
            policy_name: name of the policy to be opened

        """
        self._driver.find_element(By.XPATH, "//a[text()='" + policy_name + "']").click()

    @WebAction()
    def _is_exists_tagname(self, tag_name):
        """
        Check if tag name for ondemand exists on the LM Home Page

        Args:
            tag_name: tag name for the uploaded file

        Example:
            ("tag1")

        Raises:
            Exception:
                if failed to find tag name on LM Home Page
        """
        try:
            if self._driver.find_element(By.LINK_TEXT, tag_name):
                return True
        except NoSuchElementException:
            return False

    @WebAction()
    def _is_exists_policy(self, policy_name):
        """
        Check if given policy name exists on the LM Home Page

        Args:
            policy_name: policy name for the policy to be verified

        Example:
            ("policy1")

        Raises:
            Exception:
                if failed to validate policy name on LM Home Page
        """
        try:
            if self._driver.find_element(By.LINK_TEXT, policy_name):
                return True
        except NoSuchElementException:
            return False

    @PageService()
    def is_exists_tagname(self, tag_name):
        """
        Check if tag name for ondemand exists on the LM Home Page

        Args:
            tag_name: tag name for the uploaded file

        Example:
            ("tag1")

        Raises:
            Exception:
                if failed to find tag name on LM Home Page
        """
        return self._is_exists_tagname(tag_name)

    @PageService()
    def is_exists_policy(self, policy_name):
        """
        Check if given policy name exists on the LM Home Page

        Args:
            policy_name: policy name for the policy to be verified

        Example:
            ("policy1")

        Raises:
            Exception:
                if failed to validate policy name on LM Home Page
        """
        return self._is_exists_policy(policy_name)

    @PageService()
    def click_policy(self, policy_name):
        """
        Selects and opens the given policy from LM Home Page

        Args:
            policy_name: name of the policy to be opened
        """
        self._click_policy(policy_name)
        self._webconsole.wait_till_load_complete()

    @PageService()
    def get_count_policy(self, policy_name):
        """
        Gets the number of log lines indexed for a particular policy

        Args:
            policy_name : the policy for which data is indexed

        Example:
            ("policy1")
        """
        if self._is_exists_policy(policy_name):
            count = self._get_count_policy(policy_name)
            return count
        else:
            raise Exception("Failed to get the count of the log lines indexed")
