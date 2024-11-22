# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import handle_testcase_exception
from Reports.utils import TestCaseUtils

from Automation.AutomationUtils.idautils import CommonUtils
from Automation.AutomationUtils.machine import Machine
from Automation.Install.install_helper import InstallHelper
from Automation.Server.JobManager.jobmanager_helper import JobManager
from cvpysdk.job import Job

from Automation.VirtualServer.VSAUtils import VsaTestCaseUtils


class TestCase(CVTestCase):
    """Class for testing push agent to perform guest file restores for vCloud"""

    def __init__(self):
        """" Initializes test case class objects"""""
        super(TestCase, self).__init__()
        self.name = "Project 1910 | Check Push Install Job"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.status_list = []

    def setup(self):
        decorative_log("Initalising Browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        decorative_log("Creating an object for Virtual Server helper")
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        self.vsa_obj.hypervisor = self.tcinputs['ClientName']
        self.vsa_obj.instance = self.tcinputs['InstanceName']
        self.vsa_obj.subclient = self.tcinputs['SubclientName']
        self.vsa_obj.cs_client = self.tcinputs['CSClient']
        self.vsa_obj.subclient_obj = self.subclient
        self.vsa_obj.testcase_obj = self
        self.ida_util = CommonUtils(self.commcell)
        dest_machine = Machine(machine_name=self.tcinputs['dest_machine'], commcell_object=self.commcell,username=self.tcinputs['dest_vm_creds']['username'], password=self.tcinputs['dest_vm_creds']['password'])
        self.install_helper = InstallHelper(commcell=self.commcell, machine_obj=dest_machine)
        self.vsa_obj.dest_vm_creds = self.tcinputs["dest_vm_creds"]
        self.vsa_obj.cs_creds = self.tcinputs["cs_creds"]
        self.log.info("Created VSA object successfully.")

    def _fail_or_skip(self, string, status):
        self.log.error('Error: %s', str(string))
        self.result_string = str(string)
        self.status = status

    def _individual_status(self, test_label, test_status="PASS", test_comments=" - "):
        self.status_list.append([test_label, test_status, test_comments])

    def _display_results(self):
        result_table = 'Test \t| Status \t| Comments\n'
        for test in self.status_list:
            result_table += '{} \t| {} \t| {} \n'.format(test[0], test[1], test[2])

        all_passed = all(i[1] == 'PASS' for i in self.status_list)

        if not all_passed:
            self._fail_or_skip(result_table, constants.FAILED)

        self.log.info('\n' + result_table)

    def run(self):
        """Main function for testcase execution"""
        try:
            decorative_log("Check for additional key: bRestoreViaCVTools")
            self.commcell.add_additional_setting(category='CommServe',
                                                 key_name='bRestoreViaCVTools',
                                                 data_type='BOOLEAN', value='True')

            decorative_log("Starting initialization Backup")
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.backup()
        except Exception as exp:
            handle_testcase_exception(self, exp)
            return

        try:
            decorative_log("Running Restore Tests")
            current_test = "Restore to VM without agent"
            self.log.info("Testing: {}".format(current_test))
            self.vsa_obj.guest_files_restore(restore_via_cv_tools=True, push_expected=True)
            self._individual_status(test_label=current_test)
        except Exception as exp:
            handle_testcase_exception(self, exp)

        try:
            current_test = "Restore to VM with agent"
            self.log.info("Testing: {}".format(current_test))
            self.vsa_obj.guest_files_restore(restore_via_cv_tools=True, push_expected=False)
            self._individual_status(test_label=current_test)
        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            Browser.close_silently(self.browser)

    def tear_down(self):
        try:
            if self.vsa_obj:
                self.vsa_obj.cleanup_testdata()
                self.vsa_obj.post_restore_clean_up(status= self.status)
        except Exception:
            self.log.warning("Testcase and/or Restored vm cleanup was not completed")

        try:
            decorative_log("Uninstalling agent from VM")
            self.install_helper.uninstall_client()
        except Exception:
            self.log.warning("Couldn't uninstall agent from VM during cleanup")
