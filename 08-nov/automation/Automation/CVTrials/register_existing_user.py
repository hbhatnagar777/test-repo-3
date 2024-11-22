from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing commvault registration

Registration is the only class defined in this file.

Registration: Class for performing commvault registration

Registration:
=============

    __init__()                              -- To initialize the Registraion class

    _wait_for_registration_completion()     -- To wait for registration to complete

    check_if_entity_exists()                -- To check if entity exists in the webpage

    execute()                               -- Main method to perform registration

    fill_form_by_id()                       -- To fill a web element using Name or ID

    register_existing_Account()             -- To register using an existing account

    select_hyperlink()                      -- To select a hyperlink on the web page

    submit_form()                           -- To click on the submit button

    wait_for_completion()                   -- Wait for the page to load

    wait_for_loader()                       -- Waits for the loader on the page to load completely so that
                                                all items on page are visible

**Note** Command line arguments to be passed in the below mentioned order

Command Line Arguments:
-----------------------

    1. chrome driver path

    2. URL to be opened

    3. Username for registration

    4. Password for registration

    5. Activation code for registration

"""
import sys
import time

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


class Registration:
    """Class to perform registration related operations"""
    def __init__(self):
        """Initialize instance of the Registration class."""
        self.interval = 1
        self.total_time = 600
        self.driver = None

    def check_if_entity_exists(self, entity_name, entity_value):
        """Check if a particular element exists or not

        Args:
            entity_name      (str)   --  the entity attribute to check for presence

            entity_value     (str)   --  the entity to be checked

        Returns:
            True    --  If the entity is available

            False   --  If the entity is not available

        """
        try:
            if entity_name == "link":
                self.driver.find_element(By.LINK_TEXT, entity_value)
                return True
            elif entity_name == "id":
                self.driver.find_element(By.ID, entity_value)
                return True
            elif entity_name == "xpath":
                self.driver.find_element(By.XPATH, entity_value)
                return True
            elif entity_name == "name":
                self.driver.find_element(By.NAME, entity_value)
                return True
        except NoSuchElementException:
            return False

    def fill_form_by_id(self, element_id, value):
        """
        Fill the value in the web page element

        Args:
            element_id  (str)   -- ID or name to identify the element uniquely

            value       (str)   -- value to be filled in the element

        Raises:
            Exception:
                If there is no element with given name/id

        """
        if self.check_if_entity_exists("id", element_id):
            element = self.driver.find_element(By.ID, element_id)
        elif self.check_if_entity_exists("name", element_id):
            element = self.driver.find_element(By.NAME, element_id)
        else:
            raise Exception("There is no element with the given name or ID")
        element.clear()
        element.send_keys(value)
        self.wait_for_completion()

    def select_hyperlink(self, link_text):
        """
        To select hyperlink in the given page

        Args:
            link_text (str)  -- Link text as displayed in the web page.

        """
        if self.check_if_entity_exists("link", link_text):
            self.driver.find_element(By.LINK_TEXT, link_text).click()
        else:
            xpath_direct = "//a[contains(.,'" + link_text + "')]"
            xpath_text_level_down = "//a/span[contains(.,'" + link_text + "')]"
            if self.check_if_entity_exists("xpath", xpath_direct):
                self.driver.find_element(By.XPATH, xpath_direct).click()
            elif self.check_if_entity_exists("xpath", xpath_text_level_down):
                self.driver.find_element(By.XPATH, xpath_text_level_down).click()
            else:
                raise Exception(
                    "Could not locate Hyperlink:[{}] ".format(
                        link_text))
        self.wait_for_completion()

    def submit_form(self):
        """
        To click on the submit button

        Raises:
            Exception:
                If the button is not found

        """
        if self.check_if_entity_exists("xpath", "//button[@type='submit']"):
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
            self.wait_for_completion()
        else:
            raise Exception("Form not active or Save button not found")

    def wait_for_loader(self):
        """
        Waits for the loader on the page to load completely so that all items on page are visible
        """
        WebDriverWait(self.driver, 60).until(
            EC.invisibility_of_element_located((By.XPATH, "//span[@class = 'grid-spinner']")))

    def wait_for_completion(self):
        """Checks for the notification bar at the top of the browser."""
        exists = True
        completion_time = 0
        while exists:
            time.sleep(self.interval)
            completion_time += self.interval
            if completion_time > self.total_time:
                break
            exists = self.check_if_entity_exists(
                "xpath", "//div[@id='loading-bar']")
        self.wait_for_loader()

    def register_existing_account(
            self,
            email=None,
            password=None,
            activation_code=None):
        """
        To register using the existing account

        Args:
            email           (str)   -- Email address to register account

            password        (str)   -- Password for the account

            activation_code (str)   -- Activation code received in the mail

        """
        # To click on use existing account if it exists
        if self.check_if_entity_exists('xpath', '//a[contains(text(), "Use existing account")]'):
            self.select_hyperlink('Use existing account')

        self.fill_form_by_id('cloudEmail', email)
        self.fill_form_by_id('cloudPassword', password)
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

        if self.check_if_entity_exists('xpath', "//div[@class='ok']"):
            # To wait for the page redirect to complete
            self.wait_for_completion()
        else:
            raise Exception("Failed in user registration")

    def execute(self):
        """main method to register commvault"""
        try:
            # To open chrome browser
            self.driver = webdriver.Chrome(sys.argv[1])

            # To maximize the browser
            self.driver.maximize_window()
            self.driver.get(sys.argv[2])
            self.wait_for_completion()

            # To register using existing user
            self.register_existing_account(
                email=sys.argv[3],
                password=sys.argv[4],
                activation_code=sys.argv[5]
            )
            print('Registration successful')
        except Exception as exp:
            print('Registration failed: ', exp)

        finally:
            self.driver.quit()


if __name__ == "__main__":
    # If no arguments are passed print help message
    if len(sys.argv) <= 1:
        sys.argv.append('-h')

    registration = Registration()
    registration.execute()
