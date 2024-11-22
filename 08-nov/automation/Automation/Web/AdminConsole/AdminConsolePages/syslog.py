# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Service CommCell page on the AdminConsole

Class:

    Syslog()

Functions:

    _init_()                    :   initialize the class object

    __select_sysylog_tile()     :   selects the service commcell tile on the systems page

    __get_hostname()            :   Reads the hostname for the syslog configuration

    __get_port()                :   Reads the port number for the syslog configuration

    __get_forward_entities()    :   Reads the hostname for the syslog configuration

    __select_deselect_forward_entity()  :   Selects/Deselects the checkbox corresponding to the entity

    __select_enable_toggle()    :   Function to enable syslog forward toggle

    navigate_to_syslog()        :   navigates to the service commcell page in the adminconsole

    add_syslog()                :   Function to add syslog server details

    validate_syslog_configuration()     :   Function to add syslog server details

    disable_syslog()              :   Function to click syslog toggle

"""
from selenium.webdriver.common.by import By

from Web.Common.page_object import (WebAction, PageService)

class Syslog:
    """ Class for Syslog page in Admin Console """

    def __init__(self, admin_console):
        """
        Method to initiate Companies class

        Args:
            admin_console   (Object) :   Admin Console Class object
        """
        self.__admin_console = admin_console
        self.__log = admin_console.log
        self.__driver = admin_console.driver

    @WebAction()
    def __select_syslog_tile(self):
        """Selects the service commcell tile in the systems page"""
        xpath = "//a[@id='tileMenuSelection_syslogServer']"
        if self.__admin_console.check_if_entity_exists('xpath', xpath):
            xpath = xpath+'/..'
            self.__driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __get_hostname(self):
        """
        Reads the hostname for the syslog configuration
        """
        xpath = '//input[@name="hostname"]'
        data = self.__driver.find_element(By.XPATH, xpath).get_attribute('value')
        return data

    @WebAction()
    def __get_port(self):
        """
        Reads the port number for the syslog configuration
        """
        xpath = '//input[@name="port"]'
        data = self.__driver.find_element(By.XPATH, xpath).get_attribute('value')
        return data

    @WebAction()
    def __get_forward_entities(self):
        """
        Reads the hostname for the syslog configuration
        """
        entities_list = ['Alerts', 'Audit trail', 'Events']
        data = {'Alerts': False, 'Audit trail': False, 'Events': False}
        for entity in entities_list:
            if entity == 'Audit trail':
                entity1 = 'Audit'
            else:
                entity1 = entity
            is_selected = self.__driver.find_element(By.XPATH, '//input[@name="' + entity1 + '"]').is_selected()
            data[entity] = is_selected
        return data

    @WebAction()
    def __select_deselect_forward_entity(self, entity, status):
        """
        Selects/Deselects the checkbox corresponding to the entity
        Args:
            entity (string)     :   the name of the forward entity to be selected/deselected
            status (boolean)    :   the status to be set for the entity passed
        """
        xpath = '//span[@class="cv-material-input-wrapper cv-checkbox-wrapper ng-scope"]' \
                '//span[contains(text(),"' + entity + '")]'
        if entity == 'Audit trail':
            entity = 'Audit'
        is_selected = self.__driver.find_element(By.XPATH, '//input[@name="' + entity + '"]').is_selected()
        if status != is_selected:
            self.__driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __select_enable_toggle(self):
        """
        Function to enable syslog forward toggle
        """
        xpath = '//div[@class="cv-material-toggle cv-toggle isOff"]'
        self.__driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __select_disable_toggle(self):
        """
        Function to disable syslog forward toggle
        """
        xpath = '//div[@class="cv-material-toggle cv-toggle isOn"]'
        self.__driver.find_element(By.XPATH, xpath).click()

    @PageService()
    def navigate_to_syslog(self):
        """Function to navigate to service commcell page"""
        self.__admin_console.navigator.navigate_to_systems()
        self.__select_syslog_tile()

    @PageService()
    def add_syslog(self, hostname, port, forward_entities):
        """
        Function to add syslog server details
        Args:
            hostname (string)           :   the hostname of the syslog server
            port (string)               :   the port number of the syslog server
            forward_entities (dict)     :   type of logs to forward
        """
        self.__admin_console.fill_form_by_id('hostname', hostname)
        self.__admin_console.fill_form_by_id('port', port)
        self.__select_enable_toggle()
        for key in forward_entities.keys():
            self.__select_deselect_forward_entity(key, forward_entities[key])
        self.__admin_console.click_button_using_text('Submit')
        self.__admin_console.get_notification()

    @PageService()
    def validate_syslog_configuration(self, hostname, port, forward_entities):
        """
        Function to add syslog server details
        Args:
            hostname (string)           :   the hostname of the syslog server
            port (string)               :   the port number of the syslog server
            forward_entities (dict)     :   type of logs to forward
        """
        ui_hostname = self.__get_hostname()
        ui_port = self.__get_port()
        ui_forward_entities = self.__get_forward_entities()
        if hostname == ui_hostname:
            self.__log.info('Hostname match')
        if port == ui_port:
            self.__log.info('Port number match')
        if forward_entities == ui_forward_entities:
            self.__log.info('Forward entities match')

    @PageService()
    def disable_syslog(self):
        """
        Function to click syslog toggle
        """
        self.__select_disable_toggle()
        self.__admin_console.click_button_using_text('Submit')
