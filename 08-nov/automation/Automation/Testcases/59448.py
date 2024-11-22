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
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils
from Web.AdminConsole.VSAPages.vm_groups import VMGroups


class TestCase(CVTestCase):
    """Class for executing AWS VMGroup CRUD case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "AWS Add subclient content using Tags and validating with the VMs " \
                    "in AWS through preview operation - Command Center UI"
        self.browser = None
        self.vm_group_name = "AWS_TAG_TEST"
        self.vmgroup_obj = None
        self.admin_console = None
        self.vsa_obj = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "ContentRule": None,
            "Plan": None,
            "BackupContent": None,
            "ContentRuleVMs": None
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
            no_of_rules = len(self.tcinputs['ContentRule']['Rule'])
            if no_of_rules < 4:
                raise Exception("Number of rules less than 4, Please add atleast 4 Rules")
            decorative_log("Adding vmgroup with rules: ".format(self.tcinputs['ContentRule']))
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vmgroup_obj.add_vm_group(vm_group_name=self.vm_group_name,
                                          vm_content=self.tcinputs['ContentRule'],
                                          hypervisor_name=self.tcinputs['ClientName'],
                                          plan=self.tcinputs['Plan'],
                                          vendor=self.tcinputs['InstanceName'])

            decorative_log("Validating the VM group content with rules")
            self.admin_console.navigator.navigate_to_vm_groups()
            self.vsa_obj.validate_vmgroup(vmgroup_name=self.vm_group_name,
                                          validate_input={"vmgroup_name": self.vm_group_name,
                                                          "hypervisor_name": self.tcinputs['ClientName'],
                                                          "plan": self.tcinputs['Plan'],
                                                          "vm_group_content": self.tcinputs['ContentRuleVMs']})
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
            self.utils.handle_testcase_exception(self, exp)

        finally:
            self.browser.close()

    def tear_down(self):

        if self.vsa_obj:
            self.vsa_obj.cleanup_testdata()

