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
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from VirtualServer.VSAUtils import VirtualServerUtils
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log, set_inputs
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Attach disk restore to same instance from a backup copy with root volume filtered in admin account"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Attach volume to same instance with root volume filtered from backup copy in admin account"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "AvailabilityZone": None,
            "network": None
        }

    def setup(self):
        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        decorative_log("Browser object is created here")
        self.browser.open()
        decorative_log("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        vsa_obj_inputs = {
            'hypervisor': self.tcinputs['ClientName'],
            'instance': self.tcinputs['InstanceName'],
            'subclient': self.tcinputs['SubclientName'],
            'disks_to_be_attached': self.tcinputs.get('disks', []),
            'source': self.tcinputs['source'],
            'availability_zone': self.tcinputs['AvailabilityZone'],
            'network': self.tcinputs['network'],
        }
        self.vsa_obj.snap_restore = False
        self.vsa_obj.encryptionKey, self.vsa_obj.encryptionKeyArn = self.tcinputs['encryptionkey'].split("|")
        set_inputs(vsa_obj_inputs, self.vsa_obj)
        self.vsa_obj.subclient_obj = self.subclient
        self.vsa_obj.testcase_obj = self
        self.vsa_obj.auto_vsa_subclient = VirtualServerUtils.subclient_initialize(self)

    def run(self):
        """Main function for test case execution"""
        try:
            decorative_log("Running a backup--2nd phase")
            self.vsa_obj.backup_type = "full"
            self.vsa_obj.backup()
            decorative_log("Restoring the snap copy to the Existing Instance")
            self.vsa_obj.attach_disk_restore('My instance', False)
            decorative_log("Restoring the disk is completed")
        except Exception as _exception:
            self.utils.handle_testcase_exception(_exception)
        finally:
            Browser.close_silently(self.browser)

    def tear_down(self):
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()

