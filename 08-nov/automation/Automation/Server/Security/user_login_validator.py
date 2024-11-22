# -*- coding: utf-8 -*-
# pylint: disable=W1202

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for performing user's login related validations.

LoginValidator is the only class defined in this file

LoginValidator:

    __init__(test_object)                   --  initialize instance of the LoginValidator class

    validate()                              --  entry point for validation

    cleanup()                               --  deletes entities which got created part of test case run.

    create_local_user_entity()              --  creates user/user group

    restart_webserver()                     -- restart webserver service for windows/linux

    _users_to_be_validated()                --  adds users to global list of users to be verified.

    retry_webconsole_user_login()             --  retries webconsole login for 'n' number of times

    prerequisites()                         --  Registers Directories with commcell/company and
                                                imports External groups/users

    validate_user_login()                   --  Validates user's login with username/email from adminconsole,
                                                webconsole, GUI

    validate_association_less_login()       --  Validate users'login when no security associations are            found                                             

    validate_domain_less_login()            --  validates domain less user login feature

    validate_password_complexity_and_history_features   --  validates password history, complexity and
                                                            expired password features

    validate_ownership_transfer()                   --  validates ownership transfer cases for (commcell user,
                                                        company user and LDAP users)

    _verify_ownership_associations()                -- verifies whether owned entities present in security
                                                        associations or not
