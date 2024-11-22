# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing testcase 54930

TestCase is the only class defined in this file

TestCase: Class for executing this testcase

TestCase:
    __init__()      --  Initializes test case class object

    setup()       --  Setup function for this testcase

    run()           --  Main funtion for testcase execution

"""
# Test Suite Imports
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL
from AutomationUtils.config import get_config
from Server.Workflow.workflowhelper import WorkflowHelper
from Web.Common.cvbrowser import BrowserFactory
from Web.WebConsole.Laptop.gmail_helper import GmailHelper

class TestCase(CVTestCase):
    """Class for validating Invite for Commvault Edge workflow"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "WORKFLOW - Validate Invite for Commvault Edge"
        self._workflow = None
        self.machine = None
        self.workflow_name = 'WF_INVITE_FOR_COMMVAULT_EDGE'
        self.sqlobj = None
        self.tcinputs = {
            'invitee_email': None,
            'email_pwd': None,
            'share_link': None,
            'user_id': None
        }
        self._workflowhelper = None
        self.browser = None
        self.driver = None
        self.helper = None
        self.invitee_email = None
        self.email_pwd = None

    def check_user_credentials(self):
        """Validate if user received login credentials for edge drive"""
        self.browser = BrowserFactory().create_browser_object(name="ClientBrowser")
        self.browser.open()
        self.driver = self.browser.driver
        self.helper = GmailHelper(self.driver)
        self.helper.login_to_gmail(self.invitee_email, self.email_pwd)
        self.helper.search_gmail_with_sender('commvaultedge@commvault.com',
                        "Welcome to Commvault Edge. Your credentials and next steps.")
        retur_value = self.helper.read_username_password(self.invitee_email)
        if not retur_value:
            raise Exception('Validation of user credentials failed')
        self.log.info('User credentials are present in the email')
        self.helper.delete_gmail('commvaultedge@commvault.com')
        self.helper.logout()
        self.browser.close()

    def setup(self):
        """Setup function of this test case"""
        self._workflowhelper = WorkflowHelper(self, self.workflow_name)
        _CS_CONFIG = get_config()
        db_uname = _CS_CONFIG.Schedule.db_uname
        db_password = _CS_CONFIG.Schedule.db_password
        self.sqlobj = MSSQL(self.commcell.commserv_name + r'\commvault', db_uname,
                            db_password, "commserv")
        self.invitee_email = (self.tcinputs["invitee_email"])
        self.email_pwd = (self.tcinputs["email_pwd"])

    def run(self):
        """Main function of this testcase execution"""
        try:
            self.log.info("Deleting user: {0} from commcell before workflow starts"
                          .format(self.invitee_email))
            query1 = f"delete from umusergroup where " \
                    f"userid in (select id from umusers where email = '{self.invitee_email}')"
            query2 = "delete from umusers where email = '{}'".format(self.invitee_email)
            self.sqlobj.execute(query1)
            self.sqlobj.execute(query2)
            #Execute workflow
            self._workflowhelper.execute(
                {
                    'InviteeEmail': self.invitee_email,
                    'ShareLink': self.tcinputs["share_link"],
                    'RequestorUserId': self.tcinputs["user_id"]
                }
                )
            self.log.info("Validating if user: %s has received login credentials to access Edge",
                          format(self.invitee_email))
            self.check_user_credentials()
        except Exception as excp:
            self.log.info("Exception raise %s", format(excp))
            self._workflowhelper.test.fail(excp)
        finally:
            self._workflowhelper.cleanup()
            