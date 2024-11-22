from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""
This module provides the common functions that can be used in Metallic Hub

Classes:
        Utils           --          Provides helper functions to use common elements in Metallic Hub

        Functions:

            __init__                    --           Constructor for the class

            select_radio_by_id          --           Selects the radio button with the given
                                                     element id

            checkbox_select             --           Selects the checkbox with the given
                                                     form control name attribute

            submit_dialog               --           Submits the dialog

            select_value_from_dropdown  --           Selects value from drop down element

            wait_for_spinner            --           Waits for the spinner element to  complete

"""
from time import sleep
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from Web.Common.page_object import (
    WebAction,
    PageService
)


class Utils:
    """This class provides helpers to common methods in Hub"""

    def __init__(self, adminconsole):
        """Constructor function for this class
        Args :
            adminconsole (obj:'AdminConsole')   : Object of AdminConsole class
        """
        self.adminconsole = adminconsole
        self._driver = adminconsole.driver

    @WebAction()
    def __wait_for_spinner_element(self, wait_time):
        """Waits for spinner element to complete"""
        if self.adminconsole.check_if_entity_exists("xpath",
                                                    "//mdb-spinner[@class = \"ng-star-inserted\"]"):
            WebDriverWait(self._driver, wait_time).until(
                ec.invisibility_of_element_located((By.XPATH,
                                                    "//mdb-spinner[@class = \"ng-star-inserted\"]")))

    @WebAction()
    def select_radio_by_id(self, elem_id):
        """Clicks the radio button with the given element id
        Args :
            elem_id (str)   :   id of the radio button
        """
        self._driver.find_element(By.XPATH, f"//input[@type='radio' and @id=\"{elem_id}\"]"
                                           f"/following-sibling::label").click()

    @WebAction()
    def checkbox_select(self, form_control_name):
        """Selects the checkbox
        Args:
            form_control_name   (str)   :   formcontrolname attribute of the mdb-checkbox tag
        """
        self._driver.find_element(By.XPATH, 
            f"//mdb-checkbox[@formcontrolname =\"{form_control_name}\"]").click()

    @WebAction()
    def submit_dialog(self):
        """ Submits the dialog """
        self._driver.find_element(By.XPATH, 
            "//div[contains(@class, 'modal-content')]//button[contains(@class, 'btn btn-secondary') and not(contains("
            "@class,'ng-hide'))]"
        ).click()

    @WebAction()
    def select_value_from_dropdown(self, form_control_name, value):
        """Selects value from drop down element
        Args :
            form_control_name   :   formcontrolname attribute of the mdb-select tag
            value               :   value to be selected from dropdown
        """
        self._driver.find_element(By.XPATH, 
            f"//mdb-select[@formcontrolname = \"{form_control_name}\"]").click()
        sleep(5)
        dropdown_values_xpath = "//mdb-select//mdb-select-dropdown//li[@role='option']"
        dropdown_values = self._driver.find_elements(By.XPATH, dropdown_values_xpath)
        for dropdown_value in dropdown_values:
            if value.lower() == dropdown_value.text.lower():
                dropdown_value.click()
                return
        raise Exception(f"Exception raised in __select_value_from_dropdown. "
                        f"No element with value, {value}, found in dropdown {form_control_name}")

    @PageService()
    def wait_for_spinner(self):
        """Waits for the spinner element to  complete"""
        self.__wait_for_spinner_element(wait_time=300)

    @WebAction()
    def tab_identifier(self):
        """
        get the current tab on the metallic configuration page
        Returns:
            str : name of the current tab
        """
        current_tab_xpath = "//li[contains(@class,'active')]//span[@class = 'step-label'] | " \
                            "//li[contains(@class,'active')]//div[contains(@class,'wizard-step-text')]"
        current_tab = self._driver.find_element(By.XPATH, current_tab_xpath)
        return current_tab.text

    @WebAction()
    def get_small_text_info(self, xpath):
        """
        get the status of task completions
            like : client creaton, local storage creation ..etc
        Args:
            xpath   (str):  base xpath of the current tab

        Returns:
            (str): success info the task
        """
        xpath1 = xpath + "//small[contains(@class,'text-info')]"
        xpath2 = xpath + "//div[contains(@class,'bc-step-badge-container')][3]" \
                         "//div[contains(@class,'bc-step-badge-content')]//form/div[2]"
        xpath = xpath1 + " | " + xpath2
        info_elem = self._driver.find_element(By.XPATH, xpath)
        return info_elem.text

    @WebAction()
    def get_small_danger_info(self, xpath):
        """
        get the status of task completions
            like : client creaton, local storage creation ..etc
        Args:
            xpath   (str):  base xpath of the current tab
        Returns:
            (str): failure info the task
        """
        xpath1 = xpath + "//small[contains(@class,'text-danger')]"
        xpath2 = xpath + "//div[contains(@class,'bc-step-badge-container')][3]" \
                         "//div[contains(@class,'bc-step-badge-content')]//form/div[2]"
        xpath = xpath1 + " | " + xpath2
        text_elem = self._driver.find_element(By.XPATH, xpath)
        return text_elem.text

    @WebAction()
    def wait_for_submission_complete(self, base_xpath, button1, button2):
        """
                wait for the client creation completion
                Returns:
                    failure or success info
                """
        import time
        next_xpath = base_xpath + "//button[@disabled]/span[contains(text(), '" + button1 + "')]"
        submit_xpath = base_xpath + "//button[@disabled]/span[contains(text(),'" + button2 + "')]"
        time.sleep(10)
        while True:
            if not self.adminconsole.check_if_entity_exists('xpath', next_xpath):
                return self.get_small_text_info(base_xpath)
            if not self.adminconsole.check_if_entity_exists('xpath', submit_xpath):
                return self.get_small_danger_info(base_xpath)
            time.sleep(10)
