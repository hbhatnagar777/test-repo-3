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

import re
import time
from Server.Alerts.alert_helper import AlertHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase


# Class of Testcase is named as TestCase which inherits from CVTestCase
class TestCase(CVTestCase):
    """ Class for executing test case for Custom Alert to notify Clients not backed up for X Minutes"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase to for Custom Alert to notify Clients not backed up for X Minutes'
        self.cache = None
        self.rule_name = "ClientsnotbackedupforXminutes.xml"
        self.wait = 500
        # Some custom alerts require additional query info to be injected into the alert XML
        self.custom_query_details = ''
        self.backup_threshold = 1 # Backup Threshold in minutes


    def populate_custom_query_details(self, query_id, backup_threshold, client_name):
        """Populates the custom query xml which is required by some custom alerts"""
        self.custom_query_details = f'''&lt;?xml version='1.0' encoding='UTF-8'?&gt;&lt;CVGui_CustomQueryDetailsForAlert queryId=&quot;{query_id}&quot; additionalQueryInfo=&quot;&amp;lt;?xml version='1.0' encoding='UTF-8'?&gt;&amp;lt;CVGui_QueryAdditionalInfo&gt;&amp;lt;queryParameters&gt;&amp;lt;queryParameters paramName=&amp;quot;subclientname&amp;quot; value=&amp;quot;&amp;amp;lt;subclientname/&gt;&amp;quot; /&gt;&amp;lt;queryParameters paramName=&amp;quot;ClientList&amp;quot; value=&amp;quot;&amp;amp;lt;ClientList&gt;&amp;amp;lt;clientId&gt;2&amp;amp;lt;/clientId&gt;&amp;amp;lt;displayName&gt;GroupCS&amp;amp;lt;/displayName&gt;&amp;amp;lt;clientName&gt;{client_name}&amp;amp;lt;/clientName&gt;&amp;amp;lt;/ClientList&gt;&amp;quot; /&gt;&amp;lt;queryParameters paramName=&amp;quot;clientGroupList&amp;quot; value=&amp;quot;&amp;amp;lt;clientGroupList/&gt;&amp;quot; /&gt;&amp;lt;queryParameters paramName=&amp;quot;IDAName&amp;quot; value=&amp;quot;&amp;amp;lt;IDAName/&gt;&amp;quot; /&gt;&amp;lt;queryParameters paramName=&amp;quot;BackupThresholdinMins&amp;quot; value=&amp;quot;&amp;amp;lt;BackupThresholdinMins&gt;{backup_threshold}&amp;amp;lt;/BackupThresholdinMins&gt;&amp;quot; /&gt;&amp;lt;/queryParameters&gt;&amp;lt;/CVGui_QueryAdditionalInfo&gt;&quot; /&gt;'''
        self.custom_query_details = self.custom_query_details.replace("\n", "")

    def run(self):
        """Main function for test case execution"""
        try:
            # Initialize alerts object
            self.log.info('Initializing Alerts')
            alert_helper = AlertHelper(commcell_object=self.commcell,
                                       category='Custom Rules',
                                       alert_type='all')

            # Get Required Alert Rule from Automation/AlertRules folder
            rule_xml_request = alert_helper.read_alert_rule(rule_name=self.rule_name)

            # Modify alert xml to suit trigger criteria
            rule_xml_request = alert_helper.set_custom_alert_frequency(rule_xml_request,
                                                                       query_frequency=120)
            alert_helper.alert_xml = rule_xml_request

            # Import the Alert Rule
            # Query id flag is used in custom alerts, passed later when populating alert xml
            query_id = alert_helper.import_alert_rule(rule_name=self.rule_name,
                                                      xml_request=rule_xml_request)

            # Populate Custom Query Details --> Required for some custom alerts
            self.populate_custom_query_details(query_id=query_id,
                                               backup_threshold=self.backup_threshold,
                                               client_name=self.commcell.commserv_client.client_name)

            # Get Custom alert details
            custom_alert_details = alert_helper.get_custom_alert_xml(name='ClientNotBackedUp',
                                                                     notif_type=['Email'],
                                                                     to_users_mail=["admin"],
                                                                     query_id=query_id,
                                                                     mail_recipent=["TestAutomation3@commvault.com"],
                                                                     send_individual_notif=True,
                                                                     notification_criteria={'notify_if_persists': 60,
                                                                                            'repeat_notif': 60},
                                                                     custom_query_details=self.custom_query_details)

            # Initialize Mailbox object
            query_name = alert_helper.get_custom_query_name(rule_xml_request)
            alert_helper.initialize_mailbox(custom_rule_name=query_name)

            # Creating Custom Alert
            self.log.info('Creating Alert %s for testcase %s', custom_alert_details.get("alert_name"), self.id)
            alert_helper.create_alert_from_xml()

            # Trigger Alert Situation
            alert_helper.alert_situations.toggle_commcell_activity(enable=False)

            # Function to read email and confirm alert notification
            # There's a thread that runs -> Wait for 10 minutes before starting check for notifications
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
            # Enabling All activity on commcell
            alert_helper.alert_situations.toggle_commcell_activity()
            # Alerts Cleanup
            alert_helper.cleanup()
