""" Module for panel like component that opens in the right side of the screen

ModalPanel:

    cancel()                        :       Cancel panel

    submit()                        :       Submit panel irrespective of the text in submit button

    title()                         :       Returns the title of panel

    access_tab()                    :       Access tab inside panel

    search_and_select()             :       Method to transfer select a value from the search and select input

    is_accordion_expanded()         :       Checks if accordion is expanded

RModalPanel:

    search_and_select()             :       Method to select a value from the search and select input       

    submit()                        :       Submit panel irrespective of the text in submit button
    
    select_path_from_treeview()     :      Expand the tree view and selects the given path
    
    collapse_treeview_node()        :      Method to collapse node in treeview of the modal panel

    title()                         :       returns the title of panel

    access_tab()                    :       Access tab inside panel

Backup:

    submit_backup()                 :       Submits backup job in the panel

MultiJobPanel:

    config_operation()              :       Sets action type and selection type by clicking their radio buttons

    submit()                        :       Submits the panel

PanelInfo:

    enable_toggle()                 :       Enables the toggle bar if disabled

    disable_toggle()                :       Disables the toggle bar if enabled

    get_toggle_element()            :       Gets WebElement corresponding to the label

    is_toggle_enabled()             :       Checks if toggle is enabled

    edit_tile()                     :       click on edit icon for tile contents

    add_tile_entity()               :       click on Add for specific entity inside tile

    edit_tile_entity()              :       click on edit for specific entity inside tile

    get_calendar_details()          :       Gets all the calendar details in overview page of client

    get_details()                   :       Gets all the information contained in the panel

    check_if_hyperlink_exists_on_tile():    Checks if hyperlink on tile exists

    open_hyperlink_on_tile()        :       Opens hyperlink on tile

    get_all_hyperlinks()            :       Gets list of hyperlinks on tile

    click_button_on_tile()          :       Clicks button on tile

    save_dropdown_selection         :       Clicks on the tick mark near dropdown to save the selection

    get_list()                      :       Gets the list type values in panel

    more_tile()                     :       click on More dropdown link in General Tile (instance Details Page)


RPanelInfo:

    enable_toggle()                 :       Enables the toggle bar if disabled

    disable_toggle()                :       Disables the toggle bar if enabled

    get_toggle_element()            :       Gets WebElement corresponding to the label

    is_toggle_enabled()             :       Checks if toggle is enabled

    edit_tile()                     :       click on edit icon for tile contents

    view_tile()                     :       click on view icon for tile contents

    add_tile_entity()               :       to be implemented

    edit_tile_entity()              :       Method to edit inline tile entity

    get_calendar_details()          :       Gets all the calendar details in overview page of client

    get_details()                   :       Gets all the information contained in the panel

    get_overflow_items              :       Gets the overflow items list

    get_tree_list()                 :       Gets the tree structure from list

    check_if_hyperlink_exists_on_tile():    Checks if hyperlink on tile exists

    click_action_item()             :       Clicks on provided action item from Panel actions list

    open_hyperlink_on_tile()        :       Opens hyperlink on tile

    edit_title()                    :       Edits entity name from details page
    
    is_tile_disabled()              :       Method to check if tile / panel is disabled
    
    is_edit_visible()               :       Method to check if edit option is visible on panel
    
    available_panels()              :       Method to return all panel names available on page

    edit_and_save_tile_entity       :       Method to edit an inline entity and save it

    check_if_button_exists()        :       Checks if a button with given label exists or not

    click_button()                  :       Method to click button using label

    click_button_by_title()         :       Clicks on a button in RPanelInfo by title

    click_button_from_menu()        :       Method to click button from a dropdown

    select_browse_time              :       Picks the browse time from recovery panel

    date_picker                     :       Picks the date and browse time from recovery panel


Security:

    edit_security_association       :       Add/remove security associations

    get_details                     :       Gets all the information contained in the Security panel

RSecurityPanel:

    get_details                     :       Gets all the information contained in the Security panel

Dropdown:

    select_drop_down_values         :       Select values in isteven-multi-select dropdown

    deselect_drop_down_values       :       Deselect values in isteven-multi-select dropdown

    get_values_of_drop_down_by_index    :   Returns the values in a drop down by accessing drop down using index.

RDropDown:

    collapse_drop_down              :       Collapses the dropdown

    get_values_of_drop_down         :       Returns the values in a drop down next to the
    provided label value

    get_selected_values             :       Returns the list of selected values of the drop down

    select_drop_down_values         :       select values from drop down

    deselect_drop_down_values       :       deselect values from drop down

    wait_for_dropdown_load          :       Method to wait for dropdown list to load

RecoveryCalendar:

    select_date() :    Picks the date from recovery calendar


Integration tests for components are added in below mentioned test cases, for any new functionality added here
add the corresponding integration method

        TC 59742        --      Test case for RPanelInfo class(React Panel)
        TC 59727        --      Test case for RDropDown class(React Panel)

"""

import time
from abc import ABC
from enum import Enum
import re
from selenium.webdriver import ActionChains
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import (
    NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException, WebDriverException
)

from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.core import Toggle, Checkbox


class ModalPanel(ABC):
    """ Modal class """

    def __init__(self, admin_console):
        """ Initialize the base panel

        Args:
            admin_console: instance of AdminConsoleBase

        """
        self._driver = admin_console.driver
        self._admin_console = admin_console
        self.__xp = "*//div[@class='button-container']"
        self._dropdown = DropDown(admin_console)
        self._rdropdown = RDropDown(admin_console)

    @WebAction(delay=2)
    def __click_submit(self):
        """ Clicks submit button of the panel doesnt matter about the text in it"""
        submit_buttons = self._driver.find_elements(By.XPATH,
                                                    "//button[contains(@class,'btn btn-primary cvBusyOnAjax')]")

        if not submit_buttons:
            raise NoSuchElementException("Cannot find Submit button")

        for button in submit_buttons:
            if button.is_displayed():
                self._driver.execute_script("return arguments[0].scrollIntoView();", button)
                button.click()
                break

    @WebAction()
    def __click_cancel(self):
        """ Clicks Cancel button of the panel"""
        self._driver.find_element(By.XPATH,
                                  "//button[contains(@class,'btn btn-default') and contains(text(),'Cancel')]"
                                  ).click()

    @WebAction()
    def __click_close(self):
        """ Clicks Close button of the panel"""
        self._driver.find_element(By.XPATH,
                                  "//button[contains(@class,'btn btn-default') and normalize-space(text())='Close']"
                                  ).click()

    @WebAction(delay=1)
    def _expand_accordion(self, name):
        """Clicks the heading of an accordion"""

        if self._admin_console.check_if_entity_exists('xpath',
                                                      f'//span[contains(text(), "{name}")]/ancestor::a'):
            element = self._driver.find_element(By.XPATH,
                                                f'//span[contains(text(), "{name}")]/ancestor::a'
                                                )
            element.click()

        elif self._admin_console.check_if_entity_exists('xpath', f'//span[contains(text(), "{name}")]'):
            element = self._driver.find_element(By.XPATH, f'//span[contains(text(), "{name}")]')
            element.click()

    @WebAction()
    def _is_visible(self, element_id):
        """Checks if the element is visible"""
        try:
            element = self._driver.find_element(By.ID, element_id)
            assert element.is_displayed() is True
            return True
        except (AssertionError, NoSuchElementException):
            return False

    @WebAction()
    def __click_tab(self, tab_text):
        """
        clicks on tab inside panel
        Args:
            tab_text: localized tab text
        """
        self._driver.find_element(By.XPATH,
                                  f'//a[@data-ng-click="selectTab(pane)" and contains(text(),"{tab_text}")]'
                                  ).click()

    def _expand_accordion_if_not_visible(self, element_id, accordion_name):
        """checks for visibility"""
        if self._is_visible(element_id):
            return
        self._expand_accordion(accordion_name)

    @WebAction()
    def __read_title(self):
        """Reads Modal panel title"""
        return self._driver.find_element(By.XPATH, "//div[@class='modal-content']//h1").text

    @WebAction()
    def __check_radio_button_and_type(self, option, type_text=False, text=""):
        """
        checks the radio button and types text if needed
        Args:
            option ([string]): radio button label to be checked
            type_text ([bool]): to type text or not
            text ([sting]): text to typed in textbox
        """
        self._driver.find_element(By.XPATH, f'//label[contains(normalize-space(),"{option}")]').click()
        if type_text:
            textbox = self._driver.find_element(By.XPATH, '//div[@class="modal-body"]//textarea')
            textbox.clear()
            textbox.send_keys(text)

    @PageService()
    def title(self):
        """Returns the title of panel"""
        return self.__read_title()

    @PageService(react_frame=False)
    def submit(self, wait_for_load=True):
        """submits the panel"""
        self.__click_submit()
        if wait_for_load:
            self._admin_console.wait_for_completion()

    @PageService(react_frame=False)
    def cancel(self):
        """Cancel the panel"""
        self.__click_cancel()
        self._admin_console.wait_for_completion()

    @PageService(react_frame=False)
    def close(self):
        """Close the panel"""
        self.__click_close()
        self._admin_console.wait_for_completion()

    @PageService(react_frame=False)
    def access_tab(self, tab_text):
        """
        Access tab inside panel
        Args:
            tab_text: localized tab text
        """
        self.__click_tab(tab_text)
        self._admin_console.wait_for_completion()

    @PageService(react_frame=False)
    def select_radio_button_and_type(self, option, type_text, text):
        """
            Select radio option inside panel and type text if required

        Args:
            option ([string]): radio option description to be selected
            type_text ([bool]): if true, text is required
            text ([string]): text to be entered
        """
        if option is None:
            self.cancel()
        self.__check_radio_button_and_type(option=option, type_text=type_text, text=text)

    @WebAction()
    def __expand_search_and_select(self, label, id=None):
        """Method to expand the user group search drop down"""
        if id:
            user_group_input_xpath = f"//*[@id='{id}']"
        else:
            user_group_input_xpath = f"//label[./text()='{label}']/following-sibling::div//span"
        self._driver.find_element(By.XPATH, user_group_input_xpath).click()

    @WebAction()
    def __enter_search_value(self, user_group):
        """ Method to search for user group in user group input"""
        search_box = self._driver.find_element(By.XPATH, "//div[@id='select2-drop']//input")
        search_box.send_keys(user_group)

    @WebAction()
    def __select_value(self, value):
        """ Method to select new owner from Transfer ownership pop-up
            Args:
                value : value of the search result
        """
        search_results = self._driver.find_elements(By.XPATH,
                                                    "//ul[contains(@class,'select2-results')]")
        for results in search_results:
            if results.is_displayed():
                results.find_element(By.XPATH, f".//*[text()='{value}']").click()
                break

    @PageService(react_frame=False)
    def search_and_select(self, label, select_value, id=None):
        """
        Method to transfer select a value from the search and select input

        Args:
            label        (str): Label text of the label next to which the input

            select_value (str): Value to select from the search and select input

            id           (string) : ID of the select

        Raises:
            Exception:
                If there is no option to transfer owner
        """
        self.__expand_search_and_select(label, id=id)
        self.__enter_search_value(select_value)
        self._admin_console.log.info("Waiting for 10 seconds.")
        time.sleep(10)
        self.__select_value(select_value)

    @WebAction()
    def is_accordion_expanded(self, label):
        """ Checks if accordion is expanded.
            Args:
                label: label of accordion to check
        """
        xp = f"//span[contains(text(),'{label}')]/..//i[contains(@class,'glyphicon-chevron-down')]"
        accordion_element = self._driver.find_elements(By.XPATH, xp)
        if accordion_element:
            return True
        return False

    @WebAction()
    def click_edit_inline_pencil(self, label, group_type):
        """
            Clicks the edit button for anchor tag with the inline-pencil class
            Args:
                label : label of the anchor tag
                group_type (str) : Client group number
                    Eg : 1 for Servers, 2 for Infrastructure, 3 for Server Gateway, 4 for network gateway
        """
        xp = f"//div[@id='advancedOptions_Group{group_type}']//label[text()='{label}']/..//a[contains(@class, 'inline-pencil')]"
        self._admin_console.scroll_into_view(xp)
        self._driver.find_element(By.XPATH, xp).click()

    @WebAction()
    def click_save_inline_editor(self, label, group_type):
        """
            Clicks the save button for anchor tag with the inline-editor class
            Args:
                label (str) : label of the anchor tag
                group_type (str) : Client group number
                    Eg : 1 for Servers, 2 for Infrastructure, 3 for Server Gateway, 4 for network gateway
        """
        xp = f"//div[@id='advancedOptions_Group{group_type}']//label[text()='{label}']/..//a[contains(@data-ng-click,'ctrl.saveEdit()')]"
        self._admin_console.scroll_into_view(xp)
        self._driver.find_element(By.XPATH, xp).click()

    @WebAction()
    def clear_selected_checkbox(self, form_name=None):
        """
            Un-checks all the checkboxes visible in the panel to clear all selection

        """
        if form_name:
            all_checkboxes = self._driver.find_elements(By.XPATH,
                                                        f"//form[@name='{form_name}']//*[@type='checkbox']")

        else:
            all_checkboxes = self._driver.find_elements(By.XPATH,
                                                        f"//div[@class='panel-body']//*[@type='checkbox']")

        for checkbox in all_checkboxes:
            if checkbox.is_selected():
                checked_xpath = (f"//*[@id = '{checkbox.get_attribute('id')}']/following-sibling::label | "
                                 f"//*[@id = '{checkbox.get_attribute('id')}']/following-sibling::span")
                self._driver.find_element(By.XPATH, checked_xpath).click()

    @WebAction()
    def get_error_message(self):
        """gets the error message"""
        xp = "//div[contains(@class,'modal-content')]//p"
        return self._driver.find_element(By.XPATH, xp).text

    @WebAction()
    def _enable_notify_via_email(self):
        """ Enables notify via email checkbox """
        if not self._is_notify_via_email_enabled():
            self._driver.find_element(By.XPATH, "*//span[contains(text(),'notify me via email')]").click()

    @WebAction()
    def _disable_notify_via_email(self):
        """ Enables notify via email checkbox """
        if self._is_notify_via_email_enabled():
            self._driver.find_element(By.XPATH, "*//span[contains(text(),'notify me via email')]").click()

    @WebAction()
    def _is_notify_via_email_enabled(self):
        """ method to check if Notify checkbox is enabled"""
        xpath = "//span[contains(text(), 'notify me via email')]/ancestor::div/input[contains(@class , 'ng-not-empty')]"
        return self._admin_console.check_if_entity_exists("xpath", xpath)


