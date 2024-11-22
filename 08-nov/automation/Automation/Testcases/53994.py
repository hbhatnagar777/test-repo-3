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
from Web.AdminConsole.Helper.LoginHelper import LoginMain
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Amazon backup & Attach disk restore to new new instance test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of Amazon backup & Attach disk restore in AdminConsole"
        self.product = self.products_list.VIRTUALIZATIONAMAZON
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.test_individual_status = True
        self.test_individual_failure_message = ""

    def setup(self):

        decorative_log("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating the login object")
        login_obj = LoginMain(self.browser.driver, self.csdb)

        login_obj.login(self.inputJSONnode['commcell']['commcellUsername'],
                        self.inputJSONnode['commcell']['commcellPassword']
                        )

        decorative_log("Creating an object for Virtual Server helper")

        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser.driver,
                                            self.commcell, self.csdb)
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.subclient_obj = self.subclient
    def run(self):
        """Main function for test case execution"""
        try:

            decorative_log("Running a backup")
            self.vsa_obj.backup_type = "INCR"
            self.vsa_obj.backup()

            try:
                decorative_log("Attach Disk Restore to a new instance")
                self.vsa_obj.ami = self.tcinputs['AMI']
                self.vsa_obj.attach_disk_restore('New instance')
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
                decorative_log("Deleting Restored instance")
                restored_vm = self.vsa_obj.vm_restore_prefix+_vm
                self.vsa_obj.restore_destination_client.VMs[restored_vm].delete_vm()
