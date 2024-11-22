# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
alerts definitions tab on the Alerts Page on the AdminConsole

Class:

    AlertsDefinitionsInfo()

Functions:

edit_alert_target()          -- Method to edit alert targets tile

edit_alert_entities()        -- Method to edit alert entities tile

edit_alert_summary()         -- Method to edit alert summary tile

delete_alert_from_details()  -- Method to delete an alert definition from details page

alert_info()                 -- Method to extract alert info from details page

"""
from selenium.webdriver.common.by import By

from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.AdminConsole.Components.table import Table
from Web.Common.exceptions import CVWebAutomationException


class AlertsDefinitionsInfo:
    """
    This class provides the function or operations that can be performed on the alerts definitions
    tab on the Alerts Page
    """
    def __init__(self, admin_console):
        """
        Method to initiate Companies class

        Args:
            admin_page   (Object) :   Admin Page Class object
        """
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.log = self.__admin_console.log
        self.__table = Table(admin_console)

    @WebAction()
    def __access_target_modal(self):
        """Access the target modal"""
        self.__driver.find_element(By.XPATH, "//a[@ng-click='openTargetEditModal()']").click()

    @WebAction()
    def __get_to_elements(self):
        """Return html 'To' Recipient elements"""
        elements = self.__driver.find_elements(By.XPATH, "//div[@id='s2id_toUserList']/ul/li")
        return elements

    @WebAction()
    def __get_cc_elements(self):
        """Return html 'Cc' Recipient elements"""
        elements = self.__driver.find_elements(By.XPATH, "//div[@id='s2id_ccUserList']/ul/li")
        return elements

    @WebAction()
    def __get_bcc_elements(self):
        """Return html 'Bcc' Recipient elements"""
        elements = self.__driver.find_elements(By.XPATH, "//div[@id='s2id_bccUserList']/ul/li")
        return elements

    @WebAction()
    def __select_recipient_entity(self,entity, value):
        """Select the respective recipient entity"""
        entity.find_element(By.XPATH, ".//span[contains(text(),'" + value + "')]\
                                            /../following-sibling::a").click()

    @WebAction()
    def __fill_to_list(self, value):
        """Fill to list"""
        self.__driver.find_element(By.XPATH, "//div[@id='s2id_toUserList']/ul/li/input").send_keys(value)

    @WebAction()
    def __fill_cc_list(self, value):
        """Fill cc list"""
        self.__driver.find_element(By.XPATH, "//div[@id='s2id_ccUserList']/ul/li/input").send_keys(value)

    @WebAction()
    def __fill_bcc_list(self, value):
        """Fill bcc list"""
        self.__driver.find_element(By.XPATH, "//div[@id='s2id_bccUserList']/ul/li/input").send_keys(value)

    @WebAction()
    def __select_user_element(self, value):
        """Select to element"""
        self.__driver.find_element(By.XPATH, "//span[@class='user-type plan-user-suggestion' and contains\
                                                (text(),' (" + value + ")" + "')]").click()

    @WebAction()
    def __select_group_element(self, value):
        """Select cc element"""
        self.__driver.find_element(By.XPATH, "//span[@class='group-type plan-user-suggestion' and contains\
                                                (text(),' (" + value + ")" + "')]").click()

    @WebAction()
    def __select_email_element(self, value):
        """Select bcc element"""
        self.__driver.find_element(By.XPATH, "//span[@class='email-type plan-user-suggestion' and contains\
                                                (text(),'" + value + "')]").click()

    @WebAction()
    def __select_entity_dropdown(self):
        """Select email entity dropdown"""
        self.__driver.find_element(By.XPATH, "//div[@id='select2-drop-mask']").click()

    @WebAction()
    def __select_confirm_button(self):
        """Selects the confirm button"""
        self.__driver.find_element(By.XPATH, "//button[@class='btn btn-primary cvBusyOnAjax']").click()

    @PageService()
    def edit_alert_target(self,
                          alert_target,
                          to_recipients,
                          cc_recipients,
                          bcc_recipients):

        ''' Method to alert target tile for given alert

        Args:
            alert_target    (list)          -- list containing alert targets

                Eg. send_alert_to = ['Email', 'Event viewer', 'Console', 'SNMP']

            to_recipients    (dictionary)   --  dictionary containing users to be added or removed
                                                 from the Alert
                Eg.- {""Add":{"Group":["ViewAll"],
                      "Email":["jsrdude1@gmail.com"],
                      "User":[]},
                      "Remove":["jrana@commvault.com", "admin"]}

            cc_recipients    (dictionary)   --  dictionary containing users to be added or removed
                                                 from the Alert
                Eg.- {"Add":{"Group":["ViewAll"],
                      "Email":["jsrdude1@gmail.com"],
                      "User":[]},
                      "Remove":["jrana@commvault.com", "admin"]}

            bcc_recipients    (dictionary)   --  dictionary containing users to be added or removed
                                                 from the Alert
                Eg.- {"Add":{"Group":["ViewAll"],
                      "Email":["jsrdude1@gmail.com"],
                      "User":[]},
                      "Remove":["jrana@commvault.com", "admin"]}
        Returns:
            None

        Raises:
            Exception:
                -- if fails to edit alert targets
        '''

        to_list = []
        cc_list = []
        bcc_list = []

        add_to_recipients = to_recipients['Add']
        add_cc_recipients = cc_recipients['Add']
        add_bcc_recipients = bcc_recipients['Add']

        for group in add_to_recipients['Group']:
            to_list.append(group)
        for user in add_to_recipients['User']:
            to_list.append(user)
        for email in add_to_recipients['Email']:
            to_list.append(email)
        for group in add_cc_recipients['Group']:
            cc_list.append(group)
        for user in add_cc_recipients['User']:
            cc_list.append(user)
        for email in add_cc_recipients['Email']:
            cc_list.append(email)
        for group in add_bcc_recipients['Group']:
            bcc_list.append(group)
        for user in add_bcc_recipients['User']:
            bcc_list.append(user)
        for email in add_bcc_recipients['Email']:
            bcc_list.append(email)

        self.__access_target_modal()
        self.__admin_console.wait_for_completion()

        if alert_target:
            if alert_target['Email']:
                self.__admin_console.checkbox_select('alertNotifTypeEmail')

                if to_recipients['Remove']:
                    entities = self.__get_to_elements()
                    for value in to_recipients['Remove']:
                        for entity in entities:
                            if self.__admin_console.is_element_present(
                                    ".//span[contains(text(),'"+value+"')]", entity):
                                self.__select_recipient_entity(entity, value)
                                self.__admin_console.wait_for_completion()

                if cc_recipients['Remove']:
                    entities = self.__get_cc_elements()
                    for value in cc_recipients['Remove']:
                        for entity in entities:
                            if self.__admin_console.is_element_present(
                                    ".//span[contains(text(),'"+value+"')]", entity):
                                self.__select_recipient_entity(entity, value)
                                self.__admin_console.wait_for_completion()

                if bcc_recipients['Remove']:
                    entities = self.__get_bcc_elements()
                    for user in bcc_recipients['Remove']:
                        for entity in entities:
                            if self.__admin_console.is_element_present(
                                    ".//span[contains(text(),'" + value + "')]", entity):
                                self.__select_recipient_entity(entity, value)
                                self.__admin_console.wait_for_completion()

                if to_list:
                    self.log.info("Adding recipients in TO LIST")
                    for value in to_list:
                        self.__fill_to_list(value)
                        self.__admin_console.wait_for_completion()
                        if self.__admin_console.check_if_entity_exists(
                                "xpath", "//span[@class='group-type plan-user-suggestion' and \
                            contains(text(),' ("+value+")"+"')]"):
                            self.__select_group_element(value)
                        elif self.__admin_console.check_if_entity_exists(
                                "xpath", "//span[@class='user-type plan-user-suggestion' and \
                            contains(text(),' ("+value+")"+"')]"):
                            self.__select_user_element(value)
                        elif self.__admin_console.check_if_entity_exists(
                                "xpath", "//span[@class='email-type plan-user-suggestion' and \
                            contains(text(),'"+value+"')]"):
                            self.__select_email_element(value)
                        self.__admin_console.wait_for_completion()

                if cc_list:
                    self.log.info("Adding recipients in CC LIST")
                    for value in cc_list:
                        self.__fill_cc_list(value)
                        self.__admin_console.wait_for_completion()
                        if self.__admin_console.check_if_entity_exists(
                                "xpath", "//span[@class='group-type plan-user-suggestion' and \
                            contains(text(),' ("+value+")"+"')]"):
                            self.__select_group_element(value)
                        elif self.__admin_console.check_if_entity_exists(
                                "xpath", "//span[@class='user-type plan-user-suggestion' and \
                            contains(text(),' ("+value+")"+"')]"):
                            self.__select_user_element(value)
                        elif self.__admin_console.check_if_entity_exists(
                                "xpath", "//span[@class='email-type plan-user-suggestion' and \
                            contains(text(),'"+value+"')]"):
                            if self.__admin_console.check_if_entity_exists(
                                    "xpath", "//div[@id='select2-drop-mask']"):
                                self.__select_entity_dropdown()
                            self.__select_email_element(value)
                        self.__admin_console.wait_for_completion()

                if bcc_list:
                    self.log.info("Adding recipients in BCC LIST")
                    for value in bcc_list:
                        self.__admin_console.wait_for_completion()
                        self.__fill_bcc_list(value)
                        if self.__admin_console.check_if_entity_exists(
                                "xpath", "//span[@class='group-type plan-user-suggestion' and \
                            contains(text(),' ("+value+")"+"')]"):
                            self.__select_group_element(value)
                        elif self.__admin_console.check_if_entity_exists(
                                "xpath", "//span[@class='user-type plan-user-suggestion' and \
                            contains(text(),' ("+value+")"+"')]"):
                            self.__select_user_element(value)
                        elif self.__admin_console.check_if_entity_exists(
                                "xpath", "//span[@class='email-type plan-user-suggestion' and \
                            contains(text(),'"+value+"')]"):
                            if self.__admin_console.check_if_entity_exists(
                                    "xpath", "//div[@id='select2-drop-mask']"):
                                self.__select_entity_dropdown()
                            self.__select_email_element(value)
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

                    if to_recipients['Remove']:
                        entities = self.__get_to_elements()
                        for value in to_recipients['Remove']:
                            for entity in entities:
                                if self.__admin_console.is_element_present(
                                        ".//span[contains(text(),'"+value+"')]", entity):
                                    self.__select_recipient_entity(entity, value)
                                    self.__admin_console.wait_for_completion()

                    if to_list:
                        self.log.info("Adding recipients in TO LIST")
                        for value in to_list:
                            self.__fill_to_list(value)
                            self.__admin_console.wait_for_completion()
                            if self.__admin_console.check_if_entity_exists(
                                    "xpath", "//span[@class='group-type plan-user-suggestion' and \
                                contains(text(),' ("+value+")"+"')]"):
                                self.__select_group_element(value)
                            elif self.__admin_console.check_if_entity_exists(
                                    "xpath", "//span[@class='user-type plan-user-suggestion' and \
                                contains(text(),' ("+value+")"+"')]"):
                                self.__select_user_element(value)
                            elif self.__admin_console.check_if_entity_exists(
                                    "xpath", "//span[@class='email-type plan-user-suggestion' and \
                                contains(text(),'"+value+"')]"):
                                self.__select_email_element(value)
                            self.__admin_console.wait_for_completion()
            else:
                self.__admin_console.checkbox_deselect('alertNotifTypeCA')

            if alert_target['SNMP']:
                self.__admin_console.checkbox_select('alertNotifTypeSNMP')

            else:
                self.__admin_console.checkbox_deselect('alertNotifTypeSNMP')

        self.__select_confirm_button()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @WebAction()
    def __access_alert_entities_modal(self):
        """Get the alert entities modal"""
        self.__driver.find_element(By.XPATH, "//a[@ng-click='openEntitiesEditModal()']").click()

    @WebAction()
    def __select_alert_entity(self):
        """Select an alert entity"""
        self.__driver.find_element(By.XPATH, "//div[@class='ng-scope selected']/span/span").click()

    @WebAction()
    def __get_alert_collapsed_elements(self):
        """Returns the collapsed elements"""
        elem = self.__driver.find_elements(By.XPATH, "//button[@class='collapsed']")
        return elem

    @WebAction()
    def __get_serverlist_entities(self):
        """Returns the serverlist entities"""
        entities = self.__driver.find_element(By.XPATH, "//div[@class='browse-tree alerts-browse']")
        return entities

    @WebAction()
    def __select_serverlist_entity(self, entities, value):
        """Select a serverlist entity from the entity tree"""
        entities.find_element(By.XPATH, "//span[./text()='" + str(value) + "']").click()

    @PageService()
    def edit_alert_entities(self, alert_entities):

        ''' Method to alert entities tile for given alert

        Args:
            alert_entities   (list)      : server groups or clients for which alert is defined

                Eg. alert_entities = ["Server groups", "Clients"]

        Returns:
            None

        Raises:
            Exception:
                -- if fails to edit alert entities
        '''

        self.__access_alert_entities_modal()
        self.__admin_console.wait_for_completion()

        while self.__admin_console.check_if_entity_exists("xpath", "//div[@class='ng-scope selected']"):
            self.__select_alert_entity()

        if self.__admin_console.check_if_entity_exists(
                "xpath", "//button[@class='collapsed']"):
            collapsed_elems = self.__get_alert_collapsed_elements()
            for elem in collapsed_elems:
                elem.click()
            entities = self.__get_serverlist_entities()
            for value in alert_entities['server_group_list']:
                self.__select_serverlist_entity(entities, value)
            for value in alert_entities['server_list']:
                self.__select_serverlist_entity(entities, value)

        self.__admin_console.click_button("Save")

    @PageService()
    def edit_alert_summary(self, ind_notification):

        ''' Method to edit alert summary tile for given alert

        Args:
            ind_notification  (str)    :  individual notification to be enabled/disabled
                    Eg. - ind_notification = 'ON'

        Returns:
            None

        Raises:
            Exception:
                -- if fails to edit alert summary
        '''

        if ind_notification == 'ON':
            self.__admin_console.enable_toggle(index=0)
        else:
            self.__admin_console.disable_toggle(index=0)

    @WebAction()
    def __get_alert_title(self):
        """Returns the alert title"""
        title = self.__driver.find_element(By.XPATH, "//h1[@class='no-margin page-title editable js-page-title']")
        return title

    @WebAction()
    def __get_alert_tiles(self):
        """Returns Alert details page tile elements"""
        entities = self.__driver.find_elements(By.XPATH, "//div[@class='page-details group']")
        return entities

    @WebAction()
    def __get_entity_title(self, entity):
        """Returns alert tile title"""
        title = entity.find_element(By.XPATH, "./span").text
        return title

    @WebAction()
    def __get_alert_target_key(self, elem):
        """Return alert target key"""
        key = elem.find_element(By.XPATH, ".//div/div/ul/li/span[1]").text
        return key

    @WebAction()
    def __get_alert_target_value(self, elem):
        """Return alert target value"""
        value = elem.find_element(By.XPATH, ".//div/div/ul/li/span[2]").text
        return value

    @PageService()
    def alert_info(self, alert_target):
        '''Method to extract information about an alert

        Returns:
            None

        Raises:
            Exception:
                -- if fails to extract alert info from details page
        '''
        try:
            details = {}
            count = 0
            title = self.__get_alert_title()
            details.update({"AlertName":title.text})
            elems = self.__get_alert_tiles()
            for elem in elems:
                entity_name = self.__get_entity_title(elem)
                if entity_name == 'Alert target':
                    keyvalue_list = []
                    keyvalue_dict = {}
                    key = self.__get_alert_target_key(elem)
                    value = self.__get_alert_target_value(elem)
                    keyvalue_dict.update({key: value})
                    if alert_target['Email'] or alert_target['Console']:
                        recipients = elem.find_elements(By.XPATH, 
                            ".//div/div/div[2]/cv-tabset-component/div/div")
                        for recipient in recipients:
                            count += 1
                            if count > 1 and not alert_target['Email']:
                                break
                            else:
                                recipient.find_element(By.XPATH, 
                                    "./../../ul/li["+str(count)+"]/a").click()
                                key = recipient.find_element(By.XPATH, 
                                    "./../../ul/li["+str(count)+"]/a").text
                                li_elems = recipient.find_elements(By.XPATH, ".//li")
                                temp_dict = {}
                                for li_elem in li_elems:
                                    k = li_elem.find_element(By.XPATH, "./span[1]/label").text
                                    v = li_elem.find_element(By.XPATH, "./span[2]").text
                                    temp_dict.update({k: v})
                                keyvalue_dict.update({key:temp_dict})
                        details.update({entity_name: keyvalue_dict})
                else:
                    div_elements = elem.find_elements(By.XPATH, "./div")
                    for div_elem in div_elements:
                        keyvalue_list = []
                        keyvalue_dict = {}
                        key = ''
                        ul_elements = div_elem.find_elements(By.XPATH, ".//ul")
                        if not ul_elements:
                            inner_div_elems = div_elem.find_elements(By.XPATH, 
                                ".//div[@class='ng-scope']")
                            for inner_div_elem in inner_div_elems:
                                key = inner_div_elem.find_element(By.XPATH, "./span").text
                                keyvalue_list.append(key)
                            details.update({entity_name: keyvalue_list})
                        for ul_elem in ul_elements:
                            li_elements = ul_elem.find_elements(By.XPATH, './/li')
                            for li_elem in li_elements:
                                if self.__admin_console.is_element_present(
                                        ".//toggle-control", li_elem):
                                    if li_elem.find_element(By.XPATH, 
                                            ".//toggle-control/div").get_attribute("class") \
                                        == "cv-material-toggle cv-toggle":
                                        keyvalue_dict[li_elem.find_element(By.XPATH, 
                                            ".//span[@class='pageDetailColumn']").text] = "OFF"
                                    else:
                                        keyvalue_dict[li_elem.find_element(By.XPATH, 
                                            ".//span[@class='pageDetailColumn']").text] = "ON"
                                inside_li_tags = li_elem.find_elements(By.XPATH, './/span')
                                tag_iterate_count = 0
                                for tag in inside_li_tags:
                                    tag_iterate_count += 1
                                    if tag.text:
                                        if tag_iterate_count == 1:
                                            key = tag.text
                                            if len(inside_li_tags) == 1:
                                                keyvalue_list.append(key)
                                                break
                                        else:
                                            value = tag.text
                                            if 'Edit' in value:
                                                value = value.rstrip('\nEdit')
                                            keyvalue_dict.update({key: value})

                            if len(inside_li_tags) == 1:
                                details.update({entity_name: keyvalue_list})
                            else:
                                details.update({entity_name: keyvalue_dict})
            return details
        except Exception as exp:
            raise CVWebAutomationException(exp)
