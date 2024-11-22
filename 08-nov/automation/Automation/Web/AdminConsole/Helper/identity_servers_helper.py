# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be used to run
basic operations on identity servers page.

Class:

    IdentityServersMain:

        __init__()                  --Initializes the Identity servers helper module

IdentityServersMain():

    check_if_saml_app_exists()	    --searches for the given app with search box

    create_saml_app()				--Helper method for creating SAML app in admin console

    open_saml_app()				    --Searches for a given SAML app and opens it

    edit_saml_rule_or_mappings()	--Edit the redirect rule or mappings in SAML app

    modify_saml_general_settings()--Edit the redirect rule or mappings in SAML app

    delete_app()					--Deletes a given SAML app

    validate_saml_app()			    --Checks for the displayed values with the given values

    download_spmetadata()			--Downloads metadata of app

    edit_saml_idp()				    --Edits a given SAML app

    edit_trust_party_adfs()		--Create or delete relying trust party created at the AD machine

    initiate_saml_login()				    --Initiates SAML login

    initiate_saml_logout()				--Performs a SAML logout

    add_associations_on_saml_app()  -- Adds associations for a user on a SAML app

    edit_sp_entity_id()         -- Edit SP Entity ID of SAML App

    add_sp_alias()              -- Add a new SP Alias to SAML App

