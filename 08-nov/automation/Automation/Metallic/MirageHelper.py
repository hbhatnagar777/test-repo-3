# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file to perform operations related to Mirage / Cloud Command Project

MirageCCHelper: Helper class for performing UI operations related to Mirage

MirageCCHelper:
    __init__()                          --      Initialize instance of the MirageCCHelper class

    is_service_catalog_available()       --      Method to check if service catalog available for user

    go_to_service_catalog()              --      Method to go to service catalog

    available_services()                 --      Method to get list of available services on service catalog

    click_on_service()                   --      Method to click on service name from catalog

    register_metallic_trial()            --      Method to register for metallic trial for software only customers

    link_hybrid_company()                --      Method to link Hybrid company

    subscribe_to_mirage_trial()          --      Method to register for a metallic trial as either software only or hybrid

    go_to_user_management()              --      Method to go to user management

    add_user()                           --      Method to add new user from user management page

    has_user()                           --      Method to check if user exists on user management page

    delete_user()                        --      Method to delete user from user management page

    is_switcher_available()              --      Method to check if switcher available

    switch_to_commcell()                 --      Method to switch to specified commcell

    current_commcell()                   --      Method to get the current commcell

    click_on_service_hubside()           --      Method to click on service on HUB side

    go_to_metallic_cloud_command()           --      Method to click on cloud command from HUB side

    validate_page_visibility()           --      Method to validate if a user can visit all the pages

    validate_commcell_switcher()         --      Method to validate switcher functionality

    is_service_panel_disabled()          --      Method to check if service is disabled on service catalog

    get_users()                          --      Method to get user emails from Cloud users listing page

    is_cloud_company_switcher_available()--      Method to check if cloud company switcher available

    available_companies()                --      Method to get available companies in the switcher

    select_company()                     --      Method to select company from the cloud switcher

    current_company()                    --      Method to get the currently selected company

    reset_cloud_switcher                 --      Method to reset cloud switcher

    validate_service_panel_disability()  --      Method to validate if service panels are disabled on the service catalog

    validate_cloud_user_list()           --      Method to validate cloud user list from the user management page

    validate_cloud_switcher()            --      Method to validate cloud switcher functionality for the given customer groups

    get_active_mgmt_status()             --      Method to get active management status of service commcell

    get_entity_sync_status()             --      Method to get sync status of the entity

    enable_active_management()           --      Method to enable active management on service commcell

    check_hub_connectivity_with_service_commcell() -- Method to check the connectivity of Hub with the Service Commcell

MirageApiHelper: Class for performing Mirage related api actions

MirageApiHelper:
    __init__()                          --      Initialize instance of the MirageApiHelper class

    run_registration()                  --      Triggers User Registration for Metrics Server

    register_with_new_user()            --      Register commcell with new user

    run_register_beaming_wf()           --      Method to run the register beaming workflow

    run_create_company_subgroup_users_wf() --   Method to run the create company subgroup users workflow

    clean_up()                          --      Clean up the entities at Cloud / Metallic / OKta side

    create_metallic_tenant()            --      Method to create a tenant on Ring using a workflow

    configure_hybrid_customer()         --      Method to insert hybrid customer entry in HistoryDB

    deconfigure_hybrid_customer()       --      Method to remove hybrid customer entry from HistoryDB

    is_customer_hybrid()                --      Method to check if customer is hybrid

    get_customer_usergroups()           --      Method to get customer user groups

    get_users_of_customer_group()       --      Method to get user emails of specified customer group name

    configure_user_account()            --      Method to configure user accounts on cloud

    make_user_global_admin()            --      Method to make user a global admin

    get_account_id()                     --      Method to get account id of the user

    make_customer_hybrid()               --      Method to make customer hybrid

    cloud_side_gcm_clean_up()            --      Method to clean up the entities at Cloud Side

    service_commcell_gcm_clean_up()      --      Method to clean up the entities at Service Commcell Side - csdb

    service_commcell_mongo_clean_up()    --      Method to clean up the entities at Service Commcell Side - mongodb

    validate_active_management_status()  --      Method to validate active management status on cloud and service commcell
    
    retry_function_execution()           --      Method to retry the function execution

MirageTrailHelper: Class for performing Mirage trial related actions

MirageTrailHelper:
    __init__()                          --      Initialize instance of the MirageTrailHelper class

    login_to_cloud_console()            --      Method to login to cloud console

    perform_mirage_trial()              --      Method to perform mirage trial

    validate_cloud_company_switcher()   --      Method to validate cloud company switcher

    login_from_metallic()               --      Method to start the flow from metallic
    
OktaHelper: Class for performing Okta related actions

OktaHelper:
    __init__()                          --      Initialize instance of the OktaHelper class

    create_user()                       --      Create user at Okta side

    delete_user()                       --      Delete user at Okta side

    filter_users()                      --      To filter users based on email

