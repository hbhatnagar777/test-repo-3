# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

import random
import string
from cvpysdk.commcell import Commcell
from cvpysdk.alert import Alert, Alerts
from Server.Alerts.alert_helper import AlertHelper
from Server.Security.userhelper import UserHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase


# Class of Testcase is named as TestCase which inherits from CVTestCase
class TestCase(CVTestCase):
    """ Class for executing basic test case of File System Backup using user defined parameters"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Alert Role Based Security Verification'
        self.user_name1 = "user1"
        self.user_name2 = "user2"
        self.user_name3 = "user3"
        self.user_name4 = "user4"
        self.user_email = "TestAutomation3@commvault.com"
        self.user_password = "#####"
        self.user_helper = None

    def generate_random_email(self):
        """Generates a random email address and returns it for User creation"""
        random_char =  ''.join(random.choice(string.ascii_letters) for x in range(8))
        return random_char+"@commvault.com"

    def setup_entities(self):
        """Sets up the Entities required for this testcase"""
        self.log.info("=============================")
        self.log.info("Settting up Testcase Entities")
        self.user_helper = UserHelper(self.commcell)
        # Defining Entity and Role associations for users
        # user1
        user1_entities_list = {"assoc1": {"commCellName": [self.commcell.commserv_name], "role": ["Client Admins"]},
                               "assoc2": {"commCellName": [self.commcell.commserv_name], "role": ["Alert Admin"]}}
        # user2
        user2_entities_list = {"assoc1": {"commCellName": [self.commcell.commserv_name], "role": ["Client Admins"]},
                               "assoc2": {"commCellName": [self.commcell.commserv_name],
                                          "role": ["All Users Laptops"]}}
        # user3
        user3_entities_list = {"assoc1": {"commCellName": [self.commcell.commserv_name], "role": ["Client Admins"]},
                               "assoc2": {"commCellName": [self.commcell.commserv_name], "role": ["Delete Alert"]}}
        # user4
        user4_entities_list = {"assoc1": {"commCellName": [self.commcell.commserv_name], "role": ["Client Admins"]},
                               "assoc2": {"commCellName": [self.commcell.commserv_name], "role": ["Edit Alert"]}}
        # Creating users : user1,user2,user3,user4
        user1_email = self.generate_random_email()
        user2_email = self.generate_random_email()
        user3_email = self.generate_random_email()
        user4_email = self.generate_random_email()

        self.user_helper.create_user(user_name=self.user_name1,
                                     email=user1_email,
                                     password=self.user_password,
                                     security_dict=user1_entities_list)
        self.user_helper.create_user(user_name=self.user_name2,
                                     email=user2_email,
                                     password=self.user_password,
                                     security_dict=user2_entities_list)
        self.user_helper.create_user(user_name=self.user_name3,
                                     email=user3_email,
                                     password=self.user_password,
                                     security_dict=user3_entities_list)
        self.user_helper.create_user(user_name=self.user_name4,
                                     email=user4_email,
                                     password=self.user_password,
                                     security_dict=user4_entities_list)
        self.log.info("Entities Setup Completed")
        self.log.info("=============================")

    def cleanup_entities(self):
        """Cleans up the entities created for the testcase"""
        self.log.info("Cleaning Up Testcase Entities")
        self.user_helper.delete_user(user_name=self.user_name1,
                                     new_user="admin")
        self.user_helper.delete_user(user_name=self.user_name2,
                                     new_user="admin")
        self.user_helper.delete_user(user_name=self.user_name3,
                                     new_user="admin")
        self.user_helper.delete_user(user_name=self.user_name4,
                                     new_user="admin")
        self.log.info("Testcase Entities Cleaned")

    def login_user(self, hostname, username, password):
        """Used to return Commcell object for another user with credentials provided in tcinputs"""
        commcell = Commcell(hostname, username, password)
        return commcell

    def modify_alert_properties(self, commcell_object, alert_name):
        """
        modifies the properties of an alert
        Exception:
            if modification of the alert failed
        """
        current_alert = Alert(commcell_object=commcell_object,
                              alert_name=alert_name)
        self.log.info(f'Trying to modify alert properties as {commcell_object.commcell_username}')
        try:
            current_alert._modify_alert_properties()
            self.log.info('Successfully able to modify alert properties')
        except Exception as excp:
            self.log.error(str(excp))
            self.log.error(f'Failed to modify Alert Properties as {commcell_object.commcell_username}')

    def run(self):
        """Main function for test case execution"""
        try:
            # Setup testcase entities
            self.setup_entities()
            # Initialize alerts object
            self.log.info('Initializing Alerts')

            # First Try creating alert as User1 who has Alert Creation Rights
            self.log.info('Logging in as User1')
            user1_commcell = self.login_user(self.commcell.webconsole_hostname,
                                             self.user_name1,
                                             self.user_password)
            self.log.info('Logged in as User1')

            alert_helper1 = AlertHelper(commcell_object=user1_commcell,
                                        category='Job Management',
                                        alert_type='Data Protection')

            # Creating Alert of given type
            # Feed alert data to create the right format
            alert_data1 = alert_helper1.get_alert_details(name='TestAlert1',
                                                          notif_type=['Email'],
                                                          entities={'clients': self.tcinputs['ClientName']},
                                                          users=["admin"],
                                                          criteria=1
                                                          )

            self.log.info('Creating Alert %s for testcase %s as User1', alert_data1.get("alert_name"), self.id)
            try:
                alert_helper1.create_alert()
            except Exception as creation_excp:
                self.log.error(f'Exception occured during alert creation {creation_excp}')

            # Try creating alert as User2 who does not have Alert Creation Rights
            self.log.info('Logging in as User2')
            user2_commcell = self.login_user(self.commcell.webconsole_hostname,
                                             self.user_name2,
                                             self.user_password)
            self.log.info('Logged in as User2')

            alert_helper2 = AlertHelper(commcell_object=user2_commcell,
                                        category='Job Management',
                                        alert_type='Data Protection')

            alert_data2 = alert_helper2.get_alert_details(name='TestAlert2',
                                                          notif_type=['Email', 'Console Alerts'],
                                                          entities={'clients': self.tcinputs['ClientName']},
                                                          users=["admin"],
                                                          criteria=1,
                                                          mail_recipent="TestAutomation3@commvault.com"
                                                          )

            self.log.info('Creating Alert %s for testcase %s as User2', alert_data2.get("alert_name"), self.id)
            try:
                alert_helper2.create_alert()
                alert_helper2.cleanup()
            except Exception as creation_excp:
                self.log.error(f'Exception occured during alert creation {creation_excp}')

            # Alert edit rights verification
            self.modify_alert_properties(commcell_object=user2_commcell,
                                         alert_name=alert_data1.get("alert_name"))

            # Login with User4 and try alert modification
            self.log.info('Logging in as User4')
            user4_commcell = self.login_user(self.commcell.webconsole_hostname,
                                             self.user_name4,
                                             self.user_password)
            self.log.info('Logged in as User4')
            self.modify_alert_properties(commcell_object=user4_commcell,
                                         alert_name=alert_data1.get("alert_name"))

            # Alert deletion rights verification
            alert_helper_user2 = AlertHelper(commcell_object = user2_commcell)
            alert_helper_user2.delete_alert(alert_name=alert_data1.get("alert_name"))

            # Login with User4 and try alert deletion
            self.log.info('Logging in as User3')
            deletion_attempt = False
            user3_commcell = self.login_user(self.commcell.webconsole_hostname,
                                             self.user_name3,
                                             self.user_password)
            self.log.info('Logged in as User3')
            alert_helper_user3 = AlertHelper(commcell_object = user3_commcell)
            deletion_attempt = alert_helper_user3.delete_alert(alert_name=alert_data1.get("alert_name"))

        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            self.cleanup_entities()
            if deletion_attempt is False:
                alert_helper1.cleanup()
