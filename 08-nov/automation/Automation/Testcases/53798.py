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

    tear_down()      --  tears down the things created for running the testcase

"""

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import handle_testcase_exception
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log, subclient_initialize
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Ali Cloud backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Alibaba Cloud Full Backup and Restore in AdminConsole"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None

    def setup(self):
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)

        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                        self.inputJSONnode['commcell']['commcellPassword']
                        )

        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.subclient_obj = self.subclient
        self.vsa_obj.restore_proxy_input = None
        self.vsa_obj.auto_vsa_subclient = subclient_initialize(self)
        self.vsa_obj.testcase_obj = self

    def run(self):
        """Main function for test case execution"""

        try:
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.backup()

            try:
                decorative_log("Performing file level restore")
                self.vsa_obj.file_level_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                decorative_log("Performing full VM restore from subclient level")
                self.vsa_obj.unconditional_overwrite = True
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                handle_testcase_exception(self, exp)


            try:
                decorative_log("Performing full VM restore from subclient level to different availability domain")
                self.vsa_obj.restore_proxy_input = self.tcinputs['RestoreProxyName']
                self.vsa_obj.unconditional_overwrite = True
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                handle_testcase_exception(self, exp)

        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            Browser.close_silently(self.browser)

    def tear_down(self):
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()
