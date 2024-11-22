# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information
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
from Web.Common.cvbrowser import BrowserFactory
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
from VirtualServer.VSAUtils.VirtualServerUtils import set_inputs, decorative_log, subclient_initialize
from VirtualServer.VSAUtils import OptionsHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of AzureRM incremental backup and Restore
     in AdminConsole"""""

    def __init__(self):
        """" Initializes test case class objects"""""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test of Azure RM incremental Backup and Restore in AdminConsole"
        self.product = self.products_list.VIRTUALIZATIONAZURE
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.test_individual_status = True
        self.test_individual_failure_message = ""

    def run(self):
        """"Main function for testcase execution"""
        try:
            self.log.info("Started executing %s testcase", self.id)

            decorative_log("Initialize browser objects")

            factory = BrowserFactory()
            browser = factory.create_browser_object()
            browser.open(maximize=True)

            admin_console = AdminConsole(browser, self.commcell.webconsole_hostname)
            admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                self.inputJSONnode['commcell']['commcellPassword'])
            self.log.info("Login completed successfully")

            vsa_obj = AdminConsoleVirtualServer(self.instance, browser,
                                                self.commcell, self.csdb)
            vsa_obj_inputs = {
                'hypervisor': self.tcinputs['ClientName'],
                'instance': self.tcinputs['InstanceName'],
                'subclient': self.tcinputs['SubclientName'],
                'storage_account': self.tcinputs.get('StorageAccount', None),
                'resource_group': self.tcinputs.get('ResourceGroup', None),
                'region': self.tcinputs.get('Region', None),
                'managed_vm': self.tcinputs.get('ManagedVM', False),
                'disk_type': self.tcinputs.get('DiskType', None),
                'availability_zone': self.tcinputs.get('AvailabilityZone', "Auto"),
                'snapshot_rg': self.tcinputs.get('SnapshotRG', None),
                'subclient_obj': self.subclient,
                'testcase_obj': self,
                'auto_vsa_subclient': subclient_initialize(self)
            }

            set_inputs(vsa_obj_inputs, vsa_obj)
            self.log.info("Created VSA object successfully.")

            decorative_log("Backup")
            vsa_obj.backup_type = "INCR"
            vsa_obj.backup()

            decorative_log("Attach Disk")

            try:
                # Attach Disk Restore
                vsa_obj.agentless_vm = self.tcinputs.get('AgentlessVM', None)
                vsa_obj.attach_disk_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            decorative_log("File Level restore")

            try:
                # File level Restore
                vsa_obj.file_level_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            decorative_log("In Place Full VM Restore")

            try:
                # Full VM In Place restore
                vsa_obj.unconditional_overwrite = True
                vsa_obj.full_vm_in_place = True
                vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            decorative_log("out of Place Full VM Restore")

            try:
                # Full VM out of Place restore
                vsa_obj.unconditional_overwrite = True
                vsa_obj.full_vm_in_place = False
                vsa_obj.full_vm_restore()
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:

            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                browser.close()
                if vsa_obj:
                    vsa_obj.cleanup_testdata()

            except:
                self.log.warning("Testcase and/or Restored VM cleanup was not completed")
                pass

            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
