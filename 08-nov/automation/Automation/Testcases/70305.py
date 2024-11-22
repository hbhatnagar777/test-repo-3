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
                                Values: 'NetApp'

    SubclientContent    --      Data to be backed up


Compliance Lock - Snap

Steps:
1. add method to cleanup 3 days old plan/SPs
2. Create Plan (random name), subclient, create vault copy (based on replica type).
3. modify retention on primary snap copy and primary copy to 1 day.
4. enable compliance lock on Primary snap copy and primary copy.
5. validate disable compliance lock on Primary snap copy and primary copy.
6. validate changing retention type on compliance lock snap copy is not allowed (days to Job based and vice versa)
7. Run steps to validate retention modification on compliance lock copies. (Increasing is allowed, decrease not allowed)
8. Run snap backup, backup copy and aux copy.
9. validate snap delete operation on locked snap.
10. validate JOB delete operation on locked copy.
11. validate delete copy operation on locked copy.
12. validate delete plan operation of locked copy.

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
        self.name = "Command Center: Acceptance Test case and Validations for Compliance lock on Snap copies"
        self.snapengine_list = ['NetApp']
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
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.snap_template = SnapTemplate(self, self.admin_console)
            self.snap_template.snaptemplate5()

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
