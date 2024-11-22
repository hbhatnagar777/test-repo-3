from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Module for Wizard component the is to be used while create entites in react

Wizard:
    upload_file()                   :   Uploads file into a upload field

    select_radio_card()             :   Selects radio cards

    fill_text_in_field()            :   Method used for filling data into an input field

    click_button()                  :   Method to click on a button

    is_toggle_enabled()             :   Method to get status of toggle element

    enable_toggle()                 :   Method used to Enable a toggle

    disable_toggle()                :   Method used to disable toggle element

    select_side_tab()               :   Click on side tab

    select_drop_down_values()       :   Method to select values in dropdown

    click_icon_button()             :   Method to click icons

    select_radio_button()           :   Method to select radio button
    
    select_card()                   :   Method to select card

    fill_input_by_id()              :   Method to fill input using id

    click_next()                    : Method to click next button

    click_cancel()                  : Method to click cancel button

    select_plan()                   : Select the plan in select plan screen
    
    get_all_plans()                 : Returns list of all the plans in the select plan screen

    get_input_data()                : Method to get data/text filled in wizard elements

    get_active_step()               : Method to get current step in the wizard flow

    click_add_icon()                : Method to click on add(+) icon
    
    clear_text_in_field()           : Method to clear data in the input field

    click_refresh_icon()            : Method to click on refresh icon
    
    click_element()                 : Click element by xpath
        
    get_job_id()                    : Get the job ID from the restore wizard

TC: 62698 -- Integration test for wizard
Please after adding public methods add test for it in the integration testcase

