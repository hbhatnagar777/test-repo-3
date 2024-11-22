# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Companies page on the AdminConsole

Class:

    IdentityServers()

Functions:

_init_()                    -- initialize the class object identity serveres page
click_add()                 -- clicks the add saml app link
click_saml()                -- selects the SAML tab in add domain dialog box
set_application_name()      -- fills the application name field with the given application name
set_description()           -- fills the description for SAML app
upload_idp_metadata()       -- uploads the idp metadata file
set_service_provider_endpoint()    -- fills the webconsole_url field with the specified URL
upload_jks_file()           -- uploads the keystore file
set_alias_name()            -- fills the alias name field with the given value
set_keystore_password()     --sets the keystore password field with given value
set_key_password()          --sets the key password field with given value
save_saml_app()             --clicks the save button in add saml app
click_next()                -- click NEXT button in the panel during SAML app creation
add_email_association()     -- Associate email suffix to SAML app
add_company_association()   --  Associate company to SAML app
add_domain_association()    --  Associate AD to SAML app
add_usergroup_association() --  Associate usergroups to SAML app
select_identity_server()    --clicks on the given saml app link
add_saml_app()              -- adds saml app
is_indentity_server_exists()-- Method to check if identity server exists
list_indentity_servers()    -- Method to return the list of indentity servers
clear_column_filter()       -- Method to clear the column filter

Class:
    Domains

Functions:

