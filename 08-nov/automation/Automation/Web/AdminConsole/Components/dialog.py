""" Module for dialog panel

RModalDialog & ModalDialog are 2 classes defined in this file

ModalDialog:    Class to represent modal dialog window in admin console

RModalDialog:   Class to represent React Modal Dialog window in admin console.

ModalDialog:

    click_cancel()            :       Clicks Cancel button of the panel

    click_submit()            :       Clicks submit button of the panel (doesnt matter about the text in it)

    title()                   :       Returns the title of the modal dialog window

    get_details()             :       Returns the details present in modal body

    type_text_and_delete()    :       Types the text on modal window and clicks Delete

    get_text()                :       Retrieve message text from Modal Dialog

    get_messagebox_text()     :       Retrieve the text from the message box

    check_toggle_status       :       Checks if toggle is enabled or not in a dialog box (Credential Manager)

    enable_toggle             :       Enables toggle button in a dialog box (Credential Manager)

    disable_toggle            :       Disables the toggle button in a dialog box (Credential Manager)

    click_add_on_cred_manager :       Clicks the '+' button on credential manager dialog box

TransferOwnership
    transfer_ownership()      :       Method to transfer ownership to a user

CreateView
    add_rule()                :       Method to add rule to the opened view

    delete_rule()             :       Method to delete rule from the view

    submit()                  :       Method to submit the view by "Save" button

    create_view()             :       Method to create view and submit

RModalDialog:

    click_close()             :       Click close button in a react modal dialog

    click_cancel()            :       Clicks Cancel button of the panel

    click_add()                :      Clicks add icon on the panel

    click_submit()            :       Clicks submit button of the panel (doesnt matter about the text in it)

    title()                   :       Returns the title of the modal dialog window

    is_dialog_present()       :       Checks if this dialog is open and present in page

    fill_text_in_field()      :       Enter text in text field of the modal dialog

    get_text_in_field()       :       Returns the text that is present in text field

    select_dropdown_values()  :       Select values from dropdown in modal dialog

    get_selected_options()  :      Method to get selected elements in the search and select

    select_items()           :       Method to select the tale items inside a dialog

    browse_path()            :       Method to browse and select path inside a dialog

    click_button_on_dialog()  :       Method to click a button on a dialog using text

    select_radio_by_id()      :       Method to select the radio button by id

    select_radio_by_name()    :       Method to select radio button by name

    select_radio_by_value()    :       Method to select radio button by value

    click_action_item()       :       Method to select an action item from the actions menu in the modal dialog

    select_checkbox()         :         Selects checkbox that matches the ID

    click_yes_button()         :        Click Yes button in a react modal dialog

    click_preview_button()     :       Click preview button in react modal dialog

    click_save_button()        :        Click Save button in a react modal dialog

    click_redirect_options()   :        Click redirect options button in a react modal dialog

    get_preview_details()      :        Returns the details present in preview modal body

    enable_notify_via_email():         Enables notify via email checkbox

    disable_notify_via_email():        Disables notify via email checkbox

    upload_file()           :       Input absolute path of the file to be uploaded
    
    copy_content_of_file_from_dialog() : Method to copy the content of a file view from a dialog

    click_icon_by_title()              : Method to click on icon by title

RTransferOwnership
    transfer_ownership()      :       Method to transfer ownership to a user

RSecurity
    edit_security_association()     :       Method to edit security association from entity details page

    get_security_associations()     :       Method to read and return the security associations displayed

    add_associated_entities()       :       Method to add associated entities from user / usergroup details page

    laptop_plan_select_user()       :       Method to select user or user group from the search result in the Associate
                                            users or user groups dialog box in the laptop plan details page

RBackup:

    set_backup_level()                   :       Sets backup type

    enable_notify_via_email()            :       Enables notify via email checkbox

    select_backupset_and_subclient()     :       Selects the required backupset and subclient

    submit_backup()                      :       Submits backup job in the panel

ServiceCommcellSelectionDialog:

    available_commcells()               :   gets the available commcells in dropdown

    select_commcell()                   :   selects the given commcell from dropdown

TagsDialog: Class to handle Manage Tags dialog window

    is_dialog_present()                 :   checks if dialog is already open

    get_tags()                          :   gets the tags data from dialog

    delete_tag()                        :   deletes given tag

    add_tag()                           :   adds the given tag

SecurityDialog: Class to handle angular security dialog window

    is_dialog_present()                 :   checks if dialog is already open

    get_user_role_associations()        :   gets the user role associations

    get_usergroup_role_associations()   :   gets the usergroup role associations

    remove_association()                :   deletes the given user, role association

    add_association()                   :   adds the given user, role association

ServiceCommcellAssociationsDialog: Class to handle angular associations dialog in service commcells page

    is_dialog_present()                 :   checks if dialog is already open

    get_user_suggestions()              :   gets the suggestions from dropdown for given term

    available_commcells()               :   gets the commcells available for associations in dropdown

    add_association()                   :   associates the given entity to commcells

    get_associations()                  :   gets the associations listed in dialog

    delete_association()                :   deletes the association for given entity to all service commcells

"""
import os
from time import sleep
from typing import List

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, WebDriverException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.panel import RDropDown, DropDown
from Web.AdminConsole.Components.table import Table, Rtable
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Components.core import Toggle, Checkbox, TreeView
from enum import Enum


class ModalDialog:
    """ Modal class """

    def __init__(self, admin_console):
        """ Initialize the backup object

        Args:
            admin_console: instance of AdminConsoleBase

        """
        self._driver = admin_console.driver
        self._adminconsole_base = admin_console

    @WebAction()
    def click_submit(self, submit_type=False):
        """ Clicks submit button of the panel doesnt matter about the text in it

            Args:

                submit_type     (bool)      --  Button is of type 'submit' or not
        """
        type_str = 'and @type="submit"'
        btn_xpath = f"//div[contains(@class, 'modal-content')]//button[contains(@class, 'btn btn-primary') and not(contains(@class,'ng-hide')){type_str if submit_type else ''}]"
        if submit_type:
            self._driver.find_element(By.XPATH, btn_xpath).click()
        else:
            self._driver.find_element(By.XPATH, btn_xpath).click()

    @WebAction()
    def click_cancel(self):
        """ Clicks Cancel button of the panel"""
        self._driver.find_element(By.XPATH,
                                  "//div[contains(@class, 'modal-content')]//button[contains(@class, 'btn btn-default')]"
                                  ).click()

    @WebAction()
    def type_text_and_delete(self, text_val, checkbox_id=None, button_name="Delete", button_id=None):
        """
            Types the text on popup and clicks Delete

            Args:
                text_val (basetring)        : Text to be entered
                checkbox_id (str)    : Id of the checkbox that has to be selected
                button_name (str)    : Name of the button

            """
        if self._adminconsole_base.check_if_entity_exists(
                "xpath", "//div[@class= 'modal-content']"):
            elem = self._driver.find_element(By.XPATH, "//div[contains(@class, 'form-group')]//input")
            elem.clear()
            elem.send_keys(text_val)
            if self._adminconsole_base.check_if_entity_exists("xpath", f"//*[@id = '{checkbox_id}']"):
                self._adminconsole_base.checkbox_select(checkbox_id)
            if button_id:
                self._adminconsole_base.click_button_using_id(button_id)
            else:
                self._adminconsole_base.click_button_using_text(button_name)

    @WebAction(delay=0)
    def __read_title(self):
        """Reads Modal panel title"""
        return self._driver.find_element(By.XPATH, "//div[@class='modal-content']//h1").text

    @PageService()
    def title(self):
        """Returns the title of panel"""
        return self.__read_title()

    @WebAction()
    def __modal_details(self):
        """ Retrieves modal details

        Returns :
            (list) : all visible tags containing text or toggle

        """
        info_xp = "//span[contains(@class, 'pageDetailColumn')]"
        tags = self._driver.find_elements(By.XPATH, info_xp)
        return [each_tag for each_tag in tags if each_tag.is_displayed()]

    @PageService()
    def get_details(self):
        """ Gets all the information contained in the modal

        Returns :
            details (dict) : Details of the modal in key value pair

        """
        details = {}
        tags = self.__modal_details()
        tag_count = 0
        key = None
        value = None
        for each_tag in tags:
            tag_count += 1
            if tag_count % 2 != 0:
                key = each_tag.text
            else:
                value = each_tag.text
            details.update({key: value})
        return details

    @WebAction()
    def __read_body_text(self):
        """
        Read text from body of Modal Dialog

        Returns:
            (str)           : Text contained inside Modal Body
        """
        return self._driver.find_element(By.XPATH, "//div[contains(@class, 'modal-body')]").text

    @PageService()
    def get_text(self):
        """
        Retrieve message text from Modal Dialog

        Returns:
            (str)           : Message text
        """
        return self.__read_body_text()

    @PageService()
    def get_messagebox_text(self):
        """
            Method to get the text displayed in the message box for a Dialog panel
        """
        _msg_xpath = "//div[contains(@data-ng-class, 'messageBoxClass')]/span/h5"
        _message = self._driver.find_element(By.XPATH, _msg_xpath).text
        return _message

    @WebAction()
    def check_toggle_status(self, label, preceding_label=False):
        """
        Checks toggle status for Modal dialog box(Credential Manager)

        Args:
            label           :  label corresponding to the toggle

            preceding_label :  If the position of the label is preceding, use preceding-sibling tag

        Returns:
            (bool)          :  True if toggle enabled, else false
        """

        toggle_control_xpath = 'preceding-sibling' if preceding_label else 'following'
        return 'enabled' in self._driver.find_element(By.XPATH,
                                                      f"//*[contains(text(), '{label}')]/{toggle_control_xpath}::toggle-control/div"
                                                      ).get_attribute('class')

    @WebAction()
    def __click_toggle(self, label, preceding_label=False):
        """
        Clicks toggle button on Modal Dialog(Credential Manager)

        Args:
            label           :  label corresponding to the toggle

            preceding_label :  If the position of the label is preceding, use preceding-sibling tag
        """
        toggle_control_xpath = 'preceding-sibling' if preceding_label else 'following'
        xpath_toggle = f"//*[contains(text(), '{label}')]/{toggle_control_xpath}::toggle-control"
        self._driver.find_element(By.XPATH, xpath_toggle).click()

    @WebAction()
    def __click_add_btn(self):
        """Clicks the '+' add button on the Credential Manager dialog box"""
        xpath_add_btn = "//span[@title = 'Add']/ancestor::span[@class='input-group-btn']"
        self._driver.find_element(By.XPATH, xpath_add_btn).click()

    @PageService()
    def enable_toggle(self, label, preceding_label=False):
        """
        Enables toggle button on Modal Dialog(Credential Manager) if not already enabled

        Args:
            label           :  label corresponding to the toggle

            preceding_label :  If the position of the label is preceding, use preceding-sibling tag
        """
        if not self.check_toggle_status(label, preceding_label):
            self.__click_toggle(label, preceding_label)

    @PageService()
    def disable_toggle(self, label, preceding_label=False):
        """
        Disables toggle button on Modal Dialog(Credential Manager) if not already disabled

        Args:
            label           :  label corresponding to the toggle

            preceding_label :  If the position of the label is preceding, use preceding-sibling tag
        """
        if self.check_toggle_status(label, preceding_label):
            self.__click_toggle(label, preceding_label)

    @PageService()
    def click_add_on_cred_manager(self):
        """Clicks the add button ('+') on credential manager dialog box"""
        self.__click_add_btn()
        self._adminconsole_base.wait_for_completion()

    @WebAction()
    def __enter_name(self, entity):
        """
        search the entity from the drop-down
        Args:
            entity(str): name of the entity to be searched
        """
        input_boxes = self._driver.find_elements(By.XPATH, "//div[@class='select2-search']/input")
        for box in input_boxes:
            if box.is_displayed():
                box.send_keys(entity)

    @WebAction()
    def __select_entity(self, entity):
        """
        selects the entity from the drop-down
        Args:
            entity(str): name of the entity to be selected
        """
        self._driver.find_element(By.XPATH,
                                  f"//*[contains(@id,'select2-result')] /div[contains(text(),'{entity}')]").click()

    @PageService()
    def add_association(self, entity):
        """
        method to add association from select2_drop drop-down
        Args:
            entity(str): name of the entity
        """
        self.__enter_name(entity)
        self.__select_entity(entity)


