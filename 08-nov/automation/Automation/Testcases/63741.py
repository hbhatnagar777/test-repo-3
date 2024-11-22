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
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils import VirtualServerUtils


class TestCase(CVTestCase):

    """Class for executing Basic Acceptance Test for VMware Cloud Director to Vmware Full VM Conversion Restores"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "vCloud Director to VMware | Full VM Conversion Restore | FULL"
        self.browser = None
        self.vsa_obj = None
        self.vsa_obj_vmw = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "Destination_Virtualization_client": None
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

        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = VirtualServerUtils.create_adminconsole_object(self)
        self.vsa_obj.restore_client = self.tcinputs["Destination_Virtualization_client"]

    def run(self):

        """Main function for test case execution"""

        try:
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.backup()

            try:
                self.vsa_obj_vmw = VirtualServerUtils.create_adminconsole_object(self, is_destination_client=True)
                self.vsa_obj.full_vm_conversion_restore(self.vsa_obj_vmw)
            except Exception as exp:
                self.utils.handle_testcase_exception(exp)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            Browser.close_silently(self.browser)

    def tear_down(self):
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()
        if self.vsa_obj_vmw:
            self.vsa_obj_vmw.post_conversion_clean_up(status=self.status)



