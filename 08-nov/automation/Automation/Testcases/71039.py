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
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log, subclient_initialize
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Web.Common.page_object import handle_testcase_exception

class TestCase(CVTestCase):

    """Class for executing OCI agentless guest file restore case"""
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA OCI backup and  file level restore to windows and linux instance in AdminConsole"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)

    def setup(self):

        decorative_log("Initializing browser Objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating a login Object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance,
                                                 self.browser,
                                                 self.commcell, self.csdb)
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.subclient_obj = self.subclient
        self.vsa_obj.auto_vsa_subclient = subclient_initialize(self)
        self.vsa_obj.testcase_obj = self

    def run(self):
        """Main function for test case execution"""
        try:
            decorative_log("Running a backup")
            self.vsa_obj.backup_type = "INCR"
            self.vsa_obj.backup()

            try:
                decorative_log("Restoring data to linux agentless instance")
                self.vsa_obj.agentless_vm = self.tcinputs['AgentlessLinuxVM']
                self.vsa_obj.agentless_restore()
            except Exception as exp:
                self.log.exception('Failure in Case 1 : {}'.format(exp))
                handle_testcase_exception(self, exp)

            try:
                decorative_log("Restoring data to windows agentless instance")
                temp_dict = dict()
                vm_list = []
                for each_vm in self.vsa_obj.vms:
                    vm_list.append(each_vm)
                    temp_dict[each_vm] = self.tcinputs.get("AgentlessWinVM")
                self.vsa_obj._set_agentless_dict(temp_dict)
                self.vsa_obj._vms = vm_list
                self.vsa_obj.agentless_vm = self.tcinputs['AgentlessWinVM']
                self.vsa_obj.agentless_restore()
            except Exception as exp:
                self.log.exception('Failure in Case 2 : {}'.format(exp))
                handle_testcase_exception(self, exp)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()
