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
from Reports.utils import TestCaseUtils
from Web.AdminConsole.VSAPages.vm_groups import VMGroups

from Automation.VirtualServer.VSAUtils.VirtualServerConstants import HypervisorDisplayName
from Web.Common.page_object import handle_testcase_exception

from cvpysdk.subclient import Subclients

class TestCase(CVTestCase):
    """Test case for performing CRUD on VMware Cloud director VM Groups. """

    def __init__(self):
        """ Initializes test case class objects"""
        super(TestCase, self).__init__()
        self.name = "VMware Cloud director VM group CRUD "
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.vm_group_name = 'vm_group_63973_A_Del'
        self.browser = None
        self.vsa_obj = None
        self.vmgroup_obj = None
        self.admin_console = None
        self.hypervisor_details_obj = None
        self.hypervisor_ac_obj = None
        self.utils = TestCaseUtils(self)

    def setup(self):
        decorative_log("Initalising Browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        decorative_log("Creating login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        self.vmgroup_obj = VMGroups(self.admin_console)

    def run(self):
        """Main function for testcase execution"""
        try:
            self.admin_console.navigator.navigate_to_vm_groups()
            decorative_log("Adding VM Group")

            # Create
            self.vmgroup_obj.add_vm_group(vm_group_name=self.vm_group_name,
                                          vm_content=self.tcinputs['VMContent'],
                                          hypervisor_name=self.tcinputs['ClientName'],
                                          plan=self.tcinputs['Plan'],
                                          vendor=HypervisorDisplayName.Vcloud.value)

            # Read/Validate VM Group details

            vm_list = [vm.split("/")[-1] for vm in self.tcinputs['VMContent']['Content']]

            input_details = {
                "vmgroup_name": self.vm_group_name,
                "hypervisor_name": self.tcinputs['ClientName'],
                "plan": self.tcinputs['Plan'],
                "vm_group_content": vm_list
            }

            decorative_log("Validating VM Group")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vsa_obj.validate_vmgroup(vmgroup_name=self.vm_group_name, validate_input=input_details)


            # Delete VM Group

            decorative_log("Deleting VM Group {}".format(self.vm_group_name))
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vmgroup_obj.action_delete_vm_groups(self.vm_group_name)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            Browser.close(self.browser)

    def tear_down(self):

        try:
            decorative_log("Deleting VM Group {}".format(self.vm_group_name))
            subclient_obj = Subclients(self.commcell)
            subclient_obj.delete(self.vm_group_name)
        except Exception as exp:
            self.log.info("Unable to delete VM Group, it might already be deleted. - " + str(exp))