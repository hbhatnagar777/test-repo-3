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
from cvpysdk.exception import SDKException
from Server.Alerts.alert_helper import AlertHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine


# Class of Testcase is named as TestCase which inherits from CVTestCase
class TestCase(CVTestCase):
    """ Class for executing test case for Custom Alert to notify No Data Aging in the past X Days"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase to for Custom Alert to notify No Data Aging in the past X Days'
        self.cache = None
        self.rule_name = "NoDataAgingInThePastXDays.xml"
        self.wait = 500
        # Some custom alerts require additional query info to be injected into the alert XML
        self.custom_query_details = ''
        self.no_days = 1 # Backup Threshold in minutes

    def append_task_info_xml(self, custom_rule_xml):
        """Populates the task info xml required for custom rule xml"""
        active_start_date = int(time.time())
        freq_interval = 300
        guid = self.commcell.commserv_guid
        modified_xml = ''
        task_info_xml = f'''<?xml version='1.0' encoding='UTF-8'?><TMMsg_TaskInfo><task description="" ownerId="3" runUserId="1" taskType="2" ownerName="master" alertId="0" GUID="{guid}" policyType="10" associatedObjects="0" taskName="" taskId="0"><securityAssociations><ownerAssociations /></securityAssociations><originalCC commCellId="2" /><taskSecurity><associatedUserGroups userGroupId="1" _type_="15" userGroupName="master" /><advancedPrivacySettings authType="1"><passkeySettings enableAuthorizeForRestore="0"><expirationTime time="0" /></passkeySettings></advancedPrivacySettings><ownerCapabilities /></taskSecurity><createAs><user><user userName="admin" userId="1" /></user></createAs><taskFlags isEdgeDrive="0" isEZOperation="0" forDDB="0" uninstalled="0" isSystem="0" isIndexBackup="0" disabled="0" isEdiscovery="0" /><task taskName="" taskId="3047" /></task><appGroup /><subTasks><subTask subTaskOrder="0" subTaskName="" subTaskType="1" flags="0" operationType="5014" subTaskId="0"><subTask subtaskId="3129" subtaskName="" /></subTask><pattern active_end_occurence="0" freq_subday_interval="{freq_interval}" freq_type="2048" patternId="284" flags="0" description="" active_end_time="86340" active_end_date="0" skipOccurence="0" skipDayNumber="0" active_start_time="0" freq_restart_interval="0" active_start_date="{active_start_date}" freq_interval="127" freq_relative_interval="0" name="" freq_recurrence_factor="1"><daysToRun week="0" Monday="1" Thursday="1" Friday="1" Sunday="1" Wednesday="1" Tuesday="1" day="0" Saturday="1" /><calendar calendarName="Standard" calendarId="1" /><timeZone TimeZoneID="" /></pattern><options><backupOpts><dataOpt autoCopy="0" /></backupOpts><commonOpts><automaticSchedulePattern useStorageSpaceFromMA="0" /></commonOpts></options></subTasks></TMMsg_TaskInfo>'''
        task_info_xml = task_info_xml.replace("<", "&lt;").replace('"', "&quot;")
        modified_xml = re.sub('visibility="\d+">', f'''taskInfoXml="{task_info_xml}" visibility="0">''', custom_rule_xml)
        return modified_xml

    def populate_custom_query_details(self, query_id, no_days):
        """Populates the custom query xml which is required by some custom alerts"""
        self.custom_query_details = f'''&lt;?xml version='1.0' encoding='UTF-8'?&gt;&lt;CVGui_CustomQueryDetailsForAlert queryId=&quot;{query_id}&quot; additionalQueryInfo=&quot;&amp;lt;?xml version='1.0' encoding='UTF-8'?&gt;&amp;lt;CVGui_QueryAdditionalInfo&gt;&amp;lt;queryParameters&gt;&amp;lt;queryParameters paramName=&amp;quot;noOfDays&amp;quot; value=&amp;quot;&amp;amp;lt;noOfDays&gt;{no_days}&amp;amp;lt;/noOfDays&gt;&amp;quot; /&gt;&amp;lt;/queryParameters&gt;&amp;lt;/CVGui_QueryAdditionalInfo&gt;&quot; /&gt;'''
        self.custom_query_details = self.custom_query_details.replace("\n", "")

    def restart_services(self):
        # Restart Client Services
        self.log.info(f'Stopping Commserve Services')
        self.commcell.commserv_client.stop_service()
        self.log.info('sleeping 120 seconds for stopping services')
        time.sleep(120)

        self.log.info('Starting Commserve Services')
        machine = Machine(self.tcinputs['client machine name'], username=self.tcinputs['client machine administrator'],
                          password=self.tcinputs['client machine password'])
        machine.start_all_cv_services()
        self.log.info('sleeping 60 seconds for starting services')
        time.sleep(60)


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

            # Modify rule xml to suit trigger criteria
            rule_xml_request = self.append_task_info_xml(rule_xml_request)

            # Import the Alert Rule
            # Query id flag is used in custom alerts, passed later when populating alert xml
            query_id = alert_helper.import_alert_rule(rule_name=self.rule_name,
                                                      xml_request=rule_xml_request)

            # Populate Custom Query Details --> Required for some custom alerts
            self.populate_custom_query_details(query_id=query_id,
                                               no_days=self.no_days)

            # Get Custom alert details
            custom_alert_details = alert_helper.get_custom_alert_xml(name='NoDataAgingInPastXDays',
                                                                     notif_type=['Email'],
                                                                     to_users_mail=["admin"],
                                                                     query_id=query_id,
                                                                     mail_recipent=["TestAutomation3@commvault.com"],
                                                                     send_individual_notif=True,
                                                                     custom_query_details=self.custom_query_details)

            # Initialize Mailbox object
            query_name = alert_helper.get_custom_query_name(rule_xml_request)
            alert_helper.initialize_mailbox(custom_rule_name=query_name)

            # Run Data Aging Job
            data_aging_job = self.commcell.run_data_aging()

            # Creating Custom Alert
            self.log.info('Creating Alert %s for testcase %s', custom_alert_details.get("alert_name"), self.id)
            alert_helper.create_alert_from_xml()

            # Trigger Alert Situation
            alert_helper.alert_situations.toggle_commcell_activity(enable=False)
            # Shift system date to T+2 days
            alert_helper.alert_situations.no_backup_in_n_days(n=3)
            self.restart_services()

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
            # Alerts Cleanup
            alert_helper.cleanup()
            alert_helper.alert_situations.cleanup_no_backup_in_n_days()
            # Enabling All activity on commcell
            alert_helper.alert_situations.toggle_commcell_activity()
