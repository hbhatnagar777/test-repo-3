# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing User related operations on Commcell
UserProperties:
    __init__()                      --  initializing the user details

UserHelper:
    __init__()                      --  Initialize UserHelper object

    create_user()                   --  Creates new user on the CommCell

    delete_user()                   --  Deletes user passed

    _browser_setup()                --  Sets up browser constants

    gui_login()                     --  Performs auth token logins

    qlogin()                        --  Performs qlogin's

    web_login()                     --  Performs admin console and admin console login

    gen_TFA_password()              --  Fetches one time pin for users

    enable_TFA()                    --  Enables Two Factor Authentication on the CommCell

    disable_TFA()                   --  Disables Two Factor Authentication on the CommCell

    special_char_user_generator()   --  generates username and full name with special characters

    modify_security_associations()  --  Validates security Associations on user and userggroup

    check_if_hidden_user_exists()    --  Checks if hidden user exits or not on the CommCell

    password_generator()             --  generates password based on complexity level and min length

    create_random_ownership_entity() --  Creates ownership entities like Alert, Client group\SCG, credentials account

    cleanup_users()                  --   Delete users that has provided marker / string

    validate_users_cache_data()      --  validates the data returned from Mongo cache for user collection

    validate_sort_on_cached_data()   --  validates sort parameter on entity cache API call

    validate_limit_on_cache()        --  validates limit parameter on entity cache API call

    validate_search_on_cache()       --  validates search parameter on entity cache API call

    validate_filter_on_cache()       --  validates fq param on entity cache API call

    __get_token_from_email()         --  Parses the reset password email and extracts the token from the reset link

    reset_tenant_admin_password()    --  Resets the tenant admin password using the token extracted from the reset email

