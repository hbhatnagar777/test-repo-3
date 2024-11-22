from selenium.webdriver.common.by import By
"""
CVDropDown :

select_value_from_dropdown : Selects a value from the dropdown list in DIPs Page

enter_value_in_dropdown :  Enter the value in editable input for dropdown


"""
from selenium.common.exceptions import NoSuchElementException
from abc import ABC
import time
from Web.Common.page_object import PageService


class CVDropDown(ABC):
    def __init__(self, admin_console):
        """
        Initializes the CVDropDown
        """
        self._driver = admin_console.driver
        self._admin_console = admin_console

    @PageService()
    def select_value_from_dropdown(self, label, value):
        """
        Method to select the value from the dropdown items

        Args:
            label (str) : label of the dropdown (interface1 or interface2)

            value (str) : value to be selected in dropdown
        """
        button_xp = f"//cv-editable-select//button[@name='{label}']"
        self._driver.find_element(By.XPATH, button_xp).click()

        xp = '//cv-editable-select//div[contains(@class,"cv-dropdown-item")]'
        interface_list = self._driver.find_elements(By.XPATH, xp)
        for i in interface_list:
            if i.text == value:
                i.click()
                time.sleep(2)
                return
        raise NoSuchElementException("No such interfaces found")

    @PageService()
    def enter_value_in_dropdown(self, interface,  value):
        """
            Method to enter the value inside the dropdown input

            Args:
                interface (str) : Interface type : interface1 , interface2

                value (str) : value to be selected in dropdown

            """
        xp = f'//cv-editable-select[@name="{interface}"]/div/div/div/input'
        self._driver.find_element(By.XPATH, xp).send_keys(value)


