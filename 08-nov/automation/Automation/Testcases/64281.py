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
from VirtualServer.VSAUtils.VirtualServerConstants import HypervisorDisplayName
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Web.AdminConsole.VSAPages.vm_groups import VMGroups
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing VMGroups CRUD case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Nutanix VMGroups CRUD test"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vm_group_name = "AHV_VMGROUP_TEST"
        self.vmgroup_obj = None
        self.admin_console = None
        self.vsa_obj = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "vm_content": None,
            "Plan": None,
            "vm_content1": None
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
        self.vsa_obj = AdminConsoleVirtualServer(self.instance, self.browser,
                                                 self.commcell, self.csdb)
        self.vmgroup_obj = VMGroups(self.admin_console)

    def run(self):
        try:
            decorative_log("Adding vmgroup content: ".format(self.tcinputs['vm_content']))
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vmgroup_obj.add_vm_group(vm_group_name=self.vm_group_name,
                                          vm_content=self.tcinputs['vm_content'],
                                          hypervisor_name=self.tcinputs['ClientName'],
                                          plan=self.tcinputs['Plan'],
                                          vendor=HypervisorDisplayName.Nutanix.value)

            decorative_log("Validating the VM group content")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vsa_obj.validate_vmgroup(vmgroup_name=self.vm_group_name,
                                          validate_input={"vmgroup_name": self.vm_group_name,
                                                          "hypervisor_name": self.tcinputs['ClientName'],
                                                          "plan": self.tcinputs['Plan'],
                                                          "vm_group_content": self.tcinputs['vm_content']})

            decorative_log("Adding vmgroup with vm inventory search")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vmgroup_obj.set_vm_group_content(vendor=HypervisorDisplayName.Nutanix.value,
                                                  vm_content=self.tcinputs['vm_content1'],
                                                  remove_existing_content=True,
                                                  vm_group=self.vm_group_name)

            decorative_log("Validating vmgroup with vm inventory search")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vsa_obj.validate_vmgroup(vmgroup_name=self.vm_group_name,
                                          validate_input={"vm_group_content": self.tcinputs['vm_content1']})

            # Delete the vmgroup
            decorative_log("Deleting vmgroup")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vmgroup_obj.action_delete_vm_groups(self.vm_group_name)

            # Validate whether vmgroup got deleted or not.
            decorative_log("checking for deleted vmgroup")
            self.admin_console.navigator.navigate_to_vm_groups()
            if not self.vmgroup_obj.has_vm_group(self.vm_group_name):
                self.log.info("VM group doesnt exist")
                pass
            else:
                self.log.error("VM group not deleted")
                raise Exception
        except Exception as exp:
            self.test_individual_status = False
            self.test_individual_failure_message = str(exp)
            handle_testcase_exception(self, exp)

        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

