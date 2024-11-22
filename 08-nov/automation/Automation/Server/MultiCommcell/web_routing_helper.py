# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file for performing web routing related operations

WebRoutingHelper is the only class defined in this file

----------------------------------------------------------------------------------------------------------------------


WebRoutingHelper
======================================== PROPERTIES =============================================

    service_cs                      --  commcell sdk object for service commcell
    service2_cs                     --  commcell sdk object for second service commcell if any

    service_machine                 --  machine object for service commcell
    service2_machine                --  machine object for second service commcell
    router_machine                  --  machine object for router commcell

    service_dbops                   --  dbops object for service commcell
    service2_dbops                  --  dbops object for second service commcell
    router_dbops                    --  dbops object for router commcell

    service_master_user             --  a master user in service commcell
    service_aduser                  --  a created AD user in service commcell (with admin rights)
    service_unpreviledged_user      --  a commcell user in service commcell without rights
    service_company_entiites        --  a company with tenant admin, tenant user in service commcell
    service_samluser                --  a dummy SAML user in service commcell
    router_only_user                --  a user only in router
    router_and_service_user         --  a user present in both router and service
    router_only_aduser              --  an AD user who can be created in router, not yet present
    service_only_aduser             --  an AD user who can be created in service, not yet present
    router_and_service_aduser       --  an AD user common to both router and service, but not present in either yet

======================================== UTILS =============================================

    setup_ad                        --  reads creds and created AD in given commcell

    clean_up                        --  cleans up most of the entities created

    validate_entire_sync            --  validates full sync of all domain, rule, userspace, authcodes

    validate_roles                  --  validates the multi commcell roles in DB are set as expected

    validate_third_party_app        --  validates the TPA rows are present properly

    validate_unregistration         --  validates service commcell unregistration

    get_api_redirects               --  fetches redirect list via API

    get_dbsp_redirects              --  fetches redirect list via DB storedproc

    get_ui_redirects                --  fetches redirect list rendered/handled in UI

    get_redirects_stats             --  fetches collected stats for redirect via API, UI, DB and response times

======================================== TEST STEPS ========================================

    registration_test               --  tests all registration and unregistration cases

    force_unregister_test           --  tests force unregistration case when services down

    refresh_test                    --  tests on demand sync and auto reverse sync when entities created in service

    validate_all_redirects          --  tests all the redirects for different user types

----------------------------------------------------------------------------------------------------------------------

DBOps
=====

    get_synced_redirect_rules       --  gets synced authcodes, domains, rules from app_componentprop for service cs

    get_synced_userspace            --  gets usernames from umusersservicecommcell for given service cs

    get_globalparam_role            --  gets the multicommcellrole from gxglobalparam

    get_tpa_apps                    --  gets the appnames from app_thirdpartyapp with given app id

    get_local_redirect_rules_db     --  gets authcodes, rules, domains to be sent to router for sync
                                        via storedproc MCC_FetchRedirectsforRouterCommcell

    get_user_redirects_from_sp      --  gets all redirect_urls for given user or email
                                        via storedproc MCC_HandleRedirectsForUser