class RModalPanel(ABC):
    """ Class for RModalPanel """

    def __init__(self, admin_console: AdminConsole):
        """ Initialize the base panel

        Args:
            admin_console: instance of AdminConsole

        """
        self._driver = admin_console.driver
        self._admin_console = admin_console
        self._checkbox = Checkbox(self._admin_console)

    def __get_element(self, xpath: str) -> WebElement:
        """Method to get web element from xpath

        Args:
            xpath (str): xpath to get the element

        Returns:
            WebElement object having given xpath
        """

        # TODO: This method is going to go in some common file which would take a base xpath and xpath to select
        #       and then return the element
        element = self._driver.find_element(By.XPATH, xpath)
        return element

    def __clear_input_field(self, xpath:str) -> None:
        """Clears input field

        Args:
            xpath (str): xpath to get the element
        """
        element = self.__get_element(xpath)

        # clear the input element
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.DELETE)
        try:
            click_element = self.__get_element("//button[@title='Clear']")
            self._admin_console.mouseover_and_click(element, click_element)
        except:
            pass

    @WebAction()
    def __expand_search_and_select(self, label: str = None, id: str = None) -> None:
        """Method to expand the search drop down

        Args:
            label (str)         : label to search the drop down with
            id (str) [optional] : id for the dropdown
        """
        if id:
            drop_down_input_xpath = f"//*[@id='{id}' and contains(@class, 'MuiInputBase-input')]"
        elif label:
            drop_down_input_xpath = f"//label[./text()='{label}']/following-sibling::div//span/ancestor::div[contains(@class, 'MuiInput-root')]//input"
        else:
            raise CVWebAutomationException("Please give label or id for the dropdown to select")

        drop_down_element = self.__get_element(drop_down_input_xpath)
        drop_down_element.click()

    @WebAction()
    def __enter_search_value_and_select(self, value: str, id: str = None, label: str = None) -> None:
        """ Method to search for user group in user group input

        Args:
            id (str)       : id of the dropdown input
            value (str)    : value to be entered and selected in dropdown
        """
        if id:
            drop_down_input_xpath = f"//*[@id='{id}' and contains(@class, 'MuiInputBase-input')]"
        elif label:
            drop_down_input_xpath = f"//label[./text()='{label}']/following-sibling::div//span/ancestor::div[contains(@class, 'MuiInput-root')]//input"
        else:
            raise CVWebAutomationException("Please give label or id for the dropdown to select")
        self.__clear_input_field(drop_down_input_xpath)
        search_box = self.__get_element(drop_down_input_xpath)
        search_box.send_keys(value)
        # wait for the suggestions to load
        time.sleep(3)

        dropdown_value_xp = f"//div[contains(@class, 'MuiAutocomplete-popper')]//*[contains(normalize-space()," \
                            f" '{value}')  and @role='option']"

        WebDriverWait(self._driver, 30).until(
            ec.visibility_of_element_located((By.XPATH, dropdown_value_xp)))

        dd_value_element = self.__get_element(dropdown_value_xp)
        dd_value_element.click()

    @WebAction()
    def __expand_collapser_element(self, corresponding_item):
        """Method to get collapser element"""

        self.__base_xpath = "//*[contains(@class, 'modal-content')]"

        return self._driver.find_element(By.XPATH,
                                         self.__base_xpath + f"//*[text()='{corresponding_item}']/preceding::span[contains(@class, 'k-icon')][1]"
                                         )

    @WebAction()
    def submit(self) -> None:
        """Method to click submit/save in RModal"""
        xpath = "//button[@type='submit']"
        submit_btn_element = self.__get_element(xpath)
        submit_btn_element.click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def save(self) -> None:
        """Method to click save button in RModal"""
        xpath = "//button[@aria-label='Save']"
        self._driver.find_element(By.XPATH, xpath).click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def click_restore_button(self) -> None:
        """Method to click restore button in RModal"""
        x_path = r"//*[contains(@class, 'modal-content')]//button[@aria-label='Restore']"
        self._driver.find_element(By.XPATH, x_path).click()


    @WebAction()
    def __wait_for_spinner(self, wait_time: int) -> None:
        """Wait for spinner to load for folder"""
        waiter = WebDriverWait(self._driver, wait_time, poll_frequency=2)
        waiter.until_not(
            ec.presence_of_element_located(
                (By.XPATH, self.__base_xpath + "//span[contains(@class, 'k-i-loading')]"))
        )

    @WebAction()
    def __check_if_drop_down_closed(self, drop_down_id):
        """
        Method to collapse the dropdown if not already
        """
        try:
            if self._driver.find_element(By.XPATH, "//div[contains(@class,'MuiAutocomplete-popper')]"):
                self._driver.find_element(By.XPATH, f'//input[@id = "{drop_down_id}"'
                                                    f' and contains(@class, "MuiInputBase-input")]').click()
        except NoSuchElementException:
            pass

    @PageService()
    def search_and_select(self, select_value: str, label: str = None, id: str = None) -> None:
        """
        Method to select a value from the search and select input

        Args:
            select_value (str): Value to select from the search and select input
            label        (str): Label text of the label next to which the input
            id           (str) : ID of the select
        """

        if not label and not id:
            raise CVWebAutomationException("Please give label or id for the dropdown to select")

        self.__expand_search_and_select(label, id)
        self.__enter_search_value_and_select(select_value, id, label)
        self.__check_if_drop_down_closed(drop_down_id=id)
        self._admin_console.wait_for_completion()

    @PageService()
    def collapse_treeview_node(self, node_name):
        """
        Method to collapse node in treeview of the modal panel

            Args:
                node_name (str) : corresponding node name
        """
        collapser = self.__expand_collapser_element(node_name)
        collapser_attr = collapser.get_attribute("class")
        if 'alt-right' in collapser_attr or 'expand' in collapser_attr:
            collapser.click()
        self.__wait_for_spinner(wait_time=60)

    @PageService()
    def select_path_from_treeview(self, path):
        """
        Expand the tree view and selects the given path
        Args:
            path (str): selects paths
        Examples:
            c:/data/f1  --> select f1
            c:  --> select c:
            data/f1  --> select f1
        """
        temp_path = path.replace('\\', '/')
        paths = temp_path.split('/')
        if '' in paths:
            paths.remove('')
        if len(paths) > 1:
            for idx in range(0, len(paths) - 1):
                self.collapse_treeview_node(paths[idx])
                self._admin_console.wait_for_completion()
        self._checkbox.check(label=paths[-1])
        self._admin_console.wait_for_completion()

    @PageService()
    def fill_input(self, label: str = None, text: str = None, id: str = None):
        """Method to fill input text field in a Modal Dialog"""
        if id:
            xpath = f"//input[@id='{id}']"
        elif label:
            xpath = f"//label[contains(@class, 'MuiInputLabel-root') and text()='{label}']/..//input"
        else:
            raise CVWebAutomationException("Enter ID or label for input to fill data")

        element = self.__get_element(xpath)
        element.send_keys(u'\ue009' + 'a' + u'\ue003')  # CTRL + A + Backspace
        element.send_keys(text)

    @WebAction()
    def __read_title(self) -> str:
        """
        Reads Modal panel title

        returns:
            (str)     -   title text
        """
        if self._admin_console.check_if_entity_exists("xpath", "//div[@class='mui-modal-header']//h2"):
            header = self._driver.find_element(By.XPATH, "//div[@class='mui-modal-header']//h2").text
        elif self._admin_console.check_if_entity_exists("xpath","//div[@class='confirm-container']//h4"):
            header = self._driver.find_element(By.XPATH, "//div[@class='confirm-container']//h4").text
        else:
            raise Exception("Invalid panel")
        return header

    @PageService()
    def title(self) -> str:
        """
        Returns the title of panel

        returns:
            (str)     -   title text
        """
        return self.__read_title()

    @WebAction()
    def _access_tab(self, tab_text):
        """Access tab inside panel

            Args:

                tab_text    (str)   :       localized tab text

        """
        tab_xpath = f"//*[@role='tab']//*[contains(text(), '{tab_text}')]//parent::button"
        tab_element = self._driver.find_element(By.XPATH, tab_xpath)
        tab_element.click()

    @PageService()
    def access_tab(self, tab_text):
        """Access tab inside panel

            Args:

                tab_text    (str)   :       localized tab text

        """
        self._access_tab(tab_text)
        self._admin_console.wait_for_completion()

class Backup(ModalPanel):
    """ Class for backup panel"""

    class BackupType(Enum):
        """ type of backup to submit """
        FULL = "FULL"
        INCR = "INCREMENTAL"
        SYNTH = "SYNTHETIC_FULL"
        TRANSAC = "TRANSACTION_LOG"
        DIFF = "DIFFERENTIAL"

    @WebAction()
    def __set_backup_level(self, backup_type):
        """ Sets backup type

        Args:
            backup_type (BackupType): Type of backup should be one among the types defined in
                                      BackupType enum
        """
        self._driver.find_element(By.XPATH,
                                  "//input[@type='radio' and @value='" + backup_type.value + "']").click()

    @WebAction()
    def _select_backupset_and_subclient(self, backupset_name, subclient_name):
        """Selcts the required backupset and subclient
        Args:
            backupset_name (String) : Name of backupset to be selected

            subclient_name (String) : Name of the subclient to be selected

        """
        self._driver.find_element(By.XPATH,
                                  f'//label[text()="{backupset_name}"]/../..//label[text()="{subclient_name}"]'
                                  "/../preceding-sibling::span[1]//input"
                                  ).click()

    @PageService()
    def submit_backup(self, backup_type, backupset_name=None, subclient_name=None, notify=False,
                      incremental_with_data=False, cumulative=False, log=False):
        """ Submits backup job in the panel
        Args:
            backup_type (BackupType): Type of backup should be one among the types defined in
                                      BackupType enum
            backupset_name (str)    : backupset name
            subclient_name (str)    : subclient name
            notify (bool)           : to enable by email
            incremental_with_data(bool)    : To enable data in incremental backup
            cumulative  (bool)      : to enable cumulative backup
            log (bool)              : to enable log backup

        Returns:
            job_id: job id from notification
        """

        if backupset_name:
            self._select_backupset_and_subclient(backupset_name, subclient_name)
            self._admin_console.wait_for_completion()
            self.submit(wait_for_load=True)

        if backup_type not in self.BackupType:
            raise CVWebAutomationException("Invalid backup type, "
                                           "format should be one among the type in BackupType")
        self.__set_backup_level(backup_type)
        if incremental_with_data:
            self._admin_console.checkbox_select('data')
        else:
            xp = f"//*[@id = 'data']"
            if self._admin_console.check_if_entity_exists("xpath", xp):
                self._admin_console.checkbox_deselect('data')
        if cumulative:
            self._admin_console.checkbox_select('cumulative')
        if log:
            self._admin_console.checkbox_select('logCheckbox')
        if notify:
            self._enable_notify_via_email()
        else:
            self._disable_notify_via_email()
        self.submit(wait_for_load=False)
        _jobid = self._admin_console.get_jobid_from_popup()
        self._admin_console.wait_for_completion()
        return _jobid


