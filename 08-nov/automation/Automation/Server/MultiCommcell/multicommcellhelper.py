# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file for performing multicommcell operations


MultiCommcellHandler
===================

    refresh()                       --  clears all the stored machine, commcell, db and other objects

    get_commcell_object()           --  returns the commcell object for defined cs

    get_machine_object()            --  returns the machine object for defined cs

    get_dbops_object()              --  returns the specified dbops object for defined cs

    get_object()                    --  returns the custom object for defined cs

    __get_attr__                    --  get attr is defined for wrapping above functions using dot notation


CommcellSwitcher
================

    refresh()                       --  clears all the stored commcell objects and switcher data

    region_mapping_for_switcher     --  the region mapping additional setting value set in this cs

    region_mapping_api              --  region mapping api endpoint additional setting value set in this cs

    commcell_switcher_props         --  gets all the service commcell properties stored in this cs

    get_service_commcell_props()    --  fetches the properties for given service commcell

    get_service_session()           --  gets a commcell sdk session for given service commcell

    get_region_mapping_info()       --  makes api call to region mapping api and gets response


MultiCommcellHelper
===================

    __init__                        --  initializes multicommcellhelper object

    validate_client_listing()       --  Validates the clients listed when
    logged into commcell using username-password and when logged in using SAML token

    validate_incorrect_authtoken()  --  Validates whether exception is raised when
    an incorrect authtoken is passed for operations

    cleanup_certificates()          -- deletes certificates created by test cases

    saml_config()                   -- performs initial configuration for multicommcell
    operations

    token_validity_check()          -- Validates that the commcell login fails if
    token is used after expiry

    tampered_validity_check()       -- Validates that the commcell login fails if token's
    time is tampered

    job_validate()                  -- validates the jobs run by multicommcell user
    on SP commcell

    get_commcell_displayName_hostname_map() --  Returns a map for commcell display name and hostname

    validate_redirect()             -- validates correct redirection
