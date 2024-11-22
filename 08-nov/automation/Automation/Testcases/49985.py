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

from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of HyperV backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of HyperV SYNTH Backup and Restore in " \
                    "AdminConsole"
        self.product = self.products_list.VIRTUALIZATIONHYPERV
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.tcinputs = {
         #   "AgentlessVM": None
        }

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)

            self.log.info("%(boundary)s %(message)s %(boundary)s",
                          {'boundary': "-" * 25, 'message': "Initialize browser objects"})
            factory = BrowserFactory()
            browser = factory.create_browser_object()
            browser.open()
            self.log.info("Creating the login object")
            admin_console = AdminConsole(browser, self.inputJSONnode['commcell']['webconsoleHostname'])
            admin_console.login()
            # login_obj = LoginMain(driver, self.csdb)
            #
            # login_obj.login(self.inputJSONnode['commcell']['commcellUsername'],
            #                 self.inputJSONnode['commcell']['commcellPassword']
            #                )

            self.log.info("Login completed successfully. Creating object for VSA")

            vsa_obj = AdminConsoleVirtualServer(self.instance, browser,
                                                self.commcell, self.csdb)
            vsa_obj.hypervisor = self.tcinputs['ClientName']
            vsa_obj.instance = self.tcinputs['InstanceName']
            vsa_obj.subclient = self.tcinputs['SubclientName']

            self.log.info("Created VSA object successfully. Now starting a backup")
            vsa_obj.backup_type = "SYNTH"
            vsa_obj.backup()

            try:
                # Restoring test data to the source VM in the source path
                self.log.info("%(boundary)s %(message)s %(boundary)s",
                              {'boundary': "-" * 25,
                               'message': "Restoring data to source VM in source path"})
                vsa_obj.guest_files_restore(in_place=True)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                # Restoring test data to the source VM in a different path
                self.log.info("%(boundary)s %(message)s %(boundary)s",
                              {'boundary': "-" * 25,
                               'message': "Restoring data to source VM to different path"})
                vsa_obj.guest_files_restore(in_place=False)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                # Restoring test data to a different VM
                self.log.info("%(boundary)s %(message)s %(boundary)s",
                              {'boundary': "-" * 25,
                               'message': "Restoring data to a agentless VM"})
                vsa_obj.agentless_vm = self.tcinputs['AgentlessVM']
                vsa_obj.agentless_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                # Restoring test data to guest agent
                vsa_obj.file_level_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                # Restoring test data to the guest agent
                vsa_obj.virtual_machine_files_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                # Restoring the VM to hyper-v default folder
                self.log.info("%(boundary)s %(message)s %(boundary)s",
                              {'boundary': "-" * 25,
                               'message': "Restoring the VM to hyper-v default folder"})
                vsa_obj.unconditional_overwrite = True
                vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                # Restoring the VM to a different folder
                self.log.info("%(boundary)s %(message)s %(boundary)s",
                              {'boundary': "-" * 25,
                               'message': "Restoring the VM to a different folder"})
                vsa_obj.restore_location = "Select a folder"
                vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                # Restoring the VM in-place
                self.log.info("%(boundary)s %(message)s %(boundary)s",
                              {'boundary': "-" * 25,
                               'message': "Restoring the VM in-place"})
                vsa_obj.full_vm_in_place = True
                vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            browser.close()
            if vsa_obj:
                vsa_obj.cleanup_testdata()
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
