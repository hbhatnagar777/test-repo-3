# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
testcases of SharePoint for Business module.

To begin, create an instance of SharePoint for test case.

To initialize the instance, pass the testcase object to the SharePoint class.

Call the required definition using the instance object.

This file consists of only one class SharePoint
"""
import re
import time

from selenium.common.exceptions import ElementNotInteractableException, ElementClickInterceptedException
from selenium.webdriver.common.by import By

from AutomationUtils import logger

from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.AdminConsole.Components.panel import PanelInfo, ModalPanel, RPanelInfo
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.Office365Pages import constants
from Web.AdminConsole.Office365Pages.office365_apps import Office365Apps
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.Components.wizard import Wizard


class SharePoint(Office365Apps):
    """ Class for SharePoint object """

    def __init__(self, tcinputs, admin_console, is_react=False):
        super(SharePoint, self).__init__(tcinputs, admin_console, is_react=is_react)
        self._table = Table(self._admin_console)
        self._rtable = Rtable(self._admin_console)
        self._wizard = Wizard(self._admin_console)
        self._modal_panel = ModalPanel(self._admin_console)
        self._panel = PanelInfo(self._admin_console)
        self._rpanel = RPanelInfo(self._admin_console)
        self._navigator = self._admin_console.navigator
        self.job_details = None
        self.log = logger.get_log()
        self.is_react = is_react
        self._driver = admin_console.driver

    @WebAction()
    def _get_last_discover_cache_update_time(self):
        """Returns last discover cache time available or not"""
        if self.is_react:
            discovery_not_completed_xpath = "//div[@id='tile-discovery-status']//div[@class='tile-row-value-display']"
        else:
            discovery_not_completed_xpath = f"//span[@data-ng-bind='o365spReAssociateWebCtrl.lastDiscoverCacheUpdateTime']"
        return self._driver.find_element(By.XPATH, discovery_not_completed_xpath).text

    @WebAction()
    def _click_last_discover_cache_update_time(self):
        """Clicks last discover cache time"""
        discovery_not_completed_xpath = f"//span[@data-ng-bind='o365spReAssociateWebCtrl.lastDiscoverCacheUpdateTime']"
        self._driver.find_element(By.XPATH, discovery_not_completed_xpath).click()

    @WebAction(delay=3)
    def _click_refresh_cache(self):
        """Clicks refresh cache button on discovery dialog"""
        if self.is_react:
            self._driver.find_element(By.XPATH, "//button/div[text()='Refresh cache']").click()
        else:
            self._driver.find_element(By.XPATH,
                                      f"//a[normalize-space()='{self._admin_console.props['action.refreshSPDiscover']}']"
                                      ).click()

    @WebAction()
    def _click_page_drop_down_in_sites_tab(self):
        """Clicks on drop down to select page option in sites tab"""
        page_drop_down = self._driver.find_element(By.XPATH, 
            f"//*[@*='k-select']"
        )
        page_drop_down.click()

    @WebAction()
    def _select_page_option_in_sites_tab(self, page_option):
        """Selects the page option on the top left of the sites table in sites tab"""
        option = self._driver.find_element(By.XPATH, 
            f"//*[@class='k-list-scroller']//li[.='{page_option}']"
        )
        option.click()

    @WebAction()
    def _access_job_site_status_tab(self):
        """Access the site status tab in job details page"""
        self._driver.find_element(By.XPATH, 
            f"//span[contains(text(), 'Site status')]").click()

    @WebAction()
    def _view_site_details(self, site_name):
        """Goes to site details page for given site
            Args:
                site_name (str)  -- name of the site
        """
        self._driver.find_element(By.XPATH, 
            f"//a[contains(text(), '{site_name}')]").click()

    @WebAction()
    def _select_file_option(self, file_option="skip"):
        """Selects the specified file option
            Args:
                file_option (str)  -- file option
                                      Acceptable values: skip, unconditional_overwrite
        """
        self._driver.find_element(By.XPATH, 
            f"//span[contains(text(), '{self._admin_console.props['header.filelevel.options']}')]").click()
        if file_option == 'skip':
            self._driver.find_element(By.ID, self.app_type.RESTORE_SKIP_OPTION.value).click()
        elif file_option == 'unconditional_overwrite':
            self._driver.find_element(By.ID, self.app_type.RESTORE_UNCONDITIONAL_OVERWRITE_OPTION.value).click()
        else:
            raise Exception("Only skip or unconditional_overwrite file options are supported")

    @WebAction()
    def _select_restore_advanced_option(self, advanced_option):
        """Selects the specified advanced restore option
            Args:
                advanced_option (str)  -- advance option
        """
        self._wizard.select_checkbox(checkbox_label=advanced_option)

    @WebAction()
    def _fill_azure_storage_account_details(self, azure_user_account, azure_account_key):
        """Fills azure storage account details in restore options panel
            Args:
                azure_user_account (str)        --      azure storage user account
                azure_account_key  (str)        --      key value of storage account
        """
        if self._admin_console.check_if_entity_exists("xpath",
                                                           "//span[contains(text(), 'Azure storage account')]"):
            self._driver.find_element(By.ID, 'azureUserAccount').send_keys(azure_user_account)
            self._driver.find_element(By.ID, 'azurePassword').send_keys(azure_account_key)

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

        timestamp_element = self._driver.find_element(By.XPATH, f"//button[@aria-label='{restore_time}']")
        timestamp_element.click()

    @WebAction()
    def _enter_disk_destination_path(self, path):
        """Clicks the restore to disk destination path

                path (str)   --  The destination path to which files/sites are to be restored
        """
        self._wizard.fill_text_in_field(id='fileServerPathInput', text=path)

    @WebAction()
    def _click_enter_destination_path_button(self):
        """Clicks on upward arrow button to enter destination path
        """
        self._driver.find_element(By.XPATH, 
            "//button[@data-ng-disabled='spDocRestoreCtrl.restoreToOriginalPath']").click()

    @WebAction()
    def _get_status_tab_stats(self):
        """Returns the stats of status tab in job details page"""
        return self._driver.find_element(By.XPATH, f"//div[@data-testid='grid-custom-component-container']").text + " "

    @WebAction()
    def _select_radio_by_id(self, radio_button_id):
        """ Method to select radio button based on id """
        try:
            if not self._driver.find_element(By.ID, radio_button_id).is_selected():
                self._driver.find_element(By.ID, radio_button_id).click()
        except ElementClickInterceptedException:
            self.log.info('Radio button was already selected')

    @WebAction()
    def _fill_form_by_xpath(self, xpath, value):
        """
        Fill the value in a text field with xpath element id.

        Args:
            xpath (str)      -- the xpath attribute of the element to be filled
            value (str)      -- the value to be filled in the element

        Raises:
            Exception:
                If there is no element with given name/id

        """
        element = self._driver.find_element(By.XPATH, xpath)
        element.clear()
        element.send_keys(value)
        self._admin_console.wait_for_completion()

    @WebAction()
    def _select_oop_destination_site(self, oop_site):
        """Selects the destination site for oop restore
            Args:
                oop_site (set)  -- destination site info
                    Example:
                        {
                          "Title":"Test Site",
                          "URL":"https://tenant.sharepoint.com/sites/TestSPAutomationSite"
                       }
        """
        search_element = self._driver.find_element(By.ID, 'searchInput')
        if search_element.is_displayed():
            self._admin_console.fill_form_by_id(element_id='searchInput', value=oop_site['URL'])
        self._table.select_rows([oop_site['Title']])

    @WebAction()
    def _select_sites_from_associated_sites(self, sites):
        """Selects the specified sites from associated sites"""
        if self.is_react:
            table = self._rtable
        else:
            table = self._table
        for site in sites:
            table.apply_filter_over_column('URL', site)
            if self.is_react:
                search_element = self._driver.find_element(By.XPATH, "//input[@aria-label='grid-search']")
                if search_element.is_displayed():
                    search_element.click()
                    self._admin_console.fill_form_by_xpath(xpath="//input[@aria-label='grid-search']", value=site)
            else:
                search_element = self._driver.find_element(By.ID, 'searchInput')
                if search_element.is_displayed():
                    self._driver.find_element(By.XPATH, f"*//span[contains(@class,'k-icon k-i-zoom')]").click()
                    self._admin_console.fill_form_by_id(element_id='searchInput', value=site)
            site_ellipses = '.../' + '/'.join(site.split('/')[3:])
            self._select_user(site_ellipses)
            table.clear_column_filter('URL', site)

    @WebAction()
    def _edit_tenant_admin_site_url(self, new_tenant_admin_site_url):
        """
        Modifies the tenant admin site url to the new value given as argument
            Args:
            new_tenant_admin_site_url (str)     :   New value of tenant admin site url to be set

        """
        self._driver.find_element(By.XPATH, 
            f"//span[text()='Tenant admin site URL'"
            f"]//ancestor::li//a[contains(normalize-space(),'Edit')]"
        ).click()
        self._admin_console.wait_for_completion()
        self._driver.find_element(By.ID, 'sharePointTenantAdminUrl').clear()
        self._driver.find_element(By.ID, 'sharePointTenantAdminUrl').send_keys(new_tenant_admin_site_url)
        self._driver.find_element(By.XPATH, '//span[@class="k-icon k-i-check"]').click()
        self._admin_console.wait_for_completion()

    @WebAction()
    def _add_azure_storage_account(self, azure_storage_account, azure_storage_account_key):
        """
        Adds azure storage account in the configuration page for SharePoint
        Args:
            azure_storage_account (str)           :   azure storage account to be set
            azure_storage_account_key (str)       :   key of azure storage account
        """
        azure_storage_account_label = 'Azure storage account'
        self._driver.find_element(By.XPATH, 
            f"//span[text()='{azure_storage_account_label}'"
            f"]//ancestor::li//a[text()='Add']"
        ).click()
        self._admin_console.wait_for_completion()
        self._driver.find_element(By.ID, 'userName').send_keys(azure_storage_account)
        self._driver.find_element(By.ID, 'password').send_keys(azure_storage_account_key)
        self._modal_dialog.click_submit()
        self._admin_console.wait_for_completion()

    @WebAction()
    def _edit_azure_storage_account(self, azure_storage_account, azure_storage_account_key):
        """
        Edits azure storage account in the configuration page for SharePoint
        Args:
            azure_storage_account (str)           :   azure storage account to be set
            azure_storage_account_key (str)       :   key of azure storage account
        """
        azure_storage_account_label = 'Azure storage account'
        self._driver.find_element(By.XPATH, 
            f"//span[text()='{azure_storage_account_label}'"
            f"]//ancestor::li//a[text()='Edit']"
        ).click()
        self._admin_console.wait_for_completion()
        self._driver.find_element(By.ID, 'userName').clear()
        self._driver.find_element(By.ID, 'userName').send_keys(azure_storage_account)
        self._driver.find_element(By.ID, 'password').send_keys(azure_storage_account_key)
        self._modal_dialog.click_submit()
        self._admin_console.wait_for_completion()

    @WebAction()
    def _edit_o365_plan_retention(self, retention):
        """Edits the retention period of o365 plan
             Args:
               retention = {'deleted_item_retention': {'value': '5', 'unit': 'Day(s)'}
        """
        RPanelInfo(self._admin_console, 'Retention').edit_tile()
        if retention.get('deleted_item_retention', None):
            if retention['deleted_item_retention']['value'] == "Indefinitely":
                self._select_radio_by_id("indefiniteRetention")
            else:
                self._select_radio_by_id("deletionBasedRetention")
                self._admin_console.fill_form_by_id("deletionRetentionPeriodTimePeriod",
                                                    retention['deleted_item_retention']['value'])
                self._rmodal_dialog.select_dropdown_values(
                    drop_down_id="deletionRetentionPeriodTimePeriodUnit",
                    values=[retention['deleted_item_retention']['unit']])
        self._rmodal_dialog.click_submit(wait=True)

    # @WebAction()
    # def _open_add_sites_panel(self):
    #     """Open the Add sites panel in Sites Tab in SharePoint client
    #     """
    #     self._driver.find_element(By.ID, "AddNewWeb").click()
    #     self._driver.find_element(By.ID, "AddNewWeb_add").click()

    @PageService()
    def edit_tenant_admin_site_url(self, tenant_admin_site_url=None):
        """Edits tenant admin site url and verifies it
            Args:
                tenant_admin_site_url (str)        :   admin site url of SharePoint tenant
        """
        if self.tcinputs['office_app_type'] == Office365Apps.AppType.share_point_online:
            self._admin_console.select_configuration_tab()
            if not tenant_admin_site_url:
                tenant_admin_site_url = self.tcinputs['EditSiteAdminUrl']
            self._edit_tenant_admin_site_url(tenant_admin_site_url)
            general_panel = PanelInfo(self._admin_console, title=self._admin_console.props['label.generalPane'])
            details = general_panel.get_details()
            if not details['Tenant admin site URL'].startswith(tenant_admin_site_url):
                raise CVWebAutomationException("Tenant admin site url is not edited properly")
        else:
            raise CVWebAutomationException("Option not supported for the agent")

    @PageService()
    def add_sp_azure_storage_account(self, azure_storage_account=None, azure_storage_account_key=None):
        """Verifies add option of azure storage account
            Args:
                azure_storage_account (str)           :   azure storage account to be set
                azure_storage_account_key (str)       :   key of azure storage account
        """
        self._admin_console.select_configuration_tab()
        if not azure_storage_account and not azure_storage_account_key:
            azure_storage_account = self.tcinputs['AzureStorageAccount']
            if not azure_storage_account:
                raise CVWebAutomationException(
                    "Please provide azure storage details to add azure storage account")
            azure_storage_account_key = self.tcinputs['AzureStorageAccountKey']
        self._add_azure_storage_account(azure_storage_account, azure_storage_account_key)
        infra_panel = PanelInfo(self._admin_console, title=self._admin_console.props['label.infrastructurePane'])
        infra_details = infra_panel.get_details()
        if not infra_details['Azure storage account'].startswith(azure_storage_account):
            raise CVWebAutomationException("Azure storage account is not added properly")

    @PageService()
    def edit_sp_azure_storage_account(self, azure_storage_account=None, azure_storage_account_key=None):
        """Verifies edit option of azure storage account
            Args:
                azure_storage_account (str)           :   azure storage account to be set
                azure_storage_account_key (str)       :   key of azure storage account
        """
        self._admin_console.select_configuration_tab()
        if not azure_storage_account and not azure_storage_account_key:
            azure_storage_account = self.tcinputs['EditAzureStorageAccount']
            if not azure_storage_account:
                raise CVWebAutomationException(
                    "Please provide azure storage details to add azure storage account")
            azure_storage_account_key = self.tcinputs['EditAzureStorageAccountKey']
        self._edit_azure_storage_account(azure_storage_account, azure_storage_account_key)
        infra_panel = PanelInfo(self._admin_console, title=self._admin_console.props['label.infrastructurePane'])
        infra_details = infra_panel.get_details()
        if not infra_details['Azure storage account'].startswith(azure_storage_account):
            raise CVWebAutomationException("Azure storage account is not edited properly")

    @PageService()
    def wait_for_discovery_to_complete(self, time_out=600, poll_interval=60,
                                       last_discover_cache_update_time='Not available'):
        """Waits for discovery to complete and returns last discover cache update time
           Args:
            time_out (int)                          :   Time out
            poll_interval (int)                     :   Regular interval for check
            last_discover_cache_update_time (str)   :   Last discover cache update time
        """
        self._admin_console.access_tab(constants.SharePointOnline.OVERVIEW_TAB.value)
        if not self.is_react:
            self._open_add_user_panel()
        attempts = time_out // poll_interval
        while attempts != 0:
            latest_discover_cache_update_time = self._get_last_discover_cache_update_time()
            if latest_discover_cache_update_time == last_discover_cache_update_time:
                self.log.info('Please wait. Discovery in progress...')
                time.sleep(poll_interval)
                self._admin_console.refresh_page()
                self._admin_console.wait_for_completion()
                if not self.is_react:
                    self._open_add_user_panel()
            else:
                last_discover_cache_update_time = latest_discover_cache_update_time
                break
            attempts -= 1
        if attempts == 0:
            raise CVWebAutomationException('Discovery exceeded stipulated time.'
                                           'Test case terminated.')
        self._admin_console.refresh_page()
        return last_discover_cache_update_time

    @PageService()
    def remove_from_content(self, site=None, is_group=False):
        """
        Excludes the given site from backup
        Args:
            site (str):         Site which has to be removed
            is_group (bool):    Whether user/group is to be deleted
        """
        if site:
            if not is_group:
                site = '.../' + '/'.join(site.split('/')[3:])
            self._select_user(site, is_group=is_group)
        else:
            self._select_user(self.users[0], is_group=is_group)
        self._click_remove_content(user=site)
        self._admin_console.wait_for_completion()
        self._rmodal_dialog.click_submit()
        self._admin_console.wait_for_completion()
        self.log.info(f'Site removed from content: {site}')

    @PageService()
    def verify_added_auto_association_groups(self, groups=None):
        """Verifies the groups added to the app
            Args:
                groups (list)    :  list of auto associated group names
        """
        if not groups:
            groups = self.groups
        self._admin_console.access_tab(self.app_type.CONTENT_TAB.value)
        group_list = self._rtable.get_column_data(column_name='Name')
        for group in groups:
            if group not in group_list:
                raise CVWebAutomationException(f"{group} is not associated as expected")
        self.log.info(f'Added groups verified: {groups}')

    @PageService()
    def get_total_associated_sites_count(self):
        """Returns count of total associated sites"""
        if self.is_react:
            table = self._rtable
        else:
            table = self._table
        self._admin_console.access_tab(self.app_type.ACCOUNT_TAB.value)
        return int(table.get_total_rows_count())

    @PageService()
    def get_o365_plan_retention(self, plan):
        """Returns the retention period of o365 plan
             Args:
                plan (str)                :  Plan for which the retention should be returned
        """
        self._navigator.navigate_to_plan()
        Plans(self._admin_console).select_plan(plan)
        panel = PanelInfo(self._admin_console,
                          title=self._admin_console.props['label.retention'])
        return panel.get_details().get(self._admin_console.props['label.retainBasedOnDeletedItems'])

    @PageService()
    def change_o365_plan_retention(self, plan, retention):
        """Changes retention period for o365 plan
             Args:
                plan (str)                :  Plan for which the retention should be changed
                retention (str)           :  Retention period
                    Example:
                        10 days, 50 months, Indefinitely etc
        """
        retention = retention.split(' ')
        retention_dict = {
            'deleted_item_retention': {
                'value': retention[0]
            }
        }
        if len(retention) > 1:
            retention_dict['deleted_item_retention']['unit'] = retention[1]
        self._navigator.navigate_to_plan()
        Plans(self._admin_console).select_plan(plan)
        self._edit_o365_plan_retention(retention_dict)

    @PageService()
    def get_discovery_dialog_stats(self, retry=0):
        """Returns discovery stats in discovery dialog"""
        while retry < 3:
            if self.is_react:
                discovery_stats = self._rpanel.get_details()
            else:
                discovery_stats = self._modal_dialog.get_details()
            if not discovery_stats:
                retry = retry + 1
                time.sleep(30)
            else:
                return discovery_stats
        if retry > 3:
            raise Exception('Unable to fetch discovery stats')

    @PageService()
    def open_discovery_stats_dialog(self):
        """Opens discovery stats dialog"""
        if self.is_react:
            self._admin_console.access_tab("Overview")
            self._driver.find_element(By.XPATH, "//div[@id='tile-discovery-status']//button").click()
            time.sleep(5)
        else:
            self._admin_console.access_tab(self.app_type.ACCOUNT_TAB.value)
            self._open_add_user_panel()
            self._admin_console.wait_for_completion()
            self._click_last_discover_cache_update_time()

    @PageService()
    def get_sites_count_under_add_webs(self):
        """Returns sites count under add webs"""
        if self.is_react:
            self._admin_console.access_tab(self.app_type.CONTENT_TAB.value)
        else:
            self._admin_console.access_tab(self.app_type.ACCOUNT_TAB.value)

        self._rtable.access_toolbar_menu('Add')
        self._wizard.select_card("Add content to backup")
        self._wizard.click_next()
        self._wizard.select_card(self.app_type.ADD_USER_CARD_TEXT.value)
        self._wizard.click_next()
        self._admin_console.wait_for_completion()

        if self.is_react:
            total_sites = int(self._rtable.get_total_rows_count())
        else:
            total_sites = int(self._table.get_total_rows_count())
        self._admin_console.refresh_page()
        return total_sites

    @PageService()
    def refresh_cache(self, wait_for_discovery_to_complete=True, time_out=300, poll_interval=30):
        """Refreshes the discovery cache by running discovery
            Args:
                wait_for_discovery_to_complete (bool)   :   waits for discovery to complete once it is launched
                                                            on access node
                time_out (int)                          :   Time out
                poll_interval (int)                     :   Regular interval for check
        """
        self.open_discovery_stats_dialog()
        self._click_refresh_cache()
        if wait_for_discovery_to_complete:
            attempts = time_out // poll_interval
            while attempts > 0:
                time.sleep(poll_interval)
                self._admin_console.refresh_page()
                self.open_discovery_stats_dialog()
                discovery_stats = self.get_discovery_dialog_stats()
                if discovery_stats['Status'] == self._admin_console.props['label.discover.finished']:
                    break
                attempts -= 1
            if attempts == 0:
                raise CVWebAutomationException('Discovery exceeded stipulated time.'
                                               'Test case terminated.')
        self._admin_console.refresh_page()

    @PageService()
    def initiate_backup(self, sites=None, page_option=None, client_level=None):
        """
        Initiates backup for the SharePoint app

        Args:
            sites (list):   List of sites to be backed up
            page_option (int): page option to be selected
                               Example: 1 : Select page
                                        2 : Select all pages
            client_level (bool): flag whether to initiate client level backup
        Returns:
            job_id (str): Job Id of the initiated backup job

        """
        if sites or page_option:
            if sites:
                if self.is_react and self._admin_console.get_current_tab != self.app_type.ACCOUNT_TAB.value:
                    self._admin_console.access_tab(self.app_type.ACCOUNT_TAB.value)
                    self._admin_console.wait_for_completion()
                self._select_sites_from_associated_sites(sites)
            else:
                self._click_page_drop_down_in_sites_tab()
                if page_option == 2:
                    self._select_page_option_in_sites_tab(self._admin_console.props['label.o365sp.selectAllPages'])
                else:
                    self._select_page_option_in_sites_tab(self._admin_console.props['label.customSelectAll.selectAll'])
            self._click_backup()
            self._rmodal_dialog.click_submit()
            job_id = self._get_job_id()
            return job_id
        else:
            if client_level:
                self._navigator.navigate_to_office365()
                if self.is_react:
                    self._rtable.access_action_item(self.tcinputs['Name'], "Backup")
                    self._driver.find_element(By.XPATH, ".//span[contains(@class, 'positive-modal-btn')]//button").click()
                else:
                    self._table.access_action_item(self.tcinputs['Name'], self._admin_console.props['action.backup'])
                    self._driver.find_element(By.XPATH, "//button[@aria-label='Submit']").click()
            else:
                if self.is_react:
                    self._driver.find_element(By.XPATH, "//button/div[text()='Backup']").click()
                    self._driver.find_element(By.XPATH, ".//span[contains(@class, 'positive-modal-btn')]//button").click()
                else:
                    self._admin_console.access_menu_from_dropdown('Backup')
                    self._modal_dialog.click_submit()
            job_id = self._get_job_id()
            return job_id

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
        if self.is_react:
            table = self._rtable
        else:
            table = self._table
        time.sleep(5)
        columns = table.get_visible_column_names()
        for site in expected_sites_details:
            expected_sites_details[site]['URL'] = '.../' + '/'.join(site.split('/')[3:])
        self._admin_console.access_tab(self.app_type.ACCOUNT_TAB.value)
        table.apply_sort_over_column('URL', ascending=False)
        for site, site_details in expected_sites_details.items():
            table.apply_filter_over_column('URL', site)
            for column, value in site_details.items():
                if column not in columns:
                    try:
                        table.display_hidden_column(column)
                    except ElementNotInteractableException:
                        # Here ElementNotInteractableException is raised though the element is interactable
                        pass
                ui_column_value = table.get_column_data(column)[-1]
                if ui_column_value != value:
                    raise CVWebAutomationException(f"Expected value for {column} is {value}, "
                                                   f"displayed value is {ui_column_value}")
            table.clear_column_filter('URL', site)

    @PageService()
    def process_status_tab_stats(self, stats):
        """Returns the status_tab_stats of status tab in job details page after processing them into dictionary
            Args:
                stats (str)         :  site stats of status tab in job details page
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
    def navigate_to_job_page(self, job_id):
        """Navigates to specified job page
            Args:
                job_id (str)                     : Job Id of the ob
        """
        self._navigator.navigate_to_jobs()
        if not self._jobs.if_job_exists(job_id):
            self._jobs.access_job_history()
            if not self._jobs.if_job_exists(job_id):
                raise CVWebAutomationException("Job is not present in Active jobs or job history")
        self._jobs.view_job_details(job_id)

    @PageService()
    def get_job_details(self, job_id):
        """Returns the job details
            Args:
                job_id (str)                     : Job Id of the ob
        """
        try:
            self.navigate_to_job_page(job_id)
        except CVWebAutomationException as e:
            if e == CVWebAutomationException("Job is not present in Active jobs or job history"):
                return None
        details = self._jobs.job_details()
        return details

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
        self.navigate_to_job_page(job_id)
        self._access_job_site_status_tab()
        self._admin_console.wait_for_completion()
        status_tab_stats = self.process_status_tab_stats(self._get_status_tab_stats())
        for label, value in status_tab_expected_stats.items():
            if not value == status_tab_stats[label]:
                raise CVWebAutomationException(f"Status tab stats are not validated\n"
                                               f"Expected Stats: {status_tab_expected_stats}\n"
                                               f"Actual Stats: {status_tab_stats}")

    @PageService()
    def verify_job_completion(self, job_id):
        """Verifies that backup jobs complete successfully
            Args:
                job_id (str)                     : Job Id of the backup job
        """
        self._jobs.access_job_by_id(job_id)
        self.job_details = self._jobs.job_details()
        # self._modal_panel.close()
        if (self.job_details[self._admin_console.props['Status']] not in
                ["Committed", "Completed", "Completed w/ one or more errors",
                 "Completed w/ one or more warnings"]):
            raise Exception(f'Job {job_id} did not complete successfully')
        else:
            self.log.info(f'Job {job_id} completed successfully')

    @PageService()
    def verify_backup_job(self, job_id, status_tab_expected_stats=None):
        """Waits till the completion of backup job and verifies it
             Args:
                job_id (str)                     : Job Id of the backup job
                status_tab_expected_stats (dict) : Expected stats of the status tab
        """
        # sometimes displaying backup job on job page takes some time, so waiting for it
        time.sleep(90)
        self._jobs.job_completion(job_id=job_id, skip_job_details=True)
        self._navigator.navigate_to_office365()
        self.access_office365_app(self.tcinputs['Name'])
        self.view_jobs()
        if int(self._rtable.get_total_rows_count()) > 0:
            self.verify_job_completion(job_id=job_id)
        else:
            raise CVWebAutomationException('Jobs are not present in job history')
        if status_tab_expected_stats:
            self.verify_status_tab_stats(job_id=job_id, status_tab_expected_stats=status_tab_expected_stats)

    @PageService()
    def click_site_level_restore(self, sites, site_restore=False):
        """Selects specified sites and open browse page by clicking restore
            Args:
                sites  (list)       --  selects sites and clicks on restore
                site_restore (bool) --  clicks restore sites

        """
        self._select_sites_from_associated_sites(sites)
        self._click_backupset_level_restore(restore_content=site_restore)
        self._admin_console.wait_for_completion()

    @PageService()
    def click_point_in_time_browse(self, restore_time=None):
        """Selects time and click point in time restore
            Args:
                restore_time (str)  --  time of backup job for which items have to be restored
                                        Format: Nov 5, 2020 5:35:58 PM

        """
        if restore_time:
            self._select_restore_time(restore_time)
        # self._admin_console.select_hyperlink('Restore')
        self._driver.find_element(By.XPATH, "//*[@id='submit-btn' and @aria-label='Restore']").click()
        self._admin_console.wait_for_completion()

    @PageService()
    def view_site_details(self, site):
        """Clicks on the site name in app page
            Args:
                site  (str)         --  title of the site
        """
        self._view_site_details(site)

    @WebAction()
    def _click_file_option(self, file_option):
        """Clicks file option in React Restore wizard

            Args:

                file_option (str)   :       Text for the radio labelled 'If documents exists'
                                            Acceptable values: 'Skip', 'Unconditionally overwrite'

        """
        self._wizard.select_radio_button(label=file_option)


    @PageService()
    def enter_details_in_restore_wizard(self, destination, file_option=None, advanced_option=None,
                                        file_server=None, dest_path=None, oop_site=None):
        """

        Args:
            destination (str)       --  Specifies the destination
                                        Acceptable values: to_disk, in_place, out_of_place
            file_option (str)       --  file option to restore
                                        Acceptable values: 'Skip', 'Unconditionally overwrite'
            advanced_option (str)   --  Advanced option to restore
            file_server (str)       --  File Server name for disk restore
            dest_path (str)         --  Path to which the files have to be restored
            oop_site (dict)         --  Site to which files have to be restored
                Example:
                    {
                        'Title': 'Site Title',
                        'URL': 'https://tenant.sharepoint.com/site'
                    }
        """

        if destination == constants.RestoreType.TO_DISK:
            self._wizard.select_card('File location')
            self._rdropdown.select_drop_down_values(drop_down_id='fileServersDropdown',
                                                    values=[file_server])
            self._enter_disk_destination_path(dest_path)
        elif destination == constants.RestoreType.OOP:
            self._rdropdown.select_drop_down_values(drop_down_id='agentDestinationDropdown',
                                                    values=['Restore the data to another location'])
            self._wizard.click_icon_button_by_title('Browse')
            self._rtable.search_for(oop_site['URL'])
            self._rtable.select_rows([oop_site['Title']])
            self._rmodal_dialog.click_submit()
        self._wizard.click_next()
        if file_option:
            self._click_file_option(file_option)
        if advanced_option:
            self._select_restore_advanced_option(advanced_option)

    @PageService()
    def _get_job_id_from_wizard(self):
        """Gets Job ID from a React wizard alert"""
        text = self._wizard.get_alerts()
        return re.findall(r'\d+', text)[0]

    @PageService()
    def run_restore(
            self, destination, file_option=None, advanced_option=None, file_server=None, dest_path=None, oop_site=None):
        """
        Runs the restore

        Args:
            destination (str)       --  Specifies the destination
                                        Acceptable values: to_disk, in_place, out_of_place
            file_option (str)       --  file option to restore
                                        Acceptable values: 'Skip', 'Unconditionally overwrite'
            advanced_option (str)   --  Advanced option to restore

            file_server (str)       --  Name of file server in case of restore to disk
            dest_path (str)         --  Path to which the files have to be restored
            oop_site (str)          --  Site to which the OOP restore should be done

        Returns:
            job_details (dict): Details of the restore job

        """
        self.enter_details_in_restore_wizard(
            destination=destination,
            file_option=file_option,
            advanced_option=advanced_option,
            file_server=file_server,
            dest_path=dest_path,
            oop_site=oop_site)
        self._wizard.click_next()
        self._wizard.click_submit()
        self._admin_console.wait_for_completion()
        job_id = self._get_job_id_from_wizard()
        self._wizard.click_button('Close')
        self._jobs.job_completion(job_id=job_id, skip_job_details=True)
        # Waiting for all job details to get updated on job page
        time.sleep(60)
        job_details = self.get_job_details(job_id)
        self.log.info('job details: %s', job_details)
        return job_details
