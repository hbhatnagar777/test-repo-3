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

from cvpysdk.exception import SDKException
from Server.Security.usergrouphelper import UsergroupHelper
from Server.Security.userhelper import UserHelper
from Server.Alerts.alert_helper import AlertHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase


# Class of Testcase is named as TestCase which inherits from CVTestCase
class TestCase(CVTestCase):
    """ Class for verifying negative scenarios failure for Alert notification not received"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Negative Scenarios for Token Filters for Alerts'
        self.user1_name = 'TestUser1'
        self.user2_name = 'TestUser2'
        self.user1_email = 'TestAutomation3@commvault.com' # Should be the same as email provided in config.json
        self.user2_email = 'TestingUser@commvault.com'
        self.usergroup_name = 'TESTGROUP'
        self.cache = None
        self.cache1 = None
        self.user_helper = None
        self.usergroup_helper = None

    def setup_entities(self):
        """Sets up the Entities required for this testcase"""
        self.log.info("Setting up Testcase Entities")
        # Create User needed for the testcase
        self.user_helper = UserHelper(self.commcell)
        self.usergroup_helper = UsergroupHelper(self.commcell)
        self.user_helper.create_user(user_name=self.user1_name,
                                     email=self.user1_email,
                                     )
        self.user_helper.create_user(user_name=self.user2_name,
                                     email=self.user2_email,
                                     )
        self.usergroup_helper.create_usergroup(group_name=self.usergroup_name,
                                               users=[self.user1_name, self.user2_name])
        self.log.info("Entities Setup complete")

    def cleanup_entities(self):
        """Cleans up the entities created for the testcase"""
        self.log.info("Cleaning up testcase entities")
        self.user_helper.delete_user(user_name=self.user1_name,
                                     new_user="admin")
        self.user_helper.delete_user(user_name=self.user2_name,
                                     new_user="admin")
        self.usergroup_helper.delete_usergroup(group_name=self.usergroup_name,
                                               new_user="admin")

    def run(self):
        """Main function for test case execution"""
        try:
            # Setup testcase entities
            self.setup_entities()
            # Initialize alerts object
            self.log.info('Initializing Alerts')
            alert_helper = AlertHelper(commcell_object=self.commcell,
                                       category='Job Management', alert_type='Data Protection')

            # Creating Alert of given type
            # Feed alert data to create the right format
            alert_data = alert_helper.get_alert_xml(name='Test Alert User Group Exclusion',
                                                    notif_type=['Email'],
                                                    entities={'clients': self.tcinputs['ClientName']},
                                                    criteria=1,
                                                    to_usergroups_mail = [self.usergroup_name]
                                                    )
            # Initialize Mailbox object
            alert_helper.initialize_mailbox()

            self.log.info('Creating Alert %s for testcase %s', alert_data.get("alert_name"), self.id)
            alert_helper.create_alert_from_xml()

            # Trigger alert and check if notification received
            # Trigger Alert Situation
            self.cache = alert_helper.alert_situations.backup_generated_data(client=self.client,
                                                                             subclient=self.subclient,
                                                                             backup_type=self.tcinputs['BackupType'],
                                                                             size=1)

            # Function to read email and confirmation alert notification
            alert_helper.check_if_alert_mail_received(short_interval=30,
                                                      patterns=[self.cache.get("job_id"),
                                                                self.tcinputs["BackupsetName"],
                                                                self.tcinputs["SubclientName"]])

            # Remove user1 from usergroup
            self.log.info(f'Removing user "{self.user1_name}" from group {self.usergroup_name}')
            usergroup_object = self.commcell.user_groups.get(self.usergroup_name)
            usergroup_object.update_usergroup_members(request_type='DELETE',
                                                      users_list=[self.user1_name])

            self.log.info(f'Removed "{self.user1_name}" from group {self.usergroup_name}')

            # Now trigger alert situation and see if user is receiving the alert
            self.cache1 = alert_helper.alert_situations.backup_job(client=self.client,
                                                                   subclient=self.subclient,
                                                                   backup_type=self.tcinputs['BackupType']
                                                                   )

            try:
                alert_helper.check_if_alert_mail_received(short_interval=30,
                                                          patterns=[self.cache1.get("job_id"),
                                                                    self.tcinputs["BackupsetName"],
                                                                    self.tcinputs["SubclientName"]])
                # If still receiving notification, raise exception
                raise SDKException('Alert', '102', 'Alert notification should not have been received')
            except Exception as excp:
                self.log.info(f'Alert negative scenario, User exclusion from Usergroup working as expected\nEncountered exception : {excp}')


        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            # Cleanup phase
            if self.cache:
                self.log.info("Will try to remove the test data directory")
                self.cache['client_machine'].remove_directory(self.cache['test_data_path'])
                self.log.info("Test Data directory removed successfully")

                self.log.info('Will try to disconnect from the machine')
                self.cache['client_machine'].disconnect()
                self.log.info('Disconnected from the machine successfully')
            # Cleanup entities
            self.cleanup_entities()
            # Alerts Cleanup
            alert_helper.cleanup()