"""

from time import sleep, time
import base64
from random import randint, choices, choice
import string
import asyncio
import platform
import xml.etree.ElementTree as ET
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RPanelInfo, RDropDown
from Web.AdminConsole.Components.dialog import RModalDialog, Form
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.AdminConsolePages.Plans import Plans
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.adminconsole import AdminConsole
from AutomationUtils import logger
from okta.client import Client as OktaClient
from Web.AdminConsole.Hub.dashboard import Dashboard as Hub
from Web.AdminConsole.Hub.constants import HubServices
from cvpysdk.commcell import Commcell
from AutomationUtils import database_helper
from typing import List, Tuple, Any, Callable, Dict, Union
import re
import traceback
from AutomationUtils.config import get_config
from cvpysdk.license import LicenseDetails
from Server.organizationhelper import OrganizationHelper


class MirageCCHelper:
    """ Helper class for the Mirage """

    def __init__(self, admin_console: AdminConsole, commcell: Commcell):
        """
        Method to initiate MirageCCHelper class

        Args:
            admin_console   (AdminConsole) :   admin console object

            commcell        (Commcell)     :   commcell object
        """
        self.__admin_console = admin_console
        self.__commcell = commcell
        self._navigator = None
        self.__driver = self.__admin_console.driver
        self.log = self.__admin_console.log
        self.__dialog = RModalDialog(self.__admin_console)
        self.__rpanel = RPanelInfo(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)
        self.__form = Form(self.__admin_console)
        self.__mirage_api = MirageApiHelper(commcell)
        self.__rdropdown = RDropDown(self.__admin_console)

    @property
    def __navigator(self):
        """Method to get navigator object"""
        if self._navigator is None:
            self._navigator = self.__admin_console.navigator
        return self._navigator

    @PageService()
    def is_service_catalog_available(self) -> bool:
        """Method to check if service catalog available for user"""
        return self.__navigator.check_if_element_exists('Service catalog')

    @PageService()
    def go_to_service_catalog(self) -> None:
        """Method to go to service catalog"""
        if self.__admin_console.check_if_entity_exists('id', 'SERVICE_CATALOG'):
            self.log.info('User already on service catalog...')
            return

        self.__navigator.navigate_to_service_catalog()
        self.__admin_console.wait_for_completion()

    @PageService()
    def available_services(self) -> list:
        """Method to get list of available services on service catalog"""
        self.go_to_service_catalog()
        return [solution.split('\n')[0] for solution in self.__rpanel.available_panels()]

    @PageService()
    def click_on_service(self, service_name: str) -> None:
        """Method to click on service name from catalog"""
        self.go_to_service_catalog()
        service_panel = f"//*[text()='{service_name}']//ancestor::*[contains(@class,'grid')]//*[contains(@id, 'sc-configure') or contains(@id, 'sc-manag')]"
        self.__driver.find_element(By.XPATH, service_panel).click()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def is_service_panel_disabled(self, service_name: str) -> bool:
        """
            Method to check if service is disabled on service catalog

            Args:
                service_name (str)  :   Service Name
        """
        element = self.__driver.find_element(By.XPATH, f"//*[text()='{service_name}']//ancestor::*[contains(@class,'grid')]//*[contains(@id, 'sc-configure') or contains(@id, 'sc-manag')]")
        return self.__admin_console.is_any_parent_disabled(element)

    @PageService()
    def register_metallic_trial(self, info: dict) -> None:
        """Method to register for metallic trial for software only customers

            Args:
                info (dict)     :   User details

                info = {
                    "FirstName"     :   "",
                    "LastName"      :   "",
                    "Title"         :   "",
                    "CompanyName"   :   "",
                    "Email"         :   "",
                    "Phno"          :   "",
                    "Country"       :   "",
                    "State"         :   "",
                    "Commcell"      :   "",
                    "Solutions"     :   ["",""]
                }
        """
        field_mapping = {
            'FirstName':   'metallicTrialFirstName',
            'LastName':   'metallicTrialLastName',
            'Title':   'metallicTrialTitle',
            'CompanyName':   'metallicTrialCompanyName',
            'Email':   'metallicTrialEmailAddress',
            'Phno':   'metallicTrialPhoneNumber',
            'Country':   'CountrySelection',
            'State':   'StateSelection',
            'Commcell':   'metallicCommcell',
            'Solutions':   'MetallicProductList'
        }

        if info.get('Commcell'):
            self.__admin_console.hotkey_settings('mirageTrialTest', True)
            self.__admin_console.wait_for_completion()

        for key, field in field_mapping.items():
            if value := info.get(key):
                if field in ['CountrySelection', 'StateSelection', 'MetallicProductList']:
                    self.__admin_console.scroll_into_view(field)
                    self.__form.select_dropdown_values(field, [value])
                else:
                    self.__form.fill_text_in_field(field, value)

        self.__form.checkbox.check(id='TermAndConditions')
        self.__form.click_submit()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def link_hybrid_company(self, authcode: str) -> None:
        """Method to link Hybrid company"""
        self.__dialog.fill_text_in_field('authcode', authcode)
        self.__dialog.click_button_on_dialog('Verify authorization code')
        self.__admin_console.check_error_message()
        self.__dialog.click_submit()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def wait_for_trial_completion(self, timeout=300):
        """Method to wait until trial completes"""
        try:
            WebDriverWait(self.__driver, timeout).until(ec.presence_of_element_located((By.ID, "Save")))
        except Exception as e:
            self.log.error(e)
            raise CVWebAutomationException(f'Trial completion failed! Didnt receive mirage push on time [WaitTime: {timeout}] {e}')
        self.__admin_console.click_button_using_id('Save')
        self.__admin_console.wait_for_completion()
        self.log.info('Trial completed successfully!')

    @PageService()
    def subscribe_to_mirage_trial(self, ring_name: str=None, auth_code: str=None) -> None:
        """
            Method to register for a metallic trial as either software only or hybrid
            
            Args:
                ring_name (str)     :   Name of the ring, Needed for Software only customers
                auth_code (str)      :   Authorization code, Needed for Hybrid customers
        """
        self.log.info('Subscribing to the trial...')
        services = [service for service in self.available_services() if service not in [
            'Cloud Console', 'Active Directory', 'Microsoft Dynamics 365', 'VM & Kubernetes']]
        trial_solution = choice(services)
        self.log.info(f'Subscribing to the {trial_solution} solution...')
        self.click_on_service(trial_solution)

        details = {
            'FirstName': 'Backup',
            'LastName': 'Admin',
            'Title': 'Backup Admin',
            'Phno': '+910000000000',
            'Country': 'United States',
            'State': 'Texas',
            'Commcell': ring_name
        }

        if auth_code:
            self.link_hybrid_company(auth_code)
        else:
            self.register_metallic_trial(details)

        current_page_url = self.__admin_console.current_url()
        if 'cloudCommand' not in current_page_url:
            raise CVWebAutomationException(f'After registering for the trial, the page didn\'t redirect to Cloud Command. Current Page URL: {current_page_url}')

        self.wait_for_trial_completion()
        self.__admin_console.wait_for_completion()

        WebDriverWait(self.__driver, 30).until(ec.element_to_be_clickable((By.ID, "mirageDashboard")))

        if not self.is_switcher_available():
            raise CVWebAutomationException('The switcher did not appear post trial subscription.')
        self.log.info('Switcher successfully appeared post trial completion!')

    @PageService()
    def wait_for_am_enablement_completion(self, service_commcell_name: str, timeout=300):
        """
            Method to wait until AM enablement completes

            Args:
                service_commcell_name (str) : Service Commcell Name
                timeout (int)               : Timeout in seconds
        """
        self.log.info(f'Waiting for active management enablement to complete... [Timeout: {timeout}s]')
        self.__navigator.navigate_to_gcm_service_commcells()
        self.__admin_console.wait_for_completion()
        
        start_time = time()

        while (time() - start_time) < timeout:
            if self.__admin_console.check_if_entity_exists('id', 'navigationItem_manage'):
                self.log.info('Active Management enablement completed successfully!')
                self.log.info('AM completion push is working!')
                return  # Exit the loop if the first condition is met

            self.__rtable.reload_data()
            am_status = self.get_active_mgmt_status(service_commcell_name)
            if am_status == 'On':
                self.log.info('Active Management enablement completed successfully!')
                self.log.warn('AM completion push is not working! Refreshing page manually...')
                self.__admin_console.refresh_page()
                self.__admin_console.wait_for_completion()
                return  # Exit the loop if the second condition is met

            sleep(10)  # Wait for 10 seconds before checking again

        raise TimeoutError(f"Timed out waiting for Active Management enablement to complete within {timeout} seconds.")

    @PageService()
    def go_to_user_management(self) -> None:
        """Method to go to user management"""
        self.go_to_service_catalog()
        self.__admin_console.click_button_using_text('User management') # service catalog v2
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    @PageService()
    def add_user(self, user_name: str, email: str) -> None:
        """Method to add new user from user management page"""
        self.go_to_user_management()
        self.__rtable.access_toolbar_menu('Add user')
        self.__dialog.fill_text_in_field('name', user_name)
        self.__dialog.fill_text_in_field('email', email)
        self.__dialog.click_submit()
        self.__admin_console.check_error_message()

    @PageService()
    def has_user(self, user_name: str = '', email: str = '') -> bool:
        """Method to check if user exists on user management page"""
        self.go_to_user_management()
        if user_name and self.__rtable.is_entity_present_in_column(column_name='Name', entity_name=user_name):
            return True

        return bool(
            email
            and self.__rtable.is_entity_present_in_column(
                column_name='Email', entity_name=email
            )
        )

    @PageService()
    def delete_user(self, user_name: str = '', email: str = '') -> None:
        """Method to delete user from user management page"""
        self.go_to_user_management()
        self.__rtable.access_action_item(
            user_name or email, self.__admin_console.props['action.delete'])
        self.__dialog.click_submit()
        self.__admin_console.check_error_message()

    @PageService()
    def get_users(self) -> list:
        """Method to get user emails from Cloud users listing page"""
        user_emails = self.__rtable.get_column_data(
            column_name='Email', fetch_all=True)
        self.log.info(f'User emails fetched from UI: {user_emails}')
        return user_emails

    @PageService()
    def make_global_admin(self, user_name: str) -> None:
        """Method to make user a global admin"""
        pass

    @PageService()
    def make_cs_recovery_mgr(self, user_name: str) -> None:
        """Method to make user a cs recovery manager"""
        pass

    @PageService()
    def remove_global_admin(self, user_name: str) -> None:
        """Method to remove user from being a global admin"""
        pass

    @PageService()
    def remove_cs_recovery_mgr(self, user_name: str) -> None:
        """Method to remove user from being a cs recovery manaager"""
        pass

    @PageService()
    def is_switcher_available(self) -> bool:
        """Method to check if switcher available"""
        return self.__admin_console.check_if_entity_exists('id', 'header-commcell-dropdown')

    @PageService()
    def is_cloud_company_switcher_available(self) -> bool:
        """Method to check if cloud company switcher available"""
        return self.__admin_console.check_if_entity_exists('id', 'cloudCompanySwitcher')

    @WebAction()
    def __is_cloud_switcher_expanded(self) -> bool:
        """Method to check if cloud switcher is already expanded"""
        return self.__admin_console.check_if_entity_exists('id', 'cloudCompanySwitcherSearchInput')

    @WebAction()
    def __expand_cloud_switcher(self) -> None:
        """Method to expand the cloud switcher"""
        if self.__is_cloud_switcher_expanded():
            return
        dd_element = self.__driver.find_element(By.ID, "cloudCompanySwitcher")
        dd_element.click()

    @WebAction()
    def __set_cloud_switcher_search_string(self, keyword: str) -> None:
        """Clears the search box and sets with the given string on cloud company switcher"""
        search_box_id = "cloudCompanySwitcherSearchInput"
        if self.__driver.find_elements(By.ID, search_box_id):
            search_box = self.__driver.find_element(By.ID, search_box_id)
            search_box.send_keys(u'\ue009' + 'a' + u'\ue003') # CTRL + A + Backspace
            search_box.send_keys(keyword)

    @WebAction()
    def __select_company_from_cloud_switcher(self, company_name: str) -> None:
        """Method to click on the given company name from the search result"""
        company_name_xpath = f"//*[contains(@class, 'Dropdown') and @title='{company_name}']"
        WebDriverWait(self.__driver, 30).until(
            ec.presence_of_element_located((By.XPATH, company_name_xpath)))
        company_name = self.__driver.find_element(By.XPATH, company_name_xpath)
        company_name.click()
    
    @WebAction()
    def __reset_cloud_switcher(self) -> None:
        """Method to reset cloud switcher"""
        reset_button = self.__driver.find_element(By.XPATH, "//*[contains(@class,'Dropdown')]//*[text()='Reset']")
        reset_button.click()

    @WebAction()
    def __search_for_company(self, company_name: str) -> None:
        """Method to search for a company in the cloud switcher"""
        self.__expand_cloud_switcher()
        self.__set_cloud_switcher_search_string(company_name)

    @PageService()
    def available_companies(self) -> list[str]:
        """Method to get available companies in the switcher"""
        return [element.text for element in self.__driver.find_elements(By.XPATH, "//*[contains(@class, 'dd-list-item')]")]

    @PageService()
    def select_company(self, company_name: str) -> None:
        """Method to select company from the cloud switcher"""
        self.__search_for_company(company_name)
        self.__select_company_from_cloud_switcher(company_name)

    @WebAction()
    def __extract_company_id(self):
        """Extracts the company ID from the given URL"""
        current_url = self.__admin_console.current_url()
        self.log.info(f'Current URL: {current_url}')

        # Match the company ID in the URL
        match = re.search(r'(companyId|cloudCompanyId)=(\d+)', current_url)

        # If the company ID was matched, return it. Otherwise, raise exception
        if match:
            return int(match.group(2))
        raise CVWebAutomationException(
            f'Failed to fetch company id from the current url: {current_url}')

    @PageService()
    def current_company(self) -> tuple:
        """
            Method to get the currently selected company details
            
            Args:
                None

            Returns:
                tuple (company name (str), company id (int))
        """
        company_name = self.__driver.find_element(By.ID, "cloudCompanySwitcher").text
        company_id = self.__extract_company_id()
        return company_name, company_id

    @PageService()
    def reset_cloud_switcher(self) -> None:
        """Method to reset cloud switcher"""
        self.__expand_cloud_switcher()
        self.__reset_cloud_switcher()

    @WebAction()
    def __select_commcell(self, commcell_name: str) -> None:
        """Method to expand the commcell switcher"""
        self.__rdropdown.select_drop_down_values(values=[commcell_name], drop_down_id='header-commcell-dropdown')

    @PageService()
    def switch_to_ring(self, commcell_name: str) -> None:
        """Method to switch to specified commcell"""
        self.__select_commcell(commcell_name)
        self.__admin_console.wait_for_completion()
        self.__close_welcome_modal()
    
    @PageService()
    def switch_to_cloud(self, cloud_name: str) -> None:
        """Method to switch to specified cloud"""
        self.__navigator.switch_service_commcell(cloud_name)
        self.log.info('Sucesfully attempted to switch into the cloud...')

    @PageService()
    def current_commcell(self) -> None:
        """Method to get the current commcell"""
        commcell_switcher = self.__driver.find_element(By.ID, "commcell-dropdown")
        return commcell_switcher.text.strip()

    @WebAction()
    def __close_welcome_modal(self) -> None:
        """Method to close the welcome modal if it appears"""
        new_update_info_xpath = "//button[contains(text(), 'Ok, got it')]"
        if elements := self.__driver.find_elements(By.XPATH, new_update_info_xpath):
            elements[0].click()

        try:
            self.log.info('Waiting for the welcome modal...')
            welcome_model_dismiss_btn_id = "welcomeModalDismissButton"
            WebDriverWait(self.__driver, 30).until(ec.element_to_be_clickable((By.ID, welcome_model_dismiss_btn_id)))
            self.log.info('Closing welcome modal...')
            self.__driver.find_element(By.ID, welcome_model_dismiss_btn_id).click()
            self.__admin_console.wait_for_completion()
        except Exception as e:
            self.log.info('Welcome modal not found. Continuing...')

    @WebAction()
    def __click_on_cloud_console(self) -> None:
        """Method to click on cloud console from Metallic Service Catalog side"""
        self.__driver.find_element(By.ID, 'sc-manage-cloud-command').click()

    @PageService()
    def go_to_metallic_cloud_command(self) -> None:
        """Method to click on cloud command from HUB side"""
        self.__navigator.navigate_to_service_catalogue()
        self.__admin_console.wait_for_completion()
        self.__close_welcome_modal()
        self.__click_on_cloud_console()
        sleep(30)  # Waiting for redirection to complete. Using sleep() as we dont have any specific element to use WebDriverWait
        if 'cloudcommand' in self.__admin_console.current_url().lower():
            return # cloud command dashboard opened in the same tab - metallic only user case
        self.__driver.close()
        # change focus to new window
        self.__driver.switch_to.window(self.__driver.window_handles[0])
        self.__admin_console.wait_for_completion()

    @WebAction()
    def __available_dashboards(self) -> list:
        """Method to check available dashboards shown on UI"""
        xpath = "//div[contains(@class, 'summary')]//*[contains(@id, 'popper')]"
        return [element.text for element in self.__driver.find_elements(By.XPATH, xpath)]

    @PageService()
    def available_dashboards(self):
        """Method to check available dashboards shown on UI"""
        return self.__available_dashboards()

    @PageService()
    def validate_service_panel_disability(self, is_reseller: bool = False) -> None:
        """Validate if service panels are disabled on the service catalog.

        Args:
            is_reseller (bool): Flag indicating if the user is a reseller.
        Returns:
            None
        """
        self.log.info(f'Validating service panel disability... [Reseller: {is_reseller}]')
        self.go_to_service_catalog()
        error_messages = []
        logged_in_user = self.__admin_console.username

        for service_panel in self.available_services():
            is_disabled = self.is_service_panel_disabled(service_panel)

            if service_panel == 'Cloud Console':
                if is_disabled:
                    error_messages.append(
                        f'Cloud Console is disabled on the service catalog (Reseller: {is_reseller}) [User: {logged_in_user}]'
                    )
            elif is_reseller and not is_disabled:
                error_messages.append(
                    f'For a reseller, {service_panel} is not disabled on the service catalog! [User: {logged_in_user}]'
                )
            elif not is_reseller and is_disabled:
                error_messages.append(
                    f'For a non-reseller, {service_panel} is disabled on the service catalog! [User: {logged_in_user}]'
                )

            self.log.info(
                f'Service: {service_panel} => Disabled: {is_disabled}, Reseller: {is_reseller} [User: {logged_in_user}]')

        if error_messages:
            error_message = '\n'.join(error_messages)
            raise CVWebAutomationException(error_message)
        
        self.log.info('Validation of service panel disability completed successfully!')

    @PageService()
    def validate_page_visibility(self, global_admin=True):
        """Method to validate if a user can visit all the pages"""
        if not global_admin:
            if self.is_service_catalog_available():
                raise CVWebAutomationException(
                    'Non-global admin user should not have access to the service catalog breadcrumb.')

            current_page_url = self.__admin_console.current_url()
            if 'dashboard' not in current_page_url:
                raise CVWebAutomationException(
                    f'Non-global admin users should be on the Cloud Command page. Current Page URL: {current_page_url}')

            self.log.info(
                'Successfully validated that a non-global admin user can only visit the Cloud Command page.')
            return

        available_services = self.available_services()
        self.log.info(f'Available services on service catalog page => {available_services}')

        expected_service_count = 10
        if (total_service := len(available_services)) < expected_service_count:
            raise CVWebAutomationException(
                f'{total_service} services available on the service catalog page. Expected: {expected_service_count}')

        for service_name in available_services:
            self.click_on_service(service_name)
        self.go_to_user_management()

        self.log.info(
            'Successfully validated that a global admin user can visit all the available pages.')

    @PageService()
    def validate_commcell_switcher(self, new_commcell: str, new_wc_hostname: str, switching_to_ring: bool) -> None:
        """
            Method to validate switcher functionality
            
            Args:
                new_commcell (str)      :   Name of the commcell to switch to
                new_wc_hostname (str)   :   Hostname of the commcell to switch to
                switching_to_ring (bool):   Flag indicating if the user is switching to ring from the cloud
        """
        if switching_to_ring:
            self.switch_to_ring(new_commcell)
        else:
            self.switch_to_cloud(new_commcell)

            # on test setups, switching from ring to cloud will take us to /commandcenter
            # so we need to explicitly move to /cloudconsole
            current_url = self.__admin_console.current_url()
            self.log.info(f'Current URL: {current_url}')

            if new_wc_hostname in current_url:
                self.log.info('Successfully switched to cloud!')
                self.log.info(f'Are we on Command Center? - {"/commandcenter" in self.__admin_console.current_url()}')

                # custom logic to move to cloudconsole
                cloudconsole_url = f'https://{new_wc_hostname}/cloudconsole'
                self.__admin_console.navigate(cloudconsole_url)
                self.__admin_console.wait_for_completion()
            
            self.log.info('Wait for the redirection to complete...')
            WebDriverWait(self.__driver, 300).until(ec.element_to_be_clickable((By.ID, "mirageDashboard")))

        current_page_url = self.__admin_console.current_url()

        if new_wc_hostname not in current_page_url:
            raise CVWebAutomationException(
                f'Switching to {new_commcell} failed. Current page URL: {current_page_url}')

        if 'login' in current_page_url:
            raise CVWebAutomationException(
                f'It seems we have landed on the login page. Please ensure that you have logged in at least once. Current page URL: {current_page_url}')

        self.log.info(f'Successfully switched to the commcell => {new_commcell}')

    @PageService()
    def validate_user_management_operations(self, domain_name: str):
        """Method to validate user managerment operations"""
        # add user
        email = f'randomuser{randint(0,10000)}@{domain_name}'
        username = f'randomuser{randint(0,10000)}'
        self.add_user(username, email)
        self.log.info('Waiting for 3 min till user gets created...')
        sleep(180)

        if not self.has_user(username) or not self.has_user(email=email):
            raise CVWebAutomationException(
                f'Failed to create user from user management page! [{username}, {email}]')

        # delete user
        self.delete_user(email=email)
        self.log.info('Waiting for 3 min till user gets deleted...')
        sleep(180)
        if self.has_user(username) or self.has_user(email=email):
            raise CVWebAutomationException(
                f'Failed to delete user from user management page! [{username}, {email}]')

    @PageService()
    def validate_cloud_user_list(self, company_name: str) -> None:
        """Validate cloud user list from the user management page.

        Args:
            company_name (str): Name of the company to validate user list for.
        Returns:
            None
        """
        self.log.info(f'Validating user list for company: {company_name}')
        if self.is_cloud_company_switcher_available():
            self.select_company(company_name)
            self.__admin_console.wait_for_completion()

        self.go_to_user_management()
        ui_user_list = self.get_users()
        api_user_list = self.__mirage_api.get_users_of_customer_group(company_name)

        if not all(element in api_user_list for element in ui_user_list):
            raise CVWebAutomationException(
                f'User from other company showing up in the cloud user list! '
                f'UI Users: {ui_user_list} != API Users: {api_user_list} [Company: {company_name}]'
            )
        self.log.info(
            'Successfully validated user list on User management page!')

    @PageService()
    def validate_switcher_flow(self, inputs_dict: dict, global_admin: bool):
        """
            Method to validate switcher functionality/flow

            Args:
                input_dict = {
                    'cloud_name': 'Name of the cloud',
                    'cloud_hostname': 'Hostname of the cloud',
                    'ring_name': 'Name of the ring',
                    'ring_hostname': 'Hostname of the ring'
                }

                global_admin (bool)  :   Flag indicating if the user is a global admin
        """
        cloud_name = inputs_dict['cloud_name']
        cloud_hostname = inputs_dict['cloud_hostname']
        ring_name = inputs_dict['ring_name']
        ring_hostname = inputs_dict['ring_hostname']

        self.log.info('To make switcher work, please ensure that the user already has a session at SSO.')

        self.log.info(f'Current url: {self.__admin_console.current_url()}')
        self.log.info(f'Are we on ring? : {ring_hostname in self.__admin_console.current_url()}')
        # if we are already on the ring, switch to cloud
        if ring_hostname in self.__admin_console.current_url():
            self.validate_commcell_switcher(cloud_name, cloud_hostname, switching_to_ring=False)

        self.validate_commcell_switcher(ring_name, ring_hostname, switching_to_ring=True)
        self.validate_commcell_switcher(cloud_name, cloud_hostname, switching_to_ring=False)
        self.validate_commcell_switcher(ring_name, ring_hostname, switching_to_ring=True)

        if global_admin:
            self.go_to_metallic_cloud_command()
            WebDriverWait(self.__driver, 300).until(ec.element_to_be_clickable((By.ID, "mirageDashboard")))
            current_page_url = self.__admin_console.current_url()
            if '/cloudconsole/#/cloudCommand' not in current_page_url:
                raise CVWebAutomationException(
                    f'Clicked on cloud command from Metallic Service Catalog, but the page didn\'t redirect to Cloud Command. Current Page URL: {current_page_url}')

    @PageService()
    def validate_cloud_switcher(self, customer_groups: List[Tuple[str, int, int]]) -> None:
        """
        Validate cloud switcher functionality for the given customer groups.

        Args:
            customer_groups: List of tuples containing customer user group details
                            [('Customer Group Name', User Group ID, Company ID), (,,),...]
        Returns:
            None
        """
        if not self.__admin_console.check_if_entity_exists('id', 'SERVICE_CATALOG'):
            self.__navigator.navigate_to_service_catalog()

        default_company = self.current_company()
        self.log.info(f'Default Company: {default_company}')
        # This is to ensure that we are in another company's context, so we can access the RESET button.
        other_company = ''

        if default_company in customer_groups:
            customer_groups.remove(default_company) # To avoid stale element reference error

        self.log.info(f'Validating cloud switcher functionality as user: [{self.__admin_console.username}]')
        for usergroup_name, usergroup_id, company_id in customer_groups:
            self.log.info(f'Validating for User Group Name: [{usergroup_name}], User Group ID: [{usergroup_id}], Company ID: [{company_id}]')
            # is customer converted to company model
            usergroup_converted = bool(company_id)
            self.select_company(usergroup_name)
            sleep(60) # Wait for context switch to complete
            self.__admin_console.wait_for_completion()

            # check if url got updated
            current_company_name, current_company_id = self.current_company()
            self.log.info(f'Current Company: [{current_company_name}, {current_company_id}]')   
            if current_company_id != (company_id or usergroup_id):
                raise CVWebAutomationException(
                    f'Switching to company failed! ({usergroup_name}, {usergroup_id}, {company_id}) Current Company => [{current_company_name, current_company_id}]'
                )
            
            # check if new company name shows up in the switcher
            if current_company_name != usergroup_name:
                raise CVWebAutomationException(
                    f'Company name not shown in the switcher! ({usergroup_name}, {usergroup_id}, {company_id}) Current Company => [{current_company_name, current_company_id}]'
                )
            
            # check if service catalog panels are disabled
            if not usergroup_converted:
                self.validate_service_panel_disability(is_reseller=True)

            # validate user lists on cloud user listing page
            if not usergroup_converted:
                self.validate_cloud_user_list(usergroup_name)

            if usergroup_name != default_company[0]:
                other_company = usergroup_name

        # validate RESET button
        if self.current_company() == default_company:  # if default company is already set, switch to other company
            self.select_company(other_company)
            self.__admin_console.wait_for_completion()

        self.reset_cloud_switcher()
        self.__admin_console.wait_for_completion()
        if (current_company := self.current_company()) != default_company:
            raise CVWebAutomationException(
                f'Resetting cloud switcher did not set the default company. '
                f'User: [{self.__admin_console.username}] Current Company: {current_company}]'
            )

    def get_active_mgmt_status(self, service_commcell_name: str) -> str:
        """
            Method to get active management status of service commcell

            Args:
                service_commcell_name (str) : Service Commcell Name
        """
        self.__navigator.navigate_to_gcm_service_commcells()
        _, data  = self.__rtable.get_rows_data(search=service_commcell_name)
        self.log.info(f'Data received from UI: {data}')
        return data[0]['Active management']

    def get_entity_sync_status(self, entity_name: str) -> str:
        """
            Method to get sync status of the entity

            Args:
                entity_name (str) : Entity Name
        """
        self.__admin_console.wait_for_completion()
        _, data  = self.__rtable.get_rows_data(search=entity_name)
        self.log.info(f'Data received from UI: {data}')
        return data[0]['Sync status']

    def __open_active_management_model(self, service_commcell_name: str) -> None:
        """Method to open active management model"""
        self.__navigator.navigate_to_gcm_service_commcells()
        self.__admin_console.wait_for_completion()

        # If AM status is stuck in pending, retry enabling AM
        am_status = self.get_active_mgmt_status(service_commcell_name)
        self.log.info(f'Active management status: {am_status}')

        if am_status == 'Pending':
            self.__rtable.access_action_item(service_commcell_name, 'Retry enable active management')
        else:
            self.__rtable.access_action_item(service_commcell_name, 'Enable active management')

        self.__admin_console.wait_for_completion()

    def __fill_active_management_form(self, username: str, password: str, authcode: str=None) -> None:
        """Method to fill active management form"""
        self.__admin_console.wait_for_completion()
        self.__dialog.fill_text_in_field('userName', username)
        self.__dialog.fill_text_in_field('password', password)

        # If user is already a company user, user won't get authcode option even if it is a hybrid user, So Skip authcode part
        if self.__admin_console.check_if_entity_exists('id', 'authcode') and authcode:
            self.link_hybrid_company(authcode)
        else:
            self.__dialog.click_submit()

        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    def __restart_cvd(self, commcell_obj: Commcell) -> None:
        """Method to restart CDV on the service commcell"""
        service_commcell_name = commcell_obj.commserv_client.client_name

        # Restarting cvd is flaky, so retrying 3 times
        max_retries = 3
        while max_retries:
            try:
                self.log.info(f'Restarting cvd on the service commcell client => [{service_commcell_name}]...')
                commcell_obj.clients.get(service_commcell_name).restart_service('cvd')
                self.log.info('cvd restarted successfully!')
                break
            except Exception as e:
                self.log.info(f'Failed to restart cvd on the service commcell client => [{service_commcell_name}]... [Error: {e}]')
                max_retries -= 1
                if max_retries == 0:
                    raise CVWebAutomationException(
                        f'Failed to restart cvd on the service commcell client => [{service_commcell_name}]... [Error: {e}]'
                    )
                self.log.info(f'Retrying to restart cvd on the service commcell client => [{service_commcell_name}]...')

    @PageService()
    def enable_active_management(self, service_commcell_name: str, username: str, password: str, authcode: str=None, linux_sc_commcell_obj: Commcell=None) -> None:
        """
            Method to enable active management on service commcell

            Args:
                service_commcell_name (str) : Service Commcell Name
                username (str)              : Username of the user
                password (str)              : Password of the user
                authcode (str)              : Authcode of the metallic company to link
                linux_sc_commcell_obj (Commcell) : Linux Service Commcell Object (Only required for Linux Service Commcell - To restart cvd)
        """
        self.__open_active_management_model(service_commcell_name)

        self.__fill_active_management_form(username, password, authcode)

        # Wait for user / user group migration to complete
        if not self.is_switcher_available():
            self.wait_for_trial_completion()

        # If Service Commcell OS is Linux, then we need to restart cvd on the service commcell
        if linux_sc_commcell_obj:
            self.log.info('Waiting for 2 minutes to upload the request to edc staging...')
            sleep(120)
            self.__restart_cvd(linux_sc_commcell_obj)

        # Wait for active management enablement to complete
        try:
            self.wait_for_am_enablement_completion(service_commcell_name, 600 if linux_sc_commcell_obj else 300)
        except Exception as e:
            self.log.info(
                f'Active management enablement seems to be failed or AM completion push is not received! Refreshing Page! [Service Commcell Name: {service_commcell_name}] [Error: {e}]'
            )
            self.__admin_console.refresh_page()
            self.__admin_console.wait_for_completion()

        # Get active management status from UI
        am_status = self.get_active_mgmt_status(service_commcell_name)
        self.log.info(f'Active management status: {am_status}')

        if am_status != 'On':
            raise CVWebAutomationException(
                f'Active management not enabled on service commcell! [Service Commcell Name: {service_commcell_name}] [AM Status: {am_status}]'
            )
        
        self.log.info(
            f'Active management enabled on service commcell! [Service Commcell Name: {service_commcell_name}] [AM Status: {am_status}]'
        )

    def create_global_plan(self, plan_name: str, storage_name: str, service_commcell_name: str) -> None:
        """Method to create a global plan on the master commcell"""
        self.log.info(f"Creating global plan... Plan Name: {plan_name} Storage Name: {storage_name}")
        self.__navigator.navigate_to_plan()
        self.__plans.create_server_plan(plan_name=plan_name, 
                                        storage={'name': storage_name},
                                        service_commcells=[service_commcell_name])

        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()

    def validate_global_plan_sync_status(self, plan_name: str, service_commcell: Commcell) -> None:
        """
            Method to validate the sync status of the global plan with the service commcell

            Args:
                plan_name (str)             : Plan Name
                service_commcell (Commcell) : Service Commcell Object
        """
        self.__navigator.navigate_to_plan()
        self.__admin_console.wait_for_completion()
        sync_status = self.get_entity_sync_status(entity_name=plan_name)
        self.log.info(f'Sync status of the plan: {sync_status}')

        service_commcell.plans.refresh()
        self.log.info(f'All Plans => {service_commcell.plans.all_plans}')
        if not service_commcell.plans.has_plan(f'{plan_name} (global)'):
            raise CVWebAutomationException(
                f'Plan not found in the service commcell! [Plan Name: {plan_name}] and UI Status: {sync_status}'
            )
        
        if sync_status != 'In sync':
            raise CVWebAutomationException(
                f'Plan not synced with the service commcell! [Plan Name: {plan_name}] [Sync Status: {sync_status}]. But Plan found in the service commcell!'
            )
        
        self.log.info(f'Plan synced with the service commcell! [Plan Name: {plan_name}] [Sync Status: {sync_status}]')

    def wait_until_entity_syncs(self, entity_name: str, timeout: int = 300, raise_exception: bool = False) -> None:
        """
        Method to wait until the entity gets synced or fails to sync within the given timeout

        Args:
            entity_name (str)   : Entity Name
            timeout (int)       : Timeout in seconds
            raise_exception (bool) : Flag to raise exception if the entity fails to sync within the given timeout
        """
        self.log.info(f'Waiting for {entity_name} to sync... Timeout set to {timeout} seconds')
        self.__admin_console.wait_for_completion()
        start_time = time()
        sync_status = 'In progress'

        while sync_status == 'In progress' and (time() - start_time) < timeout:
            self.__rtable.reload_data()
            sync_status = self.get_entity_sync_status(entity_name=entity_name)
            if sync_status != 'In progress':
                break  # Exit loop if sync is not In progress anymore

            sleep(10)  # Wait for 10 seconds before checking again

        if sync_status == 'In progress':
            self.log.warn(f"Timed out waiting for '{entity_name}' to sync within {timeout} seconds. Current Status: [{sync_status}]")
            if raise_exception:
                raise TimeoutError(f"Timed out waiting for '{entity_name}' to sync within {timeout} seconds.")

    def check_hub_connectivity_with_service_commcell(self, service_commcell: Commcell) -> bool:
        """
            Method to check the connectivity of Hub with the Service Commcell

            Args:
                service_commcell (Commcell) : Service Commcell Object
        """
        service_commcell_name = service_commcell.commserv_name
        self.__plans = Plans(self.__admin_console)
        plan_name = 'TestConnectivityGlobalPlan ' + ''.join(choices(string.ascii_letters + string.digits, k=10))
        storage_name = choice(list(service_commcell.storage_pools.all_storage_pools.keys()))

        self.create_global_plan(plan_name, storage_name, service_commcell_name)

        self.__navigator.navigate_to_plan()
        self.wait_until_entity_syncs(entity_name=plan_name)

        self.validate_global_plan_sync_status(plan_name, service_commcell)
        
        # Clean up
        self.__plans.delete_plan(plan_name)
        self.log.info('Hub to service commcell connectivity completed successfully!')

    def __perform_negative_tests_for_active_management(self, 
                                                        cloud_user_name: str, 
                                                        service_commcell: Commcell, 
                                                        service_commcell_password: str,
                                                        authcode: str=None, 
                                                        linux_sc_commcell_obj: Commcell=None) -> None:
        """
            Method to perform negative tests for active management

            Args:
                cloud_user_name (str)           : Cloud User Name
                service_commcell (Commcell)     : Service Commcell Object
                service_commcell_password (str) : Service Commcell Password
                auth_code (str)                 : Auth Code for linking the company
                linux_sc_commcell_obj (Commcell) : Linux Service Commcell Object (Only required for Linux Service Commcell - To restart cvd)
        """
        # Try to enable active management with wrong password
        random_password = ''.join(choices(string.ascii_letters + string.digits + string.punctuation, k=10))
        self.log.info(f'Trying to enable active management with wrong password: {random_password}')
        try:
            self.enable_active_management(service_commcell.commserv_name, cloud_user_name, random_password, authcode, linux_sc_commcell_obj)
        except CVWebAutomationException as exp:
            self.log.info(f'Ignoring Exception => {exp}')
        else:
            raise CVWebAutomationException('Active management enabled with wrong password')
        
        # remove user from master user group
        self.log.info(f'On Service Commcell, Removing user {cloud_user_name} from master user group')
        service_commcell.users.get(cloud_user_name).remove_usergroups(['master'])
        self.log.info(f'[{service_commcell.commserv_name}] : Associated User Groups for user [{cloud_user_name}]  => {service_commcell.users.get(cloud_user_name).associated_usergroups}')

        # Try to enable active management with less previliges
        self.log.info('Trying to enable active management with less previliges')
        try:
            self.enable_active_management(service_commcell.commserv_name, cloud_user_name, service_commcell_password, authcode, linux_sc_commcell_obj)
        except CVWebAutomationException as exp:
            self.log.info(f'Ignoring Exception => {exp}')
        else:
            raise CVWebAutomationException('Active management enabled with less previliges')

        # Add user back to master user group
        self.log.info(f'On Service Commcell, Adding user {cloud_user_name} to master user group')
        service_commcell.users.get(cloud_user_name).add_usergroups(['master'])
        self.log.info(f'[{service_commcell.commserv_name}] : Associated User Groups for user [{cloud_user_name}]  => {service_commcell.users.get(cloud_user_name).associated_usergroups}')

    def validate_active_management_flow(self, 
                                        company_name: str,
                                        cloud_user_name: str,
                                        service_commcell_password: str,
                                        service_commcell: Commcell, 
                                        cloud_commserv_csdb: database_helper.MSSQL,
                                        service_commcell_csdb: database_helper.MSSQL,
                                        negative_validation: bool = False,
                                        authcode: str=None, 
                                        linux_sc_commcell_obj: Commcell=None) -> None:
        """
            Method to validate active management flow

            Args:
                company_name (str)              : Name of the company
                cloud_user_name (str)           : Cloud User Name
                service_commcell_password (str) : Service Commcell Password
                service_commcell (Commcell)     : Service Commcell Object
                cloud_commserv_csdb (database_helper.MSSQL) : Cloud CommServ CSDB Object
                service_commcell_csdb (database_helper.MSSQL) : Service CommCell CSDB Object
                negative_validation (bool)      : Flag to perform negative validation   
        """
        self.log.info(f'Validating active management flow for company: {company_name}')
        commcell_name = service_commcell.commserv_name

        if negative_validation:
            self.__perform_negative_tests_for_active_management(cloud_user_name, service_commcell, service_commcell_password, authcode, linux_sc_commcell_obj)
        
        # Enable active management with correct password and previliges
        self.log.info(f'Enabling active management with correct password and previliges... [AuthCode Passed: {bool(authcode)}] [Linux Service Commcell: {bool(linux_sc_commcell_obj)}')
        self.enable_active_management(commcell_name, cloud_user_name, service_commcell_password, authcode, linux_sc_commcell_obj)

        self.__commcell.organizations.refresh() # refresh cloud commcell organizations
        
        # Validate active management status

        # extract hub base url from additional settings
        hub_base_url = [settings['value'] for settings in self.__commcell.get_configured_additional_setting() if settings['displayLabel'] == 'hubServiceBaseUrl'][0]
        hub_conn_url = f"{hub_base_url.strip('/')}/cvhub"

        info = {
            'CompanyGUID': self.__commcell.organizations.all_organizations_props[company_name.lower()]['GUID'],
            'CompanyID': self.__commcell.organizations.get(company_name).organization_id,
            'HubBaseUrl': hub_conn_url,
            'CommcellGUID': service_commcell.commserv_guid
        }
        self.log.info(f'Passing info to validate active management status: {info}')
        self.__mirage_api.validate_active_management_status(cloud_commserv_csdb, service_commcell_csdb, info)
        
        # validate hub connection via simple entity creation with 3 retries
        for _ in range(1,3):
            try:
                self.check_hub_connectivity_with_service_commcell(service_commcell=service_commcell)
                break  # Break if successful
            except Exception as exp:
                self.log.error(f"Error while checking hub connectivity : {exp}")
        else:
            self.log.info('Checking hub connectivity... with last attempt')
            self.check_hub_connectivity_with_service_commcell(service_commcell=service_commcell)

class MirageApiHelper:
    """ Helper class for the Mirage """

    def __init__(self, commcell: Commcell):
        """
        Method to initiate MirageApiHelper class

        Args:
            commcell        (Commcell)     :   commcell object
        """
        self.__commcell = commcell
        self.log = logger.get_log()
        self.config = get_config()
        self._verify_ssl = self.config.API.VERIFY_SSL_CERTIFICATE

    def run_registration(self, xml, commcell_obj: Commcell=None):
        """
            Triggers User Registration for Metrics Server
            
            Args:
                xml             (str)           :   XML to trigger registration
                commcell_obj    (Commcell)      :   Commcell object to run the registration from
        """
        commcell_obj = commcell_obj or self.__commcell
        self.log.info(
            f"Starting Registration of commcell {commcell_obj} with provided xml : {xml}")
        response = commcell_obj.qoperation_execute(xml)

        if response["errorCode"] != 0:
            raise Exception("Error in Registration. Response:", response["errorMessage"])

        self.log.info("Wait for 2 minutes to sync updates")
        sleep(120)
        self.log.info(f"Commcell {commcell_obj} registered successfully!")

    def register_with_new_user(self, user_details: dict, commcell_obj: Commcell=None) -> None:
        """
        Register commcell with new user

        Args:
            user_details (dict): Dictionary containing user details
                {
                    'FirstName': '',
                    'LastName': '',
                    'EmailAddress': '',
                    'Password': '',
                    'CompanyName': ''
                }
        """
        commcell_obj = commcell_obj or self.__commcell
        self.log.info("Starting registering Commcell with New user...")

        xml_response = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
        <EVGui_SetRegistrationInfoReq>
            <commCell _type_="1" commCellId="2" type="0"/>
            <registrationInformation ccguid="{commcell_obj.commserv_guid}" ccinstalltime="1452247766"
                commcellId="0" commcellName="" companyName="{user_details['CompanyName']}" description=""
                emailAddress="{user_details['EmailAddress']}" ipAddress="" isRegistered="0" majorbrandid="1" minibrandid="1"
                password="{base64.b64encode(user_details['Password'].encode()).decode()}" phoneNumber="123">
                <customerAddress address1="" address2="" city="" country="" state="" zip=""/>
                <customerName firstName="{user_details['FirstName']}" lastName="{user_details['LastName']}"/>
            </registrationInformation>
        </EVGui_SetRegistrationInfoReq>
        """

        self.run_registration(xml_response, commcell_obj)
        self.log.info(
            f"Registered Commcell {commcell_obj} with new user : [{user_details['EmailAddress']}] successfully!")

    def run_register_beaming_wf(self, commcell_id: str) -> None:
        """
            Method to run RegisterBeamingWorkflow on cloud side

            Args:
                commcell_id (str) : Commcell ID
        """
        self.log.info(f"Running RegisterBeamingWorkflow on cloud side for commcell: {commcell_id}")
        _, job = self.__commcell.workflows.get('RegisterBeamingCommserver').execute_workflow(workflow_inputs={'commcellIds': commcell_id})

        self.log.info(f'Job ID: {job.job_id} => Status: [{job.status}]. Waiting for completion...')
        
        if not job.wait_for_completion():
            raise Exception(
                "Failed to execute the workflow with error: " + job.delay_reason
            )

        self.log.info('Successfully Executed "%s" Workflow', 'RegisterBeamingWorkflow')
            
    def run_create_company_subgroup_users_wf(self, user_name, user_email, company_name, make_global_admin: bool = False) -> None:
        """
            Method to run CreateCompanySubgroupUsersWorkflow on cloud side

            Args:
                user_name (str)     : User Name
                user_email (str)    : User Email
                company_name (str)  : Company Name
                make_global_admin (bool) : Flag to make user global admin
        """
        input_xml = f"""
        <WebReport_CloudCompanyReq operation="3" userId="1">
        <companyInfo>
            <company userGroupId="" userGroupName="{company_name}" />
            <users operation="1" isCreator="0" email="{user_email}">
                <user userName="{user_name}" />
            </users>
        </companyInfo>
        </WebReport_CloudCompanyReq>
        """.strip()
        self.log.info(f"Running CreateCompanySubgroupUsersWorkflow for user: {user_name} and company: {company_name} : {input_xml}")

        _, job = self.__commcell.workflows.get('Create Company Subgroup Users').execute_workflow(workflow_inputs={'inputXml': input_xml})

        self.log.info(f'Job ID: {job.job_id} => Status: [{job.status}]. Waiting for completion...')
        
        if not job.wait_for_completion():
            raise Exception(
                "Failed to execute the workflow with error: " + job.delay_reason
            )

        self.log.info('Successfully Executed "%s" Workflow', 'CreateCompanySubgroupUsersWorkflow')

        self.__commcell.users.refresh()
        self.__commcell.user_groups.refresh()

        self.log.info(f'Adding user: [{user_name}] to the user group [{company_name}]...')
        self.__commcell.user_groups.get(company_name).update_usergroup_members(request_type='UPDATE', users_list=[user_name])

        if make_global_admin:
            self.make_user_global_admin(user_name, company_name)

    def clean_up(self, company_name: str, metallic_obj: Commcell = None, okta_helper=None, okta_user_marker: str = None, am_clean_up_info: dict = None, service_commcell: Commcell = None):
        """
        Method to clean up the entities at Cloud / Metallic / Okta side / Active Management

        Args:
            company_name (str)         : Name of the company
            metallic_obj (Commcell)    : Commcell object of the metallic
            okta_helper (OktaHelper)   : Okta helper object
            okta_user_marker (str)     : Marker to identify okta users
            am_clean_up_info (dict)    : Dictionary containing active management clean up info
                {
                    'cloud_hostname': '',
                    'cloud_sql_username': '',
                    'cloud_sql_password': '',
                    'service_commcell_hostname': '',
                    'service_commcell_username': '',
                    'service_commcell_password': '',
                    'service_commcell_sql_username': '',
                    'service_commcell_sql_password': '',
                    'service_commcell_mongo_password': '',
                    'hub_client_name': '',

                    # For Linux Service Commcell
                    'linux_service_commcell': bool
                }
            service_commcell (Commcell) : Service Commcell Object
        """
        max_retries = 3
        retries = 0
        while retries < max_retries:
            try:
                # Cloud side clean up
                self.log.info('Cleaning up at CLOUD side...')
                self.clean_up_cloud_side(company_name)

                # Metallic side clean up
                if metallic_obj:
                    self.log.info('Cleaning up at RING side...')
                    self.clean_up_metallic_side(metallic_obj, company_name)

                # Okta Side clean up
                if okta_helper:
                    self.log.info('Cleaning up at OKTA...')
                    self.clean_up_okta_side(okta_helper, okta_user_marker)

                # service commcell side clean up
                if service_commcell:
                    self.log.info('Cleaning up users at Service Commcell side...')
                    for user_name, _ in service_commcell.users.all_users.items():
                        if company_name in user_name:
                            service_commcell.users.delete(user_name, 'admin')

                if not am_clean_up_info:
                    return

                # Active Management clean up
                self.clean_up_active_management(am_clean_up_info)
                self.log.info('Clean up completed successfully!')
                break
            except Exception as e:
                self.log.error(f'Error occurred while cleaning up! [Error: {e}].')
                retries += 1
                if retries == max_retries:
                    raise e
                self.log.info(f'Retrying Clean up in a min... [Attempt: {retries}]')
                sleep(60)

    def clean_up_cloud_side(self, company_name):
        """
            Method to clean up the entities at Cloud side

            Args:
                company_name (str) : Name of the company
        """
        self.__commcell.organizations.refresh()
        OrganizationHelper(self.__commcell).cleanup_orgs(marker=company_name)

        self.__commcell.user_groups.refresh()
        if self.__commcell.user_groups.has_user_group(company_name):
            for user_name in self.__commcell.user_groups.get(company_name).users:
                self.log.info(f'Deleting user => {user_name}')
                self.__commcell.users.delete(user_name, 'admin')

    def clean_up_metallic_side(self, metallic_obj, company_name):
        """
            Method to clean up the entities at Metallic side

            Args:
                metallic_obj (Commcell) : Commcell object of the metallic
                company_name (str)      : Name of the company
        """
        OrganizationHelper(metallic_obj).cleanup_orgs(marker=company_name)

    def clean_up_okta_side(self, okta_helper, okta_user_marker):
        """
            Method to clean up the entities at Okta side

            Args:
                okta_helper (OktaHelper)    : Okta helper object
                okta_user_marker (str)      : Marker to identify okta users
        """
        for email in okta_helper.filter_users(marker=okta_user_marker):
            okta_helper.delete_user(email)

    def __restart_service_commcell_webservice(self, service_commcell: Commcell, is_linux_service_commcell: bool, webserver_name: str) -> None:
        """Method to restart webservice on service commcell"""
        if is_linux_service_commcell:
            self.log.info(f'Restarting webservice on the webserver => [{webserver_name}]...')
            service_commcell.clients.get(webserver_name).execute_command('commvault restart -service WebServerCore')
            self.log.info('Webservice restarted successfully!')
        else:
            self.log.info(f'Restarting IIS on the webserver => [{webserver_name}]...')
            try:
                # running IISRESET command from remote machine is stoping IIS but not starting it back
                # so splitting the iis command to stop and start
                service_commcell.clients.get(webserver_name).execute_command('iisreset /stop & iisreset /start')
            except Exception as e:
                self.log.warn(f'Failed to restart IIS on service commcell! [Error: {e}]')
                self.log.info('Ignoring the error and continuing... as connection must have been closed by IIS reset')

        self.log.info('Waiting for services to be up... [Sleeping for 1 minute]')
        sleep(60)
        self.log.info(f'Restarting WebService / IIS on service commcell: [{webserver_name}]... Done!')

    def __restart_hub_service(self, hub_client_name: str) -> None:
        """Method to restart HubService on HubServer"""
        max_retries = 3
        retries = 0

        while retries < max_retries:
            try:
                self.log.info(f'Restarting HubService on HubServer: [{hub_client_name}]...')
                self.__commcell.clients.get(hub_client_name).restart_service('CVHubService(Instance001)')
                break
            except Exception as e:
                self.log.error(f'Error occurred while restarting hub service! [Error: {e}].')
                retries += 1

                if retries == max_retries:
                    raise e

                self.log.info(f'Retrying Hub Service restart in a min... [Attempt: {retries}]')
                sleep(60)

        self.log.info(f'Restarting HubService on HubServer: [{hub_client_name}]... Done!')

    def clean_up_active_management(self, am_clean_up_info):
        """
        Method to clean up the entries of Active Management

        Args:
            am_clean_up_info (dict) : Dictionary containing active management clean up info
                {
                    'cloud_hostname': '',
                    'cloud_sql_username': '',
                    'cloud_sql_password': '',
                    'service_commcell_hostname': '',
                    'service_commcell_username': '',
                    'service_commcell_password': '',
                    'service_commcell_sql_hostname': '',
                    'service_commcell_sql_username': '',
                    'service_commcell_sql_password': '',
                    "service_commcell_mongo_hostname": '',
                    'service_commcell_mongo_password': '',
                    'hub_client_name': '',
                    'linux_service_commcell': bool
                }
        """
        # read service commcell details
        sc_hostname, sc_username, sc_password, sc_sql_username, sc_sql_password, is_linux_sc = (
            am_clean_up_info['service_commcell_hostname'],
            am_clean_up_info['service_commcell_username'],
            am_clean_up_info['service_commcell_password'],
            am_clean_up_info['service_commcell_sql_username'],
            am_clean_up_info['service_commcell_sql_password'],
            am_clean_up_info.get('linux_service_commcell', False)
        )

        # read cloud commcell details
        cloud_hostname, cloud_sql_username, cloud_sql_password = (
            am_clean_up_info['cloud_hostname'],
            am_clean_up_info['cloud_sql_username'],
            am_clean_up_info['cloud_sql_password']
        )

        # connect to service commcell
        service_commcell = Commcell(sc_hostname, sc_username, sc_password, verify_ssl=self._verify_ssl)

        # Support for load balancer used in k8s - use sql hostname if provided
        if sql_hostname := am_clean_up_info.get('service_commcell_sql_hostname'):
            sc_sql_hostname = sql_hostname
        else:
            sc_sql_hostname = service_commcell.commserv_hostname
        
        self.log.info('Connecting to SQL DBs for AM clean up...')
        cloud_commserv_db = self.__connect_to_db(cloud_hostname, cloud_sql_username, cloud_sql_password, 'CommServ', windows_cs=True)
        
        cloud_cvcloud_db = self.__connect_to_db(cloud_hostname, cloud_sql_username, cloud_sql_password, 'CVCloud', windows_cs=True)

        sc_csdb = self.__connect_to_db(sc_sql_hostname, sc_sql_username, sc_sql_password, 'CommServ', windows_cs=not is_linux_sc)

        # Get default webserver of service commcell
        default_webserver_name, default_webserver_hostname = self.__get_default_webserver(sc_csdb)

        # support for load balancer used in k8s - use mongo hostname if provided
        if am_clean_up_info.get('service_commcell_mongo_hostname'):
            default_webserver_hostname = am_clean_up_info['service_commcell_mongo_hostname']

        self.log.info('Starting Active Management clean up...')
        self.cloud_side_gcm_clean_up(service_commcell.commserv_name, cloud_commserv_db, cloud_cvcloud_db)
        self.service_commcell_gcm_clean_up(sc_csdb)
        self.service_commcell_mongo_clean_up(default_webserver_hostname, am_clean_up_info['service_commcell_mongo_password'])

        # Restart webservice on service commcell
        self.__restart_service_commcell_webservice(service_commcell, bool(am_clean_up_info.get('linux_service_commcell')), default_webserver_name)

        # Restart HubService on HubServer with multiple retries as it is flaky
        self.__restart_hub_service(hub_client_name=am_clean_up_info['hub_client_name'])

        self.log.info('Active Management clean up completed successfully!')

    def __get_default_webserver(self, csdb: database_helper.MSSQL) -> Tuple[str, str]:
        """Method to get the default webserver of the commcell"""
        query = "SELECT CL.name, CL.net_hostname FROM GXGlobalParam P JOIN APP_Client CL ON P.value = CL.id WHERE P.name LIKE 'Web Search Server for Super Search'"
        return csdb.execute(query).rows[0] # (webserver_name, webserver_hostname)

    def __execute_interactive_workflow(self, request_xml: str):
        """
        Helper function to execute an interactive workflow.

        Args:
            request_xml (str): The XML request to execute the workflow.

        Returns:
            str: The XML response string.
        """
        self.log.info(f"Sending request - [{request_xml}]")
        flag, response = self.__wf_commcell.workflows._cvpysdk_object.make_request(
            'POST',
            self.__wf_commcell._services['EXECUTE_INTERACTIVE_WORKFLOW'],
            request_xml
        )

        if not flag:
            response_string = self.__wf_commcell._update_response_(
                response.text)
            raise Exception('Response', '101', response_string)

        if not response:
            raise Exception('Response', '102')

        self.log.info(f"Received response - [{response.json()}]")
        return response.json().get("message", {})  # XML string

    def __execute_trials_v2_workflow(self, workflow_name: str, workflow_inputs: dict, wf_commcell: Commcell = None) -> None:
        """
        Executes the Trials v2 workflow.

        Args:
            workflow_name (str): The name of the workflow.
            workflow_inputs (dict): Input parameters for the workflow.
            wf_commcell (Commcell): The Commcell object for the workflow execution.

        Raises:
            Exception: If creating the tenant fails.
        """
        self.log.info(
            f"Creating company on CommCell ring => {workflow_inputs['commcell']}")
        self.__wf_commcell = wf_commcell or self.__commcell
        client_id = self.__wf_commcell.commserv_client.client_id
        client_name = self.__wf_commcell.commserv_client.client_name
        hostname = self.__wf_commcell.commserv_client.client_hostname

        # To start workflow job
        request_xml = f"""
            <Workflow_StartWorkflow>
                <workflow workflowName='{workflow_name}'/>
            </Workflow_StartWorkflow>
        """.strip()
        response_xmlstring = self.__execute_interactive_workflow(request_xml)
        root = ET.ElementTree(ET.fromstring(response_xmlstring)).getroot()

        # Send inputs to the triggered job
        session = root.attrib['sessionId']
        job_id = root.attrib['jobId']
        process_step_id = root.attrib['processStepId']
        popup_request_xml = '<Workflow_PopupInputRequest ' \
            f'sessionId="{session}" jobId="{job_id}" processStepId="{process_step_id}" ' \
            f'okClicked="1" action="OK" ' \
            f'inputXml="&lt;inputs>' \
            f'&lt;firstName class=&quot;java.lang.String&quot;>' \
            f'{workflow_inputs["firstname"]}&lt;/firstName>' \
            f'&lt;lastName class=&quot;java.lang.String&quot;>{workflow_inputs["lastname"]}' \
            f'&lt;/lastName>' \
            f'&lt;companyName class=&quot;java.lang.String&quot;>' \
            f'{workflow_inputs["company_name"]}&lt;/companyName>' \
            f'&lt;email class=&quot;java.lang.String&quot;>{workflow_inputs["email"]}' \
            f'&lt;/email>' \
            f'&lt;country class=&quot;java.lang.String&quot;>Canada&lt;/country>&lt;' \
            f'commcell class=&quot;java.lang.String&quot;>' \
            f'{workflow_inputs["commcell"]}&lt;/commcell>' \
            f'&lt;phone class=&quot;java.lang.String&quot;>{workflow_inputs["phone"]}' \
            f'&lt;/phone>&lt;/inputs>">' \
            f'<client clientId="{client_id}" clientName="{client_name}" ' \
            f'hostName="{hostname}"/>' \
            f'<commCell commCellId="{client_id}" commCellName="{client_name}"/>' \
            f'</Workflow_PopupInputRequest>'
        response_xmlstring = self.__execute_interactive_workflow(
            popup_request_xml)
        expected_success_response = "Request Queued , look out for email with reset password link or reset pwd from Commandcenter as MSP"
        if expected_success_response not in response_xmlstring:
            raise Exception(f'Creating tenant failed: {response_xmlstring}')

        # Click OK part
        root = ET.ElementTree(ET.fromstring(response_xmlstring)).getroot()
        process_step_id = root.attrib['processStepId']
        request_xml = '<Workflow_InformationalMessageRequest ' \
            f'sessionId="{session}" ' \
            f'jobId="{job_id}" ' \
            f'processStepId="{process_step_id}" okClicked="1" action="OK">' \
            f'<client clientId="{client_id}" clientName="{client_name}" ' \
            f'hostName="{hostname}" />' \
            f'<commCell commCellId="{client_id}" commCellName="{client_name}" csGUID=""/>' \
            '</Workflow_InformationalMessageRequest>'
        self.__execute_interactive_workflow(request_xml)

    def create_metallic_tenant(self, wf_commcell: Commcell, workflow_inputs: dict):
        """
        Method to create a tenant on Ring using a workflow.

        Args:
            wf_commcell (Commcell): The Commcell object of the CommServe where the workflow is located.
            workflow_inputs (dict): Input parameters for the workflow.
                Example:
                {
                    "firstname": "",
                    "lastname": "",
                    "company_name": "",
                    "phone": "",
                    "commcell": "",
                    "email": ""
                }
        """
        workflow_name = "Metallic Trials On-boarding v2"
        company_name = workflow_inputs['company_name']
        self.log.info(
            f"Starting workflow [{workflow_name}] with inputs - [{workflow_inputs}]")
        self.__execute_trials_v2_workflow(
            workflow_name, workflow_inputs, wf_commcell)
        self.log.info(
            "Workflow execution complete. Checking if tenant is created!")

        # Wait until company gets created
        timeout = 5 * 60  # Timeout of 5 minutes (5 * 60 seconds)
        start_time = time()

        while not self.__commcell.organizations.has_organization(company_name):
            self.__commcell.organizations.refresh()
            self.log.info(
                f"Tenant is still not created [{company_name}]. Sleeping for 30 seconds")
            sleep(30)

            elapsed_time = time() - start_time
            if elapsed_time >= timeout:
                raise Exception(
                    "Tenant creation from trials v2 workflow failed. Please check logs for more info")

        self.log.info(f"Tenant [{company_name}] created successfully.")

    def configure_hybrid_customer(self, mssql_obj: database_helper.MSSQL, info: dict) -> bool:
        """Method to insert hybrid customer entry in HistoryDB

            Args:
                mssql_obj   :  database_helper.MSSQL('hostname\\Commvault', sql_user, sql_password, 'HistoryDB')

                info (dict) :  Commcell Information

                info = {
                    'AccountId' : '',
                    'AccountName' : '',
                    'CommCell' : '',
                    'MetallicTenantGUID' : '',
                }

            Returns:
                bool : Indicating if customer is hybrid or not
        """
        if self.is_customer_hybrid(mssql_obj, account_id=info['AccountId']):
            return True
        
        query = f"""
            INSERT INTO [HistoryDB].[dbo].[MCC_MirageSoftwareAndMetallicCustomers]
            (AccountId, AccountName, CommCell, CommCellIsActive, MetallicTenantGUID, MetallicIsActive)
            SELECT '{info["AccountId"]}', '{info["AccountName"]}', '{info["CommCell"]}', 'True', '{info["MetallicTenantGUID"]}', 'True'
        """
        mssql_obj.execute(query)

        return self.is_customer_hybrid(mssql_obj, account_id=info['AccountId'])

    def deconfigure_hybrid_customer(self, mssql_obj: database_helper.MSSQL, account_id: str) -> bool:
        """Method to remove hybrid customer entry from HistoryDB

        Args:
            mssql_obj   :  database_helper.MSSQL('hostname\\Commvault', sql_user, sql_password, 'HistoryDB')

            account_id (str)    :   Account ID of the customer

        Returns:
            bool : Indicating if customer is hybrid or not
        """
        query = f"DELETE FROM [HistoryDB].[dbo].[MCC_MirageSoftwareAndMetallicCustomers] WHERE AccountId = '{account_id}'"
        mssql_obj.execute(query)

        return self.is_customer_hybrid(mssql_obj, account_id)

    def is_customer_hybrid(self, mssql_obj: database_helper.MSSQL, account_id: str) -> bool:
        """Method to check if customer is hybrid

        Args:
            mssql_obj   :  database_helper.MSSQL('hostname\\Commvault', sql_user, sql_password, 'HistoryDB')

            account_id (str)    :   Account ID of the customer
        """
        query = f"SELECT 1 FROM [HistoryDB].[dbo].[MCC_MirageSoftwareAndMetallicCustomers] WHERE AccountId = '{account_id}';"

        return bool(mssql_obj.execute(query).rows)

    def get_customer_usergroups(self, csdb) -> list:
        """
            Method to get customer user groups

            Args:
                csdb    :   Commserve DB object
        """
        query = """SELECT UG.id, UG.name, UG.umdsProviderId FROM UMGroups UG WITH(NOLOCK)
        JOIN UMGroupsProp PROP WITH(NOLOCK) ON UG.id = PROP.componentNameId
        WHERE PROP.attrName LIKE 'Customer User Group'"""

        csdb.execute(query)

        details = [(usergroup_name, int(usergroup_id), int(company_id))
                   for usergroup_id, usergroup_name, company_id in csdb.fetch_all_rows()]

        return details

    def get_users_of_customer_group(self, customer_group: str) -> list:
        """
            Method to get user emails of specified customer group name
            Args:
                customer_group (str)    :   User group name
        """
        self.__commcell.users.refresh()
        self.__commcell.user_groups.refresh()
        user_emails = [self.__commcell.users.get(
            user_name).email for user_name in self.__commcell.user_groups.get(customer_group).users]
        self.log.info(f'User emails fetched from API: {user_emails}')
        return user_emails

    def configure_user_account(self, service_commcell: Union[Commcell, str], okta_helper,
                               company_name: str, new_password: str,
                               cloud_commserv_csdb: database_helper.MSSQL, 
                               cloud_history_db: database_helper.MSSQL, 
                               hybrid_account: bool=False, metallic_commcell: Commcell = None, metrics_commcell: Commcell = None,
                               ring_name: str=None,
                               make_global_admin: bool = True,
                               cloud_admin_password: str=None) -> Tuple[str, str]:
        """
        Method to configure user account on cloud side

        Args:
            service_commcell (commcell or str)  : Commcell object to create user on service commcell or else just pass Commcell Hex
            okta_helper (OktaHelper)     : Okta helper object
            company_name (str)           : Name of the company
            new_password (str)           : New password for the user

            Note: If the account needs to be configured as hybrid, then the following parameters are needed

            hybrid_account (bool)        : Flag indicating if the account needs to be configured as hybrid or not
            metallic_commcell (Commcell) : Commcell object of the metallic commcell (optional, needed only if the account needs to be configured as hybrid)
            metrics_commcell (Commcell)  : Commcell object of the metrics commcell (optional, needed only if the account needs to be configured as hybrid)
            cloud_history_db (database_helper.MSSQL) : Database connection object for cloud history

        Returns:
            Tuple[str, str] : Tuple containing the cloud user name and email address
        """
        user_details = {
            'FirstName': company_name,
            'LastName': str(randint(0, 100000000)),
            'EmailAddress': f'{company_name}{randint(0, 100000000)}@{company_name}.com',
            'Password': new_password,
            'CompanyName': company_name
        }
        cloud_user = user_details['EmailAddress'].split('@')[0]

        # register user to the cloud
        self.log.info('Registering user to the cloud...')
        max_retries = 3
        retries = 0
        while retries < max_retries:
            try:
                # For Mirage cases, there is no need of service commcell object, just commcell hex is enough
                if isinstance(service_commcell, str):
                    service_commcell_hex = service_commcell
                else:
                    service_commcell_hex = LicenseDetails(service_commcell).commcell_id_hex

                self.run_register_beaming_wf(service_commcell_hex)
                self.run_create_company_subgroup_users_wf(user_name=cloud_user, user_email=user_details['EmailAddress'], company_name=company_name)
                # self.register_with_new_user(user_details, service_commcell)
                self.log.info('User registered successfully!')
                break
            except Exception as e:
                self.log.error(f'Error occurred while registering user! [Error: {e}].')
                retries += 1
                if retries == max_retries:
                    raise e
                self.log.info(f'Retrying Registration in 2 mins... [Attempt: {retries}]')
                sleep(120)

                # Sometimes, the user gets registered, and the registration job might still be running. However, we still encounter an exception.
                # Therefore, just check if the user is created and break the loop if the user is created.
                self.__commcell.users.refresh()
                if self.__commcell.users.has_user(cloud_user):
                    self.log.info('User already registered! Skipping registration... Sleeping for 3 mins to let the Commcell Registraion WF job complete...')
                    sleep(180)
                    break

        # cloud side operations
        self.__commcell.users.refresh(hard=True)
        self.__commcell.user_groups.refresh(hard=True)

        # update password for the user
        self.log.info(f'Updating password for the user: [{cloud_user}]...')
        self.__commcell.users.get(cloud_user).update_user_password(new_password, cloud_admin_password)

        if make_global_admin:
            self.make_user_global_admin(cloud_user, company_name)

        # create necessary users at service commcell and okta side
        if isinstance(service_commcell, Commcell):
            self.log.info('Creating user at service commcell side with the same email address...')
            service_commcell.users.add(user_name=cloud_user, email=user_details["EmailAddress"], password=user_details['Password'], local_usergroups=['master'])

        self.log.info('Cleaning up the old okta user from the same company...')
        for email in okta_helper.filter_users(marker=f'@{company_name}.com'):
            okta_helper.delete_user(email)

        self.log.info('Creating user at okta side with the same email address...')
        okta_helper.create_user(first_name=user_details['FirstName'],
                                last_name=user_details['LastName'],
                                email=user_details['EmailAddress'],
                                password=user_details['Password']
                                )

        # once user is registered, we can get the account id from the csdb
        account_id = self.get_account_id(company_name, cloud_csdb=cloud_commserv_csdb)
        
        if hybrid_account:
            workflow_inputs = {
                "firstname": user_details['FirstName'],
                "lastname": user_details['LastName'],
                "company_name": company_name,
                "phone": "0000000000",
                "commcell": ring_name,
                "email": user_details['EmailAddress'],
                "account_id": account_id
            }
            self.make_customer_hybrid(workflow_inputs, metallic_commcell, metrics_commcell, cloud_history_db)
        else:
            self.deconfigure_hybrid_customer(cloud_history_db, account_id)

        self.log.info(f'Configuration Complete!! [User: {cloud_user}]')

        return cloud_user, user_details['EmailAddress']

    def make_user_global_admin(self, user_name: str, company_name: str) -> None:
        """
            Method to make user a global admin

            Args:
                user_name (str)     :   Username to make global admin
                company_name (str)  :   Company name of the user
        """
        if not self.__commcell.roles.has_role('Metrics Management Admin_Role'):
            raise Exception('Metrics Management Admin_Role not found in the Commcell!')
        
        self.log.info(f'Adding user: [{user_name}] to the user group [{company_name}]...')
        self.__commcell.user_groups.get(company_name).update_usergroup_members(request_type='UPDATE', users_list=[user_name])

        self.log.info(f'Making user: [{user_name}] a global admin.. ')
        security_assoc = {
            'assoc1':
                {
                    'userGroupName': [company_name],
                    'role': ['Metrics Management Admin_Role']
                }
        }
        self.__commcell.users.refresh()
        self.__commcell.users.get(user_name).update_security_associations(security_assoc, 'UPDATE')
        self.log.info('User made global admin successfully!')

    def get_account_id(self, company_name: str, cvlicgen_db: database_helper.MSSQL=None, cloud_csdb: database_helper.MSSQL=None) -> str:
        """
            Method to get account ID of the company

            Args:
                cvlicgen_db (MSSQL) :   Licence DB object
                company_name (str)  :   Company name
        """
        if cvlicgen_db:
            account_id_query = f"SELECT AccountId FROM LACCMAccount WHERE Name = '{company_name}'"
            account_id = cvlicgen_db.execute(account_id_query).rows[0][0]
            self.log.info(f'Account ID fetched from Licence DB: {account_id}')
        else:
            query = f"SELECT PROP.attrVal FROM UMGroups UG JOIN UMGroupsProp PROP ON UG.id = PROP.componentNameId AND UG.name = '{company_name}' AND PROP.attrName = 'Customer User Group'"
            account_id = cloud_csdb.execute(query).rows[0][0]
            self.log.info(f'Account ID fetched from CSDB: {account_id}')
        return account_id

    def make_customer_hybrid(self, workflow_inputs:dict, metallic_commcell: Commcell, metrics_commcell: Commcell, cloud_history_db: database_helper.MSSQL) -> None:
        """
            Method to make a customer hybrid

            Args:
                workflow_inputs (dict)          :   Workflow inputs
                metallic_commcell (Commcell)    :   Metallic Commcell object
                metrics_commcell (Commcell)     :   Metrics Commcell object
                cloud_history_db (MSSQL)        :   Cloud History DB object

                workflow_inputs = {
                    "firstname": "",
                    "lastname": "",
                    "company_name": ,
                    "phone": "",
                    "commcell": "M052",
                    "email": "",
                    "account_id":""
                }    
        """
        company_name = workflow_inputs['company_name']

        self.log.info(f'Creating company [{company_name}] on metallic side...')
        try:
            self.create_metallic_tenant(metrics_commcell, workflow_inputs)
        except Exception as e:
            self.log.error(f'Error occurred while creating company on metallic side! [Error: {e}].')
            self.log.warn('Sometimes WF job fails but company gets created successfully!. So, Waiting for a minute and will check if company is created...')
            sleep(60)
            metallic_commcell.organizations.refresh()
            if not metallic_commcell.organizations.has_organization(company_name):
                raise e
            self.log.info(f'Company [{company_name}] created successfully!')

        metallic_commcell.organizations.refresh()
        self.log.info(f'AuthCode: {metallic_commcell.organizations.get(company_name).auth_code}')

        self.log.info('Inserting entries in HistoryDB...')
        self.configure_hybrid_customer(mssql_obj=cloud_history_db, info={
            'AccountId': workflow_inputs['account_id'],
            'AccountName': company_name,
            'CommCell': 2,
            'MetallicTenantGUID': metallic_commcell.organizations.all_organizations_props[company_name.lower()]['GUID']
        })
        self.log.info('Successfully made customer hybrid!')

    def cloud_side_gcm_clean_up(self, commcell_name: str, cloud_commserv_db: database_helper.MSSQL, cloud_cvcloud_db: database_helper.MSSQL) -> None:
        """
            Method to clean up the GCM entries on cloud side

            Args:
                commcell_name           :   Commcell Name
                cloud_commserv_db       :   Cloud Commserve DB object
                cloud_cvcloud_db        :   Cloud CVCloud DB object
        """
        self.log.info('Cleaning up on Cloud Side...')

        query1 = f"SELECT ID, CommServGUID FROM cf_CommcellIdNameMap WHERE CustomerName = '{commcell_name}'"
        component_id, commcell_guid = cloud_cvcloud_db.execute(query1).rows[0]

        delete_queries = [
            f"DELETE ACP FROM APP_ComponentProp ACP WHERE componentType = 1055 AND componentId = {component_id}",
            f"DELETE ACP FROM APP_ComponentProp ACP WHERE PropertyTypeId = 4002 AND componentId = {component_id}",
            f"DELETE PROP FROM App_ThirdPartyAppProp PROP INNER JOIN App_ThirdPartyApp APP ON PROP.componentNameId = APP.id AND APP.appType = 11 AND APP.appName = '{commcell_guid}'",
            f"DELETE APP FROM App_ThirdPartyApp APP WHERE appType = 11 and appName = '{commcell_guid}'"
        ]

        for query in delete_queries:
            row_count = cloud_commserv_db.execute(query).rowcount
            self.log.info(f"Rows affected for query '{query}': {row_count}")

    def service_commcell_gcm_clean_up(self, service_commcell_csdb: database_helper.MSSQL) -> None:
        """
            Method to clean up the GCM entries on service commcell side

            Args:
                service_commcell_csdb   :   Service Commcell Commserve DB object
        """
        self.log.info('Cleaning up on the service commcell...')

        queries = [
            'DELETE FROM APP_ComponentProp WHERE PropertyTypeId = 4002',
            "DELETE FROM GXGlobalParam WHERE name LIKE 'CVHubUrl'",
            'DELETE FROM APP_ComponentProp WHERE componentType = 1055',
            "DELETE PROP FROM App_ThirdPartyAppProp PROP INNER JOIN App_ThirdPartyApp APP ON APP.id = PROP.componentNameId AND APP.appType = 10",
            "DELETE FROM App_ThirdPartyApp WHERE appType = 10"
        ]

        for query in queries:
            row_count = service_commcell_csdb.execute(query).rowcount
            self.log.info(f"Rows affected for query '{query}': {row_count}")

    def service_commcell_mongo_clean_up(self, mongo_hostname: str, mongo_password: str, mongo_username: str = 'mongoadmincv') -> None:
        """
            Method to clean up the MongoDB entries on service commcell side

            Args:
                mongo_hostname (str)    :   MongoDB hostname
                mongo_password (str)    :   MongoDB password
                mongo_username (str)    :   MongoDB username    
        """
        self.log.info(f'Cleaning up MongoDB on {mongo_hostname}...')
        self.log.info(f'On Linux Service Commcell, Please make sure that mongo can be connected remotely... [Mongo: {mongo_hostname}]')

        mongo_port = 27017
        databases_to_delete = ['GCMTracking', 'GlobalConfigManager']
        uri = f'mongodb://{mongo_username}:{mongo_password}@{mongo_hostname}:{mongo_port}/'

        # Connect to MongoDB
        from pymongo import MongoClient
        client = MongoClient(uri)

        # Delete the specified databases
        for db_name in databases_to_delete:
            client.drop_database(db_name)
            self.log.info(f"The database '{db_name}' on host '{mongo_hostname}' has been deleted successfully.")
        client.close()

    def validate_active_management_status(self, cloud_csdb: database_helper.MSSQL, service_commcell_csdb: database_helper.MSSQL, info: dict) -> None:
        """
        Method to validate active management status on cloud and service commcell side

        Args:
            cloud_csdb                  :   Cloud Commserve DB object
            service_commcell_csdb       :   Service Commserve DB object
            info (dict)                 :   Other Information

            info {
                'CompanyGUID': '',
                'CompanyID': '',
                'HubBaseUrl': '',
                'CommcellGUID': ''
            }
        """
        self.log.info('Validating Active Management status on service commcell side...')

        # Validate Third Party App prop on service commcell side
        third_party_app_id = service_commcell_csdb.execute(f"SELECT id FROM App_ThirdPartyApp WHERE appType = 10 AND appName = '{info['CompanyGUID']}'").rows[0][0]
        third_party_app_prop_set = bool(service_commcell_csdb.execute(f"SELECT 1 FROM App_ThirdPartyAppProp WHERE componentNameId = {third_party_app_id} AND attrName = 'Cloud Active Management Enabled' and attrVal = 1").rows)
        
        if not third_party_app_prop_set:
            raise Exception(f'Cloud Active Management Enabled prop is not set on service commcell! Status: [{third_party_app_prop_set}]')
        self.log.info('Third Party App prop set successfully on service commcell side!')

        # Validate CVHubUrl on service commcell side
        cvhuburl = service_commcell_csdb.execute("SELECT value FROM GXGlobalParam WHERE name LIKE 'CVHubUrl'").rows[0][0]
        expected_cvhuburl = info['HubBaseUrl']
        if cvhuburl != expected_cvhuburl:
            raise Exception(f'CVHubUrl mismatch! Expected: {expected_cvhuburl}, Actual: {cvhuburl}')
        self.log.info('CVHubUrl validated successfully on service commcell side!')

        # Validate Commcell tracking ID on service commcell side
        service_commcell_tracking_id = service_commcell_csdb.execute("SELECT stringVal FROM APP_ComponentProp WHERE componentType = 1055").rows[0][0]
        self.log.info(f'Commcell tracking ID: {service_commcell_tracking_id}')
        self.log.info('Active Management status validated successfully on service commcell side!')

        self.log.info('Validating Active Management status on cloud side...')

        # Validate Commcell tracking ID on cloud side
        cloud_side_commcell_tracking_id = cloud_csdb.execute(f"SELECT stringVal FROM APP_ComponentProp WHERE componentType = 1055 and stringVal = '{service_commcell_tracking_id}'").rows[0][0]
        if cloud_side_commcell_tracking_id != service_commcell_tracking_id:
            raise Exception(f'Commcell tracking ID mismatch! Service Commcell Side: {service_commcell_tracking_id}, Cloud Side: {cloud_side_commcell_tracking_id}')

        # Validate Third Party App prop on cloud side
        third_party_app_id = cloud_csdb.execute(f"SELECT id FROM App_ThirdPartyApp WHERE appType = 11 and appName = '{info['CommcellGUID']}'").rows[0][0]
        third_party_app_prop_val = cloud_csdb.execute(f"SELECT attrVal FROM App_ThirdPartyAppProp WHERE componentNameId = {third_party_app_id} AND attrName = 'Company for TPA'").rows[0][0]
        
        if int(third_party_app_prop_val) != int(info['CompanyID']):
            raise Exception(f'Company for TPA mismatch! Expected: {info["CompanyID"]}, Actual: {third_party_app_prop_val}')
        
        self.log.info('Active Management status validated successfully on cloud side!')

    def perform_active_management_and_do_validation(
        self,
        service_commcell_name: str,
        admin_console: AdminConsole,
        windows_cs: bool = True,
        negative_validation: bool = False,
        hybrid: bool = False,
    ) -> None:
        """
        Method to perform active management and validate the flow

        Args:
            service_commcell_name   :   Name of the service commcell
            admin_console           :   AdminConsole object
            windows_cs              :   Flag indicating if the service commcell is windows or not
            negative_validation     :   Flag indicating if the testcase is for negative validation or not
            hybrid                  :   Flag indicating if the testcase is for hybrid or not

        Add the following config details in config.json:
        {
            ...
            "GCM": {
                "CLOUD": {
                    "cloud_name": "",
                    "cloud_hostname": "",
                    "cloud_commcell_username": "",
                    "cloud_commcell_password": "",
                    "cloud_sql_username": "",
                    "cloud_sql_password": "",
                    "hub_client_name": ""
                },
                "RING": {
                    "metallic_ring_name": "",
                    "metallic_ring_hostname": "",
                    "metallic_ring_username": "",
                    "metallic_ring_password": ""
                },
                "METALLIC_METRICS": {
                    "metrics_hostname": "",
                    "metrics_username": "",
                    "metrics_password": ""
                },
                "OKTA": {
                    "okta_org_url": "",
                    "api_token": ""
                },
                "CommcellName1": {
                    "company_name": "",
                    "commcell_hex": "",
                    "service_commcell_hostname": "",
                    "service_commcell_username": "",
                    "service_commcell_password": "",
                    "service_commcell_sql_hostname": "",
                    "service_commcell_sql_username": "",
                    "service_commcell_sql_password": "",
                    "service_commcell_mongo_hostname": "",
                    "service_commcell_mongo_password": ""
                }
                "CommcellName2": {
                    ...
                }
            }
            ...
        }
        """
        # Get config details
        gcm_config = get_config().GCM
        CLOUD_CONFIG = gcm_config.CLOUD
        RING_CONFIG = gcm_config.RING
        METRICS_CONFIG = gcm_config.METALLIC_METRICS
        OKTA_CONFIG = gcm_config.OKTA

        # Fetch service commcell details
        SERVICE_COMMCELL = self.__fetch_service_commcell(gcm_config, service_commcell_name)

        # Create commcell objects
        cloud_commcell = Commcell(CLOUD_CONFIG.cloud_hostname, CLOUD_CONFIG.cloud_commcell_username, CLOUD_CONFIG.cloud_commcell_password, verify_ssl=self._verify_ssl)
        metallic_ring = Commcell(RING_CONFIG.metallic_ring_hostname, RING_CONFIG.metallic_ring_username, RING_CONFIG.metallic_ring_password, verify_ssl=self._verify_ssl)
        service_commcell = Commcell(SERVICE_COMMCELL.service_commcell_hostname, SERVICE_COMMCELL.service_commcell_username, SERVICE_COMMCELL.service_commcell_password, verify_ssl=self._verify_ssl)

        # Create Okta helper
        okta_helper = OktaHelper(OKTA_CONFIG.okta_org_url, OKTA_CONFIG.api_token)

        # Create database connections
        cloud_commserv_csdb = self.__connect_to_db(
            cloud_commcell.commserv_hostname, CLOUD_CONFIG.cloud_sql_username, CLOUD_CONFIG.cloud_sql_password, 'CommServ', not cloud_commcell.is_linux_commserv
        )
        cloud_history_db = self.__connect_to_db(
            cloud_commcell.commserv_hostname, CLOUD_CONFIG.cloud_sql_username, CLOUD_CONFIG.cloud_sql_password, 'HistoryDB', not cloud_commcell.is_linux_commserv
        )
        service_commcell_csdb = self.__connect_to_db(
            SERVICE_COMMCELL.service_commcell_sql_hostname,
            SERVICE_COMMCELL.service_commcell_sql_username,
            SERVICE_COMMCELL.service_commcell_sql_password,
            'CommServ', windows_cs
        )

        # create metric commcell object if hybrid
        metric_commcell = Commcell(METRICS_CONFIG.metrics_hostname, METRICS_CONFIG.metrics_username, METRICS_CONFIG.metrics_password, verify_ssl=self._verify_ssl) if hybrid else None

        # Perform clean up before starting the testcase
        am_mgmt_clean_up_info = self.__prepare_clean_up_info(CLOUD_CONFIG, RING_CONFIG, SERVICE_COMMCELL, windows_cs)
        self.clean_up(company_name=SERVICE_COMMCELL.company_name, metallic_obj=metallic_ring, okta_helper=okta_helper,
                      am_clean_up_info=am_mgmt_clean_up_info, service_commcell=service_commcell)

        self.log.info('Post cleanup logging into service commcell again...')
        self.log.info('If service commcell login errors with "Commcell not reachable" then webservice restart did not happen properly... Please check/start manually...')
        service_commcell = Commcell(SERVICE_COMMCELL.service_commcell_hostname, SERVICE_COMMCELL.service_commcell_username, SERVICE_COMMCELL.service_commcell_password, verify_ssl=self._verify_ssl)

        # Configure user account
        cloud_user_name, cloud_user_email = self.configure_user_account(
            service_commcell, okta_helper, SERVICE_COMMCELL.company_name, 
            SERVICE_COMMCELL.service_commcell_password, cloud_commserv_csdb, 
            cloud_history_db, hybrid, metallic_ring, metric_commcell, 
            RING_CONFIG.metallic_ring_name,
            make_global_admin=True,
            cloud_admin_password=CLOUD_CONFIG.cloud_commcell_password
        )

        # Fetch auth code for newly created company, if hybrid
        auth_code = self.__fetch_auth_code(metallic_ring, company_name=SERVICE_COMMCELL.company_name) if hybrid else None

        # Login as newly created user
        self.__login_as_new_user(admin_console, cloud_commcell, cloud_user_email, SERVICE_COMMCELL.service_commcell_password)

        # Validate active management flow       
        self.mirage_cc_helper.validate_active_management_flow(SERVICE_COMMCELL.company_name, cloud_user_name, SERVICE_COMMCELL.service_commcell_password,
                                                            service_commcell, cloud_commserv_csdb, service_commcell_csdb,
                                                            negative_validation=negative_validation, authcode=auth_code,
                                                            linux_sc_commcell_obj=service_commcell if not windows_cs else None)

        self.log.info('Testcase execution completed successfully!')

    def __fetch_service_commcell(self, config, service_commcell_name):
        for item in config._fields:
            if service_commcell_name.lower() == item.lower():
                return getattr(config, item)
        raise ValueError(f"Service commcell with name '{service_commcell_name}' not found in config")

    def __connect_to_db(self, hostname, username, password, db_name, windows_cs=True):
        if not windows_cs:
            return database_helper.MSSQL(hostname, username, password, db_name)
        else:
            return database_helper.MSSQL(f'{hostname}\\Commvault', username, password, db_name)

    def __prepare_clean_up_info(self, cloud_config, ring_config, service_commcell, windows_cs):
        am_mgmt_clean_up_info = {}
        am_mgmt_clean_up_info.update(cloud_config._asdict())
        am_mgmt_clean_up_info.update(ring_config._asdict())
        am_mgmt_clean_up_info.update(service_commcell._asdict())
        am_mgmt_clean_up_info['linux_service_commcell'] = not windows_cs
        return am_mgmt_clean_up_info

    def __fetch_auth_code(self, metallic_ring_obj, company_name):
        metallic_ring_obj.organizations.refresh()
        auth_code = metallic_ring_obj.organizations.get(company_name).auth_code
        self.log.info(f'Fetched AuthCode From Metallic Company => {auth_code}')
        return auth_code

    def __login_as_new_user(self, admin_console, cloud_commcell, email, password):
        self.log.info('Logging in as a newly created user...')
        AdminConsole.logout_silently(admin_console)

        admin_console.login(email, password)
        WebDriverWait(admin_console.driver, 300).until(ec.element_to_be_clickable((By.ID, "mirageDashboard")))
        admin_console.wait_for_completion()
        self.mirage_cc_helper = MirageCCHelper(admin_console=admin_console, commcell=cloud_commcell)

    def retry_function_execution(self, func: Callable, **kwargs) -> None:
        """
            Method to retry function execution with retries
            
            Args:
                func (Callable) : Function to execute
                kwargs (dict)   : Keyword arguments for the function
        """
        max_retries = kwargs.pop('max_retries', 3)
        sleep_time = kwargs.pop('sleep_time', 60)

        for attempt in range(1, max_retries + 1):
            try:
                self.log.info(f'Executing function with attempt: {attempt}')
                func(**kwargs)
                break  # Break if successful
            except Exception as exp:
                self.log.info(f'Error occurred! [Error: {exp}].')
                self.log.info(traceback.format_exc())

                if kwargs.get('admin_console'):
                    kwargs['admin_console'].refresh_page()

                self.log.info('Retrying in a minute...')
                sleep(sleep_time)
        else:
            self.log.info('Retrying with last attempt...')
            func(**kwargs)