"""
import base64
import time

from AutomationUtils import logger
from AutomationUtils.machine import Machine
from Web.AdminConsole.Components.table import Table
from Web.IdentityProvider.identity_provider_support import IDPSupport
from Web.AdminConsole.AdminConsolePages.identity_servers import IdentityServers, Domains
from Web.AdminConsole.AdminConsolePages.identity_server_details import IdentityServerDetails
from Web.Common.exceptions import CVWebAutomationException
from Web.Common.page_object import PageService
from random import sample


class IdentityServersMain:
    """
        Helper for IdentityServers page
    """

    def __init__(self, admin_console, commcell=None, csdb=None):
        """
            Initializes the Identity servers helper module

             Args:

                admin_console   (object) -- _Navigator class object

                commcell -- comcell object

                csdb -- csdb object

            Returns : None
        """
        self.__admin_console = admin_console
        self.csdb = csdb
        self.commcell = commcell
        self.__navigator = admin_console.navigator
        self.saml_details = IdentityServerDetails(self.__admin_console)
        self.saml = IdentityServers(self.__admin_console)
        self.identity_provider_obj = IDPSupport(admin_console=self.__admin_console, options_type='ADFS')
        self.okta_obj = IDPSupport(self.__admin_console, 'OKTA')
        self.azure_obj = IDPSupport(self.__admin_console, 'AZURE')
        self.log = logger.get_log()
        self._app_name = None
        self._enable_company = False
        self._redirect_rule = None
        self._associations = None
        self._attribute_mapping = None
        self._sp_entity_id = None
        self._sso_url = None
        self._slo_url = None
        self.__table = Table(self.__admin_console)
        self.identity_servers = IdentityServers(self.__admin_console)
        self.domains = Domains(self.__admin_console)
        self.select_ui_name_query = """
            SELECT
                CONCAT(
                    U.DOMAINNAME,
                    CASE WHEN UP.attrval IS NOT NULL AND UP.attrval<>'' THEN ' (' + UP.attrval + ')' ELSE '' END
                ) AS visiblename
            FROM
                UMDSPROVIDERS U WITH (NOLOCK)
            LEFT JOIN
                UMDSPROVIDERPROP UP WITH (NOLOCK) ON U.id = UP.componentNameId AND UP.attrName LIKE 'displayName'
        """

    @property
    def app_name(self):
        """ Get SAML app name"""
        return self._app_name

    @app_name.setter
    def app_name(self, value):
        """
        Get SAML app name

        Args:
            value   (str)   -- name of the app
        """
        self._app_name = value

    @property
    def sp_entity_id(self):
        """ Get SP Entity Id"""
        return self._sp_entity_id

    @property
    def sso_url(self):
        """ Get Single Sign on URL"""
        return self._sso_url

    @property
    def slo_url(self):
        """ Get Single Logout URL"""
        return self._slo_url

    @property
    def associations(self):
        """ Get SAML app associations"""
        return self._associations

    @associations.setter
    def associations(self, value):
        """ Get SAML app associations

         Args:
            value   (List)   -- List of associations to be set

                    Sample: ['user1,user2']
        """
        self._associations = value

    @property
    def attribute_mapping(self):
        """ Get attribute mapping"""
        return self._attribute_mapping

    @attribute_mapping.setter
    def attribute_mapping(self, value):
        """ Set attribute mapping

        Args:
            value   (dict)   -- Attribute mappings to be set

                    Sample:

                        {
                            "user attribute":"SAML attribute"
                        }
        """
        self._attribute_mapping = value

    def check_if_saml_app_exists(self, app_name):
        """
        searches for the given app with search box

        Args:

        app_name    (str)   --   SAML app name

        Returns:     None
        """
        self.__table.search_for(app_name)
        return self.__admin_console.check_if_entity_exists("link", app_name)

    def create_saml_app(self, idp_metadata_path, description=None,
                        sp_endpoint=None, auto_generate_key=True,
                        jks_file_path=None, alias_name=None,
                        keystore_password=None, key_password=None,
                        email_suffix=None, companies=None,
                        domains=None, user_groups=None):
        """
        creating SAML app in admin console

        Args:

        idp_metadata_path       (str)    : IDP metadata file path

        description             (str)    : Description in SAML app

        sp_endpoint             (str)    : Webconsole url to edit

        auto_generate_key       (bool)   : True if key is auto generated

        jks_file_path           (str)    : keystore file path

        alias_name              (str)    : Alias name for the .jks file

        keystore_password       (str)    : keystore password for the .jks file

        key_password            (str)    : key password for the .jks file

        email_suffix            (list)   : Email suffix of the users to associate

        companies               (list)   : List of companies to associate

        domains                 (list)   : List of ADs to associate

        user_groups             (list)   : List of user groups to associate


        Returns: None
        """
        self.log.info("Creating SAML app")
        self.saml.add_saml_app(self.app_name, idp_metadata_path,
                               description, sp_endpoint, auto_generate_key,
                               jks_file_path, alias_name, keystore_password, key_password,
                               email_suffix, companies, domains, user_groups)
        self.log.info("SAML app is created successfully")

    def open_saml_app(self, app_name):
        """
            Searches for a given SAML app and opens it

            Args:

                app_name    (str)   --   SAML app name

            Returns:     None
        """
        self.saml.select_identity_server(app_name)

    def edit_saml_rule_or_mappings(self, app_name, redirect_rule=None, mappings=None):
        """
            Edit the redirect rule or mappings in SAML app

            Args:

                app_name    (str)   --   SAML app name

                redirect_rule(str)   -- the redirect rule that has to be set

                mappings (str)   --   the attribute mappings that have to be set

            Returns:     None

        """
        if redirect_rule:
            self.saml_details.edit_redirect_rule(redirect_rule)
        if mappings:
            self.saml_details.edit_attribute_mappings(mappings)

    def modify_saml_general_settings(self, app_name, modify_app_state=False, enable_app=True,
                                     modify_auto_create=False, auto_create_user=True,
                                     add_default_usergroup=False,
                                     modify_user_group=False, user_group=None):
        """
            Edit the general settings in SAML app

            Args:

                app_name            (str)   --   SAML app name

                modify_app_state    (bool)   -- Changes the app state to disabled/enabled

                enable_app          (bool)   --  Changes the state of the app

                modify_auto_create  (bool)   --  Changes teh auto user create option

                auto_create_user    (bool)   --  Changes the auto create user to enabled /disabled

                add_default_usergroup(bool)  --  Add's Default User group

                modify_user_group   (bool)   --  Modifies the user group

                user_group          (str)   -- Sets the given user group

            Returns:     None

        """
        self.log.info(" Editing saml app general settings ")
        if modify_app_state:
            self.saml_details.modify_enable_app(enable_app)
        if modify_auto_create:
            self.saml_details.modify_auto_create_user(auto_create_user)
        if add_default_usergroup:
            self.saml_details.add_default_usergroup(user_group)
        if modify_user_group:
            if user_group:
                self.saml_details.modify_user_group(user_group)
            else:
                self.log.info("please give a valid user group")

    def delete_app(self):
        """
            Deletes a given SAML app
        """

        self.log.info("Deleting the command center SAML app ")
        self.__navigator.navigate_to_identity_servers()
        time.sleep(4)
        self.saml.delete_identity_server(self.app_name)

    def validate_saml_app(self, validate_key_dict):
        """
            Checks for the displayed values with the given values

            Args:
                validate_key_dict(dict) --Dictionary of values to validate with displayed values
                                          Sample:{'AppName': 'app name',
                            'Auto user create flag': True,
                            'Default user group': 'company name\\Tenant Users',
                            'Company name': 'company name',
                            'SP entity ID': 'https://hostname:443/webconsole',
                            'SSO URL':
                            'https://hostname:443/identity/samlAcsIdpInitCallback.do?samlAppKey
                            =NDVDQ0E2NUMwMkEzNDkz',
                            'Associations': None,
                            'Redirect rule': {'domain name', 'smtp address'}
                            'Attribute mapping': None}

            Returns:     None

        """
        displayed_val = self.saml_details.saml_app_info()

        self.log.info("Validating the SAML app created")
        for key, value in validate_key_dict.items():
            if displayed_val[key]:
                if isinstance(value, (str, bool)):
                    if displayed_val[key] == validate_key_dict[key]:
                        self.log.info("%s displayed for %s matches with %s given",
                                      displayed_val[key], key, validate_key_dict[key])
                    else:
                        raise CVWebAutomationException("%s displayed for %s does not match with %s given",
                                                       displayed_val[key], key, validate_key_dict[key])
                elif isinstance(value, list):
                    if set(displayed_val[key]) == set(validate_key_dict[key]):
                        self.log.info("%s displayed for %s matches with %s given",
                                      displayed_val[key], key, validate_key_dict[key])
                    else:
                        raise CVWebAutomationException("%s displayed for %s does not match with %s given",
                                                       displayed_val[key], key, validate_key_dict[key])
                else:
                    self.log.info('Entity displayed_val :%s', value)
                    for item, value_dict in value.items():
                        d_val = displayed_val[key][item].replace(" ", "")
                        key_val = validate_key_dict[key][item].replace(" ", "")
                        if d_val == key_val:
                            self.log.info("%s values match", item)
                        else:
                            raise CVWebAutomationException("%s displayed for %s does not match with %s given", d_val,
                                                           item, key_val)
            else:
                self.log.info("Displayed value for %s has None", validate_key_dict[key])
                if validate_key_dict[key] is None:
                    self.log.info("%s displayed for %s matches with %s given",
                                  displayed_val[key], key, validate_key_dict[key])

    def download_spmetadata(self, download_dir):
        """
        Downloads metadata of app

        Args:

            download_dir    (str)   --  Download location of the  SP metadata

        Returns:     None
        """
        downloaded_path = self.saml_details.download_sp_metadata(self.app_name, download_dir)
        return downloaded_path

    def edit_saml_idp(self, app_name, idp_meta_path=None, web_console_url=None,
                      jks_file_path=None, key_password=None, keystore_password=None,
                      alias_name=None):
        """
            Edits a given SAML app

        Args:
            app_name           (str)  :name of the identity server app

            idp_meta_path   (str)   :Location of IDP metadata path

            web_console_url        (str)   :webconsole url to edit

            jks_file_path        (str)    :keystore file path

            key_password        (str)     :key password for the .jks file

            keystore_password    (str)    :keystore password for the .jks file

            alias_name            (str)    :alias name for the .jks file

        Returns:     None
        """
        self.saml_details.edit_idp_details(idp_meta_path, web_console_url, jks_file_path,
                                           key_password, keystore_password, alias_name)

    @staticmethod
    def edit_trust_party_adfs(app_name, ad_host_ip, ad_machine_user, ad_machine_password,
                              sp_metadata_location=None, operation="Create"):
        """
            Create or delete the relying trust party created at the AD machine

            Args:

                app_name            (str)    : name of ADFS app

                ad_host_ip        (str)    :IP/name of AD machine

                ad_machine_user        (str)   :AD machine username

                ad_machine_password        (str)    :AD machine password

                sp_metadata_location    (str)    :path of SP metdata file

                operation                (str)    :Create-if app is created
                                                    Delete-if app is deleted
                                                    Default value is create

            Returns:     None
        """
        machine = Machine(machine_name=ad_host_ip, username=ad_machine_user,
                          password=ad_machine_password)
        if 'Create' in operation:
            output = machine.get_registry_value(
                value="ProgramFilesDir",
                win_key=r"HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion")
            if output:
                destination_path = output.replace("\r\n", "")
                file_name = sp_metadata_location.split('\\')[-1] if sp_metadata_location \
                    else f"SPMetadata_{app_name}.xml"
                destination_file_path = machine.join_path(destination_path, file_name)
                if machine.check_file_exists(destination_file_path):
                    machine.delete_file(destination_file_path)
                machine.copy_from_local(sp_metadata_location, destination_path)
                output = machine.execute_command(
                    'Add-AdfsRelyingPartyTrust -Name "%s" '
                    '-MetadataFile "%s" -IssuanceAuthorizationRules \'@RuleTemplate = '
                    '"AllowAllAuthzRule"=> issue(Type = '
                    '"http://schemas.microsoft.com/authorization/claims/permit", Value '
                    '= "true");\' -IssuanceTransformRules \'@RuleTemplate = '
                    '"LdapClaims"@RuleName = "r1"c:[Type =="http://schemas.microsoft.com/ws/'
                    '2008/06/identity/claims/windowsaccountname",Issuer== "AD AUTHORITY"]=> '
                    'issue(store = "Active Directory", '
                    'types =("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/'
                    'nameidentifier"), query=";mail;{0}", '
                    'param = c.Value);\'' % (app_name, destination_file_path))
                if output.exception:
                    raise CVWebAutomationException("Create operation Failed at ADFS\n" + output.exception)
                if machine.check_file_exists(destination_file_path):
                    machine.delete_file(destination_file_path)
            else:
                raise CVWebAutomationException("Destination path not found")
        elif 'Delete' in operation:
            command = 'Remove-adfsRelyingPArtyTrust -TargetName "' + app_name + '"'
            output = machine.execute_command(command)
            if output.exception:
                raise CVWebAutomationException("Delete operation Failed at ADFS\n" + output.exception)
        else:
            raise CVWebAutomationException("Invalid operation given")

    def initiate_saml_login(self, is_idp_initiated, ad_name, command_center_url, adfs_app_name, user,
                            password, tab_off_approach=True, verify_sso=True, is_test_login=False):
        """
        Initiates SAML login

        Args:
            is_idp_initiated: True if the login has to be initiated form the AD site

            ad_name         (str)   --    AD machine name /IP

            command_center_url(str)   -- web console URL of the client

            adfs_app_name  (str)   --  relying party trust app name

            user           (str)   --   user to login

            password        (str)   --password of the user

            tab_off_approach    (bool)  --True if SP init login is with tab approach

            verify_sso          (bool)  --verifies if SSO is successful

            is_test_login       (bool)  -- if this is a test login, it will click "Test login" button on saml app details page and will do the saml login

        Returns:True if the SAML login succeeds and false otherwise

        """
        hostname = command_center_url.split('//')[-1].split('/')[0].split(':')[0].lower()
        if is_idp_initiated:
            status = self.identity_provider_obj.identity_provider_initiated_login(ad_name,
                                                                                  command_center_url,
                                                                                  adfs_app_name,
                                                                                  user, password,
                                                                                  verify_sso)
        else:
            if tab_off_approach:
                status = self.identity_provider_obj.service_provider_initiated_login(
                    ad_name,
                    hostname,
                    command_center_url,
                    user,
                    password,
                    tab_off_approach,
                    verify_sso,
                    is_test_login=is_test_login)
            else:
                _query = "select appKey from App_ThirdPartyApp where appname = '{0}' and " \
                         "appType = 2".format(self.app_name)
                self.csdb.execute(_query)
                app_key = self.csdb.fetch_one_row()
                if app_key:
                    saml_app_key = base64.b64encode(bytes(app_key[0], 'utf-'))
                else:
                    raise CVWebAutomationException("No such app exists")
                sp_initiated_link = (command_center_url + "/initiateSaml.do?samlAppKey=" +
                                     str(saml_app_key.decode("utf-8")))

                status = self.identity_provider_obj.service_provider_initiated_login(
                    ad_name,
                    hostname,
                    command_center_url,
                    user,
                    password,
                    tab_off_approach,
                    verify_sso,
                    sp_initiated_link
                )
        return status

    def initiate_saml_logout(self, is_idp_initiated, ad_name, command_center_url,
                             verify_single_logout=True):
        """
        Performs a SAML logout

        Args:
            is_idp_initiated    (bool)   -- True if it is a IDP initiated logout

            ad_name             (str)   --Name/IP of the AD machine

            command_center_url     (str)   --web console URL of the client

            verify_single_logout(bool)   --True ,if single logout is to be verified

        Returns:True if logout succeeds or not otherwise False

        """
        hostname = command_center_url.split('//')[-1].split('/')[0].split(':')[0].lower()
        if is_idp_initiated:
            status = self.identity_provider_obj.identity_provider_initiated_logout(
                ad_name,
                command_center_url,
                verify_single_logout)
        else:
            status = self.identity_provider_obj.service_provider_initiated_logout(
                ad_name,
                hostname,
                verify_single_logout)
        return status

    def add_associations_on_saml_app(self, user):
        """
        Adds associations for a user on a SAML app

        Args:

            user    (str)   -- user to be added under associations

        Returns:None

        """
        _query = "select appKey from App_ThirdPartyApp where appname = '{0}' and " \
                 "appType = 2".format(self.app_name)
        self.csdb.execute(_query)
        app_key = self.csdb.fetch_one_row()[0]
        if not app_key:
            raise CVWebAutomationException("No such app exists")

        _query = "select props from App_ThirdPartyApp where appname = '{0}' and " \
                 "appType = 2".format(self.app_name)
        self.csdb.execute(_query)
        props = self.csdb.fetch_one_row()[0]

        self.commcell.add_associations_to_saml_app(self.app_name, app_key, props, user)

    def sp_metadata_values(self):
        """
        returns the SSO url of SAML app
        """
        self._sp_entity_id, self._sso_url, self._slo_url = self.saml_details.sp_metadata_attributes()

    def login_to_okta(self, okta_url, username, pwd):
        """
        Performs Login at OKTA site and verifies if login is successful
        """
        self.__admin_console.browser.open_url_in_new_tab(okta_url)
        self.__admin_console.wait_for_completion()
        self.okta_obj.login(username, pwd)

    def login_to_okta_and_edit_general_settings(self, okta_url, username, pwd, app_name,
                                                sso_url, sp_entity_id, name_id_format=None,
                                                attributes=None, group_attribute=None,
                                                slo=False, single_logout_url=None,
                                                sp_issuer=None, certificate=None):
        """
        Login to OKTA and edit the general settings

        okta_url (str)          : OKTA web url
        username (str)          : username to login
        pwd (str)               : password
        app_name (str)          : app name whose details are to be edited
        sso_url (str)           : Single sign on URL
        sp_entity_id (str)      : SP entity ID
        name_id_format (str)    : Type of value to be received from SAML response
        attributes (dict)       : Attribute Mappings
        group_attribute (dict)  : Group Attribute Mappings
        """
        self.login_to_okta(okta_url, username, pwd)

        self.okta_obj.edit_general_settings(app_name,
                                            sso_url,
                                            sp_entity_id,
                                            name_id_format,
                                            attributes,
                                            group_attribute,
                                            slo, single_logout_url,
                                            sp_issuer, certificate)

    def logout_from_okta(self, admin_user=True):
        """
        Logout from OKTA
        Args :
            admin_user          (bool)      True if logging out of admin user session, False otherwise
        """
        self.okta_obj.logout_from_okta(admin_user)

    def initiate_saml_login_with_okta(
            self,
            command_center_url,
            hostname,
            okta_url,
            username,
            pwd,
            app_name,
            is_idp_initiated,
            tab_off_approach=True,
            sp_initiated_link=None):
        """
        Initiates SAML login with OKTA as Identity provider

        command_center_url (str) :   webconsole url
        hostname (str)          :   commcell hostname
        okta_url (str)          :   OKTA web url
        username (str)          :   username to login
        pwd (str)               :   password
        app_name (str)          :   SAML app name in OKTA
        is_idp_initiated (bool) :   True/False
        tab_off_approach (bool) :   redirects to other url on tab
        sp_initiated_link (str) :   link to initiate SAML login

        return  :   current url after SP/IDP initiated SAML login
        """
        if is_idp_initiated:
            status = self.okta_obj.idp_initiated_login(hostname, okta_url, app_name,
                                                       username, pwd)

        else:
            status = self.okta_obj.sp_initiated_login(command_center_url,
                                                      hostname,
                                                      okta_url,
                                                      username,
                                                      pwd,
                                                      tab_off_approach=tab_off_approach,
                                                      verify_sso=False,
                                                      sp_initiated_link=sp_initiated_link)

        return status

    def initiate_saml_logout_with_okta(self, hostname):
        """
        initiates SAML logoutloaded_url,

        loaded_url (str) :   current url after SAML login
        hostname (str)   :   webconsole hostname
        """
        self.okta_obj.saml_logout(hostname)

    def single_logout(self, okta_url):
        """
        Performs single logout

        okta_url (str)   : OKTA web url
        """
        self.__admin_console.browser.open_url_in_new_tab(okta_url)
        self.__admin_console.wait_for_completion()
        self.okta_obj.single_logout()

    def delete_mapping(self, mapping_dict):
        """
        Deletes Attribute Mappings

        mapping_dict (dict)  :   Mapping dictionary
        """
        self.saml_details.delete_attribute_mapping(mapping_dict, from_edit=False)

    def check_if_login_is_successful(self):
        """
        Checks if Login is successful or not
        """
        self.okta_obj.check_if_login_successful()

    def check_slo(self, okta_url):
        """
        Check single logout status
        """
        return self.okta_obj.check_slo_status(okta_url)

    def login_to_azure_and_edit_basic_saml_configuration(self, username, pwd, appname,
                                                         entity_id=None, acs_url=None,
                                                         slo_url=None, metadata=None):
        """
        Login to Azure and edit Basic SAML configuration details in the app
        Args:
            username    (str)   :   Username to login at Azure site
            pwd         (str)   :   Password of the Azure user
            appname     (str)   :   SAML app name created in IDP
            entity_id   (str)   :   SP entity ID to upload in IDP
            acs_url     (str)   :   SP Single signon url
            slo_url     (str)   :   SP single logout url
            metadata    (str)   :   SP metadata xml file path
        """
        self.__admin_console.browser.open_url_in_new_tab("https://portal.azure.com/")
        self.__admin_console.wait_for_completion()
        self.azure_obj.login_as_new_user()
        is_logged_in = self.azure_obj.login(username, pwd)

        if is_logged_in:
            self.azure_obj.edit_basic_saml_configuration(appname, entity_id, acs_url, slo_url, metadata)

    def initiate_saml_login_with_azure(self, webconsole_url,
                                       username, pwd,
                                       app_name, is_idp_initiated=False,
                                       tab_off_approach=True, sp_initiated_link=False):
        """
            Initiates SAML login with Azure as IDP
            Args:
                webconsole_url  (str)   :   SP webconsole url
                username        (str)   :   SAML username
                pwd             (str)   :   SAML user pwd to login at azure site
                app_name        (str)   :   SAML app name created in IDP
                is_idp_initiated(bool)  :   Is IDP initiated login? (true/false)
                tab_off_approach(bool)  :   Give username and press tab to redirect to IDP (true/false)
                sp_initiated_link (str) :   Auto-redirect to IDP with sp init link present in javaGUI
        """
        hostname = webconsole_url.split('//')[-1].split('/')[0].split(':')[0].lower()
        if is_idp_initiated:
            status = self.azure_obj.idp_initiated_login(hostname,
                                                        app_name,
                                                        username, pwd)

        else:
            status = self.azure_obj.sp_initiated_login(webconsole_url,
                                                       hostname,
                                                       username,
                                                       pwd,
                                                       tab_off_approach=tab_off_approach,
                                                       sp_initiated_link=sp_initiated_link)

        return status

    def logout_from_azure(self):
        """
            Logout from Azure site
        """
        self.azure_obj.logout_from_Azure()

    def sp_init_logout(self, hostname):
        """
        Initiate SAML logout from SP
        Args:
            hostname        (str)   :   webconsole hostname
            azure_url       (str)   :   Azure portal URL
        """
        return self.azure_obj.sp_initiated_logout(hostname)

    def edit_oidc_app_in_okta(self, app_name, login_uri):
        """
        Edit and get properties of OpenID app created in OKTA IDP
        Args:
            app_name        (str)   :   OpenID app name created in IDP
            login_uri       (str)   :   Login URI of the SP

        """
        return self.okta_obj.edit_oidc_app_in_okta(app_name, login_uri)

    def oidc_login(self, webconsole_url, hostname, okta_url, username, pwd):
        """
        OpenID login
        Args:
            webconsole_url (str)    :   webconsole url
            hostname (str)          :   commcell hostname
            okta_url (str)          :   OKTA web url
            username (str)          :   username to login
            pwd      (str)          :   openID user pwd to login at OKTA site
        """
        status = self.okta_obj.oidc_login(webconsole_url,
                                          username, pwd)
        return status

    def oidc_logout(self, hostname):
        """ initiating logout from SP for openID user"""
        return self.okta_obj.initiated_logout_from_sp(hostname)

    def download_gui_console_jnlp(self):
        """Download Commcell GUI from the webconsole applications page"""
        self.azure_obj.download_gui_console_jnlp()

    @PageService()
    def __get_data_for_validation(self, query, type=None, company_name=None, configured=None):
        """Method to retrieve Identity Servers data from UI and DB for validation purpose"""
        self.identity_servers.reset_filters()  # clear all filters before fetching data
        self.csdb.execute(query)
        db_data = {temp[0] for temp in self.csdb.fetch_all_rows() if temp[0] != ''}
        ui_data = set(
            self.identity_servers.list_indentity_servers(type=type, company_name=company_name, configured=configured))

        if db_data != ui_data:
            self.log.info(f'DB Identity Servers : {sorted(db_data)}')
            self.log.info(f'UI Identity Servers : {sorted(ui_data)}')
            data_missing_from_ui = db_data - ui_data
            extra_entities_on_ui = ui_data - db_data
            raise CVWebAutomationException(
                f'Mismatch found between UI and DB\nData missing from UI : {data_missing_from_ui}\
                                           Extra entities on UI : {extra_entities_on_ui}')

        if type: self.identity_servers.clear_column_filter('Type', type)
        if configured is not None: self.identity_servers.clear_column_filter('Configured',
                                                                             'Yes' if configured else 'No')
        self.log.info('Validation completed')

    @PageService()
    def validate_listing_different_indentity_server_types(self):
        """Method to validate different identity_server types"""
        self.log.info("Validating different identity server types...")
        self.__navigator.navigate_to_identity_servers()
        service_types = {
            'Active directory': 2,
            'Apple directory service': 8,
            'Oracle directory': 9,
            'Open LDAP': 10,
            'SAML': 12,
            'LDAP server': 14,
        }
        for service, type in service_types.items():
            query = f"{self.select_ui_name_query} WHERE SERVICETYPE = {type}"
            if service == 'Active directory':
                self.__get_data_for_validation(query=query, type=service, configured=True)
            elif service == 'SAML':
                self.__get_data_for_validation(query=f'{query} and FLAGS = 12', type=service)  # active saml app
                self.__get_data_for_validation(
                    query=f'{query} and FLAGS = 4',
                    type='Active directory',
                    configured=False,
                )  # deconfigured saml app
            else:
                self.__get_data_for_validation(query, service)

    @PageService()
    def validate_listing_company_filter(self):
        """Method to validate company filter on identity server listing page"""
        self.log.info("Validating company filter on identity server listing page..")
        self.__navigator.navigate_to_identity_servers()

        self.__get_data_for_validation(query=f'{self.select_ui_name_query} WHERE SERVICETYPE NOT IN (0,1,5,11)',
                                       company_name='All')
        self.__get_data_for_validation(
            query=f'{self.select_ui_name_query} WHERE SERVICETYPE NOT IN (0,1,5,11) AND OWNERCOMPANY = 0',
            company_name='CommCell')

        self.csdb.execute('SELECT ID, HOSTNAME FROM UMDSPROVIDERS WHERE SERVICETYPE=5 AND ENABLED=1 AND FLAGS=0')
        company_details = self.csdb.fetch_all_rows()
        if len(company_details) > 5: company_details = sample(company_details, 5)
        for id, company_name in company_details:
            self.__get_data_for_validation(
                query=f"{self.select_ui_name_query} WHERE SERVICETYPE NOT IN (0,1,5,11) AND OWNERCOMPANY = {id}",
                company_name=company_name)
        self.log.info("company filter validation completed")

    @PageService()
    def validate_listing_simple_indentity_server_creation(self, input):
        """Method to validate a simple identity server creation"""
        if self.commcell.domains.has_domain(input['netbios_name']):  # clean up before starting
            self.commcell.domains.delete(input['netbios_name'])
        self.log.info("Validating identity server creation...")
        self.__navigator.navigate_to_identity_servers()
        self.domains.add_domain(domain_name=input['domain_name'], netbios_name=input['netbios_name'],
                                username=input['username'], password=input['password'])
        self.__admin_console.wait_for_completion()
        self.__navigator.navigate_to_identity_servers()

        self.csdb.execute(f"SELECT DOMAINNAME FROM UMDSPROVIDERS WHERE DOMAINNAME = '{input['netbios_name']}'")
        if not [identity_server[0] for identity_server in self.csdb.fetch_all_rows() if identity_server[0] != '']:
            raise CVWebAutomationException('[DB] Identity Server not found in database.')

        if not self.identity_servers.is_indentity_server_exists(input['netbios_name']):
            raise CVWebAutomationException('[UI] Identity Server not found on UI.')
        self.log.info('Identity server creation validation completed')

    @PageService()
    def validate_listing_indentity_server_deletion(self, domain_name):
        """Method to validate identity server deletion"""
        self.log.info("Validating identity server deletion..")
        self.__navigator.navigate_to_identity_servers()
        self.domains.delete_domain(domain_name)
        self.__admin_console.driver.implicitly_wait(10)

        self.csdb.execute(f"SELECT DOMAINNAME FROM UMDSPROVIDERS WHERE DOMAINNAME = '{domain_name}'")
        if [identity_server[0] for identity_server in self.csdb.fetch_all_rows() if identity_server[0] != '']:
            raise CVWebAutomationException('[DB] Identity Server found in database after deletion.')

        if self.identity_servers.is_indentity_server_exists(domain_name):
            raise CVWebAutomationException('[UI] Identity Server found on UI after deletion.')
        self.__admin_console.driver.implicitly_wait(0)
        self.log.info('Identity server deletion validation completed')

    def edit_sp_entity_id(self, sp_entity_id):
        """Method to edit sp entity Id of saml app
            Args:
                sp_entity_id        (str)  new value of sp entity id
        """
        self.saml_details.edit_sp_entity_id(sp_entity_id)

    def add_sp_alias(self, sp_alias):
        """Adds a new sp alias to saml app"""

        self.saml_details.add_sp_alias(sp_alias)
