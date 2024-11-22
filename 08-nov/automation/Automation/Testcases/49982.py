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

import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Reports.utils import TestCaseUtils
from VirtualServer.VSAUtils import VsaTestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of HyperV backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of HyperV Full Backup and Restore in " \
                    "AdminConsole along with Restore Workload Validation"
        self.product = self.products_list.VIRTUALIZATIONHYPERV
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.tc_utils = None

    def setup(self):
        try:
            decorative_log("Initializing browser objects")
            factory = BrowserFactory()
            self.browser = factory.create_browser_object()
            self.browser.open()

            decorative_log("Creating a login object")
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.log.info("Sleep for 60 seconds")
            time.sleep(60)
            self.log.info("Login successful")
            decorative_log("Creating an object for VSA")
            self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                     self.commcell, self.csdb)
            self.vsa_obj.hypervisor = self.tcinputs['ClientName']
            self.vsa_obj.instance = self.tcinputs['InstanceName']
            self.vsa_obj.subclient = self.tcinputs['SubclientName']
            self.vsa_obj.subclient_obj = self.subclient
            self.vsa_obj.unconditional_overwrite = True
            self.vsa_obj.validate_restore_workload = True
            self.vsa_obj.full_vm_in_place = False
            self.vsa_obj.restore_client = self.tcinputs['RestoreClient']
            self.restore_path = self.tcinputs['RestorePath']
            self.vsa_obj.restore_network = self.tcinputs['RestoreNetwork']
            self.vsa_obj.restore_host = self.tcinputs['RestoreHost']
            self.agentless_vm = self.tcinputs['AgentlessVM']
            self.vsa_obj.vm_restore_prefix = "del"
            self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                              self.products_list.VIRTUALIZATIONHYPERV,
                                                              self.features_list.DATAPROTECTION)
            self.vsa_obj.auto_subclient = self.tc_utils.initialize(self)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Created VSA object successfully.")
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.backup()

            try:
                # Restoring test data to the source VM in the source path
                self.vsa_obj.guest_files_restore(in_place=True)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                # Restoring test data to the source VM in a different path
                self.vsa_obj.guest_files_restore(in_place=False)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                # Restoring test data to a different VM
                self.vsa_obj.agentless_vm = self.agentless_vm
                self.vsa_obj.agentless_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                # Restoring test data to guest agent
                self.vsa_obj.file_level_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                # Restoring test data to the guest agent
                self.vsa_obj.virtual_machine_files_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            self.vsa_obj.restore_proxy = "Automatic"

            try:
                # Restoring the VM to hyper-v default folder
                self.vsa_obj.unconditional_overwrite = True
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
            finally:
                self.vsa_obj.post_restore_clean_up(False, True)

            try:
                # Restoring the VM to a different folder
                self.vsa_obj.restore_location = "Select a folder"
                self.vsa_obj.restore_path = self.restore_path
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
            finally:
                self.vsa_obj.post_restore_clean_up(False, True)


            try:
                # Restoring the VM in-place
                self.vsa_obj.full_vm_in_place = True
                self.vsa_obj.restore_client = None
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
            
            if not self.test_individual_status:
                raise Exception(self.test_individual_failure_message)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        try:
            if self.vsa_obj:
                self.vsa_obj.vm_restore_prefix = "del"
                self.vsa_obj.cleanup_testdata()

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
