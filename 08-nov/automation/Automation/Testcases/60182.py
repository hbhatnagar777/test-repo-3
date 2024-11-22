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


Two sets of Inputs:

    ClientName          --      name of the client for backup

    StoragePoolName     --      backup location for disk storage

    SnapEngine          --      Netapp snap engine

    SubclientContent    --      Data to be backed up

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
        self.name = "Command Center: Multi-Site Snap Acceptance Test for NetApp"
        self.snapengine_list = ['NetApp']

        self.browser = None
        self.admin_console = None
        self.snap_template = None
        self.tcinputs = {
            "ClientName": None,
            "StoragePoolName": None,
            "SnapEngine": None,
            "SubclientContent": None,
            "ClientName_2": None,
            "StoragePoolName_2": None,
            "SnapEngine_2": None,
            "SubclientContent_2": None
        }

    def run(self):
        """Main function for test case execution"""
        multisite = True

        try:
            if self.tcinputs['SnapEngine'] not in self.snapengine_list:
                exp = "Snap Engine name not valid for this TC"
                raise Exception(exp)
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.snap_template = SnapTemplate(self, self.admin_console, self.csdb)
            self.snap_template.multisite = True
            self.snap_template.snaptemplate1()
            self.snap_template.client_name = self.tcinputs['ClientName_2']
            self.snap_template.storagepool_name = self.tcinputs['StoragePoolName_2']
            self.snap_template.snap_engine = self.tcinputs['SnapEngine_2']
            self.snap_template.subclient_content = self.tcinputs['SubclientContent_2']
            if multisite == 1:
                self.snap_template.snaptemplate1()



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
