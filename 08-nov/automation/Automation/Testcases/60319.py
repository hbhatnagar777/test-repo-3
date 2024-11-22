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
from AutomationUtils.options_selector import CVEntities
from Server.Alerts.alert_helper import AlertHelper, AlertSituations
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase


# Class of Testcase is named as TestCase which inherits from CVTestCase
class TestCase(CVTestCase):
    """ Class for executing test case for Custom Alert to notify When Scan Phase Exceeds Threshold"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase to for Custom Alert to notify when Scan Phase Exceeds Threshold'
        self.cache = None
        self.rule_name = "Backupjobscanphaseexceedsthreshold.xml"
        self.wait = 60
        # Some custom alerts require additional query info to be injected into the alert XML
        self.custom_query_details = ''
        self.scan_threshold = 1  # Scan Phase Threshold in minutes
        self._entities = None
        self._utility = None

    def populate_custom_query_details(self, query_id, scan_threshold):
        """Populates the custom query xml which is required by some custom alerts"""
        self.custom_query_details = f'''&lt;?xml version='1.0' encoding='UTF-8'?&gt;&lt;CVGui_CustomQueryDetailsForAlert queryId=&quot;{query_id}&quot; additionalQueryInfo=&quot;&amp;lt;?xml version='1.0' encoding='UTF-8'?&gt;&amp;lt;CVGui_QueryAdditionalInfo&gt;&amp;lt;queryParameters&gt;&amp;lt;queryParameters paramName=&amp;quot;LRJMPhaseTriggerTime&amp;quot; value=&amp;quot;&amp;amp;lt;LRJMPhaseTriggerTime&gt;{scan_threshold}&amp;amp;lt;/LRJMPhaseTriggerTime&gt;&amp;quot; /&gt;&amp;lt;/queryParameters&gt;&amp;lt;/CVGui_QueryAdditionalInfo&gt;&quot; /&gt;'''
        self.custom_query_details = self.custom_query_details.replace("\n", "")

    def run(self):
        """Main function for test case execution"""
        try:
            # Entities Setup
            self.log.info("Entities Setup for TestCase")
            alert_situations = AlertSituations(self.commcell)
            subclient_prop = alert_situations.create_entities(testcase_obj=self,
                                                              content=["C:\\"])

            # Initialize alerts object
            self.log.info('Initializing Alerts')
            alert_helper = AlertHelper(commcell_object=self.commcell,
                                       category='Custom Rules',
                                       alert_type='all')

            # Get Required Alert Rule from Automation/AlertRules folder
            rule_xml_request = alert_helper.read_alert_rule(rule_name=self.rule_name)

            # Modify alert xml to suit trigger criteria
            rule_xml_request = alert_helper.set_custom_alert_frequency(custom_rules_xml=rule_xml_request,
                                                                       query_frequency=60)

            # Import the Alert Rule
            # Query id flag is used in custom alerts, passed later when populating alert xml
            query_id = alert_helper.import_alert_rule(rule_name=self.rule_name,
                                                      xml_request=rule_xml_request)

            # Populate Custom Query Details --> Required for some custom alerts
            self.populate_custom_query_details(query_id=query_id,
                                               scan_threshold=self.scan_threshold)

            # Get Custom alert details
            custom_alert_details = alert_helper.get_custom_alert_xml(name='ScanPhaseExceedsThreshold',
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
            # Set File system Data Protection and indexing job runtime threshold

            # Run Backup Job for created subclient (Content : /C)
            subclient_obj = subclient_prop.get("subclient").get("object")
            try:
                alert_helper.alert_situations.suspend_in_scan_phase(subclient=subclient_obj,
                                                                    backup_type=self.tcinputs['BackupType'])
            except Exception as job_excp:
                self.log.info(job_excp)

            # Function to read email and confirm alert notification
            self.log.info(f"Waiting for {self.wait}seconds before searching for alert notification")
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
            # Delete created subclient
            try:
                alert_situations.cleanup_entities(subclient_prop)
            except Exception as entity_cleanup_excp:
                self.log.info(f"Encountered Exception in entities cleanup : {entity_cleanup_excp}")
            # Alerts Cleanup
            alert_helper.cleanup()
            # Run Data Aging job to clean redundant job metadata
            self.commcell.run_data_aging()