class TransferOwnership(ModalDialog):
    """ Class for Transfer Ownership dialog"""

    @WebAction()
    def __search_new_owner(self, owner_transfer):
        """ Method to search for new owner in transfer ownership/Confirm Delete pop-up """
        search_box = self._driver.find_element(By.XPATH,
                                               "//div[contains(@class,'modal-body')]//input[@name='searchComponent']")
        search_box.send_keys(owner_transfer)

    @WebAction()
    def __select_new_owner(self, owner_transfer):
        """ Method to select new owner from Transfer ownership pop-up """
        search_results = self._driver.find_element(By.XPATH,
                                                   "//div[contains(@class,'modal-body')]//ul[contains(@class,'results-container')]")
        search_results.find_element(By.XPATH, f".//h5[text()='{owner_transfer}']").click()

    @PageService()
    def transfer_ownership(self, owner_transfer):
        """
        Method to transfer ownership to a user

        Args:
            owner_transfer (str): User to which ownership has to be transferred

        Raises:
            Exception:
                If there is no option to transfer owner
        """
        if owner_transfer:
            self.__search_new_owner(owner_transfer)
            self._adminconsole_base.wait_for_completion()
            self.__select_new_owner(owner_transfer)
        self.click_submit()
        self._adminconsole_base.check_error_message()
        self._adminconsole_base.wait_for_completion()


class CreateView(ModalDialog):
    """Class for create view dialog in Job history page"""

    @WebAction()
    def __get_last_row_id_no(self):
        """Method to return the last rule's row element id"""
        column_select = self._driver.find_elements(By.XPATH,
                                                   '//ul[@class="list-inline ng-scope"]//select[contains(@class,"rule-column-name")]')[
            -1]
        return column_select.get_attribute("id")[5:]

    @WebAction()
    def __fill_dropdown_form(self, id_no, value):
        """Method to search value and select it from drop down"""
        dd_input = self._driver.find_element(By.XPATH,
                                             f'//*[@id="ruleFilter-{id_no}_wrapper"]/div//input'
                                             )
        dd_input.send_keys(value)
        self._adminconsole_base.wait_for_completion()
        filter_item_checkbox = f"//*[@id='ruleFilter-{id_no}_listbox']/li/label[text()='{value}']"
        self._driver.find_element(By.XPATH, filter_item_checkbox).click()
        self._adminconsole_base.wait_for_completion()
        self._driver.find_element(By.XPATH, "//h1[text()='Create view']").click()  # remove focus from drop down

    @WebAction()
    def add_rule(self, column, value):
        """Method to add new rule with column filter and value"""
        self._driver.find_element(By.XPATH, f"//button[contains(.,'Add rule')]").click()
        self._adminconsole_base.wait_for_completion()
        id_no = self.__get_last_row_id_no()

        self._adminconsole_base.select_value_from_dropdown(f"rule-{id_no}", column)
        if column not in ["Instance", "Backup set", "Subclient", "Plan", "Company", "Total number of files",
                          "Error description", "Error code"]:
            self.__fill_dropdown_form(id_no, value)
        else:
            self._adminconsole_base.fill_form_by_id(f"ruleFilter-{id_no}", value)
        self._adminconsole_base.wait_for_completion()

    @WebAction()
    def delete_rule(self, index):
        """Method to delete Nth rule from top where N is the index"""
        cross = self._driver.find_elements(By.XPATH, '//ul[@class="list-inline ng-scope"]//li[@class="ng-scope"]')[
            index]
        cross.click()
        self._adminconsole_base.wait_for_completion()

    @PageService()
    def submit(self):
        """Method to submit the panel"""
        self._adminconsole_base.click_button_using_text("Save")
        self._adminconsole_base.wait_for_completion()
        self._adminconsole_base.check_error_message()
        self._adminconsole_base.wait_for_completion()

    @PageService()
    def create_view(self, view_name, rules, set_default=False):
        """
        Creates a new view by adding rules and submitting the panel
        Args:
            view_name: Name of the view to be created
            rules: A dictionary of rules in the form of {<column-name>: <value>}
                    eg: {'Operation': 'Backup'}
                    rule conditions are left as default i.e. contains, equals..
            set_default: Sets the view as default
        """
        self._adminconsole_base.click_by_xpath('//*[@id="grid-context-menu-container"]')
        self._adminconsole_base.select_hyperlink("Create view")
        self._adminconsole_base.fill_form_by_id("viewName", view_name)
        if set_default:
            self._adminconsole_base.checkbox_select("chkSetAsDefault")
        self.delete_rule(0)
        for key in rules:
            self.add_rule(key, rules[key])
        self.submit()


