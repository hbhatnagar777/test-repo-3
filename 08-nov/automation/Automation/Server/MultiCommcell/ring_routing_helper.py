# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file for performing ring routing related operations

RingRoutingHelper is the only class defined in this file

----------------------------------------------------------------------------------------------------------------------

Constants
=========
COMPANY_LINKS                       --  dict with links from companies page and expected URLs after redirection

ENTITY_LABELS                       --  dict with entity names returned by API and corresponding UI labels

----------------------------------------------------------------------------------------------------------------------

RingRoutingHelper
===================

    __init__                        --  initializes RingRoutingHelper object

======================================== SETUP FUNCTIONS =============================================

    setup_reseller()                --  Sets up a reseller company with associations 

    create_child_company()          --  Sets up child company

    setup_tenant_admin()            --  Sets up tenant admin user and other variables for testing on existing Reseller

    clean_up()                      --  Cleans up all created entities using this helper

    guided_setup_reseller()         --  Assigns plan to reseller and all its dummies, for completing guided setup

    guided_setup_child()            --  Assigns plan to child company, for completing guided setup

    setup_tenant_operator()         --  Sets up Company user as operator to child company

    setup_company_user()            --  Sets up a normal Company user

    complete_guided_setup()         --  Completes guided setup using laptop plan, from the redirected page

======================================== LOGIN UTILS =============================================

    current_commcell()              --  Gets the cvpysdk commcell object of current webpage's commcell

    use_msp_admin()                 --  Relogs as MSP admin user given initially

    use_tenant_admin()              --  Relogs as Tenant Admin user of reseller

    use_tenant_operator()           --  Relogs as Tenant Operator to child company of reseller

    use_tenant_user()               --  Relogs as normal Tenant User of reseller

    use_child_admin()               --  Relogs as Tenant Admin user of child company

======================================== VALIDATION UTILS =============================================

    parse_api_associations()        --  Converts API associations json to comparable format

    parse_ui_associations()         --  Converts UI associations table data to comparable format

    changed_theme()                 --  Gets the changed colors (w.r.t default theme) from given theme

======================================== ASSOCIATION VALIDATIONS =============================================

    setup_associations_page()       --  Sets up service commcells page

    validate_user_suggestions()     --  Validates the user suggestions from UI for given term

    validate_all_associations()     --  Validates all the service commcell associations in table

    validate_entity_associations()  --  Validates service commcell associations for given entity

======================================== COMPANIES LIST VALIDATIONS =============================================

    setup_companies_page()          --  Sets up companies page

    validate_manage_operators()     --  Validates manage operators dialog from companies page

    validate_manage_tags()          --  Validates manage tags dialog from companies page

    validate_entities_summary()     --  Validate entities summary from companies page 

    verify_redirects()              --  Verifies all the redirecting links from companies page

    activate_and_validate()         --  Activates company and validates

    deactivate_and_validate()       --  Deactivates company and validates

    delete_and_validate()           --  Deletes company and validates

    create_and_validate()           --  Creates child company and validates

======================================== RESELLER SYNC VALIDATIONS =============================================

    setup_company_overview()        --  Sets up company overview page

    validate_edit_operators()       --  Validates operators panel in company overview

    validate_edit_contacts()        --  Validates contacts panel in company overview

    validate_edit_tags()            --  Validate tags panel in company overview

    validate_dlp()                  --  Validates Enable Data Privacy toggle in company overview

    validate_autodiscovery()        --  Validates autodiscovery toggle in company overview

    setup_theme_page()              --  Sets up themes page for company level customization

    validate_theme()                --  Validates the theme values in themes page for company level

    validate_visible_theme()        --  Validates the theme colors as is visible in Nav and headers

    validate_associated_commcells() --  Validates the associated commcells panel for Reseller Admin in overview

    validate_sync_properties()      --  Validates the properties displayed in overview page in all commcells for reseller

