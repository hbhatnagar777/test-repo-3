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

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from VirtualServer.VSAUtils.VirtualServerUtils import (
    set_inputs,
    decorative_log,
    subclient_initialize,
)
from VirtualServer.VSAUtils import OptionsHelper


class TestCase(CVTestCase):
    """Class for executing basic testcase for Backup and Restore for Xen in Command Center"""

    def __init__(self):
        """" Initializes test case class objects""" ""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of XenServer Full Backup and Restore in Command Center"
        self.product = self.products_list.VIRTUALIZATIONXEN
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.test_individual_status = True
        self.test_individual_failure_message = ""

    def run(self):
        """ "Main function for testcase execution"""
        try:
            self.log.info(f"Started executing {self.id} testcase")

            decorative_log("Initialize browser objects")

            factory = BrowserFactory()
            browser = factory.create_browser_object()
            browser.open(maximize=True)
            self.log.info("Creating the login object")
            admin_console = AdminConsole(browser, self.commcell.webconsole_hostname)
            admin_console.login(
                self.inputJSONnode["commcell"]["commcellUsername"],
                self.inputJSONnode["commcell"]["commcellPassword"],
            )

            self.log.info("Login completed successfully")
            vsa_obj = AdminConsoleVirtualServer(
                self.instance, browser, self.commcell, self.csdb
            )
            vsa_obj_inputs = {
                "testcase_obj": self,
                "subclient_obj": self.subclient,
                "auto_vsa_subclient": subclient_initialize(self),
                "hypervisor": self.tcinputs["ClientName"],
                "instance": self.tcinputs["InstanceName"],
                "subclient": self.tcinputs["SubclientName"],
                "xen_server": self.tcinputs["xen_server"],
                "storage": self.tcinputs["storage"],
                "network": self.tcinputs["network"]
            }

            set_inputs(vsa_obj_inputs, vsa_obj)

            self.log.info("Created VSA object successfully.")

            decorative_log("Backup")
            vsa_obj.backup_type = "FULL"
            vsa_obj.backup()

            try:
                decorative_log("Starting guest file restore")
                vsa_obj.unconditional_overwrite = True
                vsa_obj.file_level_restore()
            except Exception as exp:
                handle_testcase_exception(self, exp)

            try:
                decorative_log("Out of Place Full VM Restore")
                vsa_obj.unconditional_overwrite = True
                vsa_obj.full_vm_in_place = False
                vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            handle_testcase_exception(self, exp)
            self.log.error("Failed with error: %s", str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                browser.close()
                if vsa_obj: vsa_obj.cleanup_testdata()

            except:
                self.log.warning("Testcase and/or Restored VM cleanup was not completed")
                pass

            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
