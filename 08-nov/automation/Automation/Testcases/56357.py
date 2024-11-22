# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

import time
from cvpysdk.commcell import Commcell, SDKException
from AutomationUtils.cvtestcase import CVTestCase
from Server.Monitoring import monitoringhelper
from Server.serverhelper import ServerTestCases
from Server.Alerts import alert_helper


class TestCase(CVTestCase):
    """Class for Event Raiser Policy Acceptance"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Event Raiser Monitoring Policy] - Acceptance"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.LOGMONITORING
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = False

    def setup(self):
        """Setup function of this test case"""
        self._server_tc = ServerTestCases(self)
        self._monitoring_policies = monitoringhelper.MonitoringHelper(self.commcell)

    def run(self):
        """Main function for test case execution"""

        try:

            self._server_tc.log_step(
                """
                            Test Case
                            1) Create event raiser policy with criteria 'UserName/Password are incorrect'
                               and continuous mode on the 'WebServer.log'.
                            2) Check if an alert got auto created for this policy with format
                               [event raiser alert for monitoring policy[policyname]]
                            2) add an email address as email recepient to the auto created alert
                            3) enable the alert
                            4) Generate the positive event by Logging in with incorrect Credentials.
                            5) Generate a negative event by changing the description of any client.
                               (one which does not match the provided criteria)
                            5) Attach to the mailbox for the alert email address.
                            6) Check for the alert based on the subject and provided criteria
                               in the mail body for both positive and negative event.
                            """, 200
            )

            self._server_tc.log_step("""(Step 1) Create event raiser policy with criteria 'UserName/Password are
                                        incorrect' and continuous mode on the 'WebServer.log'.""")
            policy_name = str(self.id)+'_policy'
            _conditions_xml = '<LogMonitoring_ConditionsList ' \
                              'criteriaName="(Description contains Username/Password are incorrect)" ' \
                              'opBetweenConditions="0">' \
                              '<conditions value1="Username/Password are incorrect" operation="2">' \
                              '<column _type_="87" columnId="6" columnName="Description" />' \
                              '</conditions></LogMonitoring_ConditionsList>'
            self._monitoring_policies.create_monitoring_policy(policy_name, 'Commvault Logs', None,
                                                               self.commcell.commserv_client.client_name,
                                                               '%LOG_DIR%\\WebServer.log', False, policy_type=1,
                                                               conditionsXML=_conditions_xml,
                                                               continuousMode=True)

            self._server_tc.log_step("""(Step 2) Check if auto created alert is present and add the test email address
                                        as recipient.""")
            alert_obj = self.commcell.alerts.get('event raiser alert for monitoring policy[%s]' % policy_name)
            alert_obj.email_recipients = ['testautomation3@commvault.com']
            alert_obj.enable()

            self._server_tc.log_step("""(Step 3) Generate the positive event by Logging in with incorrect
                                        Credentials.""")
            try:
                Commcell(self.commcell.commserv_hostname, self.id, '######')
            except SDKException:
                self.log.info('This is a known exception as it is a forced invalid login attempt')

            self._server_tc.log_step("""(Step 4) Generate a negative event by changing the description of any
                                     client""")
            self.commcell.commserv_client.description = "test negative event"

            self._server_tc.log_step("""(Step 5) Attach to the test email address mailbox""")
            alert_helper_obj = alert_helper.AlertHelper(self.commcell, alert_obj=alert_obj)
            alert_helper_obj.initialize_mailbox()

            self.log.info("Sleeping for 5 minutes as its a continuous monitoring job")
            time.sleep(300)

            self._server_tc.log_step("""(Step 6) Check for the alert based on the subject and provided criteria
                               in the mail body for both positive and negative event.""")
            alert_helper_obj.check_if_alert_mail_received(short_interval=30,
                                                          patterns=['Username/Password are incorrect'])

            try:
                alert_helper_obj.check_if_alert_mail_received(short_interval=2, patterns=['test negative event'])
                self._server_tc.fail('Incorrectly raised alert for a negative event')
            except Exception:
                self.log.info("This is a known exception as it is a negative event")

        except Exception as excp:
            self._server_tc.fail(excp)

        finally:
            self._monitoring_policies.cleanup_policies()