class MultiJobPanel(ModalPanel):
    """Class for multi-job control panel"""

    class SelectionType(Enum):
        """Type of job selection criteria to select"""
        ALL = "allJobs"
        SELECTED = "allSelectedJobs"
        CLIENT = "allJobsForClient"
        CLIENT_GROUP = "allJobsForClientGroup"
        JOB_TYPE = "allJobsForJobType"
        AGENT_ONLY = "onlyJobForAgent"

    @WebAction(delay=2)
    def __click_submit(self):
        """ Clicks submit button of the panel doesnt matter about the text in it"""
        submit_buttons = self._driver.find_elements(By.XPATH,
                                                    "//button[contains(@aria-label,'OK')]")
        for button in submit_buttons:
            if button.is_displayed():
                self._driver.execute_script("return arguments[0].scrollIntoView();", button)
                button.click()
                break

    @PageService()
    def submit(self, wait_for_load=True):
        """submits the panel"""
        self.__click_submit()
        if wait_for_load:
            self._admin_console.wait_for_completion()

    @PageService()
    def config_operation(self, action_type, selection_type, entity_name=None, agent_name=None):
        """
        Sets action type and selection type by clicking their radio buttons
        Args:
            action_type     (str): one of ("suspend","resume","kill")
            selection_type (enum): one of SelectionType Enum
            entity_name     (str): name of value from dropdown to select
            agent_name      (str): agent name if selection type is "client"
        """
        if selection_type == self.SelectionType.AGENT_ONLY:
            selection_type = self.SelectionType.CLIENT
        self._admin_console.select_radio(value=action_type)
        self._admin_console.select_radio(value=selection_type.value)
        if selection_type != self.SelectionType.ALL and selection_type != self.SelectionType.SELECTED:
            self._rdropdown.select_drop_down_values(
                drop_down_id=f"{selection_type.value}_dropdown",
                values=[entity_name]
            )
        if agent_name:
            self._admin_console.checkbox_select(MultiJobPanel.SelectionType.AGENT_ONLY.value)
            self._rdropdown.select_drop_down_values(
                drop_down_id=f"{MultiJobPanel.SelectionType.AGENT_ONLY.value}_dropdown",
                values=[agent_name]
            )


class PanelInfo(ModalPanel):
    """ Gets all the page details """

    def __init__(self, admin_console, title=None):
        """ Initialize the panel info object

        Args:
            admin_console : instance of AdminConsoleBase

            title (str) : Header of the panel/tile to be handled
        """
        super(PanelInfo, self).__init__(admin_console)
        if title:
            self.__tile_xp = f"//span[contains(@title,'{title}')]/ancestor::div[@class='page-details group']"
        else:
            self.__tile_xp = ""

    @WebAction(delay=0)
    def __toggle_present(self, tag):
        """ Checks whether toggle is present in tag

        Args:
            tag: panel details

        Returns (bool) : If toggle exists in the tag

        """
        tags = tag.find_elements(By.XPATH, './/Toggle-Control')
        return len(tags) > 0

    @WebAction(delay=0)
    def __toggle_details(self, tag):
        """ Checks toggle status

        Args:
            tag: panel details

        Returns (str) : Whether toggle is ON or OFF

        """
        toggle_class = tag.find_element(By.XPATH,
                                        './/Toggle-Control/div').get_attribute('class')
        toggle_value = "OFF"
        if "enabled" in toggle_class:
            toggle_value = "ON"
        return toggle_value

    @WebAction()
    def is_toggle_enabled(self, element=None, label=None, ):
        """ Checks if toggle is enabled

        Args:
            element: WebElement corresponding to the toggle option.
            label: label for the toggle element
        Returns (bool) : True if toggle is enabled

        """
        if label:
            element = self.get_toggle_element(label)
        return 'enabled' in element.get_attribute('class')

    @WebAction()
    def get_toggle_element(self, label):
        """ Gets WebElement corresponding to the label.

        Args:
            label   (str):   Label corresponding to the toggle option.

        Returns : toggle WebElement

        """
        return self._driver.find_element(By.XPATH,
                                         self.__tile_xp +
                                         "//span[contains(text(), '" + label + "')]/ancestor::li//toggle-control"
                                                                               "/div[contains(@class,'cv-material-toggle cv-toggle')]")

    @PageService()
    def enable_toggle(self, label):
        """
        Enables the toggle bar if disabled,
        Args:
            label   (str):   Label corresponding to the toggle option.

        """

        element = self.get_toggle_element(label)

        if not self.is_toggle_enabled(element):
            element.click()
            self._admin_console.wait_for_completion()

    @PageService()
    def disable_toggle(self, label):
        """
        Disables the toggle bar if enabled

        Args:
            label   (str):   Label corresponding to the toggle option.

        """

        element = self.get_toggle_element(label)

        if self.is_toggle_enabled(element):
            element.click()
            self._admin_console.wait_for_completion()

    @WebAction()
    def __calendar_details(self):
        """ Retrieves all calendar details

        Returns :
            (list) : list of values containing Year , month  and days from the calendar of the overview page
            Example:
                 ['January 2023', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14',
                  '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31']

        """
        calendar_xp = "//div[contains(@class, 'date-time-picker')]//button[contains(@class,'btn btn-default btn-sm')]"
        calendar_xp = self.__tile_xp + calendar_xp
        calendar_tags = self._driver.find_elements(By.XPATH, calendar_xp)
        return [each_tag.text for each_tag in calendar_tags if each_tag.is_displayed() and (each_tag.text != '' and
                                                                                            each_tag.text != 'previous' and each_tag.text != 'next')]

    @PageService(react_frame=False)
    def get_calendar_details(self):
        """gets all the calendar details from calendar tile

        Returns:
            (dict) : Returns Days , Month and Year present on the calendar of the overview page
            Example:
                {"Days" : ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15',
                 '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31'] ,
                 "Month" : 'January' ,
                 "Year" : '2023' }
        """
        calendar_list = self.__calendar_details()
        calendar_dict = {"Days": [], "Month": "", "Year": ""}
        for idx in range(len(calendar_list)):
            if idx == 0:
                calendar_dict["Month"] = calendar_list[idx].split()[0]
                calendar_dict["Year"] = calendar_list[idx].split()[1]
            else:
                calendar_dict["Days"].append(calendar_list[idx])
        return calendar_dict

    @WebAction()
    def __panel_details(self):
        """ Retrieves panel details

        Returns :
            (list) : all visible tags containing text or toggle

        """
        info_xp = ("//span/following-sibling::div//*[(contains(@class, 'pageDetailColumn') or "
                   "contains(@class,'pageDetail-three-columns-first') or "
                   "contains(@class,'pageDetail-three-columns-second') or "
                   "contains(@class,'media-heading') or "
                   "contains(@class,'status-text') or "
                   "contains(@ng-if,'validationInfo')) and not(contains(@class, 'text-muted') or contains(@class, 'full-width'))]")
        info_xp = self.__tile_xp + info_xp
        tags = self._driver.find_elements(By.XPATH, info_xp)
        return [each_tag for each_tag in tags if each_tag.is_displayed()]

    @WebAction(delay=0)
    def __is_link_present(self, tag=None):
        """ Check if panel contains list of elements instead of pair """
        if tag:
            if not self._admin_console.is_element_present("./following-sibling::span", tag) and \
                    not self._admin_console.is_element_present("./following-sibling::a"
                                                               "[contains(@class, 'pageDetailColumn')]", tag):
                if self._admin_console.is_element_present("./following-sibling::a", tag):
                    return True
            return False
        else:
            links = self._driver.find_elements(By.XPATH,
                                               self.__tile_xp + "//ul[contains(@class,'list-style')]/li/a"
                                               )
            for link in links:
                if link.is_displayed():
                    return True
            return False

    @WebAction(delay=0)
    def __fetch_panel_list(self):
        """
        fetch all visible anchor tags from panel

        Returns:
            (list) : list of elements displayed in the panel
         """
        list_elements = self._driver.find_elements(By.XPATH,
                                                   self.__tile_xp + "//ul[contains(@class,'list-style')]/li/span")
        values = []
        for list_element in list_elements:
            if list_element.is_displayed():
                values.append(list_element.text)
        return values

    @WebAction(delay=0)
    def __fetch_panel_links(self, tag=None):
        """
        fetch all visible anchor tags from panel

        Returns:
            (list) : all visible anchor tags displayed in the panel
         """
        if tag:
            link = tag.find_element(By.XPATH, "./following-sibling::a")
            return link.text
        else:
            links = self._driver.find_elements(By.XPATH,
                                               self.__tile_xp + "//ul[contains(@class,'list-style')]//a")
            return [link.text for link in links if link.is_displayed()]

    @WebAction(delay=0)
    def __copy_label_exist(self, tag):
        """Returns True if copy label exist"""
        # sample in company page with authcode
        return tag.find_elements(By.XPATH, './label/span[@uib-tooltip="Copy to clipboard"]')

    @WebAction(delay=1)
    def __expand_cv_accordion(self, name):
        """Clicks the heading of an accordion inside panel"""
        xpath = f'{self.__tile_xp}//span[@class="cv-accordion-text" and text()="{name}"]/ancestor::a'

        if self._admin_console.check_if_entity_exists('xpath', xpath):
            element = self._driver.find_element(By.XPATH, xpath)
            element.click()

    @WebAction(delay=0)
    def __click_dropdown_toggle(self, tag):
        """clicks on link show dropdown"""
        # sample in company page with supported solutions
        dropdown_list = tag.find_elements(By.XPATH,
                                          "//a[contains(@class, 'dropdown-toggle') and contains(text(), '+')]"
                                          )
        if dropdown_list:
            dropdown_list[0].click()

    @PageService()
    def get_list(self):
        """Gets the list from panels

        Returns:
            list of values in panel
        """
        values = self.__fetch_panel_list()
        return values

    @PageService()
    def get_details(self):
        """ Gets all the information contained in the panel

        Returns :
            details (dict) : Details of the panel in key value pair

        """
        details = {}
        self.__expand_cv_accordion('More')
        tags = self.__panel_details()
        if not tags:
            if self.__is_link_present():
                values = self.__fetch_panel_links()
                return values
            else:
                values = self.__fetch_panel_list()
                return values
        tag_count = 0
        key = None
        for each_tag in tags:
            tag_count += 1
            if tag_count % 2 != 0:
                key = each_tag.text
            else:
                if self.__toggle_present(each_tag):
                    value = self.__toggle_details(each_tag)
                else:
                    value = each_tag.text
                    if '+' in value:
                        self.__click_dropdown_toggle(each_tag)
                        value = each_tag.text
                        value = re.sub(' , \+([0-9]+)', '', value)
                        value = value.replace('\n', ', ')

                if key in details.keys():
                    if isinstance(details[key], list):
                        value = details[key] + [value]
                    else:
                        value = [details[key]] + [value]
                details.update({key: value})
        return details

    @WebAction()
    def add_tile_entity(self, entity_name=None):
        """click on Add for specific entity inside tile """
        if entity_name:
            xpath = (self.__tile_xp +
                     f"//span[contains(text(),'{entity_name}')]/ancestor::li//a[contains(text(),'Add')]")
        else:
            xpath = self.__tile_xp + "//div[contains(@class,'page-details-box-links')]//a[contains(text(),'Add')]"

        entity_add_icon = self._driver.find_element(By.XPATH, xpath)
        entity_add_icon.click()

    @WebAction()
    def edit_tile(self):
        """click on edit icon for tile contents """
        tile_edit_icon = self._driver.find_element(By.XPATH,
                                                   self.__tile_xp +
                                                   "//div[contains(@class,'page-details-box-links')]//*[contains(text(),'Edit')]"
                                                   )
        tile_edit_icon.click()

    @PageService()
    def more_tile(self):
        """Clicks on more icon for tile contents"""
        self.__expand_cv_accordion("More")

    @WebAction()
    def edit_tile_entity(self, entity_name):
        """click on edit for specific entity inside tile """
        base_xpath = f"{self.__tile_xp}//span[contains(text(),'{entity_name}')]/ancestor::li//"
        xpath = base_xpath + "a[contains(text(),'Edit')]"
        if not self._admin_console.check_if_entity_exists("xpath", xpath):
            xpath = base_xpath + "span[contains(text(),'Edit')]"

        if not self._admin_console.check_if_entity_exists("xpath", xpath):
            xpath = base_xpath + "a[contains(@class, 'inline-editor-button')]"

        if not self._admin_console.check_if_entity_exists("xpath", xpath):
            xpath = base_xpath + "span[contains(@title,'Edit')]"

        entity_edit_icon = self._driver.find_element(By.XPATH, xpath)
        entity_edit_icon.click()

    @WebAction()
    def open_hyperlink_on_tile(self, hyperlink):
        """ Opens hyperlink on tile

        Args:
            hyperlink : hyperlink to be clicked on
            """
        tile_hyperlink = self._driver.find_element(By.XPATH, f"{self.__tile_xp}//a[contains(text(),'{hyperlink}')]")
        tile_hyperlink.click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def get_all_hyperlinks(self):
        """Gets list of all link texts"""
        tile_hyperlinks = self._driver.find_elements(By.XPATH, self.__tile_xp + "//a[contains(@class, 'display')]")
        return list(set(link.text.strip() for link in tile_hyperlinks))

    @WebAction()
    def click_button_on_tile(self, button_text):
        """
        Clicks button on tile

        Args:
            button_text :   text on the button to be clicked
        """
        button_element = self._driver.find_element(By.XPATH,
                                                   f"{self.__tile_xp}//button[contains(text(),'{button_text}')]")
        button_element.click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def check_if_hyperlink_exists_on_tile(self, hyperlink):
        """ Checks if hyperlink on tile exists

        Args:
            hyperlink : hyperlink to be clicked on

        Returns:
            True if hyperlink exists
            False if hyperlink doesn't exist
            """
        tile_hyperlink_xpath = self.__tile_xp + f"//a[contains(text(),'{hyperlink}')]"
        return self._admin_console.check_if_entity_exists('xpath', tile_hyperlink_xpath)

    @WebAction()
    def __click_confirm(self):
        """Click on confirm"""
        self._admin_console.driver.find_element(By.XPATH,
                                                self.__tile_xp + "//a[@title='Confirm']").click()

    def confirm(self):
        """Click on confirm"""
        self.__click_confirm()

    @WebAction()
    def __click_tick_mark_after_dropdown_selection(self, label):
        """Clicks on the tick mark near dropdown to save the selection
        Args:
            label  :    Name of label which was edited
        """
        xpath = self.__tile_xp + f"//span[normalize-space()='{label}']" \
                                 f"/..//*[@class='k-icon k-i-check']"
        if not self._admin_console.check_if_entity_exists("xpath", xpath):
            xpath = self.__tile_xp + f"//span[normalize-space()='{label}']" \
                                     f"/../..//*[@class='k-icon k-i-check']"
        tick_mark = self._driver.find_element(By.XPATH, xpath)
        tick_mark.click()

    @PageService()
    def save_dropdown_selection(self, label):
        """Clicks on the tick mark near dropdown to save the selection
                Args:
                    label  :    Name of label which was edited
                """
        self.__click_tick_mark_after_dropdown_selection(label)
        self._admin_console.wait_for_completion()


