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
from AutomationUtils import constants
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils.VirtualServerUtils import set_inputs, decorative_log, subclient_initialize
from VirtualServer.VSAUtils import OptionsHelper


class TestCase(CVTestCase):
    """Class for performing streaming and restore of encrypted Azure VM test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Encrypted Azure VM streaming backup and restore- FULL"
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
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        vsa_obj_inputs = {
            'hypervisor': self.tcinputs['ClientName'],
            'instance': self.tcinputs['InstanceName'],
            'subclient': self.tcinputs['SubclientName'],
            'storage_account': self.tcinputs.get('StorageAccount', None),
            'resource_group': self.tcinputs.get('ResourceGroup', None),
            'region': self.tcinputs.get('Region', None),
            'managed_vm': self.tcinputs.get('ManagedVM', False),
            'disk_type': self.tcinputs.get('DiskType', None),
            'backup_type': self.tcinputs.get('BackupType', "FULL"),
            'availability_zone': self.tcinputs.get('AvailabilityZone', "Auto"),
            'snapshot_rg': self.tcinputs.get('SnapshotRG', None),
            'subclient_obj': self.subclient,
            'testcase_obj': self
        }
        set_inputs(vsa_obj_inputs, self.vsa_obj)
        self.log.info("Created VSA object successfully.")

    def run(self):
        """Main function for test case execution"""

        try:
            decorative_log("Running backup")
            self.vsa_obj.backup()

            decorative_log("Running Full VM Out Of Place Restore")

            try:
                self.vsa_obj.unconditional_overwrite = True
                self.vsa_obj.full_vm_in_place = False
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            decorative_log("Running Full VM In-Place Restore")

            try:
                self.vsa_obj.unconditional_overwrite = True
                self.vsa_obj.full_vm_in_place = True
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED

    def tear_down(self):
        try:
            if self.vsa_obj:
                self.vsa_obj.cleanup_testdata()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
