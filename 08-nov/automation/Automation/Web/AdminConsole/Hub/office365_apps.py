# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
testcases of Office365 module for Hub.

To begin, create an instance of Office365Apps for test case.

To initialize the instance, pass the testcase object to the Office365Apps class.

Call the required definition using the instance object.

This file consists of only one class Office365Apps.

Office365Apps:

    create_office365_app()                  --      Creates O365 App

    create_office365_app_syntex()           --      Creates O365 Syntex App

    get_app_name()                          --      Gets the app name from the app page. Useful for Metallic app

    get_plans_list()                        --      Gets the list of available plans

    get_retention_period()                  --      Returns retention period of the o365 plan

    get_converted_retention_period()        --      Converts the retention period to no of days format and returns it

    verify_retention_of_o365_plans()        --      Verifies retention for o365 plans

    access_office365_app()                  --      Accesses the Office365 app from the Office365 landing page

    verify_added_user_groups()              --      Verifies the groups added to the app

    create_o365_plan()                      --      Creates an o365 plan

    add_user_group()                        --      Adds user/sharepoint/teams/mailboxes groups to the app

    remove_user_group()                     --      Removes the specified user/sharepoint/teams/mailboxes group from the app

    add_service_acc_custom()                --      Adds service account details in configuration page using the Custom config option

    add_user()                              --      Adds users to the office 365 app

    add_teams()                             --      Adds teams to the office 365 Teams App.

    verify_status_tab_stats()               --      Verifies status tab stats in job details page

    run_backup()                            --      Runs backup by selecting all the associated users to the app

    run_restore()                           --      Runs the restore by selecting all users associated to the app

    delete_office365_app()                  --      Deletes the office365 app

    fetch_exchange_overview_details()       --      Fetch the overview tab details for the tab

    browse_entity()                         --      Browse the Mailbox/User for exchange or OneDrive

    get_browse_page_details()               --      Get the browse page details

    refresh_cache()                         --      Runs manual discovery to the office 365 app

    add_custom_category()                   --      Add custom category to the office 365 app

    enable_user_chat()                      --      Enables user chat to the office 365 app

    mark_export_api_yes_for_teams_app()     --      It will mark atleast one azure app as export yes

    add_azure_app_via_express_configuration() --    Adds azure app via express configuration

    delete_backup_data()                    --      Performs command center delete operation

    access_folder_in_browse                 --      To access data inside a folder in browse

    perform_point_in_time_restore()         --      Performs point in time restore at the client level and entity level for a client

    process_streams_tab()                   --      process streams tab in job details page

    edit_streams()                          --      edits the max streams in configuration page

    get_rows_from_browse()                  --      navigates to browse and return rows count

    start_backup_job()                      --      starts backup by selecting all the associated users to the app and returns job id

    start_restore_job()                     --      Starts the restore by selecting all users associated to the app and returns job id

    click_agent_overview_for_backup_size()  --      Clicks the agent backup size to display the active, inactive and total size

    change_capacity_usage()                 --      Changes the capacity usage to all backup version if it is latest and vice-versa

    fetch_agent_active_inactive_capacity()  --      Fetches the active, inactive and total capacity for one agent

    get_compliance_search_count()           --      Get number of results in compliance search page

    select_restore_options()                --      Select the operation for restore

    disable_backup()                        --      Disable the backup for the client

    enable_backup()                         --      Enable the backup for the client

    get_discovery_status_count()            --      Get the count of mailboxes as per discovery type

    get_audit_trail_data()                  --      Get the data from audit trail table

    _get_app_stat()                         --      Gets the stats from the app page

    get_app_stat ()                           --      Get App stats from app page

