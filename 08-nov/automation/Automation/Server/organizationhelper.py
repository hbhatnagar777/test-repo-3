# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for performing Domains -> Organization related operations.

OrganizationHelper: Class for performing Organization operations

OrganizationHelper:
    __init__()                  --  Initialize instance of the OrganizationHelper class

    create()                    -- Create Company

    add_domain()                -- Associate a domain to the Company

    get_entity_count()          -- Returns the total number entities associated to an organization

    edit_company_properties()   -- Method to edit an organization's general properties

    associated_entities_count() -- Returns the total count of entities associated to organization from API

    get_company_entities()      -- Returns the total count of entities associated to organization from DB tables

    get_company_clients()       -- Returns the list of clients of company

    check_entity_belongs_to_company()   -- Returns True If an entity belongs to company

    associate_plans()                   --  Associates Plans to company

    switch_default_plans()              --  Sets default plan for a company, One after another

    add_new_msp_user_and_make_operator() --  Creates New MSP user and Makes operator for company

    add_new_company_user_and_make_tenant_admin() -- Creates New Company User and adds the user to Tenant Admin group of company

    add_role()                          -- Creates New Role for an Organization and verifies tagging.

    add_user()                          -- Creates New User for an Organization and verifies tagging.

    add_usergroup()                     -- Creates New User group for an Organization and verifies tagging.

    assign_role_for_user()              -- For a  user, assigns specified role on Organization

    setup_company()                     -- Creates Company with default values and returns dictionary of company details

    run_backup_on_company_client()      -- With specified details picks client and runs backup on it.

    get_tfa_status()                    -- Verifies the two-factor authentication status

    enable_tfa()                        -- Enables two-factor authentication at commcell level/organization level

    disable_tfa()                       -- Disables two-factor authentication at commcell level/organization level

    get_tfa_pin()                       -- Fetches the two-factor authentication pin from the mail

    cleanup_orgs()                      --  Delete companies that has provided marker in it

    _get_organization_status_from_csdb()--  fetches status of an organization from csdb

    validate_organization_cache_data()  --  validates the data returned from Mongo cache for organization collection

    validate_sort_on_cached_data()      --  validates sort parameter on entity cache API call

    validate_limit_on_cache()           --  validates limit parameter on entity cache API call

    validate_search_on_cache()          --  validates search parameter on entity cache API call

    validate_filter_on_cache()          --  validates fq param on entity cache API call

-----------------------------------------------------------------------
_get_theme()            --  gets the company level theme from DB

simplify_operators()    --  removes id and other data from operators for easier processing

simplify_tags()         --  removes id and other data from tags for easier processing
-----------------------------------------------------------------------

ResellerHelper: Class for performing Reseller operations

ResellerHelper:
    __init__()                  --  Initialize instance of the ResellerHelper class

    setup_reseller()            --  Setup a reseller company with associations

    setup_tenant_admin()        --  Setup tenant admin and logins for existing reseller

    associated_service_commcells() -- Gets the displaynames of commcells associated to reseller

    clean_up()                  --  Deletes Reseller and associations and msp users created

    enable_dlp()                --  Enables and validates the data encryption property

    enable_autodiscovery()      --  Enables and validates the autodiscover clients property

    setup_tenant_user()         --  Setup tenant user to reseller as tenant admin/contact

    setup_msp_user()            --  Setup MSP user in idp and make operator to reseller company

    setup_tags()                --  Setup tags in reseller IDP

    setup_role()                --  Setup roles in idp or workloads at msp level/reseller

    setup_theme()               --  Sets random company level theme

    verify_sync_props()         --  Verifies Reseller properties in IDP are synced to workloads

    verify_sync_continous()     --  Continously checks for properties sync

    create_child_company()      --  Creates and validates child company remotely from IDP

    setup_child_operators()     --  Creates tenant users, roles to test manage operators on child company

    setup_child_tags()          --  Creates tags from workload and idp and verifies sync

    deactivate_child()          --  Deactivates child from IDP and validates in workload

    activate_child()            --  Activates child from IDP and validates in workload

    delete_child()              --  Deletes child and validates from workload

    get_random_permissions()    --  Gets random list of permissions for role

    get_random_theme()          --  Returns dict with theme keys and random color values

    compare_themes()            --  Returns the theme colors that do not match