class MirageTrialHelper(MirageCCHelper, MirageApiHelper):
    """Helper class to perform Mirage trial operations"""

    def __init__(self, admin_console: AdminConsole , commcell: Commcell, commcell_name: str = ''):
        """
            Initialize the class with the AdminConsole and Commcell objects

            Args:
                admin_console (AdminConsole)    :   AdminConsole object
                commcell (Commcell)             :   Commcell object
                commcell_name (str)             :   Commcell Name

        For config structure, refer to the method docstring of MirageApiHelper > perform_active_management_and_do_validation method
        """
        self.__admin_console = admin_console
        self.__commcell = commcell
        MirageCCHelper.__init__(self, admin_console=admin_console, commcell=commcell)
        MirageApiHelper.__init__(self, commcell=commcell)
        
        # read config details
        self.__config = get_config().GCM
        self.CLOUD_CONFIG = self.__config.CLOUD
        self.RING_CONFIG = self.__config.RING
        self.METRICS_CONFIG = self.__config.METALLIC_METRICS
        self.OKTA_CONFIG = self.__config.OKTA
        if commcell_name:
            self.SERVICE_COMMCELL = self._MirageApiHelper__fetch_service_commcell(self.__config, commcell_name)

    def __process_trial_inputs(self) -> None:
        """Method to process the trial inputs"""
        self.log.info('Processing trial inputs...')
        self.commcell_hex = self.SERVICE_COMMCELL.commcell_hex
        self.company_name = self.SERVICE_COMMCELL.company_name
        self.cloud_name = self.CLOUD_CONFIG.cloud_name
        self.ring_name = self.RING_CONFIG.metallic_ring_name
        self.password = self.CLOUD_CONFIG.cloud_commcell_password # use the same cloud password for the newly created account
        self.metrics_commcell = None
        self.auth_code = None
        self.make_global_admin = True

    def __connect_to_commcells(self) -> None:
        """Method to connect to commcells"""
        self.log.info('Connecting to commcells...')
        self.metallic_commcell = Commcell(self.RING_CONFIG.metallic_ring_hostname, self.RING_CONFIG.metallic_ring_username, self.RING_CONFIG.metallic_ring_password, verify_ssl=self._verify_ssl)

        if self.configure_hybrid_account:
            self.metrics_commcell = Commcell(self.METRICS_CONFIG.metrics_hostname, self.METRICS_CONFIG.metrics_username, self.METRICS_CONFIG.metrics_password, verify_ssl=self._verify_ssl)

        self.okta_helper = OktaHelper(self.OKTA_CONFIG.okta_org_url, self.OKTA_CONFIG.api_token)

    def __connect_to_dbs(self) -> None:
        """Method to connect to databases"""
        self.log.info('Connecting to databases...')

        self.cloud_csdb = self._MirageApiHelper__connect_to_db(self.__commcell.commserv_hostname, self.CLOUD_CONFIG.cloud_sql_username, self.CLOUD_CONFIG.cloud_sql_password, 'CommServ', not self.__commcell.is_linux_commserv)

        self.cloud_history_db = self._MirageApiHelper__connect_to_db(self.__commcell.commserv_hostname, self.CLOUD_CONFIG.cloud_sql_username, self.CLOUD_CONFIG.cloud_sql_password, 'HistoryDB', not self.__commcell.is_linux_commserv)

    def login_to_cloud_console(self, email: str, password: str, post_linking:bool=False) -> None:
        """
            Method to login as Global/NonGlobal Admin and Pre/Post Linking

            Args:
                email (str) : Email address of the user
                password (str) : Password of the user
                post_linking (bool) : Flag indicating if the login is post linking or not
                metallic_wc_hostname (str) : Metallic Commcell hostname
        """
        AdminConsole.logout_silently(self.__admin_console)

        if post_linking:
            self.__admin_console.login(email, password, saml=True)
        else:
            self.__admin_console.login(email, password)

        WebDriverWait(self.__admin_console.driver, 300).until(ec.element_to_be_clickable((By.ID, "mirageDashboard")))
        self.__admin_console.wait_for_completion()

    @PageService()
    def __do_pretrial_validations(self, company_name: str) -> None:
        """
            Method to perform pretrial validations

            Args:
                company_name (str) : Name of the company
        """
        self.log.info('Performing pretrial validations...')
        if self.is_cloud_company_switcher_available():
            raise CVWebAutomationException('[Before Trial]: The cloud switcher is accessible for global admins who are not resellers.')
            
        self.validate_service_panel_disability(is_reseller=False)

        self.validate_page_visibility(global_admin=True)

        self.validate_user_management_operations(f'{company_name}.com')

        self.validate_cloud_user_list(company_name)

    def __fetch_authcode_from_metallic(self, company_name: str) -> str:
        """Method to fetch authcode from metallic company"""
        self.metallic_commcell.organizations.refresh()
        auth_code = self.metallic_commcell.organizations.get(company_name).auth_code
        self.log.info(f'Fetched AuthCode From Metallic Company => {auth_code}')
        return auth_code

    def __validate_switching_between_ring_and_cloud(self) -> None:
        """Method to validate the switcher flow"""
        # validate switcher flow
        switcher_details = {
            'cloud_name': self.__commcell.webconsole_hostname, # on test setups, wchostname is shown in switcher
            'ring_name': self.ring_name,
            'cloud_hostname': self.__commcell.webconsole_hostname,
            'ring_hostname': self.metallic_commcell.webconsole_hostname
        }
        self.log.info(f'Validating switcher flow... [Details: {switcher_details}]')

        if self.is_cloud_company_switcher_available():
            raise CVWebAutomationException('[Post Trial]: The cloud switcher is accessible for global admins who are not resellers.')

        self.validate_switcher_flow(switcher_details, True)

        self.log.info('Switcher flow validated successfully!')

    def __validate_login_flow_from_metallic(self, ring_hostname: str) -> None:
        """
            Method to login to metallic commcell
            
            Args:
                ring_hostname (str) : Metallic Commcell hostname
        """
        self.log.info('Logging out from cloud console...')
        AdminConsole.logout_silently(self.__admin_console)

        self.login_from_metallic(ring_hostname)

        # on test setups, wchostname is shown in switcher
        self.validate_commcell_switcher(self.__commcell.webconsole_hostname, self.__commcell.webconsole_hostname, False)

        self.log.info('Successfully validated the login flow starting from metallic!')

    def login_from_metallic(self, ring_hostname: str) -> None:
        """Method to login to metallic commcell"""
        self.log.info('Logging out from current session...')
        AdminConsole.logout_silently(self.__admin_console)

        self.__admin_console.base_url = f'https://{ring_hostname}/commandcenter/'
        self.log.info('Logging into metallic...')
        try:
            self.__admin_console.login(self.user_email, self.password, saml=True)
        except Exception as e:
            self.log.info(f'Error occurred while logging into metallic console! [Error: {e}].')
            self.log.info('Ignoring the error as session at SSO might have already exists and proceeding further...')
        self.__admin_console.wait_for_completion()

    def perform_mirage_trial(self, do_only_pretrial_validations: bool = False, hybrid_account: bool=False) -> None:
        """
            Method to perform either sw only or hybrid trial based on the inputs

            Args:
                tcinputs (dict) : Testcase inputs
                admin_console (AdminConsole) : AdminConsole object
                do_only_pretrial_validations (bool) : Flag indicating if only pretrial validations are needed or not
                hybrid_account (bool) : Flag indicating if the account is hybrid or not

                tcinputs : {
                    "cloud_name": "",
                    "company_name": "",
                    "metallic_ring": "",
                    "metallic_wchostname": "",
                    "metallic_username": "",
                    "metallic_password": "",
                    "onprem_wchostname": "",
                    "onprem_username": "",
                    "onprem_password": "",
                    "okta_org_url" : "",
                    "api_token" : "",
                    "cloud_sql_user": "",
                    "cloud_sql_password": "",

                    # required for hybrid case
                    "metrics_wchostname": "",
                    "metrics_username": "",
                    "metrics_password": ""
                }
        """
        self.configure_hybrid_account = hybrid_account
        self.__process_trial_inputs()
        self.__connect_to_commcells()
        self.__connect_to_dbs()

        # Cleanup at cloud/metallic/okta side before starting the test case
        self.clean_up(self.company_name, self.metallic_commcell, self.okta_helper, self.company_name)

        # Configure required users and Configure customer as SW Only / Hybrid
        self.user_name, self.user_email = self.configure_user_account(self.commcell_hex, self.okta_helper, self.company_name, self.password, self.cloud_csdb,
                                                      self.cloud_history_db, self.configure_hybrid_account, self.metallic_commcell, self.metrics_commcell, self.ring_name, self.make_global_admin, self.password)
        
        if self.configure_hybrid_account:
            self.auth_code = self.__fetch_authcode_from_metallic(self.company_name)

        self.retry_function_execution(func=self.login_to_cloud_console, email=self.user_email, password=self.password)

        if do_only_pretrial_validations:
            self.retry_function_execution(func=self.__do_pretrial_validations, company_name=self.company_name)
            return
        
        self.retry_function_execution(func=self.subscribe_to_mirage_trial, ring_name=self.ring_name, auth_code=self.auth_code)

        # We should not reset the password as authentication happens via OpenID
        # self.metallic_commcell.users.get(f'{self.company_name}\\{self.user_name}').update_user_password(new_password=self.RING_CONFIG.metallic_ring_password, 
        #                                                                     logged_in_user_password=self.RING_CONFIG.metallic_ring_password)

        # validate post linking login flow
        self.retry_function_execution(func=self.login_to_cloud_console, email=self.user_email, password=self.password, post_linking=True)
        
        self.retry_function_execution(func=self.__validate_switching_between_ring_and_cloud)

        self.retry_function_execution(func=self.__validate_login_flow_from_metallic, ring_hostname=self.metallic_commcell.webconsole_hostname)
        
        self.log.info('Testcase execution completed successfully!')

    def validate_cloud_company_switcher(self, user_name: str, password: str, customer_usergroups: list) -> None:
        """
            Method to validate the cloud company switcher

            Args:
                user_name (str) : Username
                password (str) : Password
                customer_usergroups (list) : List of usergroups that the user is part of
        """
        self.login_to_cloud_console(user_name, password)
        self.validate_cloud_switcher(customer_usergroups)
        self.log.info(f'Validation completed successfully for user: {user_name}!')

