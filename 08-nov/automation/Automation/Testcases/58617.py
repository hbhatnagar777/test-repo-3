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
from Web.Common.page_object import handle_testcase_exception
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic Acceptance Test of VMware Cloud Director backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VMware Cloud Director Full Backup and Restore of Organization hypervisor VMs as Tenant Admin"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "VcloudVdc": None,
            "ACUsername": None,
            "ACPassword": None
        }

    def setup(self):
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.tcinputs['ACUsername'], self.tcinputs['ACPassword'])

        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.restore_proxy = self.tcinputs['restore_proxy']
        self.vsa_obj.subclient_obj = self.subclient
        self.vsa_obj.testcase_obj = self
        self.vsa_obj.organization = self.tcinputs.get('VcloudOrganization', None)
        self.vsa_obj.org_vdc = self.tcinputs['VcloudVdc']
        VS_Utils.set_inputs(self.tcinputs, self.vsa_obj)
        self.log.info("Created VSA object successfully.")

    def run(self):
        """Main function for test case execution"""

        try:
            self.vsa_obj.backup_type = "Full"
            self.vsa_obj.backup()

            try:
                decorative_log("Performing file level restore to source VM from organization hypervisor")
                self.vsa_obj.guest_files_restore(in_place=True)
            except Exception as exp:
                handle_testcase_exception(self, exp)

            try:
                decorative_log("Performing Full VM Out of Place restore from organization hypervisor")
                self.vsa_obj.full_vm_in_place = False
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                handle_testcase_exception(self, exp)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        try:
            self.vsa_obj.cleanup_testdata()
            self.vsa_obj.post_restore_clean_up(status=self.status)
        except Exception as exp:
            self.log.exception(exp)
            self.log.warning("Testcase and/or Restored vm cleanup was not completed")
