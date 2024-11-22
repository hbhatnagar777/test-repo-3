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
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Amazon backup & file level restore to windows
    instance test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Amazon backup &  file level restore to windows instance in AdminConsole"

        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "AgentlessVM": None
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
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
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
            self.vsa_obj.backup_method = "snap"
            self.vsa_obj.backup()

            try:
                decorative_log("Restoring data to source instance")
                self.vsa_obj.guest_files_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message += str(exp)

            try:
                decorative_log("Restoring data to Agentless Windows VM ")
                self.vsa_obj.agentless_vm = self.tcinputs['AgentlessVM']
                self.vsa_obj.agentless_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message += str(exp)

            try:
                decorative_log("Restoring data to guest agent")
                self.vsa_obj.file_level_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message += str(exp)

            try:
                decorative_log("Restoring data to guest agent - snap")
                self.vsa_obj.snap_restore = True
                self.vsa_obj.file_level_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message += str(exp)
            try:
                decorative_log("Restoring data to source instance -snap")
                self.vsa_obj.guest_files_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message += str(exp)

            try:
                decorative_log("Restoring data to Agentless Windows VM - snap")
                self.vsa_obj.agentless_restore()
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
