from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Module has all the features which are present in downloadcenter page.

DownloadCenter:

    access_manage_information    --  Access manage information

    download_package             --  Download specified packages

    get_package_list             --  Get packages list

    is_subcategory_exists        --  check if specified subcategory exists

    search_package_keyword       --  Search for package keyword in search bar

    navigate_to_downloads_tab	 --	 Navigates to the downloads tab

    add_repository	 			 --	 Adds a repository

    delete_repository			 --	 Deletes a repository

    is_repository_exists		 --	 Check if Repository exists

    add_readme_location			 --	 Adds a readme file from browse

    add_category				 --	 Adds a category for the package

    add_subcategory				 --	 Adds a subcategory for the package

    add_download				 --	 Adds a downloadable file/package

    add_package					 --	 Adds a downloadable package

    delete_package				 --	 Deletes a package

    is_package_exists			 --	 Check if package exists

    get_file_names_with_checksum --	 Gets the file names with respective checksum from the package
"""
import random
from AutomationUtils import config
from Web.Common.page_object import (
    WebAction,
    PageService
)
from Web.AdminConsole.DownloadCenter.settings import ManageInformation
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RDropDown
from Web.AdminConsole.Components.dialog import RModalDialog

_CONFIG = config.get_config()


class DownloadCenter:
    """
    Class contains Download Center operations
    """

    def __init__(self, admin_console: AdminConsole):
        self._driver = admin_console.browser.driver
        self._admin_console = admin_console
        self._rtable = Rtable(self._admin_console)
        self._rdropdown = RDropDown(self._admin_console)
        self._rmodaldialog = RModalDialog(self._admin_console)

    @property
    def download_center_url(self):
        """download center url"""
        return self._admin_console.base_url + "publicLink.do?path=%2FdownloadCenter%2Fdownloads"

    @WebAction()
    def _click_manage_information(self):
        """
        click on manage information
        """
        self._rtable.access_toolbar_menu("Manage categories")

    @WebAction()
    def _click_add_repository(self):
        """
        Clicks add repository
        """
        self._rtable.access_toolbar_menu("Add repository")

    @WebAction()
    def _click_add_package(self):
        """
        Clicks add Package
        """
        self._rtable.access_toolbar_menu("Add package")

    @WebAction()
    def _click_add_category(self):
        """
        Clicks Add Category
        """
        self._admin_console.driver.find_element(By.XPATH, "//button[contains(@title, 'Add category')]").click()

    @WebAction()
    def _click_add_subcategory(self):
        """
        Clicks Add SubCategory
        """
        self._admin_console.driver.find_element(By.XPATH, "//button[contains(@title, 'Add subcategory')]").click()

    @WebAction()
    def _set_input_by_name(self, locator, value):
        """
        Type inputs
        Args:
            locator (str) - locator
            value (str) - value
            """
        self._admin_console.fill_form_by_id(locator, value)

    @WebAction()
    def _select_repository_type(self, repository_type):
        """
        Selects repository type from the dropdown
        Args:
            repository_type (str):  Type of repository
        """
        self._rdropdown.select_drop_down_values(drop_down_id="serverType", values=[repository_type])

    @WebAction()
    def _select_webserver(self, webserver):
        """
        Selects webserver from the dropdown
        Args:
            webserver   (str):  webserver name to be selected
        """
        self._rdropdown.select_drop_down_values(drop_down_id="webserver", values=[webserver])

    @WebAction()
    def _fill_network_location_info(self, network_path, username, password):
        """
        Fills the network location info
        Args:
            network_path       (str):  valid network path
            username           (str):  Username for network path
            password           (str):  Password for network path
        """
        self._admin_console.fill_form_by_id('networkPath', network_path)
        self._admin_console.fill_form_by_id('username', username)
        self._admin_console.fill_form_by_id('password', password)

    @WebAction()
    def _fill_object_store_info(self, webconsole_url, username, password):
        """
        Fills the object store info
        Args:
            webconsole_url     (str):  Webconsole url
            username           (str):  Username for webconsole url
            password           (str):  Password for webconsole url
        """
        self._admin_console.fill_form_by_id('networkPath', webconsole_url)
        self._admin_console.fill_form_by_id('username', username)
        self._admin_console.fill_form_by_id('password', password)

    @WebAction()
    def _set_package_description(self):
        """
        Sets Description for the package
        """
        frame = self._admin_console.driver.find_element(By.CLASS_NAME, 'k-iframe')
        self._admin_console.driver.switch_to.frame(frame)
        input_field = self._admin_console.driver.find_element(By.CLASS_NAME, 'ProseMirror')
        input_field.send_keys('This is a package created by Automation')
        self._admin_console.unswitch_to_react_frame()

    @WebAction()
    def _fill_users_in_dropdown(self, dropdown_id, users, wait_until=30):
        """
        Fills users in the dropdown
        Args:
            dropdown_id     (str):  id of the dropdown
            users           (list): list of users
            wait_until      (int):  implicit wait time in seconds
        """
        input_box = self._admin_console.driver.find_element(By.ID, dropdown_id)
        for user in users:
            input_box.send_keys(user)
            self._admin_console.driver.implicitly_wait(wait_until)
            self._admin_console.driver.find_element(By.XPATH, f"//div[contains(text(),'({user})')]").click()
            self._admin_console.wait_for_completion()

    @WebAction()
    def _fill_name_in_input(self, xpath, value):
        """
        Fills name in the input field
        Args:
            xpath       (str):      xpath of the input field
            value       (str):      value to be filled in the input field
        """
        name_elem = self._admin_console.driver.find_element(By.XPATH, xpath)
        name_elem.send_keys(value)

    @PageService()
    def access_manage_information(self):
        """
        Access manage information
        """
        self._click_manage_information()
        self._admin_console.wait_for_completion()
        return ManageInformation(self._admin_console)

    @PageService()
    def search_package_keyword(self, search_keyword):
        """
        Search for package with specified keyword
        Args:
            search_keyword                  (String)      --       Keyword to be searched
        """
        self._rtable.search_for(search_keyword)

    @PageService()
    def download_package(self, package_name, user_logged_in=False):
        """
        Download package
        Args:
            package_name                     (String)     --       Name of the package
            user_logged_in                   (Bool)       --       True if user is logged in else False
        """
        if user_logged_in:
            self._rtable.access_action_item(package_name, 'Download')
        else:
            self._rtable.access_link_by_column(package_name, 'Download')

    @PageService()
    def is_subcategory_exists(self, sub_category):
        """Check specified sub category exists
        Args:
            sub_category                    (String)     --       Name of the subcategory
        """
        return self._rtable.is_entity_present_in_column('Subcategory', sub_category)

    @PageService()
    def get_package_list(self):
        """Get packages list"""
        package_data = self._rtable.get_table_data()
        package_list = package_data['Download name']
        return package_list

    @PageService()
    def navigate_to_downloads_tab(self):
        """
        Navigates to the downloads tab
        """
        self._admin_console.access_tab('Downloads')

    @PageService()
    def add_repository(self, repository_name, entity_name, repository_type='Web Servers', username=None, password=None):
        """
         Adds a repository
         Args:
             repository_name    (str):  Name of the repository
             repository_type    (str):  Type of repository to be added
             entity_name        (str):  Based on repository type (webserver/network path/webconsole url)
             username           (str):  Username for network path/webconsole url
             password           (str):  Password for network path/webconsole url
        """
        self._click_add_repository()
        self._admin_console.wait_for_completion()
        self._select_repository_type(repository_type)
        if repository_type == 'Web Servers':
            self._select_webserver(entity_name)
        elif repository_type == 'A Network Location':
            self._fill_network_location_info(entity_name, username, password)
        elif repository_type == 'Commvault Object Store':
            self._fill_object_store_info(entity_name, username, password)
        else:
            raise Exception('Please enter valid Repository Type.')
        self._set_input_by_name('respositoryName', repository_name)
        if repository_type in ['A Network Location', 'Commvault Object Store']:
            self._admin_console.click_button_using_text('Validate')
            notification = self._admin_console.get_notification()
            if notification != 'Successfully validated repository':
                raise Exception(f'Error in Validating Repository. {notification}')
        self._admin_console.click_button_using_text('Add')

    @PageService()
    def delete_repository(self, repository_name):
        """
        Deletes a repository
        Args:
            repository_name (str):  Name of the repository
        """
        self._rtable.access_action_item(repository_name, 'Delete')
        self._admin_console.click_button_using_text('Yes')

    @PageService()
    def is_repository_exists(self, repository_name):
        """
        Check if Repository exists

        Args:
            repository_name           (str):   Name of Repository
        Returns:
            True                                if Repository exist
            False                               if Repository do not exist
        """
        return self._rtable.is_entity_present_in_column('Repository name', repository_name)

    @PageService()
    def add_readme_location(self, repository_name):
        """
        Adds a readme file from browse
        Args:
            repository_name         (str):  Repository from which file will be choosen
        """
        self._admin_console.click_button_using_text('Browse repository')
        self._admin_console.wait_for_completion()
        self._rmodaldialog.select_dropdown_values('repositoriesDropdown', [repository_name])
        README_FILE_TYPES = ['doc', 'docx', 'pdf', 'ppt', 'pptx', 'html', 'htm', 'rtf', 'txt', 'describe']
        File_Names = self._rtable.get_column_data('Name')
        Allowed_files = []
        for file in File_Names:
            extension = file.split('.')[-1]
            if extension in README_FILE_TYPES:
                Allowed_files.append(file)
        choosen_file = random.choice(Allowed_files)
        self._rtable.select_rows([choosen_file])
        self._rmodaldialog.click_submit()

    @PageService()
    def add_category(self, category_name, public_view=False, public_download=False):
        """
        Adds a category for the package
        Args:
            category_name           (str):  category name to be added
            public_view             (bool): public view toggle to be enabled
            public_download         (bool): public download toggle to be enabled
        """
        self._click_add_category()
        self._admin_console.wait_for_completion()
        self._fill_name_in_input("//div[contains(@class, 'modal-content')]//input[@id='name']", category_name)
        self._admin_console.fill_form_by_id('description', 'Category created by Automation')
        if public_view:
            self._rmodaldialog.enable_toggle('publicView')
        if public_download:
            if not public_view:
                raise Exception('Public View Should be enabled for Public Download to get enable')
            self._rmodaldialog.enable_toggle('publicDownload')
        self._rmodaldialog.click_submit()

    @PageService()
    def add_subcategory(self, category_name, subcategory_name, public_view=False, public_download=False):
        """
        Adds a subcategory for the package
        Args:
            category_name       (str):  category name for which subcategory to be added
            subcategory_name    (str):  subcategory name to be added
            public_view             (bool): public view toggle to be enabled
            public_download         (bool): public download toggle to be enabled
        """
        self._click_add_subcategory()
        self._admin_console.wait_for_completion()
        self._rmodaldialog.select_dropdown_values('category', [category_name])
        self._fill_name_in_input("//div[contains(@class, 'modal-content')]//input[@id='name']", subcategory_name)
        self._admin_console.fill_form_by_id('description', 'SubCategory created by Automation')
        if public_view:
            self._rmodaldialog.enable_toggle('publicView')
        if public_download:
            if not public_view:
                raise Exception('Public View Should be enabled for Public Download to get enable')
            self._rmodaldialog.enable_toggle('publicDownload')
        self._rmodaldialog.click_submit()

    @PageService()
    def add_download(self, platform, download_type, repository_name):
        """
        Adds a downloadable file/package
        Args:
            platform            (str):  Platform for which the package is to be added
            download_type       (str):  Download Type for the package file
            repository_name     (str):  Repository from which file will be choosen
        """
        self._admin_console.select_hyperlink("Add download")
        self._admin_console.wait_for_completion()
        self._rmodaldialog.select_dropdown_values('platformDropdown', [platform])
        self._rmodaldialog.select_dropdown_values('downloadTypeDropdown', [download_type])
        self._admin_console.click_button_using_text('Browse repository')
        self._admin_console.wait_for_completion()
        self._rdropdown.select_drop_down_values(drop_down_id='repositoriesDropdown', values=[repository_name])
        File_Names = self._rtable.get_column_data('Name')
        choosen_file = random.choice(File_Names)
        self._rtable.select_rows([choosen_file])
        self._admin_console.click_button_using_text('Select')
        self._admin_console.wait_for_completion()
        self._admin_console.click_button_using_text('Save')
        self._admin_console.wait_for_completion()

    @PageService()
    def add_package(self, package_name, repository_name, category_name, subcategory_name, vendor='CommVault',
                    version=11, rank=1, platform='Windows', download_type='Config', visible_to=None,
                    not_visible_to=None, early_preview=None):
        """
        Adds a downloadable package
        Args:
            package_name        (str):  name of the package
            repository_name     (str):  Repository name from which package files will be added
            category_name       (str):  Category name for the package
            subcategory_name    (str):  SubCategory name for the package
            vendor              (str):  name of the vendor
            version             (int):  version of the package
            rank                (int):  Listing order of the package
            platform            (str):  Platform for which the package is to be added
            download_type       (str):  Download Type for the package file
            visible_to          (list): List of the users to which the package must be visible
            not_visible_to      (list): List of the users to which the package must not be visible
            early_preview       (list): List of the users to which the package should be available earlier than others
        """
        # Package Description Page
        self._click_add_package()
        self._admin_console.wait_for_completion()
        self._set_input_by_name('name', package_name)
        self._set_package_description()
        self.add_readme_location(repository_name)
        self.add_category(category_name)
        self._rdropdown.select_drop_down_values(drop_down_id="categoryDropdown", values=[category_name])
        self.add_subcategory(category_name, subcategory_name)
        self._rdropdown.select_drop_down_values(drop_down_id="subCategory", values=[subcategory_name])
        self._rdropdown.select_drop_down_values(drop_down_id="vendorDropdown", values=[vendor])
        self._rdropdown.select_drop_down_values(drop_down_id="versionDropdown", values=[version])
        self._set_input_by_name('rank', rank)
        self._admin_console.click_button_using_text('Next')

        # Add Package Page
        self.add_download(platform, download_type, repository_name)
        self._admin_console.click_button_using_text('Next')

        # Users Page
        if visible_to:
            self._fill_users_in_dropdown("userdropdown_visibleToUsers_usersAndGroupsList", visible_to)
        if not_visible_to:
            self._fill_users_in_dropdown("userdropdown_notvisibleToUsers_usersAndGroupsList", not_visible_to)
        if early_preview:
            self._fill_users_in_dropdown("userdropdown_earlyUsers_usersAndGroupsList", early_preview)
        self._admin_console.click_button_using_text('Next')

        # Summary Page
        self._admin_console.click_button_using_text('Submit')
        self._admin_console.wait_for_completion()

    @PageService()
    def delete_package(self, package_name):
        """
        Deletes a package
        Args:
            package_name (str):  Name of the Package
        """
        self._rtable.access_action_item(package_name, 'Delete')
        self._admin_console.click_button_using_text('Yes')

    @PageService()
    def is_package_exists(self, package_name):
        """
        Check if package exists

        Args:
            package_name           (str):   Name of Package
        Returns:
            True                                if Package exist
            False                               if Package do not exist
        """
        return self._rtable.is_entity_present_in_column('Download name', package_name)

    @PageService()
    def get_file_names_with_checksum(self, package_name):
        """
        Gets the file names with respective checksum from the package
        Args:
            package_name           (str):   Name of Package
        Return:
            file_with_checksum_dict (dict): dictionary having key as file name and value as it's md5 checksum
        """
        self._rtable.access_link_by_column(package_name, package_name)
        file_name = self._rtable.get_column_data('File name')
        checksum = self._rtable.get_column_data('SHA256 checksum')
        file_with_checksum_dict = dict(zip(file_name, checksum))
        return file_with_checksum_dict
