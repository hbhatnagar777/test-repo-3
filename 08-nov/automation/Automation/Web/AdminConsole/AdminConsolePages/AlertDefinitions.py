# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
alert definitions tab on the Alerts page on the AdminConsole

Class:

    AlertDefinitions()

Functions:

create_alert_definition()           --   Method to Add a new alert definition

delete_alert_definition()           --   Method to delete an alert definition

enable_alert_definition()           --   Method to enable an alert definition

disable_alert_definition()          --   Method to disable an alert definition

select_alert()                      --   Method to open an alert definition

get_alert_definitions()             --   Method to get all the alert definitions associated to a logged in user

get_alert_definitions_for_company() --   Method to get all the alert definitions associated to a company



Class:
    
    RAlertDefinitions()

Functions:

    delete_alert_definition()                   --          Method to delete alert definition

    __select_alert_checkbox()                   --          Select alert_checkbox

    __deselect_alert_checkbox()                 --          De-Select alert_checkbox

    enable_alert_definition()                   --          Enables the alert definition

    disable_alert_definition()                  --          Disables a alert definition

    select_alert()                              --          Method to open alert details

    get_alert_definitions()                     --          Method to get all the alert definitions associated to a logged in user

    get_alert_definitions_for_company()         --          Method to get all the alert definitions associated to a company

    __process_input()                           --          Process input data

    __process_dropdown()                        --          Process dropdown data

    __process_toggle()                          --          Process toggle data

    __process_checkbox()                        --          Process checkbox data

    __process_combobox()                        --          Process combobox data

    __process_treeview()                        --          Process treeview data

    __switch_iframe_and_fill_content()          --          Switch to iframe and fill content in template page

    create_alert_definition()                   --          Method to create alert definition



Class:
    
    RAlertDefinitions()

Functions:

    delete_alert_definition()                   --          Method to delete alert definition

    __select_alert_checkbox()                   --          Select alert_checkbox

    __deselect_alert_checkbox()                 --          De-Select alert_checkbox

    enable_alert_definition()                   --          Enables the alert definition

    disable_alert_definition()                  --          Disables a alert definition

    select_alert()                              --          Method to open alert details

    get_alert_definitions()                     --          Method to get all the alert definitions associated to a logged in user

    get_alert_definitions_for_company()         --          Method to get all the alert definitions associated to a company

    __process_input()                           --          Process input data

    __process_dropdown()                        --          Process dropdown data

    __process_toggle()                          --          Process toggle data

    __process_checkbox()                        --          Process checkbox data

    __process_combobox()                        --          Process combobox data

    __process_treeview()                        --          Process treeview data

    __switch_iframe_and_fill_content()          --          Switch to iframe and fill content in template page

    create_alert_definition()                   --          Method to create alert definition