class RModalDialog:
    """ React Modal class """

    def __init__(self, admin_console, title=None, xpath=None):
        """ Initialize the React Modal Dialog Class

        Args:
            admin_console: instance of AdminConsoleBase

            xpath        : base xpath
        """
        self._driver = admin_console.driver
        self._adminconsole_base = admin_console
        self._dropdown = RDropDown(admin_console)
        self._admin_console = admin_console
        self._title = title
        if title:
            self._dialog_xp = f"(//*[contains(@class,'mui-modal-title') and normalize-space()='{title}']" \
                              f"//ancestor::div[contains(@class, 'mui-modal-dialog')] " \
                              f"| //*[normalize-space()='{title}']//ancestor::div[@class='confirm-container']/div)"
        elif xpath:
            self._dialog_xp = xpath
        else:
            self._dialog_xp = "(//div[contains(@class, 'mui-modal-dialog mui-modal-centered')] " \
                              "| //div[contains(@class, 'confirm-container')]/div" \
                              "| //div[@aria-labelledby ='customized-dialog-title'])"

        self.__toggle = Toggle(admin_console, self._dialog_xp)
        self.__checkbox = Checkbox(admin_console, self._dialog_xp)
        self.__base_element = None

    @WebAction()
    def is_dialog_present(self):
        """
        Checks if the Tags dialog is already open/closed or another dialog is open

        Returns:
            bool    -   True if this dialog is open in browser, else false
        """
        try:
            current_title = self.title()
            if self._title and current_title != self._title:
                raise CVWebAutomationException("A different dialog is open!")
            else:
                return True  # since we don't know what title is expected,
                # just return True since some title was read successfully
        except NoSuchElementException:
            return False

    @property
    def base_xpath(self):
        """
        Returns the base xpath of the dailog
        """
        return self._dialog_xp

    @property
    def toggle(self):
        """Returns instance of toggle class"""
        return self.__toggle

    @WebAction()
    def __enable_notify_via_email(self):
        """ Enables notify via email checkbox """
        if not self.__is_notify_via_email_enabled():
            self._driver.find_element(By.XPATH, "//*[@id='notifyUser'] | //*[@id='notifyUserOnJobCompletion']").click()

    @WebAction()
    def __disable_notify_via_email(self):
        """ disables notify via email checkbox """
        if self.__is_notify_via_email_enabled():
            self._driver.find_element(By.XPATH, "//*[@id='notifyUser'] | //*[@id='notifyUserOnJobCompletion']").click()

    @WebAction()
    def __is_notify_via_email_enabled(self):
        """ method to check if Notify checkbox is enabled"""
        xpath = "(*//input[contains(@id,'notifyUser')] | *//input[contains(@id,'notifyUserOnJobCompletion')])" \
                "/parent::span[contains(@class,'Mui-checked')]"
        return self._admin_console.check_if_entity_exists("xpath", xpath)

    @property
    def checkbox(self):
        """Returns instance of checkbox class"""
        return self.__checkbox

    def __get_base_element(self):
        """Get Base element for dialog component"""
        elems = self._driver.find_elements(By.XPATH, self._dialog_xp)
        if not elems:
            raise NoSuchElementException(f"No Dialog with xpath: {self._dialog_xp} found")

        for elem in elems:
            if elem.size['height'] > 0:
                self.__base_element = elem
                break

        if not self.__base_element:
            raise NoSuchElementException("No open base element found for modal dialog")

    @WebAction()
    def _get_element(self, xpath: str) -> WebElement:
        """
        Sets the base element if not already set and gets the element corresponding to xpath
        from the base element

        Args:
           xpath (str): xpath of the element to be found

        Returns:
            WebElement: if element is found

            Raises Exception if element is not found
        """
        if not self._dialog_xp or self._dialog_xp == ' ':
            self.__base_element = self._driver
            element = self.__base_element.find_element(By.XPATH, xpath)
        else:
            if not self.__base_element:
                self.__get_base_element()
            try:
                element = self.__base_element.find_element(By.XPATH, xpath)
            except (StaleElementReferenceException, WebDriverException, NoSuchElementException):
                self.__get_base_element()
                element = self.__base_element.find_element(By.XPATH, xpath)
            except Exception as excep:
                raise excep

        return element

    @WebAction()
    def _get_elements(self, xpath: str) -> List[WebElement]:
        """
        Sets the base element if not already set and gets the elements corresponding to xpath
        from the base element

        Args:
           xpath (str): xpath of the element to be found

        Returns:
            List[WebElement]: if elements are found

            Returns empty list
        """
        if not self._dialog_xp or self._dialog_xp == ' ':
            self.__base_element = self._driver
            element = self.__base_element.find_elements(By.XPATH, xpath)
        else:
            if not self.__base_element:
                self.__get_base_element()

            try:
                element = self.__base_element.find_elements(By.XPATH, xpath)
            except (StaleElementReferenceException, WebDriverException, NoSuchElementException):
                self.__get_base_element()
                element = self.__base_element.find_elements(By.XPATH, xpath)
            except Exception as excep:
                raise excep

        return element

    @WebAction()
    def __click_save(self):
        """ Clicks submit button of the panel doesnt matter about the text in it"""

        save_btn_xp = ".//span[contains(@class, 'positive-modal-btn')]//button" \
                      " | .//button[contains(@class, 'MuiButton-containedPrimary')]" \
                      " | .//button[@type='submit']"\
                      " | .//button[@id='Save']"

        self._get_element(save_btn_xp).click()

    @WebAction()
    def __click_preview_button(self):
        """Click Preview button in a react modal dialog """
        self._driver.find_element(By.XPATH,
                                  f"//button[contains(@class, 'MuiButton-root')]//div[text()='Preview']").click()
        self._adminconsole_base.wait_for_completion()

    @WebAction()
    def __click_yes_button(self):
        """Click Yes button in a react modal dialog """
        self._driver.find_element(By.XPATH,
                                  f"//button[contains(@class, 'MuiButton-root')]//div[text()='Yes']").click()

    @WebAction()
    def __click_save_button(self):
        """Click save button in react modal dialog """
        xpath = f"//button[contains(@class, 'MuiButton-root')]//div[text()='Save']"
        self._driver.find_element(By.XPATH, self._dialog_xp + xpath).click()

    @WebAction()
    def __click_redirect_options(self):
        """Click Redirect options button in react modal dialog """
        self._driver.find_element(By.XPATH,
                                  f"//button[contains(@class, 'MuiButton-root')]"
                                  f"//div[text()='Redirect' or text() = 'Redirect options' or text() = 'Redirect Path']").click()


    @WebAction()
    def __preview_details(self):
        """ Retrieves preview modal details

        Returns :
            (list) : all visible text

        """
        info_xp = "//div[contains(@class, 'CodeMirror-lines')]"
        tags = self._driver.find_elements(By.XPATH, info_xp)
        return [each_tag.text for each_tag in tags if each_tag.is_displayed()]

    @WebAction()
    def __click_cancel(self):
        """ Clicks Cancel button of the panel"""

        cancel_btn_xp = ".//span[contains(@class, 'modal-footer') " \
                        "and not(contains(@class, 'positive-modal-btn'))]" \
                        "//button[not(contains(@class, 'MuiButton-containedPrimary')) ]//ancestor::button"

        alt_cancel_btn_xp = ".//span[not(contains(@class,'positive-modal-btn'))]" \
                            "//button[contains(@class, 'MuiButton-outlined') and " \
                            "not(contains(@class, 'MuiButton-containedPrimary')) ]" \
                            "//div[text()!='Equivalent API']/ancestor::button"

        cancel_btn_xp_cc = ".//div[contains(@class, 'confirm-container')]" \
                           "//span[not(contains(@class, 'positive-modal-btn'))]//button"
        cancel_button_xpaths = [cancel_btn_xp, alt_cancel_btn_xp, cancel_btn_xp_cc]
        for xpath in cancel_button_xpaths:
            try:
                ele = self._get_element(xpath=xpath)
                ele.click()
                return
            except NoSuchElementException:
                pass
        raise NoSuchElementException()

    @WebAction()
    def __click_close(self):
        """ Method to click close on react modal (x) """
        xpath = "//button[@title='Close' or @aria-label='Close']"
        self.__click_element(self._dialog_xp + xpath)

    @WebAction()
    def __click_add(self):
        """ Method to click add on react modal (+) """
        xpath = "//button[@aria-label= 'Create new' or @aria-label='Add']"
        if self._adminconsole_base.check_if_entity_exists('xpath', self._dialog_xp + xpath):
            self._driver.find_element(By.XPATH, self._dialog_xp + xpath).click()

    @WebAction()
    def __click_element(self, xpath, is_entity_visible_only_on_hover=False):
        """ Method to click element on react modal (+)
        Args :
            xpath : xpath of the element to be clicked
            is_entity_visible_only_on_hover : flag to determine if element is visible only on hover
        """
        if is_entity_visible_only_on_hover:
            element = self._get_element(xpath)
            ActionChains(self._driver).move_to_element(element).click().perform()
        else:
            element = self._get_element(xpath)
            element.click()

    @WebAction()
    def __select_tab(self, tab_text):
        """
        clicks on tab inside Modal Dialog
        Args:
            tab_text: localized tab text
        """
        tab_xpath = f'//div[@role="tablist"]//span[text()="{tab_text}"]//ancestor::button'
        self._driver.find_element(By.XPATH, tab_xpath).click()

    @PageService()
    def click_yes_button(self):
        """Click yes button in react modal dialog"""
        self.__click_yes_button()

    @PageService()
    def click_preview_button(self):
        """Click preview button in react modal dialog"""
        self.__click_preview_button()

    @PageService()
    def click_save_button(self):
        """Click save button in react modal dialog """
        self.__click_save_button()

    @PageService()
    def click_redirect_options(self):
        """Click Redirect options button in react modal dialog """
        self.__click_redirect_options()

    @PageService()
    def get_preview_details(self):
        """ Gets all the information contained in the preview modal

        Returns :
            preview_script (list) : Preview script present in the modal

        """
        tags = self.__preview_details()
        preview_script = '\n'.join(tags)
        return preview_script

    @PageService()
    def click_close(self):
        """ Click close button in a react modal dialog """
        self.__click_close()
        self._adminconsole_base.wait_for_completion()

    @PageService()
    def click_submit(self, wait=True):
        """ Click submit button in a react modal dialog """
        self.__click_save()
        if wait:
            self._adminconsole_base.wait_for_completion()

    @PageService()
    def click_cancel(self):
        """ Click cancel button in a react modal dialog """
        self.__click_cancel()

    @PageService()
    def click_add(self):
        """ Click add button in a react modal dialog """
        self.__click_add()

    @WebAction()
    def click_element(self, xpath, is_entity_visible_only_on_hover=False):
        """
        click element on the dialog
        Args:
            xpath: (str) xpath of the element on the dialog
            is_entity_visible_only_on_hover (bool): flag to determine if element is visible only on hover
        """
        self.__click_element(xpath, is_entity_visible_only_on_hover)

    @WebAction()
    def type_text_and_delete(self, text_val, checkbox_id=None, button_name="Delete", wait=True):
        """
        Types the text on popup and clicks Delete

        Args:
            text_val (basestring)        : Text to be entered
            checkbox_id (str)    : Id of the checkbox that has to be selected
            button_name (str)    : Name of the button
            wait (bool)          : Wait for completion or not

        """

        if self._adminconsole_base.check_if_entity_exists("xpath", "//div[@class= 'modal-content'] | "
                                                                   "//div[contains(@class, 'mui-modal-body')]"):
            elem = self._driver.find_element(By.XPATH, "//div[contains(@class, 'form-content')]//input")
            elem.send_keys(text_val)
            if checkbox_id is not None:
                self._adminconsole_base.checkbox_select(checkbox_id)
            self.click_submit(wait=wait)

    @WebAction(delay=0)
    def upload_file(self, label, absolute_path):
        """
        uploads file path by passing absolute path in the input

        Args:
            label (str): label of the file input
            absolute_path (str):  Path of the file to be uploaded (Example : "C:\\Location\\of\\file")
        """
        """ Absolute path of the file to be uploaded"""
        xpath = f"//span[text()='{label}']/ancestor::div[contains(@class, 'field-wrapper')]/div[@class='input-wrapper']//input[@type='file']"
        file_input = self._driver._get_elements(xpath)
        file_input.send_keys(absolute_path)


    @WebAction(delay=0)
    def __read_title(self):
        """Reads Modal panel title"""
        return self._driver.find_element(By.XPATH, "//div[@class='mui-modal-header']/*[@class='mui-modal-title']").text

    @WebAction()
    def get_selected_options(self):
        """
        Gives selected elements from search and select

        Returns (List): List of selected elements in search and select

        """
        user_or_group_drop_down_xpath = ".//div[contains(@class, 'MuiChip-root')]/span"
        items = self._get_elements(user_or_group_drop_down_xpath)
        return [item.text.split("\n")[0] for item in items]

    @PageService()
    def select_items(self, item_list):
        """ Method to select the tale items inside a dialog """
        self.rtable = Rtable(self._admin_console, xpath="//div[@class='grid-body']")
        self.rtable.select_rows(item_list)

    @PageService()
    def browse_path(self, folder):
        """ Method to browse and select path inside a dialog
        Arg:
            folder (str) : path of the folder which is to be selected

        """
        browse = TreeView(self._admin_console, xpath="//div[@aria-labelledby ='customized-dialog-title']")
        browse_dialog = RModalDialog(self._admin_console, title="Select a path")
        paths = folder.replace('\\', '/').split('/')
        if '' in paths:
            paths.remove('')
        for node in paths:
            browse.expand_node(node)
        browse.select_items([os.path.basename(folder)])
        browse_dialog.click_save_button()

    @PageService(react_frame=True)
    def title(self):
        """Returns the title of panel"""
        return self.__read_title()

    @PageService(react_frame=True)
    def select_dropdown_values(self, drop_down_id=None, values=None, partial_selection=False, case_insensitive=False,
                               index=None):
        """Method to select values in dropdown

        Args:
            drop_down_id        (str)   --  Dropdown ID to select

            values              (list)  --  List of values to select from dropdown

            partial_selection (bool) -- flag to determine if dropdown values should be
                                        selected in case of partial match or not

            case_insensitive (bool) -- flag to determine whether dropdown value selection
                                        should be case sensitive or not

            index            (int)  --  Order of drop down in the sequence of display on page (starting from 0)

        """
        self.__get_base_element()
        if self.__base_element:
            self._dropdown = RDropDown(admin_console=self._adminconsole_base, base_element=self.__base_element)
        if drop_down_id is not None:
            self._dropdown.wait_for_dropdown_load(drop_down_id)
        self._dropdown.select_drop_down_values(drop_down_id=drop_down_id, values=values,
                                               partial_selection=partial_selection,
                                               case_insensitive_selection=case_insensitive, index=index)
    
    @PageService(react_frame=True)
    def deselect_dropdown_values(self, drop_down_id, values):
        """
        Method to deselect values in dropdown

        Args:
            drop_down_id        (str)   --  Dropdown ID to select
            
            values              (list)  --  List of values to deselect from dropdown 
        """
        self.__get_base_element()
        if self.__base_element:
            self._dropdown = RDropDown(admin_console=self._adminconsole_base, base_element=self.__base_element)
        self._dropdown.wait_for_dropdown_load(drop_down_id)
        self._dropdown.deselect_drop_down_values(drop_down_id=drop_down_id, values=values)

    def check_if_button_exists(self, text=None, aria_label=None):
        """
        Check if a button with given text or aria_label exists in the dialog box or not

        Args:
            text     (str)   -- Text inside button.
            aria_label (str) -- aria label of the button.
        """
        if text:
            return self._adminconsole_base.check_if_entity_exists(
                'xpath',
                self._dialog_xp + f"//button[contains(.,'{text}')]"
            )
        else:
            return self._adminconsole_base.check_if_entity_exists(
                'xpath',
                self._dialog_xp + f"//*[@aria-label='{aria_label}']//parent::div//button"
            )

    @WebAction()
    def click_button_on_dialog(self, text=None, preceding_label=False, aria_label=None, button_index=0, id=None):
        """Method to click a button on a dialog using text

            Args:

                text                (str)   --  Button text

                id                  (str)   --  Button id

                preceding_label     (bool)  --  If True, look for button corresponding to a label to click

                aria_label          (str)   --  aria-label value of button

                button_index        (int)   --  Index of the button if there are multiple buttons in the dialog
        """
        if aria_label:
            self._get_elements(
                f".//*[@aria-label='{aria_label}']//parent::div//button")[button_index].click()
        elif id:
            xpath = self._dialog_xp + f"//button[@id='{id}']"
            self._driver.find_element(By.XPATH, xpath).click()

        elif text:
            if not preceding_label:

                elem = self._get_elements(
                    f".//button[contains(.,'{text}')]")[button_index]

                self._adminconsole_base.scroll_into_view_using_web_element(elem)
                elem.click()


            else:
                # Button without a text may have a label which is a sibling.
                # Search for the label text if preceding_label is true
                button_xpath = f".//*[contains(text(), '{text}')]//following-sibling::div//button"
                self._get_elements(button_xpath)[button_index].click()
        else:
            self._get_elements(".//button")[button_index].click()

    @WebAction()
    def get_anchor_element_on_dialog(self, text):
        """Method to get anchor element on dialog using text"""
        return self._get_element(f".//a[contains(.,'{text}')]")

    def fill_input_by_xpath(self, text: str, element_id: str=None, element_xpath: str=None) -> None:
        """
        Method to fill text by xpath inside a modal dialog

        Args:
            text            (str)   --  text to be entered in the field
            element_id      (str)   --  id of the input field
            element_xpath   (str)   --  xpath of the input field (Add dot at the start of the xpath to search inside the dialog)
        """
        if not element_id and not element_xpath:
            raise AttributeError("element_id or element_xpath is required to fill text in the field")
        if element_xpath and not element_xpath.startswith("."):
            element_xpath = f".{element_xpath}"

        element = self._get_element(xpath=f".//*[@id='{element_id}']" if element_id else element_xpath)
        element.send_keys(u'\ue009' + 'a' + u'\ue003')  # CTRL + A + Backspace
        element.send_keys(text)

    @PageService(react_frame=True)
    def fill_text_in_field(self, element_id, text):
        """Method to fill text in field in dialog

        Args:
            element_id          (str)   --  Element ID of the text field to input text

            text                (str)   --  Text to enter in the field

        """
        ele = self._get_element(xpath=f".//*[@id='{element_id}']")
        ele.send_keys(u'\ue009' + 'a' + u'\ue003')  # CTRL + A + Backspace
        ele.send_keys(text)

    @PageService()
    def get_text_in_field(self, element_id):
        """Method to get text in field in dialog

        Args:
            element_id          (str)   --  Element ID of the text field to read text

        Returns:
            text    (str)   -   the string present in given text field
        """
        ele = self._get_element(xpath=f".//*[@id='{element_id}']")
        return ele.get_attribute('value')

    def select_radio_by_id(self, radio_id):
        """
        select the radio input based on id
        Args:
            radio_id     (str):  id of the element

        Returns:
            None
        """
        self._adminconsole_base.select_radio(radio_id)

    def select_radio_by_name(self, radio_name):
        """
                select the radio input based on name
                Args:
                    radio_name     (str):  name of the element

                Returns:
                    None
                """
        self._adminconsole_base.select_radio(name=radio_name)

    def select_radio_by_value(self, radio_value):
        """
                select the radio input based on value
                Args:
                    radio_value    (str):  value of the element

                Returns:
                    None
                """
        self._adminconsole_base.select_radio(value=radio_value)

    @WebAction()
    def __get_toggle_status(self, toggle_element_id=None, label=None):
        """
           Checks whether a toggle is enabled or disabled
               Args:
                   toggle_element_id    : Element ID of the toggle
                   label                : Label of the toggle
               Returns:
                   (bool)               : True if toggle enabled, else false
        """
        if label:
            xpath = f"//div[contains(@class, 'teer-toggle')]" \
                    f"//span[text()='{label}']/..//span[contains(@class, 'MuiSwitch-switchBase')]"
            element = self._driver.find_element(By.XPATH, xpath)

            status = True if 'Mui-checked' in element.get_attribute('class') else False
        else:
            status = self._driver.find_element(By.XPATH, f"//div[contains(@class, 'teer-toggle')]"
                                                        f"//*[@id='{toggle_element_id}']").is_selected()
        return status

    @WebAction()
    def __click_on_toggle(self, toggle_element_id=None, label=None):
        """
        Method to click on toggle
            Args:
                toggle_element_id : Element id of the toggle to be clicked on
                label             : Label of the toggle
        """
        if label:
            xpath = f"//div[contains(@class, 'teer-toggle')]" \
                    f"//span[text()='{label}']/../span[contains(@class, 'MuiSwitch-root')]//input[@type='checkbox']"
            self._driver.find_element(By.XPATH, xpath).click()
        else:
            self._driver.find_element(By.XPATH, f"//div[contains(@class, 'teer-toggle')]"
                                               f"//*[@id='{toggle_element_id}']").click()

    @PageService(react_frame=True)
    def enable_toggle(self, toggle_element_id=None, label=None):
        """
        Method to enable Toggle
            Args:
                toggle_element_id : Element id of the toggle to be clicked on
                label             : Label of the toggle
        """
        status = self.__get_toggle_status(toggle_element_id, label)
        if not status:
            self.__click_on_toggle(toggle_element_id, label)

    @PageService(react_frame=True)
    def disable_toggle(self, toggle_element_id=None, label=None):
        """
        Method to disable Toggle
            Args:
                toggle_element_id : Element id of the toggle to be clicked on
                label             : Label of the toggle
        """
        status = self.__get_toggle_status(toggle_element_id, label)
        if status:
            self.__click_on_toggle(toggle_element_id, label)

    @PageService(react_frame=True)
    def enable_disable_toggle(self, id: str, enable: bool) -> None:
        """
        Enables or disables a toggle element based on the given enable flag.

        Args:
            id (str): The ID of the toggle element.
            enable (bool): Flag indicating whether to enable or disable the toggle element.
        """
        self.enable_toggle(toggle_element_id=id) if enable else self.disable_toggle(toggle_element_id=id)

    @PageService(react_frame=True)
    def select_link_on_dialog(self, text, wait_time=10):
        """
        Select link text on dialog

        Args:
            text  (str)  --  Link text to select
        """
        button_xpath = f".//a[text() = '{text}'] | " + \
                f".//a/div[contains(text(),'{text}')]"
        self._get_element(button_xpath).click()
        sleep(wait_time)
        self._adminconsole_base.wait_for_completion()

    @PageService(react_frame=True)
    def submit_file(self, element_id, file_location):
        """
        method to submit file
        Args:
            element_id: id of the element
            file_location: location of the file to submit

        """
        ele = self._driver.find_element(By.ID, element_id)
        ele.send_keys(file_location)

    @WebAction()
    def __is_accordion_expanded(self, label=None, id=None):
        """
        Method to check if accordion is expanded
            Args:
                label : Accordion label

                id : Accordion panel ID
        """
        if id:
            return 'panel-closed' not in self._driver.find_element(By.ID, id).get_attribute("class")
        else:
            xp = f"//div[@class='accordion-title']//h3[contains(text(),'{label}')]" \
                 f"/ancestor::div[contains(@class,'panel-closed')]"
            return 'panel-closed' not in self._driver.find_element(By.XPATH, xp).get_attribute("class")

    @WebAction()
    def __click_accordion(self, label=None, id=None):
        """
        Method to click on accordion
            Args:
                label : Accordion label

                 id : Accordion panel ID
        """
        if id:
            self._driver.find_element(By.ID, id).click()
        else:
            xp = f"//div[@class='accordion-title']//h3[contains(text(),'{label}')]" \
                 f"/ancestor::div[contains(@class,'panel-closed')]"
            self._driver.find_element(By.XPATH, xp).click()

    @WebAction()
    def get_input_details(self, input_id: str, ignore_exception: bool = False, **kwargs):
        """
            Args:
                input_id      (str) - id of the input field

            Returns:
                List of all object in each row of rmodal dialog
                List of all object in each row of rmodal dialog
        """
        xpath = self._dialog_xp + f"//*[@id='{input_id}']"

        # TODO : Remove this after fixing the issue with input fields
        xpath = f"{xpath} | {self._dialog_xp}//*[@id='{input_id}']//p" if kwargs.get("paragraph_element_value") else xpath

        try:
            element = self._get_element(xpath)
            retvalue = element.get_attribute("value")
            if retvalue is None:
                retvalue = element.text
        except:
            if ignore_exception:
                retvalue = None
            else:
                raise Exception(f"Failed to get input value for input with id: {input_id}")
        finally:
            return retvalue

    @WebAction()
    def get_input_state(self, input_id: str, ignore_exception: bool = False):
        """
            Retrieves the state of an input element identified by its ID.

            Args:
                input_id (str): The ID of the input element.

            Returns:
                bool: True if the input element is disabled, False otherwise.

            """
        xpath = self._dialog_xp + f"//*[@id='{input_id}']"

        try:
            element = self._get_element(xpath)
            _disabled_attributes = ["disabled", "aria-disabled"]
            is_disabled = True if any([element.get_attribute(attr) for attr in _disabled_attributes]) else False
        except:
            if ignore_exception:
                is_disabled = False
            else:
                raise Exception(f"Failed to get input state for input with id: {input_id}")
        finally:
            return is_disabled

    @PageService()
    def expand_accordion(self, label=None, id=None):
        """
        Method to expand accordion
            Args:
                label : Accordion label

                id : Accordion panel ID
        """
        if not self.__is_accordion_expanded(label, id):
            self.__click_accordion(label, id)

    @WebAction()
    def __click_on_icon(self, tooltip: str, index: int):
        """
        Method to click on icon

            Args:
                tooltip : Icon label
                index   : Index of icon to click on
        """
        icon_xpath = f".//*[@aria-label='{tooltip}']//*[contains(@class, 'MuiIconButton')]"
        self._get_element(f'({icon_xpath})[{index}]').click()

    @PageService()
    def click_icon(self, tooltip: str, index: int = 1):
        """
        Method to click on icon

            Args:
                tooltip : Icon label
                index   : Index of icon to click on
        """
        self.__click_on_icon(tooltip, index)

    @WebAction()
    def __click_icon_by_title(self, title: str):
        """
        Method to click on icon by title

            Args:
                title : Icon title
        """
        icon_xpath = f".//*[@title='{title}']"
        self._get_element(f'({icon_xpath})').click()

    @PageService()
    def click_icon_by_title(self, title: str):
        """
        Method to click on icon by title

            Args:
                title : Icon title
        """
        self.__click_icon_by_title(title)

    @PageService()
    def access_tab(self, tab_text):
        """
        Access tab inside Modal Dialog
        Args:
            tab_text: localized tab text
        """
        self.__select_tab(tab_text)
        self._adminconsole_base.wait_for_completion()

    @PageService()
    def current_tab(self):
        """
        Returns the current tab

        Returns:
                CurrentTab      (str)--     Current Navigated Tab

        """
        if self._adminconsole_base.check_if_entity_exists('xpath', "//div[@role='tablist']"):
            return self._driver.find_element(By.XPATH,
                                             "//div[@role='tablist']/button[contains(@class, 'Mui-selected')]/span[1]").text
        return ""

    @PageService()
    def select_dropdown_value_action(self, action, index=None, value=None, drop_down_id=None):
        """Select action item from a dropdown value"""

        self._dropdown.select_dropdown_value_action(action, index, value, drop_down_id=drop_down_id)

    @property
    def dropdown(self):
        return self._dropdown

    @PageService()
    def click_action_item(self, action_name, aria_label=None, preceding_label=None):
        """Clicks on given Action item from the actions menu in modal

        Args:
            action_name  (str) :  name of action item to be clicked
            aria_label  (str) :  aria-label value of dropdown button
            preceding_label     (str) : label corresponding to the button
        """
        self.__click_actions_menu(aria_label, preceding_label)
        self.__click_action_item(action_name)
        self._adminconsole_base.wait_for_completion()

    @WebAction()
    def __click_actions_menu(self, aria_label=None, preceding_label=None):
        """
            Clicks on the actions menu

            aria_label          (str)   --  aria-label value of button
            preceding_label     (str) : Button corresponding to this label
        """
        if aria_label:
            self._get_element(f".//div[contains(@class,'action-list-dropdown-wrapper')]/descendant::"
                              f"button[@aria-label='{aria_label}'][1]").click()
        else:
            if not preceding_label:
                self._get_element(".//div[contains(@class,'action-list-dropdown-wrapper')]//button[1]").click()
            else:
                self._get_element(f".//*[contains(text(), '{preceding_label}')]//following-sibling::"
                                  f"div[contains(@class,'action-list-button')]//button[1]").click()

    @WebAction()
    def __click_action_item(self, action_name):
        """
        Selects button for action item in the Panel

        Args:
            action_name : Name of action item to be clicked
         """
        action_items = self._get_elements(
            f"//div[@id='action-list']//div[contains(text(), '{action_name}')]/ancestor::button")
        for elem in action_items:
            if elem.is_displayed():
                elem.click()
                break
    @WebAction()
    def select_checkbox(self, checkbox_id: str = None, checkbox_label: str = None):
        """
               Selects checkbox that matches the ID
               Args:
                   checkbox_id   (str)  -- id of the checkbox from dev or input tag
                   checkbox_label (str)  -- label of the checkbox
        """
        self.__checkbox.check(label=checkbox_label, id=checkbox_id)

    @WebAction()
    def deselect_checkbox(self, checkbox_id: str = None, checkbox_label: str = None):
        """
               Selects checkbox that matches the ID
               Args:
                   checkbox_id   (str)  -- id of the checkbox from dev or input tag
                   checkbox_label (str)  -- label of the checkbox
        """
        self.__checkbox.uncheck(label=checkbox_label, id=checkbox_id)

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

    @PageService()
    def enable_notify_via_email(self):
        "Enables notify via email checkbox"
        self.__enable_notify_via_email()

    @PageService()
    def disable_notify_via_email(self):
        "Disables notify via email checkbox"
        self.__disable_notify_via_email()
    
    @PageService()
    def copy_content_of_file_from_dialog(self, element_id):
        """Retrieve and return the text content from the specified element
            Args:
                element_id (str) : ID of the file view element
        """
        element = self._get_element(f'//*[@id="{element_id}"]//pre')
        text_content = element.text

        return text_content