"""
import copy
import random
import re
import string
import time
from _operator import itemgetter
from itertools import product
from typing import Union
from urllib.parse import urlparse

from AutomationUtils import logger
from AutomationUtils.constants import PERMISSION_ID
from AutomationUtils.options_selector import OptionsSelector
from Server.MultiCommcell.multicommcellconstants import RingRoutingConfig
from Server.MultiCommcell.multicommcellhelper import CommcellSwitcher, MultiCommcellHandler
from Server.MultiCommcell.web_routing_helper import WebRoutingHelper
from Web.Common.cvbrowser import Browser, BrowserFactory

from cvpysdk.commcell import Commcell
from cvpysdk.exception import SDKException
from cvpysdk.organization import Organizations, Organization, RemoteOrganization
from selenium.common.exceptions import NoSuchElementException

from Web.AdminConsole.AdminConsolePages.Companies import Companies
from Web.AdminConsole.AdminConsolePages.CompanyDetails import CompanyDetails
from Web.AdminConsole.AdminConsolePages.service_commcell import ServiceCommcell
from Web.AdminConsole.AdminConsolePages.theme import Theme
from Web.AdminConsole.Setup.getting_started import GettingStarted
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from cvpysdk.security.role import Role
from cvpysdk.security.user import User

COMPANY_LINKS = {
    "edit": "subscriptions/%s",
    "dashboard": "/subscriptions/dashboard/%s",
    "company_link": "subscriptions/%s",
    "configure": "subscriptions/%s",
    "alert": "alertsDefinitions?companyId=%s",
    "role": "roles?companyId=%s",
    "client group": "serverGroups?companyId=%s",
    "user": "users?companyId=%s",
    "user group": "usergroups?companyId=%s",
    "file servers": "fsServers?companyId=%s",
    "plan": "profile?companyId=%s"
}
OPERATOR_ROLE_REDIRECTS = ["dashboard", "company_link"]
NON_ROLE_REDIRECTS = ["configure", "edit"]
ENTITY_LABELS = {
    'alert': ['Alert definitions', 'Alerts definitions'],
    'role': ['Roles', 'Role'],
    'client group': ['Server group', 'Servers group', 'Server groups'],
    'user': ['User', 'Users'],
    'user group': ['User group', 'User groups', 'Users groups'],
    'file server': ['File servers', 'Files servers', 'File server'],
    'plan': ['Plan', 'Plans'],
    'total': ['total']
}


def _force_lower(obj):
    if isinstance(obj, str):
        return obj.lower()
    elif isinstance(obj, list):
        return [_force_lower(elem) for elem in obj]
    elif isinstance(obj, dict):
        for k in obj:
            obj[k] = _force_lower(obj[k])
        return obj


def _compare_list(list_1, list_2):
    return [i for i in list_1 if i not in list_2] == []


def simplify_operators(operators):
    """
    Simplifies the operators list for comparison/addition with other list

    Args:
        operators (list) - list of dicts as returned by organization.operators property

    Returns:
        simple_set (list) - list of dicts sorted and formatted to input format of operators setter property
    """
    simple_set = []
    for operator in operators:
        user = operator.get('user', {}).get('userName')
        user_group = operator.get('userGroup', {}).get('userGroupName')
        role = operator.get('role', {}).get('roleName')
        if role is None or (user is None and user_group is None):
            raise Exception(f"Operators API returning invalid configuration: {operators}")
        operator_dict = {
            'role': role
        }
        if user:
            operator_dict['user'] = user
        if user_group:
            operator_dict['userGroup'] = user_group
        simple_set.append(operator_dict)
    return sorted(simple_set, key=itemgetter('role'))


def simplify_tags(tags):
    """
    Simplifies the tags list for comparison/addition with other list

    Args:
        tags (list) - list of tags as returned by organization.tags property

    Returns:
        simple_tags (list) - list of tags sorted and formatted to input format of tags property setter
    """
    simple_tags = []
    for tag in tags:
        simple_tag = tag.copy()
        del simple_tag['id']
        if simple_tag not in simple_tags:
            simple_tags.append(simple_tag)
    return sorted(simple_tags, key=itemgetter('name'))


class RingRoutingHelperAPI:
    """Helper Class for testing Ring Routing API features"""

    class DBOps(WebRoutingHelper.DBOps):
        # TODO: ADD DB VALIDATIONS
        pass

    def __init__(self, router_cs: Commcell, **options) -> None:
        """
        Initialize instance of the RingRoutingHelperAPI class

        Args:
            router_cs (obj)     -- Commcell object of router/idp

            options:
                -------------- entity options (defaults are randomly set) ---------------
                avoid_enabling_reseller (bool)  --  avoids enabling reseller if given
                avoid_cleanup   (bool)          --  skips cleanup if given
                company  (str)                  --  organization name to test on
                child    (str)                  --  child organization name to test on
                router_password     (str)       --  password for msp admin account in router
                default_password    (str)       --  default password for all created users
                service_commcells   (list)      --  list of service commcells to test on
                idp_commcell        (str)       --  specific idp commcell to use
                workload_commcells   (list)     --  specific workload commcells to use
                child_idp_commcell  (str)       --  specific idp commcell for child
                child_workload_commcells (list) --  specific workloads for child commcell
                plan     (str)                  --  name of laptop plan to associate by default
                -------------- credentials (defaults are from multicommcellconstants.RingRoutingConfig) ---------------

        """
        # TODO: VERIFY RR KEYS PRESENT, AND ALL USERS ASSOCIATED FOR TOKEN GENERATION
        self.log = logger.get_log()
        self._router_commcell = router_cs
        self._company_name = options.get('company')
        self._child_name = options.get('child')
        self._plan_name = options.get('plan', RingRoutingConfig.PLAN)
        self._default_password = (options.get('default_password')
                                  or RingRoutingConfig.DEFAULT_PASSWORD
                                  or OptionsSelector.get_custom_password(15, strong=True))
        self._router_password = options.get('router_password', RingRoutingConfig.CS_PASSWORD)
        self.config = options
        self.msp_router_switcher = CommcellSwitcher(self._router_commcell)

        self._router_listing = self._router_commcell.organizations
        self._router_listing.fanout = True

        self.reseller_idp_as_reseller = None
        self.reseller_idp_switcher = None

        if self._company_name is not None:
            self.reseller_idp_remote_org = self._router_listing.get_remote_org(self._company_name)
            self.reseller_idp_hostname = self.msp_router_switcher.get_service_commcell_props(
                self.reseller_idp_remote_org.homecell)["hostname"]
            self.reseller_workloads_hostnames = [
                self.msp_router_switcher.get_service_commcell_props(cname)["hostname"]
                for cname in self.reseller_idp_remote_org.workloads
            ]
            self.reseller_idp_as_msp = self.msp_router_switcher.get_service_session(self.reseller_idp_hostname)
            self.reseller_idp_local_org = self.reseller_idp_as_msp.organizations.get(self._company_name)
            self.reseller_idp_as_reseller = self._setup_tenant_admin(self.reseller_idp_remote_org)
            self.reseller_idp_switcher = CommcellSwitcher(self.reseller_idp_as_reseller)
            self.setup_plans_for_reseller()

            if self._child_name is not None:
                self._reseller_listing = self.reseller_idp_as_reseller.organizations
                self._reseller_listing.fanout = True

                self.child_idp_remote_org = self._reseller_listing.get_remote_org(self._child_name)
                self.child_idp_hostname = self.reseller_idp_switcher.get_service_commcell_props(
                    self.child_idp_remote_org.homecell)["hostname"]

                self.child_workloads_hostnames = self.child_idp_remote_org.workloads
                self.child_idp_as_reseller = self.reseller_idp_switcher.get_service_session(self.child_idp_hostname)
                self.child_idp_local_org = self.child_idp_as_reseller.organizations.get(self._child_name)
                self._setup_tenant_admin(self.child_idp_remote_org)
                self.setup_plans_for_child()

            else:
                self.child_idp_hostname = (
                        options.get('child_idp_commcell', RingRoutingConfig.CHILD_IDP)
                        or random.choice(self.reseller_workloads_hostnames)
                )
                self.child_idp_hostname = self.msp_router_switcher.get_service_commcell_props(
                    self.child_idp_hostname)["hostname"]
                self.child_workloads_hostnames = (
                        options.get('child_workload_commcells', RingRoutingConfig.CHILD_WORKLOADS) or
                        list(set(self.reseller_workloads_hostnames) - {
                                                      self.child_idp_hostname})
                )
                self.child_workloads_hostnames = [
                    self.msp_router_switcher.get_service_commcell_props(workld)["hostname"]
                    for workld in self.child_workloads_hostnames
                ]
        else:
            service_commcells = set(options.get('service_commcells', RingRoutingConfig.SERVICE_COMMCELLS) or [
                sc.get('hostname') for sc in self.msp_router_switcher.commcell_switcher_props
            ])
            self.reseller_idp_hostname = (
                    options.get('idp_commcell', RingRoutingConfig.RESELLER_IDP)
                    or random.choice(list(service_commcells))
            )
            self.reseller_workloads_hostnames = (
                    options.get('workload_commcells', RingRoutingConfig.RESELLER_WORKLOADS)
                    or list(service_commcells - {self.reseller_idp_hostname})
            )
            self.child_idp_hostname = (
                    options.get('child_idp_commcell', RingRoutingConfig.CHILD_IDP)
                    or random.choice(self.reseller_workloads_hostnames)
            )
            self.child_workloads_hostnames = (
                    options.get('child_workload_commcells', RingRoutingConfig.CHILD_WORKLOADS) or
                    list(set(self.reseller_workloads_hostnames) - {self.child_idp_hostname})
            )
            for csname in self.child_workloads_hostnames + [self.child_idp_hostname]:
                if csname not in self.reseller_workloads_hostnames + [self.reseller_idp_hostname]:
                    raise Exception("Child cannot have workloads or IDP outside Reseller's workloads and IDP!!")

            # replacing by hostname to better identify from other idp commcell's switchers
            # cs name may be different in each service commcell's DB, but hostname should be same
            # todo: maybe switch to guid for guaranteed unique match

            self.reseller_idp_hostname = self.msp_router_switcher.get_service_commcell_props(
                self.reseller_idp_hostname)["hostname"]
            self.reseller_workloads_hostnames = [
                self.msp_router_switcher.get_service_commcell_props(cname)["hostname"]
                for cname in self.reseller_workloads_hostnames
            ]
            self.child_idp_hostname = self.msp_router_switcher.get_service_commcell_props(
                self.child_idp_hostname)["hostname"]
            self.child_workloads_hostnames = [
                self.msp_router_switcher.get_service_commcell_props(workld)["hostname"]
                for workld in self.child_workloads_hostnames
            ]
        self.top_level = self._router_commcell.users.get(self._router_commcell.commcell_username).user_company_name

        self.log.info(">>> initializing ring routing helper ...")
        self.log.info(f'>>> top org level: {self.top_level}')
        self.log.info(f">>> idp = {self.reseller_idp_hostname}, workloads = {self.reseller_workloads_hostnames}")
        self.log.info(f">>> default pwd = {self._default_password}")
        self.reseller_idp_as_msp = self.msp_router_switcher.get_service_session(self.reseller_idp_hostname)

        self.mcc = MultiCommcellHandler(RingRoutingConfig, options, RingRoutingHelperAPI.DBOps)
        # TODO: re-organize commcells management using above handler
        self.created_users = []
        self.created_roles = []
        self.created_companies = []

    def setup_reseller(self, company_name: str = None, company_alias: str = None) -> None:
        """
        Sets up reseller company for further operations

        Args:
            company_name    (str)   -   name of reseller company
            company_alias   (str)   -   alias name for reseller company
        """
        random_word1 = ''.join(random.choices(string.ascii_lowercase, k=6))
        random_word2 = ''.join(random.choices(string.ascii_lowercase, k=6))

        company_name = company_name or f'autocompany {random_word1} {random_word2}'
        company_alias = company_alias or f'alias{random_word1[:2]}{random_word2[:2]}'

        domain = f'{company_alias}.com'
        tenant_admin = f'{company_alias}_admin'
        email = f'{tenant_admin}@{domain}'

        self._company_name = company_name
        self.log.info("-------------- Random Reseller Generated --------------")
        self.log.info(f'Name: {company_name}')
        self.log.info(f'Alias: {company_alias}')
        self.log.info(f'tenant admin email: {email}')
        self.log.info(f'tenant admin login: {company_alias}\\{tenant_admin}')
        self.log.info(f'IDP: {self.reseller_idp_hostname}')
        self.log.info(f'Workloads: {self.reseller_workloads_hostnames}')

        self.log.info(f"Creating as normal company using comet API")
        self.reseller_idp_remote_org = self._router_listing.add_remote_org(
            company_name,
            email,
            tenant_admin,
            company_alias,
            target=self.msp_router_switcher.get_service_commcell_props(self.reseller_idp_hostname)['commcellname']
        )
        self.created_companies.append(company_name)
        self.log.info("Company created successfully in service commcell")

        self.reseller_idp_as_msp.organizations.refresh()
        self.reseller_idp_local_org = self.reseller_idp_as_msp.organizations.get(self._company_name)

        if self.config.get('avoid_enabling_reseller'):
            self.log.info("Avoiding enabling reseller step")
        else:
            self.log.info("Enabling Reseller")
            self.reseller_idp_local_org.reseller_enabled = True
            self.log.info("Reseller enabled successfully")

        self.log.info("Setting Tenant Admin Password")
        self.reseller_idp_as_msp.users.get(f"{company_alias}\\{tenant_admin}").update_user_password(
            self._default_password, self._router_password
        )
        self.log.info("Tenant Admin Password set successfully")

        self.log.info("Waiting 5 secs before associating")
        time.sleep(5)

        associations = [
            self.msp_router_switcher.get_service_commcell_props(service_commcell)['displayname']
            for service_commcell in self.reseller_workloads_hostnames
        ]
        self.log.info(f"Associating the reseller to service commcells: {associations}")

        for service_commcell in associations:
            self._router_commcell.add_service_commcell_associations(self.reseller_idp_local_org, service_commcell)
            self.log.info(f"Associated to {service_commcell} successfully")
        self.log.info(f"Association successfully finished. Reseller setup is complete!")

        associations_api_resp = [
            assoc["entity"]["entityName"]
            for assoc in self._router_commcell.get_service_commcell_associations(self.reseller_idp_local_org)
        ]
        if set(associations_api_resp) == set(associations):
            self.log.info("Association verified")
        else:
            self.log.error(f"Association failed! got response: {associations_api_resp}")
            raise Exception("Association Failed!")

        self._router_listing.refresh()
        self.reseller_idp_remote_org = self._router_listing.get_remote_org(self._company_name)
        api_workload_commcell_names = [
            self.msp_router_switcher.get_service_commcell_props(workload)['displayname']
            for workload in self.reseller_idp_remote_org.workloads
        ]
        if set(api_workload_commcell_names) != set(associations):
            self.log.error(f"Got workload commcells from fanout companies API as :{api_workload_commcell_names}")
            self.log.error(f"Expected: {associations}")
            raise Exception("Company fanout not returning Workload Commcells!")
        else:
            self.log.info("Company fanout API updated with workloads!")

        self.reseller_idp_as_reseller = Commcell(
            self.msp_router_switcher.get_service_commcell_props(self.reseller_idp_hostname)['hostname'],
            commcell_username=f"{company_alias}\\{tenant_admin}",
            commcell_password=self._default_password
        )
        self.reseller_idp_switcher = CommcellSwitcher(self.reseller_idp_as_reseller)
        self.setup_plans_for_reseller()

    def setup_plans_for_reseller(self):
        """
        Sets a plan to reseller company in all its workloads
        """
        if self._plan_name:
            self.log.info("Assigning plan to reseller in all its workloads")
            for cs_hn in self.reseller_workloads_hostnames + [self.reseller_idp_hostname]:
                cs = self.msp_router_switcher.get_service_session(cs_hn)
                cs.organizations.fanout = False
                cs.organizations.refresh()
                reseller_org = cs.organizations.get(self._company_name)
                if self._plan_name not in reseller_org.plans:
                    reseller_org.plans = reseller_org.plans + [self._plan_name]
            self.log.info("Plan successfully assigned, guided setup can be completed easily now")

    def setup_plans_for_child(self):
        """
        Sets a plan to child company in all its workloads
        """
        if self._plan_name:
            self.log.info("Assigning plan to child and in all workloads")
            for cs_hn in self.child_workloads_hostnames + [self.child_idp_hostname]:
                cs = self.reseller_idp_switcher.get_service_session(cs_hn)
                cs.organizations.fanout = False
                cs.organizations.refresh()
                child_org = cs.organizations.get(self._child_name)
                if self._plan_name not in child_org.plans:
                    child_org.plans = child_org.plans + [self._plan_name]
            self.log.info("Plan successfully assigned, guided setup can be completed easily now")

    def setup_laptop_plan(self, plan_name: str) -> None:
        """
        Creates plan using given name on all workloads and service commcells
        which can be used for guided setup solutions
        """
        for cs_hn in self.reseller_workloads_hostnames + [self.reseller_idp_hostname]:
            cs = self.msp_router_switcher.get_service_session(cs_hn)
            if plan_name in cs.plans.all_plans:
                self.log.info(f"laptop plan already exist in {cs_hn}")
            else:
                self.log.info(f"creating laptop plan in {cs_hn}")
                if cs.storage_pools.all_storage_pools:
                    pool = random.choice(list(cs.storage_pools.all_storage_pools))
                else:
                    self.log.info("No storage pools found, creating dummy_pool")
                    if not cs.media_agents.all_media_agents:
                        raise CVTestStepFailure("Cannot setup dummy plan, no media agent installed!")
                    try:
                        drive_letter = cs.commserv_client.install_directory[0]
                        cs.storage_pools.add(
                            'dummy_storage_pool', f'{drive_letter}:\\dummy_storage', cs.commserv_client.client_name
                        )
                    except Exception as exp:
                        self.log.error("Error while adding storage pool, using CS MA, maybe cs doesnt have MA")
                        raise exp
                    self.log.info("Created dummy_storage_pool successfully")
                    pool = 'dummy_storage_pool'

                cs.plans.add(
                    plan_name=plan_name,
                    plan_sub_type='Laptop',
                    storage_pool_name=pool
                )
            self.log.info(f"laptop plan done in {cs_hn}")
        self.log.info(f"Laptop Plans {plan_name} setup successfully on all commcells!")

    def _setup_tenant_admin(self, company: RemoteOrganization) -> Commcell:
        """
        Sets up tenant admin account for given company, and returns IDP session

        Args:
            company (RemoteOrganization)    -   remote_org class of any company on any service commcell

        Returns:
            idp_login   (Commcell)          -   Commcell SDK object of tenant admin logged in
        """
        company_alias = company.domain_name
        domain = f'{company_alias}.com'
        tenant_admin = f'{company_alias}_admin'
        ta_name = f"{company_alias}\\{tenant_admin}"
        ta_grp_name = f"{company_alias}\\Tenant Admin"
        email = f'{tenant_admin}@{domain}'
        msp_session = self.msp_router_switcher.get_service_session(company.homecell)

        if msp_session.users.has_user(ta_name):
            self.log.info("Tenant Admin already exists, reusing it")
            ta = msp_session.users.get(ta_name)
            ta_grp = msp_session.user_groups.get(ta_grp_name)
            if ta_name not in ta_grp.users:
                self.log.info("user not in tenant admin group, adding to group")
                ta.add_usergroups([ta_grp_name])
        else:
            self.log.info("Creating tenant admin user")
            msp_session.users.add(
                user_name=ta_name,
                email=email,
                password=self._default_password,
                local_usergroups=[ta_grp_name],
                full_name=f"Fullname {tenant_admin}"
            )
        self.log.info("Setup tenant admin successfully")

        try:
            reseller_login_idp = Commcell(
                self.msp_router_switcher.get_service_commcell_props(company.homecell)['hostname'],
                commcell_username=ta_name,
                commcell_password=self._default_password
            )
        except SDKException as e:
            if "Username/Password are incorrect" in str(e) or "Account Disabled" in str(e):
                self.log.info(f"Got error: {str(e)}")
                self.log.info("ReSetting Tenant Admin Password")
                msp_session.users.get(ta_name).update_user_password(self._default_password, self._router_password)
                msp_session.users.refresh(mongodb=True, hard=True)
                self.log.info("Tenant Admin Password set successfully. Relogging")
                reseller_login_idp = Commcell(
                    self.msp_router_switcher.get_service_commcell_props(self.reseller_idp_hostname)['hostname'],
                    commcell_username=ta_name,
                    commcell_password=self._default_password
                )
            else:
                raise e
        return reseller_login_idp

    def clean_up(self):
        """
        Deletes association, reseller company, msp users created by this helper from all commcells
        """
        self.log.info(">>> cleanup phase: ")
        if self.config.get('avoid_cleanup'):
            self.log.info("Skipping cleanup as given in inputs")
            return
        if not self._company_name:
            self.log.info("Nothing to clean up")
            return

        if not self.config.get('company'):
            try:
                self.log.info("removing association")
                self._router_commcell.reset_company()
                self._router_commcell.remove_service_commcell_associations(self.reseller_idp_local_org)
                self.log.info("association removed successfully")
            except Exception as exp:
                self.log.error(f"error removing associations: {str(exp)}")
        else:
            self.log.info('reseller company was given by user, so it will not be cleaned')

        for cs_name in self.reseller_workloads_hostnames + [self.reseller_idp_hostname]:
            cs = self.msp_router_switcher.get_service_session(cs_name)
            cs.reset_company()
            cs.organizations.refresh()
            for company in self.created_companies:
                if cs.organizations.has_organization(company.lower()):
                    self.log.info(f"deleting company from {cs_name}")
                    try:
                        cs.organizations.delete(company.lower())
                        self.log.info(f"deleted {company} successfull")
                    except Exception as exp:
                        self.log.error(f'failed to delete {company}: {str(exp)}')
                else:
                    self.log.info("company not present, not deleting")
            self.log.info(f"companies cleaned from {cs_name}")
            cs.users.refresh()
            for username in self.created_users:
                if cs.users.has_user(username):
                    try:
                        cs.users.delete(username, cs.commcell_username)
                        self.log.info(f'deleted user: {username}')
                    except Exception as exp:
                        self.log.error(f'failed to delete user {username}: {str(exp)}')
            self.log.info(f"users cleaned from {cs_name}")
            cs.roles.refresh()
            for rolename in self.created_roles:
                if cs.roles.has_role(rolename):
                    try:
                        cs.roles.delete(rolename)
                        self.log.info(f'deleted role {rolename}')
                    except Exception as exp:
                        self.log.error(f'failed to delete role: {rolename}')
            self.log.info(f"roles cleaned from {cs_name}")

    # RESELLER COMPANY SYNC SETUP UTILS

    def modify_dlp(self, as_reseller: bool = True) -> None:
        """
        Enables DLP property for reseller company

        Args:
            as_reseller (bool)  :   enables using reseller login if True
        """
        reseller_local = self.reseller_idp_local_org
        if as_reseller:
            reseller_local = self.reseller_idp_as_reseller.organizations.get(self._company_name)
            self.log.info(f'Modifying DLP property as {self.reseller_idp_as_reseller.commcell_username}')
        else:
            self.log.info(f'Modifying DLP property as {self.reseller_idp_as_msp.commcell_username}')
        if reseller_local.is_data_encryption_enabled:
            self.log.info("DLP already enabled, testing disable instead...")
            reseller_local.set_data_encryption_enabled(False)
            self.log.info("DLP disabled successfully")
        else:
            reseller_local.set_data_encryption_enabled(True)
            self.log.info("DLP enabled successfully")

    def modify_autodiscovery(self, as_reseller: bool = True) -> None:
        """
        Enables autodiscover property for reseller company

        Args:
            as_reseller (bool)  :   enables using reseller login if True
        """
        reseller_local = self.reseller_idp_local_org
        if as_reseller:
            reseller_local = self.reseller_idp_as_reseller.organizations.get(self._company_name)
            self.log.info(f'Modifying Autodiscovery as {self.reseller_idp_as_reseller.commcell_username}')
        else:
            self.log.info(f'Modifying Autodiscovery as {self.reseller_idp_as_msp.commcell_username}')
        if reseller_local.is_auto_discover_enabled:
            self.log.info("Autodiscover already enabled, testing disable instead")
            reseller_local.disable_auto_discover()
            self.log.info("Autodiscover disabled successfully")
        else:
            reseller_local.enable_auto_discover()
            self.log.info("Autodiscover enabled successfully")

    def setup_company_user(self, as_reseller: bool = True, user_name: str = None, **options) -> User:
        """
        Sets up tenant user for furthur operations

        Args:
            as_reseller     (bool)  -   creates the tenant user as reseller if True
            user_name       (str)   -   name of tenant user
            options:
                workloads       (bool)  -   creates same user in workloads also if True
                tenant_admin    (bool)  -   makes the created user part of tenant admin group if True
                add_contact     (bool)  -   adds created user to company contacts if True

        Returns:
            tenant_user  (User)  -   user object of the user created in idp
        """
        idp = self.reseller_idp_as_msp
        switcher = self.msp_router_switcher
        reseller_local = self.reseller_idp_local_org
        add_contact = options.get('add_contact', False)
        tenant_admin = options.get('tenant_admin', add_contact)
        workloads = options.get('workloads', False)
        if add_contact and not tenant_admin:
            raise Exception("Can only add tenant admins as contact!")

        if not user_name:
            user_name = ["tenant_user_", "tenant_admin_"][int(tenant_admin)]
            if workloads:
                user_name += "everywhere_"
            user_name += str(int(time.time() * 1000))[-5:]

        full_uname = user_name
        if '\\' in user_name:
            user_name = user_name.split('\\')[1]
        if '\\' not in user_name:
            full_uname = self.reseller_idp_local_org.domain_name + '\\' + user_name
        email = f'{user_name}@{self.reseller_idp_local_org.domain_name}.com'

        if as_reseller:
            idp = self.reseller_idp_as_reseller
            switcher = self.reseller_idp_switcher
            reseller_local = self.reseller_idp_as_reseller.organizations.get(self._company_name)
            self.log.info(f'Creating new tenant user: {full_uname} - {email} '
                          f'as {self.reseller_idp_as_reseller.commcell_username}')
        else:
            self.log.info(f'Creating new tenant user: {full_uname} - {email} '
                          f'as {self.reseller_idp_as_msp.commcell_username}')
        ug_name = f"{self.reseller_idp_local_org.domain_name}\\{['Tenant Users', 'Tenant Admin'][tenant_admin]}"

        user = idp.users.add(user_name=full_uname, email=email,
                             password=self._default_password,
                             local_usergroups=[ug_name],
                             full_name=f"Fullname {user_name}")
        self.created_users.append(user.user_name)
        if workloads:
            self.log.info("workloads enabled, creating same user on workloads also")
            for commcell_name in self.reseller_workloads_hostnames:
                workload = switcher.get_service_session(commcell_name)
                self.log.info(f"creating user on {workload.commserv_name}")
                workload.users.add(user_name=full_uname, email=email,
                                   password=self._default_password,
                                   local_usergroups=[ug_name],
                                   full_name=f"Fullname {user_name}")
                self.log.info(f"user created successfully in {workload.commserv_name}")
        self.log.info("Tenant User is Successfully Setup")

        if add_contact:
            self.log.info("Adding as contact in IDP")
            reseller_local.contacts = self.reseller_idp_local_org.contacts + [full_uname]
            self.log.info("Tenant Admin added as contact successfully")
        return user

    def setup_msp_user(self, user_name: str = None, **options) -> User:
        """
        Sets up MSP user (top level user) for further operations

        Args:
            user_name       (str)   -   name of user
            options:
                workloads       (bool)  -   created the MSP user in workloads also if True
                tenant_operator (bool)  -   makes the user operator of reseller company if True
                role            (str)   -   name of role to assign if set as operator (default Tenant Operator)

        Returns:
            msp_user    (User)  -   User object of msp user created in IDP
        """
        tenant_operator = options.get('tenant_operator', False)
        rolename = options.get('role', 'Tenant Operator')
        workloads = options.get('workloads', False)

        if not user_name:
            user_name = f"msp_operator_"
            if workloads:
                user_name += "everywhere_"
            user_name += str(int(time.time() * 1000))[-5:]

        email = f'{user_name}@operatingauto.com'

        self.log.info(f'Creating new msp user on company idp: {user_name} - {email}')

        user = self.reseller_idp_as_msp.users.add(user_name=user_name, email=email,
                                                  password=self._default_password,
                                                  full_name=f"Fullname {user_name}")
        self.log.info("User successfully created on idp")
        self.created_users.append(user.user_name)

        if workloads:
            self.log.info("workloads enabled, creating same user on workloads also")
            for sc in self.reseller_workloads_hostnames:
                workload = self.msp_router_switcher.get_service_session(sc)
                self.log.info(f"creating user on {workload.commserv_name}")
                workload.users.add(user_name=user_name, email=email,
                                   password=self._default_password,
                                   full_name=f"Fullname {user_name}")
                self.log.info(f"user created successfully in {workload.commserv_name}")

        self.log.info("MSP User is Successfully Setup")
        if tenant_operator:
            self.log.info("Setting as operator in IDP")
            operator_dict = {
                'role': rolename,
                'user': user.user_name
            }
            self.reseller_idp_local_org.operators = simplify_operators(self.reseller_idp_local_org.operators) + [
                operator_dict]
            self.reseller_idp_local_org.refresh()
            if operator_dict not in simplify_operators(self.reseller_idp_local_org.operators):
                raise Exception("Operator Failed to be added!")
        return user

    def setup_tags(self, tag_name: str = None, tag_value: str = None, as_reseller: bool = True):
        """
        Adds tags to reseller company tags

        Args:
            tag_name    (str)   -   tag name to add
            tag_value   (str)   -   tag value to add
            as_reseller (bool)  -   will add the tags as reseller if True

        Returns:
            None
        """
        seed = str(int(time.time() * 1000))[-5:]
        if not tag_name:
            tag_name = f"tag_name_{seed}"
        if not tag_value:
            tag_value = f"tag_value_{seed}"
        self.log.info(f"Setting tag {tag_name} : {tag_value}")
        idp_org = self.reseller_idp_local_org
        if as_reseller:
            idp_org = self.reseller_idp_as_reseller.organizations.get(self._company_name)
            self.log.info(f"Setting tag {tag_name} : {tag_value} as {self.reseller_idp_as_reseller.commcell_username}")
        else:
            self.log.info(f"Setting tag {tag_name} : {tag_value} as {self.reseller_idp_as_msp.commcell_username}")
        tag_dict = {
            'name': tag_name,
            'value': tag_value
        }
        idp_org.tags = idp_org.tags + [tag_dict]
        idp_org.refresh()
        if tag_dict not in simplify_tags(idp_org.tags):
            raise Exception("Tag failed to be added!")
        self.log.info("tags set on idp successfully")

    def setup_role(self, as_reseller: bool = True, role_name: str = None, **options) -> Role:
        """
        Sets up new role/roles for further test

        Args:
            as_reseller (bool)  -   creates the role as reseller at company level if True
                                    (role in idp will always be created at reseller level)
            role_name   (str)   -   name of role to create
            options:
                permissions (list)  -   list of permission to create the role with as given to Roles object
                workloads   (bool)  -   will create role in workloads also if True

        Returns:
            role (Role) -   Role object of role created in idp
        """
        permissions = options.get('permissions', [])
        workloads = options.get('workloads', False)
        idp = self.reseller_idp_as_reseller
        switcher = self.msp_router_switcher

        if not role_name:
            role_name = ["msp_role_", "company_role_"][int(as_reseller)]
            if workloads:
                role_name += "everywhere_"
            role_name += str(int(time.time() * 1000))[-5:]

        if not permissions:
            permissions = self.get_random_permissions()

        if as_reseller:
            switcher = self.reseller_idp_switcher
            self.log.info(f'Creating Role : {role_name} as {self.reseller_idp_as_reseller.commcell_username}')
        else:
            self.log.info(f'Creating Role : {role_name} as {self.reseller_idp_as_msp.commcell_username}')
        self.log.info(f'With permissions: {permissions}')
        role = idp.roles.add(rolename=role_name, permission_list=permissions)
        self.created_roles.append(role.role_name)

        if workloads:
            for cs_name in self.reseller_workloads_hostnames:
                cs = switcher.get_service_session(cs_name)
                self.log.info(f'creating same role in {cs.commserv_name}')
                cs.roles.add(role_name, self.get_random_permissions())
        self.log.info('roles setup successfully')

        if as_reseller:
            self.log.info("Validating Company Role")
            role_company = self.reseller_idp_as_reseller.roles.get(role_name).company_name.lower()
            if not (role_company == self._company_name.lower()
                    or role_company == self.reseller_idp_local_org.domain_name.lower()):
                raise Exception(f'Role shows tagged to company {role_company}')

            if workloads:
                for cs_name in self.reseller_workloads_hostnames:
                    cs = switcher.get_service_session(cs_name)
                    role_company = cs.roles.get(role_name).company_name.lower()
                    if not (role_company == self._company_name.lower()
                            or role_company == self.reseller_idp_local_org.domain_name.lower()):
                        raise Exception(
                            f'Role shows tagged to company {role_company} in workload {cs.commserv_name}')
            self.log.info('Company Roles Validated')
        return role

    def setup_theme(self, as_reseller: bool = True, theme_dict: dict = None) -> dict:
        """
        Sets up new company level theme to verify sync

        Args:
            as_reseller (bool)  -   sets the theme as reseller if True
            theme_dict  (dict)  -   the theme to set in given format
                                    Example:
                                    {
                                        loginAndBannerBg: '#0B2E44',
                                        headerColor: '#DDE5ED',
                                        headerTextColor: '#0B2E44',
                                        navBg: '#FFFFFF',
                                        navIconColor: '#0b2e44',
                                        pageHeaderText: '#0B2E44',
                                        actionBtnBg: '#0B2E44',
                                        actionBtnText: '#eeeeee',
                                        linkText: '#4B8DCC',
                                        iconColor: '#0B2E44'
                                    }

        Returns:
            theme_dict  (dict)  -   the theme set
        """
        idp = self.reseller_idp_as_msp

        if not theme_dict:
            theme_dict = self.get_random_theme()

        if as_reseller:
            idp = self.reseller_idp_as_reseller

        self.log.info(f'Setting Theme : {theme_dict} as {idp.commcell_username}')

        idp.organizations.get(self._company_name).company_theme = theme_dict
        themes_returned = idp.organizations.get(self._company_name).company_theme
        theme_diff = self.compare_themes(theme_dict, themes_returned)
        if theme_diff:
            self.log.error(f"set theme {theme_dict}")
            self.log.error(f"returned theme: {themes_returned}")
            raise Exception(f"Theme setup failed on  {theme_diff}")

        self.log.info("Theme set successfully")

        return theme_dict

    # RESELLER COMPANY SYNC VALIDATIONS

    def verify_sync_props(self) -> bool:
        """
        Verifies the 6 properties of reseller from IDP are synced to Workloads

        Returns:
            bool    -   True if properties are synced, false otherwise
        """
        self.reseller_idp_local_org.refresh()
        flag = False
        idp_theme = self.reseller_idp_local_org.company_theme
        idp_autodiscovery = self.reseller_idp_local_org.is_auto_discover_enabled
        idp_dlp = self.reseller_idp_local_org.is_data_encryption_enabled
        idp_operators = self.reseller_idp_local_org.operators
        idp_contacts = self.reseller_idp_local_org.contacts
        idp_tags = self.reseller_idp_local_org.tags

        for cs_name in self.reseller_workloads_hostnames:
            cs = self.msp_router_switcher.get_service_session(cs_name)
            company_dummy = cs.organizations.get(self._company_name)
            self.log.info(F"-----VERIFYING SYNC ON {cs.commserv_name}------")
            synced_theme = company_dummy.company_theme
            synced_autodiscovery = company_dummy.is_auto_discover_enabled
            synced_dlp = company_dummy.is_data_encryption_enabled
            synced_operators = company_dummy.operators
            synced_contacts = company_dummy.contacts
            synced_tags = company_dummy.tags

            if not idp_theme == synced_theme:
                self.log.error(f"IDP Theme: {idp_theme}")
                self.log.error(f"Workload Theme: {synced_theme}")
                self.log.error("Theme Sync Failed")
                flag = True

            if not synced_autodiscovery == idp_autodiscovery:
                self.log.error("Autodiscovery sync failed")
                flag = True

            if not synced_dlp == idp_dlp:
                self.log.error("DLP sync failed")
                flag = True

            if not simplify_tags(synced_tags) == simplify_tags(idp_tags):
                self.log.error("tags sync failed")
                self.log.error(f"synced: {simplify_tags(synced_tags)}")
                self.log.error(f"idp: {simplify_tags(idp_tags)}")
                flag = True

            if not synced_contacts == idp_contacts:
                self.log.error("Contacts sync failed")
                self.log.error(f"synced: {synced_contacts}")
                self.log.error(f"idp: {idp_contacts}")
                flag = True

            if not simplify_operators(idp_operators) == simplify_operators(synced_operators):
                self.log.error(f"Operators sync failed")
                self.log.error(f"synced: {simplify_operators(synced_operators)}")
                self.log.error(f"idp: {simplify_operators(idp_operators)}")
                flag = True

            self.log.info(f"Sync check completed in {cs.commserv_name}")

        if not flag:
            self.log.info("Properties Sync Verified")
            return True
        else:
            return False

    def verify_sync_continous(self, poll: int = 30, timeout: int = 150) -> None:
        """
        Checks for property sync continuously

        Args:
            poll (int)      -   how often in seconds to check properties sync (default: 30 sec)
            timeout (int)   -   how long in seconds to perform properties check (default: 600 sec)

        Returns:
            None    -   Once properties sync is verified, else raises exception after timeout

        Raises:
              Exception -   if failed to sync within given timeout
        """
        start = time.time()
        while not time.time() - start >= timeout:
            if self.verify_sync_props():
                return
            else:
                self.log.info(f"Property sync failed, waiting {poll} secs")
                time.sleep(poll)
        else:
            raise Exception(f"Property Sync Failed to Match within {timeout} secs")

    # RESELLER CHILD FANOUT API CRUD TEST

    def create_child_company(self, company_name: str = None, company_alias: str = None) -> None:
        """
        Creates child company remotely with given parameters and validates in workload

        Args:
            company_name    (str)   -   name of child company
            company_alias   (str)   -   alias name for child company
        """
        random_word1 = ''.join(random.choices(string.ascii_lowercase, k=6))
        random_word2 = ''.join(random.choices(string.ascii_lowercase, k=6))

        company_name = company_name or f'autochild {random_word1} {random_word2}'
        company_alias = company_alias or f'childalias{random_word1[:2]}{random_word2[:2]}'

        domain = f'{company_alias}.com'
        tenant_admin = f'{company_alias}_admin'
        email = f'{tenant_admin}@{domain}'

        self._child_name = company_name
        self.log.info("-------------- Random Child Generated --------------")
        self.log.info(f'Name: {company_name}')
        self.log.info(f'Alias: {company_alias}')
        self.log.info(f'child admin email: {email}')
        self.log.info(f'child admin login: {company_alias}\\{tenant_admin}')
        self.log.info(f'IDP: {self.child_idp_hostname}')

        self.log.info(f"Creating child company as reseller using comet API")
        self._reseller_listing = self.reseller_idp_as_reseller.organizations
        self._reseller_listing.fanout = True
        self.child_idp_remote_org = self._reseller_listing.add_remote_org(
            company_name,
            email,
            tenant_admin,
            company_alias,
            target=self.reseller_idp_switcher.get_service_commcell_props(self.child_idp_hostname)['commcellname']
        )
        self.created_companies.append(company_name)
        self.log.info(f"Child company created successfully in {self.child_idp_hostname}")
        self.child_idp_as_reseller = self.reseller_idp_switcher.get_service_session(self.child_idp_hostname)
        self.child_idp_as_reseller.organizations.refresh()
        self.child_idp_local_org = self.child_idp_as_reseller.organizations.get(company_name)
        self.setup_plans_for_child()

    def setup_child_operators(self, test: bool = True) -> tuple[list[User], list[Role]]:
        """
        Creates reseller users and roles for setting as child company operators remotely from idp

        Args:
            test    (bool)  -   Assigns the tenant users as operators of child company with random roles
                                and validates sync if True

        Returns:
            users   (list[User])   -   List of User objects of created tenant user
            role    (list[Role])   -   List of Role objects of created roles

        """
        self.log.info("setting up users and roles created by msp/reseller, and some already present in workload")
        users = [self.setup_company_user(as_reseller=x, workloads=y) for x, y in product([False, True], repeat=2)]
        roles = [self.setup_role(workloads=y) for y in [False, True]]
        self.log.info("users and roles setup successfully")
        if not test:
            return users, roles

        new_operators = []
        i = 0
        for user in users:
            new_operators.append({
                'user': user.user_name,
                'role': roles[i].role_name
            })
            i = (i + 1) % 2
        self.log.info(f"adding operators: {new_operators}")
        self.child_idp_remote_org.operators = simplify_operators(self.child_idp_remote_org.operators) + new_operators

        self.child_idp_remote_org.refresh()
        self.child_idp_local_org.refresh()

        for operator in new_operators:
            if operator not in simplify_operators(self.child_idp_remote_org.operators):
                raise Exception(f"operator {operator} did not get added")

        if simplify_operators(self.child_idp_remote_org.operators) == simplify_operators(
                self.child_idp_local_org.operators):
            self.log.info("Manage operators of child verified from idp as reseller")
        else:
            self.log.error(f"Child operators in idp: {self.child_idp_remote_org.operators}")
            self.log.error(f"Child operators in workload: {self.child_idp_local_org.operators}")
            raise Exception("Manage operators failed from idp")
        return users, roles

    def setup_child_tags(self) -> None:
        """
        Sets the child company tags form workload and idp and verifies sync
        """
        seed = str(int(time.time() * 1000))[-5:]
        tag_dict2 = {
            'name': f"remote_tag_{seed}",
            'value': f"remote_value_{seed}"
        }
        tag_dict1 = {
            'name': f"local_tag_{seed}",
            'value': f"local_value_{seed}"
        }

        self.log.info(f"Adding tag {tag_dict1} locally from workload")
        self.child_idp_local_org.tags = self.child_idp_local_org.tags + [tag_dict1]

        self.log.info(f"Setting tag {tag_dict2} remotely from idp")
        self.child_idp_remote_org.tags = self.child_idp_remote_org.tags + [tag_dict2]

        self.child_idp_local_org.refresh()
        self.child_idp_remote_org.refresh()

        if tag_dict1 not in simplify_tags(self.child_idp_local_org.tags):
            raise Exception(f"Tag {tag_dict1} failed to get added in workload")
        if tag_dict2 not in simplify_tags(self.child_idp_remote_org.tags):
            raise Exception(f"Tag {tag_dict2} failed to get added in idp")

        if not simplify_tags(self.child_idp_local_org.tags) == simplify_tags(self.child_idp_remote_org.tags):
            self.log.error(f"Child tags from idp: {self.child_idp_remote_org.tags}")
            self.log.error(f"Child tags from workload: {self.child_idp_local_org.tags}")
            raise Exception("Tags Sync Failed for child company")

        self.log.info("Manage tags validated for child as reseller")

    def deactivate_child(self) -> None:
        """Deactivates child company and verifies from workload"""
        self.log.info("Deactivating child remotely")
        self.child_idp_remote_org.deactivate()
        self.child_idp_local_org.refresh()
        if not (
                self.child_idp_local_org.is_backup_disabled
                and self.child_idp_local_org.is_login_disabled
                and self.child_idp_local_org.is_restore_disabled
        ):
            raise Exception("Deactivate from idp failed")
        self.log.info("Deactivate child validated from idp as reseller")

    def activate_child(self) -> None:
        """Activates child company and verifies from workload"""
        self.log.info("Activating child remotely")
        self.child_idp_remote_org.activate()
        self.child_idp_local_org.refresh()
        if self.child_idp_local_org.is_backup_disabled \
                or self.child_idp_local_org.is_login_disabled \
                or self.child_idp_local_org.is_restore_disabled:
            raise Exception("Activate from idp failed")
        self.log.info("Activate child validated from idp as reseller")

    def delete_child(self) -> None:
        """Deletes child company and verifies from workload"""
        self._reseller_listing = self.reseller_idp_as_reseller.organizations
        self._reseller_listing.fanout = True
        if not self._reseller_listing.has_organization(self._child_name):
            raise Exception("Child is not visible from IDP!")
        self.log.info("Deleting child remotely")
        self._reseller_listing.delete(self._child_name)
        local_list = self.child_idp_as_reseller.organizations
        for _ in range(10):
            local_list.refresh()
            if not local_list.has_organization(self._child_name):
                self.log.info("Delete child validated from idp as reseller")
                return
            self.log.info("Child still shown in workload, waiting 10 seconds")
            time.sleep(10)
        raise Exception("Delete from idp failed, workload still shows child")

    # EXTEND CHILD TEST

    def get_random_region_country(self, commcell: str) -> tuple[str, str]:
        """Gets random region and country to extend to given commcell"""
        region_mapping = CommcellSwitcher(self.reseller_idp_as_msp).get_region_mapping_info()
        commcell_regions = [region for region in region_mapping if region_mapping[region]['commcell'] == commcell]
        if not commcell_regions:
            raise Exception(f"region mapping returned no regions for commcell: {commcell}")
        random_region = random.choice(commcell_regions)
        cont = region_mapping[random_region]['countries']
        if not cont:
            raise Exception(f"region mapping returned no coutries for region: {random_region}")
        return random_region, random.choice(cont)

    def extend_child(self) -> None:
        """Extends child company and verifies company got created in child workloads"""
        self.log.info(f"Extending child to : {self.child_workloads_hostnames}")
        for child_workload in self.child_workloads_hostnames:
            disp_name = self.reseller_idp_switcher.get_service_commcell_props(child_workload)['displayname']
            region, country = self.get_random_region_country(disp_name)
            self.child_idp_remote_org.extend(region, country, disp_name)
            self.log.info(f"Extended to {disp_name} successfully")
        self.log.info("validating extensions")
        self._reseller_listing.refresh()
        self.child_idp_remote_org = self._reseller_listing.get_remote_org(self._child_name)

        child_workloads = [
            self.msp_router_switcher.get_service_commcell_props(cs)['hostname']
            for cs in self.child_idp_remote_org.workloads
        ]
        if set(child_workloads) == set(self.child_workloads_hostnames):
            self.log.info("extend completed successfully! company autocreated in workloads!")
        else:
            self.log.info(f"extend failed! got workloads: {self.child_idp_remote_org.workloads}")
            raise Exception("extend test failed! child company is not autocreated!")

        self.log.info("testing negative cases:")

        try:
            disp_name = self.reseller_idp_switcher.get_service_commcell_props(
                self.child_idp_hostname)['displayname']
            region, country = self.get_random_region_country(disp_name)
            self.log.info(f"trying extend to own idp commcell -> {disp_name}")
            self.child_idp_remote_org.extend(region, country, disp_name)
            raise Exception("no error message when extend to own idp!")
        except Exception as exp:
            if 'Cannot extend on same commcell' not in str(exp):
                # from line 868 in cvs code: CVWebHandler.MultiCommcell.cs
                raise exp
            else:
                self.log.info("verified error message")
        try:
            disp_name = self.reseller_idp_switcher.get_service_commcell_props(
                self.child_workloads_hostnames[0])['displayname']
            region, country = self.get_random_region_country(disp_name)
            self.log.info(f"trying extend to already extended -> {disp_name}")
            self.child_idp_remote_org.extend(region, country, disp_name)
            raise Exception("no error message when extend to already extended commcell!")
        except Exception as exp:
            if 'Cannot extend.Already extended' not in str(exp):
                # from line 910 in cvs code: CVWebHandler.MultiCommcell.cs
                self.log.warning(str(exp))  # raise exp
            else:
                self.log.info("verified error message")
        self.log.info("negative cases passed, extend verified!")

    @staticmethod
    def get_random_permissions(amount=5):
        """
        Gets list of random permissions without db call

        Args:
            amount  (int)   -   number of permissions

        Returns:
            list    -   list of random permissions
        """
        permissions = list(PERMISSION_ID.values())
        return list(random.sample(permissions, k=amount))

    @staticmethod
    def get_random_theme():
        """
        Returns a random theme

        Returns:
            theme_dict  (dict)  -   dict with random theme ids and colors
        """

        def random_color():
            return '#%02X%02X%02X' % (
                random.randint(100, 255),
                random.randint(100, 255),
                random.randint(100, 255)
            )

        return {color_id: random_color() for color_id in Theme.color_ids_default}

    @staticmethod
    def compare_themes(theme1, theme2):
        """
        compares theme dicts and returns difference

        Returns:
            diff    (dict)  -   dict with keys in theme1 whose values don't match in theme2
        """
        return [key for key in theme1 if theme1[key].lower() != theme2.get(key, '').lower()]


class RingRoutingHelperUI(RingRoutingHelperAPI):
    """ Helper Class for testing Ring Routing UI Features """

    test_step = TestStep()

    def __init__(self, router_cs: Commcell, admin_console: AdminConsole = None, **options) -> None:
        """
        Initializes the RingRoutingHelper module

        Args:
            router_cs (object)          :   commcell object of router/idp
            admin_console (object)      :   Admin console object if browser already created
                                            (can be avoided, browser is handled within class)

            options:
                -------------- entity options (defaults are randomly set) ---------------
                avoid_enabling_reseller (bool)  --  avoids enabling reseller if given
                avoid_cleanup   (bool)          --  skips cleanup if given
                company  (str)                  --  organization name to test on
                child    (str)                  --  child organization name to test on
                router_password     (str)       --  password for msp admin account in router
                default_password    (str)       --  default password for all created users
                service_commcells   (list)      --  list of service commcells to test on
                idp_commcell        (str)       --  specific idp commcell to use
                workload_commcells   (list)     --  specific workload commcells to use
                child_idp_commcell  (str)       --  specific idp commcell for child
                child_workload_commcells (list) --  specific workloads for child commcell
                plan     (str)                  --  name of laptop plan to associate by default
                -------------- credentials (defaults are from multicommcellconstants.RingRoutingConfig) ---------------
        """
        super().__init__(router_cs, **options)
        self.child_admin = None
        self.tenant_user = None
        self.msp_operator = None
        self.tenant_operator = None
        self.__admin_console = None
        self.__browser = None
        self.user_idp_switchers = {}
        self.user_info_cache = {}
        if admin_console:
            self.reset_admin_console(admin_console)
        self.sync_properties = {
            "dlp": self.validate_dlp,
            "autodiscovery": self.validate_autodiscovery,
            "operators": self.validate_edit_operators,
            "contacts": self.validate_edit_contacts,
            "tags": self.validate_edit_tags,
            "themes": self.validate_visible_theme
        }

    def reset_admin_console(self, admin_console):
        """
        Resets variables to point to different browser/admin console
        """
        self.__admin_console = admin_console
        self.__browser = admin_console.browser
        self.__sc_page = ServiceCommcell(admin_console)
        self.__companies_page = Companies(admin_console)
        self.__company_details = CompanyDetails(admin_console)
        self.__guided_setup = GettingStarted(admin_console)
        self.__themes_page = Theme(admin_console)
        self.__navigator = admin_console.navigator
        self.companies_redirects = {
            "edit": self.__companies_page.access_edit,
            "dashboard": self.__companies_page.access_dashboard,
            "company_link": self.__companies_page.access_self_company,
            "configure": self.__companies_page.access_configure,
            "entity_links": {}
        }

    # # # # # SETUPS # # # # #

    def setup_tenant_operator(self) -> None:
        """ 
        Sets up a company user as operator to child company for furthur testing 
        
        Returns:
            None
        """
        self.log.info(f"setting up operator for child company {self._child_name}")

        full_uname = self.reseller_idp_local_org.domain_name + '\\' + 'auto_child_operator'
        if self.reseller_idp_as_reseller.users.has_user(full_uname):
            self.tenant_operator = self.reseller_idp_as_reseller.users.get(full_uname)
            return

        self.tenant_operator = self.setup_company_user(user_name='auto_child_operator')
        new_operator = {
            'user': self.tenant_operator.user_name,
            'role': 'Tenant Operator'
        }
        self.log.info(f"adding operator: {new_operator}")
        self.child_idp_remote_org.operators = simplify_operators(self.child_idp_remote_org.operators) + [new_operator]

        self.child_idp_remote_org.refresh()
        self.child_local.refresh()

        if new_operator not in simplify_operators(self.child_idp_remote_org.operators):
            raise Exception(f"operator {new_operator} did not get added")

        if simplify_operators(self.child_idp_remote_org.operators) == simplify_operators(self.child_local.operators):
            self.log.info("Manage operators of child verified from idp as reseller")
        else:
            self.log.error(f"Child operators in idp: {self.child_idp_remote_org.operators}")
            self.log.error(f"Child operators in workload: {self.child_local.operators}")
            raise Exception("Manage operators failed from idp")

    def setup_tenant_user(self) -> None:
        """ 
        Sets up a company user for furthur testing 
        
        Returns:
            None
        """
        self.log.info(f"setting up company user")
        full_uname = self.reseller_idp_local_org.domain_name + '\\' + 'auto_user'
        if self.reseller_idp_as_reseller.users.has_user(full_uname):
            self.tenant_user = self.reseller_idp_as_reseller.users.get(full_uname)
            return
        self.tenant_user = self.setup_company_user(user_name='auto_user')

    def complete_guided_setup(self, initial_commcell: str = None, initial_company: str = None) -> bool:
        """
        Handles guided setup redirects by completing laptop solution and takes back to original page

        Args:
            initial_commcell   (str)   -   the commcell to redirect to, after completing guided setup
            initial_company    (str)   -   the company to operate as, after completing guided setup

        Returns:
            True    -   if guided setup was completed
            False   -   if guided setup failed
            None    -   if guided setup was not needed/redirected
        """

        def is_plan_assigned():
            created_plan_msg = 'Plan is already created'
            return self.__admin_console.check_if_entity_exists(
                "xpath", f"//p[text()='{created_plan_msg}']"
            )

        if "gettingStarted" in self.__admin_console.current_url():
            self.log.info(">>> Redirected to Guided Setup, Completing Setup")
            self.__guided_setup.expand_solutions()
            self.__guided_setup.access_panel('Laptops')
            if not is_plan_assigned():
                self.log.error(">>> Guided setup cannot be completed, no plan assigned :(")
                return False
            self.__admin_console.driver.back()
            self.log.info(">>> Completed guided setup, resetting to retry test")
            if initial_commcell:
                self.log.info(f">>> returning to original commcell {initial_commcell}")
                self.__navigator.switch_service_commcell(initial_commcell)
            if initial_company:
                self.log.info(f">>> returning to original operating company {initial_company}")
                self.__navigator.switch_company_as_operator(initial_company)
            self.log.info(">>> successfully returned to original state, continue testing...")
            return True
        else:
            self.log.info(">>> No Guided setup redirects, continuing")

    # # # # # LOGIN UTILS # # # # #
    def clean_browser(self) -> None:
        """
        Cleans up adminconsole and browser in this helper
        """
        AdminConsole.logout_silently(self.__admin_console)
        Browser.close_silently(self.__browser)

    def get_user_idp_switcher(self, user_name: str) -> CommcellSwitcher:
        """
        Gets the CommcellSwitcher obj for given user login in his idp
        """
        if user_name.lower() not in self.user_idp_switchers:
            self.log.info(f"getting switcher object for user: {user_name}")
            if user_name.lower() == self.msp_router_switcher.idp_login.commcell_username.lower():
                self.user_idp_switchers[user_name.lower()] = self.msp_router_switcher
            elif self.reseller_idp_switcher \
                    and user_name.lower() == self.reseller_idp_switcher.idp_login.commcell_username.lower():
                self.user_idp_switchers[user_name.lower()] = self.reseller_idp_switcher
            else:
                if not self._is_msp_user():
                    company_alias = user_name.split('\\')[0]
                    company_idp = self._router_commcell.get_user_suggestions(
                        company_alias)[0]['company']['entityInfo']['multiCommcellName']
                    self.log.info(f"user: {user_name} belongs to company, whose idp is {company_idp}")
                    cs_hn = self.msp_router_switcher.get_service_commcell_props(company_idp)['hostname']
                else:
                    cs_hn = self._router_commcell.webconsole_hostname
                    self.log.info(f"user: {user_name} belongs to msp, assuming home to: {cs_hn}")
                self.user_idp_switchers[user_name.lower()] = CommcellSwitcher(
                    Commcell(cs_hn, user_name, self._default_password)
                )
        return self.user_idp_switchers[user_name.lower()]

    @property
    def current_userobj(self) -> User:
        un = re.sub(
            r'\\\\+', r'\\',
            self.__browser.get_js_variable('cv.loggedInUserName')
        )
        if un.lower() not in self.user_info_cache:
            self.user_info_cache[un.lower()] = self.current_commcell(True).users.get(un)
        return self.user_info_cache[un.lower()]

    def current_commcell(self, msp_level: bool = False) -> Commcell:
        """
        Gets the current user and current commcell's Commcell object

        Args:
            msp_level (bool)  -   if True, returns the msp level session for this commcell
        
        Returns:
            current_commcell    -   Commcell object of current webpage
        """
        if msp_level:
            this_username = self._router_commcell.commcell_username
            company = None
        else:
            this_username = re.sub(
                r'\\\\+', r'\\',
                self.__browser.get_js_variable('cv.loggedInUserName')
            )
            company = self.__navigator.operating_company_displayed()
        this_commcell = urlparse(self.__admin_console.current_url()).netloc
        this_cs_obj = self.get_user_idp_switcher(this_username).get_service_session(this_commcell)
        if company:
            this_cs_obj.switch_to_company(company)
        else:
            this_cs_obj.reset_company()
        return this_cs_obj

    def _is_msp_level(self) -> bool:
        """
        Returns if current user is at MSP level or not
        
        Returns:
            bool    -   True if user is msp and is not operating any company
        """
        return self._is_msp_user() and not self.__navigator.operating_company_displayed()

    def _is_msp_user(self) -> bool:
        """
        Returns if current user is MSP user or not
        
        Returns:
            bool    -   True if user is a commcell level user and doesn't belong to company
        """
        return self.current_userobj.user_company_name == 'commcell'

    def get_ui_login(self, username: Union[str, User], service: str = None,
                     redirect: str = None, operating_company: str = None) -> 'RingRoutingHelperUI':
        """
        Logs in as given user into given service commcell as operator to given company
        and returns browser and adminconsole objects

        Args:
            username            (str/obj)   -   name of user or User sdk object
            service             (str)       -   service commcell to login to
            redirect            (str)       -   redirect hostname to expect/wait for
            operating_company   (str)       -   company to operate

        Returns:
            RingRoutingHelperUI   -   RingRoutingHelperUI obj for a new browser with the persona login
        """
        if isinstance(username, User):
            login_name = username.user_name
            user_fullname = username.full_name
        else:
            self.log.info(f">>> assuming login name and full name to be given {username}")
            login_name = username
            user_fullname = username

        self.log.info(f">>> attempting to log into user {login_name}, "
                      f"from {('service commcell from dialog ' + service) if service else 'router'}, "
                      f"{('via autoredirect to ' + redirect) if redirect else ''}, "
                      f"{('as operator to ' + operating_company) if operating_company else ''}")
        use_password = self._default_password
        if login_name.lower() == self._router_commcell.commcell_username.lower():
            use_password = self._router_password
        self.log.info(">>> checking if current user needs to logout")
        try:
            visible_header_username = self.__admin_console.logged_in_user().lower()
        except:
            visible_header_username = None

        if visible_header_username != user_fullname.lower():
            if not visible_header_username:
                self.log.info(">>> no user currently logged, so attempting new browser login from router cs url")
            else:
                self.log.info(f"required user {user_fullname}")
                self.log.info(f">>> different user is currently logged [{visible_header_username}]"
                              f", creating new browser for current user login")

            browser = BrowserFactory().create_browser_object(name=f"browser for user {username}")
            browser.open()
            admin_console = AdminConsole(browser, self._router_commcell.webconsole_hostname)
            try:
                admin_console.login(
                    username=login_name, password=use_password,
                    service_commcell=service, on_prem_redirect_hostname=redirect
                )
            except Exception as exp:
                AdminConsole.logout_silently(admin_console)
                Browser.close_silently(browser)
                raise exp
            self_copy = copy.deepcopy(self)
            self_copy.reset_admin_console(admin_console) # setting the browser

        else:
            self.log.info("Same user is logged in main browser, reusing it..")
            admin_console = self.__admin_console
            self_copy = self

        self.log.info(">>> checking if commcell needs to be switched")
        if service:
            service_switcher_name = self.get_user_idp_switcher(
                login_name).get_service_commcell_props(service)['regionname']
            if service_switcher_name != admin_console.navigator.service_commcell_displayed()[1]:
                self.log.info(f">>> switching to commcell {service} via commcell switcher")
                admin_console.navigator.switch_service_commcell(service_switcher_name)
        self.log.info(">>> checking if company needs to be switched")
        if operating_company:
            current_company = admin_console.navigator.operating_company_displayed()
            if not (current_company and operating_company in current_company):
                self.log.info(f">>> switching to company {operating_company} via company switcher")
                admin_console.navigator.switch_company_as_operator(operating_company)
        self.log.info(">>> login successfull!")
        return self_copy

    def reseller_level_login(
            self, user_obj: User, as_operator_of: str = None, workload: str = None) -> 'RingRoutingHelperUI':
        """
        New Browser login as given Reseller level user_obj

        Args:
            user_obj    (User)      -   the user object (in idp) of reseller level persona
            as_operator_of  (str)   -   company to operate on
            workload    (str)       -   which workload commcell of company to operate on

        Returns:
            RingRoutingHelperUI   -   RingRoutingHelper for a new browser with the persona login
        """
        if as_operator_of == 'child':
            as_operator_of = self._child_name
            if not workload:
                workload = self.child_idp_hostname
        if as_operator_of and workload:
            as_operator_of = (f'{as_operator_of} '
                              f'({self.reseller_idp_switcher.get_service_commcell_props(workload)['regionname']})')

        return self.get_ui_login(
            user_obj,
            redirect=self.reseller_idp_hostname,  # expect redirect to IDP
            operating_company=as_operator_of
        )

    def use_msp_admin(self, as_operator_of: str = None, workload: str = None) -> 'RingRoutingHelperUI':
        """
        New Browser login as MSP user of Commcell obj given initially

        Args:
            as_operator_of  (str)   -   company to operate on
            workload    (str)       -   which workload commcell of company to operate on

        Returns:
            RingRoutingHelperUI   -   RingRoutingHelper for a new browser with the persona login
        """
        user_obj_master = self._router_commcell.users.get(self._router_commcell.commcell_username)
        if as_operator_of == 'reseller':
            as_operator_of = self._company_name
            if not workload:
                workload = self.reseller_idp_hostname
        if as_operator_of == 'child':
            as_operator_of = self._child_name
            if not workload:
                workload = self.child_idp_hostname
        if as_operator_of and workload:
            as_operator_of = (f"{as_operator_of} "
                              f"({self.msp_router_switcher.get_service_commcell_props(workload)['regionname']})")
        return self.get_ui_login(user_obj_master, operating_company=as_operator_of)

    def use_tenant_admin(self, as_operator_of: str = None, workload: str = None) -> 'RingRoutingHelperUI':
        """
        New Browser login as Tenant admin of reseller given/setup

        Args:
            as_operator_of  (str)   -   company to operate on
            workload    (str)       -   which workload commcell of company to operate on

        Returns:
            RingRoutingHelperUI   -   RingRoutingHelper for a new browser with the persona login
        """
        return self.reseller_level_login(
            self.reseller_idp_as_msp.users.get(self.reseller_idp_as_reseller.commcell_username),
            as_operator_of, workload
        )

    def use_tenant_operator(self, as_operator_of: str = None, workload: str = None) -> 'RingRoutingHelperUI':
        """
        New Browser login as Tenant operator setup

        Args:
            as_operator_of  (str)   -   company to operate on
            workload    (str)       -   which workload commcell of company to operate on

        Returns:
            RingRoutingHelperUI   -   RingRoutingHelper for a new browser with the persona login
        """
        return self.reseller_level_login(self.tenant_operator, as_operator_of, workload)

    def use_tenant_user(self) -> 'RingRoutingHelperUI':
        """
        New Browser login as tenant user setup

        Returns:
            RingRoutingHelperUI   -   RingRoutingHelper for a new browser with the persona login
        """
        return self.reseller_level_login(self.tenant_user)  # no operating rights

    def use_child_admin(self) -> 'RingRoutingHelperUI':
        """
        New Browser login as child company admin

        Returns:
            RingRoutingHelperUI   -   RingRoutingHelper for a new browser with the persona login
        """
        return self.get_ui_login(
            self.child_admin,
            redirect=self.child_idp_hostname  # expect redirect to child workload
        )

    def post_redirect_steps(self) -> None:
        """Steps to execute like close popup, warning dialog, after any redirect to new commcell"""
        self.__admin_console.close_popup()
        self.__admin_console._AdminConsole__close_warning_dialog()
        self.__admin_console.check_error_page()

    # # # # # VALIDATION UTILS # # # # #

    @staticmethod
    def parse_api_associations(api_associations: dict) -> dict:
        """
        Util for converting API returned associations to comparable format

        Args:
            api_associations    (dict)  -   dict with json returned by associations API

        Returns:
            parsed_associations (dict)  -   dict with key as entity and value list of associated commcells
        """
        parsed_associations = {}
        for assoc in api_associations['associations']:
            user_name = assoc['userOrGroup'].get('userName')
            user_group_name = assoc['userOrGroup'].get('userGroupName')
            provider_name = assoc['userOrGroup'].get('providerDomainName')
            name = user_name or user_group_name or provider_name

            if name not in parsed_associations:
                parsed_associations[name] = {}
            parsed_associations[name]['service_commcells'] = \
                parsed_associations[name].get('service_commcells', []) + [assoc['entity']['entityName']]

            if user_name:
                parsed_associations[user_name]['type'] = 'User'
            elif user_group_name:
                parsed_associations[user_group_name]['type'] = 'User group'
            elif provider_name:
                parsed_associations[provider_name]['type'] = 'Company'
        return parsed_associations

    @staticmethod
    def parse_ui_associations(ui_associations: dict) -> dict:
        """
        Util for converting UI returned associations to comparable format

        Args:
            ui_associations     (dict)  -   dict with association table data read from service commcells page

        Returns:
            parsed_associations (dict)  -   dict with key as entity and value list of associated commcells
        """
        parsed_associations = {}
        for index in range(len(ui_associations['Name'])):
            name = ui_associations['Name'][index]
            services = list(map(lambda s: s.strip(), ui_associations['Service CommCells'][index].split(',')))
            etype = ui_associations['Type'][index]
            parsed_associations[name] = {
                'service_commcells': services,
                'type': etype
            }
        return parsed_associations

    @staticmethod
    def changed_theme(theme: dict) -> dict:
        """
        Util for getting only the changed theme colors from default theme
        
        Args:
            theme   (dict)  -   the theme dict to convert

        Returns:
            changed_theme   (dict)  -   dict with only key,value pairs of theme colors changed from default
        """
        return {
            key: value
            for key, value in theme.items()
            if value.lower() != Theme.color_ids_default[key].lower()
        }

    @staticmethod
    def _get_api_label(entity: str) -> str:
        """
        Util for getting the API term for company associated entity name from UI term

        Args:
            entity  (str)   -   the entity name as visible in UI
        
        Returns:
            api_term    (str)   -   the entity name as returned from API
        """
        for api_term in ENTITY_LABELS:
            if entity in ENTITY_LABELS[api_term]:
                return api_term

    @staticmethod
    def _compare_operators(ui_operators: dict, api_operators: dict) -> bool:
        """
        Compares operator associations from UI with operator associations returned by API

        Args:
            ui_operators    (dict)  -   dict of operators in same format as returned by panel
            api_operators   (dict)  -   dict of operators in format returned by organization.operators

        Returns:
            True    -    if both operators associations match
            False   -    if some association is missing
        """

        def assoc_exists(a, b):
            return {
                'user': a,
                'role': b
            } in api_operators or {
                'userGroup': a,
                'role': b
            } in api_operators

        ui_op_count = 0
        for user, roles in ui_operators.items():
            if isinstance(roles, str):
                ui_op_count += 1
                if not assoc_exists(user, roles):
                    return False
            else:
                for role in roles:
                    ui_op_count += 1
                    if not assoc_exists(user, role):
                        return False
        if ui_op_count == len(api_operators):
            return True

        # # # # # VALIDATIONS AND TESTS # # # # #

    def _fanout_organizations(self) -> Organizations:
        """
        Gets the current commcell's Organizations object with fanout enabled
        
        Returns:
            orgs    -   Organizations object with fanout enabled
        """
        orgs = self.current_commcell().organizations
        orgs.fanout = True
        orgs.refresh()
        return orgs

    def _local_organizations(self) -> Organizations:
        """
        Gets the current commcell's Organizations object with fanout disabled
        
        Returns:
            orgs    -   Organizations object with fanout disabled
        """
        orgs = self.current_commcell().organizations
        if orgs.fanout:
            orgs.fanout = False
            orgs.refresh()
        return orgs

    def _get_child_operators_setup(self) -> list[dict]:
        """
        Sets up operators for child company and returns args to give to the page functions

        Returns:
            operators   (list)  -   list of operator dicts as required to input to operators dialog
        """
        users, roles = self.setup_child_operators(False)
        new_operators = []
        i = 0
        for user in users:
            new_operators.append({
                'user': user.user_name,
                'role': roles[i].role_name
            })
            i = (i + 1) % 2
        return new_operators

    def _get_msp_operators_setup(self) -> list[dict]:
        """
        Sets up msp operators for reseller company and returns args to give to the page functions

        Returns:
            operators   (list)  -   list of operator dicts as required to input to operators dialog
        """
        self.reseller_idp_as_msp.reset_company()

        new_operators = []
        roles = [
            self.setup_role(workloads=x, as_reseller=y)
            for x in [True, False] for y in [True, False]
        ]

        for role in roles:
            u1 = self.setup_msp_user(workloads=True)
            u2 = self.setup_msp_user(workloads=False)
            new_operators.append({
                'user': u1.user_name,
                'role': role.role_name
            })
            new_operators.append({
                'user': u2.user_name,
                'role': role.role_name
            })
        return new_operators

    def _get_contacts_setup(self) -> list[str]:
        """
        Creates tenant admins and returns list of full names to add as contacts

        Returns:
            contacts    (list)  -   list of full names of tenant admin users
        """
        users = []
        for x in [True, False]:
            for y in [True, False]:
                users.append(
                    self.setup_company_user(
                        as_reseller=x, workloads=y, tenant_admin=True, add_contact=False
                    ).full_name
                )
        return users

    # # # # # ASSOCIATIONS VALIDATIONS # # # # #

    def setup_associations_page(self) -> None:
        """
        Sets up Service Commcells Page
        
        Returns:
            None
        """
        if 'serviceCommcells' not in self.__navigator.current_url():
            self.__navigator.navigate_to_service_commcell()

    @test_step
    def validate_user_suggestions(self, term: str, pages: int = 1) -> None:
        """
        Validates the user suggestions returned for given term
        
        Args:
            term    (str)   -   the term to validate user suggestions for
            pages   (int)   -   the amount of pages to parse for validation
        
        Returns:
            None
        
        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        self.setup_associations_page()
        ui_suggestions = self.__sc_page.get_user_suggestions(term, pages)
        api_suggestions = self._router_commcell.get_user_suggestions(term)
        for entity_dict in api_suggestions:
            suggestion = f"{entity_dict['loginName']} ( {entity_dict['company']['entityInfo']['multiCommcellName']} )"
            if suggestion not in ui_suggestions:
                raise CVTestStepFailure(f"Suggestion {suggestion} is missing from UI")
        self.log.info("User suggestions successfully validated")

    @test_step
    def validate_all_associations(self) -> None:
        """
        Validates all the service commcell associations visible
        
        Returns:
            None

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        self.setup_associations_page()
        ui_associations = self.parse_ui_associations(self.__sc_page.get_service_commcell_associations(all_pages=True))
        api_associations = self.parse_api_associations(self._router_commcell._service_commcells_association())
        for name in api_associations:
            if ui_associations.get(name) != api_associations[name]:
                self.log.error(f"UI -> {ui_associations.get(name)}")
                self.log.error(f"API -> {api_associations[name]}")
                raise CVTestStepFailure(f"Association details failed to match for {name}")
        self.log.info("Associations successfully validated")

    @test_step
    def validate_entity_associations(self, entity: str, edit: bool = True, service_commcells: list[str] = None) -> None:
        """
        Validates the service commcells associated for given entity
        
        Args:
            entity          (str)       -   name of entity
            edit            (bool)      -   performs edit and validates if True
            service_commcells   (list)  -   list of service commcells to associate to, if edit is True
        
        Returns:
            None
        
        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        self.setup_associations_page()

        if edit:
            self.__sc_page.add_entity_association(entity, service_commcells)
            self.validate_entity_associations(entity, edit=False)
            self.__sc_page.delete_entity_association(entity, service_commcells)
            self.validate_entity_associations(entity, edit=False)
            return

        ui_assoc = self.parse_ui_associations(self.__sc_page.get_service_commcell_associations(entity)).get(entity)
        api_assoc = self.parse_api_associations(self._router_commcell._service_commcells_association()).get(entity)
        if ui_assoc != api_assoc:
            self.log.error(f"UI -> {ui_assoc}")
            self.log.error(f"API -> {api_assoc}")
            raise CVTestStepFailure(f"Association details failed to match for {entity}")

        self.log.info("Associated entity Validated")

    # # # # # COMPANIES LIST VALIDATIONS # # # # #

    def setup_companies_page(self) -> None:
        """
        Navigates to companies page if not already present
        
        Returns:
            None
        """
        if not self.__navigator.current_url().endswith('/subscriptions'):
            self.__navigator.navigate_to_companies()

    @test_step
    def validate_companies_list(self, error_limit: int = 0) -> None:
        """
        Verifies fanned out list of companies match as returned by API

        Args:
            error_limit (int)   -   the max acceptable difference between number of companies in UI and API

        Returns:
            None

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        self.log.info(">>>>> Preparing to validate companies listing")
        self.log.info(">>> Getting API Data from /Organizations")
        api_data = self._fanout_organizations().all_organizations_props
        api_list = list(api_data.keys())
        self.log.info(">>> API Data loaded")
        if not self._is_msp_level():
            self.log.info(">>> Logged User is not MSP level, verifying child companies listing")
            if self._company_name in api_list:
                api_list.remove(self._company_name)
        else:
            self.log.info(">>> Logged User is MSP level, verifying all commcells companies listing")

        self.setup_companies_page()
        self.__companies_page.set_scope_local(False)

        self.log.info(">>>>> Starting Validating Companies listing")
        self.log.info(">>>> Validating number of companies")
        api_count = len(api_list)
        ui_count = int(self.__companies_page.get_total_companies_count())

        if api_count != ui_count:
            self.log.error(f">>> API Count: {api_count}")
            self.log.error(f">>> UI Count: {ui_count}")
            if abs(ui_count - api_count) <= error_limit:
                self.log.warning(">>>> Difference is within error limit, ignoring")
            else:
                raise CVTestStepFailure("Companies count mismatch from API and UI")
        else:
            self.log.info(">>>> Companies table count validated")

        if len(api_list) > 30:
            self.log.info(">>>> Too many companies to validate, skipping individual company name validation")
            return
        else:
            self.log.info(">>>> Validating company names")
            ui_list = sorted(_force_lower(self.__companies_page.get_all_companies()))
            api_list = sorted(_force_lower(api_list))

            if api_list == ui_list:
                self.log.info(">>>> UI Companies List successfully validated from API!")
            else:
                self.log.error(f">>> Missing Company Names: {set(api_list) - set(ui_list)}")
                self.log.error(f">>> Extra Company Names: {set(ui_list) - set(api_list)}")
                raise CVTestStepFailure("Company Names did not match")
        self.log.info(">>>>> Companies Listing Validated Successfully!")

    def compare_manage_operators(self, company: str) -> None:
        """
        Compares manage operators dialog content with API returned response

        Args:
            company (str)   -   company to verify manage operators for
        """
        self.log.info(">>> Comparing UI manage operators dialog with API")
        api_ops = _force_lower(simplify_operators(self._fanout_organizations().get_remote_org(company).operators))
        ui_ops = _force_lower(self.__companies_page.access_operators(company))
        self.log.warning(f">>> UI operators: {ui_ops}")
        self.log.warning(f">>> API operators: {api_ops}")
        if self._compare_operators(ui_ops, api_ops):
            self.log.info(">>> UI Operators successfully validated from API!")
        else:
            raise CVTestStepFailure("UI Operators do not match API returned operators")

    @test_step
    def validate_manage_operators(self, company: str = None, edit: bool = True) -> None:
        """
        Validates the manage operators dialog opened from Companies table actions

        Args:
            company (str)   -   name of company on who to apply, will assume reseller/child if None
            edit    (bool)  -   will validate after adding some operators as well as deleting if True

        Returns:
            None

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        self.log.info(">>>>> Preparing to run manage operators test")
        user_is_msp = self._is_msp_level()
        if not company:
            self.log.info(">>> No company input, will test depending on logged user level")
            company = self._child_name
            if user_is_msp:
                self.log.info(f">>> Logged User is MSP level, will test on reseller {self._company_name}")
                company = self._company_name
            else:
                self.log.info(f">>> Logged User is not MSP level, will test on child {self._child_name}")

        self.setup_companies_page()
        self.log.info(">>>>> Starting Manage operators test")
        if edit:
            self.log.info(">>>> Edit manage operators test enabled")
            if not user_is_msp:
                self.log.info(">>> Logged User is not msp, setting up company users to operate on child")
                operators_dict = self._get_child_operators_setup()
            else:
                self.log.info(">>> Logged User is msp, setting up commcell users to operate on reseller")
                operators_dict = self._get_msp_operators_setup()
            self.log.info(f">>> Created users and roles: {operators_dict}")
            self.log.info(">>>> Adding random operators")
            self.__companies_page.add_operators(company, operators_dict)
            self.compare_manage_operators(company)
            self.log.info(">>>> Add operators verified")

            random_operators = list(random.sample(operators_dict, k=2))
            self.log.info(">>>> Deleting random operators")
            self.__companies_page.delete_operators(company, random_operators)

        self.compare_manage_operators(company)
        if edit:
            self.log.info(">>>> Delete operators verified")
        self.log.info(">>>>> Manage operators validated successfully!")

    def compare_manage_tags(self, company: str) -> None:
        """
        Compares manage tags dialog for given company with tags returned by API

        Args:
            company (str)   -   company to compare manage tags dialog for
        """
        self.log.info(">>> Comparing UI manage tags dialog to API")
        api_tags = _force_lower(simplify_tags(self._fanout_organizations().get_remote_org(company).tags))
        ui_tags = _force_lower(self.__companies_page.access_tags(company))
        self.log.warning(f">>> UI tags: {ui_tags}")
        self.log.warning(f">>> API tags: {api_tags}")
        if _compare_list(api_tags, ui_tags):
            self.log.info(">>> UI Tags successfully validated from API!")
        else:
            raise CVTestStepFailure("UI Tags do not match API returned tags")

    @test_step
    def validate_manage_tags(self, company: str = None, edit: bool = True) -> None:
        """
        Validates the manage tags dialog opened from Companies table actions

        Args:
            company (str)   -   name of company on who to apply, will assume reseller/child if None
            edit    (bool)  -   will validate after adding some tags as well as deleting if True

        Returns:
            None

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        self.log.info(">>>>> Preparing to run manage tags test")
        if not company:
            self.log.info(">>> No company input, will test depending on logged user level")
            company = self._child_name
            if self._is_msp_level():
                self.log.info(f">>> Logged User is MSP level, will test on reseller {self._company_name}")
                company = self._company_name
            else:
                self.log.info(f">>> Logged User is not MSP level, will test on child {self._child_name}")

        self.setup_companies_page()
        self.log.info(">>>>> Starting Manage tags test")
        if edit:
            self.log.info(">>>> Edit manage tags test enabled")
            random_tags_dict = [
                {
                    'name': f'tagname_{"".join(random.choices(string.ascii_lowercase, k=6))}',
                    'value': ''
                },
                {
                    'name': f'tagname_{"".join(random.choices(string.ascii_lowercase, k=6))}',
                    'value': f'value_{"".join(random.choices(string.ascii_lowercase, k=6))}'
                }
            ]
            self.log.info(">>>> Adding random tags")
            self.__companies_page.add_tags(company, random_tags_dict)
            self.compare_manage_tags(company)
            self.log.info(">>>> Added tags verified")
            self.__companies_page.delete_tags(company, [random_tags_dict[random.randint(0, 1)]])
            self.log.info(">>>> Deleting random tags")
        self.compare_manage_tags(company)
        if edit:
            self.log.info(">>>> Delete tags verified")
        self.log.info(">>>>> Manage tags validated successfully!")

    @test_step
    def validate_entities_summary(self, company: str = None) -> None:
        """
        Validates the entities summary popup and total value shown in companies table

        Args:
            company (str)   -   name of company, will assume reseller/child otherwise

        Returns:
            None

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        self.log.info(">>>>> Preparing to validate entities summary callout")
        if not company:
            self.log.info(">>> No company input, will test depending on logged user level")
            company = self._child_name
            if self._is_msp_level():
                self.log.info(f">>> Logged User is MSP level, will test on reseller {self._company_name}")
                company = self._company_name
            else:
                self.log.info(f">>> Logged User is not MSP level, will test on child {self._child_name}")

        self.setup_companies_page()
        self.log.info(">>>>> Starting entities summary test")

        key_map = ENTITY_LABELS
        api_summary = self._fanout_organizations().get_remote_org(company).get_entity_counts()
        # api_summary['total'] = self._fanout_organizations().all_organizations_props[company.lower()]['count']
        ui_summary = self.__companies_page.access_entities_summary(company)
        self.log.warning(f"API summary: {api_summary}")
        self.log.warning(f"UI summary: {ui_summary}")

        for entity in api_summary:
            ui_entity = None
            for mapping in key_map[entity]:
                if mapping in ui_summary:
                    ui_entity = mapping
            if not ui_entity:
                self.log.error(f"Entity {key_map[entity]} missing from summary for {company}")
                raise CVTestStepFailure("API returned extra entities not shown by UI")
            if int(api_summary[entity]) != int(ui_summary[ui_entity]):
                raise CVTestStepFailure("API returned summary not matching UI displayed")

        self.log.info(">>>>> Entities summary successfully validated!")

    def _verify_redirect(self, redirect_name: str, company: Organization, expected_commcell_hostname: str) -> None:
        """
        Verifies if the given link correctly redirected to expected commcell to correct company page

        Args:
            redirect_name   (str)                -   name of the redirect (edit/dashboard...see COMPANY_LINKS)
            company (obj)                        -   Organization object of company
            expected_commcell_hostname   (str)   -   hostnamename of commcell expected

        Returns:
            None

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        self.log.info(f">>> Verifying redirection {redirect_name} of {company} to {expected_commcell_hostname}")
        if redirect_name not in COMPANY_LINKS and self._get_api_label(redirect_name) is None:
            self.log.warning(f"Redirect {redirect_name} Unknown! Skipping test!")
            return

        expected_url = COMPANY_LINKS.get(
            redirect_name,
            COMPANY_LINKS.get(self._get_api_label(redirect_name))
        ) % company.organization_id
        redirected_url = self.__admin_console.current_url()
        company_switcher = self.__navigator.operating_company_displayed()

        if expected_commcell_hostname not in redirected_url:
            raise CVTestStepFailure(f"{redirect_name} - Incorrect Commcell Redirect")
        self.log.info(">>> redirected commcell verified")

        if expected_url not in redirected_url:
            self.log.error(f"Expected URL: {expected_url}")
            self.log.error(f"Got instead: {redirected_url}")
            raise CVTestStepFailure(f"{redirect_name} - Incorrect Page redirect")
        self.log.info(f">>> redirected url verified")

        if redirect_name in OPERATOR_ROLE_REDIRECTS:
            if company_switcher != company.organization_name:
                raise CVTestStepFailure(f"{redirect_name} failed to redirect thru login as operator")
            self.log.info(">>> operator role verified")
        if redirect_name in NON_ROLE_REDIRECTS:
            if company_switcher == company.organization_name:
                raise CVTestStepFailure(f"{redirect_name} failed to redirect above company level, "
                                        f"got company switcher {company_switcher} after redirect!")
            self.log.info(">>> lack of operator role verified")
        self.log.info(f">>> Redirection Verified for {redirect_name}!")

    @test_step
    def verify_redirects(self, exclusions: list[str] = None, org_obj: Organization = None) -> None:
        """
        Verifies all the links in companies page
        edit, dashboard, configure, company link, entities summary links

        Args:
            exclusions  (list)  -   list of redirects to skip (see COMPANY_LINKS)
                                    'entity_links' to skip all entity links
            org_obj (obj)       -   Organization object of company to verify redirects for,
                                    will assume reseller/child setup otherwise

        Returns:
            None

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        if exclusions is None:
            exclusions = []
        self.log.info(">>>>> Preparing to start company redirect links test")
        self.setup_companies_page()

        icon, current_commcell = self.__navigator.service_commcell_displayed()
        current_company = self.__navigator.operating_company_displayed()

        if org_obj:
            company = org_obj
            expected_commcell = urlparse(org_obj._commcell_object.webconsole_hostname).netloc
            self.log.info(f">>> Got input company-> {org_obj.organization_name}")
        else:
            self.log.info(">>> No company given, will test depend on user level")
            if self._is_msp_level():
                company = self.reseller_idp_local_org
                expected_commcell = self.reseller_idp_hostname
                self.log.info(">>> Logged User is MSP, will test on reseller")
            else:
                self.log.info(">>> Logged User is not MSP, will test on child")
                company = self.child_idp_local_org
                expected_commcell = self.child_idp_hostname
        self.log.info(f">>>> Testing links of {company.organization_name}, expected to redirect to {expected_commcell}")

        testing_redirects = list(set(self.companies_redirects.keys()) - set(exclusions))
        self.log.info(f">>>> Checking links available")
        if "entity_links" in testing_redirects:
            testing_redirects.remove("entity_links")
            available_entity_links = list(
                self.__companies_page.access_entities_summary(company.organization_name).keys())
            testing_redirects += available_entity_links
            testing_redirects.remove('total')
            testing_redirects = list(set(testing_redirects) - set(exclusions))

        self.log.info(f">>>> Got links to test: {testing_redirects}")
        self.log.info(">>>>> Starting Redirect Links test")
        for redirect_name in testing_redirects:
            self.log.info(f">>>> Testing redirect-> {redirect_name}")
            redirect_method = self.companies_redirects.get(
                redirect_name,
                lambda company_name: self.__companies_page.access_entities_link(company_name, redirect_name)
            )
            redirect_method(company.organization_name)
            self.post_redirect_steps()

            guided_setup_redirect_result = self.complete_guided_setup(current_commcell, current_company)
            if guided_setup_redirect_result:
                self.log.info(">>> Returning to companies page to click the same redirect again")
                self.__navigator.navigate_to_companies()
                redirect_method(company.organization_name)
            elif guided_setup_redirect_result is not None:
                raise CVTestStepFailure("Guided setup interruption :/, "
                                        "unable to test redirects, please assign plan or input plan name")

            self.log.info(">>> Redirection completed, verifying URL...")
            try:
                self._verify_redirect(redirect_name, company, expected_commcell)
            except CVTestStepFailure as exp:
                self.log.error('>>> Redirect still failed even after guided setup was supposedly completed')
                raise exp

            self.log.info(">>> returning to original page")
            self.__navigator.switch_service_commcell(current_commcell)
            if current_company:
                self.log.info(">>> returning to original operating role")
                self.__navigator.switch_company_as_operator(current_company)
            self.log.info(">>> successfully returned to original state")
        self.log.info(">>>>> ALL REDIRECTS VERIFIED")

    @test_step
    def validate_switchers_slo(self) -> None:
        """
        Validates the commcell switcher options are working and SLO is also validated
        """
        self.log.info(">>> Testing Switcher SSO and SLO")
        if self._is_msp_level():
            self.log.info(f">>> Logged User is MSP level")
            idp_switcher_name = self.msp_router_switcher.get_service_commcell_props(
                self._router_commcell.commserv_name)['regionname']
            idp_hn = self._router_commcell.webconsole_hostname
            workload_hns = self.reseller_workloads_hostnames + [self.reseller_idp_hostname]
        else:
            self.log.info(f">>> Logged User is not MSP level")
            idp_switcher_name = self.reseller_idp_switcher.get_service_commcell_props(
                self.reseller_idp_as_reseller.commserv_name)['regionname']
            idp_hn = self.reseller_idp_as_msp.webconsole_hostname
            workload_hns = self.reseller_workloads_hostnames
        if len(workload_hns) < 2:
            raise CVTestStepFailure(
                f"Cannot test switcher workload <-> workload case, need atleast 2 workloads, given: {workload_hns}")

        workload_hns = random.sample(workload_hns, 2)
        self.log.info(f">> Testing switching between {idp_switcher_name} <-> {workload_hns}")
        icon, current_commcell = self.__navigator.service_commcell_displayed()
        if current_commcell != idp_switcher_name:
            self.log.info("Current commcell is not IDP, switching!")
            self.__navigator.switch_service_commcell(idp_switcher_name)

        workload_switcher_name1 = self.reseller_idp_switcher.get_service_commcell_props(workload_hns[0])['regionname']
        self.log.info(f"> Switching IDP ({idp_switcher_name}) -> Workload1 ({workload_switcher_name1})")
        self.__navigator.switch_service_commcell(workload_switcher_name1)
        if (correct_url := workload_hns[0]) not in (this_url := self.__admin_console.current_url()):
            raise CVTestStepFailure(f'switcher SSO loaded wrong url -> {this_url}, expected {correct_url}')
        self.__navigator.navigate_to_jobs()
        self.__navigator.navigate_to_companies()
        self.log.info("SSO verified!")

        workload_switcher_name2 = self.reseller_idp_switcher.get_service_commcell_props(workload_hns[1])['regionname']
        self.log.info(f"> Switching Workload1 ({workload_switcher_name1}) -> Workload2 ({workload_switcher_name2})")
        self.__navigator.switch_service_commcell(workload_switcher_name2)
        if (correct_url := workload_hns[1]) not in (this_url := self.__admin_console.current_url()):
            raise CVTestStepFailure(f'switcher SSO loaded wrong url -> {this_url}, expected {correct_url}')
        self.__navigator.navigate_to_jobs()
        self.__navigator.navigate_to_companies()
        self.log.info("SSO verified!")

        self.log.info(f"> Switching Workload2 ({workload_switcher_name2}) -> IDP ({idp_switcher_name})")
        self.__navigator.switch_service_commcell(idp_switcher_name)
        if idp_hn not in (this_url := self.__admin_console.current_url()):
            raise CVTestStepFailure(f'switcher SSO loaded wrong url -> {this_url}, expected {idp_hn}')
        self.__navigator.navigate_to_jobs()
        self.__navigator.navigate_to_companies()
        self.log.info("SSO verified!")

        self.log.info("> Now validating SLO!")
        self.__admin_console.logout()
        time.sleep(7)
        if self.__admin_console.driver.title.lower() not in ['logout', 'command center']:
            raise CVTestStepFailure("Logout page not found after attempting Logout")
        self.log.info('Logout is successfull')

        url = f'http://{workload_hns[0]}'
        self.log.info(f"Check session persist on {workload_hns[0]} by access url {url}")
        self.__admin_console.driver.get(url)
        time.sleep(7)
        if self.__admin_console.driver.title != 'Login':
            raise CVTestStepFailure("Login page not found, session still exists maybe?")
        self.log.info("SLO verified in workload1!")

        url = f'http://{workload_hns[1]}'
        self.log.info(f"Check session persist on {workload_hns[1]} by access url {url}")
        self.__admin_console.driver.get(url)
        time.sleep(7)
        if self.__admin_console.driver.title != 'Login':
            raise CVTestStepFailure("Login page not found, session still exists maybe?")
        self.log.info("SLO verified in workload2 also!")
        self.log.info(">>> SLO and SSO using switchers verified!!")
        self.clean_browser()

    @test_step
    def activate_and_validate(self, company: str = None) -> None:
        """
        Activates company remotely and validates from API

        Args:
            company (str)   -   name of company, will assume reseller/child by default

        Returns:
            None

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        self.log.info(">>>>> Preparing to Validating Activate Company")
        if not company:
            self.log.info(">>> No company input, will test depending on logged user level")
            company = self._child_name
            if self._is_msp_level():
                self.log.info(f">>> Logged User is MSP level, will test on reseller {self._company_name}")
                company = self._company_name
            else:
                self.log.info(f">>> Logged User is not MSP level, will test on child {self._child_name}")

        self.setup_companies_page()
        self.log.info(">>>>> Starting Activate Company test")
        self.__companies_page.activate_company(company)
        remote_org = self._fanout_organizations().get_remote_org(company)
        for _ in range(5):
            remote_org.refresh()
            if remote_org.is_login_disabled or \
                    remote_org.is_backup_disabled or \
                    remote_org.is_restore_disabled:
                time.sleep(10)
                self.log.warning("Activate failed to validate, retrying in 10 seconds")
            else:
                self.log.info(f">>>>> Activate validated for {company}")
                return
        raise CVTestStepFailure("Activate company Failed")

    @test_step
    def deactivate_and_validate(self, company: str = None) -> None:
        """
        Deactivates company and validates from API

        Args:
            company (str)   -   name of company, will assume reseller/child by default

        Returns:
            None

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        self.log.info(">>>>> Preparing to Validating Deactivate Company")
        if not company:
            self.log.info(">>> No company input, will test depending on logged user level")
            company = self._child_name
            if self._is_msp_level():
                self.log.info(f">>> Logged User is MSP level, will test on reseller {self._company_name}")
                company = self._company_name
            else:
                self.log.info(f">>> Logged User is not MSP level, will test on child {self._child_name}")

        self.setup_companies_page()
        self.log.info(">>>>> Starting deactivate company test")
        self.__companies_page.deactivate_company(company)
        remote_org = self._fanout_organizations().get_remote_org(company)
        for _ in range(5):
            remote_org.refresh()
            if not (remote_org.is_login_disabled and
                    remote_org.is_backup_disabled and
                    remote_org.is_restore_disabled):
                self.log.warning("Deactivate failed to validate, retrying in 10 seconds")
                time.sleep(10)
            else:
                self.log.info(f">>>>> De-activate remotely validated for {company}")
                return
        raise CVTestStepFailure("De-activate company Failed")

    @test_step
    def delete_and_validate(self, company: str = None) -> None:
        """
        Deletes company and validates from API

        Args:
            company (str)   -   name of company, will assume reseller/child by default

        Returns:
            None

        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        self.log.info(">>>>> Preparing to Validating Delete Company")
        if not company:
            self.log.info(">>> No company input, will test depending on logged user level")
            company = self._child_name
            if self._is_msp_level():
                self.log.info(f">>> Logged User is MSP level, will test on reseller {self._company_name}")
                company = self._company_name
            else:
                self.log.info(f">>> Logged User is not MSP level, will test on child {self._child_name}")

        self.setup_companies_page()
        self.log.info(">>>>> Starting deactivate company test")
        self.__companies_page.deactivate_and_delete_company(company)
        companies_org = self._fanout_organizations()
        for _ in range(5):
            companies_org.refresh()
            if companies_org.has_organization(company):
                self.log.warning(f"Delete unable to validate, checking after 10 seconds")
                time.sleep(10)
            else:
                self.log.info(f">>>>> Delete remotely validated for {company} (via API)")
                company_data = self.__companies_page.get_company_data(company)
                if len(company_data[list(company_data.keys())[0]]) != 0:
                    self.log.error(f"Company data returned: {company_data}")
                    self.log.warning("Company still visible in page after deletion")
                    if company_data['Status'][0] != 'Deleted':
                        raise CVTestStepFailure("UI error: company still shown even after API returns none")
                    else:
                        self.log.info("Status is showing correctly as deleted")
                self.log.info(">>>>> Delete validated in UI as well")
                return
        raise CVTestStepFailure("Delete company Failed")

    @test_step
    def create_and_validate(self, company_name: str = None, company_alias: str = None) -> str:
        """
        Creates company and validates from API

        Args:
            company_name (str)      -   name of company, generate random name if not given
            company_alias   (str)   -   alias name for company

        Returns:
            company (str)   -   name of company created
        
        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        creating_child = not self._is_msp_level()
        self.log.info("Validating Add Company UI")
        if not creating_child:
            self.log.info("Validating reseller creation at MSP level")
            target = self.reseller_idp_hostname
            company_name_prefix = 'autocompany'
            company_alias_prefix = 'alias'
        else:
            self.log.info("Validating child company creation from reseller level")
            target = self.child_idp_hostname
            company_name_prefix = 'autochild'
            company_alias_prefix = 'childalias'

        random_word1 = ''.join(random.choices(string.ascii_lowercase, k=6))
        random_word2 = ''.join(random.choices(string.ascii_lowercase, k=6))

        company_name = company_name or f'{company_name_prefix} {random_word1} {random_word2}'
        company_alias = company_alias or f'{company_alias_prefix}{random_word1[:2]}{random_word2[:2]}'

        domain = f'{company_alias}.com'
        tenant_admin = f'{company_alias}_admin'
        email = f'{tenant_admin}@{domain}'

        plans = [self._plan_name] if self._plan_name else None

        self.setup_companies_page()
        self.__companies_page.add_company(
            company_name,
            email,
            tenant_admin,
            plans,
            company_alias,
            service_commcell=target
        )
        self.log.info("company created from UI successfully")
        self.created_companies.append(company_name)
        if creating_child:
            self._child_name = company_name
            self._reseller_listing = self.reseller_idp_as_reseller.organizations
            self._reseller_listing.fanout = True
            self.child_idp_remote_org = self._reseller_listing.get_remote_org(self._child_name)
            self.child_idp_as_reseller = self.reseller_idp_switcher.get_service_session(self.child_idp_hostname)
            self.child_idp_local_org = self.child_idp_as_reseller.organizations.get(company_name)
            self.log.info("Child company API data initialized")

        remote_org_prop = self._fanout_organizations().all_organizations_props.get(company_name, {})
        if ((comet_hn := self.msp_router_switcher.get_service_commcell_props(
                remote_org_prop.get('home_commcell', ''))['hostname']) == target):
            self.log.info("Remote Company creation verified from API")
        else:
            self.log.error(f"API returns this: {remote_org_prop} -> {comet_hn}")
            raise CVTestStepFailure("Remote Company creation failed, API does not show correct details")
        return company_name

    @test_step
    def extend_and_validate(self, company_name: str = None) -> None:
        """
        extends company and validates extend is successfull
        """
        pass  # todo: get this done!

    # # # # # RESELLER SYNC VALIDATIONS # # # # #

    def setup_company_overview(self, company: str) -> None:
        """
        Navigates to company overview for given company if not already there
        
        Args:
            company (str)   -   name of company to set up overview page of
        
        Returns:
            None
        """
        user_company = self.current_userobj.user_company_name

        local_company_id = self._local_organizations().all_organizations.get(company.lower())
        if local_company_id and COMPANY_LINKS['configure'] % local_company_id in self.__navigator.current_url():
            return

        if self.__navigator.check_if_element_exists('Companies'):
            self.__navigator.navigate_to_companies()
            try:
                self.__companies_page.access_configure(company)
            except NoSuchElementException:
                if user_company not in ['commcell', company]:
                    raise Exception(f"Current user cannot access overview page of {company} in this commcell")
                self.__admin_console.access_tab('Overview')
        elif self.__navigator.check_if_element_exists('Company') and user_company == company:
            self.__navigator.navigate_to_company()
        else:
            raise Exception(f"Unable to access overview page of {company}")

    @test_step
    def validate_edit_operators(self, company: str = None, edit: bool = True, ui_data: dict = None) -> None:
        """
        Validates operators panel of company overview

        Args:
            company (str)   -   name of company
            edit    (bool)  -   validates after addition/deletion if True
            ui_data (dict)  -   operators dict read from panel
        
        Returns:
            None
        
        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        if not company:
            company = self._company_name
        elif company == 'child':
            company = self._child_name
        self.setup_company_overview(company)

        if edit:
            self.log.info("Editing manage operators")
            if company == 'child':
                operators_dict = self._get_child_operators_setup()
            else:
                operators_dict = self._get_msp_operators_setup()
            self.__company_details.add_operators(operators_dict)
            self.validate_edit_operators(company=company, edit=False)
            random_operators = list(random.sample(operators_dict, k=2))
            self.__company_details.delete_operators(random_operators)
            return self.validate_edit_operators(company=company, edit=False)

        self.log.info("Validating Edit Operators")
        api_ops = _force_lower(simplify_operators(self._local_organizations().get(company).operators))

        if ui_data is None:
            ui_data = self.__company_details.company_info(['Operators'])['Operators']
        if 'User/Group' in ui_data:
            del ui_data['User/Group']

        if ui_data == []:
            ui_data = {}
        ui_ops = _force_lower(ui_data)

        if self._compare_operators(ui_ops, api_ops):
            self.log.info("UI Operators successfully validated from API in overview!")
        else:
            self.log.error(f"UI operators: {ui_ops}")
            self.log.error(f"API operators: {api_ops}")
            raise CVTestStepFailure("UI Operators do not match API returned operators in overview")

    @test_step
    def validate_edit_contacts(self, company: str = None, edit: bool = True, ui_data: dict = None) -> None:
        """
        Validates contacts panel of company overview

        Args:
            company (str)   -   name of company
            edit    (bool)  -   validates after addition/deletion if True
            ui_data (dict)  -   data from contacts panel

        Returns:
            None
        
        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        if not company:
            company = self._company_name
        elif company == 'child':
            company = self._child_name

        self.setup_company_overview(company)
        current_commcell = self.current_commcell(True)

        if edit:
            self.log.info("Editing Contacts")
            new_contacts = self._get_contacts_setup()
            current_contacts = [
                current_commcell.users.get(contact).full_name
                for contact in self._local_organizations().get(company).contacts
            ]
            self.__company_details.edit_contacts(new_contacts + current_contacts)
            self.validate_edit_contacts(company=company, edit=False)
            random_contacts = list(random.sample(new_contacts, k=2))
            self.__company_details.edit_contacts(random_contacts + current_contacts)
            return self.validate_edit_contacts(company=company, edit=False)

        self.log.info("Validating Edit Contacts")
        if ui_data is None:
            ui_data = self.__company_details.company_info(['Contacts'])['Contacts']

        api_contacts = _force_lower([
            current_commcell.users.get(contact).full_name
            for contact in self._local_organizations().get(company).contacts
        ])
        ui_contacts = _force_lower(ui_data['Contact name'])

        if _compare_list(api_contacts, ui_contacts):
            self.log.info("UI Contacts successfully validated from API in overview!")
        else:
            self.log.error(f"UI contacts: {ui_contacts}")
            self.log.error(f"API contacts: {api_contacts}")
            raise CVTestStepFailure("UI Contacts do not match API returned contacts in overview")

    @test_step
    def validate_edit_tags(self, company: str = None, edit: bool = True, ui_data: dict = None) -> None:
        """
        Validates tags panel of company overview

        Args:
            company (str)   -   name of company
            edit    (bool)  -   validates after addition/deletion if True
            ui_data (dict)  -   data from Tags panel

        Returns:
            None
        
        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        if not company:
            company = self._company_name
        elif company == 'child':
            company = self._child_name

        self.setup_company_overview(company)

        if edit:
            self.log.info("Editing tags")
            random_tags_dict = [
                {
                    'name': f'tagname_{"".join(random.choices(string.ascii_lowercase, k=6))}',
                    'value': ''
                },
                {
                    'name': f'tagname_{"".join(random.choices(string.ascii_lowercase, k=6))}',
                    'value': f'value_{"".join(random.choices(string.ascii_lowercase, k=6))}'
                }
            ]
            self.__company_details.add_tags(random_tags_dict)
            self.validate_edit_tags(company=company, edit=False)
            self.__company_details.delete_tags([random_tags_dict[random.randint(0, 1)]])
            return self.validate_edit_tags(company=company, edit=False)

        self.log.info("Validating Edit Tags")
        api_tags = _force_lower(simplify_tags(self._local_organizations().get(company).tags))
        if ui_data is None:
            ui_data = self.__company_details.company_info(['Tags'])['Tags']
        ui_tags = ui_data
        ui_tags = [{
            'name': tag_name,
            'value': tag_value
        } for tag_name, tag_value in ui_tags.items()]
        ui_tags = _force_lower(ui_tags)

        if _compare_list(api_tags, ui_tags):
            self.log.info("UI Tags successfully validated from API in overview!")
        else:
            self.log.error(f"UI tags: {ui_tags}")
            self.log.error(f"API tags: {api_tags}")
            raise CVTestStepFailure("UI Tags do not match API returned tags in overview")

    @test_step
    def validate_dlp(self, company: str = None, edit: bool = True, ui_data: str = None) -> None:
        """
        Validates data encryption toggle of company overview

        Args:
            company (str)   -   name of company
            edit    (bool)  -   validates after activation if True
            ui_data (str)   -   dlp toggle shown in UI (ON/OFF)
        
        Returns:
            None
        
        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        if not company:
            company = self._company_name
        elif company == 'child':
            company = self._child_name

        self.setup_company_overview(company)
        if ui_data is None:
            ui_data = self.__company_details.company_info(['General'])['General']['Allow owners to enable data ' \
                                                                                  'encryption']
        ui_dlp = (ui_data == 'ON')
        api_dlp = self._local_organizations().get(company).is_data_encryption_enabled
        if ui_dlp != api_dlp:
            self.log.error(f"api dlp: {api_dlp}, ui dlp: {ui_dlp}")
            raise CVTestStepFailure("DLP validation failed")
        else:
            self.log.info("DLP validation successful")
        if edit:
            self.__company_details.edit_general_settings({
                'data_encryption': True,
            })
            self.validate_dlp(company=company, edit=False)

    @test_step
    def validate_autodiscovery(self, company: str = None, edit: bool = True, ui_data: str = None) -> None:
        """
        Validates autodiscovery toggle of company overview

        Args:
            company (str)   -   name of company
            edit    (bool)  -   validates after activation if True
            ui_data (str)   -   autodiscovery toggle shown in UI (ON/OFF)

        Returns:
            None
        
        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        if not company:
            company = self._company_name
        elif company == 'child':
            company = self._child_name

        self.setup_company_overview(company)
        if ui_data is None:
            general_details = self.__company_details.company_info(['General'])['General']
            ui_data = (
                    general_details.get('Auto discover applications') or
                    general_details.get('Enable auto discover')
            )
            if ui_data is None:
                self.log.error(f'General Panel: {general_details}')
                raise CVTestStepFailure('Unable to find Autodiscovery property!')
        ui_autodiscovery = (ui_data == 'ON')
        api_autodiscovery = self._local_organizations().get(company).is_auto_discover_enabled
        if ui_autodiscovery != api_autodiscovery:
            self.log.error(f"api autodisc: {api_autodiscovery}, ui autodisc: {ui_autodiscovery}")
            raise CVTestStepFailure("Autodiscovery/DLP validation failed")
        else:
            self.log.info("Autodiscovery validation successful")
        if edit:
            self.__company_details.edit_general_settings({
                'auto_discover_applications': True
            })
            self.validate_autodiscovery(company=company, edit=False)

    def setup_theme_page(self, company: str) -> None:
        """
        Navigates to themes page of company level (by switching to idp as operator)

        Args:
            company (str)   -   name of company to edit theme of
        
        Returns:
            None
        """
        as_operator = self.__navigator.operating_company_displayed()
        already_operator = as_operator and as_operator.lower() == company.lower()
        company_idp = self._displayname(
            self._organizations.all_organizations_props[company.lower()]['home_commcell'])
        if self._is_msp_level() and not already_operator:
            self.__navigator.switch_company_as_operator(f"{company} ({company_idp})")
        else:
            self.__navigator.switch_service_commcell(company_idp)
        self.__navigator.navigate_to_theme()

    @test_step
    def validate_theme(self, company: str = None, edit: bool = True, reset: bool = True) -> None:
        """
        Validates company level theme in themes page

        Args:
            company (str)   -   name of company
            edit    (bool)  -   changes Theme if True
            reset   (bool)  -   resets theme to default if True

        Returns:
            None
        
        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        if not company:
            company = self._company_name
        elif company == 'child':
            company = self._child_name

        org = self._local_organizations().get(company)

        if edit:
            self.setup_theme_page(company)
            random_theme = self.get_random_theme()
            self.log.info(f"Setting random color theme {random_theme}")
            self.__themes_page.set_color_settings(**random_theme)

        self.__navigator.navigate_to_theme()
        self.log.info("Validating Company Theme")
        ui_theme = self.changed_theme(self.__themes_page.get_theme_values())
        api_theme = org.company_theme
        theme_diff = self.compare_themes(ui_theme, api_theme)

        for _ in range(10):
            if theme_diff:
                self.log.warning("Themes mismatch, retrying after 10 seconds")
                time.sleep(10)
                org.refresh()
            else:
                self.log.info("Theme successfully validated")
                if reset:
                    self.__themes_page.reset_theme()
                self.__navigator.navigate_to_dashboard()
                self.__admin_console.refresh_page()
                return
            api_theme = org.company_theme
            theme_diff = self.compare_themes(ui_theme, api_theme)

        self.log.error(f'DB Theme: {api_theme}')
        self.log.error(f'UI Theme: {ui_theme}')
        self.log.error(f'difference: {theme_diff}')
        raise CVTestStepFailure(f"Theme setting mismatch/missing!")

    @test_step
    def validate_visible_theme(self, company: str = None, edit: bool = False, ui_data: dict = None) -> None:
        """
        Validates theme visible as current user under company

        Args:
            company (str)   -   name of company
            edit    (bool)  -   changes the theme first if True
            ui_data (dict)  -   nav colors data

        Returns:
            None
        
        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        if not company:
            company = self._company_name
        elif company == 'child':
            company = self._child_name

        org = self._local_organizations().get(company)

        if edit:
            # TODO - add themes API edit and refresh logic
            pass

        if ui_data is None:
            ui_data = self.__navigator.get_nav_colors()

        api_theme = org.company_theme
        visible_theme = self.changed_theme(ui_data)
        theme_diff = self.compare_themes(visible_theme, api_theme)

        for _ in range(10):
            if theme_diff:
                self.log.warning("Themes mismatch, retrying after 10 seconds")
                time.sleep(10)
                org.refresh()
            else:
                self.log.info("Visible Theme successfully validated")
                return
            api_theme = org.company_theme
            theme_diff = self.compare_themes(visible_theme, api_theme)

        self.log.error(f'DB Theme: {api_theme}')
        self.log.error(f'Visible Theme: {visible_theme}')
        self.log.error(f'difference: {theme_diff}')
        raise CVTestStepFailure(f"Theme setting mismatch/missing!")

    def _validate_overview_panels(self, exclusions: Union[str, list] = 'all', edit_list: Union[str, list] = '') -> None:
        """
        Validates the 6 synced reseller properties in Company Overview page
        
        Args:
            exclusions  (str/list)  -   reseller properties to ignore on absence from UI
                                        (dlp/autodiscovery/operators/contacts/tags/all)
                                        (can be comma seperated string or list)
            edit_list   (str/list)  -   list of properties to validate with edit 
                                        (dlp/autodiscovery/operators/contacts/tags/all)
                                        (can be comma seperated string or list)
        
        Returns:
            None
        
        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        overview_details = self.__company_details.company_info()
        general = overview_details.get('General', {})

        ui_data = {
            'dlp': general.get('Allow owners to enable data encryption'),
            'autodiscovery': general.get('Auto discover applications') or general.get('Enable auto discover'),
            'operators': overview_details.get('Operators'),
            'contacts': overview_details.get('Contacts'),
            'tags': overview_details.get('Tags'),
        }

        try:
            ui_data['themes'] = self.__navigator.get_nav_colors()
        except Exception as e:
            if 'themes' in exclusions or 'all' in exclusions:
                pass
            else:
                self.log.error('Theme Colors Failed to be read')
                raise e

        for synced_prop in ui_data:
            if ui_data[synced_prop] is None:
                if synced_prop in exclusions or 'all' in exclusions:
                    self.log.info(f"Skipping property {synced_prop} sync test as it is not visible")
                    continue
                else:
                    self.log.error(f'Overview Data: {overview_details}')
                    raise CVTestStepFailure(f'Overview Page missing property/panel for {synced_prop}')

            self.sync_properties[synced_prop](edit=(synced_prop in edit_list), ui_data=ui_data[synced_prop])

    @test_step
    def validate_associated_commcells(self, company: str = None, links: bool = True,
                                      exclusions: Union[str, list] = 'all') -> None:
        """
        Validates the associated commcells panel in company overview under reseller

        Args:
            company     (str)       -   name of reseller to validate for
            links       (bool)      -   verifies the associated commcell links redirection if True
            exclusions  (str/list)  -   synced properties to ignore absence in UI
                                        (dlp/autodiscovery/operators/contacts/tags/all)

        Returns:
            None
        
        Raises:
            CVTestStepFailure   -   if failed to validate
        """
        self.log.info("Validating associated commcells")
        if not company:
            company = self._company_name
        elif company == 'child':
            company = self._child_name

        self.setup_company_overview(company)

        ui_associated_commcells = self.__company_details.get_associated_commcells()
        api_associated_commcells = [
            assoc["entity"]["entityName"]
            for assoc in self._router_commcell.get_service_commcell_associations(
                self._local_organizations().get(company)
            )
        ]
        if sorted(ui_associated_commcells) == sorted(api_associated_commcells):
            self.log.info("Associated commcells verified")
        else:
            self.log.error(f"UI Associated Commcells: {ui_associated_commcells}")
            self.log.error(f"API Associated Commcells: {api_associated_commcells}")
            raise CVTestStepFailure("UI Associated commcells do not match API returned")

        if links:
            self.log.info("Validating associated commcell links")

            icon, current_commcell = self.__navigator.service_commcell_displayed()
            current_company = self.__navigator.operating_company_displayed()

            for commcell_name in ui_associated_commcells:
                self.__company_details.access_associated_commcell(commcell_name)
                self.__admin_console.close_popup()

                if self.complete_guided_setup(current_commcell, current_company):
                    self.setup_company_overview(company)
                    self.__company_details.access_associated_commcell(commcell_name)

                self._verify_redirect('configure',
                                      self._local_organizations().get(company),
                                      commcell_name)
                self._validate_overview_panels(exclusions)

                self.log.info("returning to original page")
                self.__navigator.switch_service_commcell(current_commcell)
                if current_company:
                    self.log.info("returning to original operating role")
                    self.__navigator.switch_company_as_operator(current_company)
                self.__navigator.navigate_to_companies()
                self.setup_company_overview(company)
                self.log.info("successfully returned to original state")
            self.log.info("Associated Commcells Successfully Verified")

    @test_step
    def validate_sync_properties(self, company: str = None,
                                 exclusions: Union[str, list] = 'all', edit_list: Union[str, list] = '') -> None:
        """
        Validates the synced properties as visible from company details overview tab for each workload's reseller

        Args:
            company     (str)       -   name of reseller
            exclusions  (str/list)  -   synced properties to ignore absence in UI
                                        (dlp/autodiscovery/operators/contacts/tags/all)
            edit_list   (str/list)  -   list of properties to verify edit also
                                        (dlp/autodiscovery/operators/contacts/tags/all)

        Returns:
            None
        
        Raises:
            CVTestStepFailure   -   if failed to validate
        """

        if not company:
            company = self._company_name

        as_msp = self._is_msp_user()
        as_msp_operator = self.__navigator.operating_company_displayed() == company
        as_tenant = self.current_userobj.user_company_name == company
        as_tenant_admin = (self.__navigator.logged_in_user().lower()
                           == self.reseller_idp_as_reseller.commcell_username.lower())
        if not (as_msp or as_msp_operator or as_tenant):
            raise Exception("Use a relevant persona to test, current user is neither msp nor tenant of given company")

        self.log.info(f'Validating reseller properties sync as '
                      f'{"Tenant" if as_tenant else "MSP"} '
                      f'{"Admin" if as_tenant_admin else ""} '
                      f'{"as Operator" if as_msp_operator else ""}')

        if as_tenant_admin:
            self.setup_company_overview(company)
            self._validate_overview_panels(exclusions, edit_list=edit_list)
            return self.validate_associated_commcells(company, links=True, exclusions=exclusions)

        for cs in [self.reseller_idp_as_reseller] + self.reseller_workloads_hostnames:
            self.__navigator.switch_service_commcell(cs.commserv_name)
            if as_msp_operator:
                self.__navigator.switch_company_as_operator(f"{company} ({cs.commserv_name})")
            self.setup_company_overview(company)
            self.log.info(f"Validating Reseller Overview in {cs.commserv_name}")
            if cs == self.reseller_idp_as_reseller:
                self._validate_overview_panels(exclusions, edit_list)
            else:
                self._validate_overview_panels(exclusions)

            self.log.info(f"Reseller Properties verified in {cs.commserv_name}")
        self.log.info(f"Sync properties verified for {company}")
