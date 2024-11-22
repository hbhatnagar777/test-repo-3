from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
ExchangeAppHelper  --  This class contains all the methods Exchange Page related actions
"""
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.Components.panel import DropDown
from Web.AdminConsole.Components.panel import ModalPanel
from Web.AdminConsole.Components.dialog import ModalDialog
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.FSPages.fs_agent import FSSubClient
from Web.AdminConsole.GovernanceAppsPages.CaseManager import CaseManager
from Web.Common.page_object import (
    WebAction, PageService
)
class ExchangeAppHelper:
    """
     This class contains all the methods for action in ExchangeAppHelper page
    """
    def __init__(self, admin_console):
        """
        Args:
            admin_console (AdminConsole): adminconsole base object
        """
        self.__admin_console = admin_console
        self.driver = admin_console.driver
        self.__table = Table(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)
        self.__dropdown = DropDown(self.__admin_console)
        self.__plans = Plans(self.__admin_console)
        self.__dialog = ModalDialog(self.__admin_console)
        self.__panel = ModalPanel(self.__admin_console)
        self.cm_obj = CaseManager(self.__admin_console)

    @WebAction()
    def _select_smtp_journaling(self):
        """
        Click on SMTP Journaling Link
        """
        xpath = "//span[@class='k-link k-menu-link']/a[contains(text(),'SMTP journaling')]"
        self.driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __set_input(self, id_name, value):
        """
        Sets the given value in the textbox with given id
        Args:
            id_name (str): Id name of input textbox
            value (str): Value to be entered in the textbox
        """
        view = self.driver.find_element(By.XPATH, "//input[@id='"+id_name+"']")
        view.clear()
        view.send_keys(value)

    @WebAction()
    def __is_infrastructure_set(self):
        """
        Check if Infrastructure is set for Server Plan
        Returns:
               True - if Server plan has infrastructure set
        """
        is_infra = False
        if self.__admin_console.check_if_entity_exists\
                    ("xpath", "//button[@type='submit'][contains(text(),'Finish')]"):
            is_infra = True
        return is_infra

    @WebAction()
    def __finish_app_creation(self):
        """
        Click on 'Finish' button
        """
        xpath = "//button[@type='submit'][contains(text(),'Finish')]"
        self.driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __expand_settings(self, setting_name):
        """
        Expand settings section with the given name
        Args:
            setting_name (str): Setting name to be expanded
        """
        xpath = "//div[@class='cv-accordion-header']//span[contains(text(),'"+setting_name+"')]"
        self.driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def __get_browse_buttons(self):
        """
        Get Browse buttons for smtp cache
        """
        browse_xpath = "//button[contains(text(),'Browse')]"
        browse_elements = self.driver.find_elements(By.XPATH, browse_xpath)
        return browse_elements

    @WebAction()
    def __upload_certificate_file(self, file):
        """
        Select certificate file on local machine
        Args:
            file (str): certificate filename
        """
        xpath = "//label[contains(text(),'Certificate file')]/..//input[@type='file']"
        self.driver.find_element(By.XPATH, xpath).send_keys(file)

    @WebAction()
    def __click_tab(self, tabname):
        """
        Click on tab name in Plans page
        Args:
             tabname (str): Tab name to be clicked
        """
        xpath = "//div[@class='wrapper-view']//span[contains(text(),'"+tabname+"')]"
        self.driver.find_element(By.XPATH, xpath).click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __click_associated_entities(self):
        """
                Clicks on associated entities in Plans page
        """
        self.__admin_console.access_tab("Associated entities")

    @PageService()
    def browse_smtp_cache_loc(self, cache_loc_list):
        """
        Browse SMTP cache location on SMTP servers
        Args:
             cache_loc_list(list): SMTP Cache locations list
        """
        browse_elements = self.__get_browse_buttons()
        indx = 0
        for element in browse_elements:
            element.click()
            self.__admin_console.wait_for_completion()
            FSSubClient(self.__admin_console).\
                browse_and_select_data([cache_loc_list[indx]], 'windows')
            indx = indx + 1

    @PageService()
    def isexchange_client_listed(self, client_name):
        """
        Check if the client with given name exists in Exchange page
        Args:
             client_name: Name of the exchange client
        Returns:
             True - If client exists
                    else False
        """
        try:
            value = False
            self.__admin_console.wait_for_completion()
            if self.__rtable.is_entity_present_in_column('Name', client_name):
                value = True
            return value
        except Exception:
            return False

    @PageService()
    def ismailbox_listed_in_app(self, mailbox_name):
        """
        Check if the mailbox with given name exists in Client page
        Args:
             mailbox_name: Name of the mailbox
        Returns:
             True - If Mailbox exists
                    else False
        """
        try:
            value = False
            if self.__table.is_entity_present_in_column('Name', mailbox_name):
                value = True
            return value
        except Exception:
            return False

    @PageService()
    def add_smtp_mailbox(self, client_name, mailbox_attributes):
        """
        Add Mailbox to the client
        Args:
               client_name: Name of the client to which mailbox has to be added
               mailbox_attributes: Dictionary with mailbox attributes
        """
        self.cm_obj.select_case(client_name)
        self.__admin_console.select_hyperlink('Add Mailbox')
        self.__admin_console.wait_for_completion()
        self.__set_input('name', mailbox_attributes["Display Name"])
        self.__set_input('smtpAddress', mailbox_attributes["SMTP Address"])
        self.cm_obj.select_dropdown_input('exchangePlan', mailbox_attributes["Exchange Plan"])
        self.__expand_settings("Network Settings")
        self.__set_input('whiteListIPs', mailbox_attributes["IP addresses"])
        self.__expand_settings("Certificate Settings")
        self.__upload_certificate_file(mailbox_attributes["Certificate Location"])
        # Restart services on access node dialogue
        self.__dialog.click_submit()
        self.__set_input('certificateFilePassword', mailbox_attributes["Certification Password"])
        #Placing Infrastructure settings in the last, as browse_smtp_cache_loc def submits the panel
        #without allowing automation to enter Network and Certificate settings
        self.__expand_settings("Infrastructure settings")
        self.__dropdown.select_drop_down_values(0, mailbox_attributes["SMTP Servers"])
        self.browse_smtp_cache_loc(mailbox_attributes["Cache Locations"])

    @PageService()
    def create_smtp_journaling_client(self, app_name, server_plan, index_server, proxy_list):
        """
        Create SMTP Journaling App
        Args:
            app_name(str): Name of Exchange SMTP App to be created
            server_plan(str): Name of server plan
            index_server(str): Indexserver to be chosen
            proxy_list(list): List of access nodes
        """
        self.__table.access_toolbar_menu('addApps')
        self._select_smtp_journaling()
        self.__set_input('serverName', app_name)
        self.cm_obj.select_dropdown_input('serverPlan', server_plan)

        is_infra = self.__is_infrastructure_set()
        self.__panel.submit()

        if not is_infra:
            self.cm_obj.select_dropdown_input('indexServer', index_server)
            self.__dropdown.select_drop_down_values(0, proxy_list)
            self.__finish_app_creation()

    @PageService()
    def is_client_associated_with_plan(self, client_name, serverplan):
        """
        Verifies if client is associated with plan
        Args:
            client_name(str): Name of the client
            serverplan(str): Serverplan name
        Returns: True if client is listed in the associated entities page of plans
                 else False
        """
        self.__admin_console.navigator.navigate_to_plan()
        self.__plans.select_plan(serverplan)
        self.__click_associated_entities()
        self.__admin_console.wait_for_completion()
        return self.isexchange_client_listed(client_name)