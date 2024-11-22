# -*- coding: utf-8 -*-


# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for validating [Laptop Install] - [Plans] - Negative end user scenarios

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

import re

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Laptop.laptophelper import LaptopHelper
from Server.Security.userhelper import UserHelper
from Server.Security.securityhelper import OrganizationHelper
from Install.client_installation import Installation


class TestCase(CVTestCase):
    """Test case class for [Laptop Install] - [Plans] - Negative end user scenarios"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Laptop Install] - [Plans] - Negative end user scenarios"
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}
        self.laptop_helper = None
        self.user_helper = None

    def setup(self):
        """ Setup test case inputs from config template """
        common_inputs = ["DomainUserWithoutRights", "DomainUserPasswordWithoutRights"]
        self.tcinputs.update(LaptopHelper.set_inputs(self, 'Commcell', common_inputs))
        self.user_helper = UserHelper(self.commcell)

    def register_client(self, user, password, sim_error, log_success, create_user=True):
        """ Module to register client and test negative conditions

            Args:

            user: (str)                     - User name

            password: (str)                 - Password for the user

            sim_error: (str)                - Expected SimCallWrapper error

            log_success: (str)              - Log message on success

            create_user: (bool)             - (True/False) Create user ?

            Raises:
                Exception:
                 - If failed to satisfy failure conditions
        """

        if create_user:
            self.user_helper.delete_user(user_name=user, new_user='admin')
            self.user_helper.create_user(user_name=user, full_name=user, email='test@commvault.com', password=password)
            user_association = {'assoc1':{'userName': [user], 'role': ['View']}}
            self.user_helper.modify_security_associations(user_association, user)

        try:
            self.laptop_helper.installer.execute_register_me_command(
                user, password, self.tcinputs['Machine_client_name'], self.tcinputs['Machine_client_name']
            )
            raise Exception("Register client validation failed.")
        except Exception as excp:
            if not re.search(sim_error, str(excp)):
                self.log.error("Exception: [{0}]".format(excp))
                raise Exception("Register client validation failed.")
            self.log.info("{0} with sim error [{1}]".format(log_success, excp))
        finally:
            self.user_helper.delete_user(user_name=user, new_user='admin')

    def run(self):
        """ Main function for test case execution."""
        try:
            self.laptop_helper = LaptopHelper(self)

            #-------------------------------------------------------------------------------------
            self.laptop_helper.tc.log_step("""
                This test verifies simcallwrapper error codes and basic functionality for fresh install as:

                - Install and register with domain username [SimCallWrapper] which is a blacklisted user.
                - AD User without capability
                - Galaxy User without capability
                - User with special characters in name and password
                - Install and register with wrong username
                - Install and register with wrong password for the user with 'Secure Agent Install' authentication
                    set to on
                - Install with authcode with active user session for a blacklisted domain user on the client.
                    Activation should fail.
                - Install and register with wrong authcode

                Expectations:
                All installs should fail with valid reasons
            """, 200)

            #-------------------------------------------------------------------------------------
            self.laptop_helper.tc.log_step("""
                Set Default Laptop plan for the Commcell
            """)
            orghelper = OrganizationHelper(self.commcell)
            orghelper.commcell_default_plan = self.tcinputs['Default_Plan']

            #-------------------------------------------------------------------------------------
            self.laptop_helper.tc.log_step("""
                Install and register with domain username [SimCallWrapper] which is a blacklisted user.
            """)
            sim_error = "User is blacklisted"
            log_success = "Registration for user {0} failed expectedly".format(self.tcinputs['Activation_User'])

            self.refresh()
            self.install_kwargs['blacklist_user'] = self.tcinputs['Activation_User']
            try:
                self.laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)
                raise Exception("Register client validation failed.")
            except Exception as excp:
                if not re.search(sim_error, str(excp)):
                    raise Exception("Register client validation failed.")
                self.log.info("{0} with error [{1}]".format(log_success, excp))

            #-------------------------------------------------------------------------------------
            self.laptop_helper.tc.log_step("""
                AD User without capability
            """)
            user = self.tcinputs['DomainUserWithoutRights']
            passwd = self.tcinputs['DomainUserPasswordWithoutRights']
            sim_error = "Please provide a user account that has permissions to perform installs"
            log_success = "Registration for user {0} failed expectedly".format(user)

            self.register_client(user, passwd, sim_error, log_success, False)

            #-------------------------------------------------------------------------------------
            self.laptop_helper.tc.log_step("""
                Galaxy User without capability
            """)
            user = OptionsSelector.get_custom_str()
            sim_error = "Please provide a user account that has permissions to perform installs"
            log_success = "Registration for user {0} failed expectedly".format(user)

            self.register_client(user, user, sim_error, log_success)

            #-------------------------------------------------------------------------------------
            self.laptop_helper.tc.log_step("""
                User with special characters in name and password
            """)
            user = r"!@#$%^&*()_{}[]:|"
            sim_error = "Please provide a user account that has permissions to perform installs"
            log_success = "Registration for user {0} failed expectedly".format(user)

            self.register_client(user, user, sim_error, log_success)

            #-------------------------------------------------------------------------------------
            self.laptop_helper.tc.log_step("""
                Install and register with wrong username
            """)
            user = OptionsSelector.get_custom_str()
            sim_error = "Invalid login"
            log_success = "Registration for user {0} failed expectedly".format(user)
            self.user_helper.delete_user(user_name=user, new_user='admin')
            self.register_client(user, user, sim_error, log_success, False)

            #-------------------------------------------------------------------------------------
            self.laptop_helper.tc.log_step("""
                Install and register with wrong password for user with 'Secure Agent Install' authentication set to on.
            """)

            if int(self.laptop_helper.utility.get_gxglobalparam_val('Secure Agent Install')) != 1:
                self.log.error("Testcase requires Secure Agent Install to be set on the commcell")
                raise Exception("Secure Agent Install test case failed")

            user = r"LaVidaEsBuena"
            sim_error = "Invalid login"
            log_success = "Registration for user {0} failed expectedly".format(user)

            self.user_helper.delete_user(user_name=user, new_user='admin')
            self.user_helper.create_user(user_name=user, full_name=user, email='test@commvault.com', password=user)
            user_association = {'assoc1':{'userName': [user], 'role': ['Master']}}
            self.user_helper.modify_security_associations(user_association, user)

            self.register_client(user, "WrongPassword", sim_error, log_success, False)

            #-------------------------------------------------------------------------------------
            self.laptop_helper.cleanup(self.tcinputs)
            self.laptop_helper.tc.log_step("""
                Install with authcode with active user session for a blacklisted domain user on the client.
                    Activation should fail.
            """)
            self.refresh()
            install_authcode = Installation(self.tcinputs, self.commcell).commcell_install_authcode()
            self.install_kwargs = {
                'install_with_authcode': True,
                'authcode': install_authcode,
                'execute_simcallwrapper': False,
                'check_num_of_devices': False,
                'client_groups': [self.tcinputs['Default_Plan'] + ' clients', 'Laptop clients'],
                'blacklist_user': self.tcinputs['Activation_User']
            }

            try:
                self.laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)
                raise Exception("Activation expected to fail. TestCase Failed.")
            except Exception as excp:
                self.log.info("Activation failed as expected: [{0}]".format(excp))
                clientobject = self.commcell.clients.get(self.tcinputs['Machine_client_name'])
                self.laptop_helper.laptop_status(self.tcinputs['Machine_object'], clientobject, activated_mode=0)

            #-------------------------------------------------------------------------------------
            self.laptop_helper.cleanup(self.tcinputs)
            self.laptop_helper.tc.log_step("""
                Install and register with wrong authcode.
            """)
            self.refresh()
            install_authcode = Installation(self.tcinputs, self.commcell).commcell_install_authcode()
            self.install_kwargs = {
                'install_with_authcode': True,
                'authcode': "WRONGAUTHCODE",
                'execute_simcallwrapper': False,
                'check_num_of_devices': False,
                'client_groups': [self.tcinputs['Default_Plan'] + ' clients', 'Laptop clients'],
            }

            try:
                self.laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)
                raise Exception("Activation expected to fail. TestCase Failed.")
            except Exception as excp:
                if not re.search("No client exists with given name", str(excp)):
                    self.log.error("Actual failure: [{0}]".format(excp))
                    self.log.error("Expected failure: No client exists with given name")
                    raise Exception("TestCase Failed with exception: [{0}]".format(excp))
                self.log.info("Activation failed as expected: [{0}]".format(excp))

            self.laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            self.laptop_helper.tc.fail(excp)
            self.log.error("Testcase failed with exception [{0}]".format(excp))
            self.laptop_helper.cleanup(self.tcinputs)

    def refresh(self):
        """ Refresh the dicts
        Args:

            client_group (str): Client group
        """
        self.config_kwargs.clear()
        self.install_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': False
        }

        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True,
            'check_num_of_devices': False,
        }
