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
    """ Class for executing basic test case for Auxiliary Copy Job management Alert"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'TestCase for Alerts - Job Management - Auxiliary Copy'
        self.cache = None
        tcinputs = {
          "AgentName":None,
          "ClientName":None,
          "StoragePolicy":None,
          "BackupsetName":None,
          "SubclientName":None,
          "BackupType":None,
          "CopyName":None
        }

    def run(self):
        """Main function for test case execution"""
        try:
            # Initialize alerts object
            self.log.info('Initializing Alerts')
            alert_helper = AlertHelper(commcell_object=self.commcell,
                                       category='Job Management',
                                       alert_type='Auxiliary Copy')

            # Creating Alert of given type
            # Feed alert data to create the right format
            alert_data = alert_helper.get_alert_xml(name='Test Aux Copy Job Alert',
                                                    notif_type=['Email', 'Console Alerts'],
                                                    entities={'storage_policies': self.tcinputs['StoragePolicy']},
                                                    criteria=1,
                                                    mail_recipent=["TestAutomation3@commvault.com"])
            # Initialize Mailbox object
            alert_helper.initialize_mailbox()

            self.log.info('Creating Alert %s for testcase %s', alert_data.get("alert_name"), self.id)
            alert_helper.create_alert_from_xml()

            # Trigger Alert Situation
            self.cache = alert_helper.alert_situations.backup_generated_data(client=self.client,
                                                                             subclient=self.subclient,
                                                                             backup_type=self.tcinputs['BackupType'],
                                                                             size=1)

            self.cache = alert_helper.alert_situations.auxiliary_copy_job(storage_policy_name=self.tcinputs["StoragePolicy"],
                                                                          copy_name=self.tcinputs["CopyName"])

            # Function to read email and confirmation alert notification
            alert_helper.check_if_alert_mail_received(short_interval=20,
                                                      patterns=[self.cache.get("job_id"),
                                                                self.tcinputs["StoragePolicy"]])

        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            # Alerts Cleanup
            if alert_helper:
                alert_helper.cleanup()
