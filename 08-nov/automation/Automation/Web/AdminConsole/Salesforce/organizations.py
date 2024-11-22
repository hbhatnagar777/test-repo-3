from selenium.webdriver.common.by import By

# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from ..Components.page_container import PageContainer

"""
This module provides functions and operations that can be performed on the Salesforce apps list page

SalesforceApps:

    access_org()                        --  Access organization details page

    __wait_for_button_to_be_enabled()   --  Waits until button is enabled

    __test_connection()                 --  Clicks on test connection button and returns message text

    _fill_infrastructure_settings()     --  Fills in details on Infrastructure settings panel in Add organization and
                                            tests connection with database

    __wait_for_login_window_to_close()  --  Waits for login window opened by Login to Salesforce to close

    __login_with_salesforce()           --  Performs OAuth login with Salesforce

    _create_new_oauth_credentials()     --  Clicks on create new connected app credentials on Add Organization page,
                                            fills form and saves

    _fill_salesforce_account_details()  --  Fills Salesforce account details on Add Organization page and tests
                                            connection with Salesforce

    check_if_org_exists()               --  Checks if org with given name already exists in commcell

    add_org()                           --  Add a new Salesforce Organization to commcell

    _click_on_backup()                  --  Method to click on backup

    restore()                           --  Clicks on run restore for a Salesforce org and opens Select Restore Type
                                            page
"""
from cvpysdk.commcell import Commcell
from selenium.common.exceptions import TimeoutException, NoSuchElementException, NoSuchWindowException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from AutomationUtils.config import get_config
from Web.Common.page_object import PageService, WebAction
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RDropDown, ModalPanel
from Web.AdminConsole.Components.dialog import RModalDialog, ModalDialog, RBackup
from Web.AdminConsole.Components.wizard import Wizard
from .base import SalesforceBase
from .constants import DATABASE_FORM, SalesforceEnv, ACCOUNT_TYPE, VENDOR_TYPE

_CONFIG_DATA = get_config().Salesforce