class RPanelInfo(RModalPanel):
    """ Gets all the details for React Panel """

    def __init__(self, admin_console, title=None):
        """ Initialize the panel info object

        Args:
            admin_console : instance of AdminConsoleBase

            title (str) : Header of the panel/tile to be handled
        """
        super(RPanelInfo, self).__init__(admin_console)
        if title:
            self.__tile_xp = f"//span[contains(@class, 'MuiCardHeader-title') and normalize-space()='{title}']" \
                             f"/ancestor::div[contains(@class, 'MuiCard-root')]"
        else:
            self.__tile_xp = ""
        self.__toggle = Toggle(admin_console, self.__tile_xp)
        self.__checkbox = Checkbox(admin_console, self.__tile_xp)
        self.__recovery_calendar = RecoveryCalendar(admin_console, self.__tile_xp)

    @property
    def toggle(self) -> Toggle:
        """Returns instance of toggle class"""
        return self.__toggle

    @property
    def checkbox(self) -> Checkbox:
        """Returns instance of checkbox class"""
        return self.__checkbox

    @WebAction()
    def __calendar_details(self):
        """ Retrieves all calendar details in React

        Returns :
            (list) : list of values containing Year , month  and days from the calendar of the overview page
            Example:
                 ['Jan 2023', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14',
                  '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31']

        """

        calendar_xp = "//div[contains(@id, 'teer-calendar')]//div[contains(@class,'sc-dXxSUK')] |" \
                      "//div[contains(@id, 'teer-calendar')]//div[contains(@class,'sc-zsjhC')] |" \
                      "//div[contains(@id, 'teer-calendar')]//div[contains(@class,'sc-jIsiFf')]"
        calendar_xp = self.__tile_xp + calendar_xp
        calendar_tags = self._driver.find_elements(By.XPATH, calendar_xp)
        calendar_list = []
        for each_tag in calendar_tags:
            if each_tag.text not in calendar_list and each_tag.is_displayed() and each_tag.text != '':
                calendar_list.append(each_tag.text)
        return calendar_list

    @PageService()
    def get_calendar_details(self):
        """gets all the calendar details from calendar tile in React

        Returns:
            (dict) : Returns Days , Month and Year present on the calendar of the overview page
            Example:
                {"Days" : ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15',
                 '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31'] ,
                 "Month" : 'January' ,
                 "Year" : '2023' }
        """
        calendar_list = self.__calendar_details()
        calendar_dict = {"Days": [], "Month": "", "Year": ""}
        for idx in range(len(calendar_list)):
            if idx == 0:
                calendar_dict["Month"] = calendar_list[idx].split()[0]
                calendar_dict["Year"] = calendar_list[idx].split()[1]
            else:
                calendar_dict["Days"].append(calendar_list[idx])
        return calendar_dict

    @WebAction()
    def __panel_details(self):
        """ Retrieves panel details

        Returns :
            (dict) : Dict containing the panel details
        """
        tile_row_details = {}

        row_label_xpath = "//*[@class='tile-row-label' or contains(@class, 'tile-row-label') "\
                          "or contains(@class,'label-wrapper')] |" \
                          "//h4[contains(@class,'kpi-title')]"

        row_labels = self._driver.find_elements(By.XPATH, self.__tile_xp + row_label_xpath)

        for row_label in row_labels:
            has_toggle = row_label.find_elements(By.XPATH,
                                                 ".//following-sibling::div[contains(@class, 'tile-row-value') or contains(@class,'input-wrapper')]//*[contains(@class, 'teer-toggle')]")
            has_callout = row_label.find_elements(By.XPATH,
                                                  ".//following-sibling::div[contains(@class, 'tile-row-value') or contains(@class,'input-wrapper')]//*[contains(@id, 'popper-callout')]//a")
            if has_toggle:
                label_text = row_label.text
                toggle_element = has_toggle[0].find_element(By.XPATH,
                                                            ".//span[contains(@class, 'MuiSwitch-switchBase')]")
                value = False
                if 'Mui-checked' in toggle_element.get_attribute("class"):
                    value = True

                tile_row_details[label_text] = value
            else:
                label_text = row_label.text
                row_val = row_label.find_elements(By.XPATH,
                                                  "(.//following-sibling::div[contains(@class, 'tile-row-value')]"
                                                  "/div[@class='tile-row-value-display']) | .//following-sibling::div"
                                                  "[contains(@class, 'tile-row-value')] | "
                                                  ".//following-sibling::div[contains(@class, 'input-wrapper')] | "
                                                  "(.//following-sibling::h5[contains(@class,'kpi-subtitle')])")
                row_val_text = ""
                if row_val:
                    row_val_text = row_val[0].text

                if has_callout:
                    row_val_text = row_val_text.split('\n')[0] + ", " + self.__add_callout_data(row_label)

                # Handle operators tile in company details page, where same user can have multiple roles
                if label_text in tile_row_details:
                    tile_row_details[label_text] = [tile_row_details[label_text], row_val_text]
                else:
                    tile_row_details[label_text] = row_val_text

        return tile_row_details


    @WebAction()
    def __is_link_present(self, tag=None):
        """ Check if tag is a link or not

        Args :
            tag: Web element to check
        """
        if tag:
            if self._admin_console.is_element_present("./following-sibling::a", tag):
                return True

        return False

    @WebAction(delay=0)
    def __fetch_panel_links(self, tag=None):
        """
        fetch all visible anchor tags from panel

        Returns:
            (list) : all visible anchor tags displayed in the panel
         """
        if tag:
            link = tag.find_element(By.XPATH, "./following-sibling::a")
            return link.text

        return ""

    @WebAction()
    def __has_overflow_item(self, tag):
        """ Checks if the web element contains overflow list items

        Args :
            tag: Web element to check for overflow items
        """
        if tag:
            if self._admin_console.is_element_present(".//div"
                                                      "[contains(@class,'overflow-list-container')]", tag):
                return True

        return False

    @WebAction()
    def __click_overflow_dropdown(self, tag=None):
        """ click overflow dropdown """
        xpath = "//button[@class='overflow-list-item overflow-dropdown-link']"

        if self._admin_console.is_element_present(xpath, tag):
            self._driver.find_element(By.XPATH, self.__tile_xp + xpath).click()

    @WebAction()
    def __get_overflow_items(self, tag):
        """ Gets the data from overflow list container

        Args :
            tag: Web element to get overflow items from

        Returns :
            (list) : List of overflow items
        """
        xpath = self.__tile_xp + "//span[@class='overflow-list-item']"

        self.__click_overflow_dropdown(tag)
        self._admin_console.wait_for_completion()
        items = self._driver.find_elements(By.XPATH, xpath)
        overflow_list = []
        for item in items:
            if item.is_displayed():
                if item.text[-1] == " ":
                    overflow_list.append(item.text[:-2])
                else:
                    overflow_list.append(item.text)
        return overflow_list

    @PageService()
    def get_overflow_items(self):
        """
        Gets the overflow items list
        Returns :
            (list) : List of overflow items
        """
        tag_element = self._driver.find_element(By.XPATH, self.__tile_xp)
        list = []
        if self.__has_overflow_item(tag_element):
            list = self.__get_overflow_items(tag_element)
        return list

    @WebAction()
    def __click_tile_action(self, tile_label=None):
        """ Click on edit icon for tile contents """
        tile_xpath = f"{self.__tile_xp}//button[@title='Edit']"
        if tile_label:
            tile_xpath = f"//span[contains(text(), '{tile_label}')]/../following-sibling::*{tile_xpath}"
        self._admin_console.scroll_into_view(tile_xpath)
        tile_edit_icon = self._driver.find_element(By.XPATH, tile_xpath)
        tile_edit_icon.click()

    @WebAction()
    def __click_tile_view(self):
        """ Click on view icon for tile contents """
        tile_view_icon = self._driver.find_element(By.XPATH,
                                                   self.__tile_xp +
                                                   "//button[@title='View']"
                                                   )
        tile_view_icon.click()

    @WebAction()
    def __click_hyperlink(self, hyperlink):
        """ Opens hyperlink on tile

        Args:
            hyperlink : hyperlink to be clicked on
        """
        self.__click_overflow_dropdown()
        self._driver.find_element(By.XPATH,
                                  self.__tile_xp + f"//a[normalize-space()='{hyperlink}']"
                                  ).click()

    @WebAction()
    def __check_if_tile_disabled(self):
        """ Method to check if tile is disabled"""
        return self._admin_console.check_if_entity_exists('xpath',
                                                          self.__tile_xp + "//div[contains(@class, 'MuiCardContent-root disabled')]")

    @WebAction()
    def __check_edit_button_visibility(self):
        """ Method to check if edit button is visible"""
        return self._admin_console.check_if_entity_exists('xpath', self.__tile_xp + "//button[@title='Edit']")

    @WebAction()
    def __click_inline_edit(self, label: str) -> None:
        """ Clicks on edit icon for inline edit

        Args:
                label (str): label for option to edit

        """
        xpath = f"//div[contains(@class,'tile-row center')]//*[text()='{label}']/" \
                f"ancestor::div[contains(@class, 'tile-row center')]" \
                f"//div[contains(@class, 'tile-row-edit-links')]//button"

        custom_edit_xpath = f"//div[contains(@class,'tile-row')]//*[text()='{label}']" \
                            f"/following-sibling::div[contains(@class, 'tile-row-value')]" \
                            f"//div[contains(@class,'edit') or contains(@aria-label,'Edit')]" \
                            f"//button[contains(@class, 'MuiIconButton-root')]"

        if self._admin_console.check_if_entity_exists("xpath", xpath):
            element = self._driver.find_element(By.XPATH, self.__tile_xp + xpath)
        elif self._admin_console.check_if_entity_exists("xpath", custom_edit_xpath):
            element = self._driver.find_element(By.XPATH, self.__tile_xp + custom_edit_xpath)
        else:
            raise CVWebAutomationException(f"No element with given label exists, xpaths tried:"
                                           f" [{xpath}] and [{custom_edit_xpath}]")
        element.click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def __click_inline_add(self, label: str) -> None:
        """
        Clicks on the add inline icon button

        Args:
                label (str) : label/entity name for add icon button
        """
        custom_add_xpath = f"//div[contains(@class,'tile-row')]//*[text()='{label}']" \
                           f"/following-sibling::div[contains(@class, 'tile-row-value')]" \
                           f"//button[contains(@class, 'MuiIconButton-root') and contains(@id, 'add')]"

        element = self._driver.find_element(By.XPATH, self.__tile_xp + custom_add_xpath)
        element.click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def check_if_button_exists(self, label):
        """
        Check if a button with given label exists or not

        Args:
                label (str): button text to check.
        Returns:
            True if button exists
            False if button doesn't exist
        """
        xpath = f"//button[contains(@class, 'MuiButton-root')]//div[text()='{label}']"
        return self._admin_console.check_if_entity_exists('xpath', self.__tile_xp + xpath)

    @WebAction()
    def click_button(self, label):
        """Clicks on a button in RPanelInfo

        Args:
                label (str): button text to click
        """
        xpath = f"//button[contains(@class, 'MuiButton-root')]//div[text()='{label}']"
        element = self._driver.find_element(By.XPATH, self.__tile_xp + xpath)
        element.click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def click_button_by_title(self, title):
        """Clicks on a button in RPanelInfo by title
        Args:
                title (str): button title to click
        """
        xpath = f"//button[contains(@class, 'MuiButtonBase-root') and contains(@title, '{title}')]"
        element = self._driver.find_element(By.XPATH, self.__tile_xp + xpath)
        element.click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def fill_input(self, label, text):
        """Method to fill inline input text field based on row label

        Args:
                label (str): label for the input to fill text in
                text (str): text to be filled
        """
        xpath = f"//*[text()='{label}']/..//input[contains(@class, 'MuiInput-input')]"
        element = self._driver.find_element(By.XPATH, xpath)
        element.send_keys(u'\ue009' + 'a' + u'\ue003')  # CTRL + A + Backspace
        element.send_keys(text)

    @WebAction()
    def __toggle_with_delay(self, label: str, delay: str) -> None:
        """ Enables the toggle with delay

        Args:
            label: label for the toggle element
            delay: the amount of delay to add
                    (1 hour/4 hours/8 hours/.../1 day)
        """
        row_xp = f"//*[contains(text(), '{label}')]//ancestor::div[contains(@class,'tile-row')]"
        delay_button_xp = "//span[contains(@class,'enableDelayDetails')]"
        self._driver.find_element(By.XPATH, self.__tile_xp + row_xp + delay_button_xp).click()
        time.sleep(2)
        menu_items = self._driver.find_elements(By.XPATH,
                                                f"//ul[contains(@class,'MuiMenu-list')]"
                                                f"//*[contains(text(),'{delay}')]//parent::li"
                                                )
        for menu_item in menu_items:
            if menu_item.is_displayed():
                menu_item.click()

    @WebAction()
    def __click_action_item(self, action_name):
        """
        Selects button for action item in the Panel

        Args:
            action_name : Name of action item to be clicked
         """
        action_items_xp = "//div[@id='action-list']//div[contains(text(), '{}')]/ancestor::button".format(action_name)
        action_items = self._driver.find_elements(By.XPATH, action_items_xp)
        for elem in action_items:
            if elem.is_displayed():
                elem.click()
                break

    @PageService()
    def fill_value_with_label(self, label, text):
        """Method to fill text field based on corresponding input label

        Args:
                label (str)  :   Inline edit text box label
                text  (str)  :   Text to be filled in
        """
        xpath = f"{self.__tile_xp}//*[text()='{label}']//following-sibling::div//input"
        element = self._driver.find_element(By.XPATH, xpath)
        element.send_keys(u'\ue009' + 'a' + u'\ue003')  # CTRL + A + Backspace
        element.send_keys(text)

    @PageService()
    def is_tile_disabled(self):
        """ To check if tile is disabled"""
        return self.__check_if_tile_disabled()

    @PageService()
    def is_edit_visible(self):
        """ To check if edit button on panel is visible"""
        return self.__check_edit_button_visibility()

    @PageService()
    def edit_tile(self, tile_label=None) -> None:
        """ Edit tile info"""
        self.__click_tile_action(tile_label)

    @PageService()
    def view_tile(self) -> None:
        """ View tile info """
        self.__click_tile_view()

    @PageService()
    def add_tile_entity(self, entity_name: str) -> None:
        """
        Method to click on inline add icon button

        Args:
                entity_name (str): entity name/label for which the add icon button is to be clicked
        """
        self.__click_inline_add(entity_name)

    @PageService()
    def edit_tile_entity(self, entity_name: str) -> None:
        """ Edit the inline properties in tile

        Args:
                entity_name (str)   : Entity name/label for which the edit icon button is to be clicked
        """
        self.__click_inline_edit(entity_name)

    @PageService()
    def edit_and_save_tile_entity(self, entity_name, text):
        """ Edits inline tile entity, fills text and save it

            Args:
                    entity_name (str): label for the entity
                    text (str): text to fill in the input field
        """
        self.edit_tile_entity(entity_name)
        self.fill_input(entity_name, text)
        self.click_button("Submit")
        self._admin_console.wait_for_completion()

    @WebAction()
    def is_toggle_enabled(self, element=None, label=None):
        """ Checks if toggle is enabled
        Args:
            element: WebElement corresponding to the toggle option.
            label: label for the toggle element
        Returns (bool) : True if toggle is enabled
        """
        if label:
            element = self.get_toggle_element(label)
        return 'checked' in element.get_attribute('class')

    @WebAction()
    def get_toggle_element(self, label):
        """ Gets WebElement corresponding to the label
        Args:
            label   (str):   Label corresponding to the toggle option.

        Returns : toggle WebElement
        """
        return self._driver.find_element(By.XPATH,
                                         self.__tile_xp + f"//*[text()='{label}']/ancestor::div[contains(@class, "
                                                          f"'tile-row') or contains(@class, 'field-wrapper')]"
                                                          f"//span[contains(@class, 'MuiSwitch-switchBase')]")

    @PageService()
    def enable_toggle(self, label, delay=None):
        """ Enables the toggle bar if disabled
        Args:
            label   (str):   Label corresponding to the toggle option.
            delay   (str):  Enabled with delay if given (1 hour/ 4 hours/ 8 hours ...1 day)
        """
        element = self.get_toggle_element(label)

        if not self.is_toggle_enabled(element):
            if not delay:
                element.click()
            else:
                self.__toggle_with_delay(label, delay)
            self._admin_console.wait_for_completion()

    @PageService()
    def disable_toggle(self, label):
        """ Disables the toggle bar if enabled
        Args:
            label   (str):   Label corresponding to the toggle option.
        """
        element = self.get_toggle_element(label)

        if self.is_toggle_enabled(element):
            element.click()
            self._admin_console.wait_for_completion()

    @PageService()
    def enable_disable_toggle(self, label, enable=True):
        """ Enables or disables the toggle bar
        Args:
            label   (str):   Label corresponding to the toggle option.
            enable  (bool):  True to enable, False to disable
        """
        self.enable_toggle(label) if enable else self.disable_toggle(label)

    @PageService()
    def get_details(self):
        """ Gets all the information contained in the panel

        Returns :
            details (dict) : Details of the panel in key value pair

        """
        details = self.__panel_details()
        return details

    @PageService()
    def get_list(self):
        """ Gets all the information contained in the list

        Returns:
            (list) : list of elements displayed in the panel
         """
        xpath = self.__tile_xp + f"//span[contains(@class, 'MuiListItemText')]"
        list_elements = self._driver.find_elements(By.XPATH, xpath)
        values = []
        for list_element in list_elements:
            if list_element.is_displayed():
                values.append(list_element.text)
        return values

    @PageService()
    def get_label(self):
        """ Gets all labels from the panel

        Returns:
            (list) : list of label texts found in the panel
        """
        xpath = self.__tile_xp + f"//div[contains(@class,'tile-row-label')]//div"
        elements = self._driver.find_elements(By.XPATH, xpath)
        labels = []
        for element in elements:
            if element.is_displayed():
                labels.append(element.text)
        return labels

    @PageService()
    def get_tree_list(self):
        """ Gets all the tree structure type information

        Returns:
            (dict)  : dict with parent list item key and list of its children value
                      example (permissions panel in role details) - {
                          'permission_category1': ['permission1', 'permission2'],
                          'permission_category2': ['permissionX', ...],
                          ...
                      }
        """
        xpath = self.__tile_xp + "//*[@class='tile-row']/*/*/*"
        list_elements = self._driver.find_elements(By.XPATH, xpath)
        tree = {}
        for parent_div, children_div in zip(list_elements[::2], list_elements[1::2]):
            tree[parent_div.text] = children_div.get_attribute('innerText').split('\n')
        return tree

    @PageService()
    def open_hyperlink_on_tile(self, hyperlink):
        """ Opens the provided hyperlink

        Args:
            hyperlink: hyperlink to be clicked
        """
        self.__click_hyperlink(hyperlink)
        self._admin_console.wait_for_completion()

    @PageService()
    def check_if_hyperlink_exists_on_tile(self, hyperlink):
        """ Checks if hyperlink on tile exists

        Args:
            hyperlink : hyperlink to be clicked on

        Returns:
            True if hyperlink exists
            False if hyperlink doesn't exist
            """
        tile_hyperlink_xpath = self.__tile_xp + f"//a[contains(text(),'{hyperlink}')]"
        return self._admin_console.check_if_entity_exists('xpath', tile_hyperlink_xpath)

    @PageService()
    def click_action_item(self, action_name, aria_label=None):
        """Clicks on given Action item from panel

        Args:
            action_name  (str) :  name of action item to be clicked
            aria_label  (str) :  aria-label value of dropdown button
        """
        self.__click_actions_menu(aria_label)
        self.__click_action_item(action_name)
        self._admin_console.wait_for_completion()

    @WebAction()
    def available_panels(self):
        """Method to return available panels"""
        return [element.text for element in self._driver.find_elements(By.XPATH, "//*[contains(@class, 'MuiCardHeader-title')]")]

    @WebAction()
    def click_title(self, title: str):
        """Method to click on panel title

        Args:
            title (str)   : panel title
        """
        xpath = f"//span[contains(@class, 'MuiCardHeader-title') and normalize-space()='{title}']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def click_button(self, button_name):
        """Method to click button on RPanelInfo component

        Args:
            button_name (str)   : label for the button to click
        """
        xpath = f"{self.__tile_xp}//*[text()='{button_name}']/ancestor::button[contains(@class, 'MuiButton-root')]"
        self._driver.find_element(By.XPATH, xpath).click()
        self._admin_console.wait_for_completion()

    @PageService()
    def click_button_from_menu(self, dd_label, button_name):
        """Method to click button from a menu dropdown on a react panel

        Args:
            dd_label (str)  : label for the dropdown to click
            button_name (str): label for button to click in dropdown menu
        """
        self.click_button(dd_label)
        self._admin_console.click_button_using_text(button_name)

    @PageService()
    def submit(self, wait_for_load=True):
        """Proxy method for backwards compatibility"""
        self._admin_console.click_submit()
        if wait_for_load:
            self._admin_console.wait_for_completion()

    @PageService()
    def save(self, wait_for_load=True):
        """Saves the panel"""
        self._admin_console.click_save()
        if wait_for_load:
            self._admin_console.wait_for_completion()

    @PageService()
    def cancel(self):
        """Cancel the panel"""
        self._admin_console.click_cancel()
        self._admin_console.wait_for_completion()

    @WebAction()
    def __click_actions_menu(self, aria_label=None):
        """
            Clicks on the panel actions

            aria_label          (str)   --  aria-label value of button
        """
        if aria_label:
            xpath = self.__tile_xp + f"//button[@aria-label='{aria_label}']" \
                                     f"/ancestor::div[contains(@class,'action-list-dropdown-wrapper')]"
        else:
            xpath = self.__tile_xp + "//div[contains(@class,'action-list-dropdown-wrapper')]//button[1]"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __add_callout_data(self, row_label):
        """Formats and returns row value after adding callout data"""
        """Formats and returns row value after adding callout data"""
        callout_elem = row_label.find_element(By.XPATH,
                                              ".//following-sibling::div[contains(@class, 'tile-row-value')]//*[contains(@id, 'popper-callout')]")
        anchor_elements = callout_elem.find_elements(By.XPATH, ".//a")
        # If callout's href attribute has a link, we cannot click it as it may re-direct to a different page
        for element in anchor_elements:
            if element.get_attribute("href"):
                return ""

        callout_elem.click()

        popover_body = self._driver.find_element(By.XPATH, "//div[@class='popover-body']")
        callout_str = popover_body.text.replace("\n", ", ")

        return callout_str

    @PageService()
    def select_browse_time(self, time_value):
        """
           Picks the browse time from recovery panel

           Args:
               time_value   (dict): the time to be set during browse

           Examples:
                    time_value:   {
                                       'hours':    09,
                                       'minutes':     19,
                                   }

        """
        if time_value.get("hours"):
            if time_value['hours'] > 12:
                time_string = f"{time_value['hours'] - 12}:{time_value['minutes']:02d} PM"
            elif time_value['hours'] == 12:
                time_string = f"{time_value['hours']}:{time_value['minutes']:02d} PM"
            else:
                if time_value['hours'] == 0:
                    time_string = f"12:{time_value['minutes']:02d} AM"
                else:
                    time_string = f"{time_value['hours']}:{time_value['minutes']:02d} AM"
            hr_min = f"{time_value['hours']}:{time_value['minutes']:02d}"

            if self._admin_console.check_if_entity_exists("xpath", f"//button[@aria-label='{hr_min}']"):
                self._admin_console.click_by_xpath(f"//button[@aria-label='{hr_min}']")
            else:
                self._admin_console.click_by_xpath(f"//button[@aria-label='{time_string}']")

    @PageService()
    def date_picker(self, time_value):
        """
           Picks the date and browse time from recovery panel

           Args:
               time_value   (dict): the time to be set as range during the browse

           Examples:
                    time_value:   {   'year':     2017,
                                       'month':    december,
                                       'date':     31,
                                       'hours':    09,
                                       'minutes':  19
                                   }

        """

        self.__recovery_calendar.select_date(time_value)
        self.select_browse_time(time_value)

    @WebAction()
    def _click_action_menu_for_tile_row(self, tile_row_xpath):
        """Opens the action menu for a tile row in the panel

            Args:

                tile_row_xpath  (str)   :       XPath for the tile row containing action menu
        """
        action_menu_xpath = tile_row_xpath + "//div[@aria-label='More']"
        self._driver.find_element(By.XPATH, action_menu_xpath).click()

    @WebAction()
    def _click_action_item_for_tile_row(self, action_item):
        """Clicks on the action item on the opened action menu for a tile row in the panel

            Args:

                action_item (str)   :       Action item text
        """
        action_item_xpath = f"//li[@role='menuitem']//*[contains(text(), '{action_item}')]"
        self._driver.find_element(By.XPATH, action_item_xpath).click()

    @PageService()
    def click_action_item_for_tile_label(self, label, action_item):
        """Clicks action item for a tile label in the panel

            Args:

                label       (str)   :       Label text in the react panel

                action_item (str)   :       Action item text

        """
        tile_row_xp = (f"//*[contains(@class, 'tile-row-label')]//*[contains(text(), '{label}')]"
                       "//ancestor::div[contains(@class, 'tile-row')]")

        self._click_action_menu_for_tile_row(tile_row_xp)
        self._admin_console.wait_for_completion()
        self._click_action_item_for_tile_row(action_item)

    @WebAction()
    def click_add_icon(self, label):
        """Clicks on add icon next to a label in the panel"""
        tile_row_xp = (f"//*[contains(@class, 'tile-row-label')]//*[contains(text(), '{label}')]"
                       "//ancestor::div[contains(@class, 'tile-row')]")
        self._driver.find_element(By.XPATH, tile_row_xp + "//button[@title='Manage']").click()


