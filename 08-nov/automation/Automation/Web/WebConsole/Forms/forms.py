from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Add all the actions on the forms landing page go here

Forms:

    _get_opened_form_title                  --      Get the title of opened form

    _click_ok                               --      Click ok

    _get_form_submit_message                --      Get the message of submit form

    _open_search_results                    --      Opens the SearchResults page for the
                                                    Searchable input based on label

    _search_submit_dropdown                 --      Search the value in SearchResults page
                                                    and select the value

    _search_workflow                        --      Search the workflow in search box

    _open_workflow                          --      Open the workflow window

    close_form                             --      Close the opened form

    select_file                             --      Select list of files for file type input

    select_dropdown                         --      Select drop down element with label

    set_textbox_value                       --      Set value to textbox element based on label

    set_textbox_value_for_v1_form           --      Set value to textbox element based on label for v1 form

    set_multiline_value                     --      Set value to multiline input based on label

    select_radio_value                      --      Select value for radiobox based on label

    select_checkbox_value                   --      Select value for checkbox based on label

    select_listbox_value                    --      Select value for listbox type input
                                                    based on input label

    click_cancel                            --      Cancel form submission

    set_time                                --      Set the time value for time control
                                                    type input based on label

    set_calendar                            --      Set the calendar value for calendar type input

    informational_message                   --      Message displayed in informational window

    click_action_button                     --      Click the custom action button

    click_action_button_in_v1_form          --      Click the custom action button in v1 form

    set_boolean                             --      Set true or false for a boolean checkbox

    select_dropdown_list_value              --      Select list of values in dropdown input type

    get_listbox_value                       --      Show Drop down value

    get_radiobox_value                      --      Show radiobox value

    get_checkbox_value                      --      Show Checkbox value

    get_dropdown_value                      --      Retrieves the selected value for
                                                    drop-down single select type

    get_dropdown_list_value                 --      Retrieves the value list for
                                                    drop-down multi select type

    close_full_page                         --      Close the full Page form

    click_forms_full_page                   --      Click Forms link in the opened
                                                    full Page Form

    click_customize_link                    --      Click CustimizeThisForm link
                                                    in the open form

    get_action_button_labels                --      Retrieves action button

    click_ok_on_v1_form                     --      Switch driver frame for V1 form and clicks ok

    is_form_open                            --      Check if form is already open

    is_v1_form_open                         --      Check if v1 form is already open

    submit                                  --      submit the form by clicking on ok

    submit_v1_form                          --      submit the v1 form by clicking on ok

    is_form_submitted                       --      Check if form submitted successfully

    select_searchable_dropdown_value        --      Select a value for input type
                                                    of searchable,Dropdown

    open_workflow                           --      Opens the workflow

    submit_interaction                      --      Submit interaction

    is_full_page_open                       --      Check if opened form is fullPage
                                                    form or not

Actions:

    open_Action                            --      Click on the action to open it

    goto_Actions                           --      Click the Actions tab in forms application

    goto_Open_Actions                      --      Click the Open tab

    goto_Completed_Actions                 --      Click the Completed tab

