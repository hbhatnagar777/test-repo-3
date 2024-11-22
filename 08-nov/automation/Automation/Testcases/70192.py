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
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type
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
        self.name = "VSA GCP VMGroups CRUD case"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vm_group_name = "TC_test_vmgroup_gcp"
        self.vmgroup_obj = None
        self.admin_console = None
        self.vsa_obj = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
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
            decorative_log("Adding vmgroup with content")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vmgroup_obj.add_vm_group(vm_group_name=self.vm_group_name,
                                          vm_content=self.tcinputs['BackupContent'],
                                          hypervisor_name=self.tcinputs['ClientName'],
                                          plan=self.tcinputs['Plan'],
                                          vendor=hypervisor_type.Google_Cloud.value,
                                          project=self.tcinputs['project'])
            decorative_log("Validating the VM group content with rules")

            self.admin_console.navigator.navigate_to_vm_groups()
            self.vsa_obj.validate_vmgroup(vmgroup_name=self.vm_group_name,
                                          validate_input={"vmgroup_name": self.vm_group_name,
                                                          "hypervisor_name": self.tcinputs['ClientName'],
                                                          "plan": self.tcinputs['Plan'],
                                                          "vm_group_content": self.tcinputs['BackupContent']})

            decorative_log("Edit vmgroup with content")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vmgroup_obj.set_vm_group_content(vendor=hypervisor_type.Google_Cloud.value,
                                                  vm_content=self.tcinputs['NewContent'],
                                                  remove_existing_content=True,
                                                  vm_group=self.vm_group_name,
                                                  project=self.tcinputs['project'])
            decorative_log("Validating vmgroup with instance search")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vsa_obj.validate_vmgroup(vmgroup_name=self.vm_group_name,
                                          validate_input={"vm_group_content": self.tcinputs['NewContent']})

            decorative_log("Adding vmgroup with rule")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vmgroup_obj.set_vm_group_content(vendor=hypervisor_type.Google_Cloud.value,
                                                  vm_content=self.tcinputs['ContentRule'],
                                                  remove_existing_content=True,
                                                  vm_group=self.vm_group_name)
            decorative_log("Validating vmgroup with rule")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vsa_obj.validate_vmgroup(vmgroup_name=self.vm_group_name,
                                          validate_input={"vm_group_content": self.tcinputs['ContentRule']},
                                          content_rule=True)

            # Delete the vmgroup
            decorative_log("Deleting vmgroup")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vmgroup_obj.action_delete_vm_groups(self.vm_group_name)

            # Validate whether vmgroup is deleted or not.
            decorative_log("checking for deleted vmgroup")
            self.admin_console.navigator.navigate_to_vm_groups()
            if not self.vmgroup_obj.has_vm_group(self.vm_group_name):
                self.log.info("VM group doesnt exist")
            else:
                self.log.error("VM group not deleted")
                raise Exception
        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            self.admin_console.navigator.navigate_to_vm_groups()
            if self.vmgroup_obj.has_vm_group(self.vm_group_name):
                self.vmgroup_obj.action_delete_vm_groups(self.vm_group_name)
            Browser.close_silently(self.browser)``