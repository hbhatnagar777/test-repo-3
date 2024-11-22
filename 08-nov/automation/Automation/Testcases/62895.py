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

    setup()         --  setup function of this test case
    run()           --  run function of this test case
    tear_down()     --  tear down function of this test case
Inputs:
    ClientName          --      name of the client for backup
    StoragePoolName     --      backup location for disk storage
    SnapEngine          --      snap engine to set at values :
					            IBM  FlashCopy or
					            IBM Space-efficient FlashCopy
    SubclientContent    --      Data to be backed up
"""
import time
from AutomationUtils.cvtestcase import CVTestCase
from Web.AdminConsole.Helper.snaptemplate import SnapTemplate
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.adminconsole import AdminConsole


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""

    def __init__(self):
        """Initializing the Test case file"""
        super(TestCase, self).__init__()
        self.name = "Command Center: Backup copy and Modifying Server Plan to change Retention for Snap copy"
        self.browser = None
        self.snap_template = None
        self.navigator = None
        self.admin_console = None
        self.tcinputs = {
            "ClientName": None,
            "StoragePoolName": None,
            "SubclientContent": None,
            "SnapEngine": None
        }

    def run(self):
        """Main function for test case execution"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.snap_template = SnapTemplate(self, self.admin_console)
            self.snap_template.snaptemplate4()
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