# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations from the test case on Users page.

To begin, create an instance of UserMain for users test case.

Functions:

add_new_user                    --                Calls method from base file to add new
                                                    user in Admin Console

delete_user                     --                Calls method to delete users created in
                                                    Admin Console

edit_local_user_details         --                Calls method to edit user details

validate_user                   --                Validates if the user details are retained
                                                    correctly against usr inputs

__set_default_values_if_none    --                Organizes user input for comparison against
                                                    displayed values

logout_of_admin_console         --                Method to logout of admin console
"""

import ast
import time

from AutomationUtils import logger
from Server.Security.userhelper import UserHelper

from Web.AdminConsole.AdminConsolePages.Users import Users
from Web.AdminConsole.AdminConsolePages.UserDetails import UserDetails
from AutomationUtils import database_helper
from Web.Common.exceptions import CVTestStepFailure
from random import sample

from Web.Common.page_object import TestStep


def _force_lower(obj):
    if isinstance(obj, str):
        return obj.lower()
    elif isinstance(obj, list):
        return [_force_lower(elem) for elem in obj]
    elif isinstance(obj, dict):
        for k in obj:
            obj[k] = _force_lower(obj[k])
        return obj


class UserMain:
    """
    Helper file to provide arguments and handle function call to base files
    """
    test_step = TestStep()

    def __init__(self, admin_console, commcell):
        """
        Initialize method for UserMain

        Args:
            admin_page   (object)    --  _Navigator class object
            commcell    (object)    --  CommCell object
        """
        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.__commcell = commcell
        self.__users = Users(self.__admin_console)
        self.__user_details = UserDetails(self.__admin_console)
        self.__users_api = self.__commcell.users
        self.__user_helper = UserHelper(commcell)
        self.__commcell = commcell
        self.csdb = database_helper.CommServDatabase(commcell)
        self.log = logger.get_log()

        random_value = str(time.time()).split(".")[0]
        self._user_name = f'User_{random_value}'
        self._new_user_name = None
        self._email = f'xyz{random_value}@commvault.com'
        self._user_groups = []
        self._full_name = f'User_{random_value}'
        self._system_password = False
        self._password = '######'
        self._admin_password = None
        self._external_provider = None
        self._invite_user = False
        self._user_enabled = True
        self._plan = None
        self._old_user_name = None
        self.__user_list = []
        self.__external_user_list = []
        self._owner_transfer = None
        self.company = None

    @property
    def user_name(self):
        """ Get user_name"""
        return self._user_name

    @user_name.setter
    def user_name(self, value):
        """ Set user_name"""
        self._user_name = value

    @property
    def new_user_name(self):
        """ Get new user name for editing """
        return self._new_user_name

    @new_user_name.setter
    def new_user_name(self, value):
        """ Set new_user_name for editing"""
        self._new_user_name = value

    @property
    def email(self):
        """ Get email"""
        return self._email

    @email.setter
    def email(self, value):
        """ Set email"""
        self._email = value

    @property
    def user_groups(self):
        """ Get user_groups"""
        return self._user_groups

    @user_groups.setter
    def user_groups(self, value):
        """ Set user_groups"""
        self._user_groups = value

    @property
    def full_name(self):
        """ Get full_name"""
        return self._full_name

    @full_name.setter
    def full_name(self, value):
        """ Set full_name"""
        self._full_name = value

    @property
    def system_password(self):
        """ Get system_password"""
        return self._system_password

    @system_password.setter
    def system_password(self, value):
        """ Set system_password"""
        self._system_password = value

    @property
    def password(self):
        """ Get password"""
        return self._password

    @password.setter
    def password(self, value):
        """ Set password"""
        self._password = value

    @property
    def admin_password(self):
        """ Get admin_password"""
        return self._admin_password

    @admin_password.setter
    def admin_password(self, value):
        """ Set admin_password"""
        self._admin_password = value

    @property
    def external_provider(self):
        """ Get external_provider"""
        return self._external_provider

    @external_provider.setter
    def external_provider(self, value):
        """ Set external_provider"""
        self._external_provider = value

    @property
    def invite_user(self):
        """ Get invite_user"""
        return self._invite_user

    @invite_user.setter
    def invite_user(self, value):
        """ Set invite_user"""
        self._invite_user = value

    @property
    def user_enabled(self):
        """ Get user_enabled"""
        return self._user_enabled

    @user_enabled.setter
    def user_enabled(self, value):
        """ Set user_enabled"""
        self._user_enabled = value

    @property
    def plan(self):
        """ Get plan"""
        return self._plan

    @plan.setter
    def plan(self, value):
        """ Set plan"""
        self._plan = value

    @test_step
    def add_new_local_user(self, negative_case=False):
        """calls add user method from Users page"""

        self.__navigator.navigate_to_users()
        try:
            self.__users.add_local_user(email=self.email,
                                        username=self.user_name,
                                        name=self.full_name,
                                        company=self.company,
                                        groups=self.user_groups,
                                        system_password=self.system_password,
                                        password=self.password,
                                        invite_user=self.invite_user)
        except Exception as exp:
            if 'smtpclient' in str(exp).lower() and (self.system_password or self.invite_user):
                self.log.error(f"Got SMTP error: {str(exp)}. Expected.")
            else:
                raise exp

        self.__user_list.append(self.user_name)
        if negative_case:
            self.log.info("Validating Negative user creation cases")

            self.__navigator.navigate_to_users()
            self.log.info(f"Trying to add another user with same name: {self.user_name} but different email")
            try:
                self.__users.add_local_user(email="differentmail@rediffmail.in",
                                            username=self.user_name,
                                            name=self.full_name,
                                            company=self.company,
                                            system_password=True)
                raise CVTestStepFailure("No error found, expected error message for same user existing")
            except Exception as exp:
                if 'already exist' in str(exp).lower() and self._user_name.lower() in str(exp).lower():
                    self.log.info("Verified username exists negative case")
                else:
                    self.log.error(f"Got different error: {str(exp).lower()}")
                    raise exp

            self.__navigator.navigate_to_users()
            self.log.info("Trying to add another user with same email but different name")
            try:
                self.__users.add_local_user(email=self.email,
                                            username="diff_username",
                                            name="diff_fullname",
                                            company=self.company,
                                            system_password=True)
                raise CVTestStepFailure("No error found, expected error message for same UPN existing")
            except Exception as exp:
                if 'already exist' in str(exp).lower() and self._email.lower() in str(exp).lower():
                    self.log.info("Verified UPN exists negative case")
                else:
                    self.log.error(f"Got different error: {str(exp).lower()}")
                    raise exp

            self.log.info("Negative user creation cases validated successfully!")

    @test_step
    def add_new_external_user(self, negative_case=False):
        """calls add user method from Users page"""

        self.__navigator.navigate_to_users()
        self.__users.add_external_user(external_provider=self.external_provider,
                                       username=self.user_name,
                                       email=self.email,
                                       groups=self.user_groups)
        self.__external_user_list.append(self.external_provider + "\\" + self.user_name)
        if negative_case:
            self.log.info("Validating Negative AD user creation case")
            self.__navigator.navigate_to_users()
            self.log.info(f"Trying to add AD user with same name: {self.user_name}")
            try:
                self.__users.add_external_user(external_provider=self.external_provider,
                                               username=self.user_name,
                                               email=self.email,
                                               groups=self.user_groups)
                raise CVTestStepFailure("No error found, expected error message for same AD user existing")
            except Exception as exp:
                if 'already exist' in str(exp).lower():
                    self.log.info("Verified AD user exists negative case")
                else:
                    self.log.error(f"Got different error: {str(exp).lower()}")
                    raise exp

    @test_step
    def delete_user(self):
        """Calls method to delete the specified user"""

        if self.__user_list:
            self.__navigator.navigate_to_users()
            for user_name in self.__user_list:
                self.__users.delete_user(user_name, self._owner_transfer)

    def delete_user_api(self):
        """Method to clean usersfrom API"""
        self.__users_api.refresh()
        for user in self.__user_list + self.__external_user_list:
            if self.__users_api.has_user(user):
                self.__users_api.delete(user, self.__commcell.commcell_username)
                self.log.info('User : %s is deleted successfully', user)

    @test_step
    def edit_local_user_details(self, negative_case=False):
        """
        Calls method to edit user details
        """
        self.__navigator.navigate_to_users()
        self.__users.open_user(self.user_name)
        self.__user_details.edit_user(self.email,
                                      self.full_name,
                                      self.new_user_name,
                                      self.user_groups,
                                      self.plan,
                                      self.user_enabled,
                                      self.password,
                                      self.admin_password,
                                      self.email)
        if self.user_name != self.new_user_name:
            self.__user_list.append(self.new_user_name)
            if self.user_name in self.__user_list:
                self.__user_list.remove(self.user_name)
            self._user_name = self.new_user_name

        if negative_case:
            self.log.info("Creating dummy user to update existing user name and email on")
            dummy_user = 'update_test_user'
            if not self.__user_helper.commcell_obj.users.has_user(dummy_user):
                self.__user_helper.create_user(dummy_user, 'dummyuser@dummyemail.com', password='Fakepass!123*?')
                self.log.info("Dummy user created")

            self.log.info("Validating Negative user updation cases")

            self.__navigator.navigate_to_users()
            self.__users.open_user(dummy_user)
            self.log.info(f"Trying to update with existing name: {self.user_name} but different email")
            try:
                self.__user_details.edit_user(email="differentmail@rediffmail.in",
                                              user_name=self.user_name,
                                              full_name=self.full_name)
                raise CVTestStepFailure("No error found, expected error message for same username existing")
            except Exception as exp:
                if 'already exist' in str(exp).lower() and self._user_name.lower() in str(exp).lower():
                    self.log.info("Verified username exists negative case")
                else:
                    self.log.error(f"Got different error: {str(exp).lower()}")
                    raise exp

            self.__admin_console.refresh_page()
            self.log.info("Trying to add another user with same email but different name")
            try:
                self.__user_details.edit_user(email=self.email,
                                              upn=self.email,
                                              user_name="diff_username",
                                              full_name="diff_fullname")
                raise CVTestStepFailure("No error found, expected error message for same UPN existing")
            except Exception as exp:
                if 'already exist' in str(exp).lower() and self._email.lower() in str(exp).lower():
                    self.log.info("Verified UPN exists negative case")
                else:
                    self.log.error(f"Got different error: {str(exp).lower()}")
                    raise exp
            self.__admin_console.refresh_page()
            self.log.info("Negative user updation cases validated successfully!")

    @test_step
    def validate_user(self):
        """ Method to validate if the user details are displayed correctly """

        self.__navigator.navigate_to_users()
        self.__users.open_user(self.user_name)
        displayed_val = self.__user_details.get_user_details()
        displayed_val['Enabled'] = self.__user_details.is_user_enabled()
        self.__admin_console.access_tab("User groups")
        displayed_val['Group'] = self.__user_details.get_usergroups()

        validate_key_dict = self.__set_default_values_if_none()

        validate_key_dict = _force_lower(validate_key_dict)
        displayed_val = _force_lower(displayed_val)

        self.log.info(f'Expected data : {validate_key_dict}')
        self.log.info(f'Displayed data : {displayed_val}')

        for key, value in validate_key_dict.items():
            if isinstance(value, list):
                if sorted(displayed_val[key]) != sorted(value):
                    raise CVTestStepFailure(
                        f'Value doesnot match for {key}, Displayed value : {displayed_val[key]}, Expected value : {value}')
            else:
                if displayed_val[key] != value:
                    raise CVTestStepFailure(
                        f'Value doesnot match for {key}, Displayed value : {displayed_val[key]}, Expected value : {value}')

    def __set_default_values_if_none(self):
        """this function sets default values to the parameters provided for user creation
            for comparison against displayed values"""
        if self.user_enabled:
            enabled = True
        else:
            enabled = False

        if self.full_name:
            full_name = self.full_name
        else:
            full_name = ''

        group_list = self.user_groups

        if not self.plan:
            self.plan = 'No plan'

        validate_key_dict = {
            'Full name': full_name,
            'Email': self.email,
            'Enabled': enabled,
            'Group': group_list
        }

        return validate_key_dict

    @test_step
    def validate_users_list(self):
        """Method to validate if all the users from DB are listed on users page"""
        self.__navigator.navigate_to_users()
        users_list_UI = self.__users.get_all_users()
        users_list_DB = self.__user_helper.get_all_users()

        if users_list_DB == users_list_UI:
            self.log.info("{0} matches with {1}".format(users_list_DB, users_list_UI))
        else:
            excep = f"User list from UI {users_list_UI} does not match with Users list from DB {users_list_DB}"
            raise CVTestStepFailure(excep)

    def __get_data_for_validation(self, query, company_name=None, user_type=None):
        """Method to fetch user data from UI and Database for validation"""
        self.csdb.execute(query)
        db_users = [users[0] for users in self.csdb.fetch_all_rows() if users[0] != '']
        ui_users = self.__users.list_users(company_name, user_type)

        if sorted(db_users) != sorted(ui_users):
            self.log.info(f'UI users : {sorted(ui_users)}')
            self.log.info(f'DB users : {sorted(db_users)}')
            raise CVTestStepFailure(f'Mismatch between UI and DB')

    @test_step
    def validate_company_filter(self):
        """Method to validate company filter"""
        self.log.info(f"Validating company filter on user listing page..")
        self.__navigator.navigate_to_users()

        self.__get_data_for_validation(query='SELECT LOGIN FROM UMUSERS WHERE FLAGS&0X001 > 0 AND FLAGS&0X004 = 0',
                                       company_name='All')
        self.__get_data_for_validation(
            query='SELECT LOGIN FROM UMUSERS WHERE FLAGS&0X001 > 0 AND FLAGS&0X004 = 0 AND ID NOT IN (SELECT ENTITYID FROM APP_COMPANYENTITIES WHERE ENTITYTYPE = 13)',
            company_name='CommCell')

        self.csdb.execute("SELECT ID, HOSTNAME FROM UMDSPROVIDERS WHERE SERVICETYPE=5 AND ENABLED=1 AND FLAGS=0 AND ID NOT IN \
                            (SELECT COMPONENTNAMEID FROM APP_COMPANYPROP WHERE ATTRNAME LIKE 'ALLOW TO MANAGE OTHER COMPANIES')")
        company_details = self.csdb.fetch_all_rows()
        if len(company_details) > 5: company_details = sample(company_details, 5)
        for id, company_name in company_details:
            self.__get_data_for_validation(
                query=f"SELECT LOGIN FROM UMUSERS WHERE FLAGS&0X001 > 0 AND FLAGS&0X004 = 0 AND ID IN (SELECT ENTITYID FROM APP_COMPANYENTITIES WHERE ENTITYTYPE = 13 AND COMPANYID = {id})",
                company_name=company_name)
        self.log.info('Company filter validation completed')

    @test_step
    def listing_page_search(self, user_name):
        """method to validate if a user is listed in listing page"""
        self.__navigator.navigate_to_users()
        if self.__users.is_user_exist(user_name):
            self.log.info('listing page search validation completed for the user')
        else:
            raise CVTestStepFailure('User not listed in listing page')