class RTransferOwnership(RModalDialog):
    """ Class for react Transfer Ownership dialog"""

    @PageService()
    def transfer_ownership(self, owner_transfer):
        """
        Method to transfer ownership to a user

        Args:
            owner_transfer (str): User to which ownership has to be transferred

        Raises:
            Exception:
                If there is no option to transfer owner
        """
        if owner_transfer:
            self.dropdown.search_and_select(select_value=owner_transfer, id='transferOwnership')

        self.click_submit()
        self._adminconsole_base.check_error_message()
        self._adminconsole_base.wait_for_completion()


class RSecurity(RModalDialog):
    """ React Security Class """

    @WebAction()
    def __select_entity_type(self, entity_type):
        """Method to select entitytype from the dropdown list"""
        self._dropdown.select_drop_down_values(values=[entity_type], drop_down_id='entityTypeHierarchy')

    @WebAction()
    def __select_role(self, rolename):
        """Method to select the role"""
        self._dropdown.select_drop_down_values(values=[rolename], drop_down_id='rolesList')

    @WebAction()
    def __click_on_add(self):
        """Method to click on the add button"""
        self.click_button_on_dialog('Add')

    @WebAction()
    def __search_entity_name(self, value, wait_until=30):
        """Method to search entity"""

        input_box = self._get_element(".//input[contains(@class,'MuiAutocomplete-input')]")
        input_box.send_keys(u'\ue009' + 'a' + u'\ue003')
        input_box.send_keys(value)

        # There is a change in self._dialog_xp if this operation fails correct xpath this element locator,
        # after changing do remove this comment
        WebDriverWait(self._driver, wait_until).until(
            ec.presence_of_element_located(
                (By.XPATH, f"//div[contains(text(),'({value})')]")
            )
        )

    @WebAction(delay=3)
    def __select_entity_name(self, value):
        """Method to select an entity after search"""
        self._get_element(f"//*[text()='{value}']").click()

    @WebAction(delay=3)
    def __select_user_name(self, value):
        """Method to select username after search"""
        self._get_element(f"//*[contains(text(),'({value})')]").click()

    @PageService()
    def __add_user_security_association(self, username, rolename):
        """Method to add security association from entity details page"""
        self.__search_entity_name(username)
        self.__select_user_name(username)
        self.__select_role(rolename)
        self.__click_on_add()

    @WebAction()
    def __remove_user_security_association(self, username, rolename):
        """Method to remove security association from entity details page"""
        self._get_element(f".//label[text()='{rolename}']//following-sibling::span//*[@title='Delete {username}']"
        ).click()

    @PageService()
    def __add_associated_entity(self, entity_type, entity_name, role_name):
        """Method to add association from user / usergroup details page"""
        self.__select_entity_type(entity_type)
        self.__search_entity_name(entity_name)
        self.__select_entity_name(entity_name)
        self.__select_role(role_name)
        self.__click_on_add()

    @PageService()
    def edit_security_association(self, associations, add=True):
        """
        Method to edit security association from entity details page

        Args:
            associations (dict) : dictionary containing user and role pairs
                Eg. -> associations = {
                'user1' : ['View', 'Alert owner'],
                'user2': ['Master', 'Plan Subscription Role', 'Tenant Admin', 'Tenant Operator']
                }

            add (boolean) : True means add association, False means remove
        """
        for user, roles in associations.items():
            for role in roles:
                if add:
                    self.__add_user_security_association(user, role)
                else:
                    self.__remove_user_security_association(user, role)

        self.click_submit()

    @WebAction()
    def get_security_associations(self):
        """
        Method to get security associations from the dialog

        Returns:
            associations (dict) : dictionary containing user and role pairs
                Eg. -> associations = {
                'user1' : ['View', 'Alert owner'],
                'user2': ['Master', 'Plan Subscription Role', 'Tenant Admin', 'Tenant Operator']
                }
        """
        labels = self._driver.find_elements(By.XPATH, self._dialog_xp + "//ul/li//label")
        label_texts = [label.get_attribute('title') for label in labels]
        associations = {}
        for i in range(0, len(label_texts), 2):
            associations[label_texts[i]] = associations.get(label_texts[i], []) + [label_texts[i + 1]]
        return associations

    def add_associated_entities(self, associations):
        """Method to add associated entities from user / usergroup details page

        Args:
            associations (dict) : dictionary containing
                Eg. -> associations = {
                        'Commcell' : [{
                                'entity_name' : 'commcell_name',
                                'role_name' : 'View'
                            }],
                        'Plan': [{
                                'entity_name' : 'plan_1',
                                'role_name' : 'Plan Subscription Role'
                            },
                            {
                                'entity_name' : 'plan_2',
                                'role_name' : 'View'
                            }
                        ]
                    }

        """
        for entity_type in associations.keys():
            for entity in associations[entity_type]:
                self.__add_associated_entity(entity_type, entity['entity_name'], entity['role_name'])
        self.click_button_on_dialog('Save')

    @PageService()
    def associate_permissions(self, username):
        """
           Method to associate a user/user group to view a particular entity
           Args:
               username: Username of the user
        """
        self.__search_entity_name(username)
        self.__select_user_name(username)
        self.__click_on_add()
        self.click_button_on_dialog('Save')

    @PageService()
    def laptop_plan_select_user(self, user_or_group):
        """ Method to select user or user group from the search result in the Associate users or user groups dialog box
         in the laptop plan details page

         Args:
             user_or_group (str): string containing the user name or the user group name to select from search result"""
        self.__select_user_name(user_or_group)