class Security(ModalPanel):
    """ Class to edit security panel """

    def __init__(self, admin_console):
        """ Initialize the panel info object

        Args:
            admin_console : instance of AdminConsoleBase
        """
        super(Security, self).__init__(admin_console)
        self._dropdown = DropDown(admin_console)
        self.__tile_xp = f"//span[@title='Security']/ancestor::div[@class='page-details group']"

    @PageService()
    def edit_security_association(self, associations, add=True, title="Security"):
        """
        edit security association

        Args:
             associations (dict) : dictionary containing user and role pairs
                Eg. -> associations = {
                                        'User1' : [['View'], ['Alert owner']],
                                        'master': [['Master'], ['Create Role', 'Edit Role', 'Delete Role']]
                                      }
            add (boolean) : True means add association, False means remove
        """
        from Web.AdminConsole.Components.dialog import SecurityDialog

        PanelInfo(self._admin_console, title).edit_tile()
        self._admin_console.wait_for_completion()
        if not add:
            for user, roles in associations.items():
                for role in roles:
                    if len(role) > 1:
                        joined_text = ' , '.join(role)
                        role = [f'[Custom] - {joined_text} ']  # Eg: Master user can have custom multiple roles
                    SecurityDialog(self._admin_console, title).remove_association(user, role[0])

        if add:
            for user, roles in associations.items():
                for role in roles:
                    if len(role) > 1:
                        continue  # Can only add a single role at a time
                    SecurityDialog(self._admin_console, title).add_association(user, role[0])
                    self._admin_console.wait_for_completion()

        self.submit()
        self._admin_console.check_error_message()

    @WebAction()
    def __get_row(self):
        """ Method to get the Security detail row"""
        return self._driver.find_elements(By.XPATH, "//*[@id='tileContent_Security']//li[@class='group ng-scope']")

    @WebAction()
    def __get_user(self, row):
        """ Method to get user on row provided as input"""
        return row.find_element(By.XPATH, "./span[1]").text

    @WebAction()
    def __get_role(self, row):
        """ Method to get role on row provided as input"""
        return row.find_element(By.XPATH, "./span[2]").text

    @WebAction()
    def __click_show_inherited(self):
        """ Action method to click on show inherited link"""
        xpath = "//a[text()='Show inherited association']"
        self._driver.find_element(By.XPATH, xpath).click()

    @PageService()
    def get_details(self, show_inherited=False):
        """ Get all details displayed in the Security tile """
        if show_inherited:
            self.__click_show_inherited()

        rows = self.__get_row()
        temp_dict = {}
        for row in rows:
            nested_key = self.__get_user(row)
            nested_value = self.__get_role(row)
            nested_value_list = []
            if "[Custom] - " in nested_value:
                nested_value = nested_value[11:]
                nested_value_list = nested_value.split(" , ")
            else:
                nested_value_list.append(nested_value)
            if nested_key in temp_dict:
                temp_dict[nested_key].append(nested_value_list)
            else:
                temp_dict[nested_key] = [nested_value_list]
            temp_dict[nested_key].sort()
        return temp_dict