class OktaHelper:
    """Okta Helper class to manage user on Okta"""

    def __init__(self, org_url, api_token):
        """
        Initialize the OktaHelper class with the Okta organization URL and API token.
        """
        self.okta_client = OktaClient({
            'orgUrl': org_url,
            'token': api_token
        })
        self.log = logger.get_log()

    def _run_async(self, coroutine):
        """
        Run the given asynchronous coroutine with an event loop.
        """
        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy())

        try:
            loop = asyncio.new_event_loop()
            return loop.run_until_complete(coroutine)
        finally:
            loop.close()

    def create_user(self, first_name, last_name, email, password):
        """
           Method to create a user in Okta.

            Args:
                first_name (str): The first name of the user.
                last_name (str): The last name of the user.
                email (str): The email address of the user.
                password (str): The password for the user.
        """
        self.log.info(f'Creating Okta User with email [{email}]')
        user_payload = {
            'profile': {
                'firstName': first_name,
                'lastName': last_name,
                'email': email,
                'login': email
            },
            'credentials': {
                'password': {
                    'value': password
                },
                'recovery_question': {
                    'question': "What is the food you least liked as a child?",
                    'answer': "FoodNameHere"
                }
            }
        }

        async def create_user_async():
            user, _, err = await self.okta_client.create_user(user_payload)
            if err:
                raise Exception(f"Error creating user: {err}")
            else:
                self.log.info(
                    f"User '{user.profile.firstName} {user.profile.lastName}' created successfully.")

        self._run_async(create_user_async())

    def delete_user(self, email: str):
        """
        Delete the user with the specified email

        Args:
            email (str): The email address of the user
        """
        self.log.info(f'Deleting user : [{email}] from Okta...')

        async def delete_user_async():
            users, _, err = await self.okta_client.list_users(
                query_params={
                    'filter': f'((status eq "DEPROVISIONED" or status eq "ACTIVE") and profile.email eq "{email}")'}
            )
            if err:
                raise Exception(f"Error retrieving user: {err}")

            if not users:
                raise Exception("No user found!!")

            user = users[0]
            self.log.info(f'Found user => {user.profile.email} and status => {user.status}')

            # Deactivate / Deprovision User
            if user.status != 'DEPROVISIONED':
                self.log.info(f'{user.profile.email} is not deprovisioned yet! Deprovisioning now!')
                _, err = await self.okta_client.deactivate_or_delete_user(user.id)
                if err:
                    raise Exception(f"Error deactivating user {user.profile.email}: {err}")
                else:
                    self.log.info(f"User {user.profile.email} deactivated successfully.")

            # Delete User
            _, err = await self.okta_client.deactivate_or_delete_user(user.id)
            if err:
                raise Exception(f"Error deleting user {user.profile.email}: {err}")
            else:
                self.log.info(f"User {user.profile.email} deleted successfully.")

        self._run_async(delete_user_async())

    def filter_users(self, marker: str) -> list:
        """
            Method to retrieve a list of user emails that contain the specified marker

            Args:
                marker (str)    :   Search term
        """
        async def get_users_async():
            users, _, err = await self.okta_client.list_users(query_params={
                "search": f'(profile.firstName sw "{marker}" or profile.lastName sw "{marker}" or profile.login sw "{marker}" or profile.email sw "{marker}")',
            })
            if not users:
                self.log.info(f'No users found with specified marker : [{marker}]')

            if err:
                raise Exception(f"Error retrieving users: {err}")

            email_ids = [user.profile.email for user in users if marker in user.profile.email]
            self.log.info(f'Found matching emails => {email_ids}')
            return email_ids

        return self._run_async(get_users_async())
