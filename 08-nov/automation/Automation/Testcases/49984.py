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

import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants

from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of HyperV backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of HyperV Full Backup and Restore in " \
                    "AdminConsole"
        self.product = self.products_list.VIRTUALIZATIONHYPERV
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.tcinputs = {
            #   "AgentlessVM": None
        }

    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Started executing %s testcase", self.id)

            self.log.info("%(boundary)s %(message)s %(boundary)s",
                          {'boundary': "-" * 25, 'message': "Initialize browser objects"})
            factory = BrowserFactory()
            browser = factory.create_browser_object()
            browser.open()
            self.log.info("Creating the login object")
            admin_console = AdminConsole(browser, self.inputJSONnode['commcell']['webconsoleHostname'])
            admin_console.login()
            # login_obj = LoginMain(driver, self.csdb)
            #
            # login_obj.login(self.inputJSONnode['commcell']['commcellUsername'],
            #                 self.inputJSONnode['commcell']['commcellPassword']
            #                )

            self.log.info("Login completed successfully. Creating object for VSA")

            vsa_obj = AdminConsoleVirtualServer(self.instance, browser,
                                                self.commcell, self.csdb)
            vsa_obj.hypervisor = self.tcinputs['ClientName']
            vsa_obj.instance = self.tcinputs['InstanceName']
            vsa_obj.subclient = self.tcinputs['SubclientName']

            self.log.info("Created VSA object successfully. Now starting a backup")
            vsa_obj.backup_type = "INCR"
            vsa_obj.backup()
            # vsa_obj.vsa_discovery

            # ""

            try:
                # Restoring test data to a different VM
                self.log.info("%(boundary)s %(message)s %(boundary)s",
                              {'boundary': "-" * 25,
                               'message': "Restoring data to a agentless VM"})

                temp_dict = dict()
                vm_list = []
                for each_vm in vsa_obj.vms:
                    if "win" in vsa_obj.hvobj.VMs[each_vm].guest_os.lower():
                        continue
                    else:
                        vm_list.append(each_vm)
                        temp_dict[each_vm] = self.tcinputs.get("AgentlessWinVM", self.tcinputs.get("AgentlessVM"))

                vsa_obj._set_agentless_dict(temp_dict)
                vsa_obj._vms = vm_list
                vsa_obj.agentless_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)



        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            admin_console.logout()
            browser.close()
            time.sleep(200)
            if vsa_obj:
                vsa_obj.cleanup_testdata()
            if not self.test_individual_status:
                self.log.info("Testcase failed with error {0} :".format(self.test_individual_failure_message))
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