"""
from datetime import datetime
import inspect

from AutomationUtils import database_helper, logger, config
from AutomationUtils.options_selector import OptionsSelector

from cvpysdk.security.user import Users
from cvpysdk.security.role import Roles
from cvpysdk.commcell import Commcell
from cvpysdk.client import Clients
from cvpysdk.subclient import Subclients, Subclient
import random, time, re
from datetime import timedelta
from cvpysdk.job import JobController, Job
from cvpysdk.security.usergroup import UserGroups
from cvpysdk.security.two_factor_authentication import TwoFactorAuthentication
from exchangelib import Account, UTC
from typing import Tuple
import locale


class OrganizationHelper(object):
    """Helper class to provide Organization related operations on Commcell"""

    def __init__(self, commcell: Commcell, company: str = None):
        """ initialize instance of the OrganizationHelper class

        Args:
            commcell (obj)    -- Commcell object

            company  (str)    -- Organization name
        """

        self._commcell = commcell
        self._company_name = company
        self._company_id = None
        self._company = None
        self._commcell_default_plan = None
        self._tenant_client_group = None
        self.organization = None
        self.tfa_obj = None

        if company is not None:
            self._company_name = company
            self._company = self._commcell.organizations.get(company)
            self._company_id = self._company.organization_id
            self._machine_count = self._company.machine_count
            self._tenant_client_group = None

        self._csdb = database_helper.CommServDatabase(commcell)
        self._options_selector = OptionsSelector(commcell)
        self.log = logger.get_log()
        if company is not None: self.organization = self._commcell.organizations.get(self._company_name)
        self.config = config.get_config()
        self._verify_ssl = self.config.API.VERIFY_SSL_CERTIFICATE

    def create(self,
               name=None,
               email=None,
               contact_name=None,
               company_alias=None,
               email_domain=None,
               primary_domain=None,
               default_plans=None):
        """ Create a Tenant company
            Args:

                name            (str)    --      Company name to create

                email           (str)    --      Email associated to the company owner

                contact_name    (str)    --      Contact name for the Company owner

                company_alias   (str)    --      Company alias

                email_domain    (str)    --      Email Domain

                primary_domain  (str)    --      Primary domain associated to the company

                default_plans   (str)    --      Default plan associated to the company

            Returns:
                company_object   (obj)   --      Company object

            Raises
                Exception:
                    In case failed in any step to create company

        """
        try:
            if name is None:
                name = f"DEL Automated - {random.randint(0, 100000)}"
            if contact_name is None:
                contact_name = f"user{random.randint(0, 100000)}"
            if company_alias is None:
                company_alias = f"cvlt{random.randint(0, 100000)}"
            if email is None:
                email = f"{contact_name}@{company_alias}.com"

            args = [name, email, contact_name, company_alias, email_domain, primary_domain, default_plans]
            if self._commcell.organizations.has_organization(name):
                self.log.info("Company [{0}] already exists on commcell".format(name))
                self._company = self._commcell.organizations.get(name)
            else:
                self.log.info("""Creating organization [{0}], with email [{1}], contact name [{2}], company alias[{3}],
                                 email domain [{4}], primary domain [{5}], default plans [{6}]""".format(*args))
                self._company = self._commcell.organizations.add(name=name, email=email, contact_name=contact_name,
                                                                 company_alias=company_alias,
                                                                 email_domain=email_domain,
                                                                 primary_domain=primary_domain,
                                                                 default_plans=default_plans)

            self._company_name = name
            self._machine_count = self._company.machine_count

            return self._company

        except Exception as excp:
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def add_domain(self, domain, netbios, user, password, company_id="", ad_proxy_list=None, enable_sso=True):
        """ Create a domain for the company and associate with it

            Args:
                domain        (str)    - Domain name

                netbios       (str)    - Netbios name for the domain

                user          (str)    - Domain User

                password      (str)    - Domain user password

                company_id    (str)    - Associated company id

                ad_proxy_list (list)   - Active Domain proxy list

                enable_sso    (bool)   - Enablle SSO? (True/False)

            Returns:
                domain object for created domain (obj)

            Raises:
                Exception:
                    - In case failed at any step to create domain
        """
        try:
            args = [domain, netbios, user, password, company_id, ad_proxy_list, enable_sso]
            if self._commcell.domains.has_domain(netbios):
                self.log.info("Domain [{0}] already exists on commcell".format(domain))
                domain = self._commcell.domains.get(netbios)
            else:
                self.log.info("""Creating domain [{0}], with netbios [{1}], user [{2}], pass [{3}], company_id [{4}],
                                 ad_proxy_list [{5}], enable_sso option as [{6}]""".format(*args))
                domain = self._commcell.domains.add(*args)

            return domain

        except Exception as excp:
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def get_company_properties(self):
        """"""
        general_tile_api = {
            "Company created on": self._company.organization_created_on,
            "Company alias": self._company.domain_name,
            "Associated email suffixes": self._company.email_domain_names[0],
            "Requires authcode for installation": self._company.is_auth_code_enabled,
            "Enable two factor authentication": self._company.is_tfa_enabled,
            "Enable reseller mode": self._company.reseller_enabled,
            "Allow owners to enable data encryption": self._company.is_auto_discover_enabled,
            "Enable auto discover": self._company.is_auto_discover_enabled,
            "Infrastructure type": self._company.infrastructure_type,
            "Supported solutions": self._company.supported_solutions,
            "Job start time": self._company.job_start_time,
            "Password ages in": str(
                self._company.password_age_days) + ' day(s)' if self._company.password_age_days else 'Password age not set',
            "Download software from internet": self._company.is_download_software_from_internet_enabled,
            "User session timeout value": self._company.user_session_timeout
        }

        return general_tile_api

    @property
    def company_smart_client_group_object(self):
        """Returns smart client group object"""
        for client_group in self._company.client_groups.keys():
            client_grp_object = self._commcell.client_groups.get(client_group)
            if client_grp_object.is_smart_client_group:
                return client_grp_object

    @property
    def company_id(self):
        """Returns company id"""
        return self._company_id

    def edit_company_properties(self, properties_dict):
        """
        Method to edit an organization's general properties

        Args:
                properties_dict (dict): Dict containing the properties to be changed
                Eg.
                    properties_dict = {
                        "newName": "string",
                        "general": {
                            "newAlias": "string",
                            "emailSuffix": "string",
                            "authcodeForInstallation": true,
                            "twoFactorAuth": {
                                "enable": true,
                                "all": true,
                                "userGroups": [
                                    {
                                        "id": 0,
                                        "name": "string"
                                    }
                                ]
                            },
                            "resellerMode": true,
                            "enableDataEncryption": true,
                            "autoDiscoverApp": true,
                            "infrastructureType": "RENTED_STORAGE",
                            "supportedSolutions": [
                                "FILE_SERVER"
                            ],
                            "assignLaptopOwners": "LOGGED_IN_ACTIVE_DIRECTORY_USERS",
                        }
                    }

        Returns:
                None
        """

        if isinstance(properties_dict, dict):
            self.log.info(
                f"Setting following properties {properties_dict} to organization with name {self._company_name}")
            self._company.update_general_settings(properties_dict)

    def get_entity_count(self, entity_name):
        """Get count for specific entity for a company"""
        self._csdb.execute(f"""select count(*)
                   from App_CompanyEntities, App_Entity
                   WHERE App_CompanyEntities.entityType=App_Entity.entityType
                   and App_Entity.entityTypeName like '{entity_name}'
                   and App_CompanyEntities.companyId = {self._company_id}""")
        query_result = self._csdb.fetch_all_rows()
        return int(query_result[0][0])

    def associated_entities_count(self):
        """Get associated entities count for a company"""
        self._commcell.refresh()
        return self._commcell.organizations.all_organizations_props[self._company_name.lower()]['count']

    def __get_company_laptop_count(self):
        """Get the count of laptops associated to a company"""
        self._csdb.execute(f"""
                            select count(*) from app_client 
                            where status & 4096=4096 and id in 
                                (select entityId from app_companyentities
                                 where companyId = {self._company_id} and entityType in (3))
                            """)
        query_result = self._csdb.fetch_all_rows()
        return int(query_result[0][0])

    def __get_company_ma_count(self):
        """Get the count of media agent associated to a company"""
        self._csdb.execute(f"""
                            (select count(entityId) from app_companyentities
                            where companyId = {self._company_id} and entityType in (11))
                            """)
        query_result = self._csdb.fetch_all_rows()
        return int(query_result[0][0])

    def __get_company_file_servers_count(self):
        """Get the count of file servers associated to a company"""
        laptop_count = self.__get_company_laptop_count()
        self._csdb.execute(f"""
                            (select count(entityId) from app_companyentities
                            where companyId = {self._company_id} and entityType in (3))
                            """)
        query_result = self._csdb.fetch_all_rows()
        return int(query_result[0][0]) - laptop_count

    def __get_roles_count(self):
        """Get count for specific entity for a company"""
        self._csdb.execute(f"""select count(*)
                   from App_CompanyEntities, App_Entity
                   WHERE App_CompanyEntities.entityType=App_Entity.entityType
                   and App_Entity.entityType = 120
                   and App_CompanyEntities.companyId = {self._company_id}""")
        query_result = self._csdb.fetch_all_rows()
        return int(query_result[0][0])

    def get_company_entities(self):
        """Get count for company entities that have pages on adminconsole"""
        # We covered basic entities, please add count for your entities if they appear on associated count popup
        # on company listing page

        self._csdb.execute(f"select count(*) from UMUsers where companyId={self._company_id} and flags in (1, 1025)")
        user_count = int(self._csdb.fetch_all_rows()[0][0])

        plans_count = self.get_entity_count('Plan')

        alert_count = self.get_entity_count('Alert')

        usergroup_count = self.get_entity_count('user group') - 1

        file_server_count = self.__get_company_file_servers_count()

        laptop_count = self.__get_company_laptop_count()

        ma_count = self.__get_company_ma_count()

        servergroup_group = self.get_entity_count("clientgroup")

        roles_count = self.__get_roles_count()

        total_count = user_count + plans_count + alert_count + usergroup_count + file_server_count \
                      + servergroup_group + ma_count + roles_count + laptop_count

        return total_count

    def get_company_clients(self):
        """Returns the list of clients of the company

        Raises:
                        Exception:
                            - if failed to update data in DB
        """
        clients = []
        company_id = self.organization.organization_id
        query = f'''DECLARE @inClientId INT = 0/*GetAllClients*/;
                    DECLARE @inSCGId INT = 0/*SCGProcessing*/;
                    select name from app_client where id in ((
                     SELECT clientId FROM dbo.scgV2CompanyClientAssociations('=', {company_id}  , @inClientId, @inSCGId )
                    )  UNION  (
                     SELECT clientId FROM dbo.scgV2CompanyClientInstallAssociations('=', {company_id}  , @inClientId, @inSCGId )
                    ));'''

        records = self._options_selector.update_commserve_db_via_cre(sql=query)
        for client in records:
            clients.append(client[0])

        return clients

    def check_entity_belongs_to_company(self, entity_type, entity_id):
        """This Methods Checks whether given entity is properly tagged to company
        Args:
            entity_type (int)  -- Entity type
            entity_id   (int)  -- Entity ID
        Returns:
            result (bool) -- Returns True, If Entity is tagged to company else Returns False.
        """
        self._csdb.execute(
            f"select count(*) from App_CompanyEntities where companyId = {self._company.organization_id} and entityType = {entity_type} and entityId = {entity_id}")
        count = int(self._csdb.fetch_all_rows()[0][0])
        return True if count else False

    def associate_plans(self, plan_list: list, company_name: str = None):
        """Associate plans to company
        Args:
            plan_list (list)    --  List of plans name, to be associated to company.
            company_name (str)  --  Company Name, If not provided, it will consider self._company_name

        Raises Exception:
                if any of the plan in plan_list, failed to associate to company.
        """
        company = self._commcell.organizations.get(company_name) if company_name else self._company
        self.log.info(f'Associating plans {plan_list} to Company => [{company.name}]...')
        company.plans += plan_list
        if not all([True if plan.lower() in company.plans else False for plan in plan_list]):
            raise Exception('Failed to associate plans to company')

    def switch_default_plans(self, plans_list, server_plans=True):
        """
        This Method will switch server or laptop plan as default plan one after the another.
        Set server_plans = False, If plans_list is of laptop plans
        Args:
            plans_list (list)    --  list of plans, these plans are set as default one after another.
            server_plans (bool)  --  By default, Server Plans is considered. If plans_list is full of laptop plans, Set server_plans = False.

        Raises Exception:
                if failed to set default plan
        """
        self.log.info('Switching default plans...')
        for plan in plans_list:
            self._company.default_plan = {'Server Plan' if server_plans else 'Laptop Plan': plan}
            if plan.lower() not in [i.lower() for i in self._company.default_plan]:
                raise Exception('Failed to set default Plan')

    def add_new_msp_user_and_make_operator(self, user_name, password):
        """Creates new MSP user and makes him tenant operator of company"""
        self.log.info('Creating new user and making him as operator...')
        is_company_user = '\\' in self._commcell.commcell_username
        domain_name = self._commcell.commcell_username.split('\\')[0] if is_company_user else None
        users = Users(self._commcell)
        self.log.info(f'Creating new user and making him as operator... [User Name: {user_name}] [Domain: {domain_name}]')
        user = users.add(
            user_name=user_name,
            email=f'mspuser{random.randint(0, 10000)}@gmail.com',
            password=password,
        )
        
        if is_company_user:
            user_name = domain_name + '\\' + user_name
        
        if not users.has_user(user_name):
            raise Exception('Failed to create MSP user')
        self._company.add_users_as_operator([user_name], 'UPDATE')
        return user

    def add_new_company_user_and_make_tenant_admin(self, user_name: str, password: str) -> object:
        """Creates a new company user and makes them a tenant admin of the company.

        Args:
            user_name (str): The username for the new company user.
            password (str): The password for the new company user.

        Returns:
            User obj: The newly created user object.
        """
        if '\\' not in user_name:
            user_name = self._company.domain_name + '\\' + user_name

        email = f'companyuser{random.randint(0, 10000)}@commvault.com'

        log_message = f'Creating new user and making them a Tenant Admin of the company... [User Name: {user_name}] [Email: {email}] [Password: {password}]'
        self.log.info(log_message)

        users = Users(self._commcell)

        new_user = users.add(user_name=user_name, email=email,
                             password=password, local_usergroups=[self._company.domain_name + '\\Tenant Admin'],
                             full_name=f"User {self._company.domain_name}")

        if not users.has_user(user_name):
            raise Exception('Failed to create company user')

        return new_user

    def add_role(self, role_name, permissions):
        """Creates New Company Role and Verifies Whether tagged to company or not
        Args:
            role_name (str)     --   New Role Name
            permissions (list)  --   List of Permissions for New Role
        Raises Exception:
                if you are trying to create role for company as MSP.
                if Role Creation Failed.
                If Created role isnt tagged to company.
        """
        self.log.info(f'Creating Role : {role_name}')
        roles_obj = Roles(self._commcell)
        roles_obj.add(rolename=role_name, permission_list=permissions)

        if roles_obj.get(role_name).company_name.lower() != self._company.domain_name.lower():
            raise Exception('New Role Failed to tagged to the Company')

    def add_user(self, user_name, password):
        """Creates New Company User and Verifies Whether tagged to company or not
        Args:
            user_name (str) --   User Name.
            password (str)  --   Password for New User.

        Raises Exception:
                if user creation failed.
                if user isnt tagged to company.
        """
        self.log.info(f'Creating Company User : {user_name}')
        if '\\' not in user_name:
            user_name = self._company.domain_name + '\\' + user_name

        users = Users(self._commcell)
        users.add(user_name=user_name, email='companyuser' + str(random.randint(0, 10000)) + '@gmail.com',
                  password=password)

        if users.get(user_name).user_company_name.lower() != self._company.domain_name.lower():
            raise Exception('New User Failed to tagged to the Company')

    def add_usergroup(self, usergroup_name):
        """Creates New Company User Group and Verifies Whether tagged to company or not
        Args:
            usergroup_name (str) -- New User Group Name.

        Raises Exception:
                if user group creation failed.
                if user group isnt tagged to company.
        """
        self.log.info(f'Creating Company User group : {usergroup_name}')
        ugrps = UserGroups(self._commcell)
        ugrps.add(usergroup_name=usergroup_name, domain=self._company.domain_name)

        if ugrps.get(
                self._company.domain_name + '\\' + usergroup_name).company_name.lower() != self._company.domain_name.lower():
            raise Exception('New Usergroup Failed to tagged to the Company')

    def assign_role_for_user(self, user_name, role):
        """This Method Assigns role for a given user
        Args:
            user_name (str) : name of a user to whom role is to be associated.
            role (str)      : Existing Role Name

        Raises Exception:
                if role association failed for a specified user.
        """
        self.log.info('Assigning role for a given user...')
        self._company.update_security_associations(user_name, role, 'UPDATE')
        security_associations = self._company.get_security_associations().get(user_name, None)

        if not (security_associations and (role in security_associations)):
            raise Exception('Role Assign Failed for a given user')

    def setup_company(self, company_name=None, domain_name=None, email=None, plans=None,
                      ta_password=None, to_password=None):
        """
        This method will create company and returns dictionary with details of company created

        Args:
            company_name (str)   -- Company Name (optional).
            domain_name  (str)   -- Company Domain or Alias (optional).
            email (str)          -- Email adress of Tenant Admin (optional).
            plans (list)         -- Plans to be associated while company creation (optional).
            ta_password (str)    -- Tenant admin password, Creates New TA with specified password (optional).
            to_password (str)    -- Operator password, Creates New MSP user and makes him operator for this company (optional).

        Returns:
            company_details (dict)  -- It will have the information of created company.

            company_details = {
                'company_obj' : User can make use of this object, to get details or make changes directly on the company,
                'company_name' : ,
                'company_alias' : ,
                'associated_plans' : ,
                'contact_name' : ,
                'ta_name' : ,
                'ta_loginobj' : If password is specified for the Tenant Admin, User will be created and logs in. Use this TA login object, to perform action on Company as TA.
                'to_name' :
                'to_loginobj' : Tenant Operator Login Object. Switch to this company using this login object to Get Complete rights as Operator.
            }
        """
        results = {}
        results['company_obj'] = company_obj = self.create(name=company_name, email=email, company_alias=domain_name,
                                                           default_plans=plans)
        results['company_name'] = company_obj.organization_name
        results['company_alias'] = company_obj.domain_name
        results['associated_plans'] = company_obj.plans
        results['contact_name'] = company_obj.contacts[0]

        if ta_password:
            self.log.info('Configuring Tenant Admin for Company....')
            results['ta_name'] = results['company_alias'] + '\\' + 'tauser' + str(random.randint(0, 100000))
            self.add_new_company_user_and_make_tenant_admin(user_name=results['ta_name'], password=ta_password)
            results['ta_loginobj'] = Commcell(self._commcell.webconsole_hostname, commcell_username=results['ta_name'],
                                              commcell_password=ta_password, verify_ssl=self._verify_ssl)

        if to_password:
            self.log.info('Configuring Tenant Operator for Company....')
            results['to_name'] = f'del_automated_mspuser{random.randint(0, 100000)}'
            user = self.add_new_msp_user_and_make_operator(user_name=results['to_name'], password=to_password)
            self.log.info(f"Logging in as {user.user_name}..")
            results['to_loginobj'] = Commcell(self._commcell.webconsole_hostname, commcell_username=user.user_name,
                                              commcell_password=to_password, verify_ssl=self._verify_ssl)

        return results

    def run_backup_on_company_client(self, value={}) -> Tuple[Subclient, Job]:
        """
        This is helper function to run backup on clients
        Args:
            value (dict)  -- Backup Details (Optional)

            example:
                value = {
                    'client_display_name' : None,
                    'agent' : None,
                    'backupset_name' : None,
                    'subclient_name' : None,
                    'plan_name' : None,
                    'backup_level' : None
                }

        If client_display_name is None, picks random client and runs backup
        "File System", "defaultBackupSet" and "default" subclient are default Values.
        if plan is specified, plan will be associated to subclient.
        backup_level : "Incremental" (default) | "Full"

        Returns:
            subclient , job (tuple)  -- Returns Subclient Object and Running Job Instance

        Raises:
            Exception:
                if input is of not dict type

                if specified client is not found
        """

        if not isinstance(value, dict):
            raise Exception('Input should be dictionary')

        company_clients = Clients(self._commcell).all_clients

        if value.get('client_display_name', None) is None:
            client_name = random.choice(list(company_clients.keys()))
        else:
            keys, values = list(company_clients.keys()), list(company_clients.values())
            for properties in company_clients.values():
                if properties['displayName'] == value.get('client_display_name', None).lower():
                    client_name = keys[values.index(properties)].lower()  # returns client name from display name
                    break
            else:
                raise Exception('Client with specified Display name not found for the user.')

        agent = 'File System' if value.get('agent', None) is None else value['agent']
        backupset = 'defaultBackupSet' if value.get('backupset_name', None) is None else value['backupset_name']
        subclient = 'default' if value.get('subclient_name', None) is None else value['subclient_name']
        self.log.info(f'Client Name : {client_name}')
        self.log.info(f'Agent Name : {agent}')
        self.log.info(f'Backupset Name : {backupset}')
        self.log.info(f'Subclient Name : {subclient}')

        subclient = Subclients(
            self._commcell.clients.get(client_name).agents.get(agent).backupsets.get(backupset)).get(subclient)

        if value.get('plan_name', None): subclient.plan = value['plan_name']

        backup_level = 'Incremental' if value.get('backup_level', None) is None else value['backup_level']
        job = subclient.backup(backup_level)
        self.log.info(f'Started {backup_level} backup..')
        return subclient, job

    def enable_reseller_and_verify(self):
        """Method to Enable Reseller Mode and Give Verification"""
        self._company.reseller_enabled = True
        if not self._company.reseller_enabled:
            raise Exception('Failed to Enable Reseller Mode for an Organization')

    def _get_media_agent(self):
        """To Fetch only active Media agent, Returns Media Agent Name if it is available"""
        self.log.info('Selecting Media Agent with Checking readiness..')
        media_agents = list(self._commcell.media_agents.all_media_agents.keys())
        for media_agent in media_agents:
            if self._commcell.media_agents.get(media_agent_name=media_agent).is_online:
                self.log.info(f'MA [{media_agent}] is ready..')
                ma = media_agent
                break
        else:
            raise Exception('None of the Media Agent is Ready!')
        return ma

    def __create_storage_pool(self):
        """Method to create storage pool using available online media agent"""
        media_agent_name = self._get_media_agent()
        storage_pool_name = "AutoStoragePool" + str(random.randint(0, 100000))
        self.log.info(f'Creating New Storage Pool : [{storage_pool_name}] on MA [{media_agent_name}]...')
        is_linux = 'linux' in self._commcell.clients.get(media_agent_name).os_info.lower()

        if is_linux:
            spool = self._commcell.storage_pools.add(storage_pool_name=storage_pool_name,
                                                        mountpath="/home/AutoMountPaths/" + storage_pool_name + "_path",
                                                        media_agent=media_agent_name)
        else:
            spool = self._commcell.storage_pools.add(storage_pool_name=storage_pool_name,
                                                    mountpath="c:\\AutoMountPaths\\" + storage_pool_name + "_path",
                                                    media_agent=media_agent_name,
                                                    ddb_ma=media_agent_name,
                                                    dedup_path="c:\\AutoMountPaths\\" + storage_pool_name + "_path\\DDB")
        return spool

    def create_plan_with_available_resource(self, plan_name=None, create_new_pool=False):
        """
        Checks if there is storage pool available and Creates Plan on it with default values.
        If storage pool is not available, creates storage pool on available media agent.
        If Media agent is not available, Raises Exception
        """
        self.log.info('Looking for resource to create plan...')
        spool, plan = None, None
        if not create_new_pool and self._commcell.storage_pools.all_storage_pools:
            self.log.info('Storage Pool available...')
            self.storage_pool_name = random.choice(list(self._commcell.storage_pools.all_storage_pools.keys()))
            self.log.info(f'Selected Storage Pool : {self.storage_pool_name} for Plan Creation. Out of available pools [{list(self._commcell.storage_pools.all_storage_pools.keys())}]')
        else:
            if self._commcell.media_agents.all_media_agents:
                self.log.info('Storage was not available for the user.. Creating storage on available media agent..')
                self.spool = self.__create_storage_pool()
                self.storage_pool_name = self.spool.storage_pool_name
            else:
                raise Exception('No Media Agent available in the setup!')

        self.log.info(f'Creating plan: [{plan_name}] using storage pool: [{self.storage_pool_name}]...')
        plan = self._commcell.plans.add(
            plan_name=plan_name
            if plan_name
            else f"DEL Automated_plan_{random.randint(0, 100000)}",
            plan_sub_type='Server',
            storage_pool_name=self.storage_pool_name,
            override_entities= {}
        )
        self.log.info(f'Created Plan : {plan.plan_name}')
        return spool, plan

    def share_storage_with_company(self, storage_pool_name: str, company_name: str=None):
        """
        On Specified Storage Pool, Agent Management, Administrative Management and View Permission will be given for company's tenant admin group

        Args:
            storage_pool_name (str)     --     Storage Pool, which will be shared with the specified company
            company_name (str)          --     Company name for which storage pool rights to be given
        """
        if not self._commcell.roles.has_role('Share Storage'):
            self._commcell.roles.add(rolename='Share Storage', permission_list=['Create Storage Policy', 'Create Storage Policy Copy', 'View'])

        if company_name:
            domain_name = self._commcell.organizations.get(company_name).domain_name
            usergroup_name = f"{domain_name}\\Tenant Admin"
        else:
            usergroup_name = self._company.domain_name + '\\Tenant Admin'
        
        self.log.info(f'Sharing Storage Pool : {storage_pool_name} with Usergroup : {usergroup_name}')
        storage_pool = self._commcell.storage_pools.get(storage_pool_name)
        storage_pool.update_security_associations(
            associations_list=[{'user_name': usergroup_name, 'role_name': 'Share Storage'}], isUser=False,
            request_type='UPDATE')
        self.log.info('Shared Storage with company...')

    def share_random_msp_storage_with_company(self, company_name: str=None):
        """Looks for MSP Storage Pool, If available it will be shared with the company."""
        available = list(self._commcell.storage_pools.all_storage_pools.keys())
        for storage_pool in available:  # if it is company storage pool. It will raise exception. So will try next storage pool on exception.
            try:
                self.log.info(f'Sharing Storage Pool : {storage_pool}')
                self.share_storage_with_company(storage_pool_name=storage_pool, company_name=company_name)
                self.log.info(f'Shared storage Pool : {storage_pool} with company..')
                return self._commcell.storage_pools.get(storage_pool)
            except Exception as err:
                self.log.info(f'Exception while sharing storage : {err}')

    def create_new_storage_share_with_company(self):
        """Creates new storage pool on available MA and Shares the storage pool with company"""
        self.log.info('Creating and Sharing Storage with company...')
        self.storage_pool_object = self.__create_storage_pool()

        self.log.info('Sharing Storage with the company...')
        self.share_storage_with_company(storage_pool_name=self.storage_pool_object.storage_pool_name)
        return self.storage_pool_object

    def create_plan_for_company(self):
        """
            User will switch to the company and creates plan with available resource

            Returns:
                plan_storage_pool (obj)  --  Storage Pool Object
                plan_object (obj)        --  Plan Object
                created_new_storage_pool (bool) -- True, If New Storage Pool is created and shared with company
        """
        try:
            self.log.info('Creating / Sharing storage pool with company..')
            created_new_storage_pool = False
            storage_pool_object = self.share_random_msp_storage_with_company()
            if not storage_pool_object:
                storage_pool_object = self.create_new_storage_share_with_company()
                created_new_storage_pool = True
        except Exception as err:
            self.log.warn(f'Exception while creating / sharing storage pool : {err}')
            self.log.info('User may not have rights to create/share storage pool. Trying to create plan with available resource..')
            
        self._commcell.switch_to_company(self._company_name)
        self._commcell.refresh()
        self.log.info("Creating plan..")
        plan_storage_pool, plan_object = self.create_plan_with_available_resource()
        self.log.info(f'Newly Created Plan : {plan_object.plan_name}')
        self._commcell.reset_company()
        self._commcell.refresh()
        return storage_pool_object, plan_object, created_new_storage_pool

    def select_or_create_commcell_plan(self):
        """ It will check whether any plan is available. If not, it will create new plan
        If incase new plan is created, Last Argument in return will be set to True"""
        server_plans = list(self._commcell.plans.filter_plans(plan_type='Server', company_name='Commcell').keys())
        self.log.info(f'Avaialable Server Plans : {server_plans}')
        if not server_plans:
            storage_pool_object, plan_object = self.create_plan_with_available_resource()
            self.log.info(f'Newly Created Plan : {plan_object.plan_name}')
            return storage_pool_object, plan_object, True
        else:
            plan_object = self._commcell.plans.get(plan_name=random.choice(server_plans))
            self.log.info(f'Selected Plan : {plan_object.plan_name}')
            return None, plan_object, False

    def activate_company(self):
        """Activates Company and verifies the same"""
        self._company.activate()
        self._company.refresh()
        if self._company.is_backup_disabled:
            raise Exception('Failed to enable backup for company.')
        if self._company.is_restore_disabled:
            raise Exception('Failed to enable restore for company.')
        if self._company.is_login_disabled:
            raise Exception('Failed to enable login for company.')

    def deactivate_company(self, disable_backup=True, disable_restore=True, disable_login=True):
        """
        Deactivates and verifies company successsfully deactivated or not

        Raises:
            Exception:
                if any of property fails to get update.
        """

        if disable_backup or disable_restore or disable_login:
            self._company.deactivate(disable_backup, disable_restore, disable_login)

            if not (disable_backup is self._company.is_backup_disabled):
                raise Exception('Failed to disable backup for company.')
            if not (disable_restore is self._company.is_restore_disabled):
                raise Exception('Failed to disable restore for company.')
            if not (disable_login is self._company.is_login_disabled):
                raise Exception('Failed to disable login for company.')
        else:
            raise Exception('Atleast one of the Activity should be disabled for deactivating company!')

    def delete_company(self, wait=False, timeout=15):
        """if wait == true, It waits for company to get fully deleted until timeout (default : 15 mins)"""
        self._commcell.organizations.delete(self._company.organization_name)

        if not wait:
            return

        start_time = time.time()
        company_not_deleted = True
        while company_not_deleted:
            self.log.info('Waiting for company deletion..')
            time.sleep(30)
            self._commcell.refresh()
            if not self._commcell.organizations.has_organization(self._company.organization_name):
                if not self.check_if_company_fully_deleted():
                    company_not_deleted = False
            waiting_time = (time.time() - start_time) / 60
            if company_not_deleted and waiting_time > timeout:
                break
        else:
            self.log.info("Company Cleanup finished!")

    def _kill_active_jobs_on_client(self, client_name, wait_before_kill=1):
        """By default : If there are any active jobs running on client. It will wait for 1 mins to let the job complete"""
        self.log.info('Checking for Active jobs running on client..')
        jobs = JobController(commcell_object=self._commcell)
        active_jobs = jobs.active_jobs(client_name=client_name)
        self.log.info(f'Active Jobs on Client [{client_name}] -> {active_jobs}')

        for job in list(active_jobs.keys()):  # We cant uninstall client, if there are active jobs running on client
            job = jobs.get(job_id=job)
            if job.status == 'Suspended': job.resume()
            job.wait_for_completion(timeout=wait_before_kill)  # will wait if job gets complete within this time.
            try:
                self.log.info(f'Killing Active Job : {job.job_id} as User: {self._commcell.commcell_username}')
                job.kill(wait_for_job_to_kill=True)
            except Exception as error:
                self.log.warning(f'While Killing Active Job: {error}')

    def _wait_for_uninstall_job_to_complete(self, job, timeout, pause_interval):
        """job will be paused and resume back once job elapsed time reaches pause_interval"""
        start_time = time.time()
        job_completed = False
        job_paused = False
        while not job_completed:
            self.log.info('Waiting for job completion..')
            time.sleep(30)
            if job.is_finished: job_completed = True

            waiting_time = (time.time() - start_time) / 60
            if (not job_completed) and (waiting_time > timeout):
                # job.kill(wait_for_job_to_kill= True)
                break
            if pause_interval > waiting_time and (
            not job_paused):  # Kind of refreshing job, if it is struck at some percent
                try:  # sometimes we can't pause jobs
                    job.pause(wait_for_job_to_pause=True)
                    job.resume()
                    job_paused = True
                except Exception as error:
                    self.log.info(error)
        else:
            self.log.info("Job Completed!")

    def uninstall_client(self, client_name):
        """ Completely removes client from Commcell - If MA is installed, MA package will be removed first"""
        self.log.info(f'hostname : {client_name}')
        jobs = JobController(commcell_object=self._commcell)
        self._commcell.clients.refresh()
        if self._commcell.clients.has_client(client_name=client_name):
            self.log.info('Client Found.. Trying to Uninstall..')
            client_obj = self._commcell.clients.get(name=client_name)
            self._kill_active_jobs_on_client(
                client_name=client_obj.client_name)  # if there is any active job running on client, Uninstallation Fails. So kiilling jobs

            if self._commcell.media_agents.has_media_agent(media_agent_name=client_obj.client_name):
                self.log.info('MA is present on the client. Uninstalling media agent first..')
                self._commcell.media_agents.delete(media_agent=client_obj.client_name, force=True)
                # Deleting MA doesnt return job ID, So checking for active jobs on client to get job id.
                active_jobs = jobs.active_jobs(client_name=client_obj.client_name, job_filter='UNINSTALLCLIENT')
                if active_jobs:
                    job = jobs.get(job_id=list(active_jobs.keys())[0])
                    self.log.info(
                        f"Uninstall Client Job Launched Successfully, Will wait until Job: {job.job_id} Completes")
                    self._wait_for_uninstall_job_to_complete(job=job, timeout=15, pause_interval=10)
                    if not job.is_finished: self._wait_for_uninstall_job_to_complete(job=job, timeout=15,
                                                                                     pause_interval=10)  # retry

                    if not job.wait_for_completion():
                        self.log.info(f"{job.job_id} Failed! - Reason : [{job.delay_reason}]")
                        self.log.info(
                            f'{client_obj.client_name} : Media Agent Uninstallation Failed. Reason : [{job.delay_reason}]')
                        return False
                    self.log.info(f'MA uninstallation Job Status : {job.status}')

            job = client_obj.uninstall_software()
            self.log.info(f"Uninstall Client Job Launched Successfully, Will wait until Job: {job.job_id} Completes")
            self._wait_for_uninstall_job_to_complete(job=job, timeout=15, pause_interval=10)
            if not job.wait_for_completion(timeout=60):
                self.log.info("{0} - Client Uninstallation Failed".format(client_obj.client_name))
                self.log.info(f'{client_obj.client_name} Client Uninstallation Failed. Reason : [{job.delay_reason}]')
                return False
            self.log.info('Uninstallation of Existing Client Finished!')
            self._commcell.clients.refresh()
            if self._commcell.clients.has_client(client_obj.client_name):
                self.log.info('Client is in deconfigured state!')
                self._kill_active_jobs_on_client(client_name=client_obj.client_name)
                self._commcell.clients.delete(client_obj.client_name)
                return True
        else:
            self.log.info('No Client Found for uninstallation!')
            return True

    def install_client(self, hostname, username, password, package_list=[702], wait=True):
        """
        Args:
            hostname -- Client IP or Hostname
            username -- Machine Login username
            password -- Machine Login base 64 encoded password
            package_list -- List of package IDs to install on client, eg: For FS + MA [702, 51]
        """
        self.log.info(f'hostname : {hostname}')

        job_install = self._commcell.install_software(
            client_computers=[hostname],
            windows_features=package_list,
            username=username,
            password=password
        )
        if not wait: return job_install
        self.log.info(f"Install Client Job Launched Successfully, Will wait until Job: {job_install.job_id} Completes")
        if not job_install.wait_for_completion():
            self.log.info(f"{hostname} : Client installation Failed. Reason : [{job_install.delay_reason}]")
            return False
        else:
            self.log.info('Client Installation Finished!')
            return True

    def validate_edit_general_settings(self):
        """Editing General Settings of Organization"""
        self.log.info('Editing General Settings..')
        return
        new_alias = 'cvlt' + str(random.randint(0, 100000))
        old_name = self._company.organization_name
        old_alias = self._company.domain_name
        company = self._commcell.organizations.get(name=old_name)
        company.organization_name = self.new_company_name
        if not (company.organization_name == self.new_company_name.lower()): raise Exception(
            'Failed to change name for company!')
        company.organization_name = old_name
        company.domain_name = new_alias
        if not (company.domain_name == new_alias): raise Exception('Failed to change domain for company!')
        company.domain_name = old_alias

    def _generate_random_password(self, length=None):
        import secrets, random
        password_length = length if length else 20

        small = list(range(97, 123))
        large = list(range(65, 91))
        special = list(range(33, 47))
        numbers = list(range(48, 57))

        minimum_req = chr(random.choice(small)) + chr(random.choice(large)) + chr(random.choice(special)) + chr(
            random.choice(numbers))
        pw = secrets.token_urlsafe(password_length) + minimum_req
        self.log.info(f'Generated PW: {pw}')
        return pw

    def validate_edit_security(self, company_user_name=None, role_name=None):
        """For a given user and role, it adds and deletes security association"""
        self.log.info('Editing Security Settings..')
        company = self._commcell.organizations.get(name=self._company.organization_name)

        if not company_user_name:
            company_user_name = company.domain_name + '\\' + 'tenantuser' + str(random.randint(0, 10000))
            self.add_user(user_name=company_user_name, password=self._generate_random_password())

        if not role_name: role_name = 'Tenant Admin'
        # adding security associations
        company.update_security_associations(company_user_name, role_name, 'UPDATE')
        associations = company.get_security_associations().get(company_user_name, [])
        if role_name not in associations:
            raise Exception('Failed to add new security association for company!')

        # deleting security associations
        self.log.info('deleting security associations..')
        company.update_security_associations(company_user_name, role_name, 'DELETE')
        associations = company.get_security_associations().get(company_user_name, [])
        if role_name in associations:
            raise Exception('Failed to delete security association from company!')

    def validate_edit_contact_names(self, company_user_name=None):
        """Editing Contact Names of Organization"""
        self.log.info('Editing Contact Names..')
        company = self._commcell.organizations.get(name=self._company.organization_name)
        if not company_user_name:
            company_user_name = company.domain_name + '\\' + 'tenantuser' + str(random.randint(0, 1000))
            self.add_user(user_name=company_user_name, password=self._generate_random_password())

        self._commcell.users.refresh()
        user = self._commcell.users.get(user_name=company_user_name)

        try:
            company.contacts = [company_user_name]
        except Exception as err:
            self.log.info(f'[Trying out Negative case: Adding Non Tenant Admin to Contact List] : {err}')
        else:
            raise Exception('Non Tenant Admin user can be added to Contact list..!')

        user.add_usergroups(usergroups_list=[company.domain_name + '\\Tenant Admin'])

        company.contacts = [company_user_name]
        if company_user_name not in company.contacts:
            raise Exception('Failed to Change Contact Name')

        try:
            company.contacts = []
        except:
            pass
        else:
            raise Exception('Contact List is Empty Now!')

    def validate_edit_email_settings(self, sender_name=None, sender_email=None):
        """Editing Email Settings of Organization"""
        self.log.info('Editing Email Settings..')
        company = self._commcell.organizations.get(name=self._company.organization_name)

        email_settings = {
            'sender_name': sender_name if sender_name else 'Email Sender',
            'sender_email': sender_email if sender_email else 'email.sender@cmvt.com'
        }

        company.update_email_settings(email_settings=email_settings)

        if company.sender_name != email_settings['sender_name'] or company.sender_email != email_settings[
            'sender_email']:
            raise Exception('Failed to Update Email Settings')

    def validate_edit_site_details(self, primary_site=None, additional_sites=None):
        """Editing Site details of Organization"""
        self.log.info('Editing Site details..')
        company = self._commcell.organizations.get(name=self._company.organization_name)

        random_string = str(random.randint(0, 1000))
        if not primary_site:
            primary_site = f'abcd.{random_string}.com'
        if not additional_sites:
            additional_sites = [f'hello.{random_string}.com', f'world{random_string}.com']

        # adding site info
        company.sites = {'primary_site': primary_site, 'additional_sites': additional_sites}

        if (
            primary_site != company.sites['primary_site']
            or additional_sites.sort() != company.sites['additional_sites'].sort()
        ):
            raise Exception('Failed to update Sites Properties for Organization')

        # clear up site information
        company.sites = {}
        if company.sites['primary_site'] != '' or company.sites['additional_sites'] != []:
            raise Exception('Failed to clear up sites Properties for Organization')

    def validate_edit_plans(self, server_plans=[]):
        """Editing plan details of Organization"""
        self.log.info('Editing Plan associations..')
        created_new_plans = False
        if not server_plans:
            server_plans = list(self._commcell.plans.filter_plans(plan_type='Server', company_name='Commcell').keys())
        if len(server_plans) < 3:
            self.spool1, self.plan1 = self.create_plan_with_available_resource()
            self.spool2, self.plan2 = self.create_plan_with_available_resource()
            plan_list = [self.plan1.plan_name, self.plan2.plan_name]
            created_new_plans = True
        else:
            plan_list = random.sample(server_plans, 2)

        self.log.info(f'Plans : {plan_list}')
        self.associate_plans(plan_list)

        company = self._commcell.organizations.get(name=self._company.organization_name)
        company.dissociate_plans(plan_list)

        if created_new_plans:
            self._commcell.plans.delete(self.plan1.plan_name)
            self._commcell.plans.delete(self.plan2.plan_name)

    def validate_edit_operators(self, delete_user=True):
        """Editing Operators of Organization"""
        self.log.info('Editing Operators for company..')
        self._commcell.refresh()
        is_company_user = '\\' in self._commcell.commcell_username
        domain_name = self._commcell.commcell_username.split('\\')[0] if is_company_user else None
        msp_username = f'del_automated_mspuser{random.randint(0, 1000)}'
        self.add_new_msp_user_and_make_operator(user_name=msp_username, password=self._generate_random_password())
        if is_company_user:
            msp_username = domain_name + '\\' + msp_username
        self.mspuser = self._commcell.users.get(msp_username)
        company = self._commcell.organizations.get(name=self._company.organization_name)
        company.add_users_as_operator(user_list=[msp_username], request_type='DELETE')

        if msp_username in company.tenant_operator.keys():
            raise Exception('Failed to remove user from operator role on Organization')
        if delete_user: self._commcell.users.delete(msp_username, self._commcell.commcell_username)

    def validate_edit_passkey(self, password=None):
        """Editing Passkey properties of Organization"""
        before = self._commcell.get_commcell_properties().get('allowUsersToEnablePasskey')

        # create tenant admin to manage passkey
        tenant_admin_name = self._company.domain_name + '\\' + 'tauser' + str(random.randint(0, 100000))
        ta_password = self._generate_random_password()
        self.add_new_company_user_and_make_tenant_admin(user_name=tenant_admin_name, password=ta_password)
        tenant_admin = Commcell(self._commcell.webconsole_hostname, tenant_admin_name, ta_password,
                                verify_ssl=self._verify_ssl)

        self.log.info('Editing Passkey Settings..')
        company = tenant_admin.organizations.get(name=self._company.organization_name)
        password = password if password else self._generate_random_password()
        try:
            self._commcell.allow_users_to_enable_passkey(flag=False)
            company.passkey(current_password=password, action='enable')
        except Exception as err:
            self.log.info(f'[Negative Case] : {err}')

        self._commcell.allow_users_to_enable_passkey(flag=True)
        company.passkey(current_password=password, action='enable')
        if not company.isPasskeyEnabled: raise Exception('Failed to Enable Passkey')

        company.passkey(current_password=password, action='disable')
        if company.isPasskeyEnabled: raise Exception('Failed to Disable Passkey')

        company.passkey(current_password=password, action='enable')
        company.passkey(current_password=password, action='authorise')
        if not company.isAuthrestoreEnabled: raise Exception('Failed to Enable property : Authorize for restore')

        company.passkey(current_password=password, action='change passkey', new_password=password[::-1])
        try:
            company.passkey(current_password=password, action='disable')  # trying to disable with old password
        except Exception as err:
            self.log.info(f'[Negative Case Trying with Wrong Passkey] : {err}')
            company.passkey(current_password=password[::-1], action='disable')
        else:
            raise Exception('Either Passkey didnt change or Old passkey is still active')

        company.allow_owners_to_enable_passkey(flag=True)
        if not company.isAllowUsersToEnablePasskeyEnabled: raise Exception(
            'Failed to Enable property : Allow owners to enable passkey')

        company.allow_owners_to_enable_passkey(flag=False)
        if company.isAllowUsersToEnablePasskeyEnabled: raise Exception(
            'Failed to Disable property : Allow owners to enable passkey')

        self._commcell.allow_users_to_enable_passkey(flag=before)  # reverting back commcell properties

    def validate_edit_laptop_retire_properties(self):
        """Editing laptop retire properties of Organization"""
        self.log.info('Editing Laptop Retire Properties..')
        company = self._commcell.organizations.get(name=self._company.organization_name)

        retire_days = random.randint(1, 100)
        delete_days = random.randint(retire_days, 1000)

        company.retire_offline_laptops(retire_days, delete_days)

        new_retire_days = company.get_retire_laptop_properties['retireDevicesAfterDays']
        new_delete_days = company.get_retire_laptop_properties['forceDeleteDevicesAfterDays']

        if retire_days != new_retire_days or delete_days != new_delete_days:
            raise Exception('Failed to update retire laptop propeties at organization level')

    def validate_edit_file_exceptions(self, windows_filter=None, unix_filter=None):
        """Editing File Exception at Organization Level"""
        self.log.info('Editing File Exceptions..')
        company = self._commcell.organizations.get(name=self._company.organization_name)
        if not windows_filter: windows_filter = ['*.py', '*.exe']
        if not unix_filter: unix_filter = ['*.apk', '*.mp3']

        # adding up new file exceptions
        company.file_exceptions = {
            'Windows': windows_filter,
            'Unix': unix_filter
        }, 'OVERWRITE'

        if not all([True if filter in company.file_exceptions['Windows'] else False for filter in windows_filter]):
            raise Exception('Failed to update Windows Filter')

        if not all([True if filter in company.file_exceptions['Unix'] else False for filter in unix_filter]):
            raise Exception('Failed to update Unix Filter')

        # clear up file exceptions
        company.file_exceptions = {
            'Windows': [],
            'Unix': []
        }, 'OVERWRITE'
        if company.file_exceptions['Windows'] or company.file_exceptions['Unix']:
            raise Exception('Failed to clear up File exception Filter')

    def validate_edit_tags(self, key=None, value=None):
        """Editing tags of Organization"""
        self.log.info('Editing Tags..')
        company = self._commcell.organizations.get(name=self._company.organization_name)
        if not key: key = 'Team'
        if not value: value = 'Server Core'
        # adding tags
        company.tags = [{
            'name': key,
            'value': value
        }]

        for tag in company.tags:
            company_key = tag.get('name', '')
            company_value = tag.get('value', '')
            if key == company_key and value == company_value:
                break
        else:
            raise Exception('Failed to update tags for an Organization')
        # remove tags
        company.tags = []
        if company.tags:
            raise Exception('Failed to remove tags from Organization')

    def _verify_migration(self, client_obj, company_name):
        """Verifies whether client is present in correct company"""
        client_obj.refresh()
        self.log.info(f'Actual Clients Company : {client_obj.company_name.lower()}')
        self.log.info(f'Expected Clients Company : {company_name.lower()}')
        if client_obj.company_name.lower() != company_name.lower():
            raise Exception('Client Migration Failed')
        self.log.info('verified')

    def validate_change_company(self, client_name, destination_company, move_back_after_validation=True):
        """Moves client to specified company and brings back after validation"""
        client = self._commcell.clients.get(name=client_name)
        old_company = client.company_name.lower()
        destination_company = destination_company.lower()
        self.log.info(f'Old Company of client        : {old_company}')
        self.log.info(f'Destination Company of client   : {destination_company}')

        client.change_company_for_client(destination_company_name=destination_company)
        client_company = 'commcell' if client.company_name == '' else client.company_name.lower()
        self.log.info(f'Migrated to... {client_company}')
        if not (client_company == destination_company): raise Exception(
            'Client Failed to migrate to destination company')
        self.log.info(f'Client : {client_name} successfully migrated!')

        if move_back_after_validation: client.change_company_for_client(
            destination_company_name='commcell' if old_company == '' else old_company)

    def validate_change_company_wrt_plan_assoc(self, client_obj, subclient_obj, msp_plan_name, company1_obj,
                                               company1_plan, company2_obj, parent_company: str = 'Commcell'):
        """"""
        company_1_name = company1_obj.organization_name
        company_2_name = company2_obj.organization_name

        # MSP client with MSP plan
        client_obj.change_company_for_client(parent_company)
        self._verify_migration(client_obj=client_obj, company_name=parent_company)

        self.log.info(
            '1. MSP client with MSP plan => Trying to move the client to target company without and then with the msp plan association to the company')
        subclient_obj.plan = msp_plan_name
        try:
            client_obj.change_company_for_client(company_1_name)
        except:
            pass
        else:
            raise Exception(
                'Client Moved to Destination company, Even though destination company doesnot have rights on plans associated with client')
        company1_obj.plans += [msp_plan_name]  # now associate plans to company and try
        self.log.info(f'Company 1 Plans :{company1_obj.plans}')
        client_obj.change_company_for_client(company_1_name)
        self._verify_migration(client_obj=client_obj, company_name=company_1_name)

        # Company client with MSP plan
        self.log.info(
            '2. Company client with MSP plan => Trying to move the client to the other company without and then with the msp plan association to the company')
        try:
            client_obj.change_company_for_client(company_2_name)
        except:
            pass
        else:
            raise Exception(
                'Client Moved to Destination company, Even though destination company doesnot have rights on plans associated with client')
        company2_obj.plans += [msp_plan_name]
        self.log.info(f'Company 2 Plans :{company2_obj.plans}')
        client_obj.change_company_for_client(company_2_name)
        self._verify_migration(client_obj=client_obj, company_name=company_2_name)
        client_obj.change_company_for_client(parent_company)
        self._verify_migration(client_obj=client_obj, company_name=parent_company)

        self.log.info(
            '3. Company client with Company plan => Trying to move the client to the other company and commcell')
        client_obj.change_company_for_client(company_1_name)
        subclient_obj.plan = company1_plan
        try:
            client_obj.change_company_for_client(company_2_name)
        except:
            pass
        else:
            raise Exception('Company Client associated with Company plan moved to other company')
        try:
            client_obj.change_company_for_client(parent_company)
        except:
            pass
        else:
            raise Exception('Company Client associated with Company plan moved to commcell')
        self._verify_migration(client_obj=client_obj, company_name=company_1_name)

        subclient_obj.plan = None
        company1_obj.plans = [company1_plan]
        company2_obj.plans = []
        self.log.info('Moving Back Client to Commcell..')
        client_obj.change_company_for_client(parent_company)

        self.log.info('Validation wrt to plan association is complete..')

    def validate_server_group_change_company(self):
        """Method to validate change company functionality for server groups"""
        pseudo_clients = [f'pseudo_{random.randint(0, 100000)}' for _ in range(0, 3)]
        client_group_name = f'DEL automated_{random.randint(0, 100000)}'

        self.log.info(f'Creating pseudo clients : {pseudo_clients}')
        for client in pseudo_clients:
            self._commcell.clients.create_pseudo_client(client)

        self.log.info(f'Creating client group : {client_group_name}')
        client_grp = self._commcell.client_groups.add(client_group_name, pseudo_clients)

        self.log.info('Moving client group to a new company...')
        client_grp.change_company(self._company_name)

        self.log.info('Validating the changes...')
        if client_grp.company_name != self._company.domain_name:
            raise Exception('Client Group Change Company Validation Failed!')

        failed = [self._commcell.clients.get(client_name).company_name.lower() != self._company_name.lower() for
                  client_name in pseudo_clients]
        if any(failed):
            raise Exception('All clients didnt migrated to target company')

        self.log.info('Cleaning up the created entities...')
        self._commcell.client_groups.delete(client_group_name)
        for client in pseudo_clients:
            self.log.info(f'Deleting client : {client}')
            self._commcell.clients.delete(client)
        self.log.info('Validation Finished!')

    def install_laptop_client(self, value, wait_for_completion=True):
        """
        value = {
            'os' : 'WINDOWS',
            'machine_hostname' : 'machinename.domain.com',
            'machine_username' : 'domain\\username',
            'machine_password' : 'base 64 encoded password'
        }
        """

        request_json = {
            "taskInfo": {
                "task": {
                    "taskType": "IMMEDIATE"
                },
                "associations": [
                    {
                        "clientSidePackage": True,
                        "consumeLicense": True
                    }
                ],
                "subTasks": [
                    {
                        "subTask": {
                            "subTaskType": "ADMIN",
                            "operationType": "INSTALL_CLIENT"
                        },
                        "options": {
                            "adminOpts": {
                                "clientInstallOption": {
                                    "clientDetails": [
                                        {
                                            "clientEntity": {
                                                "clientName": value['machine_hostname'],
                                                "commCellName": self._commcell.commserv_name
                                            }
                                        }
                                    ],
                                    "installOSType": value['os'],
                                    "discoveryType": "MANUAL",
                                    "installerOption": {
                                        "RemoteClient": False,
                                        "requestType": "PRE_DECLARE_CLIENT",
                                        "User": {
                                            "userName": self._commcell.commcell_username
                                        },
                                        "Operationtype": "INSTALL_CLIENT",
                                        "CommServeHostName": self._commcell.commserv_hostname,
                                        "clientComposition": [
                                            {
                                                "overrideSoftwareCache": False,
                                                "clientInfo": {
                                                    "client": {
                                                        "cvdPort": 0,
                                                        "evmgrcPort": 0
                                                    }
                                                },
                                                "components": {
                                                    "componentInfo": [
                                                        {
                                                            "osType": value['os'],
                                                            "ComponentName": "File System Core",
                                                            "consumeLicense": True,
                                                            "ComponentId": 1,
                                                            "clientSidePackage": True
                                                        }
                                                    ],
                                                    "fileSystem": {
                                                        "configureForLaptopBackups": True
                                                    }
                                                },
                                                "packageDeliveryOption": "CopyPackage",
                                                "clientRoles": {
                                                    "bLaptopBackup": True
                                                }
                                            }
                                        ],
                                        "installFlags": {
                                            "overrideClientInfo": True
                                        }
                                    },
                                    "clientAuthForJob": {
                                        "userName": value['machine_username'],
                                        "password": value['machine_password'],
                                        "confirmPassword": value['machine_password']
                                    }
                                }
                            },
                            "commonOpts": {
                                "subscriptionInfo": "<Api_Subscription subscriptionId =\"11\"/>"
                            }
                        }
                    }
                ]
            }
        }

        CREATE_TASK = self._commcell._services['CREATE_TASK']

        flag, response = self._commcell._cvpysdk_object.make_request(
            'POST', CREATE_TASK, request_json
        )

        if flag:
            if response.json() and 'jobIds' in response.json() and response.json()['jobIds'][0]:

                response_json = response.json()
                jobid = int(response_json["jobIds"][0])
                self.log.info(f'JOB ID : [{jobid}]')
                job_obj = self._commcell.job_controller.get(jobid)
                if not wait_for_completion:
                    return job_obj
            else:
                raise Exception('Failed to get the response')

        else:
            raise Exception(self._commcell._update_response_(response.text))

        self.log.info(f"Install Laptop Client Job Launched Successfully, Will wait until Job: {jobid} Completes")
        if not job_obj.wait_for_completion():
            self.log.info(f"Laptop installation Failed. Reason : [{job_obj.delay_reason}]")
            return False
        else:
            self.log.info('Laptop Installation Finished!')
            return True

    def check_if_company_fully_deleted(self, company_name=None):
        """Returns Number of Entity Left to be deleted"""
        if company_name:
            organization_id = self._commcell.organizations.get(name=company_name).organization_id
        else:
            organization_id = self._company.organization_id
        self._csdb.execute(f"select count(*) from App_CompanyEntities where companyId = {organization_id}")
        count = int(self._csdb.fetch_all_rows()[0][0])
        return count

    def verify_disabled_backup(self, subclient_object, plan_object):
        """Verifying whether Backup is disabled on Company"""
        try:
            subclient_object.plan = plan_object.plan_name
            subclient_object.backup()
        except Exception as err:
            self.log.info(f'[Negative Case] : {err}')
        else:
            raise Exception('Backup is running, even though Data Management activity is disabled')

    def verify_disabled_restore(self, subclient_object):
        """Verifying whether Restore is disabled on Company"""
        try:
            job = subclient_object.restore_in_place(paths=['C:'])
            self.log.info(f'Job Status => {job.status}')
        except Exception as err:
            self.log.info(f'[Negative Case] : {err}')
        else:
            self.log.debug('Job is created. Let us check if the job also successfully started though restore is disabled..')
            jpr = job.summary.get('pendingReason')
            self.log.debug(f'Job Status => [{job.status}] & Job Pending Reason => [{job.pending_reason}]')

            pattern = r"^Data Recovery activity for .+ is disabled\. The Restore job will not run.+"

            if not re.match(pattern, jpr):
                raise Exception(f'Restore is running, even though Data Recovery activity is disabled. Status: [{job.status}] JPR: {jpr}')
            self.log.info('Validation Successful - Restore is disabled')

    def verify_disabled_login(self, company_user, user_password):
        """Verifying whether Login is disabled for Company user"""
        try:
            Commcell(self._commcell.commserv_hostname, company_user, user_password, verify_ssl=self._verify_ssl)
        except Exception as err:
            self.log.info(f'[Negative Case] : {err}')
        else:
            raise Exception('Login is disabled for the company, Still user is able to login.')

    def get_tfa_status(self, commcell, organization_id=None):
        """
        Verifing the two-factor authentication status
            Args:
                commcell (obj)    -- Commcell object

                organization_id   -- id of the organization on which two factor authentication
                                        operations to be performed.

                Returns True if enabled, else False
        """
        self.tfa_obj = TwoFactorAuthentication(commcell, organization_id)
        return self.tfa_obj.is_tfa_enabled

    def enable_tfa(self, commcell, organization_id=None, user_groups=None):
        """Enabling two-factor authentication at commcell level/ organization level
            Args:
                    commcell (obj)    -- Commcell object

                    organization_id   -- id of the organization on which two-factor authentication
                                            operations to be performed.

                    user_groups(list)  --  user group names on which two-factor authentication needs to be enabled
        """
        if organization_id:
            self.log.info(f"Enabling Two Factor Authentication on  {self._company} in  {commcell}")
        else:
            self.log.info(f"Enabling Two Factor Authentication on commcell {commcell}")
        self.tfa_obj = TwoFactorAuthentication(commcell, organization_id)
        self.tfa_obj.enable_tfa(user_groups)
        self.log.info("Successfully enabled Two Factor Authentication")

    def disable_tfa(self, commcell, organization_id=None):
        """Disabling two-factor authentication at commcell level/organization level
            Args:
                commcell (obj)    -- Commcell object

                organization_id   -- id of the organization on which two-factor authentication
                                        operations to be performed.
        """
        if organization_id:
            self.log.info(f"Disabling Two Factor Authentication on {self._company} in {commcell}")
        else:
            self.log.info(f"Disabling Two Factor Authentication on {commcell}")
        self.tfa_obj = TwoFactorAuthentication(commcell, organization_id)
        self.tfa_obj.disable_tfa()
        self.log.info("Successfully disabled Two Factor Authentication")

    def get_tfa_pin(self, configuration, email, sent_time):
        """Fetching the two-factor authentication pin from the mail
            Args:
                configuration(dict): Dictionary with supported keys

                    credentials (dict)
                        client_id  (str)
                        client_secret  (str)
                        tenant_id  (str)
                        identity   (str)
                    auth_type
                    version
                    service_endpoint

                email(str): email address from which the pin must be fetched

                sent_time: email sent time

        """
        self.log.info(f"Fetching the pin from mail {email}")
        account = Account(primary_smtp_address=email, config=configuration, autodiscover=False, default_timezone=UTC)
        pin = None
        for item in account.inbox.all().order_by('-datetime_received')[0:10]:
            # Fetching the received time stamp of the mail
            date_time = datetime(item.datetime_received.year, item.datetime_received.month,
                                 item.datetime_received.day, item.datetime_received.hour,
                                 item.datetime_received.minute)
            local_time = date_time + timedelta(hours=5, minutes=33)
            received_time = int(time.mktime(local_time.timetuple()))
            if item.subject == "CommServe Administrator just doubled your safety!" and \
                    sent_time < received_time:
                message = item.text_body
                temp = re.findall(r'\d+', message)
                values = list(map(int, temp))
                pin = values[-1]
                break
        return pin

    def cleanup_orgs(self, marker):
        """
        Delete companies that has provided marker in it

            Args:
                marker      (str)   --  marker tagged to companies for deletion
        """
        self._commcell.organizations.refresh()

        for org in self._commcell.organizations.all_organizations:
            if marker.lower() in org:
                try:
                    self._commcell.organizations.delete(org)
                    self.log.info("Deleted org - {0}".format(org))
                except Exception as exp:
                    self.log.error(
                        "Unable to delete org {0} due to {1}".format(
                            org,
                            str(exp)
                        )
                    )

    def _get_organization_status_from_csdb(self, organization_id: int) -> int:
        """
        Method to get status of an organization from csdb
        """
        self._csdb.execute(f'select flags from UMDSProviders where id = {organization_id}')
        flags = int(self._csdb.rows[0][0])
        if flags == 0:
            return 1
        elif flags & 0x0010 != 0 and flags & 0x0020 == 0:
            return 2
        else:
            return 3

    def validate_organization_cache_data(self) -> bool:
        """
        Validates the data returned from Mongo cache for organization collection.

        Returns:
            bool: True if validation passes, False otherwise
        """
        self.log.info("Starting validation for organizations cache...")
        cache = self._commcell.organizations.get_organizations_cache(enum=False)
        out_of_sync = []

        for company, cache_data in cache.items():
            self.log.info(f'Validating cache for organization: {company}')
            company_prop = self._commcell.organizations.get(company)
            validations = {
                'id': int(company_prop.organization_id),
                'fullName': company_prop.contacts_fullname if 'fullName' in cache_data else None,
                'providerGUID': self._commcell.organizations.all_organizations_props.get(company).get('GUID').lower(),
                'status': self._get_organization_status_from_csdb(cache_data.get('id')),
                'tags': company_prop.tags if 'tags' in cache_data else None
            }

            for key, expected_value in validations.items():
                self.log.info(f'Comparing key: {key} for company: {company}')
                if expected_value is not None and cache_data.get(key) != expected_value:
                    out_of_sync.append((company, key))
                    self.log.error(f'Cache not in sync for prop "{key}". Cache value: {cache_data.get(key)}; '
                                   f'csdb value: {expected_value}')

        if out_of_sync:
            raise Exception(f'Validation Failed. Cache out of sync: {out_of_sync}')
        else:
            self.log.info('Validation successful. All the organization cache are in sync')
            return True

    def validate_sort_on_cached_data(self) -> bool:
        """
        Method to validate sort parameter on entity cache API call

        Returns:
            bool: True if validation passes, False otherwise
        """
        # setting locale for validating sort
        locale.setlocale(locale.LC_COLLATE, 'English_United States')

        self.log.info("starting Validation for sorting in organizations cache...")
        columns = ['connectName', 'fullName', 'associatedEntitiesCount', 'status', 'providerGUID', 'tags']
        unsorted_col = []
        for col in columns:
            optype = random.choice([1, -1])
            # get sorted cache from Mongo
            cache_res = self._commcell.organizations.get_organizations_cache(fl=[col], sort=[col, optype])
            # sort the sorted list
            if col == 'connectName':
                cache_res = list(cache_res.keys())
                res = sorted(cache_res, key=lambda x: locale.strxfrm(str(x)), reverse=optype == -1)
            else:
                cache_res = [[key, value.get(col)] for key, value in cache_res.items() if col in value]
                if all(isinstance(item[1], int) for item in cache_res):
                    res = sorted(cache_res, key=lambda x: x[1], reverse=optype == -1)
                else:
                    res = sorted(cache_res, key=lambda x: locale.strxfrm(str(x[1])), reverse=optype == -1)

            # check if sorted list got modified
            if res == cache_res:
                self.log.info(f'sort on column {col} working.')
            else:
                self.log.error(f'sort on column {col} not working')
                unsorted_col.append(col)
        if not unsorted_col:
            self.log.info("validation on sorting cache passed!")
            return True
        else:
            raise Exception(f"validation on sorting cache Failed! Column : {unsorted_col}")

    def validate_limit_on_cache(self) -> bool:
        """
        Method to validate limit parameter on entity cache API call

        Returns:
            bool: True if validation passes, False otherwise
        """
        self.log.info("starting Validation for limit in organizations cache...")
        cache = self._commcell.organizations.get_organizations_cache()

        # generate random limit
        test_limit = random.randint(1, len(cache.keys()))
        limited_cache = self._commcell.organizations.get_organizations_cache(limit=['0', str(test_limit)])
        # check the count of entities returned in cache
        if len(limited_cache) == test_limit:
            self.log.info('Validation for limit on cache passed!')
            return True
        else:
            self.log.error(f'limit returned in cache : {len(limited_cache)}; expected limit : {test_limit}')
            raise Exception(f"validation for limit on cache Failed!")

    def validate_search_on_cache(self) -> bool:
        """
        Method to validate search parameter on entity cache API call

        Returns:
            bool: True if validation passes, False otherwise
        """
        self.log.info("starting Validation for search in organizations cache...")
        # creating a test company
        name = f"caching_automation_{random.randint(0, 100000)} - organization"
        company = self.create(name=name)

        if company:
            # calling the API with search param
            response = self._commcell.organizations.get_organizations_cache(search=company.organization_name)
            # checking if test company is present in response
            if len(response.keys()) == 1 and [True for key in response.keys() if key == company.organization_name]:
                self.log.info('Validation for search on cache passed')
                return True
            else:
                self.log.error(f'{company.organization_name} is not returned in the response')
                raise Exception("Validation for search on cache failed!")
        else:
            raise Exception('Failed to create company. Unable to proceed.')

    def validate_filter_on_cache(self, filters: list, expected_response: list) -> bool:
        """
        Method to validate fq param on entity cache API call

        Args:
            filters (list) -- contains the columnName, condition, and value
                e.g. fq = [['connectName','contains','test'],['status','equals','active']]
            expected_response (list) -- expected list of organizations to be returned in response

        Returns:
            bool: True if validation passes, False otherwise
        """
        self.log.info("starting Validation for filters in organizations cache...")
        if not filters or not expected_response:
            raise ValueError('Required parameters not received')

        try:
            res = self._commcell.organizations.get_organizations_cache(fq=filters)
        except Exception as exp:
            self.log.error("Error fetching organizations cache")
            raise Exception(exp)

        missing_companies = [company for company in expected_response if company not in res.keys()]

        if missing_companies:
            raise Exception(f'Validation failed. Missing organizations: {missing_companies}')
        self.log.info("validation for filter on cache passed!")
        return True

    # Helper function to configure and run the testcases in n-level reseller configuration
    def configure_n_level_reseller_company(self, testcase_id: str, commcell: Commcell, level: int, password: str, clients: list=[]) -> dict:
        """
        Method to configure N-level reseller company for backend automation

        Args:
            testcase_id (str)   --  testcase id for which the company needs to be configured
            commcell (obj)      --  Commcell object
            level (int)         --  level of reseller company to be created (MSP-0 > Reseller-1 > Reseller-2)
            password (str)      --  password to be used for company tenant admin
            clients (list)      --  list of clients to be associated with the company

        Returns:
            dict: dict containing the company details as same as setup_company method
        """
        if level < 1:
            raise Exception("Invalid level. Level should be greater than 0")
        reseller_company_info = {}

        self.log.info(f'Creating N-level reseller company for testcase {testcase_id}...')
        for i in range(1, level+1):
            company_name = f'TC {testcase_id} - Reseller {i} - {random.randint(0, 1000)}'
            reseller_company_info = self.setup_company(company_name=company_name, ta_password=password)

            commcell.organizations.get(company_name).reseller_enabled = True

            commcell.switch_to_company(company_name)
            commcell.refresh()

        reseller_company = commcell.organizations.get(reseller_company_info['company_name'])
        reseller_company_name = reseller_company.name
        self.log.info(f'Created reseller company for testcase {testcase_id} => {reseller_company_name}')

        commcell.reset_company()
        commcell.refresh()
        self.log.info('Configuring required steps for reseller company...')

        if clients:
            self.log.info(f'Associating clients [{clients}] to company {reseller_company_name}')
            for client_name in clients:
                subclient = Subclients(self._commcell.clients.get(client_name).agents.get('File System').backupsets.get('defaultBackupSet')).get('default')
                subclient.plan = None  # remove plan to avoid change company blocking

                self.log.info(f'Changing company for client {client_name} to {reseller_company_name}...')
                commcell.clients.get(client_name).change_company_for_client(reseller_company_name)

        self.log.info('Providing full WF permission to company... so that ta users can run queries usind csdb object...')
        req_role = 'All WorkFlow Permissions Role'
        if not self._commcell.roles.has_role(req_role):
            self._commcell.roles.add(rolename=req_role, categoryname_list=['Workflow'])

        user_group_obj = commcell.user_groups.get(f'{reseller_company.domain_name}\\Tenant Admin')
        user_group_obj.update_security_associations(
            entity_dictionary={'assoc1':
                {
                    "commCellName": [commcell.commserv_name],
                    "role": [req_role]
                }}, request_type="UPDATE")

        return reseller_company_info