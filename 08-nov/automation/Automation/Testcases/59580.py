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
    """ Class for executing basic test case of SCOM Alert notification verification"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Verification of SCOM Alert when Backup Job Succeeds'
        self.cache = None

    def run(self):
        """Main function for test case execution"""
        try:
            # Initialize alerts object
            self.log.info('Initializing Alerts')
            alert_helper = AlertHelper(commcell_object=self.commcell,
                                       category='Job Management', alert_type='Data Protection')

            # Creating Alert of given type
            # Feed alert data to create the right format
            alert_data = alert_helper.get_alert_details(name='Test SCOM Backup Job',
                                                        notif_type=['Scom'],
                                                        entities={'clients': self.tcinputs['ClientName']},
                                                        users=["admin"],
                                                        criteria=1,
                                                        )

            self.log.info('Creating Alert %s for testcase %s', alert_data.get("alert_name"), self.id)
            alert_helper.create_alert()

            # Trigger Alert Situation
            self.cache = alert_helper.alert_situations.backup_generated_data(client=self.client,
                                                                             subclient=self.subclient,
                                                                             backup_type=self.tcinputs['BackupType'],
                                                                             size=1)

            # Function to read email and confirmation alert notification
            alert_helper.check_if_scom_alert_received(wait_interval=30,
                                                      patterns=[self.cache.get("job_id"),
                                                                self.tcinputs["BackupsetName"],
                                                                self.tcinputs["SubclientName"]])

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