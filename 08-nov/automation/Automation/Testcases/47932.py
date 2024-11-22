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
import time

from cvpysdk.exception import SDKException
from Server.Alerts.alert_helper import AlertHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine


# Class of Testcase is named as TestCase which inherits from CVTestCase
class TestCase(CVTestCase):
    """ Class for executing test case of Alert when no backup has taken place in N Days"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Creation of Alert when No Backup has taken place in N Days'
        self.options_selector = None
        self.last_backup_time = None
        self.subclient_id = None
        self.restarted_services = False

    def restart_services(self):
        # Restart Client Services
        # Restart Client Services
        self.log.info(f'Stopping Commserve Services')
        self.commcell.commserv_client.stop_service()
        self.log.info('sleeping 120 seconds after stopping services')
        time.sleep(120)

        self.log.info('Starting Commserve Services')
        machine = Machine(self.tcinputs['client machine name'], username=self.tcinputs['client machine administrator'],
                          password=self.tcinputs['client machine password'])
        machine.start_all_cv_services()
        self.log.info('sleeping 120 seconds after starting services')
        time.sleep(120)
        self.restarted_services = True

    def run(self):
        """Main function for test case execution"""
        try:
            # Initialize alerts object
            alert_helper = AlertHelper(commcell_object=self.commcell,
                                       category='Job Management',
                                       alert_type='Data Protection')

            # Creating Alert of given type
            # Feed alert data to create the right format
            alert_data = alert_helper.get_alert_details(name='Alert when No Backup has taken place in N1 Days',
                                                        notif_type=['Email', 'Console Alerts'],
                                                        entities={'clients': self.tcinputs['ClientName']},
                                                        users=["admin"],
                                                        criteria=65,
                                                        params_list=[
                                                            {
                                                                "unit": 3,
                                                                "type": 1,
                                                                "value": 4,
                                                                "paramIndex": 0
                                                            }
                                                        ],
                                                        mail_recipent="TestAutomation3@commvault.com"
                                                        )

            # Initialize Mailbox object
            alert_helper.initialize_mailbox()

            # Run backup job before alert creation
            self.cache = alert_helper.alert_situations.backup_generated_data(client=self.client,
                                                                             subclient=self.subclient,
                                                                             backup_type=self.tcinputs['BackupType'],
                                                                             size=10)

            self.log.info('Creating Alert %s for testcase %s', alert_data.get("alert_name"), self.id)
            alert_helper.create_alert()

            alert_helper.alert_situations.no_backup_in_n_days(n=12)
            self.restart_services()

            # Function to read email and confirmation alert notification
            alert_helper.check_if_alert_mail_received(short_interval=100, patterns=[self.commcell.commserv_name])

        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            # Cleanup phase
            if self.restarted_services:
                # Alerts cleanup
                alert_helper.cleanup()
                # Situation cleanup
                # Other Cleanup
                alert_helper.alert_situations.cleanup_no_backup_in_n_days()
                # Created directories cleanup
                if self.cache:
                    self.log.info("Will try to remove the test data directory")
                    self.cache['client_machine'].remove_directory(self.cache['test_data_path'])
                    self.log.info("Test Data directory removed successfully")

                    self.log.info('Will try to disconnect from the machine')
                    self.cache['client_machine'].disconnect()
                    self.log.info('Disconnected from the machine successfully')
            else:
                self.log.error("Can't perform Alert and created entities cleanup. Services are down")