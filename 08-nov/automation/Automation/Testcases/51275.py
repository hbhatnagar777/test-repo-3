# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Commcell Alerts on Cloud Dashboards"""
from time import sleep
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase

from Reports.storeutils import StoreUtils
from Reports.utils import TestCaseUtils
from Reports import reportsutils

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestStepFailure, CVTestCaseInitFailure
from Web.WebConsole.Reports.Metrics.dashboard import Dashboard
from Web.Common.page_object import TestStep
from Web.WebConsole.Reports.Custom import viewer
from Web.WebConsole.webconsole import WebConsole
from Web.WebConsole.Reports.navigator import Navigator


from FileSystem.FSUtils.fshelper import FSHelper

CONSTANTS = get_config()


class TestCase(CVTestCase):
    """ Commcell Alerts on Cloud Dashboards """
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.util = StoreUtils(self)
        self.workflow_name = 'Commcell Alerts on Cloud Dashboards'
        self.store_api = None
        self.table = None
        self.browser = None
        self.client = None
        self.agent = None
        self.webconsole = None
        self.helper = None
        self.storage_policy = None
        self.job_id = None
        self.name = "Commcell Alerts on Cloud Dashboards"
        self.alert_name = "Automation_tc_51275_alert"
        self.utils = TestCaseUtils(self)

    def init_webconsole(self):
        """Initialize webconsole"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            webconsole_hostname = CONSTANTS.Reports.PUBLIC_CLOUD
            self.webconsole = WebConsole(self.browser, webconsole_hostname)
            self.webconsole.login(username=CONSTANTS.email.username, password=CONSTANTS.email.password)
            self.webconsole.goto_commcell_dashboard()
            navigator = Navigator(self.webconsole)
            commcell_name = reportsutils.get_commcell_name(self.commcell)
            navigator.goto_commcell_dashboard(commcell_name)
            commcell_dashboard = Dashboard(self.webconsole)
            commcell_dashboard.access_commcell_alerts()
            _viewer = viewer.CustomReportViewer(self.webconsole)
            self.table = viewer.DataTable("Details")
            _viewer.associate_component(self.table)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def create_backupset(self):
        """"create backupset"""
        self.tcinputs.update({('TestPath', 'c:\\test')})
        self.tcinputs.update({('StoragePolicyName', self.storage_policy)})
        self.client = self.commcell.clients.get(self.commcell.commserv_name)
        self.agent = self.client.agents.get('file system')
        FSHelper.populate_tc_inputs(self)
        backupset_name = "auto_backupset_" + self.id
        self.helper.create_backupset(backupset_name, True)
        self.log.info("[%s] backupset is created", backupset_name)

    def create_subclient(self):
        """Create subclient"""
        subclient_name = "auto_subclient_" + self.id
        subclient_content = ["c:\\auto_subclient_content_" + self.id]
        self.helper.create_subclient(name=subclient_name,
                                     storage_policy=self.storage_policy,
                                     content=subclient_content,
                                     delete=False)

    def create_storage_policy(self):
        """Create storage policy"""
        self.storage_policy = "Auto_sp_" + self.id
        if self.commcell.storage_policies.has_policy(self.storage_policy):
            self.log.info("[%s] Storage policy already exists!", self.storage_policy)
            return
        library = "auto_lib_51275"
        if not self.commcell.disk_libraries.has_library(library):
            self.commcell.disk_libraries.add(library, self.commcell.commserv_client.name,
                                             "c:\\testme")
        _ret = self.commcell.storage_policies.add(self.storage_policy, library,
                                                  self.commcell.commserv_name)
        self.log.info("Created [%s] storage policy successfully!", self.storage_policy)

    def setup(self):
        """Test case Pre Configuration"""
        self.delete_commcell_alert()
        self.create_storage_policy()
        self.create_backupset()
        self.create_subclient()

    @test_step
    def verify_cloud_alert(self):
        """Verify commcell alert is present in cloud webconsole"""
        self.log.info("Verify alert is present in cloud")
        self.table.set_filter(column_name="Job ID", filter_string=self.job_id)
        self.table.set_filter(column_name="Alert Name", filter_string=self.alert_name)
        data = self.table.get_table_data()
        if ["No data to display."] in list(data.values()):
            raise CVTestStepFailure("No row exists in commcell alert report with [%s] "
                                    "job id" % self.job_id)
        if data.get('Client') == [self.commcell.commserv_client.display_name] and \
                data.get('Job ID') == [self.job_id] and \
                data.get('Alert Name') == [self.alert_name]:
            self.log.info("Verified alert in cloud successfully")
            return
        raise CVTestStepFailure("Verify client name and alert name for [%s] job id in "
                                "cloud alert report" % self.job_id)

    @test_step
    def delete_commcell_alert(self):
        """Delete commcell alert"""
        self.log.info("Deleting commcell alert")
        if self.commcell.alerts.has_alert(self.alert_name):
            self.commcell.alerts.delete(self.alert_name)
        self.log.info("Commcell alert is deleted!")

    @test_step
    def create_commcell_alert(self):
        """Create commcell alert"""
        #  create alert with job management -> data protection, with default client
        self.log.info("Creating commcell alert [%s]", self.alert_name)
        xml = """<?xml version="1.0" encoding="UTF-8" standalone="no" ?><CVGui_AlertCreateReq ownerId="1"><processinginstructioninfo><user _type_="13" userId="1" userName="admin"/><locale _type_="66" localeId="0"/><formatFlags continueOnError="0" elementBased="0" filterUnInitializedFields="0" formatted="0" ignoreUnknownTags="1" skipIdToNameConversion="1" skipNameToIdConversion="0"/></processinginstructioninfo><alertDetail alertSeverity="0" alertTokenRuleGroupXml="" checkForEventParams="0" customQueryDetailsXml="" escalationSeverity="0" eventCriteriaXML="" periodicNotificationInterval="0" recipient="" senderDisplayName="" senderEmailId="" xmlEntityList="&lt;?xml version='1.0' encoding='UTF-8'?>&lt;CVGui_CommCellTreeNode>&lt;associations clientName=&quot;&quot; clientId=&quot;2&quot; _type_=&quot;3&quot;>&lt;flags exclude=&quot;0&quot; />&lt;/associations>&lt;/CVGui_CommCellTreeNode>"><alert GUID="" createdTime="1552386977" description="" escNotifType="0" notifType="512" organizationId="0" origCCId="0" status="0"><alert id="0" name="Automation_tc_51275_alert"/><alertCategory id="1" name="Job Management"/><alertType id="3" name="Data Protection"/><creator id="1" name="admin"/><organization _type_="189"/></alert><runCommands arguments="" cmdPath="" cvpassword="" domain="" enabled="0" esclationLevel="1" flags="0" impersonateUser="0" loginName="" password="||#5!M2NmZTNlZWI4NTRlOGFhNjRlMDE1NWJlYzAxOTY3NGQ1&#xA;" runCommandFlag="0" runDataArchiver="0" useNetworkShare="0"/><runCommands arguments="" cmdPath="" cvpassword="" domain="" enabled="0" esclationLevel="2" flags="0" impersonateUser="0" loginName="" password="||#5!M2NmZTNlZWI4NTRlOGFhNjRlMDE1NWJlYzAxOTY3NGQ1&#xA;" runCommandFlag="0" runDataArchiver="0" useNetworkShare="0"/><criteria criteriaId="5" criteriaSeverity="0" delayTimeSeconds="0" esclationLevel="1" persistTimeSeconds="0" reportId="0" reportingOptions="1" taskId="0" value=""><criteriaParams paramIndex="0" type="2" unit="5" value="1"/></criteria><criteria criteriaId="54" criteriaSeverity="0" delayTimeSeconds="0" esclationLevel="1" persistTimeSeconds="0" reportId="0" reportingOptions="1" taskId="0" value=""/><notifMsgs esclationLevel="1" localeId="0" messageFormat="1" notifMessage="&lt;SUBJECT BEGIN> Alert: &lt;ALERT NAME> Type: &lt;ALERT CATEGORY - ALERT TYPE> &lt;IS ESCALATED?> &lt;SUBJECT END> MsgNewLine_ Alert: &lt;ALERT NAME> MsgNewLine_ Type: &lt;ALERT CATEGORY - ALERT TYPE> MsgNewLine_MsgTab_ Detected Criteria: &lt;DETECTED CRITERIA> MsgNewLine_MsgTab_ Detected Time: &lt;TIME> MsgNewLine_MsgTab_ CommCell: &lt;COMMCELL NAME> MsgNewLine_MsgTab_ User: &lt;USER NAME> MsgNewLine_ MsgNewLine_ MsgTab_ Job ID: &lt;JOB ID> MsgNewLine_MsgTab_ Status: &lt;STATUS> MsgNewLine_MsgTab_ Client: &lt;CLIENT NAME> MsgNewLine_MsgTab_ Agent Type: &lt;AGENT TYPE NAME> MsgNewLine_MsgTab_ Instance: &lt;INSTANCE NAME> MsgNewLine_MsgTab_ Backup Set: &lt;BACKUPSET NAME> MsgNewLine_MsgTab_ Subclient: &lt;SUBCLIENT NAME> MsgNewLine_MsgTab_ Backup Level: &lt;LEVEL> MsgNewLine_MsgTab_ Storage Policies Used: &lt;STORAGE POLICIES USED> MsgNewLine_MsgTab_ Virtual Machine Name: &lt;VIRTUAL MACHINE NAME> MsgNewLine_MsgTab_ Virtual Machine Host Name: &lt;VIRTUAL MACHINE HOST NAME> MsgNewLine_MsgTab_ Virtual Machine Backup Status: &lt;VM STATUS> MsgNewLine_MsgTab_ Failure reason for Virtual Machine Backup: &lt;VM FAILURE REASON> MsgNewLine_MsgTab_ Start Time: &lt;START TIME> MsgNewLine_MsgTab_ Scheduled Time: &lt;SCHEDULE TIME> MsgNewLine_MsgTab_ End Time: &lt;END TIME> MsgNewLine_MsgTab_ Error Code: &lt;ERR CODE> MsgNewLine_MsgTab_ Failure Reason: &lt;FAILURE REASON> MsgNewLine_MsgTab_ Protected Counts: &lt;PROTECTED COUNT> MsgNewLine_MsgTab_ Failed Counts: &lt;FAILED COUNT> MsgNewLine_MsgTab_ &lt;ADDITIONAL VM INFO> " notifMessageHtml="&lt;SUBJECT BEGIN> Alert: &lt;ALERT NAME> Type: &lt;ALERT CATEGORY - ALERT TYPE> &lt;IS ESCALATED?> &lt;SUBJECT END>&lt;div id=&quot;contentTbl-table-scroll&quot;>&#xA;      &lt;table cellpadding=&quot;0&quot; cellspacing=&quot;0&quot; border=&quot;1&quot; align=&quot;center&quot; width=&quot;75%&quot; style=&quot;border-left-color: #dedede; border-bottom-width: 0px; border-bottom-style: solid; border-left-width: 0px; border-top-style: solid; border-top-color: #dedede; border-right-color: #dedede; border-bottom-color: #dedede; border-left-style: solid; border-right-style: solid; border-top-width: 0px; border-right-width: 0px&quot;>&#xA;        &lt;tr>&#xA;          &lt;td>&#xA;            &lt;center>&#xA;              &lt;table cellpadding=&quot;0&quot; border=&quot;0&quot; id=&quot;contentTbl&quot; width=&quot;100%&quot; align=&quot;center&quot; cellspacing=&quot;0&quot;>&#xA;                &lt;tr style=&quot;background-color: #666666&quot;>&#xA;                  &lt;td valign=&quot;middle&quot; align=&quot;left&quot;>&#xA;                    &lt;div style=&quot;margin-left: 10px; margin-bottom: 4px; margin-top: 4px&quot;>&#xA;                      &lt;font size=&quot;6&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#EEEEEE&quot;>&amp;lt;ALERT NAME&amp;gt; &lt;/font>&#xA;                    &lt;/div>&#xA;                  &lt;/td>&#xA;                &lt;/tr>&#xA;                &lt;tr>&#xA;                  &lt;td colspan=&quot;1&quot; valign=&quot;middle&quot; align=&quot;left&quot; bgcolor=&quot;#DCDEDE&quot;>&#xA;                    &lt;ul style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                      &lt;font size=&quot;4&quot; face=&quot;Helvetica,sans-serif&quot;>&lt;strong>CommCell: &lt;/strong>&lt;/font>&lt;strong>&lt;font color=&quot;#660000&quot; size=&quot;4&quot; face=&quot;Helvetica,sans-serif&quot;>&amp;lt;COMMCELL NAME&amp;gt;&lt;/font>&lt;/strong>&#xA;                    &lt;/ul>&#xA;                    &lt;ul style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                      &lt;font size=&quot;4&quot; face=&quot;Helvetica,sans-serif&quot;>&lt;strong>Type: &lt;/strong>&lt;/font>&lt;strong>&lt;font color=&quot;#660000&quot; size=&quot;4&quot; face=&quot;Helvetica,sans-serif&quot;>&amp;lt;ALERT CATEGORY - ALERT TYPE&amp;gt;&lt;/font>&lt;/strong>&#xA;                    &lt;/ul>&#xA;                    &lt;ul style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                      &lt;font size=&quot;4&quot; face=&quot;Helvetica,sans-serif&quot;>&lt;strong>Detected Criteria: &lt;/strong>&lt;/font>&lt;strong>&lt;font color=&quot;#660000&quot; size=&quot;4&quot; face=&quot;Helvetica,sans-serif&quot;>&amp;lt;DETECTED CRITERIA&amp;gt;&lt;/font>&lt;/strong>&#xA;                    &lt;/ul>&#xA;                    &lt;ul style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                      &lt;font size=&quot;4&quot; face=&quot;Helvetica,sans-serif&quot;>&lt;strong>Detected Time: &lt;/strong>&lt;/font>&lt;strong>&lt;font color=&quot;#660000&quot; size=&quot;4&quot; face=&quot;Helvetica,sans-serif&quot;>&amp;lt;TIME&amp;gt;&lt;/font>&lt;/strong>&#xA;                    &lt;/ul>&#xA;                  &lt;/td>&#xA;                &lt;/tr>&#xA;                &lt;tr>&#xA;                  &lt;td width=&quot;100%&quot; colspan=&quot;1&quot; align=&quot;left&quot;>&#xA;                    &lt;ul>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>User: &amp;lt;USER NAME&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Job ID: &amp;lt;JOB ID&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Status: &amp;lt;STATUS&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Client: &amp;lt;CLIENT NAME&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Agent Type: &amp;lt;AGENT TYPE NAME&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Instance: &amp;lt;INSTANCE NAME&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Backup Set: &amp;lt;BACKUPSET NAME&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Subclient: &amp;lt;SUBCLIENT NAME&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Backup Level: &amp;lt;LEVEL&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Storage Policies Used: &amp;lt;STORAGE POLICIES USED&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Virtual Machine Name: &amp;lt;VIRTUAL MACHINE NAME&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Virtual Machine Host Name: &amp;lt;VIRTUAL MACHINE HOST NAME&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Virtual Machine Backup Status: &amp;lt;VM STATUS&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Failure reason for Virtual Machine Backup: &amp;lt;VM FAILURE REASON&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Start Time: &amp;lt;START TIME&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Scheduled Time: &amp;lt;SCHEDULE TIME&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>End Time: &amp;lt;END TIME&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Error Code: &amp;lt;ERR CODE&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Failure Reason: &amp;lt;FAILURE REASON&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Protected Counts: &amp;lt;PROTECTED COUNT&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>Failed Counts: &amp;lt;FAILED COUNT&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                      &lt;li style=&quot;margin-top: 4px; margin-bottom: 4px&quot;>&#xA;                        &lt;font size=&quot;3&quot; face=&quot;Helvetica,sans-serif&quot; color=&quot;#000000&quot;>&amp;lt;ADDITIONAL VM INFO&amp;gt;&#xA;&lt;/font>                      &lt;/li>&#xA;                    &lt;/ul>&#xA;                  &lt;/td>&#xA;                &lt;/tr>&#xA;                &lt;tr style=&quot;background-color: #666666&quot;>&#xA;                  &lt;td colspan=&quot;1&quot; align=&quot;left&quot;>&#xA;                    &#xA0;&#xA;                  &lt;/td>&#xA;                &lt;/tr>&#xA;              &lt;/table>&#xA;            &lt;/center>&#xA;          &lt;/td>&#xA;        &lt;/tr>&#xA;      &lt;/table>&#xA;    &lt;/div>" notifOptions="0" notifType="512"><saveAlertToDisk alertLocation="CLOUD" cvpassword="" impersonateUser="0" loginName="" password="||#5!M2NmZTNlZWI4NTRlOGFhNjRlMDE1NWJlYzAxOTY3NGQ1&#xA;" useNetworkShare="2"/><feeds baseLocation="" rssFeedLocation="" selectedChannel="" seperateIndex="0"/><entity _type_="0"/></notifMsgs><locale localeID="0" localeName=""/><reportingParams delayTimeSeconds="0" persistTimeSeconds="0" reportingOptions="0"/><appTypeFilters/><securityAssociations processHiddenPermission="0"/><alertProperties/></alertDetail></CVGui_AlertCreateReq>"""
        response = self.commcell.execute_qcommand("qoperation execute", xml)
        if response:
            if 'alertId' in response.json().keys():
                self.log.info("commcell alert [%s] is created successfully", self.alert_name)
                return
        raise CVTestStepFailure("Failed to create alert with reason: %s" % response.content)

    def initiate_backup(self):
        """Initiates backup of subclient"""
        self.job_id = self.helper.run_backup(wait_to_complete=False)[0].job_id
        self.log.info("Backup triggered for [%s] subclient", self.subclient.name)

    def run(self):
        try:
            self.create_commcell_alert()
            self.initiate_backup()
            self.log.info("wait for 3 minutes to complete alert xml upload and processing")
            sleep(180)
            self.init_webconsole()
            self.verify_cloud_alert()
            self.delete_commcell_alert()
        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            WebConsole.logout_silently(self.webconsole)
            Browser.close_silently(self.browser)
