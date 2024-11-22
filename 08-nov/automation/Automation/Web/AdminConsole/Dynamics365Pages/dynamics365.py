import os

from selenium.webdriver.common.by import By

import AutomationUtils.constants
from Application.Dynamics365.d365web_api.d365_rec import Record
from AutomationUtils.machine import Machine
from .constants import D365FilterType
from ..Components.core import RCalendarView
from ..Components.cventities import CVActionsToolbar
from ..Components.page_container import PageContainer
from AutomationUtils.machine import Machine
from ..Components.core import RCalendarView
from ..Components.cventities import CVActionsToolbar
from ..Components.page_container import PageContainer

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright CommVault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from ..Components.wizard import Wizard

"""
This module provides the function or operations that can be used to run
    web automation testcases of Dynamics 365 module.

To begin, create an instance of Dynamics365Apps for test case.

To initialize the instance, pass the testcase object to the Dynamics 365 Apps class.

Call the required definition using the instance object.

This file consists of only one class Dynamics365Apps.
"""

import time
import os
import selenium
import AutomationUtils.constants
from enum import Enum

import selenium.webdriver.support.expected_conditions as EC
from selenium.common.exceptions import (ElementNotInteractableException,
                                        NoSuchElementException,
                                        ElementClickInterceptedException, NoSuchWindowException)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from AutomationUtils.machine import Machine
from AutomationUtils import logger
from Web.Common.page_object import PageService, WebAction
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog
from Web.AdminConsole.Components.panel import DropDown, PanelInfo, RPanelInfo, RDropDown, RModalPanel
from Web.AdminConsole.Components.browse import Browse
from Web.AdminConsole.Components.table import Table, Rtable
from ..Components.core import RCalendarView
from ..Components.cventities import CVActionsToolbar
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Dynamics365Pages import constants


