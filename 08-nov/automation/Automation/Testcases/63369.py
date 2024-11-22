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

    setup()         --  setup function of this test case

    tear_down()     --  tear down function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log, subclient_initialize
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory,Browser
from Web.Common.page_object import handle_testcase_exception

class TestCase(CVTestCase):
    """Class for executing VMWare Custom Attributes Automation Test Case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VMWare - Custom Attributes - Automation"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None

    def setup(self):
        """Setup function for test case execution"""
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
            decorative_log("Performing Full Backup")
            self.vsa_obj.backup_type = "FULL"
            self.vsa_obj.vsa_discovery()
            for vm in self.vsa_obj.hvobj.VMs:
                self.vsa_obj.hvobj.VMs[vm].get_custom_attributes()
            self.vsa_obj.run_discovery = False
            self.vsa_obj.backup()
            self.vsa_obj.unconditional_overwrite = True
            source_vm_list = list(self.vsa_obj.hvobj.VMs.keys())

            try:
                decorative_log('Case 1: Performing Full VM Restore without adding/removing Custom Attributes')
                self.vsa_obj.full_vm_restore()
                for vm_name in source_vm_list:
                    restore_vm_name = self.vsa_obj.vm_restore_prefix + vm_name
                    self.vsa_obj.hvobj.VMs = restore_vm_name
                    if not self.vsa_obj.hvobj.VMs[restore_vm_name].validate_custom_attributes(self.vsa_obj.hvobj.VMs[vm_name], \
                                                                                         self.vsa_obj.custom_attributes_to_add, self.vsa_obj.custom_attributes_to_remove):
                        self.test_individual_status = False
                        self.test_individual_failure_message = "Custom Attributes validation failed for Case 1"
                        break
            except Exception as exp:
                self.log.exception('Failure in Case 1 : {}'.format(exp))
                handle_testcase_exception(self, exp)

            try:
                self.vsa_obj.custom_attributes_to_add = self.tcinputs['custom_attributes_to_add']
                self.vsa_obj.custom_attributes_to_remove = self.tcinputs['custom_attributes_to_remove']
                decorative_log('Case 2: Adding Custom Attributes {} and Removing Custom Attributes {} to/from the VMs and performing validation.'\
                               .format(self.vsa_obj.custom_attributes_to_add, self.vsa_obj.custom_attributes_to_remove))
                self.vsa_obj.full_vm_restore()
                for vm_name in source_vm_list:
                    restore_vm_name = self.vsa_obj.vm_restore_prefix + vm_name
                    self.vsa_obj.hvobj.VMs = restore_vm_name
                    if not self.vsa_obj.hvobj.VMs[restore_vm_name].validate_custom_attributes(self.vsa_obj.hvobj.VMs[vm_name], \
                                                                                         self.vsa_obj.custom_attributes_to_add, self.vsa_obj.custom_attributes_to_remove):
                        if  self.test_individual_status:
                            self.test_individual_status = False
                            self.test_individual_failure_message = "Custom Attributes validation failed for Case 2"
                        break
            except Exception as exp:
                self.log.exception('Failure in Case 2 : {}'.format(exp))
                handle_testcase_exception(self, exp)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED

    def tear_down(self):
        try:
            if self.vsa_obj:
                self.vsa_obj.cleanup_testdata()
                self.vsa_obj.post_restore_clean_up(status=self.status)

        except Exception as exp:
            self.log.warning("Testcase and/or Restored vm cleanup was not completed : {}".format(exp))

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)