# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations on user groups page from test case.

To begin, create an instance of UserGroupMain for user group test case.

Functions:

add_new_user_group()             --     Calls method from base file to add new user in Admin Console

delete_user_group()              --     Calls method to delete users created in Admin Console

edit_user_group_details()        --     Calls method to edit user details

remove_users_from_usergroup()    --     Method to remove users from user group

validate_user_group()            --     Validates if the user details are retained correctly against
                                        user inputs

logout_of_admin_console()        --     Method to logout of admin console
"""

import ast
import time

from AutomationUtils import logger
from Web.AdminConsole.AdminConsolePages.UserGroups import UserGroups
from Web.AdminConsole.AdminConsolePages.UserGroupDetails import UserGroupDetails
from Web.AdminConsole.Components.table import Rtable
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep
from random import sample, randint
from Server.Security.usergrouphelper import UsergroupHelper


def _force_lower(obj):
    if isinstance(obj, str):
        return obj.lower()
    elif isinstance(obj, list):
        return [_force_lower(elem) for elem in obj]
    elif isinstance(obj, dict):
        for k in obj:
            obj[k] = _force_lower(obj[k])
        return obj


class UserGroupMain(object):
    """
    Helper file to provide arguments and handle function call to main file
    """
    test_step = TestStep()

    def __init__(self, admin_console, csdb=None, commcell=None):
        """
        Initialize method for UserGroupMain
        """
        self.local_group = None
        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.__user_groups = UserGroups(self.__admin_console)
        self.__user_group_details = UserGroupDetails(self.__admin_console)

        self.log = logger.get_log()
        self.csdb = csdb
        self.commcell = commcell
        if commcell: self.__user_group_sdk_helper = UsergroupHelper(commcell)
        random_time = str(time.time()).split(".")[0]
        self._group_name = f"UserGroup{random_time}"
        self._description = f'Automated Group Description'
        self._quota = True
        self._group_enabled = True
        self._laptop_admins = False
        self._quota_limit = 50
        self._plan = None
        self._user_list = []
        self._owner_transfer = None
        self._edit_flag = False
        self._old_group_name = None
        self._service_commcells = None

    @property
    def group_name(self):
        """ Get group_name"""
        return self._group_name

    @group_name.setter
    def group_name(self, value):
        """ Set group_name"""
        self._group_name = value

    @property
    def description(self):
        """ Get description"""
        return self._description

    @description.setter
    def description(self, value):
        """ Set description"""
        self._description = value

    @property
    def quota(self):
        """ Get quota"""
        return self._quota

    @quota.setter
    def quota(self, value):
        """ Set quota"""
        self._quota = value

    @property
    def group_enabled(self):
        """ Get group_enabled"""
        return self._group_enabled

    @group_enabled.setter
    def group_enabled(self, value):
        """ Set group_enabled"""
        self._group_enabled = value

    @property
    def laptop_admins(self):
        """ Get laptop_admins"""
        return self._laptop_admins

    @laptop_admins.setter
    def laptop_admins(self, value):
        """ Set laptop_admins"""
        self._laptop_admins = value

    @property
    def quota_limit(self):
        """ Get quota_limit"""
        return self._quota_limit

    @quota_limit.setter
    def quota_limit(self, value):
        """ Set quota_limit"""
        self._quota_limit = value

    @property
    def plan(self):
        """ Get plan"""
        return self._plan

    @plan.setter
    def plan(self, value):
        """ Set plan"""
        self._plan = value

    @property
    def user_list(self):
        """ Get user_list"""
        return self._user_list

    @user_list.setter
    def user_list(self, value):
        """ Set user_list"""
        self._user_list = value

    @property
    def service_commcells(self):
        """gets service commcell list"""
        return self._service_commcells

    @service_commcells.setter
    def service_commcells(self, value: list):
        """sets service commcell list"""
        self._service_commcells = value

    @test_step
    def add_new_user_group(self, negative_case=False):
        """calls add user method from Users page"""

        self.__navigator.navigate_to_user_groups()
        self.__user_groups.add_user_group(self.group_name,
                                          self.description,
                                          self.quota,
                                          self.quota_limit,
                                          self.service_commcells)
        self._old_group_name = self.group_name
        if negative_case:
            self.log.info("validating negative case")
            self.__navigator.navigate_to_user_groups()
            self.log.info("adding user group with existing name")
            try:
                self.__user_groups.add_user_group(
                    self.group_name,
                    self.description
                )
                raise CVTestStepFailure("No error found, expected error message for same user group existing")
            except Exception as exp:
                if 'already exist' in str(exp).lower() and self.group_name.lower() in str(exp).lower():
                    self.log.info("Verified user group exists negative case")
                else:
                    self.log.error(f"Got different error: {str(exp).lower()}")
                    raise exp

    def create_gcm(self, service_commcells: list = None) -> str:
        """test"""
        if service_commcells:
            self.service_commcells = service_commcells
        else:
            self.service_commcells = ['All']

        self.add_new_user_group()
        return self.group_name + " (Global)"

    @test_step
    def add_new_ad_group(self, negative_case=False):
        """calls add user method from Users page"""

        self.__navigator.navigate_to_user_groups()
        self.__user_groups.add_external_group(
            self.group_name,
            self.local_group,
            self.quota,
            self.quota_limit
        )

        if negative_case:
            self.log.info("validating negative case")
            self.__navigator.navigate_to_user_groups()
            self.log.info("adding AD group with existing name")
            try:
                self.__user_groups.add_external_group(self.group_name)
                raise CVTestStepFailure("No error found, expected error message for same AD group existing")
            except Exception as exp:
                if 'already exist' in str(exp).lower():
                    self.log.info("Verified user group exists negative case")
                else:
                    self.log.error(f"Got different error: {str(exp).lower()}")
                    raise exp

    @test_step
    def delete_user_group(self):
        """Calls method to delete designated user group"""

        self.__navigator.navigate_to_user_groups()
        self.__user_groups.delete_user_group(self.group_name,
                                             self._owner_transfer)
        if self.__user_groups.is_user_group_exists(self.group_name):
            raise CVTestStepFailure('[UI] User group found on UI even after deletion')

    @test_step
    def edit_user_group_details(self, negative_case=False):
        """
        Calls method to edit user group details
        """
        self.__navigator.navigate_to_user_groups()
        self.__user_groups.open_user_group(self._old_group_name)
        self.__user_group_details.edit_user_group(self.group_name,
                                                  self.description,
                                                  self.plan,
                                                  self.quota,
                                                  self.group_enabled,
                                                  self.laptop_admins,
                                                  self.quota_limit)
        if len(self._user_list) != 0:
            self.__user_group_details.add_users_to_group(self.user_list)
        self._edit_flag = True
        if negative_case:
            self.log.info("Creating dummy usergrp to update existing usergrp name on")
            dummy_usergrp = 'update_test_usergrp'
            if not self.__user_group_sdk_helper.commcell_obj.user_groups.has_user_group(user_group_name=dummy_usergrp):
                self.__user_group_sdk_helper.create_usergroup(dummy_usergrp)
                self.log.info("Dummy usergroup created")

            self.log.info("Validating Negative usergroup updation cases")
            self.__navigator.navigate_to_user_groups()
            self.__user_groups.open_user_group(dummy_usergrp)
            try:
                self.__user_group_details.edit_user_group(self.group_name)
                raise CVTestStepFailure("No error found, expected error message for same user group existing")
            except Exception as exp:
                if 'already exist' in str(exp).lower() and self.group_name.lower() in str(exp).lower():
                    self.log.info("Verified user group exists negative case")
                else:
                    self.log.error(f"Got different error: {str(exp).lower()}")
                    raise exp
            self.log.info("Successfully validated Negative usergroup updation cases")
            self.__admin_console.refresh_page()

    @test_step
    def remove_users_from_user_group(self):
        """
         Calls method to remove users from a user group
        """
        self.__navigator.navigate_to_user_groups()
        self.__user_groups.open_user_group(self._group_name)
        self.__user_group_details.remove_users_from_group(self.user_list)
        self.user_list = []

    @test_step
    def validate_user_group(self):
        """validates if the user group details are displayed correctly"""

        self.__navigator.navigate_to_user_groups()
        self.__user_groups.open_user_group(self.group_name)
        displayed_val = self.__user_group_details.get_user_group_details()
        user_list = []
        user_details = self.__user_group_details.list_users()
        for user in user_details:
            user_list.append(user)
        displayed_val.update({'Users': user_list})

        if not self._edit_flag:
            validate_key_dict = self.__set_default_values_if_none(get_validate_key_dict='Pre-edit')
        else:
            validate_key_dict = self.__set_default_values_if_none(get_validate_key_dict='Post-edit')

        validate_key_dict = _force_lower(validate_key_dict)
        displayed_val = _force_lower(displayed_val)

        for key_dict, val_dict in validate_key_dict.items():
            if isinstance(val_dict, list):
                self.log.info('Entity given_val "{0}"'.format(val_dict))
                if set(displayed_val[key_dict]) == set(validate_key_dict[key_dict]):
                    self.log.info(
                        "{0} displayed for {1} matches with {2} given".format(
                            displayed_val[key_dict], key_dict, validate_key_dict[key_dict]))
                else:
                    exp = "{0} displayed for {1} does not match with {2} given ".format(
                        displayed_val[key_dict], key_dict, validate_key_dict[key_dict])
                    raise CVTestStepFailure(exp)
            elif isinstance(val_dict, str):
                self.log.info('Entity given_val "{0}"'.format(val_dict))
                if displayed_val[key_dict] == validate_key_dict[key_dict]:
                    self.log.info(
                        "{0} displayed for {1} matches with {2} given".format(
                            displayed_val[key_dict], key_dict, validate_key_dict[key_dict]))
                else:
                    exp = "{0} displayed for {1} does not match with {2} given " \
                        .format(displayed_val[key_dict], key_dict, validate_key_dict[key_dict])
                    raise CVTestStepFailure(exp)
            else:
                self.log.info('Entity given_val :{0}'.format(val_dict))
                for item in val_dict.items():
                    d_val = displayed_val[key_dict][item]
                    key_val = validate_key_dict[key_dict][item]
                    if d_val == key_val:
                        self.log.info("{0} values match".format(item))
                    else:
                        exp = "{0} displayed for {1} does not match with {2} given " \
                            .format(d_val, item, key_val)
                        raise CVTestStepFailure(exp)

    def __set_default_values_if_none(self, get_validate_key_dict):
        """ This function sets default values to the parameters provided for user group creation
            for comparison against displayed values"""

        if self.group_enabled:
            enabled = 'Yes'
        else:
            enabled = 'No'

        if get_validate_key_dict == 'Pre-edit':
            key_dict = {
                "Description": self._description,
                "Enabled": enabled,
                "Quota limit": str(self.quota_limit) + " GB",
                "Associated external groups": "No group is found",
                "Users": []
                # "Restricted Consoles": "No consoles restricted"
            }
        elif get_validate_key_dict == 'Post-edit':
            key_dict = {
                "Description": self._description,
                "Enabled": enabled,
                "Associated external groups": "No group is found",
                "Users": self.user_list
                # "Restricted Consoles": "No consoles restricted"
            }

        return key_dict

    @test_step
    def has_user(self, username):
        """Returns True if usergroup has user otherwise false

        Args:
            username (str): Username for the user
        """
        self.__navigator.navigate_to_user_groups()
        self.__user_groups.filter_all_user_groups()
        self.__user_groups.open_user_group(self.group_name)
        users_table = Rtable(self.__admin_console, 'Users')
        users_table.reload_data()
        return users_table.is_entity_present_in_column('User name', username)

    @test_step
    def __get_data_for_validation(self, company_name=None, local_groups=False, external_groups=False):
        """Method to fetch data for the user group data from UI and DB for validation purpose"""
        self.__user_groups.reset_filters() # clear filters before fetching data
        db_data = set(
            self.__user_group_sdk_helper.get_all_usergroup(company_name=None if company_name == 'All' else company_name,
                                                           local_groups=local_groups, external_groups=external_groups))
        if local_groups:
            usergroup_type = 'Local group'
        elif external_groups:
            usergroup_type = 'External group'
        else:
            usergroup_type = 'All'

        if company_name and company_name.lower() == 'commcell': company_name = 'CommCell'
        ui_data = set(self.__user_groups.list_usergroups(company_name, usergroup_type))

        if db_data != ui_data:
            self.log.info(f'DB User Groups : {sorted(db_data)}')
            self.log.info(f'UI User Groups : {sorted(ui_data)}')
            data_missing_from_ui = db_data - ui_data
            extra_entities_on_ui = ui_data - db_data
            raise CVTestStepFailure(
                f'Mismatch found between UI and DB\nData missing from UI : {data_missing_from_ui}\
                                           Extra entities on UI : {extra_entities_on_ui}')
        self.log.info('Validation completed')

    @test_step
    def validate_listing_company_filter(self):
        """Mathod to validate the company filter on user group listing page"""
        self.log.info(f"Validating Company Filter on user group listing page..")
        self.__navigator.navigate_to_user_groups()
        self.__get_data_for_validation(company_name='Commcell')
        self.csdb.execute("SELECT ID, HOSTNAME FROM UMDSPROVIDERS WHERE SERVICETYPE=5 AND ENABLED=1 AND FLAGS=0 AND ID NOT IN \
                            (SELECT COMPONENTNAMEID FROM APP_COMPANYPROP WHERE ATTRNAME LIKE 'ALLOW TO MANAGE OTHER COMPANIES')")
        company_details = self.csdb.fetch_all_rows()
        if len(company_details) > 5: company_details = sample(company_details, 5)
        for id, company_name in company_details:
            self.__get_data_for_validation(company_name=company_name)
        self.__get_data_for_validation(company_name='All')
        self.log.info("Company Filter Validation Success")

    @test_step
    def validate_listing_tab_filter(self):
        """Method to validate the TAB filter"""
        self.log.info("Validating TABs Filter...")
        self.__navigator.navigate_to_user_groups()
        self.__get_data_for_validation(local_groups=True)
        self.__get_data_for_validation(external_groups=True)
        self.log.info("TAB filters validation completed")

    @test_step
    def validate_listing_user_group_deletion(self, group_name=None):
        """Method to validate the user group deletion"""
        if not group_name:
            group_name = f"DEL Automated - {str(randint(0, 100000))}"
            self.commcell.user_groups.add(group_name)
        self.log.info("Validating User Group Deletion...")
        self.__navigator.navigate_to_user_groups()
        self.__user_groups.delete_user_group(group_name)
        self.__admin_console.driver.implicitly_wait(10)

        if self.__user_groups.is_user_group_exists(group_name):
            raise CVTestStepFailure('[UI] User group found on UI even after deletion')

        self.csdb.execute(f"SELECT NAME FROM UMGROUPS WHERE NAME = '{group_name}'")
        if [grps[0] for grps in self.csdb.fetch_all_rows() if grps[0] != '']:
            raise CVTestStepFailure('[DB] User group found in database even after deletion')
        self.__admin_console.driver.implicitly_wait(0)
        self.log.info('User group deletion validated successfully')

    @test_step
    def validate_listing_user_group_creation(self, group_name=None):
        """Method to validate the user group creation"""
        if not group_name:
            group_name = f"DEL Automated - {str(randint(0, 100000))}"
        self.log.info("Validating User Group Creation...")
        self.__navigator.navigate_to_user_groups()
        self.__user_groups.add_user_group(group_name)
        self.__admin_console.wait_for_completion()
        self.log.info("User group created successfully...")

        self.__navigator.navigate_to_user_groups()

        self.csdb.execute(f"SELECT NAME FROM UMGROUPS WHERE NAME = '{group_name}'")
        if not [grps[0] for grps in self.csdb.fetch_all_rows() if grps[0] != '']:
            raise CVTestStepFailure('[DB] New user group not found in database')

        if not self.__user_groups.is_user_group_exists(group_name):
            raise CVTestStepFailure('[UI] New user group not found on UI')
        self.commcell.user_groups.refresh()
        self.commcell.user_groups.delete(group_name, self.commcell.commcell_username)
        self.log.info('User group creation validated successfully')

    @test_step
    def listing_page_search(self, group_name):
        """Method to validate a user group in listing page"""
        self.__navigator.navigate_to_user_groups()
        if self.__user_groups.is_user_group_exists(group_name):
            self.log.info('listing page search validation completed for the user group')
        else:
            raise CVTestStepFailure('User group not listed in listing page')