"""
import random
import locale
import string
import re
from datetime import datetime
import pyotp
import requests
from cvpysdk.commcell import Commcell
from AutomationUtils import database_helper, cvhelper
from Server.Security.securityhelper import RoleHelper
from AutomationUtils import logger, options_selector, config
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.WebConsole.webconsole import WebConsole

from Server.Security.credentialmanagerhelper import CredentialHelper
from Server.Scheduler.schedulerhelper import ScheduleCreationHelper


class UserProperties(object):
    """initializing the user details """

    def __init__(self, name, cs_host, full_name=None, email=None, password=None, domain=None):
        """Initializes UserProperties object

        Args:
            name        (str)   --  name of the user

            cs_host     (str)   --  commcell host name

            full_name   (str)   --  full name for user

            email       (str)   --  user's email id

            password    (str)   --  password for user

            domain      (str)   --  domain name to which user is belongs to
        """
        self.username = name
        self.cs_host = cs_host
        self.full_name = full_name
        self.email = email
        self.password = password
        self.domain = domain


class UserHelper(object):
    """Helper class to perform User related operations"""

    def __init__(self, commcell: Commcell, user=None):
        """Initializes UserHelper object

        Args:
            commcell    (obj)   --  Commcell object

            user        (obj)   --  user object
        """
        self._user = None
        if user:
            self._user = user
        self.log = logger.get_log()
        self.commcell_obj = commcell
        self.single_user = None
        self.usergroup = None
        self.config_json = config.get_config()
        self._csdb = database_helper.CommServDatabase(commcell)
        self.role_helper = RoleHelper(self.commcell_obj)
        self._utility = options_selector.OptionsSelector(self.commcell_obj)
        self.__cl_obj = None # create during runtime to avoid object creation failure for non-admin users
        self.login_obj = None
        self.options_selector = options_selector.OptionsSelector(commcell)
        self.users_obj = self.commcell_obj.users

    @property
    def cl_obj(self):
        if not self.__cl_obj:
            self.__cl_obj = self.commcell_obj.commserv_client
        return self.__cl_obj

    def create_user(self, user_name, email, full_name=None, domain=None, password=None,
                    local_usergroups=None, security_dict=None):
        """Adds a local/external user to this commcell

            Args:
                user_name                     (str)     --  name of the user to be
                                                            created

                full_name                     (str)     --  full name of the user to be
                                                            created

                email                         (str)     --  email of the user to be
                                                            created

                domain                        (str)     --  Needed in case you are adding
                                                            external user

                password                      (str)     --  password of the user to be
                                                            created
                                                            default: None

                local_usergroups              (str)     --  user can be member of
                                                            these user groups

                security_dict                 (str)     --  Role-Entity combination

                                e.g.: Security_dict={
                                'assoc1':
                                    {
                                        'entity_type':['entity_name'],
                                        'entity_type':['entity_name', 'entity_name'],
                                        'role': ['role1']
                                    },
                                'assoc2':
                                    {
                                        'mediaAgentName': ['networktestcs', 'standbycs'],
                                        'clientName': ['Linux1'],
                                        'role': ['New1']
                                        }
                                    }
         """
        self.log.info("Creating User %s", user_name)
        self._user = self.commcell_obj.users.add(user_name=user_name,
                                                 full_name=full_name,
                                                 domain=domain,
                                                 password=password,
                                                 email=email,
                                                 local_usergroups=local_usergroups,
                                                 entity_dictionary=security_dict)

        self.log.info("User [{0}] created successfully".format(user_name))
        return self._user

    def delete_user(self, user_name, new_user=None, new_group=None):
        """Deletes the user passed
        Args:
            user_name       (str)   -- object of user to be deleted

            new_user        (str)   -- user to whom ownership of entities will be transferred

            new_group       (str)   -- user group to whom ownership will be transferred

        """
        self.log.info("Deleting user: %s", user_name)

        self.commcell_obj.users.refresh()
        user = self.commcell_obj.users.has_user(user_name=user_name)
        if user:
            self.commcell_obj.users.delete(user_name=user_name, new_user=new_user, new_usergroup=new_group)
            self.log.info("Deleted user [{0}] successfully".format(user_name))
        else:
            self.log.info("Specified user is not present on the CommCell %s", user_name)

    def _browser_setup(self):
        """sets up browser constants

            returns:
                browser object
         """
        self.log.info("Initializing browser objects.")
        factory = BrowserFactory()
        browser = factory.create_browser_object()
        browser.open()
        return browser

    def web_login(self, user_name, password, web, is_webconsole=False):
        """Performs admin console and admin console login
        Args:
            user_name   (str)   --  name of the user

            password    (str)   --  password for user

            web         (object)   --  object of class WebConstants

            is_webconsole (bool) -- check for Webconsole login

            Raises:
                Exception:
                    if user deletion is unsuccessful

        """

        if is_webconsole:
            web_urls = [web.adminconsole_url, web.webconsole_url]
            self.log.info("Login to webconsole and admin console")
        else:
            web_urls = [web.adminconsole_url]
            self.log.info("Login to admin console")

        browser = self._browser_setup()
        for url in web_urls:
            try:
                self.log.info("Create the login object.")
                self.log.info("Login to %s.", url)
                self.log.info("trying login with password: %s", password)
                if url.lower().endswith("adminconsole"):
                    self.login_obj = AdminConsole(browser, self.commcell_obj.webconsole_hostname)
                elif url.lower().endswith("webconsole"):
                    self.login_obj = WebConsole(browser, self.commcell_obj.webconsole_hostname)
                else:
                    raise Exception('please pass valid interface name')
                if self.commcell_obj.users.has_user(user_name) and self.commcell_obj.users.get(user_name.lower()).is_tfa_enabled and self.get_tfa_otp(user_name):
                    self.login_obj.login(user_name, password, pin_generator=lambda: self.get_tfa_otp(user_name))
                else:
                    self.login_obj.login(user_name, password)
                base = AdminConsole(browser, self.commcell_obj.webconsole_hostname)
                base.check_error_message()
                self.log.info("Successfully logged into %s.", url)
                if url.lower().endswith("adminconsole"):
                    self.login_obj.navigator.navigate_to_virtualization()
                    self.login_obj.wait_for_completion()
                    AdminConsole.logout(self.login_obj)
                else:
                    WebConsole.logout(self.login_obj)
            except Exception as exp:
                self.log.error("Failed: %s", exp)
                Browser.close_silently(browser)
                raise Exception("Something went wrong. Please check logs for more details. error = {0}".format(exp))
        Browser.close_silently(browser)

    def gui_login(self, cs_host, user_name, password):
        """performs authtoken logins
        Args:

            cs_host     (str)   --  CommCell host name

            user_name   (str)   --  user object to perform web login operation

            password    (str)   --  password for user

            Raises:
                Exception:
                    if user login is unsuccessful

        """
        try:
            Commcell(cs_host, user_name, password, verify_ssl=self.config_json.API.VERIFY_SSL_CERTIFICATE)
            self.log.info("login successful")
        except Exception as exp:
            if 'Two-Factor' in str(exp):
                self.log.info("Two-Factor Authentication is enabled on this CommServe")
                new_password = self.gen_tfa_password(user_name=user_name, password=password)
                self.log.info("trying gui login with new password %s", new_password)
                try:
                    Commcell(cs_host, user_name, new_password, verify_ssl=self.config_json.API.VERIFY_SSL_CERTIFICATE)
                    self.log.info("Two Factor Authentication login is successful")
                except Exception as exp:
                    raise Exception("login is not successful due to:", exp)
            else:
                raise Exception("login is not successful due to:", exp)

    def qlogin(self, username=None, password=None, **kwargs):
        """
        Performs qlogin's

        Args:
             username       (str)   --    name of the user

             password       (str)   --     password of the user

             kwargs         (dict)  --  additional script arguments.

             pls refer below doc for additionals arguments and it's description.
                https://documentation.commvault.com/commvault/v11_sp20/article?p=45203.htm

        Raises:
            Exception:
                if qlogin's fail
                if required params are not sent
        """
        cmd_args = ""
        if not username and not password:
            cmd_args = cmd_args + '-localadmin localadmin'
        else:
            if not username:
                raise Exception('username parameter is required for qlogin')
            if not password and 'passwordstrong' not in kwargs:
                raise Exception("password or passwordstrong paramter is required for qlogin")
            cmd_args = cmd_args + '-u ' + f"'{username}'"
            if 'commserve' in kwargs:
                cmd_args = cmd_args + ' -cs ' + kwargs.get('commserve')
            if 'argsfile' in kwargs:
                cmd_args = cmd_args + ' -af ' + kwargs.get('argsfile')
            if 'logintokenfile' in kwargs:
                cmd_args = cmd_args + ' -f ' + kwargs.get('logintokenfile')
            if 'givetoken' in kwargs:
                cmd_args = cmd_args + ' -gt '
            if 'csclientName' in kwargs:
                cmd_args = cmd_args + ' -csn ' + kwargs.get('csClientName')
            if 'sso' in kwargs:
                cmd_args = cmd_args + ' -sso '
            if 'passwordstrong' in kwargs:
                cmd_args = cmd_args + ' -ps ' + kwargs.get('passwordstrong')
            else:
                cmd_args = cmd_args + ' -clp ' + f"'{password}'"
        self.commcell_obj.commserv_client.execute_command(command="qlogout", script_arguments="-all")
        self.log.info("Final qlogin cmd = {0}".format(cmd_args))
        output = self.commcell_obj.commserv_client.execute_command(command="qlogin", script_arguments=cmd_args)
        self.log.info("qlogin output = {0}".format(output))
        if output[0]:
            if 'Two-Factor' in output[2]:
                self.log.info("Two-Factor Authentication is enabled on this CommServe")
                old_password = password if password else kwargs.get('passwordstrong')
                new_password = self.gen_tfa_password(user_name=username,
                                                     password=old_password)
                self.log.info("trying qlogin login with new password %s", new_password)
                output = self.commcell_obj.commserv_client.execute_command(command="qlogin",
                                                                           script_arguments=cmd_args.replace(
                                                                               f"'{old_password}'", f"'{new_password}'"))
            if output[0]:
                raise Exception('Qlogin Failed for user: output = {0}'.format(output))
        else:
            self.log.info('qlogin is successful for user = {0}, output = {1}'.format(username, output))

    def gen_tfa_password(self, user_name, password):
        """Fetches one time pin for users
        Args:
            user_name   (str)   --  user object to perform web login operation

            password    (str)   --  password for user

        Returns:
            New password(str)   --  returns new password (old password+OTP)

            Raises:
                Exception:
                    if user login is unsuccessful

        """
        self.log.info("Generating pwd+otp for user: %s ", user_name)
        return password + self.get_tfa_otp(user_name)

    def get_tfa_otp(self, user_name):
        """
        Gets OTP for TFA user from secret key in DB
        """
        self.log.info("Generating OTP for user: %s ", user_name)
        self.single_user = self.commcell_obj.users.get(user_name)
        db_key = self.get_user_secret_key(self.single_user.user_id)
        if not db_key:
            return False
        totp = pyotp.totp.TOTP(db_key)
        return totp.now()

    def get_user_secret_key(self, user_id):
        """Gets user's secret key from DB"""
        query = "select attrVal from UMUsersProp where componentNameId={0} and attrName='secret'"
        self._csdb.execute(query.format(user_id))
        try:
            return cvhelper.format_string(self.commcell_obj, self._csdb.rows[0][0])
        except:
            return None

    def enable_tfa(self):
        """Enables Two Factor Authentication on the CommCell
        """
        self.log.info("Enbling Two-Factor Authentication on Commcell")

        self.cl_obj.add_additional_setting(category='CommServDB.GxGlobalParam',
                                           key_name='EnableTwoFactorAuthentication',
                                           data_type='BOOLEAN', value='1')
        self.log.info("*****Successfully Enabled Two-Factor Authentication*****")
        self.log.info("*****Failed Login attempt is required to generate One Time Pin*****")

    def disable_tfa(self):
        """Disables Two Factor Authentication on the CommCell
        """
        self.log.info("Dissabling Two-Factor Authentication on Commcell")

        self.cl_obj.add_additional_setting(category='CommServDB.GxGlobalParam',
                                           key_name='EnableTwoFactorAuthentication',
                                           data_type='BOOLEAN', value='0')
        self.log.info("*****Successfully Disabled Two-Factor Authentication*****")

    def special_char_user_generator(self, special_char_only: bool = True):
        """Creating user with special characters
        Args:
            special_char_only    (bool)   :   name of the user

        Returns:
            username, fullname
        """
        special_char = ['!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', ':', ';', '<', '=',
                        '>', '?', '@', '[', ']', '^', '_', '`', '{', '|', '}', '~', '¡', '¢', '£', '¤', '¥', '¦',
                        '§', '¨', '©', 'ª', '«', '¬', '®', '¯', '°', '±', '²', '³', '´', 'µ', '¶', '·', '¸', '¹',
                        '»', '¼', '½', '¾', '¿', '†', '‡', '•', '…', '‰', '′', '″', '‹', '›', '‼', '‽', '⁂', '€',
                        '∑', '∏', '√', '中', '文', 'º']
        if not special_char_only:
            special_char.extend(string.ascii_letters)
            username = random.sample(special_char, random.randint(21, 30))
            fullname = random.sample(special_char, random.randint(21, 30))
        else:
            username = random.sample(special_char, random.randint(8, 10))
            fullname = random.sample(special_char, random.randint(8, 10))
        username = ''.join(username)
        fullname = ''.join(fullname)
        return username, fullname

    def modify_security_associations(self, entity_dict, user_name, request='UPDATE'):
        """Validates security Associations on user and userggroup
        Args:
            entity_dict         (Dict)  :   entity-role association dict

            request             (Str)   :   decides whether to UPDATE, DELETE or
                                            OVERWRITE user security association
        Raises:
                Exception:
                    if any of the association from passed entity_dict doesn't present on the user
                    or usergroup.

        """
        if request not in ['UPDATE', 'ADD', 'OVERWRITE', 'DELETE']:
            raise Exception("Invalid Request type is sent to the  function!!")
        else:
            self.user = self.commcell_obj.users.get(user_name)
            self.user.update_security_associations(entity_dictionary=entity_dict,
                                                   request_type=request)
            self.log.info("Secussful !!")

    def check_if_hidden_user_exists(self, user_name):
        """Checks if the hidden user exists in db or not
        Args:
            user_name           (Str)   :   name of the user

            request             (Str)   :   decides whether to UPDATE, DELETE or
                                            OVERWRITE user security association
        Returns:
            True : If user exists
            False : If user doesnt exists.
        """

        query_1 = "select 1 from UMUsers where login = '{0}'".format(user_name)
        self._csdb.execute(query_1)
        if (self._csdb.rows[0][0] == '1'):
            return True
        return False

    def get_user_clients(self):
        """Returns the list of clients for the user
        """
        clients = []
        user_id = self._user.user_id
        query = f"""CREATE TABLE #getIdaObjects 
                                  (clientId INT, apptypeId INT, instanceID INT, backupsetId INT, subclientID INT,primary key(clientId,appTypeId,instanceId,backupsetId,subclientId))
                                  EXEC sec_getIdaObjectsForUser {user_id}, 3, 0,0, '#getIdaObjects', 0, '2';
                                  select name from app_client where id in (select clientId from #getIdaObjects);"""
        db_response = self.options_selector.update_commserve_db_via_cre(query)
        for client in db_response:
            clients.append(client[0])

        return clients

    @staticmethod
    def password_generator(complexity_level=2, min_length=8):
        """
        generates password based on complexity level and min length

        Args:
            complexity_level    (int) -- complexity level
                supported values: 1 or 2 or 3

                1 - There are no requirements for passwords.
                2 - Passwords must have at least eight characters, one uppercase letter, one lowercase letter,
                    one number, and one special character.
                    Example: Wer1f*gd
                3 - Passwords must have at least eight characters, two uppercase letters, two lowercase letters,
                    two numbers, and two special characters.
                    Example: We1*G!9d

            min_length          (int) -- length of the password

        Returns:
            password        --  (str)

        Raises:
            Exception:
                if invalid values are passed
        """
        if complexity_level < 1 or complexity_level > 3 or min_length < 1:
            raise Exception("Please pass supported values")

        if complexity_level > 1 and min_length < 8:
            raise Exception("password length cannot be less than 8 for complexity level greater than 1")

        numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

        lower = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
                 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q',
                 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

        upper = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
                 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q',
                 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']

        special = ['@', '#', '$', '%', '=', ':', '?', '.', '/', '|', '~', '>', '*', '(', ')', '!']

        combined = numbers + lower + upper + special

        temp_list = None
        if complexity_level == 1:
            temp_list = random.choices(combined, k=min_length)

        if complexity_level in (2, 3):
            rand_nums = random.choices(numbers, k=complexity_level - 1)
            rand_lower = random.choices(lower, k=complexity_level - 1)
            rand_upper = random.choices(upper, k=complexity_level - 1)
            rand_special = random.choices(special, k=complexity_level - 1)

            temp = rand_nums + rand_lower + rand_upper + rand_special

            # shuffle once to avoid same patterns
            random.shuffle(temp)

            # picking random char from lower + upper + numbers only to avoid generating level 3 password rather than 2.
            if complexity_level == 2:
                combined = numbers + lower + upper

            for i in range(min_length - len(temp)):
                temp = temp + random.choices(combined, k=1)
                random.shuffle(temp)
            temp_list = temp

        final_password = ""
        for char in temp_list:
            final_password = final_password + char

        return final_password

    def create_random_ownership_entity(self, username, password, list_of_entities=None):
        """
        Creates random ownership entities by user whose username and password are passed to this method.

        Args:
            username        -- (str)    username

            password        --  (str)   password

            list_of_entities    --  (list)  entitytype names
                values:
                "Alert", "Credential_Account", "Schedule_Policy", "Workflow",
                    "Custom_Reports"

                Default:
                picks and creates any random ownership entity like alert/schedule policy

        Returns:
            dict        --  names of entities created
                eg:- {
                    'Credentials' : 'name',
                    'alertName' : 'name',
                    'schedulePolicyName' : 'name'
                }

        Raises:
            Exception:
                if failed to create entity
        """
        entities = ["Alert", "Credential_Account", "Schedule_Policy"]
        # "Workflow", "Custom_Reports" -- not including in random pick up for now
        result_dict = {}
        commcell_obj = Commcell(webconsole_hostname=self.commcell_obj.webconsole_hostname,
                                commcell_username=username,
                                commcell_password=password, verify_ssl=self.config_json.API.VERIFY_SSL_CERTIFICATE)
        user_obj = commcell_obj.users.get(username)
        if list_of_entities:
            entities_to_be_created = list_of_entities
        else:
            entities_to_be_created = random.choices(entities)
        timestamp = datetime.strftime(datetime.now(), '%H%M%S')
        if "Credential_Account" in entities_to_be_created:
            creds_obj = CredentialHelper(commcell_obj).add(account_type=random.choices(["windows", "linux"])[0],
                                                           credential="credential_" + timestamp,
                                                           username=username, password=password,
                                                           description="created by user {0}".format(username))
            result_dict['Credentials'] = creds_obj.credential_name

        if "Alert" in entities_to_be_created:
            alert_dict = {
                'alert_type': 3,
                'notif_type': [1],
                'notifTypeListOperationType': 0,
                'alert_severity': 0,
                'nonGalaxyUserOperationType': 0,
                'criteria': 1,
                'associationOperationType': 0,
                'entities': {'client_groups': user_obj.user_company_name if user_obj.user_company_name else
                "Infrastructure"},
                'userListOperationType': 0,
                'users': [username],
                'alert_name': "alert_" + username + "_" + timestamp}

            commcell_obj.alerts.create_alert(alert_dict)
            result_dict['alertName'] = "alert_" + username + "_" + timestamp
        if "Client_Group" in entities_to_be_created:
            description = "Created for ownership transfer validation by user {0}".format(username)
            choice = random.choices([0, 1])[0]
            if choice:
                cg_obg = commcell_obj.client_groups.add(clientgroup_name="Client_Group_" + username + "_" + timestamp,
                                                        clientgroup_description=description)
                result_dict['clientGroupName'] = cg_obg.name
            else:
                from Server.SmartClientGroups.smartclient_helper import SmartClientHelper
                scg_name = "SCG_" + timestamp
                scg_helper = SmartClientHelper(commcell_obj, group_name=scg_name,
                                               description=description, client_scope='Clients of User',
                                               value=username)
                rule = scg_helper.create_smart_rule(filter_rule='Client',
                                                    filter_condition='equal to',
                                                    filter_value='Installed')
                scg_helper.create_smart_client([rule])
                result_dict['clientGroupName'] = scg_name
        if "Schedule_Policy" in entities_to_be_created:
            assocs = [{
                'clientGroupName': user_obj.user_company_name if user_obj.user_company_name else 'Infrastructure'
            }]
            date, rtime = ScheduleCreationHelper.add_minutes_to_datetime(minutes=1400)
            pattern = [{'name': 'Auto' + timestamp,
                        'pattern': {"freq_type":
                                        'daily',
                                    "active_start_date": str(date),
                                    "active_start_time": str(rtime)
                                    }}]
            types = [{"appGroupName": "Protected Files"}]
            schedule_policy = commcell_obj.schedule_policies.add(name='auto' + timestamp,
                                                                 policy_type='Data Protection', associations=assocs,
                                                                 schedules=pattern, agent_type=types)
            result_dict['schedulePolicyName'] = 'auto' + timestamp
        if "Workflow" in entities_to_be_created:
            pass
        if "Custom_Reports" in entities_to_be_created:
            pass
        return result_dict

    def get_all_users(self):
        """Method to get all users from DB

        Returns:
            List: a list of all the users present in DB
        """
        query = "select login from UMUsers where flags&0x001 > 0 and flags&0x004 = 0"
        self._csdb.execute(query)
        temp_user_list_db = self._csdb.fetch_all_rows()
        user_list_db = []
        [user_list_db.append(item[0]) for item in temp_user_list_db]
        return sorted(user_list_db, key=str.casefold)

    def cleanup_users(self, marker):
        """
            Delete users that has provided marker / string

            Args:
                marker      (str)   --  marker tagged to users for deletion
        """
        self.users_obj.refresh()
        for user in self.users_obj.all_users:
            if marker.lower() in user:
                try:
                    self.users_obj.delete(user, self.commcell_obj.commcell_username)
                    self.log.info("Deleted user - {0}".format(user))
                except Exception as exp:
                    self.log.error(
                        "Unable to delete user {0} due to {1}".format(
                            user,
                            str(exp)
                        )
                    )

    def validate_users_cache_data(self) -> bool:
        """
        Validates the data returned from Mongo cache for user collection.

        Returns:
            bool: True if validation passes, False otherwise
        """
        self.log.info("Starting validation for users cache...")
        cache = self.users_obj.get_users_cache(enum=False)
        out_of_sync = []

        for user, cache_data in cache.items():
            self.log.info(f'Validating cache for user: {user}')
            user_prop = self.users_obj.get(user)

            validations = {
                'userId': int(user_prop.user_id),
                'email': user_prop.email,
                'fullName': user_prop.full_name,
                'description': user_prop.description,
                'UPN': user_prop.upn,
                'enabled': user_prop.status,
                'locked': user_prop.get_account_lock_info.get('isAccountLocked'),
                'numberOfLaptops': user_prop.number_of_laptops,
            }

            for key, expected_value in validations.items():
                self.log.info(f'Comparing key: {key} for user: {user}')
                if cache_data.get(key) != expected_value:
                    out_of_sync.append((user, key))
                    self.log.error(f'Cache not in sync for prop "{key}". Cache value: {cache_data.get(key)}; '
                                   f'csdb value: {expected_value}')

            if cache_data.get('company') == 'Commcell':
                company_in_cache = cache_data.get('company').lower()
            else:
                company_in_cache = self.commcell_obj.organizations.get(cache_data.get('company')).domain_name.lower()

            self.log.info(f'Comparing key: company for user: {user}')
            if company_in_cache != user_prop.user_company_name.lower():
                out_of_sync.append((user, 'company'))
                self.log.error(f'Cache not in sync for prop "company". Cache value: {cache_data.get("company")} '
                               f'; csdb value: {user_prop.user_company_name}')

        if out_of_sync:
            raise Exception(f'Validation Failed. Cache out of sync: {out_of_sync}')
        else:
            self.log.info('Validation successful. All the users cache are in sync')
            return True

    def validate_sort_on_cached_data(self) -> bool:
        """
        Method to validate sort parameter on entity cache API call

        Returns:
            bool: True if validation passes, False otherwise
        """
        # setting locale for validating sort
        locale.setlocale(locale.LC_COLLATE, 'English_United States')

        columns = ['UserName', 'UserId', 'email', 'FullName', 'description', 'upn', 'enabled', 'locked',
                   'numberOfLaptops', 'company']
        unsorted_col = []
        for col in columns:
            optype = random.choice([1, -1])
            # get sorted cache from Mongo
            cache_res = self.users_obj.get_users_cache(fl=[col], sort=[col, optype])
            # sort the sorted list
            if col == 'clientName':
                cache_res = list(cache_res.keys())
                res = sorted(cache_res, key=lambda x: locale.strxfrm(str(x)), reverse=optype == -1)
            else:
                cache_res = [[key, value.get(col)] for key, value in cache_res.items() if col in value]
                if all(isinstance(item[1], int) for item in cache_res):
                    res = sorted(cache_res, key=lambda x: x[1], reverse=optype == -1)
                else:
                    res = sorted(cache_res, key=lambda x: locale.strxfrm(str(x[1])), reverse=optype == -1)

            # check is sorted list got modified
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

        cache = self.users_obj.get_users_cache()

        # generate random limit
        test_limit = random.randint(1, len(cache.keys()))
        limited_cache = self.users_obj.get_users_cache(limit=['0', str(test_limit)])
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
        # creating a test group

        user_name = f"caching_automation_{random.randint(0, 100000)} - users"
        email = f"caching_Automation_user - {random.randint(0, 100000)}@test.com"
        password = "######"
        user = self.create_user(user_name=user_name,
                                email=email,
                                full_name=user_name,
                                password=password)

        if user:
            # calling the API with search param
            response = self.users_obj.get_users_cache(search=user.name)
            # checking if test group is present in response
            if len(response.keys()) == 1 and [True for key in response.keys() if key == user.name]:
                self.log.info('Validation for search on cache passed')
                return True
            else:
                self.log.error(f'{user.name} is not returned in the response')
                raise Exception("Validation for search on cache failed!")
        else:
            raise Exception('Failed to create server group. Unable to proceed.')

    def validate_filter_on_cache(self, filters: list, expected_response: list) -> bool:
        """
        Method to validate fq param on entity cache API call

        Args:
            filters (list) -- contains the columnName, condition, and value
                e.g. filters = [['UserName','contains', 'test'],['email','contains', 'test']]
            expected_response (list) -- expected list of users to be returned in response

        Returns:
            bool: True if validation passes, False otherwise
        """
        if not filters or not expected_response:
            raise ValueError('Required parameters not received')

        try:
            res = self.users_obj.get_users_cache(fq=filters)
        except Exception as exp:
            self.log.error("Error fetching users cache")
            raise Exception(exp)

        missing_users = [user for user in expected_response if user not in res.keys()]

        if missing_users:
            raise Exception(f'Validation failed. Missing users: {missing_users}')
        self.log.info("validation for filter on cache passed!")
        return True

    @staticmethod
    def __get_token_from_email(mail_content: str) -> str:
        """
        Parses the reset password email and extracts the token from the reset link.

        Args:
            mail_content (str): The body of the email containing the reset link.

        Returns:
            str: The extracted token from the reset link.

        Raises:
            ValueError: If the reset password link is not found in the email.
            ValueError: If the token is not found in the URL.
            requests.RequestException: If the HTTP request fails.
        """
        # Find the reset password link in the email
        url_match = re.search(r'Set your password\s<\[\[(https?://\S+?)\]\]>', mail_content)
        if not url_match:
            raise ValueError('Reset password link not found in the email.')

        try:
            # Get the URL and follow any redirects
            response = requests.get(url_match.group(1), allow_redirects=True)
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        except requests.RequestException as e:
            raise Exception(f'Failed to retrieve the reset link. Error: {str(e)}')

        # Extract the token from the redirected URL
        token_match = re.search(r'tk=([a-fA-F0-9]+)', response.url)
        if not token_match:
            raise ValueError(f'Token not found in the URL. URL = {response.url}')

        return token_match.group(1)

    def reset_tenant_admin_password(self, user_name: str, mail_content: str, password: str):
        """
        Resets the tenant admin password using the token extracted from the reset email.

        Args:
            user_name (str): The username of the tenant admin whose password is to be reset.
            mail_content (str): The body of the email containing the reset password link.
            password (str): The new password to set for the tenant admin.
        """
        self.log.info("Extracting the token from the email")
        token = self.__get_token_from_email(mail_content)

        self.log.info("Refresh the Commcell object and reset the password using the token")
        self.commcell_obj.refresh()
        if not self.commcell_obj.users.get(user_name).reset_tenant_password(token=token, password=password):
            raise Exception("failed to reset password for the user")

        self.log.info(f"Successfully reset password for user {user_name}")