class Dynamics365Apps:
    """Class for all Dynamics 365 Apps page"""

    def __init__(self, tc_object, admin_console, is_react=False):
        """Initializes the Dynamics365Apps class instance

                Args:
                    tc_object       (Object)    --  Testcase object
                    admin_console   (Object)    --  Object denoting the admin console

        """
        self.tcinputs = tc_object.tcinputs
        self._admin_console = admin_console
        self._driver = admin_console.driver
        self.log = logger.get_log()
        self.modern_authentication = False
        self.newly_created_app_name = None
        self._modal_dialog = ModalDialog(self._admin_console)
        self._rmodal_dialog = RModalDialog(self._admin_console)
        self.app_stats_dict = {}
        # Required Components
        self._table = Table(self._admin_console)
        self._rtable = Rtable(self._admin_console)
        self._dropdown = DropDown(self._admin_console)
        self._rdropdown = RDropDown(self._admin_console)
        self._rpanel = RModalPanel(self._admin_console)
        self._wizard = Wizard(self._admin_console)
        self._jobs = Jobs(self._admin_console)
        self._plans = Plans(self._admin_console)
        self._browse = Browse(self._admin_console, is_new_o365_browse=True)
        self._alert = Alert(self._admin_console)
        self.__cvactions_toolbar = CVActionsToolbar(self._admin_console)
        self._page_container = PageContainer(self._admin_console)

        self._job_details = JobDetails(self._admin_console)
        self.__is_react = is_react
        self.client_name = str()
        # Call Localization method
        self._admin_console.load_properties(self)

        self.d365tables = list()
        self.instances = list()
        self.d365_plan: str = self.tcinputs.get('Dynamics365Plan', str())

        # Pass Tables if you need to back up only tables. Pass Tables as a list of 2 sized lists.
        # First element is the table name and second element is the instance name. For eg. [["table1", "instance1"]].
        if "Tables" in self.tcinputs:
            for table, instance in self.tcinputs.get("Tables", []):
                self.d365tables.append((table, instance))

        # Pass D365_Instance if you need to perform instance level backup.
        # Pass Instances as a string of instances separated by comma(,).
        if 'D365_Instance' in self.tcinputs:
            self.d365instances = self.tcinputs.get('D365_Instance').split(",")

        self.d365_online_user = tc_object.tcinputs.get("TokenAdminUser", tc_object.tcinputs.get("GlobalAdmin"))
        self.d365_online_password = tc_object.tcinputs.get("TokenAdminPassword", tc_object.tcinputs.get("Password"))

    @property
    def jobs(self):
        """For accessing job attribute of the class"""
        return self._jobs

    ###############################
    # Client Creation Web Actions #
    ###############################

    @WebAction()
    def _create_app(self):
        """
            Opens the Create a Dynamics 365 App Page
        """
        self._rtable.access_toolbar_menu(menu_id="Add Dynamics 365 app")

    @WebAction(delay=2)
    def _enter_shared_path_for_multinode(self, shared_jrd: str = None):
        """Enters the shared Job Results directory for multiple access nodes"""
        shared_jrd = shared_jrd if shared_jrd else self.tcinputs["UNCPath"]
        if shared_jrd:
            self._wizard.fill_text_in_field(id="uncPathInput", text=shared_jrd)
        else:
            raise CVWebAutomationException("Shared job results can not be None")

    @WebAction(delay=2)
    def _add_account_for_shared_path(self, user_account=None, password=None):
        """Enters the user account and password to access the shared path"""
        self._wizard.click_icon_button_by_title(title="Add")
        if user_account:
            self._driver.find_element(By.ID, 'username').clear()
            self._driver.find_element(By.ID, 'username').send_keys(user_account)

            self._driver.find_element(By.ID, 'password').send_keys(password)
            self._driver.find_element(By.ID, 'confirmPassword').send_keys(password)
        else:
            self._rmodal_dialog.fill_text_in_field(element_id="accountName", text=self.tcinputs["UserAccount"])
            self._rmodal_dialog.fill_text_in_field(element_id="password", text=self.tcinputs["UserAccPwd"])
            self._rmodal_dialog.fill_text_in_field(element_id="confirmPassword", text=self.tcinputs["UserAccPwd"])
        self._rmodal_dialog.click_button_on_dialog(text="Add", preceding_label=False)
        self._admin_console.wait_for_completion()

    @WebAction()
    def _edit_global_admin(self, new_global_admin, new_admin_pwd):
        """
        Modifies the global admin to the new value given as argument
        Args:
            new_global_admin:   New value of global admin to be set
            new_admin_pwd:      Password for global admin account
        """
        self.tcinputs['GlobalAdmin'] = new_global_admin
        self.tcinputs['Password'] = new_admin_pwd

        self._driver.find_element(By.XPATH,
                                  f"//span[text()='{self._admin_console.props['label.globalAdministrator']}'"
                                  f"]//ancestor::li//a[text()='Edit']"
                                  ).click()
        self._admin_console.wait_for_completion()
        self._driver.find_element(By.ID, 'globalAdministrator').clear()
        self._driver.find_element(By.ID, 'globalAdministrator').send_keys(new_global_admin)
        self._driver.find_element(By.ID, 'password').send_keys(new_admin_pwd)
        self._driver.find_element(By.ID, 'confirmPassword').send_keys(new_admin_pwd)
        self._modal_dialog.click_submit()
        self._admin_console.wait_for_completion()

    def _edit_infrastructure_settings(self, server_plan=None, max_streams=None, index_server=None, access_node=None,
                                      shared_jrd=None, username=None, password=None):
        """
        Modifies the infrastructure settings to the new values given as arguments
        Args:
            server_plan:    New value of server plan to be set
            max_streams:    New value of max streams to be set
            index_server:   New value of index server to be set
            access_node:    New value of access node to be set
            shared_jrd:     New value of shared JRD to be set
            username:       New value of username to be set
            password:       New value of password to be set
        """
        edit_button_xpath = "//div[@id='{}']//div[contains(@class, 'edit')]"
        if server_plan:
            self._driver.find_element(By.XPATH, edit_button_xpath.format("serverPlan")).click()
            self._admin_console.wait_for_completion()
            self._rdropdown.select_drop_down_values(values=[server_plan], drop_down_id='plan')
            self._admin_console.wait_for_completion()
            self._rmodal_dialog.click_submit()
            # Confirm dialog box click
            self._rmodal_dialog.click_submit()
            self._admin_console.click_button("Ok")
            self._admin_console.wait_for_completion()
        if max_streams:
            self._driver.find_element(By.XPATH, edit_button_xpath.format("backupStreamCount")).click()
            self._admin_console.wait_for_completion()
            self._driver.find_element(By.ID, 'tile-row-field').clear()
            self._driver.find_element(By.ID, 'tile-row-field').send_keys(max_streams)
            self._admin_console.click_button_using_text("Submit")
            self._admin_console.wait_for_completion()
        if index_server:
            self._driver.find_element(By.XPATH, edit_button_xpath.format("indexServer")).click()
            self._admin_console.wait_for_completion()
            self._rdropdown.select_drop_down_values(values=[index_server], drop_down_id='IndexServersDropdown')
            self._rmodal_dialog.click_submit()
            # Confirm dialog box click
            self._admin_console.click_button("Yes")
            self._admin_console.wait_for_completion()
        if access_node and username and password and shared_jrd:
            self._driver.find_element(By.XPATH, edit_button_xpath.format("accessNodes")).click()
            self._admin_console.wait_for_completion()
            self._rdropdown.select_drop_down_values(values=[access_node], drop_down_id='accessNodeDropdown',
                                                    preserve_selection=True)
            self._rmodal_dialog.fill_text_in_field(element_id="sharedJRD", text=shared_jrd)
            self._rmodal_dialog.fill_text_in_field(element_id="lsaUser", text=username)
            self._rmodal_dialog.fill_text_in_field(element_id="password", text=password)
            self._rmodal_dialog.fill_text_in_field(element_id="confirmPassword", text=password)
            self._rmodal_dialog.click_submit()
            self._admin_console.wait_for_completion()

    @WebAction()
    def _edit_server_plan(self, server_plan):
        """
        Modifies the server plan to the new value given as argument
        Args:
            server_plan: New value of server plan to be set
        """
        self.tcinputs['ServerPlan'] = server_plan
        self._edit_infrastructure_settings(server_plan=server_plan)

    @WebAction(delay=2)
    def _edit_stream_count(self, new_stream_count):
        """
        Modifies the count of max streams to the new value given as argument
        Args:
            new_stream_count:   New value of 'Max streams' to be set
        """
        self.tcinputs['MaxStreams'] = new_stream_count
        self._edit_infrastructure_settings(max_streams=new_stream_count)

    @WebAction(delay=2)
    def _edit_index_server(self, new_index_server):
        """
        Modifies the index server to the new value given as argument
        Args:
            new_index_server:   New value of index server to be set
        """
        self.tcinputs['IndexServer'] = new_index_server
        self._edit_infrastructure_settings(index_server=new_index_server)

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
        self.tcinputs['UserAccount'] = new_user_account
        self.tcinputs['UserAccPwd'] = new_password

        self._edit_infrastructure_settings(shared_jrd=new_shared_path, access_node=new_access_node,
                                           username=new_user_account, password=new_password,)

    @WebAction()
    def _click_prereq_mfa_disabled(self):
        """Select the MFA Disabled on Tenant confirmation prompt"""
        mfa_disabled_id = "MFA_DISABLED"
        self._admin_console.checkbox_select(checkbox_id=mfa_disabled_id)

    @WebAction()
    def _click_prereq_azure_app_auth(self):
        """Select the pre- requisite: The Azure app is authorized from the Azure portal with all the required
        permissions. """
        pre_req_azure_app_cofig_and_auth_id = "APP_PERMISSIONS"
        self._admin_console.checkbox_select(checkbox_id=pre_req_azure_app_cofig_and_auth_id)

    @WebAction()
    def _click_prereq_redirect_uri_configured(self):
        """Select the pre- requisite: The redirect URI of the Azure app is set to
        <AdminConsole-URL>/processAuthToken.do """
        redirect_uri_configured_id = "REDIRECT_URI"
        self._admin_console.checkbox_select(checkbox_id=redirect_uri_configured_id)

    @WebAction()
    def _submit_add_azure_app_form(self):
        """Submit the add azure app form"""
        self._admin_console.submit_form()

    @WebAction()
    def _click_prereq_application_user_configured(self):
        """Click the Application User configured pre- requisite"""
        app_user_configured_label = "applicationUserConfigured"
        self._admin_console.checkbox_select(app_user_configured_label)
        # Renewing it, as for GCC High checking the application user check box is required

    @WebAction()
    def _mark_prerequisites_for_d365(self, cr_type: str, region=1):
        """
            Mark all the pre- requisites for Dynamics 365
            Arguments:
                cr_type        (str)--     Custom or Express Config
                region    (int)--     Default-1 , GCC-2, GCC High-3
                Client creation method type
                Possible Values:
                    "CUSTOM" , "EXPRESS" , "GLOBAL-Express"
        """
        if cr_type == "EXPRESS":
            self._click_prereq_mfa_disabled()

        elif cr_type == "CUSTOM":
            if region != 3:
                self._submit_add_azure_app_form()
                self._click_prereq_redirect_uri_configured()
            else:
                self._click_prereq_application_user_configured()
                self._submit_add_azure_app_form()
            self._click_prereq_azure_app_auth()

        elif cr_type == "GLOBAL-Express":
            if region == 3:
                self._click_prereq_application_user_configured()

    @WebAction()
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
        auth_xpath = f"//a[text() = '{self._admin_console.props['action.authorize.app']}']"
        elem = self._driver.find_element(By.XPATH, auth_xpath)
        self._driver.execute_script("arguments[0].click();", elem)

    @WebAction(delay=3)
    def _switch_to_window(self, window):
        """Switch to specified window

                Args:
                    window (WebElement)  -- Window element to switch to
        """
        self._driver.switch_to.window(window)

    @WebAction(delay=10)
    def _enter_email(self, email):
        """Enter email in email type input

                Args:
                    email (str)  --  Microsoft Global Admin email
        """
        if self._admin_console.check_if_entity_exists('id', 'otherTileText'):
            self._driver.find_element(By.ID, "otherTileText").click()
            self._enter_email(email)
        else:
            self._admin_console.wait_for_element_to_be_clickable('i0116')
            self._admin_console.fill_form_by_id('i0116', email)
            self._click_submit()

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
        try:
            self._admin_console.wait_for_element_based_on_xpath("//input[@id='idSIButton9' and @value='Yes']")
            self._driver.find_element(By.XPATH, "//input[@id='idSIButton9' and @value='Yes']").click()
        except (Exception, NoSuchElementException):
            self.log.info("Stay Signed in button not shown. Progressing ....")

    @WebAction()
    def _click_submit(self):
        """Click submit type button"""
        # This xpath is used to click submit button on Microsoft login pop up window
        ms_submit_xpath = "//input[@type='submit']"
        try:
            self._admin_console.scroll_into_view(ms_submit_xpath)
            if self._admin_console.check_if_entity_exists('xpath', ms_submit_xpath):
                self._driver.find_element(By.XPATH, ms_submit_xpath).click()
        except selenium.common.exceptions.WebDriverException:
            pass
            # Accept permissions is not shown for custom config when app is authorized, and in app user creation
            # for other cases, it might raise an Exception

    @WebAction(delay=5)
    def _check_acquire_token_success(self):
        """Checks acquire token was successful during custom config"""
        _in_progress_xpath = "//div[contains(@class,'MuiGrid-root')]//div[@id='spinner']"
        _success_xpath = "//div[contains(@class,'MuiGrid-root')]//*[name()='svg']//*[name()='g' and @clip-path='url(" \
                         "#Success_svg__a)']"
        _failure_xpath = "//div[contains(@class,'MuiGrid-root')]//*[name()='svg']//*[name()='g' and @clip-path='url(" \
                         "#Failed_svg__a)']"
        count = 0
        token_acquired = False
        fail_message = None
        while count < 3:
            _message_xpath = "/ancestor::span/following-sibling::span"
            if self._admin_console.check_if_entity_exists("xpath", _in_progress_xpath):
                self.log.info("Acquiring token is running ...")
                time.sleep(15)
                count += 1
            elif self._admin_console.check_if_entity_exists("xpath", _failure_xpath):
                element = self._driver.find_element(By.XPATH, _failure_xpath + _message_xpath)
                self.log.info("Step Failed {}".format(element.text))
                raise CVWebAutomationException(element.text)
            elif self._admin_console.check_if_entity_exists("xpath", _success_xpath):
                self.log.info("All steps completed")
                token_acquired = True
                break
        if token_acquired:
            self.log.info("Token acquiring successful")

    @WebAction(delay=2)
    def _get_new_app_name(self):
        """Fetches the newly created Azure app name from MS permission dialog"""

        return self._driver.find_element(By.XPATH, "//div[@class='row app-name']").text

    @WebAction(delay=2)
    def _check_app_creation_success(self):
        """Checks if all the steps for app creation are successfully executed"""
        count: int = 1
        _in_progress_xpath = "//div[contains(@class,'MuiGrid-root')]//div[@id='spinner']"
        _success_xpath = "//div[contains(@class,'MuiGrid-root')]//*[name()='svg']//*[name()='g' and @clip-path='url(" \
                         "#Success_svg__a)']"
        _failure_xpath = "//div[contains(@class,'MuiGrid-root')]//*[name()='svg']//*[name()='g' and @clip-path='url(" \
                         "#Failed_svg__a)']"

        while count < 3:
            if self._admin_console.check_if_entity_exists(entity_name="xpath", entity_value=_in_progress_xpath):
                self.log.info("Corresponding action is in progress...")
                time.sleep(15)
                count = count + 1

            if self._admin_console.check_if_entity_exists(entity_name="xpath", entity_value=_success_xpath):
                self.log.info("Multi tenant App configuration was successful")
                return True

            if count == 3:
                self.log.info("Timeout in configuring the multi tenant App")
                raise CVWebAutomationException("App configuration was unsuccessful")

    @WebAction()
    def _authorize_permissions(self, global_admin: str, password: str, custom_config: bool = False,
                               app_user: bool = False):
        """Clicks authorize now and enables permissions for the app

            Args:
                global_admin (str)  --  Microsoft Global admin email id
                password (str)  --  Global admin password
                custom_config (bool)    --   Client creation type: Custom or Express
                    If Custom: True
                    If Express: False
        """
        if custom_config:
            self._click_acquire_token()
        wait = WebDriverWait(self._driver, 50)
        wait.until(EC.number_of_windows_to_be(2))
        window_handles = self._driver.window_handles
        admin_console_window = window_handles[0]
        azure_window = window_handles[1]
        self._driver.switch_to.window(azure_window)
        self._enter_email(global_admin)
        self._enter_password(password)
        if not app_user:
            self.newly_created_app_name = self._get_new_app_name()
            self._click_submit()
        self._driver.switch_to.window(admin_console_window)
        wait.until(EC.number_of_windows_to_be(1))
        if not app_user:
            if self._check_app_creation_success():
                self.log.info("Azure app is created and authorized successfully")
            else:
                self.log.error("Azure app is not created and there are some errors")
        else:
            if not self.check_application_user_config_success():
                raise CVWebAutomationException("Application User Creation was unsuccessful")
        self._admin_console.click_button_using_text("Close")
        self._admin_console.wait_for_completion()
        if custom_config:
            self._check_acquire_token_success()

    @WebAction(delay=2)
    def _click_acquire_token(self):
        """Clicks the Acquire Token button"""
        if self.__is_react:
            self._admin_console.click_button(value="Acquire token")
        else:
            acquire_token_xp = '//a[@id="tokenStatus"]'
            self._driver.find_element(By.XPATH, acquire_token_xp).click()
        self._admin_console.wait_for_completion()

    @WebAction(delay=1)
    def _open_add_azure_app_panel(self):
        """Open the Add Azure app in client creation panel"""
        add_azure_app_xpath = f"//a[contains(normalize-space()," \
                              f"'{self._admin_console.props['label.option.addAzureAppManually']}')]"
        self._driver.find_element(By.XPATH, add_azure_app_xpath).click()

    @WebAction(delay=5)
    def _close_app_user_info_panel(self):
        """Close the panel with instructions on how to create an Application User"""
        self._admin_console.checkbox_select('CONFIRM_CREATE_APPLICATION_USER')
        self._modal_dialog.click_cancel()

    @WebAction()
    def _click_show_details_for_client_readiness(self):
        """Clicks on show details for client readiness check"""
        self._driver.find_element(By.XPATH,
                                  f"//a[contains(text(), '{self._admin_console.props['label.showDetails']}')]"
                                  ).click()

    @WebAction(delay=5)
    def _get_client_readiness_value(self):
        """Gets the value of Client Readiness check"""
        elements = self._driver.find_elements(By.XPATH,
                                              "//td[@data-ng-bind-html='item.status']")
        readiness = list()
        for row in elements:
            readiness.append(row.text)
        return readiness

    @WebAction()
    def _region_selector_present(self):
        """
            Method to check if the selector for the Dynamics 365 cloud region is displayed
        """
        if self.__is_react:
            _region_selector_id: str = "CloudRegionDropdown"
        else:
            _region_selector_id: str = "createOffice365App_isteven-multi-select_#1167"
        return self._admin_console.check_if_entity_exists(entity_name="id", entity_value=_region_selector_id)

    @WebAction()
    def _select_storage_region(self, region="East US 2"):
        """Selects the storage region for metallic client creation"""
        self._wizard.select_drop_down_values(id="storageRegion", values=[region])
        self._wizard.click_next()

    @WebAction()
    def _fill_app_name(self, app_name):
        """Fills the app name in the client creation page"""
        if app_name:
            self._wizard.fill_text_in_field(id="appNameField", text=app_name)
        else:
            raise CVWebAutomationException("App Name can not be None")

    @WebAction()
    def _select_cloud_region(self, region):
        """Select the cloud region while Dynamics 365 App Creation"""
        if region == 1:
            _region = self.tcinputs.get('Region', constants.CLOUD_REGIONS.DEFAULT.value)
        elif region == 2:
            _region = self.tcinputs.get('Region', constants.CLOUD_REGIONS.GCC.value)
        else:
            _region = self.tcinputs.get('Region', constants.CLOUD_REGIONS.GCC_HIGH.value)
        self._wizard.select_drop_down_values(id="CloudRegionDropdown", values=[_region])
        if not self._admin_console.check_if_entity_exists(By.XPATH, "//button[@aria-label='Create']"):
            self._wizard.click_next()

    @WebAction()
    def _select_server_plan(self, server_plan):
        """Select the server plan during D365 Client creation"""
        if server_plan:
            self._wizard.fill_text_in_field(id="searchPlanName", text=server_plan)
            self._wizard.select_plan(plan_name=server_plan)
            self._wizard.click_next()
        else:
            raise CVWebAutomationException("Server Plan can not be None")

    @WebAction()
    def _select_infrastructure_details(self, index_server, access_nodes, client_group=None):
        """selects the infrastructure details during client creation"""
        if index_server:
            self._wizard.select_drop_down_values(id="IndexServersDropdown", values=[index_server])
        else:
            raise CVWebAutomationException("Index server can not be None")
        if access_nodes:
            if isinstance(access_nodes, list):
                self._wizard.select_drop_down_values(id="accessNodeDropdown", values=access_nodes)
                self._enter_shared_path_for_multinode()
                self._add_account_for_shared_path()
            else:
                self._wizard.select_drop_down_values(id="accessNodeDropdown", values=[access_nodes])
        elif client_group:
            self._wizard.select_drop_down_values(id="accessNodeDropdown", values=access_nodes)
            self._enter_shared_path_for_multinode()
            self._add_account_for_shared_path()
        else:
            raise CVWebAutomationException("Client Group and Access Node both can not be None")
        self._wizard.click_next()

    @WebAction()
    def _add_app_using_express_configuration(self, global_admin_username, global_admin_password):
        """Adds an express configuration app in during client creation"""
        self._wizard.fill_text_in_field(id="globalAdmin", text=global_admin_username)
        self._wizard.fill_text_in_field(id="globalAdminPassword", text=global_admin_password)
        self._admin_console.checkbox_select(checkbox_id="saveGlobalAdminCredsOption")
        self._admin_console.checkbox_select(checkbox_id="mfaConfirmation")
        self._wizard.click_button(name="Create Azure app")
        self._admin_console.wait_for_completion()

    @WebAction()
    def _add_app_using_custom_configuration(self, application_id, app_secret_key, azure_directory_id):
        """Adds a custom configured app in the console while client creation"""
        self._wizard.select_card(text="Custom configuration (Advanced)")
        self._wizard.fill_text_in_field(id="addAzureApplicationId", text=application_id)
        self._wizard.fill_text_in_field(id="addAzureApplicationSecretKey", text=app_secret_key)
        self._wizard.fill_text_in_field(id="addAzureDirectoryId", text=azure_directory_id)
        self._admin_console.checkbox_select(checkbox_id="permissionsConfirmation")
        self._admin_console.checkbox_select(checkbox_id="redirectUriSetConfirmation")

    @WebAction()
    def _check_if_azure_app_created(self, time_out, poll_interval):
        """Check if azure app is created using express configuration"""
        attempts = time_out // poll_interval
        while True:
            if attempts == 0:
                raise CVWebAutomationException('App creation exceeded stipulated time.'
                                               'Test case terminated.')
            self.log.info("App creation is in progress..")

            self._admin_console.wait_for_completion()
            self._check_for_errors()

            # Check authorize app available
            if len(self._driver.window_handles) > 1:
                break

            if self._admin_console.check_if_entity_exists("link",
                                                          self._admin_console.props['action.authorize.app']):
                break

            time.sleep(poll_interval)
            attempts -= 1

    ############################################
    #   Multi Tenant Azure app Web Actions     #
    ############################################

    @WebAction()
    def is_multi_tenant_enabled(self):
        """
            Method to check if the multi tenant configuration is enabled on the CS/ Command Center

            Returns:
                multi_tenant_enabled        (bool)--    Whether multi tenant configuration is enabled on the CS
        """
        _sign_in_msft_button_xpath = "//div[@id = 'id-o365-sign-in-with-msft-onboarding']//*[name() = 'svg']"
        return self._admin_console.check_if_entity_exists(entity_name="xpath", entity_value=_sign_in_msft_button_xpath)

    @WebAction()
    def _click_sign_in_with_msft_button(self):
        """
            Method to select on the Sign in with Microsoft button
        """
        _sign_in_msft_button_xpath = "//div[@id = 'id-o365-sign-in-with-msft-onboarding']//*[name() = 'svg']"
        self._driver.find_element(By.XPATH, _sign_in_msft_button_xpath).click()

    @WebAction(delay=2)
    def _check_multi_tenant_form_displayed(self):
        """
            Method to check if the multi tenant form/ modal is visible

            Returns:
                form_displayed          (bool)--    Multi Tenant app configuration form displayed or now
        """
        _multi_tenant_form_xpath = "//div[@aria-labelledby = 'customized-dialog-title' ]"
        return self._driver.find_element(By.XPATH, _multi_tenant_form_xpath).is_displayed()

    @WebAction()
    def _fetch_and_parse_multi_tenant_dialog_details(self):
        """
            Method to fetch and parse the test details from the multi tenant app config modal dialog

            Returns:
                _dialog_details         (list)--        List element for the test fetched from the multi tenant dialog
        """
        _dialog_details = self._driver.find_element(By.XPATH,
                                                    "//div[contains(@class,'MuiGrid-container') and @justify='center']").text.split(
            "\n")

        return _dialog_details

    @WebAction()
    def _wait_app_authorization_redirect(self):
        """
            Method to wait for the command center to redirect to the MSFT login page for
            Azure app Authorization
        """
        count = 1
        while count < 3:
            if len(self._driver.window_handles) > 1:
                return True
            else:
                self._driver.find_element(By.LINK_TEXT, 'here').click()

        if count == 3:
            raise CVWebAutomationException("Unable to open the MSFT login page for Azure app authorization")

    @WebAction()
    def _get_message_text(self):
        """
            Gets the message text from the dialog
        """
        _message_text_box_xpath = "//div[@aria-labelledby='customized-dialog-title']//div[contains(@class, " \
                                  "'MuiAlert-message')]"
        element = self._driver.find_element(By.XPATH, _message_text_box_xpath)
        return element.text

    @WebAction(delay=3)
    def _check_error_multi_tenant_config(self):
        """
            Method to check if there was any error in configuring the multi tenant app
        """
        if self.__is_react:
            _failure_xpath = "//button[@aria-label='Retry']/div[text()='Retry']"
        else:
            _failure_xpath = "//button[@aria-label='Close']/div[text()='Close']"
        if self._admin_console.check_if_entity_exists(entity_name="xpath", entity_value=_failure_xpath):
            _error_message = self._get_message_text()
            self.log.info("Op Failed with the error: {}".format(_error_message))
            raise CVWebAutomationException("Unable to configure the multi tenant Azure app")

    @WebAction(delay=3)
    def check_multi_tenant_config_success(self):
        """
            Method to check if the configuration for the multi tenant app was successful
        """
        count: int = 1
        _in_progress_xpath = "//div[contains(@class,'MuiGrid-root')]//div[@id='spinner']"
        _success_xpath = "//div[contains(@class,'MuiGrid-root')]//*[name()='svg']//*[name()='g' and @clip-path='url(" \
                         "#Success_svg__a)']"
        _failure_xpath = "//div[contains(@class,'MuiGrid-root')]//*[name()='svg']//*[name()='g' and @clip-path='url(" \
                         "#Failed_svg__a)']"

        while count < 3:
            _app_details_status = self._fetch_and_parse_multi_tenant_dialog_details()
            if self._admin_console.check_if_entity_exists(entity_name="xpath", entity_value=_in_progress_xpath):
                self.log.info("Corresponding action is in progress...")
                time.sleep(15)
                count = count + 1

            if self._admin_console.check_if_entity_exists(entity_name="xpath", entity_value=_success_xpath):
                self.log.info("Multi tenant App configuration was successful")
                return True

            if count == 3:
                self.log.info("Timeout in configuring the multi tenant App")
                raise CVWebAutomationException("App configuration was unsuccessful")

            if self._admin_console.check_if_entity_exists(entity_name="xpath", entity_value=_failure_xpath):
                _error_message = self._get_message_text()
                self.log.info("Op Failed with the error: {}".format(_error_message))
                raise CVWebAutomationException("Unable to configure the multi tenant Azure app")

    @WebAction(delay=3)
    def _authorize_multi_tenant_app(self, global_admin_address: str, global_admin_passwd: str):
        """
            Method to Authorize the Multi Tenant Azure App

            Arguments:
                global_admin_passwd         (str)--     Password for the Azure global admin account
                global_admin_address        (str)--     Email address for the Azure global admin account
        """
        self.log.info("Starting Multi tenant Azure app Authorization...")
        self._wait_app_authorization_redirect()
        self._authorize_permissions(global_admin=global_admin_address,
                                    password=global_admin_passwd,
                                    custom_config=False)

        self._admin_console.wait_for_completion()
        self._check_error_multi_tenant_config()
        self.log.info("Multi tenant Azure app Authorized...")

    @WebAction()
    def _configure_with_multi_tenant_app(self, global_admin_address: str, global_admin_passwd: str):
        """
            Method to configure the Multi Tenant Azure app with the Dynamics 365 client
        """
        self._click_sign_in_with_msft_button()
        self._admin_console.wait_for_completion()

        if not self._check_multi_tenant_form_displayed():
            raise CVWebAutomationException("Azure Multi Tenant Authentication Model was not loaded")

        self._admin_console.wait_for_completion()
        # two condition now: failure in fetching app details or success in fetching app details.
        self._check_error_multi_tenant_config()
        #   check if error in fetching/ loading Azure app details

        self._authorize_multi_tenant_app(global_admin_address=global_admin_address,
                                         global_admin_passwd=global_admin_passwd)
        self._admin_console.wait_for_completion()
        #   for: fetching environment details

        if not self.check_multi_tenant_config_success():
            #   will handle any error in fetching environment details
            raise CVWebAutomationException("Multi tenant Azure app configuration was unsuccessful")

        self._driver.find_element(By.XPATH, "//button[@aria-label='Close']").click()
        #   To select the close/ save button, click cancel func is working

    ############################################
    #   Client config modification Web Actions #
    ############################################
    @WebAction()
    def _get_app_name(self):
        """Gets the app name from the app page. Useful for Metallic app"""
        if self.__is_react:
            return self._driver.find_element(By.XPATH, "//span[@class='title-display']").text

    @WebAction()
    def _edit_global_admin(self, new_global_admin: str, new_admin_pwd: str):
        """
        Modifies the global admin to the new value given as argument
        Args:
            new_global_admin:   New value of global admin to be set
            new_admin_pwd:      Password for global admin account
        """
        self.tcinputs['GlobalAdmin'] = new_global_admin
        self.tcinputs['Password'] = new_admin_pwd

        self._driver.find_element(By.XPATH,
                                  f"//span[text()='{self._admin_console.props['label.globalAdministrator']}'"
                                  f"]//ancestor::li//a[text()='Edit']"
                                  ).click()
        self._admin_console.wait_for_completion()
        self._driver.find_element(By.ID, 'globalAdministrator').clear()
        self._driver.find_element(By.ID, 'globalAdministrator').send_keys(new_global_admin)

        self._driver.find_element(By.ID, 'password').send_keys(new_admin_pwd)
        self._driver.find_element(By.ID, 'confirmPassword').send_keys(new_admin_pwd)
        self._modal_dialog.click_submit()
        self._admin_console.wait_for_completion()

    #########################################
    #   Content Modification Web Actions    #
    #########################################

    @WebAction()
    def _open_add_table_panel(self):
        """Opens the panel to add Tables to the client"""
        try:
            self._admin_console.access_tab(constants.Dynamics365.TABLE_TAB.value)
            _add_button_id = 'ID_USER'
            self._driver.find_element(By.ID, _add_button_id).click()
            time.sleep(2)
            _add_table_id = 'ADD_USER'
            add_table_element = self._driver.find_element(By.ID, _add_table_id)
            time.sleep(2)
            add_table_element.click()
        except (ElementClickInterceptedException, NoSuchElementException):
            raise CVWebAutomationException("Unable to open Add Table Panel")

    @WebAction()
    def check_for_discovery_errors(self):
        """Check if any error in discovery"""
        error_xpaths = [
            "//div[@ng-bind='addOffice365.appCreationErrorResponse']"
        ]

        for xpath in error_xpaths:
            if self._admin_console.check_if_entity_exists('xpath', xpath):
                if self._driver.find_element(By.XPATH, xpath).text:
                    raise CVWebAutomationException(
                        'Error while creating the app: %s' %
                        self._driver.find_element(By.XPATH, xpath).text
                    )
        pass

    @WebAction(delay=3)
    def check_application_user_config_success(self):
        """
            Method to check if the configuration for the application user was successful
        """
        count: int = 1
        _in_progress_xpath = "//div[contains(@class,'MuiGrid-root')]//div[@id='spinner']"
        _success_xpath = ("//div[contains(@class,'MuiGrid-root')]//span[contains(@class,'check-circle') "
                          "and @color='green']")
        _failure_xpath = "//div[contains(@class,'MuiGrid-root')]//*[name()='svg']//*[name()='g' and @clip-path='url(" \
                         "#Failed_svg__a)']"

        while count < 3:
            if self._admin_console.check_if_entity_exists(entity_name="xpath", entity_value=_in_progress_xpath):
                self.log.info("Corresponding action is in progress...")
                time.sleep(30)
                count = count + 1

            elif self._admin_console.check_if_entity_exists(entity_name="xpath", entity_value=_success_xpath):
                self.log.info("Application User creation was successful")
                return True

            elif self._admin_console.check_if_entity_exists(entity_name="xpath", entity_value=_failure_xpath):
                _error_message = self._alert.check_error_message()
                self.log.info("Op Failed with the error: {}".format(_error_message))
                raise CVWebAutomationException(
                    "Unable to configure the Application User for Azure app/ Dynamics 365 Environment")

            if count == 3:
                self.log.info("Timeout in configuring the application user")
                raise CVWebAutomationException("Application User configuration was unsuccessful")



    @WebAction()
    def _click_add_instance(self, all_instances: bool = False):
        """Clicks on Add Instance button of Dynamics 365 Client"""
        self._admin_console.access_tab(self._admin_console.props['label.content'])
        self._driver.find_element(By.XPATH, "//a[@id='ADD']").click()
        try:
            if all_instances:
                self._driver.find_element(By.XPATH, "//a[@id='ADD_ALL_GROUP]").click()
            else:
                self._driver.find_element(By.XPATH, "//a[@id='ADD_GROUP']").click()
        except ElementClickInterceptedException:
            if all_instances:
                self._driver.find_element(By.XPATH,
                                          f"//span[text()='{self._admin_console.props['subtext.add.allInstances']}']"
                                          ).click()
            else:
                self._driver.find_element(By.XPATH,
                                          f"//span[text()='{self._admin_console.props['subtext.add.instances']}']"
                                          ).click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def _click_delete_content(self, content_name: str = None, is_instance: bool = False, instance_name: str = str()):
        """Clicks the exclude content button under action context menu"""
        if not self.__is_react:
            if not is_instance:
                manage_id = 'contentTable_actionContextMenu_MANAGE'
                disable_id = 'contentTable_actionContextMenu_REMOVE'
                self._table.apply_filter_over_column(column_name=constants.Dynamics365.ASSOC_PARENT_COL.value,
                                                     filter_term=instance_name)
                self._table.set_pagination(pagination_value=500)
            else:
                manage_id = 'contentTable_actionContextMenu_MANAGE'
                disable_id = 'contentTable_actionContextMenu_REMOVE'

            self._table.hover_click_actions_sub_menu(entity_name=content_name,
                                                     mouse_move_over_id=manage_id,
                                                     mouse_click_id=disable_id)
        else:
            if not is_instance:
                self._admin_console.access_tab(constants.Dynamics365.TABLE_TAB.value)
                self._rtable.apply_filter_over_column(column_name="Environment", filter_term=instance_name)
                self._rtable.apply_filter_over_column(column_name="Name", filter_term=content_name)
                self._rtable.hover_click_actions_sub_menu(entity_name=content_name,
                                                          action_item="Manage",
                                                          sub_action_item="Remove from content")
            else:
                self._admin_console.access_tab(constants.Dynamics365.CONTENT_TAB.value)
                self._rtable.apply_filter_over_column(column_name="Name", filter_term=content_name)
                self._rtable.hover_click_actions_sub_menu(entity_name=content_name,
                                                          action_item="Manage",
                                                          sub_action_item="Remove from content")

    @WebAction(delay=2)
    def _select_content(self, content_name: str, is_instance: bool = False, instance_name: str = str()):
        """
        Selects the content specified
        Args:
            content_name (str):    Item to be selected
            is_instance (bool):    Whether or not the item is an Instance

        """
        if not self.__is_react:
            if not is_instance:
                self._admin_console.access_tab(constants.Dynamics365.TABLE_TAB.value)
                self._table.set_pagination(pagination_value=500)
                self._table.apply_filter_over_column(column_name=constants.Dynamics365.ASSOC_PARENT_COL.value,
                                                     filter_term=instance_name)
                xp = f"//*[@id='cv-k-grid-td-DISPLAY_NAME']/a[normalize-space()='{content_name}']/ancestor::tr/td[" \
                     f"contains(@id,'checkbox')] "
            else:
                self._admin_console.access_tab(constants.Dynamics365.CONTENT_TAB.value)
                xp = f"//*[@id='cv-k-grid-td-DISPLAY_NAME']/span[normalize-space()='{content_name}']/ancestor::tr/td[" \
                     f"contains(@id,'checkbox')] "
            if not is_instance:
                self._table.clear_column_filter(column_name=constants.Dynamics365.ASSOC_PARENT_COL.value)
            self._driver.find_element(By.XPATH, xp).click()
        else:
            if not is_instance:
                self._admin_console.access_tab(constants.Dynamics365.TABLE_TAB.value)
                self._rtable.apply_filter_over_column(column_name="Name", filter_term=content_name)
                self._rtable.select_rows(names=[content_name])
                self._rtable.clear_column_filter(column_name="Name", filter_term=content_name)

            else:
                self._rtable.apply_filter_over_column(column_name="Environment", filter_term=instance_name)
                self._rtable.select_rows(names=[instance_name])
                self._rtable.clear_column_filter(column_name="Environment", filter_term=instance_name)

    @WebAction(delay=2)
    def _get_table_index_in_page(self, table_name: str, ):
        """

        Args:
            table_name      (str):  Name of the tables
        Returns:

        """
        tables = self._rtable.get_column_data(column_name="Name")
        index = -1
        for i in range(len(tables)):
            if table_name == tables[i]:
                index = i
                break
        return index

    @WebAction()
    def _click_exclude_content(self, content_name: str = None, is_instance: bool = False, instance_name: str = str()):
        """Clicks the exclude content button under action context menu"""
        if not self.__is_react:
            if not is_instance:
                manage_id = 'contentTable_actionContextMenu_MANAGE'
                disable_id = 'contentTable_actionContextMenu_DISABLE'
                self._table.apply_filter_over_column(column_name=constants.Dynamics365.ASSOC_PARENT_COL.value,
                                                     filter_term=instance_name)
                self._table.set_pagination(pagination_value=500)

            else:
                manage_id = 'contentTable_actionContextMenu_MANAGE'
                disable_id = 'contentTable_actionContextMenu_DISABLE'

            self._table.hover_click_actions_sub_menu(entity_name=content_name,
                                                     mouse_move_over_id=manage_id,
                                                     mouse_click_id=disable_id)
        else:
            if not is_instance:
                self._admin_console.access_tab(constants.Dynamics365.TABLE_TAB.value)
                self._rtable.apply_filter_over_column(column_name="Environment", filter_term=instance_name)
                self._rtable.apply_filter_over_column(column_name="Name", filter_term=content_name)
                self._rtable.hover_click_actions_sub_menu(entity_name=content_name,
                                                          action_item="Manage",
                                                          sub_action_item="Exclude from backup")
            else:
                self._admin_console.access_tab(constants.Dynamics365.CONTENT_TAB.value)
                self._rtable.apply_filter_over_column(column_name="Name", filter_term=content_name)
                self._rtable.hover_click_actions_sub_menu(entity_name=content_name,
                                                          action_item="Manage",
                                                          sub_action_item="Exclude from backup")

    @WebAction(delay=3)
    def _click_include_content(self, content_name: str = None, is_instance: bool = False, instance_name: str = str()):
        """Clicks the exclude content button under action context menu"""
        if not self.__is_react:
            if not is_instance:
                manage_id = 'contentTable_actionContextMenu_MANAGE'
                enable_id = 'contentTable_actionContextMenu_ENABLE'
                self._table.apply_filter_over_column(column_name=constants.Dynamics365.ASSOC_PARENT_COL.value,
                                                     filter_term=instance_name)
                self._table.set_pagination(pagination_value=500)
            else:
                manage_id = 'contentTable_actionContextMenu_MANAGE'
                enable_id = 'contentTable_actionContextMenu_ENABLE'

            self._table.hover_click_actions_sub_menu(entity_name=content_name,
                                                     mouse_move_over_id=manage_id,
                                                     mouse_click_id=enable_id)
        else:
            if not is_instance:
                self._admin_console.access_tab(constants.Dynamics365.TABLE_TAB.value)
                self._rtable.apply_filter_over_column(column_name="Environment", filter_term=instance_name)
                self._rtable.apply_filter_over_column(column_name="Name", filter_term=content_name)
                self._rtable.hover_click_actions_sub_menu(entity_name=content_name,
                                                          action_item="Manage",
                                                          sub_action_item="Include in backup")
            else:
                self._admin_console.access_tab(constants.Dynamics365.CONTENT_TAB.value)
                self._rtable.apply_filter_over_column(column_name="Name", filter_term=content_name)
                self._rtable.hover_click_actions_sub_menu(entity_name=content_name,
                                                          action_item="Manage",
                                                          sub_action_item="Include in backup")

    @WebAction()
    def _wait_for_discovery_to_complete(self, timeout=600, poll_interval=10):
        """Wait for the discovery to over and tables to show up"""
        attempts = timeout // poll_interval
        discovery_table = Rtable(self._admin_console, id="d365ContentTable")
        while attempts != 0:
            row_count = discovery_table.get_total_rows_count()
            if attempts == 0 and int(row_count) == 0:
                raise CVWebAutomationException("Discovery did not complete in a stipulated amount of time.")
            elif int(row_count) > 0:
                break
            else:
                self.log.info("Waiting for the discovery to get completed")
                time.sleep(poll_interval)
                try:
                    discovery_table.reload_data()
                except (ElementClickInterceptedException, ElementNotInteractableException):
                    self.log.debug("reload button is not clickable")
                    continue
            attempts = - 1

    @WebAction()
    def _select_content_type(self, content_type):
        """Associate to content on the basis of association type"""
        if content_type == constants.D365AssociationTypes.TABLE:
            self._wizard.select_card("Tables")
        elif content_type == constants.D365AssociationTypes.INSTANCE:
            self._wizard.select_card("Environments")
        elif content_type == constants.D365AssociationTypes.ALL_INSTANCES:
            self._wizard.select_card("All Environments")
        self._wizard.click_next()

    @WebAction()
    def _select_environments(self, content_type, instance_names: list = None):
        """Selects the environments according to content type"""
        if content_type == constants.D365AssociationTypes.TABLE:
            if len(instance_names) > 1:
                instance_names = [instance_names[0]]
            try:
                self._wizard.select_drop_down_values(id="environmentsDropdown", values=instance_names)
            except CVWebAutomationException:
                self._wizard.click_icon_button_by_title(title="Refresh")
                # Wait for the discovery to complete
                time.sleep(10)
                self._wizard.select_drop_down_values(id="environmentsDropdown",
                                                     values=instance_names)
        elif content_type == constants.D365AssociationTypes.INSTANCE:
            self._wait_for_discovery_to_complete()
            discovery_table = Rtable(self._admin_console, id="d365ContentTable")
            discovery_table.select_rows(names=instance_names, search_for=True)
            # In case of tables, we will check if application user is created already or not on the same step
            self._wizard.click_next()

    @WebAction()
    def _select_tables(self, content_type, tables: list = None):
        """Selects the tables for backup """
        if content_type == constants.D365AssociationTypes.TABLE:
            self._wait_for_discovery_to_complete()
            discovery_table = Rtable(self._admin_console, id="d365ContentTable")
            if tables:
                d365_tables = tables
            else:
                d365_tables = self.tcinputs["D365-Tables"].split(",")
            for table in d365_tables:
                discovery_table.search_for(table)
                discovery_table.select_rows([table])
        self._wizard.click_next()

    @WebAction()
    def _select_dynamics_plan(self, dynamics_365_plan):
        """Selects the Dynamics 365 plan for the association"""
        self._wizard.select_drop_down_values(id="cloudAppsPlansDropdown", values=[dynamics_365_plan])
        self._wizard.click_next()

    #########################
    #   Backup Web Actions  #
    #########################

    @WebAction()
    def _click_backup(self):
        """Clicks the backup button on the app page"""
        if not self.__is_react:
            _backup_menu_id = 'BACKUP_GRID'
            self._table.access_toolbar_menu(menu_id=_backup_menu_id)
        else:
            self._rtable.access_toolbar_menu(menu_id="Backup")

    @WebAction()
    def _click_client_main_tab_toggle(self):
        """Click the toggle for the Dynamics 365 client"""
        _client_main_tab_toggle_xpath = '//a[@class="uib-dropdown-toggle main-tab-menu-toggle dropdown-toggle"]'

        if self._admin_console.check_if_entity_exists('xpath', _client_main_tab_toggle_xpath):
            self._driver.find_element(By.XPATH, _client_main_tab_toggle_xpath).click()

    @WebAction(delay=3)
    def _click_client_level_backup(self):
        """Click the Client level backup from Dynamics 365"""
        _client_level_backup_xpath = "//a[@class='tabAction']//span[text()='Back up']"

        if self._admin_console.check_if_entity_exists('xpath', _client_level_backup_xpath):
            self._driver.find_element(By.XPATH, _client_level_backup_xpath).click()
        else:
            self._admin_console.click_button("Backup")

    # @WebAction(delay=2)
    # def _get_job_id(self):
    #     """Fetches the jobID from the toast"""
    #     return self._admin_console.get_jobid_from_popup()

    @WebAction()
    def get_job_details(self, job_id=None):
        """Waits for job completion and gets the job details"""
        if not job_id:
            job_id = self._get_job_id()
        job_details = self._jobs.job_completion(job_id=job_id)
        job_details['Job Id'] = job_id
        self.log.info('Job Details: %s', job_details)
        job_details["Successful Tables"] = self._jobs.get_successful_tables()
        if job_details['Status'] not in \
                ["Committed", "Completed", "Completed w/ one or more errors"]:
            raise CVWebAutomationException('Job did not complete successfully')
        return job_details

    @WebAction(delay=2)
    def _click_view_jobs(self, client_page: bool = False):
        """Clicks the view jobs link from the app page"""
        if client_page:
            self._rtable.access_action_item(self.client_name, self._admin_console.props['action.jobs'])
        else:
            if self.__is_react:
                self._driver.find_element(By.XPATH, "//div[@aria-label='More' and @class='popup']").click()
                self._admin_console.click_button("View jobs")
                self._jobs.access_active_jobs()
            else:
                view_jobs_xpath = f"//span[text()='{self._admin_console.props['action.jobs']}']"
                self._driver.find_element(By.XPATH, view_jobs_xpath).click()
                self._admin_console.wait_for_completion()

    #############################
    #   Browse Ops Web Actions  #
    #############################

    @WebAction()
    def _view_table_details(self, table_name: str, instance: str):
        """
        Go to table details page for given table

        Args:
            table_name (str):    Name of the table to be accessed
            instance    (str):   Name of the instance
        """
        self._admin_console.access_tab(constants.Dynamics365.TABLE_TAB.value)
        self._table.apply_filter_over_column(column_name=constants.Dynamics365.ASSOC_PARENT_COL.value,
                                             filter_term=instance)
        self._table.access_link(entity_name=table_name)
        self._admin_console.wait_for_completion()

    @WebAction()
    def _select_restore_time(self, restore_time):
        """
        Clicks on the given restore time

        Args:
            restore_time (str): Start time of backup job for
                                which items have to be restored
                                Format: Nov 5, 2020 5:35:58 PM

        """
        split_time = restore_time.split(' ')
        split_time[3] = split_time[3].split(':')
        split_time[3] = split_time[3][0] + ':' + split_time[3][1] + ' '
        restore_time = split_time[3] + split_time[4]
        self._driver.find_element(By.XPATH,
                                  f"//div[contains(@class,'cv-ProductNav_Link ng-scope')]//span[text()='{restore_time}']"
                                  ).click()

    #############################
    #   Restore job Web Action  #
    #############################

    @WebAction(delay=2)
    def _click_restore(self, table: bool = True):
        """Clicks the browse button on the app page

                table (boolean)  --     If true - whole table is restored.
                                        If false records are restored
        """
        try:
            if not self.__is_react:
                _click_restore_id = 'RESTORE_OPTIONS'
                self._driver.find_element(By.ID, _click_restore_id).click()
                if table:
                    table_restore_xpath = '//li[@id="batch-action-menu_RESTORE"]//a[@id="RESTORE"]'
                    self._driver.find_element(By.XPATH, table_restore_xpath).click()
                else:
                    record_restore_xpath = '//li[@id="batch-action-menu_BROWSE"]//a[@id="BROWSE"]'
                    self._driver.find_element(By.XPATH, record_restore_xpath).click()
            else:
                self._rtable.access_toolbar_menu(menu_id="Restore")
                if table:
                    restore_xpath = "//li[contains(@class,'MuiButtonBase-root') and contains(text(),'Restore table')]"
                else:
                    restore_xpath = "//li[contains(@class,'MuiButtonBase-root') and contains(text(),'Restore rows')]"
                self._driver.find_element(By.XPATH, restore_xpath).click()
        except Exception:
            self._driver.find_element(By.XPATH, "//span[normalize-space()='Restore']").click()

    @WebAction()
    def _select_level(self, level):
        """Selects restore level"""
        from Web.AdminConsole.Components.panel import RDropDown
        drop_down_obj = RDropDown(self._admin_console)
        drop_down_obj.select_drop_down_values(drop_down_id="relatedRecordsDepthDropdown",
                                              values=[level], partial_selection=True)

    @WebAction()
    def _run_inplace(self):
        """Run in place restore"""
        self._wizard.click_next()

    @WebAction()
    def _run_oop(self, destination):
        """Run oop restore"""
        self._wizard.select_drop_down_values(id="agentDestinationDropdown",
                                      values=["Restore the data to another location"])
        self._driver.find_element(By.XPATH, "//button[@title='Browse']").click()
        destination_table = Rtable(self._admin_console)
        destination_table.select_rows([destination])
        self._driver.find_element(By.XPATH, "//button[@id='Save']").click()
        self._wizard.click_next()

    @WebAction()
    def _enter_details_in_restore_panel(self, restore_type: Enum, destination_instance: str = str(),
                                        record_option: Enum = None, restore_level: str = None):
        """

        Args:
            record_option               <object>      Specifies the destination
                    Acceptable values: Enum: RESTORE_RECORD_OPTIONS
            destination_instance        <str>  Path to which the files have to be restored
            restore_type                <object>
                    Restore type from: ENUM RESTORE_TYPES
            restore_level:              <str>   Level of restore to be triggered, None for normal restore (default)
        """
        if restore_type is None or restore_type == constants.RESTORE_TYPES.IN_PLACE:
            self._run_inplace()
        elif restore_type == constants.RESTORE_TYPES.OOP:
            self._run_oop(destination_instance)

        if record_option == constants.RESTORE_RECORD_OPTIONS.OVERWRITE:
            self._driver.find_element(By.XPATH, "//input[@id='OVERWRITE']").click()

        elif record_option == constants.RESTORE_RECORD_OPTIONS.Skip or record_option is None:
            self._driver.find_element(By.XPATH, "//input[@id='SKIP']").click()

        if restore_level in ["Level 1", "Level 2", "Level 3"]:
            self._driver.find_element(By.XPATH, "//input[@id='RESTORE_RELATED_RECORDS']").click()
            self._select_level(restore_level)
        self._wizard.click_next()

    @WebAction()
    def _click_restore_on_calendar(self):
        """Click on restore on the calendar view"""
        restore_xpath = "//button[@id='submit-btn' and @aria-label='Restore']"
        element = self._driver.find_element(By.XPATH, restore_xpath)
        element.click()

    @WebAction()
    def _select_environment_from_browse(self, environment):
        """Click on environment in the browse page"""

        
        environment_xpath = f"//div[@id='dynamics365BrowseGrid']//div/span[contains(text(), '{environment}')]"
        element = self._driver.find_element(By.XPATH, environment_xpath)
        element.click()

    @WebAction()
    def _get_selected_items(self):
        """Get Items selected from the restore Panel"""
        selected_item_table = Rtable(self._admin_console, id="ATBackupSelectedItems")
        return len(selected_item_table.get_column_data('Name'))

    @WebAction()
    def _perform_restore_from_browse(self, restore_type: Enum = None,
                                     dest_instance: str = str(),
                                     record_option: Enum = None,
                                     restore_level: str = None):
        """Performs restore on browse page"""
        job_details = dict()
        self._rtable.select_all_rows()
        # self.__cvactions_toolbar.select_action_sublink(text="Restore", expand_dropdown=False)
        self._page_container.click_button(id="RESTORE")
        self._admin_console.wait_for_completion()
        self._enter_details_in_restore_panel(
            restore_type=restore_type,
            destination_instance=dest_instance,
            record_option=record_option,
            restore_level=restore_level)
        selected_items = self._get_selected_items()
        job_details["SelectedItems"] = selected_items
        self._wizard.click_button(id='Next')
        job_id = self._get_job_id_from_wizard()
        self.log.info('Job ID for Dynamics 365 CRM Restore job: %s', job_id)
        job_details.update(self.get_job_details(job_id))
        return job_details

    @WebAction()
    def _select_two_versions(self, version1, version2):
        """Selects two versions in compare dialog box"""
        self._driver.find_element(By.XPATH, "//input[@id='compareWithPreviousBackup']").click()
        browse_buttons = self._driver.find_elements(By.XPATH, "//button[@title='Browse']")
        browse_buttons[0].click()
        self._rtable.select_rows([version1])
        self._driver.find_element(By.XPATH, "//button[@aria-label='Add']").click()
        browse_buttons[1].click()
        self._rtable.select_rows([version2])
        self._driver.find_element(By.XPATH, "//button[@aria-label='Add']").click()
        time.sleep(5)
        self._driver.find_element(By.XPATH, "//button[@aria-label='Compare']").click()
        time.sleep(10)

    @PageService()
    def _compare_records(self, record_dict):
        """Compares the record with the previous version on the browse page"""
        browse_table = Rtable(self._admin_console, id="dynamics365BrowseGrid")
        browse_table.access_action_item(entity_name=record_dict["RecordName"], action_item="Compare")
        time.sleep(10)
        self._select_two_versions(record_dict["Versions"][0], record_dict["Versions"][1])
        compare_table = Rtable(self._admin_console,
        xpath="(//div[contains(@class, 'mui-modal-dialog mui-modal-centered')] | //div["
                                     "@aria-labelledby ='customized-dialog-title'])//div[contains(@class,"
                                     "'grid-holder')]")
        compare_data = compare_table.get_table_data()
        self._driver.find_element(By.XPATH, "//div[@class='mui-modal-header']//button[@title='Close']").click()
        return compare_data

    @WebAction()
    def _click_restore_on_calendar(self):
        """Click on restore on the calendar view"""
        restore_xpath = "//button[@id='submit-btn' and @aria-label='Restore']"
        element = self._driver.find_element(By.XPATH, restore_xpath)
        element.click()

    @WebAction()
    def _click_browse_filter(self):
        """Clicks the browse filter"""
        xpath = "//button[@aria-label='Filters']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def _click_search(self):
        """Clicks search button on the browse filter"""
        xpath = "//button[@aria-label='Search']"
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def _apply_browse_filter(self, item_type: Enum, item_name: str):
        """Apply the browse filter"""
        self._admin_console.fill_form_by_id("ITEM_NAME", item_name)
        if item_type == D365FilterType.ROW:
            self._rdropdown.select_drop_down_values(values=[item_type.value], drop_down_id="ITEM_TYPE")
        elif item_type == D365FilterType.TABLE:
            self._rdropdown.select_drop_down_values(values=[item_type.value], drop_down_id="ITEM_TYPE")
        self._click_search()

    @WebAction()
    def _click_restore_from_compare(self):
        """Clicks the restore button from the compare panel"""
        xpath = '//li[@id="RESTORE_COMPARE_GRID_LEFT"]'
        self._driver.find_element(By.XPATH, xpath).click()

    @WebAction()
    def _compare_record_with_live_data(self, older_record):
        """Compare the record with live data"""
        self._admin_console.wait_for_completion()
        self._rmodal_dialog.click_element('//input[@id="compareWithLiveData"]')
        self._driver.find_element(By.XPATH, "//button[@aria-label='Browse']").click()
        self._admin_console.wait_for_completion()
        self._rtable.select_rows(["1.0"])  # Select the first version
        select_version_dialog = RModalDialog(self._admin_console, title="Select version")
        select_version_dialog.click_submit()
        self._rpanel.submit()
        self._admin_console.wait_for_completion()
        alert = self._alert.check_error_message()
        compare_table = Rtable(self._admin_console, xpath="(//div[contains(@class, 'mui-modal-dialog mui-modal-centered')] | //div[@aria-labelledby ='customized-dialog-title'])//div[contains(@class,'grid-holder')]")          
        compare_data = compare_table.get_table_data()
        self._driver.find_element(By.XPATH, "//div[@class='mui-modal-header']//button[@title='Close']").click()
        return compare_data

    @WebAction()
    def _click_restore_on_calendar(self):
        """Click on restore on the calendar view"""
        restore_xpath = "//button[@id='submit-btn' and @aria-label='Restore']"
        element = self._driver.find_element(By.XPATH, restore_xpath)
        element.click()

    ###############################
    # Client Creation Page Service#
    ###############################

    @PageService()
    def check_if_app_exists(self, app_name: str):
        """Checks if the given app already exists

                Args:
                    app_name (str)  --  Name of the Dynamics 365 CRM app to check
        """
        return self._rtable.is_entity_present_in_column(
            self._admin_console.props['label.name'], app_name)

    @PageService()
    def create_dynamics365_app(self, client_name: str, cloud_region: int, storage_region: str = "East US 2",
                               time_out=600, poll_interval=10,
                               is_metallic: bool = False):
        """
        Create a Dynamics 365 App

        Arguments:

            time_out            (int):      Time out for app creation

            poll_interval       (int):      Regular interval for app creating check

            client_name         (str):      Name of the client

            is_metallic         (bool):     If client creation is run on Metallic environment

            cloud_region        (int):      Cloud region for app creation

            storage_region      (str):      Storage region for which you need to use server plans
        """

        # General Required details
        name = client_name

        if not is_metallic:
            self._create_app()

        if True:
            # Required details for Dynamics 365 Client
            index_server = None
            access_node = None
            client_group = None
            global_admin = None
            password = None
            application_id = None
            application_key_value = None
            azure_directory_id = None
            acquire_token_user = None
            acquire_token_passwd = None

            if 'IndexServer' in self.tcinputs:
                index_server = self.tcinputs['IndexServer']
            if 'AccessNode' in self.tcinputs:
                access_node = self.tcinputs['AccessNode']
            elif 'ClientGroup' in self.tcinputs:
                client_group = self.tcinputs['ClientGroup']
            if 'GlobalAdmin' in self.tcinputs:
                global_admin = self.tcinputs['GlobalAdmin']
                password = self.tcinputs['Password']
            elif 'application_id' in self.tcinputs:
                application_id = self.tcinputs['application_id']
                application_key_value = self.tcinputs['application_key_value']
                azure_directory_id = self.tcinputs['azure_directory_id']

                if 'TokenAdminUser' in self.tcinputs:
                    acquire_token_user = self.tcinputs['TokenAdminUser']
                    acquire_token_passwd = self.tcinputs['TokenAdminPassword']
            if not self.__is_react:
                self._admin_console.fill_form_by_id('appName', name)
                if not is_metallic:
                    # Metallic config: details fetched from company/ server plan configuration
                    server_plan = self.tcinputs['ServerPlan']
                    self._dropdown.select_drop_down_values(values=[server_plan],
                                                           drop_down_id='planSummaryDropdown')
                    # Check if infrastructure settings are inherited from plan or not
                    if self._admin_console.check_if_entity_exists('xpath',
                                                                  "//button[contains(@id, 'indexServers')]"
                                                                  ):
                        self._dropdown.select_drop_down_values(values=[index_server],
                                                               drop_down_id='createOffice365App_isteven-multi-select_#2568')
                        if access_node:
                            if isinstance(access_node, list):
                                self._dropdown.select_drop_down_values(
                                    values=access_node, drop_down_id='createOffice365App_isteven-multi-select_#5438')
                                self._enter_shared_path_for_multinode()
                                self._add_account_for_shared_path()
                            else:
                                self._dropdown.select_drop_down_values(
                                    values=[access_node], drop_down_id='createOffice365App_isteven-multi-select_#5438')
                        elif client_group:
                            self._dropdown.select_drop_down_values(
                                values=[client_group], drop_down_id='createOffice365App_isteven-multi-select_#5438')
                            self._enter_shared_path_for_multinode()
                            self._add_account_for_shared_path()

                if self._region_selector_present():
                    if cloud_region == 1:
                        _region = self.tcinputs.get('Region', constants.CLOUD_REGIONS.DEFAULT.value)
                    elif cloud_region == 2:
                        _region = self.tcinputs.get('Region', constants.CLOUD_REGIONS.GCC.value)
                    else:
                        _region = self.tcinputs.get('Region', constants.CLOUD_REGIONS.GCC_HIGH.value)
                    self._dropdown.select_drop_down_values(
                        values=[_region],
                        drop_down_id='createOffice365App_isteven-multi-select_#1167')

                if global_admin and self.is_multi_tenant_enabled():
                    self._configure_with_multi_tenant_app(global_admin_address=global_admin,
                                                          global_admin_passwd=password)
                    self._mark_prerequisites_for_d365(cr_type="GLOBAL-Express", region=cloud_region)

                elif global_admin:
                    self._admin_console.fill_form_by_id('globalUserName', global_admin)
                    self._admin_console.fill_form_by_id('globalPassword', password)

                    self._admin_console.checkbox_select('SAVE_GA_CREDS')
                    self._mark_prerequisites_for_d365(cr_type="EXPRESS")
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
                        if len(self._driver.window_handles) > 1:
                            break

                        if self._admin_console.check_if_entity_exists("link",
                                                                      self._admin_console.props[
                                                                          'action.authorize.app']):
                            break

                        time.sleep(poll_interval)
                        attempts -= 1

                    self._authorize_permissions(global_admin, password)
                    if cloud_region == 3:
                        self._close_app_user_info_panel()

                elif application_id:
                    self._driver.find_element(By.XPATH,
                                              "//input[@type='radio' and @value='MANUALLY']"
                                              ).click()
                    self._open_add_azure_app_panel()
                    self._admin_console.fill_form_by_id('applicationId', application_id)
                    self._admin_console.fill_form_by_id('secretAccessKey', application_key_value)
                    self._admin_console.fill_form_by_id('tenantName', azure_directory_id)

                    self._mark_prerequisites_for_d365(cr_type="CUSTOM", region=cloud_region)
                    if cloud_region != 3:
                        self._authorize_permissions(acquire_token_user, acquire_token_passwd, custom_config=True)

                self._admin_console.submit_form()

                self._admin_console.wait_for_completion()
                time.sleep(5)  # Wait for Discovery process to launch in access node
            else:
                if is_metallic:
                    self._select_storage_region(storage_region)
                self._fill_app_name(name)
                if self._region_selector_present():
                    self._select_cloud_region(cloud_region)
                if not is_metallic:
                    server_plan = self.tcinputs['ServerPlan']
                    self._select_server_plan(server_plan)
                    self._select_infrastructure_details(index_server, access_node, client_group)
                if global_admin and self.is_multi_tenant_enabled():
                    self._configure_with_multi_tenant_app(global_admin_address=global_admin,
                                                          global_admin_passwd=password)
                    self._mark_prerequisites_for_d365(cr_type="GLOBAL-Express", region=cloud_region)
                elif global_admin:
                    self._add_app_using_express_configuration(global_admin, password)
                    self._check_if_azure_app_created(time_out, poll_interval)
                    self._authorize_permissions(global_admin, password)
                    if cloud_region == 3:
                        self._close_app_user_info_panel()
                elif application_id:
                    self._add_app_using_custom_configuration(application_id, application_key_value, azure_directory_id)
                    self._authorize_permissions(acquire_token_user, acquire_token_passwd, custom_config=True)
                self._wizard.click_next()
                self._admin_console.wait_for_completion()
                self._wizard.click_button(name="Close")
                self._admin_console.wait_for_completion()
                time.sleep(5)  # Wait for Discovery process to launch in access node
        self.client_name = client_name

    @PageService()
    def get_all_dynamics365_apps(self):
        """
        List of all App Names
        """
        return self._rtable.get_column_data(self._admin_console.props['label.name'])

    @PageService()
    def get_app_name(self):
        """
            Fetches the name of the created Dynamics 365 client.
            This is useful for metallic where client name is preceded with the company name
        """
        return self._get_app_name()

    @PageService()
    def delete_dynamics365_app(self, app_name):
        """
            Deletes the Dynamics 365 app
                Args:
                    app_name (str)  --  Name of the Dynamics 365 app to delete

        """
        self._rtable.access_action_item(app_name, self._admin_console.props['action.releaseLicense'])
        self._rmodal_dialog.click_submit()
        self._admin_console.wait_for_completion()
        self._rtable.access_action_item(app_name, self._admin_console.props['action.delete'])
        self._rmodal_dialog.type_text_and_delete(text_val='DELETE', checkbox_id='onReviewConfirmCheck')
        self._admin_console.wait_for_completion()

    @PageService()
    def select_client(self, client_name: str = None):
        """
        Accesses the Dynamics 365 client
        from the Dynamics 365 client listing page

        Args:
            client_name (string)  --  Name of the Dynamics 365 client to access

        """
        if not client_name:
            client_name = self.client_name
        self._rtable.access_link(client_name)
        # x_path = f"//span[normalize-space(text()) = '{client_name}']/parent::span/parent::a"
        # self._driver.find_element(By.XPATH, x_path).click()
        self._admin_console.wait_for_completion()

    #############################
    # Client Config Page Service#
    #############################

    @PageService()
    def get_azure_app_details(self):
        """Get the azure app details from Configuration Tab"""
        self._admin_console.select_configuration_tab()
        details = self._table.get_table_data()
        return details

    @PageService()
    def access_client_configuration_tab(self):
        """Method to select the Client configuration tab"""
        self._admin_console.select_configuration_tab()

    @PageService()
    def get_client_general_configuration(self):
        """Get the values from the general tab on the configuration tab for a Dynamics 365 Client"""
        if self._admin_console.get_current_tab() != self._admin_console.props['label.nav.configuration']:
            self.access_client_configuration_tab()
        general_panel = RPanelInfo(self._admin_console, title=self._admin_console.props['label.generalPane'])
        details = general_panel.get_details()
        return details

    @PageService()
    def get_client_infrastructure_details(self):
        """Get the Infrastructure values for a Dynamics 365 client from the configuration tab"""
        self.access_client_configuration_tab()
        infra_panel = RPanelInfo(self._admin_console, title=self._admin_console.props['label.infrastructurePane'])
        infra_details = infra_panel.get_details()
        return infra_details

    @PageService()
    def run_client_check_readiness(self):
        """
            Method to run check readiness for the Dynamics 365 Client
            Returns:
                client_readiness    -- Result of the client readiness operation
        """
        self.access_client_configuration_tab()
        self._click_show_details_for_client_readiness()
        self._admin_console.wait_for_completion()
        client_readiness = self._get_client_readiness_value()
        self._driver.find_element(By.LINK_TEXT, self.client_name).click()
        self._admin_console.wait_for_completion()
        return client_readiness

    @PageService()
    def is_app_associated_with_plan(self, client_name: str):
        """
        Verifies if client is associated with plan
        Returns: True if client is listed in the associated entities page of plans
                 else False
        """
        self._admin_console.navigator.navigate_to_plan()
        self._plans.select_plan(self.tcinputs['ServerPlan'])
        self._admin_console.wait_for_completion()
        self._admin_console.access_tab('Associated entities')
        if not self.check_if_app_exists(client_name):
            raise CVWebAutomationException('The Dynamics client does not have any Server Plan configured')

    #############################################
    #   Client config view/ modification Page Service #
    #############################################

    @PageService()
    def get_instances_configured_count(self):
        """
            Method to get a count of the total number of configured instances
        """
        self._admin_console.access_tab(constants.Dynamics365.CONTENT_TAB.value)
        return self._table.get_total_rows_count()

    @PageService()
    def get_tables_configured_count(self):
        """
            Method to get a count of the configured tables
        """
        self._admin_console.access_tab(constants.Dynamics365.TABLE_TAB.value)
        return self._table.get_total_rows_count()

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
        if new_access_node and new_shared_path:
            self._edit_access_node(new_shared_path, new_user_account, new_password, new_access_node)

    @PageService()
    def get_configured_content(self, instance: bool = False):
        """
            Method to get a list of the configured content

            Arguments:
                instance        (bool)--    Whether to get a list of the configured instances
        """
        self._admin_console.wait_for_completion()
        if instance:
            self._admin_console.access_tab(constants.Dynamics365.CONTENT_TAB.value)
        else:
            self._admin_console.access_tab(constants.Dynamics365.TABLE_TAB.value)
        self._table.set_pagination(pagination_value=500)
        _content = self._table.get_column_data(column_name="Name")
        return _content

    @PageService()
    def disable_activity_control_toggle(self):
        """
            Disables activity control toggle button to disable backup
        """
        self._admin_console.select_configuration_tab()
        general_panel = PanelInfo(self._admin_console,
                                  title=self._admin_console.props['heading.clientActivityControl'])
        general_panel.disable_toggle(self._admin_console.props['Data_Backup'])

    @PageService()
    def get_client_summary_details(self) -> dict:
        """
            Get the Client Summary Stats from the Overview page for a Dynamics 365 Client
        """
        self._admin_console.wait_for_completion()
        self._admin_console.access_tab(constants.Dynamics365.OVERVIEW_TAB.value)

        _client_stats_panel = PanelInfo(self._admin_console, title=self._admin_console.props['overview.summary'])

        return _client_stats_panel.get_details()

    @PageService()
    def get_client_stats(self) -> dict:
        """
            Get the stats for the client from the overview tab
        """
        self._admin_console.wait_for_completion()
        self._admin_console.access_tab(constants.Dynamics365.OVERVIEW_TAB.value)

        _bkp_size_xpath = f"//div[text()='{self._admin_console.props['office365dashboard.entities.backup.size']}']/" \
                          f"preceding-sibling::span/h4"
        _bkp_size = self._driver.find_element_by_xpath(_bkp_size_xpath).text

        _tables_count_xpath = f"//div[text()='{self._admin_console.props['overview.stats.entities']}']/preceding" \
                              f"-sibling::span/h4"
        _tables_count = self._driver.find_element_by_xpath(_tables_count_xpath).text

        _item_count_xpath = f"//div[text()='{self._admin_console.props['column.numberOfItems']}']/preceding-sibling" \
                            f"::span/h4 "
        _item_count = self._driver.find_element_by_xpath(_item_count_xpath).text

        return {"Backup Size": _bkp_size, "Tables Count": _tables_count, "Items Count": _item_count}

    ##########################################
    #   Content Modification Page Service    #
    ##########################################

    @staticmethod
    def filter_content_list(tables: list = None):
        """
            This method will arrange the input of the form:
                [('table1', 'environment1') , ('table2' , 'environment1') , ('table1', 'environment2')
            to the form:
                { 'environment1': ['table1' , 'table2' , 'table3'] , 'environment2' : ['table1']}
            Reason is:
                earlier, we were displaying all tables in a single GUI table,
                    and we could filter on each environment and associate them.
                now, we have an extra initial step, where we need to choose environment,
                    and then discovery is performed for that environment.

        """
        tables_dict: dict = dict()
        for table, environment in tables:
            if environment in tables_dict:
                tables_dict[environment].append(table)
            else:
                tables_dict[environment] = [table]
        return tables_dict

    @PageService()
    def configure_application_user(self, environment_name: str, instance_modal: bool = True,
                                   content_type: constants.D365AssociationTypes = None):
        """
            Method to configure an application user

            Arguments:
                environment_name    (str):      Name of the environment for which application user is to be configured
                instance_modal      (bool):     Whether to use the 'All Environment' modal or 'Add Table' modal.
                content_type        (Enum):     Type of content to be associated
        """
        if not self.__is_react:
            if instance_modal:
                self._click_add_instance()
                self._admin_console.wait_for_completion()
                self._table.access_action_item(entity_name=environment_name,
                                               action_item=constants.Dynamics365.APP_USER_LABEL.value)

            else:
                self._open_add_table_panel()
                self._admin_console.wait_for_completion()

                _app_user_env_select_id = "office365OneDriveAddAssociation_isteven-multi-select_#5444"
                self._dropdown.select_drop_down_values(values=[environment_name],
                                                       drop_down_id=_app_user_env_select_id)

                self._driver.find_element(By.LINK_TEXT, 'here').click()

            self._admin_console.wait_for_completion()
            self._modal_dialog.click_submit()
            # this will click the proceed button

            self._check_error_multi_tenant_config()
            # check if any error in fetching App details

            self._admin_console.wait_for_completion()
            self._authorize_permissions(global_admin=self.d365_online_user,
                                        password=self.d365_online_password,
                                        app_user=True)

            self._admin_console.wait_for_completion()

            if not self.check_application_user_config_success():
                #   will handle any error in fetching environment details
                raise CVWebAutomationException("Application User Creation was unsuccessful")

            self._modal_dialog.click_cancel()  # click close on the app user config panel
            self._modal_dialog.click_cancel()  # click cancel on the add environment panel
            self._admin_console.wait_for_completion()
        else:
            if content_type == constants.D365AssociationTypes.INSTANCE:
                environment_table = Rtable(self._admin_console, id="d365ContentTable")
                environment_table.search_for(environment_name)
                status = environment_table.get_column_data(column_name="Accessibility")
                if status[0] == "Not accessible":
                    environment_table.access_action_item(entity_name=environment_name,
                                                         action_item=constants.Dynamics365.APP_USER_LABEL.value)
                else:
                    self.log.info("Application User already configured")
                    return True
            elif content_type == constants.D365AssociationTypes.TABLE:
                try:
                    alert = self._wizard.get_alerts()
                except NoSuchElementException:
                    self.log.info("Application User already configured")
                    return True
                if "Application user is not configured correctly" in alert:
                    self.log.info("Application user is not configured, Creating one...")
                    self._admin_console.select_hyperlink("here")
            self._admin_console.wait_for_completion()
            self._rmodal_dialog.click_element("//button[@aria-label='Proceed']")
            self._admin_console.wait_for_completion()
            self._authorize_permissions(global_admin=self.d365_online_user,
                                        password=self.d365_online_password,
                                        app_user=True)
            return True

    @PageService()
    def add_association(self, assoc_type: constants.D365AssociationTypes, instances: list = None, tables: list = None,
                        plan: str = None,
                        all_instances: bool = False):
        """
        Method to add an association to a Dynamics 365 Client
            Args:
                assoc_type:         <Enum>:         Tye of Association
                    Allowed values:
                        constants.D365AssociationTypes.TABLE
                        constants.D365AssociationTypes.INSTANCE

                instances:          <LIST<STR>> :    List of Instances to associate
                tables:             <list<tuple(string,string)>>
                                                :   List of tables to associate
                    Format:
                        [
                            (table1, environment-of-table1), (table2, environment-of-table2)...
                        ]
                plan:               <str>:          Dynamics 365 Plan to be used for creating the association
                    If plan is not passed, then the value passed in test case inputs is used
                all_instances:      <bool>:         Whether to associate all instances
                    Default Value is False


        """
        tables_dict = None
        instance = None
        if plan:
            d365_plan = plan
        else:
            d365_plan = self.d365_plan
        if not self.__is_react:
            if assoc_type == constants.D365AssociationTypes.TABLE:
                self._open_add_table_panel()
            elif assoc_type == constants.D365AssociationTypes.INSTANCE or all_instances is True:
                self._click_add_instance(all_instances=all_instances)
            self._admin_console.wait_for_completion()
            _plan_drop_down_id = 'office365OneDriveAddAssociation_isteven-multi-select_#5444'
            try:
                if assoc_type == constants.D365AssociationTypes.TABLE:
                    if not tables:
                        tables = self.d365tables
                        # read tables from the input JSON directly
                    tables_dict = self.filter_content_list(tables=tables)
                    for environment in tables_dict:
                        # select the environment from the dropdown
                        _add_table_env_select_id = "office365OneDriveAddAssociation_isteven-multi-select_#5444"
                        self._dropdown.select_drop_down_values(values=[environment],
                                                               drop_down_id=_add_table_env_select_id)
                        self._driver.find_element(By.LINK_TEXT, 'here').click()
                        self._admin_console.wait_for_completion()
                        for table in tables_dict[environment]:
                            search_element = self._driver.find_element(By.ID, 'searchInput')
                            if search_element.is_displayed():
                                self._admin_console.fill_form_by_id(element_id='searchInput', value=table)
                            self._table.select_rows([table])
                            time.sleep(10)
                        self._dropdown.select_drop_down_values(
                            values=[d365_plan],
                            drop_down_id=_plan_drop_down_id)
                    self.log.info(f'Tables added: {tables}')

                elif assoc_type == constants.D365AssociationTypes.INSTANCE:
                    if instances:
                        for instance in instances:
                            search_element = self._driver.find_element(By.ID, 'searchInput')
                            if search_element.is_displayed():
                                self._admin_console.fill_form_by_id(element_id='searchInput', value=instance)
                            self._table.select_rows([instance])
                        self.log.info(f'Instances added: {instances}')
                    else:
                        for instance in self.instances:
                            search_element = self._driver.find_element(By.ID, 'searchInput')
                            if search_element.is_displayed():
                                self._admin_console.fill_form_by_id(element_id='searchInput', value=instance)
                            self._table.select_rows([instance])
                        self.log.info(f'Instances added: {self.instances}')

                    self._dropdown.select_drop_down_values(
                        values=[d365_plan],
                        drop_down_id=_plan_drop_down_id)
            except (ElementNotInteractableException, NoSuchElementException):
                self.check_for_discovery_errors()

            self._admin_console.submit_form()
            self._admin_console.wait_for_completion()
            self._admin_console.close_popup()

            if assoc_type == constants.D365AssociationTypes.TABLE:
                self._modal_dialog.click_cancel()
        else:
            if tables:
                tables_dict = self.filter_content_list(tables=tables)
                instances = [tables[0][1]]
            elif instances:
                instances = instances
            self._admin_console.access_tab(constants.Dynamics365.CONTENT_TAB.value)
            self._rtable.access_toolbar_menu(menu_id="Add")
            self._wizard.select_card("Add content to backup")
            self._wizard.click_next()
            self._admin_console.wait_for_completion()
            self._wizard.expand_accordion("Advanced")
            self._select_content_type(assoc_type)
            if assoc_type == constants.D365AssociationTypes.INSTANCE:
                self._wait_for_discovery_to_complete()
                for instance in instances:
                    if not self.configure_application_user(environment_name=instance, content_type=assoc_type):
                        raise CVWebAutomationException("Application user configuration failed")
            self._select_environments(assoc_type, instances)
            if assoc_type == constants.D365AssociationTypes.TABLE:
                if not self.configure_application_user(environment_name=tables[0][1], content_type=assoc_type):
                    raise CVWebAutomationException("Application user configuration failed")
                self._wizard.select_drop_down_values(id="environmentsDropdown",
                                                     values=instances)
                self._wizard.click_next()
                tables_dict = self.filter_content_list(tables=tables)
            self._select_tables(assoc_type, tables_dict[instances[0]] if tables_dict else None)
            self._select_dynamics_plan(d365_plan)
            self._wizard.click_button(id="Submit")
            self._admin_console.wait_for_completion()

    @PageService()
    def add_association_gcc_high(self, instances: list, instances_url: list, plan: str = None):
        """
        Method to add an association to a Dynamics 365 Client
            Args:
                instances:          <LIST<STR>> :    List of Instances to associate
                instances_url:        <LIST<STR>> :    List of Instances URL's to associate
                plan:               <str>:          Dynamics 365 Plan to be used for creating the association
                    If plan is not passed, then the value passed in test case inputs is used
        """

        if plan:
            d365_plan = plan
        else:
            d365_plan = self.d365_plan

        _plan_drop_down_id = 'office365OneDriveAddAssociation_isteven-multi-select_#5444'
        try:
            for ind in range(len(instances)):
                self._click_add_instance()
                self._admin_console.wait_for_completion()
                self._admin_console.fill_form_by_id(element_id='environmentUrl', value=instances_url[ind])
                self._modal_dialog.click_submit()
                self._admin_console.wait_for_completion()
                search_element = self._driver.find_element(By.ID, 'searchInput')
                if search_element.is_displayed():
                    self._admin_console.fill_form_by_id(element_id='searchInput', value=instances[ind])
                self._table.select_rows([instances[ind]])
                self.log.info(f'Instance added: {instances[ind]}')
                self._dropdown.select_drop_down_values(
                    values=[d365_plan],
                    drop_down_id=_plan_drop_down_id)
                self._admin_console.submit_form()
                self._admin_console.wait_for_completion()
                self._admin_console.close_popup()

        except (ElementNotInteractableException, NoSuchElementException):
            self.check_for_discovery_errors()

    @PageService()
    def get_configured_instances(self):
        """
            Method to get a list of the configured instances

            Returns:
                instance_list       (list)--    List of configured instances
        """
        self._admin_console.access_tab(constants.Dynamics365.CONTENT_TAB.value)
        instance_list = self._table.get_column_data(column_name='Name')
        return instance_list

    @PageService()
    def get_tables_associated_for_instance(self, instance_list: list):
        """
            Get the tables associated with the client corresponding to the passed instances

            Arguments:
                instance_list       <list<str>>--   List of instances for which we have to verify

            Returns:
                tables_dict         <dict>--        Dictionary of tables associated
                    Format:
                        Key::               Instance Name
                        Value:              List of tables
        """
        tables_dict = dict()
        self._admin_console.access_tab(constants.Dynamics365.TABLE_TAB.value)
        for instance in instance_list:
            self._rtable.apply_filter_over_column(column_name=constants.Dynamics365.ASSOC_PARENT_COL.value,
                                                  filter_term=instance)
            discv_tables = self._rtable.get_column_data(column_name="Name")
            tables_dict[instance] = discv_tables
        return tables_dict

    @PageService()
    def exclude_content(self, name: str = str(), is_instance: bool = False, instance_name: str = str()):
        """
        Excludes the given content from backup

        Args:
            instance_name:      Name of instance to which the table belong to
            is_instance:        Whether the content is an instance or not
            name:               Name of content to exclude from backup

        """

        self._click_exclude_content(content_name=name, is_instance=is_instance, instance_name=instance_name)
        self._admin_console.wait_for_completion()
        self._rmodal_dialog.click_submit()
        self._admin_console.wait_for_completion()
        self._rtable.clear_column_filter(column_name="Name", filter_term=name)
        if not is_instance:
            self._rtable.clear_column_filter(column_name="Environment", filter_term=instance_name)
        self.log.info(f'Content Excluded from Backup:: {name}')

    @PageService()
    def include_in_backup(self, name: str, instance_name: str = str(), is_instance: bool = False):
        """
        Includes the given content to back up

        Args:
            is_instance:        Whether the content is an instance or not
            instance_name:      Name of the instance, corresponding to the table
            name:               Name of the Dynamics 365 table/ instance

        """
        # self._select_content(content_name=name, instance_name=instance_name, is_instance=is_instance)
        self._click_include_content(instance_name=instance_name, is_instance=is_instance, content_name=name)
        self._admin_console.wait_for_completion()
        self._rmodal_dialog.click_submit()
        self._admin_console.wait_for_completion()
        self._rtable.clear_column_filter(column_name="Name", filter_term=name)
        if not is_instance:
            self._rtable.clear_column_filter(column_name="Environment", filter_term=instance_name)
        self.log.info(f'Content included in backup: {name}')

    @PageService()
    def delete_from_content(self, name: str, instance_name: str = str(), is_instance: bool = False):
        """
        Delete the content from Dynamics 365 client association

            is_instance:        Whether the content is an instance or not
            instance_name:      Name of the environment, corresponding to the table
            name:               Name of the Dynamics 365 table/ instance

            EXAMPLE:
                Removing an environment
                    name = "test-env"   |   is_instance = True
                Removing a table
                    name = "Accounts"   |   instance_name = "test-env"  | is_instance ' False
        """

        # self._select_content(content_name=name, instance_name=instance_name, is_instance=is_instance)
        self._click_delete_content(instance_name=instance_name, is_instance=is_instance, content_name=name)
        self._admin_console.wait_for_completion()
        self._rmodal_dialog.click_submit()
        self._admin_console.wait_for_completion()
        self._rtable.clear_column_filter(column_name="Name", filter_term=name)
        if not is_instance:
            self._rtable.clear_column_filter(column_name="Environment", filter_term=instance_name)
        self.log.info(f'Deleted: {name} from client content')

    @PageService()
    def get_content_status(self, name: str, instance: str = str(), is_instance=False):
        """
        Gets the status of the content

        Args:
        Returns:
            status (str):       Status of the content
                                Valid values - Active, Disabled, Deleted

        """
        if not is_instance:
            self._admin_console.access_tab(constants.Dynamics365.TABLE_TAB.value)
        else:
            self._admin_console.access_tab(constants.Dynamics365.CONTENT_TAB.value)

        columns = self._rtable.get_visible_column_names()
        if 'Status' not in columns:
            self._rtable.display_hidden_column('Status')

        self._rtable.apply_filter_over_column('Name', name)
        self._admin_console.wait_for_completion()
        if not is_instance:
            self._rtable.apply_filter_over_column(constants.Dynamics365.ASSOC_PARENT_COL.value, instance)
            self._admin_console.wait_for_completion()
        table_index = self._get_table_index_in_page(table_name=name)
        if table_index == -1:
            return constants.AssocStatusTypes.DELETED
        status = self._rtable.get_table_data().get('Status')[table_index]
        self._rtable.clear_column_filter('Name', name)
        if not is_instance:
            self._rtable.clear_column_filter(constants.Dynamics365.ASSOC_PARENT_COL.value, instance)
        assoc_status = constants.AssocStatusTypes(status)
        return assoc_status

    @PageService()
    def get_content_assoc_plan(self, name: str, instance: str = str(), is_instance=False):
        """

        Args:
            name:
            instance:
            is_instance:

        Returns:

        """
        if not is_instance:
            self._admin_console.access_tab(constants.Dynamics365.TABLE_TAB.value)
        else:
            self._admin_console.access_tab(constants.Dynamics365.CONTENT_TAB.value)

        columns = self._table.get_visible_column_names()
        if 'Status' not in columns:
            self._table.display_hidden_column('Plan')

        self._table.apply_filter_over_column('Name', name)
        if not is_instance:
            self._table.apply_filter_over_column(constants.Dynamics365.ASSOC_PARENT_COL.value, instance)
            self._table.set_pagination(pagination_value=100)
        table_index = self._get_table_index_in_page(table_name=name)
        if table_index == -1:
            return None
        assoc_plan = self._table.get_table_data().get('Plan')[table_index]
        self._table.clear_column_filter('Name')
        if not is_instance:
            self._table.clear_column_filter(constants.Dynamics365.ASSOC_PARENT_COL.value)

        return assoc_plan

    @PageService()
    def get_backup_health_content(self) -> dict:
        """
            Get the backup health report for a Dynamics 365 client.
        """
        self._admin_console.access_tab(constants.Dynamics365.OVERVIEW_TAB.value)
        self._admin_console.wait_for_completion()

        _percent_xpath = "//*[@class='dial-center-percent']"
        _health_percent = self._driver.find_element_by_xpath(_percent_xpath).text.strip().replace("%", "")

        _bkp_tables_xpath = "//span[contains(text(),'Tables backed up recently')]/following-sibling::span"
        _not_bkp_tables_xpath = "//span[contains(text(),'Tables not backed up recently')]/following-sibling::span"
        _successful_tables = self._driver.find_element_by_xpath(_bkp_tables_xpath).text.strip()
        _unsuccessful_tables = self._driver.find_element_by_xpath(_not_bkp_tables_xpath).text.strip()

        return {"health_percent": _health_percent,
                "backedup_tables": _successful_tables,
                "not_backed_tables": _unsuccessful_tables}

    #########################
    #   Backup Page Service #
    #########################

    @PageService()
    def run_d365client_backup(self, full_backup: bool = False, client_level: bool = False):
        """
            Run D365 Client backup
            Arguments:
                full_backup         (bool)--    Whether to run a full backup for the client
                client_level        (bool)--    Whether to run a client level backup or a backupset level
                    If client level:
                        backup is initiated from the action menu item on the client listing page
                    if backupset_level  (client_level is False):
                        backup is initiated from the action menu on the client page

        """
        if not client_level:
            # self.select_client()
            self._click_client_main_tab_toggle()
            self._click_client_level_backup()
        else:
            self._admin_console.navigator.navigate_to_dynamics365()
            self._rtable.access_action_item(self.client_name, self._admin_console.props['action.backup'])
        if full_backup:
            self._admin_console.checkbox_select(checkbox_id="convertJobToFull")
        if not self.__is_react:
            self._modal_dialog.click_submit(submit_type=True)
        else:
            self._rmodal_dialog.click_submit()
        job_id = self._get_job_id(client_level)
        self.log.info('Job ID for Dynamics 365 CRM Backup job: %s', job_id)
        return job_id

    @PageService()
    def initiate_backup(self, content: list = None, is_instance: bool = False):
        """
        Initiates backup for the given Tables

        Args:
            is_instance (bool):     Is the content passed, list of instances
            content:    (list):     LIst of content to be backed up
                If Instances:
                    list of instance
                If Tables
                    List of table tuples
                    Format:
                        [   (table1, instance1), (table2, instance2)    ]

        Returns:
            job_id (str): Job ID of the initiated backup job

        """
        if not content:
            if self.d365tables:
                for table, instance in self.d365tables:
                    self._select_content(content_name=table, is_instance=False, instance_name=instance)
            elif self.instances:
                for instance in self.instances:
                    self._select_content(content_name=instance, is_instance=True)
        else:
            if not is_instance:
                for table, instance in content:
                    self._select_content(content_name=table, is_instance=False, instance_name=instance)
            else:
                for instance in content:
                    self._select_content(content_name=instance, is_instance=True)
        self._click_backup()
        if not self.__is_react:
            self._modal_dialog.click_submit()
        else:
            self._rmodal_dialog.click_submit()
        job_id = self._get_job_id()
        self._admin_console.refresh_page()
        return job_id

    @PageService()
    def is_playback_completed(self):
        """Check if playback was successfully completed."""
        return self._table.get_total_rows_count() > 0

    @WebAction()
    def _get_job_id_from_wizard(self):
        """Get job id from wizard"""
        job_details = self._driver.find_element(By.XPATH, "//div[@role='alert']")
        job_text = job_details.text
        job_text = job_text.split("\n")[0]
        job_text = job_text.split(" ")
        job_id = job_text[2]
        return job_id

    @WebAction(delay=2)
    def _get_job_id(self, client_page: bool = False):
        """Fetches the jobID from the toast"""
        try:
            return self._alert.get_jobid_from_popup(wait_time=2)
        # Sometimes the notification prints: Backup started for clients. View job details
        # This doesn't have a job id and hence it fails here.
        # Following code to handle above case
        except CVWebAutomationException:
            time.sleep(60)
            self._click_view_jobs(client_page=client_page)
            return self._jobs.get_job_ids()[0]

    ##############################
    #   Restore job Page Service  #
    ##############################

    @PageService
    def select_client_restore(self):
        """Clicks the restore from the client page header"""

        self._admin_console.access_menu(self._admin_console.props['action.restore'])
        self._admin_console.wait_for_completion()

    @PageService()
    def run_restore(self, tables: list = None,
                    restore_type: Enum = None,
                    dest_instance: str = str(),
                    record_option: Enum = None,
                    is_instance: bool = False,
                    restore_level: str = None):
        """
        Runs the restore by selecting any particular table configured to the app

        Args:
                is_instance:        If the content to be restored is an instance
                record_option:      Overwrite/ Skip option for records
                    Possible values:
                        constants.RESTORE_RECORD_OPTIONS
                dest_instance:      Destination instance for OOP restore
                restore_type:       Type of restore
                    Possible values:
                        constants.RESTORE_TYPES Enum
                tables:             List of tables to restore   (if any)
                restore_level:      Level of restore to be triggered, None for normal restore (default)

        Returns:
            job_details (dict): Details of the restore job

        """
        self.log.info("Parameters for Restore Job:")
        self.log.info("Tables: {}".format(tables))
        self.log.info("Restore Type: {}".format(restore_type))
        self.log.info("Record Level Option: {}".format(record_option))
        self.log.info("Destination instance: {}".format(dest_instance))
        self.log.info("Restore level : {}".format(restore_level))
        self._admin_console.access_tab(constants.Dynamics365.TABLE_TAB.value)
        if not is_instance:
            if not tables:
                for table, instance in self.d365tables:
                    self._select_content(content_name=table,
                                         is_instance=False,
                                         instance_name=instance)
            else:
                for table, instance in tables:
                    self._select_content(content_name=table,
                                         is_instance=False,
                                         instance_name=instance)
        else:
            if not tables:
                for instance in self.instances:
                    self._select_content(content_name=instance,
                                         is_instance=True)
            else:
                for instance in tables:
                    self._select_content(content_name=instance,
                                         is_instance=True)

        self._click_restore(table=True)
        self._admin_console.wait_for_completion()
        self._enter_details_in_restore_panel(
            restore_type=restore_type,
            destination_instance=dest_instance,
            record_option=record_option,
            restore_level=restore_level)
        self._wizard.click_button(id='Next')
        job_id = self._get_job_id_from_wizard()
        self.log.info('Job ID for Dynamics 365 CRM Restore job: %s', job_id)
        return job_id

    @PageService()
    def run_point_in_time_restore(self, restore_dict: dict = None,
                                  restore_type: Enum = None,
                                  dest_instance: str = str(),
                                  record_option: Enum = None,
                                  is_instance: bool = False,
                                  restore_level: str = None):
        """
            Runs restore at a certain date and time from the calendar

        """
        restore_job_details = None
        time_dict = {
            "day": restore_dict["Date"],
            "month": restore_dict["Month"],
            "year": restore_dict["Year"],
            "time": restore_dict["Start Time"]
        }
        if not restore_dict:
            raise CVWebAutomationException("Pass the PIT restore dictionary")
        else:
            if restore_dict["ClientLevel"]:
                self._admin_console.access_tab("Overview")
            else:
                self._admin_console.access_tab("Content")
                self._rtable.access_link(restore_dict["Entity"])
            calendar_view = RCalendarView(self._admin_console)
            if calendar_view.is_calendar_exists():
                if restore_dict["ClientLevel"]:
                    calendar_view.set_date_and_time(time_dict)
                    self._admin_console.wait_for_completion()
                else:
                    calendar_view.select_date(time_dict)
                    self._admin_console.wait_for_completion()
                self._click_restore_on_calendar()
                self._admin_console.wait_for_completion()
                if restore_dict["ClientLevel"]:
                    self._select_environment_from_browse(environment=restore_dict["Entity"])
                    self._admin_console.wait_for_completion()
                restore_job_details = self._perform_restore_from_browse(restore_type,
                                                                        dest_instance,
                                                                        record_option,
                                                                        restore_level)
            else:
                raise CVWebAutomationException("Calendar is not visible")
        return restore_job_details

    @PageService()
    def compare_versions_of_records(self, association_dict: dict):
        """Compare versions of records in the D365 Tables
            association_dict (dict) -- Should contain the following information about the table records and versions

                association dict -- {
                                        "TableName": "Account",
                                        "EnvironmentName" : "cv-test",
                                        "PrimaryColumnValue" : "Row value of the primary column",
                                        "CompareVersions" : ["1.0","2.0"]
                                    }
        """
        self._admin_console.access_tab("Tables")
        self._admin_console.wait_for_completion()
       
  
        self._rtable.select_rows([association_dict["TableName"]])
        self._click_restore(table=False)
        self._admin_console.wait_for_completion()
        record_dict = {
            "RecordName": association_dict["PrimaryColumnValue"],
            "Versions": association_dict["CompareVersions"]
        }
        comparison_dict = self._compare_records(record_dict)
        return comparison_dict

    @PageService()
    def download_properties(self, primary_row_value: str):
        """Download properties of the primary row"""

        browse_table = Rtable(self._admin_console, id="dynamics365BrowseGrid")
        browse_table.access_action_item(entity_name=primary_row_value, action_item="Download")
        time.sleep(20)
        machine = Machine()
        file_name = "{}.json".format(primary_row_value)
        AUTOMATION_DIRECTORY = AutomationUtils.constants.AUTOMATION_DIRECTORY
        downloaded_folder_path = os.path.join(AUTOMATION_DIRECTORY, 'Temp')
        file_path = os.path.join(downloaded_folder_path, file_name)
        if machine.check_file_exists(file_path) and int(machine.get_file_size(file_path, in_bytes=True)) > 0:
            self.log.info("File downloaded successfully")
            machine.delete_file(file_path)
        else:
            raise CVWebAutomationException("Properties files not downloaded please check")

    @PageService()
    def restore_table_attributes(self):
        """Restore changed attributes of the table from the Comparisons Panel"""
        compare_table = Rtable(self._admin_console, xpath='//div[@aria-labelledby="customized-dialog-title"]'
                                                          '//div[contains(@class,"grid-holder")]')
        compare_table.select_all_rows()
        compare_table.access_toolbar_menu("Restore")
        self._click_restore_from_compare()
        self._wizard.click_next()
        self._wizard.select_radio_button("Unconditionally overwrite")
        self._wizard.click_next()
        self._wizard.click_button("Submit")
        self._admin_console.wait_for_completion()
        job_id = self._wizard.get_job_id()
        self._wizard.click_button(id="Submit")
        return job_id

    @PageService()
    def compare_table_attributes_with_live_data(self, table_name : str, older_record: Record, primary_attribute: str):
        """
            Compare the attributes of the table with the Live Data
            table_name (str) -- Name of the table
            older_record (Record) -- Older record
            primary_attribute (str) -- Primary attribute to search for in the Browse
        """
        self._admin_console.access_tab("Tables")
        self._admin_console.wait_for_completion()
        self._rtable.select_rows(names=[table_name], search_for=True)
        self._click_restore(table=False)
        self._admin_console.wait_for_completion()
        row_name = older_record.record_data.get(primary_attribute)
        self._click_browse_filter()
        self._apply_browse_filter(D365FilterType.ROW, row_name)
        self._rtable.access_action_item(row_name, "Compare")
        compare_data = self._compare_record_with_live_data(older_record)
        modified_dict = {}
        for key in compare_data.keys():
            if "Backup as" in key:
                modified_dict.update({"Backup": compare_data.get(key)})
            elif "Live data" in key:
                modified_dict.update({"Live Data": compare_data.get(key)})
            else:
                modified_dict.update({key: compare_data.get(key)})
        compare_dict = {
            'LiveVersion': dict(zip(modified_dict['Attribute'], modified_dict['Live Data'])),
            'OldVersion': dict(zip(modified_dict['Attribute'], modified_dict['Backup']))
        }
        return compare_dict






