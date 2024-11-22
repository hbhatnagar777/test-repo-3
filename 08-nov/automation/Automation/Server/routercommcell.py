# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing Router Commcell related operations on Commcell
RouterCommcell:

    __init__()                              -- intializing the router commcell details

    get_service_commcell()                  -- Returns the service commcell object

    register_service_commcell()             -- Registers the Service Commcell to router commcell

    check_registration()                    -- checks if commcell is registered successfully or not

    unregister_service_commcell()           -- Unregisters the Service Commcell to router commcell

    _get_redirect_rules_on_router()         -- Gets the redirect rules from Router commcell

    _get_users_on_router()            -- Gets the users space from Router commcell

    create_service_db_connection()          -- creates a db connection to service database

    get_redirect_rules_on_servicedb()      -- gets the redirect rules from Service commcell database

    get_redirect_rules_on_service()         -- gets the redirect rules from Service commcell

    get_users_on_service()            -- gets the users space from Service commcell

    validate_redirect_rules()               -- validates the redirect rules

    validate_users_space()                  -- validates the users space

    get_redirect_service_commcells()        -- gets the valid service commcells to redirect for username given

    check_if_user_exists_on_service()       -- checks if the user exists on service commcell

    check_if_mail_exists_on_service()       -- checks if the user with mail id exists on service commcell

    validate_sync()                         -- validates sync operation after registration

    validate_user_user_group()              -- validates user to usergroup association

    validate_commcells_idp()                -- validates the commcells list registered for IdP

    get_commcell_object()                   -- gets the commcell object of the specified user

    service_commcell_sync()                 -- Sync service commcell
    
    start_services_on_service()             -- Starts services on service commcell machine

    stop_services_on_service()              -- Stops services on service commcell machine

    force_unregister_service_commcell()     -- Force unregisters service commcell from router

    validate_redirect_list()                -- Validates redirect list of input user or mail with storedProc

    get_redirect_list_from_api()            -- Gets list of commcells returned by redirect list API

    get_redirect_list_from_sp()             -- Gets list of commcells returned by Stored Proc in router DB

    collect_redirect_times()                -- Calls redirect list API few times and returns response time stats