class SalesforceOrganizations(SalesforceBase):
    """Class for Salesforce organizations page"""

    def __init__(self, admin_console, commcell):
        """
        Constructor for the class

        Args:
            admin_console (AdminConsole): AdminConsole object
            commcell (Commcell): Commcell object
        """
        super().__init__(admin_console, commcell)
        self.__admin_console = admin_console
        self.__driver = self.__admin_console.driver
        self.__table = Rtable(self.__admin_console)
        self.__dialog = ModalDialog(self.__admin_console)
        self.__dialog = RModalDialog(self.__admin_console)
        self.__drop_down = RDropDown(self.__admin_console)
        self.__modal_panel = ModalPanel(self.__admin_console)
        self.__backup = RBackup(self.__admin_console)
        self.__page_container = PageContainer(self.__admin_console)
        self.__wizard = Wizard(self.__admin_console)

    @PageService()
    def access_organization(self, org_name):
        """
        Access organization details page

        Args:
            org_name (str): name of organization

        Returns:
            None:
        """
        self.__page_container.select_tab("Organizations")  # Replace it with localization when available
        self.__table.access_link(org_name)

    @WebAction()
    def __click_on_test_connection(self, button):
        """
        Waits for button to become clickable, clicks on it and waits for page to load

        Args:
            button (WebElement): Button WebElement for test connection

        Returns:
            None:
        """
        button.click()

    @WebAction()
    def __get_test_connection_button(self):
        """
        Gets Selenium WebElement for Test Connection button

        Returns:
            WebElement: Test Connection button
        """
        return self.__driver.find_element(By.XPATH,
                                          f"//button[@aria-label='{self.__admin_console.props['label.testConnection']}']"
                                          )

    @WebAction()
    def __check_if_test_connection_successful(self, button):
        """
        Checks if test connection is successful

        Args:
            button (WebElement): Test Connection button

        Returns:
            bool: True if test connection successful, else False
        """
        return len(button.find_elements(By.XPATH, "span")) > 1

    @PageService()
    def __test_connection(self, button_type):
        """
        Clicks on test connection button and returns message text

        Args:
            button_type (str): Type of test connection button (Infrastructure or Salesforce)

        Returns:
            None:

        Raises:
            Exception: if test connection fails
        """
        test_connection_button = self.__get_test_connection_button()
        self.__click_on_test_connection(test_connection_button)
        message_text = "Unable to retrieve message text"
        try:
            message_text = self.__admin_console.get_notification()
        except NoSuchElementException:
            pass
        if not self.__check_if_test_connection_successful(test_connection_button):
            raise Exception(f"Test connection for {button_type} failed with message: {message_text}")

    @PageService(hide_args=True)
    def _fill_infrastructure_settings(self, **kwargs):
        """
        Fills in details on Infrastructure settings panel in Add organization and tests connection with database. If any
        keyword arguments are not provided, they are read from config file.

        Keyword Args:
            access_node (str): access node client or client group name,
            cache_path (str): path to download cache directory on access node,
            db_type (DbType): (default is DbType.POSTGRESQL),
            db_host_name (str): hostname/ip address of db server,
            db_name (str): ,
            db_instance (str):
            db_port (int): (default is 5432 for POSTGRESQL and 1433 for SQLSERVER),
            db_user_name (str): ,
            db_password (str):

        Returns:
            None:

        Raises:
            Exception: if connection to database fails
        """
        kwargs = _CONFIG_DATA.infrastructure_options._asdict() | kwargs
        required_fields = ('cache_path', 'db_host_name', 'db_name', 'db_user_name', 'db_password')
        self.__admin_console.scroll_into_view('accessNode')
        self.__drop_down.select_drop_down_values(drop_down_id='accessNode', values=[kwargs['access_node']])
        self.__admin_console.scroll_into_view(DATABASE_FORM['db_type'])
        self.__drop_down.select_drop_down_values(drop_down_id=DATABASE_FORM['db_type'], values=[kwargs['db_type']])
        if kwargs['db_type'] == 'SQLSERVER' and 'db_instance' in kwargs:
            self.__admin_console.fill_form_by_name(DATABASE_FORM['db_instance'], kwargs['db_instance'])
        for name, value in ((DATABASE_FORM[key], kwargs[key]) for key in required_fields):
            self.__admin_console.fill_form_by_name(name, value)
        if 'db_port' in kwargs:
            self.__admin_console.fill_form_by_name(DATABASE_FORM['db_port'], str(kwargs['db_port']))

    @WebAction()
    def __wait_for_login_window_to_close(self, wait_time=120):
        """
        Waits for login window opened by Login to Salesforce to close

        Args:
            wait_time (int): Max time to wait for window to close

        Returns:
            bool: Whether window closed or not
        """
        try:
            WebDriverWait(self.__driver, wait_time).until(EC.number_of_windows_to_be(1))
            return True
        except TimeoutException:
            return False

    @WebAction()
    def __allow_connected_app_with_permissions(self):
        """
                Clicks allow for connected app permissions

                Returns:
                    None:

                Raises:
                    Exception: if fails to grant permissions
                """
        try:
            WebDriverWait(self.__driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='oaapprove']"))).click()
        except (TimeoutException, NoSuchWindowException):
            self.__admin_console.log.info("Permissions already given to the connected app")
        except ...:
            raise Exception("Failed to allow permissions for connected app. Check screenshot for error message")

    @WebAction(hide_args=True)
    def __login_with_salesforce(self, user_name, user_password):
        """
        Performs OAuth login with Salesforce

        Args:
            user_name (str): Salesforce username
            user_password (str): Salesforce password

        Returns:
            None:

        Raises:
            Exception: if login with Salesforce fails
        """
        config_page = self.__driver.current_window_handle
        self.__admin_console.click_button(self.__admin_console.props['label.loginWithSalesforce'])
        if not self.__wait_for_login_window_to_close(wait_time=30):
            self.__driver.switch_to.window(
                self.__driver.window_handles[1] if not self.__driver.window_handles[1] == config_page else
                self.__driver.window_handles[0])
            self.__driver.find_element(By.ID, 'username').send_keys(user_name)
            self.__driver.find_element(By.ID, 'password').send_keys(user_password)
            self.__driver.find_element(By.XPATH, "//input[@type='submit']").click()
            self.__allow_connected_app_with_permissions()
            if not self.__wait_for_login_window_to_close():
                raise Exception("Login with Salesforce error from Salesforce side. Check screenshot for error message")
        self.__driver.switch_to.window(config_page)
        self.__admin_console.wait_for_completion()
        WebDriverWait(self.__driver, 100).until(
            EC.element_to_be_clickable((By.XPATH,
                                        f"//button[@aria-label='Close']"
                                        f"/div[text()='{self.__admin_console.props['label.close']}']"))).click()

    @PageService(hide_args=True)
    def _create_new_oauth_credentials(self, salesforce_credential_name, consumer_id, consumer_secret):
        """
        Clicks on create new connected app credentials on add organization page, fills form and saves

        Args:
            salesforce_credential_name (str): Credential name
            consumer_id (str): Salesforce consumer key
            consumer_secret (str): Salesforce consumer secret

        Returns:
            None:
        """
        self.__admin_console.click_by_xpath("//button[@title='Create new']")
        self.__drop_down.select_drop_down_values(drop_down_id='accountType', values=[ACCOUNT_TYPE])
        self.__drop_down.select_drop_down_values(drop_down_id='vendorType', values=[VENDOR_TYPE])
        self.__admin_console.fill_form_by_name('name', salesforce_credential_name)
        self.__admin_console.fill_form_by_name('consumerKey', consumer_id)
        self.__admin_console.fill_form_by_name('consumerSecret', consumer_secret)
        self.__dialog.click_submit()

    @PageService(hide_args=True)
    def _fill_salesforce_account_details(self, oauth=True, **kwargs):
        """
        Fills Salesforce account details on Add organization page and tests connection with Salesforce

        Args:
            oauth (bool): to use OAuth or not

        Keyword Args:
            sandbox (bool): Whether this is Sandbox organization or not (Default False)
            salesforce_login_url (str): (default 'https://login.salesforce.com')
            salesforce_user_name (str): Username of Salesforce user
            salesforce_user_password (str): Password of Salesforce user
            salesforce_user_token (str): API token of Salesforce user
            consumer_id (str): Consumer key of Salesforce connected app
            consumer_secret (str): Consumer secret of Salesforce connected app
            salesforce_credential_name (str): Name of Credential to use as connected app

        Returns:
            None:

        Raises:
            Exception: if connection to salesforce is unsuccessful

        Examples:
            for login with password authentication (oauth=False):

            options = {
                sandbox (bool): ,

                salesforce_login_url (str): (default 'https://login.salesforce.com'),

                salesforce_user_name (str): Username of Salesforce user,

                salesforce_user_password (str): Password of Salesforce user,

                salesforce_user_token (str): API token of Salesforce user (Optional),

                consumer_id (str): Consumer key of Salesforce connected app,

                consumer_secret (str): Consumer secret of Salesforce connected app
            }

            for login with oauth with existing connected app credentials:

            options = {
                sandbox (bool): ,

                salesforce_user_name (str): Username of Salesforce user,

                salesforce_user_password (str): Password of Salesforce user,

                salesforce_credential_name (str): Name of Credential to use as connected app
            }

            for login with oauth and create new connected app credentials:

            options = {
                sandbox (bool): ,

                salesforce_user_name (str): Username of Salesforce user,

                salesforce_user_password (str): Password of Salesforce user,

                salesforce_credential_name (str): Name of Credential to use as connected app,

                consumer_id (str): Consumer key of Salesforce connected app,

                consumer_secret (str): Consumer secret of Salesforce connected app
            }

            for login with resource pool (already configured with connected app credentials):

            options = {
                sandbox (bool): ,

                salesforce_user_name (str): Username of Salesforce user,

                salesforce_user_password (str): Password of Salesforce user,
            }
        """
        kwargs = _CONFIG_DATA.salesforce_options._asdict() | kwargs
        if kwargs.get('sandbox', False):
            self.__drop_down.select_drop_down_values(
                drop_down_id='environmentType',
                values=[SalesforceEnv.SANDBOX.value]
            )
        if oauth:
            if self.__admin_console.check_if_entity_exists('id', 'credentials'):
                credential_name = kwargs['salesforce_credential_name']
                if credential_name in self.__drop_down.get_values_of_drop_down('credentials'):
                    self.__drop_down.select_drop_down_values(
                        drop_down_id='credentials',
                        values=[credential_name]
                    )
                else:
                    self._create_new_oauth_credentials(
                        salesforce_credential_name=credential_name,
                        consumer_id=kwargs['consumer_id'],
                        consumer_secret=kwargs['consumer_secret']
                    )
            self.__login_with_salesforce(kwargs['salesforce_user_name'], kwargs['salesforce_user_password'])
        else:
            self.__admin_console.select_radio(id='authenticationPassword')
            self.__admin_console.fill_form_by_name('endpoint', kwargs['login_url'])
            self.__admin_console.fill_form_by_name('userName', kwargs['salesforce_user_name'])
            self.__admin_console.fill_form_by_name('password', kwargs['salesforce_user_password'])
            self.__admin_console.fill_form_by_name('token', kwargs['salesforce_user_token'])
            self.__admin_console.fill_form_by_name('consumerId', kwargs['consumer_id'])
            self.__admin_console.fill_form_by_name('consumerSecret', kwargs['consumer_secret'])

    @PageService()
    def check_if_org_exists(self, name):
        """
        Checks if organization with given name already exists in commcell

        Args:
            name (str): name of organization to check for

        Returns:
            bool: True if organization already exists, else False
        """
        self.__page_container.select_tab("Organizations")
        return self.__table.is_entity_present_in_column(self.__admin_console.props['label.name'], name)

    @WebAction()
    def __is_infrastructure_settings_visible(self):
        """
        Checks if Infrastructure settings form is visible

        Returns:
            bool:
        """
        return self.__admin_console.check_if_entity_exists(
            'xpath',
            f"//h3[contains(@class, 'accordion') and "
            f"text()='{self.__admin_console.props['title.infrastructureSettings']}']"
        )

    @PageService()
    def __select_region(self, region):
        """
        Method to select region

        Args:
            region: region that needs to be selected

        Returns:

        """
        if region:
            self.__wizard.select_drop_down_values(id="storageRegion", values=[region], partial_selection=True)

    @PageService()
    def __is_wizard_visible(self):
        """
        Checks if wizard based onboarding is available

        Returns:
            bool
        """
        return self.__admin_console.check_if_entity_exists("xpath",
                                                           "//div[contains(@class,'wizard-title') "
                                                           "and text()='Create Salesforce app']")

    @PageService(hide_args=True)
    def add_org(
            self,
            org_name,
            plan=None,
            oauth=True,
            click_on_add_org=True,
            **kwargs
    ):
        """
        Add a new Salesforce organization to Commcell. If any keyword arguments are not provided, they are read from
        config file. For more details check docstring of _fill_infrastructure_settings() and
        _fill_salesforce_account_details() methods to know what arguments are required for what type of organization.

        Args:
            org_name (str): name of new Salesforce organization
            plan (str): plan to associate the new organization with
            oauth (bool): to use OAuth or not
            click_on_add_org (bool): set to False if already on Add organization page

        Keyword Args:
            access_node (str): access node client or client group name
            cache_path (str): path to download cache directory on access node
            db_type (DbType: (default is DbType.POSTGRESQL)
            db_host_name (str): hostname/ip address of db server
            db_name (str): database name
            db_port (int): (default is 5432 for POSTGRESQL and 1433 for SQLSERVER)
            db_user_name (str):
            db_password (str):
            sandbox (bool):
            salesforce_login_url (str): (default 'https://login.salesforce.com'),
            salesforce_user_name (str): Username of Salesforce user,
            salesforce_user_password (str): Password of Salesforce user,
            salesforce_user_token (str): API token of Salesforce user (Optional),
            salesforce_credential_name (str): Name of Credential to use as connected app,
            consumer_id (str): Consumer key of Salesforce connected app,
            consumer_secret (str): Consumer secret of Salesforce connected app

        Returns:
            None:

        Raises:
            Exception:
                if organization with given name already exists in commcell,
                if either DB/Salesforce test connection fails
        """
        if click_on_add_org:
            if self.check_if_org_exists(org_name):
                raise Exception(f"Salesforce organization with name {org_name} already exists in commcell")
            self.__admin_console.click_button_using_text(self.__admin_console.props['action.addOrganization'])

        if self.__is_wizard_visible():
            self.__select_region(kwargs.get("region"))
            self.__wizard.click_next()
            self.__admin_console.wait_for_completion()
            self.__admin_console.fill_form_by_name('appName', org_name)
            self._fill_salesforce_account_details(oauth, **kwargs)
            self.__wizard.click_button("Create")
            self.__admin_console.wait_for_completion()
            self.__admin_console.click_button(self.__admin_console.props["label.close"])
            return

        self.__admin_console.fill_form_by_name('appName', org_name)
        if plan:
            self.__drop_down.select_drop_down_values(drop_down_id='plan', values=[plan])
        self._fill_salesforce_account_details(oauth, **kwargs)
        if self.__is_infrastructure_settings_visible():
            self._fill_infrastructure_settings(**kwargs)
        if not oauth:
            self.__test_connection(self.__admin_console.props['header.salesforceAcctDetails'])
        self.__admin_console.submit_form()

    @PageService()
    def _click_on_backup(self, org_name):
        """
        Method to click on backup

        Args:
            org_name (str): Name of organization to click on backup for

        Returns:
            None:
        """
        self.__page_container.select_tab("Organizations")
        self.__table.access_action_item(org_name, self.__admin_console.props['label.backup'])

    @PageService()
    def click_on_restore(self, org_name):
        """
        Clicks on run restore for a Salesforce organization and opens Select Restore Type page

        Args:
            org_name (str): Name of organization to click on restore for

        Returns:
            None:
        """
        self.__page_container.select_tab("Organizations")
        self.__table.access_action_item(org_name, self.__admin_console.props['label.globalActions.restore'])

    @PageService()
    def refresh_orgs(self):
        """Method to refresh orgs by clicking on reload"""
        self.__page_container.select_tab("Organizations")
        self.__table.reload_data()
