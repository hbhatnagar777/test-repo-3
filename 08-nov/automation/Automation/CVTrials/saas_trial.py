# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods to onboard a Saas trial customer using UI/API

Classes:

    SaasTrial: Class to perform registration related API operations
    SaasTrialUI: Class to perform registration related UI operations

Functions:

    SaasTrial:

        __init__()                          --  Initialize instance of the API Registration class.

        __get_auth_token()                  --  Method to authenticate the user and generate authtoken.

        onboard_user()                      --  Method to onboard a trial user and create a company.

    SaasTrialUI:

        __init__()                          --  Initialize instance of the UI Registration class.

        method to create browser object()   --  method to create browser object.

        __check_if_entity_exists()          --  Check if a particular element exists or not.

        __fill_form_by_id()                 --  Fill the value in a text field with id element id.

        __click_button_using_text()         --  Method to click on a button using text

        __checkbox_select()                 --  Method to click on a button using text

        __checkbox_select()                 --  Selects checkbox that matches the ID

        __check_if_invalid_email()             --  Method to check for error messages in screen

        register_to_start_trial()           --  Method to register trial user for free trial.
"""
import time
import requests
import json
from Web.Common.cvbrowser import BrowserFactory
from selenium.common.exceptions import (
    NoSuchElementException,
    InvalidSelectorException
)
from Web.Common.exceptions import (
    CVWebAutomationException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from AutomationUtils import logger


class SaasTrial:
    """Class to perform registration related API operations"""
    def __init__(self, lh_env: str, user: str, password: str):
        """Initialize instance of the API Registration class."""
        self._request = requests
        self._auth_token = None
        self.base_url = f'https://{lh_env}/api/v1'
        self.env_user = user
        self.env_password = password
        self.company = None
        self.email = None
        self.name = None
        self.adminconsole_obj = None
        self.log = logger.get_log()

    def __get_auth_token(self):
        """
        Method to authenticate the user and generate authtoken.

        Raises:
            Exception: If there is any error in the API request or response
        """
        self.log.info('Generating authcode...')
        url = f'{self.base_url}/auth/authenticate'
        data = {
            "username": self.env_user,
            "password": self.env_password
        }
        try:
            response = requests.post(url, json=data)

            if response and response.status_code == 200:
                response_data = response.json()
                auth_token = response_data.get('data', {}).get('authToken')
            else:
                raise Exception(response.json().get('error'))

            if not auth_token:
                raise ValueError('Auth token not found in the response')

            self._auth_token = auth_token
            self.log.info("Successfully Generated authcode!")

        except requests.exceptions.HTTPError as http_err:
            raise Exception(f'Unable to complete the request: {http_err}')

    def onboard_user(self, inputs: dict):
        """
        Method to onboard a trial user and create a company.
        Args:
             inputs (dict)  :   input collected from free trial page
             e.g.
                {
                "companyName": <name of the company>,
                "email": <user's email with company domain>,
                "title": <title of the user>,
                "firstName": <first name of the user>,
                "lastName": <last name of the user>,
                "phone": <phone number>,
                "country": <name of the country>,
                "state": <name of the state>,
                "optInForContact": True,
                "utmCampaign": "amer_hybrid-cloud",
                "utmContent": "video",
                "utmMedium": "paidsocial",
                "utmSource": "linkedin",
                "utmTerm": "cv-",
                "trialInterest": [
                    "Metallic Salesforce", "Metallic Database"]
            }

        """
        # Generate authtoken
        self.__get_auth_token()

        if not self._auth_token:
            raise Exception('Unable to generate authtoken. Authentication failed')

        headers = {
            'Authorization': f'Bearer {self._auth_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        url = f'{self.base_url}/signup/trial'
        try:
            self.log.info('starting signup...')
            json_data = json.dumps(inputs)

            response = requests.post(url, headers=headers, data=json_data)

            if response and response.status_code == 201:
                response_data = response.json().get('data')
                if response_data.get('id') and response_data.get('status') == "in_progress":
                    self.company = response_data.get('requestData', {}).get("companyName")
                    self.email = response_data.get('requestData', {}).get("email")
                    self.name = f'{self.company}\{self.email.split("@")[0]}'
                self.log.info("Sign up successful!")
                return self.name
            else:
                raise Exception(response.json().get('error'))

        except requests.exceptions.HTTPError as http_err:
            raise Exception(http_err)


class SaasTrialUI:
    """Class to perform registration related UI operations"""

    def __init__(self, url: str, browser=None):
        """Initialize instance of the UI Registration class."""
        self.log = logger.get_log()
        self.driver = None
        self.browser = browser
        self.url = url
        if not browser:
            self.__create_browser_object()
        self.name = None

    def __create_browser_object(self):
        """method to create browser object."""
        self.log.info('Creating browser object...')
        self.browser = BrowserFactory().create_browser_object()

    def __check_if_entity_exists(self, entity_name: str, entity_value: str):
        """Check if a particular element exists or not.

        Args:
            entity_name      (str)   --  the entity attribute to check for presence
            entity_value     (str)   --  the entity to be checked

        return:
            True    --  If the entity is available
            False   --  If the entity is not available
        """
        try:
            if entity_name == "link":
                return self.driver.find_element(By.LINK_TEXT, entity_value).is_displayed()
            elif entity_name == "id":
                return self.driver.find_element(By.ID, entity_value).is_displayed()
            elif entity_name == "css":
                return self.driver.find_element(By.CSS_SELECTOR, entity_value).is_displayed()
            elif entity_name == "xpath":
                return self.driver.find_element(By.XPATH, entity_value).is_displayed()
            elif entity_name == "name":
                return self.driver.find_element(By.NAME, entity_value).is_displayed()
            elif entity_name == "class":
                return self.driver.find_element(By.CLASS_NAME, entity_value).is_displayed()
        except NoSuchElementException:
            return False

    def __fill_form_by_id(self, element_id: str, value: str):
        """
        Fill the value in a text field with id element id.

        Args:
            element_id (str) -- the ID attribute of the element to be filled
            value (str)      -- the value to be filled in the element

        Raises:
            Exception:
                If there is no element with given name/id

        """
        element = self.driver.find_element(By.ID, element_id)
        element.click()
        element.send_keys(u'\ue009' + 'a' + u'\ue003')  # CTRL + A + Backspace
        element.send_keys(value)
        time.sleep(3)

    def __click_button_using_text(self, value: str):
        """
        Method to click on a button using text

        Args:
            value (str) : text of the button to be clicked
        """
        buttons = self.driver.find_elements(By.XPATH, f"//button[contains(.,'{value}')]")
        for button in buttons:
            if button.is_displayed():
                button.click()
                break
            else:
                raise CVWebAutomationException(f"{value} not found.")

    def __checkbox_select(self, checkbox_id: str):
        """
        Selects checkbox that matches the ID
        Args:
            checkbox_id   (str)  -- id of the checkbox from dev or input tag
        """
        xp = f"//*[@id = '{checkbox_id}']"
        chkbox = self.driver.find_element(By.XPATH, xp)
        if chkbox.tag_name == 'input' and not chkbox.is_selected():
            element = self.driver.find_element(By.XPATH, xp)
            element.click()
            time.sleep(3)

    def __check_if_invalid_email(self):
        """
        Method to check if email entered was valid
        """
        error_string = 'Please use a work email to sign up for the free trial.'
        xp = "//div[@id='metallic-trial-form-alert-422']"
        time.sleep(3)
        onscreen_error = self.driver.find_element(By.XPATH,xp).text
        if error_string == onscreen_error:
            raise Exception(onscreen_error)
        self.log.info('Valid email entered!')

    def register_to_start_trial(self, email: str, company: str):
        """
        Method to register trial user for free trial.

        Args:
            email   (str)   --  email of the trial user
            company (str)   --  Name of the company of the trial user
        """
        self.browser.open()
        self.driver = self.browser.driver
        self.log.info(f'Navigating to url : {self.url}')
        self.driver.get(self.url)

        if not self.__check_if_entity_exists('xpath', "//div[@class = 'form-heading']"
                                                      "/*[contains(text(), 'Register to start trial')]"):
            raise NoSuchElementException('Trial form not visible')

        try:
            self.log.info("filling the trial form...")
            form_fields = {
                'metallic-trial-form-email-one': email,
                'metallic-trial-form-first-name': 'Saas-trial',
                'metallic-trial-form-last-name': 'user',
                'metallic-trial-form-phone-number': '+1 870-516-4882',
                'metallic-trial-form-title': 'QA_test',
                'metallic-trial-form-company-name': company,
                'metallic-trial-form-country': 'Canada'
            }

            for field_id, value in form_fields.items():
                self.__fill_form_by_id(field_id, value)
                if field_id == 'metallic-trial-form-email-one':
                    self.__click_button_using_text('Continue')
                    self.__check_if_invalid_email()

            element = self.driver.find_element(By.ID, 'metallic-trial-form-states')
            if not Select(element).first_selected_option.text:
                raise InvalidSelectorException

            checkboxes = ['metallic-trial-form-tandc', 'metallic-trial-form-optin']
            for checkbox_id in checkboxes:
                self.__checkbox_select(checkbox_id)

            self.__click_button_using_text('Start trial now')

            timeout = 90
            start_time = time.time()

            while time.time() - start_time < timeout:
                # Check if the registration is success
                self.log.info('Checking if registration is successful...')
                if self.__check_if_entity_exists('xpath', "//div[contains(@class,'wp-block-metallic-form__success')]"):
                    self.name = f'{company}\\{email.split("@")[0]}'
                    self.log.info('registration successful!')
                    return self.name

                # Check if the user already exists
                if self.__check_if_entity_exists('id', "metallic-trial-form-user-exists"):
                    raise Exception("Your account already exists. Create a new email.")

                if self.__check_if_entity_exists('id', 'metallic-trial-form-unknown-err-exists'):
                    raise CVWebAutomationException("Error : We’ve sorry we were unable to process your request.")

                # Wait before checking again
                time.sleep(1)  # Wait for 1 second before checking again

            raise TimeoutError("Timed out waiting for conditions to be met.")

        except Exception as exp:
            raise CVWebAutomationException(f'Failed to fill form. Error: {exp}')

        finally:
            self.browser.close()
