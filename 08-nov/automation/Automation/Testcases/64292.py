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
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils.VirtualServerUtils import set_inputs, decorative_log, subclient_initialize, create_adminconsole_object

class TestCase(CVTestCase):
    """CommandCenter v2 - Azure- Snap- Full"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Azure Snap & Backup copy - Full backup using Restore points"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
        }

    def setup(self):
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        decorative_log("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.admin_console.close_popup()
        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = create_adminconsole_object(self)
        self.utils.copy_config_options(self.vsa_obj, "RestoreOptions")

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Created VSA object successfully.")
            decorative_log("Running Incremental snap backup")
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.backup_method = "SNAP"
            self.vsa_obj.backup()
            self.vsa_obj.unconditional_overwrite = True

            try:
                # Full VM out of place restore
                self.vsa_obj.full_vm_in_place = False
                self.vsa_obj.full_vm_restore()

            except Exception as exp:
                self.utils.handle_testcase_exception(exp)

            try:
                # Guest File restore
                decorative_log("Starting guest file restore")
                self.vsa_obj.file_level_restore()
            except Exception as exp:
                self.utils.handle_testcase_exception(exp)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()
