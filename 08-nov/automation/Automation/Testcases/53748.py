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

    run()           --  run function of this test case
"""
from Automation.Web.Common.page_object import handle_testcase_exception
from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory, Browser
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "v2 VSA Fusion Compute FULL Backup and Restore Cases"
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        
    def setup(self):
        decorative_log("Initialising Browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.subclient_obj = self.subclient
        self.unconditional_overwrite = True
        self.vsa_obj.testcase_obj = self
        self.log.info("Created VSA object successfully.")

    def run(self):
        """Main function for test case execution"""

        try:
            decorative_log("Starting Backup")
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.backup()

            try:
                decorative_log("Performing file level restore")
                self.vsa_obj.file_level_restore()
            except Exception as exp:
                handle_testcase_exception(self, exp)
            
            try:
                decorative_log("Performing OOP Full VM Restore")
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                handle_testcase_exception(self, exp)
                
        except Exception as exp:
            handle_testcase_exception(self, exp)    
        finally:
            Browser.close_silently(self.browser)
    
    def tear_down(self):
        try:
            self.vsa_obj.cleanup_testdata()
            self.vsa_obj.post_restore_clean_up(status = self.status)
        except Exception:
            self.log.warning("Testcase and/or Restored VM clean up failed")