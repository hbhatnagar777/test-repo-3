from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations related to Commvault trial page
CommvaultTrial : This class provides methods for trail related operations

CommvaultTrial
==============

    navigate_to_commvault_home()  -- To navigate to the commvault home page

    select_free_trial()     -- To select commvault free trial from commvault home page

    fill_trial_form()       -- To fill the free trail form

"""
from Web.AdminConsole.Components.AdminConsoleBase import AdminConsoleBase
from Web.Common.page_object import PageService


class CommvaultTrial(AdminConsoleBase):
    """
    Class for commvault's trial page
    """
    def __init__(self, driver):
        """
        Commvault Trial Class initialization
        """
        super(CommvaultTrial, self).__init__(driver)
        self.driver = driver

    @PageService()
    def navigate_to_commvault_home(self):
        """
        To navigate to the home page of commvault
        """
        self.navigate('https://www.commvault.com')

    @PageService()
    def select_free_trial(self):
        """
        To select commvault free trial

        """
        # To select the free trial
        self.select_hyperlink('FREE TRIALS')
        self.select_hyperlink('START YOUR 30-DAY TRIAL')

    @PageService()
    def fill_trial_form(
            self,
            first_name=None,
            last_name=None,
            phone=None,
            postal_code=None,
            company=None,
            email=None,
            country=None):
        """
        To fill the free trail form

        Args:
            first_name      (str)   -- First name of the new user

            last_name       (str)   -- Last name of the new user

            phone           (str)   -- Phone number of the new user

            postal_code     (str)   -- postal code of the new user

            company         (str)   -- Company the user belongs

            email           (str)   -- Email ID of the new user

            country         (str)   -- Country of the new user

        """
        # To fill all the needed details
        self.fill_form_by_id('FirstName', first_name)
        self.fill_form_by_id('LastName', last_name)
        self.fill_form_by_id('Phone', phone)
        self.fill_form_by_id('PostalCode', postal_code)
        self.fill_form_by_id('Company', company)
        self.fill_form_by_id('Email', email)
        self.select_value_from_dropdown('Country', country)

        # To select the terms and conditions checkbox
        self.driver.find_element(By.ID, 'mktofreetrialterms').click()

        # To submit the form and download trial
        self.click_button('Download my trial')

        # To validate if its redirect to the Thank you page
        if not self.check_if_entity_exists(
                "xpath", "//h1[contains(text(),'Thank you for registering for ')]"):
            raise Exception("Download page is not redirected to the Thank you page")