"""
import json
import time
import base64
import re
from typing import Callable, Any, Type
from urllib.parse import urlparse

import xmltodict

from AutomationUtils import logger
from AutomationUtils import options_selector
from AutomationUtils.database_helper import CSDBOperations
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.machine import Machine
from cvpysdk.commcell import Commcell
from cvpysdk import identity_management
from Web import AdminConsole
from cvpysdk.exception import SDKException


class MultiCommcellHandler:
    """
    A utility class to manage CS, DB, Machine objects and configurations of any number of commcells
    Meant as helper to multicommcell helpers
    """
    def __init__(self, default_config_obj: Any, user_configs: dict,
                 dbops_class: Type[CSDBOperations], other_classes: dict = None) -> None:
        """
        Init function of this class,

        Args:
            default_config_obj  (Any)   -   A config object from config.json or a class object
                                            We will call
                                            object.RDP_USERNAME, object.RDP_PASSWORD
                                            object.DB_USERNAME, object.DB_PASSWORD
                                            object.CS_USERNAME, object.CS_PASSWORD
                                            and object.<TOKEN>_HOSTNAME
                                            to get the default values for credentials not given in user_configs
            Note:
                <token> is a variable name or identifier string for each commcell
                you may think of it like role, 'router', 'service1', 'service2', 'source', 'dest', etc

            user_configs    (dict)      -   a dict with credentials for each commcell given in below format
                                            <token>_rdp_username,<token>_rdp_password
                                            <token>_db_username,<token>_db_password
                                            <token>_cs_username,<token>_cs_password
                                            <token>_hostname
            dbops_class     (class)     -   This is any derived class of CSDBOperations, it will be instantiated
                                            using the given configs.
            other_classes   (dict)      -   A template to handle (like @property) any object for each commcell
                                            example:
                                            {
                                                ('obj', class_obj): {kwargs to instantiate},
                                                ('obj2', class_obj2): {kwargs}
                                            }
                                            the keys are variable name and class obj to instantiate under that name
                                            in above example. mcc.<token>_obj and mcc.<token>_obj2 will
                                            return the correct objects for commcell identified by token

                                            kwargs can have special keyword in value:
                                                "__commcell__": to pass the commcell object
                                                "__machine__": to pass machine object for each commcell obj
                                                "__db__": to pass dbops object for each commcell obj
                                                class_objX : to pass class_objX's instance

                                            Note: Can cause infinite loop deadlock if <class_obj> and another
                                                <class_obj2> need each other to instantiate themselves.
        """
        if other_classes is None:
            other_classes = {}
        self.defaults = default_config_obj
        self.user_configs = user_configs
        self._commcell_objects = {}
        self._machine_objects = {}
        self._dbops_objects = {}
        self._dbops_cls = dbops_class
        self._other_templates = other_classes
        self._objtoken_map = {objtoken: class_type for objtoken, class_type in other_classes}
        self._other_objects = {}

    def refresh(self) -> None:
        """Clears all the stored commcell, machine, dbops objects"""
        self._commcell_objects = {}
        self._machine_objects = {}
        self._dbops_objects = {}

    def __getattr__(self, item) -> Any:
        """
        Defining __getattr__ for more convenient access using dot notation

        Example usage:
            self.mcc = MultiCommcellHandler(.....)
            self.mcc.router_cs
            self.mcc.service_machine
            self.mcc.<token>_<obj>
            [all <token> must be present in configs or inputs given during __init__]
            [all <obj> except commcell, machine, dbops, must have been specified in other_classes during __init__]
        """
        token = item
        obj = None
        if "_" in item:
            token = item.split("_")[0]
            obj = "".join(item.split("_")[1:])
        if not obj:
            return self.get_commcell_object(token)
        if obj == 'cs':
            return self.get_commcell_object(token)
        if obj == 'machine':
            return self.get_machine_object(token)
        if obj == 'dbops':
            return self.get_dbops_object(token)
        return self.get_object(token, obj)

    def get_commcell_object(self, token: str) -> Commcell:
        """
        Stores and Gets Commcell object using given inputs

        Args:
            token (str)   -     this is the cs identifier token used to fetch creds from user_configs
        """
        if token not in self._commcell_objects:
            hostname = self.user_configs.get(f'{token}_hostname') or getattr(self.defaults, f'{token.upper()}_HOSTNAME')
            if not hostname:
                raise Exception(f"no cs hostname input given for {token}, in user option or defaults")
            self._commcell_objects[token] = Commcell(
                hostname,
                self.user_configs.get(f'{token}_cs_username') or self.defaults.CS_USERNAME,
                self.user_configs.get(f'{token}_cs_password') or self.defaults.CS_PASSWORD,
            )
        return self._commcell_objects[token]

    def get_machine_object(self, token: str) -> Machine:
        """
        Stores and Gets Machine object for given Commcell

        Args:
            token (str)   -     this is the cs identifier token used to fetch creds from user_configs
        """
        if token not in self._machine_objects:
            hostname = self.user_configs.get(f'{token}_hostname') or getattr(self.defaults, f'{token.upper()}_HOSTNAME')
            if not hostname:
                raise Exception(f"no cs hostname input given for {token}, in user option or defaults")
            if (rdp_un := self.user_configs.get(f'{token}_rdp_username', self.defaults.RDP_USERNAME)) and (
                    rdp_pwd := self.user_configs.get(f'{token}_rdp_password', self.defaults.RDP_PASSWORD)):
                self._machine_objects[token] = Machine(
                    machine_name=hostname, username=rdp_un, password=rdp_pwd
                )
            else:
                self._machine_objects[token] = Machine(self.get_commcell_object(token).commserv_client)
        return self._machine_objects[token]

    def get_dbops_object(self, token: str) -> CSDBOperations:
        """
        Stores and Gets DBOps object for given Commcell

        Args:
            token (str)   -     identifier token of a commcell
        """
        if token not in self._dbops_objects:
            db_user = self.user_configs.get(f'{token}_db_username') or self.defaults.DB_USERNAME
            db_pass = self.user_configs.get(f'{token}_db_password') or self.defaults.DB_PASSWORD
            cs_machine = None
            if not (db_user and db_pass):
                cs_machine = self.get_machine_object(token)
            self._dbops_objects[token] = self._dbops_cls(
                self.get_commcell_object(token), db_user, db_pass, commcell_machine=cs_machine
            )
        return self._dbops_objects[token]

    def get_object(self, commcell_token: str, object_token: str) -> Any:
        """
        Stores and Gets custom class_type object for given Commcell

        Args:
            commcell_token   (str)      -   the token to identify a commcell
            object_token    (str)       -   the object token described in templates
        """
        if object_token not in self._objtoken_map:
            raise Exception(f"{object_token} is not given in templates, no idea what or how to initialize it.")
        if commcell_token not in self._other_objects:
            self._other_objects[commcell_token] = {}
        if object_token not in self._other_objects[commcell_token]:
            class_type = self._objtoken_map.get(object_token)
            if not class_type:
                raise Exception(f"no idea what class to instantiate for {object_token}, classobj not given in template")
            kwargs = self._other_templates[(object_token, class_type)]
            processed_kwargs = {}
            for key, value in kwargs.items():
                if isinstance(value, str) and value.startswith('__') and value.endswith('__'):
                    if value == '__commcell__':
                        processed_kwargs[key] = self.get_commcell_object(commcell_token)
                    elif value == '__machine__':
                        processed_kwargs[key] = self.get_machine_object(commcell_token)
                    elif value == '__db__':
                        processed_kwargs[key] = self.get_dbops_object(commcell_token)
                    else:
                        processed_kwargs[key] = self.get_object(commcell_token, value.strip("__"))
                else:
                    processed_kwargs[key] = value
            self._other_objects[commcell_token][class_type.__name__] = class_type(**processed_kwargs)
        return self._other_objects[commcell_token][object_token]

    # TODO: Integrate CommcellSwitcher class as another object
    # def get_switcher_object


class CommcellSwitcher:
    """Class to handle service commcell switcher related operations"""

    def __init__(self, idp_commcell: Commcell) -> None:
        """
        Init function of this class

        Args:
            idp_commcell    (Commcell)  -   can be any idp login of any user with switcher access
        """
        self.idp_login = idp_commcell
        self._service_commcell_props = None
        self._service_commcell_sessions = {}
        self._region_mapping_for_switcher = None
        self._region_mapping_api = None

    def refresh(self):
        """ Method to refresh the commcell switcher data """
        self._service_commcell_props = None
        self._service_commcell_sessions = {}
        self._region_mapping_for_switcher = None

    def _get_region_name(self, commcell_hostname):
        try:
            for sc_data in self.idp_login.commcells_for_user:
                if urlparse(sc_data.get('redirectUrl').lower()).netloc == commcell_hostname.lower():
                    return sc_data.get('commcellName')
        except SDKException:
            return None

    @property
    def region_mapping_for_switcher(self) -> dict:
        """
        parsed dict of the xml region mapping set in additional settings
        """
        if self._region_mapping_for_switcher is None:
            for setting in self.idp_login.get_configured_additional_setting():
                if setting.get('keyName') == 'ringRegionMappingForCommcellSwitcher':
                    self._region_mapping_for_switcher = xmltodict.parse(
                        setting.get('value', '')
                    ).get('ringRegionMappings')
                    break
        return self._region_mapping_for_switcher

    @property
    def region_mapping_api(self) -> str:
        """
        The api endpoint value set in additional settings
        """
        if self._region_mapping_api is None:
            for setting in self.idp_login.get_configured_additional_setting():
                if setting.get('keyName') == 'metallicRegionMappingAPI':
                    self._region_mapping_api = setting.get('value', '')
                    break
        if self._region_mapping_api is None:
            raise Exception("Cannot test region mapping! metallicRegionMappingAPI key not present!")
        return self._region_mapping_api

    @property
    def commcell_switcher_props(self) -> list:
        """
        List of dicts containing all service commcell properties
        """
        if self._service_commcell_props is None:
            self._service_commcell_props = []
            all_switcher_commcells = (self.idp_login.commcells_for_switching.get('serviceCommcell', []) +
                                      self.idp_login.commcells_for_switching.get('routerCommcell', []) +
                                      [self.idp_login.commcells_for_switching.get('IDPCommcell', {})])
            for sc_data in all_switcher_commcells:
                hostname = urlparse(sc_data.get('webUrl')).netloc or sc_data.get('commcellHostname')
                self._service_commcell_props.append(
                    {
                        'weburl': sc_data.get('webUrl'),
                        'hostname': hostname,
                        'displayname': sc_data.get('commcellAliasName'),
                        'commcellname': sc_data.get('commcell', {}).get('commCellName'),
                        'GUID': sc_data.get('commcell', {}).get('csGUID'),
                        'commcellid': sc_data.get('commcell', {}).get('commCellId'),
                        'regionname': self._get_region_name(hostname)
                    }
                )
                if sc_data.get('commcell', {}).get('csGUID', '').lower() == str(self.idp_login.commserv_guid).lower():
                    self._service_commcell_sessions[hostname] = self.idp_login
        return self._service_commcell_props

    def get_service_commcell_props(self, service_commcell: str) -> dict:
        """
        Utility to fetch any property about service commcell from given CS's switcher data

        Args:
            service_commcell    (str)   -   any identifying attribute of service commcell,
                                            aliasName, displayname, url, guid, cs id, anything
                                            as long as it is unique to this service commcell

        Returns:
            properties (dict)           -   all properties of the service commcell stored in Switcher
            Example:
            {
                'hostname': ..., 'displayname': ..., 'commcellname': ..., 'GUID': ..., 'commcellid': ...
            }
        """
        for sc_props in self.commcell_switcher_props:
            for prop, val in sc_props.items():
                if str(val).lower().strip() == str(service_commcell).lower().strip():
                    return sc_props.copy()
        raise Exception(
            f"Couldn't identify service commcell given from -> {service_commcell}\n Switcher data only has:" +
            json.dumps(self.idp_login.commcells_for_switching.get('serviceCommcell', []), indent=4)
        )

    def get_service_session(self, service_commcell: str) -> Commcell:
        """
        Gets the service commcell SDK login object by switching (using idp saml token)

        Args:
            service_commcell    (str)   -   any identifying attribute of service commcell,
                                            aliasName, displayname, url, guid, cs id, anything
                                            as long as it is unique to this service commcell

        Returns:
            login_obj   (Commcell)  -   sdk commcell object of the service commcell
        """
        sc_hostname = self.get_service_commcell_props(service_commcell)['hostname']
        if not self._service_commcell_sessions.get(sc_hostname):
            self._service_commcell_sessions[sc_hostname] = Commcell(
                sc_hostname,
                authtoken=self.idp_login.get_saml_token(),
                is_service_commcell=True
            )
        c = self._service_commcell_sessions[sc_hostname]
        c.reset_company()
        return c

    def get_region_mapping_info(self) -> dict[str, dict[str, str]]:
        """
        Makes GET API call to the region mapping API and returns region mapping from response

        Example: {
            'region1': {'commcell': 'cs1', 'countries': ['country1', 'country2', ...]},
            'region2': {...},
            ...
        }
        """
        region_map = {}
        flag, response = self.idp_login._cvpysdk_object.make_request(
            'GET', self.region_mapping_api, headers={'Accept': 'application/json'}
        )
        for region in response.json().get('data', {}).get('geoCountryRegionRingMappings', []):
            region_map[region.get('region')] = {
                'commcell': region.get('commcell'),
                'countries': region.get('countries')
            }
        return region_map


class MultiCommcellHelper(object):
    """Helper class to perform multicommcell operations"""

    def __init__(self, inputs: dict, admin_console: AdminConsole = None):
        """Initializes MultiCommcellHelper object and gets the commserv database
           object if not specified

            Args:
                inputs    (dict)    --  inputs passed to initialise the object
                admin_console (AdminConsole)    -- Adminconsole object
        """
        self.log = logger.get_log()
        self.sp_commcell = None
        self.idp_commcell = None
        self.admin_console = admin_console
        if inputs.get("SPCommserver", None):
            self.sp_commcell = Commcell(
                inputs["SPCommserver"],
                inputs["SPadminUser"],
                inputs["SPadminUserPwd"]
            )
        if inputs.get("IDPCommserver", None):
            self.idp_commcell = Commcell(
                inputs["IDPCommserver"],
                inputs["IDPadminUser"],
                inputs["IDPadminUserPwd"]
            )
        self._idp_options_selector = options_selector.OptionsSelector(self.idp_commcell)
        self.identity_app = None
        self.service_app = None

    def validate_client_listing(self, regular_commcell, saml_commcell):
        """Validates the clients listed when logged into commcell using
           username-password and when logged in using SAML token

            Args:
                regular_commcell    (obj)   -   Commcell object wehn logged in
                                                using username & password

                saml_commcell       (obj)   -   Commcell object wehn logged in
                                                using authtoken

            Returns:
                bool    -   True if validated. False otherwise
        """
        self.log.info("\tValidating the listing of clients")
        return regular_commcell.clients.all_clients == saml_commcell.clients.all_clients

    def validate_incorrect_authtoken(self, sp_commcell, idp_commcell):
        """Validates whether exception is raised when an incorrect authtoken
           is passed for operations

            Args:
                sp_commcell         (obj)   -   Commcell object of service provider

                idp_commcell        (obj)   -   Commcell object of ID provider

            Returns:
                bool    -   True if validated. False otherwise
        """
        idp_token = idp_commcell.get_saml_token()
        self.log.info("\tValidating invalid authtoken failure")
        try:
            idp_token = '{0}xyzabc'.format(idp_token)
            sp_user_commcell = Commcell(
                sp_commcell.commserv_hostname,
                authtoken=idp_token
            )
            if sp_user_commcell:
                return False
        except Exception as exp:
            self.log.info('Login with tampered authtoken successfully prevented - {0}'.format(
                str(exp))
            )
            return True

    def cleanup_certificates(self):
        """Helper method to delete the certificates created by the TC

        Returns:
            bool    -   True if deletion successful. False otherwise.
        """
        sp_apps = identity_management.IdentityManagementApps(self.sp_commcell)
        idp_apps = identity_management.IdentityManagementApps(self.idp_commcell)

        try:
            if not self.service_app:
                self.service_app = sp_apps.get_commcell_identity_apps
            if not self.identity_app:
                self.identity_app = idp_apps.get_local_identity_app

            if isinstance(self.service_app, list):
                for app in self.service_app:
                    sp_apps.delete_identity_app(app.app_name)
            else:
                sp_apps.delete_identity_app(self.service_app.app_name)

            idp_apps.delete_identity_app(self.identity_app.app_name)
        except Exception as exp:
            self.log.error('Cleanup failed due to - {0}'.format(str(exp)))

    def saml_config(self, app_display_name, user_dict=None):
        """This method performs the initial configuration on SP and IDP commcells,
           checks for multicommcell login
            Args:
                app_display_name    (str)   -   display name for the commcell app

                user_dict    (dict)  -   dict containing SP & IDP users details
                                         {
                                             'SPUser': {
                                                 'userName': 'user1_name',
                                                 'password': 'user1_password'
                                             },
                                             'IDPUser': {
                                                 'userName': 'user2_name',
                                                 'password': 'user2_password'
                                             }
                                         }

            Returns:
                tuple   -   Tuple containing service provider's commcell
                            object and ID provider's commcell object

        """
        idp_username = user_dict['IDPUser']['userName']
        sp_username = user_dict['SPUser']['userName']

        if not self.idp_commcell.users.has_user(idp_username):
            self.log.info("\tAttempting to create IDP user on {0}".format(
                self.idp_commcell.commserv_name
            )
            )
            idpuser_obj = self.idp_commcell.users.add(
                idp_username,
                "IDP User",
                "test@commvault.com",
                password=user_dict['IDPUser']['password'],
                local_usergroups=['master']
            )

        else:
            idpuser_obj = self.idp_commcell.users.get(idp_username)

        if not self.sp_commcell.users.has_user(sp_username):
            self.log.info("\tAttempting to create SP user on {0}".format(
                self.sp_commcell.commserv_name
            )
            )
            spuser_obj = self.sp_commcell.users.add(
                sp_username,
                "SP User",
                "test@commvault.com",
                password=user_dict['IDPUser']['password'],
                local_usergroups=['master']
            )
        else:
            spuser_obj = self.sp_commcell.users.get(sp_username)

        self.log.info("\n\tUNREGISTERING THE APPLICATION AT IDP IF IT WAS ALREADY REGISTERED")
        idp_apps_object = identity_management.IdentityManagementApps(self.idp_commcell)
        idp_app = idp_apps_object.get_local_identity_app
        if idp_app:
            idp_apps_object.delete_identity_app(idp_app.app_name)

        self.log.info("\n\tCREATING CERTIFICATE AT IDP")
        self.identity_app = idp_apps_object.configure_local_identity_app(
            [idpuser_obj.user_name]
        )

        if self.identity_app:
            self.log.info("IDP Certificate created successfully")
            local_identity_props = self.identity_app.get_app_props()

        self.log.info("\n\tUNREGISTERING THE APPLICATION AT SP IF IT WAS ALREADY REGISTERED")
        sp_apps_object = identity_management.IdentityManagementApps(self.sp_commcell)
        commcell_app_list = sp_apps_object.get_commcell_identity_apps
        if commcell_app_list:
            for app in commcell_app_list:
                sp_apps_object.delete_identity_app(app.app_name)

        self.log.info("\n\tREGISTER APPLICATION AT SP")
        self.service_app = sp_apps_object.configure_commcell_app(
            local_identity_props,
            self.idp_commcell.commserv_guid,
            app_display_name,
            user_assoc_list=[spuser_obj.user_name],
            user_mappings={
                idpuser_obj.user_name: spuser_obj.user_name
            }
        )
        if self.service_app:
            self.log.info("SP app created successfully")

        self.log.info("\n\tMULTICOMMCELL LOGIN TO SP")
        idp_user_commcell = Commcell(
            self.idp_commcell.commserv_hostname,
            idpuser_obj.user_name,
            user_dict['IDPUser']['password']
        )

        if idp_user_commcell:
            saml_token = idp_user_commcell.get_saml_token()

        if saml_token:
            sp_user_commcell = Commcell(
                self.sp_commcell.commserv_hostname,
                authtoken=saml_token
            )

        return (idp_user_commcell, sp_user_commcell)

    def token_validity_check(self, idp_commcell, sp_commcell, validity_mins=2):
        """Validates that the commcell login fails if token is used
           after expiry

            Args:
                idp_commcell    (obj)   -   identity provider commcell

                sp_commcell     (obj)   -   service provider commcell

            Returns:
                bool    -   True if validated. False otherwise
        """
        self.log.info("Requesting for a {0} minute valid token".format(validity_mins))
        idp_token = idp_commcell.get_saml_token(validity=validity_mins)

        timeout = time.time() + 60 * validity_mins
        expiry_failure = None
        try:
            while True:
                if time.time() > timeout:
                    self.log.info(
                        "Attempting login after {0} minute timeout".format(
                            validity_mins
                        )
                    )
                    Commcell(
                        sp_commcell.commserv_hostname,
                        authtoken=idp_token
                    )
                    expiry_failure = True
                    raise Exception(
                        'Login succeeded even after token expiry'
                    )
                else:
                    self.log.info(
                        "Timeout of {0} minutes not reached. Attempting login".format(
                            validity_mins
                        )
                    )
                    Commcell(
                        sp_commcell.commserv_hostname,
                        authtoken=idp_token
                    )
                    self.log.info("Login successful")
                    time.sleep(30)
        except Exception as exp:
            if expiry_failure:
                self.log.error(
                    "Login succeeded after token expiry - {0}".format(exp)
                )
            else:
                if exp.exception_id is '106':
                    self.log.info("Token validity passed - {0}".format(exp))
                else:
                    self.log.error("General exception - {0}".format(exp))

    def tampered_validity_check(self, idp_commcell, sp_commcell, validity_mins=2):
        """Validates that the commcell login fails if token's time is tampered

            Args:
                idp_commcell    (obj)   -   identity provider commcell

                sp_commcell     (obj)   -   service provider commcell

                validity_mins   (obj)   -   time duration in minutes for the token validity
        """
        self.log.info("Requesting for a {0} minute valid token".format(validity_mins))
        idp_token = idp_commcell.get_saml_token(validity=validity_mins)
        decoded_token = base64.b64decode(idp_token).decode('utf-8')[3:]
        tampered_token = re.sub(
            '(?<=NotOnOrAfter=").*Z',
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time())),
            decoded_token
        )
        encoded_token = "SAML {0}".format(
            base64.b64encode(tampered_token.encode('utf-8')).decode('utf-8')
        )
        try:
            Commcell(sp_commcell.commserv_hostname, authtoken=encoded_token)
            self.log.error("Login succeeded with tampered token. Please check webserver.log")
        except Exception as exp:
            self.log.info("Login with tampered token prevented with error - {0}".format(
                exp
            ))

    def job_validate(self, job_type, sp_commcell, client_name=None):
        """Validates the jobs run by multicommcell user on SP commcell

            Args:
                job_type    (str)   -   type of the job to be run, input in upper case

                sp_commcell (obj)   -   service provider commcell where job is to be run

                client_name (str)   -   client that is to be backed up
        """
        utils_obj = CommonUtils(sp_commcell)
        subclient_obj = utils_obj.get_subclient(client_name)

        job_obj = utils_obj.subclient_backup(
            subclient_obj,
            backup_type=job_type
        )
        if job_obj.summary['status'] == 'Completed':
            self.log.info('Job operation successful')
        else:
            raise Exception('Job triggerd by SP user has not completed')

    def get_commcell_displayName_hostname_map(self) -> dict:
        """Returns a map for commcell display name and hostname

        Returns:
            dict: dict containing a commcell name mapped to commcell hostname
        """
        clients = self.idp_commcell.clients.all_clients
        commcell_hostname_map = {}
        for client in clients:
            commcell_hostname_map[clients[client]["hostname"]] = clients[client]["displayName"]

        return commcell_hostname_map

    def validate_redirect(self, workload_url: str) -> None:
        """Method to validate for correct redirection

        Args:
            workload_url (str): Expected redirect URL
        """
        url = self.admin_console.driver.current_url
        if workload_url not in url:
            raise Exception(f"Test redirected to {url} instead of {workload_url}")