"""

import time
import re
import os.path
from selenium.webdriver.common.by import By
from AutomationUtils.commonutils import get_job_starting_time
from AutomationUtils.machine import Machine
import AutomationUtils.constants
from Automation.Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.Components.cventities import CVActionsToolbar
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.core import SearchFilter
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.alert import Alert
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, ElementNotInteractableException
from selenium.webdriver.common.keys import Keys
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from Web.AdminConsole.Components.dialog import ModalDialog, RModalDialog
from Web.AdminConsole.Components.panel import DropDown, ModalPanel, PanelInfo, RPanelInfo
from Web.AdminConsole.Components.table import Table, Rtable, Rfilter, ContainerTable
from Web.AdminConsole.Components.core import RCalendarView, TreeView
from Web.AdminConsole.Hub.constants import O365AppTypes
from Web.AdminConsole.Office365Pages import constants
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import WebAction, PageService
from Web.AdminConsole.Components.browse import Browse


class Office365Apps:

    def __init__(self, admin_console, app_type, is_react=False):
        """Init function for the metallic hub"""
        self.__admin_console = admin_console
        self.__driver = self.__admin_console.driver
        self.log = self.__admin_console.log
        self.is_react = is_react
        self.app_type = app_type
        self.search_filter = SearchFilter(admin_console)
        self.__table = Table(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)
        self.__container_table = ContainerTable(self.__admin_console)
        self.__rmodal_dialog = RModalDialog(self.__admin_console)
        self.__dropdown = DropDown(self.__admin_console)
        self.__jobs = Jobs(self.__admin_console)
        self._alert = Alert(self.__admin_console)
        self.__modal_dialog = ModalDialog(self.__admin_console)
        self.__modal_panel = ModalPanel(self.__admin_console)
        self.__panelInfo_obj = PanelInfo(self.__admin_console)
        self.__RpanelInfo_obj = RPanelInfo(self.__admin_console)
        self.__Browse_obj = Browse(self.__admin_console, is_new_o365_browse=True)
        self.__RCalendarView_obj = RCalendarView(self.__admin_console)
        self.__admin_console.load_properties(self)
        self.__navigator = self.__admin_console.navigator
        self.__cvactions_toolbar = CVActionsToolbar(self.__admin_console)
        self.__wizard = Wizard(self.__admin_console)
        self.__treeview = TreeView(self.__admin_console)
        self.check_file_location_restore = None
        self.o365_plan = None
        self.app_details = None
        self.app_name = None
        self.groups = None
        if self.app_type == O365AppTypes.exchange:
            self.constants = constants.ExchangeOnline
        elif self.app_type == O365AppTypes.onedrive:
            self.constants = constants.OneDrive
        elif self.app_type == O365AppTypes.sharepoint:
            self.constants = constants.SharePointOnline
        elif self.app_type == O365AppTypes.teams:
            self.constants = constants.Teams

    @WebAction()
    def __click_button_if_present(self, value):
        """
            Clicks the button with specified name if present
        """
        if self.__admin_console.check_if_entity_exists('xpath', f"//button[contains(.,'{value}')]"):
            self.__admin_console.click_button(value)

    @WebAction()
    def __is_multi_tenant_enabled(self):
        """
            Method to check if the multi tenant configuration is enabled on the CS/ Command Center

            Returns:
                multi_tenant_enabled        (bool)--    Whether multi tenant configuration is enabled on the CS
        """
        _sign_in_msft_button_xpath = "//div[@id = 'id-o365-sign-in-with-msft-onboarding']//*[name() = 'svg']"
        return self.__admin_console.check_if_entity_exists(entity_name="xpath", entity_value=_sign_in_msft_button_xpath)

    @WebAction()
    def __click_sign_in_with_msft_button(self):
        """
            Method to select on the Sign in with Microsoft button
        """
        _sign_in_msft_button_xpath = "//div[@id = 'id-o365-sign-in-with-msft-onboarding']//*[name() = 'svg']"
        self.__driver.find_element(By.XPATH, _sign_in_msft_button_xpath).click()

    @WebAction(delay=2)
    def __check_multi_tenant_form_displayed(self):
        """
            Method to check if the multi tenant form/ modal is visible

            Returns:
                form_displayed          (bool)--    Multi Tenant app configuration form displayed or now
        """
        _multi_tenant_form_xpath = "//div[@aria-labelledby = 'customized-dialog-title' ]"
        return self.__driver.find_element(By.XPATH, _multi_tenant_form_xpath).is_displayed()

    @WebAction()
    def _fetch_and_parse_multi_tenant_dialog_details(self):
        """
            Method to fetch and parse the test details from the multi tenant app config modal dialog

            Returns:
                _dialog_details         (list)--        List element for the test fetched from the multi tenant dialog
        """
        _dialog_details = self.__driver.find_element(By.XPATH,
                                                     "//div[contains(@class,'MuiGrid-container') and @justify='center']").text.split(
            "\n")

        return _dialog_details

    @WebAction()
    def _get_message_text(self):
        """
            Gets the message text from the dialog
        """
        _message_text_box_xpath = "//div[@aria-labelledby='customized-dialog-title']//div[contains(@class, 'MuiAlert-message')]"
        element = self.__driver.find_element(By.XPATH, _message_text_box_xpath)
        return element.text

    @WebAction()
    def __wait_app_authorization_redirect(self):
        """
            Method to wait for the command center to redirect to the MSFT login page for
            Azure app Authorization
        """
        count = 1
        while count < 3:
            if len(self.__driver.window_handles) > 1:
                return True
            else:
                time.sleep(3)
                count = count + 1
                self.__driver.find_element(By.LINK_TEXT, 'here').click()

        if count == 3:
            raise CVWebAutomationException("Unable to open the MSFT login page for Azure app authorization")

    @WebAction(delay=3)
    def __check_error_multi_tenant_config(self):
        """
            Method to check if there was any error in configuring the multi tenant app
        """
        _failure_xpath = "//div[contains(@class,'MuiGrid-root')]//*[name()='svg']//*[name()='g' and @clip-path='url(#Failed_svg__a)']"
        if self.__admin_console.check_if_entity_exists(entity_name="xpath", entity_value=_failure_xpath):
            _error_message = self._get_message_text()
            self.log.info("Op Failed with the error: {}".format(_error_message))
            raise CVWebAutomationException("Unable to configure the multi tenant Azure app")

    @WebAction(delay=3)
    def __check_multi_tenant_config_success(self):
        """
            Method to check if the configuration for the multi tenant app was successful
        """
        count: int = 1
        _in_progress_xpath = "//div[contains(@class,'MuiGrid-root')]//div[@id='spinner']"
        _success_xpath = "//div[contains(@class,'MuiGrid-root')]//*[name()='svg']//*[name()='g' and @clip-path='url(#Success_svg__a)']"
        _failure_xpath = "//div[contains(@class,'MuiGrid-root')]//*[name()='svg']//*[name()='g' and @clip-path='url(#Failed_svg__a)']"

        while count < 3:
            _app_details_status = self._fetch_and_parse_multi_tenant_dialog_details()
            if self.__admin_console.check_if_entity_exists(entity_name="xpath", entity_value=_in_progress_xpath):
                self.log.info("Corresponding action is in progress...")
                time.sleep(15)
                count = count + 1

            if self.__admin_console.check_if_entity_exists(entity_name="xpath", entity_value=_success_xpath):
                self.log.info("Multi tenant App configuration was successful")
                return True

            if count == 3:
                self.log.info("Timeout in configuring the multi tenant App")
                raise CVWebAutomationException("App configuration was unsuccessful")

            if self.__admin_console.check_if_entity_exists(entity_name="xpath", entity_value=_failure_xpath):
                _error_message = self._get_message_text()
                self.log.info("Op Failed with the error: {}".format(_error_message))
                raise CVWebAutomationException("Unable to configure the multi tenant Azure app")

    @WebAction()
    def __authorize_multi_tenant_app(self, global_admin_address: str, global_admin_passwd: str):
        """
            Method to Authorize the Multi Tenant Azure App

            Arguments:
                global_admin_passwd         (str)--     Password for the Azure global admin account
                global_admin_address        (str)--     Email address for the Azure global admin account
        """
        self.log.info("Starting Multi tenant Azure app Authorization...")
        self.__wait_app_authorization_redirect()
        self.__authorize_permissions(global_admin=global_admin_address,
                                     password=global_admin_passwd)
        self.__admin_console.wait_for_completion()
        self.__check_error_multi_tenant_config()
        self.log.info("Multi tenant Azure app Authorized...")

    @WebAction()
    def __configure_with_multi_tenant_app(self, global_admin_address: str, global_admin_passwd: str):
        """
            Method to configure the Multi Tenant Azure app with the Office 365 client
        """
        self.__click_sign_in_with_msft_button()
        self.__admin_console.wait_for_completion()
        current_window_handles = self.__driver.window_handles
        app_window = None
        azure_window = None
        if len(current_window_handles) >= 2:
            app_window = current_window_handles[0]
            azure_window = current_window_handles[1]
            self.__driver.switch_to.window(app_window)
        if not self.__check_multi_tenant_form_displayed():
            raise CVWebAutomationException("Azure Multi Tenant Authentication Model was not loaded")
        self.__admin_console.wait_for_completion()
        self.__check_error_multi_tenant_config()
        self.__authorize_multi_tenant_app(global_admin_address=global_admin_address,
                                          global_admin_passwd=global_admin_passwd)
        self.__admin_console.wait_for_completion()
        if not self.__check_multi_tenant_config_success():
            raise CVWebAutomationException("Multi tenant Azure app configuration was unsuccessful")
        self.__admin_console.click_button(self.__admin_console.props['label.action.close'])

    @WebAction()
    def __check_for_errors(self):
        """Checks for any errors while creating app"""
        error_xpaths = [
            "//div[@class='help-block']",
            "//div[@ng-bind='addOffice365.appCreationErrorResponse']"
        ]

        for xpath in error_xpaths:
            if self.__admin_console.check_if_entity_exists('xpath', xpath):
                if self.__driver.find_element(By.XPATH, xpath).text:
                    raise CVWebAutomationException(
                        'Error while creating the app: %s' %
                        self.__driver.find_element(By.XPATH, xpath).text
                    )

    @WebAction(delay=2)
    def __click_create_azure_ad_app(self):
        """Clicks create azure ad app button"""
        create_azure_ad_app_xpath = "//button[@id='createOffice365App_button_#6055']"
        self.__driver.find_element(By.XPATH, create_azure_ad_app_xpath).click()
        self.__check_for_errors()

    @WebAction(delay=2)
    def __click_show_details(self):
        """Clicks the Show details link for Azure App"""
        if self.__admin_console.check_if_entity_exists("link", self.__admin_console.props['label.showDetails']):
            self.__admin_console.select_hyperlink(self.__admin_console.props['label.showDetails'])

    @WebAction(delay=3)
    def __click_authorize_now(self):
        """Clicks on authorize now button"""
        self.__admin_console.select_hyperlink("here")

    @WebAction(delay=3)
    def __switch_to_window(self, window):
        """Switch to specified window

                Args:
                    window (WebElement)  -- Window element to switch to
        """
        self.__driver.switch_to.window(window)

    @WebAction(delay=3)
    def __click_submit(self):
        """Click submit type button"""
        # This xpath is used to click submit button on Microsoft login pop up window
        ms_submit_xpath = "//input[@type='submit']"
        self.__admin_console.scroll_into_view(ms_submit_xpath)
        self.__driver.find_element(By.XPATH, ms_submit_xpath).click()

    @WebAction(delay=2)
    def __enter_email(self, email):
        """Enter email in email type input

                Args:
                    email (str)  --  Microsoft Global Admin email
        """
        if self.__admin_console.check_if_entity_exists('id', 'i0116'):
            self.__admin_console.fill_form_by_id('i0116', email)
            self.__click_submit()
        elif self.__admin_console.check_if_entity_exists('id', 'otherTileText'):
            self.__driver.find_element(By.ID, "otherTileText").click()
            self.__enter_email(email)

    @WebAction(delay=2)
    def __enter_password(self, password):
        """Enter password into password type input

                Args:
                    password (str)  --  Global Admin password
        """
        if self.__admin_console.check_if_entity_exists('id', 'i0118'):
            self.__admin_console.fill_form_by_id('i0118', password)
            self.__click_submit()

    @WebAction(delay=2)
    def __get_new_app_name(self):
        """Fetches the newly created Azure app name from MS permission dialog"""
        return self.__driver.find_element(By.XPATH, "//div[@class='row app-name']").text

    @WebAction(delay=2)
    def __get_id_and_xml_text(self):
        """Gets the sharepoint app id, tenant id and request xml"""
        if self.is_react:
            sharepoint_app_id = self.__driver.find_element(
                By.XPATH, "//p[contains(text(), 'Copy the App ID')]/following-sibling::p").text
            sharepoint_tenant_id = self.__driver.find_element(
                By.XPATH, "//p[contains(text(), 'Copy the tenant ID')]/following-sibling::p").text
            sharepoint_request_xml = self.__driver.find_element(By.XPATH, "//div/code").text
        else:
            sharepoint_app_id = self.__driver.find_element(By.XPATH,
                                                           "//code[@data-ng-bind='o365SPCreateAppPrincipleCtrl.azureAppDetails.azureAppId']").text
            sharepoint_tenant_id = self.__driver.find_element(By.XPATH,
                                                              "//code[@data-ng-bind='o365SPCreateAppPrincipleCtrl.azureAppDetails.azureDirectoryId']").text
            sharepoint_request_xml = self.__driver.find_element(By.XPATH,
                                                                "//code[@data-ng-bind='o365SPCreateAppPrincipleCtrl.appPrincipleXML']").text
        return sharepoint_app_id, sharepoint_tenant_id, sharepoint_request_xml

    @WebAction()
    def __grant_sharepoint_permissions(self):
        """Clicks on the link given to grant sharepoint permissions"""
        self.__driver.find_element(By.XPATH, ".//a[contains(@href, '_layouts/15/appinv.aspx')]").click()

    @WebAction(delay=2)
    def __enter_app_id_and_lookup(self, sharepoint_app_id):
        """Enters the app id in the textbox and clicks on lookup

            Args:
                sharepoint_app_id (str) :   SharePoint App Id

        """
        self.__driver.find_element(By.XPATH, "//input[contains(@id, 'TxtAppId')]").send_keys(sharepoint_app_id)
        self.__driver.find_element(By.XPATH, "//input[ @value = 'Lookup']").click()

    @WebAction(delay=2)
    def __enter_details_and_create(self, sharepoint_tenant_id, sharepoint_request_xml):
        """Enters the rest of the details and clicks on create

            Args:
                sharepoint_tenant_id (str)  :   SharePoint Tenant Id
                sharepoint_request_xml(str) :   SharePoint Request XML

        """
        self.__driver.find_element(By.XPATH, "//input[@title = 'App Domain']").send_keys(sharepoint_tenant_id)
        self.__driver.find_element(By.XPATH, "//textarea[@title = 'Permission Request XML']").send_keys(
            sharepoint_request_xml)
        self.__driver.find_element(By.XPATH, "//input[ @value = 'Create']").click()

    @WebAction(delay=2)
    def __click_trust_it(self):
        """Clicks on the Trust It button"""
        self.__driver.find_element(By.XPATH, "//input[ @value = 'Trust It']").click()

    @WebAction(delay=2)
    def __close_current_tab(self):
        """
        To close the current tab
        """
        self.__driver.close()

    @WebAction()
    def search_recovery_point_mailbox(self, mailbox):
        """Clicks the search box for recovery point mailbox selection
                Args : the mailbox that needs to be searched
        """
        search_box = self.__driver.find_element(By.XPATH,
                                                "//form[@id='exchangeMBListTableForm']//input[@data-testid='grid-search-input']")
        search_box.click()
        self.__admin_console.wait_for_completion()
        search_box.clear()
        search_box.send_keys(mailbox)

    @WebAction(delay=2)
    def __verify_sharepoint_service_account(self):
        """Verify if one sharepoint service account is created"""
        try:
            sp_service_acc_xpath = ("//span[@ng-bind='addOffice365.office365Attributes"
                                    ".generalAttributes.sharepointOnlineServiceAccount']")
            text = self.__driver.find_element(By.XPATH, sp_service_acc_xpath).text
            if "CVSPBackupAccount" in text:
                self.log.info('Sharepoint Service account created from web server:%s', text)
        except:
            raise CVWebAutomationException("Service account not created for SharePoint Online from web server")

    @WebAction(delay=2)
    def __verify_sharepoint_modern_authentication(self):
        """Verifies if SharePoint online app is created using modern authentication enabled."""
        try:
            sp_modern_xpath = ("//div[contains(@data-ng-if, "
                               "'addOffice365.office365Attributes.sharepointAttributes."
                               "sharepointBackupSet.spOffice365BackupSetProp.isModernAuthEnabled')]")
            text = self.__driver.find_element(By.XPATH, sp_modern_xpath).text
            if "Using modern authentication" in text:
                self.modern_authentication = True
                self.log.info('Modern authentication is enabled on the tenant and app is created with mod auth')
        except:
            self.log.info('Modern authentication is not enabled on the tenant and app is created with basic auth')
            self.modern_authentication = False

    @WebAction(delay=2)
    def __verify_app_principal(self):
        """Verify if one sharepoint app principal is authorized"""
        try:
            app_principal_xpath = "//div[@data-ng-if='addOffice365.isAzureAppPrincipleCreated']"
            text = self.__driver.find_element(By.XPATH, app_principal_xpath).text
            if "App principal created" in text:
                self.log.info('For SharePoint Online:%s', text)
        except:
            raise CVWebAutomationException("App principal not created for sharepoint online")

    @WebAction(delay=2)
    def __select_page_of_entities(self):
        """Selects all items in the page"""
        self.__driver.find_element(By.XPATH, "//th[@id='cv-k-grid-th-:checkbox']").click()
        self.__driver.find_element(By.XPATH, "//span[text()='Select page']").click()

    @WebAction(delay=2)
    def __select_all_entities(self):
        """Selects all pages across the table"""
        if self.is_react:
            self.__rtable.select_all_rows()
        else:
            self.__driver.find_element_by_xpath("//th[@id='cv-k-grid-th-:checkbox']").click()
            if self.__admin_console.check_if_entity_exists("xpath", "//span[text()='Select all pages']"):
                self.__driver.find_element_by_xpath("//span[text()='Select all pages']").click()

    @WebAction(delay=2)
    def __select_entity(self, entities):
        """Selects given entities
            entities(list): Name of entities to select
        """
        self.__rtable.select_rows(entities, True)

    @WebAction(delay=2)
    def __deselect_all_entities(self):
        """Deselects all items in the table"""
        self.__driver.find_element(By.XPATH, "//th[@id='cv-k-grid-th-:checkbox']").click()
        if self.__admin_console.check_if_entity_exists("xpath", "//span[text()='None']"):
            self.__driver.find_element(By.XPATH, "//span[text()='None']").click()

    @WebAction(delay=2)
    def __get_app_name(self):
        """Gets the app name from the app page. Useful for Metallic app"""
        if self.is_react:
            return self.__driver.find_element(By.XPATH, "//span[@class='title-display']").text
        else:
            return self.__driver.find_element(By.XPATH, "//div[@id='cv-changename']//h1").text

    @WebAction(delay=2)
    def __open_add_user_panel(self):
        """Opens the panel to add users to the client"""
        self.__driver.find_element(By.ID, self.constants.ADD_BUTTON_ID.value).click()
        time.sleep(3)
        self.__driver.find_element(By.ID, self.constants.ADD_USER_BUTTON_ID.value).click()

    @WebAction(delay=2)
    def __job_details(self):
        """Waits for job completion and gets the job details"""
        try:
            job_id = self._alert.get_jobid_from_popup(wait_time=5)
        except CVWebAutomationException:
            self.__driver.find_element(By.XPATH, "//div[@aria-label='More' and @class='popup']").click()
            self.__admin_console.click_button("View jobs")
            self.__jobs.access_active_jobs()
            job_id = self.__jobs.get_job_ids()[0]
        if self.app_type == O365AppTypes.sharepoint or self.app_type == O365AppTypes.exchange:
            self.__jobs.job_completion(job_id=job_id, skip_job_details=True)
            # Waiting for all job details to get updated on job page
            time.sleep(60)
            job_details = self.__get_job_details(job_id)
        else:
            job_details = self.__jobs.job_completion(job_id=job_id)
        job_details['Job Id'] = job_id
        self.log.info('job details: %s', job_details)
        # job_details[self.__admin_console.props['Status']]
        if (job_details[self.__admin_console.props['Status']] not in [
            "Committed", "Completed", "Completed w/ one or more errors"]):
            raise CVWebAutomationException('Job did not complete successfully')
        return job_details

    @WebAction(delay=2)
    def __click_backup(self):
        """Clicks the backup button on the app page"""
        if self.is_react:
            self.__driver.find_element(By.ID, "BACKUP").click()
        else:
            if self.app_type == O365AppTypes.exchange:
                self.__table.access_toolbar_menu(self.constants.METALLIC_BACKUP_MENU_ID.value)
            else:
                self.__table.access_toolbar_menu(self.constants.BACKUP_MENU_ID.value)

    @WebAction(delay=2)
    def __click_restore(self, recovery_point=False):
        """Clicks the browse button on the app page"""
        if self.is_react:
            self.__rtable.access_toolbar_menu("Restore")
            if recovery_point:
                self.__driver.find_element(By.XPATH, self.constants.ACCOUNT_RECOVERY_XPATH.value).click()
            else:
                self.__driver.find_element(By.XPATH,"//li[@id='RESTORE_ENTIRE_CONTENT']").click()
        else:
            self.__driver.find_element_by_id(self.constants.CLICK_RESTORE_ID.value).click()
            if recovery_point:
                self.__driver.find_element(By.XPATH, self.constants.ACCOUNT_RECOVERY_XPATH.value).click()
            else:
                self.__driver.find_element(By.XPATH, self.constants.ACCOUNT_RESTORE_XPATH.value).click()

    @WebAction()
    def __click_recovery_point_browse(self):
        """CLick the browse button on recovery point creation page"""
        self.__driver.find_element(By.XPATH, "//button[@title='Browse']").click()

    @WebAction(delay=2)
    def click_restore_page_action(self):
        """Clicks the restore button on the app page"""
        self.__driver.find_element(By.ID, self.constants.RESTORE_PAGE_OPTION.value).click()
        self.__admin_console.wait_for_completion()

    @WebAction(delay=2)
    def __apply_filter_to_search_in_browse(self, filter_placeholder_value, item, is_dropdown=False,
                                           dropdown_label="Type", dropdown_value=None):
        """Applies filter to search for Team/Mailbox/Sharepoint site/OneDrive user
            filter_placeholder_value (str) -- Placeholder value of filter
            items                    (str) -- Item name to filter : Team/Mailbox/Sharepoint site/OneDrive user
            is_dropdown              (bool)-- Set if need to select Type from dropdown
                Default: False
            dropdown_label          (str) -- If dropdown is set, then the item-label of dropdown
            dropdown_value          (str) -- If dropdown is set, then the value of dropdown menu to select
        """
        self.search_filter.click_filter()
        if is_dropdown:
            self.search_filter.select_dropdown_value(dropdown_label, dropdown_value)
        self.search_filter.apply_input_type_filter(filter_placeholder_value, item)
        self.search_filter.submit()
        self.__admin_console.wait_for_completion()
    
    @WebAction(delay=2)
    def delete_item_in_browse(self, items):
        """Searches and deletes the items in browse page
            items   (list) -- List of items to delete - Mailbox, Team, SharePoint Sites, Onedrive User
        """
        for item in items:
            if self.app_type == O365AppTypes.teams:
                self.__apply_filter_to_search_in_browse("Contains", item, True, "Type", "Team")
            elif self.app_type == O365AppTypes.exchange:
                self.search_filter.click_filter()
                self.search_filter.apply_input_type_filter('Mailboxes separated by semicolon', item)
                self.search_filter.submit()
            self.__rtable.select_rows([item])
            self._click_delete_and_confirm()
            job_details = self.__job_details()
            return job_details

    @WebAction()
    def _click_delete_and_confirm(self):
        """Clicks delete button and submits delete"""
        self.__driver.find_element(By.XPATH, "//button[@id='DELETE_BACKUP_DATA']").click()
        self.__admin_console.wait_for_completion()
        self.__driver.find_element(By.XPATH, "//input[@id='notifyPlaceHolder']").send_keys("AUTOMATION")
        self.__driver.find_element(By.XPATH, "//button[@id='Save' and @aria-label='Delete']").click()
        self.__admin_console.wait_for_completion()
        self.__driver.find_element(By.XPATH, "//input[@id='confirmText']").send_keys("DELETE")
        self.__driver.find_element(By.XPATH, "//button[@id='Save' and @aria-label='Submit']").click()

    @WebAction(delay=2)
    def validate_delete_item_in_browse(self, items):
        """Validate if the data has been deleted from browse
            items   (list) -- List of items to validate - Mailbox, Team, SharePoint Sites, Onedrive User
        """
        for item in items:
            self.search_filter.click_filter()
            if self.app_type == O365AppTypes.teams:
                self.__apply_filter_to_search_in_browse("Item name", item, True, "searchType", "Team")
            elif self.app_type == O365AppTypes.exchange:
                self.search_filter.apply_input_type_filter('Mailboxes separated by semicolon', item)
            search_x_path = f"//div[contains(@class,'cv-kendo-grid')]//*[contains(text(), '{item}')]" \
                            f"/ancestor::tr//input[@type='checkbox']/ancestor::td"
            elem_presence = len(self.__driver.find_elements(By.XPATH, search_x_path)) > 0
            if elem_presence:
                raise CVWebAutomationException(f"Deletion of item: {item} failed.")

    @WebAction(delay=2)
    def __click_app_restore(self):
        """Clicks the restore button on the app page"""
        self.__driver.find_element(By.XPATH,"//button[@id='APP_LEVEL_RESTORE']").click()
        self.__admin_console.wait_for_completion()

    @WebAction(delay=2)
    def __click_browse(self):
        """Clicks the browse button on the app page"""
        self.__rtable.access_toolbar_menu("Restore")
        self.__driver.find_element(By.XPATH, self.constants.REACT_BROWSE_RESTORE_XPATH.value).click()

    @WebAction(delay=2)
    def __expand_restore_options(self):
        """Expands restore options"""
        if self.is_react:
            if self.app_type == O365AppTypes.exchange:
                self.__driver.find_element(By.XPATH, f"//div[@accordion-label='{self.__admin_console.props['header.messagelevel.options']}']").click()
            else:
                self.__driver.find_element(By.XPATH, f"//span[text()='{self.__admin_console.props['header.filelevel.options']}']").click()
        else:
            self.__driver.find_element_by_xpath(
                f"//span[normalize-space()='{self.__admin_console.props['header.messagelevel.options']}'"
                f" or normalize-space()='{self.__admin_console.props['header.filelevel.options']}']"
            ).click()

    @WebAction(delay=2)
    def __click_overwrite_radio_button(self):
        """Clicks the radio button for unconditionally overwrite"""
        if self.is_react:
            self.__driver.find_element(By.XPATH, "//input[@value='OVERWRITE'] | "
                                                 "//input[@id='whenDocExistsOverwrite']").click()
        else:
            self.__driver.find_element_by_xpath(
                f'//input[@type="radio" and @value="{self.constants.RADIO_BUTTON_OVERWRITE.value}"]'
            ).click()

    @WebAction()
    def __access_job_site_status_tab(self):
        """Access the site status tab in job details page"""
        self.__driver.find_element(By.XPATH,
            f"//span[normalize-space()='Site status']").click()

    @WebAction()
    def __get_status_tab_stats(self):
        """Returns the stats of status tab in job details page"""
        if self.__admin_console.check_if_entity_exists("id", "office365UserStats"):
            return self.__driver.find_element(By.ID, 'office365UserStats').text + " "
        else:
            stat_xpaths = "//div[@class='kpi-category']/span/span"
            stat_text = ""
            for element in self.__driver.find_elements(By.XPATH, stat_xpaths):
                stat_text = stat_text + element.text
            return stat_text + " "

    @WebAction()
    def __click_last_discover_cache_update_time(self):
        """Clicks last discover cache time"""
        self.__driver.find_element(By.XPATH, self.constants.LAST_DISCOVERY_CACHE_UPDATE_TIME.value).click()

    @WebAction()
    def __get_last_discover_cache_update_time(self):
        """Returns last discover cache time available or not"""
        return self.__driver.find_element(By.XPATH, self.constants.LAST_DISCOVERY_CACHE_UPDATE_TIME.value).text

    @WebAction()
    def __click_refresh_cache(self):
        """Clicks refresh cache button on discovery dialog"""
        self.__driver.find_element(By.XPATH, "//button[@aria-label='Refresh cache']").click()

    @WebAction(delay=2)
    def __close_current_tab(self):
        """
        To close the current tab
        """
        self.__driver.close()

    @WebAction()
    def __click_export(self):
        """Clicks the export button for the user"""
        self.__driver.find_element(By.XPATH, "//button[@id='CREATE_EXPORT']").click()

    @WebAction()
    def __click_mailbox(self):
        """Clicks the mailbox on the browse page"""
        self.__driver.find_element(By.XPATH,
                                   "//td[contains(@role,'gridcell')]//span[contains(text(),'.com')]").click()

    @WebAction()
    def __redirect_to_plans(self):
        """Clicks on plans breadcrumb"""
        self.__driver.find_element(By.LINK_TEXT, self.__admin_console.props['label.nav.profile']).click()

    @WebAction()
    def __click_row_hyperlink(self, link_text):
        """Clicks hyperlink of the row in the given react table
            Args:
                link_text       (str)       :       Link name as displayed in the webpage.
        """
        x_path = f'//a[contains(text(),"{link_text}")]'
        self.__driver.find_element(By.XPATH, x_path).click()

    @WebAction()
    def __get_export_file_download_status(self):
        """Fetches the download status from the status column of export file table"""
        element = self.__driver.find_element(By.XPATH, "//div[@class='download-status']//span")
        return element.get_attribute('title')

    @WebAction()
    def __get_export_file_type(self):
        """Fetches the export file type form the File Type column of export file table"""
        element = self.__driver.find_element(By.XPATH, "//td[@id='cv-k-grid-td-fileType']/span")
        return element.get_attribute('title')

    @WebAction()
    def __get_backup_stats(self):
        """Fetches the backup stats from the client"""
        backup_stats = dict()
        tags_xpath = "//span[text()='Backup stats']/ancestor::div[contains(@class,'MuiCardHeader-root')]/following-sibling::div//div[@class='kpi-item']/h4"
        tags = self.__driver.find_elements(By.XPATH, tags_xpath)
        values_xpath = "//div[@class='kpi-item']/h4[text()='{}']/following-sibling::h5"
        for tag in tags:
            value = self.__driver.find_element(By.XPATH, values_xpath.format(tag.text)).text
            backup_stats.update({tag.text: value})
        return backup_stats

    @WebAction()
    def __close_backup_demo_popup(self):
        """Close Congratulations about to do 1st backup which appears after 1st content association"""
        if self.__admin_console.check_if_entity_exists("xpath", "//div[@id='pendo-guide-container']"):
            self.__driver.find_element_by_xpath(
                "//button[contains(@id, 'pendo-button') and contains(text(), 'Close')]").click()

    @WebAction()
    def __select_backup_service(self):
        """Select the backup service from the wizard if prompted"""
        if self.__admin_console.check_if_entity_exists("xpath", "//div[@id='Card_COMMVAULT_CLOUD']"):
            self.__wizard.select_card('Commvault Cloud Backup & Recovery for Microsoft 365')
            self.__wizard.click_next()

    @WebAction()
    def __select_agent(self):
        """Select the agent from the wizard"""
        title = self.__wizard.get_wizard_title()
        if title == "Configure Office 365 App":
            if self.app_type == O365AppTypes.exchange:
                agent_type = "Exchange Online"
            elif self.app_type == O365AppTypes.sharepoint:
                agent_type = "SharePoint Online"
            elif self.app_type == O365AppTypes.onedrive:
                agent_type = "OneDrive for Business"
            else:
                agent_type = "Teams"
            self.__wizard.select_radio_card(agent_type)
            self.__wizard.click_next()

    @WebAction()
    def __select_region(self, region: str) -> None:
        """Helper method to select region while creating O365 app
            Args:
                region(str) -- region if required
        """
        if self.__admin_console.check_if_entity_exists("xpath","//div[@id='storageRegion']"):
            self.__wizard.select_drop_down_values(id='storageRegion', values=[region])
            self.__wizard.click_next()
            self.__admin_console.wait_for_completion()

    @WebAction()
    def __select_server_backup_plan(self, plan: str) -> None:
        """Helper method to select plan while creating O365 app
            Args:
                plan(str) -- plan if required
        """
        if self.__admin_console.check_if_entity_exists("id", "planDropdown"):
            self.__wizard.select_drop_down_values(id='planDropdown', values=[plan])
        self.__wizard.click_next()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def confirm_app_principal_checkbox(self):
        """Clicks on confirm app principal checkbox during SharePoint client creation in React"""
        self.__driver.find_element(
            By.XPATH,
            "//h4[text()='Confirmation']/following-sibling::div/div//label//input[@id='appPrincipalConfirmation']"
        ).click()

    @WebAction()
    def _refresh_stats(self):
        """Refresh stats shown in Discovery cache info dialog"""
        refresh_stat_xpath = "//button[@aria-label ='Updates the discovery progress']"
        self.__driver.find_element(By.XPATH,refresh_stat_xpath).click()

    @WebAction()
    def _get_discovery_status(self):
        """Gets the discovery status form the discovery cache dialog (in react)"""
        status_xpath = "//div[@aria-labelledby='customized-dialog-title']//div[contains(@class,'tile-row center " \
                       "false')]/div[text()='Status']/following-sibling::div"
        status = self.__driver.find_element(By.XPATH, status_xpath).text
        return status

    @WebAction()
    def _get_discovery_percentage(self):
        """Gets the discovery percentage from the discovery cache dialog"""
        percentage_xpath = "//div[@aria-labelledby='customized-dialog-title']//div[contains(@class,'tile-row center" \
                           " false')]/div[text()='Progress']/following-sibling::div//p"
        percentage = self.__driver.find_element(By.XPATH, percentage_xpath).text
        return percentage

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
                stat_type_temp=stat_type
                if stat_type == 'Mails':
                    stat_type_temp = 'Emails' if not self.is_react else 'Items'
                elif stat_type == 'Indexed mails':
                    stat_type_temp = 'Indexed emails'
                stat_xpath = (f"//span[@ng-bind='entity.title' and contains(text(),'{stat_type_temp}')]"
                              f"/parent::*/span[@ng-bind='entity.value']") if not self.is_react else \
                    f"//span[contains(text(),'{stat_type_temp}')]/ancestor::span/span[contains(@class,'count')]"
                element = self.__driver.find_element(By.XPATH, stat_xpath)
                return element.text
            except NoSuchElementException as exp:
                self.log.info("%s Stats not updated yet. Attempt: %s", stat_type, retry + 1)
                time.sleep(10)
                self.log.info("Refreshing the page")
                self.__admin_console.refresh_page()
                retry += 1

    @PageService()
    def get_app_stat(self, stat_type):
        """
        Get App stats from app page
                Args:
                    stat_type (str)  --  Type of stat we want to fetch from App details page
                        Valid options:
                            Mails -- To fetch the number of mails displayed on App page
                            Mailboxes -- To fetch the number of mailboxes displayed on App page
                            Indexed mails -- To fetch the number of Indexed mails on App page
        """
        value = self._get_app_stat(stat_type=stat_type)
        if not value:
            raise CVWebAutomationException(
                f'{stat_type} Stats were not able to get fetched from the page.')
        return value

    @PageService()
    def get_discovery_status_count(self, status="Manual"):
        """
        Get Count of mailboxes with given discovery type
            Args:
                status - Discovery Type (Manual or Auto)

        """
        visible_columns = self.__rtable.get_visible_column_names()
        if constants.ExchangeOnline.DISCOVERY_TYPE.value not in visible_columns:
            self.__rtable.display_hidden_column(constants.ExchangeOnline.DISCOVERY_TYPE.value)
        self.__rtable.apply_filter_over_column(column_name=constants.ExchangeOnline.DISCOVERY_TYPE.value, filter_term=status,
                                               criteria=Rfilter.equals)
        count = len(self.__rtable.get_column_data(column_name="Name"))
        return count

    @PageService()
    def get_audit_trail_data(self, app_name, user_name):
        """
        Get Audit trail tabel details
            Args:
                app_name - App name to filter details
                user_name - Username to filter details
        """
        self.__admin_console.access_tab(constants.ExchangeOnline.REPORTS_TAB.value)
        self.__admin_console.click_button_using_text(value="Audit trail")
        time.sleep(10)
        self.__admin_console.fill_form_by_id(element_id="SearchString", value=app_name)
        self.__admin_console.click_button("Apply")
        self.__rtable.apply_filter_over_column(column_name="User", filter_term=user_name, criteria=Rfilter.equals)
        return self.__rtable.get_table_data()

    @PageService()
    def _handle_discovery_alerts(self):
        """Handles the discovery alerts shown while exchange discovery"""
        self.__admin_console.wait_for_completion()
        alert = self.__wizard.get_alerts()
        if self.app_type == O365AppTypes.exchange:
            attempts = 5
            while alert == "Retrieving the mailbox list for the first time. Please check back in few minutes." or alert == "The mailbox list is getting refreshed. Please check back in few minutes.":
                self.__rtable.reload_data()
                time.sleep(5)
                alert = self.__wizard.get_alerts()
                attempts-=1
                if attempts == 0:
                    self.__wizard.click_button("Previous")
                    self.__admin_console.wait_for_completion()
                    self.__wizard.click_next()
                    self.__admin_console.wait_for_completion()
                    alert = self.__wizard.get_alerts()
            if "showing mailboxes from cache" in alert.lower():
                self.log.info("Discovery completed")
                return
            elif "mailboxes and groups are being discovered in the background." in alert.lower():
                button_xpath = "//button[@label='Discovery status']"
                self.__driver.find_element(By.XPATH,button_xpath).click()
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
        elif self.app_type == O365AppTypes.sharepoint:
            if "sites are being discovered in the background." in alert.lower():
                button_xpath = "//button[@label='Discovery status']"
                self.__driver.find_element(By.XPATH, button_xpath).click()
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
        self.__admin_console.click_button("Close")
        self.__admin_console.wait_for_completion()

    @PageService()
    def disable_backup(self):
        """
        Disable the backup for the client
        """
        self.__rmodal_dialog.disable_toggle(toggle_element_id="backupToggle")
        self.__admin_console.wait_for_completion()
        self.__rmodal_dialog.click_submit()
        self.__admin_console.wait_for_completion()

    @PageService()
    def enable_backup(self):
        """
        Enable the backup for the client
        """
        self.__rmodal_dialog.enable_toggle(toggle_element_id="backupToggle")
        self.__admin_console.wait_for_completion()

    @PageService()
    def __authorize_permissions(self, global_admin, password):
        """Clicks authorize now and enables permissions for the app

            Args:
                global_admin (str)  --  Microsoft Global admin email id
                password (str)  --  Global admin password

        """
        retry = 5
        while retry > 0:
            retry -= 1
            if len(self.__driver.window_handles) == 1:
                self.__click_authorize_now()

            admin_console_window = self.__driver.window_handles[0]
            azure_window = self.__driver.window_handles[1]

            self.__switch_to_window(azure_window)

            self.__enter_email(global_admin)

            self.__enter_password(password)
            try:
                self.newly_created_app_name = self.__get_new_app_name()

                # Final Accept button
                self.__click_submit()

                self.__switch_to_window(admin_console_window)
                self.__admin_console.wait_for_completion()
                break
            except (NoSuchElementException, StaleElementReferenceException):
                self.__close_current_tab()

        # Clicking multiple times is required sometimes
        authorize_now_xpath = "//a[text()='here']"
        attempts = 5
        while (self.__admin_console.check_if_entity_exists('xpath', authorize_now_xpath)
               or self.__admin_console.check_if_entity_exists(
                    'link', self.__admin_console.props['action.authorize.app'])):
            is_app_authorized_xpath = (f'//span[contains(normalize-space(), '
                                       f'\'{self.__admin_console.props["confirm.appAuthorized"]}\')]')
            if attempts == 0:
                if self.__admin_console.check_if_entity_exists(
                        'xpath', is_app_authorized_xpath):
                    self.__driver.find_element(By.XPATH,
                        f'{is_app_authorized_xpath}//a[normalize-space()="Yes"]').click()
                    return
                else:
                    raise CVWebAutomationException("Failed to grant permissions.")

            self.log.info('Accept permissions button did not work. Trying again..')
            self.__click_authorize_now()

            try:
                admin_console_window = self.__driver.window_handles[0]
                azure_window = self.__driver.window_handles[1]

                self.__switch_to_window(azure_window)
                self.__click_submit()

                self.__switch_to_window(admin_console_window)
                self.__admin_console.wait_for_completion()
            except (NoSuchElementException, StaleElementReferenceException):
                self.__close_current_tab()

            attempts -= 1

    @PageService()
    def __authorize_permissions_for_teams(self, password):
        """Enter the password and authorize the Azure app.

            Args:
                password (str)  --  Global admin password

        """
        admin_console_window = self.__driver.window_handles[0]
        azure_window = self.__driver.window_handles[1]
        self.__switch_to_window(azure_window)
        self.__enter_password(password)
        self.newly_created_app_name = self.__get_new_app_name()
        self.__click_submit()
        self.__switch_to_window(admin_console_window)

    @PageService()
    def __create_app_principal(self):
        """Creates app principal required for SharePoint V2 Pseudo Client Creation"""
        sharepoint_app_id, sharepoint_tenant_id, sharepoint_request_xml = self.__get_id_and_xml_text()
        self.__grant_sharepoint_permissions()

        admin_console_window = self.__driver.window_handles[0]
        app_principal_window = self.__driver.window_handles[1]

        if not self.__admin_console.check_if_entity_exists("class", "ms-input"):
            self.__switch_to_window(app_principal_window)
            self.__admin_console.wait_for_completion()

        self.__enter_app_id_and_lookup(sharepoint_app_id)
        self.__admin_console.wait_for_completion()
        self.__enter_details_and_create(sharepoint_tenant_id, sharepoint_request_xml)
        self.__admin_console.wait_for_completion()
        self.__click_trust_it()
        self.__admin_console.wait_for_completion()
        self.__close_current_tab()
        self.__switch_to_window(admin_console_window)
        self.__admin_console.wait_for_completion()
        if self.is_react:
            self.confirm_app_principal_checkbox()
        else:
            self.__admin_console.checkbox_select("CONFIRM_CREATE_APP_PRINCIPAL")
        self.__admin_console.click_button("Close")
        self.__admin_console.wait_for_completion()

    @PageService()
    def __get_discovery_dialog_stats(self, retry=0):
        """Returns discovery stats in discovery dialog"""
        while retry < 3:
            time.sleep(30)
            discovery_stats = self.__modal_dialog.get_details()
            if not discovery_stats:
                retry = retry + 1
            else:
                return discovery_stats
        if retry > 3:
            raise Exception('Unable to fetch discovery stats')

    @PageService()
    def __wait_while_discovery_in_progress(self, time_out=600, poll_interval=60):
        """Waits for cache to get populated

            Args:
                time_out (int): Time out
                poll_interval (int): Regular interval for check
        """
        if self.is_react:
            attempts = time_out // poll_interval
            if self.app_type in [O365AppTypes.exchange, O365AppTypes.sharepoint]:
                self._handle_discovery_alerts()
            else:
                search_text = "//*[contains(text(),'cache last updated on')]"
                while not self.__admin_console.check_if_entity_exists(By.XPATH, search_text):
                    if attempts == 0:
                        raise CVWebAutomationException("Discovery exceeded Stipulated time. Testcase terminated.")
                    self.log.info("Please wait while the discovery is in progress")
                    time.sleep(20)
                    self.__rtable.reload_data()
                    attempts -= 1
        else:
            self.__open_add_user_panel()
            self.__admin_console.wait_for_completion()
            attempts = time_out // poll_interval
            exchange_discovery_failure_flag = False
            if self.app_type == O365AppTypes.sharepoint:
                self.__click_last_discover_cache_update_time()
            while attempts != 0:
                if self.app_type == O365AppTypes.sharepoint or exchange_discovery_failure_flag:
                    discovery_stats = self.__get_discovery_dialog_stats()
                    is_discovery_still_in_progress = discovery_stats['Status'] != 'Completed'
                else:
                    is_discovery_still_in_progress = self.__admin_console.check_if_entity_exists(
                        'link', self.__admin_console.props['action.refresh'])
                if is_discovery_still_in_progress:
                    self.log.info('Please wait. Discovery in progress...')
                    time.sleep(poll_interval)
                    if not self.app_type == O365AppTypes.sharepoint and not exchange_discovery_failure_flag:
                        self.__admin_console.select_hyperlink(self.__admin_console.props['action.refresh'])
                        self.__admin_console.wait_for_completion()
                else:
                    if self.app_type == O365AppTypes.exchange and not exchange_discovery_failure_flag:
                        latest_discover_cache_update_time = self.__get_last_discover_cache_update_time()
                        if latest_discover_cache_update_time == 'Not available':
                            exchange_discovery_failure_flag = True
                            self.__click_last_discover_cache_update_time()
                            self.__click_refresh_cache()
                            time.sleep(poll_interval)
                            continue
                    elif self.app_type == O365AppTypes.sharepoint or exchange_discovery_failure_flag:
                        self.__modal_panel.close()
                    break
                attempts -= 1
            if attempts == 0:
                raise CVWebAutomationException('Discovery exceeded stipulated time.'
                                               'Test case terminated.')

    @PageService()
    def get_total_associated_users_count(self):
        """Returns count of total associated users"""
        self.__admin_console.access_tab(self.constants.ACCOUNT_TAB.value)
        if self.is_react:
            return int(self.__rtable.get_total_rows_count())
        else:
            return int(self.__table.get_total_rows_count())

    @PageService()
    def __navigate_to_job_page(self, job_id):
        """Navigates to specified job page
            Args:
                job_id (str)                     : Job Id of the ob
        """
        self.__admin_console.navigator.navigate_to_jobs()
        if not self.__jobs.if_job_exists(job_id):
            self.__jobs.access_job_history()
            if not self.__jobs.if_job_exists(job_id):
                raise CVWebAutomationException("Job is not present in Active jobs or job history")
        self.__jobs.view_job_details(job_id)

    @PageService()
    def __get_job_details(self, job_id):
        """Returns the job details
            Args:
                job_id (str)                     : Job Id of the ob
        """
        self.__jobs.access_job_by_id(job_id)
        jd = JobDetails(self.__admin_console)
        details = jd.get_all_details()
        return details

    @PageService()
    def __process_status_tab_stats(self, stats):
        """Returns the status_tab_stats of status tab in job details page after processing them into dictionary
            Args:
                stats (str)         :  site/user stats of status tab in job details page
            Returns:
                stats_dict (dict)   :  dictionary of stats
        """
        status_tab_stats = re.findall("\d+[A-Za-z]+", stats)
        stats_dict = {}
        for stat in status_tab_stats:
            value, label = re.findall("\d+|[A-Za-z]+", stat)
            stats_dict[label] = int(value)
        return stats_dict

    @PageService()
    def _verify_downloaded_file_details(self, mail_details: dict = None, export_file_details: dict = None) -> bool:
        """Verify the downloaded file from the browse page
        mail_details (dict) :- Pass the mail details dictionary for verifying PST/CAB files
        export_file_details (dict) :- Pass the export file details dictionary for verifying the export file
        """
        is_download = False
        machine = Machine()
        AUTOMATION_DIRECTORY = AutomationUtils.constants.AUTOMATION_DIRECTORY
        downloaded_folder_path = os.path.join(AUTOMATION_DIRECTORY, 'Temp')
        file_path = machine.get_latest_timestamp_file_or_folder(folder_path=downloaded_folder_path,
                                                                operation_type="file")
        file_name = file_path.split("\\")[-1]
        file_name = re.sub(r"\s*\(\d\)\.\w+$", "", file_name)
        if self.app_type == O365AppTypes.exchange:
            if mail_details:
                if re.sub(r"[:_\-]", "", mail_details["Subject"]) == re.sub(r"[:_\-]", "", file_name):
                    self.log.info("File is successfully downloaded")
                    machine.delete_file(file_path)
                else:
                    raise CVWebAutomationException("Mail was not downloaded. Please check")
            elif export_file_details:
                if export_file_details["Name"] == file_name:
                    self.log.info("Export file is successfully downloaded")
                    machine.delete_file(file_path)
                else:
                    raise CVWebAutomationException("Export file was not downloaded. Please check.")
            else:
                raise Exception("Please pass the mail details to verify")
        return is_download

    @PageService()
    def _get_export_file_details(self, file_name):
        """Get the export file details in the view exports dialog"""
        table = Table(self.__admin_console, id='exportSetDetails')
        table.search_for(file_name)
        export_table_data = table.get_table_data()
        export_file_details = {key: export_table_data[key][0] for key in export_table_data}
        export_file_details['Status'] = self.__get_export_file_download_status()
        export_file_details['Type'] = self.__get_export_file_type()
        return export_file_details

    @WebAction()
    def _create_recovery_point_by_mailbox(self, mailbox):
        """
            Creates recovery point for a certain mailbox

            mailbox (str) --- name of the mailbox which needs to recovered
            backup_job_id (str) --- job_id corresponding to which we need to create the recovery point

            returns:

            Job details of the recovery job
        """
        self.__admin_console.access_tab(self.__admin_console.props["header.monitoring"])
        self.__admin_console.click_button(value=self.__admin_console.props["label.recovery.point.list"])
        table = Rtable(self.__admin_console, id="office365CurrentActivityTable")
        table.access_toolbar_menu(self.__admin_console.props["label.createRecoveryPoint"])
        self.__click_recovery_point_browse()
        self.__admin_console.wait_for_completion()
        self.search_recovery_point_mailbox(mailbox)
        self.__rtable.select_rows([mailbox])
        self.__admin_console.click_button_using_text("Add")
        self.__admin_console.wait_for_completion()
        self.__admin_console.submit_form()
        self.__rmodal_dialog.click_submit()
        job_details = self.__job_details()
        self.log.info('Recovery Point Creation Job Details: %s', job_details)
        return job_details

    @PageService()
    def _restore_from_recovery_point(self, recovery_id):
        """
            Restores the mailbox from a recovery point

            recovery_id (str) --- ID of the recovery job
        """
        self.__admin_console.access_tab(self.__admin_console.props["header.monitoring"])
        self.__admin_console.click_button(value=self.__admin_console.props["label.recovery.point.list"])
        table = Rtable(self.__admin_console, id="office365CurrentActivityTable")
        table.apply_filter_over_column("Recovery point job id", recovery_id)
        table.select_rows([recovery_id])
        self.__click_restore(recovery_point=True)
        self.__admin_console.wait_for_completion()
        self.select_restore_options()
        job_details = self.__job_details()
        self.log.info('Restore Recovery Job details: %s', job_details)

    @WebAction()
    def _verify_downloaded_file_details(self, mail_dict):
        """Verify the downloaded file from the browse page"""
        machine = Machine()
        AUTOMATION_DIRECTORY = AutomationUtils.constants.AUTOMATION_DIRECTORY
        downloaded_folder_path = os.path.join(AUTOMATION_DIRECTORY, 'Temp')
        file = machine.get_latest_timestamp_file_or_folder(folder_path=downloaded_folder_path, operation_type="file").split("\\")[-1]
        if self.app_type == O365AppTypes.exchange:
            if mail_dict:
                return mail_dict["Subject"] == file
            else:
                raise Exception("Please pass the mail details to verify")

    @WebAction()
    def _get_purchased_additional_or_licensed_usage(self):
        """fetches the purchased, additional and included usages"""
        label_xpath = "//span[@class='kpi-category-label']"
        value_xpath = "//span[@class='kpi-category-label' and contains(text(), '{}')]/preceding-sibling::span"
        purchased_and_additional_usage = dict()
        elements = self.__driver.find_elements(By.XPATH, label_xpath)
        for element in elements:
            key = element.text
            value = self.__driver.find_element(By.XPATH, value_xpath.format(key)).text
            purchased_and_additional_usage.update({key: value})
        return purchased_and_additional_usage

    @WebAction()
    def _get_total_capacity_usage(self):
        """Fetches the total capacity, total active capacity and total inactive capacity usage"""
        total_capacity_usage = {}
        label_xpath = "//div[contains(@class,'MuiGrid-root')]/*/div[contains(text(),'{}')]/following-sibling::div"
        total_capacity_usage["Total Capacity Usage"] = self.__driver.find_element(By.XPATH, label_xpath.format(
            "Total Capacity Usage")).text
        total_capacity_usage["Total Active Capacity Usage"] = self.__driver.find_element(By.XPATH, label_xpath.format(
            "Total Active Capacity Usage")).text
        total_capacity_usage["Total Inactive Capacity Usage"] = self.__driver.find_element(By.XPATH, label_xpath.format(
            "Total Inactive Capacity Usage")).text
        return total_capacity_usage

    @WebAction()
    def _get_total_licensed_users(self):
        """Fetches the total capacity, total active capacity and total inactive capacity usage"""
        total_licensed_users = {}
        label_xpath = "//div[contains(@class,'MuiGrid-root')]/*/div[contains(text(),'{}')]/following-sibling::div"
        total_licensed_users["Total Licensed Users"] = self.__driver.find_element(By.XPATH, label_xpath.format(
            "Total Users")).text
        total_licensed_users["Total Exchange Users"] = self.__driver.find_element(By.XPATH, label_xpath.format(
            "Total Exchange Users")).text
        total_licensed_users["Total OneDrive Users"] = self.__driver.find_element(By.XPATH, label_xpath.format(
            "Total OneDrive Users")).text
        return total_licensed_users

    @WebAction()
    def _get_monthly_usage(self):
        """Fetches the monthly usage for all the agents"""
        monthly_usage = dict()
        data = self.__rtable.get_table_data()
        for key in data:
            if key == "Application":
                agent_usage = {key: None for key in data["Application"]}
                for index in range(0, len(data[key])):
                    agent_usage[data["Application"][index]] = data["Active Capacity"][index]
                monthly_usage["Monthly Usage"] = agent_usage
            if key == "Email address":
                row_xpath = "//span[text()='{}']/ancestor::tr/td/span[contains(@class,'usage-details')]"
                license_user_usage = {key: {O365AppTypes.exchange.value: False, O365AppTypes.onedrive.value: False} for
                                      key in data["Email address"]}
                for index in range(0, len(data[key])):
                    isExchange, isOneDrive = self.__driver.find_elements(By.XPATH,
                                                                         row_xpath.format(data["Email address"][index]))
                    if isExchange.get_attribute("class") == "usage-details-check":
                        license_user_usage[data["Email address"][index]][O365AppTypes.exchange.value] = True
                    if isOneDrive.get_attribute("class") == "usage-details-check":
                        license_user_usage[data["Email address"][index]][O365AppTypes.onedrive.value] = True
                monthly_usage = license_user_usage
        return monthly_usage

    @PageService()
    def __acquire_token_custom_app(self, global_admin: str, password: str) -> None:
        """Clicks authorize now and enables permissions for the app

            Args:
                global_admin (str)  --  Microsoft Global admin email id
                password (str)      --  Global admin password
        """
        time.sleep(5)
        if len(self.__driver.window_handles) == 1:
            self.__driver.find_element(
                By.XPATH, "//a[normalize-space()='if you are not redirected automatically.").click()
        admin_console_window = self.__driver.window_handles[0]
        azure_window = self.__driver.window_handles[1]
        self.__switch_to_window(azure_window)
        self.__enter_email(global_admin)
        self.__enter_password(password)
        if self.__admin_console.check_if_entity_exists('id', 'idBtn_Back'):
            self.__driver.find_element(By.ID, "idBtn_Back").click()
        time.sleep(2)
        self.__switch_to_window(admin_console_window)
        self.__admin_console.wait_for_completion()
        self.__check_for_errors()
        self.__driver.find_element(By.XPATH,
                                   "//button[contains(@class, 'MuiButtonBase-root')]/div[text()='Close']").click()

    @PageService()
    def __create_custom_app(self, app_id: str, app_secret: str, dir_id: str, cert_path: str, cert_pass: str,
                            tenant_site_url: str = None) -> None:
        """Creates custom app
            app_id   (str)          -- App id
            app_secret (str)        -- App secret
            dir_id(str)             -- Directory ID
            cert_path(str)          -- Path of the location where the Certificate private key (pfx file) is present
            cert_pass(str)          -- Password of the Certificate
            tenant_site_url(str)    -- Tenant URL for sharepoint app (Default: None)

        """
        if not self.__admin_console.check_if_entity_exists(entity_name="id", entity_value="addAzureApplicationId"):
            time.sleep(2)
        self.__wizard.fill_text_in_field(id="addAzureApplicationId", text=app_id)
        self.__wizard.fill_text_in_field(id="addAzureApplicationSecretKey", text=app_secret)
        self.__wizard.fill_text_in_field(id="addAzureDirectoryId", text=dir_id)
        cert_upload = self.__driver.find_element(By.XPATH, "//input[contains(@accept, 'pfx')]")
        cert_upload.send_keys(cert_path)
        self.__wizard.fill_text_in_field(id="certificatePassword", text=cert_pass)
        self.__driver.find_element(By.ID, "permissionsConfirmation").click()
        if self.app_type == O365AppTypes.teams:
            self.__driver.find_element(By.ID, "redirectUriSetConfirmation").click()
            self.__driver.find_element(By.ID, "userAccountAddForBackupConfirmation").click()
        elif self.app_type == O365AppTypes.sharepoint:
            self.__wizard.fill_text_in_field(id="addTenantAdminSiteURL", text=tenant_site_url)

    @PageService()
    def __get_azure_app_details(self):
        """Get azure apps details of Office365 app"""
        self.__admin_console.access_tab(constants.O365AppTabs.Configuration.value)
        if self.app_type == O365AppTypes.teams:
            self.__rtable.display_hidden_column("Export API access")
        return self.__rtable.get_table_data()

    @PageService()
    def mark_export_api_yes_for_teams_app(self):
        """It will mark atleast one azure app as export api yes"""
        azure_apps = self.__get_azure_app_details()
        if azure_apps['Export API access'][0] != 'Yes':
            self.__admin_console.access_tab(constants.O365AppTabs.Configuration.value)
            self.__rtable.access_action_item(azure_apps['Azure app'][0], "Edit chat backup settings")
            self.__rmodal_dialog.enable_toggle(label="Enable this app to use paid Export APIs")
            self.__driver.find_element(By.XPATH, "//button[@aria-label='Save']").click()
            self.__admin_console.wait_for_completion()
        self.log.info(f"Export marked successfully for app {azure_apps['Azure app'][0]}")

    @PageService()
    def __wait_for_authorization_step(self):
        """wait for authorization step in app creation process"""
        retry = 5
        while retry > 0 and not self.__admin_console.check_if_entity_exists(By.XPATH,
                                                             "//span[text()='Azure sync completed successfully']"):
            retry -= 1
            time.sleep(10)

    @PageService()
    def add_azure_app_via_express_configuration(self, global_admin, password):
        """Add azure app via express configuration"""
        self.__admin_console.access_tab(constants.O365AppTabs.Configuration.value)
        self.__driver.find_element(By.XPATH, "//button[@aria-label='Add Azure app']").click()
        self.__wizard.click_next()
        self.__wizard.click_button(name="Add Azure app")
        self.__wait_for_authorization_step()
        self.__authorize_permissions(global_admin, password)
        self.__admin_console.click_button_using_text("Close")
        self.__wizard.click_button(name="Close")
        self.__admin_console.wait_for_completion()

    @PageService()
    def delete_backup_data(self, item_names):
        """
            Performs command center delete operation
            Args:
                item_names      (list)       :   List of item names to be deleted
                """

        try:
            self.__rtable.select_rows(item_names)
        except :
            self.log.info("Item with the specified name doesn't exist")
        browse_table = Rtable(self.__admin_console, id="oneDriveBrowseGrid2")
        before_delete_count = len(browse_table.get_column_data('Name'))
        self._click_delete_and_confirm()
        self.__admin_console.wait_for_completion()
        after_delete_count = len(browse_table.get_column_data('Name'))
        return [before_delete_count, after_delete_count]

    @PageService()
    def add_custom_category(self, custom_dict, plan=None):
        """Adds Custom category to the office 365 app
            Args:
                custom_dict (dict)  --  dictionary of custom category name and rule details.
                    //Example:
                        {
                        "name":"Display name contains custom"
                        "rules":
                            [
                                {
                                "fieldSourceSelect":"Team Display Name",
                                "fieldOperatorSelect":"Contains",
                                "fieldSourceString":"custom"
                                }
                            ]
                        }
                plan (str)     : Name of plan to be selected
                                    //Default: None
        """
        if self.is_react:
            self.__admin_console.access_tab(self.constants.CONTENT_TAB.value)
            self.__rtable.access_toolbar_menu('Add')
            self.__wizard.select_card("Add content to backup")
            self.__wizard.click_next()
            self.__wizard.expand_accordion("Advanced")
            self.__wizard.select_card("Custom categories")
            self.__wizard.click_next()
            self.__admin_console.wait_for_completion()
            self.__driver.find_element(By.XPATH, "//input[@id='customCategoryName']").send_keys(custom_dict['name'])
            for rule in custom_dict['rules']:
                self.__add_rule(rule)
            self.__wizard.click_next()
            self.__wizard.select_drop_down_values(id="cloudAppsPlansDropdown",
                                                  values=[plan] if plan else [self.o365_plan])
            self.log.info(f'Selected Office365 Plan: {plan or self.o365_plan}')
            self.__wizard.click_next()
            self.__admin_console.click_button("Submit")
            self.__admin_console.wait_for_completion()

    @PageService()
    def get_teams_tab_table_data(self):
        """Get a office365 Teams client Teams tab table data."""
        self.__admin_console.access_tab(self.constants.ACCOUNT_TAB.value)
        table_data = self.__rtable.get_table_data()
        if len(table_data['Name']) == 0:
            retry = 3
            while retry > 0:
                self.__admin_console.refresh_page()
                table_data = self.__rtable.get_table_data()
                if len(table_data['Name']) == 0:
                    retry -= 1
                    time.sleep(20)
                else:
                    return table_data
        return table_data

    @PageService()
    def __add_rule(self, rule):
        """Adds Rule to the custom category
                   Args:
                       rule -- dict of rule details
                       Example:
                            {
                            "fieldSourceSelect":"Team Display Name",
                            "fieldOperatorSelect":"Contains",
                            "fieldSourceString":"custom"
                            }
                            The "custom" field needs to be set true when we are creating a Custom Category rule for a
                            custom property, like PropertyBag for SharePoint. For all other scenarios the "custom"
                            field can be omitted.
               """
        element = self.__driver.find_element(By.XPATH, "//button[@aria-label='Add rule']")
        element.click()
        self.__admin_console.wait_for_completion()
        self.__rmodal_dialog.select_dropdown_values("fieldSourceSelect", [rule["fieldSourceSelect"]])
        if ("custom" in rule) and rule["custom"]:
            self.__rmodal_dialog.fill_text_in_field("fieldNameInput", rule["fieldNameInput"])
            self.__rmodal_dialog.select_dropdown_values("fieldTypeSelect", [rule["fieldTypeSelect"]])
            self.__rmodal_dialog.select_dropdown_values("fieldOperatorSelect", [rule["fieldOperatorSelect"]])
            if self.__admin_console.check_if_entity_exists('id', "fieldSourceNumber"):
                self.__rmodal_dialog.fill_text_in_field("fieldSourceNumber", rule["fieldSourceNumber"])
            elif self.__admin_console.check_if_entity_exists('id', "fieldSourceString"):
                self.__rmodal_dialog.fill_text_in_field("fieldSourceString", rule["fieldSourceString"])
        else:
            self.__rmodal_dialog.select_dropdown_values("fieldOperatorSelect", [rule["fieldOperatorSelect"]])
            if self.__admin_console.check_if_entity_exists('id', "fieldSourceString"):
                self.__rmodal_dialog.fill_text_in_field("fieldSourceString", rule["fieldSourceString"])
            else:
                self.__rmodal_dialog.select_dropdown_values("fieldMaskSelect6", [rule["fieldSourceString"]])
        self.__rmodal_dialog.click_button_on_dialog("Add")

    @PageService()
    def enable_user_chat(self):
        """Enables user chat for Teams app."""
        self.__admin_console.access_tab(constants.O365AppTabs.Configuration.value)
        if not self.__admin_console.check_if_entity_exists('xpath', "//div[contains(text(),'Paid Export APIs')]"):
            self.__driver.find_element(By.XPATH, "//div[@id='personalChat']//button").click()
            self.__driver.find_element(By.XPATH, "//div[@id='personalChatOpModeDropdown']").click()
            self.__driver.find_element(By.XPATH, "//div[@title='Paid Export APIs']").click()
            self.__admin_console.click_button_using_text("Submit")
            self.__admin_console.checkbox_select(checkbox_id='confirmationCheckboxCostImplication')
            self.__admin_console.checkbox_select(checkbox_id='confirmationCheckboxAzureSubscription')
            self.__admin_console.click_button("Enable")

    def __click_discovery_status_button(self):
        """Clicks discovery status button in overview tab"""
        self.__admin_console.access_tab(self.constants.OVERVIEW_TAB.value)
        self.__driver.find_element(By.XPATH, "//div[@id='tile-discovery-status']//button").click()

    def refresh_cache(self):
        """Refresh cache for office 365 app"""
        self.__click_discovery_status_button()
        self.__click_refresh_cache()
        self.__wait_till_current_discovery_ends()
        self.__admin_console.click_button("Close")

    @WebAction()
    def _apply_discover_filter(self,discovery_filter_value):
        """
        Check for discovery filter option while creating client
        Args:
            discovery_filter_value(dict)    : Attribute name and Attribute value for discovery filter while creating client
                                                Eg: {Attribute name: Attribute value}
        """
        for attribute_name in discovery_filter_value:
            self.__admin_console.fill_form_by_id(element_id="filterAttrName",value=attribute_name)
            self.__admin_console.fill_form_by_id(element_id="filterAttrVal",value=discovery_filter_value[attribute_name])
        self.__admin_console.submit_form()

    @PageService()
    def __create_office365_app_react(self, name, time_out, poll_interval, global_admin=None, password=None, app_id=None,
                                     dir_id=None, app_secret=None, cert_path=None, cert_pass=None,
                                     tenant_site_url=None, is_express_config=True, region=None, plan=None,
                                     discovery_filter_value=None):
        """Creates O365 App For react page

            Args:
                name(str)                   :  Name to be given to the app
                time_out        (int):  Time out for app creation
                poll_interval   (int):  Regular interval for app creating check
                global_admin(str)           :  Global admin email id (Default: None)
                password(str)               :  Password for global admin (Default: None)
                app_id(str)                 :  App id (Default: None)
                dir_id(str)                 :  Directory id (Default: None)
                app_secret(str)             :  App Secret (Default: None)
                cert_path(str)              :  Path of the location where the Certificate private key (pfx file) is present
                cert_pass(str)              :  Password of the Certificate
                tenant_site_url(str)        :  Tenant Site url (Default: None)
                is_express_config(boolean)  :  Time out for app creation
                region          (str)       :  Storage Region
                plan            (str)       :  Server plan
                discovery_filter_value(dict)    : Attribute name and Attribute value for discovery filter while creating client
                                                Eg: {Attribute name: Attribute value}
        """
        self.__select_backup_service()
        self.__select_agent()
        self.__select_region(region)
        self.__select_server_backup_plan(plan)
        self.__wizard.fill_text_in_field(id='appNameField', text=name)
        if is_express_config:
            if self.__is_multi_tenant_enabled():
                self.__configure_with_multi_tenant_app(global_admin_address=global_admin, global_admin_passwd=password)
            else:
                self.__admin_console.fill_form_by_id('globalUserName', global_admin)
                self.__admin_console.fill_form_by_id('globalPassword', password)
                if self.app_type == O365AppTypes.teams:
                    self.__admin_console.checkbox_select('TEAMS_SVC_USAGE')
                self.__admin_console.checkbox_select('SAVE_GA_CREDS')
                self.__admin_console.checkbox_select('MFA_DISABLED')
                time.sleep(90)
                self.__click_create_azure_ad_app()
                attempts = time_out // poll_interval
                while True:
                    if attempts == 0:
                        raise CVWebAutomationException('App creation exceeded stipulated time.'
                                                       'Test case terminated.')
                    self.log.info("App creation is in progress..")

                    self.__admin_console.wait_for_completion()
                    self.__check_for_errors()
                    # Check authorize app available
                    if self.__admin_console.check_if_entity_exists(
                            "link", self.__admin_console.props['action.authorize.app']):
                        break
                    time.sleep(poll_interval)
                    attempts -= 1
                self.__authorize_permissions(global_admin, password)
            self.__admin_console.submit_form()
        else:
            self.__wizard.select_card("Custom configuration (Advanced)")
            self.__create_custom_app(app_id, app_secret, dir_id, cert_path, cert_pass, tenant_site_url)
        self.__wizard.click_button(self.__admin_console.props['label.client.create'])
        self.__admin_console.wait_for_completion()
        if self.__wizard.get_active_step()=="Discovery Filters" and discovery_filter_value:
            self.__admin_console.click_button_using_text("Add")
            self._apply_discover_filter(discovery_filter_value=discovery_filter_value)
            self.__wizard.click_next()
            self.__admin_console.wait_for_completion()
        if self.__wizard.get_active_step()=="Discovery Filters":
            self.__admin_console.click_button_using_text("Add")
            self._apply_discover_filter(discovery_filter_value={"*":"*"})
            self.__wizard.click_next()
            self.__admin_console.wait_for_completion()
        self.__admin_console.click_button(self.__admin_console.props['label.action.close'])
        self.__admin_console.wait_for_completion()
        time.sleep(5)  # Wait for Discovery process to launch in access node
        self.__close_backup_demo_popup()

    @PageService()
    def __create_office365_app_angular(self, name, global_admin, password, time_out=600, poll_interval=10):
        """Creates O365 App For react page
            Args:
                    name(str)                   :  Name to be given to the app
                    global_admin(str)           :  Global admin email id
                    password(str)               :  Password for global admin

        Args:
            name            (str):  Name to be given to the app
            global_admin    (str):  Global admin email id
            password        (str):  Password for global admin
            time_out        (int):  Time out for app creation
            poll_interval   (int):  Regular interval for app creating check
        """

        self.__admin_console.fill_form_by_id('appName', name)
        self.__click_button_if_present('Got it')
        if self.__is_multi_tenant_enabled():
            self.__configure_with_multi_tenant_app(global_admin_address=global_admin, global_admin_passwd=password)
            if self.app_type == O365AppTypes.sharepoint:
                self.__driver.find_element(By.LINK_TEXT, 'here').click()
                self.__create_app_principal()
        else:
            self.__admin_console.fill_form_by_id('globalUserName', global_admin)
            self.__admin_console.fill_form_by_id('globalPassword', password)
            if self.app_type == O365AppTypes.teams:
                self.__admin_console.checkbox_select('TEAMS_SVC_USAGE')
            self.__admin_console.checkbox_select('SAVE_GA_CREDS')
            self.__admin_console.checkbox_select('MFA_DISABLED')
            time.sleep(90)
            self.__click_create_azure_ad_app()
            attempts = time_out // poll_interval
            while True:
                if attempts == 0:
                    raise CVWebAutomationException('App creation exceeded stipulated time.'
                                                   'Test case terminated.')
                self.log.info("App creation is in progress..")

                self.__admin_console.wait_for_completion()
                self.__check_for_errors()
                # Check authorize app available
                if self.__admin_console.check_if_entity_exists(
                        "link", self.__admin_console.props['action.authorize.app']) or len(
                    self.__driver.window_handles) > 1:
                    break
                time.sleep(poll_interval)
                attempts -= 1
            self.__authorize_permissions(global_admin, password)
            if self.app_type == O365AppTypes.sharepoint:
                self.__create_app_principal()
                self.__verify_sharepoint_service_account()
                self.__verify_sharepoint_modern_authentication()
                time.sleep(5)
                self.__verify_app_principal()
        self.__admin_console.submit_form()
        self.__admin_console.wait_for_completion()
        time.sleep(5)  # Wait for Discovery process to launch in access node

    @WebAction()
    def _get_job_starting_time(self, job_details):
        """
        Gets the start time of the job
        job_details (dict): job details
        """
        date_time = job_details[self.__admin_console.props['label.startTime']]
        language = self.__admin_console.get_locale_name()
        year, month, date, start_time = get_job_starting_time(date_time, language)
        return year, month, date, start_time
    @WebAction()
    def __click_restore_recovery_point(self):
        """Clicks restore button in recovery points tab"""
        try:
            restore_xpath = f"//button[@id='submit-btn']"
            self.__driver.find_element(By.XPATH, restore_xpath).click()
        except:
            raise CVWebAutomationException("Unable to click on Restore in recovery points tab")

    @WebAction(delay=2)
    def __click_day_in_calender_view(self,date):
        """
        clicks on date in calender view
        date (str): date, Ex: 13
        """
        day_xpath=f"//div[@class='tile-row']//div[@id='day-{date}-btn']"
        self.__driver.find_element(By.XPATH, day_xpath).click()

    @WebAction(delay=2)
    def __edit_streams(self,max_streams):
        """
        edits the max streams in configuration page
        max_streams (int): streams, Ex: 5
        """

        self.__admin_console.access_tab("Configuration")
        self.__driver.find_element(By.XPATH,"//div[@id='backupStreamCount']//button[@title='Edit']").click()
        self.__admin_console.wait_for_completion()
        input_field=self.__driver.find_element(By.XPATH,"//div[@id='backupStreamCount']//input[@type='number']")
        input_field.send_keys(Keys.CONTROL + "a")
        input_field.send_keys(Keys.DELETE)
        input_field.send_keys(max_streams)
        self.__admin_console.wait_for_completion()
        self.__driver.find_element(By.XPATH,"//div[@id='backupStreamCount']//button[@aria-label='Submit']").click()

    @WebAction()
    def __click_discovery_stats(self):
        """
        Open Discovery Stats Panel
        """
        self.__driver.find_element(By.XPATH, "//div[@id='tile-discovery-status']//button[@title='View details']").click()

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

    @PageService()
    def get_discovery_panel_data(self):
        """
        Get data from discovery panel
        """
        details=self.__RpanelInfo_obj.get_details()
        self.__admin_console.click_button(id="Cancel")
        return details

    @WebAction()
    def __edit_discovery_filter_value(self,discovery_filter_value):
        """
        Edit discovery filter in configuration tab
            discovery_filter_value(dict)    : Attribute name and Attribute value for discovery filter while creating client
                                                Eg: {Attribute name: Attribute value}
        """
        self.__driver.find_element(By.XPATH,"//div[contains(@class,'k-grid-no-sort')]//div[contains(@class,'root')]").click()
        self.__driver.find_element(By.XPATH,"//li[text()='Edit']").click()
        self.__admin_console.wait_for_completion()
        self._apply_discover_filter(discovery_filter_value)

    @WebAction()
    def __enable_discovery_filter(self):
        """
        Enable or disable discovery filter in metallic
        """
        toggle_id=None
        if self.app_type==O365AppTypes.exchange:
            toggle_id="exchangeDiscoveryFilters-toggle-btn"

        self.__rmodal_dialog.enable_toggle(toggle_element_id=toggle_id)
        self.__admin_console.wait_for_completion()

    @PageService()
    def create_office365_app(self, name, global_admin=None, password=None, app_id=None, dir_id=None, app_secret=None,
                             cert_path=None, cert_pass=None, tenant_site_url=None, is_express_config=True, time_out=600,
                             poll_interval=10, region=constants.O365Region.EAST_US_2.value, plan=None,
                             discovery_filter=False,discovery_filter_value=None):
        """
        Creates O365 App

        Args:
            name            (str):  Name to be given to the app
            global_admin    (str):  Global admin email id (Default: None)
            password        (str):  Password for global admin (Default: None)
            app_id          (str):  App id (Default: None)
            dir_id          (str):  Directory id (Default: None)
            app_secret      (str):  App Secret (Default: None)
            cert_path       (str):  Path of the location where the Certificate private key (pfx file) is present
            cert_pass       (str):  Password of the Certificate
            tenant_site_url (str):  Tenant Site url (Default: None)
            is_express_config(boolean):  Time out for app creation
            time_out        (int):  Time out for app creation
            poll_interval   (int):  Regular interval for app creating check
            region          (str):  Storage region

            plan            (str): Server plan for client
            discovery_filter(bool): discovery filter enable
            discovery_filter_value(dict)    : Attribute name and Attribute value for discovery filter while creating client
                                                Eg: {Attribute name: Attribute value}

        """

        if (is_express_config or self.app_type == O365AppTypes.teams) and not (global_admin and password):
            raise Exception("Global Admin and password are required")
        if self.__admin_console.check_if_entity_exists("xpath", "//div[@class='dashboard-tabs-container']"):
            self.__admin_console.access_tab("Apps")
            self.__rtable.access_toolbar_menu("Add Office 365 app")
            self.__admin_console.wait_for_completion()
        if self.is_react:
            self.__create_office365_app_react(name, time_out, poll_interval, global_admin, password, app_id, dir_id,
                                              app_secret, cert_path, cert_pass, tenant_site_url, is_express_config,
                                              region, plan, discovery_filter_value)
        else:
            self.__create_office365_app_angular(name, global_admin, password, time_out, poll_interval)

    @PageService()
    def create_office365_app_syntex(self, name, global_admin=None, password=None):
        """
        Creates O365 Syntex App

        Args:
            name            (str):  Name to be given to the app
            global_admin    (str):  Global admin email id (Default: None)
            password        (str):  Password for global admin (Default: None)
        """

        if not (global_admin and password):
            raise Exception("Global Admin and password are required")

        self.__admin_console.access_tab("Apps")
        self.__rtable.access_toolbar_menu("Add Office 365 app")
        self.__admin_console.wait_for_completion()

        self.__wizard.select_card("This solution provides ")
        self.__wizard.click_next()
        self.__select_agent()
        self.__wizard.fill_text_in_field(id='appNameField', text=name)
        self.__configure_with_multi_tenant_app(global_admin_address=global_admin, global_admin_passwd=password)
        if self.app_type == O365AppTypes.sharepoint:
            self.__wizard.select_radio_button(id='appPrincipalConfirmation')
        self.__wizard.click_next()
        self.__admin_console.wait_for_completion()
        self.__admin_console.click_button(self.__admin_console.props['label.action.close'])
        self.__admin_console.wait_for_completion()

    @PageService()
    def get_app_name(self):
        """Fetches the name of the created app. This is useful for metallic app"""
        return self.__get_app_name()

    @PageService()
    def get_plans_list(self):
        """Gets the list of available plans"""
        try:
            plans = self.__rtable.get_column_data(self.__admin_console.props['tableHeader.planName'])
        except ValueError:
            plans = self.__rtable.get_column_data('Profile name')
        self.log.info("plans: %s" % plans)
        for plan in plans:
            if 'o365-plan' in plan:
                self.o365_plan = plan
                break
        return plans

    @PageService()
    def get_retention_period(self):
        """Returns retention period of the o365 plan"""
        retention_panel = RPanelInfo(self.__admin_console, title=self.__admin_console.props['label.retention'])
        retention_details = retention_panel.get_details()
        return retention_details.get(self.__admin_console.props['label.retentionPeriod'],
                                     retention_details.get(self.__admin_console.props['label.retentionDays']))

    @PageService()
    def get_converted_retention_period(self, retention_period):
        """Converts the retention period to no of days format and returns it

             Args:
                    retention_period(str) : retention period
                    // Example: '5-years', 'infinite'

        """
        self.log.info(f'Given retention period : {retention_period}')
        retention_dict = {
            '5-years': '1825 days',
            '7-years': '2555 days',
            'infinite': 'Infinite',
            'enterprise': '1095 days',
            'standard': '365 days'
        }
        # Need to implement this conversion completely. For now taking static values
        converted_retention_period = retention_dict[retention_period]
        self.log.info(f'Converted retention period : {converted_retention_period}')
        return converted_retention_period

    @PageService()
    def verify_retention_of_o365_plans(self, tenant_name, plans):
        """Verifies retention for o365 plans

            Args:
                    tenant_name(str) : name of the tenant/company

                    plans(list)      : list of plans

        """
        tenant_name = tenant_name.lower()
        for plan in plans:
            if 'o365-plan' in plan:
                expected_retention = self.get_converted_retention_period(
                    plan.split(tenant_name)[-1].split('metallic-o365-plan')[0].strip('-'))
                if self.is_react:
                    self.__rtable.access_link(plan)
                else:
                    self.__table.access_link(plan)
                actual_retention = self.get_retention_period()
                if expected_retention != actual_retention:
                    raise Exception(f'Retention is not set correctly for {plan}'
                                    f'Expected Value: {expected_retention}, Actual Value: {actual_retention}')
                else:
                    self.log.info(f'Retention is set correctly for {plan}')
                self.__redirect_to_plans()

    @PageService()
    def access_office365_app(self, app_name):
        """Accesses the Office365 app from the Office365 landing page

                Args:
                    app_name (str) : Name of the Office365 app to access

        """
        self.__admin_console.access_tab(self.__admin_console.props['office365dashboard.tabs.apps'])
        self.__rtable.access_link(app_name)
        # self.__click_row_hyperlink(app_name)

    def verify_added_user_groups(self, groups=None):
        """Verifies the groups added to the app
            Args:
                groups (list)    :  list of auto associated group names
        """
        if not groups:
            groups = self.groups
        self.__admin_console.access_tab(self.constants.CONTENT_TAB.value)
        group_list = self.__rtable.get_column_data(column_name='Name')
        for group in groups:
            if group not in group_list:
                raise CVWebAutomationException(f"{group} is not associated as expected")
        self.log.info(f'Added groups verified: {groups}')

    @PageService()
    def create_o365_plan(self, plan_name, days):
        """Creates an o365 plan
                    Args:
                        plan_name (str)    :   name of plan
                        days (int)          :  number of retention days
        """

        self.__rtable.access_menu_from_dropdown(menu_id="Office 365", label="Create plan")
        self.__admin_console.fill_form_by_id(element_id='planName', value=plan_name)
        retention_time_xpath = "//label[contains(.,'Retain deleted items for')]/following-sibling::div"
        self.__driver.find_element_by_xpath(retention_time_xpath + "//button").click()
        self.__driver.find_element_by_xpath(retention_time_xpath + "//span[text()='day(s)']").click()
        self.__admin_console.fill_form_by_xpath(xpath=(retention_time_xpath + "//input[@type='number']"),
                                                value=str(days))
        self.__driver.find_element_by_xpath("//button[contains(.,'Save')]").click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def add_user_group(self, group_name, plan=None):
        """Adds user/sharepoint/teams/mailboxes groups to the app
            Args:
                group_name (str)    :   name of the user/sharepoint/teams/mailboxes group
                    Valid Options:
                        For SharePoint -
                            All sites
                            All team sites
                            All Project Online sites
                        For Onedrive -
                            All users
                            AD groups
                        For Teams -
                            All teams
                        For Exchange -
                            All mailboxes
                            AD groups
                            All public folders
                            All O365 group mailboxes

                plan (str)          :   O365 plan name to which the groups need to be associated
        """
        o365_plan = ""
        if plan:
            o365_plan = plan
        else:
            o365_plan = self.o365_plan
        self.__admin_console.access_tab(self.constants.CONTENT_TAB.value)
        self.__rtable.access_toolbar_menu('Add')
        self.__wizard.select_card("Add content to backup")
        self.__wizard.click_next()
        self.__wizard.expand_accordion("Advanced")
        self.__wizard.select_card(group_name)
        self.__wizard.click_next()
        time.sleep(2)
        self.__wizard.click_next()
        self.__wizard.select_drop_down_values(id="cloudAppsPlansDropdown", values=[o365_plan])
        self.log.info(f'Selected Office365 Plan: {o365_plan}')
        self.__wizard.click_next()
        self.__admin_console.click_button("Submit")
        self.__admin_console.wait_for_completion()
        if self.app_type == O365AppTypes.sharepoint:
            return self.get_total_associated_users_count()

    @PageService()
    def remove_user_group(self, group_name):
        """Removes the specified user/sharepoint/teams/mailboxes group from the app
            Args:
                group_name (str)    :   name of auto associated group
        """
        self.__admin_console.access_tab(self.constants.CONTENT_TAB.value)
        self.__rtable.hover_click_actions_sub_menu(
            entity_name=group_name,
            action_item="Manage",
            sub_action_item="Remove from content"
        )
        time.sleep(1)
        self.__admin_console.click_button(id="Save")
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __click_add_service_acc(self):
        """Method to click on add service account"""
        self.__driver.find_element(By.XPATH, "//button[@aria-label='Add service account']").click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def add_service_acc_custom(self, user_email, passw):
        """Adds service account details in configuration page using the Custom config option
            Args:
                user_email(str): User Email of account
                passw (str)    : Password of account

        """
        self.__admin_console.access_tab(constants.O365AppTabs.Configuration.value)
        self.__driver.find_element(By.ID, "serviceAccountsTab").click()
        self.__admin_console.wait_for_completion()
        self.__click_add_service_acc()
        self.__wizard.select_radio_button("Custom configuration (Advanced)")
        self.__wizard.click_next()
        self.__wizard.fill_text_in_field(id='svcAccEmailAddress', text=user_email)
        self.__wizard.fill_text_in_field(id='svcAccPassword', text=passw)
        self.__wizard.fill_text_in_field(id='svcAccConfirmPassword', text=passw)
        self.__wizard.select_radio_button(id='mfaConfirmation')
        self.__wizard.select_radio_button(id='permissionsConfirmation')
        self.__wizard.click_next()
        self.__admin_console.wait_for_completion()
        self.__wizard.click_button("Submit")
        self.__admin_console.wait_for_completion()
        self.__admin_console.access_tab(constants.O365AppTabs.Content.value)
        self.__admin_console.wait_for_completion()

    @PageService()
    def add_user(self, users, plan=None, team_user=False):
        """Adds users to the office 365 app

            Args:
                users (list)    : List of users to be added to the client
                plan (str)     : Name of plan to be selected
                                    //Default: None

                team_user (Boolean) : True if we are trying to add team users otherwise False
                                    //Default : False
        """
        if self.is_react:
            self.__admin_console.access_tab(self.__admin_console.props['label.content'])
            self.__rtable.access_toolbar_menu(self.__admin_console.props['label.add'])
            self.__wizard.select_card("Add content to backup")
            self.__wizard.click_button(id="Submit")
            if self.app_type == O365AppTypes.onedrive:
                self.__wizard.select_card("Users")
            elif self.app_type == O365AppTypes.sharepoint:
                self.__wizard.select_card("Sites")
            elif self.app_type == O365AppTypes.exchange:
                self.__wizard.select_card(self.__admin_console.props['label.mailboxes'])
            elif self.app_type == O365AppTypes.teams:
                if team_user:
                    self.__wizard.select_drop_down_values(id="teamsDropdownForTeamsVsPersonalChat", values=["Users"])
                    self.__wizard.select_card("Users")
                else:
                    self.__wizard.select_card("Teams")
            self.__wizard.click_button(id="Next")
            self.__wait_while_discovery_in_progress()
            for user in users:
                self.__rtable.search_for(user)
                if self.app_type == O365AppTypes.sharepoint:
                    self.__rtable.select_rows([users[user]])
                else:
                    self.__rtable.select_rows([user])
            self.log.info(f'Users added: {users}')
            self.__wizard.click_button(id="Next")
            self.__wizard.select_drop_down_values(id="cloudAppsPlansDropdown",
                                                  values=[plan] if plan else [self.o365_plan])

            self.log.info(f'Selected Office365 Plan: {plan or self.o365_plan}')
            self.__wizard.click_button(id="Next")
            self.__wizard.click_button(id="Submit")
            self.__admin_console.wait_for_completion()
            if self.app_type == O365AppTypes.sharepoint:
                return self.get_total_associated_users_count()
        else:
            self.__admin_console.access_tab(self.constants.ACCOUNT_TAB.value)
            self.__wait_while_discovery_in_progress()
            self.__dropdown.select_drop_down_values(
                values=[plan] if plan else [self.o365_plan],
                drop_down_id=self.constants.O365_PLAN_DROPDOWN_ID.value)
            for user in users:
                search_element = self.__driver.find_element(By.ID, 'searchInput')
                if search_element.is_displayed():
                    self.__admin_console.fill_form_by_id(element_id='searchInput', value=user)
                if self.app_type == O365AppTypes.sharepoint:
                    self.__table.select_rows([users[user]])
                else:
                    self.__table.select_rows([user.split("@")[0]])
            self.log.info(f'Users added: {users}')
            if self.app_type == O365AppTypes.sharepoint:
                self.__modal_dialog.click_submit()
                self.__close_backup_demo_popup()
                return self.get_total_associated_users_count()
            else:
                self.__admin_console.submit_form()
        self.__admin_console.refresh_page()
        self.__close_backup_demo_popup()

    @PageService()
    def add_ad_group(self, groups=None, plan=None):
        """
            Adds AD Group from the Content Tab

            Arguments:-

                groups (list) -- groups you want to associate

                plan (str) -- plan with which you wanna associate
        """
        if plan:
            office365_plan = plan
        else:
            office365_plan = self.o365_plan

        if groups:
            ad_groups = groups
        else:
            ad_groups = self.groups

        self.__admin_console.access_tab('Content')
        if self.is_react:
            self.__rtable.access_toolbar_menu('Add')
            self.__wizard.select_card("Add content to backup")
            self.__wizard.click_next()
            self.__wizard.expand_accordion("Advanced")
            self.__wizard.select_card("AD groups")
            self.__wizard.click_next()
            self.__wait_while_discovery_in_progress()
            for group in ad_groups:
                self.__rtable.search_for(group)
                self.__rtable.select_rows([group])
            self.log.info(f'Groups added: {ad_groups}')
            self.__wizard.click_next()
            self.__wizard.select_drop_down_values(id="cloudAppsPlansDropdown", values=[office365_plan])
            self.log.info(f'Selected Office365 Plan: {office365_plan}')
            self.__wizard.click_next()
            self.__wizard.click_button("Submit")
            self.__admin_console.wait_for_completion()
            self.__admin_console.refresh_page()

    @PageService()
    def add_teams(self, teams, plan=None):
        """Adds teams to the office 365 Teams App.

            Args:
                teams   (list)  :   Teams to be added, list of team names to be provided, team name is of type 'str'.
                plan    (str)   :   Name of plan to be selected
                                    //Default: None
        """
        self.add_user(teams, plan=plan)

    @WebAction(delay=2)
    def _click_remove_from_content(self, entity=None):
        """Clicks the exclude user button under action context menu"""
        if self.is_react:
            self.__rtable.hover_click_actions_sub_menu(entity_name=entity,
                                                       action_item="Manage",
                                                       sub_action_item="Remove from content")

    @PageService()
    def remove_from_content(self, entity=None, is_group=False):
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
                column_name=self.__admin_console.props[column_field])

        # Now remove one user from the app
        self._click_remove_from_content(entity)
        if self.is_react:
            self.__rmodal_dialog.click_submit()
        else:
            self.__modal_dialog.click_submit()
        self.__admin_console.wait_for_completion()

        # Verify that user was removed
        entity_list_new = table.get_column_data(
            column_name=self.__admin_console.props[column_field])
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
        self.__admin_console.wait_for_completion()
        if self.is_react:
            self.__rmodal_dialog.click_submit()
        else:
            self.__modal_dialog.click_submit()
        self.__admin_console.wait_for_completion()
        self.__admin_console.refresh_page()
        entity_type = 'Group' if is_group else 'User'
        self.log.info(f'{entity_type} excluded from backup: {entity}')

    @WebAction(delay=2)
    def _click_include_user(self, entity=None):
        """Clicks the exclude user button under action context menu"""

        if self.is_react:
            self.__rtable.hover_click_actions_sub_menu(entity_name=entity,
                                                       action_item="Manage",
                                                       sub_action_item="Include in backup")

    @PageService()
    def include_in_backup(self, entity=None, is_group=False):
        """
        Includes the given user to backup

        Args:
            user (str):         User which has to be enabled
            is_group (bool):    Whether user/group is to be enabled

        """
        if not is_group:
            self.__rtable.search_for(entity)
        self._click_include_user(entity=entity)
        self.__admin_console.wait_for_completion()
        if self.is_react:
            self.__rmodal_dialog.click_submit()
        else:
            self.__modal_dialog.click_submit()
        self.__admin_console.wait_for_completion()
        self.__rtable.clear_search()
        self.__admin_console.wait_for_completion()
        self.log.info(f'User included to backup: {entity}')

    def verify_mailbox_backup(self, user, processed_backup=True):
        """
            Verifies that backup is either processed/not processed for given user
            Args:
                user (str):         User whose backup has to be verified
                processed_backup (bool):    Whether user backup is supposed to be processed or not
        """

        self.__rtable.search_for(keyword=user)
        last_backup_of_user = (self.__rtable.get_column_data(column_name="Last backup"))[0]
        active_backup_size_of_user = (self.__rtable.get_column_data(column_name="Active backup size"))[0]
        active_items_backed_up_of_user = (self.__rtable.get_column_data(column_name="Active items backed up"))[0]
        self.__rtable.clear_search()
        if processed_backup:
            return last_backup_of_user != 'Not processed' and active_backup_size_of_user != '0' and active_items_backed_up_of_user != '0'
        else:
            return last_backup_of_user == 'Not processed' and active_backup_size_of_user == '0' and active_items_backed_up_of_user == '0'

    @PageService()
    def verify_status_tab_stats(self, job_id, status_tab_expected_stats):
        """Verifies status tab stats in job details page
            Args:
                job_id (str)                     : Job Id of the backup job
                status_tab_expected_stats (dict) : Expected stats of the status tab
                    Example:
                            {
                               "Total":2,
                               "Successful":2,
                               "Successful with warnings":0,
                               "Failed":0,
                               "Skipped":0,
                               "Suspended":0,
                               "To be processed":0
                            }
        """
        self.__jobs.access_job_by_id(job_id)
        self.__access_job_site_status_tab()
        status_tab_stats = self.__process_status_tab_stats(self.__get_status_tab_stats())
        for label, value in status_tab_expected_stats.items():
            if not value == status_tab_stats[label]:
                raise CVWebAutomationException(f"Status tab stats are not validated\n"
                                               f"Expected Stats: {status_tab_expected_stats}\n"
                                               f"Actual Stats: {status_tab_stats}")

    @PageService()
    def verify_site_details(self, expected_sites_details):
        """
        Verifies details of the sites displayed on the sites tab
        Args:
            expected_sites_details (dict):   dictionary of sites along with their details
                Example:
                    {
                        "https://testtenant.sharepoint.com/sites/Test_Automation_Site" :
                            {
                                "Name" : "Site Title",
                                "Last backup" : "Feb 16, 12:48 PM",
                                "Plan" : "O365 Plan",
                                "Size": "1.08 MB",
                                "Site type": "Regular",
                                "Item type": "Site",
                                "Status" : "Active",
                                "Auto discovered" : "Manual"
                            }
                    }
        """
        if not expected_sites_details:
            raise CVWebAutomationException("Please provide sites to verify site details")
        self.__admin_console.access_tab(self.constants.ACCOUNT_TAB.value)
        columns = self.__rtable.get_visible_column_names()
        for site in expected_sites_details:
            expected_sites_details[site]['URL'] = '.../' + '/'.join(site.split('/')[3:])
        self.__rtable.apply_sort_over_column('URL', ascending=False)
        for site, site_details in expected_sites_details.items():
            self.__rtable.apply_filter_over_column('URL', site)
            for column, value in site_details.items():
                if column not in columns:
                    try:
                        self.__rtable.display_hidden_column(column)
                    except ElementNotInteractableException:
                        # Here ElementNotInteractableException is raised though the element is interactable
                        pass
                ui_column_value = self.__rtable.get_column_data(column)[-1]
                if ui_column_value != value:
                    raise CVWebAutomationException(f"Expected value for {column} is {value}, "
                                                   f"displayed value is {ui_column_value}")
            self.__rtable.clear_column_filter('URL', site)

    def change_office365_plan_group(self, group_name, plan_name):
        self.__admin_console.access_tab(self.constants.CONTENT_TAB.value)
        self.__rtable.hover_click_actions_sub_menu(
            entity_name=group_name,
            action_item="Manage",
            sub_action_item="Change plan"
        )
        self.__rmodal_dialog.select_dropdown_values(
            drop_down_id="cloudAppsPlansDropdown",
            values=[plan_name]
        )
        self.__admin_console.click_button(value='Submit')

    @WebAction()
    def __click_app_level_backup(self):
        """
            Clicks the app level backup button on the app page
        """
        self.__driver.find_element(By.ID, "APP_LEVEL_BACKUP").click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def run_client_backup(self):
        """
        Runs backup at client level for any Office365 Client
        """
        self.__click_app_level_backup()
        self.__rmodal_dialog.click_submit()
        job_details = self.__job_details()
        self.log.info('job details: %s', job_details)
        return job_details

    @PageService()
    def run_backup(self):
        """Runs backup by selecting all the associated users to the app"""
        if self.is_react:
            if self.app_type == O365AppTypes.sharepoint:
                self.__admin_console.access_tab(self.constants.ACCOUNT_TAB.value)
            else:
                self.__admin_console.access_tab(self.__admin_console.props['label.content'])
        else:
            self.__admin_console.access_tab(self.constants.ACCOUNT_TAB.value)
        self.__select_all_entities()
        self.__click_backup()
        if self.is_react:
            self.__rmodal_dialog.click_submit()
        else:
            self.__modal_dialog.click_submit()
        job_details = self.__job_details()
        self.log.info('job details: %s', job_details)
        return job_details

    @PageService()
    def start_backup_job(self,user_list=None):
        """
        starts backup by selecting all the associated users to the app and returns job id
        Args:
        user_list(list)   -- list of users           Ex:['user1','user2']
        """
        if self.is_react:
            if self.app_type == O365AppTypes.sharepoint:
                self.__admin_console.access_tab(self.constants.ACCOUNT_TAB.value)
            else:
                self.__admin_console.access_tab(self.constants.CONTENT_TAB.value)
        else:
            self.__admin_console.access_tab(self.constants.ACCOUNT_TAB.value)
        if user_list:
            self.__rtable.select_rows(user_list)
        else:
            self.__select_all_entities()
        self.__click_backup()
        if self.is_react:
            self.__rmodal_dialog.click_submit()
        else:
            self.__modal_dialog.click_submit()

        try:
            job_id = self.__admin_console.get_jobid_from_popup(wait_time=5)
        except CVWebAutomationException:
            self.__driver.find_element(By.XPATH, "//div[@aria-label='More' and @class='popup']").click()
            self.__admin_console.click_button("View jobs")
            self.__jobs.access_active_jobs()
            job_id = self.__jobs.get_job_ids()[0]
        return job_id

    @PageService()
    def process_streams_tab(self,job_id):
        """process streams tab in job details page"""
        try:
            self.__jobs.access_job_by_id(job_id)
            attempts=10
            while attempts!=0:
                self.__admin_console.refresh_page()
                if self.__admin_console.check_if_entity_exists("xpath","//div[@id='jobDetailsPageId']//button[@id='id_Streams']"):
                    self.__driver.find_element(By.XPATH, "//div[@id='jobDetailsPageId']//button[@id='id_Streams']").click()
                    data = self.__rtable.get_column_data(column_name='Num')
                    return data
                time.sleep(30)
                attempts-=1
        except Exception:
            raise CVWebAutomationException('Streams processing exceeded stipulated time')

    @PageService()
    def run_backup_content(self, all_groups=True, groups=None):
        """Runs backup on all groups or by selecting different groups in content tab
            all_groups(boolean) -- if backup needs to run on all groups in cotent tab
                Default: True
            groups (list)       -- name of groups on which backup needs to run, provided only if all_groups is False
                Default: None
        """
        if not all_groups and not groups:
            raise CVWebAutomationException("Groups list is required")
        self.__admin_console.access_tab(self.constants.CONTENT_TAB.value)
        if all_groups:
            self.__select_all_entities()
        else:
            self.__select_entity(groups)
        self.__click_backup()
        self.__rmodal_dialog.click_submit()
        job_details = self.__job_details()
        self.log.info('job details: %s', job_details)
        return job_details

    @PageService()
    def __wait_till_current_discovery_ends(self, time_out=1200, poll_interval=60):
        """
        Wait for the current running discovery to end by checking the discovery running status
        on the Discovery Status panel
        Args:
            time_out (int)                          :   Time out
            poll_interval (int)                     :   Regular interval for check
        """
        attempts = time_out // poll_interval
        while attempts != 0:
            if self._get_discovery_status().lower() != 'completed':
                time.sleep(poll_interval)
                self._refresh_stats()
            else:
                break
            attempts -= 1
        if attempts == 0:
            raise CVWebAutomationException('Discovery exceeded stipulated time.'
                                           'Test case terminated.')

    @PageService()
    def wait_for_discovery_to_complete(self, time_out=1200, poll_interval=60):
        """Waits for discovery to complete and returns last discover cache update time
           Args:
            time_out (int)                          :   Time out
            poll_interval (int)                     :   Regular interval for check
        """
        self.__click_discovery_status_button()
        self.__wait_till_current_discovery_ends(time_out, poll_interval)
        self.__admin_console.click_button("Close")

    @PageService()
    def select_restore_options(self, unconditional_overwrite=True, out_of_place=False, oop_destination=None):
        """Selects the options for restore

            Args:

                unconditional_overwrite (bool)  :       True if you want to overwrite the existing messages
                                                        False if you don't want to overwrite existing messages

                out_of_place            (bool)  :       Whether the restore is in-place or out-of-place

                oop_destination         (dict)  :       Destination location for out-of-place restore
        """
        self.__admin_console.wait_for_completion()
        if not self.__admin_console.check_if_entity_exists('xpath', "//strong[text()='File location']"):
            self.check_file_location_restore=False
        if out_of_place:
            self.__wizard.select_drop_down_values(id="agentDestinationDropdown",
                                                  values=['Restore the data to another location'])
            self.browse_out_of_place_destination(oop_destination)
        else:
            self.__wizard.select_drop_down_values(id='agentDestinationDropdown',
                                                  values=["Restore the data to its original location"])
        self.__wizard.click_next()
        if unconditional_overwrite:
            self.__click_overwrite_radio_button()
        self.__wizard.click_next()
        self.__wizard.click_submit()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __apply_passkey(self,pass_key):
        """
        Apply pass key to do browse or to restore
        Args:
            access_key(str) :   Pass key for the browse page or restore
        """
        self.__admin_console.fill_form_by_id('passkey', pass_key)
        self.__admin_console.click_button("Save")

    @PageService(react_frame=False)
    def run_restore(self, email=None, unconditional_overwrite=True, team_user=None,pass_key=None):
        """Runs the restore by selecting all users associated to the app
            Args:-
                email (str) - email address value to backup

                unconditional_overwrite (bool) -    True if you want to overwrite the existing messages
                                                    False if you don't want to overwrite existing messages

                team_user (str)  - display name or Email id of a user to where chats to be restored.
                                    //Default - None
                pass_key(str)   -   Pass key for the browse page or restore
        """
        self.__admin_console.access_tab(self.constants.ACCOUNT_TAB.value)
        if not email:
            self.__select_all_entities()
        else:
            self.__rtable.apply_filter_over_column(self.constants.EMAIL_ADDRESS_TAB.value, email)
            self.__rtable.select_rows([email])
        self.__click_restore()
        self.select_restore_options(unconditional_overwrite)
        if self.__admin_console.check_if_entity_exists("xpath","//label[@id='passkey-label']"):
            self.__apply_passkey(pass_key)
            self.__wizard.click_submit()
            self.__admin_console.wait_for_completion()
        job_details = self.__job_details()
        self.log.info('job details: %s', job_details)
        return job_details

    @PageService(react_frame=False)
    def start_restore_job(self, unconditional_overwrite=True, user_list=None,team_user=None):
        """Starts the restore by selecting all users associated to the app and returns job id
            Args:-
                user_list(list)   -- list of users           Ex:['user1','user2']

                unconditional_overwrite (bool) -    True if you want to overwrite the existing messages
                                                    False if you don't want to overwrite existing messages

                team_user (str)  - display name or Email id of a user to where chats to be restored.
                                    //Default - None
        """
        self.__admin_console.access_tab(self.constants.ACCOUNT_TAB.value)
        if user_list:
            self.__rtable.select_rows(user_list)
        else:
            self.__select_all_entities()
        self.__click_restore()
        self.__admin_console.wait_for_completion()
        if team_user:
            self.__driver.find_element(By.XPATH, "//button[@id='primaryDestinationBrowseBtn']").click()
            self.__admin_console.wait_for_completion()
            current_table = Table(self.__admin_console, id="discoveryContentTable")
            current_table.search_for(team_user)
            current_table.select_rows([team_user])
            self.__driver.find_element(By.XPATH, "//button[@id='office365OOPBrowseForm_btn_submit']").click()
        self.__expand_restore_options()
        if unconditional_overwrite:
            self.__click_overwrite_radio_button()
        self.__admin_console.submit_form(wait=False)

        try:
            job_id = self.__admin_console.get_jobid_from_popup(wait_time=5)
        except CVWebAutomationException:
            self.__driver.find_element(By.XPATH, "//div[@aria-label='More' and @class='popup']").click()
            self.__admin_console.click_button("View jobs")
            self.__jobs.access_active_jobs()
            job_id = self.__jobs.get_job_ids()[0]
        return job_id

    @PageService()
    def disable_compliance_lock(self, tenant_name):
        """Disables the compliance lock feature
            Args:
                tenant_name(str) : Tenant Name
        """

        self.__navigator.navigate_to_air_gap_protect_storage()
        self.__admin_console.wait_for_completion()
        self.__rtable.search_for(tenant_name)
        self.__rtable.access_link(tenant_name)
        self.__admin_console.access_tab("Configuration")
        self.__admin_console.wait_for_completion()
        self.__RpanelInfo_obj.disable_toggle(self.__admin_console.props['label.softwareWORM'])
        self.__rmodal_dialog.click_yes_button()
        self.__admin_console.wait_for_completion()

    @PageService()
    def delete_office365_app(self, app_name):
        """Deletes the office365 app

                Args:
                    app_name (str)  :   Name of the office365 app to be deleted

        """
        self.__admin_console.access_tab(self.__admin_console.props['office365dashboard.tabs.apps'])
        self.__rtable.access_action_item(app_name, self.__admin_console.props['action.releaseLicense'])
        self.__rmodal_dialog.click_submit()
        time.sleep(30)
        self.__rtable.access_action_item(app_name, self.__admin_console.props['action.delete'])
        self.__rmodal_dialog.type_text_and_delete(text_val='DELETE', checkbox_id='onReviewConfirmCheck')
        self.__admin_console.wait_for_completion()

    @WebAction()
    def _fetch_backup_stats(self):
        """Fetch the Backup stats from the overview page"""
        backup_stats = {"Backup stats": None}
        backup_stats_xpath = "//span[text()='Backup stats']/" \
                             "ancestor::div[contains(@class,'MuiCardHeader-root')]/" \
                             "following-sibling::div//div[@class='kpi-item']/h4"
        backup_parameters_xpath = "//div[@class='kpi-item']/h4[text()='{}']" \
                                  "/following-sibling::h5"

        tags = self.__driver.find_elements(By.XPATH, backup_stats_xpath)
        for tag in tags:
            backup_stats.update({tag.text: None})
            stat = self.__driver.find_element(By.XPATH, backup_parameters_xpath.format(tag.text))
            backup_stats[tag.text] = stat.text
        return backup_stats

    @PageService()
    def fetch_onedrive_overview_details(self):
        """Fetch the overview tab details for OneDrive"""
        self.__admin_console.access_tab(self.constants.OVERVIEW_TAB.value)
        stats_dict = self.__RpanelInfo_obj.get_details()
        calendar_exists = self.__RCalendarView_obj.is_calendar_exists()
        return [stats_dict, calendar_exists]

    @PageService()
    def fetch_exchange_overview_details(self):
        """Fetch the overview tab details for the tab"""
        client_details_dict = dict()
        general_panel = RPanelInfo(self.__admin_console, title="General")
        summary_panel = RPanelInfo(self.__admin_console, title="Summary")
        general_stats = general_panel.get_details()
        backup_stats = self.fetch_backup_stats_for_client()
        summary_stats = summary_panel.get_details()
        client_details_dict.update(general_stats)
        client_details_dict.update(backup_stats)
        client_details_dict.update(summary_stats)
        return client_details_dict

    @WebAction()
    def _click_browse_bread_crumb_item(self, item):
        """Clicks on the specified browse bread crumb item
             Args:
                    item (str)  --  item to be clicked
        """
        self.__driver.find_element(By.XPATH, f"//*[@id='level_0']/a[contains(text(), '{item}')]").click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def click_browse_bread_crumb_item(self, item):
        """Clicks on the specified browse bread crumb item
            Args:
                    item (str)  --  item to be clicked
        """
        return self._click_browse_bread_crumb_item(item)

    @PageService()
    def access_sub_folder_in_browse_tree(self, folder_name):
        """
            To access data inside a folder of a user in browse
            Args:
                    folder_name (str)  --  name of the folder accessed
        """
        self.__treeview.select_items([folder_name])
        self.__admin_console.wait_for_completion()

    @PageService()
    def access_folder_in_browse(self, folder_name):
        """ To access data inside a folder in browse
             Args:
                    foldername (str)  --  name of the folder accessed
        """
        self.__Browse_obj.select_path_for_restore(folder_name, select_items=False)
        self.__admin_console.wait_for_completion()

    @PageService()
    def browse_entity(self, entity_name):
        """Browse the Mailbox/User/Sites for exchange/OneDrive/SharePoint"""
        self.__admin_console.access_tab(self.constants.ACCOUNT_TAB.value)
        if self.app_type == O365AppTypes.sharepoint:
            self.__rtable.apply_filter_over_column(column_name="URL", filter_term=entity_name[0])
            self.__rtable.select_rows([entity_name[1]])
        else:
            self.__rtable.apply_filter_over_column(column_name="Email address", filter_term=entity_name)
            self.__rtable.select_rows([entity_name])
        self.__click_browse()
        self.__admin_console.refresh_page()
        self.__admin_console.wait_for_completion()
        if self.__admin_console.check_if_entity_exists('xpath', "fieldSourceString"):
            self.__driver.find_element(By.XPATH, ".//button[@title='Close' or @aria-label='Close']").click()

    @PageService()
    def get_browse_page_details(self, folder_name):
        """Get the browse page details"""
        Details_Dict = dict()
        Browse_Obj = Browse(admin_console=self.__admin_console, is_new_o365_browse=True)
        Folders = Browse_Obj.get_folders_from_tree_view(folder_name)[1:]
        Details_Dict["Folders"] = Folders
        if self.app_type == O365AppTypes.exchange:
            Details_Dict["No. Of Mails"] = self.__rtable.get_total_rows_count()
        elif self.app_type == O365AppTypes.onedrive:
            Details_Dict["No. Of Folders"] = self.__rtable.get_total_rows_count()
        else:
            Details_Dict["No. Of Entities"] = self.__rtable.get_total_rows_count()
        return Details_Dict

    @PageService()
    def delete_item(self, items_to_delete):
        """Delete items in sites for SharePoint
            Params:
                items_to_delete (list): List of items to delete
                delete_all (bool): Either to delete all items on browse page or only the selected item
        """
        browse_obj = Browse(admin_console=self.__admin_console, is_new_o365_browse=True)
        for item in items_to_delete:
            browse_obj.search_for_content(item)
            browse_obj.access_table_action_item(entity_name=item, action_item='Delete')
            browse_obj.confirm_delete_data_popup()

    @PageService()
    def verify_items_present_in_browse(self, items):
        """Verify items present in browse of SharePoint sites
            Params:
                items (dict):   Stores the names and number of items which should be in browse
                                Example:
                                    items = {'file.txt':1, 'manifest.sml':3}
        """
        self.__admin_console.refresh_page()
        browse_obj = Browse(admin_console=self.__admin_console, is_new_o365_browse=True)
        for item in items:
            browse_obj.search_for_content(item)
            rows = self.__table.get_total_rows_count(search_keyword=item)
            if rows != items[item]:
                raise CVWebAutomationException(f"Could not delete file {item}")

    def go_to_add_app_page(self):
        """ Goes to the CreateO365App page for the type of app """
        create_app_type = {O365AppTypes.teams: 'TEAMS', O365AppTypes.exchange: 'EXCHANGE',
                           O365AppTypes.sharepoint: 'SHAREPOINT', O365AppTypes.onedrive: 'ONEDRIVE'}

        self.__admin_console.navigator.navigate_to_office365()
        self.__admin_console.wait_for_completion()
        add_app = self.__driver.find_element(By.XPATH, "//button[@aria-label='Add Office 365 app']")
        add_app.click()
        self.__admin_console.wait_for_completion()
        app = self.__driver.find_element(By.XPATH, f"//input[@id='{create_app_type[self.app_type]}']/"
                                        f"following-sibling::div")
        app.click()
        self.__admin_console.wait_for_completion()

    def search_and_goto_app(self, app_name: str):
        """ Searches for the app in the App tab of Office365 and visits the client page
                Args:
                    app_name    (str): Name of app to search
        """
        self.__admin_console.navigator.navigate_to_office365()
        xpath = self.__rtable._xpath
        search_box = self.__driver.find_elements(By.XPATH,
                                                 xpath + "//input[contains(@data-testid,'grid-search-input')]")
        val = search_box and search_box[0].is_displayed()
        if val:
            search_xpath = f"{xpath}//button[contains(@class,'grid-search-btn')]"
            if self.__admin_console.check_if_entity_exists("xpath", search_xpath):
                search_btn = self.__driver.find_element(By.XPATH, search_xpath)
                search_btn.click()
            search_box = self.__driver.find_element(By.XPATH,
                                                    xpath + "//input[contains(@data-testid,'grid-search-input')]")
            search_box.clear()
            search_box.send_keys(app_name)
            self.__admin_console.wait_for_completion()
            time.sleep(8)
        self.__admin_console.scroll_into_view(xpath)
        app = self.__driver.find_element(By.XPATH, f"//a[contains(text(),'{app_name}')]")
        app.click()
        self.__admin_console.wait_for_completion()

    def __authorize_permission_custom_config(self, global_admin: str, global_password: str) -> None:
        """Signs in to MS page to acquire token
            Args:
                global_admin (str)  --  Microsoft Global admin email id
                global_password (str)  --  Global admin password
        """
        retry = 5
        while retry > 0:
            retry -= 1
            admin_console_window = self.__driver.window_handles[0]
            azure_window = self.__driver.window_handles[1]
            self.__switch_to_window(azure_window)
            self.__enter_email(global_admin)
            self.__enter_password(global_password)
            try:
                self.__click_submit()
                time.sleep(5)
                if len(self.__driver.window_handles) > 1:
                    if self.__admin_console.check_if_entity_exists("id", "proceed-button"):
                        self.__driver.find_element(By.ID, 'proceed-button').click()
                self.__switch_to_window(admin_console_window)
                self.__admin_console.wait_for_completion()
                break
            except (NoSuchElementException, StaleElementReferenceException, Exception):
                self.__switch_to_window(admin_console_window)

    def __create_o365_app_set_infra(self, acc_node: list = None, ind_server: str = None, jr_path_details: dict = None):
        """ Sets details during creation of O365 app in commvault complete
            Args:
                acc_node        (list): List of names of access nodes to be selected
                                        //Shouldn't be None if plan doesnt have infra settings
                ind_server      (str):  Name of index server to be selected.
                                        //Shouldn't be None if plan doesnt have infra settings
                jr_path_details (dict): dict containing the JR path details.
                                        //Shouldn't be None if multiple proxies, proxy group or local jr is
                                        //not present for proxy
                                        //Structure : {'path': '', 'username':'', 'password':''}
        """
        if self.__admin_console.check_if_entity_exists("id", "IndexServersDropdown"):
            if not acc_node or not ind_server:
                raise Exception(f"Details cannot be empty. {'Access Node,' if not acc_node else ''}"
                                f"{'Index Server' if not ind_server else ''} ")
            self.__driver.find_element(By.ID, "IndexServersDropdown").click()
            time.sleep(5)
            self.__driver.find_element(By.XPATH, f"//span[normalize-space()='{ind_server}']").click()
            time.sleep(3)
            self.__driver.find_element(By.ID, "accessNodeDropdown").click()
            time.sleep(5)
            for node in acc_node:
                search = self.__driver.find_element(By.ID, 'accessNodeDropdownSearchInput')
                search.send_keys(node)
                node_len = len(node)
                self.__driver.find_element(By.XPATH, f"//span[normalize-space()='{node}']").click()
                while node_len:
                    node_len -= 1
                    search.send_keys(Keys.BACKSPACE)
            self.__driver.find_element(By.XPATH, "//button[@aria-label='OK']").click()
            self.__admin_console.wait_for_completion()
            if self.__admin_console.check_if_entity_exists("id", "uncPathInput"):
                if not jr_path_details:
                    raise Exception(f"JR details cannot be empty.")
                self.__admin_console.fill_form_by_id('uncPathInput', jr_path_details['path'])
                self.__driver.find_element(By.XPATH, "//button[@title='Add']").click()
                self.__admin_console.wait_for_completion()
                self.__admin_console.fill_form_by_id('accountName', jr_path_details['username'])
                self.__admin_console.fill_form_by_id('password', jr_path_details['password'])
                self.__admin_console.fill_form_by_id('confirmPassword', jr_path_details['password'])
                self.__driver.find_element(By.XPATH, "//button[@aria-label='Add']/div").click()
                self.__admin_console.wait_for_completion()

    def __create_team_cvpysdk_set_details(self, name: str, server_plan: str, infra_details: dict = None,
                                          cloud: constants.O365Region = None) -> None:
        """ Sets details during creation of O365 teams app in commvault complete
            Args:
                name            (str):  Name to be given to the app
                server_plan     (str):  Server plan for the azure app
                infra_details   (dict): Infrastructure details for app creation.
                                        // Shouldn't be None if plan doesnt have infra settings
                                        // Structure: {"index_server":'', "access_nodes":[],
                                        // "jr_details(optional)":{"path":"", "username":"", "password":""}}
                                        // Default: None
                cloud   (O365Region Enum): Region for the azure app
        """
        self.__admin_console.fill_form_by_id('appNameField', name)
        self.__click_button_if_present('Got it')
        if cloud:
            self.__driver.find_element(By.ID, 'CloudRegionDropdown').click()
            time.sleep(5)
            self.__driver.find_element(By.XPATH, f"//li[@role='menuitem'][@value='{cloud}']").click()
        self.__driver.find_element(By.XPATH, "//button[normalize-space()='Next']").click()
        self.__admin_console.wait_for_completion()
        search = self.__driver.find_element(By.ID, "searchPlanName")
        search.click()
        search.send_keys(server_plan)
        self.__driver.find_element(By.XPATH, f"//span[normalize-space()='{server_plan}']").click()
        self.__driver.find_element(By.XPATH, "//button[normalize-space()='Next']").click()
        self.__admin_console.wait_for_completion()
        if self.__admin_console.check_if_entity_exists("id", "IndexServersDropdown"):
            self.__create_o365_app_set_infra(infra_details.get("access_nodes"), infra_details.get("index_server"),
                                             infra_details.get("jr_details"))
        self.__driver.find_element(By.XPATH, "//button[normalize-space()='Next']").click()

    def create_team_cvpysdk_express(self, name: str, server_plan: str, global_admin: str, global_password: str,
                                    infra_details: dict = None, time_out: int = 600, poll_interval: int = 10) -> str:
        """
        Creates O365 Teams app using express configuration in commvault complete
            Args:
                name            (str):  Name to be given to the app
                server_plan     (str):  Server plan for the azure app
                global_admin    (str):  Global admin email id
                global_password (str):  Password for global admin
                infra_details   (dict): Infrastructure details for app creation.
                                        // Shouldn't be None if plan doesnt have infra settings
                                        // Structure: {"index_server":'', "access_nodes":[],
                                        // "jr_details(optional)":{"path":"", "username":"", "password":""}}
                                        // Default: None
                time_out        (int):  Time out for app creation
                poll_interval   (int):  Regular interval for app creating check

            Returns:
                Name of the app created
        """
        if "createOffice365AppV2".lower() not in self.__driver.current_url.lower():
            self.go_to_add_app_page()
        self.__create_team_cvpysdk_set_details(name, server_plan, infra_details)
        self.__admin_console.fill_form_by_id('globalAdmin', global_admin)
        self.__admin_console.fill_form_by_id('globalAdminPassword', global_password)
        self.__admin_console.checkbox_select('saveGlobalAdminCredsOption')
        self.__admin_console.checkbox_select('mfaConfirmation')
        time.sleep(10)
        self.__admin_console.submit_form()
        attempts = time_out // poll_interval
        while True:
            if attempts == 0:
                raise CVWebAutomationException('App creation exceeded stipulated time.'
                                               'Test case terminated.')
            self.log.info("App creation is in progress..")
            self.__admin_console.wait_for_completion()
            self.__check_for_errors()
            # Check authorize app available
            if self.__admin_console.check_if_entity_exists(
                    "link", self.__admin_console.props['action.authorize.app']) or len(self.__driver.window_handles
                                                                                       ) > 1:
                break
            time.sleep(poll_interval)
            attempts -= 1
        self.__authorize_permissions(global_admin, global_password)
        windows = self.__driver.window_handles
        if len(windows) > 1:
            self.__switch_to_window(windows[1])
            if self.__admin_console.check_if_entity_exists("id", "proceed-button"):
                self.__driver.find_element(By.ID, 'proceed-button').click()
        self.__switch_to_window(windows[0])
        self.__admin_console.wait_for_completion()
        self.__driver.find_element(By.XPATH, "//button[@aria-label='Close']/div").click()
        time.sleep(3)
        self.__driver.find_element(By.XPATH, "//button[@aria-label='Create']").click()
        self.__admin_console.wait_for_completion()
        div_text = self.__driver.find_element(By.XPATH, "//div[@class='text-center mt-2']").text
        app_name = re.search("<b>(.*)</b>", div_text)
        time.sleep(5)  # Wait for Discovery process to launch in access node
        self.app_name = app_name.group(1)
        return app_name.group(1)

    def create_team_cvpysdk_custom(self, name: str, server_plan: str, global_admin: str, global_password: str,
                                   app_details: dict, infra_details: dict = None, time_out: int = 600,
                                   poll_interval: int = 10) -> str:
        """
            Creates O365 Teams app using express configuration in commvault complete
                Args:
                    name            (str):  Name to be given to the app
                    server_plan     (str):  Server plan for the azure app
                    global_admin    (str):  Global admin email id
                    global_password (str):  Password for global admin
                    app_details     (dict): App details
                                            //Structure: {"app_id":"", "dir_id":"", "app_secret":""}
                    infra_details   (dict): Infrastructure details for app creation.
                                        // Shouldn't be None if plan doesnt have infra settings
                                        // Structure: {"index_server":'', "access_nodes":[],
                                        // "jr_details(optional)":{"path":"", "username":"", "password":""}}
                                        // Default: None
                    time_out        (int):  Time out for app creation
                    poll_interval   (int):  Regular interval for app creating check
                    poll_interval   (int):  Regular interval for app creating check

                Returns:
                    Name of the app created
        """
        if "createOffice365AppV2".lower() not in self.__driver.current_url.lower():
            self.go_to_add_app_page()
        self.__create_team_cvpysdk_set_details(name, server_plan, infra_details)
        self.__driver.find_element(By.XPATH, "//input[@id='customConfig']/following-sibling::div").click()
        time.sleep(5)
        self.__admin_console.fill_form_by_id('addAzureApplicationId', app_details.get("app_id"))
        self.__admin_console.fill_form_by_id('addAzureApplicationSecretKey', app_details.get("app_secret"))
        self.__admin_console.fill_form_by_id('addAzureDirectoryId', app_details.get("dir_id"))
        time.sleep(3)
        self.__admin_console.submit_form()
        if self.app_type == O365AppTypes.teams:
            self.__admin_console.checkbox_select('userAccountAddForBackupConfirmation')
        self.__admin_console.checkbox_select('redirectUriSetConfirmation')
        self.__admin_console.checkbox_select('permissionsConfirmation')
        time.sleep(60)
        self.__driver.find_element(By.XPATH, "//button[@label='Acquire token']").click()
        attempts = time_out // poll_interval
        while True:
            if attempts == 0:
                raise CVWebAutomationException('App creation exceeded stipulated time. Test case terminated.')
            self.log.info("App creation is in progress..")
            self.__admin_console.wait_for_completion()
            self.__check_for_errors()
            # Check authorize app available
            if len(self.__driver.window_handles) > 1:
                break
            time.sleep(poll_interval)
            attempts -= 1
        self.__authorize_permission_custom_config(global_admin, global_password)
        self.__driver.find_element(By.XPATH, "//button[@aria-label='Close']/div").click()
        time.sleep(3)
        self.__driver.find_element(By.XPATH, "//button[@aria-label='Create']").click()
        self.__admin_console.wait_for_completion()
        div_text = self.__driver.find_element(By.XPATH, "//div[@class='text-center mt-2']").text
        app_name = re.search("<b>(.*)</b>", div_text)
        time.sleep(5)  # Wait for Discovery process to launch in access node
        self.app_name = app_name.group(1)
        return app_name.group(1)

    def visit_tab(self, tab: constants.O365AppTabs, app_name: str) -> None:
        """Visits the specified tab of O365 app
            tab     (constants.O365AppTabs)    -- Tab to visit
            app_name(str)                       -- Name of the app
        """
        if f"office365/appDetails/".lower() not in self.__driver.current_url.lower() or (
                self.__driver.find_element(By.XPATH, "//span[@class='title-display']").text != app_name):
            self.search_and_goto_app(app_name)
        self.__driver.find_element(By.XPATH, f"//span[normalize-space()='{tab.value}']").click()
        self.__admin_console.wait_for_completion()

    def validate_infra(self, app_name: str, server_plan: str, infra_details: dict = None, global_admin: str = None
                       ) -> bool:
        """Validates the infrastructure settings of O365 app. Make sure the app is on the configuration page
            Args:
                app_name        (str)   -- Name of the app
                server_plan     (str)   -- Server plan expected
                infra_details   (dict)  -- Dictionary of infrastructure settings expected
                    // Structure: {"index_server":'', "access_nodes":[], "jr_details(optional)":{"path":"",
                                    "username":""}}
                    // Default: None
                global_admin    (str)   --  Global admin expected(Not added by default for Custom apps)
            Returns:
                True if infrastructure settings are successfully verified

            Raises:
                Exception if settings do not match
        """
        details = None
        self.visit_tab(constants.O365AppTabs.Configuration, app_name)
        while True:
            try:
                details = RPanelInfo(self.__admin_console).get_details()
                break
            except Exception as exp:
                if "stale element reference" in str(exp):
                    continue
                else:
                    raise CVWebAutomationException(str(exp))
        if global_admin and details['Global Administrator'].lower().strip() != global_admin.lower():
            raise Exception(f"Global admin does not match. Expected: {global_admin.lower()}, Got: " +
                            details['Global Administrator'].lower().strip())
        if details['Server plan'].lower().strip() != server_plan.lower():
            raise Exception("Server Plan does not match Expected: {server_plan.lower()}, Got: " +
                            details['Server plan'].lower().strip())
        if not infra_details:
            return True
        if details['Index Server'].lower().strip() != infra_details.get("index_server").lower():
            raise Exception("Index Server does not match. Expected: {infra_details.get('index_server')}, Got: " +
                            details['Index server'].lower().strip())
        cc_details = details['Access nodes'].split("\n")
        cc_acc_nodes = cc_details[0].split(",")
        acc_nodes = [z.lower() for z in infra_details.get('access_nodes', [])]
        if len(cc_acc_nodes) != len(acc_nodes):
            raise Exception(f"Access node list do not match. Expected: {acc_nodes}, Got:{cc_acc_nodes}")
        for proxy in cc_acc_nodes:
            if proxy.strip().lower() not in acc_nodes:
                raise Exception(f"{proxy} not present in list of input access nodes")
        if not infra_details.get("jr_details"):
            return True
        if cc_details[1].strip().lower() != infra_details.get("jr_details").get("username", "").lower():
            raise Exception(f"Job directory username does not match. Expected: "
                            f"{infra_details.get('jr_details').get('username', '').lower()}, "
                            f"Got:{cc_details[2].strip().lower()}")
        if cc_details[-1].strip().lower() != f"{infra_details.get('jr_details').get('path', '').lower()}\\jobresults":
            raise Exception(f"Job Results directory do not match. Expected: "
                            f"{infra_details.get('jr_details').get('path', '').lower()}, "
                            f"Got:{cc_details[-1].strip().lower()}")
        return True

    def add_teams_react(self, teams: list, plan: str) -> None:
        """Adds teams to the office 365 Teams App.

            Args:
                teams   (list)  :   Teams to be added, list of team names to be provided, team name is of type 'str'.
                plan    (str)   :   Name of plan to be selected
        """
        self.visit_tab(constants.O365AppTabs.Content, self.app_name)
        self.__driver.find_element(By.XPATH, "//button[@aria-label='Add']/div[normalize-space()='Add']").click()
        self.__admin_console.wait_for_completion()
        self.__driver.find_element(By.ID, "teams").click()
        self.__driver.find_element(By.XPATH, "//button[normalize-space()='Next']").click()
        time.sleep(5)
        self.__admin_console.wait_for_completion()
        if not self.__admin_console.check_if_entity_exists("xpath", "//tr[@class='k-master-row k-alt  ']"):
            attempts = 30
            self.__driver.find_element(By.XPATH, "//button[@aria-label='Reload data']").click()
            while attempts:
                attempts -= 1
                if self.__admin_console.check_if_entity_exists("xpath", "//tr[@class='k-master-row k-alt  ']"):
                    break
                time.sleep(30)
        search = self.__driver.find_element(By.XPATH, "//input[@aria-label='grid-search']")
        search.clear()
        for team in teams:
            team = team.strip()
            length = len(team)
            search.send_keys(team)
            self.__admin_console.wait_for_completion()
            temp = self.__driver.find_element(By.XPATH, f"//td[normalize-space()='{team}']")
            elem = temp.find_element(By.XPATH, "..")
            elem.click()
            while length:
                length -= 1
                search.send_keys(Keys.BACKSPACE)
        self.__driver.find_element(By.XPATH, "//button[normalize-space()='Next']").click()
        self.__admin_console.wait_for_completion()
        self.__driver.find_element(By.ID, "cloudAppsPlansDropdown").click()
        time.sleep(3)
        self.__driver.find_element(By.XPATH, f"//div[@title='{plan}']").click()
        self.__driver.find_element(By.XPATH, "//button[normalize-space()='Next']").click()
        self.__admin_console.wait_for_completion()
        self.__driver.find_element(By.XPATH, "//button[@aria-label='Submit']/div").click()
        self.__admin_console.wait_for_completion()
        self.log.info("Added teams successfully")

    def verify_added_teams(self, teams: list, app_name: str = None) -> bool:
        """Verifies if the teams are associated with client
            Args:
                teams   (list)  -- List of teams name
                app_name (str)  --  Name of the app to check against
                    //Default:  None

            Returns:
                Boolean result
        """
        self.visit_tab(constants.O365AppTabs.Teams, self.app_name if not app_name else app_name)
        for team in teams:
            try:
                self.log.info(f"Checking if team: {team} is added to client")
                self.__driver.find_element(By.XPATH, f"//a[normalize-space()='{team}']")
            except NoSuchElementException:
                return False
            except Exception:
                return False
        self.log.info("Verified teams successfully")
        return True

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
            self.__navigator.navigate_to_office365()
            self.access_office365_app(client_name)
            job_details = self._create_recovery_point_by_mailbox(mailbox)
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
            self.__navigator.navigate_to_office365()
            self.access_office365_app(client_name)
            self._restore_from_recovery_point(recovery_id)

    @PageService()
    def perform_restore_operation(self):
        """Perform restore operation in the browse page"""
        if self.app_type == O365AppTypes.exchange:
            self.__click_mailbox()
        self.__admin_console.wait_for_completion()
        if int(self.__rtable.get_total_rows_count()) > 0:
            self.__rtable.select_all_rows()
        self.__driver.find_element(By.XPATH, "//button[@id='RESTORE']").click()
        self.select_restore_options()
        restore_job_details = self.__job_details()
        self.log.info('Restore job details: %s', restore_job_details)
        return restore_job_details

    @PageService()
    def click_download_file(self, export_name):
        """Clicks download file of export from view exports table
                Args:
                    export_name (str)  --  Name of the export
        """
        self.__rtable.access_action_item(export_name, self.__admin_console.props['action.download'])
        self.__rmodal_dialog.click_cancel()  # this click cancel actually clicks close button

    @PageService()
    def get_export_size(self, export_name):
        """Read size column value from view exports table
                Args:
                    export_name (str)  --  Name of the export
        """
        self.__rtable.search_for(export_name)
        __export_rtable = Rtable(self.__admin_console,
                                 xpath="//div[contains(@class,'k-widget k-grid teer-grid teer-grid-no-grouping')]")
        export_size = (__export_rtable.get_column_data(column_name=self.__admin_console.props['column.size']))[-1]
        self.__rtable.clear_search()
        return export_size

    @WebAction(delay=2)
    def _click_view_exports(self):
        """Clicks the view exports link from the browse page"""
        view_exports_xpath = "//span[contains(text(),'View exports')]"
        self.__driver.find_element(By.XPATH, view_exports_xpath).click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def click_view_exports(self):
        """
            Click view exports
        """
        self._click_view_exports()

    @WebAction()
    def __get_num_selected_mails(self):
        """
            Gets number of selected mails from the export modal
        """
        selected_mails_element = self.__driver.find_element(By.XPATH, "//input[@type = 'radio'][@value='Selected']/../span")
        num_mails = int(re.findall(r'\d+', selected_mails_element.text)[0])
        return num_mails

    @PageService()
    def perform_export_operation(self, client_name, export_as=None, file_format=None):
        """
        Perform export operation on the client
        client_name (str) : Client Name
        export_as   (str) : Type of Export that needs to be done
                            For Exchange agents only
                            Valid Arguments
                                -- PST  (for PST export)
                                -- CAB  (for CAB export)
        """
        export_filename = None
        if self.app_type == O365AppTypes.exchange:
            self.__click_mailbox()
            self.__admin_console.wait_for_completion()
            self.__rtable.select_all_rows()
            self.__click_export()
            self.__admin_console.wait_for_completion()
            if export_as == "PST":
                export_filename = f"PST_{client_name}_Exchange"
                self.__admin_console.select_radio(id="exportTypePST")
            elif export_as == "CAB":
                if not file_format:
                    file_format = "MSG"
                export_filename = f"CAB_{file_format}_{client_name}_Exchange"
                self.__admin_console.select_radio(id="exportTypeCAB")
                if file_format == "EML":
                    self.__admin_console.select_radio(id="fileExtensionTypeEML")
                else:
                    self.__admin_console.select_radio(id="fileExtensionTypeMSG")
            else:
                raise Exception("Please pass the type of export for the mails")
        self.__admin_console.fill_form_by_id(element_id="exportName", value=export_filename)
        self.__admin_console.submit_form()
        export_job_details = {
            "ExportFileName": export_filename,
            "AgentName": self.app_type.value,
        }
        self.__admin_console.wait_for_completion()
        export_job_details.update(self.__job_details())
        self.log.info("Export job details: %s", export_job_details)
        return export_job_details

    @PageService()
    def perform_download_operation(self):
        """Perform download operation for the message
        returns
        dict() : detail of the downloaded mail
        """
        if self.app_type == O365AppTypes.exchange:
            if int(self.__table.get_total_rows_count()) > 0:
                mails = self.__table.get_table_data()
                import re
                mail_dict = dict()
                mail = re.sub(r'\n+', '\n', mails["Received time"][0]).split('\n')
                mail_dict["Sender"] = mail[0]
                mail_dict["Time"] = mail[1]
                mail_dict["Subject"] = mail[2]
                mail_dict["Size"] = mail[3]
                self.__cvactions_toolbar.select_action_sublink(text="Download", expand_dropdown=False)
                self.__admin_console.wait_for_completion()
                status = self._verify_downloaded_file_details(mail_details=mail_dict)
                mail_dict.update({"File Downloaded": status})
                return mail_dict
            else:
                raise CVWebAutomationException("There are no mails to display. Please check.")

    @PageService()
    def get_self_service_user_dashboard_details(self):
        """
        Fetches the self service Dashboard details for the user which is self service enabled
        Returns
        (dict) :- Self Service Dashboard Details
        """
        dashboard_details = {}
        dashboard = DashboardTile(self.__admin_console)
        self_service_user = dashboard.get_self_service_user()
        self.log.info("User name is {}".format(self_service_user))
        dashboard_details["User"] = self_service_user
        self_service_clients_details = dashboard.get_all_details()
        self.log.info("User is associated to these clients: {}".format(self_service_clients_details))
        user_mappings = dashboard.get_user_mappings()
        self.log.info("Mappings of the user with Exchange and Onedrive agents {}".format(user_mappings))
        dashboard_details["AssociationByAgent"] = user_mappings
        dashboard_details["ClientDetailsInfo"] = self_service_clients_details
        return dashboard_details

    @PageService()
    def get_self_service_user_details_by_client(self, client_name):
        """Get the details for a self service enabled user for any particular client
        Args:-
            client_name (str) :- Client name to which that user is associated
        Return:-
            client_details (dict)
        """
        details_panel = None
        backup_stats = None
        dashboard = DashboardTile(self.__admin_console)
        dashboard.click_details_by_client(client_name)
        if self.app_type == O365AppTypes.exchange:
            details_panel = RPanelInfo(self.__admin_console, title="Mailbox details")
            backup_stats = RPanelInfo(self.__admin_console, title="Backup stats")
        elif self.app_type == O365AppTypes.onedrive:
            details_panel = RPanelInfo(self.__admin_console, title="User details")
            backup_stats = RPanelInfo(self.__admin_console, title="Backup stats")
        client_details_dict = details_panel.get_details()
        backup_stats_dict = backup_stats.get_details()
        client_details_dict.update(backup_stats_dict)
        return client_details_dict

    @PageService()
    def perform_operations_on_self_user_client(self, client_name, operation, export_as=None):
        """
        Perform operations for the self service enabled user on the client
        client_name (str)   : Name of the client
        operation   (str)   : Operation you want to perform on the client
                              For Restore operation = Restore
                              For Export operation = Export
                              For Download operation = Download
        export_as   (str)   : Only for Exchange App Type Clients
                              For PST use export_as = PST
                              For CAB use export_as = CAB
        """
        dashboardTile = DashboardTile(self.__admin_console)
        dashboardTile.click_restore_by_client(client_name)
        self.__admin_console.wait_for_completion()
        if operation == "Restore":
            job_details = self.perform_restore_operation()
        elif operation == "Export":
            job_details = self.perform_export_operation(client_name, export_as)
        elif operation == "Download":
            job_details = self.perform_download_operation()
        else:
            raise Exception("Operation is passed as NoneType")
        return job_details

    @PageService()
    def verify_export_file_details_for_self_service_user(self, client_name, export_job_details, verify_download=False):
        """Verifies the export file details in View Exports for Self Service User
        client_name(str) -- Name of the client
        export_job_details(dict) -- job details of the export job
        """
        dashboard = DashboardTile(self.__admin_console)
        dashboard.click_details_by_client(client_name)
        page_container = PageContainer(self.__admin_console, id_value="selfServiceDetailsPage")
        page_container.access_page_action("View exports")
        export_file_details = self._get_export_file_details(file_name=export_job_details["ExportFileName"])
        if export_file_details:
            if export_file_details["Name"] == export_job_details["ExportFileName"]:
                self.log.info("{} File is present in View exports".format(export_job_details["ExportFileName"]))
            else:
                raise CVWebAutomationException("Export file with the name {} does not exist. Please check".format(
                    export_job_details["ExportFileName"]))
            if export_file_details["Job ID"] == export_job_details["Job Id"]:
                self.log.info("Job Id is verified")
            else:
                raise CVWebAutomationException(
                    "Job ID shown for the file is different from the Export Job ID. Please check.")
            if export_file_details["Creation time"] and export_job_details["Start time"]:
                export_file_date_time = export_file_details["Creation time"].split()
                export_file_date = '{0} {1} {2}'.format(export_file_date_time[0], export_file_date_time[1],
                                                        export_file_date_time[2])
                export_job_date_time = export_job_details["Start time"].split()
                export_job_date = '{0} {1} {2}'.format(export_job_date_time[0], export_file_date_time[1],
                                                       export_file_date_time[2])
                if export_file_date == export_job_date:
                    self.log.info("Job date and file creation date matched")
                else:
                    raise CVWebAutomationException("Job date and file creation date is not matching. Please check")
            else:
                raise CVWebAutomationException(
                    "Date Parameter is not present in Export job details or Export file details Please check")
        else:
            raise CVWebAutomationException("Exported file details are not fetched properly. Please check.")
        if verify_download:
            self.__table.select_rows([export_file_details["Name"]])
            self.__table.access_action_item(entity_name=export_file_details["Name"], action_item="Download",
                                            partial_selection=True)
            # Waiting for the file to download
            time.sleep(50)
            if self._verify_downloaded_file_details(export_file_details=export_file_details):
                self.log.info("Export file is successfully downloaded")
            else:
                raise CVWebAutomationException("File did not download. Please check once")
        self.log.info("Deleting the export file view exports")
        self.__table.access_action_item(entity_name=export_file_details["Name"], action_item="Delete")
        self.__modal_dialog.click_submit()
        self.__admin_console.wait_for_completion()
        message = self.__admin_console.get_notification()
        if message == "Selected exports deleted successfully.":
            self.__modal_dialog.click_cancel()
        else:
            raise CVWebAutomationException(
                "Exports were not deleted and reported the error message as {}".format(message))

    @PageService()
    def fetch_preview_of_mails_for_self_service_user(self):
        """Verify preview of the mail which is visible for self service user
        """
        self.__admin_console.unswitch_to_react_frame()
        browse_table = Table(admin_console=self.__admin_console, id="exchangeBrowseTable")
        self.log.info("Fetching the table data")
        mails = browse_table.get_table_data()
        mail_list = []
        for row in mails["Received time"]:
            mail_dict = {}
            mail = re.sub(r'\n+', '\n', row).split('\n')
            mail_dict["Sender"] = mail[0]
            mail_dict["Time"] = mail[1]
            mail_dict["Subject"] = mail[2]
            mail_dict["Size"] = mail[3]
            mail_list.append(mail_dict)
        self.log.info("Fetching review of mails")
        browse_table.deselect_rows([mail_list[0]["Subject"]])
        for mail in mail_list:
            browse_table.select_rows([mail["Subject"]])
            self.__admin_console.wait_for_completion()
            self.__admin_console.unswitch_to_react_frame()
            self.__driver.switch_to.frame("iframeForPreview")
            element = self.__driver.find_element(By.XPATH, "/html/body")
            mail["Preview"] = element.text
            self.__admin_console.unswitch_to_react_frame()
            browse_table.deselect_rows([mail["Subject"]])
        return mail_list

    @PageService()
    def fetch_backup_stats_for_client(self):
        """Fetches and returns the backup stats for the client"""
        self.__admin_console.access_tab(self.constants.OVERVIEW_TAB.value)
        return self.__get_backup_stats()

    @PageService()
    def fetch_licensed_users_for_client(self):
        """Fetches and returns licensed users for the client"""
        LicensedUserList = list()
        self.__admin_console.access_tab(self.constants.ACCOUNT_TAB.value)
        column_names = self.__rtable.get_visible_column_names()
        if "O365 license" not in column_names:
            self.__rtable.display_hidden_column("O365 license")
        data = self.__rtable.get_table_data()
        for key in data:
            if key == "O365 license":
                for column_value in data[key]:
                    if column_value == "Licensed":
                        licensedUser = dict()
                        index = data[key].index(column_value)
                        licensedUser["User Name"] = data["Name"][index]
                        licensedUser["Email Address"] = data["Email address"][index]
                        licensedUser["Agent Name"] = self.app_type.value
                        licensedUser["License Type"] = data["O365 license"][index]
                        LicensedUserList.append(licensedUser)
        return LicensedUserList

    @PageService()
    def click_agent_overview_for_backup_size(self):
        """Clicks the agent backup size to display the active, inactive and total size"""
        if self.app_type == O365AppTypes.exchange:
            agent = "ExchangeStats"
        elif self.app_type == O365AppTypes.onedrive:
            agent = "OneDriveStats"
        elif self.app_type == O365AppTypes.sharepoint:
            agent = "SharePointStats"
        else:
            agent = "TeamsStats"
        self.__click_agent_overview_to_show_backup_data(agent)


    @WebAction()
    def change_capacity_usage(self):
        """Changes the capacity usage to all backup version if it is latest and vice-versa"""
        self.__navigator.navigate_to_company()
        if self.__admin_console.check_if_entity_exists(By.XPATH, "//div[contains(text(),'All backed-up versions')]"):
            self.__driver.find_element(By.XPATH, "//div[contains(text(),'backed-up versions')]"
                                                 "/following-sibling::div//button[@title='Edit']").click()
            self.__rmodal_dialog.select_dropdown_values(drop_down_id='capacityUsageDropdown',
                                                        values=["Latest versions only"])
            self.__rmodal_dialog.click_submit()
            self.__rmodal_dialog.fill_text_in_field(element_id="confirmText", text="Latest versions only")
        else:
            self.__driver.find_element(By.XPATH,
                                       "//div[contains(text(),'Latest versions')]"
                                       "/following-sibling::div//button[@title='Edit']").click()
            self.__rmodal_dialog.select_dropdown_values(drop_down_id='capacityUsageDropdown',
                                                        values=["All backed-up versions"])
            self.__rmodal_dialog.click_submit()
            self.__rmodal_dialog.fill_text_in_field(element_id="confirmText", text="All backed-up versions")
        self.__rmodal_dialog.click_submit()


    @PageService()
    def fetch_agent_active_inactive_capacity(self):
        """Fetches the active, inactive and total capacity for one agent"""
        self.__admin_console.access_tab(self.__admin_console.props['office365dashboard.tabs.overview'])
        self.click_agent_overview_for_backup_size(self.app_type)
        data = self.__container_table.get_table_data()
        self.__rmodal_dialog.click_close()
        return data

    @PageService()
    def fetch_capacity_usage_report(self):
        """Fetches the capacity usage report and returns it in a dictionary"""
        capacity_usage_report = dict()
        self.__admin_console.select_hyperlink(link_text="Office 365 - Capacity")
        capacity_usage_report.update(self._get_purchased_additional_or_licensed_usage())
        capacity_usage_report.update(self._get_total_capacity_usage())
        capacity_usage_report.update(self._get_monthly_usage())
        return capacity_usage_report

    @PageService()
    def fetch_license_usage_report(self):
        """Fetches the licensed users from the enterprise report"""
        license_usage_report = dict()
        self.__admin_console.select_hyperlink(link_text="Office 365 - Enterprise")
        license_usage_report.update(self._get_purchased_additional_or_licensed_usage())
        license_usage_report.update(self._get_total_licensed_users())
        license_usage_report.update(self._get_monthly_usage())
        return license_usage_report

    @PageService()
    def perform_point_in_time_restore(self, restore_dict, job_details=None):
        """
        Performs point in time restore at the client level and entity level for a client
        restore_dict (dict)  -  Ex: {"ClientLevel": True/False,"Entity": "<entity_name>","Job ID": <job_id>}
        returns:
        SharePoint -
            backup_application_size(float), restore_application_size(float)
        Other Agents -
            backup_count(int),restore_job_details(dict)
        """
        if not job_details:
            job_details = self.__get_job_details(restore_dict["Job ID"])
        year, month, date, start_time = self._get_job_starting_time(job_details)
        backup_count = int(job_details[self.__admin_console.props['label.noOfObjectsBackedup']])
        time_dict = {
            "day": date,
            "month": month,
            "year": year,
            "time": start_time
        }
        restore_job_details = None
        self.__navigator.navigate_to_office365()
        self.__admin_console.wait_for_completion()
        self.access_office365_app(job_details[self.__admin_console.props['Source\\ Client\\ Computer']][:-2])
        self.__admin_console.wait_for_completion()
        if restore_dict["ClientLevel"]:
            self.__admin_console.access_tab(self.constants.OVERVIEW_TAB.value)
        else:
            self.__admin_console.access_tab(self.constants.ACCOUNT_TAB.value)
            self.__rtable.access_link(restore_dict["Entity"])
        self.__admin_console.wait_for_completion()
        recovery_calendar = RCalendarView(self.__admin_console)
        if recovery_calendar.is_calendar_exists():
            language = self.__admin_console.get_locale_name()
            if language == "en":
                recovery_calendar.select_date(time_dict)
            else:
                self.__click_day_in_calender_view(date)
            if restore_dict["ClientLevel"]:
                recovery_calendar.select_time(start_time)
                self.__admin_console.wait_for_completion()
            self.__click_restore_recovery_point()
            self.__admin_console.wait_for_completion()
            restore_job_details = self.perform_restore_operation()
            if self.app_type == O365AppTypes.sharepoint:
                if (restore_job_details['To be restored'] == restore_job_details['Skipped files'] or
                        restore_job_details['No of files restored'] == '0' or restore_job_details['Failures'] !=
                        '0 Folders, 0 Files'):
                    raise CVWebAutomationException(f'Restore did not complete successfully')
                backup_application_size = float(job_details['Size of application'][:-3])
                restore_application_size = float(restore_job_details['Size of application'][:-3])
                return backup_application_size, restore_application_size
            else:
                return backup_count, restore_job_details
        else:
            raise CVWebAutomationException("Calender not present. Unknown error.")

    @WebAction()
    def _select_backupset_level_restore(self, contents, entire_content=False):
        """Selects rows in Content tab and clicks restores entire content

            Args:

                contents    (list)  :       Content URLs to select
        """
        self.__rtable.select_rows(contents)
        self.__driver.find_element(By.ID, 'RESTORE_SUBMENU').click()
        self.__admin_console.wait_for_completion()
        if entire_content:
            self.__driver.find_element(By.ID, 'RESTORE_ENTIRE_CONTENT').click()
        else:
            self.__driver.find_element(By.ID, 'BROWSE').click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def _click_item_in_browse_tree_view(self, item):
        """Method to expand company selection drop down
            Args:
                    item (str)  --  item to be clicked
        """
        self.__driver.find_element(
            By.XPATH, f"//li[@role='treeitem']//span[contains(text(), '{item}')]").click()

    @WebAction()
    def click_item_in_browse_tree_view(self, item):
        """Method to expand company selection drop down
            Args:
                    item (str)  --  item to be clicked
        """
        self._click_item_in_browse_tree_view(item)
        self.__admin_console.wait_for_completion()

    @WebAction()
    def _select_content_for_restore(self, contents, url=None):
        """Selects rows in Content tab and clicks restore

            Args:

                contents    (list)  :       Content names to select

                url         (str)   :       Root URL to navigate (give this arg when multiple sites are selected)
        """
        if url:
            self.click_item_in_browse_tree_view(url)
        self.click_item_in_browse_tree_view('Contents')

        self.__rtable.select_rows(contents)
        self.__driver.find_element(By.ID, 'RESTORE').click()
        self.__admin_console.wait_for_completion()

    @PageService()
    def browse_out_of_place_destination(self, destination):
        """Browses for the out-of-place destination

            Args:

                destination (dict)  :       OOP Destination
                                            Example: {
                                                'https://contoso.sharepoint.com/sites/Site1': 'Site1'
                                            }

        """
        url, name = list(destination.items())[0]
        self.__wizard.click_icon_button_by_title('Browse')
        self.__rtable.search_for(url)
        self.__admin_console.wait_for_completion()
        self.__rtable.select_rows([name])
        self.__rmodal_dialog.click_submit()

    @PageService()
    def _get_job_id_from_wizard(self):
        """Gets Job ID from a React wizard alert"""
        text = self.__wizard.get_alerts()
        return re.findall(r'\d+', text)[0]

    @PageService()
    def initiate_oop_restore(self, backup_site, oop_site, library=None):
        """Initiate an out-of-place site level restore

            Args:

                backup_site (dict)      :   Source site to restore from
                oop_site    (dict)      :   Destination OOP site
                library     (str)       :   If provided, will restore the document library instead of site

            Returns:
                job_id      (str)       :   Job ID of the restore job
        """

        self.__admin_console.access_tab(self.constants.ACCOUNT_TAB.value)
        _, name = list(backup_site.items())[0]
        self._select_backupset_level_restore([name], not bool(library))
        self.__admin_console.wait_for_completion()
        if library:
            self._select_content_for_restore([library])
        self.select_restore_options(out_of_place=True, oop_destination=oop_site)
        return self._get_job_id_from_wizard()

    @WebAction(delay=2)
    def _click_ci_path(self):
        """Clicks the content indexing job link"""
        ci_xpath = "//li[@id='CONTENT_INDEXING']"
        self.__driver.find_element(By.XPATH, ci_xpath).click()

    @PageService()
    def run_content_indexing(self, client_name):
        """
        Runs the Content Indexing from Client
        Args:
            client_name(str): name of the client
        """
        self.__admin_console.refresh_page()
        self.search_and_goto_app(client_name)
        self.__admin_console.access_tab(self.constants.ACCOUNT_TAB.value)
        self.__select_all_entities()
        self.__RpanelInfo_obj.click_button(button_name='More')
        self._click_ci_path()
        self.__rmodal_dialog.click_submit(wait=False)
        job_details = self.__job_details()
        if job_details[self.__admin_console.props['Status']] != 'Completed':
            raise CVWebAutomationException('Job did not complete successfully')
        return job_details

    @PageService()
    def validate_content_indexing(self, app_name):
        """
            Verify CI Job triggered or not after Backup
            Returns:
                ci_items_cnt (int)
        """
        self.__navigator.navigate_to_jobs()
        self.__jobs.access_job_history()
        self.__jobs.show_admin_jobs()
        self.__jobs.add_filter(column='Destination client', value=app_name)
        self.__jobs.add_filter(column='Operation', value='Content Indexing')
        current_job_ids = self.__jobs.get_job_ids()

        if current_job_ids:
            jobid = current_job_ids[0]
            self.__jobs.access_active_jobs()
        else:
            self.__jobs.add_filter(column='Destination client', value=app_name)
            self.__jobs.add_filter(column='Operation', value='Content Indexing')
            jobid = self.__jobs.get_job_ids()

        try:
            ci_job_details = self.__jobs.job_completion(jobid)
            if ci_job_details['Status'] != 'Completed':
                raise CVTestStepFailure(f'Content Indexing job not completed successfully')
            self.log.info(f"Job details are: {ci_job_details}")
        except Exception as exp:
            self.log.info(exp)
            raise CVTestStepFailure(f'Problem with Content Indexing job starting/completing')

        ci_items_cnt = int(ci_job_details['Successful messages'])
        if ci_items_cnt == 0:
            self.log.info(f'CI Items count is zero, so re-trigger the CI')
            ci_job_details = self.run_content_indexing(app_name)
            ci_items_cnt = int(ci_job_details['Successful messages'])

        return ci_items_cnt

    @PageService()
    def edit_streams(self,max_streams):
        """
        edits the max streams in configuration page
        max_streams (int): streams, Ex: 5
        """
        self.__edit_streams(max_streams)
        self.__admin_console.wait_for_completion()

    @PageService()
    def get_rows_from_browse(self):
        """
        navigates to browse and return rows count
        """
        self.__click_app_restore()
        return int(self.__table.get_total_rows_count())

    @PageService()
    def goto_office365_app(self, app_name):
        """go to the Office365 app from the Office365 landing page

                Args:
                    app_name (str) : Name of the Office365 app to access

        """
        self.__navigator.navigate_to_office365()
        self.__admin_console.access_tab(self.__admin_console.props['office365dashboard.tabs.apps'])
        self.__rtable.access_link(app_name)

    def verify_sharepoint_restore_restartability(
            self, sp_api_object, restore_job_id, library_title, files_backed_up):
        """Verifies the restore restartability for the given Job ID

            Args:

                sp_api_object   (SharePointOnline)  :   API object to validate restore restartability

                restore_job_id  (str)               :   Job ID of the OOP restore

                library_title   (str)               :   Title of the library to validate restore for

                files_backed_up (int)               :   Number of files backed up in the library

            Returns:

                dict                                :   Job details of the restore job

        """
        files_count = []
        for _ in range(2):
            sp_api_object.wait_for_library_to_populate(library_title, 1)
            try:
                self.__navigator.navigate_to_jobs()
                self.__jobs.suspend_job(restore_job_id, duration='Indefinitely', wait=600)
                self.log.info('Waiting for some time for the document library to get updated')
                sp_api_object.cvoperations.wait_time(30)
                files_count.append(sp_api_object.delete_files_in_sp_library(library_title))
                self.__jobs.resume_job(restore_job_id)
            except Exception as e:
                self.log.error(f'Error while performing suspend cycle: {e}')
                raise

        self.__jobs.job_completion(restore_job_id)

        files_count.append(sp_api_object.get_file_count_in_sp_library(library_title))
        files_restored = sum(int(c) for c in files_count)
        self.log.info(f"{files_restored = }")
        if abs(files_restored - files_backed_up) > 50:
            raise Exception(f'Restore did not restart at point of failure. {files_restored} files were '
                            f'restored, but {files_backed_up} were backed up')

        self.log.info('Restore restarted at point of failure successfully')

    def get_backupset_id(self):
        """Returns the backupset id of the current Office365 app"""
        url = self.__driver.current_url
        backupset_id = url.rsplit('/', 2)[1]
        return backupset_id

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

    @WebAction(delay=0)
    def _get_number_of_tiles(self):
        """ Fetch the number of tiles
        Returns
            (int) : number of tiles
        """
        tiles = self.__driver.find_elements(By.XPATH, self.__base_xpath)
        return len(tiles)

    @WebAction(delay=0)
    def _get_values(self, index):
        """
        Gets the values beside each column
        Returns
            (List) : values beside the columns
        """
        value_xpath = f"{self.__base_xpath}[{index}]//tbody//th"
        values = self.__driver.find_elements(By.XPATH, value_xpath)
        return [value.text for value in values]

    @WebAction(delay=0)
    def _get_columns(self, index):
        """
        Get the columns from the tile
        Returns
            (list) : Column Names
        """
        columns_xpath = f"{self.__base_xpath}[{index}]//tbody//td"
        columns = self.__driver.find_elements(By.XPATH, columns_xpath)
        return [column.text for column in columns]

    @WebAction(delay=0)
    def _get_agent_by_tile(self, index):
        """
        Fetches the agent name
        Returns
            (Str) : Agent Name
        """
        agent_header_xpath = f"{self.__base_xpath}[{index}]//thead//th"
        agent_element = self.__driver.find_element(By.XPATH, agent_header_xpath)
        return agent_element.text

    @PageService()
    def get_self_service_user(self):
        """
        Fetch the user name of which the self service Dashboard is displayed
        """
        element = self.__driver.find_element(By.XPATH,
                                             "//div[contains(@class,'dashboard-title')]//following-sibling::div")
        return element.text

    @PageService()
    def _get_details_by_tile(self, index):
        """
        Fetch the details of the tile
        index(int) :- Index of the tile
        Returns
        (dict) :- Details of the tile
        """
        details_dict = {}
        agent_name = self._get_agent_by_tile(index)
        columns = self._get_columns(index)
        values = self._get_values(index)
        details_dict.update({"AgentName": agent_name})
        for i in range(0, len(columns)):
            details_dict[columns[i]] = values[i]
        return details_dict

    @PageService()
    def get_user_mappings(self):
        """Get the details with how many agents the agent is associated"""
        agent_mapping = {
            "Exchange Online": 0,
            "OneDrive for Business": 0,
        }
        all_agents_xpath = f"{self.__base_xpath}//thead//th"
        agents = self.__driver.find_elements(By.XPATH, all_agents_xpath)
        for agent in agents:
            agent_mapping[agent.text] += 1
        return agent_mapping

    @PageService()
    def get_all_details(self):
        """
        Fetches all the details regarding the user
        Returns
        (list) :- List of all the details for the user
        """
        number_of_tiles = self._get_number_of_tiles()
        dashboard_info = []
        for index in range(1, number_of_tiles + 1):
            details = self._get_details_by_tile(index)
            dashboard_info.append(details)
        return dashboard_info

    @PageService()
    def click_details_by_client(self, client_name):
        """
        Click on the details for the client
        client_name(str) -- Client Name for which we need the details
        Returns
        (Dict) -- Client Details
        """
        details_link_xpath = self.__tile_link_xpath.format(client_name, "Details")
        self._click_link_on_tile(details_link_xpath)

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