class RSecurityPanel(RPanelInfo):
    """ Class to handle react Security tile """

    def __init__(self, admin_console, title="Security"):
        """Method to initialize RSecurity"""
        super().__init__(admin_console, title)
        self.__admin_console = admin_console

    def get_details(self, show_hidden: bool = False) -> dict:
        """Return Security information on a tile in key value format

        Args:
            show_hidden (bool)  : get details about the hidden/inherited associations as well

        Returns:
              Dict: user and roles pair
              Example:
                    {
                    "user1": ["master"]
                    "user2": ["View, Role1"]
                    }
        """
        from Web.AdminConsole.Components.table import Rtable

        table = Rtable(self.__admin_console, id='securityAssociationsTable')
        if show_hidden:
            self.open_hyperlink_on_tile("Show inherited association")

        table_data = table.get_table_data()

        security_association_dict = {}

        header = list(table_data.keys())

        for index, user in enumerate(table_data[header[0]]):
            if user in security_association_dict:
                security_association_dict[user].append(table_data[header[1]][index])
            else:
                security_association_dict[user] = [table_data[header[1]][index]]

        return security_association_dict


class DropDown:
    """ Class to handle isteven-multi-select drop down related operations """

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__driver = admin_console.driver

    @WebAction()
    def __get_drop_down_list(self):
        """get drop down list """
        drop_down_list = self.__driver.find_elements(By.XPATH, "//isteven-multi-select")
        return drop_down_list

    @WebAction()
    def __get_drop_down_by_id(self, drop_down_id):
        """ Method to get drop down based on id provided as input"""
        drop_down = None
        if self.__admin_console.check_if_entity_exists("xpath", f"//isteven-multi-select[@id='{drop_down_id}']"):
            drop_down = self.__driver.find_element(By.XPATH, f"//isteven-multi-select[@id='{drop_down_id}']")
        elif self.__admin_console.check_if_entity_exists("xpath", f"//cv-isteven-single-select[@id='{drop_down_id}']"):
            drop_down = self.__driver.find_element(By.XPATH, f"//cv-isteven-single-select[@id='{drop_down_id}']")
        else:
            drop_down = self.__driver.find_element(By.XPATH, f"//isteven-multi-select[@directive-id='{drop_down_id}']")
        return drop_down

    @WebAction()
    def __get_drop_down_by_label(self, drop_down_label):
        """ Method to get drop down based on label provided as input

            Args:

                drop_down_label     (str)       --  Dropdown item label

        """
        drop_down = self.__driver.find_element(By.XPATH, f"//isteven-multi-select[@item-label='{drop_down_label}']")
        return drop_down

    @WebAction()
    def __expand_drop_down(self, drop_down):
        """expand drop down """
        drop_down.click()

    @WebAction()
    def __select_none(self, drop_down):
        """click 'Select none' icon and de-select all values """
        if self.__admin_console.is_element_present(
                "//button//span[contains(text(), 'Select None')]", drop_down):
            elem = drop_down.find_element(By.XPATH,
                                          "//button//span[contains(text(), 'Select None')]")
            if elem.is_displayed():
                elem.click()

    @WebAction()
    def __select_all(self, drop_down):
        """click 'Select all' icon and select all values from drop down """
        if self.__admin_console.is_element_present(
                ".//div[@class='helperContainer ng-scope']/div[1]/button[1]", drop_down):
            drop_down.find_element(By.XPATH,
                                   ".//div[@class='helperContainer ng-scope']/div[1]/button[1]").click()

    @WebAction()
    def __search_entity(self, drop_down, entity):
        """search for an entity """
        if self.__admin_console.is_element_present(
                ".//div[@class='line-search']", drop_down):
            if '\\' in entity:
                header, sep, value = entity.partition('\\')
                drop_down.find_element(By.XPATH,
                                       ".//div[@class='line-search']/input").send_keys(header)
            else:
                drop_down.find_element(By.XPATH,
                                       ".//div[@class='line-search']/input").send_keys(entity)

    @WebAction()
    def __select_entity(self, drop_down, entity, partial_selection=False):
        """click on entity to be selected"""
        if '\\' in entity:
            header, sep, value = entity.partition('\\')
            if not drop_down.find_element(By.XPATH,
                                          f".//*[contains(text(),'{header}') and "
                                          f"contains(text(), '{value}')]/..").get_attribute('checked'):
                drop_down.find_element(By.XPATH,
                                       f".//*[contains(text(),'{header}') and contains(text(), '{value}')]/..").click()
        else:
            if partial_selection:
                if not drop_down.find_element(By.XPATH,
                                              f".//div[@class='checkBoxContainer']//*[contains(text(),'{entity}')]"
                                              "/ancestor::label/input").get_attribute("checked"):
                    elem = drop_down.find_element(By.XPATH,
                                                  f".//div[@class='checkBoxContainer']//*[contains(text(),'{entity}')]")
                    self.__driver.execute_script("arguments[0].scrollIntoView();", elem)
                    elem.click()
            else:
                if not drop_down.find_element(By.XPATH,
                                              f".//div[@class='checkBoxContainer']//*[text()='{entity}']"
                                              "/ancestor::label/input").get_attribute("checked"):
                    elem = drop_down.find_element(By.XPATH,
                                                  f".//div[@class='checkBoxContainer']//*[text()='{entity}']")
                    self.__driver.execute_script("arguments[0].scrollIntoView();", elem)
                    elem.click()

    @WebAction()
    def __deselect_entity(self, drop_down, entity):
        """click on entity to be deselected"""

        if drop_down.find_element(By.XPATH,
                                  f".//div[@class='checkBoxContainer']//*[contains(text(),'{entity}')]"
                                  "/ancestor::label/input").get_attribute("checked"):
            elem = drop_down.find_element(By.XPATH,
                                          f".//div[@class='checkBoxContainer']//*[contains(text(),'{entity}')]")
            self.__driver.execute_script("arguments[0].scrollIntoView();", elem)
            elem.click()

    @WebAction()
    def __clear_search_bar(self, drop_down):
        """clear search bar """
        if self.__admin_console.is_element_present(
                ".//div[@class='line-search']/button", drop_down):
            if drop_down.find_element(By.XPATH,
                                      ".//div[@class='line-search']/button").is_displayed():
                drop_down.find_element(By.XPATH,
                                       ".//div[@class='line-search']/button").click()

    @WebAction()
    def __collapse_drop_down(self, drop_down):
        """ Collapse drop down """

        if 'show' in drop_down.find_element(By.XPATH,
                                            ".//div[contains(@class,'checkboxLayer')]").get_attribute('class'):
            if self.__admin_console.is_element_present(
                    ".//div[@class='line-search']/following-sibling::div", drop_down):
                drop_down.find_element(By.XPATH,
                                       ".//div[@class='line-search']/following-sibling::div").click()
            else:
                drop_down.click()

    @WebAction()
    def __deselect_default_value(self, dropdown):
        """
        deselect the the first value which is by selected by default
        the first if statement is empty to check for the search bar
        """
        self.__admin_console.unswitch_to_react_frame()
        list_elements = dropdown.find_elements(By.XPATH,"//div[@class='checkBoxContainer']/div[contains(@class,"
                                                        "'selected')]//span")
        if list_elements and len(list_elements) > 0:
            list_elements[0].click()

    @WebAction()
    def __check_multiselect(self, dropdown) -> bool:
        """Checks to see whether the dropdown is in multiple selection mode or single selection mode"""
        return 'single' not in [dropdown.get_attribute('data-selection-mode'),
                                dropdown.get_attribute('selection-mode')]

    @PageService(react_frame=False)
    def select_drop_down_values(
            self, index=None, values=None,
            select_all=None, drop_down_id=None, partial_selection=False, default_unselect=True, drop_down_label=None):
        """
        select values from drop down

        Args:
            index (int) : order of drop down in the sequence of display on page (starting from 0)

            values (list) : values to be selected from drop down

            select_all (bool) : boolean value to select all values from drop down

            drop_down_id (str) : id of the drop down tag 'isteven-multi-select'

            partial_selection (bool) : flag to determine if dropdown values should be
            selected in case of partial match or not

                    default: False (partial match is disabled by default)

            default_unselect  (bool)  :   flag to determine whether we have to unselect the value in
                                            dropdown which is selected by default


        """

        if index is not None:
            drop_down_list = self.__get_drop_down_list()
            drop_down = drop_down_list[index]
        elif drop_down_id is not None:
            drop_down = self.__get_drop_down_by_id(drop_down_id)
        elif drop_down_label is not None:
            drop_down = self.__get_drop_down_by_label(drop_down_label)
        else:
            raise Exception("Please provide either index or id of the drop down to be handled here")

        self.__expand_drop_down(drop_down)
        if select_all:
            self.__select_all(drop_down)
            self.__collapse_drop_down(drop_down)
        else:
            self.__select_none(drop_down)
            if self.__check_multiselect(drop_down) and default_unselect:
                self.__deselect_default_value(drop_down)
            for value in values:
                self.__search_entity(drop_down, value)
                self.__select_entity(drop_down, value, partial_selection)
                self.__clear_search_bar(drop_down)
            try:
                self.__collapse_drop_down(drop_down)
            except:
                # To handle the case where dropdown is removed from DOM after option selection
                pass
        self.__admin_console.wait_for_completion()

    @PageService()
    def deselect_drop_down_values(self, index, values):
        """
        deselect values from drop down

        Args:
            index (int) : order of drop down in the sequence of display on page (starting from 0)

            values (list) : values to be deselected from drop down

        """

        drop_down_list = self.__get_drop_down_list()
        self.__expand_drop_down(drop_down_list[index])

        for value in values:
            self.__search_entity(drop_down_list[index], value)
            self.__deselect_entity(drop_down_list[index], value)
            self.__clear_search_bar(drop_down_list[index])
        self.__collapse_drop_down(drop_down_list[index])

        self.__admin_console.wait_for_completion()

    def get_values_of_drop_down(self, id):
        """
        Returns the values in a drop down next to the provided label value.

        Args:
            id   (str)   --  Id of the label corresponding to the drop down.

        """
        drop_down = self.__get_drop_down_by_id(id)
        drop_down.click()
        values = drop_down.text.split('\n')
        self.__collapse_drop_down(drop_down)
        return values

    def get_values_of_drop_down_by_index(self, index):
        """
        Returns the values in a drop down by accessing drop down using index.

        Args:
            index   (int)   --  index of the drop down.
        """
        drop_down_list = self.__get_drop_down_list()
        drop_down = drop_down_list[index]
        drop_down.click()
        values = drop_down.text.split('\n')
        self.__collapse_drop_down(drop_down)
        return values


