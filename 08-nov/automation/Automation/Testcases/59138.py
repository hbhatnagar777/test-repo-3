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

import string
from Server.Alerts.alert_helper import AlertHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase


# Class of Testcase is named as TestCase which inherits from CVTestCase
class TestCase(CVTestCase):
    """ Class for verifying negative scenarios failure for Alerts Token rule filter criterias"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Negative Scenarios for Token Filters for Alerts'
        self.cache = None
        self.cache2 = None
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
            alert_data = alert_helper.get_alert_xml(name='Test Alert Token Rule',
                                                    notif_type=['Email'],
                                                    entities={'clients': self.tcinputs['ClientName']},
                                                    criteria=1,
                                                    mail_recipent=["TestAutomation3@commvault.com"],
                                                    token_rule=[{'rule': 'LEVEL',
                                                                 'value': 'FULL',
                                                                 'operator': 0},
                                                                {'rule': 'LEVEL',
                                                                 'value': 'INCREMENTAL',
                                                                 'operator': 1}
                                                                ])
            # Initialize Mailbox object
            alert_helper.initialize_mailbox()

            self.log.info('Creating Alert %s for testcase %s', alert_data.get("alert_name"), self.id)
            alert_helper.create_alert_from_xml()

            # Trigger Alert Situation
            # First create alert situation for LEVEL = FULL -> Alert should get triggered
            level_full = "Full"
            level_incremental = "Incremental"
            self.cache = alert_helper.alert_situations.backup_generated_data(client=self.client,
                                                                             subclient=self.subclient,
                                                                             backup_type=level_full,
                                                                             size=10)

            # Full Job Alert notification should be received
            alert_helper.check_if_alert_mail_received(short_interval=30, patterns=[self.cache.get("job_id"),
                                                                                   self.tcinputs["BackupsetName"],
                                                                                   self.tcinputs["SubclientName"],
                                                                                   level_full])

            # Now trigger an incremental backup job -> Alert shouldn't get triggered
            self.cache2 = alert_helper.alert_situations.backup_generated_data(client=self.client,
                                                                              subclient=self.subclient,
                                                                              backup_type=level_incremental,
                                                                              size=10)
            try:
                alert_helper.check_if_alert_mail_received(short_interval=30, patterns=[self.cache2.get("job_id"),
                                                                                       self.tcinputs["BackupsetName"],
                                                                                       self.tcinputs["SubclientName"],
                                                                                       level_incremental])
            except Exception as mail_receive_excp:
                self.log.error(f'Didin\'t receive alert notification mail for type {level_incremental}')
                self.log.error(f'Encountered Exception : {mail_receive_excp}')

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