"""
import re
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import WebAction
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.core import Toggle, Checkbox
from selenium.common.exceptions import NoSuchElementException


class Wizard:
    """Wizard component used in Command Center for automating create screens"""

    def __init__(self, adminconsole: AdminConsole, title: str=None):
        """
        Intializes the Wizard component object

        Args:
            adminconsole (AdminConsoleBase): Adminconsole class object
            title (str): Title for the wizard component
        """
        if title:
            base_xpath = f"//h1[text()='{title}']/ancestor::div[contains(@class,'page-container')]//div[contains(@class, 'wizard ')]"

        base_xpath = "//div[contains(@class,'page-container')]//div[contains(@class, 'wizard ')]"

        self.__base_path = base_xpath
        self.__adminconsole = adminconsole
        self.__driver = self.__adminconsole.driver
        self.drop_down = RDropDown(self.__adminconsole)
        self.table = Rtable(self.__adminconsole)
        self.__toggle = Toggle(self.__adminconsole, self.__base_path)
        self.__checkbox = Checkbox(self.__adminconsole, self.__base_path)

    @property
    def toggle(self) -> Toggle:
        """Returns instance of toggle class"""
        return self.__toggle

    @property
    def checkbox(self) -> Checkbox:
        """Returns instance of checkbox class"""
        return self.__checkbox

    def __get_element(self, xpath:str) -> WebElement:
        """Method to get web element from xpath

        Args:
            xpath (str): xpath to get the element

        Returns:
            WebElement object having given xpath
        """
        element = self.__driver.find_element(By.XPATH, self.__base_path + xpath)
        return element

    def __get_elements(self, xpath:str) -> list[WebElement]:
        """Method to get web element from xpath

        Args:
            xpath (str): xpath to get the element

        Returns:
            List of WebElement object matching given xpath
        """
        elements = self.__driver.find_elements(By.XPATH, self.__base_path + xpath)
        if not elements:
            raise NoSuchElementException(f"Element with xpath: {xpath} could not be found on page {self.__driver.title}")

        return elements

    def __click_element(self, xpath:str) -> None:
        """Clicks on element

        Args:
            xpath (str): xpath to get the element
        """
        element = self.__get_element(xpath)
        self.__adminconsole.scroll_into_view(xpath)
        element.click()

    def __fill_input_field(self, xpath:str, text:str, **kwargs) -> None:
        """Fills data into an input element

        Args:
            xpath (str): xpath to get the element

            text (str): Text to enter in the field
        """
        self.__clear_input_field(xpath, **kwargs)

        element = self.__get_element(xpath)
        element.send_keys(text)

    def __clear_input_field(self, xpath:str, **kwargs) -> None:
        """Clears input field

        Args:
            xpath (str): xpath to get the element
        """
        element = self.__get_element(xpath)

        # clear the input element
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.DELETE) if kwargs.get("delete_during_clear", True) else None
        element.send_keys(Keys.BACKSPACE) if kwargs.get("backspace_during_clear", True) else None

    @WebAction()
    def __click_button_using_text(self, text:str) -> None:
        """Click button using text

        Args:
            text (str): text for the button to click
        """
        xpath = f"//button[contains(@class, 'MuiButtonBase-root')]//div[text()='{text}']"
        if not self.__adminconsole.is_element_present(xpath):
            xpath = f"//button[contains(@class, 'MuiButtonBase-root')]/span[text()='{text}']"
        self.__click_element(xpath)

    @WebAction()
    def click_element(self, xpath: str) -> None:
        """Click element using xpath

        Args:
            xpath (str): text for the button to click
        """
        self.__click_element(xpath)

    @WebAction()
    def __click_button_using_id(self, id:str) -> None:
        """
        Click button using id
            
        Args:
            id (str): id of the button to click
        """
        xpath = f"//button[contains(@class, 'MuiButtonBase-root') and contains(@id, '{id}')]"
        self.__click_element(xpath)

    def _is_accordion_expanded(self, label):
        """Check if the accordion is expanded
        Args:
            label (str): title of the accordion
        """
        accordion_xpath = f"//div[@class='accordion-wrapper']//div[text()='{label}']/parent::div/following-sibling::div"
        element = self.__get_element(accordion_xpath)
        attribute = element.get_attribute(name="class")
        if attribute == "accordion-item collapsed":
            is_expanded = False
        else:
            is_expanded = True
        return is_expanded

    @WebAction()
    def _expand_accordion(self, label):
        """Expand the accordion in the wizard

        Args:
            label (str) :- accordion label
        """
        accordion_xpath = f"//div[@class='accordion-wrapper']//div[text()='{label}']"
        self.__click_element(accordion_xpath)

    @WebAction()
    def upload_file(self, label:str, file_location:str) -> None:
        """Uploads file into a upload field

        Args:
            label (str): Upload field label

            file_location (str): Filename to upload
                Example: \\C:\\file_to_upload.json
        """
        xpath = f"//span[text()='{label}']/ancestor::div[contains(@class, 'field-wrapper')]/div[@class='input-wrapper']//input[@type='file']"

        element = self.__get_element(xpath)
        element.send_keys(file_location)

    def __toggle_toggle(self, label: str, index: int = None) -> None:
        """toggle the toggle element corresponding to label

        Args:
            label (str): Toggle label to enable/disable
        """
        xpath = f"//div[contains(@class, 'teer-toggle')]//span[text()='{label}']/../span[contains(@class, 'MuiSwitch-root')]//input[@type='checkbox']"
        if index:
            element = self.__get_elements(xpath)[index - 1]
            element.click()
        else:
            self.__click_element(xpath)

    @WebAction()
    def select_radio_card(self, text:str) -> None:
        """Selects radio cards

        Args:
            text (str): Radio card text to select
        """
        xpath = f"//div[contains(@class, 'Radio-card')]//span[text()='{text}']"
        self.__click_element(xpath)

    @WebAction()
    def select_card(self, text: str):
        """Method to click the radio tile
           Args:
            text (str): Button label to click
        """
        xpath = f"//div[contains(@class,'MuiCard-root') or contains(@class, 'grid-item')]//*[text()='{text}']"
        self.__driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def fill_text_in_field(self, label:str=None, id:str=None, text:str=None, delete_during_clear=True) -> None:
        """Method used for filling data into an input field

        Args:
            label (str): Text field label to fill input
                default: None

            id (str): ID for the text field
                default: None

            text(str): Text input to fill in the selected field

        Raise:
            Exception: If neither Label nor ID are passed
        """
        if label:
            xpath = f"//div//*[text()='{label}']/ancestor::div[contains(@class, 'MuiTextField-root')]//input"
        elif id:
            xpath = f"//input[@id='{id}']"
        else:
            raise Exception("Please provide either Label or ID")
        self.__fill_input_field(xpath, text, delete_during_clear=delete_during_clear)

    @WebAction()
    def clear_text_in_field(self, label: str = None, id: str = None, backspace_during_clear=True) -> None:
        """Method used for clearing data in an input field

        Args:
            label (str): Text field label to fill input
                default: None

            id (str): ID for the text field
                default: None

        Raise:
            Exception: If neither Label nor ID are passed
        """
        if label:
            xpath = f"//div//*[text()='{label}']/ancestor::div[contains(@class, 'MuiTextField-root')]//input"
        elif id:
            xpath = f"//input[@id='{id}']"
        else:
            raise Exception("Please provide either Label or ID")
        self.__clear_input_field(xpath, backspace_during_clear=backspace_during_clear)

    @WebAction()
    def click_button(self, name:str = None, id:str = None) -> None:
        """Method to click on a button

        Args:
            name (str): Button name to click

            id (str): ID of the button to click
        """
        if name:
            self.__click_button_using_text(name)
        elif id:
            self.__click_button_using_id(id)
        else:
            raise Exception("Please provide either Label or ID")
        # Don't add wait for completion here, add it in respective page methods

    @WebAction()
    def is_toggle_enabled(self, label: str, index: int = None) -> bool:
        """Method to get status of toggle

        Args:
            label (str): toggle label to check
            index (int): index corresponding to the toggle option (Ex.- 1, 2...so on) if there are multiple toggles
                        with similar label

        Return:
            False (bool): if toggle is disabled
            True  (bool): if toggle is enabled
        """
        xpath = f"//div[contains(@class, 'teer-toggle')]//span[text()='{label}']/..//span[contains(@class, 'MuiSwitch-switchBase')]"
        if index:
            element = self.__get_elements(xpath)[index - 1]
        else:
            element = self.__get_element(xpath)

        return True if 'Mui-checked' in element.get_attribute('class') else False

    @WebAction()
    def enable_toggle(self, label: str, index: int = None) -> None:
        """Method used to Enable a toggle

        Args:
            label (str): toggle label to enable
            index (int): index corresponding to the toggle option (Ex.- 1, 2...so on) if there are multiple toggles
                        with similar label
        """
        if self.is_toggle_enabled(label, index):
            return

        self.__toggle_toggle(label, index)

    @WebAction()
    def disable_toggle(self, label: str, index: int = None) -> None:
        """Method used to disable toggle element

        Args:
            label (str): toggle label to disable
            index (int): index corresponding to the toggle option (Ex.- 1, 2...so on) if there are multiple toggles
                        with similar label
        """
        if not self.is_toggle_enabled(label, index):
            return

        self.__toggle_toggle(label, index)

    @WebAction()
    def enable_disable_toggle(self, label: str, enable: bool, index: int = None) -> None:
        """Method used to enable/disable toggle element

        Args:
            label (str): toggle label to enable/disable
            enable (bool): True to enable, False to disable
            index (int): index corresponding to the toggle option (Ex.- 1, 2...so on) if there are multiple toggles
                        with similar label
        """
        self.enable_toggle(label) if enable else self.disable_toggle(label)

    @WebAction()
    def select_checkbox(self, checkbox_id: str = None, checkbox_label: str = None):
        """
               Selects checkbox that matches the ID
               Args:
                   checkbox_id   (str)  -- id of the checkbox from dev or input tag
                   checkbox_label (str)  -- label of the checkbox
        """
        self.checkbox.check(label=checkbox_label, id=checkbox_id)

    @WebAction()
    def deselect_checkbox(self, checkbox_id: str = None, checkbox_label: str = None):
        """
               Selects checkbox that matches the ID
               Args:
                   checkbox_id   (str)  -- id of the checkbox from dev or input tag
                   checkbox_label (str)  -- label of the checkbox
        """
        self.checkbox.uncheck(label=checkbox_label, id=checkbox_id)

    @WebAction()
    def select_deselect_checkbox(self, checkbox_id: str = None, checkbox_label: str = None, select: bool = True):
        """
        Selects or deselects the checkbox based on the select flag
        Args:
            checkbox_id   (str)  -- id of the checkbox from dev or input tag
            checkbox_label (str)  -- label of the checkbox
            select (bool)  -- flag to determine whether to select or deselect the checkbox
        """
        self.select_checkbox(checkbox_id, checkbox_label) if select else self.deselect_checkbox(checkbox_id, checkbox_label)


    @WebAction()
    def select_side_tab(self, side_heading:str) -> None:
        """Click on side tab headings

        Args:
            side_heading (str): Side heading to select
                Note: In create SAML app wizard flow, Associations step
        """
        xpath = f"//li[@class='master-list-item']//*[text()='{side_heading}']"

        self.__click_element(xpath)

    def select_drop_down_values(self, id: str, values: list, wait_for_content_load: bool = True,
                                    partial_selection: bool = False, case_insensitive_selection: bool = False) -> None:
            """Method to select values in dropdown

            Args:
                id (str): Dropdown ID to select

                values (list): list of values to select from dropdown

                wait_for_content_load (bool): Flag to determine if method needs to wait for dropdown values to load or not

                partial_selection (bool): Flag to determine if partial selection is allowed or not

                case_insensitive_selection (bool): Flag to determine if case-insensitive selection is allowed or not

            Returns:
                None
            """
            if wait_for_content_load:
                self.drop_down.wait_for_dropdown_load(id)
            self.drop_down.select_drop_down_values(values=values,
                                                   drop_down_id=id,
                                                   partial_selection=partial_selection,
                                                   case_insensitive_selection=case_insensitive_selection)

    @WebAction()
    def click_icon_button(self, label:str, title:str, index:int=0) -> None:
        """Method to click icons

        Args:
            label (str): label for icon button

            title (str): title for icon button

            index (int): index to click for icon button
                default: 0
        """
        xpath = f"//span[normalize-space()='{label}']/ancestor::div[@class='input-wrapper']//button[contains(@class, 'MuiIconButton') and @title='{title}']"
        icons = self.__get_elements(xpath)

        icons[index].click()

    @WebAction()
    def click_icon_button_by_title(self, title:str) -> None:
        """
        Method to click icons

        Args:
            title (str): title for icon button
        """
        xpath = f"//button[contains(@class, 'MuiIconButton-root') and @title='{title}']"
        icon = self.__get_element(xpath)
        icon.click()

    @WebAction()
    def click_icon_button_by_label(self, label:str) -> None:
        """
        Method to click icons

        Args:
            label (str): title for icon button
        """
        xpath = f'//div[@aria-label="{label}"]//button[contains(@class, "MuiIconButton-root")]'
        icon = self.__get_element(xpath)
        icon.click()

    @WebAction()
    def select_dropdown_list_item(self, label:str) -> None:
        """
        Method to click on list items

        Args:
            label (str): title for icon button
        """
        xpath = f"//ul[contains(@role, 'menu')]//li[contains(text(), '{label}') and contains(@role, 'menuitem')]"
        self.__click_element(xpath)

    @WebAction()
    def select_radio_button(self, label:str=None, id:str=None) -> None:
        """Method to select radio button

        Args:
            label (str): Radio button label to select
                default: None

            id (str): Radio button ID to select
                default: None

        Raise:
            Exception: If neither Label nor ID are passed
        """
        if id:
            xpath = f"//input[contains(@class, 'PrivateSwitchBase-input') and @id='{id}']"
        elif label:
            xpath = f"//span[text()='{label}']/ancestor::label[contains(@class, 'MuiFormControlLabel-root')]//input[contains(@class, 'PrivateSwitchBase-input')]"
        else:
            raise Exception("Please provide label or id to select a checkbox")

        self.__click_element(xpath)

    @WebAction()
    def click_next(self) -> None:
        """Method to click next button"""
        self.click_button("Next")
    
    @WebAction()
    def click_previous(self) -> None:
        """Method to click the button 'Previous'"""
        self.click_button("Previous")

    @WebAction()
    def click_cancel(self) -> None:
        """Method to click cancel button"""
        self.click_button("Cancel")

    @WebAction()
    def click_run(self) -> None:
        """Method to click Finish button"""
        self.click_button("Run")

    @WebAction()
    def click_finish(self) -> None:
        """Method to click Finish button"""
        self.click_button("Finish")

    @WebAction()
    def click_submit(self) -> None:
        """Method to click Submit button"""
        self.click_button("Submit")

    @WebAction()
    def select_plan(self, plan_name:str) -> None:
        """Select the plan in select plan screen"""
        xpath = f"//span[text()='{plan_name}']"
        if self.__are_multiple_plans_present():
            self.__click_element(xpath)

    def get_all_plans(self):
        """ Returns list of all the plans in the select plan screen"""
        xpath = "//*[contains(@id, 'planCard')]/span"
        elements = self.__driver.find_elements(By.XPATH, xpath)
        plans = []
        for element in elements:
            plans.append(element.text)
        return plans

    @WebAction()
    def get_input_data(self, id:str=None, label:str=None) -> str:
        """Method to get data/text filled in wizard elements

        Args:
            label (str): Input field label to get data from
                default: None

            id (str): Input field ID to get data from
                default: None

        Raise:
            Exception: If neither Label nor ID are passed
        """
        if id:
            xpath = f"//input[@id='{id}']"
        elif label:
            xpath = f"//label[text()='{label}']/ancestor::div[contains(@class, 'MuiTextField-root')]//input"
        else:
            raise Exception("Please enter a valid id or label to get data")

        element = self.__get_element(xpath)
        return element.get_attribute("value")

    @WebAction()
    def get_active_step(self) -> str:
        """Method to get current step in the wizard flow"""
        xpath = "//div[contains(@class,'active') and contains(@class,'wizard-step')]" \
                "//div[@class='wizard-step-tracker-title']"

        element = self.__get_element(xpath)
        return element.text

    @WebAction()
    def click_add_icon(self, index: int = 0) -> None:
        """Method to click on add icon
            Args:
                index (int): index to click for icon button
                    default: 0
        """
        xpath = "//button[@aria-label= 'Create new' or @aria-label='Add']"
        if not self.__adminconsole.is_element_present(xpath):
            xpath = "//div[@aria-label= 'Create new' or @aria-label='Add']/button"
        add_icons = self.__get_elements(xpath)
        add_icons[index].click()

    @WebAction()
    def click_refresh_icon(self, index: int = 0) -> None:
        """Method to click on refresh icon
            Args:
                index (int): index to click for icon button
                    default: 0
        """
        xpath = "//button[contains(@aria-label, 'Reload') or contains(@aria-label,'Refresh')" \
                "or contains(@aria-label, 'Refresh list')]"
        if not self.__adminconsole.is_element_present(xpath):
            xpath = "//div[contains(@aria-label, 'Reload') or contains(@aria-label,'Refresh')" \
                    "or contains(@aria-label, 'Refresh list')]"
        add_icons = self.__get_elements(xpath)
        add_icons[index].click()

    @WebAction()
    def get_tile_content(self) -> str:
        """Method to get the content from the tile
        Returns:
            tile_content (str)
        """
        tile_xpath = "//div[contains(@class,'wizard-content')]"
        element = self.__get_element(tile_xpath)
        return element.text

    @WebAction()
    def expand_accordion(self, label):
        """Expand the accordion in the wizard"""
        if not self._is_accordion_expanded(label):
            self._expand_accordion(label)

    @WebAction()
    def get_alerts(self):
        """Get the alerts shown on the wizard"""
        alert_xpath = "//*/div[contains(@class,'MuiGrid-container')]//div[@role='alert']"
        element = self.__get_element(alert_xpath)
        return element.text

    @WebAction()
    def get_wizard_title(self):
        """Get the title of the wizard"""
        title_xpath = "//div[@class='wizard-title ']"
        element = self.__get_element(title_xpath)
        return element.text

    @WebAction()
    def __are_multiple_plans_present(self) -> bool:
        """ Returns true if there are more than 1 plan in the dropdown

        Returns:
              bool : True / False
        """
        all_plans = self.__get_elements(xpath="//div[contains(@id,'planCard')]")
        return len(all_plans) >= 1

    @WebAction()
    def get_job_id(self):
        """
            Get the job ID from the restore wizard

            Returns:
                job_id (str) : Job ID
        """
        notification_xpath = "//div[contains(@class,'MuiAlert-message')]//span"
        element = self.__get_element(notification_xpath)
        job_id = re.findall(r'\d+', element.text)[0]
        return job_id
