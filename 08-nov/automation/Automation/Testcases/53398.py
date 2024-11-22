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
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer


class TestCase(CVTestCase):
    """Class for executing Google Cloud Backup and restore"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Google Cloud Full Streaming Backup, Full VM Restore and Guest Files Restore"
        self.product = self.products_list.VIRTUALIZATIONGCCLOUD
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.tcinputs = {}

    def setup(self):

        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating the login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        decorative_log("Creating an object for Virtual Server helper")

        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.admin_console,
                                                 self.commcell, self.csdb)
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.restore_proxy = self.tcinputs['RestoreProxy']
        self.vsa_obj.subclient_obj = self.subclient

    def run(self):
        """Main function for test case execution"""
        try:
            decorative_log("Running a full VM backup")
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.backup()

            try:
                decorative_log("Running Guest files Restore")
                self.vsa_obj.unconditional_overwrite = True
                self.vsa_obj.guest_files_restore()

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message += str(exp)

            try:
                decorative_log("Running Full VM Restore")
                self.vsa_obj.full_vm_in_place = False
                self.vsa_obj.unconditional_overwrite = True
                self.vsa_obj.full_vm_restore()

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message += str(exp)

        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            self.browser.close()
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED

    def tear_down(self):
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()
            for _vm in self.vsa_obj._vms:
                decorative_log("Powering off backed up and restored instance")
                self.vsa_obj.restore_destination_client.VMs[_vm].power_off()
