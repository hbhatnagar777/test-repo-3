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

from Server.Alerts.alert_helper import AlertHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase


# Class of Testcase is named as TestCase which inherits from CVTestCase
class TestCase(CVTestCase):
    """ Class for executing test case for verifying multiple alert notification"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Verification of Multiple ALert Notifications'
        self.cache = None
        tcinputs = {
          "AgentName":None,
          "BackupsetName":None,
          "BackupType":None,
          "ClientName":None,
          "SubclientName":None
        }

    def run(self):
        """Main function for test case execution"""
        try:
            # Initialize alerts object
            self.log.info('Initializing Alerts')
            alert_helper = AlertHelper(commcell_object=self.commcell,
                                       category='Job Management', alert_type='Data Protection')

            # Creating Alert of given type
            # Feed alert data to create the right format
            alert_data = alert_helper.get_alert_xml(name='Test Multiple Alert Notification',
                                                    notif_type=['Email', 'Console Alerts'],
                                                    entities={'clients': self.tcinputs['ClientName']},
                                                    criteria=[1, 54],
                                                    mail_recipent=["TestAutomation3@commvault.com"],
                                                    send_individual_notif=True)
            # Initialize Mailbox object
            alert_helper.initialize_mailbox(set_unread_only=False)

            self.log.info('Creating Alert %s for testcase %s', alert_data.get("alert_name"), self.id)
            alert_helper.create_alert_from_xml()

            # Get criteria Names List
            criteria_names = alert_helper.create_criteria_mapping(criteria_id_list=alert_data['criteria'])
            # Trigger Alert Situation
            self.cache = alert_helper.alert_situations.backup_generated_data(client=self.client,
                                                                             subclient=self.subclient,
                                                                             backup_type=self.tcinputs['BackupType'],
                                                                             size=10)

            # For Every Criteria in the criteria_names list check if mail received
            received_mails = []
            for criteria_to_check in criteria_names:
                try:
                    alert_helper.check_if_alert_mail_received(short_interval=10,
                                                              patterns=[self.cache.get("job_id"),
                                                                        self.tcinputs["BackupsetName"],
                                                                        self.tcinputs["SubclientName"],
                                                                        criteria_to_check])
                    received_mails.append(criteria_to_check)
                except Exception as mail_receive_excp:
                    self.log.error('Didin\'t receive alert notification mail for criteria %s', criteria_to_check)
                    self.log.error('Encountered Exception : %s', {mail_receive_excp})

            msg_received = 'Received Alert Emails for the following Criterias : '
            for received_mail in received_mails:
                msg_received += received_mail + ', '
            self.log.info('='*len(msg_received))
            self.log.info(msg_received)
            self.log.info('='*len(msg_received))

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

            # Alerts Cleanup
            alert_helper.cleanup()
