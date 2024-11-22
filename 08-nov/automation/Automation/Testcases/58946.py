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

    misc_cleanup()  --  performs miscellaneous cleanup operations for the test case

    create_alert_situation() -- Creates the alert situation to trigger the alert

    run()           --  run function of this test case
"""

from Server.Alerts.alert_helper import AlertHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase

# Class of Testcase is named as TestCase which inherits from CVTestCase
class TestCase(CVTestCase):
    """ Class for executing negative test scenario for Disk Space low on Media Agent Alert"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Testing Negative Scenario for Triggering of Alert when Media Agent has Low Disk Space'

    def restart_services(self):
        # Restart Client Services
        self.log.info('Restarting Client Services')
        self.client.restart_services()
        self.log.info('Services Restarted Successfully')

    def remove_low_disk_space_setting(self):
        """Deletes the additional setting for min free space percentage"""
        self.commcell.delete_additional_setting(category='QMachineMaint',
                                                key_name='nMinFreeSpacePercentage')

    def run(self):
        """Main function for test case execution"""
        try:
            # Initialize alerts object
            self.log.info('Initializing Alerts')
            alert_helper = AlertHelper(commcell_object=self.commcell,
                                       category='Configuration',
                                       alert_type='MediaAgents')

            # Creating Alert of given type
            # Feed alert data to create the right format
            alert_data = alert_helper.get_alert_xml(name='TEST DISK SPACE LOW MA',
                                                    notif_type=['Save to Disk'],
                                                    entities={'media_agents': self.tcinputs['ClientName']},
                                                    criteria=18,
                                                    mail_recipent=["TestAutomation3@commvault.com"],
                                                    notification_criteria = {'repeat_notif':120,
                                                                             'notify_condition_clears': True}
                                                    )
            # Initialize Mailbox object
            #alert_helper.initialize_mailbox()

            self.log.info('Creating Alert %s for testcase %s', alert_data.get("alert_name"), self.id)
            alert_helper.create_alert_from_xml()

            # Creating the alert situation to trigger the alert
            alert_helper.alert_situations.low_disk_space_settings()
            self.restart_services()

            # Function to read email and confirmation alert notification
            alert_helper.check_if_alert_saved(short_interval=100, patterns=[self.tcinputs["ClientName"],
                                                                            alert_helper.alert_category,
                                                                            alert_helper.alert_type,
                                                                            ])
            # Remove the min disk space additional setting and then check if condition cleared mail is received
            self.remove_low_disk_space_setting()

            # If alert mail is still received raise Exception else continue
            try:
                # Function to read email and confirmation alert notification
                alert_helper.check_if_alert_saved(short_interval=100, patterns=[self.tcinputs["ClientName"],
                                                                                alert_helper.alert_category,
                                                                                alert_helper.alert_type,
                                                                                "Disk Space Low",
                                                                                "cleared"])
                self.log.info("Received Condition Cleared alert, negative scenario working as expected")
            except Exception as mail_receive_excp:
                self.log.info("Negative scenario not working as expected, alert mail not received,"
                              "Encountered exception {0}".format(mail_receive_excp))


        except Exception as excp:
            self.log.info('Failed with error %s ', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.PASSED
        finally:
            # Cleanup phase
            # Alerts Cleanup
            alert_helper.cleanup()
            alert_helper.alert_situations.cleanup_low_disk_space_settings()
