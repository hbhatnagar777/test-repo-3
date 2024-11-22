# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 52890

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    setup()       --  Setup function for this testcase

    run()           --  Main funtion for testcase execution

"""
# Test Suite Imports
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.mail_box import MailBox, EmailSearchFilter
from AutomationUtils.machine import Machine
from Server.Workflow.workflowhelper import WorkflowHelper

class TestCase(CVTestCase):

    """Class for validating additional setting SendEmailsViaCommserver"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate additional setting SendEmailsViaCommserver"
        self._workflow = None
        self.machine = None
        self.workflow_name = 'WF_EMAIL_COMMSERVER'
        self._utility = OptionsSelector(self._commcell)
        self.sqlobj = None
        self.tcinputs = {"Email_list" : None}

    def setup(self):
        """Setup function of this test case"""
        self._workflowhelper = WorkflowHelper(self, self.workflow_name)
        self.machine = Machine(self.commcell.commserv_name, self._commcell)

    def run(self):
        """Main function of this testcase execution"""
        try:

            self.log.info("set additional setting sendWorkflowEmailsViaCommserver")
            self.machine.create_registry('WFEngine', 'sendWorkflowEmailsViaCommserver', 1, "DWord")

            self.log.info("set additional setting workflowGlobalCCRecipients")
            self.machine.create_registry('WFEngine', 'workflowGlobalCCRecipients', self.tcinputs['Email_list'])

            _ = self._workflowhelper.execute(
                {
                    'INP_EMAIL_ID': self._workflowhelper.email
                })
            self.log.info("Initialising the Mailbox")
            self.mailbox = MailBox()
            self.log.info("Mailbox initialised successfully")
            self.mailbox.connect()
            self.log.info("Connected to the Mailbox successfully")
            subject = "Automation : SendWorkflowEmailsViaCommserver additional setting validation"
            download_dir = constants.TEMP_DIR
            search_filter = EmailSearchFilter(subject=subject)
            self.log.info("Created search Filter")
            search_filter.get_mail_sent_from_date()
            self.log.info("Get Mail Sent from date")
            self.log.info("Initialising the download mail request")
            self.mailbox.download_mails(search_filter,
                                        download_dir, mail_folder='INBOX', save_attachments=False)
            self.log.info("Successfully downloaded the mail")

        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflowhelper.test.fail(excp)

        finally:
            self.machine.remove_registry('WFEngine', 'sendWorkflowEmailsViaCommserver')
            self.machine.remove_registry('WFEngine', 'workflowGlobalCCRecipients')
            self._workflowhelper.cleanup()