"""

import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

from Web.Common.page_object import (
    WebAction,
    PageService
)

from Web.AdminConsole.Components.core import (
    CalendarView,
    Toggle
)

from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.dialog import RModalDialog

class Forms:
    """Class for representing methods of workflows page on commandcenter"""

    def __init__(self, adminconsole):
        self._adminconsole = adminconsole
        self._browser = adminconsole.browser
        self._driver = self._browser.driver

    @WebAction()
    def _get_opened_form_title(self):
        """Get the title of opened form"""
        dialog = RModalDialog(self._adminconsole)
        return dialog.title()

    @WebAction()
    def close_form(self):
        """Close the opened form"""
        dialog = RModalDialog(self._adminconsole)
        dialog.click_close()

    @WebAction()
    def _click_ok(self):
        """Click ok"""
        dialog = RModalDialog(self._adminconsole)
        dialog.click_submit()

    @WebAction()
    def _get_form_submit_message(self):
        """Get the message of submit form"""
        submit_message = self._driver.find_element(By.XPATH, 
            "//*[@id='inputFormArea']"
        ).text
        return submit_message

    @WebAction()
    def _open_search_results(self, label):
        """Opens the SearchResults page for the Searchable input based on label"""
        xpath = f"//label[text()='{label}']/..//div[@class='dropDown wfSearchable k-icon k-i-search  ']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def _search_submit_dropdown(self, value):
        """Search the value in SearchResults page and select the value"""
        xpath = f"//div[@id='searchableTable']//input[@data-testid='grid-search-input']"
        self._driver.find_element(By.XPATH, xpath).send_keys(value)
        self._adminconsole.wait_for_completion()
        input_xpath = f"//table[@class='k-grid-table']//div[text()='{value}']//ancestor::tr//input"
        input_element = self._driver.find_element(By.XPATH, input_xpath)
        input_element.click()
        self._click_ok()

    @WebAction()
    def _search_workflow(self, workflow):
        """Search the workflow in search box"""
        search_xpath = self._driver.find_element(By.XPATH, "//input[@placeholder='Search' and @type='search']")
        search_xpath.send_keys(Keys.CONTROL, 'a')
        search_xpath.send_keys(Keys.BACKSPACE)
        search_xpath.send_keys(workflow)
        search_xpath.send_keys(Keys.ENTER)

    @WebAction()
    def _open_workflow(self, workflow):
        """Open the workflow window"""
        xpath = f"//a[@title='{workflow}']"
        select_workflow = self._driver.find_element(By.XPATH, xpath)
        select_workflow.click()

    @WebAction()
    def select_file(self, label, file):
        """
        Select list of files for file type input
        Args :
            label               (String)        --      file input label
            file                (List)          --      list of files
        Example :
            select_file('Source File', ['C:\\TestXML\\1.xml', 'C:\\TestXML\\2.xml'])
        """
        xpath = f"//label[text()='{label}']" \
                f"//ancestor::div[@class='form-group field field-file']//input[@type='file'] | " \
                f"//label[text()='{label}']" \
                f"//ancestor::div[@class='form-group field field-array']//input[@type='file']"
        for option in file:
            self._driver.find_element(By.XPATH, xpath).send_keys(option)

    @WebAction()
    def select_dropdown(self, label, value):
        """
        Select drop down element with label
        Args:
            label                   (String)       --     dropdown label
            value                   (String)       --     value to be selected
        """
        drop_down = RDropDown(self._adminconsole)
        drop_down.select_drop_down_values(drop_down_label=label, values=[value])

    @WebAction()
    def set_textbox_value(self, label, value):
        """Set value to textbox element based on label
        Args:
            label               (String)        --      textbox field label
            value               (String)        --      value to be set
        """
        xpath = f"//label[contains(text(),'{label}')]/..//input[@aria-invalid='false']"
        self._driver.find_element(By.XPATH, xpath).clear()
        self._driver.find_element(By.XPATH, xpath).send_keys(value)

    @WebAction()
    def set_textbox_value_for_v1_form(self, label, value):
        """Set value to textbox element based on label for v1 form
        Args:
            label               (String)        --      textbox field label
            value               (String)        --      value to be set
        """
        frame = self._driver.find_elements(By.XPATH, "//iframe")
        self._driver.switch_to.frame(frame[0])
        self._driver.find_element(By.XPATH, "//*[@id='{0}']".format(label)).send_keys(value)
        self._driver.switch_to.default_content()

    @WebAction()
    def set_multiline_value(self, label, value):
        """Set value to multiline input based on label
        Args:
            label               (String)        --      multiline field label
            value               (String)        --      value to be set
        """
        xpath = f"//*[contains(text(),'{label}')]/..//textarea[@aria-invalid='false']"
        self._driver.find_element(By.XPATH, xpath).clear()
        self._driver.find_element(By.XPATH, xpath).send_keys(value)

    @WebAction()
    def select_radio_value(self, label, value):
        """Select value for radiobox based on label
        Args:
            label               (String)        --      radiobox label
            value               (String)        --      value to click
        """
        xpath = f"//label[text()='{label}']//ancestor::div[@class='form-group field field-string']" \
                f"//span[text()='{value}']/..//input[@type='radio']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def select_checkbox_value(self, label, value):
        """Select value for checkbox based on label
        Args:
            label               (String)        --      Checkbox label
            value               (String)        --      value to click
        """
        xpath = f"//label[text()='{label}']//ancestor::div[@class='form-group field field-string']" \
                f"//span[text()='{value}']/..//input[@type='checkbox']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def select_listbox_value(self, label, value):
        """Select value for listbox type input based on input label
        Args:
            label               (String)        --      listbox input label
            value               (String)        --      value to select
        """
        xpath = f"//label[text()='{label}']//ancestor::div[@class='form-group field field-string']" \
                f"//select[@class='form-control list-box']//option[text()='{value}']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def click_cancel(self):
        """Cancel form submission"""
        dialog = RModalDialog(self._adminconsole)
        dialog.click_cancel()

    @WebAction()
    def set_time(self, label, value):
        """Set the time value for time control type input based on label
        Args:
            label               (String)        --      Time input field label
            value               (String)        --      time value
                                                        Eg : '03:45 pm'
        """
        xpath = f"//label[contains(@title,'{label}')]//ancestor::div[@class='form-group field field-string']" \
                f"//input[@placeholder='hh:mm (a|p)m']"
        self._driver.find_element(By.XPATH, xpath).send_keys(Keys.CONTROL + "a")
        self._driver.find_element(By.XPATH, xpath).send_keys(Keys.DELETE)
        self._driver.find_element(By.XPATH, xpath).send_keys(value)

    @WebAction()
    def set_calendar(self, label, value):
        """Set the date and time value for calendar control type input based on label
        Args:
            label               (String)        --      calendar input field label
            value               (String)        --      calendar value in mm/dd/yyyy hh:mm AM
                                                        Eg : '09/23/2021 09:30 PM'
        """
        calendar = CalendarView(self._adminconsole)
        month_abbr = {
            "01": "january",
            "02": "february",
            "03": "march",
            "04": "april",
            "05": "may",
            "06": "june",
            "07": "july",
            "08": "august",
            "09": "september",
            "10": "october",
            "11": "november",
            "12": "december"
        }
        xpath = f"//label[text()='{label}']//ancestor::div[@class='form-group field field-string']" \
                f"//button[@title='Open calendar']"
        self._driver.find_element(By.XPATH, xpath).click()
        year = int(value.split(' ')[0].split('/')[2])
        month = month_abbr[value.split(' ')[0].split('/')[0]]
        day = int(value.split(' ')[0].split('/')[1])
        date_dict = {
                        'year': year,
                        'month': month,
                        'day': day,
                    }
        calendar.select_date(date_time_dict=date_dict)
        session = value.split(' ')[2]
        minute = int((value.split(' ')[1]).split(':')[1])
        hour = int((value.split(' ')[1]).split(':')[0])
        time_dict = {
                        'hour': hour,
                        'minute': minute,
                        'session': session
                     }
        calendar.select_time(time_dict=time_dict)
        calendar.set_date()

    @WebAction()
    def click_action_button(self, button):
        """Click the custom action button
        button              (String)        --      Custom action name
        Eg:
        Popup Input, UserInput can have custom action like Approve,Deny
        """
        xpath = f"//div[contains(text(),'{button}')]//ancestor::button"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def click_action_button_in_v1_form(self, button):
        """Click the custom action button in v1 form
        button              (String)        --      Custom action name
        Eg:
        Popup Input, UserInput can have custom action like Approve,Deny
        """
        frame = self._driver.find_elements(By.XPATH, "//iframe")
        self._driver.switch_to.frame(frame[0])
        self._driver.find_element(By.XPATH, "//a[@id='{0}']".format(button)).click()
        self._driver.switch_to.default_content()

    @WebAction()
    def set_boolean(self, label, value):
        """Set true or false for a boolean checkbox
        Args:
            label               (String)        --      Input name
            value               (String)        --      true or false
        """
        toggle = Toggle(self._adminconsole)
        if value == 'true':
            toggle.enable(label=label)
        else:
            toggle.disable(label=label)

    @WebAction()
    def select_dropdown_list_value(self, label, value):
        """Select list of values in dropdown input type
            Args:
                label           (String)        --      Input name
                value           (list)        --      Input value

            Eg:
                select_dropdown_list_value("your label", ["value1", "value2"])

        """
        drop_down = RDropDown(self._adminconsole)
        drop_down.select_drop_down_values(drop_down_label=label, values=value)

    @WebAction()
    def get_listbox_value(self, label):
        """Show Drop down value"""
        xpath = f"//label[text()='{label}']//ancestor::div[@class='form-group field field-string']" \
                f"//select[@class='form-control list-box']//option"
        drop_values = []
        for option in self._driver.find_elements(By.XPATH, xpath):
            drop_values.append(option.get_attribute('innerHTML'))
        return drop_values

    @WebAction()
    def get_radiobox_value(self, label):
        """Show radiobox value"""
        xpath = f"//label[text()='{label}']//ancestor::div[@class='form-group field field-string']" \
                f"//div[@class='radioButtons  horizontal']" \
                f"//span[contains(@class,'MuiTypography-root')]"
        radio_values = []
        for option in self._driver.find_elements(By.XPATH, xpath):
            radio_values.append(option.get_attribute('innerHTML'))
        return radio_values

    @WebAction()
    def get_checkbox_value(self, label):
        """Show Checkbox value"""
        xpath = f"//label[text()='{label}']//ancestor::div[@class='form-group field field-string']" \
                f"//div[@class='checkboxes horizontal']" \
                f"//span[contains(@class,'MuiTypography-root')]"
        checkbox_values = []
        for option in self._driver.find_elements(By.XPATH, xpath):
            checkbox_values.append(option.get_attribute('innerHTML'))
        return checkbox_values

    @WebAction()
    def get_dropdown_value(self, label):
        """Retrieves the selected value for drop-down single select type
            Args:
                label           (String)        --      dropdown label
            Returns:
                (String/None)   --      Selected value or None if field is empty/xpath is not found
        """
        xpath = f"//label[contains(text(),'{label}')]/..//li"
        try:
            return self._driver.find_element(By.XPATH, xpath).text
        except NoSuchElementException:
            return None

    @WebAction()
    def get_dropdown_list_value(self, label):
        """Retrieves the value list for drop-down multi select type
            Args:
                label           (String)        --      Input name

            Eg:
                get_dropdown_list_value("your label")
        """
        value = []
        drop_down = RDropDown(self._adminconsole)
        for option in drop_down.get_values_of_drop_down(drop_down_label=label):
            value.append(option)
        return value

    @WebAction()
    def informational_message(self):
        """
        Message displayed in informational window
        Returns:
            (String)        --      Informational messagedropdownDN
        """
        msg = self._driver.find_element(By.XPATH, "//div[@class='sc-kRktcz tPDBS wfInfoArea']").text
        return msg

    @WebAction()
    def close_full_page(self):
        """Clicks the close button in fullPage form"""
        dialog = RModalDialog(self._adminconsole)
        dialog.click_close()

    @WebAction()
    def click_forms_full_page(self):
        """Clicks the Forms link in the opened full page form"""
        self._driver.find_element(By.XPATH, 
            "//*[@class='wfFullPageForm']//../*[@id='wfBaseUrlTitle']/a"
        ).click()

    @WebAction()
    def click_customize_link(self):
        """Clicks the CustomizeThisForm link in the open form"""
        self._driver.find_element(By.XPATH, 
            "//*[@id='wfCustomizeThisForm']/a"
        ).click()

    @WebAction()
    def is_full_page_open(self, form_name):
        """Checks whether the opened form is fullpage or not"""
        self._adminconsole.wait_for_completion()
        time.sleep(2)  # For the Title to fade into context
        xpath = f"//div[@class='modal-dialog modal-centered modal-full-page " \
                f"workflow-full-page modal-md modal-dialog-scrollable']//h4[text()='{form_name}']"
        if self._driver.find_element(By.XPATH, xpath):
            return True

    @WebAction()
    def get_action_button_labels(self):
        """Returns the Action button
        Returns
            List of Action button labels
        """
        xpath = "//div[contains(@class,'modal-footer')]//div[@class='sc-dIouRR gtmhjP']"
        return [buttons.text for buttons in self._driver.find_elements(By.XPATH, xpath) if buttons]

    @WebAction()
    def click_ok_on_v1_form(self):
        """Switch driver frame for V1 form and clicks ok"""
        frame = self._driver.find_elements(By.XPATH, "//iframe")
        self._driver.switch_to.frame(frame[0])
        self._driver.find_element(By.XPATH, "//a[@id='okButton']").click()
        self._driver.switch_to.default_content()

    @PageService()
    def is_form_open(self, form_name):
        """Check if form is already open"""
        time.sleep(5)  # For the Title to fade into context
        form_title = self._get_opened_form_title()
        return form_title.lower() == form_name.lower()

    @PageService()
    def is_v1_form_open(self, form_name):
        """Check if v1 form is already open"""
        self._adminconsole.wait_for_completion()
        try:
            self._driver.find_element(By.XPATH, "//span[text() = '{0}']".format(form_name))
        except NoSuchElementException:
            return False
        return True

    @PageService()
    def submit(self):
        """submit the form by clicking on ok"""
        self._click_ok()
        self._adminconsole.wait_for_completion()

    @PageService()
    def submit_v1_form(self):
        """submit the v1 form by clicking on ok"""
        self.click_ok_on_v1_form()

    @PageService()
    def is_form_submitted(self):
        """Check if form submitted successfully"""
        self._adminconsole.wait_for_completion()
        time.sleep(2)
        submit_title = self._get_opened_form_title()
        if submit_title == "Message":
            submit_message = self._get_form_submit_message()
            return submit_message == "Your form has been submitted"
        else:
            return False

    @PageService()
    def select_searchable_dropdown_value(self, label, value):
        """Select a value for input type of searchable,Dropdown"""
        self._open_search_results(label)
        self._adminconsole.wait_for_completion()
        self._search_submit_dropdown(value)

    @PageService()
    def open_workflow(self, workflow):
        """Opens the workflow"""
        self._search_workflow(workflow)
        self._open_workflow(workflow)
        self._adminconsole.wait_for_completion()

    @PageService()
    def submit_interaction(self, label):
        """Submit interaction"""
        actions = Actions(self._adminconsole)
        actions.goto_Actions()
        actions.goto_Open_Actions()
        xpath = f"//a[text()='{label}']"
        self._driver.find_element(By.XPATH, xpath).click()


class Actions:
    """Class for representing methods of Approvals page on commandcenter"""

    def __init__(self, adminconsole):
        self._adminconsole = adminconsole
        self._browser = adminconsole.browser
        self._driver = self._browser.driver

    @WebAction()
    def open_Action(self, action):
        """Open the Action"""
        link = self._driver.find_element(By.LINK_TEXT, action)
        link.click()

    @WebAction()
    def goto_Actions(self):
        """Navigate to approvals page"""
        self._adminconsole.navigator.navigate_to_approvals()
        self._adminconsole.wait_for_completion()

    @WebAction()
    def goto_Open_Actions(self):
        """Click the Open tab """
        self._driver.find_element(By.XPATH, "//button[@role='tab' and text()='Open']").click()
        self._adminconsole.wait_for_completion()

    @WebAction()
    def goto_Completed_Actions(self):
        """Click the Completed tab"""
        self._driver.find_element(By.XPATH, "//button[@role='tab' and text()='Completed']").click()
        self._adminconsole.wait_for_completion()
        self._driver.refresh()
        self._adminconsole.wait_for_completion()