__init__()                      -- initialize the class object identity serveres page
__click_ad_tab()                -- selects the AD tab in add domain dialog box
__enable_proxy_client()         -- Checks the enable proxy client checkbox
__disable_proxy_client()        -- Un-checks the enable proxy client checkbox
__return_elements()             -- Returns elements for the given xpath
__get_text_from_element_obj()   -- Returns text from the give element object
get_domains_list()              -- Returns list of domains
add_domain()                    -- adds a new domain to the admin console
delete_domain()                 -- delete the domain with the specified name
get_domains_list()              -- returns list of all domains displayed on the page
"""

import time
from selenium.webdriver.common.by import By
from Web.AdminConsole.Components.table import Rtable, Rfilter
from Web.AdminConsole.Components.panel import RModalPanel, DropDown, RDropDown, RPanelInfo
from Web.AdminConsole.Components.dialog import RTransferOwnership, RModalDialog
from Web.Common.page_object import WebAction, PageService


class IdentityServers:
    """
    This class provides the operations performed on Identity servers Page of adminconsole
    """

    def __init__(self, admin_console):
        self.__driver = admin_console.driver
        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.log = self.__admin_console.log
        self.__rpanel = RPanelInfo(self.__admin_console)
        self.__table = Rtable(self.__admin_console)
        self.__drop_down = DropDown(admin_console)
        self.__modal_dialog = RModalDialog(self.__admin_console)

    @WebAction()
    def click_add(self):
        """
        clicks the add saml app link
        """
        self.__driver.find_element(By.XPATH, "//div[contains(text(),\
            '" + self.__admin_console.props['label.add'] + "')]").click()

    @WebAction()
    def click_saml(self):
        """
        selects the SAML Option
        """
        self.__driver.find_element(By.XPATH, "//li[contains(text(),\
                    '" + self.__admin_console.props['label.saml'] + "')]").click()

    @WebAction()
    def set_application_name(self, app_name):
        """
        fills the application name field with the given application name
        Args:
            app_name    (str):name of the SAML app to edit
        """
        self.__admin_console.fill_form_by_id("appName", app_name)

    @WebAction()
    def set_description(self, description):
        """
        Set the description for SAML app
        Args:
            description    (str):   Description for SAML app
        """
        self.__admin_console.fill_form_by_id("appDescription", description)

    @WebAction()
    def upload_idp_metadata(self, idp_metadata_path):
        """
        Upload the idp metadata file
        Args:
            idp_metadata_path    (str):path of idp metadata file
        """
        self.__driver.find_element(By.NAME, "idpMetadataFile").send_keys(idp_metadata_path)
        time.sleep(3)

    @WebAction()
    def set_service_provider_endpoint(self, sp_endpoint):
        """
        fills the webconsole url field with the specified URL
        Args:
            sp_endpoint    (str): URL of the webconsole
        """
        self.__admin_console.fill_form_by_id("serviceProviderEndpoint", sp_endpoint)

    @WebAction()
    def upload_jks_file(self, jks_file_path):
        """
        uploads the keystore file
        Args:
            jks_file_path    (str): path of the jks file to upload
        """
        self.__driver.find_element(By.NAME, "jksFileUpload").send_keys(jks_file_path)

    @WebAction()
    def set_alias_name(self, alias_name):
        """
        fills the alias name field with the given value
        Args:
            alias_name    (str):    sets the given alias name for keystore file
        """
        self.__admin_console.fill_form_by_id("certificateAliasName", alias_name)

    @WebAction()
    def set_keystore_password(self, keystore_password):
        """
        fills the keystore password field with the given value
        Args:
            keystore_password    (str):     sets the given keystore_password for keystore file
        """
        self.__admin_console.fill_form_by_id("keyStorePassword", keystore_password)

    @WebAction()
    def set_key_password(self, key_password):
        """
        Fills the key password field with the given value
        Args:
            key_password    (str):    sets the given key password for keystore file
        """
        self.__admin_console.fill_form_by_id("privateKeyPassword", key_password)

    @PageService()
    def save_saml_app(self):
        """
        clicks the Finisth button in add saml app
        """
        self.__admin_console.click_button()
        self.__driver.find_element(By.XPATH, "//div[contains(text(),\
                                    '" + self.__admin_console.props['action.submit'] + "')]").click()

    @WebAction()
    def select_identity_server(self, app_name, app_type="SAML"):
        """
        selects the given app with search box
        Args:
            app_name        (str) :  app name to select
            app_type        (str) :  AD/SAML
        """
        self.__table.access_link(app_name)

    @WebAction()
    def click_next(self):
        """
        Click NEXT button
        """
        self.__driver.find_element(By.XPATH, "//div[contains(text(),\
                            '" + self.__admin_console.props['label.next'] + "')]").click()

    @WebAction()
    def click_finish(self):
        """Click Finish button"""
        self.__driver.find_element(By.XPATH, "//button[@aria-label='Finish']").click()

    @WebAction()
    def add_email_association(self, email_suffixes):
        """
        Associate email suffix to SAML app
        Args:
            email_suffixes  (list)  :   Email suffix of the users who would like to do SAML login
        """
        self.add_association = self.__driver.find_element(By.XPATH, "//div[contains(text(),\
                                                '" + self.__admin_console.props['label.add'] + "')]")
        for email_suffix in email_suffixes:
            self.__admin_console.fill_form_by_id("emailSuffix", email_suffix)
            self.add_association.click()

    @WebAction()
    def add_company_association(self, companies):
        """
        Associate ecomapny to SAML app
        Args:
            companies  (list)  :   List of company names to associate with SAML app
        """
        self.__driver.find_element(By.XPATH, "//*[@class='master-list']/li[2]/a").click()
        time.sleep(3)
        for company in companies:
            self.__admin_console.select_drop_down_values(company)
            self.add_association.click()

    @WebAction()
    def add_domain_association(self, domains):
        """
        Associate AD to SAML app
        Args:
            domains  (list)  :   List of AD names to associate with SAML app
        """
        self.__driver.find_element(By.XPATH, "//*[@class='master-list']/li[2]/a").click()
        time.sleep(3)
        for domain in domains:
            self.__admin_console.select_drop_down_values(domain)
            self.add_association.click()

    @WebAction()
    def add_usergroup_association(self, usergroups):
        """
        Associate usergroup to SAML app
        Args:
            usergroups  (list)  :   List of usergroup names to associate with SAML app
        """
        self.__driver.find_element(By.XPATH, "//*[@class='master-list']/li[2]/a").click()
        time.sleep(3)
        for usergroup in usergroups:
            self.__admin_console.select_drop_down_values(usergroup)
            self.add_association.click()

    @PageService()
    def delete_identity_server(self, app_name):
        """
        deletes the given app
        Args:
            app_name        (str) :  app name to delete
        """
        # delete the SAML app directly from the listing page.
        if self.__admin_console.check_if_entity_exists("link", app_name):
            self.__table.access_action_item(app_name, self.__admin_console.props['action.delete'])
            self.__modal_dialog.click_yes_button()
            self.__admin_console.check_error_message()
        else:
            self.log.info("SAML app is not present.")

    @PageService(react_frame=True)
    def add_saml_app(self, app_name, idp_metadata_path, description=None,
                     sp_endpoint=None, auto_generate_key=True,
                     jks_file_path=None, alias_name=None,
                     keystore_password=None, key_password=None,
                     email_suffix=None, companies=None, domains=None, user_groups=None):
        """
        Adds the saml app with the specified inputs in the arguments.
        Args:
            app_name                (str)   :   name of SAML app
            idp_metadata_path       (str)   :   IDP metadata file path
            description             (str)   :   SAML app description
            sp_endpoint             (str)   :   Service Provider endpoint
            auto_generate_key       (bool)  :   True if key is auto generated
            jks_file_path           (str)   :   keystore file path
            key_password            (str)   :   key password for the .jks file
            keystore_password       (str)   :   keystore password for the .jks file
            alias_name              (str)   :   alias name for the .jks file
            email_suffix            (list)  :   Email suffixes of users
            companies               (list)  :   Company names
            domains                 (list)  :   AD names
            user_groups             (list)  :   Usergroup names
        """
        # add a new SAML app with the given parameters
        self.click_add()
        self.__admin_console.wait_for_completion()
        self.click_saml()
        self.set_application_name(app_name)
        if description:
            self.set_description(description)
        self.click_next()
        self.upload_idp_metadata(idp_metadata_path)
        self.click_next()
        if sp_endpoint:
            self.set_service_provider_endpoint(sp_endpoint)
        if not auto_generate_key:
            self.__rpanel.disable_toggle(self.__admin_console.props['label.autoGenerateKey'])
            self.upload_jks_file(jks_file_path)
            self.set_alias_name(alias_name)
            self.set_keystore_password(keystore_password)
            self.set_key_password(key_password)
        self.click_next()

        if email_suffix:
            self.add_email_association(email_suffix)
        if companies:
            self.add_company_association(companies)
        if domains:
            self.add_domain_association(domains)
        if user_groups:
            self.add_usergroup_association(user_groups)

        self.click_next()
        self.__admin_console.check_error_message()
        self.__admin_console.wait_for_completion()

        self.click_finish()
        self.__admin_console.wait_for_completion()
        return True

    @PageService()
    def is_indentity_server_exists(self, indentity_server_name):
        """Method to check if an indentity server exists"""
        return self.__table.is_entity_present_in_column(column_name='Name', entity_name=indentity_server_name)

    @PageService()
    def reset_filters(self):
        """Method to reset the filters applied on the page"""
        self.__table.reset_filters()

    @PageService()
    def list_indentity_servers(self, type: str = str(), company_name: str = str(), configured: bool = bool()):
        """
            Lists all the indentity servers

            Arguments:
                type            (str):      To filter/ fetch indentity servers of a particular type
                company_name    (str):      To filter/ fetch indentity servers of a particular company
                configured      (bool):     To filter/ fetch active/deconfigured indentity servers
        """
        if type:
            self.__table.apply_filter_over_column(column_name='Type', filter_term=type, criteria=Rfilter.equals)
        if company_name:
            self.__table.select_company(company_name)
        if configured is not None:
            self.__table.apply_filter_over_column(column_name='Configured', filter_term='Yes' if configured else 'No',
                                                  criteria=Rfilter.equals)
        return self.__table.get_column_data(column_name='Name', fetch_all=True)

    @PageService()
    def clear_column_filter(self, column_name, filter_term):
        """
        Method to clear filter from column

        Args:
            column_name (str) : Column name filter to be removed from

            filter_term (str) : value given for the filter
        """
        self.__table.clear_column_filter(column_name, filter_term)

    def get_all_identity_server(self):
        """Method to get all identity servers on identity servers page"""
        return self.__table.get_column_data('Name', fetch_all=True)


class Domains:

    def __init__(self, admin_console):

        self.__driver = admin_console.driver
        self.__admin_console = admin_console
        self.__table = Rtable(self.__admin_console)
        self.__modal_panel = RModalPanel(self.__admin_console)
        self.__transfer_ownership = RTransferOwnership(self.__admin_console)
        self.__drop_down = RDropDown(self.__admin_console)

    @WebAction()
    def __click_ad_tab(self):
        """
        selects the AD tab in add domain dialog box
        """
        self.__driver.find_element(By.XPATH,
                                   "//div[@ng-click='authenticationChoice=1']").click()

    @WebAction()
    def enable_proxy_client(self):
        """Checks the proxy client checkbox"""
        self.__admin_console.checkbox_select("accessViaClient")

    @WebAction()
    def disable_proxy_client(self):
        """Unchecks the proxy client checkbox"""
        self.__admin_console.checkbox_deselect("accessViaClient")

    @PageService()
    def enable_secure_ldap(self):
        """Checks the secure ldap checkbox"""
        self.__admin_console.checkbox_select("useSecureLDAP")

    @PageService()
    def disable_secure_ldap(self):
        """Unchecks the secure ldap checkbox"""
        self.__admin_console.checkbox_deselect("useSecureLDAP")

    @WebAction()
    def return_elements(self, xpath):
        """Returns elements"""

        return self.__driver.find_elements(By.XPATH, xpath)

    @WebAction()
    def get_text_from_element_obj(self, elem, xpath):
        """Returns text from element object"""
        return elem.find_element(By.XPATH, xpath).text

    @WebAction()
    def get_domains_list(self):
        """Method to get domains list"""
        domain_names = []
        elems = self.return_elements(
            "//div[@class='k-grid-content k-auto-scrollable']//tbody/tr")

        for elem in elems:
            if self.get_text_from_element_obj(elem, "./td[2]/span").text == 'AD':
                domain_name = self.get_text_from_element_obj(elem, "./td[1]/span/a").text
                domain_names.append(domain_name)
        return domain_names

    @PageService()
    def add_domain(self,
                   domain_name,
                   netbios_name,
                   username,
                   password,
                   secure_ldap=False,
                   proxy_client=None,
                   proxy_client_value=None,
                   company_name=None,
                   user_group=None,
                   local_group=None,
                   quota_enabled=False,
                   quota_limit=100,
                   **kwargs):
        """
        Adds a new domain to the commcell

        Args:
            domain_name (str) : the name of the domain

            netbios_name (str): the netbios name of the domain

            username (str)    : the username of the domain

            password (str)    : the password of the domain

            proxy_client(boolean)    : enable/disable Access AD via client

            proxy_client_value(str) : client to access AD server from

            company_name (str): company name to be associated with domain

            user_group (str): user group be associated with domain

            local_group (list): list of local user groups to be associated with domain

            quota_enabled (boolean) : enable/disable quota enabled checkbox

            quota_limit (int)       : value of quota limit

            **kwargs:
                is_creator_msp (boolean)    : If the user creating the AD is msp admin user

        Returns:
            None

        """
        self.__table.access_menu_from_dropdown('AD/LDAP', 'Add')
        self.__drop_down.select_drop_down_values(values=["Active directory"], drop_down_id='directoryType')
        self.__admin_console.fill_form_by_id("NETBIOSName", netbios_name)
        self.__admin_console.fill_form_by_id("name", domain_name)
        self.__admin_console.fill_form_by_id("username", username)
        self.__admin_console.fill_form_by_id("password", password)

        if secure_ldap:
            self.enable_secure_ldap()

        if not kwargs.get("is_creator_msp", None):
            if proxy_client:
                self.enable_proxy_client()
                if proxy_client_value:
                    self.__drop_down.select_drop_down_values(values=[proxy_client_value], drop_down_id='proxies')
            else:
                self.disable_proxy_client()

        if company_name is not None:
            self.__drop_down.select_drop_down_values(drop_down_id="createForCompanies", values=[company_name])
        self.__admin_console.submit_form()
        self.__admin_console.wait_for_completion()
        self.__admin_console.check_error_message()
        # self.__admin_console.wait_for_element_to_be_clickable('localGroups')

        if user_group:
            self.add_user_group(user_group, local_group, quota_enabled, quota_limit)
        else:
            self.__admin_console.click_button(self.__admin_console.props['label.cancel'])

    @PageService()
    def add_user_group(self, user_group, local_group=None, quota_enabled=False, quota_limit=100):
        """
        Method to add user group to the domain

        Args:
            user_group  (string)    : the user group to be added to the domain

            local_group (list)      : list of local groups to associate with the domain

            quota_enabled (boolean) : enable/disable quota enabled checkbox

            quota_limit (int)       : value of quota limit
        """

        self.__modal_panel.search_and_select(user_group, label="Group name", id='adGroupName')
        if local_group:
            if isinstance(local_group, str):
                local_group = [local_group]
            self.__drop_down.select_drop_down_values(values=local_group, drop_down_id='localGroups')

        if quota_enabled:
            self.__admin_console.checkbox_select("enforceFSQuota")
            if quota_limit:
                self.__admin_console.fill_form_by_id("quotaLimitInGB", quota_limit)
        else:
            self.__admin_console.checkbox_deselect("enforceFSQuota")

        self.__modal_panel.submit()

    @PageService()
    def delete_domain(self, domain_name, skip_ownership_transfer=True, transfer_owner=None):
        """
        Deletes the domain with the given name

        Args:
            domain_name (string)            : the name of the domain whose information has to
                                                   modified

            skip_ownership_transfer (bool)  : whether ownerhip has to be transferred or not

            transfer_owner (string)         : Name of owner if ownership of domain has to be
                                                  transferred

        Returns:
            None
        """

        if self.__admin_console.check_if_entity_exists("link", domain_name):

            self.__table.access_action_item(domain_name, "Delete")
            if not skip_ownership_transfer:
                self.__transfer_ownership.transfer_ownership(transfer_owner)
            else:
                self.__admin_console.click_button("Delete")
            self.__admin_console.check_error_message()
        else:
            raise Exception("Domain does not exist")

    @PageService()
    def domains_list(self):

        """Returns list of domains visible on the page"""

        self.__admin_console.navigate_to_identity_servers()
        domains_names = self.get_domains_list()
        return domains_names
