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
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log
import VirtualServer.VSAUtils.VirtualServerUtils as VS_Utils
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from Web.AdminConsole.adminconsole import AdminConsole
from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMware backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Full VM restores as Tenant admin in Hybrid mode"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.browser = None
        self.vsa_obj = None
        self.admin_console = None
        self.utils = TestCaseUtils(self)
        self.tcinputs = {
            "ACUsername": None,
            "ACPassword": None,
            "CompanyName": None,
            "CompanyHypervisor": None,
            "CompanyVMGroup": None
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
        self.vsa_obj.testcase_obj = self
        VS_Utils.set_inputs(self.tcinputs, self.vsa_obj)

    def run(self):
        """Main function for test case execution"""

        try:

            # Verify if the input hypervisor and VM group VMs belong to commcell
            commcell_hypervisor_company = self.client.company_name
            if commcell_hypervisor_company.lower() != "commcell":
                raise Exception(
                    f"Hypervisor [{self.tcinputs['ClientName']}] doesn't belong to Company "
                    f"[Commcell], instead belongs to [{commcell_hypervisor_company}]")

            for _vm in self.vsa_obj.auto_vsa_subclient.vm_list:
                _vm_company = self.commcell.clients.get(_vm).company_name
                if _vm_company.lower() != "commcell":
                    raise Exception(
                        f"VM [{_vm}] doesn't belong to Company [Commcell], instead belongs to [{_vm_company}]")

            decorative_log("Performing backup/restore for Commcell VMs")

            self.vsa_obj.backup_type = "INCR"
            self.vsa_obj.backup()

            self.admin_console.logout()
            self.admin_console.login(self.tcinputs['ACUsername'], self.tcinputs['ACPassword'])

            try:
                decorative_log("Restoring the VM Out-of-place")
                self.vsa_obj.unconditional_overwrite = True
                self.vsa_obj.restore_client = self.tcinputs['CompanyHypervisor']
                self.vsa_obj.full_vm_restore(vm_level=True)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                decorative_log("Restoring the VM In-place")
                self.vsa_obj.full_vm_in_place = True
                self.vsa_obj.unconditional_overwrite = True
                self.vsa_obj.end_user_full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            decorative_log("Performing backup/restore for Company VMs")

            self.tcinputs['ClientName'] = self.vsa_obj.hypervisor = self.tcinputs['CompanyHypervisor']
            self.tcinputs['SubclientName'] = self.vsa_obj.subclient = self.tcinputs['CompanyVMGroup']
            self.vsa_obj.auto_vsa_subclient = None
            self.reinitialize_testcase_info()
            self.vsa_obj._client = self.client
            self.vsa_obj._agent = self.agent
            self.vsa_obj.instance_obj = self.instance
            self.vsa_obj._backupset = self.backupset
            self.vsa_obj.subclient_obj = self.subclient
            self.vsa_obj.auto_vsa_subclient = None

            # Verify if the input tenant hypervisor and VM group VMs belong to the company
            tenant_hypervisor_company = self.commcell.clients.get(self.tcinputs['CompanyHypervisor']).company_name
            if tenant_hypervisor_company.lower() != self.tcinputs['CompanyName'].lower():
                raise Exception(
                    f"Hypervisor [{self.tcinputs['CompanyHypervisor']}] doesn't belong to Company "
                    f"[{self.tcinputs['CompanyName']}], instead belongs to [{tenant_hypervisor_company}]")

            for _vm in self.vsa_obj.auto_vsa_subclient.vm_list:
                _vm_company = self.commcell.clients.get(_vm).company_name
                if _vm_company.lower() != self.tcinputs['CompanyName'].lower():
                    raise Exception(
                        f"VM [{_vm}] doesn't belong to Company [{self.tcinputs['CompanyName'].lower()}], "
                        f"instead belongs to [{_vm_company}]")

            self.vsa_obj.backup()

            try:
                decorative_log("Restoring the VM Out-of-place")
                self.vsa_obj.unconditional_overwrite = True
                self.vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                decorative_log("Restoring the VM In-place")
                self.vsa_obj.full_vm_in_place = True
                self.vsa_obj.full_vm_restore(vm_level=True)
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED

    def tear_down(self):
        try:
            if self.vsa_obj:
                self.vsa_obj.cleanup_testdata()
                self.vsa_obj.post_restore_clean_up(status=self.test_individual_status)

        except Exception as exp:
            self.log.warning("Testcase and/or Restored vm cleanup was not completed : {}".format(exp))

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