"""
import functools
import json
import time
from base64 import b64encode
from urllib.parse import urlparse

import pandas as pd
import xmltodict

from AutomationUtils import logger
from AutomationUtils.commonutils import get_differences, get_random_string
from AutomationUtils.database_helper import CSDBOperations
from AutomationUtils.options_selector import OptionsSelector
from Server.MultiCommcell.multicommcellconstants import WebRoutingConfig
from Server.MultiCommcell.multicommcellhelper import MultiCommcellHandler
from Server.Security.samlhelper import SamlHelperMain
from Web.AdminConsole.AdminConsolePages.LoginPage import LoginPage
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from cvpysdk.commcell import Commcell
from cvpysdk.exception import SDKException
from cvpysdk.security.security_association import SecurityAssociation


class WebRoutingHelper:
    """Helper class to perform Web routing related tests"""

    registration_cases = [
        'invalid_creds', 'invalid_permissions', 'service_down',  # negative cases
        'master_username', 'master_email',
        'ad_master_username', 'ad_master_email',
        'default', 'default_email'
    ]
    ROLE_BITS = {
        "NOTCONFIGURED": 0,
        "ROUTERCOMMCELL": 1,
        "ROUTERCOMMCELL_SERVICECOMMCELL": 2,
        "IDPCOMMCELL": 4,
        "IDPCOMMCELL_SERVICECOMMCELL": 8,
        "CLOUDSERVICE": 16,
        "ONPRIM_SUBSCRIBER_OF_CLOUDSERVICE": 32,
        "MSP_CLOUDSERVICE": 64
    }

    # # # # # DB UTILS SUBCLASS # # # # #
    class DBOps(CSDBOperations):
        """DB wrapper class to perform WebRouting related DB operations"""
        def get_synced_redirect_rules(self, service_commcell: str) -> dict:
            """
            Gets the redirect rules from DB

            Args:
                service_commcell    (str)   -   name of service commcell to fetch redirect rules associated to it

            Returns:
                dict - consisting of all rules, domains, authcodes synced from service commcell
                {
                    'authcodes': [...],
                    'domains': [...],
                    'rules': [...]
                }
            """
            self.log.info(f"reading redirect rules in db synced from {service_commcell}")
            resp = self.csdb.execute(
                f"select stringVal, propertyTypeId from app_componentprop "
                f"where componentType = 1047 "
                f"and componentId = (select id from app_commcell where aliasName like '{service_commcell}')"
            )
            prop_types_map = {
                'rules': 1,
                'domains': 2,
                'authcodes': 3
            }
            rrs = {
                prop_key: [value[0] for value in resp.rows if int(value[1]) == prop_val and value[0] != '']
                for prop_key, prop_val in prop_types_map.items()
            }
            self.log.info(f'got redirect rules -> {rrs}')
            return rrs

        def get_synced_userspace(self, service_commcell: str) -> list[str]:
            """Gets the users space from Router commcell

            Args:
                service_commcell    (str)   -   name of service commcell to fetch redirect rules associated to it

            Returns:

                list_of_users_space_on_router     (list)  -- list of users space on router for service commcell

                for example:    ['user1','user2','user3']

            """
            self.log.info(f"reading userspace in DB synced from {service_commcell}")
            resp = self.csdb.execute(
                f"select login from UMUsersServiceCommcell "
                f"where origCCId = (select id from app_commcell where aliasName like '{service_commcell}')"
            )
            usp = [values[0] for values in resp.rows]
            self.log.info(f'got user space -> {usp}')
            return usp

        def get_globalparam_role(self) -> int:
            """
            Gets the gxglobalparam multi commcell role from service

            Returns:
                role    (int)   -   role value from DB
            """
            role_query = "select value from GxGlobalParam where name='nMultiCommcellRole';"
            resp = self.csdb.execute(role_query)
            role = resp.rows[0][0]
            return 0 if role == '' else int(role)

        def get_tpa_apps(self, app_type: int = 3) -> list[str]:
            """
            Gets the appnames column of app_thirdPartyApp from service

            Args:
                app_type    (int)   -   app type to filter by

            Returns:
                app_names   (list)  -   list of app names
            """
            tpa_query = f"select appName from App_ThirdPartyApp where appType={app_type};"
            resp = self.csdb.execute(tpa_query)
            if resp.rows == [['']]:
                return []
            return [row[0].upper() for row in resp.rows]

        def get_local_redirect_rules_db(self) -> dict:
            """
            gets all the redirect rules from Service commcell database.

            Returns:

                dict - consisting of all rules, domains, authcodes
                {
                    'authcodes': [...],
                    'domains': [...],
                    'rules': [...]
                }
            """
            self.log.info("fetching the redirect rules using MCC_FetchRedirectsforRouterCommcell")
            resp = self.csdb.execute(f"SET NOCOUNT ON;EXEC MCC_FetchRedirectsforRouterCommcell;")
            json_resp = xmltodict.parse(resp.rows[0][0])
            self.log.info(f'got xml -> {json_resp}')
            authcodes = json_resp.get('RedirectRules', {}).get('authCodes', [])
            if isinstance(authcodes, str):
                authcodes = [authcodes]
            return {
                'authcodes': authcodes,
                'domains': json_resp.get('RedirectRules', {}).get('domains', []),
                'rules': json_resp.get('RedirectRules', {}).get('rules', []),
            }

        def get_user_redirects_from_sp(self, user_or_mail: str) -> list[str]:
            """
            Gets the redirects for given user from StoredProc

            Args:
                user_or_mail    (str)   -   the user or mail id to pass to StoredProc

            Returns:
                redirect_list   (list)  -   list of redirect names
            """
            self.log.info(f"reading MCC_HandleRedirectsForUser stored proc response for user {user_or_mail}")
            stored_proc_str = f"SET NOCOUNT ON;EXEC MCC_HandleRedirectsForUser '{user_or_mail}',3,'',0,'',1,1;"
            xml_out = self.csdb.execute(stored_proc_str).rows[0][0]
            self.log.info("got StoredProc response successfully")
            self.log.info(xml_out)
            parsed_sp = xmltodict.parse(xml_out).get('RedirectsForUser', {}).get('AvailableRedirects', [{}])
            if isinstance(parsed_sp, dict):
                parsed_sp = [parsed_sp]
            parsed_sp_list = {urlparse(red_dict.get('@redirectUrl')).netloc for red_dict in parsed_sp}
            return list(parsed_sp_list)

    # # # # # WEBROUTINGHELPER CLASS # # # # #
    def __init__(self, router_cs: Commcell, **config_options) -> None:
        """
        Initializes the WebRoutingHelper class

        Args:
            router_cs   (Commcell)  -   commcell sdk object of router commcell
            config_options:
                ---------------------------------- commcell params --------------------------------------
                <token>_hostname
                <token>_rdp_username, <token>_rdp_password
                <token>_db_username,<token>_db_password
                <token>_cs_username,<token>_cs_password
                where token should be from ['router', 'service', 'service2']
                ------------------------------------- entity params -------------------------------------
                comp_name   (str)           -   name of company to create
                comp_alias  (str)           -   alias name of company
                default_password    (str)   -   the password to set for created users
                service_master_user (str)   -   username of test master user in service
                service_master_email (str)  -   email for test master user in service
                service_unpreviledged_user  -   username of test service user without rights
                service_unpreviledged_email -   email of test service user without rights
                router_only_user    (str)   -   username for user only in router
                router_only_email   (str)   -   email for the user only in router
                router_and_service_user(str)-   username for user in both router and service
                router_and_service_email    -   email fpr the user in both router and service
                -------------------------------------- AD, SAML params ---------------------------------------
                service_ad_creds    (dict)  -   follow the format of WebRoutingConfig.SERVICE_AD_CREDS in
                                                Server.MultiCommcell.multicommcellconstants
                router_ad_creds (dict)      -   follow the format of WebRoutingConfig.ROUTER_AD_CREDS in
                                                Server.MultiCommcell.multicommcellconstants
                common_ad_creds (dict)      -   follow the format of WebRoutingConfig.COMMON_AD_CREDS in
                                                Server.MultiCommcell.multicommcellconstants
                saml_creds    (dict)        -   follow the format of WebRoutingConfig.SAML_CREDS in
                                                Server.MultiCommcell.multicommcellconstants
        """
        self.mcc = MultiCommcellHandler(
            WebRoutingConfig,
            config_options | {'router_hostname': router_cs.webconsole_hostname},
            WebRoutingHelper.DBOps
        )
        self.mcc._commcell_objects['router'] = router_cs
        self.wait_time = int(config_options.get('wait_time') or 5)
        self._router_and_service_aduser = None
        self._service_only_aduser = None
        self._router_only_aduser = None
        self._router_and_service_user = None
        self._router_only_user = None
        self.log = logger.get_log()
        self.config = config_options
        self._default_password = (
                config_options.get('default_password', WebRoutingConfig.DEFAULT_PASSWORD) or
                OptionsSelector.get_custom_password(12, True)
        )
        self._service_master_user = None
        self._service_aduser = None
        self._service_unpreviledged_user = None
        self._service_company_entities = None
        self._service_samluser = None
        self.master_roles = []
        self.cleanup_functions = {}
        self.log.info(f"WebRoutingHelper initialized with options: \n{json.dumps(self.config, indent=4)}")

    # # # # # PROPERTIES + SETUP UTILS # # # # #
    def setup_ad(self, cs: Commcell, ad_creds: dict) -> None:
        """
        util to setup AD to a CS

        Args:
            cs  (Commcell)      -   commcell sdk object
            ad_creds    (dict)  -   see multicommcellconstants.py, WebRoutingConstants.AD_CREDS
                                    for format
        """
        self.log.info(">> Attempting to setup AD")
        cs.domains.refresh()
        if not cs.domains.has_domain(ad_creds['ad_name']):
            self.log.info(f'adding domain {ad_creds['ad_name']}')
            cs.domains.add(
                domain_name=ad_creds['ad_hostname'],
                netbios_name=ad_creds['ad_name'],
                user_name=ad_creds['ad_username'],
                password=ad_creds['ad_password'],
                company_id=0
            )
            self.log.info(">> AD created successfully")
        else:
            self.log.info(">> Given AD already exists")
        cs.domains.get(ad_creds['ad_name']).set_properties({
            "emailSuffixes": [ad_creds['ad_hostname']],
            "username": ad_creds['ad_username'],
            "password": b64encode(ad_creds['ad_password'].encode()).decode()
        })
        self.cleanup_functions[f'delete AD {ad_creds['ad_name']} from {cs.commserv_name}'] = functools.partial(
            cs.domains.delete, ad_creds['ad_name']
        )

    @property
    def service_master_user(self):
        """
        master user in service commcell
        """
        if not self._service_master_user:
            un = self.config.get('service_master_user', 'test_master_user')
            if not self.mcc.service_cs.users.has_user(un):
                self._service_master_user = self.mcc.service_cs.users.add(
                    un,
                    self.config.get('service_master_email', 'test_master_user@webrouting.test'),
                    f'{un} fullname',
                    password=self._default_password
                )
            else:
                self._service_master_user = self.mcc.service_cs.users.get(un)
                self._service_master_user.update_user_password(
                    self._default_password, self.config.get('service_password', WebRoutingConfig.CS_PASSWORD)
                )
            # give admin mgmt rights by giving master role
            SecurityAssociation(self.mcc.service_cs, self.mcc.service_cs)._add_security_association([{
                "user_name": un,
                "role_name": 'Master'
            }], user=True, request_type='UPDATE')
            # self.mcc.service_cs.users.refresh(mogodb=True, hard=True)
            self.cleanup_functions[f'delete user {un}'] = functools.partial(
                self.mcc.service_cs.users.delete, un, 'admin'
            )
        return self._service_master_user

    @property
    def service_aduser(self):
        """
        ad user in service commcell
        """
        if not self._service_aduser:
            self.log.info(">> Attempting to setup AD")
            self.mcc.service_cs.domains.refresh()
            ad_creds = self.config.get('service_ad_creds', WebRoutingConfig.SERVICE_AD_CREDS)
            login_name = f"{ad_creds['ad_name']}\\{ad_creds['master_username']}"
            self.setup_ad(self.mcc.service_cs, ad_creds)
            if self.mcc.service_cs.users.has_user(login_name):
                self._service_aduser = self.mcc.service_cs.users.get(login_name)
            else:
                self._service_aduser = self.mcc.service_cs.users.add(ad_creds['master_username'], ad_creds['master_email'],
                                                                 domain=ad_creds['ad_name'])
            # give admin mgmt rights by giving master role
            if 'ad_user' in self.master_roles:
                SecurityAssociation(self.mcc.service_cs, self.mcc.service_cs)._add_security_association([{
                    "user_name": login_name,
                    "role_name": 'Master'
                }], user=True, request_type='UPDATE')
                # self.mcc.service_cs.users.refresh(mogodb=True, hard=True)
        return self._service_aduser

    @property
    def service_unpreviledged_user(self):
        """
        user without rights in service commcell
        """
        if not self._service_unpreviledged_user:
            un = self.config.get('service_unpreviledged_user', 'test_unpreviledged_user')
            if not self.mcc.service_cs.users.has_user(un):
                self._service_unpreviledged_user = self.mcc.service_cs.users.add(
                    un,
                    self.config.get('service_unpreviledged_email', 'test_unpreviledged_user@webrouting.test'),
                    f'{un} fullname',
                    password=self._default_password
                )
            else:
                self._service_unpreviledged_user = self.mcc.service_cs.users.get(un)
                self._service_unpreviledged_user.update_user_password(
                    self._default_password, self.config.get('service_password', WebRoutingConfig.CS_PASSWORD)
                )
            self.cleanup_functions[f'delete user {un}'] = functools.partial(
                self.mcc.service_cs.users.delete, un, 'admin'
            )
            # No rights are given
            # self.mcc.service_cs.users.refresh(mogodb=True, hard=True)
            if self.mcc.router_cs.users.has_user(un):
                self.mcc.router_cs.users.delete(un)
        return self._service_unpreviledged_user

    @property
    def service_company_entities(self):
        """
        fresh new company, tenant user and tenant admin in service commcell
        """
        if not self._service_company_entities:
            comp_name = self.config.get('comp_name', f"service_company {get_random_string(5)} {get_random_string(5)}")
            comp_alias = self.config.get('comp_alias', "".join([token[0] for token in comp_name.split(' ')]))
            if self.mcc.service_cs.organizations.has_organization(comp_name):
                raise Exception("No reusing companies, provide fresh non existing company name")
            org = self.mcc.service_cs.organizations.add(
                comp_name,
                f"{comp_alias}_admin@{comp_alias}.com",
                f"{comp_alias}_admin",
                comp_alias
            )
            self.cleanup_functions[f'delete company {comp_name}'] = functools.partial(
                self.mcc.service_cs.organizations.delete, comp_name
            )
            self.mcc.service_cs.users.refresh(hard=True, mongodb=True)
            tenant_admin = self.mcc.service_cs.users.get(f"{comp_alias}\\{comp_alias}_admin")
            tenant_admin.update_user_password(self._default_password,
                                              self.config.get('service_password', WebRoutingConfig.CS_PASSWORD))
            tenant_user = self.mcc.service_cs.users.add(
                f"{comp_alias}_user", f"{comp_alias}_user@{comp_alias}.com", f"{comp_alias}_user full name",
                comp_alias, self._default_password, local_usergroups=[f"{comp_alias}\\Tenant Users"]
            )
            self.mcc.service_cs.users.refresh(hard=True, mongodb=True)
            self._service_company_entities = [org, tenant_admin, tenant_user]
        return self._service_company_entities

    @property
    def service_samluser(self):
        """
        fresh new saml user in service commcell
        """
        if not self._service_samluser:
            saml_details = self.config.get('saml_creds', WebRoutingConfig.SAML_CREDS)
            login_name = saml_details['app_name'] + "\\" + saml_details['saml_username']
            if not self.mcc.service_cs.identity_management.has_identity_app(saml_details['app_name']):
                saml_helper = SamlHelperMain(self.mcc.service_cs)
                saml_helper.create_saml_app(
                    appname=saml_details['app_name'],
                    description=saml_details.get('description', 'Automated SAML App'),
                    idpmetadata_xml_path=saml_details['idpmetadata_xml_path'],
                    email_suffixes=saml_details.get('email_suffixes')
                )
                self.log.info(">> SAML App created successfully")
            else:
                self.log.info(">> SAML App already exists")
            self.cleanup_functions[f'delete saml app {saml_details['app_name']}'] = functools.partial(
                self.mcc.service_cs.identity_management.delete_saml_app, saml_details['app_name']
            )
            if self.mcc.service_cs.users.has_user(login_name):
                self._service_samluser = self.mcc.service_cs.users.get(login_name)
            else:
                self._service_samluser = self.mcc.service_cs.users.add(
                    saml_details['saml_username'], saml_details['saml_email'], domain=saml_details['app_name']
                )

            def clean_saml_user(email, app_name):
                self.mcc.service_cs.identity_management.delete_saml_app(app_name)
                time.sleep(self.wait_time)
                self.mcc.service_cs.users.refresh()
                self.mcc.service_cs.users.delete(email, 'admin')

            self.cleanup_functions[f'delete saml app {saml_details['app_name']}'] = functools.partial(
                clean_saml_user, saml_details['saml_email'], saml_details['app_name']
            )

            if 'saml_user' in self.master_roles:
                SecurityAssociation(self.mcc.service_cs, self.mcc.service_cs)._add_security_association([{
                    "user_name": login_name,
                    "role_name": 'Master'
                }], user=True, request_type='UPDATE')
                # self.mcc.service_cs.users.refresh(mogodb=True, hard=True)
        return self._service_samluser

    @property
    def router_only_user(self):
        """
        a user who is only present in router
        """
        if not self._router_only_user:
            un = self.config.get('router_only_user', 'test_router_only_user')
            if not self.mcc.router_cs.users.has_user(un):
                self._router_only_user = self.mcc.router_cs.users.add(
                    un,
                    self.config.get('router_only_email', 'test_router_only_user@webrouting.test'),
                    f'{un} fullname',
                    password=self._default_password
                )
            else:
                self._router_only_user = self.mcc.router_cs.users.get(un)
                self._router_only_user.update_user_password(
                    self._default_password, self.config.get('router_password', WebRoutingConfig.CS_PASSWORD)
                )
            if self.mcc.service_cs.users.has_user(un):
                self.mcc.service_cs.users.delete(un)
        return self._router_only_user

    @property
    def router_and_service_user(self):
        """
        a user who is present in router and service
        """
        if not self._router_and_service_user:
            un = self.config.get('router_and_service_user', 'test_router_and_service_user')
            for typ, cs in [('router', self.mcc.router_cs), ('service', self.mcc.service_cs)]:
                if not cs.users.has_user(un):
                    self._router_and_service_user = cs.users.add(
                        un,
                        self.config.get('router_and_service_email', 'test_router_and_service_user@webrouting.test'),
                        f'{un} fullname',
                        password=self._default_password
                    )
                else:
                    self._router_and_service_user = cs.users.get(un)
                    self._router_and_service_user.update_user_password(
                        self._default_password, self.config.get(f'{typ}_password', WebRoutingConfig.CS_PASSWORD)
                    )
        return self._router_and_service_user

    @property
    def router_only_aduser(self):
        """
        ad user who can be in router, not yet imported
        """
        if not self._router_only_aduser:
            ad_creds = self.config.get('router_ad_creds', WebRoutingConfig.ROUTER_AD_CREDS)
            login_name = f"{ad_creds['ad_name']}\\{ad_creds['master_username']}"
            if self.mcc.service_cs.domains.has_domain(ad_creds['ad_name']):
                self.mcc.service_cs.domains.delete(ad_creds['ad_name'])
            if self.mcc.router_cs.domains.has_domain(ad_creds['ad_name']):
                if self.mcc.router_cs.users.has_user(login_name):
                    self.mcc.router_cs.domains.delete(ad_creds['ad_name'])
            self.setup_ad(self.mcc.router_cs, ad_creds)
            self._router_only_aduser = login_name, ad_creds['master_email']
        return self._router_only_aduser

    @property
    def service_only_aduser(self):
        """
        ad user who can be in service, not yet imported
        """
        if not self._service_only_aduser:
            ad_creds = self.config.get('service_ad_creds', WebRoutingConfig.SERVICE_AD_CREDS)
            login_name = f"{ad_creds['ad_name']}\\{ad_creds['master_username']}"
            if self.mcc.router_cs.domains.has_domain(ad_creds['ad_name']):
                self.mcc.router_cs.domains.delete(ad_creds['ad_name'])
            if self.mcc.service_cs.domains.has_domain(ad_creds['ad_name']):
                if self.mcc.service_cs.users.has_user(login_name):
                    self.mcc.service_cs.domains.delete(ad_creds['ad_name'])
            self.setup_ad(self.mcc.service_cs, ad_creds)
            self._service_only_aduser = login_name, ad_creds['master_email']
        return self._service_only_aduser

    @property
    def router_and_service_aduser(self):
        """
        ad user who can be in both router, and service, not yet imported
        """
        if not self._router_and_service_aduser:
            ad_creds = self.config.get('common_ad_creds', WebRoutingConfig.COMMON_AD_CREDS)
            login_name = f"{ad_creds['ad_name']}\\{ad_creds['master_username']}"
            for cs in [self.mcc.router_cs, self.mcc.service_cs]:
                if cs.domains.has_domain(ad_creds['ad_name']):
                    if cs.users.has_user(login_name):
                        cs.domains.delete(ad_creds['ad_name'])
                self.setup_ad(cs, ad_creds)
            self._router_and_service_aduser = login_name, ad_creds['master_email']
        return self._router_and_service_aduser

    # # # # # VALIDATION UTILS # # # # #
    def validate_entire_sync(self, includes: dict = None, sync_only: list[str] = None) -> None:
        """
        validates all the redirect rules on router from service. domains, rules, authcodes, userspace included

        Args:
            includes    (dict)  -   dict with key 'userspace', 'rules', 'domain' ,'authcodes' with corresponding
                                    value a list of strings to ensure are present in both commcells
            sync_only   (list)  -   list of entities only that must be synced, other entities ignored
        """
        all_synced_rules = self.mcc.router_dbops.get_synced_redirect_rules(self.mcc.service_cs.commserv_name)
        all_synced_rules['userspace'] = self.mcc.router_dbops.get_synced_userspace(self.mcc.service_cs.commserv_name)
        all_service_rules = self.mcc.service_cs._get_all_rules_service_commcell()
        while None in all_service_rules['authcodes']:
            all_service_rules['authcodes'].remove(None)

        if sync_only:
            all_synced_rules = {
                entity: values for entity, values in all_synced_rules.items() if entity in sync_only
            }
            all_service_rules = {
                entity: values for entity, values in all_service_rules.items() if entity in sync_only
            }

        if sync_only:
            self.log.info(f"comparing sync only for {sync_only}")
        else:
            self.log.info(f"comparing all redirect rules")

        if set(all_service_rules['authcodes']).issubset(set(all_synced_rules['authcodes'])):
            # router can have older authcodes, so only validate subset match
            all_service_rules['authcodes'] = all_synced_rules['authcodes']

        errors = get_differences(
            all_synced_rules, all_service_rules, ignore_numeric_type_changes=True, ignore_order=True
        )
        if errors:
            self.log.info(f'synced rules = {all_synced_rules}')
            self.log.info(f'local rules = {all_service_rules}')
            self.log.error(f'Got errors\n{errors}')
            raise Exception('Sync fail, some rules did not sync!')
        self.log.info("all redirect rules synced successfully")
        if includes:
            for rule_type, rules_list in includes.items():
                if not set(rules_list).issubset(set(all_synced_rules[rule_type])):
                    self.log.error("> error! expected rules are missing!")
                    self.log.error(f'synced rules = {all_synced_rules}')
                    self.log.error(f'expected = {includes}')
                    self.log.error(f'failed on {rule_type}')
                    self.log.error(f'expected = {rules_list}')
                    self.log.error(f'synced = {all_synced_rules[rule_type]}')
                    raise Exception('Error, expected rules are missing')
            self.log.info("expected rules are also present")
        self.log.info("all redirect rules validated!")

    def validate_sync(self, retry: int = 5, wait_time: int = 5, **kwargs) -> None:
        """
        Validates sync router to service over period of time while retrying

        Args:
            retry   (int)   -   number of times to retry on failure
            wait_time (int) -   seconds to wait between retries
        """
        self.log.info("validating sync continuously.....")
        for attempt in range(retry):
            try:
                self.log.info(f'attempt {attempt + 1}')
                self.validate_entire_sync(**kwargs)
                self.log.info("sync successfull")
                return
            except Exception as exp:
                if attempt == retry - 1:
                    raise exp
                time.sleep(wait_time)

    def validate_roles(self, router_role: str = None, service_role: str = None) -> None:
        """
        Checks if multicommcell roles are set correctly on both commcells

        Args:
            router_role     (str)   -   name of the role expected in router commcell (from self.ROLE_BITS)
            service_role    (Str)   -   name of the role expected in service commcell (from self.ROLE_BITS)
        """
        errors = []
        self.log.info(f"validating roles:")
        if router_role:
            self.log.info(f"{router_role} for {self.mcc.router_cs.commserv_name}")
            role_in_router = self.mcc.router_dbops.get_globalparam_role()
            if role_in_router & self.ROLE_BITS[router_role] != self.ROLE_BITS[router_role]:
                errors.append(f"router: expected bit {self.ROLE_BITS[router_role]}, got {role_in_router}")
        if service_role:
            self.log.info(f"{service_role} for {self.mcc.service_cs.commserv_name}")
            role_in_service = self.mcc.service_dbops.get_globalparam_role()
            if role_in_service & self.ROLE_BITS[service_role] != self.ROLE_BITS[service_role]:
                errors.append(f"service: expected bit {self.ROLE_BITS[service_role]}, got {role_in_service}")
        if errors:
            self.log.error("roles failed to validate!")
            for error in errors:
                self.log.error(error)
            raise Exception("failed to validate roles!")
        else:
            self.log.info("GxGlobalParam multicommcellroles validated")

    def validate_third_party_app(self, in_router: bool = True, in_service: bool = True) -> None:
        """
        checks if ThirdPartyApp entry is present/absent for given router/service

        Args:
            in_router   (bool)  -   verifies if service GUID row is present in router DB
            in_service  (bool)  -   verifies if router GUID row is present in service DB
        """
        errors = []
        router_guids = self.mcc.router_dbops.get_tpa_apps(3)
        service_guids = self.mcc.service_dbops.get_tpa_apps(3)
        if self.mcc.service_cs.commserv_guid.upper() in router_guids:
            if in_router:
                self.log.info("service guid is present in router, verified")
            else:
                errors.append("APP_TPA entry missing in router!")
        else:
            if not in_router:
                self.log.info("service guid is deleted in router, verified")
            else:
                errors.append("APP_TPA entry not deleted in router!")
        if self.mcc.router_cs.commserv_guid.upper() in service_guids:
            if in_service:
                self.log.info("router guid is present in service, verified")
            else:
                errors.append("APP_TPA entry missing in service!")
        else:
            if not in_service:
                self.log.info("router guid is deleted in service, verified")
            else:
                errors.append("APP_TPA entry not deleted in service!")
        if errors:
            self.log.error("TPA entry validation failed!")
            for error in errors:
                self.log.error(error)
            raise Exception("TPA entry validation failed!")
        else:
            self.log.info("TPA entry verified!")

    def validate_unregistration(self, force=False) -> None:
        """
        Unregisters and validates db cleanups

        Args:
            force   (bool)  -   if True, validates for force unregistration, i.e. does not validate service DB
        """
        self.log.info("> starting post unregistration validations....")
        self.mcc.router_cs.refresh()
        if self.mcc.router_cs.is_commcell_registered(self.mcc.service_cs.commserv_name):
            raise Exception("service commcell could not unregister!")
        self.log.info(f"service commcell [{self.mcc.service_cs.commserv_name}] unregistered successfully")
        self.log.info("validating redirects and user space cleanup")
        all_synced_rules = self.mcc.router_dbops.get_synced_redirect_rules(self.mcc.service_cs.commserv_name)
        all_synced_rules['userspace'] = self.mcc.router_dbops.get_synced_userspace(self.mcc.service_cs.commserv_name)
        if all_synced_rules != {
            'rules': [],
            'domains': [],
            'authcodes': [],
            'userspace': []
        }:
            self.log.error(f'got synced rules = {all_synced_rules}')
            raise Exception("cleanup failed! some rules are present still in DB!")
        self.log.info("validating multiCommcellRole ---")
        expected_router_role = "ROUTERCOMMCELL"
        expected_service_role = "NOTCONFIGURED"
        if len(self.mcc.router_dbops.get_tpa_apps(3)) <= 1:  # if there are no service commcells
            expected_router_role = "NOTCONFIGURED"  # router role should no longer be present
        if force or len(self.mcc.service_dbops.get_tpa_apps(3)) >= 2:  # if service has other routers, or force unreg case
            expected_service_role = "ROUTERCOMMCELL_SERVICECOMMCELL"  # service role must remain

        self.validate_roles(router_role=expected_router_role, service_role=expected_service_role)
        self.log.info("validating TPA entry cleanup ---")
        self.validate_third_party_app(in_router=False, in_service=force or False)

    def get_api_redirects(self, user_or_mail: str, repeats: int = 1) -> tuple[list[float], list[str]]:
        """
        Gets the redirects for given user or mail via API call

        Args:
            user_or_mail    (str)   -   username or email to pass as input
            repeats (int)           -   number of times to repeat to collect response times

        Returns:
            redirect_times  (list)  -   list of response times for each API call
            redirect_resp   (list)  -   the redirects list in response of API call
        """
        _ = self.mcc.router_cs
        redirect_times = []
        redirect_resp = None
        for _ in range(repeats):
            start = time.time()
            res = self.mcc.router_cs.get_eligible_service_commcells(user_or_mail)
            if redirect_resp and redirect_resp != res:
                self.log.error(f"Got till now = {redirect_resp}")
                self.log.error(f"Got redirect now = {res}")
                raise Exception("got inconsistent redirects from API!")
            end = time.time()
            redirect_resp = res
            redirect_times.append(end - start)
        return redirect_times, redirect_resp

    def get_dbsp_redirects(self, user_or_mail: str, repeats: int = 1) -> tuple[list[float], list[str]]:
        """
        Gets the redirects for given user or mail via Stored Proc call

        Args:
            user_or_mail    (str)   -   username or email to pass as input
            repeats (int)           -   number of times to repeat to collect response times

        Returns:
            redirect_times  (list)  -   list of response times for each DB call
            redirect_resp   (list)  -   the redirects list in response of DB call
        """
        _ = self.mcc.router_dbops
        redirect_times = []
        redirect_resp = None
        for _ in range(repeats):
            start = time.time()
            res = self.mcc.router_dbops.get_user_redirects_from_sp(user_or_mail)
            if redirect_resp and redirect_resp != res:
                self.log.error(f"Got till now = {redirect_resp}")
                self.log.error(f"Got redirect now = {res}")
                raise Exception("got inconsistent redirects from StoredProc!")
            end = time.time()
            redirect_resp = res
            redirect_times.append(end - start)
        return redirect_times, redirect_resp

    def get_ui_redirects(self, user_or_mail: str, repeats: int = 1) -> tuple[list[float], list[str]]:
        """
        Gets the redirects for given user or mail via UI login page

        Args:
            user_or_mail    (str)   -   username or email to pass as input
            repeats (int)           -   number of times to repeat to collect UI load times

        Returns:
            redirect_times  (list)  -   list of load times after username entered
            redirect_resp   (list)  -   the redirects handled by UI
        """
        browser = None
        admin_console = None
        self.log.info("Initializing browser object")
        try:
            browser = BrowserFactory().create_browser_object()
            browser.open()
            admin_console = AdminConsole(browser, self.mcc.router_cs.webconsole_hostname)
            redirect_times = []
            redirect_resp = None
            for _ in range(repeats):
                admin_console._open_sso_disabled_login_page()
                redirect_list = LoginPage(admin_console).get_redirects(user_or_mail)
                if redirect_resp and redirect_resp != redirect_list[1]:
                    self.log.error(f"Got till now = {redirect_resp}")
                    self.log.error(f"Got redirect now = {redirect_list[1]}")
                    raise Exception("got inconsistent redirects in UI!")
                redirect_resp = redirect_list[1]
                redirect_times.append(redirect_list[0])
            return redirect_times, redirect_resp
        finally:
            AdminConsole.logout_silently(admin_console)
            Browser.close_silently(browser)

    def get_redirects_stats(self, user_name: str, email: str, repeats: int = 10, methods: list[str] = None) -> dict:
        """
        Collects redirects times and response via API, UI, or DB, and returns stats

        Args:
            user_name   (str)   -   username for user to check redirects
            email       (str)   -   email for user to check redirects
            repeats     (int)   -   number of times to repeat to collect response times
            methods     (list)  -   methods to use to collect responses from ['UI', 'API', 'DB']

        Returns:
            stats   (dict)  -   nested dict with stats like Max, Min, Avg, Redirects for each method used
        """
        stats = {}
        funcs = {
            'UI': lambda user_or_mail: self.get_ui_redirects(user_or_mail, 2),
            'API': lambda user_or_mail: self.get_api_redirects(user_or_mail, repeats),
            'DB': lambda user_or_mail: self.get_dbsp_redirects(user_or_mail, repeats)
        }
        if methods is None:
            methods = ['UI', 'API', 'DB']
        for key in list(funcs.keys()):
            if key not in methods:
                del funcs[key]

        for inp_val in [user_name, email]:
            this_input_stats = {}
            for key, redirect_method in funcs.items():
                resp_times, response = redirect_method(inp_val)
                this_input_stats[key] = {
                    'Max': max(resp_times),
                    'Min': min(resp_times),
                    'Avg': sum(resp_times) / len(resp_times),
                    'Redirects': sorted(response)
                }
            stats[inp_val] = this_input_stats
        return stats

    # # # # # TEST STEPS # # # # #
    def registration_test(self, case='default', retry: int = 5, wait_time: int = None) -> None:
        """
        Performs registration test for different users and unregistration validation

        Args:
            case    (str)   -   the case to test, see WebRoutingHelper.registration_cases
            retry   (int)   -   number of retries to attempt validation on failure
            wait_time  (int)-   how long to wait between retry attempts
        """
        if wait_time is None:
            wait_time = self.wait_time
        if case not in self.registration_cases:
            raise Exception(f"invalid case {case} | choose from {self.registration_cases}")
        self.log.info(f">>> Starting registration Test case = {case}")
        if self.mcc.router_cs.is_commcell_registered(self.mcc.service_cs.commserv_name):
            self.log.info("> unregistering service commcell since already registered")
            self.mcc.router_cs.unregister_commcell(self.mcc.service_cs.commserv_name)
            self.validate_unregistration()
        self.log.info("> existing registration cleared, can proceed with test")

        reg_name = self.mcc.service_cs.commcell_username
        reg_pass = self._default_password

        if case not in ['invalid_creds', 'invalid_permissions', 'service_down']:  # positive cases
            if case == 'default':
                reg_pass = self.config.get('service_password', WebRoutingConfig.CS_PASSWORD)
            elif case == 'default_email':
                reg_name = self.mcc.service_cs.users.get(reg_name).email
                reg_pass = self.config.get('service_password', WebRoutingConfig.CS_PASSWORD)
            elif case == 'master_username':
                reg_name = self.service_master_user.user_name
            elif case == 'master_email':
                reg_name = self.service_master_user.email
            elif case == 'ad_master_username':
                reg_name = self.service_aduser.user_name
            elif case == 'ad_master_email':
                reg_name = self.service_aduser.email

            self.log.info(f"> attempting registration to {self.mcc.service_cs.commserv_hostname} as {reg_name}, {reg_pass}")
            self.mcc.router_cs.register_commcell(
                self.mcc.service_cs.commserv_hostname, True, reg_name, reg_pass)
            self.log.info("> registration successful")
            self.validate_sync(retry, wait_time=wait_time)
            self.validate_roles(router_role="ROUTERCOMMCELL", service_role="ROUTERCOMMCELL_SERVICECOMMCELL")
            self.validate_third_party_app(in_router=True, in_service=True)

        else:  # negative cases
            hostname = self.mcc.service_cs.commserv_hostname
            expected_error = 'username/password are incorrect'
            if case == 'invalid_creds':
                reg_pass = 'invalid_paswd_cannot_exist'
            elif case == 'invalid_permissions':
                reg_name = self.service_unpreviledged_user.user_name
                expected_error = 'insufficient permissions'
            elif case == 'service_down':
                hostname = "unreachable_cs"
                expected_error = 'unable to verify'
            try:
                self.log.info(f"> attempting registration to {hostname} as {reg_name}, {reg_pass}")
                self.mcc.router_cs.register_commcell(
                    hostname, True, reg_name, reg_pass)
                raise Exception(f"Registration successful!? No error raised for {reg_name}! case {case}")
            except SDKException as exp:
                self.log.info(f"> caught sdk error -> {exp}")
                if expected_error in str(exp).lower():
                    self.log.info(f"> It is expected!")
                else:
                    self.log.error("It is not expected!")
                    raise Exception(f"Got unexpected error message: {exp}")
        self.log.info(">>> Registration test passed!")

    def force_unregister_test(self) -> None:
        """
        Verifies force unregistration test and validates DB
        """
        self.log.info(">>> starting unregistration test")
        self.registration_test('default')
        self.log.info(">>> stopping services on service_cs")
        self.mcc.service_machine.stop_all_cv_services()
        self.log.info(">>> services stopped, trying unregister without force")

        exp_raised = False
        try:
            try:
                self.mcc.router_cs.unregister_commcell(self.mcc.service_cs.commserv_name)
            except Exception as exp:
                exp_raised = True
                self.log.info(f"got error = {exp}")
                if 'is not reachable' in str(exp).lower():
                    self.log.info("it is expected when service down, validation successfull")
                else:
                    self.log.error(exp)
                    raise Exception(f"got unexpected error during unregistration = {exp}")
            if not exp_raised:
                raise Exception("unregister giving no error when services are off!")

            # FORCE UNREGISTER TEST
            self.log.info("trying force unregister")
            self.mcc.router_cs.unregister_commcell(self.mcc.service_cs.commserv_name, force=True)
            self.validate_unregistration(force=True)
            self.log.info("force unregistration validated!")
        finally:
            self.mcc.service_machine.start_all_cv_services()

        self.log.info("re-registering service commcell to clean up properly")
        self.registration_test('default')

    def refresh_test(self, auto_sync: bool = False, wait_time: int = None) -> None:
        """
        Creates new entities in service cs and validates after refresh, that they all are synced

        Args:
            auto_sync   (bool)  -   if True, only validates reverse sync without manual refresh
            wait_time   (int)   -   how long to wait between sync validation retry attempts
        """
        if wait_time is None:
            wait_time = self.wait_time
        self.log.info(">>> starting refresh service commcell test!")
        if not self.mcc.router_cs.is_commcell_registered(self.mcc.service_cs.commserv_name):
            self.log.info('> registering service commcell first, as its not registered already')
            self.registration_test()

        rules_before = self.mcc.service_cs._get_all_rules_service_commcell()
        self.config.update({
            'service_unpreviledged_user': 'refresh_test_service_user',
            'service_unpreviledged_email': 'refresh_test_service_user@test.com',
            'comp_name': 'refresh_test service company',
            'comp_alias': 'rsc',
        })

        try:
            # TODO: FIX ENTITY CREATIONS...USE HELPERS
            new_user = self.service_unpreviledged_user
            new_company, new_company_admin, new_company_user = self.service_company_entities
            new_authcode = new_company.enable_auth_code()
            time.sleep(self.wait_time)
            new_authcode2 = new_company.enable_auth_code()
            new_ad_user = self.service_aduser
            new_saml_user = self.service_samluser
            saml_email = new_saml_user.email.split('@')[1]
            org_email = new_company_admin.email.split('@')[1]
            ad_domain = new_ad_user.user_name.split('\\')[0]
            saml_domain = new_saml_user.user_name.split('\\')[0]

            expected_rules = {
                'userspace': [
                    new_user.user_name, new_company_user.user_name, new_company_admin.user_name,
                    new_ad_user.user_name, new_saml_user.user_name
                ],
                'authcodes': [new_authcode, new_authcode2]
            }
            if not auto_sync:
                expected_rules.update({
                    'domains': [ad_domain, saml_domain, new_company.domain_name],
                    'rules': [saml_email, org_email]
                })

            time.sleep(self.wait_time)
            self.mcc.service_cs.refresh()
            if not auto_sync:
                self.log.info("refreshing/syncing service commcell manually")
                self.mcc.router_cs.service_commcell_sync(self.mcc.service_cs)
            else:
                self.log.info("manual refresh/sync is skipped, checking auto reverse sync")
            self.validate_sync(
                includes=expected_rules, sync_only=(['userspace', 'authcodes'] if auto_sync else None),
                wait_time=wait_time
            )

        finally:
            self.cleanup_all()
            time.sleep(self.wait_time)
            rules_restored = self.mcc.service_cs._get_all_rules_service_commcell()
            if diffs := get_differences(
                    rules_before, rules_restored, ignore_numeric_type_changes=True, ignore_order=True
            ):
                self.log.error(f'got diffs after deleting entities:-\n{diffs}')
                raise Exception("even after entity deletion, all rules did not restore to initial state locally")
            self.log.info("all rules have been cleared as expected")
            self.log.info(">> verified rules locally, now checking router sync")
            self.log.info("refreshing/syncing service commcell manually")
            self.mcc.router_cs.service_commcell_sync(self.mcc.service_cs)
            self.validate_sync(wait_time=wait_time)

    def validate_all_redirects(self, method_preference: str = 'UI', **kwargs) -> tuple[pd.DataFrame, list[str]]:
        """
        Gets the redirects for given user using email, login name, via, API, UI, DB storedproc,
        and returns results

        Args:
            method_preference   (str)   -   the method that takes precedence during validation (UI by default)
            kwargs:
                params to pass to get_redirect_stats

        Returns:
            redirect_stats  (DataFrame) -   pandas dataframe with indexed table of all user types and redirect stats
            errors      (list)          -   list of strings indicating what failed
        """

        def flatten_to_tuple(d, max_level=None):
            dx = pd.json_normalize(d, sep=',', max_level=max_level)
            return {tuple(k.split(',')): v for k, v in dx.to_dict(orient='records')[0].items()}

        self.log.info(">>> starting all redirects test!")

        router_hn = self.mcc.router_cs.webconsole_hostname
        service_hn = self.mcc.service_cs.webconsole_hostname

        all_users = {
            'user_present': {
                'router_only': (self.router_only_user.user_name, self.router_only_user.email,
                                []),
                'service_only': (self.service_unpreviledged_user.user_name, self.service_unpreviledged_user.email,
                                 [service_hn]),
                'router_and_service': (self.router_and_service_user.user_name, self.router_and_service_user.email,
                                       [])
            },
            'user_can_present(ad)': {
                'router_only': self.router_only_aduser + ([],),
                'service_only': self.service_only_aduser + ([service_hn],),
                'router_and_service': self.router_and_service_aduser + ([service_hn, router_hn],)
            }
        }

        self.log.info("> all users entities created! now registering/refreshing!")
        if self.mcc.router_cs.is_commcell_registered(self.mcc.service_cs.commserv_name):
            self.log.info("> refreshing service commcell since already registered")
            self.mcc.router_cs.service_commcell_sync(self.mcc.service_cs)
        else:
            self.log.info("> registering service commcell since not registered")
            self.registration_test()

        self.log.info(">> starting redirects collection!")
        all_user_stats = {}
        errors = []
        for usertype_grouping, usertype_map in all_users.items():
            all_user_stats[usertype_grouping] = {}
            for usertype, user_tuple in usertype_map.items():
                user_stats = self.get_redirects_stats(user_tuple[0], user_tuple[1], **kwargs)
                # check if UI redirects are shown matching expected value
                if set(user_stats[user_tuple[0]][method_preference]['Redirects']) != set(user_tuple[2]):
                    errors.append(f">>> failed for username: {user_tuple[0]} - expected: {user_tuple[2]}")
                    self.log.error(f">>> failed for username: {user_tuple[0]} - expected: {user_tuple[2]}")
                if set(user_stats[user_tuple[1]][method_preference]['Redirects']) != set(user_tuple[2]):
                    errors.append(f">>> failed for user email: {user_tuple[1]} - expected: {user_tuple[2]}")
                    self.log.error(f">>> failed for user email: {user_tuple[1]} - expected: {user_tuple[2]}")
                all_user_stats[usertype_grouping][usertype] = user_stats

        dataframe_format = {k: flatten_to_tuple(v) for k, v in flatten_to_tuple(all_user_stats, 2).items()}
        df = pd.DataFrame.from_dict(dataframe_format, orient='index')
        return df, errors

    def cleanup_all(self) -> None:
        """
        Performs any cleanup for fresh entities created, to keep them fresh for next run
        """
        self.log.info("clean up all called!")
        for cleanup, func in self.cleanup_functions.items():
            self.log.info(f"performing cleanup: <{cleanup}>")
            func()
