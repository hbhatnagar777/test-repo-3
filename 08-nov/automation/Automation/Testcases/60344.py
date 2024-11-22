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
from Server.Alerts.alert_helper import AlertHelper, AlertSituations
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase


# Class of Testcase is named as TestCase which inherits from CVTestCase
class TestCase(CVTestCase):
    """ Class for executing test case for Custom Alert - Restore or Admin job runs for more than threshold time"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase to for Custom Alert - Restore or Admin job runs for more than threshold time'
        self.cache = None
        self.rule_name = "JobRunsForMoreThanXMin.xml"
        # Some custom alerts require additional query info to be injected into the alert XML
        self.custom_query_details = ''
        self.job_runtime_threshold = 1  # Runtime Threshold in minutes
        self.wait = 120
        tcinputs = {
          "AgentName":None,
          "BackupsetName":None,
          "InstanceName":None,
          "ClientName":None
        }


    def populate_custom_query_details(self, query_id, job_runtime_threshold):
        """Populates the custom query xml which is required by some custom alerts"""
        self.custom_query_details = f'''&lt;?xml version='1.0' encoding='UTF-8'?&gt;&lt;CVGui_CustomQueryDetailsForAlert queryId=&quot;{query_id}&quot; additionalQueryInfo=&quot;&amp;lt;?xml version='1.0' encoding='UTF-8'?&gt;&amp;lt;CVGui_QueryAdditionalInfo&gt;&amp;lt;queryParameters&gt;&amp;lt;queryParameters paramName=&amp;quot;runTime&amp;quot; value=&amp;quot;&amp;amp;lt;runTime&gt;{job_runtime_threshold}&amp;amp;lt;/runTime&gt;&amp;quot; /&gt;&amp;lt;/queryParameters&gt;&amp;lt;/CVGui_QueryAdditionalInfo&gt;&quot; /&gt;'''
        self.custom_query_details = self.custom_query_details.replace("\n", "")

    def run(self):
        """Main function for test case execution"""
        try:
            # Entities Setup
            self.log.info("Entities Setup for TestCase")
            alert_situations = AlertSituations(self.commcell)
            subclient_prop = alert_situations.create_entities(testcase_obj=self)
            subclient_obj = subclient_prop.get("subclient").get("object")

            # Initialize alerts object
            self.log.info('Initializing Alerts')
            alert_helper = AlertHelper(commcell_object=self.commcell,
                                       category='Custom Rules',
                                       alert_type='all')

            # Get Required Alert Rule from Automation/AlertRules folder
            rule_xml_request = alert_helper.read_alert_rule(rule_name=self.rule_name)

            # Modify alert xml to suit trigger criteria
            rule_xml_request = alert_helper.set_custom_alert_frequency(rule_xml_request, query_frequency=60)

            # Import the Alert Rule
            # Query id flag is used in custom alerts, passed later when populating alert xml
            query_id = alert_helper.import_alert_rule(rule_name=self.rule_name,
                                                      xml_request=rule_xml_request)

            # Populate Custom Query Details --> Required for some custom alerts
            self.populate_custom_query_details(query_id=query_id,
                                               job_runtime_threshold=self.job_runtime_threshold)

            # Get Custom alert details
            custom_alert_details = alert_helper.get_custom_alert_xml(name='JobRuntimeThreshold',
                                                                     notif_type=['Email'],
                                                                     query_id=query_id,
                                                                     mail_recipent=["TestAutomation3@commvault.com"],
                                                                     send_individual_notif=True,
                                                                     custom_query_details=self.custom_query_details,
                                                                     notification_criteria={'notify_if_persists': 60,
                                                                                            'repeat_notif': 60},
                                                                     associated_at_commcell_level=True
                                                                     )

            # Initialize Mailbox object
            query_name = alert_helper.get_custom_query_name(rule_xml_request)
            alert_helper.initialize_mailbox(custom_rule_name=query_name)

            # Creating Custom Alert
            self.log.info('Creating Alert %s for testcase %s', custom_alert_details.get("alert_name"), self.id)
            alert_helper.create_alert_from_xml()

            # Trigger Alert Situation

            # Part 1. Test created subclient backup, restore and trigger runtime threshold condition
            alert_helper.alert_situations.restore_runtime_threshold(client=self.client, subclient=subclient_obj)

            self.log.info(f"Waiting for {self.wait}seconds for alert to trigger")
            time.sleep(self.wait)
            alert_helper.check_if_alert_mail_received(short_interval=100,
                                                      patterns=[custom_alert_details.get("alert_name"),
                                                                "Custom Rules"])

            # Part 2. Admin Job (Data aging in this case) and trigger runtime threshold condition
            alert_helper.alert_situations.admin_job_runtime_threshold()

            # Function to read email and confirm alert notification
            self.log.info(f"Waiting for {self.wait}seconds for alert to trigger")
            time.sleep(self.wait)
            alert_helper.check_if_alert_mail_received(short_interval=100,
                                                      patterns=[custom_alert_details.get("alert_name"),
                                                                "Custom Rules"])

        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            # Cleanup phase
            # Cleanup map
            alert_situations.cleanup_entities(subclient_prop)
            # Alerts Cleanup
            alert_helper.cleanup()