class RDropDown:
    """ Class to handle React drop-down component related operations """

    def __init__(self, admin_console, base_element=None):
        """ Initialize the ReactDropDown object

            Args:
                admin_console : instance of AdminConsoleBase

        """
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__base_element = base_element

    @WebAction()
    def __get_drop_down_list(self):
        """get drop down list present in the page"""
        drop_down_list = self.__driver.find_elements(By.XPATH, "//div[contains(@class, 'dd-form-control')]")
        if self.__base_element:
            drop_down_list = self.__base_element.find_elements(By.XPATH, ".//div[contains(@class, 'dd-form-control')]")
        return drop_down_list

    @WebAction()
    def __get_drop_down_values_list(self, drop_down):
        """ Method to get the values of the drop down"""
        items = drop_down.find_elements(By.XPATH, "//ul//li[contains(@class, 'dd-list-item')]")
        return [item.text.split("\n")[0] for item in items]

    @WebAction()
    def __get_drop_down_by_id(self, drop_down_id) -> WebElement:
        """ Method to get drop down based on id provided as input"""
        drop_down = self.__driver.find_element(By.XPATH,
                                               f"//div[@id='{drop_down_id}']//ancestor::div[contains(@class, 'dd-form-control')]")
        if self.__base_element:
            drop_down = self.__base_element.find_element(By.XPATH,
                                                         f".//div[@id='{drop_down_id}']//ancestor::div[contains(@class, 'dd-form-control')]")
        return drop_down

    @WebAction()
    def __get_drop_down_by_label(self, drop_down_label) -> WebElement:
        """ Method to get drop down based on label provided as input"""
        drop_down = self.__driver.find_element(By.XPATH,
                                               f"//label[text()='{drop_down_label}']//ancestor::div[contains(@class, 'dd-form-control')]")
        if self.__base_element:
            drop_down = self.__base_element.find_element(By.XPATH,
                                                f".//label[text()='{drop_down_label}']//ancestor::div[contains(@class, 'dd-form-control')]")
        return drop_down

    @PageService()
    def is_dropdown_exists(self, drop_down_id=None, drop_down_label=None):
        """
        Checks whether the dropdown exists
        Args:
            drop_down_id (str) - id if the dropdown
            drop_down_label (str) - label of the dropdown
        """

        elem = None
        if drop_down_id:
            elem = f"//div[@id='{drop_down_id}']"
        elif drop_down_label:
            elem = f"//label[text()='{drop_down_label}']"
        else:
            raise Exception(
                "Please provide either index or id or label of the drop down to be handled here")

        try:
            self.__driver.find_element(By.XPATH,
                                       f"{elem}//ancestor::div[contains(@class, 'dd-form-control')]")

            if self.__base_element:
                self.__base_element.find_element(By.XPATH,
                                                 f".{elem}//ancestor::div[contains(@class, 'dd-form-control')]")

            return True
        except NoSuchElementException:
            return False

    @WebAction()
    def __drop_down_expanded(self, drop_down):
        """Method to check if dropdown is expanded"""
        try:
            aria_expanded = drop_down.find_element(By.XPATH, ".//div[contains(@class, 'MuiSelect')]").get_attribute(
                'aria-expanded')
            return aria_expanded is not None and 'true' in aria_expanded
        except (StaleElementReferenceException, WebDriverException, NoSuchElementException):
            return False

    @WebAction()
    def __expand_drop_down(self, drop_down):
        """ Expand drop down """
        if not self.__drop_down_expanded(drop_down):
            drop_down.click()

    @WebAction()
    def __collapse_drop_down(self, drop_down):
        """ Collapse drop down """
        try:
            if self.__drop_down_expanded(drop_down):
                if self.__check_multiselect(drop_down):
                    try:
                        drop_down.find_element(By.TAG_NAME, 'svg').send_keys(Keys.SPACE)
                    except (AssertionError, ElementNotInteractableException):
                        time.sleep(3)
                ActionChains(self.__driver).send_keys(Keys.TAB).perform()
                ActionChains(self.__driver).send_keys(Keys.ESCAPE).perform()
                if self.__drop_down_expanded(drop_down):
                    self.__driver.find_element(By.TAG_NAME, 'body').click()
        except (StaleElementReferenceException, WebDriverException):
            return

    @WebAction()
    def __select_all(self, drop_down):
        """ Picks all the item in the drop down from multi select drop down """
        if self.__admin_console.is_element_present('.//div/button[text()="Select all"]', drop_down):
            drop_down.find_element(By.XPATH, './/div/button[text()="Select all"]').click()
        else:
            all_items = self.__get_drop_down_values_list(drop_down)
            for item in all_items:
                self.__select_entity(drop_down, item)

    @WebAction()
    def __select_none(self, drop_down):
        """ Unpicks all the item in the drop down from multi select drop down """
        reset_xpath = './/button[contains(@id,"DropdownSelectNone")] | .//button/div[text()="Reset"]'
        select_none_xpath = './/div/button[text()="Select none"]'
        if self.__admin_console.is_element_present(select_none_xpath, drop_down):
            drop_down.find_element(By.XPATH, select_none_xpath).click()
        elif self.__admin_console.is_element_present(reset_xpath, drop_down):
            drop_down.find_element(By.XPATH, reset_xpath).click()
        else:
            all_items = self.__get_drop_down_values_list(drop_down)
            for item in all_items:
                self.__deselect_entity(drop_down, item)

    @WebAction()
    def __search_entity(self, drop_down, entity):
        """ search for an entity if serach field is present"""
        if self.__admin_console.is_element_present(
                './/div/input[contains(@class, "MuiInputBase-inputTypeSearch")]', drop_down):
            drop_down.find_element(By.XPATH,
                                   './/div/input[contains(@class, "MuiInputBase-inputTypeSearch")]').send_keys(
                f'{entity}')
            self.__admin_console.wait_for_completion()

    @WebAction()
    def __clear_search_bar(self, drop_down):
        """ clear search bar is search field is present """
        if self.__admin_console.is_element_present(
                './/div/input[contains(@class, "MuiInputBase-inputTypeSearch")]', drop_down):
            drop_down.find_element(By.XPATH,
                                   './/div/input[contains(@class, "MuiInputBase-inputTypeSearch")]').send_keys(
                Keys.CONTROL + "a")
            drop_down.find_element(By.XPATH,
                                   './/div/input[contains(@class, "MuiInputBase-inputTypeSearch")]').send_keys(
                Keys.DELETE)

    @WebAction()
    def __check_multiselect(self, dropdown):
        """ Check to see whether the dropdown is in multiple selection mode or single selection mode"""
        try:
            # check if it is multiselect without opening the dropdown
            return 'multiple' in dropdown.find_element(By.XPATH,
                                                       ".//*[contains(@class, 'MuiSelect-select')]").get_attribute(
                'class')
        # In Dynamic dropdown, dropdown values will get populated only after doing
        # search. In that case, identify dropdown type based on role
        except NoSuchElementException:
            if dropdown.find_element(By.XPATH, "//ul[contains(@role, 'listbox') and contains(@class,'MuiMenu-list')]"):
                return True
            return False

    @WebAction()
    def __deselect_entity(self, drop_down, entity):
        """ click on entity to be deselected """

        if 'Mui-selected' in drop_down.find_element(By.XPATH,
                                                    f".//*[contains(text(),'{entity}')]//ancestor::li").get_attribute(
            'class'):
            drop_down.find_element(By.XPATH, f".//ul//li//*[contains(text(),'{entity}')]").click()

    @WebAction()
    def __select_entity(self, drop_down, entity, partial_selection=False, case_insensitive_selection=False):
        """ click on entity to be selected """
        entity_text = "text()"
        if case_insensitive_selection:
            entity_text = "translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"
            entity = entity.lower()

        if partial_selection:
            if 'Mui-selected' not in drop_down.find_element(By.XPATH,
                                                            f".//*[contains({entity_text},'{entity}')]//ancestor::li").get_attribute(
                'class'):
                drop_down.find_element(By.XPATH, f".//ul//li//*[contains({entity_text},'{entity}')]").click()
        else:
            if 'Mui-selected' not in drop_down.find_element(By.XPATH,
                                                            f".//*[contains({entity_text},'{entity}')]//ancestor::li").get_attribute(
                'class'):
                drop_down.find_element(By.XPATH, f".//ul//li//*[{entity_text}='{entity}']").click()

    @WebAction()
    def __select_entity_action(self, drop_down, entity, action, case_insensitive_selection=False):
        """ click on entity to be selected """
        entity_text = "text()"
        if case_insensitive_selection:
            entity_text = "translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')"
            entity = entity.lower()

        drop_down_element = drop_down.find_element(
            By.XPATH, f".//*[contains({entity_text},'{entity}')]//ancestor::li")
        action_element = drop_down_element.find_element(By.XPATH, f"//button[@title='{action}']")

        if not action_element:
            return False

        action_element.click()
        return True

    @WebAction()
    def __get_selected_values(self, drop_down):
        """ gets the list of selected values of dropdown """
        values_objects = drop_down.find_elements(By.XPATH, ".//ul//li[contains(@class, 'Mui-selected')]")
        return [value.text for value in values_objects]

    @WebAction()
    def __get_selected_values_without_expanding(self, drop_down: WebElement) -> list:
        """ gets the list of selected values of dropdown without expanding it"""
        if self.__check_multiselect(drop_down):
            chips_xpath = ".//*[contains(@class, 'Dropdown-deletableChip')]"
            return [chip.text for chip in drop_down.find_elements(By.XPATH, chips_xpath)]

        single_entry_xpath = ".//*[contains(@class, 'Dropdown-singleEntry')]"
        return [elem.text for elem in drop_down.find_elements(By.XPATH, single_entry_xpath)]

    @PageService()
    def __is_dropdown_disabled(self, dropdown):
        """ To check if the dropdown is disabled """
        dd_wrapper = dropdown.find_element(By.XPATH, ".//div[contains(@class, 'dd-wrapper')]")
        return 'Mui-disabled' in dd_wrapper.get_attribute('class')

    @PageService()
    def collapse_dropdown(self, drop_down_id: str = None, drop_down_label: str = None):
        """
        Collapses the given drop down

        Args:
            drop_down_id    (str)    --  Id of the label corresponding to the drop down.

            drop_down_label    (str)    --  label of the drop down.
        """
        if drop_down_id is not None:
            drop_down = self.__get_drop_down_by_id(drop_down_id)
        elif drop_down_label is not None:
            drop_down = self.__get_drop_down_by_label(drop_down_label)
        else:
            raise Exception(
                "Please provide either id or label of the drop down to be handled here")
        self.__collapse_drop_down(drop_down)

    @PageService()
    def get_values_of_drop_down(self, drop_down_id: str = None, drop_down_label: str = None, search: str = None):
        """
        Returns the values in a drop down next to the provided label value.

        Args:
            drop_down_id    (str)    --  Id of the label corresponding to the drop down.

            drop_down_label    (str)    --  label of the drop down.

            search          (str)   --  string to be searched in the dropdown before fetching the values

        Returns:

            values (list)   --  returns the list of elements present in the drop down

        """
        if drop_down_id is not None:
            drop_down = self.__get_drop_down_by_id(drop_down_id)
        elif drop_down_label is not None:
            drop_down = self.__get_drop_down_by_label(drop_down_label)
        else:
            raise Exception(
                "Please provide either id or label of the drop down to be handled here")
        self.__expand_drop_down(drop_down)
        if search:
            self.__clear_search_bar(drop_down)
            self.__search_entity(drop_down, search)
        values = self.__get_drop_down_values_list(drop_down)
        self.__collapse_drop_down(drop_down)
        return values

    @PageService()
    def get_selected_values(self, drop_down_id, expand=True) -> list:
        """
        Returns the list of selected values of the drop down.

        Args:
            drop_down_id    (str)    --  Id of the label corresponding to the drop down.
            expand          (bool)   --  get the values with / without expanding drop down

        Returns:

            values (list)   --  returns the list of elements selected in the drop down

        """
        drop_down = self.__get_drop_down_by_id(drop_down_id)
        if not expand:
            return self.__get_selected_values_without_expanding(drop_down)
        self.__expand_drop_down(drop_down)
        values = self.__get_selected_values(drop_down)
        self.__collapse_drop_down(drop_down)
        return values

    @PageService()
    def _get_dropdown_element(self, index=None, drop_down_id=None, drop_down_label=None):
        """
        get drop down

        Args:
            index (int) : order of drop down in the sequence of display on page (starting from 0)

                default: None

            drop_down_id (str) : id of the drop down tag 'dd-wrapper'

                default: None

            drop_down_label (str) : label of the dropdown

                default: None

        Returns:

            drop_down (WebElement)   --  returns the dropdown web element

        """
        drop_down = None
        if index is not None:
            drop_down_list = self.__get_drop_down_list()
            drop_down = drop_down_list[index]
        elif drop_down_id is not None:
            drop_down = self.__get_drop_down_by_id(drop_down_id)
        elif drop_down_label is not None:
            drop_down = self.__get_drop_down_by_label(drop_down_label)
        else:
            raise Exception(
                "Please provide either index or id or label of the drop down to be handled here")
        return drop_down

    @PageService()
    def select_drop_down_values(
            self, index=None, values=None, drop_down_label=None,
            select_all=False, drop_down_id=None, partial_selection=False, case_insensitive_selection=False,
            preserve_selection=False, facet=False, search_key=None):
        """
        select values from drop down

        Args:
            preserve_selection (Bool): preserve the string selection
            index (int) : order of drop down in the sequence of display on page (starting from 0)

                default: None

            values (list) : list of values to be selected from drop down

                default: None

            drop_down_label (str) : label of the drop down

                default: None

            select_all (bool) : boolean value to select all values from drop down

                default: False

            drop_down_id (str) : id of the drop down tag 'dd-wrapper'

                default: None

            partial_selection (bool) : flag to determine if dropdown values should be
            selected in case of partial match or not

                default: False (partial match is disabled by default)

            case_insensitive_selection (bool) : flag to determine if dropdown values selection
            should honor the case or not

                default: False (case insensitive selection is disabled by default)

            facet   (bool)  :   flag to determine if dropdown is in facet filter mode or not

                default: False (dropdown will be treated as normal react dropdown)

            search_key  (Callable)  :   a function object called with value as param, to generate search string
                                        for cases when a different string needs to be searched to get the value

        """

        drop_down = self._get_dropdown_element(index, drop_down_id, drop_down_label)
        drop_down.location_once_scrolled_into_view # sometimes fails when drop down not fully in view
        if not select_all and not values:
            raise Exception("Please provide either values list or set select all flag")
        if self.__is_dropdown_disabled(drop_down):
            self.__admin_console.log.info(f"Skipping the dropdown with id '{drop_down_id}' as it is disabled.")
            return
        self.__expand_drop_down(drop_down)
        if select_all:
            self.__select_all(drop_down)
        else:
            if self.__check_multiselect(drop_down) & (preserve_selection is False):
                self.__select_none(drop_down)
            for value in values:
                search_value = value
                if search_key:
                    search_value = search_key(value)
                self.__clear_search_bar(drop_down)
                self.__search_entity(drop_down, search_value)
                self.__admin_console.wait_for_completion()
                drop_down = self._get_dropdown_element(index, drop_down_id, drop_down_label)
                if facet:
                    self.__select_entity(self.__driver, value, partial_selection, case_insensitive_selection)
                else:
                    self.__select_entity(drop_down, value, partial_selection, case_insensitive_selection)
                self.__clear_search_bar(drop_down)
        self.__collapse_drop_down(drop_down)
        self.__admin_console.wait_for_completion()

    @PageService()
    def deselect_drop_down_values(self, values, drop_down_id=None, index=None):
        """
        deselect values from drop down

        Args:

            values       (list) : values to be deselected from drop down

            drop_down_id (str) : id of the drop down tag 'dd-wrapper'

                default: None

            index        (int) : order of drop down in the sequence of display
            on page (starting from 0)

                default: None

        """

        if index is not None:
            drop_down_list = self.__get_drop_down_list()
            drop_down = drop_down_list[index]
        elif drop_down_id is not None:
            drop_down = self.__get_drop_down_by_id(drop_down_id)
        else:
            raise Exception(
                "Please provide either index or id of the drop down to be handled here")
        self.__expand_drop_down(drop_down)
        for value in values:
            self.__search_entity(drop_down, value)
            self.__deselect_entity(drop_down, value)
            ActionChains(self.__driver).move_by_offset(0,0).perform()
            self.__clear_search_bar(drop_down)
        self.__collapse_drop_down(drop_down)
        self.__admin_console.wait_for_completion()

    @PageService()
    def wait_for_dropdown_load(self, drop_down_id):
        """
        Method to wait for dropdown list to load

        Args:
            drop_down_id    (str)    --  Id of the label corresponding to the drop down.

        """
        drop_down = self.__get_drop_down_by_id(drop_down_id)
        count = 12
        for _ in range(count):
            if "loading" in drop_down.text.lower():
                time.sleep(10)
            else:
                return
        raise CVWebAutomationException("Dropdown contents is taking more than 2 minutes for loading")

    @PageService()
    def select_dropdown_value_action(
            self, action, index=None, value=None,
            drop_down_label=None, drop_down_id=None, case_insensitive_selection=False):
        """Select action item from a dropdown value"""

        drop_down = self._get_dropdown_element(index, drop_down_id, drop_down_label)
        if self.__is_dropdown_disabled(drop_down):
            self.__admin_console.log.info(f"Skipping the dropdown with id '{drop_down_id}' as it is disabled.")
            return
        self.__expand_drop_down(drop_down)
        if self.__check_multiselect(drop_down):
            self.__select_none(drop_down)

        self.__clear_search_bar(drop_down)
        self.__search_entity(drop_down, value)
        self.__admin_console.wait_for_completion()
        drop_down = self._get_dropdown_element(index, drop_down_id, drop_down_label)
        result = self.__select_entity_action(drop_down, value, action, case_insensitive_selection)
        self.__clear_search_bar(drop_down)
        self.__collapse_drop_down(drop_down)
        self.__admin_console.wait_for_completion()

        if not result:
            raise CVWebAutomationException(f"Could not select action [{action}] on dropdown value [{value}]")

    def __get_element(self, xpath: str) -> WebElement:
        """Method to get web element from xpath

        Args:
            xpath (str): xpath to get the element

        Returns:
            WebElement object having given xpath
        """

        # TODO: This method is going to go in some common file which would take a base xpath and xpath to select
        #       and then return the element
        element = self.__driver.find_element(By.XPATH, xpath)
        return element

    @WebAction()
    def __expand_search_and_select(self, label: str = None, id: str = None) -> None:
        """Method to expand the search drop down

        Args:
            label (str)         : label to search the drop down with
            id (str) [optional] : id for the dropdown
        """
        drop_down_element = self.__get_dropdown_element(label, id)
        drop_down_element.click()

    @WebAction()
    def __enter_search_value_and_select(self, value: str, id: str = None, label: str = None) -> None:
        """ Method to search for user group in user group input

        Args:
            id (str)       : id of the dropdown input
            value (str)    : value to be entered and selected in dropdown
        """
        if id:
            drop_down_input_xpath = f"//*[@id='{id}' and contains(@class, 'MuiInputBase-input')]"
        elif label:
            drop_down_input_xpath = f"//label[./text()='{label}']/following-sibling::div//span/ancestor::div[contains(@class, 'MuiInput-root')]//input"
        else:
            raise CVWebAutomationException("Please give label or id for the dropdown to select")
        search_box = self.__get_element(drop_down_input_xpath)
        search_box.send_keys(value)
        # wait for the suggestions to load
        time.sleep(3)

        dropdown_value_xp = f"//div[contains(@class, 'MuiAutocomplete-popper')]//*[contains(normalize-space(), '{value}')]"

        WebDriverWait(self.__driver, 30).until(
            ec.visibility_of_element_located((By.XPATH, dropdown_value_xp)))

        dd_value_element = self.__get_element(dropdown_value_xp)
        dd_value_element.click()

    @WebAction()
    def __check_if_drop_down_closed(self, drop_down_id):
        """
        Method to collapse the dropdown if not already
        """
        try:
            if self.__driver.find_element(By.XPATH, "//div[contains(@class,'MuiAutocomplete-popper')]"):
                self.__driver.find_element(By.XPATH, f'//input[@id = "{drop_down_id}"'
                                                     f' and contains(@class, "MuiInputBase-input")]').click()
        except NoSuchElementException:
            pass

    @PageService()
    def search_and_select(self, select_value: str, label: str = None, id: str = None) -> None:
        """
        Method to select a value from lazy load dropdowns (dropdown loads based on search)

        Args:
            select_value (str): Value to select from the search and select input
            label        (str): Label text of the label next to which the input
            id           (str) : ID of the select
        """

        if not label and not id:
            raise CVWebAutomationException("Please give label or id for the dropdown to select")

        self.__expand_search_and_select(label, id)
        self.__enter_search_value_and_select(select_value, id, label)
        self.__check_if_drop_down_closed(drop_down_id=id)
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __get_dropdown_element(self, label: str = None, id:str = None) -> WebElement:
        """Method to expand the search drop down

            Args:
                label (str)         : label to search the drop down with
                id (str) [optional] : id for the dropdown
        """
        if id:
            drop_down_input_xpath = (f"//*[@id='{id}' and contains(@class, 'MuiInputBase-input')]"
                                     f"/ancestor::div[contains(@class, 'AutoComplete-root ')]")
        elif label:
            drop_down_input_xpath = (f"//label[./text()='{label}']/following-sibling::div//span/"
                                     f"ancestor::div[contains(@class, 'AutoComplete-root ')]")
        else:
            raise CVWebAutomationException("Please give label or id for the dropdown to select")

        drop_down_element = self.__get_element(drop_down_input_xpath)

        return drop_down_element

    @WebAction()
    def __deselect_selections(self, value: str, dd_element: WebElement) -> None:
        """Method to deselect the selected selections in autocomplete dropdown"""
        xpath = (f".//div[contains(@class, 'MuiChip-deletable')]//span[normalize-space()='{value}']"
                 f"/../*[local-name()='svg']")

        dd_element.find_element(By.XPATH, xpath).click()

    @PageService()
    def deselect_auto_dropdown_values(self, value: str, label: str = None, id: str = None) -> None:
        """Method to remove selected values from dropdown element

        Not: This is to be used for dropdown elements with Mui-Autocomplete tag

        Args:
            value (str)     : Value to deselect from dropdown
            label (str)     : Label of dropdown
            id    (str)     : id of dropdown

        """
        if not label and not id:
            raise CVWebAutomationException("Please give label or id for the dropdown to deselect")

        dropdown_element = self.__get_dropdown_element(label, id)
        self.__deselect_selections(value, dropdown_element)


