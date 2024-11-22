from selenium.webdriver.common.by import By

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
testcases of Office365 module.

To begin, create an instance of Office365Apps for test case.

To initialize the instance, pass the testcase object to the Office365Apps class.

Call the required definition using the instance object.

This file consists of only one class Office365Apps.
"""

import datetime
from enum import Enum
import time
import collections
from selenium.common.exceptions import (ElementNotInteractableException,
                                        NoSuchElementException,
                                        ElementClickInterceptedException,
                                        StaleElementReferenceException, NoSuchWindowException)
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from AutomationUtils import logger
from Web.AdminConsole.Components.table import Table, Rtable, ContainerTable,Rfilter
from Web.AdminConsole.Components.cventities import CVActionsToolbar
from Web.Common.page_object import PageService, WebAction
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog
from Web.AdminConsole.Components.panel import DropDown, RDropDown, RPanelInfo, PanelInfo, ModalPanel, RModalPanel
from Web.AdminConsole.Components.browse import Browse, RBrowse
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Office365Pages import constants
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.core import CalendarView


class Office365Apps:
    """Class for all Office 365 Apps page"""

    class AppType(Enum):
        """App types for Office 365"""
        exchange_online = 'ADD_EXCHANGEONLINE_APP'
        share_point_online = 'ADD_SHAREPOINT_ONLINE_APP'
        one_drive_for_business = 'ADD_ONEDRIVE_FOR_BUSINESS_APP'

    def __init__(self, tcinputs, admin_console, is_react=True):
        """Initializes the Office365Apps class instance

                Args:
                    tc (Object)  --  Testcase object

        """
        self.tcinputs = tcinputs
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self.log = logger.get_log()
        self.modern_authentication = False
        self.newly_created_app_name = None
        self.last_deleted_app_name = None
        self.newly_created_service_account = None
        self.last_deleted_service_account = None
        self.backedup_mails = 0
        self.restored_mails = 0
        self.indexed_mails = 0
        self.app_stats_dict = {}
        # Required Components
        self.__table = Table(self._admin_console)
        self.__rtable = Rtable(self._admin_console)
        self._wizard = Wizard(self._admin_console)
        self._modal_dialog = ModalDialog(self._admin_console)
        self._rmodal_dialog = RModalDialog(self._admin_console)
        self._modal_panel = ModalPanel(self._admin_console)
        self._Rmodal_panel = RModalPanel(self._admin_console)
        self._rpanel_info = RPanelInfo(self._admin_console)
        self._dropdown = DropDown(self._admin_console)
        self._rdropdown = RDropDown(self._admin_console)
        self._rmodal_panel = RModalPanel(self._admin_console)
        self._jobs = Jobs(self._admin_console)
        self._plans = Plans(self._admin_console)
        self._browse = Browse(self._admin_console)
        self._rbrowse = RBrowse(self._admin_console)
        self._actions_toolbar = CVActionsToolbar(self._admin_console)
        self._panel_info=PanelInfo(self._admin_console)
        self._rpanel_info = RPanelInfo(self._admin_console)
        self._calendar = CalendarView(self._admin_console)
        self.navigator = self._admin_console.navigator
        self._containertable = ContainerTable(self._admin_console)
        self.is_react = is_react
        # Call Localization method
        self._admin_console.load_properties(self)
        if 'Users' in self.tcinputs:
            self.users = self.tcinputs['Users'].split(",")
        if 'Groups' in self.tcinputs:
            self.groups = self.tcinputs['Groups']

        self.agent_app_type = self.tcinputs['office_app_type']
        if self.agent_app_type == Office365Apps.AppType.exchange_online:
            self.app_type = constants.ExchangeOnline
        elif self.agent_app_type == Office365Apps.AppType.one_drive_for_business:
            self.app_type = constants.OneDrive
        elif self.agent_app_type == Office365Apps.AppType.share_point_online:
            self.app_type = constants.SharePointOnline

    @WebAction()
    def _create_app(self, app_type):
        """Creates app with given app type

                Args:
                    app_type  (str)  -- Type of app to create

        """

        add_apps_xpath = "//a[@id='ADD_APPS']"
        add_apps_new_id = "addOffice365App"
        exchange_online_xpath = (f"//div[text()='"
                                 f"{self._admin_console.props['label.nav.exchangeOnline']}']")
        onedrive_v2_xpath = (f"//div[text()='"
                             f"{self._admin_console.props['label.nav.oneDriveForBusiness']}']")
        sharepoint_online_xpath = (f"//div[text()='"
                                   f"{self._admin_console.props['label.nav.sharepointOnline']}']")
        sharepoint_online_react_xpath = (f"//strong[text()='"
                                         f"{self._admin_console.props['label.nav.sharepointOnline']}']")

        if self._admin_console.check_if_entity_exists('xpath', add_apps_xpath):
            self._driver.find_element(By.XPATH, add_apps_xpath).click()
            self._driver.find_element(By.XPATH, "//a[@id='" + app_type.value + "']").click()

        elif self._admin_console.check_if_entity_exists('id', add_apps_new_id):
            self._driver.find_element(By.ID, add_apps_new_id).click()
            self._admin_console.wait_for_completion()
            if app_type == Office365Apps.AppType.exchange_online:
                self._driver.find_element(By.XPATH, exchange_online_xpath).click()
            elif app_type == Office365Apps.AppType.one_drive_for_business:
                self._driver.find_element(By.XPATH, onedrive_v2_xpath).click()
            elif app_type == Office365Apps.AppType.share_point_online:
                self._driver.find_element(By.XPATH, sharepoint_online_xpath).click()

        elif self._admin_console.check_if_entity_exists(
                'link', self._admin_console.props['label.add.office365']):
            self._driver.find_element(By.LINK_TEXT,
                                      self._admin_console.props['label.add.office365']).click()
            self._admin_console.wait_for_completion()
            if app_type == Office365Apps.AppType.exchange_online:
                self._driver.find_element(By.XPATH, exchange_online_xpath).click()
            elif app_type == Office365Apps.AppType.one_drive_for_business:
                self._driver.find_element(By.XPATH, onedrive_v2_xpath).click()
            elif app_type == Office365Apps.AppType.share_point_online:
                self._driver.find_element(By.XPATH, sharepoint_online_xpath).click()
        elif self.is_react:
            self.__rtable.access_toolbar_menu(self._admin_console.props['label.add.office365'])
            self._admin_console.wait_for_completion()
            if self._admin_console.check_if_entity_exists("xpath","//div[@id='Card_COMMVAULT_CLOUD']"):
                self._wizard.click_next()
                self._admin_console.wait_for_completion()
            # self._admin_console.unswitch_to_react_frame()
            if self.agent_app_type == Office365Apps.AppType.share_point_online:
                self._wizard.select_card(text="SharePoint Online")
            elif self.agent_app_type == Office365Apps.AppType.exchange_online:
                self._wizard.select_card(text="Exchange Online")
            elif self.agent_app_type == Office365Apps.AppType.one_drive_for_business:
                self._wizard.select_card(text="OneDrive for Business")
            else:
                self._wizard.select_card(text="Teams")

        else:
            if app_type == Office365Apps.AppType.exchange_online:
                self._driver.find_element(By.LINK_TEXT,
                                          self._admin_console.props['link.addExchangeOnline']).click()
            elif app_type == Office365Apps.AppType.share_point_online:
                self._driver.find_element(By.LINK_TEXT,
                                          self._admin_console.props['link.addSharePointOnline']).click()
            else:
                self._driver.find_element(By.LINK_TEXT,
                                          self._admin_console.props['link.addOneDriveforBusiness']).click()

        self._admin_console.wait_for_completion()
        if not self._admin_console.check_if_entity_exists('xpath', "//input[@id='appNameField']"):
            self._wizard.click_next()
            self._admin_console.wait_for_completion()

    @WebAction(delay=2)
    def _enter_shared_path_for_multinode(self, shared_jrd=None):
        """Enters the shared Job Results directory for multiple access nodes"""
        if self.is_react:
            if self.agent_app_type == Office365Apps.AppType.share_point_online:
                if shared_jrd:
                    self._admin_console.fill_form_by_id('sharedJRD', shared_jrd + "\\JobResults")
                else:
                    self._driver.find_element(By.ID, 'uncPathInput').send_keys(
                        self.tcinputs["UNCPath"] + "\\JobResults")
            else:
                if shared_jrd:
                    self._admin_console.fill_form_by_id('sharedJRD', shared_jrd)
                else:
                    self._driver.find_element(By.ID,
                                              'uncPathInput').send_keys(self.tcinputs["UNCPath"])
        else:
            if shared_jrd:
                self._driver.find_element(By.ID, 'jobResultsDirectory').clear()
                self._driver.find_element(By.ID, 'jobResultsDirectory').send_keys(shared_jrd)
            else:
                self._driver.find_element(By.ID,
                                          'jobResultDirectory').send_keys(self.tcinputs["UNCPath"])

    @WebAction(delay=2)
    def _add_account_for_shared_path(self, user_account=None, password=None):
        """Enters the user account and password to access the shared path"""
        if self.is_react:
            if user_account:
                self._admin_console.fill_form_by_id('lsaUser', user_account)
                self._driver.find_element(By.ID, 'password').clear()
                self._driver.find_element(By.ID, 'password').send_keys(password)
                self._driver.find_element(By.ID, 'confirmPassword').clear()
                self._driver.find_element(By.ID, 'confirmPassword').send_keys(password)

            else:
                self._driver.find_element(By.XPATH, "//button[@title='Add']").click()
                self._admin_console.wait_for_completion()
                self._admin_console.fill_form_by_id('accountName', self.tcinputs['username'])
                self._admin_console.fill_form_by_id('password', self.tcinputs['password'])
                self._admin_console.fill_form_by_id('confirmPassword', self.tcinputs['password'])
                self._driver.find_element(By.XPATH, "//button[@aria-label='Add']/div").click()
                self._admin_console.wait_for_completion()

        else:
            if user_account:
                if self.agent_app_type == Office365Apps.AppType.share_point_online:
                    self._driver.find_element(By.ID, 'localAccessAccountName').clear()
                    self._driver.find_element(By.ID, 'localAccessAccountName').send_keys(user_account)
                else:
                    self._driver.find_element(By.ID, 'username').clear()
                    self._driver.find_element(By.ID, 'username').send_keys(user_account)

                self._driver.find_element(By.ID, 'password').send_keys(password)
                self._driver.find_element(By.ID, 'confirmPassword').send_keys(password)
            else:
                self._driver.find_element(By.ID, 'addLocalAccount').click()
                self._admin_console.wait_for_completion()
                self._driver.find_element(By.ID,
                                          'localSystemAccountUser').send_keys(self.tcinputs["username"])
                self._driver.find_element(By.ID, 'password').send_keys(self.tcinputs["password"])
                self._driver.find_element(By.ID,
                                          'confirmPassword').send_keys(self.tcinputs["password"])
            self._modal_dialog.click_submit()
            self._admin_console.wait_for_completion()

    @WebAction()
    def _select_custom_config(self):
        """Selects custom config in modal dialog"""
        self._driver.find_element(By.ID, "CUSTOM").click()

    @WebAction()
    def _get_browse_tree_view_content(self, active_tree=False):
        """Returns browse tree view content

            Args:

                active_tree (bool)      :   returns only active tree view items if true
        """
        if active_tree:
            xpath = self.app_type.ACTIVE_BROWSE_TREE_XPATH.value
        else:
            # TODO: Need to find a way to get inactive browse tree elements
            xpath = self.app_type.BROWSE_TREE_XPATH.value
        elements = self._driver.find_elements(By.XPATH, xpath)
        return [ele.text for ele in elements]

    @WebAction()
    def _click_item_in_browse_table(self, title):
        """Clicks on the specified title in browse table
             Args:
                    title (str)  --  title of the item to be clicked
        """
        if self.agent_app_type == Office365Apps.AppType.share_point_online:
            self._driver.find_element(By.XPATH,
                                      f"//*[@id='cv-k-grid-td-formattedTitleName']//span[contains(text(),'{title}')]"
                                      ).click()

    @WebAction()
    def _click_browse_bread_crumb_item(self, item):
        """Clicks on the specified browse bread crumb item
             Args:
                    item (str)  --  item to be clicked
        """
        if self.agent_app_type == Office365Apps.AppType.share_point_online:
            self._driver.find_element(
                By.XPATH, f"//nav[@aria-label='breadcrumb']//*[contains(text(), '{item}')]").click()

    @WebAction()
    def _apply_search_filter(self, keyword):
        """Applies search filter with given keyword
            Args:
                keyword (str)    :   keyword to apply search filter
        """
        if (self.agent_app_type == Office365Apps.AppType.share_point_online
                or self.agent_app_type == Office365Apps.AppType.one_drive_for_business):
            self._admin_console.fill_form_by_id("ATSearchInput", keyword)
            self._driver.find_element(By.ID, "ATSearchInput").send_keys(Keys.ENTER)

    @WebAction()
    def _click_item_in_browse_tree_view(self, item):
        """ Method to expand company selection drop down
            Args:
                    item (str)  --  item to be clicked
        """
        self._driver.find_element(
            By.XPATH, f"//li[@role='treeitem']//span[contains(text(), '{item}')]").click()

    @WebAction()
    def click_item_in_browse_tree_view(self, item):
        """ Method to expand company selection drop down
            Args:
                    item (str)  --  item to be clicked
        """
        self._click_item_in_browse_tree_view(item)
        self._admin_console.wait_for_completion()

    @WebAction()
    def _is_warning_message_displayed(self, warning_message):
        """Checks whether warning message is displayed or not
         when last azure app or service account is deleted
            Args:
                    warning_message (str)   --  warning message to be checked
        """
        xpath = f"//span[contains(text(),'{warning_message}')]"
        return self._admin_console.check_if_entity_exists('xpath', xpath)

    @WebAction()
    def _click_add_azure_app(self):
        """Clicks on add azure app in the modal dialog to create an azure app"""
        if self.is_react:
            self._rpanel_info.access_tab('Azure apps')
            self.__rtable.access_toolbar_menu("Add Azure app")
        else:
            self._driver.find_element(By.ID, 'createAzureApp').click()

    @WebAction()
    def _click_add_service_account(self):
        """Clicks on add service account in the modal dialog to create a service account"""
        if self.is_react:
            self._rpanel_info.access_tab('Service accounts')
            self.__rtable.access_toolbar_menu("Add service account")
        else:
            self._driver.find_element(By.ID, 'testConnection').click()

    @WebAction()
    def _is_global_admin_label_available_for_add_service_account(self):
        """Checks whether adding service account using global admin
        label is present in the modal dialog or not"""
        return len(self._driver.find_elements(By.XPATH,
            f"//div[contains(text(), '{self._admin_console.props['dialog.addServiceAccount']}')]"))

    @WebAction()
    def _is_global_admin_label_available(self):
        """Checks whether global admin label is present in the modal dialog or not"""
        label_xpath = f"//label[contains(text(), '{self._admin_console.props['label.globalAdministrator']}')]"
        return bool(self._driver.find_elements(By.XPATH, label_xpath))

    @WebAction()
    def _is_add_azure_app_dialog_open(self):
        """Checks whether add  azure app dialog is open or not"""
        if self._driver.find_elements(By.XPATH, "//div[@class='wizard-title ']"):
            return self._wizard.get_wizard_title().lower() == 'add azure app'
        return False

    @WebAction()
    def _is_add_service_account_dialog_open(self):
        """Checks whether add service account dialog is open or not"""
        if self._driver.find_elements(By.XPATH, "//div[@class='wizard-title ']"):
            return self._wizard.get_wizard_title().lower() == 'add service account'
        return False

    @WebAction()
    def _add_service_account_for_custom_config_client_creation(self, user_account, password):
        """Adds service account for custom config during client creation
            Args:
                user_account (str)    :   username of service account
                password (str)        :   password of service account
        """
        add_service_acc_xp = (f"//a[contains(normalize-space(), '"
                              f"{self._admin_console.props['label.add.sharePointServiceAccount']}"
                              f"')]")
        self._driver.find_element(By.XPATH, add_service_acc_xp).click()
        if self.agent_app_type == Office365Apps.AppType.share_point_online:
            self._driver.find_element(By.ID, 'sharePointAdminUsername').send_keys(user_account)
        else:
            self._driver.find_element(By.ID, 'exchangeAdminSmtpAddress').send_keys(user_account)
        self._driver.find_element(By.ID, 'password').send_keys(password)
        self._driver.find_element(By.ID, 'confirmPassword').send_keys(password)
        self._admin_console.checkbox_select("MFA_DISABLED")
        self._admin_console.checkbox_select("SVC_ROLES")
        self._modal_dialog.click_submit()
        self._admin_console.wait_for_completion()

    @WebAction()
    def _add_service_account_for_express_config(self, global_admin, global_admin_password):
        """Adds service account for express config in configuration page
            Args:
                global_admin (str)              :   username of global admin
                global_admin_password (str)     :   password of global admin
        """
        if self._is_global_admin_label_available():
            self._admin_console.fill_form_by_id('globalAdmin', global_admin)
            self._admin_console.fill_form_by_id('globalAdminPassword', global_admin_password)
            self._wizard.select_radio_button(id="saveGlobalAdminCredsOption")
        self._wizard.select_radio_button(id="mfaConfirmation")
        self._wizard.click_next()
        self._admin_console.wait_for_completion()
        self._wizard.click_button('Close')
        self._admin_console.wait_for_completion()

    @WebAction()
    def _add_service_account_for_custom_config(self, user_account, password):
        """Adds service account for custom config in the configuration page
            Args:
                user_account (str)    :   username of service account
                password (str)        :   password of service account
        """
        self._wizard.fill_text_in_field(id='svcAccEmailAddress', text=user_account)
        self._wizard.fill_text_in_field(id='svcAccPassword', text=password)
        self._wizard.fill_text_in_field(id='svcAccConfirmPassword', text=password)
        self._wizard.select_radio_button(id="permissionsConfirmation")
        self._wizard.select_radio_button(id="mfaConfirmation")
        self._wizard.click_next()
        self._admin_console.wait_for_completion()
        self._wizard.click_button('Close')
        self._admin_console.wait_for_completion()

    @WebAction()
    def _edit_service_account_for_custom_config(self, password):
        """Edits service account password in the configuration page
            Args:
                password (str)      :   password of service account
        """
        self._driver.find_element(By.ID, 'password').send_keys(password)
        self._driver.find_element(By.ID, 'confirmPassword').send_keys(password)
        self._rmodal_dialog.click_submit()
        self._admin_console.wait_for_completion()

    @WebAction()
    def _add_azure_app_for_express_config(self, global_admin, global_admin_password):
        """Adds azure app for express config in the configuration page
            Args:
                global_admin (str)              :   username of global admin
                global_admin_password (str)     :   password of global admin
        """
        self._wizard.click_next()
        if self._is_global_admin_label_available():
            self._wizard.fill_text_in_field(id='globalAdmin', text=global_admin)
            self._wizard.fill_text_in_field(id='globalAdminPassword', text=global_admin_password)
            self._wizard.select_radio_button(id="saveGlobalAdminCredsOption")
            self._wizard.select_radio_button(id="mfaConfirmation")
        else:
            self._wizard.select_radio_button(id="mfaConfirmation")
        self._wizard.click_button(name='Create Azure app')
        self._admin_console.wait_for_completion()
        self._authorize_permissions(global_admin, global_admin_password)
        if self.agent_app_type == Office365Apps.AppType.share_point_online:
            self._create_app_principal()
        self._wizard.click_next()
        self._wizard.click_button('Close')

    @WebAction()
    def _add_azure_app_for_custom_config_client_creation(self,
                                                         application_id,
                                                         application_key_value,
                                                         azure_directory_id):
        """Adds azure app for custom config during client creation
            Args:
                application_id (str)         :   id of azure app
                application_key_value (str)  :   key value of azure app
                azure_directory_id (str)     :   directory id of azure app
        """
        self._admin_console.fill_form_by_id('applicationId', application_id)
        self._admin_console.fill_form_by_id('secretAccessKey', application_key_value)
        self._admin_console.fill_form_by_id('tenantName', azure_directory_id)
        # app principal checkbox for SharePoint
        if self.agent_app_type == Office365Apps.AppType.share_point_online:
            self._driver.find_element(By.XPATH, "//label[@for='appPrincipalConfigured']").click()
        self._modal_dialog.click_submit()
        self._admin_console.wait_for_completion()

    @WebAction()
    def _add_azure_app_for_custom_config(self,
                                         application_id,
                                         application_key_value,
                                         azure_directory_id):
        """Adds azure app for custom config in the configuration page
            Args:
                application_id (str)         :   id of azure app
                application_key_value (str)  :   key value of azure app
                azure_directory_id (str)     :   directory id of azure app
        """
        self._wizard.fill_text_in_field(id='addAzureApplicationId', text=application_id)
        self._wizard.fill_text_in_field(id='addAzureApplicationSecretKey',
                                        text=application_key_value)
        self._wizard.select_radio_button(id='permissionsConfirmation')
        self._wizard.click_next()
        self._admin_console.wait_for_completion()
        self._wizard.click_button('Close')
        self._admin_console.wait_for_completion()

    @WebAction()
    def _edit_azure_app_for_custom_config(self, application_key_value):
        """Edits azure app key value in the configuration page
            Args:
                application_key_value (str)   :   key value of azure app
        """
        self._admin_console.fill_form_by_id('editAzureApplicationSecretKey', application_key_value)
        self._rmodal_dialog.click_submit()
        self._admin_console.wait_for_completion()

    @WebAction()
    def _add_global_admin(self, global_admin, password):
        """
        Adds global admin in the configuration page
        Args:
            global_admin (str)  :   New value of global admin to be set
            password (str)      :   Password for global admin account
        """
        self._rpanel_info.click_add_icon(self._admin_console.props['label.globalAdministrator'])
        self._admin_console.wait_for_completion()
        if self.agent_app_type == Office365Apps.AppType.share_point_online:
            self._rmodal_dialog.fill_text_in_field('accountName', global_admin)
        elif self.agent_app_type == Office365Apps.AppType.one_drive_for_business:
            self._driver.find_element(By.ID, 'globalAdministrator').send_keys(global_admin)
        elif self.agent_app_type == Office365Apps.AppType.exchange_online:
            self._driver.find_element(By.ID, 'exchangeAdminSmtpAddress').send_keys(global_admin)
        self._rmodal_dialog.fill_text_in_field('password', password)
        self._rmodal_dialog.fill_text_in_field('confirmPassword', password)
        self._rmodal_dialog.click_submit()
        self._admin_console.wait_for_completion()

    @WebAction(delay=2)
    def _edit_global_admin(self, new_global_admin, new_admin_pwd):
        """
        Modifies the global admin to the new value given as argument
        Args:
            new_global_admin:   New value of global admin to be set
            new_admin_pwd:      Password for global admin account
        """
        self._rpanel_info.click_action_item_for_tile_label(
            self._admin_console.props['label.globalAdministrator'], 'Edit')

        self.tcinputs['GlobalAdmin'] = new_global_admin
        self.tcinputs['Password'] = new_admin_pwd

        self._admin_console.wait_for_completion()
        if self.agent_app_type == Office365Apps.AppType.share_point_online:
            self._rmodal_dialog.fill_text_in_field('accountName', new_global_admin)
        elif self.agent_app_type == Office365Apps.AppType.one_drive_for_business:
            self._driver.find_element(By.ID, 'globalAdministrator').clear()
            self._driver.find_element(By.ID, 'globalAdministrator').send_keys(new_global_admin)
        elif self.agent_app_type == Office365Apps.AppType.exchange_online:
            self._driver.find_element(By.ID, 'exchangeAdminSmtpAddress').clear()
            self._driver.find_element(By.ID, 'exchangeAdminSmtpAddress').send_keys(new_global_admin)
        self._rmodal_dialog.fill_text_in_field('password', new_admin_pwd)
        self._rmodal_dialog.fill_text_in_field('confirmPassword', new_admin_pwd)
        self._rmodal_dialog.click_submit()
        self._admin_console.wait_for_completion()

    @WebAction(delay=2)
    def _edit_server_plan(self, server_plan):
        """
        Modifies the server plan to the new value given as argument
        Args:
            server_plan: New value of server plan to be set
        """
        self.tcinputs['ServerPlan'] = server_plan
        if self.is_react:
            self._driver.find_element(By.XPATH,
                                      f"//div[text() = '{self._admin_console.props['label.o365.serverPlan']}']"
                                      f"//following-sibling::div//descendant::button[@title = 'Edit']").click()
            self._admin_console.wait_for_completion()
            self._wizard.select_drop_down_values(values=[server_plan], id='plan')
            self._rmodal_dialog.click_submit()
            self._rmodal_dialog.click_submit()
            self._driver.find_element(By.XPATH, "//div[text()='Ok']").click()

        else:
            panel = PanelInfo(self._admin_console,
                              title=self._admin_console.props['label.infrastructurePane'])
            self._driver.find_element(By.XPATH,
                                      f"//span[text()='{self._admin_console.props['label.o365.serverPlan']}'"
                                      f"]//ancestor::li//a[contains(text(), 'Edit')]"
                                      ).click()
            self._admin_console.wait_for_completion()
            self._dropdown.select_drop_down_values(values=[server_plan],
                                                   drop_down_id='planSummaryDropdown')
            panel.save_dropdown_selection(self._admin_console.props['label.o365.serverPlan'])
            self._modal_dialog.click_submit()
            self._admin_console.wait_for_completion()
            self._modal_dialog.click_submit()
            self._admin_console.wait_for_completion()

    @WebAction(delay=2)
    def _edit_stream_count(self, new_stream_count):
        """
        Modifies the count of max streams to the new value given as argument
        Args:
            new_stream_count:   New value of 'Max streams' to be set
        """
        self.tcinputs['MaxStreams'] = new_stream_count
        if self.is_react:
            rpanel = RPanelInfo(self._admin_console,
                                title=self._admin_console.props['label.infrastructurePane'])
            self._driver.find_element(By.XPATH,
                                      "//div[text() = 'Max streams']//following-sibling::div//descendant::button[@title = 'Edit']").click()
            self._admin_console.wait_for_completion()
            rpanel.fill_input(label='Max streams', text=new_stream_count)
            rpanel.click_button('Submit')
            self._admin_console.wait_for_completion()

        else:
            panel = PanelInfo(self._admin_console,
                              title=self._admin_console.props['label.infrastructurePane'])
            self._driver.find_element(By.XPATH,
                                      "//span[text()='Max streams']//ancestor::li//a[contains(text(), 'Edit')]"
                                      ).click()
            self._admin_console.wait_for_completion()
            self._driver.find_element(By.ID, "maxStream").clear()
            self._driver.find_element(By.ID, "maxStream").send_keys(new_stream_count)
            panel.save_dropdown_selection('Max streams')

    @WebAction(delay=2)
    def _edit_index_server(self, new_index_server):
        """
        Modifies the index server to the new value given as argument
        Args:
            new_index_server:   New value of index server to be set
        """
        self.tcinputs['IndexServer'] = new_index_server
        self._driver.find_element(By.XPATH,
                                  "//span[text()='Index server']//ancestor::li//a[contains(text(), 'Edit')]"
                                  ).click()
        self._admin_console.wait_for_completion()
        self._dropdown.select_drop_down_values(
            values=[new_index_server], drop_down_id='updateIndexServer_isteven-multi-select_#2168')
        self._modal_dialog.click_submit()
        self._modal_dialog.click_submit()
        self._admin_console.wait_for_completion()

    @WebAction(delay=2)
    def _edit_access_node(self,
                          new_shared_path,
                          new_user_account,
                          new_password,
                          new_access_node=None):
        """
        Modifies the shared path and access node values
        Args:
            new_access_node:    New value(s) to be set for access node
            new_shared_path:    New value to be set for shared path
            new_user_account:   Local system account to access shared path
            new_password:       Password for local system account
        """
        self.tcinputs['UNCPath'] = new_shared_path
        self.tcinputs['username'] = new_user_account
        self.tcinputs['password'] = new_password
        if self.is_react:
            rpanel = RPanelInfo(self._admin_console,
                                title=self._admin_console.props['label.infrastructurePane'])
            self._driver.find_element(By.XPATH,
                                      "//span[text()='Access nodes']//parent::div//parent::div//following-sibling::div//descendant::button[@title='Edit']"
                                      ).click()
            self._admin_console.wait_for_completion()
            if new_access_node:
                self.tcinputs['AccessNode'] = new_access_node
                if isinstance(new_access_node, list):
                    self._wizard.select_drop_down_values(values=new_access_node, id='accessNodeDropdown')

                else:
                    self._wizard.select_drop_down_values(values=[new_access_node], id='accessNodeDropdown')
            self._enter_shared_path_for_multinode(new_shared_path)
            # rpanel.fill_input(label='Max streams', text=new_stream_count)
            self._add_account_for_shared_path(new_user_account, new_password)
            self._admin_console.wait_for_completion()
            self._rmodal_dialog.click_submit()
        else:
            self._driver.find_element(By.XPATH,
                                      "//span[text()='Access nodes']//ancestor::li//a[contains(text(), 'Edit')]"
                                      ).click()
            self._admin_console.wait_for_completion()
            if new_access_node:
                self.tcinputs['AccessNode'] = new_access_node
                if isinstance(new_access_node, list):
                    self._dropdown.select_drop_down_values(values=new_access_node,
                                                           drop_down_id='accessNodes')
                else:
                    self._dropdown.select_drop_down_values(values=[new_access_node],
                                                           drop_down_id='accessNodes')
            self._enter_shared_path_for_multinode(new_shared_path)
            self._add_account_for_shared_path(new_user_account, new_password)
            self._admin_console.wait_for_completion()
            close_xpath = ("//div[contains(@class, 'modal-content')]"
                           "//button[contains(@class, 'btn btn-default')]")
            if self._admin_console.check_if_entity_exists('xpath', close_xpath):
                self._modal_dialog.click_cancel()
            self._admin_console.wait_for_completion()

    @WebAction(delay=2)
    def _click_create_azure_ad_app(self):
        """Clicks create azure ad app button"""
        create_azure_ad_app_xpath = "//button[@id='createOffice365App_button_#6055']"
        self._driver.find_element(By.XPATH, create_azure_ad_app_xpath).click()
        self._check_for_errors()

    @WebAction()
    def _check_for_errors(self):
        """Checks for any errors while creating app"""
        error_xpaths = [
            "//div[@class='help-block']",
            "//div[@ng-bind='addOffice365.appCreationErrorResponse']"
        ]

        for xpath in error_xpaths:
            if self._admin_console.check_if_entity_exists('xpath', xpath):
                if self._driver.find_element(By.XPATH, xpath).text:
                    raise CVWebAutomationException(
                        'Error while creating the app: %s' %
                        self._driver.find_element(By.XPATH, xpath).text
                    )

    @WebAction(delay=3)
    def _click_authorize_now(self):
        """Clicks on authorize now button"""
        if self.is_react:
            self._admin_console.select_hyperlink("here")
        else:
            self._admin_console.select_hyperlink(self._admin_console.props['action.authorize.app'])

    @WebAction(delay=3)
    def _switch_to_window(self, window):
        """Switch to specified window

                Args:
                    window (WebElement)  -- Window element to switch to
        """
        self._driver.switch_to.window(window)

    @WebAction(delay=2)
    def _close_current_tab(self):
        """
        To close the current tab
        """
        self._driver.close()

    @WebAction(delay=10)
    def _enter_email(self, email):
        """Enter email in email type input

                Args:
                    email (str)  --  Microsoft Global Admin email
        """
        self._admin_console.wait_for_element_to_be_clickable('i0116')
        if self._admin_console.check_if_entity_exists('id', 'i0116'):
            self._admin_console.fill_form_by_id('i0116', email)
            self._click_submit()
        elif self._admin_console.check_if_entity_exists('id', 'otherTileText'):
            self._driver.find_element(By.ID, "otherTileText").click()
            self._enter_email(email)

    @WebAction(delay=2)
    def _enter_password(self, password):
        """Enter password into password type input

                Args:
                    password (str)  --  Global Admin password
        """
        self._admin_console.wait_for_element_to_be_clickable('i0118')
        if self._admin_console.check_if_entity_exists('id', 'i0118'):
            self._admin_console.fill_form_by_id('i0118', password)
            self._click_submit()

    @WebAction(delay=3)
    def _click_submit(self):
        """Click submit type button"""
        # This xpath is used to click submit button on Microsoft login pop up window
        ms_submit_xpath = "//input[@type='submit']"
        self._admin_console.scroll_into_view(ms_submit_xpath)
        self._driver.find_element(By.XPATH, ms_submit_xpath).click()

    @WebAction(delay=2)
    def _get_new_app_name(self):
        """Fetches the newly created Azure app name from MS permission dialog"""
        return self._driver.find_element(By.XPATH, "//div[@class='row app-name']").text

    @WebAction(delay=2)
    def _check_app_creation_success(self):
        """Checks if all the steps for app creation are successfully executed"""
        count: int = 1
        timeout = int(time.time()) + 60
        in_progress_xpath = "//div[contains(@class,'MuiGrid-root')]//div[@id='spinner']"
        success_xpath = "//div[contains(@class,'MuiGrid-root')]//*[name()='svg']//*[name()='g' and @clip-path='url(" \
                         "#Success_svg__a)']"

        while count < 3:
            if self._admin_console.check_if_entity_exists(entity_name="xpath", entity_value=in_progress_xpath):
                self.log.info("Corresponding action is in progress...")
                time.sleep(15)
                count = count + 1

            if self._admin_console.check_if_entity_exists(entity_name="xpath", entity_value=success_xpath):
                self.log.info("Azure App configuration was successful")
                return True

            if count == 3:
                self.log.info("Timeout in configuring the multi tenant App")
                raise CVWebAutomationException("App configuration was unsuccessful")

            if int(time.time()) >= timeout:
                return True

    @WebAction()
    def _authorize_permissions(self, global_admin, password):
        """Clicks authorize now and enables permissions for the app

            Args:
                global_admin (str)  --  Microsoft Global admin email id
                password (str)  --  Global admin password
        """
        wait = WebDriverWait(self._driver, 300)
        wait.until(EC.number_of_windows_to_be(2))
        window_handles = self._driver.window_handles
        admin_console_window = window_handles[0]
        azure_window = window_handles[1]
        self._driver.switch_to.window(azure_window)
        self._enter_email(global_admin)
        self._enter_password(password)
        self.newly_created_app_name = self._get_new_app_name()
        self._click_submit()
        self._driver.switch_to.window(admin_console_window)
        wait.until(EC.number_of_windows_to_be(1))
        if self._check_app_creation_success():
            self.log.info("Azure app is created and authorized successfully")
        else:
            self.log.error("Azure app is not created and there are some errors")
        self._admin_console.click_button_using_text("Close")
        self._admin_console.wait_for_completion()

    @WebAction(delay=2)
    def _click_show_details(self):
        """Clicks the Show details link for Azure App"""
        if self._admin_console.check_if_entity_exists(
                "link", self._admin_console.props['label.showDetails']):
            self._admin_console.select_hyperlink(self._admin_console.props['label.showDetails'])

    @WebAction(delay=2)
    def verify_modern_authentication(self):
        """Verifies if app is created using modern authentication enabled."""

        self._admin_console.select_configuration_tab()
        panel_details = self._panel_info.get_details() if not self.is_react else self._rpanel_info.get_details()
        if panel_details['Use modern authentication'] == 'Enabled':
            self.modern_authentication = True
        else:
            self.modern_authentication = False

    @WebAction(delay=2)
    def _verify_sharepoint_service_account(self):
        """Verify if one sharepoint service account is created"""
        try:
            sp_service_acc_xpath = ("//span[@ng-bind='addOffice365.office365Attributes."
                                    "generalAttributes.sharepointOnlineServiceAccount']")
            text = self._driver.find_element(By.XPATH, sp_service_acc_xpath).text
            if "CVSPBackupAccount" in text:
                self.log.info('Sharepoint Service account created from web server:%s', text)
        except:
            raise CVWebAutomationException(
                "Service account not created for SharePoint Online from web server")

    @WebAction(delay=2)
    def _verify_app_principal(self):
        """Verify if one sharepoint app principal is authorized"""
        try:
            app_principal_xpath = "//div[@data-ng-if='addOffice365.isAzureAppPrincipleCreated']"
            text = self._driver.find_element(By.XPATH, app_principal_xpath).text
            if "App principal created" in text:
                self.log.info('For SharePoint Online:%s', text)
        except:
            raise CVWebAutomationException("App principal not created for sharepoint online")

    def _is_create_app_principal_dialog_open(self):
        """Checks if the dialog for 'Create app principal' is open or not"""
        return self._admin_console.check_if_entity_exists(
            'xpath', ("//*[contains(@class, 'mui-modal-title') "
                      "and contains(text(), 'Create app principal')]"))

    @WebAction(delay=2)
    def _create_app_principal(self):
        """Creates app principal required for SharePoint V2 Pseudo Client Creation"""
        if self.is_react:
            if not self._is_create_app_principal_dialog_open():
                self._driver.find_element(By.XPATH, "//button[@label='here']").click()
            sharepoint_app_id = self._driver.find_element(
                By.XPATH, "//p[contains(text(), 'Copy the App ID')]/following-sibling::p").text
            sharepoint_tenant_id = self._driver.find_element(
                By.XPATH, "//p[contains(text(), 'Copy the tenant ID')]/following-sibling::p").text
            sharepoint_request_xml = self._driver.find_element(By.XPATH, "//div/code").text
        else:
            sharepoint_app_id = self._driver.find_element(By.XPATH,
                                                          "//code[@data-ng-bind='o365SPCreateAppPrincipleCtrl.azureAppDetails.azureAppId']").text
            sharepoint_tenant_id = self._driver.find_element(By.XPATH,
                                                             "//code[@data-ng-bind='o365SPCreateAppPrincipleCtrl.azureAppDetails.azureDirectoryId']").text
            sharepoint_request_xml = self._driver.find_element(By.XPATH,
                                                               "//code[@data-ng-bind='o365SPCreateAppPrincipleCtrl.appPrincipleXML']").text

        while len(self._driver.window_handles) < 2:
            self._driver.find_element(
                By.XPATH,
                ".//a[contains(@href, '_layouts/15/appinv.aspx')]"
            ).click()

        admin_console_window = self._driver.window_handles[0]
        app_principal_window = self._driver.window_handles[1]

        if not self._admin_console.check_if_entity_exists("class", "ms-input"):
            self._switch_to_window(app_principal_window)
            self._admin_console.wait_for_completion()

        self._driver.find_element(By.XPATH,
                                  "//input[contains(@id, 'TxtAppId')]").send_keys(sharepoint_app_id)
        self._driver.find_element(By.XPATH, "//input[ @value = 'Lookup']").click()
        self._admin_console.wait_for_completion()
        self._driver.find_element(By.XPATH,
                                  "//input[@title = 'App Domain']").send_keys(sharepoint_tenant_id)
        self._driver.find_element(By.XPATH,
                                  "//textarea[@title = 'Permission Request XML']").send_keys(
            sharepoint_request_xml)
        self._driver.find_element(By.XPATH, "//input[ @value = 'Create']").click()
        self._admin_console.wait_for_completion()
        self._driver.find_element(By.XPATH, "//input[ @value = 'Trust It']").click()
        self._admin_console.wait_for_completion()
        self._close_current_tab()
        self._switch_to_window(admin_console_window)
        self._admin_console.wait_for_completion()
        if self.is_react:
            self._driver.find_element(
                By.XPATH,
                "//h4[text()='Confirmation']/following-sibling::div/div//label//input[@id='appPrincipalConfirmation']"
            ).click()
            self._admin_console.wait_for_completion()
            self._admin_console.click_button("Close")
        else:
            self._driver.find_element(By.XPATH,
                                      "//span[text()='Confirm if the SharePoint app principal is created. ']").click()
            self._admin_console.wait_for_completion()
            self._driver.find_element(By.ID, "o365SPChangePlanAssociation_button_#2").click()

        # self._admin_console.wait_for_completion()
        # if self.is_react:
        #     self._admin_console.click_button("Close")
        # else:
        #     self._driver.find_element(By.ID, "o365SPChangePlanAssociation_button_#2").click()
        self._admin_console.wait_for_completion()

    @WebAction(delay=2)
    def _click_show_details_for_client_readiness(self):
        """Clicks on show details for client readiness check"""
        if self.is_react:
            self._driver.find_element(By.XPATH, "//button[contains(@title, 'client readiness')]").click()
            time.sleep(15)
        else:
            self._driver.find_element(By.XPATH,
                                      f"//a[contains(text(), '{self._admin_console.props['label.showDetails']}')]").click()

    @WebAction(delay=2)
    def _get_client_readiness_value(self):
        """Gets the value of Client Readiness check"""
        if self.is_react:
            readiness = Rtable(self._admin_console).get_column_data('Status')
        else:
            elements = self._driver.find_elements(By.XPATH,
                "//td[contains(@class,'grid-cell-hover')]/span[text()]")
            readiness = list()
            for row in elements:
                readiness.append(row.text)
        return readiness

    @WebAction(delay=2)
    def _open_add_user_panel(self):
        """Opens the panel to add users to the client"""
        try:
            self._driver.find_element(By.ID, self.app_type.ADD_BUTTON_ID.value).click()
            time.sleep(3)
            self._driver.find_element(By.ID, self.app_type.ADD_USER_BUTTON_ID.value).click()
            self._admin_console.wait_for_completion()
        except (ElementClickInterceptedException, NoSuchElementException):
            if self.agent_app_type == Office365Apps.AppType.exchange_online:
                self._driver.find_element(By.XPATH,
                                          f"//span[text()='{self._admin_console.props['label.addMailbox']}']").click()

    @WebAction(delay=2)
    def _select_all_users(self):
        """Selects all the users associated with the app"""
        elements = self._driver.find_elements(By.XPATH,
                                              "// input[@class ='k-checkbox k-checkbox-md k-rounded-md']")
        elements[0].click()

    @WebAction(delay=2)
    def _select_user(self, user_name, is_group=False):
        """
        Selects the user specified
        Args:
            user_name (str):    Item to be selected
            is_group (bool):    Whether or not the item is a group

        """
        if is_group:
            self._admin_console.access_tab(self.app_type.CONTENT_TAB.value)
            xpath = (f"//*[@id='cv-k-grid-td-DISPLAY_NAME']/span[normalize-space()='{user_name}']"
                     f"/ancestor::tr/td[contains(@id,'checkbox')]")
        else:
            self._admin_console.access_tab(self.app_type.ACCOUNT_TAB.value)
            if self.is_react:
                xpath = (f"//table[@class='k-grid-table']//span[text()='{user_name}']"
                         f"//ancestor::tr//td//input[@type='checkbox']")
            else:
                xpath = (f"//*[@id='cv-k-grid-td-URL']/span[normalize-space()='{user_name}']"
                         f"/ancestor::tr/td[contains(@id,'checkbox')]")

        # First row in the table has a dynamic id allocation where id = office365OneDriveUsersTable_active_cell
        if len(self._driver.find_elements(By.XPATH, xpath)) == 0:
            if is_group:
                xpath = (f"//*[@id='cv-k-grid-td-DISPLAY_NAME']/span[normalize-space()='{user_name}']"
                         f"/ancestor::tr/td[contains(@id,'office365OneDriveUsersTable_active_cell')]")
            else:
                xpath = (f"//*[@id='cv-k-grid-td-URL']/span[normalize-space()='{user_name}']"
                         f"/ancestor::tr/td[contains(@id,'office365OneDriveUsersTable_active_cell')]")
        if self._admin_console.check_if_entity_exists("xpath", xpath):
            self._driver.find_element(By.XPATH, xpath).click()
        else:
            self.__rtable.select_rows([user_name])
        self._admin_console.wait_for_completion()

    @WebAction(delay=2)
    def _click_backup(self):
        """Clicks the backup button on the app page"""
        if self.is_react:
            self.__rtable.access_toolbar_menu("Backup")
        else:
            self.__table.access_toolbar_menu(menu_id=self.app_type.BACKUP_MENU_ID.value)

    @WebAction(delay=2)
    def _click_add_autodiscover(self):
        """Clicks the Add button on Content tab"""
        if not self.is_react:
            self.__table.access_toolbar_menu(menu_id=self.app_type.ADD_MENU_ID.value)
        else:
            self.__rtable.access_toolbar_menu(menu_id="Add")

    @WebAction(delay=2)
    def _click_more_actions(self):
        """Clicks the more actions link on the app page"""
        self._rpanel_info.click_button(button_name='More')

    @WebAction(delay=2)
    def _click_restore(self, account=True, recovery_point=False, client_restore_type=None):
        """Clicks the browse button on the app page

                account (boolean)  --   If true - whole mailbox/user is restored.
                                        If false messages/files are restored

                client_restore_type(string)  -- restore type option for client level restore to support AD group
                Ex:"Restore messages","Restore mailboxes","Restore mailboxes by AD group","Restore files","Restore users","Restore users by AD group"
                These Enums added in constants
        """
        if not self.is_react:
            try:
                mouse_move_over = self._driver.find_element(By.ID, self.app_type.CLICK_RESTORE_ID.value)
                if account:
                    if self._admin_console.check_if_entity_exists("xpath", self.app_type.MAILBOX_RESTORE_XPATH.value):
                        mouse_click = self._driver.find_element(By.XPATH,
                                                                self.app_type.MAILBOX_RESTORE_XPATH.value)
                    else:
                        mouse_click = self._driver.find_element(By.XPATH,
                                                                self.app_type.ACCOUNT_RESTORE_XPATH.value)
                    self._admin_console.mouseover_and_click(mouse_move_over, mouse_click)
                elif recovery_point:
                    mouse_click = self._driver.find_element(By.XPATH,
                                                            self.app_type.ACCOUNT_RECOVERY_XPATH.value
                                                            )
                    self._admin_console.mouseover_and_click(mouse_move_over, mouse_click)
                else:
                    mouse_click = self._driver.find_element(By.XPATH,
                                                            self.app_type.BROWSE_RESTORE_XPATH.value)
                    self._admin_console.mouseover_and_click(mouse_move_over, mouse_click)
                    if self.agent_app_type == Office365Apps.AppType.exchange_online:
                        self._restore_messages()
            except Exception:
                self._driver.find_element(By.XPATH, "//span[normalize-space()='Restore']").click()
        else:
            self.__rtable.access_toolbar_menu("Restore")
            if account:
                element = self._driver.find_element(By.ID, "RESTORE_ENTIRE_CONTENT")

            else:
                element = self._driver.find_element(By.ID, "BROWSE")
            element.click()
            if client_restore_type:
                self._wizard.select_card(client_restore_type)
                self._wizard.click_next()
            self._admin_console.wait_for_completion()

    @WebAction(delay=2)
    def _click_selectall_browse(self):
        """Clicks the Select all checkbox"""
        self._browse.select_for_restore(all_files=True)

    @WebAction(delay=2)
    def _restore_messages(self):
        """Restores messages from browse window"""
        self._click_selectall_browse()
        self._admin_console.select_hyperlink("Restore")
        self._driver.find_element(By.XPATH,
                                  "//a[@class='nowrap']//span[text()='Items in current page']").click()

    @WebAction(delay=2)
    def _fetch_all_apps(self):
        """Fetches the list of apps from configuration page"""
        if not self.is_react:
            self._admin_console.refresh_page()
            panel = PanelInfo(self._admin_console, title='Exchange connection settings')
            panel.access_tab(tab_text=self._admin_console.props['label.azureApps'])
            app_details = self.__table.get_column_data(self._admin_console.props['label.addAzureApp'])
            app_status = self.__table.get_column_data(
                self._admin_console.props['label.recovery.points.status'])
        else:
            self._admin_console.refresh_page()
            self._rpanel_info.access_tab(tab_text=self._admin_console.props['label.azureApps'])
            app_details = self.__rtable.get_column_data('Azure app')
            app_status = self.__rtable.get_column_data('Status')
        return dict(zip(app_details, app_status))

    @WebAction(delay=2)
    def _verify_app(self):
        """Verifies whether the newly created app is present in the list of configuration page"""
        apps_list = self._fetch_all_apps()
        self.log.info('Apps list:%s', apps_list)
        if (self.newly_created_app_name not in apps_list and
                (apps_list[self.newly_created_app_name] !=
                 self._admin_console.props['app.status.authorized'])):
            raise CVWebAutomationException(
                "New app was not found in the list on configuration page")

    @WebAction()
    def _fetch_all_service_accounts(self):
        """Fetches the list of service accounts from configuration page"""
        self._admin_console.refresh_page()
        self._rpanel_info.access_tab('Service accounts')
        if self.agent_app_type == Office365Apps.AppType.exchange_online:
            details = self.__rtable.get_column_data('Email address/User name')
        else:
            details = self.__rtable.get_column_data(self._admin_console.props['column.userAccount'])
        return details

    @WebAction(delay=2)
    def _get_job_id(self):
        """Fetches the jobID from the toast"""
        try:
            return self._admin_console.get_jobid_from_popup(5)
        # Sometime the notification prints: Backup started for clients. View job details
        # This doesn't have a job id and hence it fails here.
        # Following code to handle above case
        except (IndexError, CVWebAutomationException):
            self._click_view_jobs()
            self._jobs.access_active_jobs()
            return self._jobs.get_job_ids()[0]

    @WebAction(delay=2)
    def _verify_connection_text(self):
        """Verifies the text on the modal after verifying connection"""
        modal_content_xpath = "//div[@class='form-group ng-scope']"
        modal_text = self._driver.find_element(By.XPATH, modal_content_xpath).text
        if not modal_text == 'The status of Azure apps has been updated.':
            raise CVWebAutomationException('Verify connection did not succeed.')

    @WebAction(delay=2)
    def _add_plan_and_verify(self, change=False):
        """Changes exchange plan and verifies the same

                Args:
                    change (boolean)  --  True if it's a change plan operation
        """
        if change:
            value = self.tcinputs['NewPlan']
            self._create_inline_o365_plan()
        else:
            value = self.tcinputs['Office365Plan']
        if not self.is_react:
            if self.agent_app_type == Office365Apps.AppType.share_point_online:
                try:
                    self._dropdown.select_drop_down_values(
                        values=[value],
                        drop_down_id='o365spReAssociateWebAssociation_isteven-select_#1')
                except NoSuchElementException:
                    self._dropdown.select_drop_down_values(
                        values=[value], drop_down_id='o365spEditAssociationCtrl_isteven-select_#1')
            else:
                self._dropdown.select_drop_down_values(
                    values=[value], drop_down_id='exchangePlan_isteven-multi-select_#2')
            self._modal_dialog.click_submit()
            self._admin_console.wait_for_completion()
            notification = self._admin_console.get_notification()
            if "Successfully updated" not in notification:
                CVWebAutomationException('Change exchange plan was not successful')
        else:
            self._wizard.select_drop_down_values(id="cloudAppsPlansDropdown", values=[value])
            self._rmodal_dialog.click_submit()

    @WebAction(delay=2)
    def _job_details(self, job_id=None, return_status=False):
        """
        Waits for job completion and gets the job details
        job_id (str):- ID for the job
        """
        if not job_id:
            job_id = self._get_job_id()
        job_details = self._jobs.job_completion(job_id=job_id)
        job_details['Job Id'] = job_id
        self.log.info('job details: %s', job_details)

        if not return_status:
            if job_details['Status'] not in [
                "Committed", "Completed", "Completed w/ one or more errors"]:
                raise CVWebAutomationException(f'Job did not complete successfully - '
                                               f'Job Status: {job_details["Status"]}')
        return job_details

    @WebAction(delay=2)
    def _get_app_stat(self, stat_type):
        """Gets the stats from the app page

                Args:
                    stat_type (str)  --  Type of stat we want to fetch from App details page
                        Valid options:
                            Mails -- To fetch the number of mails displayed on App page
                            Mailboxes -- To fetch the number of mailboxes displayed on App page
                            Indexed mails -- To fetch the number of Indexed mails on App page

        """
        retry = 0
        while retry < 3:
            try:
                stat_type_temp = stat_type
                if stat_type == 'Mails':
                    stat_type_temp = 'Emails' if not self.is_react else 'Items'
                elif stat_type == 'Indexed mails':
                    stat_type_temp = 'Indexed emails'
                stat_xpath = (f"//span[@ng-bind='entity.title' and contains(text(),'{stat_type_temp}')]"
                              f"/parent::*/span[@ng-bind='entity.value']") if not self.is_react else \
                    f"//span[contains(text(),'{stat_type_temp}')]/ancestor::span/span[contains(@class,'count')]"
                element = self._driver.find_element(By.XPATH, stat_xpath)
                return element.text
            except NoSuchElementException as exp:
                self.log.info("%s Stats not updated yet. Attempt: %s", stat_type, retry + 1)
                time.sleep(10)
                self.log.info("Refreshing the page")
                self._admin_console.refresh_page()
                retry += 1

    @WebAction(delay=2)
    def _click_view_jobs(self):
        """Clicks the view jobs link from the app page"""
        if self.is_react:
            self._driver.find_element(By.XPATH, "//div[@aria-label='More' and @class='popup']").click()
            time.sleep(1)
            view_jobs_xpath = f"//div[text()='{self._admin_console.props['action.jobs']}']"
            self._driver.find_element(By.XPATH, view_jobs_xpath).click()
        else:
            view_jobs_xpath = f"//span[text()='{self._admin_console.props['action.jobs']}']"
            self._driver.find_element(By.XPATH, view_jobs_xpath).click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def _click_backupset_level_restore(self, restore_content=False):
        """Clicks the restore link from the app page

            Args:

                restore_content (bool)  :   Whether to restore content(Restore users, Restore sites etc.)

        """
        self.__rtable.select_all_rows()
        self._driver.find_element(By.ID, 'RESTORE_SUBMENU').click()
        if restore_content:
            self._driver.find_element(By.ID, 'RESTORE_ENTIRE_CONTENT').click()
        else:
            self._driver.find_element(By.ID, 'BROWSE').click()
        self._admin_console.wait_for_completion()

    @WebAction(delay=2)
    def _click_view_exports(self):
        """Clicks the view exports link from the browse page"""
        view_exports_xpath = "//div[contains(text(),'View exports')]"
        self._driver.find_element(By.XPATH, view_exports_xpath).click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def _create_inline_o365_plan(self, plan=None):
        """Create Office365 plan from edit association modal
            Args:
                    plan (str)  --  Name of o365 plan to create
        """
        if plan:
            o365_plan = plan
        else:
            o365_plan = self.tcinputs['NewPlan']
        if self.is_react:
            try:
                self._wizard.click_add_icon()
            except NoSuchElementException:
                self.log.info("Clicking add button on the Dialog box")
                self._rmodal_dialog.click_element("//button[@aria-label='Create new' or @aria-label='Add']")
                self._admin_console.wait_for_completion()
        else:
            if self.agent_app_type == Office365Apps.AppType.share_point_online:
                try:
                    self._driver.find_element(By.ID, 'o365spReAssociateWebCeateNewPlanInline').click()
                except NoSuchElementException:
                    self._driver.find_element(By.ID, 'o365SPChangePlanAssoCreateNewPlanInline').click()
            else:
                self._driver.find_element(By.ID, 'createNewPlanInline').click()
                self._admin_console.wait_for_completion()
        self._admin_console.fill_form_by_id('planName', o365_plan)
        if not self.is_react:
            self._driver.find_element(By.ID, self.app_type.CREATE_OFFICE365_PLAN_BUTTON_ID.value).click()
        else:
            rmodal_dialog = RModalDialog(self._admin_console, 'Add plan')
            rmodal_dialog.click_button_on_dialog(id='Save')
        self._admin_console.wait_for_completion()
        return o365_plan

    @WebAction()
    def _refresh_stats(self):
        """Refresh stats shown in Discovery cache info dialog"""
        refresh_stat_xpath = "//button[@aria-label ='Updates the discovery progress']"
        self._driver.find_element(By.XPATH, refresh_stat_xpath).click()

    @WebAction()
    def _get_discovery_date(self):
        """
        Get Last discovery date from discoveru stats panel
        """
        cache_date = "//div[contains(@class,'tile-row center false')]/div[text()='Cache updated on']/following-sibling::div"
        try:
            cache_date=self._rmodal_dialog._get_element(xpath=cache_date).text
        except(NoSuchElementException):
            self._refresh_stats()
            cache_date = self._rmodal_dialog._get_element(xpath=cache_date).text
        return cache_date

    @WebAction()
    def _get_discovery_status(self):
        """Gets the discovery status form the discovery cache dialog (in react)"""
        status_xpath = "//div[@aria-labelledby='customized-dialog-title']//div[contains(@class,'tile-row center " \
                       "false')]/div[text()='Status']/following-sibling::div"
        status = self._driver.find_element(By.XPATH, status_xpath).text
        return status

    @WebAction()
    def _get_discovery_percentage(self):
        """Gets the discovery percentage from the discovery cache dialog"""
        percentage_xpath = "//div[@aria-labelledby='customized-dialog-title']//div[contains(@class,'tile-row center" \
                           " false')]/div[text()='Progress']/following-sibling::div//p"
        percentage = self._driver.find_element(By.XPATH, percentage_xpath).text
        return percentage

    @WebAction(delay=2)
    def _click_exclude_plan(self):
        """Clicks the exclude plan button on action menu"""
        exclude_plan_id = self.app_type.USERS_DELETE_ID.value
        self._driver.find_element(By.ID, exclude_plan_id).click()

    @WebAction(delay=2)
    def _click_change_plan_individual(self, user=None, is_group=False):
        """Clicks the change plan button for individual user"""
        if self.is_react:
            manage_id = self.app_type.MANAGE_ID_REACT.value
            change_plan_id = self.app_type.CHANGE_OFFICE365_PLAN_ID_REACT.value
            if not user:
                user = self.users[0]
            self.__rtable.hover_click_actions_sub_menu(entity_name=user,
                                                       action_item=manage_id,
                                                       sub_action_item=change_plan_id)
        else:
            if not is_group:
                manage_id = self.app_type.USERS_MANAGE_ID.value
                change_plan_id = self.app_type.USER_CHANGE_OFFICE365_PLAN_ID.value
            else:
                manage_id = self.app_type.GROUP_MANAGE_ID.value
                change_plan_id = self.app_type.GROUP_CHANGE_OFFICE365_PLAN_ID.value
            if not user:
                user = self.users[0]
            self.__table.hover_click_actions_sub_menu(entity_name=user,
                                                      mouse_move_over_id=manage_id,
                                                      mouse_click_id=change_plan_id)

    @WebAction(delay=2)
    def _click_exclude_user(self, user=None):
        """Clicks the exclude user button under action context menu"""
        if not user:
            user = self.users[0]
        self.__rtable.hover_click_actions_sub_menu(entity_name=user,
                                                  action_item='Manage',
                                                  sub_action_item='Exclude from backup')

    @WebAction(delay=2)
    def _click_include_user(self, user=None):
        """Clicks the exclude user button under action context menu"""
        if not user:
            user = self.users[0]
        self.__rtable.hover_click_actions_sub_menu(entity_name=user,
                                                  action_item='Manage',
                                                  sub_action_item='Include in backup')

    @WebAction(delay=2)
    def _click_remove_content(self, user=None):
        """Clicks the exclude user button under action context menu"""
        if not user:
            user = self.users[0]
        self.__rtable.hover_click_actions_sub_menu(entity_name=user,
                                                  action_item='Manage',
                                                  sub_action_item='Remove from content')

    @WebAction(delay=2)
    def _click_batch_change_plan(self):
        """Clicks the change plan button from Manage content"""
        if not self.is_react:
            if self.agent_app_type == Office365Apps.AppType.share_point_online:
                change_plan_xpath = ("//li[@id='batch-action-menu_moreContextMenu_CHANGEPLAN']"
                                     "//a[@id='CHANGEPLAN']")
            else:
                change_plan_xpath = ("//li[@id='batch-action-menu_moreContextMenu_ADD_PLAN']"
                                     "//a[@id='ADD_PLAN']")
        else:
            if self.agent_app_type == Office365Apps.AppType.share_point_online:
                change_plan_xpath = "//li[@id='CHANGE_PLAN']"
            else:
                change_plan_xpath = "//li[text()='Changeplan']"
        self._driver.find_element(By.XPATH, change_plan_xpath).click()

    @WebAction(delay=2)
    def _click_manage(self):
        """Clicks on the manage button under more actions"""
        manage_xpath = "//li[@id='batch-action-menu_moreContextMenu_MANAGE']//a[@id='MANAGE']" if not \
            self.is_react else "//li[text()='Manage']"
        self._driver.find_element(By.XPATH, manage_xpath).click()

    @WebAction(delay=2)
    def _select_content(self, content_type):
        """Selects the auto discover content.
                Args:
                    content_type -- Type of auto discovery to select
                        Valid options:
                            ALL_USERS
                            ALL_PUBLIC_FOLDERS
                            ALL_OFFICE365_GROUPS
        """
        if not self.is_react:
            select_content_xpath = f"//li[@data-cv-menu-item-id='{content_type}']"
            self._driver.find_element(By.XPATH, select_content_xpath).click()
        else:
            self._wizard.expand_accordion("Advanced")
            self._wizard.select_card(content_type)
            self._wizard.click_next()
            self._wizard.click_next()

    @WebAction(delay=2)
    def _click_remove_from_content(self, entity=None):
        """Clicks the exclude user button under action context menu"""
        if self.is_react:
            self.__rtable.hover_click_actions_sub_menu(entity_name=entity,
                                                       action_item="Manage",
                                                       sub_action_item="Remove from content")

    @PageService()
    def remove_user_from_content(self, entity=None, is_group=False):
        """Removes the content from app
                Args:
                    entity (str): User/Group which has to be removed from content
                    is_group (bool): Whether user/group is to be removed
                Raises:
                    Exception if user removal is unsuccessful
        """

        # Get the list of existing users
        table = self.__table
        if self.is_react:
            table = self.__rtable

        column_field = 'column.name'
        entity_list = table.get_column_data(
                column_name=self._admin_console.props[column_field])

        # Now remove one user from the app
        self._click_remove_from_content(entity)
        if self.is_react:
            self._rmodal_dialog.click_submit()
        else:
            self._modal_dialog.click_submit()
        self._admin_console.wait_for_completion()

        # Verify that user was removed
        entity_list_new = table.get_column_data(
            column_name=self._admin_console.props[column_field])
        diff_list = list(set(entity_list) - set(entity_list_new))
        removed_entity = entity
        entity_type = 'Group' if is_group else 'User'
        if diff_list and diff_list[0] == removed_entity:
            self.log.info(f'{entity_type} {diff_list[0]} was removed from the app')
        else:
            raise CVWebAutomationException(f'There was an error in removing {entity_type}')

    @WebAction(delay=2)
    def _click_exclude_from_backup(self, entity=None):
        """Clicks the exclude user button under action context menu"""

        if self.is_react:
            self.__rtable.hover_click_actions_sub_menu(entity_name=entity,
                                                       action_item="Manage",
                                                       sub_action_item="Exclude from backup")

    @PageService()
    def exclude_from_backup(self, entity=None, is_group=False):
        """
        Excludes the given user from backup

        Args:
            user (str):         User which has to be disabled
            is_group (bool):    Whether user/group is to be disabled

        """
        self._click_exclude_from_backup(entity=entity)
        self._admin_console.wait_for_completion()
        if self.is_react:
            self._rmodal_dialog.click_submit()
        else:
            self._modal_dialog.click_submit()
        self._admin_console.wait_for_completion()
        self._admin_console.refresh_page()
        entity_type = 'Group' if is_group else 'User'
        self.log.info(f'{entity_type} excluded from backup: {entity}')

    @PageService()
    def get_app_stat(self,stat_type):
        """
        Get App stats from app page
                Args:
                    stat_type (str)  --  Type of stat we want to fetch from App details page
                        Valid options:
                            Mails -- To fetch the number of mails displayed on App page
                            Mailboxes -- To fetch the number of mailboxes displayed on App page
                            Indexed mails -- To fetch the number of Indexed mails on App page
        """
        value=self._get_app_stat(stat_type=stat_type)
        if not value:
            raise CVWebAutomationException(
                f'{stat_type} Stats were not able to get fetched from the page.')
        return value

    @WebAction()
    def __click_backup_stats(self):
        """
        Open Backup Stats Panel
        """
        self._driver.find_element(By.XPATH, "//button[@title='Show details']").click()
        self._admin_console.wait_for_completion()

    @PageService()
    def get_backup_stats(self):
        """
        Get backup values from backup stats panel
        """
        self._admin_console.access_tab(self._admin_console.props['office365dashboard.tabs.overview'])
        self.__click_backup_stats()
        details=self._rpanel_info.get_details()
        self._rmodal_dialog.click_cancel()
        return details

    @PageService()
    def backup_stats_table_data(self):
        """
        Get data from Backup stats table
        """
        self._admin_console.access_tab(self._admin_console.props['office365dashboard.tabs.overview'])
        self.__click_backup_stats()
        data=self._containertable.get_table_data()
        self._rmodal_dialog.click_cancel()
        return data


    @WebAction()
    def click_discovery_stats(self):
        """
        Open Discovery Stats Panel
        """
        self._driver.find_element(By.XPATH, "//div[@id='tile-discovery-status']//button[@title='View details']").click()

    @PageService()
    def get_discovery_stats(self):
        """
        Get Discovery Panel Stats
        """
        status = self._get_discovery_status()
        attempts = 5
        while status.lower() != "completed":
            self.log.info("Discovery is in Progress")
            time.sleep(10)
            self._refresh_stats()
            status = self._get_discovery_status()
            attempts -= 1
            if attempts == 0 and status.lower() != "completed":
                raise CVWebAutomationException("Discovery did not complete")
        percentage=self._get_discovery_percentage()
        if percentage!="100%":
            raise CVWebAutomationException("Discovery Percentage is not valid")

    @WebAction()
    def __click_refresh_cache(self):
        """
        Click Refresh Cache Button
        """
        self._driver.find_element(By.XPATH, "//button[@aria-label='Refresh cache']").click()

    @PageService()
    def verify_discovery_stats(self):
        """
        Verify discovery stats
        """
        date_before_refresh=self._get_discovery_date()
        self.__click_refresh_cache()
        time.sleep(5)
        self.get_discovery_stats()
        date_after_refresh=self._get_discovery_date()
        if date_after_refresh<=date_before_refresh:
            raise CVWebAutomationException("Discovery stats are not updated")
        self.log.info("Discovery stats are verified")
        self._admin_console.click_button(id="Cancel")

    @PageService()
    def access_mailbox(self, mailbox_name):
        """"
            Access the mailbox from the mailbox table from the O365 client landing page

            Arguments:-

            mailbox_name (str) -- mailbox name which you want to access
        """
        self.__table.access_link(mailbox_name)
        self._admin_console.wait_for_completion()

    @PageService()
    def restore_from_recovery_point(self, recovery_id):
        """
            Restores the mailbox from a recovery point

            recovery_id (str) --- ID of the recovery job
        """
        self._admin_console.access_tab(self._admin_console.props["header.monitoring"])
        self._admin_console.select_hyperlink(link_text=self._admin_console.props["label.recovery.point.list"])
        self.__table.apply_filter_over_column("Recovery point job id", recovery_id)
        self.__table.select_rows([recovery_id])
        self._click_restore(account=False, recovery_point=True)
        self._admin_console.wait_for_completion()
        self._admin_console.submit_form(wait=False)
        job_details = self._job_details()
        self.log.info('Restore Recovery Job details: %s', job_details)

    @PageService()
    def create_recovery_point_by_mailbox(self, mailbox):
        """
            Creates recovery point for a certain mailbox

            mailbox (str) --- name of the mailbox which needs to recovered
            backup_job_id (str) --- job_id corresponding to which we need to create the recovery point

            returns:

            Job details of the recovery job
        """
        self._admin_console.access_tab(self._admin_console.props["header.monitoring"])
        self._admin_console.select_hyperlink(self._admin_console.props["label.recovery.point.list"])
        self._admin_console.select_hyperlink(link_text=self._admin_console.props["label.createRecoveryPoint"])
        self._driver.find_element(By.ID, "userBrowse_btn").click()
        self._admin_console.wait_for_completion()
        self.__table.select_rows([mailbox])
        self._admin_console.submit_form()
        self._admin_console.submit_form()
        self._modal_dialog.click_submit()
        self._admin_console.wait_for_completion()
        job_details = self._job_details()
        self.log.info('Recovery Point Creation Job Details: %s', job_details)
        return job_details

    @PageService()
    def get_discovery_status(self, mailbox):
        """
            Fetches the discovery status of the mailbox

            mailbox (str) -- mailbox name of which discovery status needs to be fetched
        """
        visible_columns = self.__table.get_visible_column_names()
        if "Discovery type" not in visible_columns:
            self.__table.display_hidden_column("Discovery type")
        self.__table.apply_filter_over_column("Name", mailbox)
        column_data = self.__table.get_column_data("Discovery type")[0]
        self.__table.clear_column_filter("Name")
        return column_data

    @PageService()
    def get_all_office365_apps(self):
        """
        List of all App Names
        """
        return self.__rtable.get_column_data(self._admin_console.props['label.name'])

    @PageService()
    def access_office365_app(self, app_name):
        """Accesses the Office365 app from the Office365 landing page

                Args:
                    app_name (str)  --  Name of the Office365 app to access

        """
        current_tab = self._admin_console.get_current_tab()
        if current_tab == self._admin_console.props['office365dashboard.tabs.overview']:
            self._admin_console.access_tab(self._admin_console.props['office365dashboard.tabs.apps'])
        self.__rtable.access_link(app_name)
        # self._driver.find_element(By.XPATH, "(//span[@ng-bind='tab.title'])[2]").click()
        if self.agent_app_type == Office365Apps.AppType.exchange_online:
            current_tab = self._admin_console.get_current_tab()
            if current_tab == self._admin_console.props['office365dashboard.tabs.overview']:
                self._admin_console.access_tab(self._admin_console.props['label.mailboxes'])

    @PageService()
    def check_if_app_exists(self, app_name):
        """Checks if the given app already exists

                Args:
                    app_name (str)  --  Name of the Office365 app to check
        """
        return (self.__rtable.is_entity_present_in_column(self._admin_console.props['label.name'],
                                                          app_name) or
                self._admin_console.check_if_entity_exists(
                    "xpath", f"//a[contains(text(), '{app_name}')]"))

    @PageService()
    def create_office365_app(self, time_out=600, poll_interval=10):
        """
        Creates O365 App

        Args:

            time_out (int): Time out for app creation

            poll_interval (int): Regular interval for app creating check
        """
        current_tab = self._admin_console.get_current_tab()
        if current_tab == self._admin_console.props['office365dashboard.tabs.overview']:
            self._admin_console.access_tab(self._admin_console.props['office365dashboard.tabs.apps'])
        # General Required details
        name = self.tcinputs['Name']

        if self.check_if_app_exists(name):
            self.delete_office365_app(name)

        self._create_app(self.agent_app_type)

        if self.agent_app_type in (Office365Apps.AppType.exchange_online,
                                   Office365Apps.AppType.one_drive_for_business,
                                   Office365Apps.AppType.share_point_online):
            # Required details for Exchange Online and OneDrive for Business
            index_server = None
            server_plan = None
            access_node = None
            client_group = None
            global_admin = None
            password = None
            application_id = None
            application_key_value = None
            azure_directory_id = None
            azure_certificate_path = None
            azure_certificate_password = None
            is_express_config = False
            site_admin_url = None
            region=None
            # sp_service_account_username = None
            # sp_service_account_password = None
            if "Region" in self.tcinputs:
                region=self.tcinputs['Region']
            if "ServerPlan" in self.tcinputs:
                server_plan = self.tcinputs['ServerPlan']
            if 'InfraPoolInfo' not in self.tcinputs:
                if 'IndexServer' in self.tcinputs:
                    index_server = self.tcinputs['IndexServer']
                if 'AccessNode' in self.tcinputs:
                    access_node = self.tcinputs['AccessNode']
                elif 'ClientGroup' in self.tcinputs:
                    client_group = self.tcinputs['ClientGroup']
            if 'GlobalAdmin' in self.tcinputs:
                is_express_config = True
                global_admin = self.tcinputs['GlobalAdmin']
                password = self.tcinputs['Password']
            else:
                if (not all(item in self.tcinputs for item in ['ApplicationId', 'ApplicationSecret', 'AzureDirectoryId',
                                                               'CertificatePath', 'CertificatePassword'])
                        and not all(item in self.tcinputs for item in ['application_id', 'application_key_value',
                                                                       'azure_directory_id', 'certificate_path',
                                                                       'certificate_password'])):
                    raise Exception("Missing Azure App config details in input JSON")
                application_id = self.tcinputs.get('ApplicationId',
                                                  self.tcinputs.get('application_id'))
                application_key_value = self.tcinputs.get('ApplicationSecret',
                                                          self.tcinputs.get('application_key_value'))
                azure_directory_id = self.tcinputs.get('AzureDirectoryId',
                                                       self.tcinputs.get('azure_directory_id'))
                azure_certificate_path = self.tcinputs.get('CertificatePath', self.tcinputs.get('certificate_path'))
                azure_certificate_password = self.tcinputs.get('CertificatePassword',
                                                               self.tcinputs.get('certificate_password'))
                if self.agent_app_type == Office365Apps.AppType.share_point_online:
                    site_admin_url = self.tcinputs['SiteAdminUrl']

            if self.is_react:
                if self._admin_console.check_if_entity_exists("xpath", "//div[@id='storageRegion']"):
                    self._wizard.select_drop_down_values(id='storageRegion', values=[region])
                    self._wizard.click_next()
                    self._admin_console.wait_for_completion()
                # fill name
                self._wizard.fill_text_in_field(id='appNameField', text=name)
                self._wizard.click_next()
                self._admin_console.wait_for_completion()
                # select Server plan
                if self._admin_console.check_if_entity_exists('xpath',"//input[@id='searchPlanName']"):
                    self._wizard.select_plan(plan_name=server_plan)
                    self._wizard.click_next()
                    self._admin_console.wait_for_completion()
                # select index server and accessnode
                if self._admin_console.check_if_entity_exists(
                        'xpath', "//div[contains(@id, 'IndexServersDropdown')]"):
                    self._wizard.select_drop_down_values(values=[index_server], id='IndexServersDropdown')
                if access_node:
                    if isinstance(access_node, list):
                        self._wizard.select_drop_down_values(values=access_node, id='accessNodeDropdown')
                        self._enter_shared_path_for_multinode()
                        self._add_account_for_shared_path()
                    else:
                        self._wizard.select_drop_down_values(values=[access_node], id='accessNodeDropdown')

                elif client_group:
                    self._wizard.select_drop_down_values(values=[client_group], id='accessNodeDropdown')
                    self._enter_shared_path_for_multinode()
                    self._add_account_for_shared_path()
                self._wizard.click_next()
                self._admin_console.wait_for_completion()
                # on express config
                if is_express_config:
                    self._wizard.select_card(text='Express configuration (Recommended)')
                    self._wizard.fill_text_in_field(id='globalAdmin', text=global_admin)
                    self._wizard.fill_text_in_field(id='globalAdminPassword', text=password)
                    self._wizard.select_radio_button(id="saveGlobalAdminCredsOption")
                    self._wizard.select_radio_button(id="mfaConfirmation")
                    self._wizard.click_button(name='Create Azure app')
                    self._authorize_permissions(global_admin, password)
                else:
                    self._wizard.select_card(text='Custom configuration (Advanced)')
                    self._wizard.fill_text_in_field(id='addAzureApplicationId', text=application_id)
                    self._wizard.fill_text_in_field(id='addAzureApplicationSecretKey', text=application_key_value)
                    self._wizard.fill_text_in_field(id='addAzureDirectoryId', text=azure_directory_id)
                    cert_upload = self._driver.find_element(By.XPATH, "//input[contains(@accept, 'pfx')]")
                    cert_upload.send_keys(azure_certificate_path)
                    self._wizard.fill_text_in_field(id="certificatePassword", text=azure_certificate_password)
                    self._wizard.select_radio_button(id='permissionsConfirmation')
                    if self.agent_app_type == Office365Apps.AppType.share_point_online:
                        self._wizard.fill_text_in_field(id='addTenantAdminSiteURL', text=site_admin_url)
                self._wizard.click_next()
                self._admin_console.wait_for_completion()
                self._wizard.click_button(id="Submit")
            else:
                self._admin_console.fill_form_by_id('appName', name)
                self._dropdown.select_drop_down_values(values=[server_plan],
                                                       drop_down_id='planSummaryDropdown')

                # Check if infrastructure settings are inherited from plan or not
                if self._admin_console.check_if_entity_exists(
                        'xpath', "//button[contains(@id, 'indexServers')]"):
                    self._dropdown.select_drop_down_values(
                        values=[index_server],
                        drop_down_id='createOffice365App_isteven-multi-select_#2568')
                    if access_node:
                        if isinstance(access_node, list):
                            self._dropdown.select_drop_down_values(
                                values=access_node,
                                drop_down_id='createOffice365App_isteven-multi-select_#5438')
                            self._enter_shared_path_for_multinode()
                            self._add_account_for_shared_path()
                        else:
                            self._dropdown.select_drop_down_values(
                                values=[access_node],
                                drop_down_id='createOffice365App_isteven-multi-select_#5438')
                    elif client_group:
                        self._dropdown.select_drop_down_values(
                            values=[client_group],
                            drop_down_id='createOffice365App_isteven-multi-select_#5438')
                        self._enter_shared_path_for_multinode()
                        self._add_account_for_shared_path()
                if 'Region' in self.tcinputs:
                    self._dropdown.select_drop_down_values(
                        values=[self.tcinputs['Region']],
                        drop_down_id='createOffice365App_isteven-multi-select_#1167')
                if is_express_config:
                    self._admin_console.fill_form_by_id('globalUserName', global_admin)
                    self._admin_console.fill_form_by_id('globalPassword', password)

                    self._admin_console.checkbox_select('SAVE_GA_CREDS')
                    self._admin_console.checkbox_select('MFA_DISABLED')

                    self._click_create_azure_ad_app()

                    attempts = time_out // poll_interval
                    while True:
                        if attempts == 0:
                            raise CVWebAutomationException('App creation exceeded stipulated time.'
                                                           'Test case terminated.')
                        self.log.info("App creation is in progress..")

                        self._admin_console.wait_for_completion()
                        self._check_for_errors()

                        # Check authorize app available

                        if self._admin_console.check_if_entity_exists(
                                "link", self._admin_console.props['action.authorize.app']):
                            break

                        time.sleep(poll_interval)
                        attempts -= 1
                    self._authorize_permissions(global_admin, password)
                else:
                    self._select_custom_config()
                    if self.agent_app_type == Office365Apps.AppType.one_drive_for_business:
                        self._admin_console.fill_form_by_id('applicationId', application_id)
                        self._admin_console.fill_form_by_id('secretAccessKey', application_key_value)
                        self._admin_console.fill_form_by_id('tenantName', azure_directory_id)
                    elif self.agent_app_type == Office365Apps.AppType.share_point_online:
                        # open azure app config panel
                        self._driver.find_element(By.XPATH, "//a[contains(.,'Add details')]").click()
                        self._admin_console.fill_form_by_id('adminSiteURL', site_admin_url)
                        self._add_azure_app_for_custom_config_client_creation(application_id,
                                                                              application_key_value,
                                                                              azure_directory_id)
                        # self._add_service_account_for_custom_config_client_creation(
                        #     sp_service_account_username, sp_service_account_password)
                    if self.agent_app_type == Office365Apps.AppType.exchange_online:
                        self._admin_console.checkbox_select('MFA_DISABLED')
                        self._admin_console.checkbox_select('SVC_ROLES')
                    self._admin_console.checkbox_select('APP_PERMISSIONS')
                self._admin_console.submit_form()
            self._admin_console.wait_for_completion()
            time.sleep(5)  # Wait for Discovery process to launch in proxy server

    @PageService()
    def delete_office365_app(self, app_name):
        """Deletes the office365 app
                Args:
                    app_name (str)  --  Name of the office365 app to delete

        """
        current_tab = self._admin_console.get_current_tab()
        if current_tab == self._admin_console.props['office365dashboard.tabs.overview']:
            self._admin_console.access_tab(self._admin_console.props['office365dashboard.tabs.apps'])
        try:
            self.__rtable.access_action_item(app_name, self._admin_console.props['action.releaseLicense'])
            self._rmodal_dialog.click_submit()
            self._admin_console.wait_for_completion()
        except NoSuchElementException as exp:
            actions = ActionChains(self._driver)
            actions.send_keys(Keys.TAB)
            actions.perform()
        self.__rtable.access_action_item(app_name, self._admin_console.props['action.delete'])
        if self.is_react:
            self._rmodal_dialog.type_text_and_delete(text_val='DELETE',
                                                     checkbox_id="onReviewConfirmCheck")
        else:
            self._rmodal_dialog.type_text_and_delete(text_val='erase and reuse media',
                                                     checkbox_id="onReviewConfirmCheck")
        self._admin_console.wait_for_completion()

    @PageService()
    def click_client_level_restore(self, app_name):
        """Clicks restore of o365 app from office365 apps page
                Args:
                    app_name (str)  --  Name of the office365 app

        """
        if not app_name:
            app_name = self.tcinputs['Name']
        self.__rtable.access_action_item(app_name, 'Restore')

    @PageService()
    def get_browse_table_content(self, columns=None):
        """Returns the browse view table content
                Args:
                    columns (list)  --  list of columns data to be returned

        """
        displayed_columns = self.__rtable.get_visible_column_names()
        if not columns:
            columns = displayed_columns
        else:
            for column in columns:
                if column not in displayed_columns:
                    try:
                        self.__rtable.display_hidden_column(column)
                    except ElementNotInteractableException:
                        # Exception is raised though the element is interactable
                        pass
        browse_column_data = [{} for _ in range(int(self.__rtable.get_total_rows_count()))]
        for column in columns:
            ui_column_value = self.__rtable.get_column_data(column)
            for row in range(len(ui_column_value)):
                browse_column_data[row][column] = ui_column_value[row]
        return browse_column_data

    @PageService()
    def get_browse_tree_view_content(self, active_tree=False):
        """Returns the browse tree view content present on the left side of browse page
            Args:
                    active_tree (bool)  --  returns only active tree view items if true
        """
        return self._get_browse_tree_view_content(active_tree)

    @PageService()
    def click_browse_bread_crumb_item(self, item):
        """Clicks on the specified browse bread crumb item
            Args:
                    item (str)  --  item to be clicked
        """
        self._click_browse_bread_crumb_item(item)
        self._admin_console.wait_for_completion()

    @PageService()
    def click_item_in_browse_table(self, title):
        """Clicks on the specified item in browse table
             Args:
                    title (str)  --  title of the item to be clicked

        """
        self._click_item_in_browse_table(title)
        self._admin_console.wait_for_completion()

    @WebAction()
    def _search_in_browse_page(self, keyword):
        """
            Sets the search input to given keyword
        """
        _search_xpath = "//input[@id='ATSearchInput']"
        search_element = self._driver.find_element(By.XPATH, _search_xpath)
        search_element.clear()
        search_element.send_keys(keyword)
        search_element.send_keys(u'\ue007')
        self._admin_console.wait_for_completion()

    @PageService()
    def search_in_browse_page(self, keyword):
        """
            Searches for given keyword in browse page
        """
        self._search_in_browse_page(keyword)
        self._admin_console.wait_for_completion()

    @PageService()
    def select_rows_in_table(self, names):
        """
            Select rows which contains given names in React Table
            Args:
                names                  (List)       --    entity name whose row has to be selected
        """
        self.__Rtable.select_rows(names, partial_selection=True)

    @WebAction()
    def _click_export(self):
        """
            Click export
        """
        self._driver.find_element(By.ID, "CREATE_EXPORT").click()
        self._admin_console.wait_for_completion()

    @WebAction(delay=2)
    def click_restore_page_action(self,restore_type="BROWSE"):
        """Clicks the restore button on the app page"""
        self._driver.find_element(By.ID, "APP_LEVEL_RESTORE").click()
        self._admin_console.wait_for_completion()
        if self.app_type == constants.ExchangeOnline:
            if restore_type == "MAILBOX":
                self._wizard.select_card(text='Restore mailboxes')
            elif restore_type == "BROWSE":
                self._wizard.select_card(text='Restore messages')
            elif restore_type == "GROUP":
                self._wizard.select_card(text='Restore mailboxes by AD group')
            self._wizard.click_next()

    @PageService()
    def perform_export(self, export_name, select_all=False,export_as=None, file_format=None,filter_value=None):
        """
        Perform export operation on the client
        export_filter_name (str) : Export filter name
        export_type   (str) : Type of Export that needs to be done
                            For Exchange agents only
                            Valid Arguments
                                -- PST  (for PST export)
                                -- CAB  (for CAB export)
        file_format (str)   :   Export file format (EML or MSG)
        filter_vale (dict)  :   filters to apply in browse page
        """
        if filter_value:
            self.apply_restore_filter(filter_value=filter_value)
        if self.app_type == constants.ExchangeOnline:
            self._admin_console.wait_for_completion()
            self.__rtable.select_all_rows()
            self._click_export()
            self._admin_console.wait_for_completion()
            if export_as == "PST":
                export_filename = f"PST_{export_name}_Exchange"
                self._admin_console.select_radio(id="exportTypePST")
            elif export_as == "CAB":
                if not file_format:
                    file_format = "MSG"
                export_filename = f"CAB_{file_format}_{export_name}_Exchange"
                self._admin_console.select_radio(id="exportTypeCAB")
                if file_format == "EML":
                    self._admin_console.select_radio(id="fileExtensionTypeEML")
                else:
                    self._admin_console.select_radio(id="fileExtensionTypeMSG")
            else:
                raise Exception("Please pass the type of export for the mails")
            self._admin_console.fill_form_by_id(element_id="exportName", value=export_filename)
        else:
            self._click_export()
            self._admin_console.fill_form_by_id('exportName', export_name)
            if select_all:
                self._Rmodal_dialog.select_radio_by_id(radio_id="selectionRangeAll")
            self._Rmodal_dialog.expand_accordion(id="ExportAdvancePanel")
            self._admin_console.click_by_id(id="folderHierarchy")
        self._admin_console.submit_form()
        self._admin_console.wait_for_completion()
        job_details=self._job_details()
        self.log.info("Export job details: %s", job_details)
        return job_details

    @PageService()
    def click_view_exports(self):
        """
            Click view exports
        """
        self._click_view_exports()

    @PageService()
    def get_export_size(self, export_name):
        """Read size column value from view exports table
                Args:
                    export_name (str)  --  Name of the export
        """
        self.__rtable.search_for(export_name)
        __export_rtable = Rtable(self._admin_console,
                                 xpath="//div[contains(@class,'k-widget k-grid teer-grid teer-grid-no-grouping')]")
        export_size = (__export_rtable.get_column_data(column_name=self._admin_console.props['column.size']))[-1]
        self.__rtable.clear_search()
        return export_size

    @PageService()
    def download_export(self, export_name):
        """
            Clicks on view exports and downloads specified export file
            Args:
                    export_name (str)  --  Name of the export
        """
        self.__rtable.access_action_item(export_name, self._admin_console.props['action.download'])
        self._rmodal_dialog.click_cancel()

    @PageService()
    def apply_global_search_filter(self, keyword):
        """Applies search filter
          Args:
                keyword (str)       --   keyword to apply search filter
        """
        self._apply_search_filter(keyword)
        self._admin_console.wait_for_completion()

    @PageService()
    def browse_items_for_restore(self, keyword):
        """Searches items by keyword and submits for restore
            Args:
                keyword (str)       --   keyword to apply search filter
        """
        self.apply_global_search_filter(keyword)
        if self.is_react:
            self.__rtable.select_all_rows()
        else:
            self.__table.select_all_rows()
        self._admin_console.click_button_using_id('RESTORE')

    @PageService()
    def apply_global_search_filter_and_get_result(self, keyword, columns=None):
        """Applies search filter and returns browse result
          Args:
                keyword (str)       --   keyword to apply search filter
                columns (list)       --  list of column data to be validated
        """
        self.apply_global_search_filter(keyword)
        browse_response = self.get_browse_table_content(columns)
        return browse_response

    @PageService()
    def get_azure_app_details(self):
        """Get the azure app details from Configuration Tab"""
        self._admin_console.select_configuration_tab()
        if self.is_react:
            details = self.__rtable.get_table_data()
        else:
            details = self.__table.get_table_data()
        return details

    @PageService()
    def get_details_from_discover_cache_info(self):
        """Get the details from Discover cache info component"""
        if self.is_react:
            details = self._rpanel_info.get_details()
            self._rpanel_info.click_button("Close")
            self._admin_console.wait_for_completion()
        else:
            details = self._modal_dialog.get_details()
            self._modal_dialog.click_cancel()
            self._admin_console.wait_for_completion()
        return details

    @PageService()
    def _handle_discovery_alerts(self):
        """Handles the discovery alerts shown while exchange discovery"""
        alert = self._wizard.get_alerts()
        if self.app_type == Office365Apps.AppType.exchange_online:
            attempts = 5
            while alert == "Retrieving the mailbox list for the first time. Please check back in few minutes." or alert == "The mailbox list is getting refreshed. Please check back in few minutes.":
                self.__rtable.reload_data()
                time.sleep(5)
                alert = self._wizard.get_alerts()
                attempts -= 1
                if attempts == 0:
                    self._wizard.click_button("Previous")
                    self._admin_console.wait_for_completion()
                    self._wizard.click_next()
                    self._admin_console.wait_for_completion()
                    alert = self._wizard.get_alerts()
            if "showing mailboxes from cache" in alert.lower():
                self.log.info("Discovery completed")
                return
            elif "mailboxes and groups are being discovered in the background." in alert.lower():
                button_xpath = "//button[@label='Discovery status']"
                self._driver.find_element(By.XPATH, button_xpath).click()
                status = self._get_discovery_status()
                attempts = 5
                while status.lower() != "completed":
                    self.log.info("Discovery is in Progress")
                    time.sleep(10)
                    self._refresh_stats()
                    status = self._get_discovery_status()
                    attempts -= 1
                    if attempts == 0 and status.lower() != "completed":
                        raise CVWebAutomationException("Discovery did not complete")
        elif self.app_type == Office365Apps.AppType.share_point_online:
            if "sites are being discovered in the background." in alert.lower():
                button_xpath = "//button[@label='Discovery status']"
                self._driver.find_element(By.XPATH, button_xpath).click()
                status = self._get_discovery_status()
                attempts = 5
                while status.lower() != "completed":
                    self.log.info("Discovery is in Progress")
                    time.sleep(15)
                    self._refresh_stats()
                    status = self._get_discovery_status()
                    attempts -= 1
                    if attempts == 0 and status.lower() != "completed":
                        progress = self._get_discovery_percentage()
                        status = self._get_discovery_status()
                        if progress == "100%":
                            break
                        elif status.lower() == "in progress":
                            attempts = 5
                            continue
                        else:
                            raise CVWebAutomationException("Discovery did not complete")
                self.log.info("Discovery completed")
        self._admin_console.click_button("Close")
        self._admin_console.wait_for_completion()

    @PageService()
    def wait_while_discovery_in_progress(self, time_out=600, poll_interval=60):
        """Waits for cache to get populated
        Args:
            time_out (int): Time out
            poll_interval (int): Regular interval for check
        """
        attempts = time_out // poll_interval
        if self.is_react:
            if self.app_type in [Office365Apps.AppType.exchange_online, Office365Apps.AppType.share_point_online]:
                self._handle_discovery_alerts()
            else:
                while int(self.__rtable.get_total_rows_count()) == 0:
                    if attempts == 0:
                        raise CVWebAutomationException("Discovery exceeded Stipulated time. Testcase terminated.")
                    self.log.info("Please wait while the discovery is in progress")
                    time.sleep(10)
                    self.__rtable.reload_data()
                    attempts -= 1
        else:
            if self._admin_console.check_if_entity_exists(
                    'link', self._admin_console.props['action.refresh']):
                while attempts != 0:
                    self.log.info('Please wait. Discovery in progress...')
                    time.sleep(poll_interval)
                    if self._admin_console.check_if_entity_exists(
                            'link', self._admin_console.props['action.refresh']):
                        self._admin_console.select_hyperlink(
                            self._admin_console.props['action.refresh'])
                        self._admin_console.wait_for_completion()
                    else:
                        break
                    attempts -= 1
            if attempts == 0:
                raise CVWebAutomationException('Discovery exceeded stipulated time.'
                                               'Test case terminated.')

    @PageService()
    def __get_total_associated_users_count(self):
        """Returns count of total associated users"""
        self._admin_console.access_tab(self.app_type.ACCOUNT_TAB.value)
        if self.is_react:
            return int(self.__rtable.get_total_rows_count())
        else:
            return int(self.__table.get_total_rows_count())

    @PageService()
    def add_user(self, users=None, plan=None, create_plan=False):
        """Adds users to the office 365 app

            Args:
                users (list)    : List of users/sites/mailboxes/teams to be added to the client
                plan (str)     : Name of plan to be selected
                create_plan (bool)   :  True if new plan is to be created
        """
        if plan:
            o365_plan = plan
        else:
            o365_plan = self.tcinputs['Office365Plan']

        if users:
            o365_users = users
        else:
            o365_users = self.users

        if self.is_react:
            self._admin_console.access_tab(self.app_type.CONTENT_TAB.value)
            self.__rtable.access_toolbar_menu('Add')
            self._wizard.select_card("Add content to backup")
            self._wizard.click_next()
            self._wizard.select_card(self.app_type.ADD_USER_CARD_TEXT.value)
            self._wizard.click_next()
            self._admin_console.wait_for_completion()
            self.wait_while_discovery_in_progress()
            self._admin_console.wait_for_completion()
            for user in o365_users:
                self.__rtable.search_for(user)
                if self.agent_app_type == Office365Apps.AppType.share_point_online:
                    self.__rtable.select_rows([o365_users[user]])
                else:
                    self.__rtable.select_rows([user.split("@")[0]])
            self.log.info(f'Users added: {o365_users}')
            self._wizard.click_next()
            self._admin_console.wait_for_completion()
            if create_plan:
                o365_plan = self._create_inline_o365_plan(plan=o365_plan)
            self._wizard.select_drop_down_values(id="cloudAppsPlansDropdown", values=[o365_plan])
            self.log.info(f'Selected Office365 Plan: {o365_plan}')
            self._wizard.click_next()
            self._admin_console.wait_for_completion()
            self._wizard.click_submit()
            self._admin_console.wait_for_completion()
            self._admin_console.refresh_page()
            if self.agent_app_type == Office365Apps.AppType.share_point_online:
                return self.__get_total_associated_users_count()
        else:
            self._open_add_user_panel()
            self._admin_console.wait_for_completion()
            try:
                self._dropdown.select_drop_down_values(
                    values=[o365_plan],
                    drop_down_id=self.app_type.O365_PLAN_DROPDOWN_ID.value)
            except (ElementNotInteractableException, NoSuchElementException):
                self.wait_while_discovery_in_progress()
                self._dropdown.select_drop_down_values(
                    values=[o365_plan],
                    drop_down_id=self.app_type.O365_PLAN_DROPDOWN_ID.value)
            for user in o365_users:
                search_element = self._driver.find_element(By.ID, 'searchInput')
                if search_element.is_displayed():
                    self._admin_console.fill_form_by_id(element_id='searchInput', value=user)
                if self.app_type == Office365Apps.AppType.share_point_online:
                    self.__table.select_rows([o365_users[user]])
                else:
                    self.__table.select_rows([user.split("@")[0]])
            self.log.info(f'Users added: {o365_users}')
            if self.agent_app_type == Office365Apps.AppType.share_point_online:
                self._modal_dialog.click_submit()
                return self.__get_total_associated_users_count()
            else:
                self._admin_console.submit_form()
            self._admin_console.refresh_page()

    @PageService()
    def add_user_group(self, group_name, plan=None):
        """Associate user/sites/teams/mailboxes groups added to the app
            Args:
                group_name (str)    :   name of auto associated group
                plan (str)          :   O365 plan name
        """
        o365_plan = ""
        if plan:
            o365_plan = plan
        else:
            o365_plan = self.tcinputs['Office365Plan']
        self._admin_console.access_tab(self.app_type.CONTENT_TAB.value)
        self.__rtable.access_toolbar_menu('Add')
        self._wizard.select_card("Add content to backup")
        self._wizard.click_next()
        self._wizard.expand_accordion("Advanced")
        self._wizard.select_card(group_name)
        self._wizard.click_next()
        self._admin_console.wait_for_completion()
        self._wizard.click_next()
        self._admin_console.wait_for_completion()
        self._wizard.select_drop_down_values(id="cloudAppsPlansDropdown", values=[o365_plan])
        self.log.info(f'Selected Office365 Plan: {o365_plan}')
        self._wizard.click_next()
        self._admin_console.click_button("Submit")
        self._admin_console.wait_for_completion()
        if self.app_type == Office365Apps.AppType.share_point_online:
            return self.__get_total_associated_users_count()

    @PageService()
    def remove_user_group(self, group_name):
        """Verifies the groups added to the app
            Args:
                group_name (str)    :   name of auto associated group
        """
        self._admin_console.access_tab(self.app_type.CONTENT_TAB.value)
        self.__rtable.hover_click_actions_sub_menu(
            entity_name=group_name,
            action_item="Manage",
            sub_action_item="Remove from content"
        )
        time.sleep(1)
        self._admin_console.click_button(id="Save")
        self._admin_console.wait_for_completion()

    @PageService()
    def add_AD_Group(self, groups=None, plan=None):
        """
            Adds AD Group from the Content Tab

            Arguments:-

                groups (list) -- groups you want to associate

                plan (str) -- plan with which you wanna associate
        """
        self._admin_console.access_tab(self.app_type.CONTENT_TAB.value)
        self._click_add_autodiscover()
        self._wizard.select_card("Add content to backup")
        self._wizard.click_next()
        self._wizard.expand_accordion("Advanced")
        self._wizard.select_card("AD groups")
        self._wizard.click_next()
        if plan:
            office365_plan = plan
        else:
            office365_plan = self.tcinputs["Office365Plan"]
        self.wait_while_discovery_in_progress()
        for group in groups:
            self.__rtable.search_for(group)
            self.__rtable.select_rows([group])
        self._wizard.click_next()
        self._wizard.select_plan(office365_plan)
        self._wizard.select_drop_down_values(id="cloudAppsPlansDropdown", values=[office365_plan])
        self._wizard.click_next()
        self._wizard.click_submit()
        self._admin_console.wait_for_completion()

    @PageService()
    def get_mailbox_tab_table_data(self):
        """Get Office365 Exchange client Mailbox tab table data"""
        return self.__rtable.get_table_data()

    @PageService()
    def verify_plan_association(self, users=None, plan=None, is_group=False):
        """
        Verifies addition of users and check if plan is associated correctly
        Args:
            users (list):   Users to be verified
            plan (string):  Office 365 plan to which user should be associated
            is_group (bool): Should be set to true if verifying plan association for group
        """
        if is_group:
            self._admin_console.access_tab(self.app_type.CONTENT_TAB.value)
            column_name = 'Name'
        else:
            self._admin_console.access_tab(self.app_type.ACCOUNT_TAB.value)
            if self.agent_app_type == Office365Apps.AppType.share_point_online:
                column_name = 'URL'
                if not users:
                    raise CVWebAutomationException(
                        "Please provide sites to verify o365 plan association")
                # users = ['.../' + '/'.join(site.split('/')[3:]) for site in users]
            else:
                column_name = 'Email address'
        if users:
            item_list = users
        elif is_group:
            item_list = self.groups
        else:
            item_list = self.users
        if plan is None:
            plan = self.tcinputs['Office365Plan']
        # ui_association = None
        email_data = list()
        plan_data = list()
        if self.is_react:
            for user in item_list:
                self.__rtable.apply_filter_over_column(column_name, user)
                email_data = email_data + self.__rtable.get_column_data(column_name)
                plan_data = plan_data + self.__rtable.get_column_data('Office 365 plan')
                self.__rtable.clear_column_filter(column_name, user)
        else:
            for user in item_list:
                self.__table.apply_filter_over_column(column_name, user)
                email_data = email_data + self.__table.get_column_data(column_name)
                plan_data = plan_data + self.__table.get_column_data('Office 365 plan')
                self.__table.clear_column_filter(column_name)
        ui_association = dict(zip(email_data, plan_data))
        if self.agent_app_type == Office365Apps.AppType.share_point_online and not is_group:
            item_list = ['.../' + '/'.join(site.split('/')[3:]) for site in item_list]
        association = {user: plan for user in item_list}
        for key, value in association.items():
            if ui_association[key] != value:
                raise CVWebAutomationException(f"Office 365 Plan has not been "
                                               f"associated to each user/group correctly "
                                               f"--> {key} is associated to {ui_association[key]} "
                                               f"when it should be associated to {value}")
        self.log.info("Users/Groups and Office 365 plans have been associated correctly")

    @PageService()
    def verify_group_members(self, members):
        """
        Verifies that all the group members are present in the client
        Args:
            members (list): List of members belonging to the group
        """
        self._admin_console.access_tab(self.app_type.ACCOUNT_TAB.value)
        self.__table.set_pagination(pagination_value=500)
        self._admin_console.wait_for_completion()
        user_list = self.__table.get_column_data(column_name='Email address')
        for member in members:
            if member not in user_list:
                raise CVWebAutomationException('Members of group not added to client')

    @PageService()
    def run_backup(self, update_mail_stats=False):
        """
        Runs backup by selecting all the associated users to the app
        update_mail_stats (bool):- Pass true when not to update backed-up mails
        """
        self._select_all_users()
        self._click_backup()
        self._admin_console.wait_for_completion()
        self._modal_panel.submit() if not self.is_react else self._rmodal_panel.submit()
        job_details = self._job_details()
        self.log.info('job details: %s', job_details)
        if 'No of objects backed up' in job_details and not update_mail_stats:
            self.backedup_mails = int(job_details['No of objects backed up'])
        return job_details

    @PageService()
    def initiate_backup(self, users=None):
        """
        Initiates backup for the given users

        Args:
            users (list):   List of users to be backed up

        Returns:
            job_id (str): Job Id of the initiated backup job

        """
        if not users:
            self._select_all_users()
        else:
            for user in users:
                self._select_user(user)
        self._click_backup()
        self._rmodal_dialog.click_submit()
        job_id = self._get_job_id()
        self._admin_console.refresh_page()
        return job_id

    @PageService()
    def add_global_admin(self, global_admin=None, password=None):
        """Adds global admin in configuration page and verifies it
            Args:
                global_admin (str)   :   value of global admin to be set
                password (str)       :   password for global admin account
        """
        self._admin_console.select_configuration_tab()
        if not global_admin and not password:
            global_admin = self.tcinputs.get('GlobalAdmin', self.tcinputs.get('AddGlobalAdmin', ''))
            if not global_admin:
                raise CVWebAutomationException(
                    "Please provide global admin details to add global admin")
            password = self.tcinputs['Password']
        self._add_global_admin(global_admin, password)
        general_panel = RPanelInfo(self._admin_console,
                                  title=self._admin_console.props['label.generalPane'])
        details = general_panel.get_details()
        if not details['Global Administrator'].startswith(global_admin):
            raise CVWebAutomationException("Global Administrator is not added properly")

    @PageService()
    def edit_global_admin(self, global_admin=None, password=None):
        """Edit global admin in configuration page and verifies it
            Args:
                global_admin (str)   :   new value of global admin to be set
                password (str)       :   password for global admin account
        """
        self._admin_console.select_configuration_tab()
        if not global_admin and not password:
            global_admin = self.tcinputs['EditGlobalAdmin']
            if not global_admin:
                raise CVWebAutomationException(
                    "Please provide global admin details to add global admin")
            password = self.tcinputs['EditGlobalAdminPassword']

        self._edit_global_admin(global_admin, password)
        general_panel = RPanelInfo(self._admin_console,
                                  title=self._admin_console.props['label.generalPane'])
        details = general_panel.get_details()
        if not details['Global Administrator'].startswith(global_admin):
            raise CVWebAutomationException("Global Administrator is not edited properly")

    @PageService()
    def delete_global_admin(self):
        """Deletes global admin in configuration page"""
        self._admin_console.select_configuration_tab()
        general_panel = RPanelInfo(self._admin_console,
                                  title=self._admin_console.props['label.generalPane'])
        details = general_panel.get_details()
        if details['Global Administrator'] == 'Not configured':
            raise CVWebAutomationException("Global Administrator is already deleted")
        self._rpanel_info.click_action_item_for_tile_label(
            self._admin_console.props['label.globalAdministrator'], 'Delete')
        self._admin_console.wait_for_completion()
        self._rmodal_dialog.click_yes_button()
        general_panel = RPanelInfo(self._admin_console,
                                   title=self._admin_console.props['label.generalPane'])
        details = general_panel.get_details()
        if not details['Global Administrator'].startswith("Not configured"):
            raise CVWebAutomationException("Global Administrator is not deleted properly")

    @PageService()
    def enable_modern_auth_toggle(self, add_azure_app=True, express_config=True):
        """Enables modern authentication toggle button and creates azure app if specified
            Args:
                add_azure_app (bool)      :   flag whether to add azure app or not
                express_config (bool)     :   flag whether to choose express or custom config
        """
        self._admin_console.select_configuration_tab()
        general_panel = RPanelInfo(self._admin_console,
                                  title=self._admin_console.props['label.generalPane'])
        details = general_panel.get_details()
        if details['Use modern authentication']:
            raise CVWebAutomationException(
                "Modern authentication toggle on configuration page is already enabled.")
        general_panel.enable_toggle(self._admin_console.props['label.useModernAuthentication'])
        if add_azure_app:
            self.add_azure_app_and_verify(express_config=express_config)
        else:
            self._admin_console.click_button('Close')

    @PageService()
    def disable_modern_auth_toggle(self, add_app_or_account=True, express_config=True):
        """Disables modern auth toggle button and creates azure app/service account if specified
            Args:
                add_app_or_account (bool)      :   flag whether to add azure app/service acc or not
                express_config (bool)          :   flag whether to choose express or custom config
        """
        self._admin_console.select_configuration_tab()
        general_panel = RPanelInfo(self._admin_console,
                                  title=self._admin_console.props['label.generalPane'])
        details = general_panel.get_details()
        if not details['Use modern authentication']:
            raise CVWebAutomationException(
                "Modern authentication toggle on configuration page is already disabled.")
        general_panel.disable_toggle(self._admin_console.props['label.useModernAuthentication'])
        if add_app_or_account:
            if self.agent_app_type == Office365Apps.AppType.share_point_online:
                self._click_add_service_account()
                self._admin_console.wait_for_completion()
                if self._is_global_admin_label_available_for_add_service_account():
                    self._modal_dialog.click_submit()
                    self._admin_console.wait_for_completion()
                else:
                    self.add_service_account(express_config=express_config)
        else:
            self._admin_console.click_button("Close")

    @PageService()
    def add_azure_app_and_verify(self, express_config=True):
        """Adds a new azure app from configuration page and verifies it
            Args:
                express_config (bool)      :   flag whether to choose express or custom config
        """
        if not self.is_react:
            if not self._is_add_azure_app_dialog_open():
                self._admin_console.select_configuration_tab()
                if self.agent_app_type == Office365Apps.AppType.share_point_online:
                    self._admin_console.select_hyperlink(
                        f"{self._admin_console.props['dialog.azureapp.title']}")
                else:
                    self._admin_console.select_hyperlink(
                        f"{self._admin_console.props['dialog.azureapp.title']} ")
                self._admin_console.wait_for_completion()
            if express_config:
                global_admin = self.tcinputs.get('GlobalAdmin', self.tcinputs.get('AddGlobalAdmin', ''))
                if not global_admin:
                    raise CVWebAutomationException(
                        "Please provide global admin details to add azure app")
                global_admin_password = self.tcinputs['Password']
                self._add_azure_app_for_express_config(global_admin, global_admin_password)
                self._verify_app()
            else:
                application_id = self.tcinputs['AddApplicationId']
                application_key_value = self.tcinputs['AddApplicationSecret']
                azure_directory_id = self.tcinputs['AzureDirectoryId']
                self._select_custom_config()
                self._add_azure_app_for_custom_config(application_id,
                                                      application_key_value,
                                                      azure_directory_id)
                self._modal_dialog.click_submit()
                self.newly_created_app_name = application_id
                self._verify_app()
        else:
            self._admin_console.access_tab("Configuration")
            self._click_add_azure_app()
            self._admin_console.wait_for_completion()
            if express_config:
                self._wizard.select_radio_button("Express configuration (Recommended)")
            else:
                self._wizard.select_card("Custom configuration (Advanced)")
            self._wizard.click_next()
            if express_config:
                if self._admin_console.check_if_entity_exists("xpath","//*[@id='globalAdmin']") and self._admin_console.check_if_entity_exists("xpath", "//*[@id='globalAdminPassword']"):
                    self._wizard.fill_text_in_field(id="globalAdmin", text=self.tcinputs.get('GlobalAdmin'))
                    self._wizard.fill_text_in_field(id="globalAdminPassword", text=self.tcinputs.get('Password'))
                    self._wizard.select_checkbox(checkbox_id="saveGlobalAdminCredsOption")
                self._wizard.select_checkbox(checkbox_id="mfaConfirmation")
                self._wizard.click_button(id="analytics-button-create-azure-app")
                self._admin_console.wait_for_completion()
                self._authorize_permissions(self.tcinputs.get('GlobalAdmin'), self.tcinputs.get('Password'))
                if self.agent_app_type == Office365Apps.AppType.share_point_online:
                    self._create_app_principal()
                    self._wizard.click_next()
                    self._admin_console.wait_for_completion()
            else:
                self._wizard.fill_text_in_field(id="addAzureApplicationId", text=self.tcinputs.get('AddApplicationId'))
                self._wizard.fill_text_in_field(id="addAzureApplicationSecretKey", text=self.tcinputs.get('AddApplicationSecret'))
                self._wizard.select_checkbox(checkbox_id="permissionsConfirmation")
                self._wizard.click_next()
                self._admin_console.wait_for_completion()
                if self.agent_app_type == Office365Apps.AppType.share_point_online:
                    self._wizard.select_radio_button(id='appPrincipalConfirmation')
                    self._wizard.click_next()
                    self._admin_console.wait_for_completion()
            self._wizard.click_button(id="Submit")
            self._admin_console.wait_for_completion()
            self._verify_app()

    @PageService()
    def edit_azure_app_and_verify(self, azure_app=None, application_key_value=None):
        """Edits azure app from configuration page and verifies it
            Args:
                azure_app (str)              :   name or id of azure app
                application_key_value (str)  :   key value of azure app
        """
        self._admin_console.select_configuration_tab()
        if not azure_app:
            azure_app = self.tcinputs.get('ApplicationId',
                                          self.tcinputs.get('AddApplicationId', ''))
            if not azure_app:
                raise CVWebAutomationException(
                    "Please provide azure app details to edit it")
            application_key_value = self.tcinputs['EditApplicationSecret']
        self.__rtable.access_action_item(azure_app,
                                         self._admin_console.props['label.globalActions.edit'])
        self._edit_azure_app_for_custom_config(application_key_value)
        self.newly_created_app_name = azure_app
        self._verify_app()

    @PageService()
    def authorize_azure_app_and_verify(self, azure_app=None):
        """Authorizes azure app option in configuration page and verifies it
            Args:
                azure_app (str)          :   name or id of azure app
        """
        self._admin_console.select_configuration_tab()
        if not azure_app:
            azure_app = self.tcinputs.get('ApplicationId',
                                          self.tcinputs.get('AddApplicationId', ''))
            if not azure_app:
                raise CVWebAutomationException(
                    "Please provide azure app details to authorize it")
        self.__rtable.access_action_item(azure_app,
                                        self._admin_console.props['action.authorize.app'])
        global_admin = self.tcinputs.get('GlobalAdmin', self.tcinputs.get('AddGlobalAdmin', ''))
        if not global_admin:
            raise CVWebAutomationException(
                "Please provide global admin details to authorize azure app")
        global_admin_password = self.tcinputs['Password']
        self._rmodal_dialog.click_button_on_dialog('Proceed')
        self._authorize_permissions(global_admin, global_admin_password)
        self._admin_console.wait_for_completion()

    @PageService()
    def create_app_principal_for_sp_app_and_verify(self, azure_app=None):
        """Creates app principal for azure app for SharePoint in configuration page
            Args:
                azure_app (str)          :   name or id of azure app
        """
        self._admin_console.select_configuration_tab()
        if not azure_app:
            azure_app = self.tcinputs.get('ApplicationId',
                                          self.tcinputs.get('AddApplicationId', ''))
            if not azure_app:
                raise CVWebAutomationException(
                    "Please provide azure app details to create app principal")
        self.__rtable.access_action_item(
            azure_app, self._admin_console.props['label.appPrncpl.createAppPrincipal'])
        self._create_app_principal()
        self._admin_console.wait_for_completion()

    @PageService()
    def verify_deleted_app(self):
        """Verifies whether the last deleted app is deleted or
        still present in the list on configuration page"""
        apps_list = self._fetch_all_apps()
        self.log.info('Apps list:%s', apps_list)
        if self.last_deleted_app_name in apps_list:
            raise CVWebAutomationException(
                "Last deleted app was found in the list on "
                "configuration page and not deleted properly")

    @PageService()
    def verify_service_account(self):
        """Verifies whether the newly created service account is present
        in the list on configuration page"""
        service_accounts_list = self._fetch_all_service_accounts()
        self.log.info('Service Accounts list:%s', service_accounts_list)
        if self.newly_created_service_account not in service_accounts_list:
            raise CVWebAutomationException(
                "New service account was not found in the list on configuration page")

    @PageService()
    def verify_deleted_service_account(self):
        """Verifies whether the last deleted service account is deleted
        or still present in the list on configuration page """
        service_accounts_list = self._fetch_all_service_accounts()
        self.log.info('Service Accounts list:%s', service_accounts_list)
        if self.last_deleted_service_account in service_accounts_list:
            raise CVWebAutomationException(
                "Last deleted service account was found in the "
                "list on configuration page and not deleted properly")

    @PageService()
    def delete_azure_app_and_verify(self, azure_app=None, delete_all=False):
        """Deletes azure app from configuration page and verifies whether deleted or not
            Args:
                azure_app (str)            :   name or id of azure app

                delete_all (bool)          :   whether to delete all azure apps
        """
        self._admin_console.select_configuration_tab()
        if not azure_app and not delete_all:
            azure_app = self.tcinputs.get('ApplicationId',
                                          self.tcinputs.get('AddApplicationId', ''))
            if not azure_app:
                raise Exception(
                    "Please provide azure app details to delete it")
        if delete_all:
            azure_apps = (self.get_azure_app_details()
            [self._admin_console.props['label.addAzureApp']])
        else:
            azure_apps = [azure_app]
        for index in range(len(azure_apps)):
            self.__rtable.access_action_item(azure_apps[index],
                                            self._admin_console.props['action.delete'])
            if not azure_app and index == len(azure_apps) - 1:
                if not self._is_warning_message_displayed(
                        self._admin_console.props['warning.oneAppNeededForBackup']):
                    raise CVWebAutomationException(
                        "Warning message should be displayed when last app is to be deleted")
            self._rmodal_dialog.click_submit()
            self.last_deleted_app_name = azure_apps[index]
            self.verify_deleted_app()

    @PageService()
    def verify_azure_apps_connection(self):
        """Verifies connection settings of all azure apps in configuration page"""
        self._admin_console.select_configuration_tab()
        if self.agent_app_type == Office365Apps.AppType.share_point_online:
            self._admin_console.click_button(
                value=f"{self._admin_console.props['action.testConnection']}")
        else:
            self._admin_console.select_hyperlink(f"{self._admin_console.props['label.connection']}")
        self._admin_console.wait_for_completion()

    @PageService()
    def add_service_account(self, express_config=True):
        """Adds a new Service account from configuration page and verifies it
            Args:
                express_config (bool)     :   flag whether to choose express or custom config
        """
        if not self.is_react:
            if not self._is_add_service_account_dialog_open():
                self._admin_console.select_configuration_tab()
                if self.agent_app_type == Office365Apps.AppType.share_point_online:
                    self._admin_console.select_hyperlink(
                        self._admin_console.props['label.addServiceAccount'])
                else:
                    if self.agent_app_type == Office365Apps.AppType.exchange_online:
                        self.verify_modern_authentication()
                        if self.modern_authentication:
                            self.delete_service_account_and_verify(delete_all=True)
                    self._admin_console.select_hyperlink(
                        self._admin_console.props['label.addServiceAccount'] + " ")
                self._admin_console.wait_for_completion()
            if express_config:
                global_admin = self.tcinputs.get('GlobalAdmin', self.tcinputs.get('AddGlobalAdmin', ''))
                if not global_admin:
                    raise CVWebAutomationException(
                        "Please provide global admin details to add service account")
                global_admin_password = self.tcinputs['Password']
                self._add_service_account_for_express_config(global_admin, global_admin_password)
            else:
                service_account_username = self.tcinputs['AddServiceAccountUsername']
                service_account_password = self.tcinputs['AddServiceAccountPassword']
                self._select_custom_config()
                self._add_service_account_for_custom_config(service_account_username,
                                                            service_account_password)
                self._admin_console.wait_for_completion()
                self.newly_created_service_account = service_account_username
                self.verify_service_account()
        else:
            if not self._is_add_service_account_dialog_open():
                self._admin_console.access_tab("Configuration")
                self._click_add_service_account()
                self._admin_console.wait_for_completion()
            if express_config:
                self._wizard.select_radio_button("Express configuration (Recommended)")
                self._wizard.click_next()
                if self._is_global_admin_label_available():
                    self._wizard.fill_text_in_field(id="globalAdmin", text=self.tcinputs.get('GlobalAdmin'))
                    self._wizard.fill_text_in_field(id="globalAdminPassword", text=self.tcinputs.get('Password'))
                    self._wizard.select_checkbox(checkbox_id="saveGlobalAdminCredsOption")
                if self.agent_app_type == Office365Apps.AppType.share_point_online:
                    self._wizard.select_radio_button(id="mfaConfirmation")
                    self._wizard.click_next()
                else:
                    self._wizard.click_button(id="analytics-button-create-service-account")
                self._admin_console.wait_for_completion()
            else:
                self._wizard.select_card("Custom configuration (Advanced)")
                self._wizard.click_next()
                if self.agent_app_type == Office365Apps.AppType.share_point_online:
                    self._wizard.fill_text_in_field(
                        id='svcAccEmailAddress', text=self.tcinputs.get('AddServiceAccountUsername'))
                    self._wizard.fill_text_in_field(
                        id='svcAccPassword', text=self.tcinputs.get('AddServiceAccountPassword'))
                    self._wizard.fill_text_in_field(
                        id='svcAccConfirmPassword', text=self.tcinputs.get('AddServiceAccountPassword'))
                    self._wizard.select_radio_button(id="mfaConfirmation")
                    self._wizard.select_radio_button(id="permissionsConfirmation")
                else:
                    self._wizard.fill_text_in_field(
                        id="serviceAccountUsername", text=self.tcinputs.get('AddServiceAccountUsername'))
                    self._wizard.fill_text_in_field(
                        id="serviceAccountPassword", text=self.tcinputs.get('AddServiceAccountPassword'))
                self._wizard.click_next()
                self._admin_console.wait_for_completion()
                self.newly_created_service_account = self.tcinputs.get('AddServiceAccountUsername')
            if express_config:
                content = self._wizard.get_tile_content()
                service_account = re.search(
                    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content).group(0)
                self.newly_created_service_account = service_account
            self._wizard.click_button(id="Submit")
            self._admin_console.wait_for_completion()
            self.verify_service_account()

    @PageService()
    def edit_service_account(self, service_account=None, password=None):
        """Edits service account from configuration page and verifies it
             Args:
                service_account (str)    :   username of service account to be edited
                password (str)           :   password of service account
        """
        self._admin_console.select_configuration_tab()
        self._rpanel_info.access_tab('Service accounts')
        if not service_account:
            service_account = self.tcinputs.get('SPServiceAccountUsername',
                                                self.tcinputs.get('AddServiceAccountUsername', ''))
            if not service_account:
                raise CVWebAutomationException(
                    "Please provide service account details to edit it")
            password = self.tcinputs['EditServiceAccountPassword']
        self.__rtable.access_action_item(service_account,
                                         self._admin_console.props['label.globalActions.edit'])
        self._edit_service_account_for_custom_config(password)
        self.newly_created_service_account = service_account
        self.verify_service_account()

    @PageService()
    def delete_service_account_and_verify(self, service_account=None, delete_all=False,
                                          check_last_account_warning=False):
        """Deletes service account from configuration page and verifies whether deleted or not
            Args:
                service_account             (str)       :   username of service account to be deleted
                delete_all                  (bool)      :   whether to delete all service accounts
                check_last_account_warning  (bool)      :   whether to check for the warning we get when last service
                                                            account is going to be deleted
        """
        self._admin_console.select_configuration_tab()
        self._rpanel_info.access_tab('Service accounts')
        if not service_account and not delete_all:
            service_account = self.tcinputs.get('SPServiceAccountUsername',
                                                self.tcinputs.get('AddServiceAccountUsername', ''))
            if not service_account:
                raise Exception(
                    "Please provide service account details to delete it")
        if delete_all:
            service_accounts = self._fetch_all_service_accounts()
        else:
            service_accounts = [service_account]
        for index in range(len(service_accounts)):
            self.__rtable.access_action_item(service_accounts[index],
                                             self._admin_console.props['action.delete'])
            if check_last_account_warning and service_account and index == len(service_accounts) - 1:
                if not self._is_warning_message_displayed(
                        self._admin_console.props['warning.oneAccountNeededForBackup']):
                    raise CVWebAutomationException(
                        "Warning message should be displayed when "
                        "last service account is to be deleted")
            self._rmodal_dialog.click_submit()
            self.last_deleted_service_account = service_accounts[index]
            self.verify_deleted_service_account()

    @PageService()
    def disable_activity_control_toggle(self):
        """Disables activity control toggle button to disable backup
        """
        self._admin_console.select_configuration_tab()
        general_panel = RPanelInfo(self._admin_console,
                                  title=self._admin_console.props['heading.clientActivityControl'])
        element = general_panel.get_toggle_element(self._admin_console.props['Data_Backup'])
        if not general_panel.is_toggle_enabled(element):
            raise CVWebAutomationException(
                "Activity Control toggle on configuration page is already disabled.")
        general_panel.disable_toggle(self._admin_console.props['Data_Backup'])
        self._rmodal_dialog.click_submit()

    @PageService()
    def verify_app_config_values(self, infra_pool=False):
        """Verifies the values in Configuration Tab against the input values provided"""
        self._admin_console.select_configuration_tab()
        time.sleep(15)
        if self.is_react:
            general_panel = RPanelInfo(self._admin_console,
                                       title=self._admin_console.props['label.generalPane'])
        else:
            general_panel = PanelInfo(self._admin_console,
                                      title=self._admin_console.props['label.generalPane'])
        details = general_panel.get_details()
        if 'GlobalAdmin' in self.tcinputs:
            global_admin = details['Global Administrator'].split('\n')[0]
            if not global_admin == self.tcinputs['GlobalAdmin']:
                raise CVWebAutomationException(
                    "Global admin value is incorrect on configuration page")
        if not details['Use modern authentication'] in ('Enabled', 'ON', True):
            raise CVWebAutomationException(
                "Modern authentication toggle on configuration page is disabled.")
        if self.is_react:
            infra_panel = RPanelInfo(self._admin_console,
                                     title=self._admin_console.props['label.infrastructurePane'])
        else:
            infra_panel = PanelInfo(self._admin_console,
                                    title=self._admin_console.props['label.infrastructurePane'])
        infra_details = infra_panel.get_details()
        if self.tcinputs['ServerPlan'] not in infra_details['Backup plan']:
            raise CVWebAutomationException("Server plan value is incorrect on configuration page")
        if not infra_pool:
            if 'AccessNode' in self.tcinputs:
                if isinstance(self.tcinputs['AccessNode'], list):
                    access_node_details = infra_details['Access nodes'].split('\n')
                    proxies = [node.strip() for node in access_node_details[0].split(',')]
                    user_account = access_node_details[1]
                    shared_jrd = access_node_details[2]
                    if shared_jrd.find("JobResults") == -1:
                        shared_jrd = shared_jrd + "\\JobResults"
                    if len(proxies) != len(self.tcinputs['AccessNode']):
                        raise CVWebAutomationException("Access node values on configuration page "
                                                       "do not match with entered values")
                    for node in self.tcinputs['AccessNode']:
                        if node not in proxies:
                            raise CVWebAutomationException(
                                "Access node value is incorrect on configuration page")
                    if user_account != self.tcinputs['username']:
                        raise CVWebAutomationException("Account to access shared path is"
                                                       " incorrect on configuration page")
                    if shared_jrd != self.tcinputs["UNCPath"] + "\\JobResults":
                        raise CVWebAutomationException("Shared Job Results Directory is "
                                                       "incorrect on configuration page")
                elif self.tcinputs['AccessNode'] not in infra_details['Access nodes']:
                    raise CVWebAutomationException(
                        "Access node value is incorrect on configuration page")
            elif 'ClientGroup' in self.tcinputs:
                access_node_details = infra_details['Access nodes'].split('\n')
                client_group = access_node_details[0]
                user_account = access_node_details[1]
                shared_jrd = access_node_details[2]
                if client_group != self.tcinputs['ClientGroup']:
                    raise CVWebAutomationException(
                        'Client Group value is incorrect on configuration page')
                if user_account != self.tcinputs['username']:
                    raise CVWebAutomationException(
                        "Account to access shared path is incorrect on configuration page")
                if shared_jrd != self.tcinputs["UNCPath"] + "\\JobResults":
                    raise CVWebAutomationException(
                        "Shared Job Results Directory is incorrect on configuration page")

            if self.tcinputs['IndexServer'] not in infra_details.get(
                    'Index server', infra_details.get('Index Server', '')):
                raise CVWebAutomationException(
                    "Index server value is incorrect on configuration page")
            try:
                if 'MaxStreams' in self.tcinputs:
                    if not infra_details['Max streams'].split('\n')[0] == self.tcinputs['MaxStreams']+' streams':
                        raise CVWebAutomationException(
                            "Max streams value is incorrect on configuration page")
                else:
                    if not infra_details['Max streams'].split('\n')[0] == '10 streams':
                        raise CVWebAutomationException(
                            "Max streams value is incorrect on configuration page")

            except KeyError:
                if (infra_details['Max streams'].split('\n')[0]
                        != self.app_type.MAX_STREAMS_COUNT.value + " streams"):
                    raise CVWebAutomationException(
                        "Max streams value is incorrect on configuration page")
        else:
            if (infra_details['Max streams'].split('\n')[0]
                    != self.tcinputs['InfraPoolInfo']['MaxStreams'] + " streams"):
                raise CVWebAutomationException(
                    "Max streams value is incorrect on configuration page")
            if self.tcinputs['InfraPoolInfo']['IndexServer'] not in infra_details.get(
                    'Index server', infra_details.get('Index Server', '')):
                raise CVWebAutomationException(
                    "Index server value is incorrect on configuration page")
            access_node_details = infra_details['Access nodes'].split('\n')
            client_group = access_node_details[0]
            user_account = access_node_details[1]
            shared_jrd = access_node_details[2]
            if client_group != self.tcinputs['InfraPoolInfo']['ClientGroup']:
                raise CVWebAutomationException(
                    'Client Group value is incorrect on configuration page')
            if user_account != self.tcinputs['InfraPoolInfo']['SharedAccount']:
                raise CVWebAutomationException(
                    "Account to access shared path is incorrect on configuration page")
            if shared_jrd != self.tcinputs['InfraPoolInfo']['SharedDirectory'] + "\\JobResults":
                raise CVWebAutomationException(
                    "Shared Job Results Directory is incorrect on configuration page")
        client_readiness = infra_details['Client readiness']
        if any(status in client_readiness for status in ['Unknown', 'Not available', 'Not Ready']):
            self._click_show_details_for_client_readiness()
            self._admin_console.wait_for_completion()
            client_readiness = self._get_client_readiness_value()
            self._driver.find_element(By.LINK_TEXT, self.tcinputs['Name']).click()
            self._admin_console.wait_for_completion()
        if isinstance(client_readiness, list):
            for value in client_readiness:
                if not value.startswith('Ready'):
                    raise CVWebAutomationException('Client is not ready.')
        else:
            if not client_readiness.startswith('Ready'):
                raise CVWebAutomationException('Client is not ready.')

        if 'GlobalAdmin' in self.tcinputs:
            status = self.get_azure_app_details()['Status']
            for app_status in status:
                if app_status != 'Authorized':
                    raise CVWebAutomationException('Azure App is not authorized')

    @PageService()
    def modify_app_config_values(self,
                                 new_global_admin=None,
                                 new_admin_pwd=None,
                                 new_server_plan=None,
                                 new_stream_count=None,
                                 new_index_server=None,
                                 new_access_node=None,
                                 new_shared_path=None,
                                 new_user_account=None,
                                 new_password=None):
        """
        Modifies the values set in the configuration page to the new values given as arguments
        Args:
            new_global_admin:   New value to be set for global admin
            new_admin_pwd:      Password for new value of global admin
            new_server_plan:    New value to be set for server plan
            new_stream_count:   New vale to be set for 'Max streams'
            new_index_server:   New value to be set for Index Server
            new_access_node:    New value(s) to be set for access node
            new_shared_path:    New value to be set for shared path
            new_user_account:   Local system account to access shared path
            new_password:       Password for local system account
        """
        self._admin_console.select_configuration_tab()
        if new_global_admin:
            self._edit_global_admin(new_global_admin, new_admin_pwd)
        if new_server_plan:
            self._edit_server_plan(new_server_plan)
        if new_stream_count:
            self._edit_stream_count(new_stream_count)
        if new_index_server:
            self._edit_index_server(new_index_server)
        if new_access_node:
            self._edit_access_node(new_shared_path, new_user_account, new_password, new_access_node)
        elif new_shared_path:
            self._edit_access_node(new_shared_path, new_user_account, new_password)

    @PageService()
    def is_app_associated_with_plan(self):
        """
        Verifies if client is associated with plan
        Returns: True if client is listed in the associated entities page of plans
                 else False
        """
        self._admin_console.navigator.navigate_to_plan()
        self._plans.select_plan(self.tcinputs['ServerPlan'])
        self._admin_console.wait_for_completion()
        self._admin_console.access_tab('Associated entities')
        if not self.check_if_app_exists(self.tcinputs['Name']):
            raise CVWebAutomationException('The client has not been associated with Server Plan')

    @WebAction()
    def __click_filter_button(self):
        """
        Click filter button in browse page
        """
        self._driver.find_element(By.XPATH,".//*[@aria-label='Filters']//parent::div//button").click()

    @PageService()
    def apply_restore_filter(self,filter_value=None):
        """
        Apply filter in browse page
            Args:
                filter_value(dict)  :{key1:value1, key2:value2, key3:value3}
        """
        self.__click_filter_button()
        filter_keys = list(filter_value.keys())
        for keys in filter_value:
            if keys=='Contains':
                self._admin_console.fill_form_by_id('ITEM_NAME',filter_value[keys])

            elif keys in ['From','To','Subject','Mailbox']:
                self._admin_console.fill_form_by_id('EX_'+keys.upper(), filter_value[keys])

            elif keys in ['Folder','Received Time','Mail Size','Has Attachment']:
                self._rmodal_dialog.enable_toggle(toggle_element_id="panelToggle")
                if keys=='Folder':
                    self._admin_console.fill_form_by_id('EX_' + keys.upper(), filter_value[keys])
                elif keys=='Received Time':
                    self._rdropdown.select_drop_down_values(
                        values=[filter_value[keys][0]],
                        drop_down_id='modifiedDropDown'
                    )
                    if filter_value[keys][0]=='Date Range':
                        self._calendar.open_calendar(label="From")
                        self._calendar.select_date(date_time_dict=filter_value[keys][1],click_today=False)
                        # self._calendar.set_date()
                        time.sleep(5)
                        self._calendar.open_calendar(label="To")
                        self._calendar.select_date(date_time_dict=filter_value[keys][2],click_today=False)
                        # self._calendar.set_date()
                elif keys=='Mail Size':
                    self._rdropdown.select_drop_down_values(
                        values=[filter_value[keys][0]],
                        drop_down_id='equalityOperatorDropDown'
                    )
                    if filter_value[keys][0] in ['Greater than','Less than']:
                        self._admin_console.fill_form_by_id('sizeValueInput', filter_value[keys][1])
                        self._rdropdown.select_drop_down_values(
                            values=[filter_value[keys][2]],
                            drop_down_id='sizeUnitDropDown'
                        )
                elif keys=='Has Attachment' and filter_value[keys]==True:
                    self._wizard.select_checkbox(checkbox_id="exHasAttachment")
        self._driver.find_element(By.XPATH, ".//button[contains(.,'Search')]").click()

    @PageService()
    def run_restore(self, mailbox=True, user_mailbox=None, in_place=True, unconditional_overwrite=False,filter_value=None,all_matches=True,ad_group_restore=None):
        """Runs the restore by selecting all users associated to the app

                Args:
                    mailbox  (Boolean)  --  Whether to restore mailbox or messages
                    :param unconditional_overwrite:
                    :param user_mailbox:
                    :param in_place:
        """
        if user_mailbox:
            self.access_mailbox(user_mailbox)
            self._click_restore(mailbox)
        elif ad_group_restore:
            self.click_restore_page_action(restore_type="GROUP")
            self._admin_console.wait_for_completion()
            self.wait_while_discovery_in_progress()
            self._admin_console.wait_for_completion()
            for user in ad_group_restore:
                self.__rtable.search_for(user)
                if self.agent_app_type == Office365Apps.AppType.share_point_online:
                    self.__rtable.select_rows([ad_group_restore[user]])
                else:
                    self.__rtable.select_rows([user.split("@")[0]])
            self.log.info(f'Users added: {ad_group_restore}')
            self._wizard.click_next()
            self._admin_console.wait_for_completion()
        else:
            self._select_all_users()
            self._click_restore(mailbox)

        if filter_value:
            self.apply_restore_filter(filter_value=filter_value)
            self.__rtable.select_all_rows()
            self._driver.find_element(By.ID, "RESTORE").click()
            if all_matches:
                self._wizard.select_card(text='Restore all items matching search criteria')
            else:
                self._wizard.select_card(text="Restore the selected items")
            self._wizard.click_next()

        if in_place:
            self._wizard.select_drop_down_values(id="agentDestinationDropdown", values=["Restore the data to its "
                                                                                        "original location"])
        else:
            self._wizard.select_drop_down_values(id="agentDestinationDropdown", values=["Restore the data to another"
                                                                                        "location"])
            # TODO : Select the OOP Restore options for different agents
        self._wizard.click_next()
        if unconditional_overwrite:
            self._wizard.select_radio_button(id="OVERWRITE")
        else:
            self._wizard.select_radio_button(id="SKIP")
        self._wizard.click_next()
        self._wizard.click_submit()
        self._admin_console.wait_for_completion()
        job_id = self._wizard.get_job_id()
        job_details = self._job_details(job_id)
        self.log.info('job details: %s', job_details)
        self.restored_mails = int(job_details['Successful messages'])
        return job_details

    @PageService()
    def verify_backedup_mails(self):
        """Verifies whether backed up mails number is correct"""

        if self.backedup_mails < self.restored_mails:
            raise CVWebAutomationException("Number of mails in the mailbox and "
                                           "number of backed up messages on command "
                                           "center are not matching")

    @PageService()
    def verify_connection(self):
        """Verifies the Azure app connection from configuration tab"""
        self._admin_console.select_configuration_tab()
        self._admin_console.select_hyperlink("Verify connection ")
        self._verify_connection_text()
        self._modal_dialog.click_submit()

    @PageService()
    def verify_added_users(self, users=None):
        """Verifies the users added to the app as against the input file"""
        if self.is_react:
            self._admin_console.access_tab(self.app_type.ACCOUNT_TAB.value)
            if self.agent_app_type == Office365Apps.AppType.one_drive_for_business:
                column_name = 'Email address'
                user_list = self.__rtable.get_column_data(column_name=column_name)
                if users:
                    for user in users:
                        if user not in user_list:
                            raise CVWebAutomationException("User list on the app page does not"
                                                           " match the input file user list")
                    self.log.info(f'Added users verified: {users}')
                else:
                    if collections.Counter(user_list) != collections.Counter(self.users):
                        raise CVWebAutomationException("User list on the app page does "
                                                       "not match the input file user list")
                    self.log.info(f'Added users verified: {self.users}')
        else:
            if self.agent_app_type == Office365Apps.AppType.share_point_online:
                column_name = 'URL'
                if not users:
                    raise CVWebAutomationException("Please provide sites to verify sites association")
                users = ['.../' + '/'.join(site.split('/')[3:]) for site in users]
            else:
                column_name = 'Email address'
            user_list = self.__table.get_column_data(column_name=column_name)
            if users:
                for user in users:
                    if user not in user_list:
                        raise CVWebAutomationException("User list on the app page does not"
                                                       " match the input file user list")
                self.log.info(f'Added users verified: {users}')
            else:
                if collections.Counter(user_list) != collections.Counter(self.users):
                    raise CVWebAutomationException("User list on the app page does "
                                                   "not match the input file user list")
                self.log.info(f'Added users verified: {self.users}')

    @PageService()
    def verify_added_groups(self, groups=None):
        """Verifies the groups added to the app"""
        if self.is_react:
            self._admin_console.access_tab(self.app_type.CONTENT_TAB.value)
            group_list = self.__rtable.get_column_data(column_name='Name')
            if self.agent_app_type == Office365Apps.AppType.one_drive_for_business:
                if not groups:
                    groups = self.groups
                for group in groups:
                    if group not in group_list:
                        raise CVWebAutomationException("Group list on the app page does "
                                                       "not match the input file group list")
                self.log.info(f'Added groups verified: {groups}')

        else:

            self._admin_console.access_tab(self.app_type.CONTENT_TAB.value)
            group_list = self.__table.get_column_data(column_name='Name')
            if groups:
                for group in groups:
                    if group not in group_list:
                        raise CVWebAutomationException("Group list on the app page does "
                                                       "not match the input file group list")
                self.log.info(f'Added groups verified: {groups}')
            else:
                if collections.Counter(group_list) != collections.Counter(self.groups):
                    raise CVWebAutomationException("Group list on the app page does "
                                                   "not match the input file group list")
            self.log.info(f'Added groups verified: {groups}')

    @PageService()
    def change_office365_plan(self, user, plan, is_group=False, inherit_from_content=False):
        """
        Changes the Office 365 Plan for the given user
        Args:
            user (str):         User for which plan has to be changed
            plan (str):         The value of the new plan
            is_group (bool):    Whether plan has to changed for user or group
            inherit_from_content (bool):   If user is autodiscovered then its plan will be inherited with the group
        """
        if self.agent_app_type == Office365Apps.AppType.share_point_online and not is_group:
            user = '.../' + '/'.join(user.split('/')[3:])

        self._select_user(user, is_group=is_group)
        self._click_change_plan_individual(user=user, is_group=is_group)
        self._admin_console.wait_for_completion()

        if self.is_react:
            drop_down_id = self.app_type.O365_PLAN_DROPDOWN_ID_REACT.value
            self._rdropdown.select_drop_down_values(values=[plan], drop_down_id=drop_down_id)
            self._rmodal_dialog.click_submit()
        else:
            if self.agent_app_type == Office365Apps.AppType.share_point_online:
                drop_down_id = self.app_type.O365_PLAN_EDIT_DROPDOWN_ID.value
            else:
                drop_down_id = self.app_type.O365_PLAN_DROPDOWN_ID.value

            if inherit_from_content:
                self._admin_console.checkbox_select("inheritPlan")
            else:
                self._dropdown.select_drop_down_values(values=[plan], drop_down_id=drop_down_id)
            self._modal_dialog.click_submit()
        # self._admin_console.
        # element = self._driver.find_element(By.XPATH, "//button[contains(@type,'submit')]")
        # self._admin_console.mouseover_and_click(element, element)
        self._admin_console.wait_for_completion()
        self._admin_console.refresh_page()
        self.log.info(f'Office 365 Plan changed to value: {plan}')

    @PageService()
    def change_plan(self):
        """Changes the exchange plan for office365 user and verifies it"""

        # Changing plan for all users using more actions link
        self._admin_console.access_tab(self.app_type.ACCOUNT_TAB.value)
        self._admin_console.wait_for_completion()
        self._select_all_users()
        self._click_more_actions()
        self._admin_console.mouseover(
            self._driver.find_element(By.XPATH, "//li[contains(text(), 'Manage')]"))
        self._click_batch_change_plan()
        self._admin_console.wait_for_completion()
        self._add_plan_and_verify(change=True)

        # Changing plan for an individual user
        if self.agent_app_type != Office365Apps.AppType.share_point_online:
            self._click_change_plan_individual()
            self._add_plan_and_verify()

    @PageService()
    def ci_job_exists(self, client_name):
        """
        Checks whether there is an already running CI Job
            client_name:- name of the client
        """
        job_id=None
        self.navigator.navigate_to_jobs()
        self._admin_console.wait_for_completion()
        try:
            job_id = self._jobs.get_job_id_by_operation("Content Indexing", client_name)
            if not job_id:
                raise ValueError("Job ID is None")
        except (ValueError, NoSuchElementException):
            self._admin_console.refresh_page()
            self.navigator.navigate_to_office365()
            self.access_office365_app(client_name)
            self.view_jobs()
            # self._jobs.show_admin_jobs()
            self._admin_console.access_tab("Admin jobs")
            try:
                job_id = self._jobs.get_job_id_by_operation("Content Indexing", client_name)
                if not job_id:
                    raise ValueError("Job ID is None")
            except (ValueError, NoSuchElementException):
                self._admin_console.refresh_page()
        return str(job_id) if job_id else None


    @PageService()
    def run_ci_job(self, client_name):
        """
        Runs the content indexing job and verifies job completes successfully
            client_name:- name of the client
        """
        job_id = self.ci_job_exists(client_name)
        if not job_id:
            self._admin_console.navigator.navigate_to_office365()
            self.access_office365_app(client_name)
            self._select_all_users()
            self._click_more_actions()
            self._click_ci_path()
            self._modal_dialog.click_submit()
        job_details = self._job_details(job_id)
        if job_details[self._admin_console.props['Status']] != "Completed":
            raise CVWebAutomationException("CI job did not completed successfully. Please check logs for more details")
        self.indexed_mails = int(job_details['Number of files transferred'])

    @WebAction(delay=2)
    def _click_ci_path(self):
        """Clicks the content indexing job link"""
        ci_xpath = "//li[@id='CONTENT_INDEXING']"
        self._driver.find_element(By.XPATH, ci_xpath).click()

    @PageService()
    def verify_app_stats(self):
        """Gets the stats from app page

                Raises:
                    Exception if stats do not match that of input file
        """
        self.app_stats_dict['Mails'] = self._get_app_stat(stat_type='Mails')
        self.app_stats_dict['Mailboxes'] = self._get_app_stat(stat_type='Mailboxes')
        self.app_stats_dict['Indexed Mails'] = self._get_app_stat(stat_type='Indexed mails')

        if not self.app_stats_dict['Mails'] or not self.app_stats_dict['Mailboxes'] or not self.app_stats_dict['Indexed Mails']:
            raise CVWebAutomationException(
                'All Mail Stats were not able to get fetched from the page.')

        if not str(len(self.users)) == self.app_stats_dict['Mailboxes']:
            raise CVWebAutomationException(
                'Mailboxes app stat is not matching with input file users')
        if not int(self.app_stats_dict['Mails']) == self.backedup_mails:
            raise CVWebAutomationException(
                'Mails app stat is not matching with backed up files from job details')
        if not int(self.app_stats_dict['Indexed Mails']) == self.indexed_mails:
            raise CVWebAutomationException(
                'Indexed Mails app stat is not matching with Indexed files from job details')

    @PageService()
    def remove_from_content(self):
        """Removes the content from app

                Raises:
                    Exception if user removal is unsuccessful
        """
        # Get the list of existing users
        user_list = self.__rtable.get_column_data(
            column_name=self._admin_console.props['column.email'])
        # Now remove one user from the app

        self._click_remove_content()
        self._rmodal_dialog.click_submit()
        self._admin_console.wait_for_completion()
        # Verify that user was removed
        user_list_new = self.__rtable.get_column_data(
            column_name=self._admin_console.props['column.email'])
        diff_list = list(set(user_list) - set(user_list_new))
        if diff_list and diff_list[0] == self.users[0]:
            self.log.info(f'user {diff_list[0]} was removed from the app')
            self.users.remove(diff_list[0])
        else:
            raise CVWebAutomationException('There was an error in removing user')

    @PageService()
    def exclude_user(self, user=None, is_group=False):
        """
        Excludes the given user from backup

        Args:
            user (str):         User which has to be disabled
            is_group (bool):    Whether user/group is to be disabled

        """
        if self.agent_app_type == Office365Apps.AppType.share_point_online:
            if user:
                user = '.../' + '/'.join(user.split('/')[3:])
                self._select_user(user, is_group=is_group)
        elif self.agent_app_type == Office365Apps.AppType.one_drive_for_business:
            if user:
                self._select_user(user, is_group=is_group)
            else:
                self._select_user(self.users[0], is_group=is_group)
        self._click_exclude_user(user=user)
        self._admin_console.wait_for_completion()
        self._rmodal_dialog.click_submit()
        self._admin_console.wait_for_completion()
        self._admin_console.refresh_page()
        self.log.info(f'User excluded from backup: {user}')

    @PageService()
    def include_in_backup(self, user=None, is_group=False):
        """
        Includes the given user to backup

        Args:
            user (str):         User which has to be enabled
            is_group (bool):    Whether user/group is to be enabled

        """
        if self.agent_app_type == Office365Apps.AppType.share_point_online:
            if user:
                user = '.../' + '/'.join(user.split('/')[3:])
                self._select_user(user, is_group=is_group)
        elif self.agent_app_type == Office365Apps.AppType.one_drive_for_business:
            if user:
                self._select_user(user, is_group=is_group)
            else:
                self._select_user(self.users[0], is_group=is_group)
        self._click_include_user(user=user)
        self._admin_console.wait_for_completion()
        self._rmodal_dialog.click_submit()
        self._admin_console.wait_for_completion()
        self.log.info(f'User included to backup: {user}')

    @PageService()
    def view_jobs(self):
        """Verifies the view jobs page from the app"""
        self._click_view_jobs()

    @PageService()
    def click_backupset_level_restore(self, restore_content=False):
        """Clicks restore from Sites page"""
        self._click_backupset_level_restore(restore_content)

    @PageService()
    def open_active_jobs_tab(self):
        """Opens the active jobs page for the client"""
        self._admin_console.access_tab(self._admin_console.props['label.activeJobs'])

    @PageService()
    def select_content(self, content_type='All mailboxes'):
        """Selects the auto discover content

                Args:
                    content_type (str)  --  Type of auto discovery content
                        Valid Options:
                            All mailboxes
                            All Public Folders
                            All O365 group mailboxes
                        Default:
                            All Users

        """
        content_type_dict = {"All mailboxes": "ALL_USERS",
                             "All public folders": "ALL_PUBLIC_FOLDERS",
                             "All O365 group mailboxes": "ALL_OFFICE365_GROUPS"
                             }

        self._admin_console.access_tab(self._admin_console.props['label.content'])
        self._click_add_autodiscover()
        self._wizard.select_card("Add content to backup")
        self._wizard.click_next()
        self._select_content(content_type=content_type_dict[content_type]) if not self.is_react else \
            self._select_content(content_type)
        self._admin_console.wait_for_completion()
        self._add_plan_and_verify()
        self._wizard.click_submit()
        self._admin_console.wait_for_completion()
        self._admin_console.refresh_page()

    @PageService()
    def deselect_content(self, content_type='All mailboxes'):
        """Disables the auto discover content

                Args:
                    content_type (str)  --  Type of auto discovery content
                        Valid Options:
                            All mailboxes
                            All Public Folders
                            All O365 group mailboxes
                        Default:
                            All Users

        """
        self._admin_console.access_tab(self._admin_console.props['label.content'])
        if not self.is_react:
            self.__table.access_action_item(content_type, self._admin_console.props['label.manage'])
        else:
            self.__rtable.hover_click_actions_sub_menu(entity_name=content_type, action_item=self._admin_console.props[
                'label.manage'], sub_action_item="Remove from content")
        self._modal_dialog.click_submit() if not self.is_react else self._rmodal_dialog.click_submit()
        self._admin_console.wait_for_completion()

    @PageService()
    def verify_content_association(self, content_list):
        """Verifies whether all user association is properly added in command center

                Args:
                    content_list (List)  --  List of users or AD groups

        """
        self._admin_console.access_tab(self._admin_console.props['label.mailboxes'])
        self._admin_console.wait_for_completion()
        users_from_local_db = content_list
        local_db_count = len(users_from_local_db)
        cc_user_count = self.__table.get_total_rows_count() if not self.is_react else \
            self.__rtable.get_total_rows_count()
        if cc_user_count == 0:
            cc_user_count = len(self.__table.get_column_data(
                self._admin_console.props['column.email'])) if not self.is_react else len(self.__rtable.get_column_data(
                self._admin_console.props['column.email']))
        self.log.info("Total rows count: %s" % cc_user_count)
        self.log.info("User from local db count : %s" % local_db_count)
        if not local_db_count == int(cc_user_count):
            self.log.info("Users from local db: %s" % users_from_local_db)
            raise CVWebAutomationException("All User association had mismatch of number of Users")

    @PageService()
    def verify_content_deassociation(self):
        """Verifies whether the content is deassociated"""
        self._admin_console.access_tab(self._admin_console.props['label.mailboxes'])
        self._admin_console.refresh_page()
        try:
            cc_user_count = str(self.__table.get_total_rows_count() if not self.is_react else
                                self.__rtable.get_total_rows_count())
            if cc_user_count != '0':
                raise CVWebAutomationException(
                    "Auto discovery de-association has some issues. Users/groups were not removed.")
        except NoSuchElementException:
            self.log.info(
                "NoSuchElementException caught. "
                "In this case it means content has been deassociated.Positive")

    @PageService()
    def verify_cache_update_time(self, ui_time, db_time):
        """
        Verifies the cache update time from db against time displayed in the UI
        Args:
            ui_time:    Time displayed in UI - format: Nov 3, 3;01 PM
            db_time:    Time stored in discovery cache - format: epoch time
        """
        epoch_time = int(time.mktime(datetime.datetime.strptime(
            ui_time, "%b %d, %I:%M %p").replace(
            year=datetime.datetime.now().year).timetuple()))
        if abs(db_time - epoch_time) > 900:
            raise CVWebAutomationException('Cache is not showing latest update time')
        self.log.info('Latest cache update time verified')

    @PageService()
    def delete_plan(self, plan_name):
        """Deletes the plan"""
        self._plans.delete_plan(plan_name)

    @WebAction(delay=2)
    def _get_user_status(self, user, is_group=False):
        """
        Gets the status of the user

        Args:
            user (str):         User whose status we need to get
            is_group (bool):    Whether user/group

        Returns:
            status (str):       Status of the user
                                Valid values - Active, Disabled, Deleted

        """
        columns = self.__rtable.get_visible_column_names()
        if 'Status' not in columns:
            self.__rtable.display_hidden_column('Status')
        if not is_group:
            if self.agent_app_type == Office365Apps.AppType.share_point_online:
                column_name = 'URL'
            else:
                column_name = 'Email address'
            self._admin_console.access_tab(self.app_type.ACCOUNT_TAB.value)
            self.__rtable.apply_filter_over_column(column_name, user)
            status = self.__rtable.get_table_data().get('Status')[0]
            self.__rtable.clear_column_filter(column_name, user)
        else:
            self._admin_console.access_tab(self.app_type.CONTENT_TAB.value)
            self.__rtable.apply_filter_over_column('Name', user)
            status = self.__rtable.get_table_data().get('Status')[0]
            self.__rtable.clear_column_filter('Name', user)
        return status

    @PageService()
    def verify_user_status(self, status, user, is_group=False):
        """
        Verify the status of the user in the Command Center

        Args:
            status (str):   Status of the user
                            Valid values - Active, Disabled, Deleted
            user:           User whose status has to be checked
            is_group:       Whether user/group

        """
        ui_status = None
        if status == constants.StatusTypes.DELETED.value:
            if is_group:
                self._admin_console.access_tab(self.app_type.CONTENT_TAB.value)
                self.__rtable.apply_filter_over_column('Name', user)
                # The function may sometimes return 'No items to display'
                if self.__rtable.get_total_rows_count() != 0:
                    raise CVWebAutomationException(f'Group {user} has not been deleted')
                ui_status = constants.StatusTypes.DELETED.value
                self.__rtable.clear_column_filter('Name', user)
            else:
                self._admin_console.access_tab(self.app_type.ACCOUNT_TAB.value)
                columns = self.__rtable.get_visible_column_names()
                if 'Status' not in columns:
                    self.__rtable.display_hidden_column('Status')
                self.__rtable.apply_filter_over_column_selection('Status', status)
                ui_status = self._get_user_status(user=user, is_group=is_group)
                self.__rtable.clear_column_filter('Status', status)
        elif status == constants.StatusTypes.REMOVED.value:
            if self.agent_app_type == Office365Apps.AppType.share_point_online:
                if is_group:
                    self._admin_console.access_tab(self.app_type.CONTENT_TAB.value)
                    sites_url_data = self.__rtable.get_column_data('Name')
                else:
                    self._admin_console.access_tab(self.app_type.ACCOUNT_TAB.value)
                    sites_url_data = self.__rtable.get_column_data('URL')
                    user = '.../' + '/'.join(user.split('/')[3:])
                if user not in sites_url_data:
                    ui_status = constants.StatusTypes.REMOVED.value
        else:
            ui_status = self._get_user_status(user=user, is_group=is_group)
        if ui_status != status:
            raise CVWebAutomationException(f'User/Group Status Verification Failed for {user}')
        self.log.info(f'Status of {user} Verified: {status}')

    @PageService()
    def verify_no_users_configured(self, is_group=False):
        """
        Verify that no users are configured

        Args:
            is_group (bool):    Whether to check User/Content Tab

        """
        if is_group:
            self._admin_console.access_tab(self.app_type.CONTENT_TAB.value)
        else:
            self._admin_console.access_tab(self.app_type.ACCOUNT_TAB.value)
        if self.__rtable.get_total_rows_count() != 0:
            raise CVWebAutomationException('Users/Groups are configured for backup')

    @PageService()
    def create_recovery_point(self, mailboxes, client_name):
        """
            Creates a recovery point for the mailboxes supplied corresponding to their job ID

            Arguments:-

            job_id (str) -- Job ID of the backup operation
            mailboxes (list) -- List of the mailboxes supplied

            Returns:-

            List of the recovery point ids created
        """
        recovery_point_jobIDs = list()
        for mailbox in mailboxes:
            self.navigator.navigate_to_office365()
            self.access_office365_app(client_name)
            job_details = self.create_recovery_point_by_mailbox(mailbox)
            recovery_point_jobIDs.append(job_details["Job Id"])
        return recovery_point_jobIDs

    @PageService()
    def restore_recovery_point(self, recovery_point_ids, client_name):
        """
            Restores client from the recovery job ids
            recovery_point_ids (list) -- IDs of the recovery job
            client_name (str) -- client name in which we want to carry restore
        """
        self.log.info("Restoring mails from created recovery points ids %s", recovery_point_ids)
        for recovery_id in recovery_point_ids:
            self.navigator.navigate_to_office365()
            self.access_office365_app(client_name)
            self.restore_from_recovery_point(recovery_id)

    @PageService()
    def verify_discovery_status(self, mailboxes, status):
        """
            Verifies the discovery status for mailbox supplied
        """
        for mailbox in mailboxes:
            self.log.info("Fetching the discovery type of the mailbox %s", mailbox)
            discovery_type = self.get_discovery_status(mailbox)
            if discovery_type.lower() == status.lower():
                self.log.info("Discovery type verified successfully.")
            else:
                raise CVWebAutomationException("Discovery type is not verified. Please check.")

    @PageService()
    def get_browse_count(self, show_deleted=False,mailbox=False,filter_value=None):
        """
                to get total number of items from browse section

                Args:
                    show_deleted (bool): to include deleted items or not in the count
                    mailbox (bool)     : to go to browse page
                    filter_value (dict): to apply filter in browse page

                Returns:
                     result (list): returns total number of items based on show_deleted flag

                     """
        result = []
        self._select_all_users()
        self._click_restore(mailbox)
        if show_deleted:
            if filter_value:
                self.apply_restore_filter(filter_value=filter_value)
            else:
                self.apply_global_search_filter("*")
            count = self.__rtable.get_total_rows_count()
            result.append(int(count))
            self._actions_toolbar.select_action_sublink("Show deleted items")
        else:
            if filter_value:
                self.apply_restore_filter(filter_value=filter_value)
            else:
                self.apply_global_search_filter("*")
        count = self.__rtable.get_total_rows_count()
        result.append(int(count))
        return result

    @WebAction(delay=1)
    def __select_table_checkbox(self, count):
        """
        Method to select values from a table

        Args:
            count (int)  :  Number of items to be chosen in the table, starting from zero
        """
        elements = self._driver.find_elements(By.XPATH, "//input[@class='k-checkbox k-checkbox-md k-rounded-md']")
        if len(elements) - 1 <= count:
            elements[0].click()
        else:
            idx = 2
            while idx <= count:
                elements[idx].click()
                idx += 1

    @PageService()
    def delete_message_in_browse(self,count=None):
        """
        Delete selected message in browse page
        Args:
            count(int): No of message to delete
        """
        if count:
            self.__select_table_checkbox(count)
        self._driver.find_element(By.ID, "DELETE_BACKUP_DATA").click()
        if count:
            self._wizard.select_card(text='Select this option to include only the currently selected items')
        else:
            self._wizard.select_card(text="Select this option to include items from all pages")
        self._admin_console.fill_form_by_id(element_id="notifyPlaceHolder",value="DELETE")
        self._admin_console.click_button_using_id(value="Save")
        self._admin_console.fill_form_by_id(element_id="confirmText", value="DELETE")
        self._admin_console.click_button_using_text(value="Submit")

    @PageService()
    def apply_sort_in_mailbox_table(self,column_name,sort_order=True):
        """
        Column_name (str):  Column name to sort
        sort_order (bool):  Sorting order (Ascending or Descending)
        """
        self.__rtable.apply_sort_over_column(column_name=column_name,ascending=sort_order)

    @WebAction()
    def _click_delete_backup_data(self, entity):
        """
        Clicks the delete backup data button under action context menu
        """
        self.__rtable.hover_click_actions_sub_menu(entity_name=entity,
                                                       action_item="Manage",
                                                       sub_action_item="Delete backup data")

    @PageService()
    def delete_backup_data(self,entity):
        """
        Delete the backup data for given user
        Args:
            entity(str):    which user backup data to delete
        """
        self._click_delete_backup_data(entity=entity)
        self._admin_console.fill_form_by_id(element_id="notifyPlaceHolder", value="DELETE")
        self._admin_console.wait_for_completion()
        if self.is_react:
            self._rmodal_dialog.click_submit()
        else:
            self._modal_dialog.click_submit()
        self._admin_console.fill_form_by_id(element_id="confirmText", value="DELETE")
        self._driver.find_element(By.XPATH, "//div[contains(@class,'confirmDeleteModal')]//button[@id='Save']").click()
        self._admin_console.wait_for_completion()
        self._admin_console.refresh_page()

    @PageService()
    def get_audit_trail_data(self, app_name, user_name,filter_value=None):
        """
        Get Audit trail tabel details
        Args:
            app_name (str)  :   To apply filter based on the client name
            user_name)str)  :   To apply filter based on username
            filter_value(dict)  :   To apply filter in audit trail page
        """
        self._admin_console.access_tab(constants.ExchangeOnline.REPORTS_TAB.value)
        self._admin_console.click_button_using_text(value="Audit trail")
        time.sleep(10)
        self._admin_console.fill_form_by_id(element_id="SearchString", value=app_name)
        self._admin_console.click_button("Apply")
        self.__rtable.apply_filter_over_column(column_name="User", filter_term=user_name, criteria=Rfilter.equals)
        if filter_value:
            self.__rtable.apply_filter_over_column(column_name="Operation",filter_term=filter_value,criteria=Rfilter.equals)

        return self.__rtable.get_table_data()

    def convert_timestamp_to_server_plan_time(self, timestamp):
        """Converts timestamp to server plan time input while taking offset for CS timezone.

            Args:

                    timestamp   (int)   :       Timestamp in seconds

            Returns:

                    str                :       Server plan time input string
        """
        dt = datetime.datetime.fromtimestamp(time.mktime(time.localtime(timestamp)))
        offset_time = self.tcinputs.get('CSTimeOffset', {'hours': 0, 'minutes': 0})
        offset = datetime.timedelta(**offset_time)
        server_time = (dt + offset).strftime('%I %M %p').split()
        result = f'{server_time[0]}:{server_time[1]} {server_time[2].lower()}'
        self.log.info(f'Server time input: {result}')
        return result

class DashboardTile:
    """Class to handle the dashboard-tile component we see during self service"""
    def __init__(self, admin_console):
        """Init function for the class"""
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__base_xpath = "//div[contains(@class,'react-grid-item')]"
        self.__tile_link_xpath = "//th[text()='{}']/ancestor::tr/ancestor::div[@class='tile-content']" \
                                 "/ancestor::div[@class='tile-container']//a[contains(text(),'{}')]"

    @WebAction(delay=0)
    def _click_link_on_tile(self, xpath):
        """
        Click link on tile
        xpath(str) - XPath for the link
        """
        if xpath:
            element = self.__driver.find_element(By.XPATH, xpath)
            element.click()
            self.__admin_console.wait_for_completion()
        else:
            raise Exception("Please provide with Xpath for the element")

    @PageService()
    def click_restore_by_client(self, client_name):
        """
        Click on the details for the client
        client_name(str) -- Client Name for which we need the details
        Returns
        (Dict) -- Client Details
        """
        restore_link_xpath = self.__tile_link_xpath.format(client_name, "Restore")
        self._click_link_on_tile(restore_link_xpath)
