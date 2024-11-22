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

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from VirtualServer.VSAUtils import VirtualServerUtils
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Amazon snap backup & restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("AMAZON : V2:(Tenant Account) Snap Incremental backup and Full VM,File Level restore from Snap"
                     "and BackupCopy Automated")
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)

    def setup(self):

        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login object")
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
        self.vsa_obj.testcase_obj = self
        self.vsa_obj.auto_vsa_subclient = VirtualServerUtils.subclient_initialize(self)

    def run(self):
        """Main function for test case execution"""
        try:

            decorative_log("Running an Incremental backup")
            self.vsa_obj.backup_type = "INCR"
            self.vsa_obj.backup_method = "SNAP"
            self.vsa_obj.backup()

            try:
                decorative_log("Performing File Level Restore - (Backup Copy)")
                self.vsa_obj.snap_restore = False
                self.vsa_obj.file_level_restore()
            except Exception as exp:
                self.utils.handle_testcase_exception(exp)

            try:
                decorative_log("Performing File Level Restore - (Snap Copy)")
                self.vsa_obj.snap_restore = True
                self.vsa_obj.file_level_restore()
            except Exception as exp:
                self.utils.handle_testcase_exception(exp)

            try:
                decorative_log("Full VM Restore - (Backup Copy)")
                self.vsa_obj.snap_restore = False
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                self.utils.handle_testcase_exception(exp)

            try:
                decorative_log("Full VM Restore - (Snap Copy)")
                self.vsa_obj.snap_restore = True
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                self.utils.handle_testcase_exception(exp)

        except Exception as _exception:
            self.utils.handle_testcase_exception(_exception)

        finally:
            self.browser.close()

    def tear_down(self):
        decorative_log("Tear Down Started")
        status = False
        if self.status == constants.PASSED:
            status = True
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()
            self.vsa_obj.post_restore_clean_up(source_vm=True, status=status)
