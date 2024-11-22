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

    run()           --  run function of this test case

    setup()         --  setup function of this test case

    tear_down()     --  tear down function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log, subclient_initialize
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory,Browser
from Web.Common.page_object import handle_testcase_exception

class TestCase(CVTestCase):
    """Class for executing OCI Full Backup and Restore case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "OCI - Tag Additon During Restore and Validation post restore"
        self.test_individual_status = True
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None

    def setup(self):
        """Setup function for test case execution"""
        decorative_log("Initializing browser Objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login Object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance,
                                                 self.browser,
                                                 self.commcell, self.csdb)
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.subclient_obj = self.subclient
        self.vsa_obj.auto_vsa_subclient = subclient_initialize(self)
        self.vsa_obj.testcase_obj = self

    def run(self):
        """Main function for test case execution"""
        try:
            decorative_log("Performing Full Backup")
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.backup()

            try:
                decorative_log(
                    'Case 1: Adding new tags {} to the restored VM and performing validation of both new tags and existing tags'.format(self.vsa_obj.tags))
                self.vsa_obj.restore_validation_options = {'tags': self.vsa_obj.tags} 
                self.vsa_obj.tags = self.tcinputs['tags']
                self.vsa_obj.unconditional_overwrite = True
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                handle_testcase_exception(self, exp)
                self.result_string = "Failure in Case 1: " + self.result_string
        except Exception as exp:
            handle_testcase_exception(self, exp)
            self.result_string = "Failure in Full Backup: " + self.result_string

    def tear_down(self):
        try:
            if self.vsa_obj:
                self.vsa_obj.cleanup_testdata()
                self.vsa_obj.post_restore_clean_up(status=self.status)
        except Exception as exp:
            self.log.warning("Testcase and/or Restored vm cleanup was not completed : {}".format(exp))
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)