"""
from selenium.webdriver.common.by import By

import time
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.wizard import Wizard
from Web.Common.page_object import PageService, WebAction
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.Components.core import Toggle, TreeView, Checkbox
from Web.AdminConsole.Components.panel import RDropDown
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException


class AlertDefinitions:
    """
    This module provides the function or operations that can be performed on the
    alert definitions tab on the Alerts page on the AdminConsole
    """

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__table = Table(admin_console)
        self.log = admin_console.log
        self.driver = admin_console.driver

    @WebAction()
    def __get_collapsed_server_elements(self):
        """ Return collapsed server elements"""
        collapsed_elements = self.driver.find_elements(By.XPATH, 
                "//button[@class='collapsed']")
        return collapsed_elements

    @WebAction()
    def __get_serverlist_entities(self):
        """ Return server list entity list"""
        server_list_entities = self.driver.find_element(By.XPATH, 
                                "//div[@class='browse-tree alerts-browse']")
        return server_list_entities

    @WebAction()
    def __select_server_entity(self, value, entities):
        """ Selects the given server entity"""
        entities.find_element(By.XPATH, 
            "//span[./text()='" + str(value) + "']").click()

    @WebAction()
    def __fill_to_input(self, value):
        """Fills the to input field"""
        self.driver.find_element(By.XPATH, 
            "//div[@id='s2id_toUserList']/ul/li/input").send_keys(value)

    @WebAction()
    def __fill_cc_input(self, value):
        """Fills the cc input field"""
        self.driver.find_element(By.XPATH, 
            "//div[@id='s2id_ccUserList']/ul/li/input").send_keys(value)

    @WebAction()
    def __fill_bcc_input(self, value):
        """Fills the bcc input field"""
        self.driver.find_element(By.XPATH, 
            "//div[@id='s2id_bccUserList']/ul/li/input").send_keys(value)

    @WebAction()
    def __select_user_entity(self, value):
        """Selects the user entity"""
        self.driver.find_element(By.XPATH, "//span[@class='user-type plan-user-suggestion' and contains\
                                            (text(),' (" + str(value) + ")" + "')]").click()

    @WebAction()
    def __select_group_entity(self, value):
        """Selects the group entity"""
        self.driver.find_element(By.XPATH, "//span[@class='group-type plan-user-suggestion' and contains\
                                            (text(),' (" + str(value) + ")" + "')]").click()

    @WebAction()
    def __select_email_entity(self, value):
        """Selects the email entity"""
        self.driver.find_element(By.XPATH, "//span[@class='email-type plan-user-suggestion' and contains\
                                            (text(),'" + str(value) + "')]").click()

    @WebAction()
    def __select_email_dropdown(self):
        """Select the email dropdown"""
        self.driver.find_element(By.XPATH, "//div[@id='select2-drop-mask']").click()

    @WebAction()
    def __get_error_text(self):
        """Returns the error text message"""
        text = self.driver.find_element(By.XPATH, "//span[@class='server-message error']").text
        return text

    @WebAction()
    def __click_error_close_button(self):
        """Clicks the error message close button"""
        self.driver.find_element(By.XPATH, "//button[@class='btn btn-default cvBusyOnAjax']").click()

    @WebAction()
    def __button_next(self, step_number):
        """
            Clicks the Next button on addAlertDefinitionForm template
        Args:
            step_number: The step at which we are in creating alert definition. (Step starts at 1)
        """
        self.driver.find_element(By.XPATH, f"(//button[contains(.,'Next')])[{step_number}]").click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def create_alert_definition(self,
                                alert_name,
                                alert_type,
                                to_recipients,
                                cc_recipients,
                                bcc_recipients,
                                value_of_x,
                                alert_entities,
                                alert_target,
                                ind_notification=None,
                                alert_locale=None,
                                mail_subject=None):
        """
        Function to create Alert Definition

        Args:
            alert_name      (str)       : Name of alert to be created

            alert_type      (str)       : Type of alert to be created

            to_recipients  (dict)       : user, user group or email to be added to alert
                                            recipients list
                Eg. to_recipients = {"Group":["master"],
                                     "Email":["jrana@commvault.com"],
                                     "User":["admin"]}

            bcc_recipients  (dict)      : user, user group or email to be added to alert
                                            recipients list
                Eg. to_recipients = {"Group":["master"],
                                     "Email":["jrana@commvault.com"],
                                     "User":["admin"]}

            cc_recipients    (dict)     : user, user group or email to be added to alert
                                            recipients list
                Eg. to_recipients = {"Group":["master"],
                                     "Email":["jrana@commvault.com"],
                                     "User":["admin"]}

            value_of_x        (integer) : value for days/time/percent based on alert selected

            alert_entities    (list)    : server groups or clients for which alert is to be
                                            defined
                Eg. alert_entities = ["Server groups", "Clients"]

            alert_target      (dict)    : dict containing values if alert targets be
                                            enabled/disabled
                Eg. alert_target = {'Email':True, 'Event viewer':True,
                                    'Console':True, 'SNMP':True}

            ind_notification  (str)    :  individual notification to be enabled/disabled
                Eg. - ind_notification = 'ON'

            alert_locale      (str)    :   alert locale to be selected
                Eg. - 'English'

            mail_subject      (str)    :   subject line for the mailer to be updated
                Eg. - 'Test Alert'

        Returns:
            None

        Raises:
            Exception:
                -- if fails to create alert definition
        """

        to_list = []
        cc_list = []
        bcc_list = []

        for group in to_recipients['Group']:
            to_list.append(group)
        for user in to_recipients['User']:
            to_list.append(user)
        for email in to_recipients['Email']:
            to_list.append(email)
        for group in cc_recipients['Group']:
            cc_list.append(group)
        for user in cc_recipients['User']:
            cc_list.append(user)
        for email in cc_recipients['Email']:
            cc_list.append(email)
        for group in bcc_recipients['Group']:
            bcc_list.append(group)
        for user in bcc_recipients['User']:
            bcc_list.append(user)
        for email in bcc_recipients['Email']:
            bcc_list.append(email)

        self.__admin_console.access_menu("Add alert definition")
        self.__admin_console.wait_for_completion()

        self.__admin_console.fill_form_by_id("alertName", alert_name)

        self.__admin_console.cv_single_select('Alert type', alert_type)

        if self.__admin_console.check_if_entity_exists("id", "alertParam"):
            self.__admin_console.fill_form_by_id("alertParam", value_of_x)

        if ind_notification == 'ON':
            self.__admin_console.enable_toggle(toggle_id='alertNotifIndividual')
        else:
            self.__admin_console.disable_toggle(toggle_id='alertNotifIndividual')

        self.__button_next(1)

        if self.__admin_console.check_if_entity_exists(
                "xpath", "//button[@class='collapsed']"):
            collapsed_elems = self.__get_collapsed_server_elements()
            for elem in collapsed_elems:
                elem.click()
            entities = self.__get_serverlist_entities()
        for value in alert_entities['server_group_list']:
            self.__select_server_entity(value, entities)
        for value in alert_entities['server_list']:
            self.__select_server_entity(value, entities)
        self.__admin_console.wait_for_completion()

        self.__button_next(2)

        if alert_target:
            if alert_target['Email']:
                self.__admin_console.checkbox_select('alertNotifTypeEmail')

                if to_list:
                    self.log.info("Adding recipients in TO LIST")
                    for value in to_list:
                        self.__fill_to_input(value)
                        self.__admin_console.wait_for_completion()
                        if self.__admin_console.check_if_entity_exists(
                                "xpath", "//span[@class='group-type plan-user-suggestion' and \
                            contains(text(),' ("+str(value)+")"+"')]"):
                            self.__select_group_entity(value)
                        elif self.__admin_console.check_if_entity_exists(
                                "xpath", "//span[@class='user-type plan-user-suggestion' and \
                            contains(text(),' ("+str(value)+")"+"')]"):
                            self.__select_user_entity(value)
                        elif self.__admin_console.check_if_entity_exists(
                                "xpath", "//span[@class='email-type plan-user-suggestion' and \
                            contains(text(),'"+str(value)+"')]"):
                            self.__select_email_entity(value)
                        self.__admin_console.wait_for_completion()

                if cc_list:
                    self.log.info("Adding recipients in CC LIST")
                    for value in cc_list:
                        self.__fill_cc_input(value)
                        self.__admin_console.wait_for_completion()
                        if self.__admin_console.check_if_entity_exists(
                                "xpath", "//span[@class='group-type plan-user-suggestion' and \
                            contains(text(),' ("+str(value)+")"+"')]"):
                            self.__select_group_entity(value)
                        elif self.__admin_console.check_if_entity_exists(
                                "xpath", "//span[@class='user-type plan-user-suggestion' and \
                            contains(text(),' ("+str(value)+")"+"')]"):
                            self.__select_user_entity(value)
                        elif self.__admin_console.check_if_entity_exists(
                                "xpath", "//span[@class='email-type plan-user-suggestion' and \
                            contains(text(),'"+str(value)+"')]"):
                            if self.__admin_console.check_if_entity_exists(
                                    "xpath", "//div[@id='select2-drop-mask']"):
                                self.__select_email_dropdown()
                            self.__select_email_entity(value)
                        self.__admin_console.wait_for_completion()

                if bcc_list:
                    self.log.info("Adding recipients in BCC LIST")
                    for value in bcc_list:
                        self.__fill_bcc_input(value)
                        self.__admin_console.wait_for_completion()
                        if self.__admin_console.check_if_entity_exists(
                                "xpath", "//span[@class='group-type plan-user-suggestion' and \
                            contains(text(),' ("+str(value)+")"+"')]"):
                            self.__select_group_entity(value)
                        elif self.__admin_console.check_if_entity_exists(
                                "xpath", "//span[@class='user-type plan-user-suggestion' and \
                            contains(text(),' ("+str(value)+")"+"')]"):
                            self.__select_user_entity(value)
                        elif self.__admin_console.check_if_entity_exists(
                                "xpath", "//span[@class='email-type plan-user-suggestion' and \
                            contains(text(),'"+str(value)+"')]"):
                            if self.__admin_console.check_if_entity_exists(
                                    "xpath", "//div[@id='select2-drop-mask']"):
                                self.__select_email_dropdown()
                            self.__select_email_entity(value)
                        self.__admin_console.wait_for_completion()
            else:
                self.__admin_console.checkbox_deselect('alertNotifTypeEmail')

            if alert_target['Event viewer']:
                self.__admin_console.checkbox_select('alertNotifTypeEV')
            else:
                self.__admin_console.checkbox_deselect('alertNotifTypeEV')

            if alert_target['Console']:
                self.__admin_console.checkbox_select('alertNotifTypeCA')
                if not alert_target['Email']:
                    if to_list:
                        self.log.info("Adding recipients in TO LIST")
                        for value in to_list:
                            self.__fill_to_input(value)
                            self.__admin_console.wait_for_completion()
                            if self.__admin_console.check_if_entity_exists(
                                    "xpath", "//span[@class='group-type plan-user-suggestion' and \
                                contains(text(),' ("+str(value)+")"+"')]"):
                                self.__select_group_entity(value)
                            elif self.__admin_console.check_if_entity_exists(
                                    "xpath", "//span[@class='user-type plan-user-suggestion' and \
                                contains(text(),' ("+str(value)+")"+"')]"):
                                self.__select_user_entity(value)
                            elif self.__admin_console.check_if_entity_exists(
                                    "xpath", "//span[@class='email-type plan-user-suggestion' and \
                                contains(text(),'"+str(value)+"')]"):
                                if self.__admin_console.check_if_entity_exists(
                                        "xpath", "//div[@id='select2-drop-mask']"):
                                    self.__select_email_dropdown()
                                self.__select_email_entity(value)
                            self.__admin_console.wait_for_completion()
            else:
                self.__admin_console.checkbox_deselect('alertNotifTypeCA')

            if alert_target['SNMP']:
                self.__admin_console.checkbox_select('alertNotifTypeSNMP')
            else:
                self.__admin_console.checkbox_deselect('alertNotifTypeSNMP')

        self.__button_next(3)

        if alert_locale:
            self.__admin_console.select_value_from_dropdown("alertLocale", alert_locale)
        if mail_subject:
            self.__admin_console.fill_form_by_id("alertNotifEmailSub", mail_subject)

        self.__admin_console.submit_form()
        self.__admin_console.wait_for_completion()

        if self.__admin_console.check_if_entity_exists(
                "xpath", "//span[@class='server-message error']"):
            exp = self.__get_error_text()
            if "doesn't have [Create Alert] permission" in exp:
                self.__click_error_close_button()
            else:
                self.__click_error_close_button()
                raise CVWebAutomationException(exp)
        self.__admin_console.check_error_message()

    @PageService()
    def delete_alert_definition(self, alert_name):
        """
        Method to delete alert definition

        Args:
           alert_name (string): Name of the alert to be deleted

        Returns:
            None

        Raises:
            Exception:
                -- if fails to delete the alert
        """
        self.__table.access_context_action_item(alert_name, 'Delete')
        self.__admin_console.click_button_using_text('Yes')
        time.sleep(1)
        notif_text = self.__admin_console.get_notification()
        if len(notif_text) == 0:
            exp = "Delete Alert confirmation message is not displayed"
            raise CVWebAutomationException(exp)

    @WebAction()
    def __select_alert_checkbox(self, alert_name):
        """
        Select alert_checkbox
        Args:
            alert_name (string) : name of the alert to be selected

            Raise:
                Exception if element is not present.
        """
        if self.__admin_console.check_if_entity_exists("xpath", "//a[contains(text(),'" + alert_name + "')]"):
            status_check_box = self.driver.find_element(By.XPATH, '//input[@class="status-checkbox"]')
            status_check_box_container = self.driver.find_element(By.XPATH, '//a[@class="k-grid-status"]')
            if not status_check_box.is_selected():
                status_check_box_container.click()
        else:
            exp = "Alert {} not present".format(alert_name)
            raise CVWebAutomationException(exp)

    @WebAction()
    def __deselect_alert_checkbox(self, alert_name):
        """
        De-Select alert_checkbox
        Args:
            alert_name (string) : name of the alert to be de-selected

            Raise:
                Exception if element is not present.
        """
        if self.__admin_console.check_if_entity_exists("xpath", "//a[contains(text(),'" + alert_name + "')]"):
            status_check_box = self.driver.find_element(By.XPATH, '//input[@class="status-checkbox"]')
            status_check_box_container = self.driver.find_element(By.XPATH, '//a[@class="k-grid-status"]')
            if status_check_box.is_selected():
                status_check_box_container.click()
        else:
            exp = "Alert {} not present".format(alert_name)
            raise CVWebAutomationException(exp)

    @PageService()
    def enable_alert_definition(self, alert_name):
        """Enables the alert definition

          Args:
                alert_name (string) : name of the alert to be disabled
        """
        self.__table.search_for(alert_name)
        self.__select_alert_checkbox(alert_name)

    @PageService()
    def disable_alert_definition(self, alert_name):
        """
        Disables a alert definition

        Args:
            alert_name (string) : name of the alert to be disabled
        """
        self.__table.search_for(alert_name)
        self.__deselect_alert_checkbox(alert_name)

    @PageService()
    def select_alert(self, alert_name):
        """
        Method to open alert details

        Args:
            alert_name (string) : Name of the alert to be opened

        Returns:
            None

        Raises:
            Exception:
                -- if fails to open alert details
        """
        self.__table.access_link(alert_name)

    @PageService()
    def get_alert_definitions(self):
        """Method to get all the alert definitions associated to a logged in user

        Returns:
            list of alerts associated to the logged in user
        """
        alerts = self.__table.get_column_data('Name')
        return alerts

    @PageService()
    def get_alert_definitions_for_company(self, company_name):
        """Method to get all the alert definitions associated to a company

        Use this method only when logged in as MSP admin
        Args:
            company_name (string) : Name of the company for which alerts are to extracted

        Returns:
            list of alerts associated to a company
        """
        self.__table.view_by_title(company_name)
        alerts = self.__table.get_column_data("Name")
        return alerts


class RAlertDefinitions:

    """
    This module provides the function or operations that can be performed on the
    alert definitions tab on the Alerts page on the AdminConsole for the new React framework
    """

    def __init__(self, admin_console):
        """
        Initializes the RAlertDefinitions class
        
        Args:
            admin_console   (object)    --  instance of the AdminConsole class
            
        """
        self.__admin_console = admin_console
        self.__admin_console.load_properties(self, unique=True)
        self.ad = admin_console
        self.__table = Rtable(admin_console)
        self.__page_container = PageContainer(admin_console)
        self.log = admin_console.log
        self.driver = admin_console.driver
        self.__wizard = Wizard(admin_console)
        self.__dialog = RModalDialog(admin_console)
        self.__toggle = Toggle(admin_console)
        self.__treeview = TreeView(admin_console)
        self.__dropdown = RDropDown(admin_console)
        self.__checkbox = Checkbox(admin_console)
        self.__alert = Alert(admin_console)
        self.__driver = self.__admin_console.driver

    @PageService()
    def delete_alert_definition(self, alert_name):
        """
        Method to delete alert definition

        Args:
           alert_name (string): Name of the alert to be deleted

        Returns:
            None

        Raises:
            Exception:
                -- if fails to delete the alert
        """
        self.__table.access_action_item(entity_name=alert_name, action_item=self.__admin_console.props["RAlertDefinitions"]["label.delete"])
        self.__dialog.click_yes_button()
        time.sleep(1)
        notif_text = self.__admin_console.get_notification()
        if len(notif_text) == 0:
            exp = "Delete Alert confirmation message is not displayed"
            raise CVWebAutomationException(exp)

    @WebAction()
    def __select_alert_checkbox(self, alert_name):
        """
        Select alert_checkbox
        Args:
            alert_name (string) : name of the alert to be selected

            Raise:
                Exception if element is not present.
        """
        try:
            self.__toggle.enable(id='statusValue')
        except:
            exp = "Alert {} not present".format(alert_name)
            raise CVWebAutomationException(exp)

    @WebAction()
    def __deselect_alert_checkbox(self, alert_name):
        """
        De-Select alert_checkbox
        Args:
            alert_name (string) : name of the alert to be de-selected

            Raise:
                Exception if element is not present.
        """
        try:
            self.__toggle.disable(id='statusValue')

        except:
            exp = "Alert {} not present".format(alert_name)
            raise CVWebAutomationException(exp)

    @PageService()
    def enable_alert_definition(self, alert_name):
        """Enables the alert definition

          Args:
                alert_name (string) : name of the alert to be disabled
        """
        self.__table.search_for(alert_name)
        self.__select_alert_checkbox(alert_name)

    @PageService()
    def disable_alert_definition(self, alert_name):
        """
        Disables a alert definition

        Args:
            alert_name (string) : name of the alert to be disabled
        """
        self.__table.search_for(alert_name)
        self.__deselect_alert_checkbox(alert_name)

    @PageService()
    def select_alert(self, alert_name):
        """
        Method to open alert details

        Args:
            alert_name (string) : Name of the alert to be opened

        Returns:
            None

        Raises:
            Exception:
                -- if fails to open alert details
        """
        self.__table.access_link(alert_name)

    @PageService()
    def get_alert_definitions(self):
        """Method to get all the alert definitions associated to a logged in user

        Returns:
            list of alerts associated to the logged in user
        """
        alerts = self.__table.get_column_data('Name')
        return alerts

    @PageService()
    def get_alert_definitions_for_company(self, company_name):
        """Method to get all the alert definitions associated to a company

        Use this method only when logged in as MSP admin
        Args:
            company_name (string) : Name of the company for which alerts are to extracted

        Returns:
            list of alerts associated to a company
        """
        self.__table.view_by_title(company_name)
        alerts = self.__table.get_column_data("Name")
        return alerts
    
    def __process_input(self, input_data):
        """
        Process input data
        Args:
            input_data (list) : input data 
                                example ->[
                                    {'id': 'id', 'label': 'label', 'text_to_fill': 'text_to_fill'},
                                    {'id': 'id', 'label': 'label', 'text_to_fill': 'text_to_fill'}
                                    ]
            Returns:
                None
        """
        for dicts in input_data:
            input_id = dicts.get('id')
            input_label = dicts.get('label')
            text_to_fill = dicts.get('text_to_fill')
            self.__wizard.fill_text_in_field(id=input_id, label=input_label, text=text_to_fill)
    
    def __process_dropdown(self, dropdown_data):
        """
        Process dropdown data
        Args:
            dropdown_data (list) : dropdown data
                                   example-> [
                                    {'id': 'id', 'options_to_select': ['option1', 'option2']},
                                    {'id': 'id', 'options_to_select': ['option3', 'option4']}
                                    ]
            Returns:
                None
        """
        for dicts in dropdown_data:
            dropdown_id = dicts.get('id')
            options_to_select = dicts.get('options_to_select')
            self.__wizard.select_drop_down_values(values=options_to_select, id=dropdown_id)
    
    def __process_toggle(self, toggle_data):
        """
        Process toggle data
        Args:
            toggle_data (list) : toggle data
                                 example-> [
                                    {'id': 'id'},
                                    {'label': 'label'}
                                    ]
            Returns:
                None
        """
        for dicts in toggle_data:
            toggle_id = dicts.get('id')
            toggle_label = dicts.get('label')
            self.__toggle.enable(id=toggle_id, label=toggle_label)
    
    def __process_checkbox(self, checkbox_data):
        """
        Process checkbox data
        Args:
            checkbox_data (list) : checkbox data
                                   example-> [
                                    {'id': 'id'},
                                    {'label': 'label'}
                                    ]
            Returns:
                None
        """
        for dicts in checkbox_data:
            checkbox_id = dicts.get('id')
            checkbox_label = dicts.get('label')
            self.__checkbox.check(checkbox_label, checkbox_id)
    
    def __process_combobox(self, combobox_data):
        """
        Process combobox data
        Args:
            combobox_data (list) : combobox data
                                   example->[
                                                {'id': 'id', 'label': 'label', 'options_to_select': ['option1', 'option2']},
                                                {'id': 'id', 'label': 'label', 'options_to_select': ['option1', 'option2']}
                                            ]
            Returns:
                None
        """
        for dicts in combobox_data:
            combobox_id = dicts.get('id')
            combobox_label = dicts.get('label')
            options_to_select = dicts.get('options_to_select')
            for option in options_to_select:
                self.__dropdown.search_and_select(id=combobox_id, label=combobox_label, select_value=option)
    
    def __process_treeview(self, treeview_data):
        """
        Process treeview data
        Args:
            treeview_data (dict) : treeview data
                                   example-> [name1, name2, etc]
            Returns:
                None
        """
        self.__treeview.select_items(treeview_data)
    
    def __switch_iframe_and_fill_content(self, content):
        """
        Switch to iframe and fill content in template page
        Args:
            content (str) : content to fill
        Returns:
            None
        """
        self.__driver.switch_to.frame(self.__driver.find_element(By.XPATH, "//iframe[@class='k-iframe']"))
        try:
            alert_template = self.__driver.find_element(By.ID, "contentTbl-table-scroll")
        except NoSuchElementException:
            alert_template = self.__driver.find_element(By.XPATH, "/html/body/div")
        alert_template.send_keys(Keys.CONTROL, 'a')
        alert_template.send_keys(content)
        self.__admin_console.wait_for_completion()
        self.__driver.switch_to.default_content()
    
    def __process_email(self, email_data):
        """ Process email data
        Args:
            email_data (dict) : email data
                                example->{
                                    "to": ["user1", "user2"],
                                    "cc": ["user3", "user4"],
                                    "bcc": ["user5", "user6"],
                                    "format": "HTML" (or) "Text",
                                    "subject": "subject",
                                    "content": "content"
                                }
        Returns:
            None
        """
        to = email_data.get("to")
        cc = email_data.get("cc")
        bcc = email_data.get("bcc")
        notif_format = email_data.get("format")
        subject = email_data.get("subject")
        content = email_data.get("content")
        if to:
            self.__process_combobox([{"id": "toUsersAutoComplete", "options_to_select": to}])
        if cc:
            self.__process_combobox([{"id": "ccUsersAutoComplete", "options_to_select": cc}])
        if bcc:
            self.__process_combobox([{"id": "bccUsersAutoComplete", "options_to_select": bcc}])
        if notif_format:
            # select checkbox either label is html or text
            if notif_format == "HTML":
                self.__checkbox.check(id="EMAILJsonFormat")
            else:
                self.__checkbox.check(id="EMAILTextFormat")
        if subject and notif_format=="HTML":
            self.__dialog.fill_text_in_field(element_id='EMAILHtmlSubject', text=subject)
        elif subject and notif_format=="Text":
            self.__dialog.fill_text_in_field(element_id='EMAILTextSubject', text=subject)
        if content:
            self.__switch_iframe_and_fill_content(content)

    def __process_console(self, console_data):
        """
        Process console data
        Args:
            console_data (dict) : console data
                                example->{
                                    "to": ["user1", "user2"],
                                    "format": "HTML" (or) "Text",
                                    "subject": "subject",
                                    "content": "content"
                                }
        Returns:
            None
        """
        to = console_data.get("to")
        notif_format = console_data.get("format")
        subject = console_data.get("subject")
        content = console_data.get("content")

        for user in to:
            self.__process_combobox([{"id": "toUsersAutoComplete", "options_to_select": [user]}])
        if notif_format:
            # select checkbox either label is html or text
            if notif_format == "HTML":
                self.__checkbox.check(id="LIVEFEEDSJsonFormat")
            else:
                self.__checkbox.check(id="LIVEFEEDSTextFormat")
        if subject and notif_format=="HTML":
            self.__dialog.fill_text_in_field(element_id='LIVEFEEDSHtmlSubject', text=subject)
        elif subject and notif_format=="Text":
            self.__dialog.fill_text_in_field(element_id='LIVEFEEDSTextSubject', text=subject)
        if content:
            self.__switch_iframe_and_fill_content(content)
    
    def __process_snmp_or_event_viewer(self, content):
        """
        Process snmp/event viewer data
        
        Args:
            content (dict) : snmp/event viewer data
                                example->{
                                    "content": "content"
                                }
        Returns:
            None
        """
        content = content.get("content")
        if content:
            self.__switch_iframe_and_fill_content(content)


    def create_alert_definition(self, inputs):
        """
        Method to create alert definition
        Args:
            inputs (dict) : input data for each tab, labelled with keys 
                            'general', 'entities', 'criteria', 'filters', 'target', 'template'
                            which further contains input data for each field in the tab in 
                            the form of a dictionary
        Returns:
            None
  
        Example:

            {
                "general":{
                    "input":[{id:id, text_to_fill:text_to_fill}],
                    "dropdown":[{id:id, options_to_select:[options_to_select]}],
                    "toggle":[{id:id}, {label:label}],
                },
                "entities":{
                    "dropdown":[{id:id, options_to_select:[options_to_select]}],
                    "treeview":[name1, name2, etc]
                    "input":[{id:id, text_to_fill:text_to_fill}],
                },
                "criteria":{
                    "input":[{id:id, text_to_fill:text_to_fill}],
                    "checkbox":[{id:id}],
                },
                "filters":{
                    "input":[{id:id, text_to_fill:text_to_fill}],
                    "checkbox":[{id:id}],
                },
                "notification":{
                    "locale":"English,
                    "email":{
                        "to": ["user1", "user2"],
                        "cc": ["user3", "user4"],
                        "bcc": ["user5", "user6"],
                        "format":"HTML" (or) "Text"
                        "subject":"subject",
                        "content":"content"
                    },

                }
            }
        """
        processing_methods = {
            'input': self.__process_input,
            'dropdown': self.__process_dropdown,
            'toggle': self.__process_toggle,
            'checkbox': self.__process_checkbox,
            'combobox': self.__process_combobox,
            'tree': self.__process_treeview,
        }

        general_tab = inputs.get('general')
        entities_tab = inputs.get('entities')
        criteria_tab = inputs.get('criteria')
        filters_tab = inputs.get('filters')
        notification_tab = inputs.get('notification')
        # target_tab = inputs.get('target')
        # template_tab = inputs.get('template')

        tabs = [general_tab, entities_tab, criteria_tab, filters_tab]   # not adding template tab since it is handled separately

        for tab in tabs:
            if tab is None:
                self.__wizard.click_next()
                continue
            for key, value in tab.items():
                processing_method = processing_methods.get(key)
                if processing_method:
                    processing_method(value)
            self.__wizard.click_next()

        # notification tab
        # select locale
        if notification_tab.get("locale"):
            self.__process_dropdown([{"id": "templateLocale", "options_to_select": [notification_tab["locale"]]}])
            self.__admin_console.wait_for_completion()
            try:
                self.__dialog.click_button_on_dialog("Yes") # ADD LOCALE
            except:
                pass # WHY IS THIS HAPPENING??
        for key, value in notification_tab.items():
            if key == 'locale':
                continue
            try:
                self.__wizard.click_button("Add") # ADD LOCALE
            except ElementClickInterceptedException as e:
                pass # WHY IS THIS HAPPENING??
            self.__dialog.select_dropdown_values(drop_down_id="notifType", values=[key.capitalize() if key!="snmp" else "SNMP"])
            if key == "email":
                self.__process_email(value)
            if key == "console":
                self.__process_console(value)
            if key == "snmp" or key == "event viewer":
                self.__process_snmp_or_event_viewer(value)
            if key == "workflow":
                for key, value in notification_tab["workflow"].items():
                    processing_method = processing_methods.get(key)
                    if processing_method:
                        processing_method(value)
                self.__admin_console.wait_for_completion()
            self.__dialog.click_button_on_dialog("Save")

        self.__wizard.click_submit()
        # check for banner message
        error_message = self.__alert.check_error_message()
        if error_message:
            raise Exception(f"Error in Creating Alert: {error_message}")
        self.__admin_console.wait_for_completion()
 
    @PageService()
    def select_add_alert_definitions(self):
        """
        Method to select Add Alert Definitions
        """
        
        self.__page_container.click_button(value="Add alert definition")
