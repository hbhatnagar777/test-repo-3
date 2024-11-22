# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

Inputs:

    ClientName          --      name of the client for backup

    StoragePoolName     --      backup location for disk storage

    SnapEngine          --      snap engine to set at subclient
                                Values: 'INFINDAT'

    SubclientContent    --      Data to be backed up


Immutable snap lock for supported Engines

Steps:
1. add method to cleanup 3 days old plan/SPs
2. Create Plan (random name), subclient, create vault copy (based on replica type).
3. Verify we cannot enable immutable snap on jobs based retention.
4. modify retention on primary snap copy and Vault/Replica to 1 day.
5. enable immutable snap lock on Primary snap copy and Vault/Replica copy based on Support.
6. validate disable immutable snap lock on Primary snap copy and Vault/Replica copy.
7. Run steps to validate retention modification on immutable snap lock copies. (Increasing is allowed, decrease not allowed)
8. Run snap backup, backup copy and aux copy.
9. validate immutable snap flag is enabled on Job in a copy.
10. validate snap expiry time by calculatig the expiry time based on snap creation time and retention set on the copy.
11. validate snap delete operation on locked snap.
12. validate JOB delete operation on locked copy.
13. validate delete copy operation on locked copy.
14. validate delete plan operation of locked copy.

"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.snaptemplate import SnapTemplate


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.name = "Command Center: Acceptance Test for Immutable snapshot support on INFINIDAT"
        self.snapengine_list = ['INFINIDAT InfiniSnap']
        self.browser = None
        self.admin_console = None
        self.snap_template = None
        self.tcinputs = {
            "ClientName": None,
            "StoragePoolName": None,
            "SnapEngine": None,
            "SubclientContent": None
        }

    def run(self):
        """Main function for test case execution"""

        self.tcinputs['lock'] = True
        try:
            if self.tcinputs['SnapEngine'] not in self.snapengine_list:
                exp = "Snap Engine name not valid for this TC"
                raise Exception(exp)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.snap_template = SnapTemplate(self, self.admin_console)
            self.snap_template.snaptemplate6()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """To cleanup entities created during TC"""
        try:
            self.snap_template.cleanup()

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
