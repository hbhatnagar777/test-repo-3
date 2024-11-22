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
from AutomationUtils import constants, config
from AutomationUtils.cvtestcase import CVTestCase


# Class of Testcase is named as TestCase which inherits from CVTestCase
class TestCase(CVTestCase):
    """ Class for executing basic test case of File System Backup using user defined parameters"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Triggering "Configuration: Schedules- Scheduler Changes" alert'
        self.alert_helper = None
        self.media_check_interval = 400
        self.email_recipient = config.get_config().email.email_id


    def run(self):
        """Main function for test case execution"""
        try:
            # Initialize alerts object
            self.log.info('Initializing Alerts')
            self.alert_helper = AlertHelper(commcell_object=self.commcell,
                                            category='Configuration',
                                            alert_type='Schedules')

            # Creating Alert of given type
            # Feed alert data to create the right format
            alert_data = self.alert_helper.get_alert_xml(name='Test Schedule Alert',
                                                         notif_type=['Email', 'Console Alerts'],
                                                         criteria=[21],
                                                         entities={'clients': self.tcinputs['ClientName']},
                                                         mail_recipent=[self.email_recipient],
                                                         notification_criteria={'repeat_notif':60}
                                                        )
            # Initialize Mailbox object
            self.alert_helper.initialize_mailbox()

            self.log.info('Creating Alert %s for testcase %s', alert_data.get("alert_name"), self.id)
            self.alert_helper.create_alert_from_xml()

            time.sleep(120)

            # Triggering the Alert
            self.schedule_policy = self.commcell.schedule_policies.add(
                name="TestSchedulePolicy",
                policy_type='Data Protection',
                associations=[
                    {
                        "clientName": self.tcinputs["ClientName"]
                    }
                ],
                schedules=[
                    {
                        'name': 'Dummy_name',
                        'pattern': {
                            "freq_type": 'automatic',
                            "use_storage_space_ma": True,
                            "sweep_start_time": 8 * 3600
                        }
                    }
                ],
                agent_type=[
                    {
                        "appGroupName": "Protected Files"
                    },
                    {
                        "appGroupName": "Archived Files"
                    }
                ]
            )
            self.schedule_policy.disable()

            # Verifying email alert
            patterns = ['Test Schedule Alert', 'Scheduler Changes', self.commcell.commserv_hostname, 'Modified', 'TestSchedulePolicy']
            self.alert_helper.check_if_alert_mail_received(short_interval=120, patterns=patterns)

        

        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED
    
    def tear_down(self):
        if self.alert_helper:
            self.alert_helper.cleanup()
            self.commcell.schedule_policies.delete("TestSchedulePolicy")
