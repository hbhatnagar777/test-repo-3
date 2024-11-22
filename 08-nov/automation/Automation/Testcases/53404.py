
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
import os

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper
from VirtualServer.VSAUtils import VirtualServerHelper as VirtualServerhelper
from AutomationUtils import logger, constants


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA Azurestack backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Virtual Server - Azure stack - Incr - DiskBackup and Restores using Unix MA"
        self.id = os.path.basename(__file__).split(".py")[0]
        self.product = self.products_list.VIRTUALIZATIONAZURE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing %s testcase", self.id)

            log.info("------------Initialize helper objects--------------------")

            auto_commcell = VirtualServerhelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerhelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerhelper.AutoVSAVSInstance(
                auto_client, self.agent, self.instance)
            auto_backupset = VirtualServerhelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerhelper.AutoVSASubclient(auto_backupset, self.subclient)
            auto_subclient.validate_inputs("windows", "unix")

            try:
                log.info("-------------------------Backup---------------------")

                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                backup_options.backup_type = "INCREMENTAL"
                auto_subclient.backup(backup_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                log.info("---------------File Level restores--------------------")

                fs_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                fs_restore_options.metadata_collected = backup_options.collect_metadata
                if "FBRMA" in self.tcinputs:
                    fs_restore_options.fbr_ma = self.tcinputs["FBRMA"]
                if "BrowseMA" in self.tcinputs:
                    fs_restore_options.browse_ma = self.tcinputs["BrowseMA"]
                auto_subclient.guest_file_restore(fs_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                log.info("--------------FULL VM out of Place restores------------")

                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.unconditional_overwrite = True
                auto_subclient.virtual_machine_restore(vm_restore_options)

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

            try:
                log.info("---------------FULL VM in  Place restores--------------")

                vm_restore_options = OptionsHelper.FullVMRestoreOptions(auto_subclient, self)
                vm_restore_options.power_on_after_restore = True
                vm_restore_options.in_place_overwrite = True
                auto_subclient.virtual_machine_restore(vm_restore_options)

                log.info("Resetting the contents of subclient")
                auto_subclient.reset_subclient_content()

            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)

        except Exception as exp:
            log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)

            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
