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

        setup()         --  sets up the variables required for running the testcase

        run()           --  run function of this test case

        teardown()      --  tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Helper.credential_manager_helper import CredentialManagerHelper
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.snaptemplate import SnapTemplate


class TestCase(CVTestCase):
    """Class for executing Acceptance test case for Add/Edit/Delete and validate Credential Manager
    for Storage Array Account by running Acceptance case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Command Center: Intellisnap Feature: Credential Manager"

        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.credential_manager_helper = None
        self.snap_template = None
        self.navigator = None
        self.tcinputs = {
            "AccountType": None,
            "CredentialName": None,
            "Username": None,
            "Password": None,
            "ClientName": None,
            "RestorePath": None,
            "SnapEngine": None,
            "StoragePoolName": None,
            "SubclientContent": None,
            "ArrayVendor": None,
            "ArrayName": None,
            "ControlHost": None,
            "Controllers": None


        }

    def setup(self):

        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.navigator = self.admin_console.navigator
        self.cred_helper_obj = CredentialManagerHelper(self.admin_console)
        self.snap_template_obj = SnapTemplate(self, self.admin_console)
        self.cred_helper_obj.account_type = self.tcinputs['AccountType']
        self.cred_helper_obj.credential_name = self.tcinputs['CredentialName']
        self.cred_helper_obj.new_credential_name = self.tcinputs.get('NewCredentialName', None)
        self.cred_helper_obj.credential_username = self.tcinputs['Username']
        self.cred_helper_obj.credential_password = self.tcinputs['Password']
        self.snap_template_obj.client_name = self.tcinputs['ClientName']
        self.snap_template_obj.restore_path = self.tcinputs['RestorePath']
        self.snap_template_obj.snap_engine = self.tcinputs['SnapEngine']
        self.snap_template_obj.storage_pool_name = self.tcinputs['StoragePoolName']
        self.snap_template_obj.subclient_content = self.tcinputs['SubclientContent']
        self.snap_template_obj.array_vendor = self.tcinputs['ArrayVendor']
        self.snap_template_obj.array_name = self.tcinputs['ArrayName']
        self.snap_template_obj.control_host = self.tcinputs['ControlHost']
        self.snap_template_obj.controllers = self.tcinputs['Controllers']
        self.snap_template_obj.array_password = self.tcinputs.get('ArrayPassword', None)
        self.snap_template_obj.array_user = self.tcinputs.get('ArrayUser', None)
        self.credentials = True

    def run(self):
        """Main function for test case execution"""

        try:

            self.cred_helper_obj.add_credential()
            self.snap_template_obj.snaptemplate4()
            self.cred_helper_obj.edit_credential()
            self.cred_helper_obj.delete_credential()


        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):

        try:
            self.snap_template_obj.cleanup()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
