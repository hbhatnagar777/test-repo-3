# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
File to perform operations on Identity Providers like ADFS, OKTA, Azure for SAML configuration and authentication.

IDPSupport, IdentityProviderSupport, OktaSupport, AzureSupport are the classed defined in this file.

IDPSupport: Base class to support common operations during SAML authentication

IdentityProviderSupport: Class to support operations on ADFS IDP

OktaSupport: Class to support operations on OKTA IDP

AzureSupport: Class to support operations on Azure AD IDP

IdentityProviderSupport:
=======================

    login_to_adfs()     --Logs in to the ADFS site in a new tab

    logout_from_adfs()  --Logs out from ADFS site

    identity_provider_initiated_login()     --Initiates a SAML login from IDP

    service_provider_initiated_login()      --Initiates a SAML login from IDP

    check_single_sign_on_status()           --checks the single sign on status with SAML logged in page

    identity_provider_initiated_logout()    --Initiates a SAML logout from IDP

    service_provider_initiated_logout()     --Initiates a SAML logout from SP

    switch_to_tab()                         --Switches to the given page in browser

    check_if_entity_is_displayed()          --Check if a particular element is displayed or not

    check_logged_in_state_adfs()            --Checks the current logged in state of the AD user

    open_url_in_new_tab()                   --Opens the given url in a new tab and change focus on the new tab opened

    wait_for_completion()                   --  wait for the page to load

    get_user_name()                         --Parses the given string and gets the username from mail id or AD username format

OktaSupport:
===========

    login()                         --  Login to OKTA site
    
    check_if_login_successful()     --  Checks if login to OKTA site is successful or not
    
    open_application()              --  Open the Application in OKTA site
    
    edit_general_settings()         --  Edits the OKTA app details
    
    logout_from_okta()              --  Logout from OKTA site
    
    sp_initiated_login()            --  Service provider initiated login
    
    check_single_sign_on_status()   --  Checks single sign on status
    
    idp_initiated_login()           --  Identity Provider initiated login
    
    saml_logout()                   --  SP init SAML logout
    
    single_logout()                 --  Performs single logout
    
    check_slo_status()              --  Checks single logout status
    
    edit_oidc_app_in_okta()         --  Edit oidc app in OKTA
    
    oidc_login()                    --  Do OpenID user login with OKTA as IDP
    
    edit_saml_config()              --  To initialise or modify okta SAML app config
    
    create_saml_app()               --  Create SAML app in OKTA
    
    assign_users_to_saml_app()      --  Assign users to SAML app in OKTA
    
    modify_idp_saml_metadata()      --  Modify SAML app metadata in OKTA
    
    assign_claim_mapping_attributes() -- Assign claim mapping attributes to SAML app in OKTA
    
    delete_idp_saml_app()           --  Delete SAML app in OKTA

AzureSupport:
============

    login()                             -- Logs in to Azure site

    open_SAML_app()                     -- Opens the SAML app in Azure site

    edit_basic_saml_configuration()     -- Edits the basic SAML configuration in Azure site

    logout_from_azure()                 -- Logs out from Azure site

    sp_initiated_login()                -- Service provider initiated login

    sp_initiated_logout()               -- Service provider initiated logout

    login_as_new_user()                 -- Checks if there is any user account in the Azure login screen and selects login as new user

    idp_initiated_login()               -- Identity Provider initiated login

    create_saml_app()                   -- Create a SAML app in Azure

    _prepare_idp_claim()                -- Prepare IDP claim attributes

    _delete_claim_mapping_policy()      -- Delete existing claim mapping policy from the SAML app in Azure

    assign_users_to_saml_app()          -- Assign users to the SAML app in Azure

    modify_idp_saml_metadata()          -- Update commvault SAML app metadata to IDP SAML app

    assign_claim_mapping_attributes()   -- Assign claim mapping attributes to the SAML app in Azure

    add_signing_certificate()           -- Add signing certificate to the SAML app in Azure

    delete_idp_saml_app()               -- Delete SAML app in Azure

