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

import time
from Server.Alerts.alert_helper import AlertHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase


# Class of Testcase is named as TestCase which inherits from CVTestCase
class TestCase(CVTestCase):
    """ Class for executing basic test case of File System Backup using user defined parameters"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Triggering Alert when Client has Low Disk Space'
        self.alert_helper = None
        self.media_check_interval = 400

    def restart_services(self):
        """Restarts the services"""
        # Restart Commserve Services
        self.log.info('Restarting Commcell Services')
        cs_client = self.commcell.commserv_client
        cs_client.restart_services()
        self.log.info('Services Restarted Successfully')

    def run(self):
        """Main function for test case execution"""
        try:
            # Initialize alerts object
            self.log.info('Initializing Alerts')
            self.alert_helper = AlertHelper(commcell_object=self.commcell,
                                            category='Configuration',
                                            alert_type='Clients')

            # Creating Alert of given type
            # Feed alert data to create the right format
            alert_data = self.alert_helper.get_alert_xml(name='TEST DISK SPACE LOW CLIENT',
                                                         notif_type=['Email', 'Console Alerts'],
                                                         entities={'clients': self.tcinputs['ClientName']},
                                                         criteria=[18, 77, 79],
                                                         mail_recipent=["TestAutomation3@commvault.com"],
                                                         notification_criteria={'repeat_notif':60}
                                                         )
            # Initialize Mailbox object
            self.alert_helper.initialize_mailbox()

            self.log.info('Creating Alert %s for testcase %s', alert_data.get("alert_name"), self.id)
            self.alert_helper.create_alert_from_xml()

            # Trigger Alert Situation
            self.alert_helper.alert_situations.low_disk_space_settings()

            # Restart Services
            self.restart_services()

            # Add 15 minutes wait for media maintenance interval check
            self.log.info(f"Waiting for {self.media_check_interval} seconds for media management maintenance interval check")
            time.sleep(self.media_check_interval)

            # Function to read email and confirmation alert notification
            self.alert_helper.check_if_alert_mail_received(short_interval=100, patterns=[self.tcinputs["ClientName"],
                                                                                         self.alert_helper.alert_category,
                                                                                         self.alert_helper.alert_type,
                                                                                         ])

        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            # Cleanup phase
            # Alerts Cleanup
            if self.alert_helper is not None:
                self.alert_helper.cleanup()
                self.alert_helper.alert_situations.cleanup_low_disk_space_settings()
