# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    setup()         --  Setup function for this testcase

    run()           --  Main funtion for testcase execution

"""
# Test Suite Imports
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.mail_box import MailBox, EmailSearchFilter
from AutomationUtils.windows_machine import WindowsMachine
from Server.Workflow.workflowhelper import WorkflowHelper
from AutomationUtils.config import get_config

_STORE_CONFIG = get_config()

class TestCase(CVTestCase):

    """Class for validating additional setting sendWorkflowEmailsViaCommserver"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - (TR) - Email to send through Commserver instead of WorkflowEngine"
        self._workflow = None
        self.workflow_name = 'WF_EMAIL_COMMSERVER'
        self.tcinputs = {
            'MailDownloadLocation': None,
            'EmailId': None
        }
        self.mailbox = None
        self.machine = None
        self.idautils = None

    def setup(self):
        """Setup function of this test case"""
        self._workflow = WorkflowHelper(self, self.workflow_name, deploy=True)

    def run(self):
        """Main function of this testcase execution"""
        try:
            self.log.info("Initialising the add "
                          "additional setting [sendWorkflowEmailsViaCommserver] request")
            self.idautils = CommonUtils(self)
            self.idautils.modify_additional_settings('sendWorkflowEmailsViaCommserver', '1', 'WFEngine', 'INTEGER')
            self.log.info("Successfully added the additional setting to"
                          "relay mails from WorkflowEngine through CommServ")
            self._workflow.execute({'INP_EMAIL_ID': _STORE_CONFIG.email.email_id})
            self.log.info("Executed the workflow %s with Email activity "
                          "successfully", self.workflow_name)
            self.log.info("Initialising the Mailbox")
            self.mailbox = MailBox()
            self.log.info("Mailbox initialised successfully")
            self.mailbox.connect()
            self.log.info("Connected to the Mailbox successfully")
            subject = "Automation : SendWorkflowEmailsViaCommserver " \
                           "additional setting validation"
            download_dir = self.tcinputs['MailDownloadLocation']
            search_filter = EmailSearchFilter(subject=subject)
            self.log.info("Created search Filter")
            search_filter.get_mail_sent_from_date()
            self.log.info("Get Mail Sent from date")
            self.log.info("Initialising the download mail request")
            self.mailbox.download_mails(search_filter,
                                        download_dir, mail_folder='INBOX', save_attachments=False)
            self.log.info("Successfully downloaded the mail")
            self.log.info("Initialising the process to read log lines of WorkflowEngine.log")
            self.machine = WindowsMachine(self.commcell.commserv_hostname, self.commcell)
            self.log.info("Created Machine class object successfully")
            log_path = self.machine.client_object.log_directory
            self.log.info("Log Directory Path is %s", log_path)
            log_file_path = "{0}{1}".format(log_path, '\\WorkflowEngine.log')
            self.log.info("Log File Path is %s", log_file_path)
            search_msg = 'relaying email through CommServ'
            self.log.info("Searching log line [%s] in WorkflowEngine.log", search_msg)
            log_message = self.machine.read_file(log_file_path, search_term=search_msg)
            if not log_message:
                raise Exception("Log message [{0}] is "
                                "not found in WorkflowEngine.log".format(search_msg))
            self.log.info("Log Message returned %s", log_message)
            self.log.info("Workflow email is relayed through Commserv successfully")
        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflow.test.fail(excp)

        finally:
            self._workflow.cleanup()
            self.idautils.delete_additional_settings('sendWorkflowEmailsViaCommserver', 'WFEngine')