"""

import json
import random
import time
from datetime import datetime

from cvpysdk.commcell import Commcell
from cvpysdk.domains import Domains
from cvpysdk.organization import Organizations
from cvpysdk.client import Client
from cvpysdk.security.user import User

from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils import logger, config
from AutomationUtils import database_helper

from Server.Security.securityhelper import SecurityHelper
from Server.Security.usergrouphelper import UsergroupHelper
from Server.organizationhelper import OrganizationHelper
from Server.Security.userhelper import UserHelper
from Server.mongodb_helper import MongoDBHelper
from Server.Security.userconstants import WebConstants


class LoginValidator:
    """DRValidator helper class to perform DR validations"""

    def __init__(self, test_object):
        """
        Initialize instance of the LoginValidator class

            Args:
                test_object     (object)            --      instance of testcase.
        """
        self.log = logger.get_log()
        self.test_object = test_object
        self._commcell = test_object.commcell
        self._csdb = test_object.csdb
        self._tcinputs = test_object.tcinputs

        self.usergrouphelper = UsergroupHelper(self._commcell)
        self.userhelper = UserHelper(self._commcell)
        self.organizations = Organizations(self._commcell)
        self.securityhelper = SecurityHelper(self._commcell)
        self.domains = Domains(self._commcell)
        self.config_json = config.get_config()
        self.utility = OptionsSelector(self._commcell)
        self.client_obj = Client(self._commcell, client_name=self._commcell.commserv_name)
        self.csdb = database_helper.CommServDatabase(self._commcell)
        self.webserver_name = MongoDBHelper.get_default_webserver(self.csdb)[0]
        self.webserver_obj = self._commcell.clients.get(self.webserver_name)
        self.users_login_details = []
        self.company_object = None
        self._tenant_admin_commell_obj = None
        self.associations = True
        self._commcell.refresh()

    def validate(self, feature, **inputs_required_for_feature):
        """
        Entry point for feature validations

            Args:
                feature        (list)      --      list of features to be validated.

                inputs_required_for_feature      (kwargs)   --  required parameters for the corresponding
                                                                feature validate method.

        Returns :
            None
        """
        try:
            self.prerequisites()
            if feature in ('user_login', 'login_attempt_limit_and_account_lock',
                           'domain_less_login', 'password_complexity_and_history_features', 'ownership_transfer', 'association_less_login'):
                getattr(self, 'validate_' + feature)(**inputs_required_for_feature)
            else:
                raise Exception('please pass the validate feature name')
        finally:
            self.cleanup()

    def cleanup(self):
        """
        Deletes entities which got created from test run.

        Returns:
             None
        """
        # cleanup order:
        # first, delete company, it will delete company associated entities like directories, groups etc
        # second, commcell level directories, it will delete external users and groups as well.
        # third, commcell level local entities like user groups and users..
        self.log.info('Cleaning up entities...')
        if self.company_object:
            # deleting company, will delete company associated entities like directories, groups etc
            self.log.info('deactivating and deleting company {0}'.format(self.company_object.name))
            self.organizations.delete(self.company_object.name)
        self.domains.refresh()
        for entity in self.users_login_details:
            if entity.get('level') == 'commcell':
                if entity.get('domain'):
                    if self.domains.has_domain(entity.get('domain')):
                        self.log.info('Deleting domain {0}'.format(entity.get('domain')))
                        self.domains.delete(entity.get('domain'))
                    else:
                        self.log.info("{0} domain doesn't exist on commcell".format(entity.get('domain')))
                else:
                    if entity.get('usergroupname'):
                        self.usergrouphelper.delete_usergroup(entity.get('usergroupname'),
                                                              new_user=self.config_json.ADMIN_USERNAME)
                    if entity.get('username'):
                        self.userhelper.delete_user(entity.get('username'), new_user=self.config_json.ADMIN_USERNAME)

    def create_local_user_entity(self, entity_inputs, tenant_admin_commcell_obj=None):
        """
        creates entities user/user group at commcell/company level
        imports external users/groups at commcell/company level
        Args:
             entity_inputs      (dict)      --      dict consisting of user/user group properties

             sample dict1:
                {
                "usergroup": {},
                "user": {}
                }
                with above dict passed,creates usergroup with random(name, permissions)
                and user with random(name, permissions, email, fullname), password from config.json
                and associates this user with above created user group.

             sample dict2;
                {
                "usergroup":
                    {
                        "group_name": "",
                        "domain": "",
                        "users": [],
                        "entity_dict": {},
                        "external_groups": [],
                        "local_groups": []
                    },
                "user":
                    {
                        "user_name": "",
                        "email": "",
                        "full_name": "",
                        "domain": "",
                        "password": "",
                        "local_usergroups": "",
                        "security_dict": {}
                    }
                }
                for more details about individual property of user/usergroup,
                please refer create_user() method from userhelper.py and create_usergroup from usergrouphelper.py

             tenant_admin_commcell_obj      (object)    --

            Adds created user details to global list self.users_login_details

         Returns:
               dict
        """
        timestamp = datetime.strftime(datetime.now(), '%H%M%S')
        user_group_object = None
        prefix = (tenant_admin_commcell_obj.commcell_username.split("\\")[
                      0] + "\\") if tenant_admin_commcell_obj else ""
        final_dict = {}
        entities_list = ['userName', 'userGroupName', 'clientGroupName']
        sec_helper = SecurityHelper(tenant_admin_commcell_obj if tenant_admin_commcell_obj else self._commcell)
        if "usergroup" in entity_inputs:
            user_group_props = entity_inputs.get("usergroup")
            create_user_group_props = {
                "usergroup_name": ("" if user_group_props.get(
                    'domain') else prefix) + (user_group_props.get("group_name", "usergroup_{0}".format(timestamp))),
                "domain": user_group_props.get('domain'),
                "users_list": user_group_props.get('users'),
                "entity_dictionary": user_group_props.get('entity_dict'),
                "external_usergroup": user_group_props.get('external_groups'),
                "local_usergroup": user_group_props.get('local_groups')
            }

            if not create_user_group_props.get('entity_dictionary') and self.associations:
                create_user_group_props['entity_dictionary'] = sec_helper.generate_random_entity_dict(
                    entity_type=random.choices(entities_list)[0] if tenant_admin_commcell_obj else None,
                )

            self.log.info("Creating usergroup with props {0}".format(create_user_group_props))

            if tenant_admin_commcell_obj:
                user_group_object = tenant_admin_commcell_obj.user_groups.add(**create_user_group_props)
                tenant_admin_commcell_obj.user_groups.refresh()
            else:
                user_group_object = self._commcell.user_groups.add(**create_user_group_props)
            self._commcell.user_groups.refresh()
        if "user" in entity_inputs:
            user_props = dict(entity_inputs.get('user'))
            username = ("" if user_props.get("domain")
                        else prefix) + (user_props.get('user_name', "testuser_{0}".format(timestamp)))
            password = '' if user_props.get('domain') else user_props.get(
                "password", self.config_json.ADMIN_PASSWORD)
            create_user_props = {
                "user_name": username,
                "email": user_props.get("email", "{0}@commvault.com".format(username.replace("\\", "_"))),
                "full_name": user_props.get("full_name", username.replace("\\", "_")),
                "domain": user_props.get("domain"),
                "password": password,
                "local_usergroups": user_props.get("local_usergroups",
                                                   [user_group_object.name] if user_group_object else None),
                "entity_dictionary": user_props.get("security_dict")
            }
            if not create_user_props.get('entity_dictionary') and self.associations:
                create_user_props['entity_dictionary'] = sec_helper.generate_random_entity_dict(
                    entity_type=random.choices(entities_list)[0] if tenant_admin_commcell_obj else None,
                )

            self.log.info("Creating user with props {0}".format(create_user_props))

            if tenant_admin_commcell_obj:
                tenant_admin_commcell_obj.users.add(**create_user_props)
                tenant_admin_commcell_obj.users.refresh()
            else:
                self._commcell.users.add(**create_user_props)
            self._commcell.users.refresh()
            final_dict['username'] = create_user_props.get('user_name')
            final_dict['password'] = user_props.get('password') if user_props.get('domain') else password
            final_dict['email'] = create_user_props.get('email')
            final_dict['domain'] = create_user_props.get('domain')
        final_dict['level'] = "commcell" if not tenant_admin_commcell_obj else "company"
        final_dict['usergroupname'] = user_group_object.name if user_group_object else None
        return final_dict

    def restart_webserver(self):
        """restart webserver for windows/linux"""
        if "windows" in self.webserver_obj.os_info.lower():
            self.log.info("Performing IISRESET")
            try:
                self.webserver_obj.execute_command('iisreset /stop & iisreset /start')
            except Exception as exp:
                self.log.warn(f'Failed to restart IIS [Error: {exp}]')
                self.log.info('Ignoring the error and continuing... as connection must have been closed by IIS reset')
        else:
            self.log.info("Performing WebServerCore restart")
            self.webserver_obj.execute_command("commvault restart -s WebServerCore")
        time.sleep(60)

    def _users_to_be_validated(self, username, password, email=None, level='commcell',
                               usergroupname=None, domain=None):
        """
        adds users to global list, which can be used by validate methods for various feature validation.

        Args:
            username        (str)       --  username

            password        (str)       --  password

            email           (str)       --  email

            level           (str)       --  level at which user is available/created
                Values:
                "commcell"
                "company"

            usergroupname   (str)       --  name of the user group, given user is part of..

            domain          (str)       --  short name of the domain

        Returns:
            None

        """
        user_template = {
            "level": level,
            "usergroupname": usergroupname,
            "username": username,
            "password": password,
            "email": email,
            "domain": domain
        }
        self.users_login_details.append(user_template)

    def retry_webconsole_user_login(self, username, password, retry_count=1):
        """
        Retries webconsole/adminconsole login for 'n' number of times

        Args:
             username   (str)       --      name of the user

             password   (str)       --      password of the user

             retry_count    (int)   --      numbers of times user login needs to be attempted.

        Returns:
            bool        --  if login succeeds for at least once.

        Raises:
            Exception:
                if user login fails 'n' times.
        """
        for count in range(retry_count):
            self.log.info("retry count = {0} for user = {1}".format(count, username))
            try:
                self.userhelper.web_login(username, password,
                                          web=WebConstants(self._commcell.commserv_hostname))
            except Exception as exp:
                if "Invalid Username or Password" in str(exp):
                    raise Exception(exp)
                if count == retry_count - 1:
                    raise Exception(exp)
                self.log.info("retry count {0}, error={1}".format(count, exp))
                continue
            return True

    def prerequisites(self):
        """
        Creates company based on input json passed.
        Registers entities LDAP's(Active directory, LDAP Server) based on the input JSON passed.
        imports entities(External User/External User Group) based on the input JSON passed.

        Returns:
            None.
        """
        for level in self._tcinputs.keys():
            tenant_admin_commell_obj = None
            if level.lower() in ("commcell", "company"):
                commcell_obj = self._commcell
                ldap_entity_details = json.loads(self._tcinputs.get(level)).get('LDAPs', None)
                local_entity_details = json.loads(self._tcinputs.get(level)).get('Local', None)
                timestamp = datetime.strftime(datetime.now(), '%H%M%S')
                if level.lower() == 'company':
                    # create company/organization
                    company_name = 'company{0}'.format(timestamp)
                    company_email = company_name + "@commvault.com"
                    self.log.info("creating company {0}".format(company_name))
                    self.company_object = self.organizations.add(
                        name=company_name, email=company_email, contact_name=company_name, company_alias=company_name)
                    self.log.info("company {0} got created successfully".format(company_name))
                    organization_helper = OrganizationHelper(self._commcell, company_name)
                    tenant_admin_name = company_name + "\\" + company_name + "2"
                    new_password = self.config_json.ADMIN_PASSWORD
                    organization_helper.add_new_company_user_and_make_tenant_admin(tenant_admin_name, new_password)
                    user_obj = User(self._commcell, user_name=tenant_admin_name)
                    if self.associations:
                        self._users_to_be_validated(username=tenant_admin_name,
                                                    password=new_password,
                                                    email=user_obj.email,
                                                    level='company')
                    self._commcell.users.refresh()
                    if user_obj.is_tfa_enabled:
                        # call tfa api such that pin will get populated in db
                        self.userhelper.web_login(tenant_admin_name, new_password,web=WebConstants(self._commcell.commserv_hostname))
                        try:
                            Commcell(self._commcell.webconsole_hostname, tenant_admin_name, new_password, verify_ssl=self.config_json.API.VERIFY_SSL_CERTIFICATE)
                        except:
                            self.log.info("SDK Login fail without OTP validated")
                        new_password = self.userhelper.gen_tfa_password(tenant_admin_name, new_password)
                    self._tenant_admin_commell_obj = Commcell(self._commcell.webconsole_hostname,
                                                              commcell_username=tenant_admin_name,
                                                              commcell_password=new_password, verify_ssl=self.config_json.API.VERIFY_SSL_CERTIFICATE)
                    commcell_obj = self._tenant_admin_commell_obj

                # create local user/usergroups
                if local_entity_details:
                    for entity in local_entity_details:
                        entity_details = self.create_local_user_entity(
                            entity_inputs=entity,
                            tenant_admin_commcell_obj=self._tenant_admin_commell_obj if level.lower() == 'company' else None)
                        self._users_to_be_validated(**entity_details)

                # Register given directories with commcell/company
                if ldap_entity_details:
                    for server in ldap_entity_details:
                        # server_details = ldap_entity_details.get(server)
                        server_details = self.config_json.Security.LDAPs._asdict().get(server)._asdict()

                        # Check Domain already exists or not
                        if self._commcell.domains.has_domain(server_details.get('NETBIOSName')):
                            self._commcell.domains.delete(server_details.get('NETBIOSName'))
                            self._commcell.users.refresh()
                            self._commcell.user_groups.refresh()

                        parsed_additional_settings = []
                        if server_details.get('additionalSettings'):
                            for setting in server_details.get('additionalSettings'):
                                parsed_additional_settings.append(setting._asdict())

                        self.log.info("Trying to register domain {0}"
                                      " at {1} level".format(server_details.get('NETBIOSName'), level))
                        commcell_obj.domains.add(domain_name=server_details.get('DomainName'),
                                                 netbios_name=server_details.get('NETBIOSName'),
                                                 user_name=server_details.get('UserName'),
                                                 password=server_details.get('Password'),
                                                 company_id=int(self.company_object.organization_id)
                                                 if level.lower == 'company' else 0,
                                                 ad_proxy_list=server_details.get('ViaProxy'),
                                                 type_of_server=server.rsplit("_", 1)[0].replace("_", " "),
                                                 group_filter=server_details.get('group_filter'),
                                                 user_filter=server_details.get('user_filter'),
                                                 unique_identifier=server_details.get('unique_identifier'),
                                                 base_dn=server_details.get('base_dn'),
                                                 email_attribute=server_details.get('email_attribute', 'mail'),
                                                 guid_attribute=server_details.get('guid_attribute', 'objectGUID'),
                                                 additional_settings=parsed_additional_settings)
                        self.log.info("Domain {0} got added successfully"
                                      " at level {1}".format(server_details.get('NETBIOSName'), level))

                        # import external groups at (commcell\company) level
                        if server_details.get("UserGroupsToImport"):
                            for group in server_details.get("UserGroupsToImport"):
                                group = group._asdict()
                                assocs = (self.securityhelper.gen_random_entity_types_dict(2)
                                          if level.lower() == "commcell" else "")
                                self.log.info("Trying to add external group {0}"
                                              " at level {1}".format(group.get('externalgroup'), level))
                                entity_inputs = {
                                    "usergroup": {
                                        "group_name": group.get('externalgroup'),
                                        "domain": server_details.get('NETBIOSName')
                                    }
                                }
                                if self.associations:
                                    entity_inputs["usergroup"]["entity_dict"] = group.get('permissions', assocs)
                                self.create_local_user_entity(
                                    entity_inputs=entity_inputs,
                                    tenant_admin_commcell_obj=self._tenant_admin_commell_obj if level.lower() == 'company'
                                    else None)
                                self.log.info("External group {0} at level {1} is"
                                              " imported successfully".format(group.get('externalgroup'), level))

                        # import external users at (commcell\company) level
                        if server_details.get("UsersToImport"):
                            for user in server_details.get("UsersToImport"):
                                user = user._asdict()
                                assocs = (self.securityhelper.gen_random_entity_types_dict(2)
                                          if level.lower() == "commcell" else "")
                                self.log.info("Trying to add external user {0}"
                                              " at level {1}".format(user.get('UserName'), level))
                                entity_inputs = {
                                    "user": {
                                        "user_name": user.get('UserName'),
                                        "email": user.get('email', ''),
                                        "domain": server_details.get('NETBIOSName'),
                                        "password": user.get('Password')
                                    }
                                }
                                if self.associations:
                                    entity_inputs["user"]["security_dict"] = user.get('permissions', assocs)
                                entity_details = self.create_local_user_entity(entity_inputs=entity_inputs,
                                                                               tenant_admin_commcell_obj=self._tenant_admin_commell_obj if level.lower() == 'company' else None)
                                self._users_to_be_validated(**entity_details)
                                self.log.info("External user {0} is imported"
                                              " successfully".format(user.get('UserName')))
            elif level.lower() in 'domain':
                self.log.info('skipping as domain is already added')
            else:
                raise Exception('Please pass valid inputs...')

    def validate_multiusergroup_tfa(self):
        # case 1
        self.log.info("Verifying UserGroup level TFA operations")
        self.log.info("Creating Commcell Level User")
        local_user = self.create_local_user_entity(entity_inputs={"user": {}})
        self.log.info("Creating two usergroups with TFA enabled and disabled")
        local_usergroups = []
        for _ in range(2):
            local_usergroups.append(self.create_local_user_entity(entity_inputs={"usergroup": {}}))
        user_obj = self._commcell.users.get(local_user['username'])
        self.log.info("Disabling TFA for one usergroup")
        self._commcell.user_groups.get(local_usergroups[0]['usergroupname']).disable_tfa()
        self.log.info("Adding User to both these usergroups")
        user_obj.add_usergroups([name['usergroupname'] for name in local_usergroups])
        try:
            Commcell(self._commcell.webconsole_hostname, local_user.get("username"), local_user.get('password'), verify_ssl=self.config_json.API.VERIFY_SSL_CERTIFICATE)
            self.userhelper.web_login(local_user.get("username"), local_user.get('password'),
                                      web=WebConstants(self._commcell.commserv_hostname))
        except Exception as e:
            if 'Two-Factor' in str(e):
                raise Exception("FAILED TO VERIFY TFA LOGIN FOR MULTI USERGROUP SENERIO")

        # Case 2 -> Enabling TFA for only usergroups
        self._commcell.disable_tfa()
        time.sleep(10)
        self._commcell.enable_tfa(user_groups=[local_usergroups[0]['usergroupname']])
        try:
            Commcell(self._commcell.webconsole_hostname, local_user.get("username"), local_user.get('password'), verify_ssl=self.config_json.API.VERIFY_SSL_CERTIFICATE)
            self.userhelper.web_login(local_user.get("username"), local_user.get('password'),
                                      web=WebConstants(self._commcell.commserv_hostname))
        except Exception as e:
            if 'Two-Factor' in str(e):
                self.log.info("Successfully verified the case where one TFA is enabled for the user if they belong "
                              "to atleast 1 usergroup where TFA is enabled")
            else:
                raise Exception("Failed to verify TFA for usergroup senerio")
        self.log.info("Verified the Multi Usergroup TFA case")

        self._commcell.disable_tfa()
        time.sleep(10)
        # Deleting Entities
        self.log.info("Cleaning up entities")
        self.userhelper.delete_user(local_user.get('username'), new_user=self.config_json.ADMIN_USERNAME)
        for i in range(2):
            self._commcell.user_groups.delete(local_usergroups[i]['usergroupname'],
                                              new_user=self.config_json.ADMIN_USERNAME)
        self.log.info("Entity cleanup successful")

        self._commcell.enable_tfa()
        time.sleep(10)

    def validate_user_login(self, login_with="username", additional_setting=None):
        """
        validates user's login with username/email from adminconsole, webconsole, GUI.

        Args:
             login_with         (str)   --      login with username or email
                values:
                "username"
                "email"

            additional_setting  (dict)  --  required details for adding key 'nAllowUserWithoutRightToLogin'
                eg:
                {
                    "category": "CommServDB.GxGlobalParam",
                    "key_name": "nAllowUserWithoutRightToLogin",
                    "data_type": "INTEGER",
                    "value": "0"
                }

        Returns:
            None
        Raises:
            Exception:
                when user login fails
        """
        self.log.info("Validating users login with {0} and additional setting {1}".format(
            login_with, additional_setting))

        failed_login_counter = 0
        failed_users_list = []
        if additional_setting:
            # add additional setting if provided
            self.log.info("Adding Additional setting {0}".format(additional_setting))
            self._commcell.add_additional_setting(category=additional_setting["category"],
                                                  key_name=additional_setting["key_name"],
                                                  data_type=additional_setting["data_type"],
                                                  value=additional_setting["value"])
        try:
            for user in self.users_login_details:
                redundant_emails_found = False
                try:
                    self.log.info("Login attempt for user with username : {0}".format(user))
                    if login_with.lower() == 'username':
                        username = ((user.get('domain') + "\\" + user.get('username'))
                                    if user.get('domain') else user.get('username'))
                    elif login_with.lower() == 'email':
                        username = user.get('email')
                        record = self.utility.exec_commserv_query(query="select count(email) as count from umusers"
                                                                        " where email='{0}' and enabled=1"
                                                                        " group by email".format(username))
                        redundant_emails_found = int(record[0][0]) > 1
                    else:
                        raise Exception('please pass validate param')
                    if user.get('level').lower() == 'company' and not user.get('domain') and additional_setting:
                        failed_login_counter = failed_login_counter + 1
                        continue

                    # Selenium based Login's from adminconsole and webconsole
                    self.retry_webconsole_user_login(username=username, password=user.get('password'))

                    # Rest API Login
                    self.userhelper.gui_login(self._commcell.webconsole_hostname, username, user.get('password'))

                    # Qlogin's
                    if self.associations:
                        self.userhelper.qlogin(username=username, password=user.get('password'))

                except Exception as exp:
                    # if login fails for one user, catch the exception and continue login validations for other users

                    if "Invalid Username or Password" in str(exp) and not redundant_emails_found:
                        failed_login_counter = failed_login_counter + 1
                        failed_users_list.append(username)
                    else:
                        raise Exception(exp)

            if failed_login_counter:
                raise Exception('Login with {1} failed for {0} users, users List = {2} please check logs'
                                ' for more info'.format(failed_login_counter, login_with, failed_users_list))
        finally:
            if additional_setting:
                self.log.info("Deleting Additional setting {0}".format(additional_setting))
                self._commcell.delete_additional_setting(category=additional_setting["category"],
                                                         key_name=additional_setting["key_name"])

    def validate_association_less_login(self, login_with="username"):
        """
                validates user's login with username/email from adminconsole, webconsole, GUI.

                Args:
                     login_with         (str)   --      login with username or email
                        values:
                        "username"
                        "email"

                Returns:
                    None
        """

        self.log.info("Validating users login with {0}".format(login_with))
        failed_login_counter = 0
        failed_users_list = []
        for user in self.users_login_details:
            if login_with.lower() == 'username':
                username = ((user.get('domain') + "\\" + user.get('username'))
                            if user.get('domain') else user.get('username'))
            elif login_with.lower() == 'email':
                username = user.get('email')
            else:
                raise Exception('please pass validate param')

            try:
                # Selenium based Login's from adminconsole and webconsole
                self.userhelper.web_login(user_name=username, password=user.get('password'),
                                          web=WebConstants(self._commcell.webconsole_hostname))
                raise Exception("User is able to login")
            except Exception as exp:
                if "You do not have the credentials to log in to this CommServe" not in str(exp):
                    failed_login_counter = failed_login_counter + 1
                    failed_users_list.append(username)
                    self.log.info(exp)

            try:
                # Rest API Login
                self.userhelper.gui_login(self._commcell.webconsole_hostname, username, user.get('password'))
                raise Exception("User is able to login")
            except Exception as exp:
                if "User has no credentials on this CommServe" not in str(exp):
                    failed_login_counter = failed_login_counter + 1
                    failed_users_list.append(username)
                    self.log.info(exp)
            try:
                # Qlogin's
                self.userhelper.qlogin(username=username, password=user.get('password'))
                raise Exception("User is able to login")
            except Exception as exp:
                if "User has no credentials on this CommServe" not in str(exp):
                    failed_login_counter = failed_login_counter + 1
                    failed_users_list.append(username)
                    self.log.info(exp)

        if failed_login_counter:
            raise Exception('Login with username failed for {0} users, users List = {1} please check logs'
                            'for more info'.format(failed_login_counter, failed_users_list))                                                     

    def validate_domain_less_login(self, default_ad_user_domain, default_cs_domain='local'):
        """
        Validates domainless login feature for various user's

        Args:
            default_ad_user_domain      (str)       --      name of the domain, which will be set as default domain

            default_cs_domain            (str)      --      name of the default cs domain
                default:
                "local"

        Returns:
            None

        Raises:
            Exception:
                if feature validations fails
        """
        self.log.info("Adding Additional settings DefaultADUserDomain with value = {0}".format(default_ad_user_domain))
        self._commcell.add_additional_setting(category="CommServDB.GxGlobalParam",
                                              key_name="DefaultADUserDomain",
                                              data_type="STRING",
                                              value=default_ad_user_domain)

        self.log.info("Key got added successfully.")
        try:
            self.restart_webserver()
            # below we are trying to login without any prefix for all user's[commcelll user, other AD users]
            # bascially negative cases are handled
            unallowed_user = 0
            # create commcell local user
            local_user = self.create_local_user_entity(entity_inputs={"user": {}})
            for user in self.users_login_details:
                try:
                    self.log.info("Performing login without prefix for user = {0}".format(user.get('username')))
                    self.userhelper.gui_login(self._commcell.webconsole_hostname,
                                              user.get('username'), user.get('password'))
                    self.retry_webconsole_user_login(username=user.get('username'), password=user.get('password'))
                    if user.get('domain') and user.get('domain').lower() != default_ad_user_domain.lower():
                        unallowed_user = unallowed_user + 1
                except Exception as excp:
                    if user.get('domain') and user.get('domain').lower() == default_ad_user_domain.lower():
                        raise Exception("User {0} must be able to login,"
                                        " something went wrong excp = {1}".format(user.get('username'), excp))
                    self.log.info("user {0} login failed, Expected"
                                  " behavior excp = {1}".format(user.get('username'), excp))
                if unallowed_user:
                    raise Exception('Login must fail for username {0}, as'
                                    ' key is set DefaultADUserDomain'.format(user.get('username')))
            #login for commcell user with 'local' as prefix
            try:
                self.retry_webconsole_user_login(username="local"+"\\"+local_user["username"], password=local_user["password"])
            except Exception as exp:
                raise Exception(exp)
            if default_cs_domain.lower() != "local":
                self.log.info("Adding additional setting DefaultCSDomain with value = {0}".format(default_cs_domain))
                self._commcell.add_additional_setting(category="CommServDB.GxGlobalParam",
                                                      key_name="DefaultCSDomain",
                                                      data_type="STRING",
                                                      value=default_cs_domain)
            self.log.info("Key got added successfully.")
            self.restart_webserver()
            # below we are trying to login with prefix for all user's(i.e)
            # for commcell local user default prefix is local\\
            self._users_to_be_validated(**local_user)
            failed_user_login = 0
            for user in self.users_login_details:
                if user.get('domain'):
                    username = user.get('domain') + "\\" + user.get('username')
                elif user.get('level').lower() == "commcell":
                    username = default_cs_domain + "\\" + user.get('username')
                else:
                    username = user.get('username')
                self.log.info("Performing user login with prefix for user {0}".format(username))
                try:
                    self.userhelper.gui_login(self._commcell.webconsole_hostname, username, user.get('password'))
                    self.retry_webconsole_user_login(username=username, password=user.get('password'))
                except Exception as excp:
                    failed_user_login = failed_user_login + 1
                    self.log.info("Login failed for user {0}, excp={1}".format(username, excp))
            if failed_user_login:
                raise Exception("login failed for {0} users, please check logs".format(failed_user_login))
            # login for commcell user with 'local' as prefix
            try:
                self.retry_webconsole_user_login(username="local" + "\\" + local_user["username"],
                                                 password=local_user["password"])
                raise Exception("User is able to login")
            except Exception as exp:
                if "Invalid Username or Password" not in str(exp):
                    raise Exception(exp)
            self.log.info("Domainless login feature is validated successfully")
        finally:
            self.log.info("Deleting additional keys...")
            self._commcell.delete_additional_setting(category="CommServDB.GxGlobalParam",
                                                     key_name="DefaultADUserDomain")
            if default_cs_domain.lower() != "local":
                self._commcell.delete_additional_setting(category="CommServDB.GxGlobalParam",
                                                         key_name="DefaultCSDomain")
            self.restart_webserver()

    def validate_password_complexity_and_history_features(self, password_history, complexity_level=2,
                                                          age_password_days=1):
        """
        validates features password history, complexity level and age user password.

        Args:
            password_history    (dict)  --  required values for enabling password history feature
                eg:- {
                        "level" : "commcell",
                        "value" : 2
                    }

            complexity_level    (int)   --  level of complex password to be verified.

            age_password_days   (int)   --  number of days for password expiry.

        Returns:
            None

        Raises:
            Exception:
                if feature validations fails
        """
        self.log.info("Adding Additional settings bMaintainPasswordHistory with"
                      " value = {0}".format(password_history))
        self._commcell.add_additional_setting(category="CommServDB.Console",
                                              key_name="bMaintainPasswordHistory",
                                              data_type="BOOLEAN",
                                              value='true')
        if password_history.get('level') == "commcell":
            self._commcell.add_additional_setting(category="CommServDB.GxGlobalParam",
                                                  key_name="Password History Count",
                                                  data_type="INTEGER",
                                                  value=str(password_history.get('value')))
        self.client_obj.restart_services()
        self.restart_webserver()

        # Changing User password with current password
        for user in self.users_login_details:
            user_obj = User(self._commcell, user_name=user.get('username'))
            self.log.info("password change with existing password..")
            try:
                user_obj.update_user_password(new_password=user.get('password'),
                                              logged_in_user_password=self.config_json.ADMIN_PASSWORD)
                raise Exception("password change operation with existing password should fail")
            except Exception as exp:
                if "Please use a different password" not in str(exp):
                    raise Exception(exp)
                self.log.info(exp)

        self.log.info("Adding Additional settings passwordComplexityLevel with"
                      " value = {0}".format(complexity_level))
        self._commcell.add_additional_setting(category="CommServDB.GxGlobalParam",
                                              key_name="passwordComplexityLevel",
                                              data_type="INTEGER",
                                              value=str(complexity_level))

        self.log.info("Keys got added successfully.")
        try:
            # try to create a local user with less complex password(i.e) using
            # password_generator generate less complex password and verify exception
            self.client_obj.restart_services()
            self.restart_webserver()

            self.log.info("try to create a local user with less complex password..")
            try:
                self.create_local_user_entity(entity_inputs={
                    "user": {"password": self.userhelper.password_generator(complexity_level - 1)}})
                raise Exception("user creation with less complex should fail")
            except Exception as excp:
                if "User password doesn't follow minimum complexity requirements" not in str(excp):
                    raise Exception(excp)
                self.log.info(excp)

            # now try creating user with complex password
            self.log.info("try creating user with password of complexity level = {0}".format(complexity_level))
            self.create_local_user_entity(entity_inputs={
                "user": {"password": self.userhelper.password_generator(complexity_level, min_length=12)}})

            for user in self.users_login_details:
                user_obj = User(self._commcell, user_name=user.get('username'))

                # expire user password
                user_obj.age_password_days = age_password_days

                # create old timestamp
                old_timestamp = int(datetime.timestamp(datetime.now())) - ((age_password_days + 2) * 24 * 60 * 60)
                self.log.info("Forcing user password expiry with age password = {0} and old timetsamp = {1}".format(
                    age_password_days, old_timestamp
                ))
                self.utility.update_commserve_db(
                    "update umusers set datePasswordSet={0} where login like '%{1}%'".format(
                        old_timestamp, user.get('username'))
                )
                self.restart_webserver()
                try:
                    self.userhelper.gui_login(self._commcell.webconsole_hostname,
                                              user.get('username'),
                                              user.get('password'))
                    raise Exception("User is able to login")
                except Exception as exp:
                    if "Password Expired" not in str(exp):
                        raise Exception(exp)
                    self.log.info(exp)
                self.log.info("user Password expiry scenario is validated successfully")
                # try password change with less complex password and verify exception
                self.log.info("try password change with less complex password..")
                try:
                    user_obj.update_user_password(
                        new_password=self.userhelper.password_generator(complexity_level - 1),
                        logged_in_user_password=self.config_json.ADMIN_PASSWORD)
                    raise Exception("password change operation with less complex should fail")
                except Exception as exp:
                    if "User password doesn't follow minimum complexity requirements" not in str(exp):
                        raise Exception(exp)
                    self.log.info(exp)

                # try password change with existing password and verify exception
                # self.log.info("password change with existing password..")
                # try:
                #     user_obj.update_user_password(new_password=user.get('password'),
                #                                   logged_in_user_password=self.config_json.ADMIN_PASSWORD)
                #     raise Exception("password change operation with existing password should fail")
                # except Exception as exp:
                #     if "Please use a different password" not in str(exp):
                #         raise Exception(exp)
                #     self.log.info(exp)

                # try password change with complex password
                new_password = self.userhelper.password_generator(complexity_level, min_length=12)
                user_obj.update_user_password(new_password=new_password,
                                              logged_in_user_password=self.config_json.ADMIN_PASSWORD)
                self.retry_webconsole_user_login(username=user.get('username'), password=new_password)
                self.userhelper.gui_login(self._commcell.webconsole_hostname, user.get('username'), new_password)
                self.log.info("Password history = {0}, Password complexity = {1}"
                              " and age password = {2} are validated"
                              " successfully".format(password_history, complexity_level, age_password_days))
        finally:
            self.log.info("Deleting additional keys...")
            self._commcell.delete_additional_setting(category="CommServDB.GxGlobalParam",
                                                     key_name="passwordComplexityLevel")
            self._commcell.delete_additional_setting(category="CommServDB.Console",
                                                     key_name="bMaintainPasswordHistory")

    def validate_ownership_transfer(self):
        """
        Validates ownership transfer for commcell, company users
        """
        # iterate over users list (commcell user, company user, LDAP users)
        # make them part of Master\Tenant admin group
        # login as user and create any ownership entity
        # transfer ownership to another user\user group
        # finally transfer to Master or Tenant admin group

        for user in self.users_login_details:
            username = ((user.get('domain') + "\\" + user.get('username'))
                        if user.get('domain') else user.get('username'))

            user_obj = self._commcell.users.get(user_name=username)
            user_groups = user_obj.associated_external_usergroups
            if 'Tenant Admin' in user_groups:
                # if user is part of Tenant admin user group. ownership will be given to
                # Tenant admin group. so skipping for now
                continue

            # Make user part of Master\Tenant admin group
            if user.get('level') == 'commcell':
                user_obj.update_security_associations(
                    entity_dictionary={'assoc1':
                        {
                            'commCellName': [self._commcell.commserv_name],
                            'role': ['Master']
                        }}, request_type="UPDATE")
            else:
                user_obj.update_security_associations(
                    entity_dictionary={'assoc1':
                        {
                            'providerDomainName': [user_obj.user_company_name],
                            'role': ['Tenant Admin']
                        }}, request_type="UPDATE")

            owned_entities = self.userhelper.create_random_ownership_entity(username=username,
                                                                            password=user.get('password'))

            user_obj = self._commcell.users.get(user_name=username)

            # Verify user has ownership associations or not
            self._verify_ownership_associations(user_obj.user_security_associations, owned_entities)

            # create new user \user group for ownership transfer
            choice = random.choices([0, 1])[0]
            # choice = 1 -- creates user entity else creates user group entity
            if choice:
                if user.get('level') == 'commcell':
                    props = self.create_local_user_entity(entity_inputs={"user": {}})
                else:
                    props = self.create_local_user_entity(entity_inputs={"user": {}},
                                                          tenant_admin_commcell_obj=self._tenant_admin_commell_obj)
            else:
                if user.get('level') == 'commcell':
                    props = self.create_local_user_entity(entity_inputs={"usergroup": {}})
                else:
                    props = self.create_local_user_entity(entity_inputs={"usergroup": {}},
                                                          tenant_admin_commcell_obj=self._tenant_admin_commell_obj)

            if choice:
                # Transfers ownership to new user
                self._commcell.users.delete(user_name=username, new_user=props.get('username'))
                new_user_obj = self._commcell.users.get(user_name=props.get('username'))
                self._verify_ownership_associations(new_user_obj.user_security_associations, owned_entities)
            else:
                # Transfers ownership to new user group
                self._commcell.users.delete(user_name=username, new_usergroup=props.get('usergroupname'))
                new_usergroup_obj = self._commcell.user_groups.get(user_group_name=props.get('usergroupname'))
                self._verify_ownership_associations(new_usergroup_obj.associations, owned_entities)

            # Finally transfer ownership to Master\Tenant admin groups and delete user\user group.

            if choice:
                if user.get('level') == 'commcell':
                    self._commcell.users.delete(user_name=props.get('username'), new_usergroup='Master')
                else:
                    self._commcell.users.delete(user_name=props.get('username'),
                                                new_usergroup=user_obj.user_company_name + '\\Tenant Admin')
            else:
                if user.get('level') == 'commcell':
                    self._commcell.user_groups.delete(user_group=props.get('usergroupname'), new_usergroup='Master')
                else:
                    self._commcell.user_groups.delete(user_group=props.get('usergroupname'),
                                                      new_usergroup=user_obj.user_company_name + '\\Tenant Admin')
            self.log.info("Ownership transfer is validated successfully for {0}".format(username))

    def _verify_ownership_associations(self, security_associations, owned_entities):
        """
        Verifies owned entities present in user\\user group security_associations

        Args:
            security_associations   --  (list)  list containing security associations

            owned_entities      --  (dict)  dict containing the owned entities

        Returns:
            None
        Raises:
            Exception:
                if security associations doesn't contain owned entity.
        """
        for entity in owned_entities:
            found = False
            for association in security_associations:
                if (entity in security_associations[association]
                        and owned_entities[entity].lower() in security_associations[association]):
                    found = True
                    self.log.info("ownership association found {0}".format(security_associations[association]))
                    break
            if not found:
                raise Exception("ownership association not found for {0}".format(owned_entities[entity]))


    def validate_qlogin_operation(self, local_user = True):
        if local_user:
            self.log.info("Creating a local user with random permissions.")
            user = self.create_local_user_entity({
                "user": {}
            })
            self.log.info("Local User creation is success.")
            username = user['username']
            password = user['password']
        else:
            username = self.config_json.EXTERNAL_USER
            password = self.config_json.EXTERNAL_USER_PASSWORD

        try:
            self.log.info("Attempting QLogin for the user")
            # Attempt Qlogin operation for the user.
            self._commcell.commserv_client.execute_command(f"qlogin -u {username}  -clp {password}")
            self.utility.sleep_time(30)
            self._commcell.commserv_client.execute_command("qlogout")
            self.log.info("Qlogin was successful, user logged out")

            if local_user:
                self.log.info("Changing the password of the user.")
                # Create the user object and then change the password.
                user_obj = User(self._commcell, user_name=user['username'])
                password = self.userhelper.password_generator(complexity_level=3)
                user_obj.update_user_password(new_password=password,
                                              logged_in_user_password=self.config_json.ADMIN_PASSWORD)
                self.log.info("Password change successful.")

                self.log.info("Attempting QLogin for the local user post password change.")
                # Now try login again with the new password.
                self._commcell.commserv_client.execute_command(f"qlogin -u {username}  -clp {password}")
                self.utility.sleep_time(30)
                self._commcell.commserv_client.execute_command("qlogout")


            self.log.info("Attempting QLogin for the user with save file parameter.")
            self._commcell.commserv_client.execute_command(f"qlogin -u {username}  -clp {password} -f")
            self.utility.sleep_time(30)
            self._commcell.commserv_client.execute_command("qlogout")
            self.log.info("Qlogin was successful, user logged out")

            self.log.info("Attempting QLogin for the user with get token param and using it to perform login.")
            response = self._commcell.commserv_client.execute_command(
                f"qlogin -u {username}  -clp {password} -gt")
            self.utility.sleep_time(30)
            self.log.info("Now performing login with the token.")
            self._commcell.commserv_client.execute_command(f"qlogin -u {username}  -ps {response[1]}")
            self.utility.sleep_time(30)
            self._commcell.commserv_client.execute_command("qlogout")
            self.log.info("Qlogin was successful, user logged out")

        except Exception as e:
            raise e

        finally:
            if local_user:
                self.userhelper.delete_user(user_name=user['username'], new_user=self.config_json.ADMIN_USERNAME)