class RecoveryCalendar:
    """RecoveryCalendar Component used in Command Center"""
    def __init__(self, admin_console, base_xpath=""):
        """
        Initialize the RecoveryCalendar object

        Args:
            admin_console   : Instance of AdminConsoleBase

            base_xpath      : Base xpath under which calendar is located
        """
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self.__xp = base_xpath + "//div[@id='teer-calendar']"
        self.__month_abbr = {
            "january": "Jan",
            "february": "Feb",
            "march": "Mar",
            "april": "Apr",
            "may": "May",
            "june": "Jun",
            "july": "Jul",
            "august": "Aug",
            "september": "Sep",
            "october": "Oct",
            "november": "Nov",
            "december": "Dec"
        }

    @WebAction()
    def __select_year(self, year):
        """Method to select year"""
        if year:
            year_xpath = "//p[2]"
            self._driver.find_element(By.XPATH, self.__xp + year_xpath).click()
            self._driver.find_element(By.XPATH,
                                      f"//button[contains(@class,'MuiPickersYear-yearButton')"
                                      f" and text()='{year}']").click()
            self._admin_console.wait_for_completion()

    @WebAction()
    def __select_month(self, month):
        """Method to select month"""
        if month:
            month_xpath = "//p[1]"
            self._driver.find_element(By.XPATH, self.__xp + month_xpath).click()
            self._driver.find_element(By.XPATH,
                                      f"//button[contains(@class,'MuiPickersMonth-monthButton')"
                                      f" and text()='{self.__month_abbr[month.lower()]}']").click()
            self._admin_console.wait_for_completion()

    @WebAction()
    def __select_date(self, date):
        """Method to select date"""
        date_xpath = f"//div[@id='day-{date}-btn']"
        self._driver.find_element(By.XPATH, self.__xp + date_xpath).click()
        self._admin_console.wait_for_completion()

    @PageService()
    def select_date(self, date_time):
        """
           Picks the date from recovery calendar

           Args:
                date_time   (dict): Dict containing date to be set in recovery calendar

           Examples:
                    time_value:   {   'year':     2017,
                                       'month':    december,
                                       'date':     31 (required)
                                   }

        """
        self.__select_year(date_time.get("year"))
        self.__select_month(date_time.get("month"))
        self.__select_date(date_time.get("date"))
        self._admin_console.wait_for_completion()
