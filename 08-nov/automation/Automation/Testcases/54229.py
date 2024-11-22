# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

Verify if backups run with valid/invalid credentials

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic, and it is the one executed

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.credential_manager_helper import CredentialManagerHelper
from Web.AdminConsole.FSPages.fs_agent import FsAgent
from Web.AdminConsole.Helper.fs_helper import FSHelper
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Verify if backups run with valid/invalid credentials"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.fs_agent_obj = None
        self.cm_helper = None
        self.fs_helper_obj = None
        self.tcinputs = {
            "account_type": None,
            "credential_name": None,
            "credential_username": None,
            "credential_password": None,
            "backupset_name": None,
            "subclient_name": None,
            "plan_name": None,
            "client": None,
            "subclient_content_path": None,
        }

    def setup(self):

        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.fs_agent_obj = FsAgent(self.admin_console)
        self.fs_helper_obj = FSHelper(self.admin_console)
        self.cm_helper = CredentialManagerHelper(self.admin_console)

    def run(self):

        try:

            self.cm_helper.account_type = self.tcinputs['account_type']
            self.cm_helper.credential_name = self.tcinputs['credential_name']
            self.cm_helper.new_credential_name = self.cm_helper.credential_name
            self.cm_helper.credential_username = self.tcinputs['credential_username']
            self.cm_helper.credential_password = self.tcinputs['credential_password'] + "xyz"

            self.cm_helper.backupset_name = self.tcinputs["backupset_name"]
            self.cm_helper.subclient_name = self.tcinputs["subclient_name"]
            self.cm_helper.sc_content = self.tcinputs["subclient_content_path"].split(",")
            self.cm_helper.client = self.tcinputs["client"]
            self.cm_helper.plan = self.tcinputs["plan_name"]

            self.log.info("*********Adding a credential with wrong password, "
                          "editing if already present*********")
            if self.cm_helper.verify_cred_visibility():
                self.cm_helper.edit_credential(verify=False)
            else:
                self.cm_helper.add_credential(verify=False)

            self.log.info("*********Create subclient*********")
            self.cm_helper.create_subclient()

            self.log.info("*********Running backup with incorrect credentials*********")
            self.cm_helper.run_backup_with_invalid_cred()

            self.log.info("*********Editing credential to correct it*********")
            self.cm_helper.credential_password = self.tcinputs['credential_password']
            self.cm_helper.edit_credential(verify=False)
            self.cm_helper.resume_job_with_valid_cred()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:

            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
