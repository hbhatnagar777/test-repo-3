from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
dashboard page on the Metallic Hub

Functions:

    choose_service_from_dashboard()     --      Chooses the required service from the dashboard
    click_new_configuration()           --      Clicks on 'New Configuration'

"""
from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.Components.dialog import RModalDialog
import time

class Dashboard:
    """
    This module provides the function or operations that can be performed on the
    dashboard page on the Metallic Hub
    """

    def __init__(self, admin_console, service, app_type=None):
        """
        Initializes the properties of the class for the selected locale

        Args:
            admin_console   :   instance of the adminconsole class
            service         :   instance of HubServices class
            app_type        :   instance of any of the following classes:-
                                Office365AppTypes/FileObjectTypes/DatabaseTypes/VMKubernetesTypes

        """
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__service = service
        self.__app_type = app_type
        self.__page_open = False
        self.log = self.__admin_console.log

    @WebAction(delay=2)
    def __close_tabs(self):
        """Closes the unwanted tabs open on the dashboard"""
        tabs_length = len(self.__driver.find_elements(By.XPATH, 
            "//div[contains(@class, 'tab-title')]"))
        #need to add this fix as ui correction
        tabs_length = tabs_length - 1
        for i in range(tabs_length):
            if self.__page_open is True:
                tab = self.__driver.find_elements(By.XPATH, "//div[contains(@class, 'tab-title')]")[2]
                tab.find_element(By.XPATH, "./i").click()
            else:
                tab = self.__driver.find_elements(By.XPATH, "//div[contains(@class, 'tab-title')]")[1]
                if tab.find_element(By.XPATH, ".//span").text == self.__service.value:
                    tab.click()
                    self.__page_open = True
                else:
                    tab.find_element(By.XPATH, "./i").click()

    @WebAction(delay=2)
    def __click_tab(self):
        """
        click the tab of the current service
        """
        tabs = self.__driver.find_elements(By.XPATH, "//div[contains(@class, 'tab-title')]")
        for tab in tabs:
            if tab.find_element(By.XPATH, ".//span").text == self.__service.value:
                tab.click()

    @WebAction(delay=2)
    def __click_xpath(self, xpath):
        """
        click the tab of the current service
        """
        elements = self.__driver.find_elements(By.XPATH, xpath)
        for elem in elements:
                elem.click()

    @WebAction(delay=2)
    def __click_service_from_dashboard(self):
        """Clicks on the respective service card on the dashboard"""
        self.__driver.find_element(By.XPATH, 
            f"//div[@class='ng-star-inserted' and normalize-space()='{self.__service.value}']").click()

    @WebAction(delay=2)
    def __choose_configuration(self):
        """Clicks on type of app to be created"""
        selection_dialog = RModalDialog(admin_console=self.__admin_console)
        popup_button = '//button[contains(@id,"pendo-button") and contains(text(),"{}")]'
        if self.__admin_console.check_if_entity_exists("xpath", popup_button.format("Let's go!")):
            self.__driver.find_element(By.XPATH, popup_button.format("Let's go!")).click()
            self.__admin_console.wait_for_completion()
        if self.__admin_console.check_if_entity_exists("xpath", popup_button.format("Got it")):
            self.__driver.find_element(By.XPATH, popup_button.format("Got it")).click()
            self.__admin_console.wait_for_completion()
        if self.__admin_console.check_if_entity_exists("xpath", popup_button.format("Yes, I do")):
            self.__driver.find_element(By.XPATH, popup_button.format("Yes, I do")).click()
            self.__admin_console.wait_for_completion()
        if self.__admin_console.check_if_entity_exists("xpath", popup_button.format("I'm ready to configure")):
            self.__driver.find_element(By.XPATH, popup_button.format("I'm ready to configure")).click()
            self.__admin_console.wait_for_completion()
        if self.__app_type:
            app_type_xpath = f".//p[text()='{self.__app_type.value}']"
            selection_dialog.click_element(app_type_xpath)

    @WebAction()
    def __wait_for_creation_of_storage_and_plan(self):
        """Waits while the storage and plan are created"""
        while True:
            if not self.__admin_console.check_if_entity_exists("xpath", "//button[text()='OK' and @disabled]"):
                break
        failed_exclamation_icon_xpath = "//i[contains(@class, 'fa-exclamation-circle')]"
        if self.__admin_console.check_if_entity_exists(
                "xpath", failed_exclamation_icon_xpath):
            elements = self.__driver.find_elements(By.XPATH, 
                failed_exclamation_icon_xpath + "//ancestor::div//following-sibling::div[@class='step-text failed']")
            if len(elements) > 0:
                for element in elements:
                    self.log.error(f'Error : {element.text}')
                raise Exception('Error occurred while provisioning storage and plan for new tenant')
        self.log.info('Storage and Plan are created successfully')

    @PageService()
    def click_get_started(self):
        """Clicks get started button for a new tenant"""
        try:
            if self.__admin_console.check_if_entity_exists("xpath",
                                                           "//button[contains(.,'No thanks, I’ll explore on my own.')]"):
                self.__admin_console.click_button(value='No thanks, I’ll explore on my own.')
            if self.__admin_console.check_if_entity_exists("class", "bb-button"):
                self.__admin_console.click_button('Got it')
                self.__admin_console.click_button('Ok, got it')
            self.__admin_console.close_popup()
            self.__admin_console.wait_for_completion()
            if self.__admin_console.check_if_entity_exists("name", "termsCheckbox"):
                self.__driver.execute_script("document.querySelector('#mdb-checkbox-1').click();")
            time.sleep(10)
            if self.__admin_console.check_if_entity_exists("xpath", "//button[contains(.,'OK, got it')]"):
                self.__admin_console.click_button('OK, got it')
            self.__admin_console.click_button('Get started')
        except:
            pass

    @PageService()
    def choose_service_from_dashboard(self, select_option='Configure'):
        """Clicks on the respective service card on the service catalog

        Args:
            select_option (str): Configure/ Manage options on the catalog
        """
        id_value = 'serviceCatalogV2'
        if self.__admin_console.check_if_entity_exists(entity_name='id', entity_value=id_value):
            service_catalog = self.__driver.find_element(By.XPATH, "//div[contains(@class, 'page-container') and "
                                                         f"@id='{id_value}']")
            xpath = f".//div[contains(@class, 'MuiCardHeader-content')]//p[contains(text(),'{self.__service.value}')]" \
                    f"//ancestor::div[contains(@class,'MuiCard-root')]//div[contains(@class,'MuiCardContent-root')]" \
                    f"//button[@aria-label='{select_option}']"
            element = service_catalog.find_element(By.XPATH, xpath)
            self.__admin_console.scroll_into_view_using_web_element(element)
            element.click()
            self.__admin_console.wait_for_completion()
        else:
            self.__close_tabs()
            if not self.__page_open:
                self.__click_service_from_dashboard()
                self.__admin_console.wait_for_completion()

    @PageService()
    def click_continue(self):
        """Clicks on continue"""
        self.__admin_console.click_button('Continue')

    @PageService()
    def wait_for_creation_of_storage_and_plan(self):
        """Waits while the storage and plan are created"""
        self.__wait_for_creation_of_storage_and_plan()
        self.__admin_console.click_button('OK')

    @PageService()
    def select_option_to_enable_region_based_storage(self, value='Yes'):
        """Selects provided option whether to enable region based storage
             Args:
                value   :   value to enable region based storage or not
        """
        self.__admin_console.click_button(value)
        self.__admin_console.click_button('OK')

    @PageService()
    def click_new_configuration(self):
        """Clicks on new configuration"""
        self.__choose_configuration()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __click_advanced_view(self):
        """
        clicks on advanced view link
        """
        advanced_view = "//a[contains(text(),'Advanced View')]"
        advanced_view_link = self.__driver.find_element(By.XPATH, advanced_view)
        advanced_view_link.click()

    @WebAction()
    def __click_metallic_icon(self):
        """
        click metallic icon on the page
        """
        metallic_icon_path = "//div[@id='custom-logo-small']"
        self.__driver.find_element(By.XPATH, metallic_icon_path).click()

    @PageService()
    def go_to_admin_console(self):
        """
        move to adminconsole from metallic hub page
        """
        self.__click_tab()
        self.__click_advanced_view()
        self.__admin_console.wait_for_completion()

    @PageService()
    def request_to_trial(self):
        """Select "Request To Trail" from Hub dialog pop up
        """
        from Web.AdminConsole.Components.dialog import RModalDialog
        if self.__admin_console.check_if_entity_exists(entity_name='id', entity_value='manageSubscription'):
            xpath = "//div[@id='manageSubscription']//button[@aria-label='Start trial']"
            if self.__admin_console.check_if_entity_exists(entity_name='xpath', entity_value=xpath):
                self.__driver.find_element(By.XPATH, xpath).click()
                self.__admin_console.wait_for_completion()
                subscription_dialog = RModalDialog(admin_console=self.__admin_console, title='Subscription created')
                subscription_dialog.click_close()
                self.__admin_console.wait_for_completion()
            xpath = "//div[@id='manageSubscription']//button[@aria-label='Continue']"
            if self.__admin_console.check_if_entity_exists(entity_name='xpath', entity_value=xpath):
                self.__driver.find_element(By.XPATH, xpath).click()
                self.__admin_console.wait_for_completion()
            return
        from Web.AdminConsole.Components.dialog import RModalDialog
        dialog_xpath = '//div[contains(@class, "modal") and @aria-hidden="false"]' \
                       '//div[contains(@class, "modal-dialog modal-dialog-scrollable")]'
        trial_dialog = RModalDialog(self.__admin_console, xpath=dialog_xpath)
        if trial_dialog.check_if_button_exists('Request to Trial'):
            trial_dialog.click_button_on_dialog('Request to Trial')
            self.__admin_console.wait_for_completion()
        if trial_dialog.check_if_button_exists('Continue Configuraton'):
            trial_dialog.click_button_on_dialog('Continue Configuraton')
            self.__admin_console.wait_for_completion()
        if trial_dialog.check_if_button_exists('Continue'):
            trial_dialog.click_button_on_dialog('Continue')
        self.__admin_console.wait_for_completion()

    @PageService(react_frame=False)
    def go_to_dashboard(self):
        """
        move back to dashboard
        """
        self.__click_metallic_icon()
        self.__admin_console.wait_for_completion()


    @WebAction()
    def __get_tile_data(self):
        """Get data from tile
        """
        col_data = {}
        data_col_xpath = '//div[contains(@class, "card d-tile d-datasource-tile")]//div[contains(@class, "data-col")]'
        for col in self.__driver.find_elements(By.XPATH, data_col_xpath):
            label = col.find_element(By.XPATH, './/div[contains(@class, "data-label")]').text
            count = col.find_element(By.XPATH, './/div[contains(@class, "data-number")]').text
            col_data[label] = count

        return col_data

    @PageService()
    def get_protected_data_sources(self):
        """
        Get count of entities displayed in protected data sources tile
        """
        return self.__get_tile_data()
