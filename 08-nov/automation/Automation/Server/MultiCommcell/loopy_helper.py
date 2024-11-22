# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file for performing loopy test validations

LoopyHelper is the only class defined in this file

-----------------------------------------------------------------------------------------------------

LoopyHelper
===================

    __init__                        --  initializes LoopyHelper object

======================================== API UTILITY FUNCTIONS =============================================

    validate_cloud_in_switcher()            -   validates the API response from commcell switcher API

    validate_membership()                   -   validates membership of synced user to metallic company usergroup

    validate_email_username_redirect()      -   validates /redirectList API using username and email

    has_cloud_key()                         -   util to check if keys are already enabled

    linked_rings()                          -   util to fetch already linked metallic cs details

    setup_cloud()                           -   sets up cloud link for testing user sync

======================================== UI UTILITY FUNCTIONS =============================================

    _setup_browser()                        -   util to get browser for UI tests

    _validate_login_switcher_slo()          -   UI validation to perform login, switch, and verify SLO

    _download_sp_metadata()                 -   gets saml SP metadata from commandcenter

======================================== COMPLETE FLOW TESTS =============================================

    commcell_user_sync_test()               -   tests complete loopy flow for commcell user

    ad_user_sync_test()                     -   tests complete loopy flow for AD user

    saml_user_sync_test()                   -   tests complete loopy flow for SAML user

    commcell_saml_user_test()               -   tests flow of cloud saml user who is also on prem user