class RBackup(RModalDialog):
    """ Class for backup panel"""
    def __init__(self, admin_console, title=None, xpath=None):
        """
        Initialize the panel info object
        """
        super(RBackup, self).__init__(admin_console, title, xpath)

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
    def __enable_notify_via_email(self):
        """ Enables notify via email checkbox """
        self._driver.find_element(By.XPATH, "*//span[contains(text(),'Notify via email')]").click()

    @WebAction()
    def _select_backupset_and_subclient(self, backupset_name, subclient_name):
        """Selects the required backupset and subclient
        Args:
            backupset_name (String) : Name of backupset to be selected

            subclient_name (String) : Name of the subclient to be selected

        """
        self._driver.find_element(By.XPATH, f'//span[contains(text(),"{backupset_name}")]/following::'
                                            f'span[contains(text(), "{subclient_name}")][1]').click()

    @PageService()
    def submit_backup(self, backup_type, backupset_name=None, subclient_name=None, notify=False,
                      incremental_with_data=False, cumulative=False, log=False, immediate_backup_copy=False,
                      purge_binary_log=True):
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
            immediate_backup_copy(bool): To enable immediate backup copy
            purge_binary_log(bool)  :  To enable purge binary logs

        Returns:
            job_id: job id from notification
        """

        if backupset_name:
            self._select_backupset_and_subclient(backupset_name, subclient_name)
            self.click_button_on_dialog(id="Save")
            self._adminconsole_base.wait_for_completion()

        if backup_type not in self.BackupType:
            raise CVWebAutomationException("Invalid backup type, "
                                           "format should be one among the type in BackupType")
        self.__set_backup_level(backup_type)
        if incremental_with_data:
            self.checkbox.check(id='dataCheckbox')
        else:
            if self.checkbox.is_exists(id='notifyUserOnJobCompletion'):
                self.checkbox.uncheck(id='notifyUserOnJobCompletion')
        if cumulative:
            self._adminconsole_base.checkbox_select('cumulative')
        if log:
            self._adminconsole_base.checkbox_select('log')
        if purge_binary_log is False:
            if self.checkbox.is_checked(id='doNotTruncateLog'):
                self.checkbox.uncheck(id='doNotTruncateLog')
        if notify:
            self.__enable_notify_via_email()
        if immediate_backup_copy:
            if self.checkbox.is_exists(id='backupCopyImmediate'):
                self.checkbox.check(id='backupCopyImmediate')
                self.select_radio_by_id(radio_id='backupCopyCurrJob')
        backup_dialog = RModalDialog(
            self._adminconsole_base,
            xpath="//button[contains(.,'Submit')]//ancestor::div[contains(@class, 'mui-modal-dialog mui-modal-centered')]")
        backup_dialog.click_button_on_dialog(text="Submit")
        if backup_type == self.BackupType.SYNTH:
            _jobid = self._adminconsole_base.get_jobid_from_popup(multiple_job_ids=True)
        else:
            _jobid = self._adminconsole_base.get_jobid_from_popup()
        self._adminconsole_base.wait_for_completion()
        return _jobid


class RTags(RModalDialog):
    """ React Tags Class """

    @WebAction()
    def __fill_tag_name(self, tag_name):
        """Method to fill tag name

        Args:
            tag_name    (str)   :   Tag name to be filled in the input field
        """
        self.fill_text_in_field('tagname', tag_name)

    @WebAction()
    def __fill_tag_value(self, tag_value):
        """Method to fill tag value

        Args:
            tag_value    (str)   :   Tag value to be filled in the input field
        """
        self.fill_text_in_field('tagValue', tag_value)

    @WebAction()
    def __get_index_of_tag(self, tag_name, tag_value):
        """Method to get index of a tag

        Args:
            tag_name    (str)   :   Tag name
            tag_value   (str)   :   Tag value
        """
        available_tags = list(self.get_tags().items())
        return available_tags.index((tag_name, tag_value))

    @WebAction()
    def __update_tag_values(self, index, tag_name, tag_value):
        """Method to update the existing tags

        Args:
            index       (int)   :   Index of tags starting from 0
            tag_name    (str)   :   New Tag name
            tag_value   (str)   :   New Tag value
        """
        tag_elements = self._driver.find_elements(By.XPATH, "//*[contains(@class, 'tagsList')]//input")

        # update tag name
        key_element = tag_elements[index * 2]
        key_element.send_keys(u'\ue009' + 'a' + u'\ue003')
        key_element.send_keys(tag_name)

        # update tag value
        value_element = tag_elements[index * 2 + 1]
        value_element.send_keys(u'\ue009' + 'a' + u'\ue003')
        value_element.send_keys(tag_value)

    @WebAction()
    def __click_on_cross_mark(self, index):
        """Method to delete the tags

        Args:
            index   (int)   :   Index of tag to be deleted
        """
        delete_buttons = self._driver.find_elements(By.XPATH, "//*[contains(@class, 'tagsList')]//button")
        delete_buttons[index].click()

    @WebAction()
    def get_tags(self):
        """Method to get stored tags"""
        text_elements = self._driver.find_elements(By.XPATH, "//*[contains(@class, 'tagsList')]//input")
        texts = [element.get_attribute('value') for element in text_elements]

        return {texts[i]: texts[i + 1] for i in range(0, len(texts), 2)}

    @PageService()
    def add_tag(self, tag_name, tag_value=''):
        """Method to add a new tag

        Args:
            tag_name    (str)   :   New Tag name
            tag_value   (str)   :   New Tag value
        """
        self.__fill_tag_name(tag_name)
        sleep(2)
        if tag_value:
            self.__fill_tag_value(tag_value)
            sleep(2)
        self.click_button_on_dialog('Add')

    @PageService()
    def delete_tag(self, tag_name, tag_value=''):
        """Method to delete the tag

        Args:
            tag_name    (str)   :   Tag name
            tag_value   (str)   :   Tag value
        """
        tags_index = self.__get_index_of_tag(tag_name, tag_value)
        self.__click_on_cross_mark(tags_index)

    @PageService()
    def modify_tag(self, old_tag: tuple, new_tag: tuple):
        """Method to update the particular

        Args:
            old_tag    (tuple)   :   Tuple of old tag name and old tag value
            new_tag    (tuple)   :   Tuple of new tag name and new tag value
        """
        index = self.__get_index_of_tag(*old_tag)
        self.__update_tag_values(index, *new_tag)


class Form(RModalDialog):
    """Class for handling Form component."""

    def __init__(self, admin_console):
        xpath = "//form[contains(@class, 'form-wrapper')]"
        super().__init__(admin_console, xpath=xpath)


class ServiceCommcellSelectionDialog(RModalDialog):
    """Class for handling service commcell selection"""

    def __init__(self, admin_console: AdminConsole):
        """
        Initialize the ServiceCommcellSelectionDialog class

        Args:
            admin_console   -   instance of AdminConsole class
        """
        super().__init__(admin_console)

    @PageService()
    def available_commcells(self):
        """
        Returns the available commcell options in the dropdown

        Returns:
            list    -   list of commcell names in dropdown
        """
        return list(set(self.dropdown.get_values_of_drop_down('multiCommcellSelection')))

    @PageService()
    def select_commcell(self, commcell_name):
        """
        Selects the given workload commcell from the list and clicks OK

        Args:
            commcell_name   (str)   -   name of the commcell to select
        """
        self.dropdown.select_drop_down_values(
            drop_down_id='multiCommcellSelection',
            values=[commcell_name]
        )
        self.click_submit()
        self._adminconsole_base.wait_for_completion()


class TagsDialog(ModalDialog):
    """
    Class for the Tags dialog opened from manage tags action from companies table

    Note: Use RTags for React dialog, this dialog will be deprecated in future
    """

    def __init__(self, admin_console, title='Manage tags'):
        """
        Initialize the TagsDialog class

        Args:
            admin_console   -   instance of AdminConsole class
            title   (str)   -   title of this Tags Dialog
        """
        super().__init__(admin_console)
        self._title = title
        self._dialog_xp = f"//h1[text()='{title}']/ancestor::div[@class='modal-content']"

    @WebAction()
    def is_dialog_present(self):
        """
        Checks if the Tags dialog is already open/closed or another dialog is open

        Returns:
            bool    -   True if this dialog is open in browser, else false
        """
        try:
            if self.title() != self._title:
                raise CVWebAutomationException("A different dialog is open!")
            else:
                return True
        except NoSuchElementException:
            return False

    @WebAction()
    def __parse_key_value(self, list_elem):
        """
        Gets the tag name and value from list element

        Args:
            list_elem   (webelement)    -   <li> element containing tag name and value

        Returns:
            tag_dict    (dict)  -   dict with tag name and value inputs in the list element
        """
        tag_name = list_elem.find_element(By.XPATH, f".//input[@id='tag.id + tag.name']").get_attribute('value')
        tag_value = list_elem.find_element(By.XPATH, f".//input[@id='tag.id + tag.value']").get_attribute('value')
        return {
            "name": tag_name,
            "value": tag_value
        }

    @WebAction()
    def _parse_tags(self):
        """
        Reads the tags from dialog

        Returns:
            list[dict]  -   list of dicts with tag name and tag value properties
        """
        tags = []
        for list_elem in self._driver.find_elements(By.XPATH, f"{self._dialog_xp}//li"):
            tags.append(self.__parse_key_value(list_elem))
        return tags

    @PageService()
    def get_tags(self):
        """
        Returns the tags currently present

        Returns:
            list[dict]  -   list of dicts with tag name and tag value keys

            example:
                tag_list = [
                    {
                    "name": "key1",
                    "value": "value1"
                    },
                    {
                    "name": "key2",
                    "value": "value2"
                    }
                ]
        """
        return self._parse_tags()

    @WebAction()
    def delete_tag(self, tag_name):
        """
        Deletes the tag with given name

        Args:
            tag_name    (str)   -   name of tag
        """
        delete_button = self._driver.find_element(By.XPATH, f"{self._dialog_xp}//a[@title='Delete {tag_name}']")
        ActionChains(self._driver).move_to_element(delete_button).click().perform()

    @WebAction(delay=1)
    def add_tag(self, tag_name, tag_value=''):
        """
        Adds a new tag with given name and value

        Args:
            tag_name    (str)   -   name of tag
            tag_value   (str)   -   value for tag, default is ''

        """
        tag_name_input = self._driver.find_element(By.XPATH, f"{self._dialog_xp}//input[@id='tagName']")
        tag_value_input = self._driver.find_element(By.XPATH, f"{self._dialog_xp}//input[@id='tagValue']")

        ActionChains(self._driver).move_to_element(tag_name_input).click().send_keys(tag_name).perform()
        if tag_value:
            ActionChains(self._driver).move_to_element(tag_value_input).click().send_keys(tag_value).perform()

        add_button = self._driver.find_element(By.XPATH, f"{self._dialog_xp}//a[@title='Add tag']")
        ActionChains(self._driver).move_to_element(add_button).click().perform()

    @WebAction()
    def click_submit(self):
        """ Clicks save button of this dialog """
        save_button = self._driver.find_element(By.ID, "addTags_save")
        ActionChains(self._driver).move_to_element(save_button).click().perform()
        self._adminconsole_base.wait_for_completion()

    @WebAction()
    def click_cancel(self):
        """ Clicks cancel button of this dialog """
        cancel_button = self._driver.find_element(By.ID, "addTags_cancel")
        ActionChains(self._driver).move_to_element(cancel_button).click().perform()
        self._adminconsole_base.wait_for_completion()


class SecurityDialog(ModalDialog):
    """
    Class for Angular Security Dialogs with user, role associations
    Note: Use RSecurity for React version, this dialog will be deprecated in future
    """

    def __init__(self, admin_console, title='Security', enter_method=False):
        """
        Initialize the angular SecurityDialog class

        Args:
            admin_console   -   instance of AdminConsole class
            title   (str)   -   title of this SecurityDialog
            enter_method    (bool)  -   will pass enter key to select user (for cases when dropdown is empty)

        """
        super().__init__(admin_console)
        self._title = title
        self._dialog_xp = f"//h1[text()='{title}']/ancestor::div[@class='modal-content']"
        self._dropdown = DropDown(admin_console)
        self.__enter_method = enter_method

    @WebAction()
    def is_dialog_present(self):
        """
        Checks if the Operators dialog is already open/closed or another dialog is open

        Returns:
            bool    -   True if this dialog is open in browser, else false
        """
        try:
            if self.title() != self._title:
                raise CVWebAutomationException("A different dialog is open!")
            else:
                return True
        except NoSuchElementException:
            return False

    @WebAction()
    def _get_user_role_associations(self):
        """
        Gets the user and role labels in dialog

        Returns:
            user_roles  (list)  -   list with user role association dicts
        """
        user_roles = []
        for user_span_elem in self._driver.find_elements(By.XPATH, f"{self._dialog_xp}//span[@class='user-type']"):
            user_name = user_span_elem.find_element(By.XPATH, ".//label[contains(@class,'user')]").text
            role_name = user_span_elem.find_element(By.XPATH, ".//label[contains(@class,'role')]").text
            user_roles.append({"user": user_name, "role": role_name})
        return user_roles

    @PageService()
    def get_user_role_associations(self):
        """
        Gets the user and role labels in dialog

        Returns:
            user_roles  (list)  -   list with user role association dicts
            Example:
            [
                {'role':'<name of role>','user':'<username>'},
                {'role':'<name of role>','user':'<username>'},
                {'role':'<name of role>','user':'<username>'}
            ]
        """
        return self._get_user_role_associations()

    @WebAction()
    def _get_usergroup_role_associations(self):
        """
        Gets the usergroup and role labels in dialog

        Returns:
            ug_roles  (list)  -   list with user role association dicts
        """
        ug_roles = []
        for group_span_elem in self._driver.find_elements(By.XPATH, f"{self._dialog_xp}//span[@class='group-type']"):
            ug_name = group_span_elem.find_element(By.XPATH, ".//label[contains(@class,'user')]").text
            role_name = group_span_elem.find_element(By.XPATH, ".//label[contains(@class,'role')]").text
            ug_roles.append({"userGroup": ug_name, "role": role_name})
        return ug_roles

    @PageService()
    def get_usergroup_role_associations(self):
        """
        Gets the usergroup and role labels in dialog

        Returns:
            ug_roles  (list)  -   list with user role association dicts
            Example:
            [
                {'role':'<name of role>','userGroup':'<usergroupname>'},
                {'role':'<name of role>','userGroup':'<usergroupname>'},
                {'role':'<name of role>','userGroup':'<usergroupname>'}
            ]
        """
        return self._get_usergroup_role_associations()

    @WebAction()
    def remove_association(self, user_name, role_name):
        """
        Deletes the operator with given name and role

        Args:
            user_name   (str)   -   name of user or group
            role_name   (str)   -   name of role associated
        """
        remove_button_xpath1 = f"{self._dialog_xp}//label[text()='{user_name}']" \
                               f"/following-sibling::label[text()='{role_name}']" \
                               f"/following-sibling::span[@class='delete-row']/a"
        remove_button_xpath2 = f"//label[@title='{user_name}']" \
                               f"/following-sibling::label[@title='{role_name}']/../span/a"

        if self._adminconsole_base.check_if_entity_exists('xpath', remove_button_xpath2):
            self._driver.find_element(By.XPATH, remove_button_xpath2).click()
        else:
            self._driver.find_element(By.XPATH, remove_button_xpath1).click()

    @WebAction()
    def __expand_user_search_bar(self):
        """expand operator search bar """
        self._driver.find_element(By.XPATH,
            f"{self._dialog_xp}//div[contains(@class,'select2-container add-user-type')]").click()

    @WebAction()
    def __select_user(self, user):
        """select operator user in add operator panel """
        input_boxes = self._driver.find_elements(By.XPATH, "//div[@class='select2-search']/input")
        for box in input_boxes:
            if box.is_displayed():
                box.click()
                box.send_keys(user)
                sleep(20)
                self._driver.find_element(By.XPATH,
                    f"//span[contains(text(),'{user}')]").click()
                return

    @WebAction()
    def __enter_user(self, user_name):
        """
        Web Action to type in the user or user group name and enter

        Args:
            user_name   (str)   -   name of user or user group
        """
        self.__expand_user_search_bar()
        for input_elem in self._driver.find_elements(By.XPATH, "//div[@class='select2-search']/input"):
            if input_elem.is_displayed():
                input_elem.click()
                input_elem.send_keys(user_name)
                sleep(20)
                input_elem.send_keys(u'\ue007')  # SEND ENTER or RETURN -> 006
                return

    @WebAction()
    def __click_add_user(self):
        """click on add button in add operator panel """
        self._driver.find_element(By.XPATH,
            f"{self._dialog_xp}//button[@data-ng-click='addNewUserGroup()']").click()

    @WebAction()
    def add_association(self, user_name, role_name):
        """
        Adds a new operator with given name and role

        Args:
            user_name   (str)   -   name of user or user group
            role_name   (str)   -   name of role
        """
        self.__expand_user_search_bar()
        if self.__enter_method:
            self.__enter_user(user_name)
        else:
            self.__select_user(user_name)

        dropdown_id = "adduserId"

        if not self._adminconsole_base.driver.find_element(By.ID, dropdown_id).tag_name.lower() == "isteven-multi-select":
            self._adminconsole_base.select_value_from_dropdown(dropdown_id, role_name)
        else:
            self._dropdown.select_drop_down_values(values=[role_name], drop_down_id=dropdown_id)

        self.__click_add_user()

    @WebAction()
    def click_submit(self, submit_type=False):
        """ Clicks save button of this dialog """
        self._adminconsole_base.click_button_using_text('Save')
        self._adminconsole_base.wait_for_completion()


class ServiceCommcellAssociationsDialog(RModalDialog):
    """ Class for service commcell associations dialog in service commcells page """

    def __init__(self, admin_console: AdminConsole, title='Service CommCell associations'):
        """
        Initializes the Service Commcell Associations dialog class

        Args:
            admin_console   -   instance of AdminConsoleBase
            title   (str)   -   title of this dialog
        """
        super().__init__(admin_console)
        self.__rtable = Rtable(admin_console, id='editAssociatedUsersGrid')
        self._title = title

    @WebAction(delay=0)
    def __read_title(self):
        """Reads Modal panel title"""
        return self._driver.find_element(By.XPATH,
            "//div[@class='modal-content']//div[contains(@class,'setup-title')]/h3").text

    @WebAction()
    def is_dialog_present(self):
        """
        Checks if this dialog is already open/closed or another dialog is open

        Returns:
            bool    -   True if this dialog is open in browser, else false
        """
        try:
            if self.title() != self._title:
                raise CVWebAutomationException("A different dialog is open!")
            else:
                return True
        except NoSuchElementException:
            return False

    @WebAction()
    def _search_entity(self, entity):
        """Searches given entity in user suggestion input"""
        self.fill_text_in_field('searchAutoComplete', entity)
        self._adminconsole_base.wait_for_completion()

    @WebAction()
    def _read_suggestions(self, pages=1):
        """Reads the suggestions in dropdown and returns list"""
        suggestions = set()
        more_link_xpath = f"{self._dialog_xp}//div[@class='show-more-container']/a"

        for elem in self._driver.find_elements(By.XPATH, f"{self._dialog_xp}//*[@class='result-item']"):
            suggestions.add(elem.get_attribute('innerText').strip())

        for _ in range(pages - 1):
            if self._adminconsole_base.check_if_entity_exists('xpath', more_link_xpath):
                self._driver.find_element(By.XPATH, more_link_xpath).click()
                self._adminconsole_base.wait_for_completion()
            else:
                break
            for elem in self._driver.find_elements(By.XPATH, f"{self._dialog_xp}//*[@class='result-item']"):
                suggestions.add(elem.get_attribute('innerText').strip())

        return list(suggestions)

    @WebAction()
    def _clear_entity_search(self):
        """Clears the search bar in user suggestion input"""
        for clear_button in self._driver.find_elements(By.XPATH,
                f"{self._dialog_xp}//div[contains(@class, 'clear-search-text')]"):
            if clear_button.is_displayed():
                clear_button.click()

    @WebAction()
    def _select_entity(self, entity, timeout=30):
        """Clicks the selected entity from drop down list"""
        entity_value_xpath = f"//div[contains(text(),' {entity} (')]"
        WebDriverWait(self._driver, timeout).until(
            ec.visibility_of_element_located((By.XPATH, entity_value_xpath)))
        
        self._driver.find_element(By.XPATH, entity_value_xpath).click()

    @WebAction()
    def _select_commcells(self, commcells):
        """Selects the given commcells from dropdown if possible"""
        self.dropdown.select_drop_down_values(values=commcells, drop_down_id='commCells')

    @PageService()
    def get_user_suggestions(self, term, pages=1):
        """
        Gets the list of suggestions for given term in associations

        Args:
            term    (str)   -   the term to search
            pages   (int)   -   number of pages of use suggestions to read

        Returns:
            suggestions (list)  -   list of suggestions as strings
        """
        self._search_entity(term)
        suggestions_list = self._read_suggestions(pages)
        self._clear_entity_search()
        return suggestions_list

    @PageService()
    def available_commcells(self):
        """
        Gets the list of commcells available to associate

        Returns:
            list    -   list of commcell names available in commcell dropdown
        """
        return self.dropdown.get_values_of_drop_down('commCells')

    @WebAction()
    def add_association(self, entity, commcells):
        """
        Associates the entity to given commcells

        Args:
            entity  (str)       -   name of entity to associate
            commcells   (list)  -   list of commcell names to associate the entity to
        """
        self._search_entity(entity)
        self._select_entity(entity)
        self._select_commcells(commcells)
        self.click_button_on_dialog('Add')
        self.click_save_button()

    @PageService()
    def get_associations(self, search=None, all_pages=True):
        """
        Gets the associations data

        Args:
            search  (str)       -   entity to search if needed
            all_pages   (bool)  -   will fetch all pages of associations if True

        Returns:
            associations    (dict)  -   dictionary with the associations table data in dialog
        """
        if search:
            self.__rtable.search_for(search)
        if all_pages:
            self.__rtable.set_pagination('All')
        data = self.__rtable.get_table_data()
        self.__rtable.clear_search()
        return data

    @WebAction()
    def delete_association(self, entity):
        """
        Deletes entity's association to all commcells

        Args:
            entity  (str)   -   name of entity to delete associations of
        """
        self.__rtable.search_for(entity)
        self.__rtable.select_rows([entity])
        self.__rtable.access_toolbar_menu('Delete')
        self.click_save_button()

class SLA(RModalDialog):
    """ React SLA Class """

    def __init__(self, admin_console: AdminConsole):
        """
        Initialize the SLA class

        Args:
            admin_console       (obj)    :   Instance of AdminConsole class
        """
        super(SLA, self).__init__(admin_console)
        self.__toggle = Toggle(admin_console)

    @WebAction()
    def __click_on_radio_button(self, radio_button_id: str) -> None:
        """Method to click on radio button using id"""
        if not self._driver.find_element(By.ID, radio_button_id).is_selected():
            self._driver.find_element(By.ID, radio_button_id).click()

    @WebAction()
    def __select_sla_period(self, period: str) -> None:
        """Method to click on radio button using id"""
        self._dropdown.select_drop_down_values(values=[period], drop_down_id='SLAPeriodDropdown')

    @PageService()
    def use_system_default_sla(self) -> None:
        """Method to select system default SLA"""
        self.__click_on_radio_button('useSystemDefaultSLA')

    @PageService()
    def select_sla_period(self, period: str=None, custom_days: int=None) -> None:
        """
            Method to select SLA period

            Args:
                period (str)        -   SLA period (e.g: 1 day / week / month)

                custom_days (int)   -   custom value for SLA in days
        """
        self.__click_on_radio_button('SLAPeriod')
        if period:
            self.__select_sla_period(period)
        if custom_days:
            self.__select_sla_period('Custom days')
            self.fill_text_in_field('customDays', str(custom_days))

    @PageService()
    def exclude_sla(self, reason: str=None) -> None:
        """
            Method to exclude SLA

            Args:
                reason (str)    -   Reason for exclusion
        """
        self.__toggle.enable('Exclude from SLA')
        if reason:
            self.fill_text_in_field('exclusionReason', reason)

    @WebAction()
    def __read_exclude_reason(self) -> str:
        """Method to read exclude reason"""
        return self._driver.find_element(By.ID, 'exclusionReason').get_attribute('value')

    @PageService()
    def get_exclude_reason(self) -> str:
        """Method to get exclude reason"""
        if self.__toggle.is_enabled('Exclude from SLA'):
            return self.__read_exclude_reason()
        return 'Not Excluded from SLA'
