# Copyright Commvault Systems, Inc.
# --------------------------------------------------------------------------
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


from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper
from AutomationUtils import logger, constants

class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Azure Stack backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Azurestack SYNTHETIC_FULL Snap Backup and Restore Cases"
        self.product = self.products_list.VIRTUALIZATIONAZURE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        try:

            log.info("Started executing %s testcase" % self.id)
            log.info(
                "-" * 25 + " Initialize helper objects " + "-" * 25)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)

            try:
                log.info(
                    "-" * 25 + " Backup " + "-" * 25)
                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                backup_options.backup_type = "SYNTHETIC_FULL"
                backup_options.backup_method = "SNAP"
                if backup_options.collect_metadata:
                    raise Exception("Metadata collection is enabled")
                auto_subclient.backup(backup_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)


            try:
                log.info(
                    "-" * 15 + " FULL VM out of Place restores " + "-" * 15)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.unconditional_overwrite = True
                auto_subclient.virtual_machine_restore(vm_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)


            try:
                log.info(
                    "-" * 15 + " FULL VM in Place restores " + "-" * 15)
                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.in_place_overwrite = True
                vm_restore_options.power_on_after_restore = True
                auto_subclient.virtual_machine_restore(vm_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)

            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