"""
import random
import string
from time import sleep
from urllib.parse import urlparse

from cvpysdk.commcell import Commcell

from AutomationUtils import logger
from AutomationUtils.config import get_config
from AutomationUtils.options_selector import OptionsSelector
from Metallic.metallichelper import MetallicHelper
from Server.Security.samlhelper import SamlHelperMain
from Server.routercommcell import RouterCommcell
from Web.AdminConsole.Helper.identity_servers_helper import IdentityServersMain
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep

CONFIG = get_config()


class LoopyHelper:
    """ Helper Class for Loopy UI (and API) Features """

    test_step = TestStep()

    def __init__(self, commcell: Commcell, default_password: str = None) -> None:
        """
        Initializes the LoopyHelper module

        Args:
            commcell (object)           :   commcell object of the onprem cs as MSP admin
            default_password    (str)   :   default password to use for all created users

        Returns:
            None
        """
        self._onprem_username = None
        self._onprem_user_email = None
        self._cloud_admin_password = None
        self._ta_name = None
        self.log = logger.get_log()
        self.__commcell = commcell
        self._cloud_company = None
        self._cloud_cs = None
        self.router_name = commcell.commserv_name
        if default_password:
            self._default_password = default_password
        elif CONFIG.MultiCommcells.Local_users_password:
            self._default_password = CONFIG.MultiCommcells.Local_users_password
        else:
            self._default_password = OptionsSelector.get_custom_password(strong=True)
        self.__routing_commcells = self.__commcell.registered_routing_commcells
        self.metallic_helper = MetallicHelper(self.__commcell)
        self.metallic_routerhelper = None
        self.saml_helper = SamlHelperMain(self.__commcell)
        self.redirect_checks = 10

    # -------------------------------- API UTILS --------------------------------------------
    def validate_cloud_in_switcher(self, cs: Commcell, expect_absence: bool = False) -> None:
        """
        Validates if switcher API returns the linked metallic cloud url

        Args:
            cs  (Commcell)          -   the commcell sdk object of user login to test
            expect_absence  (bool)  -   validates absence of metallic cloud url if set to True

        Returns:
            None

        Raises:
            CVTestStepFailure       -   if failed to validate
        """
        self.log.info(f">> got following commcells: {cs.commcells_for_switching}")
        switcher_dns = [
            csdict.get('commcellAliasName') for csdict in cs.commcells_for_switching.get('serviceCommcell', [])
        ]
        if expect_absence and len(switcher_dns) != 0:
            raise CVTestStepFailure(
                f"expected no switcher API response for user: {cs.commcell_username} but got something!"
            )
        elif not expect_absence and self._cloud_cs.commserv_name not in switcher_dns:
            raise CVTestStepFailure(
                f"expected cloudcs in switcher but not there for user: {cs.commcell_username}"
            )
        self.log.info("> Switcher verified!")

    def validate_membership(self, username: str, group_name: str) -> None:
        """
        Validates if switcher API returns the linked metallic cloud url

        Args:
            username    (str)   -   name of user to verify membership for
            group_name  (str)   -   name of group (excluding domain name) to verify membership in

        Returns:
            None

        Raises:
            CVTestStepFailure       -   if failed to validate
        """
        self.log.info(">>> VALIDATING USER GROUP MEMBERSHIP ON CLOUD/METALLIC")
        self._cloud_cs.refresh()
        group_fullname = f"{self._cloud_company.domain_name}\\{group_name}"
        grp_users = self._cloud_cs.user_groups.get(group_fullname).users
        self.log.info(f">> got following users in group {group_fullname} : {grp_users}")
        if '\\' not in username:
            expected_member = f"{self._cloud_company.domain_name}\\{username}".lower()
        else:
            expected_member = username.lower()
        if expected_member not in grp_users:
            raise CVTestStepFailure(f"Expected user: {expected_member} in {group_fullname} group, not found")

    def validate_email_username_redirect(self, username: str, email: str, expected_commcells: list[str] = None) -> None:
        """
        Validates the redirectList API using given username and email

        Args:
            username    (str)           -   name of user to validate redirect list for
            email       (str)           -   email of user to validate
            expected_commcells  (list)  -   list of commcell displaynames to expect

        Returns:
            None

        Raises:
            CVTestStepFailure       -   if failed to validate
        """
        self.log.info(">>> VALIDATING /RedirectListForUser API")
        if '\\' not in username:
            username = f"{self._cloud_company.domain_name}\\{username}"
        username_result = self.metallic_routerhelper.validate_redirect_list(
            username, expected_commcells
        )
        email_result = self.metallic_routerhelper.validate_redirect_list(
            email, expected_commcells
        )
        self.log.info(f">> Using username ({username}), test status: {username_result}")
        self.log.info(f">> Using email ({email}), test status: {email_result}")
        if not (username_result and email_result):
            raise CVTestStepFailure(f"RedirectListAPI validation failed for user: {username}")

    def has_cloud_key(self, cloud_hostname: str) -> bool:
        """
        Checks if cloudServicesUrl key is already set correctly

        Args:
            cloud_hostname  (str)   -   hostname of cloud/metallic ring

        Returns:
            True    -   if key set already correctly
            False   -   if key is not set correctly
        """
        additional_settings = self.__commcell.get_configured_additional_setting()
        for keydict in additional_settings:
            if keydict.get('displayLabel') == 'metallicCloudServiceUrl':
                if cloud_hostname in keydict.get('value', ''):
                    if keydict.get('enabled') == 1:
                        return True
        return False

    def linked_rings(self) -> dict:
        """
        Gets service commcell details with CLOUD_SERVICE role

        Returns:
            linked_ring (dict)  -   dict with linked csname key and details_dict value

        Raises:
            CVTestCaseInitFailure   -   if multiple linked rings exist
        """
        cloud_commcells = {
            csname: details for csname, details in self.__routing_commcells.items()
            if details.get('commcellRoleString') == 'CLOUD SERVICE'
        }
        if len(cloud_commcells) > 1:
            self.log.error("Found multiple cloud service commcells")
            self.log.error(cloud_commcells)
            raise CVTestCaseInitFailure("There are multiple cloud service commcells registered, no idea how to test "
                                        "in such scenario")
        return cloud_commcells

    def setup_cloud(self, cloud_hostname: str, cloud_admin_username: str,
                    cloud_admin_password: str, company: str = None, **options) -> None:
        """
        Sets up company in Ring/Cloud

        Args:
            cloud_hostname  (str)           -   hostname of cloud cs/ring
            cloud_admin_username    (str)   -   master user of cloud/ring username
            cloud_admin_password    (str)   -   master user cloud/ring password
            company (str)                   -   name of company if already exists,
                                                 else will be created at random
            options:
                company_name    (str)   -   name of company to create with
                company_alias   (str)   -   domain name of company to create
                ta_password     (str)   -   password to set for company users

        Returns:
            None

        Raises:
            CVTestCaseInitFailure   -   if any problems during setup
        """
        self._cloud_cs = Commcell(cloud_hostname, cloud_admin_username, cloud_admin_password)
        self._cloud_admin_password = cloud_admin_password
        self.log.info(">>> Checking if already linked")
        linked = self.linked_rings()
        if linked:
            self.log.info(f">> Looks Already linked: {linked}")
            if company:
                self.log.info("> Checking if linked to given company already")
                to_link_guid = self._cloud_cs.organizations.all_organizations_props.get(company, {}).get('GUID')
                linked_guid = self.__commcell.metallic.cloudservices_details.get('cloudServices', [{}])[0] \
                    .get('associatedCompany', {}).get('GUID')
                if to_link_guid.lower() == linked_guid.lower():
                    self.log.info(">> Same GUID already linked, no need to unlink")
                else:
                    self.log.info("> Different GUID, proceeding with unlink")
                    self.log.info(">> Attempting unlink")
                    self.__commcell.metallic.metallic_unsubscribe()
                    self.log.info(">> Unlinked successfully")
        else:
            self.log.info(">>> No linked rings, continuing with test")
        if not self.has_cloud_key(cloud_hostname):
            self.log.info(">>> Fixing Reg Key, different Url is set currently")
            self.metallic_helper.add_CloudServiceUrl(f"{cloud_hostname}/webconsole")
        else:
            self.log.info(">>> Key is already correctly set")

        self.metallic_routerhelper = RouterCommcell(self._cloud_cs, cloud_hostname)

        self.log.info(">>> Preparing Cloud Company")
        if not company:
            random_word1 = ''.join(random.choices(string.ascii_lowercase, k=6))
            company_name = options.get('company_name') or f'auto_company loopy {random_word1}'
            company_alias = options.get('company_alias') or f'alias{random_word1[:3]}'
            self._default_password = options.get('ta_password') or self._default_password
            domain = f'{company_alias}.com'
            tenant_admin = f'{company_alias}_admin'
            self._ta_name = f'{company_alias}\\{tenant_admin}'
            email = f'{tenant_admin}@{domain}'
            self.log.info(f"Creating new company->{company_name}, alias->{company_alias}")
            try:
                self._cloud_company = self._cloud_cs.organizations.add(
                    company_name,
                    email,
                    tenant_admin,
                    company_alias,
                )
            except Exception as exp:
                self.log.error("Company creation failed on Cloud with error")
                self.log.error(exp)
                raise CVTestCaseInitFailure("Company Creation Failed on Cloud during pre-requisite")
            self.log.info("Setting tenant admin creds")
            self._cloud_cs.users.get(self._ta_name).update_user_password(
                self._default_password, cloud_admin_password
            )
            print(f"TA password is set! for {self._ta_name} with {self._default_password}")
            print("trying login to metallic with thhose creds")
            Commcell(self._cloud_cs.webconsole_hostname, self._ta_name, self._default_password)
            self.log.info(">>> Cloud Company setup complete!")
        else:
            self.log.info("Existing company name provided, Collecting pre-requisites")
            try:
                self._cloud_company = self._cloud_cs.organizations.get(company)
            except Exception as exp:
                self.log.error("Could not collect existing company data due to error")
                self.log.error(exp)
                raise CVTestCaseInitFailure("Failed to find existing company details in cloud")

            self.log.info("Setting Tenant Admin")
            company_alias = self._cloud_company.domain_name
            tenant_admin = f'{company_alias}_admin'
            ta_name = f"{company_alias}\\{tenant_admin}"
            tag_name = f"{company_alias}\\Tenant Admin"
            self._ta_name = ta_name
            if self._cloud_cs.users.has_user(ta_name):
                self.log.info("Tenant Admin already exists, reusing it")
                ta = self._cloud_cs.users.get(ta_name)
                tag = self._cloud_cs.user_groups.get(tag_name)
                if ta_name not in tag.users:
                    self.log.info("user not in tenant admin group, adding to group")
                    ta.add_usergroups([tag_name])
            else:
                self.log.info("Creating tenant admin user")
                self._cloud_company.users.add(
                    user_name=ta_name,
                    email=f'{tenant_admin}@{company_alias}.com',
                    password=self._default_password,
                    local_usergroups=[tag_name],
                    full_name=f"Fullname {tenant_admin}"
                )
            self.log.info("Setup tenant admin successfully")
        self.log.info(">>> Cloud Company With Tenant Admin Creds is Ready!")

    # -------------------------------- UI UTILS ---------------------------------------------
    def _setup_browser(self) -> object:
        """
        Creates browser object for UI tests

        Returns:
            browser -   cvbrowser object for UI testing
        """
        self.log.info("Initializing browser objects.")
        factory = BrowserFactory()
        browser = factory.create_browser_object()
        browser.open()
        return browser

    def _validate_login_switcher_slo(self, **options) -> None:
        """
        Validates UI Login, Commcell Switcher, SLO

        Args:
            options     -   the same keyword arguments to pass to adminconsole.login()

        Returns:
            None

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        self.log.info(f">>> VALIDATING UI LOGIN, SWITCHER, SLO for user {options.get('username')}")
        browser = self._setup_browser()
        admin_console = AdminConsole(browser, self.__commcell.webconsole_hostname)
        admin_console.login(**options)
        on_prem_url = admin_console.current_url()
        self.log.info(">> Attempting to Navigate to metallic via Nav Bar")
        admin_console.navigator.navigate_to_metallic()
        self.log.info(">> Metallic is there in Nav Bar! Good.")
        self.log.info(">> Switching to Metallic via commcell switcher")
        admin_console.navigator.switch_service_commcell("Metallic")
        if not urlparse(admin_console.current_url()).netloc == self._cloud_cs.webconsole_hostname:
            raise CVTestStepFailure("Switcher Redirection Failed for on-prem master group user")
        self.log.info(">> Switch done, navigating to few pages")
        admin_console.navigator.navigate_to_server_groups()
        admin_console.navigator.navigate_to_dashboard()
        admin_console.navigator.navigate_to_jobs()
        self.log.info(">> Attempting Logout to test SLO")
        admin_console.logout()
        if admin_console.driver.title.lower() not in ['logout', 'command center']:
            raise CVTestStepFailure("Logout page not found after attempting Logout")
        self.log.info(">> Checking session on on-prem")
        admin_console.driver.get(on_prem_url)
        sleep(5)
        if admin_console.driver.title != 'Login':
            raise CVTestStepFailure("Login page not found on access on-prem url, session still exists maybe?")
        self.log.info(">>> UI LOGIN, SWITCHER, SLO VALIDATED!")
        browser.close()

    def _download_sp_metadata(self, saml_app: str, **options) -> str:
        """
        Downloads saml_app SP metadata to setup SAML logins

        Args:
            saml_app    (str)   -   name of saml app
            options             -   the same keyword arguments to pass to adminconsole login

        Returns:
            Filepath    (str)   -   OS File path of downloaded Sp metadata XML
        """
        browser = self._setup_browser()
        admin_console = AdminConsole(browser, self.__commcell.webconsole_hostname)
        admin_console.login(**options)
        admin_console.driver.get(
            f'https://{self.__commcell.webconsole_hostname}'
            f'/commandcenter/downloadSPMetadataXml.do?appName={saml_app}'
        )
        sleep(5)
        return admin_console.browser.get_latest_downloaded_file()

    # --------------------------------- USERSPACE SYNC TESTS ---------------------------------
    def commcell_user_sync_test(self, **options) -> tuple[dict, dict]:
        """
        Tests complete loopy flow for commcell user

        Args:
            options:
                username    (str)       -   name of user to create
                email       (str)       -   email for commcell user
                redirect_checks (int)   -   number of API calls to redirect list to populate timing data

        Returns:
            username_data   -   dict with redirect list API timing data when input username
            email_data      -   dict with redirect list API timing data when input email

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        self.log.info(">>> STARTING COMMCELL USER TEST")

        username = options.get('username') or OptionsSelector.get_custom_str('onprem_user')
        email = options.get('email') or f"{username}@loopytest.com"

        self.log.info(f">> Creating User in on-prem: {username}")
        onprem_user = self.__commcell.users.add(
            username, email, password=self._default_password
        )
        self._onprem_username = username
        self._onprem_user_email = email
        self.log.info(">> User created in on prem")

        self.log.info(">>> Checking /MultiCommcellsForUser Switcher API")
        self.log.info("> Logging in as the on prem user")
        onprem_user_sdk = Commcell(self.__commcell.commserv_hostname, username, self._default_password)
        self.validate_cloud_in_switcher(onprem_user_sdk, expect_absence=True)
        self.log.info(">> Adding user to master group")
        onprem_user.add_usergroups(["master"])
        self.log.info("> user added to master group")
        self.log.info(">> Checking /MultiCommcellsForUser Switcher API")
        self.log.info("> refreshing the on prem user login sdk")
        onprem_user_sdk.logout()
        onprem_user_sdk = Commcell(self.__commcell.commserv_hostname, username, self._default_password)
        self.validate_cloud_in_switcher(onprem_user_sdk)
        self.log.info(">>> /MULTICOMMCELLSFORUSER API VALIDATED")

        self._validate_login_switcher_slo(username=username, password=self._default_password)
        self.validate_membership(username, "tenant admin")
        self.log.info(">>> AUTOCREATED USERGROUP MEMBERSHIP VALIDATED")

        self.validate_email_username_redirect(username, email, [self.__commcell.commserv_name])

        self.log.info(">>> COMMCELL USER SYNC TEST PASSED SUCCESSFULLY!!")
        self.log.info(">>> Collecting API Times Data")
        username_data = self.metallic_routerhelper.collect_redirect_times(
            f"{self._cloud_company.domain_name}\\{username}", options.get('redirect_checks') or self.redirect_checks
        )
        email_data = self.metallic_routerhelper.collect_redirect_times(
            email, options.get('redirect_checks') or self.redirect_checks
        )
        return username_data, email_data

    def ad_user_sync_test(self, **options) -> tuple[dict, dict]:
        """
        Tests complete loopy flow for AD user

        Args:
            options:
                redirect_checks (int)   -   number of API calls to redirect list to populate timing data
                ADCreds (dict)          -   dict with AD details
                                            if not given will take from <config.Security.LDAPs.Active_Directory>
                    example:
                        {
                            "NETBIOSName": "...", "DomainName": "...", "UserName": "...", "Password": "...",
                            "UserGroupsToImport": [{"externalgroup": "..."}],
                            "UsersToImport": [{"UserName": "...", "Password": "...", "email": "..."}]
                        }

        Returns:
            username_data   -   dict with redirect list API timing data when input username
            email_data      -   dict with redirect list API timing data when input email

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        self.log.info(">>> STARTING AD USER TEST")
        server_details = options.get('ADCreds') or CONFIG.Security.LDAPs.Active_Directory._asdict()
        if not server_details:
            raise CVTestCaseInitFailure("No AD data given")
        netbios_name = server_details.get('NETBIOSName')
        ext_group = server_details.get('UserGroupsToImport', [{}])[0].get('externalgroup')
        aduser_name = server_details.get('UsersToImport', [{}])[0].get('UserName')
        aduser_pass = server_details.get('UsersToImport', [{}])[0].get('Password')
        aduser_email = server_details.get('UsersToImport', [{}])[0].get('email')
        if not ext_group or not aduser_name or not aduser_pass or not aduser_email:
            raise CVTestCaseInitFailure("Pls ensure AD User and domain group data is given")

        self.log.info(">> Attempting to setup AD")
        if not self.__commcell.domains.has_domain(netbios_name):
            self.__commcell.domains.add(
                domain_name=server_details.get('DomainName'),
                netbios_name=netbios_name,
                user_name=server_details.get('UserName'),
                password=server_details.get('Password'),
                company_id=0
            )
            self.log.info(">> AD created successfully")
        else:
            self.log.info(">> Given AD already exists")

        if self.__commcell.user_groups.has_user_group(f"{netbios_name}\\{ext_group}"):
            self.log.info(">> AD Group already exists")
            adgroup = self.__commcell.user_groups.get(f"{netbios_name}\\{ext_group}")
            if self.__commcell.get_service_commcell_associations(adgroup):
                self.log.info("> Removing association to test absence of switcher")
                self.__commcell.remove_service_commcell_associations(adgroup)
            else:
                self.log.inof("> It is not already associated")
        else:
            self.log.info(f">> Creating AD Group -> {ext_group}")
            adgroup = self.__commcell.user_groups.add(
                ext_group, domain=netbios_name, entity_dictionary={
                    'assoc1': {
                        'commCellName': [self.__commcell.commserv_name],
                        'role': ['Master']
                    }
                }
            )
        self.log.info(">> AD Group setup successfully")

        aduser_name = server_details.get("NETBIOSName") + "\\" + aduser_name
        self.log.info(f">> Checking /MultiCommcellsForUser Switcher API for AD User given {aduser_name}")
        self.log.info("> Logging in as the on prem user ")
        onprem_aduser_sdk = Commcell(self.__commcell.commserv_hostname, aduser_name, aduser_pass)

        self.validate_cloud_in_switcher(onprem_aduser_sdk, expect_absence=True)

        self.log.info(">> Associating the AD User Group: 'ADUserGroup' to Metallic App")
        self.__commcell.add_service_commcell_associations(
            adgroup, self._cloud_cs.commserv_name
        )
        self.log.info("> AD group associated!")
        self.log.info(">> Checking /MultiCommcellsForUser Switcher API")
        self.log.info("> refreshing the on prem user login sdk")
        onprem_aduser_sdk.logout()
        onprem_aduser_sdk = Commcell(self.__commcell.commserv_hostname, aduser_name, aduser_pass)

        self.validate_cloud_in_switcher(onprem_aduser_sdk, expect_absence=False)

        self.log.info(">>> /MULTICOMMCELLSFORUSER API VALIDATED")

        self._validate_login_switcher_slo(username=aduser_name, password=aduser_pass)

        # TODO: VALIDATE IF THE DOMAIN GOT CREATED UNDER COMPANY, ALSO HANDLE CASE WHEN DOMAIN ALREADY EXISTS

        self.validate_membership(aduser_name, "tenant users")

        self.log.info(">>> AUTOCREATED USERGROUP MEMBERSHIP VALIDATED")

        self.validate_email_username_redirect(aduser_name, aduser_email, [self._cloud_cs.commserv_name])
        self.log.info(">>>AD USER SYNC TEST PASSED SUCCESSFULLY!!")
        self.log.info(">>> Collecting API Times Data")
        username_data = self.metallic_routerhelper.collect_redirect_times(
            aduser_name, options.get('redirect_checks') or self.redirect_checks
        )
        email_data = self.metallic_routerhelper.collect_redirect_times(
            aduser_email, options.get('redirect_checks') or self.redirect_checks
        )
        return username_data, email_data

    def saml_user_sync_test(self, **options) -> tuple[dict, dict]:
        """
        Tests complete loopy flow for SAML user

        Args:
            options:
                admin_password  (str)   -   password of on prem admin user to download SAML idp metadata xml
                redirect_checks (int)   -   number of API calls to redirect list to populate timing data
                SAMLCreds (dict)        -   dict with SAML (ADFS) details
                                            if not given will take from <config.MultiCommcells.SAMLCreds>
                    example:
                        {
                            "appname": "...",
                            "idpmetadata_xml_path": "...",
                            "email_suffixes": "...",
                            "UsersToImport": [{"UserName": "...", "Password": "...", "email": "..."}],
                            "ad_host_ip": "...",
                            "ad_machine_user": "...",
                            "ad_machine_password": "..."
                        }

        Returns:
            username_data   -   dict with redirect list API timing data when input username
            email_data      -   dict with redirect list API timing data when input email

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        self.log.info(">>> STARTING SAML USER TEST")
        saml_group_name = 'TestSAMLGroup'
        saml_details = options.get('SAMLCreds') or CONFIG.MultiCommcells.SAMLCreds._asdict()
        if not saml_details:
            raise CVTestCaseInitFailure("No SAML data given")

        saml_username = saml_details.get('UsersToImport', [{}])[0].get('UserName')
        saml_email = saml_details.get('UsersToImport', [{}])[0].get('email')
        saml_password = saml_details.get('UsersToImport', [{}])[0].get('Password')
        if not saml_password or not saml_email or not saml_username:
            raise CVTestCaseInitFailure("No SAML user data provided!")

        self.log.info("> Setting up User group on metallic and on prem")
        saml_ug = self.__commcell.user_groups.add(saml_group_name, entity_dictionary={
            'assoc1': {
                'commCellName': [self.__commcell.commserv_name],
                'role': ['Master']
            }
        })
        self.log.info(f"> {saml_group_name} created on prem")
        self.log.info("> Creating same name User group on metallic")
        self._cloud_cs.user_groups.add(
            saml_group_name, domain=self._cloud_company.domain_name
        )
        self.log.info("> Same named group created on metallic as well")
        self.log.info(">> Attempting to setup SAML (ADFS)")
        if not self.__commcell.identity_management.has_identity_app(saml_details.get('appname')):
            self.saml_helper.create_saml_app(
                appname=saml_details.get('appname'),
                description=saml_details.get('description', 'Automated SAML App'),
                idpmetadata_xml_path=saml_details.get('idpmetadata_xml_path'),
                email_suffixes=saml_details.get('email_suffixes'),
                usergroups=[saml_group_name]
            )
            self.log.info(">> SAML App created successfully")
        else:
            self.log.info(">> SAML App already exists")

        self.log.info(f"> Downloading SP metadata XML")
        spmetadata_xml_path = self._download_sp_metadata(
            saml_details.get('appname'),
            username=self.__commcell.commcell_username,
            password=options.get('admin_password')
        )

        self.log.info("> SP metadata XML downloaded successfully!")
        self.log.info("> Creating trust party entry in AD Machine")
        IdentityServersMain.edit_trust_party_adfs(
            app_name=saml_details.get('appname'),
            ad_host_ip=saml_details.get('ad_host_ip'),
            ad_machine_user=saml_details.get('ad_machine_user'),
            ad_machine_password=saml_details.get('ad_machine_password'),
            sp_metadata_location=spmetadata_xml_path,
            operation="Create"
        )
        self.log.info("> Trust party added in SAML AD Machine")
        self.log.info(">> SAML app setup successfully")

        saml_username = saml_details.get('appname') + '\\' + saml_username
        self.log.info(f">> Checking /MultiCommcellsForUser Switcher API for SAML User given {saml_username}")
        self.log.info("> Logging in as the on prem user ")
        onprem_samluser_sdk = Commcell(self.__commcell.commserv_hostname, saml_username, saml_password)
        self.validate_cloud_in_switcher(onprem_samluser_sdk, expect_absence=True)

        self.log.info(f">> Associating the SAML User Group: '{saml_group_name}' to Metallic App")
        self.__commcell.add_service_commcell_associations(saml_ug, self._cloud_cs.commserv_name)
        self.log.info("> SAML group associated!")
        self.log.info(">> Checking /MultiCommcellsForUser Switcher API")
        self.log.info("> refreshing the on prem user login sdk")
        onprem_samluser_sdk.logout()
        onprem_samluser_sdk = Commcell(self.__commcell.commserv_hostname, saml_username, saml_password)
        self.validate_cloud_in_switcher(onprem_samluser_sdk, expect_absence=False)

        self.log.info(">>> /MULTICOMMCELLSFORUSER API VALIDATED")
        self._validate_login_switcher_slo(username=saml_username, password=saml_password)
        self.validate_membership(saml_username, saml_group_name)
        self.log.info(">>> AUTOCREATED USERGROUP MEMBERSHIP VALIDATED")

        self.validate_email_username_redirect(saml_username, saml_email, [self._cloud_cs.commserv_name])
        self.log.info(">>>SAML USER SYNC TEST PASSED SUCCESSFULLY!!")
        self.log.info(">>> Collecting API Times Data")
        username_data = self.metallic_routerhelper.collect_redirect_times(
            saml_username, options.get('redirect_checks') or self.redirect_checks
        )
        email_data = self.metallic_routerhelper.collect_redirect_times(
            saml_email, options.get('redirect_checks') or self.redirect_checks
        )
        return username_data, email_data

    def commcell_saml_user_test(self, **options) -> tuple[dict, dict]:
        """
        Tests loopy flow for Local + SAML user

        Args:
            options:
                redirect_checks (int)       -   number of API calls to redirect list to populate timing data
                idpmetadata_xml_path (str)  -   str with idpmetadata to add saml app (just for testing redirect)
                                                if not given, will take from <config.MultiCommcells.SAMLCreds>

        Returns:
            username_data   -   dict with redirect list API timing data when input username
            email_data      -   dict with redirect list API timing data when input email

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        self.log.info(">>> STARTING COMMCELL + SAML USER TEST")
        idp_metadata = options.get('idpmetadata_xml_path') or CONFIG.MultiCommcells.SAMLCreds.idpmetadata_xml_path
        app_name = 'TempLoopySAMLApp'
        suffix = self._onprem_user_email.split('@')[1]
        if not self._cloud_cs.identity_management.has_identity_app(app_name):
            self.saml_helper.create_saml_app(
                appname=app_name,
                description='Automated SAML App for commcell + saml user test',
                idpmetadata_xml_path=idp_metadata,
                email_suffixes=[suffix],
            )
            self.log.info(f">> SAML App: {app_name} created successfully on cloud")
        else:
            self.log.info(f">> SAML App {app_name} already exists on cloud")
        self.log.info(f">> SAML app setup successfully with suffix {suffix}")

        self.validate_email_username_redirect(
            self._onprem_username, self._onprem_user_email,
            [self.__commcell.commserv_name, app_name]
        )

        self.log.info(">>> COMMCELL + SAML REDIRECT PASSED SUCCESSFULLY!!")
        self.log.info(">>> Collecting API Times Data")
        username_data = self.metallic_routerhelper.collect_redirect_times(
            f"{self._cloud_company.domain_name}\\{self._onprem_username}",
            options.get('redirect_checks') or self.redirect_checks
        )
        email_data = self.metallic_routerhelper.collect_redirect_times(
            self._onprem_user_email,
            options.get('redirect_checks') or self.redirect_checks
        )
        return username_data, email_data