"""
import time

from cvpysdk.commcell import Commcell
from AutomationUtils import database_helper, cvhelper, defines, config
from AutomationUtils import logger
from AutomationUtils.machine import Machine
import xmltodict

CONFIG = config.get_config()


class RouterCommcell(object):
    """Initializing the router commcell details. """
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

    def __init__(self, commcell, router_machine=None):
        """Intializes the Router Commcell with commcell object. """
        self._service_machine_object = None
        self._commcell = commcell
        self.log = logger.get_log()

        if router_machine:
            self.create_master_db_connection(router_machine)
        else:
            self.csdb = database_helper.CommServDatabase(self._commcell)

        self._service_commcell = None
        self._service_commcell_db_connect = None

    def get_service_commcell(self, service_commcell_host_name, service_user_name, service_password):
        """Returns the service commcell object

        Args:

            service_commcell_host_name     (str)      --      service commcell host name

            service_user_name            (str)        --      service commcell user name

            service_password             (str)        --      service commcell password

        """
        self.log.info("Getting the service commcell object")
        try:

            self._service_commcell = Commcell(service_commcell_host_name,
                                              service_user_name,
                                              service_password)
            return self.service_commcell

        except Exception as excp:

            self.log.error('service commcell object creation failed : %s ',
                           str(excp))
            raise Exception('service commcell object creation failed : %s  ',
                            str(excp))

    @property
    def service_commcell(self):
        """returns the service commcell object"""
        if self._service_commcell is None:
            raise Exception("Service commcell is not initialized")

        return self._service_commcell

    def register_service_commcell(self, service_commcell_host_name, service_user_name, service_password,
                                  registered_for_idp=None):
        """Registers the Service Commcell to router/IdP commcell

        Args:

            service_commcell_host_name     (str)      --      service commcell host name

            service_user_name            (str)   --      service commcell user name

            service_password             (str)   --      service commcell password

            registered_for_idp           (bool)  --   True - if we want the commcell to be registered for Identity Provider
                                                      False - if we dont want the commcell to be registered for Identity Provider

        """
        self.log.info("Registering a Commcell")
        self._commcell.register_commcell(commcell_name=service_commcell_host_name,
                                         registered_for_routing=True,
                                         admin_username=service_user_name,
                                         admin_password=service_password,
                                         register_for_idp=registered_for_idp)

    def _get_globalparam_role_router(self):
        """Gets the gxglobalparam multi commcell role from router"""
        role_query = "select value from GxGlobalParam where name='nMultiCommcellRole';"
        self.csdb.execute(role_query)
        role = self.csdb.rows[0][0]
        return 0 if role == '' else int(role)

    def _get_globalparam_role_service(self):
        """Gets the gxglobalparam multi commcell role from service"""
        role_query = "select value from GxGlobalParam where name='nMultiCommcellRole';"
        resp = self.service_commcell_db.execute(role_query)
        role = resp.rows[0][0]
        return 0 if role == '' else int(role)

    def _get_tpa_guids_router(self, app_type):
        """Gets the appname column of app_thirdPartyApp from router"""
        tpa_query = f"select appName from App_ThirdPartyApp where appType={app_type};"
        self.csdb.execute(tpa_query)
        if self.csdb.rows == [['']]:
            return []
        return [row[0].upper() for row in self.csdb.rows]

    def _get_tpa_guids_service(self, app_type):
        """Gets the appname column of app_thirdPartyApp from service"""
        tpa_query = f"select appName from App_ThirdPartyApp where appType={app_type};"
        resp = self.service_commcell_db.execute(tpa_query)
        if resp.rows == [['']]:
            return []
        return [row[0].upper() for row in resp.rows]

    def validate_roles(self, router_role, service_role):
        """Checks if multicommcell roles are set correctly on both commcells
        Args:
            router_role     (str)   -   name of the role expected in router commcell (from self.ROLE_BITS)
            service_role    (Str)   -   name of the role expected in service commcell (from self.ROLE_BITS)
        """
        errors = []
        self.log.info(f"Validating Roles:")
        if router_role:
            self.log.info(f"{router_role} for {self._commcell.commserv_name}")
            role_in_router = self._get_globalparam_role_router()
            if role_in_router & self.ROLE_BITS[router_role] != self.ROLE_BITS[router_role]:
                errors.append(f"Router: Expected Bit {self.ROLE_BITS[router_role]}, Got {role_in_router}")
        if service_role:
            self.log.info(f"{service_role} for {self.service_commcell.commserv_name}")
            role_in_service = self._get_globalparam_role_service()
            if role_in_service & self.ROLE_BITS[service_role] != self.ROLE_BITS[service_role]:
                errors.append(f"Service: Expected Bit {self.ROLE_BITS[service_role]}, Got {role_in_service}")
        if errors:
            self.log.error("Roles failed to validate!")
            for error in errors:
                self.log.error(error)
            raise Exception("Failed to Validate Roles!")
        else:
            self.log.info("GxGlobalParam MultiCommcellRoles validated")

    def validate_third_party_app(self, in_router=True, in_service=True):
        """
        checks if ThirdPartyApp entry is present/absent for given router/service
        """
        errors = []
        router_guids = self._get_tpa_guids_router(3)
        service_guids = self._get_tpa_guids_service(3)
        if self.service_commcell.commserv_guid.upper() in router_guids:
            if in_router:
                self.log.info("service guid is present in router, verified")
            else:
                errors.append("APP_TPA entry missing in router!")
        else:
            if not in_router:
                self.log.info("service guid is deleted in router, verified")
            else:
                errors.append("APP_TPA entry not deleted in router!")
        if self._commcell.commserv_guid.upper() in service_guids:
            if in_service:
                self.log.info("router guid is present in service, verified")
            else:
                errors.append("APP_TPA entry missing in service!")
        else:
            if not in_service:
                self.log.info("router guid is deleted in Service, verified")
            else:
                errors.append("APP_TPA entry not deleted in service!")
        if errors:
            self.log.error("TPA Entry Validation failed!")
            for error in errors:
                self.log.error(error)
            raise Exception("TPA Entry Validation failed!")
        else:
            self.log.info("TPA Entry verified!")

    def check_registration(self):
        """checks if commcell is registered successfully or not
        Args:
            commcell_name (str)   -- Name of the commcell

        Returns:
            boolean value

        """
        self.log.info("Check for registration")
        if not self._commcell.is_commcell_registered(self.service_commcell.commserv_name):
            raise Exception("Service Commcell is not registered successfully")
        self.log.info(f"Service Commcell [{self.service_commcell.commserv_name}] registered successfully")
        self.log.info("--- Additional Step --- Validating MultiCommcellRole ---")
        self.validate_roles(router_role="ROUTERCOMMCELL", service_role="ROUTERCOMMCELL_SERVICECOMMCELL")
        self.log.info("--- Additional Step --- Validating TPA Entry ---")
        self.validate_third_party_app(in_router=True, in_service=True)

    def unregister_service_commcell(self):
        """Unregisters the Service Commcell to router commcell."""
        self.log.info("UnRegistering a Commcell")
        self._commcell.unregister_commcell(self.service_commcell.commserv_name)

    def check_unregistration(self):
        """Checks if unregistration was successfull"""
        self._commcell.refresh()
        if self._commcell.is_commcell_registered(self.service_commcell.commserv_name):
            raise Exception("Service Commcell could not unregister!")
        self.log.info(f"Service Commcell [{self.service_commcell.commserv_name}] unregistered successfully")
        self.log.info("--- Additional Step --- Validating MultiCommcellRole ---")

        expected_router_role = "ROUTERCOMMCELL"
        expected_service_role = "NOTCONFIGURED"
        if len(self._get_tpa_guids_router(3)) <= 1:  # if there are no service commcells
            expected_router_role = "NOTCONFIGURED"  # router role should no longer be present
        if len(self._get_tpa_guids_service(3)) >= 2:  # if service has other routers it serves
            expected_service_role = "ROUTERCOMMCELL_SERVICECOMMCELL"  # service role also remains

        self.validate_roles(router_role=expected_router_role, service_role=expected_service_role)
        self.log.info("--- Additional Step --- Validating TPA Entry ---")
        self.validate_third_party_app(in_router=False, in_service=False)

    def _get_redirect_rules_on_router(self):
        """Gets the redirect rules from Router commcell

        Returns:

            list_of_rules_on_router     (list)  -- list of redirect rules on router for service commcell

            for example:    [['commvault.com'],['company1'],['company2']]

        """
        self.log.info("Getting the redirect rules of service commcell on router")
        query2 = "select stringVal from app_componentprop where componentType = 1047 and componentId = " \
                 "(select id from app_commcell where aliasName like '{0}')".format(self.service_commcell.commserv_name)
        self.csdb.execute(query2)
        return [value[0] for value in self.csdb.rows if value[0] != '']

    def _get_users_on_router(self):
        """Gets the users space from Router commcell

        Returns:

            list_of_users_space_on_router     (list)  -- list of users space on router for service commcell

            for example:    [['user1'],['user2'],['user3']]

        """
        self.log.info("Getting users of service commcell on router")
        query2 = "select login from UMUsersServiceCommcell where origCCId = " \
                 "(select id from app_commcell where aliasName like '{0}')".format(self.service_commcell.commserv_name)
        self.csdb.execute(query2)
        return [values[0] for values in self.csdb.rows]

    def create_service_db_connection(self, machine_name):
        """
        creates a db connection to service database.

        Args:

        machine_name        (str)   -- name of the machine

        """
        service_machine_object = Machine(machine_name.lower(), self.service_commcell)
        os = service_machine_object.os_info.lower()
        encrypted_password = service_machine_object.get_registry_value(r"Database", "pAccess")
        sql_password = cvhelper.format_string(self.service_commcell, encrypted_password).split("_cv")[1]
        sql_instancename = machine_name.lower()
        if os != 'unix':
            sql_instancename += "\\commvault"
        self.log.info("Getting a db connectivity for service commcell")
        self._service_commcell_db_connect = database_helper.MSSQL(
            server=sql_instancename,
            user='sqladmin_cv',
            password=sql_password,
            database='commserv',
            as_dict=False,
            driver=defines.unix_driver if os == 'unix' else defines.driver
        )

    def create_master_db_connection(self, machine_name):
        """
        creates a db connection to master database.

        Args:

        machine_name        (str)   -- name of the machine

        """
        master_machine_object = Machine(machine_name.lower(), self._commcell)
        os = master_machine_object.os_info.lower()
        if "RouterSQLCreds" in CONFIG.MultiCommcell._asdict():
            sql_user = CONFIG.MultiCommcell.RouterSQLCreds.username
            sql_password = CONFIG.MultiCommcell.RouterSQLCreds.password
            self.log.info("using RouterSQLCreds from CONFIG")
        else:
            sql_user = 'sqladmin_cv'
            encrypted_password = master_machine_object.get_registry_value(r"Database", "pAccess")
            sql_password = cvhelper.format_string(self._commcell, encrypted_password).split("_cv")[1]
            self.log.info("using sqladmin_cv user from reg key")
        sql_instancename = machine_name.lower()
        if os != 'unix':
            sql_instancename += "\\commvault"
        self.log.info("Getting a db connectivity for master commcell")
        self.csdb = database_helper.MSSQL(
            server=sql_instancename,
            user=sql_user,
            password=sql_password,
            database='commserv',
            as_dict=False,
            driver=defines.unix_driver if os == 'unix' else defines.driver
        )

    def create_service_machine(self, machine_name, username, password):
        """creates machine object for service commcell"""
        self.log.info("Creating RDP machine object")
        self._service_machine_object = Machine(
            machine_name=machine_name, username=username, password=password
        )
        self.log.info("RDP Machine object created successfully")

    @property
    def service_machine_object(self):
        """returns machine object (username/password method) of service commcell"""
        if self._service_machine_object is None:
            raise Exception("Service machine object not Created!")
        return self._service_machine_object

    @property
    def service_commcell_db(self):
        """returns a db object for service commcell"""
        if self._service_commcell_db_connect is None:
            raise Exception("Service commcell db is not connected")

        return self._service_commcell_db_connect

    def get_redirect_rules_on_servicedb(self):
        """gets the redirect rules from Service commcell database.

        Returns:

            list_of_redirect_rules_service_db   (list)  -- list of redirect rules from service commcell

        """
        self.log.info("Getting the redirect rules from service commcell")
        xml_response = self.service_commcell_db.execute_stored_procedure(
            procedure_name='MCC_FetchRedirectsforRouterCommcell',
            parameters='')
        json_response = xmltodict.parse(xml_response.rows[0][0])
        list_of_rules = json_response['RedirectRules']['rules'] + json_response['RedirectRules']['domains']
        return list_of_rules

    def get_redirect_rules_on_service(self):
        """gets the redirect rules from Service commcell

        Returns:

            lis_of_redirect_rules_service   (list)  -- list of redirect rules from service commcell
        """
        return self.service_commcell.redirect_rules_of_service

    @property
    def get_users_on_service(self):
        """gets the users space from service commcell

        Returns:

            list_of_users_space_service     (list)  -- list of users space from service commcell
        """
        return self.service_commcell.users.service_commcell_users_space

    def validate_redirect_rules(self, includes=None):
        """validates the redirect rules on router from service"""
        if includes is None:
            includes = []
        self.log.info("Getting the list of rules from service")
        redirect_rules_from_service = self.get_redirect_rules_on_service()
        self.log.info("Getting the list of rules of service on router")
        redirect_rules_on_router = self._get_redirect_rules_on_router()
        self.log.info("Comparing redirect rules")
        result_list_compare = set(redirect_rules_from_service) ^ set(redirect_rules_on_router)
        if result_list_compare:
            self.log.error("Redirect rules do not match")
            self.log.error(f"Service Rules: {redirect_rules_from_service}")
            self.log.error(f"Router Rules: {redirect_rules_on_router}")
            self.log.error(f"Not matching: {result_list_compare}")
            raise Exception("Validation Failed on matching redirect list")
        self.log.info("Redirect rules matched, now checking inclusions")
        missing_includes = set(includes) - set(redirect_rules_on_router)
        if missing_includes:
            self.log.error("Some of the expected rules missing from redirect rules")
            self.log.error(f"Expected: {includes}")
            self.log.error(f"Not matching: {missing_includes}")
            raise Exception("Validation Failed on expected rules missing from redirect rules")
        if includes:
            self.log.info("Expected rules are also present")
        self.log.info("All redirect rules validated")

    def validate_users_space(self, includes=None):
        """Validates the users space on router from service"""
        if includes is None:
            includes = []
        self.log.info("Getting the list of users from service")
        users_space_from_service = self.get_users_on_service.keys()
        self.log.info("Getting the list of users of service on router")
        users_space_from_router = self._get_users_on_router()
        self.log.info("Comparing users")
        result_list_compare = set(users_space_from_service) ^ set(users_space_from_router)
        if result_list_compare:
            self.log.error("User space doesn't match!")
            self.log.error(f"Service User space: {users_space_from_service}")
            self.log.error(f"Router User space: {users_space_from_router}")
            self.log.error(f"Not matching: {result_list_compare}")
            raise Exception("Validation Failed on matching user space")
        self.log.info("User spaces matched, now checking inclusions")
        missing_includes = set(includes) - set(users_space_from_router)
        if missing_includes:
            self.log.error("Some of the expected users missing from userspace")
            self.log.error(f"Expected: {includes}")
            self.log.error(f"Not matching: {missing_includes}")
            raise Exception("Validation failed for expected users not present in user space")
        if includes:
            self.log.info("Expected users are also present")
        self.log.info("ALl user space validated")

    def get_redirect_service_commcells(self, user_name_or_mail_id):
        """gets the valid service commcells to redirect for username given

        Args:

            user_name_or_mail_id        (str)   -- login name or the mail id of the user

        Returns:

            list_of_service_commcells   (list)  -- list of service commcells to be redirected

        """
        self.log.info("Getting the list of service commcells eligible for redirecting")
        list_of_service_commcells = self._commcell.get_eligible_service_commcells(user_name_or_mail_id)
        if not self.service_commcell.commserv_name in list_of_service_commcells:
            self.log.error(f"Service Commcell not in eligible redirects for user {user_name_or_mail_id}")
            self.log.error(f"List of eligible commcells: {list_of_service_commcells}")
            raise Exception("No Service Commcell Found")
        else:
            self.log.info(f"eligible redirects validated for {user_name_or_mail_id}")
            return list_of_service_commcells

    def check_if_user_exists_on_service(self, user_name):
        """checks if user exists on service commcell

        Args:

            user_name       (str)   -- checks if user exists on service commcell

        Raises:

            when user doesnt exists on Service commcell

        """
        self.log.info("Checking if user exists on service")
        users_on_service = self.get_users_on_service.keys()
        if not user_name in users_on_service:
            self.log.error("User missing from POLL Users API")
            raise Exception("user doesnt exist on service commcell")
        self.log.info(f"validated user {user_name} exists on service {self.service_commcell.commserv_name}")

    def check_if_mail_exists_on_service(self, mail_id):
        """checks if user exists on service commcell

        Args:

            mail_id       (str)   -- checks if user with mailid exists on service commcell

        Raises:

            when user user with mail doesnt exists on Service commcell

        """
        self.log.info("Checking if user with given mailid exists")
        list_of_mail = []
        for user_name in self.get_users_on_service:
            list_of_mail.append(self.get_users_on_service[user_name]['email'])
        if mail_id not in list_of_mail:
            self.log.info(f"Mail ID missing on service commcell user space for {mail_id}")
            self.log.info(f"list of mail: {list_of_mail}")
            raise Exception("user with mail id doesnt exist on service commcell")
        self.log.info(f"Validated, mail ID [{mail_id}] exists "
                      f"in user space of service {self.service_commcell.commserv_name}")

    @property
    def user_groups_on_service_commcell(self):
        """gets the users groups space from Service commcell

        Returns:

            list_of_user_groups     (list)  -- list of user groups from service commcell
        """

        user_groups_on_service = self.service_commcell.user_groups.all_user_groups
        return user_groups_on_service.keys()

    def validate_sync(self):
        """checks if users, usergroups, companies ,AD and SAML apps are synced"""

        self.log.info("validating sync for users,usergroups,companies and AD")
        if not ((set(self.service_commcell.users.all_users.keys()).issubset(set(self._commcell.users.all_users.keys())))
                and (set(self.service_commcell.user_groups.all_user_groups.keys()).issubset(
                    set(self._commcell.user_groups.all_user_groups.keys())))
                and (set(self.service_commcell.organizations.all_organizations.keys()).issubset(
                    set(self._commcell.organizations.all_organizations.keys())))
                and (set(self.service_commcell.domains.all_domains.keys()).issubset(
                    self._commcell.domains.all_domains.keys()))
                and self.validate_user_user_group()):
            raise Exception("sync validation is not successfull")
        self.log.info("Sync validation successfull!")

    def validate_user_user_group(self):
        """Validates user to usergroup association of service on IdP """

        self.log.info("validates user to usergroup association of service on IdP")
        for ug in self.user_groups_on_service_commcell:
            if not (set(self.service_commcell.user_groups.get(ug).users).issubset(
                    set(self._commcell.user_groups.get(ug).users))):
                self.log.info("validation failed for user to ug association")
                return False
        return True

    def validate_commcells_idp(self, commcell_obj):
        """validates the list of accessible commcells to logged in user"""

        self.cc_object = commcell_obj
        commcells_for_idp = self.cc_object.commcells_for_user
        for self.service_commcell.commserv_name in commcells_for_idp:
            raise Exception("service commcell is not shown in IdP commcell list")

    def get_commcell_object(self, user_name=None, password=None, authtoken=None, service_commcell=None):
        """Returns the  commcell object

        Args:

            user_name            (str)        --      commcell user name

            password             (str)        --      commcell password

            authtoken            (str)        --    saml token generated on master commcell

            service_commcell      (boolean)   --   true- if login into service
                                                    false - if login

        """

        self.log.info("Getting the commcell object")
        try:
            if user_name and password:
                return Commcell(self._commcell.commserv_hostname, user_name, password)

            if authtoken and service_commcell:
                return Commcell(self.service_commcell.commserv_hostname,
                                authtoken=authtoken, is_service_commcell=service_commcell)

            if authtoken:
                return Commcell(self.service_commcell.commserv_hostname, authtoken=authtoken)

        except Exception as excp:

            self.log.error('service commcell object creation failed : %s ',
                           str(excp))
            raise Exception('service commcell object creation failed : %s  ',
                            str(excp))

    def service_commcell_sync(self):
        """
        Perform a sync operation on the given service commcell

        """
        self.log.info("Performing sync on %s service commcell", self.service_commcell.commserv_hostname)
        self._commcell.service_commcell_sync(self.service_commcell)

    def start_services_on_service(self):
        """Starts commvault service on service commcell machine"""
        self.log.info("Attepting to start services on machine")
        self.service_machine_object.start_all_cv_services()
        self.log.info("CV Services started successfully")
        self.log.info("Waiting few mins for WebServer to start")
        time.sleep(60 * 10)
        self.log.info("Wait over, CV web services should be ready")

    def stop_services_on_service(self):
        """Stops commvault services on service commcell machine"""
        self.log.info("Attepting to stop services on machine")
        self.service_machine_object.stop_all_cv_services()
        self.log.info("CV Services stopped successfully")

    def force_unregister_service_commcell(self):
        """Force unregisters and validates DB"""
        self._commcell.unregister_commcell(self.service_commcell.commserv_name, force=True)
        self._commcell.refresh()
        if self._commcell.is_commcell_registered(self.service_commcell.commserv_name):
            raise Exception("Service Commcell could not unregister!")
        self.log.info(f"Service Commcell [{self.service_commcell.commserv_name}] unregistered successfully")
        self.log.info("--- Additional Step --- Validating MultiCommcellRole ---")

        expected_router_role = "ROUTERCOMMCELL"
        expected_service_role = "ROUTERCOMMCELL_SERVICECOMMCELL"
        if len(self._get_tpa_guids_router(3)) <= 1:  # if there are no service commcells
            expected_router_role = "NOTCONFIGURED"  # router role should no longer be present

        self.validate_roles(router_role=expected_router_role, service_role=expected_service_role)
        self.log.info("--- Additional Step --- Validating TPA Entry ---")
        self.validate_third_party_app(in_router=False, in_service=True)

    def validate_redirect_list(self, user_or_email, expected_commcells=None):
        """
        Validates the redirect list for given user

        Args:
            user_or_email   (str)   -   user or mail for logged user
            expected_commcells  (list) - will use for validation if given, (overrides SP validation)
        
        Returns:
            Result  (bool)  -   True if expected commcells matched and SP matched API response
                                False if validation failed
        """
        validation_result = True
        self.log.info(
            f">>> Validating Redirects for User : {user_or_email}, expecting commcells : {expected_commcells}")
        api_resp = self.get_redirect_list_from_api(user_or_email)
        sp_resp = self.get_redirect_list_from_sp(user_or_email)
        if set(api_resp) == set(sp_resp):
            self.log.info(">> API and StoredProc return same, No errors!")
        else:
            self.log.error(">> API and StoredProc return different response! See Below! ")
            self.log.error("API RESPONSE:")
            self.log.error(api_resp)
            self.log.error("StoredProc Response:")
            self.log.error(sp_resp)
            validation_result = False

        if expected_commcells:
            self.log.info(">>> Checking if expected commcells are present")
            if set(api_resp) == set(expected_commcells):
                self.log.info(">> API commcells list and input expected commcells matched!")
                validation_result = True
            else:
                self.log.error(">> API commcells list is different from expected")
                self.log.error("API Response:")
                self.log.error(api_resp)
                self.log.error(f"Expected: {expected_commcells}")
                validation_result = False
        else:
            self.log.info(">>> No expected commcells given, not checking further")
        return validation_result

    def get_redirect_list_from_api(self, user_or_mail):
        """
        Gets the redirects for given user from API

        Args:
            user_or_mail    (str)   -   the user or mail id to pass to API

        Returns:
            redirect_list   (list)  -   list of redirect names
        """
        self.log.info(f"> Getting API response to /RedirectList")
        resp = self._commcell.get_eligible_service_commcells(user_or_mail, False)
        self.log.info("> API response received successfully")
        self.log.info(resp)
        return resp

    def get_redirect_list_from_sp(self, user_or_mail):
        """
        Gets the redirects for given user from StoredProc

        Args:
            user_or_mail    (str)   -   the user or mail id to pass to StoredProc

        Returns:
            redirect_list   (list)  -   list of redirect names
        """
        self.log.info("> Getting MCC_HandleRedirectsForUser stored proc response")
        stored_proc_str = f"SET NOCOUNT ON;EXEC MCC_HandleRedirectsForUser '{user_or_mail}',3,'',0,'',1,1;"
        resp = self.csdb.execute(stored_proc_str)
        xml_out = resp.rows[0][0]
        self.log.info("> Got StoredProc response successfully")
        self.log.info(xml_out)
        parsed_sp = xmltodict.parse(xml_out).get('RedirectsForUser', {}).get('AvailableRedirects', [{}])
        if isinstance(parsed_sp, dict):
            parsed_sp = [parsed_sp]
        parsed_sp_list = {red_dict.get('@redirectUrl') for red_dict in parsed_sp}
        return parsed_sp_list

    def collect_redirect_times(self, user_or_mail, attempts=10):
        """
        Calls RedirectList API few times and collects response time data

        Args:
            user_or_mail    (str)   -   the user of mail id to pass to API
            attempts    (int)       -   number of API calls to collect response time data from
        
        Returns:
            stats   (dict)  -   dict with statistics like Average, Min, Max
                example: {
                    'Average': ..., 'Min': ..., 'Max': ..., 'Data': [...time from each API call...]
                }
        """
        times = []
        for _ in range(attempts):
            start_time = time.time()
            self._commcell.get_eligible_service_commcells(user_or_mail, False)
            end_time = time.time()
            times.append(end_time - start_time)
        return {'Average': sum(times) / attempts, 'Min': min(times), 'Max': max(times), 'Data': times}