"""

import asyncio
import platform
import time
import json
from typing import Optional, Union
from datetime import datetime
from urllib.parse import urlparse
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select
from Web.AdminConsole.Components.panel import DropDown
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import WebAction, PageService
from AutomationUtils import logger, config
from azure.identity.aio import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.application_templates.application_templates_request_builder import \
    ApplicationTemplatesRequestBuilder
from kiota_abstractions.base_request_configuration import RequestConfiguration
from msgraph.generated.application_templates.item.instantiate.instantiate_post_request_body import \
    InstantiatePostRequestBody
from msgraph.generated.models.service_principal import ServicePrincipal
from msgraph.generated.models.application import Application
from msgraph.generated.models.web_application import WebApplication
from msgraph.generated.models.claims_mapping_policy import ClaimsMappingPolicy
from msgraph.generated.models.reference_create import ReferenceCreate
from uuid import UUID
from msgraph.generated.models.app_role_assignment import AppRoleAssignment
from msgraph.generated.service_principals.item.add_token_signing_certificate.add_token_signing_certificate_post_request_body import \
    AddTokenSigningCertificatePostRequestBody
from okta.client import Client as OktaClient


class IDPSupport:
    """
     this class is used to create the Objects for the classes present in this File
    """

    def __new__(cls, admin_console, options_type):
        options = {
            'ADFS': IdentityProviderSupport,
            'OKTA': OktaSupport,
            'AZURE': AzureSupport
        }
        if cls is not __class__:
            return super().__new__(cls)
        return options[options_type](admin_console, options_type)

    def __init__(self, admin_console, options_type, **kwargs):
        """
        Initializes the IDPSupport class object

        Args:
            admin_console (object)  --  instance of the AdminConsole class
            options_type (str)      --  type of IDP (ADFS, OKTA, AZURE)
            **kwargs (dict)         --  {
                                            idp_saml_app_name (str) : name of the SAML app in IDP
                                        }
        """
        self.options_type = options_type
        self.admin_console = admin_console
        self.driver = admin_console.driver
        self.log = logger.get_log()
        self.config = config.get_config()
        self.idp_saml_app_name = kwargs.get("idp_saml_app_name", '')


    @WebAction()
    def initiate_login_at_sp(self, command_center_url, username, tab_off_approach, sp_initiated_link=None,
                             is_test_login=False):
        """
            Initiate SAML login from SP

            args:
            sp_initiated_link (str)     : SP initiated login URL which redirects directly to IDP even without
                                           entering username
            tab_off_approach (bool)     : True/False
            command_center_url (str)    : Command center URL
            username (str)              : username
            is_test_login (bol)         : True if this is a test login from saml app details page
        """
        try:
            self.log.info("Do a SP initiated SAML login")
            if sp_initiated_link:
                # open the SP initiated link directly in a new tab
                self.log.info(sp_initiated_link)
                self.admin_console.browser.open_url_in_new_tab(sp_initiated_link)

            if is_test_login:
                self.log.info("This is a test saml login")
                # click on test login button
                self.driver.find_element(By.XPATH, "//button//*[contains(text(), 'Test login')]").click()
                # change the window handle to test login pop up window
                for handle in self.driver.window_handles:
                    self.driver.switch_to.window(handle)
                    if "SAMLRequest".lower() in self.driver.current_url.lower():
                        break
                self.log.info("Current window url is : " + self.driver.current_url)
            else:
                # command center login
                self.admin_console.browser.open_url_in_new_tab(command_center_url)
                self.admin_console.wait_for_completion()
                # enter username and click continue to get redirected to IDP
                self.driver.find_element(By.ID, 'username').send_keys(username)
                self.driver.find_element(By.ID, 'continuebtn').click()
                self.admin_console.wait_for_completion()

        except Exception as exp:
            raise CVWebAutomationException("Error occurred while initiating login at SP. {0}".format(str(exp)))

    @WebAction()
    def check_if_login_is_successful(self, hostname):
        """
            Checks if login to commandcenter or webconsole is successful or not

            args:
                hostname (str)  : commandcenter hostname
        """
        status = False
        time.sleep(30)
        self.admin_console.wait_for_completion()
        self.log.info(self.driver.current_url)

        # check of unsuccessful login attempt
        commandcenter_unsuccessful_url = ("https://" + hostname.lower() +
                                          "/identity/samlAcsIdpInitCallback.do?samlAppKey=")
        if self.driver.current_url.startswith(commandcenter_unsuccessful_url):
            self.log.info("Error occurred during SAML login")
            error_seen = self.driver.find_element(By.XPATH, "//div[@class='detailsDiv']/p").text
            self.log.info("FAILURE REASON::" + error_seen)
            status = False

        # check if login to command center
        elif self.driver.current_url.startswith("https://" + hostname.lower() + "/commandcenter"):
            self.log.info("Logged in to command center successfully")
            status = True

        # check if login to test login page
        elif "samlTestCompleted=true".lower() in self.driver.current_url.lower():
            status = True
        return status

    @WebAction()
    def initiated_logout_from_sp(self, hostname):
        """
        Does SP initiated SAML logout

        args:
            hostname (str)      : commandcenter hostname
        """
        status = False
        self.log.info(self.driver.current_url)
        self.log.info("Do a SP initiated SAML logout")
        commandcenter_unsuccessful_url = ("https://" + hostname.lower() +
                                          "/identity/samlAcsIdpInitCallback.do?samlAppKey=")

        # Logout from command center
        if self.driver.current_url.startswith("https://" + hostname.lower() + "/commandcenter/"):
            self.admin_console.logout()
            status = True

        # Checks for unsuccessful logins
        elif self.driver.current_url.startswith(commandcenter_unsuccessful_url):
            raise CVWebAutomationException("Login Failed. No option found to logout")

        else:
            raise CVWebAutomationException("No option found to logout")

        return status

    @staticmethod
    def _run_async(coroutine):
        """
        Run the given asynchronous coroutine with an event loop.
        """
        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy())

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coroutine)
        finally:
            loop.close()


class IdentityProviderSupport(IDPSupport):
    """
     this class provides the support for all the operations done on ADFS IDP
    """

    def __init__(self, admin_console, options_type):
        super().__init__(admin_console, options_type)
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self._adfs_idp_url = "https://%s/adfs/ls/idpinitiatedsignon"

    @WebAction()
    def login_to_adfs(self, saml_user_name, saml_password, adfs_app_name=None):
        """
        Logs in to the ADFS site in a new tab

        Args:

            saml_user_name  (str)-- username to log in

            saml_password   (str)-- password of the user

            adfs_app_name   (str)-- the  AD FS app name to sign in

       Returns:
            True    --  If the login is successful

            False   --  If the login is not successful

            loaded_url  (str)   -- URL loaded in the browser

        """
        try:
            # checks if the current page is ADFS login page
            if "/adfs/ls/?SAMLRequest=" in self.__driver.current_url:
                if adfs_app_name:
                    self.__driver.find_element(By.ID, "idp_OtherRpRadioButton").click()
                    select = Select(self.__driver.find_element(By.ID, 'idp_RelyingPartyDropDownList'))
                    select.select_by_visible_text(adfs_app_name)
                    self.__driver.find_element(By.NAME, 'SignInSubmit').click()
                    self.__admin_console.wait_for_completion()
                self.log.info("Page loaded %s", self.__driver.current_url)
                self.__driver.find_element(By.ID, 'userNameInput').clear()
                self.__driver.find_element(By.ID, 'userNameInput').send_keys(saml_user_name)
                self.__driver.find_element(By.ID, 'passwordInput').send_keys(saml_password)
                self.__driver.find_element(By.ID, 'submitButton').click()
                self.__admin_console.wait_for_completion()

            if self.__admin_console.check_if_entity_exists('id', 'errorText'):
                error_msg = self.__driver.find_element(By.ID, 'errorText').text
                raise CVWebAutomationException("Error::" + error_msg)

            loaded_url = self.__driver.current_url
            self.log.info("Page loaded %s", loaded_url)
            return True, loaded_url

        except Exception as exp:
            raise CVWebAutomationException("Error occurred during login at ADFS site. {0}".format(str(exp)))

    @WebAction()
    def logout_from_adfs(self, ad_name, local_sign_out=False):
        """
        Logs out from the ADFS site

        Args:
            ad_name         (str)-- AD machine name IP that resolved

            local_sign_out  (bool)--True when we need to sign out only from AD site

        Returns:
            True    --  If the logout is successful

            False   --  If the logout is not successful
        """
        try:
            # checks if the current page is ADFS init page otherwise opens the ADFS init page
            idp_url = self._adfs_idp_url % ad_name
            if self.__driver.current_url != idp_url:
                self.__admin_console.browser.open_url_in_new_tab(idp_url)
                self.__admin_console.wait_for_completion()

            # checks if the user is logged in to the site
            if self.check_logged_in_state_adfs():
                # to select logout local session
                if local_sign_out:
                    self.log.info("Logging out from this site")
                    self.__driver.find_element(By.ID, "idp_LocalSignOutRadioButton").click()
                # to select logout from all the sites
                else:
                    self.log.info("Logging out from all the sites")
                    self.__driver.find_element(By.ID, "idp_SingleSignOutRadioButton").click()
                # click on sign out button
                self.__driver.find_element(By.ID, 'idp_SignOutButton').click()
                self.__admin_console.wait_for_completion()
                if self.check_logged_in_state_adfs():
                    return False
            else:
                self.log.info("No user is logged in to the site")
            return True

        except NoSuchElementException as exc:
            raise CVWebAutomationException("Error occurred during logout at ADFS site. {0}".format(str(exc)))

    @WebAction()
    def check_logged_in_state_adfs(self):
        """
        checks the current logged in state of the AD user

        Returns:
            True    --  If the user is logged in

            False   --  If the user is not logged in

        """
        sign_on_state = self.__driver.find_element(By.XPATH, "//div"
                                                             "[@id='idp_SignInThisSiteStatusLabel']"
                                                             "/span").text
        return sign_on_state == "You are signed in."

    @WebAction()
    def identity_provider_initiated_login(self, ad_name, hostname, adfs_app_name, user,
                                          password, verify_sso):
        """
        Initiates a SAML login from IDP

        Args:
            ad_name         (str)-- AD machine name/ IP that resolved

            hostname        (str)-- commandcenter hostname

            adfs_app_name   (str)-- ADFS app name

            user            (str)-- AD username

            password        (str)-- AD user password

            verify_sso      (bool)--verifies if SSO is successful

        Returns:
            True    --  If the login is successful

            False   --  If the login is not successful

        """
        self.log.info("Do a IDP initiated SAML login and verify Single sign on for")
        # opens the ADFS init page
        idp_url = self._adfs_idp_url % ad_name
        self.__admin_console.browser.open_url_in_new_tab(idp_url)
        self.__admin_console.wait_for_completion()
        # logout from existing session if any
        status = self.logout_from_adfs(ad_name, local_sign_out=False)
        self.__admin_console.wait_for_completion()
        if status:
            # login to ADFS site
            self.login_to_adfs(user, password, adfs_app_name)
            status = self.check_if_login_is_successful(hostname)
            if status:
                # verify single sign on status
                if verify_sso:
                    status = self.check_single_sign_on_status(ad_name, user, hostname)

        return status

    @WebAction()
    def service_provider_initiated_login(self, ad_name, hostname, command_center_url, user, password,
                                         tab_off_approach, verify_sso, sp_initiated_link=None, is_test_login=False):
        """
        Initiates a SAML login from SP
        Args:
            ad_name             (str)-- AD machine name /IP that resolved

            hostname            (str)-- command center hostname

            command_center_url      (str)-- command center URL of the client

            user                (str)-- AD username

            password            (str)-- AD user password

            tab_off_approach    (bool)--True , if tab will be pressed during saml login

            verify_sso          (bool)-- verifies if SSO is successful

            sp_initiated_link   (str)--link to initiate SAML login.Either supply tab off or SP link

            is_test_login       (bool) -- True if this is a test login from saml app details page

        Returns:
            True    --  If the login is successful

            False   --  If the login is not successful
        """
        self.log.info("Do a SP initiated SAML login")
        # save the main window handle for test login
        main_window_handle = self.driver.current_window_handle
        # initiate login at SP to get redirected to IDP
        self.initiate_login_at_sp(command_center_url, user, tab_off_approach, sp_initiated_link, is_test_login)
        self.admin_console.wait_for_completion()
        # login to ADFS site
        self.login_to_adfs(user, password)
        status = self.check_if_login_is_successful(hostname)
        if status:
            # verify single sign on status
            if verify_sso:
                status = self.check_single_sign_on_status(ad_name, user, hostname)

        if is_test_login:
            # close the test login popup window
            for handle in self.driver.window_handles:
                self.driver.switch_to.window(handle)
                if "samlTestCompleted=true".lower() in self.driver.current_url.lower():
                    self.driver.close()
                    break
            # switch back to main window
            self.driver.switch_to.window(main_window_handle)
            self.log.info("Current window url is : " + self.driver.current_url)
        return status

    @WebAction()
    def check_single_sign_on_status(self, ad_name, command_center_url):
        """
        checks the single sign on status with SAML logged in page
        Args:
            ad_name        (str)-- name of the AD machine

            command_center_url(str)-- command center URL of the client

        Returns:
            True    --  If the login is successful

            False   --  If the login is not successful

        """
        idp_url = self._adfs_idp_url % ad_name
        # checks for command center login
        status = self.check_if_login_is_successful(command_center_url)

        self.log.info("Loaded page is command center applications page, so loading IDP in new tab")
        self.__admin_console.browser.open_url_in_new_tab(idp_url)
        self.__admin_console.wait_for_completion()

        if status and self.check_logged_in_state_adfs():
            self.log.info("SSO successful at IDP")
            return True
        self.log.info("SSO failed at IDP")
        return False

    @WebAction()
    def identity_provider_initiated_logout(self, ad_name, command_center_url, verify_single_logout):
        """
        Initiates a SAML logout from IDP

            Args:

                ad_name             (str)-- AD machine name/ IP that resolved

                command_center_url     (str)-- commandcenter URL of the client

                verify_single_logout(bool): verifies if single logout is successful

            Returns:

            True    --  If the logout is successful

            False   --  If the logout is not successful

        """
        self.log.info("Do a SP initiated SAML logout and verify Single logout")
        status = False
        if self.logout_from_adfs(ad_name, local_sign_out=False):
            status = True
            if verify_single_logout:
                self.__admin_console.browser.open_url_in_new_tab(command_center_url)
                self.__admin_console.wait_for_completion()
                if self.__driver.current_url.startswith("https://" + command_center_url.lower() + "/identity"):
                    self.log.info("Login screen loaded after log out at IDP")
                else:
                    self.log.info("Logout unsuccessful at SP")
                    status = False
        return status

    @WebAction()
    def service_provider_initiated_logout(self, ad_name, hostname, verify_single_logout):
        """
        Initiates a SAML logout from SP and validates single logout

            Args:
                ad_name             (str)-- AD machine name/ IP that resolved

                hostname            (str)-- commandcenter hostname

                verify_single_logout(bool)-- verifies if single logout is successful

            Returns:
                True    --  If the login is successful

                False   --  If the login is not successful

        """
        self.log.info("Do a SP initiated SAML logout and verify Single logout")
        idp_url = self._adfs_idp_url % ad_name
        status = self.initiated_logout_from_sp(hostname)
        if status:
            if verify_single_logout:
                self.__admin_console.browser.open_url_in_new_tab(idp_url)

                if not self.check_logged_in_state_adfs():
                    self.log.info("Logged out at IDP too")
                else:
                    status = False
                    self.log.info("Logging out at IDP failed")
        else:
            raise CVWebAutomationException("No option to logout from SP")
        return status

    def get_user_name(self, given_string):
        """
        Parses the given string and gets the username from mail id or AD username format
        Args:
            given_string:   (str)   username in mail address or domain\\username format

        Returns:  (str)    username
        """

        if '\\' in given_string:
            return given_string.split('\\')[1]
        return given_string.split('@')[0]


class OktaSupport(IDPSupport):
    """
     this class provides the support for all the operations done on OKTA IDP
    """

    def __init__(self, admin_console, options_type):
        super().__init__(admin_console, options_type)
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__drop_down = DropDown(admin_console)
        self.idp_saml_config = None
        self._okta_client = OktaClient({
            'orgUrl': self.config.Okta.OktaURL,
            'token': self.config.Okta.Token
        })
        self._okta_saml_app_id = None
    @WebAction()
    def login(self, username, pwd):
        """
        Login to OKTA site

        Args:

            username  (str)-- username to log in

            pwd   (str)-- password of the user

       Returns:

            loaded_url  (str)   -- URL loaded in the browser

        """
        self.admin_console.wait_for_element_based_on_xpath('//input[@id="okta-signin-username"]', 100)
        try:
            self.__driver.find_element(By.XPATH, '//input[@id="okta-signin-username"]').clear()
            self.__driver.find_element(By.XPATH, '//input[@id="okta-signin-username"]').send_keys(username)
            self.__driver.find_element(By.XPATH, '//input[@id="okta-signin-password"]').send_keys(pwd)
            self.__driver.find_element(By.ID, 'okta-signin-submit').click()
            self.__admin_console.wait_for_completion()

        except NoSuchElementException as exp:
            raise CVWebAutomationException("Error occurred during login at OKTA site. {0}".format(str(exp)))

    @WebAction()
    def check_if_login_successful(self):
        """
        Checks if login to OKTA site is successful or not
        """
        try:
            self.driver.find_element(By.XPATH, '//*[@data-se="user-menu"]/a').click()
            if self.__admin_console.check_if_entity_exists('xpath', '//*[@data-se="logout-link"]'):
                return True
        except NoSuchElementException as exp:
            raise CVWebAutomationException("Login Failed. {0}".format(str(exp)))

    @WebAction()
    def open_application(self, app_name):
        """Open the Application in OKTA site
        Args:
            app_name    (str)   : Name of the application to edit
        """
        time.sleep(10)
        url = self.__driver.current_url
        parsed_url = urlparse(url)
        hostname = parsed_url.netloc
        okta_application_url = "https://" + hostname + "/admin/apps/active"
        self.__admin_console.browser.open_url_in_new_tab(okta_application_url)
        self.__admin_console.wait_for_completion()
        time.sleep(5)
        self.__driver.find_element(By.XPATH, '//*[@placeholder="Search"]').send_keys(app_name)
        self.__admin_console.wait_for_completion()
        time.sleep(5)
        self.__driver.find_element(By.XPATH, '//a[@class="app-instance-name"][@title="' + app_name + '"]').click()
        self.__admin_console.wait_for_completion()
        time.sleep(5)

    @WebAction()
    def edit_general_settings(self, app_name, sso_url, sp_entity_id, name_id_format, attributes, group_attribute,
                              slo=False, single_logout_url=None, sp_issuer=None, certificate=None):
        """
        Edits the OKTA app details

        app_name (str)          : Name of the app whose details are to be edited
        sso_url (str)           : Single sign on url
        sp_entity_id (str)      : Service Provider's entity ID
        name_id_format (str)    : Name ID value
        attributes (dict)       : Attribute Mappings
        group_attribute(dict)   : Group Attribute Mappings
        """
        self.open_application(app_name)
        # editing okta app settings
        self.__driver.find_element(By.XPATH, '//a[text()="General"]').click()
        self.__admin_console.wait_for_completion()
        self.__driver.find_element(By.XPATH, '//*[@id="edit-saml-app"]').click()
        self.__admin_console.wait_for_completion()
        time.sleep(5)
        self.__driver.find_element(By.XPATH, '//*[@value="Next"]').click()
        self.__admin_console.wait_for_completion()
        # updating the SSO URL
        self.__driver.find_element(By.XPATH, '//*[@name="postBackURL"]').clear()
        time.sleep(2)
        self.__driver.find_element(By.XPATH, '//*[@name="postBackURL"]').send_keys(sso_url)
        self.__admin_console.wait_for_completion()
        # updating the SP entity ID
        self.__driver.find_element(By.XPATH, '//*[@name="audienceRestriction"]').clear()
        time.sleep(2)
        self.__driver.find_element(By.XPATH, '//*[@name="audienceRestriction"]').send_keys(sp_entity_id)
        self.__admin_console.wait_for_completion()
        if name_id_format:
            # selecting the name ID format
            self.__drop_down.select_drop_down_values(0, name_id_format)

        if attributes:
            # adding required number of fields
            add_another = self.__driver.find_element(By.XPATH, "//input[@value='Add Another']")
            for i in range(len(attributes)):
                add_another.click()
            # finding the attribute div
            attr_div = self.__driver.find_element(By.XPATH, "//a[@class='saml-attributes-learn-more-link']/../following"
                                                            "-sibling::div[1]")
            names = attr_div.find_elements(By.NAME, 'name')
            values = attr_div.find_elements(By.NAME, 'values')
            # clearing the existing values
            for idx in range(len(names)):
                names[idx].clear()
                values[idx].clear()
            cnt = 0
            # updating the attribute mappings
            for key, value in attributes.items():
                names[cnt].clear()
                values[cnt].clear()
                names[cnt].send_keys(key)
                values[cnt].send_keys(value)
                cnt = cnt + 1
            self.__admin_console.wait_for_completion()

        # clearing group attribute mapping like user groups
        grp_statment = ("//h2[text()='Group Attribute Statements (optional)']/following-"
                        "sibling::div[1]//input[@name='name']")
        self.__driver.find_element(By.XPATH, grp_statment).clear()
        self.__driver.find_element(By.XPATH, '//*[@name="filterValue"]').clear()

        if group_attribute:
            saml_attr, user_attr = None, None
            for x in group_attribute:
                user_attr = group_attribute[x]
                saml_attr = x

            self.__driver.find_element(By.XPATH, grp_statment).send_keys(saml_attr)
            self.__driver.find_element(By.XPATH, '//*[@name="filterValue"]').send_keys(user_attr)
            self.__admin_console.wait_for_completion()

        if slo:
            self.__driver.find_element(By.XPATH, '//*[@class="advanced-link float-r"]').click()
            time.sleep(2)
            # uploading certificate
            cert_upload_xpath = ("//div[@data-se='o-form-fieldset' and contains(@class, 'o-form-fieldset') "
                                 "and not(contains(@class, 'encryptionCertificateUploader'))]//input[@type='file']")
            self.__driver.find_element(By.XPATH, cert_upload_xpath).send_keys(certificate)
            time.sleep(3)
            # updating single logout URL and SP issuer
            self.__driver.find_element(By.NAME, 'logoutUrl').clear()
            self.__driver.find_element(By.NAME, 'logoutUrl').send_keys(single_logout_url)
            time.sleep(2)
            self.__driver.find_element(By.NAME, 'samlSpIssuer').clear()
            self.__driver.find_element(By.NAME, 'samlSpIssuer').send_keys(sp_issuer)
            time.sleep(2)

        self.__driver.find_element(By.XPATH, '//*[@value="Next"]').click()
        self.__admin_console.wait_for_completion()
        self.__driver.find_element(By.XPATH, '//*[@value="Finish"]').click()
        self.__admin_console.wait_for_completion()

    @WebAction()
    def logout_from_okta(self, admin_user=True):
        """
        Logout from OKTA site
        Args :
            admin_user              (bool)      True if logging out of admin user session, False otherwise
        """
        try:
            time.sleep(2)
            if admin_user:
                self.driver.find_element(By.XPATH, '//*[@data-se="admin-header--user-menu"]').click()
                time.sleep(2)
                self.driver.find_element(By.XPATH, '//*[text()="Sign out"]').click()
                time.sleep(3)

            else:
                self.driver.find_element(By.XPATH, "//*[@data-se='dropdown-menu-button-header']").click()
                time.sleep(2)
                self.driver.find_element(By.XPATH, '//a[text()="Sign out"][@class="topbar--item"]').click()
                time.sleep(2)

        except Exception as exp:
            raise CVWebAutomationException("No option found to logout. {0}".format(str(exp)))

    @WebAction()
    def sp_initiated_login(self, command_center_url, hostname, okta_url, username, pwd, tab_off_approach, verify_sso,
                           sp_initiated_link=None):
        """
        Service provider initiated login

        command_center_url (str)    : command center URL
        hostname (str)              : Commcell hostname
        okta_url (str)              : OKTA web URL
        username (str)              : name of the user to login
        pwd (str)                   : password
        tab_off_approach (bool)     : redirects to other site on click of an element
        verify_sso (bool)           : verify if SSO is achieved
        sp_initiated_link (str)     : link to initiate SAML login
        """
        # initiate login at SP to get redirected to IDP
        self.initiate_login_at_sp(command_center_url, username, tab_off_approach, sp_initiated_link)
        # login to IDP site
        self.login(username, pwd)
        status = self.check_if_login_is_successful(hostname)
        if status:
            # verify single sign on status
            if verify_sso:
                status = self.check_single_sign_on_status(okta_url)

        return status

    @WebAction()
    def check_single_sign_on_status(self, okta_url):
        """
        checks single sign on status

        okta_url (str)   : OKTA web URL

        returns : True/False
        """
        self.__admin_console.browser.open_url_in_new_tab(okta_url)
        if self.__driver.find_element(By.ID, 'logout-link'):
            return True

    def idp_initiated_login(self, hostname, okta_url, app_name, username, pwd):
        """
        Identity Provider initiated login

        hostname (str)      : commandcenter hostname
        okta_url (str)      : OKTA web URL
        app_name (str)      : SAML app name in OKTA
        username (str)      : Username to login
        pwd (str)           : Password
        verify_sso (bool)   : True/False

        return: current URL
        """
        self.log.info("Do IDP initiated login")
        # open the OKTA site
        self.__admin_console.browser.open_url_in_new_tab(okta_url)
        self.__admin_console.wait_for_completion()
        # login to okta
        self.login(username, pwd)
        self.__admin_console.wait_for_completion()
        self.__driver.find_element(By.NAME, 'dashboard-search-input').send_keys(app_name)
        self.__driver.find_element(By.XPATH, '//a[@aria-label="launch app {0}"]'.format(app_name)).click()
        self.__admin_console.wait_for_completion()
        self.admin_console.browser.switch_to_latest_tab()
        time.sleep(5)
        self.log.info(self.driver.current_url)
        status = self.check_if_login_is_successful(hostname)
        return status

    @WebAction()
    def saml_logout(self, hostname):
        """
        SP init SAML logout

        loaded_url (str)    : current web URL
        hostname (str)      : commandcenter hostname
        """
        self.log.info("Do a SAML logout")
        status = self.initiated_logout_from_sp(hostname)
        return status

    @WebAction()
    def single_logout(self):
        """
        performs single logout
        """
        try:
            self.__driver.find_element(By.XPATH, "//div[@data-se='user-menu']/a").click()
            time.sleep(3)
            self.__driver.find_element(By.XPATH, "//a[@data-se='logout-link']").click()
        except Exception as exp:
            raise CVWebAutomationException('Failed to logout at the OKTA site. {0}'.format(str(exp)))

    @WebAction()
    def check_slo_status(self, okta_url):
        """
        checks single logout status
        """
        self.log.info(self.__driver.current_url)
        self.log.info(okta_url)
        if self.__driver.current_url == okta_url:
            return True
        else:
            return False

    @WebAction()
    def edit_oidc_app_in_okta(self, app_name, login_uri):
        """
        Edit oidc app in OKTA
        Args:
            app_name (str)   : OpenID appname in OKTA
            login_uri   (str)
        """
        try:
            self.open_application(app_name)
            client_id_elem = self.driver.find_element(By.XPATH, '//*[@data-se="o-form-input-client_id"]/input')
            secret_elem = self.driver.find_element(By.XPATH, '//*[@data-se="o-form-input-client_secret"]/input')
            domain_elem = self.driver.find_element(By.XPATH, '//*[@data-se="o-form-input-"]/input')

            client_id = client_id_elem.get_attribute('value')
            client_secret = secret_elem.get_attribute('value')
            okta_domain = domain_elem.get_attribute('value')

            self.driver.find_element(By.XPATH, '//*[@aria-label="Edit General Settings"]').click()
            self.driver.find_element(By.XPATH, '//*[@name="uri"]').clear()
            self.driver.find_element(By.XPATH, '//*[@name="uri"]').send_keys(login_uri)
            self.driver.find_element(By.XPATH, '//*[@data-type="save"]').click()
            time.sleep(3)

            return client_id, client_secret, okta_domain

        except Exception as exp:
            raise CVWebAutomationException("Failed to edit OpenID app. {0}".format(str(exp)))

    @PageService()
    def oidc_login(self, command_center_url, username, password):
        """ Do OpenID user login with OKTA as IDP"""
        self.initiate_login_at_sp(command_center_url, username, tab_off_approach=True)
        time.sleep(3)
        hostname = command_center_url.split('//')[-1].split('/')[0].split(':')[0].lower()
        self.login(username, password)
        self.admin_console.wait_for_completion()
        status = self.check_if_login_is_successful(hostname)
        return status

    def edit_saml_config(self, **kwargs: dict):
        """ To initialise or modify okta SAML app config.

        Args:
            kwargs (dict)   :
                - cv_saml_app_metadata (dict) : Commvault SAML app metadata
                - idp_claim_attributes (dict) : IDP claim attribute mappings
                - idp_group_claim_attributes (str) : IDP group claim attributes

        Example:
            cv_saml_app_metadata = {"entityId": "https://commvault-hostname:443/identity",
                                    "singleSignOnUrl": "https://..:443/identity/samlAcsIdpInitCallback.do?samlAppKey=..",
                                    "singleLogoutUrl": "https://..:443/identity/server/SAMLSingleLogout?samlAppKey=.."}
            idp_claim_attributes= {"fullname": "user.firstName",
                                   "email": "user.email",
                                   "username": "user.login",
                                   "company": "company_name"}
            idp_group_claim_attributes = "groups"
        """
        if self.idp_saml_config is None:
            self.idp_saml_config = {
                "label": f"cv_saml_{datetime.today().date()}",
                "accessibility": {
                    "selfService": False,
                    "errorRedirectUrl": None,
                    "loginRedirectUrl": None
                },
                "visibility": {
                    "autoSubmitToolbar": False,
                    "hide": {
                        "iOS": False,
                        "web": False
                    }
                },
                "features": [],
                "signOnMode": "SAML_2_0",
                "credentials": {
                    "userNameTemplate": {
                        "template": "${fn:substringBefore(source.login, \"@\")}",
                        "type": "BUILT_IN"
                    },
                    "signing": {}
                },
                "settings": {
                    "app": {},
                    "notifications": {
                        "vpn": {
                            "network": {
                                "connection": "DISABLED"
                            },
                            "message": None,
                            "helpUrl": None
                        }
                    },
                    "signOn": {
                        "defaultRelayState": "",
                        "idpIssuer": "http://www.okta.com/${org.externalKey}",
                        "subjectNameIdTemplate": "${user.userName}",
                        "subjectNameIdFormat": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
                        "responseSigned": True,
                        "assertionSigned": True,
                        "signatureAlgorithm": "RSA_SHA256",
                        "digestAlgorithm": "SHA256",
                        "honorForceAuthn": True,
                        "authnContextClassRef": "urn:oasis:names:tc:SAML:2.0:ac:classes:PasswordProtectedTransport",
                        "spIssuer": None,
                        "requestCompressed": False,
                        "attributeStatements": [],
                    }
                }
            }

            # update the SAML app display name
            if self.idp_saml_app_name:
                self.idp_saml_config['label'] = self.idp_saml_app_name
            # update the SAML app metadata config
            if kwargs.get('cv_saml_app_metadata', False):
                self.idp_saml_config['settings']['signOn']['ssoAcsUrl'] = kwargs['cv_saml_app_metadata'][
                    'singleSignOnUrl']
                self.idp_saml_config['settings']['signOn']['audience'] = kwargs['cv_saml_app_metadata']['entityId']
                self.idp_saml_config['settings']['signOn']['recipient'] = kwargs['cv_saml_app_metadata'][
                    'singleSignOnUrl']
                self.idp_saml_config['settings']['signOn']['destination'] = kwargs['cv_saml_app_metadata'][
                    'singleSignOnUrl']
                slo = {
                    "enabled": True,
                    "issuer": kwargs['cv_saml_app_metadata']['entityId'],
                    "logoutUrl": kwargs['cv_saml_app_metadata']['singleLogoutUrl']
                }
                sp_certificate = {
                    'x5c': [kwargs['cv_saml_app_metadata']['sp_certificate']]
                }
                self.idp_saml_config['settings']['signOn']['spCertificate'] = sp_certificate
                self.idp_saml_config['settings']['signOn']['slo'] = slo

            # update the IDP claim attribute mappings
            if kwargs.get('idp_claim_attributes', False):
                schema = []
                for claim, value in kwargs.get('idp_claim_attributes').items():
                    schema.append({'filter_type': None, 'filter_value': None, 'name': claim,
                                   'namespace': 'urn:oasis:names:tc:SAML:2.0:attrname-format:unspecified',
                                   'type': 'EXPRESSION', 'values': [value]})
                self.idp_saml_config['settings']['signOn']['attributeStatements'] = schema
            if kwargs.get('idp_group_claim_attributes', False):
                self.idp_saml_config['settings']['signOn']['attributeStatements'].append(
                    {'filter_type': 'REGEX', 'filter_value': '.*', 'name': kwargs.get('idp_group_claim_attributes'),
                     'namespace': 'urn:oasis:names:tc:SAML:2.0:attrname-format:uri',
                     'type': 'GROUP', 'values': []})

    def create_saml_app(self, cv_saml_app_metadata: dict, idp_claim_attributes: dict, idp_group_claim_attributes: str):
        """ Create SAML app in OKTA.

        Args:
            cv_saml_app_metadata (dict) : commvault SAML app metadata
            idp_claim_attributes (dict) : IDP claim attribute mappings
            idp_group_claim_attributes (str) : IDP group claim attribute

        Example:
            cv_saml_app_metadata = {"entityId": "https://commvault-hostname:443/identity",
                                    "singleSignOnUrl": "https://..:443/identity/samlAcsIdpInitCallback.do?samlAppKey=..",
                                    "singleLogoutUrl": "https://..:443/identity/server/SAMLSingleLogout?samlAppKey=.."}
            idp_claim_attributes= {"fullname": "user.firstName",
                                   "email": "user.email",
                                   "username": "user.login",
                                   "company": "company_name"}
            idp_group_claim_attributes = "groups"

        raises:
            Exception: if failed to create SAML app in okta
        """
        self.edit_saml_config(cv_saml_app_metadata=cv_saml_app_metadata, idp_claim_attributes=idp_claim_attributes,
                              idp_group_claim_attributes=idp_group_claim_attributes)
        _, response, _ = self._run_async(self._okta_client.create_application(self.idp_saml_config))
        if response.get_status() != 200:
            raise Exception(f"Failed to create SAML app in okta. {response.get_body()}")
        self._okta_saml_app_id = response.get_body()['id']
        self.log.info("SAML app created successfully in okta, with app id: %s", self._okta_saml_app_id)

    def assign_users_to_saml_app(self, user_ids: list[str]):
        """ Assign users to SAML app in OKTA.

        Args:
            user_ids (list) : List of user id's

        Example:
            user_ids = ['00u1h4v1v7j5z4j8b5d6', '00u1h4v1v7j5z4j8b5d7']

        raises:
            Exception: if failed to assign user to SAML app in okta
        """
        for user_id in user_ids:
            _, response, _ = self._run_async(
                self._okta_client.assign_user_to_application(self._okta_saml_app_id,
                                                             {'id': user_id, 'scope': 'USER'}))
            if response.get_status() != 200:
                raise Exception(f"Failed to assign user to SAML app in okta. {response.get_body()}")
        self.log.info("Users assigned successfully to SAML app in okta.")

    def modify_idp_saml_metadata(self, cv_saml_app_metadata: dict[str, str]):
        """ Modify SAML app metadata in OKTA.

        Args:
            cv_saml_app_metadata (dict) : commvault SAML app metadata

        Example:
            cv_saml_app_metadata = {"entityId": "https://commvault-hostname:443/identity",
                                    "singleSignOnUrl": "https://..:443/identity/samlAcsIdpInitCallback.do?samlAppKey=..",
                                    "singleLogoutUrl": "https://..:443/identity/server/SAMLSingleLogout?samlAppKey=.."}

        raises:
            Exception: if failed to modify SAML app metadata in okta
        """
        self.edit_saml_config(cv_saml_app_metadata=cv_saml_app_metadata)
        _, response, _ = self._run_async(
            self._okta_client.update_application(self._okta_saml_app_id, self.idp_saml_config))
        if response.get_status() != 200:
            raise Exception(f"Failed to modify SAML app metadata in okta. {response.get_body()}")
        self.log.info("SAML app metadata modified successfully in okta.")

    def assign_claim_mapping_attributes(self, idp_claim_attributes: dict[str, str] = None,
                                        idp_group_claim_attributes: str = None):
        """ Assign claim mapping attributes to SAML app in OKTA.

        Args:
            idp_claim_attributes (dict) : IDP claim attributes
            idp_group_claim_attributes (str) : IDP group claim attribute value

        Example:
            idp_claim_attributes= {"fullname": "user.firstName",
                                   "email": "user.email",
                                   "username": "user.login",
                                   "company": "company_name"}
            idp_group_claim_attributes = "groups"
        """
        self.edit_saml_config(idp_claim_attributes=idp_claim_attributes,
                              idp_group_claim_attributes=idp_group_claim_attributes)
        _, response, _ = self._run_async(
            self._okta_client.update_application(self._okta_saml_app_id, self.idp_saml_config))
        if response.get_status() != 200:
            raise Exception(f"Failed to create SAML app in okta. {response.get_body()}")
        self.log.info("Claim mapping attributes assigned successfully to SAML app in okta.")

    def delete_idp_saml_app(self):
        """ Delete SAML app in OKTA."""
        response, _ = self._run_async(self._okta_client.deactivate_application(self._okta_saml_app_id))
        if response.get_status() != 204:
            self.log.info(f"Failed to deactivate SAML app in okta. {response.get_body()}")
        response, _ = self._run_async(self._okta_client.delete_application(self._okta_saml_app_id))
        if response.get_status() != 204:
            self.log.info(f"Failed to delete SAML app in okta. {response.get_body()}")
        self.log.info("SAML app deleted successfully in okta.")


class AzureSupport(IDPSupport):
    """
         this class provides the support for all the operations done on Azure IDP
    """

    def __init__(self, admin_console, options_type):
        super().__init__(admin_console, options_type)
        self.azure_url = "https://portal.azure.com/"
        self._credentials = ClientSecretCredential(
            self.config.Azure.Tenant,
            self.config.Azure.App.ApplicationID,
            self.config.Azure.App.ApplicationSecret,
        )
        self._scopes = ['https://graph.microsoft.com/.default']
        self._graph_client = GraphServiceClient(credentials=self._credentials, scopes=self._scopes)
        self._application_service_principal = None

    @WebAction()
    def login(self, username, pwd):
        """
        Login to Azure site

        Args:

            username  (str)-- username to log in

            pwd   (str)-- password of the user

       Returns:

            loaded_url  (str)   -- URL loaded in the browser

        """
        try:
            try:
                self.driver.find_element(By.XPATH, '//*[@name="loginfmt"]').clear()
                self.driver.find_element(By.XPATH, '//*[@name="loginfmt"]').send_keys(username)
                self.driver.find_element(By.XPATH, '//*[@type="submit"]').click()
            except NoSuchElementException:
                self.log.info("Username is auto-populated during SP initiated SAML login")
            time.sleep(2)
            self.driver.find_element(By.XPATH, '//*[@name="passwd"]').clear()
            self.driver.find_element(By.XPATH, '//*[@name="passwd"]').send_keys(pwd)
            self.driver.find_element(By.XPATH, '//*[@type="submit"]').click()
            time.sleep(2)
            # stay signed in popup in azure portal.
            if self.driver.find_elements(By.ID, 'idBtn_Back'):
                self.driver.find_element(By.ID, 'idBtn_Back').click()
            self.admin_console.wait_for_completion()
            return True
        except Exception as exp:
            raise CVWebAutomationException("Login at Azure site Failed. {0}".format(str(exp)))

    @WebAction()
    def open_SAML_app(self, app_name):
        """
            Opens the SAML app in Azure site
            args:
            app_name (str)      : SAML App name in Azure site
        """
        self.driver.find_element(By.XPATH, '//input[@type="text"]').send_keys("Enterprise applications")
        time.sleep(5)
        self.driver.find_element(By.XPATH, '//*[@id="Microsoft_AAD_IAM_Application"]/a').click()
        time.sleep(8)
        self.driver.find_element(By.XPATH, '//input[@aria-label="Search box"]').send_keys(app_name)
        time.sleep(8)
        self.driver.find_element(By.XPATH, '//a[text()="' + app_name + '"]').click()
        time.sleep(8)
        manage_button = self.driver.find_element(By.XPATH,
                                                 '//div[@aria-label="' + app_name + '"]//div[text()="Manage"]')
        if manage_button.get_attribute("aria-expanded") == "false":
            manage_button.click()
        self.driver.find_element(By.XPATH, '//div[text()="Single sign-on"]').click()
        time.sleep(8)

    @WebAction()
    def edit_basic_saml_configuration(self, app_name, entity_id=None, acs_url=None, slo_url=None, metadata=None):
        """
        Edits the basic SAML configuration details in the SAML app created in Azure

        Args:
            app_name (str)      : SAML App name in Azure
            entity_id (str)     : SP Entity ID
            acs_url (str)       : Single signon URL
            slo_url (str)       : Single logout URL
            metadata (str)      : SP metadata file path
        """
        try:
            self.open_SAML_app(app_name)
            if metadata:
                # uploads metadata file
                self.driver.find_element(By.XPATH, '//div[@title="Upload metadata file"]').click()
                self.driver.find_element(By.XPATH, '//input[@type="file"]').send_keys(metadata)
                self.driver.find_element(By.XPATH, "//div[@title='Add']").click()
            else:
                # updating SP urls
                self.driver.find_element(By.XPATH, '//li[@title="Edit basic SAML configuration"]').click()

                identifier = "//input[@placeholder='Enter an identifier']"
                reply = "//input[@placeholder='Enter a reply URL']"
                logout = "//input[@placeholder='Enter a logout url']"

                time.sleep(3)
                self.driver.find_element(By.XPATH, identifier).click()
                time.sleep(3)
                self.driver.find_element(By.XPATH, identifier).clear()
                self.driver.find_element(By.XPATH, identifier).send_keys(entity_id)
                time.sleep(3)

                self.driver.find_element(By.XPATH, reply).click()
                time.sleep(3)
                self.driver.find_element(By.XPATH, reply).clear()
                self.driver.find_element(By.XPATH, reply).send_keys(acs_url)
                time.sleep(3)

                self.driver.find_element(By.XPATH, logout).click()
                time.sleep(3)
                self.driver.find_element(By.XPATH, logout).clear()
                self.driver.find_element(By.XPATH, logout).send_keys(slo_url)

            self.driver.find_element(By.XPATH, '//div[@aria-label="Save"]').click()

            time.sleep(15)

            self.driver.find_element(By.XPATH,
                                     '''//button[@aria-label="Close content 'Basic SAML Configuration'"]''').click()

        except Exception as exc:
            raise CVWebAutomationException("Exception while editing SAML app details in Azure. {0}".format(str(exc)))

    @WebAction()
    def logout_from_azure(self):
        """
        Logout the user from Azure portal
        """
        try:
            self.driver.find_element(By.XPATH, '//*[@id="fxs-avatarmenu-button"]').click()
            time.sleep(5)
            self.driver.find_element(By.XPATH, '//a[text()="Sign out"]').click()
            time.sleep(5)

        except Exception as exc:
            raise CVWebAutomationException("Exception occurred while logout at Azure site. {0}".format(str(exc)))

    @WebAction()
    def sp_initiated_login(self, command_center_url, hostname, username, pwd, tab_off_approach,
                           sp_initiated_link=None):
        """
        Service provider initiated login

        command_center_url (str)    : Commandcenter URL
        hostname (str)              : Commcell hostname
        azure_url (str)             : Azure web URL
        username (str)              : name of the user to login
        pwd (str)                   : password
        tab_off_approach (bool)     : redirects to other site on click of an element
        sp_initiated_link (str)     : link to initiate SAML login
        """
        # initiate login at SP to get redirected to IDP
        self.initiate_login_at_sp(command_center_url, username, tab_off_approach, sp_initiated_link)
        time.sleep(3)
        # login to azure portal
        self.login(username, pwd)
        self.admin_console.wait_for_completion()
        status = self.check_if_login_is_successful(hostname)
        return status

    @WebAction()
    def sp_initiated_logout(self, hostname):
        """
            Initiate logout from SP and validate SLO

            args:
                hostname (str)      : commandcenter hostname
                azure_url (str)     : AZURE web URL
        """
        self.log.info("Do SP initiated Logout")
        # initiate logout from commandcenter
        status = self.initiated_logout_from_sp(hostname)
        if status:
            self.admin_console.browser.open_url_in_new_tab(self.azure_url)
            self.admin_console.wait_for_completion()
            if self.driver.find_element(By.XPATH, '//div[@class="lightbox-cover"]'):
                self.log.info('User logged out successfully from IDP too')
                status = True
        return status

    @WebAction()
    def login_as_new_user(self):
        """
        Checks if there is any user account in the Azure login screen and selects login as new user
        """
        try:
            if self.driver.find_element(By.XPATH, '//*[@id="otherTile"]'):
                self.driver.find_element(By.XPATH, '//*[@id="otherTile"]').click()
                time.sleep(2)
        except NoSuchElementException as exp:
            self.log.info("No such element found. {0}".format(str(exp)))

    @WebAction()
    def idp_initiated_login(self, hostname, app_name, username, pwd):
        """
        Identity Provider initiated login

        hostname (str)      : commandcenter hostname
        azure_url (str)     : AZURE web URL
        app_name (str)      : SAML app name in Azure site
        username (str)      : Username to login
        pwd (str)           : Password

        return: Login status (bool): True/False
        """
        self.log.info("Do IDP initiated login")
        # navigate to idp init page, azure portal
        self.admin_console.browser.open_url_in_new_tab(self.azure_url)
        self.admin_console.wait_for_completion()
        self.login_as_new_user()
        self.login(username, pwd)
        self.open_SAML_app(app_name)
        self.driver.find_element(By.XPATH, '//*[@title="Test"]').click()
        time.sleep(5)
        self.driver.find_element(By.XPATH, '//*[@title="Test sign in"]').click()
        time.sleep(5)
        self.admin_console.browser.switch_to_latest_tab()
        time.sleep(20)
        self.log.info(self.driver.current_url)
        status = self.check_if_login_is_successful(hostname)
        return status

    def create_saml_app(self, **kwargs):
        """
        Create a SAML app in Azure
        Args:
            kwargs (dict): {"user_object_ids": list[str],
                            "cv_saml_app_metadata": dict,
                            "idp_claim_attributes": dict,
                            "idp_group_claim_attributes": Optional[bool, str]
                            }
        Examples:
            create_saml_app(user_object_ids=["user_object_id1", "user_object_id2"],
                            cv_saml_app_metadata={"entityId": "entityId",
                                                  "singleSignOnUrl": "singleSignOnUrl",
                                                  "singleLogoutUrl": "singleLogoutUrl"},
                            idp_claim_attributes={"un": "user.displayName",
                                                  "email": "user.secondEmail",
                                                  "guid": "user.objectGUID",
                                                  "company": "company_name"},
                            idp_group_claim_attributes=True
                            )
        """
        self.log.info("Creating SAML app in Azure")
        # to get the custom application template on azure
        query_params = ApplicationTemplatesRequestBuilder.ApplicationTemplatesRequestBuilderGetQueryParameters(
            filter="displayName eq 'Custom'",
        )
        request_configuration = RequestConfiguration(query_parameters=query_params)
        custom_application_template = self._run_async(
            self._graph_client.application_templates.get(request_configuration=request_configuration)).value[0]
        # create a new SAML app with custom template
        request_body = InstantiatePostRequestBody(display_name=self.idp_saml_app_name)
        self._application_service_principal = self._run_async(
            self._graph_client.application_templates.by_application_template_id(
                custom_application_template.id).instantiate.post(request_body))
        self.log.info(f"Created SAML app with name: {self._application_service_principal.application.display_name}")
        # enable saml login for the app by updating preferred single sign on mode
        self.log.info("configuring SAML app")
        request_body = ServicePrincipal(
            preferred_single_sign_on_mode="saml",
        )
        self._run_async(self._graph_client.service_principals.by_service_principal_id(
            self._application_service_principal.service_principal.id).patch(request_body))
        # update the commvault SAML app metadata to IDP SAML app
        self.modify_idp_saml_metadata(**kwargs)
        # modify SAML claim attributes
        self.assign_claim_mapping_attributes(**kwargs)
        # add users to SAML app
        self.assign_users_to_saml_app(**kwargs)
        # add signing certificate to the SAML app
        self.add_signing_certificate()
        self.log.info("SAML app created successfully in Azure")

    def _prepare_idp_claim(self, idp_claim_attributes: dict[str, str]):
        """
        Prepare IDP claim attributes
        Args:
            idp_claim_attributes (dict): IDP claim attributes
            {
                "un": "user.displayName",
                "email": "user.secondEmail",
                "guid": "user.objectGUID",
                "fname": "user.firstName",
                "company": "user.company"
            }
        """
        claim_definition = {"ClaimsMappingPolicy": {"Version": 1, "IncludeBasicClaimSet": "true", "ClaimsSchema": []}}
        name_identifier_claim = {"Source": "user", "ID": "userprincipalname",
                                 "SamlClaimType": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier"
                                 }
        claim_definition.get("ClaimsMappingPolicy").get("ClaimsSchema").append(name_identifier_claim)
        for claim, value in idp_claim_attributes.items():
            if value.startswith('user.'):
                claim_schema = {"Source": "user", "ID": value.split('.')[-1], "SamlClaimType": claim}
            else:
                claim_schema = {"Value": value, "SamlClaimType": claim}
            claim_definition.get("ClaimsMappingPolicy").get("ClaimsSchema").append(claim_schema)
        claim_definition = json.dumps(claim_definition)
        self.log.info("generated azure claim schema: %s", claim_definition)
        return claim_definition

    def _delete_claim_mapping_policy(self):
        """to delete existing claim mapping policy from the SAML app in Azure"""
        service_principal_claims_mapping_policies = self._run_async(
            self._graph_client.service_principals.by_service_principal_id(
                self._application_service_principal.service_principal.id).claims_mapping_policies.get()
        )
        for service_principal_claims_mapping_policy in service_principal_claims_mapping_policies.value:
            self._run_async(self._graph_client.policies.claims_mapping_policies.by_claims_mapping_policy_id(
                service_principal_claims_mapping_policy.id).delete())
            self.log.info("Deleted policy with policy id: %s", service_principal_claims_mapping_policy.id)

    def assign_users_to_saml_app(self, user_object_ids: list[str], **kwargs):
        """assign users to the SAML app in Azure
        Args:
            user_object_ids (list[str]): list of azure user object ids
        Examples:
            user_object_ids = ["53581bab-de09-4e14-bc8e-f608793b5620", "a007b70d-c652-4554-a003-abf2d4b61fbv"]
        """
        self.log.info("Assigning users to SAML app in Azure")
        for user_object_id in user_object_ids:
            request_body = AppRoleAssignment(
                principal_id=UUID(user_object_id),
                principal_type="User",
                app_role_id=self._application_service_principal.application.app_roles[0].id,
                resource_id=UUID(self._application_service_principal.service_principal.id),
            )
            self._run_async(self._graph_client.service_principals.by_service_principal_id(
                self._application_service_principal.service_principal.id).app_role_assignments.post(request_body))
            self.log.info(f"Assigned user with object id: {user_object_id} to SAML app")

    def modify_idp_saml_metadata(self, cv_saml_app_metadata: dict[str, str], **kwargs):
        """update commvault SAML app metadata in Azure SAML app
        Args:
            cv_saml_app_metadata (dict): Commvault SAML app metadata
        Examples:
            cv_saml_app_metadata = {"entityId": "https://commvault-hostname:443/identity",
                                    "singleSignOnUrl": "https://..:443/identity/samlAcsIdpInitCallback.do?samlAppKey=..",
                                    "singleLogoutUrl": "https://..:443/identity/server/SAMLSingleLogout?samlAppKey=.."}
        """
        self.log.info("Updating commvault SAML app metadata in Azure SAML app")
        request_body = Application(
            identifier_uris=[
                cv_saml_app_metadata['entityId'],
            ],
            web=WebApplication(
                redirect_uris=[
                    cv_saml_app_metadata['singleSignOnUrl'],
                ],
                logout_url=cv_saml_app_metadata['singleLogoutUrl'],
            ),
        )
        self._run_async(
            self._graph_client.applications.by_application_id(self._application_service_principal.application.id).patch(
                request_body))
        self.log.info("Updated commvault SAML app metadata in Azure SAML app")

    def assign_claim_mapping_attributes(self, idp_claim_attributes: dict[str, str] = None,
                                        idp_group_claim_attributes: Union[bool, str] = None, **kwargs):
        """Assign claim mapping attributes to the SAML app in Azure
        Args:
            idp_claim_attributes (dict): IDP claim attributes dict
            idp_group_claim_attributes (Union[bool, str]): True to enable group claim in SAML Response
        Example:
            idp_claim_attributes={"un": "user.displayName",
                                  "email": "user.secondEmail",
                                  "guid": "user.objectGUID",
                                  "company": "company_name"},
            idp_group_claim_attributes=True
        """
        if idp_claim_attributes:
            self.log.info("Assigning claim mapping attributes to SAML app in Azure")
            # delete existing claim mapping policy
            self._delete_claim_mapping_policy()
            # create new claim mapping policy
            request_body = ClaimsMappingPolicy(
                definition=[
                    self._prepare_idp_claim(idp_claim_attributes)
                ],
                display_name=self._application_service_principal.application.display_name,
                is_organization_default=False,
            )
            claim_mapping_policy = self._run_async(
                self._graph_client.policies.claims_mapping_policies.post(request_body))
            request_body = ReferenceCreate(
                odata_id="https://graph.microsoft.com/v1.0/policies/claimsMappingPolicies/"
                         f"{claim_mapping_policy.id}",
            )
            # update claim mapping policy to the azure SAML app
            self._run_async(self._graph_client.service_principals.by_service_principal_id(
                self._application_service_principal.service_principal.id).claims_mapping_policies.ref.post(
                request_body))
        elif idp_group_claim_attributes:
            self.log.info("Assigning group claim mapping attributes to SAML app in Azure")
            request_body = Application(
                group_membership_claims="All"
            )
            self._run_async(self._graph_client.applications.by_application_id(
                self._application_service_principal.application.id).patch(request_body))

    def add_signing_certificate(self):
        """
        Add signing certificate to the SAML app in Azure
        """
        request_body = AddTokenSigningCertificatePostRequestBody(
            display_name=f"CN={self.idp_saml_app_name}_SSO_Certificate"
        )
        self._run_async(self._graph_client.service_principals.by_service_principal_id(
            self._application_service_principal.service_principal.id).add_token_signing_certificate.post(request_body))
        self.log.info("Signing certificate added to the SAML app in Azure")

    def delete_idp_saml_app(self):
        """
        Delete SAML app in Azure
        """
        self._delete_claim_mapping_policy()
        self._run_async(self._graph_client.applications.by_application_id(
            self._application_service_principal.application.id).delete())
        self.log.info("Deleted SAML app in Azure")
